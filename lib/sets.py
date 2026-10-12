#!/usr/bin/env python3
"""Named sets of skills, agents and Claude plugins.

sets.txt declares each set; sources.txt pins the external repositories some skills come from to a
full commit. A set is active everywhere (git config --global tack.sets, applied by install.sh) or
in one project (local tack.sets, linked into that clone by `tack set use`). `tack set` and the
installer call this module; lib/sets.sh reads the same files for what needs no checkout.
"""
import argparse
import filecmp
import fnmatch
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata

NAME = re.compile(r'^[a-z0-9][a-z0-9-]*$')
SKILL = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*$')
COMMIT = re.compile(r'^[0-9a-f]{40}$')
PLUGIN = re.compile(r'^[A-Za-z0-9._-]+@[A-Za-z0-9._-]+$')
URL = re.compile(r'^https://[A-Za-z0-9._~/@:-]+$')
# A match rule: a glob over the project's files, or FILE:NAME for a dependency or word in a file.
MATCH = re.compile(r'^[A-Za-z0-9_.*-]+(/[A-Za-z0-9_.*-]+)*(:[A-Za-z0-9_.@/-]+)?$')
# A path safe to repeat in output: no spaces, control characters or punctuation that reads as text.
PLAIN = re.compile(r'^[A-Za-z0-9_.@+/-]{1,120}$')
# An ask term: a word of a request, word* for the words that start with it, or word+word for a
# phrase. Requests are compared in lowercase without accents, so terms are written that way.
ASK = re.compile(r'^[a-z0-9]+\*?(\+[a-z0-9]+\*?)*$')
ASK_HELP = ': ask takes lowercase words without accents, as word, word* or word+word'
# How much of a message is compared with the ask terms.
ASKED = 4000
# Bounds for reading a project: how many files to list and how much of one to read.
LISTED, READ = 20000, 1024 * 1024
# Where a project's tools look for skills: the open standard folder and Claude Code's own.
PROJECT_SKILLS = ('.agents/skills', '.claude/skills')
PROJECT_AGENTS = '.claude/agents'
# The set every session relies on: active everywhere whatever is configured, and never dropped.
ALWAYS = 'core'
# Sets kept for a former full-catalog choice: listed, but not offered to an assistant, because
# they group by origin and say nothing about the work at hand.
COMPAT = 'compat'


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
            errors.append(f'{where}: expected set, kind and item' + (ASK_HELP if fields[1:] == ['ask'] else ''))
            continue
        name, kind, ref = fields[0], fields[1], fields[2]
        if not NAME.match(name):
            errors.append(f'{where}: set name {name!r} must be lowercase letters, digits and hyphens')
            continue
        entry = sets.setdefault(name, {'about': '', 'category': '', 'items': [], 'matches': [], 'asks': []})
        if kind == 'about':
            entry['about'] = ' '.join(fields[2:])
            continue
        if kind == 'category':
            if len(fields) != 3 or not NAME.match(ref):
                errors.append(f'{where}: category must be one name of lowercase letters, digits and hyphens')
            else:
                entry['category'] = ref
            continue
        if kind == 'match':
            least = fields[3] if len(fields) == 4 else '1'
            if len(fields) > 4 or not MATCH.match(ref) or '..' in ref.split('/') or not least.isdigit() or int(least) < 1:
                errors.append(f'{where}: match needs a relative file pattern, or FILE:NAME, and an optional minimum count')
            else:
                entry['matches'].append((ref, int(least)))
            continue
        if kind == 'ask':
            wrong = [term for term in fields[2:] if not ASK.match(term)]
            if wrong:
                errors.append(f'{where}: ask term {wrong[0]!r} is not valid' + ASK_HELP)
            else:
                entry['asks'].extend(fields[2:])
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
            errors.append(f'{where}: unknown kind {kind!r} (about, category, match, ask, skill, agent or plugin)')
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
    names = [name for name in names if name in sets and name != ALWAYS]
    return ([ALWAYS] if scope == 'global' and ALWAYS in sets else []) + names


def remember(scope, names, cwd=None):
    names = [name for name in names if name != ALWAYS]
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


def in_project(repo, path):
    """False when a folder between the project root and PATH is a symlink. A repository can
    commit `.claude` or `.agents/skills` as a link to anywhere; following it would create and
    remove entries outside the project."""
    current = path.parent
    while current != repo and current != current.parent:
        if current.is_symlink():
            return False
        current = current.parent
    return current == repo


def claude_plugin(action, plugin, repo):
    if not shutil.which('claude'):
        print(f'  plugin {plugin}: claude not found; run claude plugin {action} {plugin} --scope local')
        return
    result = subprocess.run(['claude', 'plugin', action, plugin, '--scope', 'local'], cwd=repo,
                            stdin=subprocess.DEVNULL, capture_output=True, text=True)
    done = 'installed' if action == 'install' else 'removed'
    if result.returncode == 0:
        print(f'  plugin {plugin}: {done} (Claude Code only)')
    else:
        # A marketplace from plugins.txt is added by the installer, not here.
        print(f'  plugin {plugin}: could not {action}; run install.sh once so its marketplace is known, then tack set sync')


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
        if (repo / folder).is_dir() and in_project(repo, repo / folder / 'entry'):
            for entry in sorted((repo / folder).iterdir()):
                if entry.is_symlink() and ours(entry, root) and entry not in links:
                    entry.unlink()
                    print(f'  removed {entry.relative_to(repo)}')
    skipped = [dest for dest in links if not in_project(repo, dest)]
    for dest in skipped:
        del links[dest]
        print(f'  kept {dest.relative_to(repo)}: a folder above it is a symlink, so it may lead outside the project')
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


def by_category(sets):
    """Set names grouped by category in file order; sets without one come last as "other"."""
    groups = {}
    for name, entry in sets.items():
        groups.setdefault(entry['category'], []).append(name)
    loose = groups.pop('', [])
    if loose:
        groups['other' if groups else ''] = loose
    return groups


def project_files(repo):
    """The project's own files: tracked, or untracked and not ignored. Paths only; nothing is run."""
    code, out, _ = git('ls-files', '-co', '--exclude-standard', '-z', cwd=repo)
    return [name for name in out.split('\0') if name][:LISTED] if code == 0 else []


def mentions(repo, name, word):
    """Whether a project file names WORD: a dependency key in a JSON manifest, a whole word elsewhere."""
    path = repo / name
    if path.is_symlink() or not path.is_file() or path.stat().st_size > READ:
        return False
    try:
        text = path.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return False
    if name.endswith('.json'):
        try:
            data = json.loads(text)
        except ValueError:
            return False
        groups = ('dependencies', 'devDependencies', 'peerDependencies', 'optionalDependencies', 'require', 'require-dev')
        return isinstance(data, dict) and any(isinstance(data.get(group), dict) and word in data[group] for group in groups)
    return re.search(rf'(?<![A-Za-z0-9_.@/-]){re.escape(word)}(?![A-Za-z0-9_.@/-])', text) is not None


def fitting(repo, sets):
    """{set: evidence} for the sets whose match rules the project's files satisfy, in file order."""
    files = project_files(repo)
    found = {}
    for name, entry in sets.items():
        if name == ALWAYS or entry['category'] == COMPAT:
            continue
        for pattern, least in entry['matches']:
            glob, _, word = pattern.partition(':')
            # A pattern without a folder matches a file of that name anywhere in the project.
            hits = [path for path in files
                    if fnmatch.fnmatchcase(path if '/' in glob else path.rsplit('/', 1)[-1], glob)]
            if word:
                hits = [path for path in hits if mentions(repo, path, word)]
            if len(hits) >= least:
                # The evidence is read by an assistant, and a file name may be written to instruct
                # one: name only a file whose path is plain.
                plain = next((path for path in hits if PLAIN.match(path)), 'a file with an unusual name')
                shown = plain if least == 1 else f'{len(hits)} files like {plain}'
                found[name] = f'{shown}{" names " + word if word else ""}'
                break
    return found


def skipped(repo):
    code, out, _ = git('config', '--local', '--get', 'tack.setsSkipped', cwd=repo)
    return [name.strip() for name in out.split(',') if name.strip()] if code == 0 else []


def pending(repo, sets):
    """Sets that fit the project, are active neither here nor everywhere, and were not declined."""
    done = set(active('local', sets, repo)) | set(active('global', sets)) | set(skipped(repo))
    return {name: why for name, why in fitting(repo, sets).items() if name not in done}


def words(text):
    """The words of a message as an ask term sees them: lowercase, without accents or punctuation."""
    plain = unicodedata.normalize('NFKD', text[:ASKED].lower())
    return re.findall(r'[a-z0-9]+', ''.join(letter for letter in plain if not unicodedata.combining(letter)))


def said(term, heard):
    """Whether the words of a term appear in the message, whole, adjacent and in order."""
    parts = term.split('+')
    return any(all(word.startswith(part[:-1]) if part.endswith('*') else word == part
                   for part, word in zip(parts, heard[start:start + len(parts)]))
               for start in range(len(heard) - len(parts) + 1))


def asked(repo, sets, prompt):
    """Sets whose ask terms the message names, active neither here nor everywhere, and not declined."""
    heard = words(prompt)
    if not heard:
        return []
    done = set(active('local', sets, repo)) | set(active('global', sets)) | set(skipped(repo))
    return [name for name, entry in sets.items()
            if name != ALWAYS and entry['category'] != COMPAT and name not in done
            and any(said(term, heard) for term in entry['asks'])]


def command_skip(args, root, sources, sets):
    changeable(args.name, sets)
    repo = project_root()
    names = skipped(repo)
    if args.name not in names:
        code, _, err = git('config', '--local', 'tack.setsSkipped', ','.join([*names, args.name]), cwd=repo)
        if code:
            raise Fail(f'cannot save the declined set: {err}')
    print(f'Declined for {repo}: {args.name}. tack set use {args.name} still activates it.')


def command_suggest(args, root, sources, sets):
    if args.apply and args.skip:
        raise Fail('choose --apply or --skip, not both')
    repo = project_root()
    found = pending(repo, sets)
    if not found:
        print('No set fits this project beyond the active and declined ones (tack set list shows them all).')
        return
    if args.skip:
        code, _, err = git('config', '--local', 'tack.setsSkipped', ','.join([*skipped(repo), *found]), cwd=repo)
        if code:
            raise Fail(f'cannot save the declined sets: {err}')
        print(f'Declined for {repo}: {", ".join(found)}. tack set use NAME still activates one.')
        return
    if not args.apply:
        print('Sets that fit this project and are not active (tack set suggest --apply activates them, --skip declines):')
        for name, why in found.items():
            print(f'  {name:<16} {why}')
        return
    names = [*active('local', sets, repo), *found]
    wanted = resolve(root, names, sources, sets)
    remember('local', names, repo)
    print(f'Active in {repo}: {", ".join(found)}')
    apply_project(root, repo, sources, sets, wanted)


def command_list(args, root, sources, sets):
    code, top, _ = git('rev-parse', '--show-toplevel')
    here = active('local', sets) if code == 0 and top else []
    everywhere = active('global', sets)
    width = max((len(name) for name in sets), default=0)
    print('Sets in sets.txt (* active everywhere, + active in this project):')
    for category, names in by_category(sets).items():
        if category:
            print(category)
        for name in names:
            entry = sets[name]
            mark = '*' if name in everywhere else '+' if name in here else ' '
            totals = [(sum(item['kind'] == kind for item in entry['items']), kind) for kind in ('skill', 'agent', 'plugin')]
            counts = ', '.join(f'{total} {kind}{"" if total == 1 else "s"}' for total, kind in totals if total)
            print(f'{mark} {name:<{width}} {entry["about"]}  ({counts})')


def command_index(args, root, sources, sets):
    """One line for startup context: the names an assistant may activate and what is already on."""
    code, top, _ = git('rev-parse', '--show-toplevel')
    here = active('local', sets) if code == 0 and top else []
    everywhere = active('global', sets)
    groups = by_category({name: entry for name, entry in sets.items()
                          if name != ALWAYS and entry['category'] != COMPAT})
    everywhere = [name for name in everywhere if name != ALWAYS]
    names = '; '.join(f'{category}: {", ".join(found)}' if category else ', '.join(found) for category, found in groups.items())
    line = f'Sets available (skills, agents and plugins that load only once activated): {names}.'
    if everywhere:
        line += ' Active everywhere: ' + ', '.join(everywhere) + '.'
    if here:
        line += ' Active here: ' + ', '.join(here) + '.'
    if code == 0 and top:
        fit = pending(Path(top), sets)
        if fit:
            line += ' Fit this project and are not active: ' + ', '.join(fit) + ' (tack set suggest --apply).'
    print(line + ' tack set use NAME and tack set drop NAME change this project\'s sets; tack set show NAME lists a'
          ' set\'s contents. Leave --global and update to the user.')


# How many skill names one reminder carries; past it the assistant is sent to the list.
REMINDED = 40


def command_reminder(args, root, sources, sets):
    """One line to accompany a message: the skills of the active sets, and the sets still to activate."""
    code, top, _ = git('rev-parse', '--show-toplevel')
    if code or not top:
        return
    repo = Path(top)
    always = {item['name'] for item in sets.get(ALWAYS, {'items': []})['items'] if item['kind'] == 'skill'}
    names = [*active('local', sets, repo), *(name for name in active('global', sets) if name != ALWAYS)]
    skills = [item['name'] for item in resolve(root, names, sources, sets, False)
              if item['kind'] == 'skill' and item['name'] not in always]
    parts = []
    if skills:
        shown = ', '.join(skills[:REMINDED]) + (f' and {len(skills) - REMINDED} more (tack set list)' if len(skills) > REMINDED else '')
        parts.append(f'Skills active in this project: {shown}. Required first step, before reading or editing anything: '
                     'load the ones whose name matches this task.')
    fit = pending(repo, sets)
    if fit:
        parts.append('Sets that fit this project and are not active: ' + ', '.join(fit)
                     + '. Activating them is the user\'s choice: end your reply with one line saying which sets fit and'
                     ' that tack set suggest --apply activates them and tack set suggest --skip declines them.')
    wanted = [name for name in asked(repo, sets, prompt_given() if args.stdin else '') if name not in fit]
    if wanted:
        parts.append('Sets that match this request and are not active: ' + ', '.join(wanted)
                     + '. Activating them is the user\'s choice: do the task as asked, and end your reply with one line'
                     ' saying which sets match and that tack set use NAME activates one and tack set skip NAME stops'
                     ' the suggestion.')
    if parts:
        print('[tack] ' + ' '.join(parts))


def prompt_given():
    """The message from a hook's input on standard input; anything else counts as no message."""
    try:
        prompt = json.loads(sys.stdin.read(READ)).get('prompt')
    except (ValueError, AttributeError, OSError):
        return ''
    return prompt if isinstance(prompt, str) else ''


def command_show(args, root, sources, sets):
    known(args.name, sets)
    print(f'{args.name}: {sets[args.name]["about"]}')
    for item in sets[args.name]['items']:
        print(f'  {item["kind"]:<7} {item["ref"]}')


def known(name, sets):
    if name not in sets:
        raise Fail(f'unknown set {name!r} (see tack set list)')


def changeable(name, sets):
    known(name, sets)
    if name == ALWAYS:
        raise Fail(f'{ALWAYS} is always active; it cannot be used or dropped')


def command_use(args, root, sources, sets):
    changeable(args.name, sets)
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
    changeable(args.name, sets)
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
    # The command guard decides from the literal words of a command, so nothing here may accept
    # another spelling: no abbreviated options, and the checkout comes from the caller (bin/tack,
    # install.sh) as the first argument, never from an option a later argument could repeat.
    parser = argparse.ArgumentParser(prog='tack set', allow_abbrev=False,
                                     description='Named sets of skills, agents and plugins.')
    parser.add_argument('root', type=Path, help=argparse.SUPPRESS)
    commands = parser.add_subparsers(dest='command')

    def command(name, run, **options):
        sub = commands.add_parser(name, allow_abbrev=False, **options)
        sub.set_defaults(run=run)
        return sub

    command('list', command_list, help='every set and where it is active (default)')
    command('show', command_show, help='what a set contains').add_argument('name')
    for name, run, text in (('use', command_use, 'activate a set in this project, or everywhere with --global'),
                            ('drop', command_drop, 'deactivate a set')):
        sub = command(name, run, help=text)
        sub.add_argument('name')
        sub.add_argument('--global', dest='everywhere', action='store_true', help='every project, through install.sh')
    command('sync', command_sync, help='recreate this project\'s links')
    command('update', command_update,
            help='move sources to their upstream head and report what changed').add_argument('sources', nargs='*')
    suggest = command('suggest', command_suggest, help='sets that fit this project\'s files')
    suggest.add_argument('--apply', action='store_true', help='activate them in this project')
    suggest.add_argument('--skip', action='store_true', help='decline them for this project')
    command('index', command_index)
    command('skip', command_skip, help='stop suggesting a set in this project').add_argument('name')
    command('reminder', command_reminder).add_argument('--stdin', action='store_true')
    command('plan', command_plan).add_argument('--no-fetch', action='store_true')
    check = command('check', command_check, help='validate sets.txt and sources.txt')
    check.add_argument('--fetch', action='store_true', help='also fetch every source and find every skill')
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
