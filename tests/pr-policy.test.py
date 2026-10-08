#!/usr/bin/env python3
"""Offline PR event checks; never need a token or GitHub API."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CHECKER = Path(__file__).resolve().parents[1] / 'skills/github-issues/assets/check-pr.py'


class PRPolicyTests(unittest.TestCase):
    def run_check(self, body='## Summary\nFix the missing order ID.\n## Validation\nTests passed: 12.\n',
                  title='fix(api): return the order ID', draft=False, extra=()):
        with tempfile.TemporaryDirectory(prefix='tack-pr-') as directory:
            path = Path(directory) / 'event.json'
            path.write_text(json.dumps({'pull_request': {'title': title, 'body': body, 'draft': draft}}), encoding='utf-8')
            return subprocess.run([sys.executable, str(CHECKER), '--event', str(path), *extra],
                                  capture_output=True, text=True, encoding='utf-8', timeout=10)

    def test_valid_metadata_and_honest_skipped_validation(self):
        self.assertEqual(self.run_check().returncode, 0)
        result = self.run_check(body='## Summary\nClarify setup instructions.\n## Validation\nNot run: prose only; reviewed links manually.')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_empty_and_placeholder_sections(self):
        for body in ['## Summary\nFixed orders.', '## Summary\n<!-- example -->\n## Validation\nTests passed.',
                     '## Summary\nTBD\n## Validation\nTODO',
                     '## Summary\nFixed orders.\n## Validation\n- [ ] TODO']:
            with self.subTest(body=body):
                self.assertEqual(self.run_check(body=body).returncode, 1)

    def test_title_and_project_specific_headings(self):
        self.assertEqual(self.run_check(title='Update stuff').returncode, 1)
        self.assertEqual(self.run_check(title='Update stuff', extra=('--title-policy', 'any')).returncode, 0)
        result = self.run_check(body='## Change\nReturn stable IDs.\n## Checks\nUnit suite: 12 passed.',
                                extra=('--summary-heading', 'Change', '--validation-heading', 'Checks'))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_drafts_defer_and_optional_issue_reference_is_only_syntax(self):
        self.assertEqual(self.run_check(body='', title='', draft=True).returncode, 0)
        self.assertEqual(self.run_check(extra=('--require-issue',)).returncode, 1)
        body = '## Summary\nFix IDs. Refs #42\n## Validation\nTests passed.'
        self.assertEqual(self.run_check(body=body, extra=('--require-issue',)).returncode, 0)
        self.assertEqual(self.run_check(body=body.replace('#42', '#0'), extra=('--require-issue',)).returncode, 1)

    def test_metadata_is_inert_and_not_echoed_as_workflow_commands(self):
        result = self.run_check(title='fix: $(touch injected) `echo unsafe`',
                                body='## Summary\n::error::injected\n## Validation\n$(echo harmless)')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('injected', result.stdout)
        self.assertNotIn('::error::', result.stdout)

    def test_invalid_event_is_an_error_and_code_headings_do_not_count(self):
        with tempfile.TemporaryDirectory(prefix='tack-pr-') as directory:
            event = Path(directory) / 'bad.json'
            event.write_text('{}', encoding='utf-8')
            result = subprocess.run([sys.executable, str(CHECKER), '--event', str(event)], capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 2)
        self.assertEqual(self.run_check(body='```md\n## Summary\nFake content\n## Validation\nFake tests\n```').returncode, 1)


if __name__ == '__main__':
    unittest.main()
