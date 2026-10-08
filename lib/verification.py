#!/usr/bin/env python3
"""Select project checks from changes and report execution evidence, never inferred correctness."""
import argparse
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

MAP = 'checks-map.json'
BASH = os.environ.get('TACK_VERIFY_BASH') or shutil.which('bash') or 'bash'
SOURCE = re.compile(r'\.(py|js|jsx|ts|tsx|mjs|cjs|go|rs|java|kt|rb|php|cs|swift|c|h|cc|cpp|hpp|scala|ex|exs|vue|svelte|dart|sh)$')
CONFIG = {'package.json', 'pyproject.toml', 'pytest.ini', 'setup.cfg', 'tox.ini', 'Cargo.toml',
          'Cargo.lock', 'go.mod', 'go.sum', 'Makefile', 'makefile', 'GNUmakefile', 'uv.lock',
          'package-lock.json', 'pnpm-lock.yaml', 'yarn.lock', 'bun.lock', 'bun.lockb'}


def git(root, *args, optional=False):
    result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, timeout=15)
    if result.returncode and not optional:
        raise ValueError(result.stderr.decode('utf-8', errors='replace').strip() or 'Git inspection failed')
    return result.stdout if result.returncode == 0 else b''


def paths(data):
    return {os.fsdecode(part) for part in data.split(b'\0') if part}


def changes(root, base):
    head = git(root, 'rev-parse', '--verify', 'HEAD', optional=True).strip().decode()
    if base:
        ref = git(root, 'rev-parse', '--verify', '--end-of-options', base + '^{commit}').strip().decode()
        base = git(root, 'merge-base', head, ref).strip().decode() if head else ref
    elif head:
        branch = git(root, 'branch', '--show-current').strip().decode()
        base = head
        if branch not in ('main', 'master', 'develop'):
            for name in ('main', 'master', 'develop'):
                ancestor = git(root, 'merge-base', head, name, optional=True).strip().decode()
                if ancestor:
                    base = ancestor
                    break
    changed = paths(git(root, 'ls-files', '--others', '--exclude-standard', '-z'))
    if base:
        changed |= paths(git(root, 'diff', '--no-ext-diff', '--no-textconv', '--no-renames', '--name-only', '-z', base, '--'))
        changed |= paths(git(root, 'diff', '--cached', '--no-ext-diff', '--no-textconv', '--no-renames', '--name-only', '-z', base, '--'))
    else:
        changed |= paths(git(root, 'ls-files', '--cached', '-z'))
    if len(changed) > 20000:
        raise ValueError('More than 20000 changed paths; narrow the task before verification')
    return sorted(changed), base or None


def definitions(root, source):
    path = root / MAP
    if path.is_symlink():
        raise ValueError(f'{MAP} must be a regular project file, not a symlink')
    if path.exists():
        if not path.is_file() or path.stat().st_size > 131072:
            raise ValueError(f'{MAP} must be a regular file no larger than 128 KiB')
        data = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data, dict) or set(data) != {'version', 'checks'} or type(data['version']) is not int or data['version'] != 1:
            raise ValueError(f'{MAP}: expected version 1 and checks')
        checks = data['checks']
        if not isinstance(checks, list) or len(checks) > 32:
            raise ValueError(f'{MAP}: checks must be a list of at most 32 entries')
        seen = set()
        for entry in checks:
            if not isinstance(entry, dict) or set(entry) - {'id', 'paths', 'command', 'timeout_seconds'}:
                raise ValueError(f'{MAP}: invalid check fields')
            name, patterns, command = (entry.get(k) for k in ('id', 'paths', 'command'))
            if not isinstance(name, str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,63}', name) or name in seen:
                raise ValueError(f'{MAP}: check IDs must be unique lowercase names')
            seen.add(name)
            if not isinstance(patterns, list) or not patterns or len(patterns) > 64 or any(
                    not isinstance(p, str) or not p or len(p) > 512 or '\x00' in p or p.startswith('/') or '..' in p.split('/') for p in patterns):
                raise ValueError(f'{MAP}: {name} needs project-relative path patterns')
            if not isinstance(command, str) or not command.strip() or len(command) > 8192 or '\x00' in command:
                raise ValueError(f'{MAP}: {name} needs a bounded command string')
            timeout = entry.get('timeout_seconds', 60)
            if type(timeout) is not int or not 1 <= timeout <= 600:
                raise ValueError(f'{MAP}: {name} timeout_seconds must be 1..600')
            entry.update(source=MAP, timeout_seconds=timeout)
        return checks, True
    detected = subprocess.run([BASH, str(source / 'lib/test-command.sh'), str(source), str(root)],
                              cwd=root, capture_output=True, text=True, encoding='utf-8', timeout=15)
    if detected.returncode:
        raise ValueError('Canonical test-command detection failed')
    command, separator, origin = detected.stdout.strip().partition('\t')
    if not command or not separator:
        return [], False
    return [dict(id='project-check', paths=[], command=command, source=origin, timeout_seconds=120)], False


def matches(path, pattern):
    # Like shell case patterns, '*' spans directories; '**/' also matches zero directories.
    return fnmatch.fnmatchcase(path, pattern) or ('**/' in pattern and fnmatch.fnmatchcase(path, pattern.replace('**/', '')))


def plan(root, source, base=None):
    changed, base = changes(root, base)
    checks, mapped = definitions(root, source)
    selected, covered = [], set()
    for check in checks:
        matched = [p for p in changed if (p == MAP or any(matches(p, pattern) for pattern in check['paths']))] if mapped else [
            p for p in changed if check['source'] == 'tack config check-fast' or SOURCE.search(p) or Path(p).name in CONFIG]
        if not matched:
            continue
        covered.update(matched)
        duplicate = next((c for c in selected if c['command'] == check['command']), None)
        if duplicate:
            duplicate['ids'].append(check['id'])
            duplicate['matched_paths'] = sorted(set(duplicate['matched_paths']) | set(matched))
            duplicate['timeout_seconds'] = min(duplicate['timeout_seconds'], check['timeout_seconds'])
        else:
            selected.append({**check, 'ids': [check['id']], 'matched_paths': matched, 'status': 'planned'})
    return dict(version=1, base=base, changed_paths=changed, checks=selected,
                unmapped_paths=sorted(set(changed) - covered), mapped=mapped, status='planned',
                note='Selected checks are declared verification, not proof of complete semantic coverage.')


def snapshot(root):
    digest = hashlib.sha256()
    head = git(root, 'rev-parse', '--verify', 'HEAD', optional=True).strip()
    digest.update(head)
    if head:
        digest.update(git(root, 'diff', '--no-ext-diff', '--no-textconv', '--binary', head.decode(), '--'))
        digest.update(git(root, 'diff', '--cached', '--no-ext-diff', '--no-textconv', '--binary', head.decode(), '--'))
    else:
        digest.update(git(root, 'diff', '--cached', '--no-ext-diff', '--no-textconv', '--binary', '--'))
    # Include untracked inputs, but never follow their symlinks outside the repository.
    names = paths(git(root, 'ls-files', '--others', '--exclude-standard', '-z'))
    if not head:
        names |= paths(git(root, 'ls-files', '--cached', '-z'))
    for name in sorted(names):
        path = root / name
        digest.update(os.fsencode(name) + b'\0')
        if path.is_symlink():
            digest.update(os.fsencode(os.readlink(path)))
        elif path.is_file():
            with path.open('rb') as stream:
                for chunk in iter(lambda: stream.read(65536), b''):
                    digest.update(chunk)
    return digest.hexdigest()


def execute(check, root, timeout):
    started = time.monotonic()
    environment = os.environ.copy()
    environment.pop('BASH_ENV', None)
    environment.pop('ENV', None)
    options = {'start_new_session': True} if os.name != 'nt' else {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP}
    with tempfile.TemporaryFile() as output:
        process = subprocess.Popen([BASH, '--noprofile', '--norc', '-o', 'pipefail', '-c', check['command']],
                                   cwd=root, env=environment, stdin=subprocess.DEVNULL, stdout=output,
                                   stderr=subprocess.STDOUT, **options)
        try:
            code = process.wait(timeout=timeout)
            check['status'] = 'passed' if code == 0 else 'failed'
        except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
            if os.name == 'nt':
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True, timeout=10)
                if process.poll() is None:
                    process.kill()
            else:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            process.wait(timeout=10)
            if isinstance(error, KeyboardInterrupt):
                raise
            code, check['status'] = 124, 'timed_out'
        check.update(exit_code=code, duration_s=round(time.monotonic() - started, 3))
        if code:
            output.seek(0, 2)
            output.seek(max(0, output.tell() - 4096))
            check['output_tail'] = output.read().decode('utf-8', errors='replace')


def run(report, root, trusted, budget):
    if report['checks'] and not trusted:
        for check in report['checks']:
            check['status'] = 'untrusted'
        report['status'] = 'untrusted'
        return 2
    if not report['checks']:
        report['status'] = 'unverified' if report['changed_paths'] else 'no_changes'
        return 3 if report['changed_paths'] else 0
    before = snapshot(root)
    deadline = time.monotonic() + budget
    for check in report['checks']:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            check['status'] = 'budget_exhausted'
        else:
            execute(check, root, min(remaining, check['timeout_seconds']))
    report['inputs_changed'] = before != snapshot(root)
    if any(c['status'] in ('failed', 'timed_out') for c in report['checks']):
        report['status'] = 'failed'
        return 1
    if report['inputs_changed'] or report['unmapped_paths'] or any(c['status'] != 'passed' for c in report['checks']):
        report['status'] = 'incomplete'
        return 3
    report['status'] = 'passed'
    return 0


def render(report):
    print(f"Verification: {report['status']} ({len(report.get('changed_paths', []))} changed paths)")
    if report.get('error'):
        print(report['error'])
    for check in report.get('checks', []):
        print(f"- {','.join(check['ids'])}: {check['status']}: {check['command']} (from {check['source']})")
        if check.get('output_tail'):
            print(check['output_tail'].rstrip())
    if report.get('unmapped_paths'):
        print('No check selected for: ' + ', '.join(repr(p) for p in report['unmapped_paths'][:30]))
    if report.get('inputs_changed'):
        print('Checks changed repository inputs; review those changes and verify again.')
    if report['status'] == 'untrusted':
        print('Commands were not run: local execution trust is required (tack trust).')
    print(report.get('note', 'No verification result is available.'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('source', type=Path)
    parser.add_argument('--plan', action='store_true')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--base')
    parser.add_argument('--budget-seconds', type=int, default=120)
    args = parser.parse_args()
    try:
        if not 1 <= args.budget_seconds <= 600:
            raise ValueError('budget-seconds must be 1..600')
        report = plan(args.root, args.source, args.base)
        code = 0 if args.plan else run(report, args.root, os.environ.get('TACK_VERIFY_TRUSTED') == '1', args.budget_seconds)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        report, code = {'version': 1, 'status': 'error', 'error': str(error)}, 2
    if args.json:
        print(json.dumps(report, ensure_ascii=True))
    else:
        render(report)
    return code


if __name__ == '__main__':
    sys.exit(main())
