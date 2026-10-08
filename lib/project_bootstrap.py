#!/usr/bin/env python3
"""Prepare an optional, standalone collaborator setup without installing anything."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

from project_config import relative_path

SOURCE = Path(__file__).resolve().parent.parent
ASSET = SOURCE / 'skills/new-project/assets/setup-tack.py'
SPEC = importlib.util.spec_from_file_location('bootstrap_asset', ASSET)
bootstrap = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bootstrap)


def source_git(*args):
    result = subprocess.run(['git', '-C', str(SOURCE), *args], capture_output=True,
                            text=True, encoding='utf-8', errors='replace', timeout=10)
    if result.returncode:
        raise ValueError('Cannot infer the tack source; provide --source URL and --revision COMMIT')
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--source')
    parser.add_argument('--revision')
    parser.add_argument('--directory', default='scripts')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if args.source and not args.revision:
        raise ValueError('An explicit --source also needs --revision COMMIT')
    root = bootstrap.native_path(args.root).resolve()
    if not relative_path(args.directory):
        raise ValueError('Use a safe project-relative setup directory')
    directory = root / args.directory
    bootstrap.no_symlinks(directory, root)
    if directory.exists() and not directory.is_dir():
        raise ValueError('Setup destination is not a directory')
    recipe = bootstrap.validate_recipe({'version': 1, 'source': args.source or source_git('remote', 'get-url', 'origin'),
                                        'revision': args.revision or source_git('rev-parse', 'HEAD')})
    files = {directory / 'setup-tack.py': ASSET.read_bytes(),
             directory / 'tack-install.json': (json.dumps(recipe, indent=2) + '\n').encode()}
    for path in files:
        bootstrap.no_symlinks(path, root)
        if path.exists():
            raise ValueError('Existing setup file left untouched: ' + str(path.relative_to(root)))
    for path in files:
        print(('Would create ' if args.dry_run else 'Create ') + str(path.relative_to(root)))
    print('Source: ' + recipe['source'] + ' @ ' + recipe['revision'])
    if args.dry_run:
        return 0
    directory.mkdir(parents=True, exist_ok=True)
    for path, content in files.items():
        with path.open('xb') as stream:
            stream.write(content)
    print('Review and commit these files. Collaborators run: python3 ' + args.directory + '/setup-tack.py')
    print('This generated setup files only; it did not install, activate or trust tack.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print('tack bootstrap: ' + str(error), file=sys.stderr)
        raise SystemExit(2)
