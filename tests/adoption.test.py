#!/usr/bin/env python3
"""Offline acceptance for adoption isolation, handoff and defect-sensitive grading."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'evals'))
import adoption as runner  # noqa: E402
import adoption_fixture as fixture  # noqa: E402
import adoption_grade as grader  # noqa: E402


def reference(root):
    fixture.seed(root)
    (root / 'src/events.js').write_text('''export function validate(event) {
  if (!event || typeof event.id !== 'string' || !event.id.trim()) throw new Error('invalid id');
  if (event.type === 'order.created' && (!Number.isSafeInteger(event.quantity) || event.quantity <= 0)) throw new Error('quantity');
  if (event.type === 'invoice.paid' && (!Number.isSafeInteger(event.amountCents) || event.amountCents < 0)) throw new Error('amount');
  return {...event};
}
''', encoding='utf-8')
    path = root / 'src/routes.js'
    path.write_text(path.read_text(encoding='utf-8').replace("'orders'}", "'orders', 'invoice.paid': 'invoices'}"), encoding='utf-8')


class AdoptionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='tack-adoption-test-')
        self.addCleanup(temporary.cleanup)
        context = runner.participant(Path(temporary.name) / 'home', None)
        isolated = context.__enter__()
        self.addCleanup(context.__exit__, None, None, None)
        environment = patch.dict(os.environ, isolated, clear=True)
        environment.start()
        self.addCleanup(environment.stop)

    def test_npm_cache_stays_in_the_temporary_home(self):
        result = runner.command(['npm', 'config', 'get', 'cache'], os.environ)
        cache = Path(result['stdout'].strip()).resolve()
        self.assertTrue(cache.is_relative_to(Path(os.environ['HOME']).resolve()))

    def test_budget_bounds_and_fixed_order(self):
        manifest = json.loads((ROOT / 'evals/batches/project-adoption.json').read_text(encoding='utf-8'))
        self.assertEqual(len(runner.matrix(manifest)), 8)
        self.assertEqual(runner.matrix(manifest), runner.matrix(manifest))
        manifest['max_sessions'] = 23
        with self.assertRaises(ValueError):
            runner.matrix(manifest)

    def test_clean_participant_and_committed_only_handoff(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.dict(os.environ, {'GIT_CONFIG_COUNT': '1', 'GIT_CONFIG_KEY_0': 'bad',
                                         'GIT_CONFIG_VALUE_0': 'bad', 'OPENAI_API_KEY': 'not-a-real-key'}):
                with runner.participant(root / 'person', None) as env:
                    self.assertNotIn('OPENAI_API_KEY', env)
                    self.assertNotIn('GIT_CONFIG_COUNT', env)
                    self.assertEqual(env['GIT_CONFIG_NOSYSTEM'], '1')
                    first = root / 'first'
                    runner.command(['git', 'init', '-q', '-b', 'main', first], env)
                    fixture.write(first, 'AGENTS.md', 'Shared conventions\n')
                    runner.command(['git', '-C', first, 'add', '.'], env)
                    runner.command(['git', '-C', first, 'commit', '-qm', 'docs: configure project'], env)
                    fixture.write(first, 'not-committed.txt', 'Must not transfer\n')
                    runner.command(['git', '-C', first, 'config', 'tack.trusted', 'true'], env)
                    second = root / 'second'
                    runner.command(['git', 'clone', '-q', first, second], env)
                    self.assertTrue((second / 'AGENTS.md').exists())
                    self.assertFalse((second / 'not-committed.txt').exists())
                    self.assertNotEqual(runner.command(['git', '-C', second, 'config', '--local', '--get', 'tack.trusted'], env, check=False)['exit_code'], 0)
            self.assertFalse((root / 'person').exists())

    def test_grader_detects_original_defect_and_accepts_reference(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture.seed(root)
            self.assertFalse(grader.acceptance(root, 'bug')['passed'])
            self.assertFalse(grader.acceptance(root, 'feature')['passed'])
            reference(root)
            self.assertTrue(grader.acceptance(root, 'bug')['passed'])
            self.assertTrue(grader.acceptance(root, 'feature')['passed'])

    def test_mutation_probe_does_not_reward_original_shallow_tests(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            reference(root)
            outcomes = grader.mutations(root, 'feature')
            self.assertFalse(outcomes['validation']['detected'])
            self.assertFalse(outcomes['routing']['detected'])
            fixture.write(root, 'tests/regressions.test.js', '''import {test} from 'node:test';
import assert from 'node:assert/strict';
import {handle} from '../src/routes.js';
test('rejects zero', () => assert.throws(() => handle({type:'order.created', id:'o', quantity:0})));
test('invoice topic', () => assert.equal(handle({type:'invoice.paid', id:'i', amountCents:0}).topic, 'invoices'));
''')
            outcomes = grader.mutations(root, 'feature')
            self.assertTrue(outcomes['validation']['detected'])
            self.assertTrue(outcomes['routing']['detected'])

    def test_transcript_usage_is_observed_and_completion_is_explicit(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'events.jsonl'
            path.write_text('not json\n' + json.dumps({'type': 'turn.failed'}) + '\n', encoding='utf-8')
            self.assertEqual(runner.transcript_metrics(path)['completed_turns'], 0)
            path.write_text(json.dumps({'type': 'turn.completed', 'usage': {'input_tokens': 25, 'cached_input_tokens': 10, 'output_tokens': 2}}), encoding='utf-8')
            result = runner.transcript_metrics(path)
            self.assertEqual(result['completed_turns'], 1)
            self.assertEqual(result['usage']['input_tokens'], 25)

    @unittest.skipUnless(os.name == 'posix', 'process-group deadline uses POSIX')
    def test_timeout_is_retained_as_incomplete(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            launcher = root / 'slow.py'
            launcher.write_text('import time\ntime.sleep(10)\n', encoding='utf-8')
            out = root / 'stage'
            out.mkdir()
            args = SimpleNamespace(launcher=launcher, codex='unused', timeout=0.1)
            result = runner.invoke(root, 'bug', out, os.environ.copy(), args, 'fixture')
            self.assertEqual(result['exit_code'], 124)
            self.assertFalse(result['completed'])
            self.assertLess(result['seconds'], 3)

    def test_fixture_contains_no_hidden_grader(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            files = fixture.seed(root)
            self.assertEqual(len(list(root.rglob('*.py'))), 0)
            self.assertNotIn('checks-map.json', files)
            result = subprocess.run(['npm', 'test'], cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_adoption_accepts_standard_uppercase_pr_template(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            root = directory / 'setup/repo'
            fixture.seed(root)
            fixture.write(root, '.github/PULL_REQUEST_TEMPLATE.md', '# Summary\n\n# Validation\n')
            (directory / 'setup/status.txt').write_text('', encoding='utf-8')
            self.assertTrue(grader.adoption(directory)['pr_template'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
