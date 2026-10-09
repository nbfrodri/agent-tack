#!/usr/bin/env python3
"""Project discovery, preservation and onboarding state in isolated repositories."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which('bash')
sys.path.insert(0, str(ROOT / 'lib'))
spec = importlib.util.spec_from_file_location('project_setup', ROOT / 'lib/project_setup.py')
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class ProjectSetup(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / 'home'
        self.home.mkdir()
        self.project = Path(self.temp.name) / 'repo'
        self.project.mkdir()
        self.env = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home), XDG_CONFIG_HOME=str(self.home / '.config'),
                        XDG_STATE_HOME=str(self.home / '.local/state'), GIT_CONFIG_NOSYSTEM='1',
                        GIT_CONFIG_GLOBAL=str(self.home / '.gitconfig'))
        for key in list(self.env):
            if key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_CONFIG_COUNT', 'BASH_ENV', 'ENV') or key.startswith(('GIT_CONFIG_KEY_', 'GIT_CONFIG_VALUE_')):
                self.env.pop(key)
        self.run_command('git', 'init', '-q')

    def run_command(self, *args, status=0):
        result = subprocess.run(args, cwd=self.project, env=self.env, text=True, encoding='utf-8', capture_output=True, timeout=30)
        self.assertEqual(result.returncode, status, result.stdout + result.stderr)
        return result.stdout

    def tack(self, *args, status=0):
        return self.run_command(BASH, str(ROOT / 'bin/tack'), *args, status=status)

    def write(self, relative, text):
        path = self.project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def symlink(self, path, target, directory=False):
        try:
            path.symlink_to(target, target_is_directory=directory)
        except OSError as error:
            if getattr(error, 'winerror', None) == 1314:
                self.skipTest('Windows symlink privilege is unavailable')
            raise

    def test_minimal_adoption_does_not_require_optional_templates(self):
        self.write('AGENTS.md', '# Project\nUse existing tests.\n')
        self.tack('enable')
        before = self.run_command('git', 'status', '--porcelain')
        report = json.loads(self.tack('setup', '--check', '--json'))
        self.assertEqual(report['issues'], [])
        self.assertEqual(set(report['missing_optional']), {'CLAUDE.md', 'docs/architecture.md', 'docs-map.txt'})
        self.assertEqual(self.run_command('git', 'status', '--porcelain'), before)
        self.assertFalse((self.project / 'docs').exists())
        self.assertIn('not test results', self.tack('setup', '--check'))

    def test_explicit_architecture_is_checked_but_unused_default_is_optional(self):
        self.tack('setup', '--check')
        self.tack('config', 'architecture-path', 'guide/system.md', '--shared')
        self.assertIn('guide/system.md', self.tack('setup', '--check', status=1))
        self.write('guide/system.md', '# System\n')
        self.tack('setup', '--check')
        self.write('CLAUDE.md', '@AGENTS.md\n')
        self.assertIn('AGENTS.md', self.tack('setup', '--check', status=1))
        self.write('AGENTS.md', '# Instructions\n')
        self.tack('setup', '--check')

    def test_clone_summary_reuses_preferences_and_exposes_local_differences(self):
        self.write('AGENTS.md', '# Instructions\n\n## Setup choices\nUse existing tests; no scaffold.\n')
        self.tack('enable', '--shared')
        self.tack('mode', 'auto', '--shared')
        self.tack('config', 'collaboration', 'team', '--shared')
        self.tack('config', 'reply-style', 'brief', '--shared')
        self.tack('config', 'setup-review', 'done')
        self.tack('trust')
        self.run_command('git', 'add', '.')
        self.run_command('git', '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'test: setup')
        clone = Path(self.temp.name) / 'clone'
        self.run_command('git', 'clone', '-q', str(self.project), str(clone))
        self.project = clone
        self.tack('config', 'collaboration', 'solo', '--global')
        self.tack('config', 'reply-style', 'visual')
        self.tack('mode', 'strict')
        before = (clone / '.git/config').read_bytes()
        report = json.loads(self.tack('setup', '--check', '--json'))
        self.assertTrue(report['workflow']['enabled'])
        self.assertFalse(report['workflow']['trusted'])
        self.assertEqual(report['workflow']['mode'], {'value': 'strict', 'source': 'local', 'shared_value': 'auto'})
        values = {item['name']: item for item in report['preferences']}
        self.assertEqual((values['collaboration']['value'], values['collaboration']['source']), ('team', 'shared'))
        self.assertEqual(values['reply-style']['shared_value'], 'brief')
        self.assertEqual({item['name'] for item in report['differences']}, {'mode', 'reply-style'})
        self.assertEqual(values['setup-review']['value'], 'pending')
        self.assertTrue(report['recorded_choices'])
        self.assertIn('Reuse', self.tack('setup'))
        self.assertEqual((clone / '.git/config').read_bytes(), before)
        self.assertEqual(self.run_command('git', 'status', '--porcelain'), '')

    def test_setup_rejects_invalid_profile_and_does_not_run_shared_commands(self):
        self.tack('config', 'check-fast', 'touch SHOULD_NOT_RUN', '--shared')
        self.tack('setup', '--check')
        self.assertFalse((self.project / 'SHOULD_NOT_RUN').exists())
        self.write('tack.json', '{"version":9}')
        self.tack('setup', '--check', status=1)

    def test_non_file_guidance_remains_an_error(self):
        (self.project / 'AGENTS.md').mkdir()
        self.assertIn('not a regular file', self.tack('setup', '--check', status=1))

    def test_existing_claude_guidance_is_not_reinterpreted_as_the_scaffold_bridge(self):
        self.write('docs/system.md', '# System\n')
        self.write('CLAUDE.md', '# Instructions\n[System](docs/system.md "Overview")\n'
                   '```text\n@nonexistent-example.md\n```\n@~/notes.md\n')
        self.tack('setup', '--check')
        self.write('CLAUDE.md', '@AGENTS.md\n')
        self.tack('setup', '--check', status=1)

    def test_empty_project_minimal_base_is_neutral_idempotent_and_needs_review(self):
        self.tack('enable', '--scaffold')
        files = {p.relative_to(self.project).as_posix() for p in self.project.rglob('*') if p.is_file() and '.git' not in p.parts}
        self.assertEqual(files, {'AGENTS.md', 'CLAUDE.md', 'docs/architecture.md', 'docs-map.txt'})
        self.assertFalse((self.project / '.tack').exists())
        report = json.loads(self.tack('setup', '--json'))
        self.assertEqual(report['manifests'], [])
        self.assertEqual(report['commands'], {})
        self.assertEqual(len(report['issues']), 2)
        self.tack('setup', '--check', status=1)
        contents = {p: (self.project / p).read_bytes() for p in files}
        self.tack('enable', '--scaffold', '--shared')
        self.assertTrue((self.project / '.tack').is_file())
        for path, content in contents.items():
            self.assertEqual((self.project / path).read_bytes(), content)

    def test_detection_does_not_execute_scripts_and_respects_existing_files(self):
        self.write('package.json', json.dumps({'scripts': {'test': 'touch PWNED', 'lint': 'eslint .'}}))
        self.write('pnpm-lock.yaml', '')
        self.write('src/app.ts', 'export const answer = 42;')
        self.write('AGENTS.md', '# Existing instructions\nKeep my choices.\n')
        self.tack('enable', '--scaffold')
        report = json.loads(self.tack('setup', '--json'))
        self.assertEqual(report['commands']['test'][0], 'pnpm run test')
        self.assertFalse((self.project / 'PWNED').exists())
        self.assertIn('Keep my choices.', (self.project / 'AGENTS.md').read_text(encoding='utf-8'))
        self.assertIn('src/* | docs/architecture.md', (self.project / 'docs-map.txt').read_text(encoding='utf-8'))

    def test_monorepo_capabilities_and_existing_pr_template_are_discovered(self):
        self.write('apps/web/package.json', '{}')
        self.write('services/api/pyproject.toml', '[project]\nname="api"')
        self.write('.agents/skills/build/SKILL.md', '# Build')
        self.write('.agents/agents/reviewer.md', '# Review')
        self.write('.cursor/agents/reviewer.md', '# Cursor review')
        self.write('.agents/skills/build/references/notes.md', '# Supporting reference')
        self.write('.github/PULL_REQUEST_TEMPLATE.md', '# Summary')
        report = json.loads(self.tack('setup', '--json'))
        self.assertEqual(len(report['manifests']), 2)
        self.assertEqual(len(report['capabilities']), 3)
        self.assertEqual(report['pr_templates'], ['.github/PULL_REQUEST_TEMPLATE.md'])
        self.assertNotIn('PR template', [item['item'] for item in report['candidates']])
        self.assertEqual(report['commands'], {})  # no root command invented for a nested package
        self.assertFalse((self.project / 'AGENTS.md').exists())

    def test_readiness_checks_links_map_targets_and_review_markers(self):
        self.tack('enable', '--scaffold')
        for relative in ('AGENTS.md', 'docs/architecture.md'):
            path = self.project / relative
            path.write_text(path.read_text(encoding='utf-8').replace(setup.PENDING, ''), encoding='utf-8')
        self.tack('setup', '--check')
        self.write('docs/architecture.md', '# Architecture\n[Missing](missing.md)')
        self.write('docs-map.txt', 'src/* | docs/absent.md\nmalformed\n')
        output = self.tack('setup', '--check', status=1)
        self.assertIn('missing.md', output)
        self.assertIn('docs/absent.md', output)
        self.assertIn('expected code glob', output)

    def test_symlink_parent_rejected_before_any_base_file_is_created(self):
        outside = self.home / 'outside'
        outside.mkdir()
        self.symlink(self.project / 'docs', outside, directory=True)
        self.tack('enable', '--scaffold', status=1)
        self.assertFalse((self.project / 'AGENTS.md').exists())
        self.assertEqual(list(outside.iterdir()), [])
        self.tack('status', '--quiet', status=1)

    def test_plain_enable_stays_file_free_and_review_choices_control_startup(self):
        self.tack('enable')
        self.assertFalse((self.project / 'AGENTS.md').exists())
        self.assertIn('Project setup review pending', self.tack('context'))
        for choice in ('done', 'deferred'):
            self.tack('config', 'setup-review', choice)
            self.assertNotIn('Project setup review pending', self.tack('context'))
        self.tack('config', 'setup-review', 'pending')
        self.assertIn('Project setup review pending', self.tack('context'))
        self.tack('setup', '--unknown', status=2)

    def test_multiple_packages_suggest_scoped_guidance_without_changing_preferences(self):
        self.write('apps/api/package.json', '{}')
        self.write('apps/web/package.json', '{}')
        self.write('apps/api/AGENTS.md', '# API conventions\n')
        report = json.loads(self.tack('setup', '--json'))
        self.assertEqual(report['areas'], [{'path': 'apps/api', 'instructions': 'apps/api/AGENTS.md'},
                                         {'path': 'apps/web', 'instructions': None}])
        self.assertIn('area guidance', [item['item'] for item in report['candidates']])
        self.assertFalse((self.project / 'tack.json').exists())

    def test_shared_marker_preserves_content_and_refuses_symlinks(self):
        self.write('.tack', '# Team activation notes\n')
        self.tack('enable', '--shared')
        self.assertEqual((self.project / '.tack').read_text(encoding='utf-8'), '# Team activation notes\n')
        (self.project / '.tack').unlink()
        target = self.home / 'keep'
        target.write_text('Keep me', encoding='utf-8')
        self.symlink(self.project / '.tack', target)
        self.tack('enable', '--shared', '--scaffold', status=1)
        self.assertEqual(target.read_text(encoding='utf-8'), 'Keep me')
        self.assertFalse((self.project / 'AGENTS.md').exists())


if __name__ == '__main__':
    unittest.main()
