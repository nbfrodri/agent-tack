"""A runtime archive must contain product code without private grading inputs."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'evals'))
from product_archive import create  # noqa: E402
import lifecycle  # noqa: E402


class RuntimeArchiveTests(unittest.TestCase):
    def test_actual_archive_excludes_evaluators_and_preserves_product(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            home, repo = base / 'home', base / 'repo'
            home.mkdir()
            repo.mkdir()
            env = {**os.environ, 'HOME': str(home), 'USERPROFILE': str(home), 'XDG_CONFIG_HOME': str(home),
                   'GIT_CONFIG_GLOBAL': str(home / '.gitconfig'), 'GIT_CONFIG_NOSYSTEM': '1'}

            def git(*args):
                return subprocess.run(['git', '-C', str(repo), *args], env=env, check=True,
                                      capture_output=True, text=True).stdout.strip()

            git('init', '-q')
            git('config', 'user.name', 'Eval test')
            git('config', 'user.email', 'eval@example.invalid')
            for name in ('bin/tack', 'lib/verification.py', 'skills/testing/SKILL.md',
                         'evals/private-grade.py', 'tests/reference.py', 'docs/benchmarks/secret.json'):
                path = repo / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(name))
            git('add', '.')
            git('commit', '-qm', 'test: seed archive')
            # Archive creation is read-only, and Git configuration stays isolated as well.
            with patch.dict(os.environ, env, clear=True):
                create(repo, git('rev-parse', 'HEAD'), base / 'product.tar')
            with tarfile.open(base / 'product.tar') as archive:
                files = {m.name for m in archive if m.isfile()}
            self.assertEqual(files, {'bin/tack', 'lib/verification.py', 'skills/testing/SKILL.md'})

    def test_provider_failure_preserves_attempt_and_stops_following_work(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            case = dict(id='first', condition='plain', scenario='stock', model='test-model')
            args = SimpleNamespace(output=root, auth=root / 'unused-auth.json')
            manifest = dict(image='unused-image', timeout_seconds=1)
            stopped = threading.Event()

            def runner(command, **kwargs):
                if command[1] == 'inspect':
                    return '[]'
                if command[1] == 'cp' and str(command[2]).endswith(':/home/dev/evidence/.'):
                    stage = root / 'first/setup'
                    stage.mkdir()
                    (stage / 'session.json').write_text(json.dumps(dict(
                        completed=False, seconds=2, exit_code=1,
                        runtime=dict(models=['test-model'], efforts=['medium']))))
                    (stage / 'transcript.jsonl').write_text(json.dumps(dict(
                        type='turn.failed', error=dict(message='Selected model is at capacity.'))))
                return ''

            with patch.object(lifecycle, 'run', side_effect=runner) as commands, \
                    patch.object(lifecycle, 'isolated_grade') as grader:
                result = lifecycle.journey(case, args, manifest, None, stopped)
                self.assertTrue(stopped.is_set())
                self.assertIn('provider interrupted', result['infrastructure_error'])
                self.assertEqual(result['stages']['setup']['seconds'], 2)
                self.assertFalse(result['stages']['setup']['completed'])
                self.assertTrue((root / 'first/setup/transcript.jsonl').is_file())
                grader.assert_not_called()
                calls = commands.call_count
                skipped = lifecycle.journey({**case, 'id': 'second'}, args, manifest, None, stopped)
                self.assertIn('skipped', skipped)
                self.assertEqual(commands.call_count, calls)


if __name__ == '__main__':
    unittest.main()
