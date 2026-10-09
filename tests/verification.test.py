#!/usr/bin/env python3
"""Behavioral verification tests with isolated Git, HOME and project commands."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
BASH = shutil.which('bash')


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tack-verify-')
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.root = self.directory / 'project'
        self.root.mkdir()
        home = self.directory / 'home'
        home.mkdir()
        self.env = {**os.environ, 'HOME': str(home), 'USERPROFILE': str(home),
                    'XDG_CONFIG_HOME': str(home / '.config'), 'XDG_STATE_HOME': str(home / '.state'),
                    'GIT_CONFIG_GLOBAL': str(home / '.gitconfig'), 'GIT_CONFIG_NOSYSTEM': '1'}
        for key in list(self.env):
            if key.startswith(('GIT_CONFIG_KEY_', 'GIT_CONFIG_VALUE_')) or key in (
                    'GIT_CONFIG_COUNT', 'GIT_DIR', 'GIT_WORK_TREE', 'BASH_ENV', 'ENV'):
                self.env.pop(key)
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.invalid')
        self.write('.gitignore', '.results\n__pycache__/\n')
        self.write('src/api.py', 'value = 1\n')
        self.write('web/app.js', 'const value = 1;\n')
        self.write('README.md', '# Example\n')
        self.commit()
        self.git('switch', '-q', '-c', 'feat/example')

    def command(self, *args):
        return subprocess.run(args, cwd=self.root, env=self.env, capture_output=True,
                              text=True, encoding='utf-8', errors='replace', timeout=30)

    def git(self, *args):
        result = self.command('git', *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')

    def commit(self):
        self.git('add', '-A')
        self.git('commit', '-qm', 'test: fixture')

    def define(self, entries):
        self.write('checks-map.json', json.dumps({'version': 1, 'checks': entries}))
        self.commit()
        # Treat the declared checks as the shared base, not as part of the task.
        self.git('branch', '-f', 'main', 'HEAD')

    def check(self, name='api', patterns=None, command='true', **extra):
        return dict(id=name, paths=patterns or ['src/*'], command=command, **extra)

    def verify(self, *args, expected=0):
        result = self.command(BASH, str(REPO / 'bin/tack'), 'verify', '--json', *args)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def trust(self):
        self.git('config', 'tack.trusted', 'true')

    def test_repository_map_keeps_prose_checks_focused_and_gaps_visible(self):
        self.define(json.loads((REPO / 'checks-map.json').read_text(encoding='utf-8'))['checks'])
        self.write('docs/setup.md', '# Updated setup\n')
        self.write('diagram.drawio', 'Diagram requiring manual review\n')
        report = self.verify('--plan')
        self.assertEqual([check['id'] for check in report['checks']], ['content'])
        self.assertEqual(report['unmapped_paths'], ['diagram.drawio'])

    def test_repository_map_runs_regressions_for_runtime_assets(self):
        self.define(json.loads((REPO / 'checks-map.json').read_text(encoding='utf-8'))['checks'])
        for path in ('lib/project_setup.py', 'skills/new-project/assets/setup-tack.py',
                     'skills/project-docs/assets/setup-private.py', 'skills/github-issues/assets/check-pr.py',
                     'bin/tack', 'hooks/claude/session-context.sh'):
            with self.subTest(path=path):
                self.write(path, '# Runtime change\n')
                report = self.verify('--plan')
                self.assertIn('regressions', {check['id'] for check in report['checks']})
                self.assertEqual(report['unmapped_paths'], [])
                (self.root / path).unlink()

    def test_shared_contract_selects_both_areas_but_web_change_stays_focused(self):
        self.define([self.check('api', ['apps/api/*', 'packages/contracts/*'], 'npm run test:api'),
                     self.check('web', ['apps/web/*', 'packages/contracts/*'], 'npm run test:web')])
        self.write('apps/web/page.js', 'const page = 1;\n')
        report = self.verify('--plan')
        self.assertEqual([check['id'] for check in report['checks']], ['web'])
        self.write('packages/contracts/order.json', '{}\n')
        report = self.verify('--plan')
        self.assertEqual({check['id'] for check in report['checks']}, {'api', 'web'})

    def test_read_only_selection_and_committed_branch_changes(self):
        self.define([self.check(command='touch .results'), self.check('web', ['web/*'])])
        self.write('src/api.py', 'value = 2\n')
        self.commit()
        report = self.verify('--plan')
        self.assertEqual([c['id'] for c in report['checks']], ['api'])
        self.assertEqual(report['changed_paths'], ['src/api.py'])
        self.assertFalse((self.root / '.results').exists())

    def test_all_checks_exposes_a_broken_clean_checkout_without_granting_trust(self):
        self.define([self.check(command="python3 -c \"exec(open('src/api.py').read()); assert value == 2\""),
                     self.check('web', ['web/*'], 'node --check web/app.js')])
        self.assertEqual(self.verify()['status'], 'no_changes')
        planned = self.verify('--all', '--plan')
        self.assertEqual({c['id'] for c in planned['checks']}, {'api', 'web'})
        self.assertEqual(self.verify('--all', expected=2)['status'], 'untrusted')
        self.trust()
        self.assertEqual(self.verify('--all', expected=1)['status'], 'failed')
        self.write('src/api.py', 'value = 2\n')
        self.commit()
        self.git('branch', '-f', 'main', 'HEAD')
        report = self.verify('--all')
        self.assertEqual(report['status'], 'passed')
        self.assertEqual(report['changed_paths'], [])

    def test_all_without_any_check_is_unverified_even_on_clean_checkout(self):
        self.define([])
        self.trust()
        self.assertEqual(self.verify('--all', expected=3)['status'], 'unverified')

    def test_untrusted_never_executes_even_with_environment_override(self):
        self.define([self.check(command='touch .results')])
        self.write('src/api.py', 'value = 2\n')
        self.env['TACK_VERIFY_TRUSTED'] = '1'
        self.assertEqual(self.verify(expected=2)['status'], 'untrusted')
        self.assertFalse((self.root / '.results').exists())

    def test_project_invariant_detects_real_defect_and_then_passes(self):
        self.define([self.check(command="python3 -c \"exec(open('src/api.py').read()); assert value == 2, 'API invariant failed'\"")])
        self.trust()
        self.write('src/api.py', 'value = 3\n')
        failed = self.verify(expected=1)
        self.assertIn('API invariant failed', failed['checks'][0]['output_tail'])
        self.write('src/api.py', 'value = 2\n')
        self.assertEqual(self.verify()['status'], 'passed')

    def test_pipeline_failure_is_preserved(self):
        self.define([self.check(command='false | cat')])
        self.trust()
        self.write('src/api.py', 'value = 2\n')
        self.assertEqual(self.verify(expected=1)['checks'][0]['exit_code'], 1)

    def test_duplicate_commands_run_once(self):
        self.define([self.check(command='echo run >> .results'),
                     self.check('also-api', ['src/*.py'], 'echo run >> .results')])
        self.trust()
        self.write('src/api.py', 'value = 2\n')
        report = self.verify()
        self.assertEqual(report['checks'][0]['ids'], ['api', 'also-api'])
        self.assertEqual((self.root / '.results').read_text(encoding='utf-8').splitlines(), ['run'])

    def test_untracked_deleted_and_renamed_paths_with_spaces(self):
        self.define([self.check(patterns=['src/*', 'web/*'])])
        self.git('mv', 'src/api.py', 'src/api renamed.py')
        (self.root / 'web/app.js').unlink()
        self.write('src/new file.py', 'value = 2\n')
        report = self.verify('--plan')
        self.assertEqual(set(report['changed_paths']), {'src/api.py', 'src/api renamed.py', 'src/new file.py', 'web/app.js'})

    def test_unmapped_is_incomplete_not_success(self):
        self.define([self.check()])
        self.trust()
        self.write('src/api.py', 'value = 2\n')
        self.write('README.md', '# Changed\n')
        report = self.verify(expected=3)
        self.assertEqual(report['status'], 'incomplete')
        self.assertEqual(report['unmapped_paths'], ['README.md'])

    def test_staged_change_is_selected_when_worktree_matches_base(self):
        self.define([self.check()])
        self.write('src/api.py', 'value = 2\n')
        self.git('add', 'src/api.py')
        self.write('src/api.py', 'value = 1\n')
        report = self.verify('--plan')
        self.assertEqual(report['changed_paths'], ['src/api.py'])
        self.assertEqual(report['checks'][0]['id'], 'api')

    def test_check_that_changes_only_index_invalidates_success(self):
        self.define([self.check(command='git reset -q HEAD -- src/api.py')])
        self.trust()
        self.write('src/api.py', 'value = 2\n')
        self.git('add', 'src/api.py')
        report = self.verify(expected=3)
        self.assertTrue(report['inputs_changed'])
        self.assertEqual(report['status'], 'incomplete')

    def test_no_checks_is_unverified_not_success(self):
        self.write('README.md', '# Changed\n')
        self.assertEqual(self.verify(expected=3)['status'], 'unverified')

    def test_no_changes_is_distinct_from_checks_passed(self):
        self.define([self.check()])
        self.assertEqual(self.verify()['status'], 'no_changes')

    def test_configuration_change_selects_all_checks(self):
        self.define([self.check(), self.check('web', ['web/*'], 'echo web')])
        self.write('checks-map.json', json.dumps({'version': 1, 'checks': [self.check(), self.check('web', ['web/*'], 'echo web')]}, indent=2))
        self.assertEqual(len(self.verify('--plan')['checks']), 2)

    def test_invalid_configuration_fails_without_running(self):
        self.define([self.check(command='touch .results')])
        self.trust()
        for data in ('{broken', '{"version":1,"checks":"wrong"}',
                     json.dumps({'version': 1, 'checks': [self.check(timeout_seconds=True)]}),
                     json.dumps({'version': 1, 'checks': [self.check(), self.check()]})):
            self.write('checks-map.json', data)
            self.assertEqual(self.verify('--plan', expected=2)['status'], 'error')
        self.assertFalse((self.root / '.results').exists())

    def test_symlink_map_is_rejected(self):
        target = self.directory / 'outside.json'
        target.write_text('{"version":1,"checks":[]}', encoding='utf-8')
        try:
            (self.root / 'checks-map.json').symlink_to(target)
        except OSError:
            self.skipTest('Creating symlinks requires local permission')
        self.assertIn('symlink', self.verify('--plan', expected=2)['error'])

    def test_timeout_is_a_failed_check(self):
        self.define([self.check(command='sleep 10', timeout_seconds=1)])
        self.trust()
        self.write('src/api.py', 'value = 2\n')
        self.assertEqual(self.verify(expected=1)['checks'][0]['status'], 'timed_out')

    def test_check_that_edits_inputs_invalidates_success(self):
        self.define([self.check(command="printf 'value = 4\n' > src/api.py")])
        self.trust()
        self.write('src/api.py', 'value = 2\n')
        report = self.verify(expected=3)
        self.assertTrue(report['inputs_changed'])
        self.assertEqual(report['status'], 'incomplete')

    def test_existing_explicit_command_is_reused_without_map(self):
        self.git('config', 'tack.checkFast', 'echo checked > .results')
        self.trust()
        self.write('README.md', '# Changed\n')
        report = self.verify()
        self.assertEqual(report['checks'][0]['source'], 'tack config check-fast')
        self.assertTrue((self.root / '.results').exists())

    def test_existing_make_target_is_discovered_without_running_it(self):
        self.write('Makefile', 'test:\n\ttouch .results\n')
        report = self.verify('--plan')
        self.assertEqual(report['checks'][0]['command'], 'make test')
        self.assertFalse((self.root / '.results').exists())

    def test_global_trust_does_not_authorize_project_commands(self):
        self.define([self.check(command='touch .results')])
        self.git('config', '--global', 'tack.trusted', 'true')
        self.write('src/api.py', 'value = 2\n')
        self.assertEqual(self.verify(expected=2)['status'], 'untrusted')
        self.assertFalse((self.root / '.results').exists())

    def test_total_budget_skips_remaining_checks(self):
        self.define([self.check(command='sleep 10'), self.check('second', command='touch .results')])
        self.trust()
        self.write('src/api.py', 'value = 2\n')
        report = self.verify('--budget-seconds', '1', expected=1)
        self.assertEqual(report['checks'][1]['status'], 'budget_exhausted')
        self.assertFalse((self.root / '.results').exists())

    def test_recursive_pattern_matches_top_level_and_nested_files(self):
        self.define([self.check(patterns=['src/**/*.py'])])
        self.write('src/api.py', 'value = 2\n')
        self.write('src/nested/extra.py', 'value = 2\n')
        report = self.verify('--plan')
        self.assertEqual(report['checks'][0]['matched_paths'], ['src/api.py', 'src/nested/extra.py'])

    def test_explicit_base_restricts_committed_changes(self):
        self.define([self.check()])
        self.write('src/api.py', 'value = 2\n')
        self.commit()
        self.assertEqual(self.verify('--plan', '--base', 'HEAD')['changed_paths'], [])
        self.assertEqual(self.verify('--plan', '--base', 'missing-ref', expected=2)['status'], 'error')

    def test_stop_hook_reports_mapped_defect_and_respects_trust(self):
        self.define([self.check(command='echo defect-found; touch .results; false')])
        self.git('config', 'tack.enabled', 'true')
        self.write('src/api.py', 'value = 2\n')
        hook = REPO / 'hooks/claude/stop-check.sh'
        def stop():
            return subprocess.run([BASH, str(hook)], input=json.dumps({'cwd': str(self.root)}),
                                  cwd=self.root, env=self.env, text=True, capture_output=True, timeout=30)
        self.assertIn('untrusted', stop().stdout)
        self.assertFalse((self.root / '.results').exists())
        self.trust()
        self.assertIn('Verification: failed', stop().stdout)
        self.assertTrue((self.root / '.results').exists())
        self.write('checks-map.json', '{invalid')
        self.assertIn('Verification: error', stop().stdout)


if __name__ == '__main__':
    unittest.main()
