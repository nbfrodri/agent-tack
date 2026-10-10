#!/usr/bin/env python3
"""Named sets of skills, agents and Claude plugins.

sets.txt declares each set; sources.txt pins the external repositories some skills come from to a
full commit. A set is active everywhere (git config --global tack.sets, applied by install.sh) or
in one project (local tack.sets, linked into that clone by `tack set use`). `tack set` and the
installer call this module; lib/sets.sh reads the same files for what needs no checkout.
"""
import argparse
import filecmp
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

NAME = re.compile(r'^[a-z0-9][a-z0-9-]*$')
SKILL = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*$')
COMMIT = re.compile(r'^[0-9a-f]{40}$')
PLUGIN = re.compile(r'^[A-Za-z0-9._-]+@[A-Za-z0-9._-]+$')
URL = re.compile(r'^https://[A-Za-z0-9._~/@:-]+$')
# Where a project's tools look for skills: the open standard folder and Claude Code's own.
PROJECT_SKILLS = ('.agents/skills', '.claude/skills')
PROJECT_AGENTS = '.claude/agents'


class Fail(Exception):
    pass


def store():
    base = os.environ.get('XDG_DATA_HOME') or os.path.join(os.path.expanduser('~'), '.local', 'share')
    return Path(base) / 'agent-tack' / 'sources'


def rows(path):
    if not path.is_file():
        return
    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        line = line.split('#', 1)[0].strip()
        if line:
            yield number, line.split()


def read_sources(root, errors):
    sources = {}
    for number, fields in rows(root / 'sources.txt'):
        where = f'sources.txt:{number}'
        if len(fields) != 3:
            errors.append(f'{where}: expected name, url and commit')
            continue
        name, url, commit = fields
        if not NAME.match(name):
            errors.append(f'{where}: source name {name!r} must be lowercase letters, digits and hyphens')
        elif name in sources:
            errors.append(f'{where}: source {name!r} is declared twice')
        elif not (URL.match(url) or (os.path.isabs(url) and not url.startswith('-'))):
            errors.append(f'{where}: {name} needs an https URL or an absolute path')
        elif not COMMIT.match(commit):
            errors.append(f'{where}: {name} must be pinned to a full 40-character commit')
        else:
            sources[name] = (url, commit)
    return sources


def read_sets(root, sources, errors):
    """Returns {set: {'about': text, 'items': [item]}}; an item is a dict with kind, ref and name."""
    sets, owners = {}, {}
    for number, fields in rows(root / 'sets.txt'):
        where = f'sets.txt:{number}'
        if len(fields) < 3:
            errors.append(f'{where}: expected set, kind and item')
            continue
        name, kind, ref = fields[0], fields[1], fields[2]
        if not NAME.match(name):
            errors.append(f'{where}: set name {name!r} must be lowercase letters, digits and hyphens')
            continue
        entry = sets.setdefault(name, {'about': '', 'items': []})
        if kind == 'about':
            entry['about'] = ' '.join(fields[2:])
            continue
        if len(fields) != 3:
            errors.append(f'{where}: unexpected text after {ref!r}')
            continue
        item = {'kind': kind, 'ref': ref, 'name': ref, 'source': None, 'path': None}
        if kind == 'skill' and ':' in ref:
            source, path = ref.split(':', 1)
            parts = path.split('/')
            if source not in sources:
                errors.append(f'{where}: source {source!r} is not in sources.txt')
                continue
            if path.startswith('/') or '\\' in path or any(part in ('', '.', '..') for part in parts) \
                    or not SKILL.match(parts[-1]):
                errors.append(f'{where}: {ref!r} needs a plain relative path to the skill folder')
                continue
            item.update(name=parts[-1], source=source, path=path)
            if (root / 'skills' / item['name']).exists():
                errors.append(f'{where}: {ref!r} has the same name as skills/{item["name"]}')
                continue
        elif kind == 'skill':
            if not SKILL.match(ref) or not (root / 'skills' / ref / 'SKILL.md').is_file():
                errors.append(f'{where}: there is no skills/{ref}/SKILL.md')
                continue
        elif kind == 'agent':
            if not SKILL.match(ref) or not (root / 'agents' / f'{ref}.md').is_file():
                errors.append(f'{where}: there is no agents/{ref}.md')
                continue
        elif kind == 'plugin':
            if not PLUGIN.match(ref):
                errors.append(f'{where}: {ref!r} should be plugin@marketplace')
                continue
        else:
            errors.append(f'{where}: unknown kind {kind!r} (about, skill, agent or plugin)')
            continue
        owner = owners.setdefault((kind, item['name']), ref)
        if owner != ref:
            errors.append(f'{where}: {ref!r} and {owner!r} would install under the same name')
            continue
        if item not in entry['items']:
            entry['items'].append(item)
    return sets


def load(root):
    errors = []
    sources = read_sources(root, errors)
    sets = read_sets(root, sources, errors)
    if errors:
        raise Fail('\n'.join(errors))
    return sources, sets


def git(*args, cwd=None):
    """Runs git without hooks or prompts; returns (exit code, stdout, stderr)."""
    env = {key: value for key, value in os.environ.items()
           if key not in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE')}
    env['GIT_TERMINAL_PROMPT'] = '0'
    result = subprocess.run(['git', '-c', f'core.hooksPath={os.devnull}', *args], cwd=cwd, env=env,
                            capture_output=True, text=True, encoding='utf-8', errors='replace')
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def fetch(name, url, commit):
    """Checks SOURCE out at its pinned commit, once, and returns the checkout."""
    dest = store() / name / commit
    if dest.is_dir():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=f'{commit[:12]}.', dir=dest.parent))
    try:
        steps = [('init', '-q'), ('remote', 'add', 'origin', url)]
        for step in steps:
            code, _, err = git(*step, cwd=work)
            if code:
                raise Fail(f'cannot fetch {name}: {err}')
        # A host that refuses a single commit still serves its branches.
        if git('fetch', '-q', '--depth', '1', 'origin', commit, cwd=work)[0]:
            git('fetch', '-q', 'origin', cwd=work)
        code, _, err = git('-c', 'advice.detachedHead=false', 'checkout', '-q', '--detach', commit, cwd=work)
        if code or git('rev-parse', 'HEAD', cwd=work)[1] != commit:
            raise Fail(f'cannot fetch {name} at {commit}: {err or "the commit is not in " + url}')
        try:
            work.rename(dest)
        except OSError:
            if not dest.is_dir():
                raise
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return dest


def skill_folder(item, sources, checkout=True):
    url, commit = sources[item['source']]
    if not checkout:
        return store() / item['source'] / commit / item['path']
    base = fetch(item['source'], url, commit)
    folder = base / item['path']
    inside = base.resolve()
    for path in (folder, folder / 'SKILL.md'):
        real = path.resolve()
        if real != inside and inside not in real.parents:
            raise Fail(f'{item["ref"]} points outside the checkout of {item["source"]}')
    if not (folder / 'SKILL.md').is_file():
        raise Fail(f'{item["ref"]} has no SKILL.md at {commit[:12]}')
    return folder


def resolve(root, names, sources, sets, checkout=True):
    """The items of the named sets, once each, with the file or folder each one installs from."""
    found, seen = [], set()
    for name in names:
        for item in sets[name]['items']:
            key = (item['kind'], item['name'])
            if key in seen:
                continue
            seen.add(key)
            target = None
            if item['kind'] == 'skill':
                target = skill_folder(item, sources, checkout) if item['source'] else root / 'skills' / item['name']
            elif item['kind'] == 'agent':
                target = root / 'agents' / f'{item["name"]}.md'
            found.append(dict(item, target=target))
    return found


def active(scope, sets, cwd=None):
    code, out, _ = git('config', f'--{scope}', '--get', 'tack.sets', cwd=cwd)
    names = [name.strip() for name in out.split(',') if name.strip()] if code == 0 else []
    for name in names:
        if name not in sets:
            print(f'tack: the {scope} set {name!r} is not in sets.txt; ignored', file=sys.stderr)
    return [name for name in names if name in sets]


def remember(scope, names, cwd=None):
    if names:
        code, _, err = git('config', f'--{scope}', 'tack.sets', ','.join(names), cwd=cwd)
    else:
        code, _, err = git('config', f'--{scope}', '--unset-all', 'tack.sets', cwd=cwd)
        code = 0 if code == 5 else code
    if code:
        raise Fail(f'cannot save the {scope} sets: {err}')


def project_root():
    code, out, _ = git('rev-parse', '--show-toplevel')
    if code or not out:
        print('tack: not inside a git repository (use --global for every project)', file=sys.stderr)
        sys.exit(2)
    return Path(out)


def ours(link, root):
    target = os.readlink(link)
    return any(target.startswith(f'{base}{os.sep}') for base in (store(), root / 'skills', root / 'agents'))


def claude_plugin(action, plugin, repo):
    if not shutil.which('claude'):
        print(f'  plugin {plugin}: claude not found; run claude plugin {action} {plugin} --scope local')
        return
    result = subprocess.run(['claude', 'plugin', action, plugin, '--scope', 'local'], cwd=repo,
                            stdin=subprocess.DEVNULL, capture_output=True, text=True)
    done = 'installed' if action == 'install' else 'removed'
    print(f'  plugin {plugin}: {done if result.returncode == 0 else "could not " + action} (Claude Code only)')


def apply_project(root, repo, sources, sets, wanted, dropped_plugins=()):
    """Links the project's sets into this clone and removes links no remaining set needs."""
    everywhere = {(item['kind'], item['name']) for item in resolve(root, active('global', sets), sources, sets, False)}
    items = [item for item in wanted if (item['kind'], item['name']) not in everywhere]
    links = {}
    for item in items:
        if item['kind'] == 'skill':
            for folder in PROJECT_SKILLS:
                links[repo / folder / item['name']] = item['target']
        elif item['kind'] == 'agent':
            links[repo / PROJECT_AGENTS / f'{item["name"]}.md'] = item['target']
    for folder in (*PROJECT_SKILLS, PROJECT_AGENTS):
        if (repo / folder).is_dir():
            for entry in sorted((repo / folder).iterdir()):
                if entry.is_symlink() and ours(entry, root) and entry not in links:
                    entry.unlink()
                    print(f'  removed {entry.relative_to(repo)}')
    for dest, target in links.items():
        if dest.is_symlink() and ours(dest, root):
            if os.readlink(dest) == str(target):
                continue
            dest.unlink()
        elif dest.is_symlink() or dest.exists():
            print(f'  kept {dest.relative_to(repo)}: the project already has it')
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(target, dest)
        print(f'  linked {dest.relative_to(repo)}')
    exclude(repo, [f'/{dest.relative_to(repo).as_posix()}' for dest in links])
    for plugin in dropped_plugins:
        claude_plugin('uninstall', plugin, repo)
    for item in items:
        if item['kind'] == 'plugin':
            claude_plugin('install', item['name'], repo)


def exclude(repo, lines):
    """Keeps the links out of the project's history without touching its .gitignore."""
    code, out, _ = git('rev-parse', '--git-path', 'info/exclude', cwd=repo)
    if code or not lines:
        return
    path = (repo / out) if not os.path.isabs(out) else Path(out)
    existing = path.read_text(encoding='utf-8') if path.is_file() else ''
    missing = [line for line in lines if line not in existing.splitlines()]
    if missing:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(existing + ('' if existing.endswith('\n') or not existing else '\n')
                        + '\n'.join(missing) + '\n', encoding='utf-8')


def plugins_of(names, sets):
    return {item['name'] for name in names for item in sets[name]['items'] if item['kind'] == 'plugin'}


def command_list(args, root, sources, sets):
    code, top, _ = git('rev-parse', '--show-toplevel')
    here = active('local', sets) if code == 0 and top else []
    everywhere = active('global', sets)
    print('Sets in sets.txt (* active everywhere, + active in this project):')
    for name, entry in sets.items():
        mark = '*' if name in everywhere else '+' if name in here else ' '
        totals = [(sum(item['kind'] == kind for item in entry['items']), kind) for kind in ('skill', 'agent', 'plugin')]
        counts = ', '.join(f'{total} {kind}{"" if total == 1 else "s"}' for total, kind in totals if total)
        print(f'{mark} {name:<14} {entry["about"]}  ({counts})')


def command_show(args, root, sources, sets):
    known(args.name, sets)
    print(f'{args.name}: {sets[args.name]["about"]}')
    for item in sets[args.name]['items']:
        print(f'  {item["kind"]:<7} {item["ref"]}')


def known(name, sets):
    if name not in sets:
        raise Fail(f'unknown set {name!r} (see tack set list)')


def command_use(args, root, sources, sets):
    known(args.name, sets)
    scope = 'global' if args.everywhere else 'local'
    repo = None if args.everywhere else project_root()
    names = active(scope, sets, repo)
    names = names if args.name in names else [*names, args.name]
    if args.everywhere:
        remember('global', names)
        print(f'{args.name} is active everywhere after the next install: run {root / "install.sh"}')
        return
    wanted = resolve(root, names, sources, sets)
    remember('local', names, repo)
    print(f'{args.name} is active in {repo}')
    apply_project(root, repo, sources, sets, wanted)


def command_drop(args, root, sources, sets):
    known(args.name, sets)
    scope = 'global' if args.everywhere else 'local'
    repo = None if args.everywhere else project_root()
    before = active(scope, sets, repo)
    names = [name for name in before if name != args.name]
    remember(scope, names, repo)
    if args.everywhere:
        print(f'{args.name} is no longer active everywhere after the next install: run {root / "install.sh"}')
        return
    print(f'{args.name} is no longer active in {repo}')
    dropped = plugins_of(before, sets) - plugins_of(names, sets)
    apply_project(root, repo, sources, sets, resolve(root, names, sources, sets), sorted(dropped))


def command_sync(args, root, sources, sets):
    repo = project_root()
    apply_project(root, repo, sources, sets, resolve(root, active('local', sets, repo), sources, sets))
    print(f'Project sets are in place in {repo}')


def command_plan(args, root, sources, sets):
    for item in resolve(root, active('global', sets), sources, sets, not args.no_fetch):
        if item['kind'] == 'skill' and item['source']:
            print(f'{item["name"]}\t{item["target"]}')


def command_check(args, root, sources, sets):
    names = list(sets)
    if args.fetch:
        resolve(root, names, sources, sets)
    print(f'{len(sets)} sets and {len(sources)} sources are valid' + (' and present upstream' if args.fetch else ''))


def same_tree(left, right):
    if not left.is_dir() or not right.is_dir():
        return False
    compared = filecmp.dircmp(left, right)
    if compared.left_only or compared.right_only or compared.funny_files:
        return False
    _, mismatch, errors = filecmp.cmpfiles(left, right, compared.common_files, shallow=False)
    return not mismatch and not errors and all(same_tree(left / name, right / name) for name in compared.common_dirs)


def command_update(args, root, sources, sets):
    for name in args.sources:
        if name not in sources:
            raise Fail(f'unknown source {name!r} (see sources.txt)')
    path, moved, failed = root / 'sources.txt', 0, 0
    text = path.read_text(encoding='utf-8')
    for name in args.sources or sorted(sources):
        url, pinned = sources[name]
        code, out, err = git('ls-remote', url, 'HEAD')
        latest = out.split()[0] if code == 0 and out else ''
        if not COMMIT.match(latest):
            print(f'{name}: cannot read the upstream head: {err or "no HEAD"}')
            failed += 1
            continue
        if latest == pinned:
            print(f'{name}: up to date at {pinned[:12]}')
            continue
        old, new = fetch(name, url, pinned), fetch(name, url, latest)
        used = sorted({item['path'] for entry in sets.values() for item in entry['items'] if item['source'] == name})
        gone = [item for item in used if not (new / item / 'SKILL.md').is_file()]
        if gone:
            print(f'{name}: kept at {pinned[:12]}; {latest[:12]} no longer has ' + ', '.join(gone))
            failed += 1
            continue
        print(f'{name}: {pinned[:12]} -> {latest[:12]}')
        for item in used:
            if not same_tree(old / item, new / item):
                print(f'  changed: {name}:{item}  (diff -ru {old / item} {new / item})')
        text = re.sub(rf'(?m)^(\s*{re.escape(name)}\s+\S+\s+){pinned}', rf'\g<1>{latest}', text)
        moved += 1
    if moved:
        path.write_text(text, encoding='utf-8')
        print(f'Updated {moved} pin(s) in {path}. Review the changes, commit, then run install.sh and tack set sync.')
    if failed:
        raise Fail(f'{failed} source(s) were not updated')


def main():
    parser = argparse.ArgumentParser(prog='tack set', description='Named sets of skills, agents and plugins.')
    parser.add_argument('--root', required=True, type=Path, help=argparse.SUPPRESS)
    commands = parser.add_subparsers(dest='command')
    commands.add_parser('list', help='every set and where it is active (default)').set_defaults(run=command_list)
    show = commands.add_parser('show', help='what a set contains')
    show.add_argument('name')
    show.set_defaults(run=command_show)
    for name, run, text in (('use', command_use, 'activate a set in this project, or everywhere with --global'),
                            ('drop', command_drop, 'deactivate a set')):
        sub = commands.add_parser(name, help=text)
        sub.add_argument('name')
        sub.add_argument('--global', dest='everywhere', action='store_true', help='every project, through install.sh')
        sub.set_defaults(run=run)
    commands.add_parser('sync', help='recreate this project\'s links').set_defaults(run=command_sync)
    update = commands.add_parser('update', help='move sources to their upstream head and report what changed')
    update.add_argument('sources', nargs='*')
    update.set_defaults(run=command_update)
    plan = commands.add_parser('plan')
    plan.add_argument('--no-fetch', action='store_true')
    plan.set_defaults(run=command_plan)
    check = commands.add_parser('check', help='validate sets.txt and sources.txt')
    check.add_argument('--fetch', action='store_true', help='also fetch every source and find every skill')
    check.set_defaults(run=command_check)
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        sources, sets = load(root)
        getattr(args, 'run', command_list)(args, root, sources, sets)
    except Fail as error:
        print(f'tack: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
