#!/usr/bin/env python3
"""Run one trusted hook command through the shared executor; output failure evidence."""
from pathlib import Path
import subprocess
import sys

from check_execution import execute


def main():
    try:
        root, seconds, command = sys.argv[1:]
        timeout = int(seconds)
        if not 1 <= timeout <= 600:
            raise ValueError('timeout must be 1..600 seconds')
        check = {'command': command}
        execute(check, Path(root), timeout)
        if check.get('output_tail'):
            print(check['output_tail'], end='')
        return check['exit_code'] if check['exit_code'] >= 0 else 1
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f'tack check: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
