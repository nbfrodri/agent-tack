#!/usr/bin/env python3
"""Offline evaluation runner and transcript regression tests."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('grade', ROOT / 'evals/grade.py')
grade = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(grade)


def use(name, **inputs):
    return {'type': 'assistant', 'message': {'content': [
        {'type': 'tool_use', 'id': inputs.pop('id', name), 'name': name, 'input': inputs}]}}


def result(identifier, text, failed=False):
    return {'type': 'user', 'message': {'content': [
        {'type': 'tool_result', 'tool_use_id': identifier, 'content': text, 'is_error': failed}]}}


class Metrics(unittest.TestCase):
    def measure(self, events, scenario='bug-fix', run='exit=0 seconds=7', complete_writes=True):
        if complete_writes:
            result_ids = {block.get('tool_use_id') for event in events
                          for block in event.get('message', {}).get('content', []) if block.get('type') == 'tool_result'}
            completed = []
            for event in events:
                completed.append(event)
                for block in event.get('message', {}).get('content', []):
                    if block.get('name') in ('Write', 'Edit', 'MultiEdit') and block.get('id') not in result_ids:
                        completed.append(result(block.get('id'), 'File updated successfully'))
            events = completed
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp) / scenario / 'baseline-1'
            (directory / 'repo').mkdir(parents=True)
            (directory / 'transcript.jsonl').write_text('\n'.join(json.dumps(e) for e in events))
            (directory / 'run.txt').write_text(run)
            with patch.object(grade, 'git', return_value=''), patch.object(
                grade.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '1 passed', '')):
                return grade.grade(directory)

    def test_one_line_implementation_edit_precedes_test(self):
        m = self.measure([use('Edit', file_path='src/cart.py', new_string='return 0'),
                          use('Write', file_path='tests/test_cart.py', content='def test_empty():\n    assert total([]) == 0')])
        self.assertIs(m['test_written_before_code'], False)

    def test_missing_evidence_is_unknown(self):
        m = self.measure([])
        for key in ('test_written_before_code', 'red_green_verified', 'cost_usd', 'input_tokens', 'planned', 'pushed_or_bypassed'):
            self.assertIsNone(m[key], key)
        self.assertEqual(m['duration_s'], 7)

    def test_test_write_without_test_execution_is_not_red_green(self):
        m = self.measure([use('Write', file_path='tests/test_cart.py', content='assert total([]) == 0'),
                          use('Edit', file_path='src/cart.py', new_string='return 0')])
        self.assertTrue(m['test_written_before_code'])
        self.assertIsNone(m['red_green_verified'])

    def test_claude_red_green_and_usage(self):
        m = self.measure([use('Write', file_path='tests/test_cart.py', content='assert total([]) == 0'),
            use('Bash', id='red', command='uv run pytest'), result('red', '1 failed', True),
            use('Edit', file_path='src/cart.py', new_string='return 0'),
            use('Bash', id='green', command='uv run pytest'), result('green', '1 passed'),
            {'type': 'result', 'duration_ms': 2500, 'total_cost_usd': .012,
             'usage': {'input_tokens': 2, 'cache_read_input_tokens': 3, 'output_tokens': 4}}])
        self.assertTrue(m['red_green_verified'])
        self.assertEqual(m['provider'], 'claude')
        self.assertEqual(m['input_tokens'], 5)
        self.assertEqual(m['duration_s'], 2.5)

    def test_codex_adapter(self):
        def event(item):
            return {'type': 'item.completed', 'item': item}
        m = self.measure([{'type': 'thread.started', 'thread_id': 'fixture'},
            event({'type': 'file_change', 'changes': [{'path': 'tests/test_cart.py', 'kind': 'add'}]}),
            event({'type': 'command_execution', 'command': 'uv run pytest', 'exit_code': 1, 'aggregated_output': '1 failed'}),
            event({'type': 'file_change', 'changes': [{'path': 'src/cart.py', 'kind': 'update'}]}),
            event({'type': 'command_execution', 'command': 'uv run pytest', 'exit_code': 0, 'aggregated_output': '1 passed'}),
            {'type': 'turn.completed', 'usage': {'input_tokens': 12, 'cached_input_tokens': 4, 'output_tokens': 8}}], 'codex-new-project')
        self.assertTrue(m['test_written_before_code'])
        self.assertTrue(m['red_green_verified'])
        self.assertEqual(m['provider'], 'codex')
        self.assertEqual(m['input_tokens'], 12)
        self.assertEqual(m['output_tokens'], 8)
        self.assertIsNone(m['cost_usd'])

    def test_codex_atomic_patch_has_no_file_order(self):
        m = self.measure([{'type': 'item.completed', 'item': {'type': 'file_change', 'changes': [
            {'path': 'tests/test_cart.py', 'kind': 'add'}, {'path': 'src/cart.py', 'kind': 'update'}]}}])
        self.assertIsNone(m['test_written_before_code'])
        self.assertIsNone(m['red_green_verified'])

    def test_failed_test_write_cannot_prove_test_first(self):
        m = self.measure([use('Write', id='test-failed', file_path='tests/test_cart.py', content='assert total([]) == 0'),
                          result('test-failed', 'Permission denied; file not written', True),
                          use('Edit', id='implementation', file_path='src/cart.py', new_string='return 0'),
                          result('implementation', 'File updated'),
                          use('Write', id='test-real', file_path='tests/test_cart.py', content='assert total([]) == 0'),
                          result('test-real', 'File written')])
        self.assertIsNone(m['test_written_before_code'])
        self.assertIsNone(m['red_green_verified'])

    def test_write_without_result_keeps_order_unknown(self):
        m = self.measure([use('Write', file_path='tests/test_cart.py', content='assert total([]) == 0'),
                          use('Edit', file_path='src/cart.py', new_string='return 0')], complete_writes=False)
        self.assertIsNone(m['test_written_before_code'])
        self.assertIsNone(m['red_green_verified'])

    def test_empty_scaffold_write_does_not_precede_test(self):
        m = self.measure([use('Write', file_path='src/__init__.py', content=''),
                          use('Write', file_path='tests/test_cart.py', content='assert total([]) == 0'),
                          use('Edit', file_path='src/cart.py', new_string='return 0')])
        self.assertTrue(m['test_written_before_code'])

    def test_malformed_transcript_makes_order_unknown(self):
        with tempfile.TemporaryDirectory() as temp:
            transcript = Path(temp) / 'transcript.jsonl'
            transcript.write_text('broken JSON\n' + json.dumps(use('Edit', file_path='src/cart.py', new_string='return 0')))
            entries = grade.observations(grade.events(transcript))
            self.assertIn({'opaque': True}, entries)

    def test_shell_writes_make_order_unknown(self):
        m = self.measure([use('Bash', command="printf 'return 0' > src/cart.py"),
                          use('Write', file_path='tests/test_cart.py', content='assert total([]) == 0')])
        self.assertIsNone(m['test_written_before_code'])


class Runner(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'home/.codex').mkdir(parents=True)
        (self.root / 'home/.codex/auth.json').write_text('{"fixture": "fake-auth"}')
        (self.root / 'bin').mkdir()
        self.env = dict(os.environ, HOME=str(self.root / 'home'), XDG_CONFIG_HOME=str(self.root / 'home/.config'),
                        CODEX_HOME=str(self.root / 'home/.codex'), GIT_CONFIG_NOSYSTEM='1',
                        GIT_CONFIG_GLOBAL=str(self.root / 'gitconfig'), EVALS_OUT=str(self.root / 'out'),
                        PATH=str(self.root / 'bin') + ':' + os.environ['PATH'])
        subprocess.run(['git', 'config', '--file', self.env['GIT_CONFIG_GLOBAL'], 'user.name', 'Eval'], env=self.env, check=True)
        subprocess.run(['git', 'config', '--file', self.env['GIT_CONFIG_GLOBAL'], 'user.email', 'eval@example.com'], env=self.env, check=True)

    def stub(self, name, body):
        path = self.root / 'bin' / name
        path.write_text('#!/usr/bin/env bash\n' + body + '\n')
        path.chmod(0o755)

    def run_eval(self, scenario):
        return subprocess.run(['bash', str(ROOT / 'evals/run.sh'), scenario, 'baseline'], env=self.env, capture_output=True, text=True)

    def test_cli_failure_retains_transcript_and_status(self):
        self.stub('claude', 'echo partial; echo diagnostic >&2; exit 42')
        outcome = self.run_eval('bug-fix')
        self.assertEqual(outcome.returncode, 42)
        run = self.root / 'out/bug-fix/baseline-1'
        self.assertIn('exit=42', (run / 'run.txt').read_text())
        self.assertIn('partial', (run / 'transcript.jsonl').read_text())
        self.assertIn('diagnostic', (run / 'stderr.log').read_text())

    def test_explicit_model_and_reproducibility_metadata(self):
        self.env['EVALS_MODEL'] = 'fixture-model'
        self.stub('claude', 'if [ "$1" = --version ]; then echo fixture-cli; exit; fi\n'
                  'printf "%s\\n" "$@" > "' + str(self.root / 'args') + '"\n'
                  "echo '{\"type\":\"system\",\"subtype\":\"init\",\"model\":\"fixture-resolved\"}'")
        outcome = self.run_eval('bug-fix')
        self.assertEqual(outcome.returncode, 0, outcome.stderr)
        metadata = json.loads((self.root / 'out/bug-fix/baseline-1/metadata.json').read_text())
        import hashlib
        prompt = (self.root / 'out/bug-fix/baseline-1/prompt.txt').read_bytes()
        self.assertEqual(metadata['prompt_sha256'], hashlib.sha256(prompt).hexdigest())
        self.assertEqual(metadata['requested_model'], 'fixture-model')
        self.assertEqual(metadata['resolved_model'], 'fixture-resolved')
        self.assertEqual(metadata['cli_version'], 'fixture-cli')
        self.assertEqual(metadata['metrics_version'], 2)
        self.assertEqual(metadata['permission_mode'], 'acceptEdits')
        self.assertIn('Bash(uv *)', metadata['allowed_tools'])
        self.assertIn('Agent', metadata['allowed_tools'])
        self.assertEqual(metadata['condition'], 'baseline')
        self.assertEqual(metadata['provider'], 'claude')
        self.assertEqual(len(metadata['harness_revision']), 40)
        self.assertIn('--model\nfixture-model', (self.root / 'args').read_text())

    def test_setup_failure_does_not_invoke_cli(self):
        self.stub('git', 'if [ "$1" = init ]; then echo setup-failed >&2; exit 23; fi\nexec /usr/bin/git "$@"')
        self.stub('claude', 'echo wrongly-invoked')
        outcome = self.run_eval('bug-fix')
        self.assertEqual(outcome.returncode, 23)
        run = self.root / 'out/bug-fix/baseline-1'
        self.assertFalse((run / 'transcript.jsonl').exists())
        self.assertIn('exit=23', (run / 'run.txt').read_text())

    def test_successful_claude_scenarios_have_baseline_flags(self):
        self.stub('claude', 'printf "%s\\n" "$@"; exit 0')
        for scenario in ('new-project', 'bug-fix', 'release'):
            with self.subTest(scenario=scenario):
                outcome = self.run_eval(scenario)
                self.assertEqual(outcome.returncode, 0, outcome.stderr)
                transcript = self.root / 'out' / scenario / 'baseline-1/transcript.jsonl'
                self.assertIn('--setting-sources', transcript.read_text())
                self.assertIn('--disable-slash-commands', transcript.read_text())

    def test_codex_baseline_isolates_config_and_retains_auth(self):
        self.stub('codex', 'test "$HOME" != "' + str(self.root / 'home') + '" || exit 61\n'
                  'test -f "$CODEX_HOME/auth.json" || exit 62\n'
                  'test ! -f "$CODEX_HOME/config.toml" || exit 63\n'
                  "python3 - <<'CHECK'\nimport os, stat\nassert stat.S_IMODE(os.stat(os.environ['CODEX_HOME'] + '/auth.json').st_mode) == 0o600\nCHECK\n"
                  'echo "$CODEX_HOME" > "' + str(self.root / 'isolated-home') + '"\necho fixture')
        (self.root / 'home/.codex/config.toml').write_text('fixture = true')
        outcome = self.run_eval('codex-new-project')
        self.assertEqual(outcome.returncode, 0, outcome.stderr)
        self.assertFalse(Path((self.root / 'isolated-home').read_text().strip()).exists())
        self.assertTrue((self.root / 'home/.codex/auth.json').exists())
        self.assertFalse(list((self.root / 'out').rglob('auth.json')))


class Report(unittest.TestCase):
    def test_unknowns_and_incompatible_versions_are_not_combined(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for rep, version, provider, value in ((1, 2, 'claude', None), (2, 2, 'codex', True), (3, None, None, False)):
                directory = root / 'new-project' / ('baseline-' + str(rep))
                directory.mkdir(parents=True)
                metrics = {'scenario': 'new-project', 'condition': 'baseline', 'test_written_before_code': value}
                if version is not None:
                    metrics.update(metrics_version=version, provider=provider)
                (directory / 'metrics.json').write_text(json.dumps(metrics))
            output = subprocess.run(['python3', str(ROOT / 'evals/report.py'), str(root)], capture_output=True, text=True, check=True).stdout
            self.assertEqual(output.count('### new-project'), 3)
            self.assertIn('Provider: codex', output)
            self.assertIn('metrics version: legacy', output)
            self.assertIn('| Test written before code | 1/1 |', output)
            self.assertNotIn('1/3', output)


if __name__ == '__main__':
    unittest.main()
