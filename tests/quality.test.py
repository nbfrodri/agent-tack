#!/usr/bin/env python3
"""Offline checks for fair inputs, bounded sessions, blind bundles and evidence-based grades."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'evals'))
import quality  # noqa: E402
import quality_fixture as fixture  # noqa: E402
import quality_grade as grader  # noqa: E402
import quality_review as review  # noqa: E402
import quality_worker as worker  # noqa: E402

REFERENCES = {
    'window': {'src/window.js': '''export function pageWindow(items, offset=0, limit=20) {
  if (!Number.isSafeInteger(offset) || offset<0 || !Number.isSafeInteger(limit) || limit<1 || limit>100) throw new RangeError('range');
  return items.slice(offset, offset+limit);
}
'''},
    'shipment': {'src/validate.js': '''export function validate(event) {
  if (!event || typeof event.id !== 'string' || !event.id.trim()) throw new Error('id');
  if (event.type === 'shipment.created') {
    if (typeof event.address !== 'string' || !event.address.trim()) throw new Error('address');
  } else if (event.type === 'shipment.cancelled') {
    if (typeof event.reason !== 'string' || !event.reason.trim() || !Number.isSafeInteger(event.revision) || event.revision<0) throw new Error('cancellation');
  } else throw new Error('type');
  return {...event};
}
''', 'src/dispatch.js': '''import {validate} from './validate.js';
const topics={'shipment.created':'shipments','shipment.cancelled':'shipment-cancellations'};
export function dispatch(event) {const payload=validate(event);return {topic:topics[payload.type],key:payload.id,payload};}
'''},
    'settings': {'settings.py': '''from copy import deepcopy
DEFAULTS={'endpoint':'http://localhost','retry':{'attempts':3,'delay_ms':100},'tags':[]}
def load_settings(overrides=None, env=None):
    if overrides is None: overrides={}
    if type(overrides) is not dict or set(overrides)-set(DEFAULTS): raise ValueError('keys')
    result=deepcopy(DEFAULTS)
    for key,value in overrides.items():
        if key=='retry':
            if type(value) is not dict or set(value)-set(DEFAULTS['retry']): raise ValueError('retry')
            result[key].update(deepcopy(value))
        else: result[key]=deepcopy(value)
    for key in ('endpoint',):
        if not isinstance(result[key],str) or not result[key]: raise ValueError(key)
    for key,lo,hi in [('attempts',1,10),('delay_ms',0,60000)]:
        value=result['retry'][key]
        if type(value) is not int or not lo<=value<=hi: raise ValueError(key)
    if not isinstance(result['tags'],list) or not all(isinstance(v,str) for v in result['tags']): raise ValueError('tags')
    if env is not None:
        if 'APP_ENDPOINT' in env:
            if not isinstance(env['APP_ENDPOINT'],str) or not env['APP_ENDPOINT']: raise ValueError('endpoint')
            result['endpoint']=env['APP_ENDPOINT']
        if 'APP_ATTEMPTS' in env:
            value=env['APP_ATTEMPTS']
            if not isinstance(value,str) or not value.isdecimal() or not 1<=int(value)<=10: raise ValueError('attempts')
            result['retry']['attempts']=int(value)
    return result
'''},
    'assignments': {'config_cli/options.py': '''import re
def parse_args(argv):
    result={}
    if len(argv)%2: raise ValueError('missing operand')
    for i in range(0,len(argv),2):
        operation,operand=argv[i:i+2]
        if operation=='--set':
            key,sep,value=operand.partition('=')
            if not sep: raise ValueError('missing equals')
        elif operation=='--unset': key=operand
        else: raise ValueError('unknown operation')
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',key): raise ValueError('key')
        if operation=='--set': result[key]=value
        else: result.pop(key,None)
    return result
''', 'config_cli/__main__.py': '''import json,sys
from .options import parse_args
def main():
    try: result=parse_args(sys.argv[1:])
    except ValueError as error:
        print(str(error),file=sys.stderr)
        return 2
    print(json.dumps(result,sort_keys=True))
    return 0
if __name__=='__main__': raise SystemExit(main())
'''},
    'pilot': {'totals.py': '''import math
def total(values):
    if any(type(v) not in (int,float) or not math.isfinite(v) for v in values): raise ValueError('number')
    return sum(values)
'''},
}


class QualityTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='tack-quality-test-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.manifest = json.loads((ROOT / 'evals/batches/quality-efficiency.json').read_text(encoding='utf-8'))

    def test_matrix_is_finite_balanced_and_reproducible(self):
        coding = quality.matrix(self.manifest, 'coding')
        self.assertEqual(len(coding), 48)
        self.assertEqual(coding, quality.matrix(self.manifest, 'coding'))
        self.assertEqual(len(quality.matrix(self.manifest, 'setup')), 8)
        self.assertEqual(len(quality.matrix(self.manifest, 'pilot')), 3)
        for condition in quality.CONDITIONS:
            self.assertEqual(sum(c['condition'] == condition for c in coding), 16)
        for key, value in [('max_sessions', 94), ('concurrency', 3), ('review_timeout', 301), ('implementation_timeout', 601)]:
            bad = {**self.manifest, key: value}
            with self.assertRaises(ValueError):
                quality.matrix(bad, 'coding')

    def test_public_inputs_have_no_process_instructions_or_hidden_checks(self):
        for task in fixture.TASKS:
            files = fixture.seed(task, self.root / task)
            text = '\n'.join(files.values()) + fixture.TASKS[task]['prompt']
            for forbidden in ('TDD', 'SOLID', 'Conventional Commits', 'write tests', 'add tests', 'modularity', 'hidden acceptance'):
                self.assertNotIn(forbidden, text)
            self.assertNotIn('AGENTS.md', files)
            self.assertEqual(fixture.seed(task, self.root / (task + '-again')), files)

    def test_hidden_checks_reject_seeds_and_accept_reference_behavior(self):
        for task in fixture.TASKS:
            with self.subTest(task=task):
                root = self.root / task
                fixture.seed(task, root)
                env = worker.environment(self.root / ('home-' + task))
                self.assertFalse(grader.acceptance(root, task, env)['passed'])
                for name, content in REFERENCES[task].items():
                    (root / name).write_text(content, encoding='utf-8')
                report = grader.acceptance(root, task, env)
                self.assertTrue(report['passed'], report)

    def test_seed_probe_does_not_reward_shallow_existing_tests(self):
        root = self.root / 'pilot'
        fixture.seed('pilot', root)
        (root / 'totals.py').write_text(REFERENCES['pilot']['totals.py'], encoding='utf-8')
        self.assertFalse(grader.grade(root, 'pilot')['seed_regression_probe']['rejected_original_defect'])
        (root / 'tests/test_regression.py').write_text('import unittest\nfrom totals import total\nclass Regression(unittest.TestCase):\n    def test_empty(self): self.assertEqual(total([]),0)\n', encoding='utf-8')
        self.assertTrue(grader.grade(root, 'pilot')['seed_regression_probe']['rejected_original_defect'])

    def bundles(self):
        source = self.root / 'source'
        for condition in quality.CONDITIONS:
            directory = source / ('private-' + condition)
            fixture.seed('pilot', directory / 'repo')
            (directory / 'repo/AGENTS.md').write_text('PRIVATE_GUIDANCE', encoding='utf-8')
            (directory / 'repo/helper.py').write_text('helper = 1\n', encoding='utf-8')
            quality.save(directory / 'case.json', {'id': directory.name, 'task': 'pilot', 'model': 'private-model',
                                                   'condition': condition, 'repetition': 1})
        destination = self.root / 'reviews'
        destination.mkdir()
        return destination, review.prepare(source, destination, 123)

    def test_review_bundles_hide_identity_include_new_helpers_and_change_order(self):
        directory, jobs = self.bundles()
        mapping = json.loads((directory / 'private-label-map.json').read_text(encoding='utf-8'))
        self.assertEqual(list(mapping[jobs[0]['id']].values()), list(reversed(list(mapping[jobs[1]['id']].values()))))
        for job in jobs:
            raw = (Path(job['bundle']) / 'bundle.json').read_text(encoding='utf-8')
            for marker in ('PRIVATE_GUIDANCE', 'private-model', 'private-current', 'tests/test_totals.py', 'AGENTS.md'):
                self.assertNotIn(marker, raw)
            self.assertIn('helper.py', raw)

    def sample_grade(self):
        directory, jobs = self.bundles()
        bundle = json.loads((Path(jobs[0]['bundle']) / 'bundle.json').read_text(encoding='utf-8'))
        grade = {'candidates': [], 'preferred': list(bundle['candidates']), 'uncertainty': 'Small task', 'origin_hints': 'None'}
        for label in bundle['candidates']:
            grade['candidates'].append({'id': label, 'dimensions': {name: {'score': 7, 'path': 'totals.py', 'line': 1, 'reason': 'Concrete evidence'} for name in review.WEIGHTS}, 'findings': []})
        return bundle, grade

    def test_grades_need_all_dimensions_real_citations_and_valid_numbers(self):
        bundle, grade = self.sample_grade()
        self.assertEqual(set(review.validate(grade, bundle).values()), {7})
        for field, value in [('score', True), ('score', 11), ('score', float('nan')), ('path', '../private-map.json'), ('line', 900), ('reason', '')]:
            bad = copy.deepcopy(grade)
            bad['candidates'][0]['dimensions']['robustness'][field] = value
            with self.assertRaises(ValueError):
                review.validate(bad, bundle)
        grade['candidates'][0]['dimensions'].pop('simplicity')
        with self.assertRaises(ValueError):
            review.validate(grade, bundle)

    def test_missing_runtime_observations_are_not_fabricated(self):
        self.assertEqual(worker.observe(self.root)['models'], [])
        env = worker.environment(self.root)
        self.assertEqual(env['GIT_CONFIG_NOSYSTEM'], '1')
        self.assertEqual(env['HOME'], str(self.root))
        self.assertNotIn('OPENAI_API_KEY', env)
        self.assertNotIn('GIT_CONFIG_COUNT', env)

    def test_unexpected_mounts_abort_before_auth_and_always_remove_container(self):
        calls = []
        def launch(args, timeout=120):
            calls.append(args)
            return '[{"Source":"unexpected"}]' if args[:2] == ['docker', 'inspect'] else ''
        with self.assertRaisesRegex(RuntimeError, 'isolation failure'):
            quality.session('image', {}, self.root / 'output', self.root / 'auth', launch=launch)
        self.assertFalse(any(args[:2] == ['docker', 'cp'] for args in calls))
        self.assertEqual(calls[-1][:3], ['docker', 'rm', '-f'])

    def test_uncommitted_and_deleted_files_are_captured_without_repair(self):
        repo, out, home = self.root / 'repo', self.root / 'out', self.root / 'home'
        out.mkdir()
        home.mkdir()
        fixture.seed('pilot', repo)
        env = worker.environment(home)
        job = {'kind': 'code', 'test_command': [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests']}
        with patch.multiple(worker, ROOT=self.root, WORK=repo, OUT=out):
            worker.prepare(job, env)
            (repo / 'totals.py').write_text(REFERENCES['pilot']['totals.py'], encoding='utf-8')
            (repo / 'new.py').write_text('value = 1\n', encoding='utf-8')
            (repo / 'README.md').unlink()
            worker.capture(job, env)
        self.assertTrue((out / 'repo/new.py').exists())
        self.assertFalse((out / 'repo/README.md').exists())
        facts = json.loads((out / 'git.json').read_text(encoding='utf-8'))
        self.assertIn('?? new.py', facts['status']['stdout'])
        self.assertEqual(facts['history']['stdout'], '')

    @unittest.skipUnless(hasattr(os, 'killpg'), 'The session worker runs in Linux containers')
    def test_worker_timeout_stops_a_real_process_and_keeps_evidence(self):
        out = self.root / 'out'
        out.mkdir()
        with patch.multiple(worker, WORK=self.root, OUT=out):
            result = worker.invoke([sys.executable, '-c', 'import time; print("started", flush=True); time.sleep(30)'], worker.environment(self.root), .2)
        self.assertEqual(result['exit_code'], 124)
        self.assertLess(result['seconds'], 5)
        self.assertIn('started', (out / 'transcript.jsonl').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
