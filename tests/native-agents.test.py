#!/usr/bin/env python3
"""Native role formats and isolated installation ownership regressions."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'lib'))
spec = importlib.util.spec_from_file_location('native_agents', ROOT / 'lib/native_agents.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


def header(text):
    return {key: json.loads(value) for key, value in
            (line.split(': ', 1) for line in text.split('---\n', 2)[1].splitlines())}


class Formats(unittest.TestCase):
    def test_native_role_formats_preserve_contract_and_restrict_tools(self):
        for tool in native.FORMATS:
            with self.subTest(tool=tool):
                text = native.render(tool, ROOT / 'agents/code-reviewer.md')
                fields = header(text)
                self.assertEqual(fields['name'], 'code-reviewer')
                self.assertIn('meticulous senior reviewer', text)
                self.assertNotIn('model', fields)
                if tool == 'cursor':
                    self.assertTrue(fields['readonly'])
                elif tool == 'opencode':
                    self.assertEqual(fields['mode'], 'subagent')
                    self.assertEqual(fields['permission']['*'], 'deny')
                    self.assertEqual(fields['permission']['bash'], 'ask')
                    self.assertNotIn('edit', fields['permission'])
                elif tool == 'gemini':
                    self.assertEqual(fields['kind'], 'local')
                    self.assertIn('read_file', fields['tools'])
                    self.assertNotIn('write_file', fields['tools'])
                else:
                    self.assertIn('read', fields['tools'])
                    self.assertNotIn('edit', fields['tools'])

    def test_editor_roles_keep_editing_tools(self):
        for tool, edit in [('gemini', 'write_file'), ('copilot', 'edit'), ('opencode', 'edit')]:
            fields = header(native.render(tool, ROOT / 'agents/docs-writer.md'))
            self.assertIn(edit, fields['permission' if tool == 'opencode' else 'tools'])
            self.assertNotIn('haiku', json.dumps(fields))

    def test_cursor_editor_does_not_get_readonly(self):
        fields = header(native.render('cursor', ROOT / 'agents/docs-writer.md'))
        self.assertNotIn('readonly', fields)

    def test_unknown_tools_fail_instead_of_silently_broadening_access(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'unknown.md'
            path.write_text('---\nname: unknown\ndescription: A role\ntools: UnknownTool\n---\nDo work.\n', encoding='utf-8')
            for tool in ('gemini', 'copilot', 'opencode'):
                with self.assertRaises(ValueError):
                    native.render(tool, path)


@unittest.skipUnless(os.name == 'posix', 'installer regression requires POSIX')
class Installation(unittest.TestCase):
    def test_install_reinstall_doctor_and_uninstall_preserve_user_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / 'home'
            home.mkdir()
            bins = root / 'bin'
            bins.mkdir()
            for tool in ('gemini', 'copilot', 'opencode', 'crush', 'cursor'):
                stub = bins / tool
                stub.write_text('#!/bin/sh\necho "1.0.0"\n', encoding='utf-8')
                stub.chmod(0o755)
            env = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(home / '.config'),
                       XDG_STATE_HOME=str(home / '.local/state'), GIT_CONFIG_NOSYSTEM='1',
                       GIT_CONFIG_GLOBAL=str(home / '.gitconfig'), PATH=str(bins) + os.pathsep + os.environ['PATH'])
            for key in list(env):
                if key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_CONFIG_COUNT') or key.startswith(('GIT_CONFIG_KEY_', 'GIT_CONFIG_VALUE_')):
                    env.pop(key)
            user_agent = home / '.copilot/agents/planner.agent.md'
            user_agent.parent.mkdir(parents=True)
            user_agent.write_text('My own planner\n', encoding='utf-8')
            gemini_settings = home / '.gemini/settings.json'
            gemini_settings.parent.mkdir(parents=True)
            gemini_settings.write_text(json.dumps({'theme': 'user-choice', 'hooks': {'SessionStart': [
                {'hooks': [{'type': 'command', 'command': 'echo user-hook'}]}]}}), encoding='utf-8')
            def run(script, *args):
                result = subprocess.run(['bash', str(ROOT / script), *args], cwd=root, env=env,
                                        capture_output=True, text=True, timeout=120)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                return result.stdout
            run('bin/tack', 'config', 'agent-roles', 'true', '--global')
            run('install.sh', '--skip-plugins', '--dry-run')
            self.assertFalse((home / '.gemini/agents').exists())
            run('install.sh', '--skip-plugins')
            self.assertEqual(json.loads(gemini_settings.read_text(encoding='utf-8'))['theme'], 'user-choice')
            for settings in (gemini_settings, home / '.copilot/hooks/tack.json'):
                content = settings.read_text(encoding='utf-8')
                self.assertIn('hooks/runtime/adapter.py', content)
                self.assertNotIn('__REPO__', content)
            paths = [home / '.gemini/agents/code-reviewer.md', home / '.copilot/agents/code-reviewer.agent.md',
                     home / '.config/opencode/agents/code-reviewer.md', home / '.cursor/agents/code-reviewer.md']
            for path in paths:
                self.assertTrue(path.is_file(), path)
            for directory in ('.gemini/skills', '.config/opencode/skills', '.config/crush/skills', '.cursor/skills'):
                self.assertTrue((home / directory / 'dev-workflow/SKILL.md').is_file())
            original = paths[0].read_bytes()
            changed = paths[1]
            changed.write_text(changed.read_text(encoding='utf-8') + '\nUser addition.\n', encoding='utf-8')
            run('install.sh', '--skip-plugins')
            self.assertEqual(paths[0].read_bytes(), original)
            self.assertIn('User addition.', changed.read_text(encoding='utf-8'))
            self.assertEqual(user_agent.read_text(encoding='utf-8'), 'My own planner\n')
            run('bin/tack', 'doctor', '--tools')
            run('install.sh', '--skip-plugins', '--no-hooks')
            self.assertNotIn('#tack', gemini_settings.read_text(encoding='utf-8'))
            self.assertIn('echo user-hook', gemini_settings.read_text(encoding='utf-8'))
            copilot_hooks = home / '.copilot/hooks/tack.json'
            self.assertTrue(not copilot_hooks.exists() or '#tack' not in copilot_hooks.read_text(encoding='utf-8'))
            run('bin/tack', 'config', 'agent-roles', 'false', '--global')
            run('install.sh', '--skip-plugins')
            for path in (paths[0], paths[2], paths[3]):
                self.assertFalse(path.exists(), path)
            self.assertIn('User addition.', changed.read_text(encoding='utf-8'))
            self.assertTrue(user_agent.exists())
            run('uninstall.sh')
            self.assertEqual(json.loads(gemini_settings.read_text(encoding='utf-8'))['theme'], 'user-choice')
            for path in (paths[0], paths[2], paths[3]):
                self.assertFalse(path.exists(), path)
            self.assertIn('User addition.', changed.read_text(encoding='utf-8'))
            self.assertTrue(user_agent.exists())

    def test_symlink_agent_directory_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home, outside = root / 'home', root / 'outside'
            (home / '.gemini').mkdir(parents=True)
            outside.mkdir()
            (home / '.gemini/agents').symlink_to(outside, target_is_directory=True)
            self.assertTrue((home / '.gemini/agents').is_symlink())
            # Exercise the install function directly, without other installation steps.
            script = ROOT / 'lib/native-agents.sh'
            shell = ('source "$1"; tool_wanted() { [ "$2" = gemini ]; }; has() { command -v "$1" >/dev/null; }; '
                     'expand_home() { printf "%s" "${1/\\~/$HOME}"; }; warn() { printf "%s\\n" "$1"; }; '
                     'fail() { return 1; }; install_native_agents')
            env = dict(os.environ, HOME=str(home), REPO=str(ROOT), DRY_RUN='0')
            result = subprocess.run(['bash', '-c', shell, 'test', str(script)], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('symlink parents', result.stdout)
            self.assertEqual(list(outside.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
