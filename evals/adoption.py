#!/usr/bin/env python3
"""Bounded three-session adoption journeys; hidden grading runs separately afterwards."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import signal
import subprocess
import sys
import time

from adoption_fixture import PROMPTS, seed


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def tree_hash(root):
    digest = hashlib.sha256()
    for path in sorted(root.rglob('*')):
        if path.is_file() and '.git' not in path.parts and '__pycache__' not in path.parts:
            digest.update(path.relative_to(root).as_posix().encode() + b'\0' + path.read_bytes() + b'\0')
    return digest.hexdigest()


def command(args, env, cwd=None, check=True, timeout=120):
    result = subprocess.run([str(a) for a in args], env=env, cwd=cwd, capture_output=True,
                            text=True, encoding='utf-8', errors='replace', timeout=timeout)
    if check and result.returncode:
        raise RuntimeError(f'{args[0]} exited {result.returncode}: {result.stderr[-2000:]}')
    return dict(exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr)


@contextmanager
def participant(home, auth):
    home.mkdir(mode=0o700)
    env = {key: value for key, value in os.environ.items()
           if key in ('PATH', 'TERM', 'LANG', 'SSL_CERT_FILE', 'SSL_CERT_DIR', 'HTTPS_PROXY', 'HTTP_PROXY', 'NO_PROXY')}
    env.update(HOME=str(home), CODEX_HOME=str(home / '.codex'), XDG_CONFIG_HOME=str(home / '.config'),
               XDG_CACHE_HOME=str(home / '.cache'), XDG_STATE_HOME=str(home / '.local/state'),
               XDG_DATA_HOME=str(home / '.local/share'), GIT_CONFIG_NOSYSTEM='1',
               GIT_CONFIG_GLOBAL=str(home / '.gitconfig'),
               PATH=str(home / '.local/bin') + os.pathsep + env.get('PATH', ''), PYTHONDONTWRITEBYTECODE='1')
    (home / '.codex').mkdir(mode=0o700)
    if auth:
        shutil.copyfile(auth, home / '.codex/auth.json')
        (home / '.codex/auth.json').chmod(0o600)
    try:
        for key, value in [('user.name', 'Eval'), ('user.email', 'eval@example.com'), ('init.defaultBranch', 'main')]:
            command(['git', 'config', '--global', key, value], env)
        yield env
    finally:
        # Only the new, private participant directory owned by this context is removed.
        shutil.rmtree(home)


def transcript_metrics(path):
    usage = {key: 0 for key in ('input_tokens', 'cached_input_tokens', 'output_tokens')}
    completed, errors, commands = 0, [], []
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get('type') == 'turn.completed':
            completed += 1
            for key in usage:
                usage[key] += event.get('usage', {}).get(key, 0)
        if event.get('type') in ('turn.failed', 'error'):
            errors.append(event)
        item = event.get('item', {})
        if event.get('type') == 'item.completed' and item.get('type') == 'command_execution':
            commands.append({'command': item.get('command'), 'exit_code': item.get('exit_code')})
    return dict(usage=usage, completed_turns=completed, errors=errors, commands=commands)


def invoke(repo, stage, out, env, args, model):
    prompt = PROMPTS[stage]
    (out / 'prompt.txt').write_text(prompt, encoding='utf-8', newline='\n')
    env = dict(env, TACK_BENCH_CODEX=args.codex)
    call = [sys.executable, str(args.launcher), 'exec', '--json', '--model', model,
            '-s', 'workspace-write', '-c', 'sandbox_workspace_write.network_access=true',
            '--skip-git-repo-check', '-C', str(repo), prompt]
    started = time.monotonic()
    with (out / 'transcript.jsonl').open('w', encoding='utf-8') as stream, (out / 'stderr.log').open('w', encoding='utf-8') as errors:
        process = subprocess.Popen(call, env=env, stdout=stream, stderr=errors,
                                   stdin=subprocess.DEVNULL, start_new_session=True)
        try:
            rc = process.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            rc = 124
        except BaseException:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            raise
    result = transcript_metrics(out / 'transcript.jsonl')
    result.update(exit_code=rc, seconds=round(time.monotonic() - started, 3),
                  completed=rc == 0 and result['completed_turns'] > 0,
                  prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest())
    observed = repo.parent / 'runtime-observation.json'
    if observed.exists():
        result['runtime'] = json.loads(observed.read_text(encoding='utf-8'))
        observed.unlink()
    save(out / 'session.json', result)
    return result


def snapshot(repo, out, env, base):
    shutil.copytree(repo, out / 'repo', symlinks=True,
                    ignore=shutil.ignore_patterns('.git', 'node_modules', '.cache'))
    for name, arguments in [('status', ['status', '--porcelain']),
                            ('history', ['log', '--format=full', base + '..HEAD']),
                            ('diff', ['diff', '--binary', base]), ('head', ['rev-parse', 'HEAD'])]:
        result = command(['git', '-C', repo, *arguments], env, check=False)
        (out / (name + '.txt')).write_text(result['stdout'], encoding='utf-8', newline='\n')
    save(out / 'public-tests.json', command(['npm', 'test'], env, repo, check=False))


def install(product, out, env):
    started = time.monotonic()
    result = command(['bash', product / 'install.sh', '--skip-plugins'], env, timeout=180)
    result['seconds'] = round(time.monotonic() - started, 3)
    save(out, result)


def journey(run, args):
    name, model, condition = run
    directory = args.output / name
    directory.mkdir()
    result = dict(run_id=name, model=model, condition=condition, stages={}, product_revision=args.revision)
    save(directory / 'journey.json', result)
    first = directory / 'first-clone'
    first.mkdir()
    try:
        with participant(directory / 'private-home-a', args.auth) as env:
            initial = seed(first)
            save(directory / 'fixture-hashes.json', {k: hashlib.sha256(v.encode()).hexdigest() for k, v in initial.items()})
            command(['git', 'init', '-q', '-b', 'main', first], env)
            command(['git', '-C', first, 'add', '.'], env)
            command(['git', '-C', first, 'commit', '-q', '-m', 'feat: seed dispatch service'], env)
            base = command(['git', '-C', first, 'rev-parse', 'HEAD'], env)['stdout'].strip()
            if condition == 'tack':
                install(args.product, directory / 'install-a.json', env)
                command(['bash', args.product / 'bin/tack', 'enable'], env, first)
                command(['bash', args.product / 'bin/tack', 'trust'], env, first)
            stage = directory / 'setup'
            stage.mkdir()
            result['stages']['setup'] = invoke(first, 'setup', stage, env, args, model)
            snapshot(first, stage, env, base)
            save(directory / 'journey.json', result)
        if not result['stages']['setup']['completed']:
            return result
        second = directory / 'second-clone'
        with participant(directory / 'private-home-b', args.auth) as env:
            command(['git', 'clone', '-q', '--no-hardlinks', first, second], env)
            base = command(['git', '-C', second, 'rev-parse', 'HEAD'], env)['stdout'].strip()
            # The committed setup is the teammate's trunk, regardless of its source branch name.
            if command(['git', '-C', second, 'show-ref', '--verify', 'refs/heads/main'], env, check=False)['exit_code']:
                command(['git', '-C', second, 'branch', 'main', 'HEAD'], env)
            if condition == 'tack':
                install(args.product, directory / 'install-b.json', env)
                observations = {}
                for key, options in [('enabled', ['status']), ('trust', ['trusted']),
                                     ('config', ['config', '--json']), ('mode', ['mode']), ('context', ['context'])]:
                    observations[key] = command(['bash', args.product / 'bin/tack', *options], env, second, check=False)
                save(directory / 'second-clone-observations.json', observations)
                command(['bash', args.product / 'bin/tack', 'trust'], env, second)
            for name in ('bug', 'feature'):
                stage = directory / name
                stage.mkdir()
                result['stages'][name] = invoke(second, name, stage, env, args, model)
                snapshot(second, stage, env, base)
                if condition == 'tack':
                    save(stage / 'verify.json', command(['bash', args.product / 'bin/tack', 'verify', '--base', base, '--json'],
                                                        env, second, check=False, timeout=150))
                save(directory / 'journey.json', result)
                if not result['stages'][name]['completed']:
                    break
                head = command(['git', '-C', second, 'rev-parse', 'HEAD'], env)['stdout'].strip()
                # Integrate only delivered commits. Never commit or discard unresolved edits.
                branch = command(['git', '-C', second, 'branch', '--show-current'], env)['stdout'].strip()
                if branch != 'main' and command(['git', '-C', second, 'merge-base', '--is-ancestor', 'main', head], env, check=False)['exit_code'] == 0:
                    command(['git', '-C', second, 'branch', '-f', 'main', head], env)
                base = head
    except Exception as error:
        result['infrastructure_error'] = str(error)
    finally:
        save(directory / 'journey.json', result)
    return result


def matrix(manifest):
    if manifest.get('effort') != 'medium':
        raise ValueError('the pinned launcher supports medium effort only')
    if manifest.get('conditions') != ['baseline', 'tack'] or not manifest.get('models'):
        raise ValueError('baseline and tack conditions and explicit models are required')
    if any(type(manifest.get(k)) is not int or manifest[k] <= 0 for k in ('repetitions', 'concurrency', 'timeout_seconds', 'max_sessions')):
        raise ValueError('positive integer limits are required')
    if manifest['concurrency'] > 2:
        raise ValueError('at most two journeys may run concurrently')
    runs = [(f'm{i}-{condition}-{rep}', model, condition) for i, model in enumerate(manifest['models'])
            for condition in manifest['conditions'] for rep in range(1, manifest['repetitions'] + 1)]
    if len(runs) * len(PROMPTS) > manifest['max_sessions']:
        raise ValueError('session limit exceeded')
    random.Random(manifest['seed']).shuffle(runs)
    return runs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--product', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--auth', type=Path)
    parser.add_argument('--launcher', type=Path, required=True)
    parser.add_argument('--codex', default='/usr/local/bin/codex')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    runs = matrix(manifest)
    if args.dry_run:
        print(json.dumps(runs, indent=2))
        return 0
    if os.name != 'posix' or not args.auth or not args.auth.is_file():
        raise ValueError('execution requires Linux/macOS and a private subscription auth file')
    args.timeout, args.revision = manifest['timeout_seconds'], manifest['product_revision']
    args.product, args.output, args.launcher = args.product.resolve(), args.output.resolve(), args.launcher.resolve()
    args.output.mkdir()  # Refuse reuse; never replace previous evidence.
    save(args.output / 'manifest.json', manifest)
    save(args.output / 'order.json', runs)
    source_hash = tree_hash(args.product)
    save(args.output / 'fingerprints.json', {'product_sha256': source_hash,
         'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         'fixture_sha256': hashlib.sha256(Path(__file__).with_name('adoption_fixture.py').read_bytes()).hexdigest(),
         'launcher_sha256': hashlib.sha256(args.launcher.read_bytes()).hexdigest(),
         'prompts': {name: hashlib.sha256(prompt.encode()).hexdigest() for name, prompt in PROMPTS.items()}})
    save(args.output / 'versions.json', {tool: command(call, os.environ)['stdout'].strip() for tool, call in
                                      [('codex', [args.codex, '--version']), ('node', ['node', '--version']), ('git', ['git', '--version'])]})
    with ThreadPoolExecutor(max_workers=manifest['concurrency']) as pool:
        futures = [pool.submit(journey, run, args) for run in runs]
        for future in as_completed(futures):
            result = future.result()
            print(result['run_id'], {k: v['completed'] for k, v in result['stages'].items()},
                  result.get('infrastructure_error', ''), flush=True)
    save(args.output / 'source-integrity.json', {'unchanged': source_hash == tree_hash(args.product)})
    return 0


if __name__ == '__main__':
    sys.exit(main())
