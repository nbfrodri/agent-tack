#!/usr/bin/env python3
"""Project preferences survive cloning without sharing personal state or execution trust."""
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('verification_fixture', REPO / 'tests/verification.test.py')
FIXTURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIXTURE)


class ProjectConfigTests(unittest.TestCase):
    def setUp(self):
        self.fixture = FIXTURE.VerificationTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def tack(self, *args, expected=0):
        result = self.fixture.command(FIXTURE.BASH, str(REPO / 'bin/tack'), *args)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result.stdout.strip()

    def selection(self, **config):
        self.fixture.write('selected.json', json.dumps({'version': 1, 'mode': 'auto', 'config': config}))

    def test_batch_preview_apply_and_noop_preserve_unselected_values(self):
        self.tack('config', 'reply-style', 'visual', '--shared')
        self.selection(**{'conventional-commits': True, 'plans-path': 'work/plans'})
        profile = self.fixture.root / 'tack.json'
        before = profile.read_bytes()
        preview = self.tack('config', '--shared', '--apply', 'selected.json', '--dry-run')
        self.assertIn('conventional-commits: added', preview)
        self.assertEqual(profile.read_bytes(), before)
        self.tack('config', '--shared', '--apply', 'selected.json')
        self.assertEqual(self.tack('config', 'reply-style'), 'visual (shared)')
        self.assertEqual(self.tack('config', 'conventional-commits'), 'true (shared)')
        self.assertEqual(self.tack('mode'), 'auto (shared)')
        before, modified = profile.read_bytes(), profile.stat().st_mtime_ns
        self.assertIn('unchanged', self.tack('config', '--shared', '--apply', 'selected.json'))
        self.assertEqual((profile.read_bytes(), profile.stat().st_mtime_ns), (before, modified))
        self.assertEqual(self.tack('trusted', expected=1), 'untrusted')
        self.assertFalse((self.fixture.root / '.tack').exists())
        self.assertFalse((self.fixture.root / 'AGENTS.md').exists())

    def test_fresh_clone_reuses_recorded_choices_without_inheriting_local_review_or_trust(self):
        self.tack('enable', '--shared')
        self.fixture.write('AGENTS.md', '# Project\n\n## Setup choices\nUse existing tests. No extra agents.\n')
        self.tack('config', 'setup-review', 'done')
        self.tack('trust')
        self.fixture.commit()
        clone = self.fixture.directory / 'choices-clone'
        self.fixture.git('clone', '-q', str(self.fixture.root), str(clone))
        self.fixture.root = clone
        context = self.tack('context')
        self.assertIn('Reuse recorded setup choices', context)
        self.assertNotIn('ask which optional files to add', context)
        self.assertEqual(self.tack('config', 'setup-review', '--get'), 'pending')
        self.assertEqual(self.tack('trusted', expected=1), 'untrusted')

    def test_batch_shared_default_beats_teammate_personal_default(self):
        self.selection(**{'conventional-commits': True})
        self.tack('config', '--shared', '--apply', 'selected.json')
        self.fixture.commit()
        clone = self.fixture.directory / 'batch-clone'
        self.fixture.git('clone', '-q', str(self.fixture.root), str(clone))
        self.fixture.root = clone
        self.tack('config', 'conventional-commits', 'false', '--global')
        self.assertEqual(self.tack('config', 'conventional-commits'), 'true (shared)')
        self.assertEqual(self.tack('trusted', expected=1), 'untrusted')
        self.tack('config', 'conventional-commits', 'false')
        self.tack('mode', 'strict')
        report = self.tack('config', '--shared', '--apply', 'selected.json')
        self.assertIn('effective false (local)', report)
        self.assertIn('effective strict (local)', report)
        self.assertEqual(self.tack('config', 'conventional-commits'), 'false (local)')

    def test_batch_invalid_selection_is_atomic(self):
        self.tack('config', 'reply-style', 'brief', '--shared')
        profile = self.fixture.root / 'tack.json'
        original = profile.read_bytes()
        invalid = [
            '{"version":1,"config":{"reply-style":"visual","setup-review":"done"}}',
            '{"version":1,"config":{"conventional-commits":"true"}}',
            '{"version":1,"config":{"plans-path":"../outside"}}',
            '{"version":1,"config":{"plans-path":"work","handoffs-path":"work"}}',
            '{"version":1,"version":1}', '{"version":2}',
            '{"version":1,"mode":"unleash"}', ' ' * 65537,
        ]
        for raw in invalid:
            with self.subTest(raw=raw[:90]):
                self.fixture.write('selected.json', raw)
                self.tack('config', '--shared', '--apply', 'selected.json', expected=2)
                self.assertEqual(profile.read_bytes(), original)

    def test_batch_flags_require_shared_selection_without_other_mutations(self):
        self.selection(**{'reply-style': 'brief'})
        for args in [('--apply', 'selected.json'), ('--shared', '--dry-run'),
                     ('--shared', '--apply', 'selected.json', '--unset'),
                     ('--shared', '--apply', 'selected.json', '--json'),
                     ('reply-style', 'visual', '--shared', '--apply', 'selected.json')]:
            self.tack('config', *args, expected=2)
        self.assertFalse((self.fixture.root / 'tack.json').exists())

    def test_batch_rejects_symlink_input_and_context_parent(self):
        outside = self.fixture.directory / 'outside'
        outside.mkdir()
        (outside / 'profile.json').write_text('{"version":1,"mode":"auto"}', encoding='utf-8')
        try:
            (self.fixture.root / 'linked').symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest('Creating symlinks requires local permission')
        self.tack('config', '--shared', '--apply', 'linked/profile.json', expected=2)
        self.selection(**{'architecture-path': 'linked/system.md'})
        self.tack('config', '--shared', '--apply', 'selected.json', expected=2)
        self.assertFalse((self.fixture.root / 'tack.json').exists())

    def test_profile_write_refuses_a_concurrent_edit(self):
        spec = importlib.util.spec_from_file_location('project_config', REPO / 'lib/project_config.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        profile = self.fixture.root / 'tack.json'
        profile.write_text('{"version":1}', encoding='utf-8')
        original = profile.read_bytes()
        actual_fsync = module.os.fsync
        def concurrent_change(descriptor):
            actual_fsync(descriptor)
            profile.write_text('{"version":1,"mode":"lite"}', encoding='utf-8')
        with patch.object(module.os, 'fsync', side_effect=concurrent_change):
            with self.assertRaisesRegex(ValueError, 'changed during'):
                module.write_profile(self.fixture.root, {'version': 1, 'mode': 'strict'}, original)
        self.assertEqual(json.loads(profile.read_text(encoding='utf-8'))['mode'], 'lite')
        self.assertFalse(list(self.fixture.root.glob('.tack-config-*')))

    def test_shared_preferences_survive_clone_but_trust_does_not(self):
        self.tack('config', 'reply-style', 'visual', '--shared')
        self.tack('mode', 'auto', '--shared')
        self.fixture.trust()
        self.fixture.commit()
        clone = self.fixture.directory / 'teammate'
        self.fixture.git('clone', '-q', str(self.fixture.root), str(clone))
        self.fixture.root = clone
        self.assertEqual(self.tack('config', 'reply-style'), 'visual (shared)')
        self.assertEqual(self.tack('mode'), 'auto (shared)')
        self.assertEqual(self.tack('trusted', expected=1), 'untrusted')

    def test_precedence_and_unset_preserve_other_scopes(self):
        self.tack('config', 'reply-style', 'detailed', '--global')
        self.tack('config', 'reply-style', 'visual', '--shared')
        self.tack('config', 'reply-style', 'brief')
        self.assertEqual(self.tack('config', 'reply-style'), 'brief (local)')
        self.assertEqual(self.tack('config', 'reply-style', '--global'), 'detailed (global)')
        self.tack('config', 'reply-style', '--unset')
        self.assertEqual(self.tack('config', 'reply-style'), 'visual (shared)')
        self.tack('config', 'reply-style', '--unset', '--shared')
        self.assertEqual(self.tack('config', 'reply-style'), 'detailed (global)')

    def test_stable_read_interfaces_report_origin(self):
        self.tack('config', 'delegation', 'off', '--shared')
        self.assertEqual(self.tack('config', 'delegation', '--get'), 'off')
        record = json.loads(self.tack('config', 'delegation', '--json'))
        self.assertEqual((record['value'], record['source']), ('off', 'shared'))
        self.assertTrue(record['shared'])

    def test_solo_preferences_need_no_shared_file(self):
        self.tack('config', 'reply-style', 'detailed')
        self.tack('mode', 'strict')
        self.assertEqual(self.tack('config', 'reply-style', '--get'), 'detailed')
        self.assertEqual(self.tack('mode'), 'strict (local)')
        self.assertFalse((self.fixture.root / 'tack.json').exists())

    def test_shared_write_preserves_other_settings(self):
        self.tack('config', 'reply-style', 'brief', '--shared')
        self.tack('config', 'conventional-commits', 'false', '--shared')
        self.tack('mode', 'auto', '--shared')
        data = json.loads((self.fixture.root / 'tack.json').read_text(encoding='utf-8'))
        self.assertEqual(data, {'version': 1, 'mode': 'auto', 'config': {
            'reply-style': 'brief', 'conventional-commits': False}})

    def test_private_and_guard_settings_cannot_be_shared(self):
        for name, value in [('memory', 'false'), ('mods', 'false'), ('activity-log', 'true'),
                            ('disabled-hooks', 'stop-check'), ('merge-requires-green', 'false'),
                            ('setup-review', 'done'), ('trusted', 'true')]:
            self.tack('config', name, value, '--shared', expected=2)
        self.tack('mode', 'unleash', '--shared', expected=2)
        self.assertFalse((self.fixture.root / 'tack.json').exists())

    def test_invalid_profile_is_reported_and_never_overwritten(self):
        for raw in ['{bad', '{"version":2}', '{"version":1,"trusted":true}',
                    '{"version":1,"mode":"unleash"}',
                    '{"version":1,"config":{"reply-style":"invented"}}',
                    '{"version":1,"config":{"conventional-commits":"false"}}',
                    '{"version":1,"version":1}']:
            self.fixture.write('tack.json', raw)
            self.tack('config', 'reply-style', expected=2)
            self.tack('config', 'reply-style', 'brief', '--shared', expected=2)
            self.assertEqual((self.fixture.root / 'tack.json').read_text(encoding='utf-8'), raw)

    def test_symlink_configuration_is_rejected(self):
        outside = self.fixture.directory / 'outside.json'
        outside.write_text('{"version":1}', encoding='utf-8')
        try:
            (self.fixture.root / 'tack.json').symlink_to(outside)
        except OSError:
            self.skipTest('Creating symlinks requires local permission')
        self.tack('config', 'reply-style', expected=2)
        self.tack('config', 'reply-style', 'brief', '--shared', expected=2)
        self.assertEqual(outside.read_text(encoding='utf-8'), '{"version":1}')

    def test_reading_or_writing_command_settings_never_runs_them(self):
        self.tack('config', 'check-fast', 'touch .results', '--shared')
        self.assertEqual(self.tack('config', 'check-fast', '--get'), 'touch .results')
        self.tack('config', '--json')
        self.assertFalse((self.fixture.root / '.results').exists())

    def test_scope_flags_cannot_conflict(self):
        self.tack('config', 'reply-style', 'brief', '--shared', '--global', expected=2)
        self.tack('mode', 'auto', '--shared', '--global', expected=2)

    def test_legacy_hook_runner_has_timeout_and_local_trust(self):
        runner = str(REPO / 'lib/run-check.sh')
        result = self.fixture.command(FIXTURE.BASH, runner, str(self.fixture.root), '1', 'touch .results')
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.fixture.root / '.results').exists())
        self.tack('trust')
        result = self.fixture.command(FIXTURE.BASH, runner, str(self.fixture.root), '1', 'sleep 20')
        self.assertEqual(result.returncode, 124, result.stdout + result.stderr)

    def test_doctor_reports_invalid_shared_profile(self):
        self.fixture.write('tack.json', '{"version": 9}')
        result = self.fixture.command(FIXTURE.BASH, str(REPO / 'bin/tack'), 'doctor')
        self.assertEqual(result.returncode, 1)
        self.assertIn('current project configuration is invalid', result.stdout)

    def test_shared_paths_drive_scaffold_context_and_trace(self):
        for name, value in [('architecture-path', 'guide/system.md'),
                            ('plans-path', 'work/plans'), ('handoffs-path', 'work/handoffs')]:
            self.tack('config', name, value, '--shared')
        self.tack('enable', '--shared', '--scaffold')
        self.assertTrue((self.fixture.root / 'guide/system.md').is_file())
        self.assertFalse((self.fixture.root / 'docs/architecture.md').exists())
        self.assertIn('guide/system.md', (self.fixture.root / 'AGENTS.md').read_text(encoding='utf-8'))
        self.fixture.write('work/handoffs/active.md', '# Handoff\nStatus: in progress\nNext: verify behavior\n')
        self.fixture.write('work/plans/plan.md', '# Plan\n- R1: positive values\n')
        self.fixture.write('tests/test_values.py', 'def test_R1():\n    assert 1 > 0\n')
        self.fixture.commit()
        clone = self.fixture.directory / 'paths-clone'
        self.fixture.git('clone', '-q', str(self.fixture.root), str(clone))
        self.fixture.root = clone
        context = self.tack('context')
        self.assertIn('guide/system.md', context)
        self.assertIn('work/handoffs/active.md', context)
        report = json.loads(self.tack('setup', '--json'))
        self.assertEqual(report['paths']['plans-path'], 'work/plans')
        self.assertFalse(any('missing base file' in x for x in report['issues']))
        trace = self.tack('trace')
        self.assertIn('linked', trace)
        self.assertIn('tests are not executed', trace)

    def test_context_respects_shared_preference(self):
        self.tack('enable')
        self.fixture.write('AGENTS.md', 'Project conventions\n')
        self.tack('config', 'context', 'false', '--shared')
        self.assertNotIn('Project conventions', self.tack('context'))

    def test_shared_check_requires_trust_and_reaches_fast_hook(self):
        self.tack('enable')
        self.tack('config', 'check-fast', 'echo reached > .results; false | cat', '--shared')
        def hook():
            return subprocess.run([FIXTURE.BASH, str(REPO / 'hooks/claude/fast-check.sh')],
                                  input=json.dumps({'cwd': str(self.fixture.root)}),
                                  cwd=self.fixture.root, env=self.fixture.env, capture_output=True,
                                  text=True, timeout=30)
        hook()
        self.assertFalse((self.fixture.root / '.results').exists())
        self.tack('trust')
        result = hook()
        self.assertTrue((self.fixture.root / '.results').is_file())
        self.assertEqual(json.loads(result.stdout)['decision'], 'block')

    def test_shared_commit_convention_reaches_git_hook(self):
        self.tack('enable')
        self.fixture.write('message.txt', 'An existing project format\n')
        result = self.fixture.command(FIXTURE.BASH, str(REPO / 'git-hooks/commit-msg'), 'message.txt')
        self.assertNotEqual(result.returncode, 0)
        self.tack('config', 'conventional-commits', 'false', '--shared')
        result = self.fixture.command(FIXTURE.BASH, str(REPO / 'git-hooks/commit-msg'), 'message.txt')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_unsafe_paths_fail_before_scaffolding(self):
        for value in ('../outside.md', '/outside.md', '.git/config', '.GIT/config', '.git./config',
                      'guide./system.md', 'docs/../outside.md', 'C:/outside', 'docs/\tprivate.md'):
            self.tack('config', 'architecture-path', value, '--shared', expected=2)
        outside = self.fixture.directory / 'outside'
        outside.mkdir()
        try:
            (self.fixture.root / 'guide').symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest('Creating symlinks requires local permission')
        self.tack('config', 'architecture-path', 'guide/system.md', '--shared')
        self.tack('setup', expected=1)
        self.tack('enable', '--scaffold', expected=1)
        self.assertFalse((outside / 'system.md').exists())
        self.assertFalse((self.fixture.root / 'AGENTS.md').exists())


if __name__ == '__main__':
    unittest.main()
