#!/usr/bin/env python3
"""Validated project preferences and local/shared/global resolution, without executing project code."""
import argparse
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tempfile

FILENAME = 'tack.json'
MAX_BYTES = 65536
SHARED_MODES = {'auto', 'lite', 'standard', 'strict'}


def registry(source):
    entries = {}
    for line in (source / 'features.txt').read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        parts = line.split(None, 7)
        if len(parts) != 8 or parts[6] not in ('yes', 'no'):
            raise ValueError('features.txt: expected the shared yes/no column')
        name, key, default, values, scope, enforcement, shared, description = parts
        entries[name] = dict(name=name, key=key, default=default, values=values, scope=scope,
                             enforcement=enforcement, shared=shared == 'yes', description=description)
    return entries


def project_root():
    result = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True,
                            encoding='utf-8', errors='replace', timeout=10)
    return Path(result.stdout.strip()) if result.returncode == 0 else None


def git_values(scope, root=None):
    prefix = ['git', '-C', str(root)] if root else ['git']
    result = subprocess.run(prefix + ['config', '--' + scope, '--null', '--get-regexp', r'^tack\.'],
                            capture_output=True, timeout=10)
    if result.returncode not in (0, 1):
        raise ValueError(f'Cannot read {scope} Git configuration')
    values = {}
    for record in result.stdout.decode('utf-8', errors='replace').split('\0'):
        if record:
            key, _, value = record.partition('\n')
            values[key.lower()] = value
    return values


def relative_path(value):
    return (isinstance(value, str) and bool(value) and len(value) <= 512
            and not any(ord(c) < 32 or c in '\\:*?[]<>|",' for c in value)
            and not value.startswith(('/', '~')) and value != '.'
            and all(part.casefold() not in ('', '.', '..', '.git') and not part.endswith((' ', '.'))
                    for part in value.split('/'))
            and not PurePosixPath(value).is_absolute())


def validate_value(feature, value, typed=False):
    kind = feature['values']
    if typed:
        if kind == 'bool' and type(value) is not bool:
            raise ValueError(f"{feature['name']} requires a JSON boolean")
        if kind == 'number' and type(value) is not int:
            raise ValueError(f"{feature['name']} requires a JSON integer")
        if kind not in ('bool', 'number', 'decimal') and not isinstance(value, str):
            raise ValueError(f"{feature['name']} requires a string")
    text = ('true' if value else 'false') if type(value) is bool else str(value)
    valid = bool(text) and len(text) <= 8192 and '\0' not in text
    if kind == 'bool':
        valid = valid and text in ('true', 'false')
    elif kind == 'number':
        valid = valid and bool(re.fullmatch(r'[1-9][0-9]*', text))
    elif kind == 'decimal':
        valid = valid and bool(re.fullmatch(r'[0-9]+(?:\.[0-9]+)?', text)) and any(c in '123456789' for c in text)
    elif kind == 'path':
        valid = valid and relative_path(text)
    elif kind.startswith('list:'):
        valid = valid and all(item and item in kind[5:].split('|') for item in text.replace(' ', '').split(','))
    elif kind != 'text':
        valid = valid and text in kind.split('|')
    if not valid:
        raise ValueError(f"invalid value for {feature['name']}: {text} (allowed: {kind})")
    return text


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'{FILENAME}: duplicate key {key}')
        result[key] = value
    return result


def load_profile(root, features):
    if root is None:
        return {}, None
    path = root / FILENAME
    if path.is_symlink():
        raise ValueError(f'{FILENAME}: symlinks are not supported')
    if not path.exists():
        return {}, None
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError(f'{FILENAME}: expected a regular file at most 64 KiB')
    original = path.read_bytes()
    data = json.loads(original.decode('utf-8'), object_pairs_hook=unique_object)
    if not isinstance(data, dict) or set(data) - {'version', 'mode', 'config'}:
        raise ValueError(f'{FILENAME}: unsupported top-level fields')
    if type(data.get('version')) is not int or data['version'] != 1:
        raise ValueError(f'{FILENAME}: expected version 1')
    if 'mode' in data and (not isinstance(data['mode'], str) or data['mode'] not in SHARED_MODES):
        raise ValueError(f'{FILENAME}: shared mode must be auto, lite, standard or strict')
    config = data.get('config', {})
    if not isinstance(config, dict):
        raise ValueError(f'{FILENAME}: config must be an object')
    for name, value in config.items():
        if name not in features or not features[name]['shared'] or features[name]['scope'] == 'global':
            raise ValueError(f'{FILENAME}: {name} cannot be shared')
        validate_value(features[name], value, typed=True)
    return data, original


def write_profile(root, data, original):
    path = root / FILENAME
    content = (json.dumps(data, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
    if len(content) > MAX_BYTES:
        raise ValueError(f'{FILENAME}: configuration exceeds 64 KiB')
    descriptor, temporary = tempfile.mkstemp(prefix='.tack-config-', dir=root)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if path.is_symlink() or (path.read_bytes() if path.exists() else None) != original:
            raise ValueError(f'{FILENAME} changed during the update; retry after reviewing it')
        os.chmod(temporary, stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def effective(feature, profile, local, global_values, selected_scope=None):
    key = feature['key'].lower()
    shared = profile.get('config', {})
    scopes = [selected_scope] if selected_scope else ['local', 'shared', 'global']
    for scope in scopes:
        if feature['scope'] == 'global' and scope != 'global':
            continue
        if scope == 'shared' and feature['name'] in shared:
            return validate_value(feature, shared[feature['name']], typed=True), 'shared'
        values = local if scope == 'local' else global_values if scope == 'global' else {}
        if key in values:
            return values[key], scope
    return feature['default'], 'default'


def project_paths(root):
    """Resolve the same safe locations for scaffolding, context and trace discovery."""
    features = registry(Path(__file__).resolve().parent.parent)
    profile, _ = load_profile(root, features)
    local, global_values = git_values('local', root), git_values('global', root)
    paths = {}
    for name in ('architecture-path', 'plans-path', 'handoffs-path'):
        feature = features[name]
        value, _ = effective(feature, profile, local, global_values)
        validate_value(feature, value)
        path = root / value
        if any(p.is_symlink() for p in (path, *path.parents) if p != root and p.is_relative_to(root)):
            raise ValueError(f'{name}: symlink paths are not supported')
        paths[name] = value
    if len(set(paths.values())) != len(paths):
        raise ValueError('architecture, plans and handoffs must have different paths')
    return paths


def configure(source, args):
    parser = argparse.ArgumentParser(prog='tack config')
    parser.add_argument('name', nargs='?')
    parser.add_argument('value', nargs='?')
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument('--global', dest='global_scope', action='store_true')
    scope.add_argument('--shared', action='store_true')
    parser.add_argument('--unset', action='store_true')
    output = parser.add_mutually_exclusive_group()
    output.add_argument('--get', action='store_true')
    output.add_argument('--json', action='store_true')
    options = parser.parse_args(args)
    features = registry(source)
    if options.name and options.name not in features:
        raise ValueError(f"unknown feature: {options.name} (run 'tack config' to list them)")
    if not options.name and (options.unset or options.shared or options.global_scope or options.get):
        raise ValueError('config needs a feature name')
    if options.unset and options.value is not None:
        raise ValueError('--unset takes no value')
    mutation = options.value is not None or options.unset
    if mutation and (options.get or options.json):
        raise ValueError('--get and --json are read-only options')
    root = project_root()
    profile, original = load_profile(root, features)
    local = git_values('local') if root else {}
    global_values = git_values('global')
    target_scope = 'global' if options.global_scope else 'shared' if options.shared else 'local'
    selected = [features[options.name]] if options.name else list(features.values())
    if mutation:
        feature = selected[0]
        if target_scope != 'global' and root is None:
            raise ValueError('not inside a git repository')
        if feature['scope'] == 'global' and target_scope != 'global':
            raise ValueError(f"{options.name} is a user-wide setting; add --global")
        if target_scope == 'shared' and not feature['shared']:
            raise ValueError(f'{options.name} cannot be shared; use a local preference')
        value = validate_value(feature, options.value) if not options.unset else None
        if target_scope == 'shared':
            profile.setdefault('version', 1)
            config = profile.setdefault('config', {})
            if options.unset:
                config.pop(options.name, None)
            else:
                config[options.name] = value == 'true' if feature['values'] == 'bool' else int(value) if feature['values'] == 'number' else value
            # An unset of a missing shared setting must not create a file.
            if original is not None or not options.unset:
                write_profile(root, profile, original)
        else:
            command = ['git', 'config', '--' + target_scope]
            command += ['--unset-all', feature['key']] if options.unset else [feature['key'], value]
            result = subprocess.run(command, capture_output=True, timeout=10)
            if result.returncode not in ((0, 5) if options.unset else (0,)):
                raise ValueError(f'cannot update {options.name}')
            values = local if target_scope == 'local' else global_values
            if options.unset:
                values.pop(feature['key'].lower(), None)
            else:
                values[feature['key'].lower()] = value
        if options.unset:
            value, origin = effective(feature, profile, local, global_values)
            print(f'Removed the {target_scope} setting for {options.name}; now {value} ({origin}).')
        else:
            print(f'Set {options.name} to {value} ({target_scope}).')
        return 0
    records = []
    for feature in selected:
        value, origin = effective(feature, profile, local, global_values,
                                  target_scope if options.global_scope or options.shared else None)
        records.append(dict(name=feature['name'], value=value, source=origin,
                            enforcement=feature['enforcement'], shared=feature['shared'], description=feature['description']))
    if options.json:
        print(json.dumps(records[0] if options.name else records, ensure_ascii=True))
    elif options.get:
        print(records[0]['value'])
    elif options.name:
        print(f"{records[0]['value']} ({records[0]['source']})")
    else:
        print(f"{'NAME':24}{'VALUE':10}{'SOURCE':9}{'ENFORCEMENT':12}DESCRIPTION")
        for record in records:
            print(f"{record['name']:24}{record['value']:10}{record['source']:9}{record['enforcement']:12}{record['description']}")
    return 0


def shared_mode(source, args):
    root = project_root()
    if root is None:
        if not args:
            return 1
        raise ValueError('not inside a git repository')
    data, original = load_profile(root, registry(source))
    if not args:
        if 'mode' not in data:
            return 1
        print(data['mode'])
        return 0
    if len(args) != 1 or args[0] not in SHARED_MODES | {'--unset'}:
        raise ValueError('shared mode must be auto, lite, standard or strict')
    if args[0] == '--unset':
        data.pop('mode', None)
    else:
        data.setdefault('version', 1)
        data['mode'] = args[0]
    if original is not None or args[0] != '--unset':
        write_profile(root, data, original)
    return 0


def main():
    try:
        source, action, *args = sys.argv[1:]
        if action == 'config':
            return configure(Path(source), args)
        if action == 'shared-mode':
            return shared_mode(Path(source), args)
        if action == 'paths':
            root = project_root()
            if root is None:
                raise ValueError('not inside a git repository')
            print('\n'.join(project_paths(root).values()))
            return 0
        raise ValueError('unknown project configuration operation')
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f'tack: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    # Shell consumers need LF records even when Python is native Windows.
    sys.stdout.reconfigure(newline='\n')
    sys.exit(main())
