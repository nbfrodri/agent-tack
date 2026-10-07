#!/usr/bin/env python3
"""Offline regression tests for reproducible, bounded experiments."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import shutil
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'evals' / (name + '.py'))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


class Comparison(unittest.TestCase):
    def test_R1_compiled_hidden_checks_do_not_change_comparison_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'test_hidden.py').write_text('def test_one(): pass', encoding='utf-8')
            metadata = module('metadata')
            before = metadata.hidden_fingerprint(root)
            (root / '__pycache__').mkdir()
            (root / '__pycache__/test_hidden.pyc').write_bytes(b'compiled-cache')
            self.assertEqual(before, metadata.hidden_fingerprint(root))
            (root / 'test_hidden.py').write_text('def test_two(): pass', encoding='utf-8')
            self.assertNotEqual(before, metadata.hidden_fingerprint(root))

    def report(self, runs):
        with tempfile.TemporaryDirectory() as temp:
            for i, updates in enumerate(runs):
                directory = Path(temp) / 'bug-fix' / ('auto-' + str(i))
                directory.mkdir(parents=True)
                data = dict(scenario='bug-fix', condition='auto', metrics_version=3, provider='fixture',
                            hidden_pass=True, completed=True, cost_usd=1, duration_s=5,
                            metadata=dict(resolved_model='small', requested_model='small', cli_version='1',
                                          harness_revision='abc', source_sha256='source', configuration_sha256='config',
                                          prompt_sha256='prompt', fixture_sha256='fixture', hidden_sha256='hidden',
                                          permission_mode='workspace', effort=None))
                data['metadata'].update(updates.pop('metadata', {}))
                data.update(updates)
                (directory / 'metrics.json').write_text(json.dumps(data), encoding='utf-8')
            return subprocess.run([sys.executable, str(ROOT / 'evals/report.py'), temp],
                                  capture_output=True, text=True, check=True).stdout

    def test_R1_different_models_and_prompts_do_not_pool(self):
        output = self.report([{}, {'metadata': {'resolved_model': 'large'}},
                              {'metadata': {'prompt_sha256': 'different'}}])
        self.assertEqual(output.count('### bug-fix'), 3)

    def test_R1_revisions_get_separate_columns(self):
        output = self.report([{}, {'metadata': {'harness_revision': 'def', 'source_sha256': 'other'}}])
        self.assertIn('abc', output)
        self.assertIn('def', output)
        self.assertNotIn('| 2/2 |', output)

    def test_R1_time_limits_do_not_pool(self):
        output = self.report([{}, {'metadata': {'timeout_seconds': '60'}},
                              {'metadata': {'timeout_seconds': '120'}}])
        self.assertEqual(output.count('### bug-fix'), 3)

    def test_R1_unknown_source_or_configuration_does_not_pool(self):
        for key in ('harness_revision', 'source_sha256', 'configuration_sha256'):
            for value in (None, 'unknown'):
                with self.subTest(key=key, value=value):
                    output = self.report([{'metadata': {key: value}}, {'metadata': {key: value}}])
                    self.assertEqual(output.count('### bug-fix'), 2)

    def test_R2_failed_costs_and_unknown_outcomes_stay_visible(self):
        output = self.report([{}, {'hidden_pass': False, 'cost_usd': 3, 'completed': False},
                              {'hidden_pass': None, 'cost_usd': None}])
        self.assertIn('1/2', output)
        self.assertIn('unknown', output.lower())
        self.assertIn('95%', output)
        self.assertIn('incomplete', output.lower())


class Batches(unittest.TestCase):
    def setUp(self):
        self.batch = module('batch')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = dict(batch_id='fixture', seed=11, repetitions=2,
                             scenarios=['bug-fix', 'search'], conditions=['baseline', 'auto'],
                             runtimes=[dict(provider='claude', model='fixture-model')],
                             limits=dict(max_runs=8, timeout_seconds=20, concurrency=1))

    def test_R1_deterministic_order_and_unique_ids(self):
        runs = self.batch.expand(self.manifest)
        self.assertEqual(runs, self.batch.expand(self.manifest))
        self.assertEqual(len(runs), 8)
        self.assertEqual(len({r['run_id'] for r in runs}), 8)

    def test_R2_invalid_manifests_are_rejected_before_execution(self):
        for change in ({'batch_id': '../escape'}, {'repetitions': 0},
                       {'conditions': ['anything']}, {'scenarios': ['unknown']},
                       {'runtimes': [{'provider': 'claude'}]},
                       {'limits': {'max_runs': 1, 'timeout_seconds': 20, 'concurrency': 1}}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.batch.expand(dict(self.manifest, **change))

    def test_R2_dry_run_does_not_create_output(self):
        manifest = self.root / 'batch.json'
        manifest.write_text(json.dumps(self.manifest), encoding='utf-8')
        output = self.root / 'results'
        result = subprocess.run([sys.executable, str(ROOT / 'evals/batch.py'), str(manifest),
                                 '--output', str(output), '--dry-run'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('8 runs', result.stdout)
        self.assertFalse(output.exists())

    def test_R1_resume_checks_manifest_and_completed_identity(self):
        path = self.root / 'batch'
        self.batch.prepare(path, self.manifest, 'source-a')
        self.batch.prepare(path, self.manifest, 'source-a')
        with self.assertRaises(ValueError):
            self.batch.prepare(path, dict(self.manifest, seed=12), 'source-a')
        with self.assertRaises(ValueError):
            self.batch.prepare(path, self.manifest, 'source-b')

    @unittest.skipUnless(os.name == 'posix', 'process-group timeout test requires POSIX')
    def test_R2_timeout_retains_evidence_and_cleans_process(self):
        fake = self.root / 'fake'
        (fake / 'evals').mkdir(parents=True)
        (fake / 'evals/run.sh').write_text('echo partial-evidence\nsleep 30\n', encoding='utf-8')
        result_root = self.root / 'results'
        result_root.mkdir()
        run = self.batch.expand(self.manifest)[0]
        manifest = dict(self.manifest, limits=dict(self.manifest['limits'], timeout_seconds=1))
        class Grader:
            def grade(self, directory):
                (directory / 'metrics.json').write_text('{"cost_usd":null}', encoding='utf-8')
                return {'cost_usd': None}
        with patch.object(self.batch, 'ROOT', fake), patch.object(self.batch, 'load', return_value=Grader()):
            result = self.batch.execute(run, result_root, manifest)
            self.assertEqual(result['exit_code'], 124)
            self.assertIn('partial-evidence', (result_root / run['run_id'] / 'runner.log').read_text())
            self.assertEqual(self.batch.execute(run, result_root, manifest), result)


class CapabilityEvidence(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'JavaScript acceptance requires Node')
    def test_R2_javascript_hidden_checks_detect_contract_defects(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            module('scenarios').seed('event-routing', root)
            check = [sys.executable, str(ROOT / 'evals/hidden/run.py'), str(ROOT / 'evals/hidden/event-routing/test_hidden.py')]
            red = subprocess.run(check, cwd=root, capture_output=True, text=True)
            self.assertNotEqual(red.returncode, 0)
            (root / 'src/routes.js').write_text("import {validate} from './events.js';\nexport function handle(event) {const e=validate(event);"
                "const invoice=e.type==='invoice.paid';if(invoice && (!Number.isSafeInteger(e.amountCents)||e.amountCents<0))throw Error('amount');"
                "if(!invoice && e.type!=='order.created')throw Error('unknown');return {topic:invoice?'invoices':'orders',key:e.id,payload:e};}", encoding='utf-8')
            (root / 'docs/catalog.md').write_text('invoice.paid', encoding='utf-8')
            green = subprocess.run(check, cwd=root, capture_output=True, text=True)
            self.assertEqual(green.returncode, 0, green.stdout + green.stderr)
            self.assertIn('6 passed, 0 failed', green.stdout)

    def test_R6_only_completed_reads_count(self):
        capabilities = module('capabilities')
        path = '.agents/skills/events/SKILL.md'
        read = {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': 'Read',
                'id': 'read1', 'input': {'file_path': path}}]}}
        self.assertEqual(capabilities.observed_reads([read]), set())
        failed = {'type': 'user', 'message': {'content': [{'type': 'tool_result', 'tool_use_id': 'read1', 'is_error': True}]}}
        self.assertEqual(capabilities.observed_reads([read, failed]), set())
        failed['message']['content'][0]['is_error'] = False
        self.assertEqual(capabilities.observed_reads([read, failed]), {path})
        echo = {'type': 'item.completed', 'item': {'type': 'command_execution', 'command': 'echo ' + path, 'exit_code': 0}}
        self.assertEqual(capabilities.observed_reads([echo]), set())

    def test_R2_creation_and_reuse_cost_are_both_counted(self):
        grade = module('grade')
        data = grade.provider_metrics([{'type': 'result', 'total_cost_usd': 0.4},
                                       {'type': 'result', 'total_cost_usd': 0.2}], Path('.'))
        self.assertAlmostEqual(data['cost_usd'], 0.6)
        data = grade.provider_metrics([{'type': 'result', 'total_cost_usd': 0.4}, {'type': 'result'}], Path('.'))
        self.assertIsNone(data['cost_usd'])

    def test_R6_extended_scenarios_seed_reproducibly(self):
        scenarios = module('scenarios')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in scenarios.NAMES:
                with self.subTest(name=name):
                    first, second = root / (name + '-1'), root / (name + '-2')
                    prompts = scenarios.seed(name, first)
                    self.assertEqual(prompts, scenarios.seed(name, second))
                    files = {p.relative_to(first).as_posix(): p.read_bytes() for p in first.rglob('*') if p.is_file()}
                    self.assertEqual(files, {p.relative_to(second).as_posix(): p.read_bytes() for p in second.rglob('*') if p.is_file()})
                    self.assertNotIn('test_hidden.py', str(files))
                    self.assertEqual(len(prompts), 1 if name in ('event-routing', 'capability-trivial', 'capability-review') else 2)


if __name__ == '__main__':
    # Even accidental Git calls in fixtures must not see the user's identity or hooks.
    with tempfile.TemporaryDirectory(prefix='tack-evidence-tests-') as isolated:
        os.environ.update(HOME=isolated, XDG_CONFIG_HOME=isolated, XDG_STATE_HOME=isolated,
                          GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=str(Path(isolated) / 'gitconfig'))
        unittest.main()
