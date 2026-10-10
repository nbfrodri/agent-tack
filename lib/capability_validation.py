#!/usr/bin/env python3
"""Read-only validation shared by the catalog and project-local skills and roles."""
import argparse
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

NAME = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')


def definition(path, expected, limit):
    errors, fields = [], {}
    try:
        text = path.read_text(encoding='utf-8')
    except (OSError, UnicodeError) as error:
        return [f'{path}: cannot read definition: {error}'], fields
    if not text.startswith('---\n'):
        return [f'{path}: missing frontmatter'], fields
    header, separator, body = text[4:].partition('\n---\n')
    if not separator:
        return [f'{path}: frontmatter is not closed with ---'], fields
    for line in header.splitlines():
        key, sep, value = line.partition(': ')
        if sep:
            if key in fields:
                errors.append(f'{path}: duplicate field {key}')
            fields[key] = value.strip()
    name, description = fields.get('name', ''), fields.get('description', '')
    if name != expected:
        errors.append(f"{path}: name '{name}' should be '{expected}'")
    if not NAME.fullmatch(name) or len(name) > 63:
        errors.append(f'{path}: name must be lowercase letters, digits and hyphens (under 64 characters)')
    if not description:
        errors.append(f'{path}: missing description')
    elif description.startswith(('>', '|')):
        errors.append(f'{path}: description must be on a single line')
    elif ': ' in description and not (description[0] == description[-1] == '"'):
        # Strict YAML readers reject a plain value holding ": " and skip the whole definition.
        errors.append(f'{path}: quote the description, or drop its ": " (strict YAML readers reject it)')
    if len(description) > limit:
        errors.append(f'{path}: description is {len(description)} chars (max {limit})')
    if not body.strip():
        errors.append(f'{path}: missing instructions')
    return errors, fields


def inside(path, root):
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (ValueError, OSError, RuntimeError):
        return False


def references(path, root):
    errors = []
    text = path.read_text(encoding='utf-8')
    targets = re.findall(r'\[[^\]]*\]\(([^)]+)\)', text)
    targets += re.findall(r'`((?:references|scripts|assets)/[^`<>]+)`', text)
    for target in targets:
        target = target.strip().strip('<>')
        parsed = urlsplit(target)
        if parsed.scheme in ('http', 'https', 'mailto') or not parsed.path:
            continue
        candidate = path.parent / unquote(parsed.path)
        if parsed.scheme or not inside(candidate, root):
            errors.append(f'{path}: reference outside project: {target}')
        elif not candidate.exists():
            errors.append(f'{path}: missing reference: {target}')
    return errors


def project(root, skills_dir='.agents/skills', agents_dir='.agents/agents'):
    root = Path(root).resolve()
    errors, definitions, total = [], [], 0
    for folder in (root / skills_dir, root / agents_dir):
        if not inside(folder, root):
            errors.append(f'{folder}: capability directory outside project')
    if errors:
        return errors
    for folder in sorted((root / skills_dir).glob('*')):
        if folder.is_dir():
            definitions.append((folder / 'SKILL.md', folder.name, 400))
    definitions += [(p, p.stem, 300) for p in sorted((root / agents_dir).glob('*.md'))]
    index_path = root / 'AGENTS.md'
    if index_path.exists() and not inside(index_path, root):
        return [f'{index_path}: instruction index outside project']
    index = index_path.read_text(encoding='utf-8') if index_path.exists() else ''
    for path, expected, limit in definitions:
        if not inside(path, root):
            errors.append(f'{path}: definition outside project')
            continue
        issues, fields = definition(path, expected, limit)
        errors.extend(issues)
        total += len(fields.get('description', ''))
        if path.relative_to(root).as_posix() not in index:
            errors.append(f'{path}: add its path and trigger to AGENTS.md for discovery')
        if not issues:
            errors.extend(references(path, root))
            if path.name == 'SKILL.md':
                for reference in sorted(path.parent.glob('references/**/*.md')):
                    if inside(reference, root):
                        errors.extend(references(reference, root))
                    else:
                        errors.append(f'{reference}: reference outside project')
    if total > 6000:
        errors.append(f'project capability descriptions total {total} chars (max 6000)')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    one = commands.add_parser('file')
    one.add_argument('path', type=Path)
    one.add_argument('name')
    one.add_argument('limit', type=int)
    local = commands.add_parser('project')
    local.add_argument('root', type=Path)
    local.add_argument('--skills-dir', default='.agents/skills')
    local.add_argument('--agents-dir', default='.agents/agents')
    args = parser.parse_args()
    if args.command == 'file':
        errors, _ = definition(args.path, args.name, args.limit)
    else:
        if not args.root.is_dir():
            parser.error('project root must exist')
        errors = project(args.root, args.skills_dir, args.agents_dir)
    for error in errors:
        print(error)
    return int(bool(errors))


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, UnicodeError, ValueError) as error:
        sys.exit(f'capability validation: {error}')
