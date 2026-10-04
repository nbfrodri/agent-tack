#!/usr/bin/env python3
"""Validate private ownership records and conservatively undo installed changes."""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile

import vscode_settings

MISSING = object()
VSCODE_PRODUCTS = ("Code", "Code - Insiders", "VSCodium")
MOD_NAME = re.compile(r"[a-z0-9][a-z0-9._-]*")
MOD_ID = re.compile(r"[a-z0-9][a-z0-9._-]*@[a-z0-9][a-z0-9._-]*")
GENERATED_NAME = re.compile(r"[a-z0-9][a-z0-9-]*\.toml")
SHA256 = re.compile(r"[0-9a-f]{64}")


def read(path):
    value = path.read_text()
    return value[:-1] if value.endswith("\n") else value


def plain_path(value):
    return (value.startswith("/") and not any(c in value for c in "\n\r\t")
            and all(p not in (".", "..") for p in value.split("/")))


def no_symlink_ancestors(path, floor):
    for current in [path, *path.parents]:
        if current == floor:
            return True
        if current.is_symlink():
            return False
    return True


def expected_link(path, target, home, repo, declaration):
    fixed = {home + "/.agents/harness": repo, home + "/.agents/tack": repo,
             home + "/.local/bin/tack": repo + "/bin/tack",
             home + "/.local/bin/harness": repo + "/bin/harness"}
    skill_dirs = {home + "/.agents/skills"}
    for line in declaration.read_text().splitlines():
        fields = line.split()
        if not fields or fields[0].startswith("#"):
            continue
        if len(fields) < 5:
            raise ValueError("invalid target declaration")
        instructions, skills = fields[3:5]
        if instructions.startswith("~/"):
            fixed[home + instructions[1:]] = repo + "/global/AGENTS.md"
        if skills.startswith("~/"):
            skill_dirs.add(home + skills[1:])
    if path in fixed:
        return target == fixed[path]
    parent, name = os.path.split(path)
    if parent in skill_dirs and name not in ("", ".", ".."):
        return target == repo + "/skills/" + name
    if parent == home + "/.claude/agents" and name.endswith(".md"):
        return target == repo + "/agents/" + name
    return False


def vscode_settings_paths(home):
    home = home.rstrip("/")
    config = os.environ.get("XDG_CONFIG_HOME", home + "/.config")
    return {base + "/" + product + "/User/settings.json"
            for base in (config, home + "/Library/Application Support")
            for product in VSCODE_PRODUCTS}


def validate(state, home):
    floor = Path(os.environ.get("XDG_STATE_HOME", home))
    if not plain_path(str(state)) or not no_symlink_ancestors(state, floor):
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
        entry_repo = read(entry / "repo")
        identity = read(entry / "parent_identity")
        if not plain_path(entry_repo) or (identity != "unavailable" and
                (len(identity.split(":")) != 2 or not all(part.isdigit() for part in identity.split(":")))):
            raise ValueError("invalid parent identity or source repository")
        if kind == "link":
            if not path.startswith(home.rstrip("/") + "/"):
                raise ValueError("link outside HOME")
            target, before = read(entry / "target"), read(entry / "before_kind")
            declaration = entry / "targets"
            if not declaration.exists():
                declaration = Path(__file__).resolve().parent.parent / "targets.txt"
            if not expected_link(path, target, home.rstrip("/"), entry_repo, declaration):
                raise ValueError("link is outside declared installation targets")
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
            if path not in (home.rstrip("/") + "/.claude/settings.json", home.rstrip("/") + "/.codex/hooks.json"):
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
            if path not in expected or read(entry / "target") != entry_repo.rstrip("/") + "/git-hooks":
                raise ValueError("unexpected Git config path")
            if "\n" in (entry / "before").read_text():
                raise ValueError("unsupported multiline Git baseline")
        elif kind == "generated":
            parent, name = os.path.split(path)
            if parent != home.rstrip("/") + "/.codex/agents" or not GENERATED_NAME.fullmatch(name):
                raise ValueError("unexpected generated file")
            if not SHA256.fullmatch(read(entry / "sha256")):
                raise ValueError("invalid generated file checksum")
        elif kind in ("mod", "modmarket"):
            name = read(entry / ("plugin" if kind == "mod" else "marketplace"))
            pattern = MOD_ID if kind == "mod" else MOD_NAME
            if not pattern.fullmatch(name) or path != home.rstrip("/") + "/.claude/plugins/" + name:
                raise ValueError("unexpected mod record")
        elif kind == "vscode":
            if path not in vscode_settings_paths(home) or read(entry / "created") not in ("0", "1"):
                raise ValueError("unexpected VS Code settings record")
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
        removed = False
        for item in after:
            if item in original:
                continue
            if item in result:
                result.remove(item)
                removed = True
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
                        removed = True
                if not hooks:
                    result.remove(group)
        if removed:
            restore_displaced_hooks(original, result)
        return MISSING if not result and before is MISSING else result
    return current


def restore_displaced_hooks(original, current):
    for group in original:
        if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
            continue
        displaced = [hook for hook in group["hooks"] if isinstance(hook, dict) and
                     any(tag in str(hook.get("command", "")) for tag in ("#tack", "#harness", "#agent-config"))]
        for hook in displaced:
            if any(isinstance(item, dict) and hook in item.get("hooks", []) for item in current):
                continue
            metadata = {key: value for key, value in group.items() if key != "hooks"}
            destination = next((item for item in current if isinstance(item, dict) and
                                isinstance(item.get("hooks"), list) and
                                {key: value for key, value in item.items() if key != "hooks"} == metadata), None)
            if destination is None:
                destination = copy.deepcopy(metadata)
                destination["hooks"] = []
                current.append(destination)
            destination["hooks"].append(copy.deepcopy(hook))


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


def restore_retired_events(before, after, managed, current, restored):
    if not isinstance(current, dict) or not isinstance(restored, dict) or "hooks" not in current:
        return
    original = before.get("hooks", {})
    installed = after.get("hooks", {})
    wanted = managed.get("hooks", {})
    present = restored.get("hooks", {})
    if not all(isinstance(value, dict) for value in (original, installed, wanted, present)):
        return
    for event, groups in original.items():
        if event in wanted or not isinstance(groups, list) or not isinstance(present.get(event, []), list):
            continue
        after_groups = installed.get(event, [])
        if not isinstance(after_groups, list):
            continue
        retained = [hook for group in after_groups if isinstance(group, dict) and
                    isinstance(group.get("hooks"), list) for hook in group["hooks"]]
        displaced = []
        for group in groups:
            if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                continue
            removed = [hook for hook in group["hooks"] if hook not in retained and
                       isinstance(hook, dict) and any(tag in str(hook.get("command", ""))
                                                     for tag in ("#tack", "#harness", "#agent-config"))]
            if removed:
                displaced.append(dict(group, hooks=removed))
        if displaced:
            destination = restored.setdefault("hooks", {}).setdefault(event, [])
            restore_displaced_hooks(displaced, destination)


def same_parent(entry, path):
    if not path.parent.is_dir() or os.path.realpath(path.parent) != read(entry / "parent"):
        return False
    info = path.parent.stat()
    return f"{info.st_dev}:{info.st_ino}" == read(entry / "parent_identity")


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


def claude(*args):
    return subprocess.run(["claude", *args], stdin=subprocess.DEVNULL, capture_output=True, text=True)


def claude_names(listing, key):
    result = claude("plugin", *listing, "--json")
    if result.returncode:
        return None
    return {item.get(key) for item in json.loads(result.stdout)}


def uninstall_mod(entry, kind, dry_run):
    name = read(entry / ("plugin" if kind == "mod" else "marketplace"))
    label = "mod" if kind == "mod" else "mods marketplace"
    if not shutil.which("claude"):
        print(f"preserved {label} {name}: claude CLI not found")
        return False
    present = claude_names(["list"] if kind == "mod" else ["marketplace", "list"],
                           "id" if kind == "mod" else "name")
    if present is not None and name not in present:
        print(f"{label} already removed: {name}")
        return True
    print(f"{'would remove' if dry_run else 'remove'} {label}: {name}")
    if not dry_run:
        args = ["uninstall", name] if kind == "mod" else ["marketplace", "remove", name]
        subprocess.run(["claude", "plugin", *args], stdin=subprocess.DEVNULL,
                       capture_output=True, check=True)
    return True


def uninstall_entry(entry, dry_run):
    kind, path = read(entry / "kind"), Path(read(entry / "path"))
    if kind in ("mod", "modmarket"):
        return uninstall_mod(entry, kind, dry_run)
    if not same_parent(entry, path):
        print(f"preserved changed parent: {path}")
        return False
    if kind == "generated":
        if not path.is_file() or path.is_symlink():
            print(f"generated file already removed: {path}")
            return True
        if hashlib.sha256(path.read_bytes()).hexdigest() != read(entry / "sha256"):
            print(f"preserved edited generated file: {path}")
            return False
        print(f"{'would remove' if dry_run else 'remove'} generated file: {path}")
        if not dry_run:
            path.unlink()
        return True
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
    if kind == "vscode":
        outcome = vscode_settings.remove(str(path), read(entry / "created") == "1", dry_run)
        if outcome == "preserved":
            print(f"preserved VS Code settings (value changed or not plain JSON): {path}")
            return False
        verb = {"deleted": "delete created file", "removed": "remove chat.useAgentsMdFile from"}[outcome]
        print(f"{'would ' if dry_run else ''}{verb} {path}")
        return True
    if kind == "settings":
        with path.open() as stream:
            current = json.load(stream)
        before = json.loads((entry / "before").read_text())
        after = json.loads((entry / "after").read_text())
        managed = json.loads((entry / "managed").read_text())
        restored = before if current == after else reverse_managed(before, managed, current)
        if current != after:
            restore_retired_events(before, after, managed, current, restored)
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
    kept_markets = set()
    # A mods marketplace goes last, and only when none of its mods was kept
    ordered = sorted(entries, key=lambda e: read(e / "kind") == "modmarket")
    for entry in ordered:
        try:
            kind = read(entry / "kind")
            if kind == "modmarket" and read(entry / "marketplace") in kept_markets:
                print(f"preserved mods marketplace {read(entry / 'marketplace')}: some mods were kept")
                continue
            complete = uninstall_entry(entry, dry_run)
            if not complete and kind == "mod":
                kept_markets.add(read(entry / "plugin").split("@", 1)[1])
            if complete and not dry_run:
                shutil.rmtree(entry)
        except (OSError, ValueError, subprocess.SubprocessError):
            if read(entry / "kind") == "mod":
                kept_markets.add(read(entry / "plugin").split("@", 1)[1])
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
