#!/usr/bin/env python3
"""List, and with --apply delete, local branches whose work is already on the base branch.

Usage: branches.py REPO [--apply]

A branch is deleted when it is an ancestor of main (or master), or when GitHub reports its
pull request merged and the branch tip is still that PR's head, so no later commit is lost.
Without gh a squash-merged branch looks unmerged and stays. The branch in use, including one
checked out in another worktree, and every unmerged branch stay.
"""
import argparse
import json
import shutil
import subprocess
import sys


def run(root, *command):
    return subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=60)


def git(root, *args):
    return run(root, 'git', *args)


def base_branch(root):
    for name in ('main', 'master'):
        if git(root, 'show-ref', '--verify', '--quiet', f'refs/heads/{name}').returncode == 0:
            return name
    return None


def in_use(root):
    """Branches checked out in this worktree or any other."""
    found = set()
    for line in git(root, 'worktree', 'list', '--porcelain').stdout.splitlines():
        if line.startswith('branch refs/heads/'):
            found.add(line[len('branch refs/heads/'):])
    return found


def merged_pull_request(root, branch, tip):
    """The number of the merged PR whose head is this branch's tip, else None."""
    result = run(root, 'gh', 'pr', 'list', '--state', 'merged', '--head', branch,
                 '--json', 'number,headRefOid', '--limit', '1')
    if result.returncode:
        return None
    try:
        pulls = json.loads(result.stdout or '[]')
    except ValueError:
        return None
    for pull in pulls if isinstance(pulls, list) else []:
        if isinstance(pull, dict) and pull.get('headRefOid') == tip:
            return pull.get('number')
    return None


def decide(root, base, have_gh):
    used = in_use(root)
    plan = []
    refs = git(root, 'for-each-ref', '--format=%(refname:short) %(objectname)', 'refs/heads').stdout.splitlines()
    for line in refs:
        name, _, tip = line.partition(' ')
        if name == base:
            continue
        if name in used:
            plan.append((name, 'keep', 'checked out', False))
        elif git(root, 'merge-base', '--is-ancestor', name, base).returncode == 0:
            plan.append((name, 'delete', f'merged into {base}', False))
        elif have_gh and (number := merged_pull_request(root, name, tip)) is not None:
            plan.append((name, 'delete', f'PR #{number} merged', True))
        else:
            plan.append((name, 'keep', 'not merged', False))
    return plan


def main():
    parser = argparse.ArgumentParser(prog='tack branches', add_help=False)
    parser.add_argument('root')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    base = base_branch(args.root)
    if base is None:
        print('tack: branches needs a main or master branch', file=sys.stderr)
        return 2
    have_gh = shutil.which('gh') is not None
    plan = decide(args.root, base, have_gh)
    width = max((len(name) for name, *_ in plan), default=0)
    failed = 0
    for name, action, reason, force in plan:
        if action == 'delete' and args.apply:
            result = git(args.root, 'branch', '-D' if force else '-d', name)
            if result.returncode:
                failed += 1
                print(f'failed   {name:<{width}} ({result.stderr.strip()[:200]})')
            else:
                print(f'deleted  {name:<{width}} ({reason})')
        else:
            print(f'{action:<8} {name:<{width}} ({reason})')
    if not have_gh:
        print('gh not found: branches merged by squash or rebase look unmerged and stay.')
    if not args.apply and any(action == 'delete' for _, action, *_ in plan):
        print('Dry run: tack branches --apply deletes the branches marked delete.')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
