#!/usr/bin/env python3
"""Inspect locally known branches without changing the source repository."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def git(root, *args):
    # Do not inherit alternate indexes, injected config, external drivers or hooks.
    env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1',
               GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0', GIT_NO_REPLACE_OBJECTS='1')
    return subprocess.run(['git', '-C', str(root), '-c', 'core.fsmonitor=false',
                           '-c', 'core.hooksPath=/dev/null', *args], env=env,
                          capture_output=True, timeout=30)


def output(root, *args):
    result = git(root, *args)
    if result.returncode:
        raise ValueError('Git inspection failed: ' + result.stderr.decode('utf-8', errors='replace').strip()[:500])
    return result.stdout.decode('utf-8', errors='replace')


def resolve(root, ref):
    if not ref:
        return None
    result = git(root, 'rev-parse', '--verify', '--end-of-options', ref + '^{commit}')
    return result.stdout.decode('ascii').strip() if result.returncode == 0 else None


def names(root, ancestor, revision):
    return sorted(set(filter(None, output(root, 'diff', '--no-ext-diff', '--no-textconv',
                                        '--no-renames', '--name-only', '-z', ancestor, revision, '--').split('\0'))))


def merge_probe(root, left, right):
    try:
        with tempfile.TemporaryDirectory(prefix='tack-merge-') as directory:
            probe = Path(directory) / 'probe.git'
            cloned = git(root, 'clone', '--quiet', '--bare', '--shared', '--no-hardlinks',
                         '--template=', '--', str(root), str(probe))
            if cloned.returncode:
                return {'status': 'unknown', 'reason': 'Cannot create isolated local merge probe'}
            result = git(probe, 'merge-tree', '--write-tree', '--name-only', '--no-messages', '-z', left, right)
            if result.returncode not in (0, 1):
                return {'status': 'unknown', 'reason': 'Merge probe unavailable (Git 2.38+ required) or failed'}
            # Exit status is authoritative; some directory conflicts have no path list.
            records = result.stdout.decode('utf-8', errors='replace').split('\0')
            conflicts = []
            for path in records[1:]:
                if not path:
                    break
                conflicts.append(path)
            return {'status': 'clean' if result.returncode == 0 else 'conflict',
                    'conflicts': sorted(set(conflicts))}
    except (OSError, subprocess.SubprocessError):
        return {'status': 'unknown', 'reason': 'Isolated merge probe could not finish'}


def compare(root, head, ref):
    revision = resolve(root, ref)
    result = {'ref': ref, 'commit': revision, 'merge': {'status': 'unknown'}}
    if not head or not revision:
        result['merge']['reason'] = 'Missing local reference or no HEAD commit'
        return result
    ancestor = git(root, 'merge-base', head, revision)
    if ancestor.returncode:
        result['merge']['reason'] = 'No known common ancestor (possibly shallow history)'
        return result
    base = ancestor.stdout.decode('ascii').strip()
    behind, ahead = output(root, 'rev-list', '--left-right', '--count', revision + '...' + head).split()
    head_paths, other_paths = names(root, base, head), names(root, base, revision)
    result.update(ancestor=base, ahead=int(ahead), behind=int(behind), head_paths=head_paths,
                  other_paths=other_paths, overlap=sorted(set(head_paths) & set(other_paths)),
                  merge=merge_probe(root, revision, head))
    return result


def report(root, base, against):
    head = resolve(root, 'HEAD')
    if base is None:
        for candidate in ('refs/remotes/origin/HEAD', 'origin/main', 'origin/master', 'main', 'master'):
            if resolve(root, candidate):
                base = candidate
                break
    dirty = list(filter(None, output(root, 'status', '--porcelain=v1', '-z', '--untracked-files=normal').split('\0')))
    notes = ['Local references only; no fetch. Remote-tracking refs may be outdated.',
             'Merge probes inspect committed trees with built-in Git drivers only; clean does not prove API compatibility.']
    if dirty:
        notes.append('Uncommitted changes are listed but excluded from merge probes.')
    return {'version': 1, 'branch': output(root, 'branch', '--show-current').strip() or None,
            'head': head, 'dirty': dirty, 'notes': notes,
            'comparisons': [compare(root, head, ref) for ref in dict.fromkeys([base, *against])]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root')
    parser.add_argument('--base')
    parser.add_argument('--against', action='append', default=[])
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    root = args.root
    if os.name == 'nt' and root.startswith('/'):
        root = subprocess.check_output(['cygpath', '-w', root], text=True, encoding='utf-8').strip()
    result = report(Path(root).resolve(), args.base, args.against)
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print('Branch: ' + (result['branch'] or '(detached)'))
        print('HEAD: ' + (result['head'] or '(unborn)'))
        print('Uncommitted records: ' + str(len(result['dirty'])))
        for comparison in result['comparisons']:
            print('\nAgainst ' + json.dumps(comparison['ref']) + ': ' + comparison['merge']['status'])
            if 'ahead' in comparison:
                print(f"Ahead {comparison['ahead']}, behind {comparison['behind']}; overlaps: "
                      + json.dumps(comparison['overlap'], ensure_ascii=True))
            if comparison['merge'].get('conflicts'):
                print('Conflicting paths: ' + json.dumps(comparison['merge']['conflicts'], ensure_ascii=True))
            if comparison['merge'].get('reason'):
                print(comparison['merge']['reason'])
        for note in result['notes']:
            print(note)
    # A successful diagnostic can contain conflicts or unknowns; consumers inspect statuses.
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print('tack team: ' + str(error), file=sys.stderr)
        raise SystemExit(2)
