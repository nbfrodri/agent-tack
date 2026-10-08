#!/usr/bin/env python3
"""Shared bounded Bash execution for project verification and advisory hooks."""
import os
import shutil
import signal
import subprocess
import tempfile
import time

BASH = os.environ.get('TACK_VERIFY_BASH') or shutil.which('bash') or 'bash'


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
