"""Preflight isolation, parity and finite execution without a model call."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'evals'))
import value  # noqa: E402
from value_fixture import request  # noqa: E402


class ValueTests(unittest.TestCase):
    def setUp(self):
        self.manifest = dict(conditions=list(value.CONDITIONS), tasks=['settings', 'shipment'],
                             max_sessions=8, concurrency=2, timeout_seconds=300,
                             model='test-model', effort='medium', image='test-image',
                             revisions={'current': 'a' * 40, 'lean': 'b' * 40})

    def test_four_conditions_keep_identical_product_requests(self):
        jobs = value.matrix(self.manifest)
        self.assertEqual(len(jobs), 8)
        for task in ('settings', 'shipment'):
            self.assertEqual(len({c['prompt_sha256'] for c in jobs if c['task'] == task}), 1)
            self.assertEqual(request(task, 'plain', 'm', 'medium', 10)['project_guide'], '')
            self.assertTrue(request(task, 'project', 'm', 'medium', 10)['project_guide'])

    def test_rejects_mutable_revisions_and_unbounded_work(self):
        for key, val in [('max_sessions', 66), ('concurrency', 3), ('timeout_seconds', 601),
                         ('revisions', {'current': 'main', 'lean': 'HEAD'})]:
            manifest = copy.deepcopy(self.manifest)
            manifest[key] = val
            with self.assertRaises(ValueError):
                value.matrix(manifest)


if __name__ == '__main__':
    unittest.main()
