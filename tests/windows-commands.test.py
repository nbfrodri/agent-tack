#!/usr/bin/env python3
"""Native Windows launchers and hook commands keep Git Bash, arguments and exit codes."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('render_settings', ROOT / 'lib/render_settings.py')
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


class WindowsCommandsTests(unittest.TestCase):
    def test_posix_hooks_keep_the_existing_command(self):
        template = {'hooks': {'Stop': [{'hooks': [{'command': "bash '__REPO__/stop.sh' #tack"}]}]}}
        result = renderer.render(template, '/repo with spaces', '/bin/bash', windows=False)
        self.assertEqual(result['hooks']['Stop'][0]['hooks'][0]['command'],
                         "bash '/repo with spaces/stop.sh' #tack")

    def test_windows_wraps_only_managed_commands_and_preserves_metadata(self):
        template = {'hooks': {'Stop': [{'hooks': [
            {'command': "python3 '__REPO__/adapter.py' copilot stop #tack", 'timeout': 90},
            {'command': 'echo user-hook'}]}]}}
        result = renderer.render(template, 'C:/repo with spaces', 'C:/Git/bin/bash.exe', windows=True)
        hooks = result['hooks']['Stop'][0]['hooks']
        self.assertTrue(hooks[0]['command'].startswith('C:/Git/bin/bash.exe '))
        self.assertIn('--noprofile --norc -c', hooks[0]['command'])
        self.assertIn('#tack', hooks[0]['command'])
        self.assertEqual(hooks[0]['timeout'], 90)
        self.assertEqual(hooks[1]['command'], 'echo user-hook')

    @unittest.skipUnless(os.name == 'nt', 'native Windows execution')
    def test_native_hook_command_preserves_stdin_paths_spaces_and_exit_status(self):
        bash = os.environ.get('TACK_TEST_BASH') or shutil.which('bash')
        with tempfile.TemporaryDirectory(prefix='tack hook ') as work:
            root = Path(work)
            script = root / 'hook.sh'
            script.write_text('cat; exit 7\n', encoding='utf-8')
            template = {'command': "bash '__REPO__/hook.sh' #tack"}
            command = renderer.render(template, root.as_posix(), bash, windows=True)['command']
            result = subprocess.run(command, shell=True, input='{"payload":"kept"}', capture_output=True, text=True)
            self.assertEqual(result.returncode, 7, result.stderr)
            self.assertEqual(json.loads(result.stdout), {'payload': 'kept'})

    @unittest.skipUnless(os.name == 'nt' and os.environ.get('TACK_TEST_INSTALLED_HOME'),
                         'runs after installation in the smoke fixture')
    def test_installed_command_and_registered_hooks_run_from_native_windows(self):
        home = Path(os.environ['TACK_TEST_INSTALLED_HOME'])
        env = dict(os.environ)
        # Reproduce native PATH order: the WSL launcher precedes Git Bash.
        env['PATH'] = str(home / '.local/bin') + os.pathsep + str(Path(env['SYSTEMROOT']) / 'System32') + os.pathsep + env['PATH']
        result = subprocess.run(['powershell.exe', '-NoProfile', '-Command',
                                 'tack --help; exit $LASTEXITCODE'], env=env,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Usage: tack', result.stdout)
        result = subprocess.run([str(home / '.local/bin/tack.cmd'), 'mode'], env=env,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('auto', result.stdout)
        for name in ('.claude/settings.json', '.codex/hooks.json'):
            settings = json.loads((home / name).read_text(encoding='utf-8'))
            command = settings['hooks']['PreToolUse'][0]['hooks'][0]['command']
            payload = json.dumps({'cwd': str(home), 'tool_name': 'Bash',
                                  'tool_input': {'command': 'git push --force origin main'}})
            result = subprocess.run(command, shell=True, env=env, input=payload,
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, '')
            self.assertEqual(json.loads(result.stdout)['hookSpecificOutput']['permissionDecision'], 'deny', result.stdout)
            for event in ('SessionStart', 'PostToolUse', 'Stop'):
                command = settings['hooks'][event][0]['hooks'][0]['command']
                payload = json.dumps({'cwd': str(home), 'stop_hook_active': True})
                result = subprocess.run(command, shell=True, env=env, input=payload,
                                        capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, f'{name} {event}: {result.stderr}')
                self.assertEqual(result.stderr, '')

    @unittest.skipUnless(os.name == 'nt', 'native Windows execution')
    def test_cmd_launcher_runs_from_powershell_and_preserves_arguments_and_exit_status(self):
        bash = os.environ.get('TACK_TEST_BASH') or shutil.which('bash')
        with tempfile.TemporaryDirectory(prefix='tack launcher ') as work:
            root = Path(work)
            (root / 'bin').mkdir()
            (root / 'bin/tack').write_text('printf "%s\\n" "$@"; exit 7\n', encoding='utf-8')
            launcher = root / 'tack.cmd'
            launcher.write_text(renderer.launcher(root.as_posix(), bash), encoding='utf-8')
            result = subprocess.run(['powershell.exe', '-NoProfile', '-Command',
                                     f"& '{launcher}' 'two words' 'another'; exit $LASTEXITCODE"],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 7, result.stderr)
            self.assertEqual(result.stdout.splitlines(), ['two words', 'another'])


if __name__ == '__main__':
    unittest.main()
