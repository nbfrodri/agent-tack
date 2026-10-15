#!/usr/bin/env python3
"""Render settings and native launchers with the installer's actual Bash executable."""
import json
import os
import subprocess
import sys


def render(value, root, bash, windows=None):
    windows = os.name == 'nt' if windows is None else windows
    if isinstance(value, list):
        return [render(item, root, bash, windows) for item in value]
    if isinstance(value, dict):
        result = {key: render(item, root, bash, windows) for key, item in value.items()}
        command = result.get('command')
        if windows and isinstance(command, str) and '#tack' in command:
            # The inner Bash parses POSIX quoting and the ownership comment, including for
            # Python adapters. Never let native Windows resolve bash to the WSL launcher.
            result['command'] = subprocess.list2cmdline(
                [bash, '--noprofile', '--norc', '-c', 'export PATH=/usr/bin:/bin:$PATH; ' + command])
        return result
    return value.replace('__REPO__', root) if isinstance(value, str) else value


def launcher(root, bash):
    # Batch expansion happens even inside quotes. Delayed expansion must stay off.
    bash = bash.replace('%', '%%')
    script = (root + '/bin/tack').replace('%', '%%')
    tools = bash.rsplit('/', 1)[0]
    return ('@echo off\nsetlocal DisableDelayedExpansion\n'
            f'set "PATH={tools};%PATH%"\n'
            f'"{bash}" "{script}" %*\nexit /b %errorlevel%\n')


def main():
    if len(sys.argv) != 4:
        sys.exit('usage: render_settings.py TEMPLATE|--launcher ROOT BASH')
    source, root, bash = sys.argv[1:]
    # Keep Bash script paths in the caller's POSIX spelling across native Python.
    root = os.environ.get('TACK_RENDER_ROOT', root)
    if source == '--launcher':
        sys.stdout.write(launcher(root, bash))
    else:
        with open(source, encoding='utf-8') as stream:
            result = render(json.load(stream), root, bash)
        json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write('\n')


if __name__ == '__main__':
    main()
