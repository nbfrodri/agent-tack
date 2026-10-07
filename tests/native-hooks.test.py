#!/usr/bin/env python3
"""Protocol translations plus real shared guard/startup checks without model calls."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('adapter', ROOT / 'hooks/runtime/adapter.py')
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


class Protocol(unittest.TestCase):
    def test_copilot_accepts_object_and_json_string_arguments(self):
        for args in ({'command': 'git status'}, '{"command":"git status"}'):
            payload = adapter.normalize('copilot', {'toolName': 'bash', 'toolArgs': args, 'sessionId': 'abc'})
            self.assertEqual(payload['tool_input']['command'], 'git status')
            self.assertEqual(payload['session_id'], 'abc')

    def test_ask_is_native_for_copilot_and_blocked_for_gemini(self):
        with patch.object(adapter, 'invoke', return_value={'hookSpecificOutput': {'permissionDecision': 'ask', 'permissionDecisionReason': 'Confirm deletion'}}):
            self.assertEqual(adapter.dispatch('copilot', 'before', {'toolName': 'bash', 'toolArgs': {'command': 'rm x'}})['permissionDecision'], 'ask')
            self.assertEqual(adapter.dispatch('gemini', 'before', {'tool_name': 'run_shell_command', 'tool_input': {'command': 'rm x'}})['decision'], 'deny')

    def test_stop_and_context_have_target_protocols(self):
        for tool in ('gemini', 'copilot'):
            with patch.object(adapter, 'invoke', return_value={'decision': 'block', 'reason': 'Fix tests'}):
                self.assertEqual(adapter.dispatch(tool, 'stop', {})['decision'], 'deny' if tool == 'gemini' else 'block')
            with patch.object(adapter, 'invoke', return_value={'hookSpecificOutput': {'additionalContext': 'Project guidance'}}):
                result = adapter.dispatch(tool, 'session', {})
                self.assertIn('Project guidance', json.dumps(result))
                self.assertIn('hookSpecificOutput' if tool == 'gemini' else 'additionalContext', result)

    def test_unrelated_after_tools_do_not_run_checks(self):
        with patch.object(adapter, 'invoke') as invoke:
            self.assertEqual(adapter.dispatch('gemini', 'after', {'tool_name': 'read_file'}), {})
            invoke.assert_not_called()

    def test_non_shell_opaque_arguments_still_reach_the_budget(self):
        with patch.object(adapter, 'invoke', return_value={}) as invoke:
            for args in (None, 'opaque', [1, 2]):
                self.assertEqual(adapter.dispatch('copilot', 'before', {'toolName': 'custom_reader', 'toolArgs': args}), {})
            self.assertEqual(invoke.call_count, 3)
            self.assertTrue(all(call.args[0] == 'budget.sh' for call in invoke.call_args_list))
        with self.assertRaises(ValueError):
            adapter.normalize('copilot', {'toolName': 'bash', 'toolArgs': None})

    def test_powershell_is_not_mistaken_for_bash(self):
        payload = adapter.normalize('copilot', {'toolName': 'powershell', 'toolArgs': {'command': 'Remove-Item x'}})
        self.assertTrue(payload['tool_input']['command'].startswith('pwsh -Command '))

    @unittest.skipUnless(os.name == 'posix', 'process group lifecycle is POSIX')
    def test_timeout_stops_descendants_without_waiting_for_their_output_pipes(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            (path / 'slow.sh').write_text('sleep 10 &\nwait\n', encoding='utf-8')
            start = time.monotonic()
            with patch.object(adapter, 'HOOKS', path), self.assertRaises(subprocess.TimeoutExpired):
                adapter.invoke('slow.sh', {}, 'gemini', 0.1)
            self.assertLess(time.monotonic() - start, 3)


class SharedHooks(unittest.TestCase):
    def test_real_guard_context_stop_loop_and_malformed_input(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / 'home'
            home.mkdir()
            project = root / 'project'
            project.mkdir()
            env = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(home / '.config'),
                       XDG_STATE_HOME=str(home / '.local/state'), GIT_CONFIG_GLOBAL=str(home / '.gitconfig'),
                       GIT_CONFIG_NOSYSTEM='1')
            for key in list(env):
                if key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_CONFIG_COUNT') or key.startswith(('GIT_CONFIG_KEY_', 'GIT_CONFIG_VALUE_')):
                    env.pop(key)
            subprocess.run(['git', 'init', '-q', str(project)], env=env, check=True)
            subprocess.run(['bash', str(ROOT / 'bin/tack'), 'enable'], cwd=project, env=env, check=True, capture_output=True)
            def run(tool, event, payload):
                result = subprocess.run([sys.executable, str(ROOT / 'hooks/runtime/adapter.py'), tool, event],
                                        input=json.dumps(payload), env=env, cwd=project, capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout)
            for tool in ('gemini', 'copilot'):
                def shell(command):
                    return dict(cwd=str(project), **({'toolName': 'bash', 'toolArgs': {'command': command}} if tool == 'copilot' else {'tool_name': 'run_shell_command', 'tool_input': {'command': command}}))
                self.assertEqual(run(tool, 'before', shell('git status')), {})
                result = run(tool, 'before', shell('rm -rf /'))
                self.assertEqual(result.get('decision', result.get('permissionDecision')), 'deny')
                result = run(tool, 'before', [])
                self.assertEqual(result.get('decision', result.get('permissionDecision')), 'deny')
                self.assertIn('Project setup review pending', json.dumps(run(tool, 'session', {'cwd': str(project)})))
                self.assertEqual(run(tool, 'stop', {'cwd': str(project), 'stop_hook_active': True}), {})


if __name__ == '__main__':
    unittest.main()
