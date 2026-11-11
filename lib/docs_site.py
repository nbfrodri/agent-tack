#!/usr/bin/env python3
"""Build tack's documentation site: one self-contained HTML page for `tack docs`.

The hand-written manual (lib/docs-site/manual.html) comes first; the CLI reference, sets, skills,
agents and guides are generated from `tack help`, sets.txt, the SKILL.md and agent files and the
Markdown under docs/, so the page cannot fall behind the repository. Nothing is fetched: an
external skill shows its description only when its pinned checkout is already on this machine.

Usage: docs_site.py ROOT OUTPUT   (reads `tack help` from standard input)
"""
import html
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import markdown_lite  # noqa: E402
import sets as tack_sets  # noqa: E402

SITE = Path(__file__).resolve().parent / 'docs-site'
COMMANDS = re.compile(r'^Commands:\s*(.+?)\s*$')
ENTRY = re.compile(r'^ {2}(\S.*?)(?: {2,}(\S.*))?$')
SECTION = re.compile(r'<section class="page" id="([a-z0-9-]+)" data-title="([^"]+)"')
CATEGORIES = {'base': 'Base', 'interfaces': 'Interfaces', 'stacks': 'Stacks', 'quality': 'Quality',
              'process': 'Process', 'operations': 'Operations', 'data-ai': 'Data and AI',
              'beyond-code': 'Beyond code', 'subagents': 'Subagents', 'compat': 'Compatibility'}


def esc(text):
    return html.escape(text or '', quote=True)


def frontmatter(path):
    """The simple `key: value` fields of a Markdown file's frontmatter, folded values joined."""
    try:
        lines = path.read_text(encoding='utf-8').splitlines()
    except OSError:
        return {}
    if not lines or lines[0].strip() != '---':
        return {}
    fields, key = {}, None
    for line in lines[1:]:
        if line.strip() == '---':
            break
        match = re.match(r'^([A-Za-z_-]+):\s*(.*)$', line)
        if match:
            key, value = match.groups()
            fields[key] = '' if value in ('>', '|', '>-', '|-') else value.strip().strip('"\'')
        elif key and line.startswith((' ', '\t')):
            fields[key] = (fields[key] + ' ' + line.strip()).strip()
    return fields


def command_groups(text):
    """[(group, [(signature, description)])] from the `Commands: GROUP` sections of `tack help`."""
    groups, current, entry = [], None, None
    for line in text.splitlines():
        heading = COMMANDS.match(line)
        if heading:
            current = (heading.group(1), [])
            groups.append(current)
            entry = None
        elif current is None or not line.strip():
            continue
        elif not line.startswith(' '):
            current, entry = None, None
        elif line.startswith('      ') and entry is not None:
            entry[1].append(line.strip())
        else:
            match = ENTRY.match(line)
            if match:
                entry = (match.group(1), [match.group(2)] if match.group(2) else [])
                current[1].append(entry)
    return [(name, [(signature, '\n'.join(lines)) for signature, lines in entries]) for name, entries in groups]


def options_text(text):
    """The help after the last command group: global and command options."""
    match = re.search(r'^Global options:.*', text, re.MULTILINE | re.DOTALL)
    return match.group(0).rstrip() if match else ''


def card(anchor, title, body, tags=()):
    badges = ''.join(f'<span class="tag">{esc(tag)}</span>' for tag in tags)
    return (f'<article class="card" id="{anchor}"><h3><a class="anchor" href="#{anchor}">{esc(title)}</a>'
            f'{badges}</h3>{body}</article>')


def page(anchor, title, body, lead=''):
    lead = f'<p class="lead">{lead}</p>' if lead else ''
    return f'<section class="page" id="{anchor}" data-title="{esc(title)}"><h1>{esc(title)}</h1>{lead}{body}</section>'


class Site:
    def __init__(self, root, help_text):
        self.root = Path(root)
        self.help = help_text
        self.sources, self.sets = tack_sets.load(self.root)
        self.pages, self.nav, self.index = [], [], []
        self.guides = self.guide_files()

    # --- shared pieces --------------------------------------------------------------------------
    def add(self, group, anchor, title, body, lead=''):
        self.pages.append(page(anchor, title, body, lead))
        self.nav.append((group, anchor, title))
        self.index.append({'id': anchor, 'title': title, 'group': group, 'text': ''})

    def entry(self, anchor, title, group, text):
        self.index.append({'id': anchor, 'title': title, 'group': group, 'text': text[:300]})

    def sets_of(self, kind, name):
        return [set_name for set_name, entry in self.sets.items()
                if any(item['kind'] == kind and item['name'] == name for item in entry['items'])]

    def set_links(self, names):
        if not names:
            return '<p class="muted">In no set.</p>'
        return '<p class="meta">Sets: ' + ', '.join(f'<a href="#set-{esc(n)}">{esc(n)}</a>' for n in names) + '</p>'

    def file_link(self, relative, label=None):
        path = (self.root / relative).resolve()
        return f'<a href="{esc(path.as_uri())}">{esc(label or relative)}</a>'

    # --- manual ---------------------------------------------------------------------------------
    def manual(self):
        text = (SITE / 'manual.html').read_text(encoding='utf-8')
        self.pages.append(text)
        for anchor, title in SECTION.findall(text):
            self.nav.append(('Manual', anchor, html.unescape(title)))
            self.index.append({'id': anchor, 'title': html.unescape(title), 'group': 'Manual', 'text': ''})

    # --- CLI reference --------------------------------------------------------------------------
    def cli(self):
        body = []
        for group, entries in command_groups(self.help):
            items = []
            for signature, description in entries:
                anchor = 'cmd-' + markdown_lite.slug(signature)
                lines = ''.join(f'<p>{esc(line)}</p>' for line in description.splitlines())
                items.append(f'<div class="command-entry" id="{anchor}"><code class="command">tack {esc(signature)}</code>{lines}</div>')
                self.entry(anchor, f'tack {signature}', 'CLI', description)
            body.append(f'<h2 id="cli-{markdown_lite.slug(group)}">{esc(group.capitalize())}</h2>' + ''.join(items))
        options = options_text(self.help)
        if options:
            body.append(f'<h2 id="cli-options">Options</h2><pre><code>{esc(options)}</code></pre>')
        self.add('Reference', 'cli', 'CLI reference', ''.join(body),
                 'Every <code>tack</code> command, from <code>tack help</code>. '
                 '<a href="#manual-cli">The CLI guide</a> shows them by task.')

    # --- sets -----------------------------------------------------------------------------------
    def item_html(self, item):
        kind, name = item['kind'], item['name']
        if kind == 'skill' and not item['source']:
            return f'<li><span class="kind">skill</span> <a href="#skill-{esc(name)}">{esc(name)}</a></li>'
        if kind == 'agent':
            return f'<li><span class="kind">agent</span> <a href="#agent-{esc(name)}">{esc(name)}</a></li>'
        if kind == 'plugin':
            return f'<li><span class="kind">plugin</span> <code>{esc(name)}</code> <span class="muted">Claude Code only</span></li>'
        url, commit = self.sources[item['source']]
        folder = tack_sets.skill_folder(item, self.sources, checkout=False)
        description = frontmatter(folder / 'SKILL.md').get('description', '')
        where = esc(item['source'])
        if url.startswith('https://github.com/'):
            path = '' if item['path'] == '.' else '/' + item['path']
            where = f'<a href="{esc((url[:-4] if url.endswith(".git") else url))}/tree/{esc(commit)}{esc(path)}">{where}</a>'
        text = esc(description) if description else '<span class="muted">Description not downloaded yet: activate the set to fetch it.</span>'
        self.entry(f'set-{item["set"]}', name, 'Skill', description)
        return (f'<li><span class="kind">skill</span> <strong>{esc(name)}</strong> '
                f'<span class="muted">from {where}</span><br>{text}</li>')

    def sets_pages(self):
        overview = []
        groups = tack_sets.by_category(self.sets)
        # Compatibility bundles repeat other sets, so they come last.
        ordered = sorted(groups.items(), key=lambda pair: pair[0] == tack_sets.COMPAT)
        for category, names in ordered:
            title = CATEGORIES.get(category, category.capitalize() or 'Other')
            anchor = 'sets-' + (category or 'other')
            cards = []
            for name in names:
                entry = self.sets[name]
                details = []
                if entry['asks']:
                    terms = ', '.join(f'<code>{esc(term.replace("+", " "))}</code>' for term in entry['asks'])
                    details.append(f'<p class="meta">Suggested when a request says: {terms}</p>')
                if entry['matches']:
                    rules = ', '.join(f'<code>{esc(rule)}</code>' + (f' ×{least}' if least > 1 else '')
                                      for rule, least in entry['matches'])
                    details.append(f'<p class="meta">Suggested for projects with: {rules}</p>')
                activate = ('<p class="meta">Always active.</p>' if name == tack_sets.ALWAYS else
                            f'<p class="meta">Activate: <code>tack set use {esc(name)}</code></p>')
                items = ''.join(self.item_html(dict(item, set=name)) for item in entry['items'])
                cards.append(card(f'set-{name}', name, f'<p>{esc(entry["about"])}</p>{activate}'
                                  f'{"".join(details)}<ul class="items">{items}</ul>'))
                self.entry(f'set-{name}', name, 'Set', entry['about'])
            overview.append(f'<li><a href="#{anchor}">{esc(title)}</a>: '
                            + ', '.join(f'<a href="#set-{esc(n)}">{esc(n)}</a>' for n in names) + '</li>')
            self.add('Sets', anchor, f'Sets: {title}', ''.join(cards))
        self.pages.insert(len(self.pages) - len(overview), page(
            'sets', 'Sets', f'<ul class="overview">{"".join(overview)}</ul>',
            'A set bundles skills, agents and plugins for one kind of work. Only active sets load, '
            'so each session carries what the project needs. <a href="#manual-sets">How to use sets</a>.'))
        self.nav.insert(len(self.nav) - len(overview), ('Sets', 'sets', 'All sets'))

    # --- skills and agents ----------------------------------------------------------------------
    def skills_page(self):
        cards = []
        for folder in sorted(path for path in (self.root / 'skills').iterdir() if (path / 'SKILL.md').is_file()):
            fields = frontmatter(folder / 'SKILL.md')
            body = (f'<p>{esc(fields.get("description"))}</p>{self.set_links(self.sets_of("skill", folder.name))}'
                    f'<p class="meta">Source: {self.file_link(f"skills/{folder.name}/SKILL.md")}</p>')
            cards.append(card(f'skill-{folder.name}', folder.name, body))
            self.entry(f'skill-{folder.name}', folder.name, 'Skill', fields.get('description', ''))
        self.add('Reference', 'skills', 'Skills', ''.join(cards),
                 'The skills of this repository. A skill loads its instructions only when a task needs them; '
                 'its description is what the assistant reads in every session of a project where its set is active. '
                 'Skills from external collections are listed in their <a href="#sets">sets</a>.')

    def agents_page(self):
        cards = []
        for path in sorted((self.root / 'agents').glob('*.md')):
            fields = frontmatter(path)
            tools = f'<p class="meta">Tools: {esc(fields["tools"])}</p>' if fields.get('tools') else ''
            body = (f'<p>{esc(fields.get("description"))}</p>{tools}{self.set_links(self.sets_of("agent", path.stem))}'
                    f'<p class="meta">Source: {self.file_link(f"agents/{path.name}")}</p>')
            cards.append(card(f'agent-{path.stem}', path.stem, body))
            self.entry(f'agent-{path.stem}', path.stem, 'Agent', fields.get('description', ''))
        self.add('Reference', 'agents', 'Agents', ''.join(cards),
                 'Specialist roles the assistant can hand work to. Each one comes with a set; '
                 'Codex and OpenCode receive generated copies.')

    # --- guides ---------------------------------------------------------------------------------
    def guide_files(self):
        """{resolved path: anchor} for README.md and docs/*.md; links to other files open the file."""
        found = {(self.root / 'README.md').resolve(): 'guide-overview'}
        for path in sorted((self.root / 'docs').glob('*.md')):
            found[path.resolve()] = 'guide-' + markdown_lite.slug(path.stem)
        return found

    def resolver(self, source):
        def link(target):
            if re.match(r'^[a-z]+:', target, re.IGNORECASE):
                return target
            path, _, fragment = target.partition('#')
            if not path:
                return f'#{self.guides[source]}-{markdown_lite.slug(fragment)}' if fragment else '#' + self.guides[source]
            resolved = (source.parent / path).resolve()
            if resolved in self.guides:
                anchor = self.guides[resolved]
                return f'#{anchor}-{markdown_lite.slug(fragment)}' if fragment else f'#{anchor}'
            return resolved.as_uri() if resolved.exists() else ''
        return link

    def guides_pages(self):
        for path, anchor in self.guides.items():
            if not path.is_file():
                continue
            text = path.read_text(encoding='utf-8')
            title_match = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else path.stem
            if anchor == 'guide-overview':
                title = 'Overview (README)'
            group = 'Guides'
            body = markdown_lite.render(text, prefix=anchor, link=self.resolver(path))
            relative = path.relative_to(self.root.resolve()).as_posix()
            self.pages.append(f'<section class="page guide" id="{anchor}" data-title="{esc(title)}">{body}'
                              f'<p class="source">Source: {self.file_link(relative)}</p></section>')
            self.nav.append((group, anchor, title))
            self.entry(anchor, title, group, re.sub(r'[#`*|>\[\]()_-]+', ' ', text)[:300])

    # --- page -----------------------------------------------------------------------------------
    def navigation(self):
        groups = {}
        for group, anchor, title in self.nav:
            groups.setdefault(group, []).append(f'<li><a href="#{anchor}">{esc(title)}</a></li>')
        return ''.join(f'<div class="nav-group"><p class="nav-title">{esc(group)}</p><ul>{"".join(items)}</ul></div>'
                       for group, items in groups.items())

    def render(self):
        self.manual()
        self.cli()
        self.sets_pages()
        self.skills_page()
        self.agents_page()
        self.guides_pages()
        index = json.dumps(self.index, ensure_ascii=False).replace('</', '<\\/')
        values = {'version': esc(version(self.root)), 'nav': self.navigation(),
                  'content': '\n'.join(self.pages), 'index': index}
        template = (SITE / 'template.html').read_text(encoding='utf-8')
        # One pass over the template, so text inside the content is never taken for a placeholder.
        return re.sub(r'\{\{(\w+)\}\}', lambda match: values[match.group(1)], template)


def version(root):
    result = subprocess.run(['git', '-C', str(root), 'describe', '--tags', '--always'],
                            capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else ''


def build(root, help_text):
    return Site(root, help_text).render()


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__.strip().splitlines()[-1])
    root, output = Path(sys.argv[1]), Path(sys.argv[2])
    try:
        text = build(root, sys.stdin.read())
    except tack_sets.Fail as error:
        sys.exit(f'tack docs: {error}')
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.tmp')
    temporary.write_text(text, encoding='utf-8')
    os.replace(temporary, output)


if __name__ == '__main__':
    main()
