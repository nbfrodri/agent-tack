#!/usr/bin/env python3
"""Optional collaborator setup. Run with Python from Bash (Git Bash on Windows)."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import urlsplit


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate recipe key: ' + key)
        result[key] = value
    return result


def validate_recipe(data):
    if not isinstance(data, dict) or set(data) != {'version', 'source', 'revision'}:
        raise ValueError('Expected only version, source and revision in the recipe')
    if type(data['version']) is not int or data['version'] != 1:
        raise ValueError('Unsupported installation recipe version')
    source = data['source']
    if not isinstance(source, str) or len(source) > 2048 or any(c.isspace() or ord(c) < 32 for c in source):
        raise ValueError('Expected a bounded repository URL')
    parsed = urlsplit(source)
    https = (parsed.scheme == 'https' and parsed.hostname and parsed.path not in ('', '/')
             and parsed.username is None and parsed.password is None and not parsed.query and not parsed.fragment)
    ssh = bool(re.fullmatch(r'git@[A-Za-z0-9.-]+:[A-Za-z0-9_./-]+', source))
    if not https and not ssh:
        raise ValueError('Use a credential-free HTTPS URL or git@host:path source')
    if not isinstance(data['revision'], str) or not re.fullmatch(r'[0-9a-f]{40}', data['revision']):
        raise ValueError('Use a full lowercase 40-character Git commit, not a moving branch or tag')
    return data


def native_path(value):
    # Native Python cannot interpret MSYS /c/... and /tmp/... spellings.
    if os.name == 'nt' and str(value).startswith('/') and shutil.which('cygpath'):
        value = subprocess.check_output(['cygpath', '-m', str(value)], text=True, encoding='utf-8').strip()
    return Path(value)


def no_symlinks(path, boundary):
    if not path.is_relative_to(boundary):
        raise ValueError('Path leaves the selected directory')
    for part in (path, *path.parents):
        if part == boundary:
            break
        if part.is_symlink() or getattr(part, 'is_junction', lambda: False)():
            raise ValueError('Symlink or junction path left untouched: ' + str(part))


def git(arguments, cwd, env):
    result = subprocess.run(['git', *arguments], cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180)
    if result.returncode:
        raise ValueError('Git operation failed; checkout preserved for review: ' + result.stderr[-1200:].strip())
    return result.stdout.strip()


def existing_installation(home):
    found = shutil.which('tack')
    for path in ([Path(found)] if found else []) + [home / '.local/bin/tack', home / '.agents/tack']:
        if path.exists() or path.is_symlink():
            return path
    return None


def checkout(recipe, directory, env):
    no_symlinks(directory, directory.parents[3])
    if not directory.exists():
        directory.parent.mkdir(parents=True, exist_ok=True)
        directory.mkdir()  # exclusive: never overwrite an existing checkout
        git(['init', '-q', '--template='], directory, env)
        git(['config', 'core.hooksPath', str(directory / '.disabled-hooks')], directory, env)
        git(['remote', 'add', 'origin', recipe['source']], directory, env)
        git(['fetch', '--depth=1', '--no-tags', '--no-recurse-submodules', 'origin', recipe['revision']], directory, env)
        git(['checkout', '--detach', recipe['revision']], directory, env)
    if not directory.is_dir() or not (directory / '.git').is_dir() or (directory / '.git').is_symlink():
        raise ValueError('Unexpected checkout; left untouched: ' + str(directory))
    if git(['rev-parse', 'HEAD'], directory, env) != recipe['revision']:
        raise ValueError('Cached checkout revision differs; left untouched: ' + str(directory))
    if git(['config', '--get', 'remote.origin.url'], directory, env) != recipe['source']:
        raise ValueError('Cached checkout source differs; left untouched: ' + str(directory))
    if git(['status', '--porcelain', '--untracked-files=all'], directory, env):
        raise ValueError('Cached checkout has local changes; left untouched: ' + str(directory))
    for name in ('install.sh', 'bin/tack'):
        path = directory / name
        no_symlinks(path, directory)
        if not path.is_file():
            raise ValueError('Selected revision lacks a regular ' + name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true', help='describe setup without downloads or changes')
    parser.add_argument('--yes', action='store_true', help='explicitly approve installation without a prompt')
    args = parser.parse_args()
    recipe_path = Path(__file__).resolve().with_name('tack-install.json')
    if recipe_path.is_symlink() or not recipe_path.is_file() or recipe_path.stat().st_size > 8192:
        raise ValueError('Expected a regular tack-install.json recipe of at most 8 KiB')
    recipe = validate_recipe(json.loads(recipe_path.read_text(encoding='utf-8'), object_pairs_hook=unique_object))
    home = Path.home().resolve()
    print('Requested tack source: ' + recipe['source'])
    print('Pinned revision: ' + recipe['revision'])
    existing = existing_installation(home)
    if existing:
        print('Existing tack installation kept unchanged: ' + str(existing))
        print('The requested revision has not been enforced. Check your installation with tack doctor;')
        print('review its source/version before using it with this project. No upgrade or replacement was made.')
        return 0
    data = native_path(os.environ.get('XDG_DATA_HOME', str(home / '.local/share')))
    if not data.is_absolute():
        raise ValueError('XDG_DATA_HOME must be an absolute path')
    data = data.absolute()
    no_symlinks(data, Path(data.anchor))
    directory = data / 'agent-tack/bootstrap' / hashlib.sha256(recipe['source'].encode()).hexdigest()[:16] / recipe['revision']
    print('Persistent checkout: ' + str(directory))
    print('Installation configures this user\'s AI tools and Git hooks; optional plugins are excluded.')
    print('Project preferences, activation and execution trust are not changed.')
    if args.dry_run:
        print('Preview only: no downloads, installation or writes.')
        return 0
    if not args.yes:
        if not sys.stdin.isatty():
            raise ValueError('Installation needs consent; run interactively or select --yes explicitly')
        if input('Download and install this revision? [y/N] ').strip().lower() not in ('y', 'yes'):
            print('Installation declined; no changes made.')
            return 0
    if not shutil.which('git') or not shutil.which('bash'):
        raise ValueError('Git and Bash are required; use Git Bash on Windows')
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GIT_LFS_SKIP_SMUDGE='1')
    checkout(recipe, directory, env)
    result = subprocess.run(['bash', (directory / 'install.sh').as_posix(), '--skip-plugins'],
                            cwd=directory, env=env, timeout=600)
    if result.returncode:
        raise ValueError(f'Installer exited {result.returncode}. Checkout preserved at {directory}; inspect and rerun its installer to repair.')
    print('Installed. Keep the checkout; installed files link to it. Start a new shell/AI session if needed.')
    print('Next: tack doctor, tack status and tack verify --plan. Grant local trust separately after review.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.SubprocessError, EOFError) as error:
        print('tack bootstrap: ' + str(error), file=sys.stderr)
        raise SystemExit(2)
