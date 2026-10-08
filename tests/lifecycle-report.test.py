"""Reporting must not turn interruptions or transported commits into measured benefits."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'evals'))
from lifecycle_report import authored_history, stage_metrics  # noqa: E402


class EvidenceReporting(unittest.TestCase):
    def stage(self, root, name, commits, events):
        directory = root / name
        directory.mkdir()
        (directory / 'git.json').write_text(json.dumps(dict(
            branch='delivery/change', commits=commits, status='', unresolved='')))
        (directory / 'transcript.jsonl').write_text('\n'.join(json.dumps(e) for e in events))
        return directory

    def test_interrupted_turn_tokens_are_unknown_not_zero_cost(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = self.stage(Path(temporary), 'change', [], [
                dict(type='turn.failed', error=dict(message='Selected model is at capacity.'))])
            saved = dict(completed=False, seconds=100, usage=dict(
                input_tokens=0, cached_input_tokens=0, output_tokens=0))
            result = stage_metrics(directory, saved)
            self.assertFalse(result['token_usage_complete'])
            self.assertEqual(result['seconds'], 100)
            self.assertEqual(len(result['errors']), 1)

    def test_integrated_and_controller_commits_are_not_new_actor_work(self):
        original = dict(hash='a', subject='feat: quote', body='feat: quote')
        transport = dict(hash='b', subject='chore: transport evaluation snapshot', body='controller')
        current = dict(hash='c', subject='feat: shipping', body='feat: shipping')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.stage(root, 'build', [original], [])
            self.stage(root, 'change', [original, transport, current], [])
            stages = dict(build=dict(workflow={}), change=dict(workflow={}))
            authored_history(root, stages)
            self.assertEqual(stages['build']['workflow']['new_authored_commits'], 1)
            self.assertEqual(stages['change']['workflow']['new_authored_commits'], 1)
            self.assertEqual(stages['change']['workflow']['controller_commits_excluded'], 1)
            self.assertTrue(stages['change']['workflow']['new_conventional'])


if __name__ == '__main__':
    unittest.main()
