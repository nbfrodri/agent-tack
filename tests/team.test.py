#!/usr/bin/env python3
"""Branch coordination diagnostics in disposable repositories."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which('bash')


class TeamTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tack-team-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.home = self.root / 'home'
        self.home.mkdir()
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
        self.env.update(HOME=str(self.home), USERPROFILE=str(self.home),
                        XDG_CONFIG_HOME=str(self.home / '.config'),
                        GIT_CONFIG_GLOBAL=str(self.home / '.gitconfig'), GIT_CONFIG_NOSYSTEM='1')
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.invalid')
        self.write('contract.txt', '\n'.join(str(n) for n in range(20)) + '\n')
        self.commit()
        self.git('checkout', '-qb', 'feat/backend')

    def command(self, *args, expected=0):
        result = subprocess.run(args, cwd=self.repo, env=self.env, capture_output=True,
                                text=True, encoding='utf-8', errors='replace', timeout=30)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result.stdout

    def git(self, *args):
        return self.command('git', *args).strip()

    def write(self, name, text):
        (self.repo / name).write_text(text, encoding='utf-8')

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'test: fixture')

    def report(self, *args):
        return json.loads(self.command(BASH, str(ROOT / 'bin/tack'), 'team', '--json', *args))

    def test_clean_branch_and_shared_collaboration_preference(self):
        self.command(BASH, str(ROOT / 'bin/tack'), 'config', 'collaboration', 'team', '--shared')
        self.assertEqual(json.loads((self.repo / 'tack.json').read_text(encoding='utf-8'))['config']['collaboration'], 'team')
        self.write('backend.txt', 'implemented\n')
        self.commit()
        report = self.report()
        self.assertEqual(report['branch'], 'feat/backend')
        comparison = report['comparisons'][0]
        self.assertEqual(comparison['ref'], 'main')
        self.assertEqual((comparison['ahead'], comparison['behind']), (1, 0))
        self.assertEqual(comparison['merge']['status'], 'clean')
        self.assertIn('backend.txt', comparison['head_paths'])

    def test_overlap_without_conflict_is_distinct_from_text_conflict(self):
        content = (self.repo / 'contract.txt').read_text(encoding='utf-8')
        self.write('contract.txt', content.replace('0\n', 'backend\n', 1))
        self.commit()
        self.git('checkout', '-qb', 'feat/frontend', 'main')
        self.write('contract.txt', content.replace('19\n', 'frontend\n'))
        self.commit()
        report = self.report('--against', 'feat/backend')['comparisons'][1]
        self.assertEqual(report['overlap'], ['contract.txt'])
        self.assertEqual(report['merge']['status'], 'clean')
        self.write('contract.txt', content.replace('0\n', 'different\n', 1))
        self.commit()
        report = self.report('--against', 'feat/backend')['comparisons'][1]
        self.assertEqual(report['merge']['status'], 'conflict')
        self.assertIn('contract.txt', report['merge']['conflicts'])

    def test_dirty_worktree_refs_index_and_objects_remain_unchanged(self):
        self.write('contract.txt', 'uncommitted\n')
        self.git('add', 'contract.txt')
        self.write('contract.txt', 'unstaged\n')
        self.write('untracked.txt', 'keep\n')
        before = {str(p.relative_to(self.repo)): p.read_bytes() for p in self.repo.rglob('*') if p.is_file()}
        report = self.report()
        after = {str(p.relative_to(self.repo)): p.read_bytes() for p in self.repo.rglob('*') if p.is_file()}
        self.assertEqual(before, after)
        self.assertTrue(report['dirty'])
        self.assertEqual(report['comparisons'][0]['merge']['status'], 'clean')
        self.assertTrue(any('Uncommitted' in note for note in report['notes']))

    def test_missing_and_option_like_refs_are_unknown_not_clean(self):
        report = self.report('--base', 'absent', '--against=--help')
        self.assertEqual([c['merge']['status'] for c in report['comparisons']], ['unknown', 'unknown'])

    def test_delete_modify_conflict_and_custom_driver_never_runs(self):
        self.write('.gitattributes', '*.txt merge=unsafe\n')
        self.commit()
        self.git('checkout', '-qb', 'feat/other')
        self.write('contract.txt', 'consumer\n')
        self.commit()
        self.git('checkout', 'feat/backend')
        self.git('rm', 'contract.txt')
        self.commit()
        marker = self.root / 'executed'
        self.git('config', 'merge.unsafe.driver', 'touch ' + marker.as_posix())
        self.git('config', '--global', 'merge.unsafe.driver', 'touch ' + marker.as_posix())
        report = self.report('--against', 'feat/other')['comparisons'][1]
        self.assertEqual(report['merge']['status'], 'conflict')
        self.assertFalse(marker.exists())

    def test_probe_failure_is_unknown(self):
        spec = importlib.util.spec_from_file_location('team', ROOT / 'lib/team.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with patch.object(module, 'git', side_effect=OSError('unsupported')):
            self.assertEqual(module.merge_probe(self.repo, 'a' * 40, 'b' * 40)['status'], 'unknown')

    def test_rename_modify_merge_and_unborn_repository(self):
        self.git('mv', 'contract.txt', 'renamed.txt')
        self.commit()
        self.git('checkout', '-qb', 'feat/consumer', 'main')
        self.write('contract.txt', 'consumer\n')
        self.commit()
        self.assertEqual(self.report('--against', 'feat/backend')['comparisons'][1]['merge']['status'], 'clean')
        empty = self.root / 'empty'
        empty.mkdir()
        self.repo = empty
        self.git('init', '-q', '-b', 'main')
        report = self.report()
        self.assertIsNone(report['head'])
        self.assertEqual(report['comparisons'][0]['merge']['status'], 'unknown')

    def test_conflicting_content_does_not_execute_custom_driver(self):
        self.write('.gitattributes', '*.txt merge=unsafe\n')
        self.commit()
        self.git('checkout', '-qb', 'feat/other')
        self.write('contract.txt', 'consumer\n')
        self.commit()
        self.git('checkout', 'feat/backend')
        self.write('contract.txt', 'producer\n')
        self.commit()
        marker = self.root / 'executed'
        driver = 'touch ' + marker.as_posix()
        self.git('config', 'merge.unsafe.driver', driver)
        self.git('config', '--global', 'merge.unsafe.driver', driver)
        self.assertEqual(self.report('--against', 'feat/other')['comparisons'][1]['merge']['status'], 'conflict')
        self.assertFalse(marker.exists())

    def test_context_indexes_parallel_handoffs_and_focuses_current_branch(self):
        self.command(BASH, str(ROOT / 'bin/tack'), 'enable')
        self.command(BASH, str(ROOT / 'bin/tack'), 'mode', 'strict')
        self.command(BASH, str(ROOT / 'bin/tack'), 'config', 'collaboration', 'team', '--shared')
        folder = self.repo / 'docs/handoffs'
        folder.mkdir(parents=True)
        self.write('docs/handoffs/backend.md', 'Status: in progress\nBranch: `feat/backend`\nBackend focus\n')
        for number in range(12):
            self.write(f'docs/handoffs/other-{number}.md', 'Status: paused\nBranch: `feat/other`\nOther body\n' * 80)
        context = self.command(BASH, str(ROOT / 'bin/tack'), 'context')
        self.assertIn('Team coordination:', context)
        self.assertIn('Backend focus', context)
        self.assertIn('other-0.md', context)
        self.assertNotIn('Other body', context)
        self.assertIn('More active handoffs', context)
        self.assertLess(len(context), 6000)
        self.write('docs/handoffs/backend.md', 'Status: in progress\nBranch: `feat/third`\nBackend focus\n')
        context = self.command(BASH, str(ROOT / 'bin/tack'), 'context')
        self.assertNotIn('Backend focus', context)
        self.assertIn('Choose the handoff relevant', context)

    def test_stop_does_not_demand_refresh_of_another_teams_handoff(self):
        self.command(BASH, str(ROOT / 'bin/tack'), 'enable')
        self.command(BASH, str(ROOT / 'bin/tack'), 'config', 'collaboration', 'team', '--shared')
        (self.repo / 'docs/handoffs').mkdir(parents=True)
        self.write('docs/handoffs/analytics.md', 'Status: paused\nBranch: `feat/analytics`\nNext: chart colors.\n')
        self.commit()
        event = json.dumps({'cwd': str(self.repo), 'stop_hook_active': False})

        def stop():
            result = subprocess.run([BASH, str(ROOT / 'hooks/claude/stop-check.sh'), '--codex'],
                                    input=event, cwd=self.repo, env=self.env, capture_output=True,
                                    text=True, encoding='utf-8', errors='replace', timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            return result.stdout

        self.assertEqual(stop().strip(), '')
        self.command(BASH, str(ROOT / 'bin/tack'), 'config', 'collaboration', 'solo')
        self.assertIn('handoff may be stale', stop())


if __name__ == '__main__':
    unittest.main()
