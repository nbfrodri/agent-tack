"""Guard experimental comparability before making paid model calls."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'evals'))
import lean  # noqa: E402
import quality_worker as worker  # noqa: E402


class LeanEvaluationTests(unittest.TestCase):
    def test_schedule_covers_matched_triplets_without_selective_omissions(self):
        manifest = dict(models=['gpt-6-luna', 'gpt-6.1-sol'], reviewer='gpt-6-astra', effort='medium',
                        review_timeout=300, seed=20261009, revisions=dict(current='a' * 40, improved='b' * 40),
                        image='sha256:' + 'c' * 64)
        schedule = lean.matrix(manifest)
        self.assertEqual(len(schedule), 24)
        self.assertEqual(len({c['id'] for c in schedule}), 24)
        for model in manifest['models']:
            for task in ('shipment', 'settings'):
                for repetition in (1, 2):
                    block = [c for c in schedule if (c['model'], c['task'], c['repetition']) == (model, task, repetition)]
                    self.assertEqual({c['condition'] for c in block}, set(lean.CONDITIONS))
        manifest['revisions']['improved'] = 'main'
        with self.assertRaises(ValueError):
            lean.matrix(manifest)

    def test_explicit_guide_survives_product_setup_byte_for_byte(self):
        with tempfile.TemporaryDirectory(prefix='tack-lean-eval-') as temp:
            root = Path(temp)
            work, out = root / 'work', root / 'evidence'
            work.mkdir()
            out.mkdir()
            (root / 'product').mkdir()
            home = root / 'home'
            home.mkdir()
            job = dict(kind='code', project_guide=lean.guide('settings'),
                       test_command=['python3', '-m', 'unittest'])
            with patch.object(worker, 'ROOT', root), patch.object(worker, 'WORK', work), patch.object(worker, 'OUT', out), \
                    patch.object(worker, 'checked', return_value={'stdout': 'fixture-head', 'exit_code': 0}) as commands:
                worker.prepare(job, worker.environment(home))
            self.assertEqual((work / 'AGENTS.md').read_text(), job['project_guide'])
            self.assertEqual(json.loads((work / 'tack.json').read_text())['config']['check-fast'], 'python3 -m unittest')
            self.assertTrue(commands.called)


if __name__ == '__main__':
    unittest.main()
