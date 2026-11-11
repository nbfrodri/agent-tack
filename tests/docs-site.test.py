#!/usr/bin/env python3
"""The documentation site: Markdown rendering, the generated reference and `tack docs`."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'lib'))

import docs_site  # noqa: E402
import markdown_lite  # noqa: E402
import sets as tack_sets  # noqa: E402


class MarkdownTests(unittest.TestCase):
    def render(self, text, **kwargs):
        return markdown_lite.render(text, prefix='p', link=kwargs.get('link', lambda target: target))

    def test_headings_get_ids_under_the_prefix(self):
        html = self.render('# Title\n\n## Sets and modes\n')
        self.assertIn('<h1 id="p-title">Title</h1>', html)
        self.assertIn('<h2 id="p-sets-and-modes">Sets and modes</h2>', html)

    def test_heading_ids_follow_github_anchors(self):
        html = self.render('### `targets.txt` columns\n')
        self.assertIn('id="p-targetstxt-columns"', html)

    def test_repeated_headings_get_distinct_ids(self):
        html = self.render('## Usage\n\n## Usage\n')
        self.assertIn('id="p-usage"', html)
        self.assertIn('id="p-usage-2"', html)

    def test_text_is_escaped_everywhere(self):
        html = self.render('a <b> & `<c>`\n\n```\n<script>\n```\n\n| x |\n| --- |\n| <i> |\n')
        self.assertNotIn('<b>', html)
        self.assertNotIn('<script>', html)
        self.assertNotIn('<i>', html)
        self.assertIn('&lt;b&gt; &amp; <code>&lt;c&gt;</code>', html)

    def test_raw_html_blocks_are_skipped(self):
        html = self.render('<p align="center">\n  <img src="x.png">\n</p>\n\nText\n')
        self.assertNotIn('img', html)
        self.assertIn('<p>Text</p>', html)

    def test_inline_markup(self):
        html = self.render('**bold**, *em*, `code` and [a link](target.md#part).')
        self.assertIn('<strong>bold</strong>', html)
        self.assertIn('<em>em</em>', html)
        self.assertIn('<code>code</code>', html)
        self.assertIn('<a href="target.md#part">a link</a>', html)

    def test_code_spans_keep_their_markup_literal(self):
        html = self.render('`**not bold**` and `[not](a link)`')
        self.assertIn('<code>**not bold**</code>', html)
        self.assertNotIn('<a ', html)

    def test_links_go_through_the_resolver(self):
        html = markdown_lite.render('[x](usage.md)', prefix='p', link=lambda target: '#guide-usage')
        self.assertIn('href="#guide-usage"', html)

    def test_unsafe_link_schemes_are_dropped(self):
        html = self.render('[x](javascript:alert(1))')
        self.assertNotIn('javascript', html)

    def test_lists_tables_code_and_quotes(self):
        text = ('- one\n- two\n  continued\n\n1. first\n2. second\n\n'
                '| A | B |\n| --- | --- |\n| `a|b` | 2 |\n\n```bash\ntack docs\n```\n\n> note\n')
        html = self.render(text)
        self.assertIn('<ul><li>one</li><li>two continued</li></ul>', html)
        self.assertIn('<ol><li>first</li><li>second</li></ol>', html)
        self.assertIn('<th>A</th><th>B</th>', html)
        self.assertIn('<td><code>a|b</code></td><td>2</td>', html)
        self.assertIn('<pre><code class="language-bash">tack docs\n</code></pre>', html)
        self.assertIn('<blockquote><p>note</p></blockquote>', html)


class CommandHelpTests(unittest.TestCase):
    def test_help_is_split_into_groups_and_commands(self):
        text = ('Usage: tack\n\nCommands: sets\n\n  set list\n      Named sets\n      and where\n\n'
                '  set agent ROLE              Check a role\n\nGlobal options:\n  -h  Help\n')
        groups = docs_site.command_groups(text)
        self.assertEqual([name for name, _ in groups], ['sets'])
        self.assertEqual(groups[0][1], [('set list', 'Named sets\nand where'),
                                        ('set agent ROLE', 'Check a role')])


class BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='tack-docs-')
        data = Path(cls.temp.name) / 'data'
        os.environ['XDG_DATA_HOME'] = str(data)
        sources, cls.sets = tack_sets.load(ROOT)
        # One external skill is checked out, so its description can be shown; the rest are not.
        cls.external = next(item for entry in cls.sets.values() for item in entry['items']
                            if item['kind'] == 'skill' and item['source'])
        url, commit = sources[cls.external['source']]
        folder = data / 'agent-tack' / 'sources' / cls.external['source'] / commit / cls.external['path']
        folder.mkdir(parents=True)
        (folder / 'SKILL.md').write_text('---\nname: x\ndescription: "Checked-out <description>."\n---\n',
                                         encoding='utf-8')
        cls.html = docs_site.build(ROOT, help_text=subprocess.run(
            ['bash', str(ROOT / 'bin' / 'tack'), 'help'], capture_output=True, text=True, check=True).stdout)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_one_self_contained_page(self):
        self.assertTrue(self.html.startswith('<!doctype html>'))
        self.assertNotRegex(self.html, r'<(script|link)[^>]+(src|href)="https?:')
        self.assertNotIn('{{', self.html)

    def test_every_set_skill_and_agent_is_documented(self):
        for name in self.sets:
            self.assertIn(f'id="set-{name}"', self.html)
        for folder in (ROOT / 'skills').iterdir():
            self.assertIn(f'id="skill-{folder.name}"', self.html)
        for path in (ROOT / 'agents').glob('*.md'):
            self.assertIn(f'id="agent-{path.stem}"', self.html)

    def test_every_command_of_the_help_is_documented(self):
        for command in ('enable', 'set use NAME', 'verify', 'docs', 'doctor'):
            self.assertRegex(self.html, rf'<code class="command">tack {re.escape(command)}')

    def test_external_skills_show_a_description_only_when_checked_out(self):
        self.assertIn('Checked-out &lt;description&gt;.', self.html)
        self.assertIn('not downloaded', self.html)

    def test_guides_are_rendered_and_link_to_each_other_in_page(self):
        self.assertIn('id="guide-usage"', self.html)
        self.assertNotRegex(self.html, r'href="[^"#:]+\.md')

    def test_decision_records_are_left_out_and_linked_as_files(self):
        self.assertNotIn('id="guide-adr-', self.html)
        self.assertIn((ROOT / 'docs' / 'adr' / '0004-personal-configuration-with-sets.md').as_uri(), self.html)

    def test_ids_are_unique_and_every_in_page_link_has_a_target(self):
        ids = re.findall(r'\sid="([^"]+)"', self.html)
        self.assertEqual(sorted(set(i for i in ids if ids.count(i) > 1)), [])
        missing = set(re.findall(r'href="#([^"]+)"', self.html)) - set(ids)
        self.assertEqual(sorted(missing), [])

    def test_search_entries_have_plain_ids_the_page_links_to(self):
        # The page drops search hits whose id is not a plain anchor, so every entry must be one.
        index = json.loads(re.search(r'id="search-index">(.*?)</script>', self.html, re.S).group(1))
        self.assertTrue(index)
        self.assertEqual([entry['id'] for entry in index if not re.match(r'^[a-z0-9_-]+$', entry['id'], re.I)], [])

    def test_the_handwritten_manual_is_included(self):
        self.assertIn('id="manual-start"', self.html)
        self.assertIn('id="manual-cli"', self.html)


class CommandTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='tack-docs-cli-')
        self.addCleanup(temp.cleanup)
        self.work = Path(temp.name)
        home = self.work / 'home'
        stubs = self.work / 'stubs'
        home.mkdir()
        stubs.mkdir()
        self.opened = self.work / 'opened'
        # Stand-ins for every opener, so a test never starts a real browser.
        for opener in ('xdg-open', 'open', 'wslview'):
            stub = stubs / opener
            stub.write_text(f'#!/bin/sh\nprintf "%s\\n" "$1" >> "{self.opened}"\n', encoding='utf-8')
            stub.chmod(0o755)
        self.env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
        self.env.update(HOME=str(home), XDG_CONFIG_HOME=str(home / '.config'),
                        XDG_CACHE_HOME=str(home / '.cache'), XDG_DATA_HOME=str(home / '.local/share'),
                        GIT_CONFIG_NOSYSTEM='1', PATH=f'{stubs}{os.pathsep}{os.environ["PATH"]}')
        self.page = home / '.cache' / 'agent-tack' / 'docs' / 'index.html'

    def tack(self, *args):
        return subprocess.run(['bash', str(ROOT / 'bin' / 'tack'), 'docs', *args], cwd=self.work,
                              env=self.env, capture_output=True, text=True)

    def test_print_path_writes_the_page_without_opening_it(self):
        result = self.tack('--print-path')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(self.page))
        self.assertIn('id="manual-start"', self.page.read_text(encoding='utf-8'))
        self.assertFalse(self.opened.exists())

    def test_opens_the_page_in_a_browser_outside_a_git_repository(self):
        result = self.tack()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.opened.read_text(encoding='utf-8').strip(), str(self.page))

    def test_when_no_opener_works_it_prints_the_path(self):
        for opener in ('xdg-open', 'open', 'wslview'):
            (self.work / 'stubs' / opener).write_text('#!/bin/sh\nexit 1\n', encoding='utf-8')
        result = self.tack()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(str(self.page), result.stdout)

    def test_unknown_options_are_refused(self):
        result = self.tack('--bogus')
        self.assertEqual(result.returncode, 2)
        self.assertIn('docs', result.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
