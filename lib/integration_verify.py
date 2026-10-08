"""Run declared checks against pinned, prospectively merged commits in a temporary checkout."""
import os
from pathlib import Path
import subprocess

from team import merge_probe, output, resolve
from verification import plan, render as render_checks, run


def inspect_integration(root, against, preview, budget):
    if not 1 <= budget <= 600:
        raise ValueError('budget-seconds must be 1..600')
    head, revision = resolve(root, 'HEAD'), resolve(root, against)
    branch = output(root, 'branch', '--show-current').strip()
    result = dict(version=1, kind='integration', head=head, branch=branch,
                  against=dict(ref=against, commit=revision), status='unknown',
                  note='Committed trees only; local settings, ignored files and dependencies are not copied. '
                       'Trusted checks run in a temporary checkout, not a security sandbox. No fetch or installation.')
    if not head or not revision:
        result['reason'] = 'Missing local reference or no HEAD commit'
        return result, 3
    if output(root, 'status', '--porcelain=v1', '-z', '--untracked-files=normal'):
        result.update(status='dirty', reason='Commit or isolate unfinished changes before checking a prospective merge; use tack verify for the working tree.')
        return result, 2
    source = Path(__file__).resolve().parent.parent
    environment = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    environment.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1', GIT_TERMINAL_PROMPT='0')
    code = 3

    def inspect_tree(probe, tree):
        nonlocal code
        checkout = probe.parent / 'checkout'
        ancestor = output(probe, 'merge-base', head, revision).strip()
        output(probe, 'worktree', 'add', '--quiet', '--detach', str(checkout), head)
        output(checkout, 'config', 'core.hooksPath', os.devnull)
        output(checkout, 'read-tree', '--reset', '-u', tree)
        verification = plan(checkout, source, base=ancestor, environment=environment)
        result.update(ancestor=ancestor, merged_tree=tree)
        code = 0 if preview else run(verification, checkout,
                                    os.environ.get('TACK_VERIFY_TRUSTED') == '1', budget, environment)
        if not preview and not verification['checks']:
            verification['status'], code = 'unverified', 3
        return verification

    try:
        merged = merge_probe(root, head, revision, inspect_tree)
        result['verification'] = merged.pop('verification', None)
        result['merge'] = merged
        if result['verification'] is not None:
            result['status'] = result['verification']['status']
        elif merged['status'] == 'conflict':
            result['status'], code = 'conflict', 1
        else:
            code = 3
            result['reason'] = merged.get('reason', 'No integration result is available')
        if (resolve(root, 'HEAD') != head or resolve(root, against) != revision
                or output(root, 'branch', '--show-current').strip() != branch
                or output(root, 'status', '--porcelain=v1', '-z', '--untracked-files=normal')):
            result.update(status='incomplete', reason='Source revisions or worktree changed during verification; this result is stale.')
            code = 3
        return result, code
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        result.update(status='error', reason=str(error))
        return result, 2


def render(report):
    print('Integration verification: ' + report['status'])
    print('HEAD: ' + str(report['head']))
    print('Against: ' + str(report['against']['ref']) + ' (' + str(report['against']['commit']) + ')')
    if report.get('merged_tree'):
        print('Merged tree: ' + report['merged_tree'])
    if report.get('verification'):
        render_checks(report['verification'])
    if report.get('reason'):
        print(report['reason'])
    if report.get('merge', {}).get('conflicts'):
        print('Conflicting paths: ' + ', '.join(report['merge']['conflicts']))
    print(report['note'])
