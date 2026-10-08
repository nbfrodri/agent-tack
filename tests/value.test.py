"""Preflight isolation, parity and finite execution without a model call."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'evals'))
import value  # noqa: E402
from value_fixture import request  # noqa: E402
import quality_worker  # noqa: E402
import adoption  # noqa: E402


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

    def test_capture_keeps_private_notes_out_of_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            work, out = root / 'work', root / 'out'
            (work / '.private/tack').mkdir(parents=True)
            out.mkdir()
            (work / '.private/tack/note.md').write_text('personal context', encoding='utf-8')
            (work / 'app.py').write_text('value = 1\n', encoding='utf-8')
            (out / 'base.json').write_text(json.dumps({'head': 'base'}), encoding='utf-8')
            with patch.object(quality_worker, 'WORK', work), patch.object(quality_worker, 'OUT', out), \
                    patch.object(quality_worker, 'call', return_value={'exit_code': 0}):
                quality_worker.capture({'test_command': ['true']}, {})
            self.assertTrue((out / 'repo/app.py').is_file())
            self.assertFalse((out / 'repo/.private').exists())
            adoption_out = root / 'adoption-out'
            adoption_out.mkdir()
            with patch.object(adoption, 'command', return_value={'stdout': '', 'exit_code': 0}):
                adoption.snapshot(work, adoption_out, {}, 'base')
            self.assertTrue((adoption_out / 'repo/app.py').is_file())
            self.assertFalse((adoption_out / 'repo/.private').exists())


if __name__ == '__main__':
    unittest.main()
