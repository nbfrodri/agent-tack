#!/usr/bin/env python3
"""Execute one bounded session inside a disposable container, never on the host."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time

ROOT = Path('/home/dev')
WORK = ROOT / 'work'
OUT = ROOT / 'evidence'


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def call(arguments, env, cwd=None, timeout=60):
    result = subprocess.run([str(x) for x in arguments], cwd=cwd or WORK, env=env, capture_output=True,
                            text=True, encoding='utf-8', errors='replace', timeout=timeout)
    return {'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}


def checked(arguments, env, cwd=None, timeout=60):
    result = call(arguments, env, cwd, timeout)
    if result['exit_code']:
        raise RuntimeError(f'{arguments[0]} failed: {result["stderr"][-1500:]}')
    return result


def environment(home):
    env = {key: value for key, value in os.environ.items() if key in ('PATH', 'LANG', 'SSL_CERT_FILE', 'SSL_CERT_DIR')}
    env.update(HOME=str(home), USERPROFILE=str(home), CODEX_HOME=str(home / '.codex'),
               XDG_CONFIG_HOME=str(home / '.config'), XDG_CACHE_HOME=str(home / '.cache'),
               XDG_STATE_HOME=str(home / '.local/state'), XDG_DATA_HOME=str(home / '.local/share'),
               GIT_CONFIG_GLOBAL=str(home / '.gitconfig'), GIT_CONFIG_NOSYSTEM='1',
               PYTHONDONTWRITEBYTECODE='1', PATH=str(home / '.local/bin') + os.pathsep + env.get('PATH', ''))
    return env


def prepare(job, env):
    for key, value in [('user.name', 'Eval'), ('user.email', 'eval@example.invalid'), ('init.defaultBranch', 'main')]:
        checked(['git', 'config', '--global', key, value], env)
    checked(['git', 'init', '-q', '-b', 'main'], env)
    checked(['git', 'add', '.'], env)
    checked(['git', 'commit', '-qm', 'feat: seed project'], env)
    save('base.json', {'head': checked(['git', 'rev-parse', 'HEAD'], env)['stdout'].strip()})
    product = ROOT / 'product'
    if not product.exists():
        return
    started = time.monotonic()
    installed = checked(['bash', product / 'install.sh', '--skip-plugins'], env, timeout=180)
    installed['seconds'] = time.monotonic() - started
    save('install.json', installed)
    tack = ['bash', product / 'bin/tack']
    checked([*tack, 'enable', '--shared'], env)
    if job['kind'] == 'code':
        (WORK / 'tack.json').write_text(json.dumps({'version': 1, 'mode': 'auto', 'config': {
            'reply-style': 'brief', 'conventional-commits': True, 'architecture-path': 'docs/architecture.md',
            'plans-path': 'work/plans', 'handoffs-path': 'work/handoffs',
            'check-fast': ' '.join(job['test_command'])}}), encoding='utf-8')
        (WORK / 'AGENTS.md').write_text('# Project\n\nProduct behavior: [contract](docs/contract.md). '
            'Structure: [architecture](docs/architecture.md).\n\nCommand: `' + ' '.join(job['test_command']) + '`.\n', encoding='utf-8')
        (WORK / 'CLAUDE.md').write_text('@AGENTS.md\n', encoding='utf-8')
        checked([*tack, 'config', 'setup-review', 'done'], env)
        checked(['git', 'add', '.'], env)
        checked(['git', 'commit', '-qm', 'chore: configure project'], env)
        save('base.json', {'head': checked(['git', 'rev-parse', 'HEAD'], env)['stdout'].strip()})
    checked([*tack, 'trust'], env)


def observe(home):
    models, efforts = set(), set()
    for path in (home / '.codex/sessions').rglob('*.jsonl'):
        for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get('type') == 'turn_context':
                context = event.get('payload', {})
                if isinstance(context.get('model'), str):
                    models.add(context['model'])
                effort = context.get('effort', context.get('reasoning_effort'))
                if isinstance(effort, str):
                    efforts.add(effort)
    return {'models': sorted(models), 'efforts': sorted(efforts), 'authentication': 'ChatGPT subscription'}


def product_hash():
    digest = hashlib.sha256()
    for path in sorted((ROOT / 'product').rglob('*')):
        if path.is_file() and not path.is_symlink() and '__pycache__' not in path.parts:
            digest.update(path.relative_to(ROOT / 'product').as_posix().encode() + b'\0' + path.read_bytes())
    return digest.hexdigest()


def teammate(env):
    home = ROOT / 'teammate-home'
    home.mkdir()
    fresh = environment(home)
    clone = ROOT / 'teammate'
    checked(['git', 'clone', '-q', '--no-hardlinks', WORK, clone], fresh, ROOT)
    checked(['git', 'config', '--global', 'tack.conventionalCommits', 'false'], fresh, clone)
    tack = ['bash', ROOT / 'product/bin/tack']
    observations = {name: call([*tack, *args], fresh, clone) for name, args in [
        ('config', ['config', '--json']), ('mode', ['mode']), ('activation', ['status']), ('trust', ['trusted'])]}
    checked(['git', 'config', '--local', 'tack.replyStyle', 'visual'], fresh, clone)
    observations['local_override'] = call([*tack, 'config', 'reply-style'], fresh, clone)
    save('teammate.json', observations)


def invoke(arguments, env, timeout):
    started = time.monotonic()
    with (OUT / 'transcript.jsonl').open('w', encoding='utf-8') as stream, (OUT / 'stderr.log').open('w', encoding='utf-8') as errors:
        process = subprocess.Popen(arguments, env=env, cwd=WORK, stdout=stream, stderr=errors,
                                   stdin=subprocess.DEVNULL, start_new_session=True)
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            code = 124
    return {'exit_code': code, 'seconds': round(time.monotonic() - started, 3)}


def capture(job, env):
    shutil.copytree(WORK, OUT / 'repo', symlinks=True,
                    ignore=shutil.ignore_patterns('.git', 'node_modules', '__pycache__', '.cache'))
    base = json.loads((OUT / 'base.json').read_text(encoding='utf-8'))['head']
    save('git.json', {name: call(['git', *args], env) for name, args in [
        ('status', ['status', '--porcelain']), ('diff', ['diff', '--binary', base]),
        ('history', ['log', '--format=full', base + '..HEAD'])]})
    save('public-tests.json', call(job['test_command'], env, timeout=60))


def main():
    OUT.mkdir()
    job = json.loads((ROOT / 'job.json').read_text(encoding='utf-8'))
    home = ROOT / 'participant'
    (home / '.codex').mkdir(parents=True, mode=0o700)
    shutil.copyfile(ROOT / 'auth.json', home / '.codex/auth.json')
    (home / '.codex/auth.json').chmod(0o600)
    (ROOT / 'auth.json').unlink()
    env = environment(home)
    result = {'completed': False, 'exit_code': None, 'seconds': None}
    before = product_hash()
    try:
        save('versions.json', {name: checked(args, env)['stdout'].strip() for name, args in [
            ('codex', ['/usr/local/bin/codex', '--version']), ('python', ['python3', '--version']),
            ('node', ['node', '--version']), ('git', ['git', '--version'])]})
        if job['kind'] != 'review':
            prepare(job, env)
        arguments = ['/usr/local/bin/codex', 'exec', '--json', '--skip-git-repo-check',
                     '--model', job['model'], '-c', 'model_reasoning_effort=' + json.dumps(job['effort']),
                     '-C', str(WORK)]
        if job['kind'] == 'review':
            arguments += ['-s', 'read-only', '--output-schema', str(ROOT / 'schema.json'),
                          '-o', str(OUT / 'review.json')]
        else:
            profile = ('permissions.benchmark={extends=":workspace",'
                       'filesystem={":workspace_roots"={".git"="write"}},network={enabled=false}}')
            arguments += ['-c', 'default_permissions="benchmark"', '-c', profile,
                          '--dangerously-bypass-hook-trust', '-c', 'developer_instructions=' + json.dumps(
                              'Work only in this local repository. Do not publish, install dependencies, '
                              'contact external services, launch subagents or ask questions. Return the local result.')]
        arguments.append(job['prompt'])
        result.update(invoke(arguments, env, job['timeout_seconds']), runtime=observe(home))
        events = []
        for line in (OUT / 'transcript.jsonl').read_text(encoding='utf-8').splitlines():
            try:
                events.append(json.loads(line))
            except ValueError:
                continue
        result['completed'] = result['exit_code'] == 0 and any(e.get('type') == 'turn.completed' for e in events)
        if job['kind'] != 'review':
            capture(job, env)
            if job['kind'] == 'setup':
                teammate(env)
    except Exception as error:
        result['infrastructure_error'] = str(error)
    finally:
        result['product_unchanged'] = before == product_hash()
        if not result['product_unchanged']:
            result['infrastructure_error'] = 'Frozen product source changed during execution'
        save('session.json', result)
        # Private homes/authentication never leave this disposable container.
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
