#!/usr/bin/env python3
"""Validate project capabilities without writing to the project or following external paths."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Capabilities(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('capability_validation', ROOT / 'lib/capability_validation.py')
        self.validator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.validator)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return path

    def skill(self, body='Run the project contract tests.'):
        path = self.write('.agents/skills/events/SKILL.md',
                          '---\nname: events\ndescription: Update event contracts when schemas change.\n---\n' + body)
        self.write('AGENTS.md', '[Events](.agents/skills/events/SKILL.md): contract changes.\n')
        return path

    def test_R5_valid_local_capabilities_and_references_are_read_only(self):
        path = self.skill('[Schema](../../../schema.md) and [Steps](references/steps.md).')
        self.write('schema.md', 'Schema reference')
        self.write('.agents/skills/events/references/steps.md', 'Run npm test.')
        before = path.read_bytes()
        self.assertEqual(self.validator.project(self.root), [])
        self.assertEqual(path.read_bytes(), before)

    def test_R5_missing_reference_and_wrong_name_are_rejected(self):
        self.skill('[Missing](references/missing.md)')
        errors = self.validator.project(self.root)
        self.assertTrue(any('missing reference' in e for e in errors), errors)
        self.write('.agents/skills/events/SKILL.md', '---\nname: wrong\ndescription: Useful.\n---\nSteps')
        self.assertTrue(any("should be 'events'" in e for e in self.validator.project(self.root)))

    def test_R5_references_cannot_escape_project(self):
        self.skill('[Outside](../../../../outside.md)')
        self.assertTrue(any('outside project' in e for e in self.validator.project(self.root)))

    def test_R6_capabilities_must_be_discoverable_from_project_instructions(self):
        self.skill()
        (self.root / 'AGENTS.md').unlink()
        self.assertTrue(any('AGENTS.md' in e for e in self.validator.project(self.root)))

    def test_R5_empty_project_does_not_need_capabilities(self):
        self.assertEqual(self.validator.project(self.root), [])
        self.assertEqual(list(self.root.iterdir()), [])

    def test_R5_invalid_or_unfinished_definition_is_rejected(self):
        for text in ('no frontmatter', '---\nname: events\n',
                     '---\nname: events\ndescription: >\n---\n',
                     '---\nname: events\ndescription: ' + 'x' * 401 + '\n---\nSteps'):
            with self.subTest(text=text[:30]):
                path = self.write('.agents/skills/events/SKILL.md', text)
                self.assertTrue(self.validator.definition(path, 'events', 400)[0])

    def test_R7_project_role_is_valid_without_native_registration(self):
        self.write('.agents/agents/event-reviewer.md', '---\nname: event-reviewer\ndescription: Review contract changes.\n---\n'
                   'Read schemas and consumer tests; report incompatible changes without editing files.')
        self.write('AGENTS.md', '[Reviewer](.agents/agents/event-reviewer.md)')
        self.assertEqual(self.validator.project(self.root), [])

    def test_R5_external_symlink_is_not_read(self):
        with tempfile.TemporaryDirectory() as outside:
            external = Path(outside) / 'private.md'
            external.write_text('not a capability', encoding='utf-8')
            target = self.root / '.agents/agents/external.md'
            target.parent.mkdir(parents=True)
            try:
                target.symlink_to(external)
            except OSError:
                self.skipTest('symlinks unavailable')
            errors = self.validator.project(self.root)
            self.assertTrue(any('outside project' in e for e in errors), errors)


if __name__ == '__main__':
    unittest.main()
