#!/usr/bin/env python3
"""Run an evaluation in an ephemeral home; only authentication crosses the boundary."""
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile


def main():
    root = Path(__file__).resolve().parent.parent
    original = os.environ.copy()
    def interrupted(signum, _frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, interrupted)
    with tempfile.TemporaryDirectory(prefix='tack-eval-home-') as temp:
        home = Path(temp)
        env = original.copy()
        for key in list(env):
            if key.startswith('GIT_CONFIG_') or key in (
                    'GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR',
                    'GIT_OBJECT_DIRECTORY', 'GIT_ALTERNATE_OBJECT_DIRECTORIES', 'BASH_ENV', 'ENV'):
                env.pop(key)
        env.update(HOME=temp, XDG_CONFIG_HOME=str(home / '.config'),
                   XDG_STATE_HOME=str(home / '.local/state'), XDG_DATA_HOME=str(home / '.local/share'),
                   XDG_CACHE_HOME=str(home / '.cache'), CODEX_HOME=str(home / '.codex'),
                   CLAUDE_CONFIG_DIR=str(home / '.claude'), GIT_CONFIG_NOSYSTEM='1',
                   GIT_CONFIG_GLOBAL=str(home / '.gitconfig'), TACK_EVAL_ISOLATED='1',
                   PATH=str(home / '.local/bin') + os.pathsep + original.get('PATH', ''))
        for directory in (home / '.codex', home / '.claude', home / '.config'):
            directory.mkdir(mode=0o700)
        for source, target in (
            (Path(original.get('CODEX_HOME', str(Path(original['HOME']) / '.codex'))) / 'auth.json', home / '.codex/auth.json'),
            (Path(original.get('CLAUDE_CONFIG_DIR', str(Path(original['HOME']) / '.claude'))) / '.credentials.json', home / '.claude/.credentials.json'),
        ):
            if source.is_file():
                shutil.copyfile(source, target)
                target.chmod(0o600)
        for key, value in [('user.name', 'Eval'), ('user.email', 'eval@example.com'), ('init.defaultBranch', 'main')]:
            subprocess.run(['git', 'config', '--global', key, value], env=env, check=True)
        process = subprocess.Popen(['bash', str(root / 'evals/run.sh'), *sys.argv[1:]], env=env)
        try:
            return process.wait()
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
