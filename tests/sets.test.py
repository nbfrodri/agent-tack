#!/usr/bin/env python3
"""Sets of skills, agents and plugins: parsing, pinned sources, project links and the installer."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which('bash')


class SetsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tack-sets-')
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name).resolve()
        self.home = self.work / 'home'
        self.home.mkdir()
        self.env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
        self.env.update(HOME=str(self.home), USERPROFILE=str(self.home),
                        XDG_CONFIG_HOME=str(self.home / '.config'),
                        XDG_DATA_HOME=str(self.home / '.local/share'),
                        XDG_STATE_HOME=str(self.home / '.local/state'),
                        GIT_CONFIG_GLOBAL=str(self.home / '.gitconfig'), GIT_CONFIG_NOSYSTEM='1')
        # A stand-in for the Claude CLI that records its arguments instead of installing plugins.
        fake = self.work / 'bin'
        fake.mkdir()
        self.calls = self.work / 'claude.calls'
        (fake / 'claude').write_text(f'#!/bin/sh\necho "$*" >> "{self.calls}"\n', encoding='utf-8')
        (fake / 'claude').chmod(0o755)
        self.env['PATH'] = f'{fake}{os.pathsep}{self.env["PATH"]}'
        # A tack checkout holding only what sets read, so the fixtures never touch the real files.
        self.tack = self.work / 'tack'
        (self.tack / 'skills/frontend').mkdir(parents=True)
        (self.tack / 'skills/frontend/SKILL.md').write_text('---\nname: frontend\n---\n', encoding='utf-8')
        (self.tack / 'agents').mkdir()
        (self.tack / 'agents/ui-reviewer.md').write_text('---\nname: ui-reviewer\n---\n', encoding='utf-8')
        # An upstream collection with two commits.
        self.upstream = self.work / 'upstream'
        self.upstream.mkdir()
        self.git(self.upstream, 'init', '-q', '-b', 'main')
        self.git(self.upstream, 'config', 'user.name', 'Test')
        self.git(self.upstream, 'config', 'user.email', 'test@example.invalid')
        self.skill('polish', 'first')
        self.skill('motion', 'first')
        (self.upstream / 'shared.md').write_text('shared reference\n', encoding='utf-8')
        self.first = self.commit()
        self.sources(self.first)
        self.sets('design about Interfaces and polish\n'
                  'design skill frontend\n'
                  'design skill up:skills/polish\n'
                  'design agent ui-reviewer\n'
                  'design plugin frontend-design@claude-plugins-official\n'
                  'motion about Animation\n'
                  'motion skill up:skills/motion\n')
        self.project = self.work / 'project'
        self.project.mkdir()
        self.git(self.project, 'init', '-q', '-b', 'main')

    def skill(self, name, body):
        folder = self.upstream / 'skills' / name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'SKILL.md').write_text(f'---\nname: {name}\n---\n{body}\n', encoding='utf-8')

    def commit(self):
        self.git(self.upstream, 'add', '.')
        self.git(self.upstream, 'commit', '-qm', 'test: fixture')
        return self.git(self.upstream, 'rev-parse', 'HEAD')

    def sources(self, commit):
        (self.tack / 'sources.txt').write_text(f'# name url commit\nup {self.upstream} {commit}\n', encoding='utf-8')

    def sets(self, text):
        (self.tack / 'sets.txt').write_text(text, encoding='utf-8')

    def run_in(self, cwd, *args, expected=0):
        result = subprocess.run(args, cwd=cwd, env=self.env, capture_output=True, text=True,
                                encoding='utf-8', errors='replace', timeout=120)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def git(self, cwd, *args):
        return self.run_in(cwd, 'git', *args).strip()

    def tool(self, *args, cwd=None, expected=0):
        return self.run_in(cwd or self.project, sys.executable, str(ROOT / 'lib/sets.py'),
                           '--root', str(self.tack), *args, expected=expected)

    def store(self, commit=None):
        return self.home / '.local/share/agent-tack/sources/up' / (commit or self.first)

    # Declarations

    def test_list_names_every_set_and_marks_the_active_ones(self):
        self.tool('use', 'motion')
        self.tool('use', 'design', '--global')
        out = self.tool('list')
        self.assertRegex(out, r'\*\s+design\s+Interfaces and polish')
        self.assertRegex(out, r'\+\s+motion\s+Animation')

    def test_show_lists_the_items_of_a_set(self):
        out = self.tool('show', 'design')
        for expected in ('frontend', 'up:skills/polish', 'ui-reviewer', 'frontend-design@claude-plugins-official'):
            self.assertIn(expected, out)

    def test_check_rejects_unsafe_or_inconsistent_declarations(self):
        cases = {
            'x skill up:../escape\n': 'path',
            'x skill up:/abs/skill\n': 'path',
            'x skill nowhere:skills/a\n': 'source',
            'x skill missing-tack-skill\n': 'skills/',
            'x agent missing-agent\n': 'agents/',
            'x plugin no-marketplace\n': 'plugin@marketplace',
            'x gadget thing\n': 'kind',
            'x skill up:skills/frontend\n': 'same name',
            'Bad_Name skill frontend\n': 'set name',
        }
        for text, message in cases.items():
            with self.subTest(text=text):
                self.sets(text)
                self.assertIn(message, self.tool('check', expected=1))

    def test_check_rejects_a_source_without_a_full_commit_or_with_another_transport(self):
        for line in ('up https://example.invalid/r.git main\n', 'up https://example.invalid/r.git abc123\n',
                     f'up git://example.invalid/r.git {self.first}\n', f'up relative/path {self.first}\n',
                     f'up --upload-pack=evil {self.first}\n'):
            with self.subTest(line=line):
                (self.tack / 'sources.txt').write_text(line, encoding='utf-8')
                self.tool('check', expected=1)

    def test_use_rejects_an_unknown_set(self):
        self.assertIn('unknown set', self.tool('use', 'nope', expected=1))

    # Project scope

    def test_use_links_the_set_into_the_project_for_every_tool_and_hides_it_from_git(self):
        self.tool('use', 'design')
        for folder in ('.agents/skills', '.claude/skills'):
            self.assertEqual((self.project / folder / 'polish/SKILL.md').read_text(encoding='utf-8').split('\n')[3], 'first')
            self.assertTrue((self.project / folder / 'frontend/SKILL.md').is_file())
        self.assertEqual(os.readlink(self.project / '.agents/skills/polish'), str(self.store() / 'skills/polish'))
        self.assertEqual(os.readlink(self.project / '.claude/agents/ui-reviewer.md'), str(self.tack / 'agents/ui-reviewer.md'))
        self.assertEqual(self.git(self.project, 'status', '--porcelain'), '')
        self.assertEqual(self.git(self.project, 'config', '--local', 'tack.sets'), 'design')
        # A skill keeps reaching files its collection shares outside its own folder.
        self.assertTrue((self.project / '.agents/skills/polish/../../shared.md').is_file())

    def test_use_is_repeatable_and_keeps_a_skill_the_project_already_has(self):
        own = self.project / '.agents/skills/polish'
        own.mkdir(parents=True)
        (own / 'SKILL.md').write_text('mine\n', encoding='utf-8')
        out = self.tool('use', 'design')
        self.tool('use', 'design')
        self.assertIn('kept', out)
        self.assertEqual((own / 'SKILL.md').read_text(encoding='utf-8'), 'mine\n')
        self.assertFalse(own.is_symlink())
        self.assertEqual(self.git(self.project, 'config', '--local', 'tack.sets'), 'design')

    def test_drop_removes_only_the_links_no_remaining_set_needs(self):
        self.tool('use', 'design')
        self.tool('use', 'motion')
        mine = self.project / '.claude/skills/mine'
        mine.mkdir()
        self.tool('drop', 'design')
        self.assertFalse((self.project / '.agents/skills/polish').is_symlink())
        self.assertFalse((self.project / '.claude/agents/ui-reviewer.md').is_symlink())
        self.assertTrue((self.project / '.agents/skills/motion').is_symlink())
        self.assertTrue(mine.is_dir())
        self.assertEqual(self.git(self.project, 'config', '--local', 'tack.sets'), 'motion')

    def test_plugins_of_a_project_set_are_installed_and_removed_for_this_clone_only(self):
        self.tool('use', 'design')
        self.tool('drop', 'design')
        self.assertEqual(self.calls.read_text(encoding='utf-8').splitlines(),
                         ['plugin install frontend-design@claude-plugins-official --scope local',
                          'plugin uninstall frontend-design@claude-plugins-official --scope local'])

    def test_a_set_active_everywhere_is_not_linked_again_in_the_project(self):
        self.tool('use', 'design', '--global')
        self.tool('use', 'design')
        self.assertFalse((self.project / '.agents/skills/polish').exists())

    def test_sync_recreates_project_links_on_another_machine(self):
        self.git(self.project, 'config', '--local', 'tack.sets', 'motion')
        self.tool('sync')
        self.assertTrue((self.project / '.claude/skills/motion/SKILL.md').is_file())

    def test_project_scope_needs_a_repository(self):
        self.assertIn('git repository', self.tool('use', 'design', cwd=self.work, expected=2))

    # Pinned sources

    def test_a_source_is_checked_out_at_its_pinned_commit_not_the_branch_head(self):
        self.skill('polish', 'second')
        self.commit()
        self.tool('use', 'design')
        self.assertIn('first', (self.project / '.agents/skills/polish/SKILL.md').read_text(encoding='utf-8'))

    def test_a_missing_commit_or_skill_fails_without_linking_anything(self):
        self.sources('0' * 40)
        self.assertIn('cannot fetch', self.tool('use', 'design', expected=1))
        self.assertFalse((self.project / '.agents/skills/frontend').exists())
        self.sources(self.first)
        self.sets('design skill up:skills/absent\n')
        self.assertIn('no SKILL.md', self.tool('use', 'design', expected=1))

    def test_a_skill_path_that_leaves_the_checkout_through_a_symlink_is_refused(self):
        outside = self.work / 'outside'
        outside.mkdir()
        (outside / 'SKILL.md').write_text('outside\n', encoding='utf-8')
        os.symlink(outside, self.upstream / 'skills/escape')
        self.sources(self.commit())
        self.sets('design skill up:skills/escape\n')
        self.assertIn('outside', self.tool('use', 'design', expected=1))

    def test_update_moves_the_pin_and_reports_what_changed(self):
        self.tool('use', 'design')
        self.skill('polish', 'second')
        second = self.commit()
        out = self.tool('update')
        self.assertIn(self.first[:12], out)
        self.assertIn(second[:12], out)
        self.assertIn('skills/polish', out)
        self.assertNotIn('skills/motion', out)
        self.assertIn(second, (self.tack / 'sources.txt').read_text(encoding='utf-8'))
        self.assertIn('# name url commit', (self.tack / 'sources.txt').read_text(encoding='utf-8'))
        self.tool('sync')
        self.assertIn('second', (self.project / '.agents/skills/polish/SKILL.md').read_text(encoding='utf-8'))
        self.assertIn('up to date', self.tool('update'))

    # Installer

    def install(self, *args):
        return self.run_in(self.checkout, BASH, str(self.checkout / 'install.sh'), '--skip-plugins', *args)

    def checkout_with_fixtures(self):
        self.checkout = self.work / 'checkout'
        shutil.copytree(ROOT, self.checkout, symlinks=True,
                        ignore=shutil.ignore_patterns('.git', 'docs', 'evals', 'tests', '__pycache__'))
        shutil.copy(self.tack / 'sets.txt', self.checkout / 'sets.txt')
        shutil.copy(self.tack / 'sources.txt', self.checkout / 'sources.txt')
        self.tack = self.checkout

    def test_installer_links_the_global_sets_for_every_tool_and_removes_dropped_ones(self):
        self.checkout_with_fixtures()
        self.tool('use', 'design', '--global')
        self.install()
        for folder in ('.agents/skills', '.claude/skills', '.codex/skills'):
            self.assertEqual(os.readlink(self.home / folder / 'polish'), str(self.store() / 'skills/polish'))
            # A tack skill outside the selected groups comes with its set.
            self.assertTrue((self.home / folder / 'frontend').is_symlink())
            self.assertFalse((self.home / folder / 'motion').exists())
        self.assertTrue((self.home / '.claude/agents/ui-reviewer.md').is_symlink())
        self.assertTrue((self.home / '.codex/agents/ui-reviewer.toml').is_file())
        self.assertFalse((self.home / '.claude/agents/planner.md').exists())
        self.tool('drop', 'design', '--global')
        self.tool('use', 'motion', '--global')
        self.install()
        for folder in ('.agents/skills', '.claude/skills', '.codex/skills'):
            self.assertFalse((self.home / folder / 'polish').is_symlink())
            self.assertFalse((self.home / folder / 'frontend').is_symlink())
            self.assertTrue((self.home / folder / 'motion').is_symlink())
        self.assertFalse((self.home / '.claude/agents/ui-reviewer.md').exists())

    def test_uninstall_removes_the_links_to_set_skills(self):
        self.checkout_with_fixtures()
        self.tool('use', 'design', '--global')
        self.install()
        self.run_in(self.checkout, BASH, str(self.checkout / 'uninstall.sh'))
        for folder in ('.agents/skills', '.claude/skills', '.codex/skills'):
            self.assertFalse((self.home / folder / 'polish').is_symlink())

    def test_installer_dry_run_fetches_and_links_nothing(self):
        self.checkout_with_fixtures()
        self.tool('use', 'design', '--global')
        out = self.install('--dry-run')
        self.assertIn('polish', out)
        self.assertFalse(self.store().exists())
        self.assertFalse((self.home / '.claude/skills').exists())

    def test_installer_keeps_working_links_when_a_source_cannot_be_fetched(self):
        self.checkout_with_fixtures()
        self.tool('use', 'design', '--global')
        self.install()
        (self.checkout / 'sources.txt').write_text(f'up {self.work / "gone"} {"1" * 40}\n', encoding='utf-8')
        result = subprocess.run([BASH, str(self.checkout / 'install.sh'), '--skip-plugins'], cwd=self.checkout,
                                env=self.env, capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertTrue((self.home / '.claude/skills/polish/SKILL.md').is_file())

    def test_the_shipped_declarations_are_valid(self):
        self.run_in(ROOT, sys.executable, str(ROOT / 'lib/sets.py'), '--root', str(ROOT), 'check')


if __name__ == '__main__':
    unittest.main()
