#!/usr/bin/env python3
"""Create optional local notes without overwriting files or changing tracked history."""
import argparse
from pathlib import Path
import stat
import subprocess


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True,
                          text=True, encoding='utf-8', timeout=10).stdout.strip()


def check_path(path):
    for parent in (path, *path.parents):
        if parent.is_symlink() or (parent.exists() and
                getattr(parent.lstat(), 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
            raise ValueError(f'linked path is not supported: {parent}')


def prepare(root, shared=False, preview=False):
    root = root.absolute()
    check_path(root)
    if Path(git(root, 'rev-parse', '--show-toplevel')).resolve() != root.resolve():
        raise ValueError('select the repository root')
    if git(root, 'ls-files', '--', '.private'):
        raise ValueError('.private contains tracked files; review them manually before setup')
    notes = root / '.private' / 'tack'
    ignore = root / '.gitignore' if shared else Path(git(root, 'rev-parse', '--path-format=absolute', '--git-path', 'info/exclude'))
    for path in (notes, ignore):
        check_path(path)
    for path in (notes.parent, notes):
        if path.exists() and not path.is_dir():
            raise ValueError(f'notes destination is not a directory: {path}')
    if ignore.exists() and (not ignore.is_file() or ignore.stat().st_size > 131072):
        raise ValueError('ignore destination must be a regular file at most 128 KiB')
    before = ignore.read_bytes() if ignore.exists() else b''
    rule = b'/.private/'
    # Append even if an earlier identical rule is followed by an exception.
    needs_rule = not before.splitlines() or before.splitlines()[-1].strip() != rule
    report = dict(notes=str(notes), ignore=str(ignore), append_rule=needs_rule, preview=preview)
    if preview:
        return report
    ignore.parent.mkdir(parents=True, exist_ok=True)
    if needs_rule:
        with ignore.open('ab') as stream:
            stream.write((b'\n' if before and not before.endswith(b'\n') else b'') + rule + b'\n')
    ignored = subprocess.run(['git', '-C', str(root), 'check-ignore', '--quiet', '--', '.private/'],
                             capture_output=True, timeout=10)
    if ignored.returncode:
        raise ValueError('Git does not ignore .private/; review overriding rules or use --shared-ignore')
    notes.mkdir(parents=True, exist_ok=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path, nargs='?', default=Path.cwd())
    parser.add_argument('--shared-ignore', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        report = prepare(args.root, args.shared_ignore, args.dry_run)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        parser.exit(1, f'private notes: {error}\n')
    print(('Would prepare' if report['preview'] else 'Prepared') + ' ' + report['notes'])
    print('Ignore location: ' + report['ignore'])
    print('Local notes only; keep shared contracts and decisions in versioned project documentation.')


if __name__ == '__main__':
    main()
