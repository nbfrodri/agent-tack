#!/usr/bin/env python3
"""Sets of skills, agents and plugins: parsing, pinned sources, project links and the installer."""
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
                           str(self.tack), *args, expected=expected)

    def store(self, commit=None):
        return self.home / '.local/share/agent-tack/sources/up' / (commit or self.first)

    # Declarations

    def test_list_names_every_set_and_marks_the_active_ones(self):
        self.tool('use', 'motion')
        self.tool('use', 'design', '--global')
        out = self.tool('list')
        self.assertRegex(out, r'\*\s+design\s+Interfaces and polish')
        self.assertRegex(out, r'\+\s+motion\s+Animation')

    def test_index_is_one_line_of_names_and_the_sets_active_here(self):
        out = self.tool('index')
        self.assertEqual(len(out.strip().splitlines()), 1)
        self.assertIn('design, motion', out)
        self.assertNotIn('Active here', out)
        self.assertNotIn('polish', out)
        self.tool('use', 'motion')
        self.assertIn('Active here: motion', self.tool('index'))
        self.tool('use', 'design', '--global')
        self.assertIn('Active everywhere: design', self.tool('index'))

    def test_categories_group_the_list_and_the_index(self):
        self.sets('design about Interfaces and polish\ndesign category interfaces\ndesign skill frontend\n'
                  'motion about Animation\nmotion category interfaces\nmotion skill up:skills/motion\n'
                  'shell about Scripts\nshell category stacks\nshell skill frontend\n'
                  'misc about Loose ends\nmisc skill frontend\n')
        index = self.tool('index')
        self.assertEqual(len(index.strip().splitlines()), 1)
        self.assertIn('interfaces: design, motion; stacks: shell; other: misc.', index)
        self.assertIn('tack set drop NAME', index)
        listed = self.tool('list').splitlines()
        self.assertLess(listed.index('interfaces'), listed.index('stacks'))
        self.sets('design category Not_A_Name\n')
        self.assertIn('category', self.tool('check', expected=1))

    def test_the_core_set_is_always_active_and_cannot_be_dropped(self):
        self.sets('core about Always on\ncore skill frontend\ndesign about Interfaces\ndesign skill up:skills/polish\n')
        self.assertRegex(self.tool('list'), r'\*\s+core\s+Always on')
        self.assertIn('always active', self.tool('drop', 'core', '--global', expected=1))
        self.assertIn('always active', self.tool('use', 'core', expected=1))
        self.tool('use', 'design', '--global')
        self.assertEqual(self.git(self.project, 'config', '--global', 'tack.sets'), 'design')
        index = self.tool('index')
        self.assertNotIn('core', index)
        self.assertIn('Active everywhere: design', index)
        # A project set does not link again what the always-active set already provides.
        self.sets('core about Always on\ncore skill frontend\nweb about Web\nweb skill frontend\nweb skill up:skills/polish\n')
        self.tool('use', 'web')
        self.assertFalse((self.project / '.agents/skills/frontend').exists())
        self.assertTrue((self.project / '.agents/skills/polish').is_symlink())

    def test_a_compatibility_set_is_listed_but_not_offered_to_the_assistant(self):
        self.sets('design about Interfaces\ndesign category interfaces\ndesign skill up:skills/polish\n'
                  'everything about The former full catalog\neverything category compat\neverything skill frontend\n')
        self.assertIn('everything', self.tool('list'))
        index = self.tool('index')
        self.assertIn('interfaces: design.', index)
        self.assertNotIn('everything', index)
        self.assertNotIn('compat', index)
        self.tool('use', 'everything', '--global')
        self.assertIn('Active everywhere: everything', self.tool('index'))

    # Suggestions from what the project contains

    def suggesting(self):
        self.sets('core about Always on\ncore skill frontend\n'
                  'python about Python\npython category stacks\npython skill up:skills/polish\n'
                  'python match pyproject.toml\npython match *.py 2\n'
                  'react about React\nreact category stacks\nreact skill up:skills/motion\nreact match package.json:react\n'
                  'saas about Payments\nsaas skill frontend\nsaas match pyproject.toml:stripe\n'
                  'shell about Shell\nshell skill frontend\nshell match *.sh 3\n'
                  'ops about Infra\nops skill frontend\nops match k8s/*\nops match Dockerfile\n'
                  'review about Review\nreview skill frontend\n'
                  'everything about Compat\neverything category compat\neverything skill frontend\neverything match *.py\n')

    def put(self, name, text='x\n'):
        path = self.project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def test_suggest_names_the_sets_a_project_s_files_call_for_with_the_evidence(self):
        self.suggesting()
        self.put('pyproject.toml', '[project]\ndependencies = ["fastapi", "stripe>=9"]\n')
        self.put('package.json', '{"dependencies": {"preact": "10", "react-dom": "19"}}')
        self.put('run.sh')
        self.put('deploy/k8s/api.yaml')
        self.put('k8s/api.yaml')
        out = self.tool('suggest')
        self.assertRegex(out, r'python\s+.*pyproject\.toml')
        self.assertRegex(out, r'saas\s+.*pyproject\.toml')
        self.assertRegex(out, r'ops\s+.*k8s/api\.yaml')
        # A dependency is matched by its exact name, a glob by enough files, a set by having a rule.
        for absent in ('react', 'shell', 'review', 'everything', 'core'):
            self.assertNotRegex(out, rf'(?m)^\s*{absent}\b')
        self.put('package.json', '{"devDependencies": {"react": "19"}}')
        self.put('a.sh')
        self.put('b.sh')
        out = self.tool('suggest')
        self.assertRegex(out, r'(?m)^\s*react\b')
        self.assertRegex(out, r'(?m)^\s*shell\b.*3')

    def test_suggest_ignores_what_git_ignores_and_what_is_already_active(self):
        self.suggesting()
        self.put('.gitignore', 'vendor/\n')
        self.put('vendor/lib/pyproject.toml')
        self.assertIn('no set', self.tool('suggest').lower())
        self.put('pyproject.toml')
        self.put('Dockerfile')
        self.tool('use', 'python')
        out = self.tool('suggest')
        self.assertNotRegex(out, r'(?m)^\s*python\b')
        self.assertRegex(out, r'(?m)^\s*ops\b')
        self.tool('use', 'ops', '--global')
        self.assertIn('no set', self.tool('suggest').lower())

    def test_suggest_apply_activates_them_in_the_project_and_the_index_says_what_is_pending(self):
        self.suggesting()
        self.put('pyproject.toml')
        self.put('Dockerfile')
        index = self.tool('index')
        self.assertIn('Fit this project and are not active: python, ops', index)
        self.assertIn('tack set suggest --apply', index)
        self.tool('suggest', '--apply')
        self.assertEqual(self.git(self.project, 'config', '--local', 'tack.sets'), 'python,ops')
        self.assertTrue((self.project / '.agents/skills/polish').is_symlink())
        self.assertNotIn('Fit this project', self.tool('index'))
        self.assertIn('no set', self.tool('suggest', '--apply').lower())

    def test_suggest_needs_a_repository_and_reads_no_file_through_a_link(self):
        self.suggesting()
        self.assertIn('git repository', self.tool('suggest', cwd=self.work, expected=2))
        secret = self.work / 'outside.toml'
        secret.write_text('stripe\n', encoding='utf-8')
        os.symlink(secret, self.project / 'pyproject.toml')
        out = self.tool('suggest')
        self.assertNotRegex(out, r'(?m)^\s*saas\b')

    def test_reminder_names_the_active_skills_and_the_sets_still_to_activate(self):
        self.suggesting()
        self.assertEqual(self.tool('reminder').strip(), '')
        self.put('pyproject.toml')
        out = self.tool('reminder')
        self.assertEqual(len(out.strip().splitlines()), 1)
        self.assertIn('fit this project and are not active: python', out)
        self.assertIn('tack set suggest --apply', out)
        self.assertIn('tack set suggest --skip', out)
        self.assertNotIn('Skills active', out)
        self.tool('use', 'python')
        self.tool('use', 'react', '--global')
        out = self.tool('reminder')
        # Skills of this project's sets and of the sets active everywhere; never the always-active ones.
        self.assertIn('Skills active in this project: polish, motion.', out)
        self.assertIn('load the ones whose name matches this task', out)
        self.assertNotIn('frontend', out)
        self.assertNotIn('fit this project', out)
        self.assertEqual(self.tool('reminder', cwd=self.work).strip(), '')

    def test_suggest_skip_declines_the_pending_sets_for_this_project_until_new_ones_fit(self):
        self.suggesting()
        self.put('pyproject.toml')
        self.put('Dockerfile')
        out = self.tool('suggest', '--skip')
        self.assertIn('python', out)
        self.assertEqual(self.git(self.project, 'config', '--local', 'tack.setsSkipped'), 'python,ops')
        self.assertIn('no set', self.tool('suggest').lower())
        self.assertEqual(self.tool('reminder').strip(), '')
        self.assertNotIn('Fit this project', self.tool('index'))
        self.assertEqual(self.run_in(self.project, 'git', 'config', '--local', '--get', 'tack.sets', expected=1), '')
        # A set that starts to fit later is still offered; a declined one can be used by name.
        self.put('package.json', '{"dependencies": {"react": "19"}}')
        self.assertIn('not active: react', self.tool('reminder'))
        self.tool('use', 'python')
        self.assertEqual(self.git(self.project, 'config', '--local', 'tack.sets'), 'python')
        self.assertIn('--apply or --skip', self.tool('suggest', '--apply', '--skip', expected=1))

    # Suggestions from what the user asks

    def asking(self):
        self.sets('core about Always on\ncore skill frontend\n'
                  'review about Review\nreview skill up:skills/polish\nreview ask review revis* pull+request\n'
                  'security about Security\nsecurity skill frontend\nsecurity ask security seguridad threat+model amenaza*\n'
                  'python about Python\npython skill up:skills/motion\npython match pyproject.toml\n')

    def remind(self, prompt, cwd=None):
        result = subprocess.run([sys.executable, str(ROOT / 'lib/sets.py'), str(self.tack), 'reminder', '--stdin'],
                                cwd=cwd or self.project, env=self.env, input=json.dumps({'prompt': prompt}),
                                capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_reminder_names_the_sets_a_request_asks_for_in_either_language(self):
        self.asking()
        cases = {
            'Review this branch before I open a pull request': 'review',
            'Revisa el código de la rama': 'review',
            'haz una REVISIÓN completa': 'review',
            'Escribe un modelo de amenazas del servicio': 'security',
            'write a threat model for uploads': 'security',
        }
        for prompt, expected in cases.items():
            with self.subTest(prompt=prompt):
                out = self.remind(prompt)
                self.assertIn(f'match this request and are not active: {expected}.', out)
                self.assertIn('tack set use NAME', out)
                self.assertIn('tack set skip NAME', out)
        self.assertIn('not active: review, security.', self.remind('security review of the pull request'))

    def test_a_word_inside_another_or_out_of_order_asks_for_nothing(self):
        self.asking()
        for prompt in ('Fix the typo in README', 'show me the preview pane', 'the model had a threat', 'insecurity is a feeling', ''):
            with self.subTest(prompt=prompt):
                self.assertEqual(self.remind(prompt).strip(), '')

    def test_a_request_never_asks_for_a_set_that_is_active_or_declined(self):
        self.asking()
        self.tool('use', 'review')
        out = self.remind('review the security of this endpoint')
        self.assertIn('match this request and are not active: security.', out)
        self.assertIn('Skills active in this project: polish.', out)
        self.assertIn('declined', self.tool('skip', 'security').lower())
        self.assertEqual(self.git(self.project, 'config', '--local', 'tack.setsSkipped'), 'security')
        self.assertNotIn('match this request', self.remind('review the security of this endpoint'))
        self.assertIn('unknown set', self.tool('skip', 'nope', expected=1))
        self.assertIn('always active', self.tool('skip', 'core', expected=1))

    def test_file_and_request_suggestions_are_reported_apart(self):
        self.asking()
        self.put('pyproject.toml')
        out = self.remind('review this')
        self.assertIn('fit this project and are not active: python.', out)
        self.assertIn('match this request and are not active: review.', out)
        self.assertEqual(len(out.strip().splitlines()), 1)
        # Without a message, as in the startup context, only the project's files speak.
        self.assertNotIn('match this request', self.tool('reminder'))

    def test_check_rejects_a_malformed_ask_rule(self):
        for rule in ('x ask\n', 'x ask re view!\n', 'x ask *view\n', 'x ask a+\n', 'x ask UPPER\n'):
            with self.subTest(rule=rule):
                self.sets('x about X\nx skill frontend\n' + rule)
                self.assertIn('ask', self.tool('check', expected=1))

    def test_check_rejects_a_malformed_match_rule(self):
        for rule in ('x match ../*.py\n', 'x match /etc/passwd\n', 'x match *.py many\n', 'x match a b c\n', 'x match pyproject.toml:\n'):
            with self.subTest(rule=rule):
                self.sets('x about X\nx skill frontend\n' + rule)
                self.assertIn('match', self.tool('check', expected=1))

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

    def test_options_are_not_abbreviated_and_the_checkout_cannot_be_redirected(self):
        # The command guard matches --global literally, so a prefix must not mean the same thing.
        self.tool('use', 'design', '--glo', expected=2)
        self.tool('drop', 'design', '--g', expected=2)
        self.assertEqual(self.run_in(self.project, 'git', 'config', '--global', '--get', 'tack.sets', expected=1), '')
        other = self.work / 'other'
        other.mkdir()
        (other / 'sets.txt').write_text('evil about Another checkout\n', encoding='utf-8')
        out = self.tool('--root', str(other), 'list', expected=2)
        self.assertNotIn('Another checkout', out)

    def test_a_project_folder_that_is_a_symlink_is_left_alone(self):
        outside = self.work / 'outside-home'
        (outside / 'skills').mkdir(parents=True)
        os.symlink(self.store() / 'skills/stale', outside / 'skills/stale')
        os.symlink(outside, self.project / '.claude')
        out = self.tool('use', 'design')
        self.assertIn('symlink', out)
        self.assertEqual(sorted(path.name for path in (outside / 'skills').iterdir()), ['stale'])
        self.assertFalse((outside / 'agents').exists())
        # The other folder is a real directory and still gets its links.
        self.assertTrue((self.project / '.agents/skills/polish').is_symlink())
        nested = self.project / '.agents/skills'
        shutil.rmtree(self.project / '.agents')
        (self.project / '.agents').mkdir()
        os.symlink(outside / 'skills', nested)
        self.tool('sync')
        self.assertEqual(sorted(path.name for path in (outside / 'skills').iterdir()), ['stale'])

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
        doctor = subprocess.run([BASH, str(self.checkout / 'bin/tack'), 'doctor'], cwd=self.checkout, env=self.env,
                                capture_output=True, text=True, timeout=120)
        self.assertNotIn('outside this checkout', doctor.stdout)
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
        self.run_in(ROOT, sys.executable, str(ROOT / 'lib/sets.py'), str(ROOT), 'check')


if __name__ == '__main__':
    unittest.main()
