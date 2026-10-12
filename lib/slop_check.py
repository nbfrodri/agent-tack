#!/usr/bin/env python3
"""Scan the code a branch changed with aislop and print the findings worth acting on.

Usage: slop_check.py ROOT [BASE]

aislop (https://github.com/scanaislop/aislop) is an optional deterministic scanner for what
coding assistants leave behind: swallowed errors, narrative comments, stubs, unsafe casts,
hardcoded secrets. It is used only when installed, or named in TACK_AISLOP; it is never
downloaded, and its telemetry and update checks are turned off. Prints nothing when there is
nothing to report. The completion hook calls this in trusted projects, because aislop reads the
project's .aislop configuration and may run its linters.
"""
import json
import os
import shutil
import subprocess
import sys

SECONDS = 60
SHOWN = 5
# A finding in a line the change did not touch is the project's existing state, not this work.
UNTOUCHED = 'existing-file-context'


def scanner():
    named = os.environ.get('TACK_AISLOP')
    if named:
        return named if os.path.isfile(named) and os.access(named, os.X_OK) else None
    return shutil.which('aislop')


def scan(binary, root, base):
    command = [binary, 'scan', '--changes', *(['--base', base] if base else []), '--json']
    env = dict(os.environ, AISLOP_NO_TELEMETRY='1', DO_NOT_TRACK='1', AISLOP_NO_UPDATE_NOTIFIER='1')
    try:
        result = subprocess.run(command, cwd=root, env=env, stdin=subprocess.DEVNULL, capture_output=True,
                                text=True, encoding='utf-8', errors='replace', timeout=SECONDS)
    except subprocess.TimeoutExpired:
        return None, f'it did not finish within {SECONDS} s'
    except OSError as error:
        return None, str(error)
    try:
        report = json.loads(result.stdout)
    except ValueError:
        report = None
    if not isinstance(report, dict) or not isinstance(report.get('diagnostics'), list):
        return None, f'exit {result.returncode} without a report'
    return report, ''


def describe(finding):
    place = str(finding.get('filePath', '?'))
    if isinstance(finding.get('line'), int):
        place += f':{finding["line"]}'
    text = ' '.join(str(finding.get('message', '')).split())[:160]
    return f'  {place} {finding.get("rule", "?")}: {text}'


def main():
    if len(sys.argv) < 2:
        return 2
    binary = scanner()
    if not binary:
        return 0
    report, problem = scan(binary, sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else '')
    if report is None:
        # No scan is not a clean scan.
        print(f'aislop could not scan the changes ({problem}): run aislop scan --changes to see why.')
        return 0
    found = [item for item in report['diagnostics']
             if isinstance(item, dict) and item.get('changeContext') != UNTOUCHED]
    if not found:
        return 0
    found.sort(key=lambda item: item.get('severity') != 'error')
    errors = sum(item.get('severity') == 'error' for item in found)
    print(f'aislop: {len(found)} finding(s) on changed code ({errors} error(s), {len(found) - errors} warning(s)):')
    for item in found[:SHOWN]:
        print(describe(item))
    if len(found) > SHOWN:
        print(f'  and {len(found) - SHOWN} more (aislop scan --changes)')
    print('  Fix the real ones (aislop fix applies the mechanical fixes) or say why one does not apply.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
