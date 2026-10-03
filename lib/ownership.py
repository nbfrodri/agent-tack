#!/usr/bin/env python3
"""Validate private ownership records and conservatively undo installed changes."""
import copy
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile

MISSING = object()


def read(path):
    value = path.read_text()
    return value[:-1] if value.endswith("\n") else value


def plain_path(value):
    return (value.startswith("/") and not any(c in value for c in "\n\r\t")
            and all(p not in (".", "..") for p in value.split("/")))


def no_symlink_ancestors(path):
    return not any(p.is_symlink() for p in [path, *path.parents])


def validate(state, home):
    if not plain_path(str(state)) or not no_symlink_ancestors(state):
        raise ValueError("unsafe ownership state path")
    for root, dirs, files in os.walk(state, followlinks=False):
        for path in [Path(root), *(Path(root) / n for n in dirs + files)]:
            info = path.lstat()
            if (path.is_symlink() or info.st_uid != os.getuid()
                    or stat.S_IMODE(info.st_mode) & 0o077
                    or not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode))):
                raise ValueError("ownership state is not private or contains unsupported files")
    if read(state / "version") != "1" or read(state / "home") != home:
        raise ValueError("unsupported ownership version or HOME mismatch")
    repo = read(state / "repo")
    if not plain_path(repo):
        raise ValueError("invalid recorded repository")
    entries = state / "entries"
    if not entries.is_dir():
        raise ValueError("missing ownership entries")
    seen = set()
    for entry in entries.iterdir():
        if not entry.is_dir() or not entry.name.isdigit():
            raise ValueError("invalid ownership entry")
        kind, path = read(entry / "kind"), read(entry / "path")
        if (kind, path) in seen or not plain_path(path) or not plain_path(read(entry / "parent")):
            raise ValueError("invalid or duplicate ownership path")
        seen.add((kind, path))
        if kind == "link":
            if not path.startswith(home.rstrip("/") + "/"):
                raise ValueError("link outside HOME")
            target, before = read(entry / "target"), read(entry / "before_kind")
            if not plain_path(target) or before not in ("absent", "symlink", "backup"):
                raise ValueError("invalid link record")
            if before == "symlink":
                original = read(entry / "before_target")
                if not original or "\n" in original:
                    raise ValueError("invalid original link target")
            if before == "backup":
                backup = read(entry / "backup")
                if not plain_path(backup) or not backup.startswith(path + ".bak-") or "/" in backup[len(path):]:
                    raise ValueError("backup is not adjacent to its managed path")
        elif kind == "settings":
            if path != home.rstrip("/") + "/.claude/settings.json":
                raise ValueError("unexpected settings path")
            for name in ("before", "after", "managed"):
                with (entry / name).open() as stream:
                    if not isinstance(json.load(stream), dict):
                        raise ValueError("settings snapshot is not an object")
        elif kind == "git":
            expected = {home.rstrip("/") + "/.gitconfig",
                        os.environ.get("XDG_CONFIG_HOME", home + "/.config") + "/git/config"}
            if os.environ.get("GIT_CONFIG_GLOBAL"):
                expected.add(os.environ["GIT_CONFIG_GLOBAL"])
            if path not in expected or not plain_path(read(entry / "target")):
                raise ValueError("unexpected Git config path")
            if "\n" in (entry / "before").read_text():
                raise ValueError("unsupported multiline Git baseline")
        else:
            raise ValueError("unknown ownership kind")
    return sorted(entries.iterdir(), key=lambda p: int(p.name))


def reverse_value(before, after, current):
    if before == after:
        return current
    if current == after:
        return copy.deepcopy(before) if before is not MISSING else MISSING
    if isinstance(after, dict) and isinstance(current, dict) and (isinstance(before, dict) or before is MISSING):
        original = before if isinstance(before, dict) else {}
        result = copy.deepcopy(current)
        for key in set(original) | set(after):
            value = reverse_value(original.get(key, MISSING), after.get(key, MISSING), current.get(key, MISSING))
            if value is MISSING:
                result.pop(key, None)
            else:
                result[key] = value
        if not result and before is MISSING:
            return MISSING
        return result
    if isinstance(after, list) and isinstance(current, list) and (isinstance(before, list) or before is MISSING):
        original = before if isinstance(before, list) else []
        result = copy.deepcopy(current)
        for item in after:
            if item in original:
                continue
            if item in result:
                result.remove(item)
                continue
            if not isinstance(item, dict) or not isinstance(item.get("hooks"), list):
                continue
            metadata = {k: v for k, v in item.items() if k != "hooks"}
            for group in result[:]:
                if not isinstance(group, dict) or {k: v for k, v in group.items() if k != "hooks"} != metadata:
                    continue
                hooks = group.get("hooks")
                if not isinstance(hooks, list):
                    continue
                for hook in item["hooks"]:
                    if hook in hooks:
                        hooks.remove(hook)
                if not hooks:
                    result.remove(group)
        return MISSING if not result and before is MISSING else result
    return current


def reverse_managed(before, managed, current):
    if isinstance(managed, dict) and isinstance(current, dict):
        original = before if isinstance(before, dict) else {}
        result = copy.deepcopy(current)
        for key, installed in managed.items():
            value = reverse_managed(original.get(key, MISSING), installed, current.get(key, MISSING))
            if value is MISSING:
                result.pop(key, None)
            else:
                result[key] = value
        return MISSING if not result and before is MISSING else result
    return reverse_value(before, managed, current)


def same_parent(entry, path):
    return os.path.realpath(path.parent) == read(entry / "parent")


def write_json(path, value):
    mode = stat.S_IMODE(path.stat().st_mode)
    fd, temporary = tempfile.mkstemp(prefix=".harness-uninstall-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            os.fchmod(stream.fileno(), mode)
            json.dump(value, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def uninstall_entry(entry, dry_run):
    kind, path = read(entry / "kind"), Path(read(entry / "path"))
    if not same_parent(entry, path):
        print(f"preserved changed parent: {path}")
        return False
    if kind == "link":
        if not path.is_symlink() or os.readlink(path) != read(entry / "target"):
            print(f"preserved changed or missing link: {path}")
            return False
        before = read(entry / "before_kind")
        backup = Path(read(entry / "backup")) if before == "backup" else None
        if backup is not None and not os.path.lexists(backup):
            print(f"preserved link with missing original backup: {path}")
            return False
        print(f"{'would remove' if dry_run else 'remove'} managed link: {path}" +
              (" and restore original" if before != "absent" else ""))
        if not dry_run:
            path.unlink()
            if before == "symlink":
                path.symlink_to(read(entry / "before_target"))
            elif backup is not None:
                backup.rename(path)
        return True
    if path.is_symlink() or not path.is_file():
        print(f"preserved changed or missing {kind} file: {path}")
        return False
    if kind == "settings":
        with path.open() as stream:
            current = json.load(stream)
        before = json.loads((entry / "before").read_text())
        after = json.loads((entry / "after").read_text())
        managed = json.loads((entry / "managed").read_text())
        restored = before if current == after else reverse_managed(before, managed, current)
        if restored == current:
            print(f"preserved settings: {path}")
            return False
        print(f"{'would restore' if dry_run else 'restore'} unchanged managed settings: {path}")
        if not dry_run:
            if restored == {} and (entry / "was_absent").exists():
                path.unlink()
            else:
                write_json(path, restored)
        return restored == before
    command = ["git", "config", "--file", str(path)]
    found = subprocess.run(command + ["--get-all", "core.hooksPath"], capture_output=True, text=True)
    if found.returncode or found.stdout != read(entry / "target") + "\n":
        print(f"preserved changed Git hooks: {path}")
        return False
    print(f"{'would restore' if dry_run else 'restore'} original Git hooks: {path}")
    if not dry_run:
        before = (entry / "before").read_text()
        args = ["--replace-all", "core.hooksPath", before] if (entry / "before_present").exists() else ["--unset-all", "core.hooksPath"]
        subprocess.run(command + args, check=True, capture_output=True)
    return True


def main():
    if len(sys.argv) not in (4, 5):
        raise ValueError("invalid ownership invocation")
    action, state, home = sys.argv[1:4]
    state = Path(state)
    entries = validate(state, home)
    if action == "validate":
        return
    if action != "uninstall":
        raise ValueError("unknown ownership action")
    dry_run = len(sys.argv) == 5 and sys.argv[4] == "--dry-run"
    failed = False
    for entry in entries:
        try:
            complete = uninstall_entry(entry, dry_run)
            if complete and not dry_run:
                shutil.rmtree(entry)
        except (OSError, ValueError, subprocess.SubprocessError):
            print(f"could not safely restore entry {entry.name}; kept ownership record", file=sys.stderr)
            failed = True
    if not dry_run and not any((state / "entries").iterdir()):
        shutil.rmtree(state)
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f"ownership refused: {type(exc).__name__}; state or paths failed validation", file=sys.stderr)
        sys.exit(1)
