#!/usr/bin/env python3
"""Check local Markdown links and images in human docs, including heading fragments.

Code fences and external URLs are skipped. This is a repository check, not a general
Markdown parser or a network availability test.
"""
import html
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


def prose(text):
    result, fence = [], None
    for line in text.splitlines():
        match = re.match(r'^\s*(`{3,}|~{3,})', line)
        if match:
            token = match[1]
            if fence is None:
                fence = token[0]
            elif token[0] == fence:
                fence = None
            result.append('')
        else:
            result.append(line if fence is None else '')
    return '\n'.join(result)


def anchors(text):
    found, counts = set(), {}
    for title in re.findall(r'^#{1,6}\s+(.+?)(?:\s+#+)?$', prose(text), re.M):
        title = re.sub(r'<[^>]*>', '', title)
        title = re.sub(r'\[([^]]+)\]\([^)]*\)', r'\1', title)
        slug = re.sub(r'[^\w\- ]', '', html.unescape(title).lower()).replace(' ', '-')
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        found.add(slug + (f'-{count}' if count else ''))
    found.update(re.findall(r'\b(?:id|name)=["\']([^"\']+)', text))
    return found


def check(root):
    files = [root / 'README.md', *(root / 'docs').rglob('*.md')]
    errors, checked = [], 0
    for path in files:
        if not path.is_file():
            errors.append(f'{path.relative_to(root)}: missing document')
            continue
        content = prose(path.read_text(encoding='utf-8'))
        targets = re.findall(r'\[[^]\n]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+"[^"]*")?\s*\)', content)
        targets += re.findall(r'\b(?:src|href)=["\']([^"\']+)', content)
        for raw in targets:
            target = html.unescape(raw.strip('<>'))
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or target.startswith('/'):
                continue
            destination = path.parent / unquote(parsed.path) if parsed.path else path
            checked += 1
            if not destination.resolve().is_relative_to(root) or not destination.exists():
                errors.append(f'{path.relative_to(root)}: missing local target {target}')
            elif parsed.fragment and destination.suffix == '.md':
                if unquote(parsed.fragment) not in anchors(destination.read_text(encoding='utf-8')):
                    errors.append(f'{path.relative_to(root)}: missing heading {target}')
    return errors, checked


if __name__ == '__main__':
    findings, count = check(Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1])
    for finding in findings:
        print(finding)
    print(f'Documentation: {count} local links checked; {len(findings)} error(s)')
    sys.exit(bool(findings))
