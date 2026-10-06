#!/usr/bin/env python3
"""Reads and edits one key of a VS Code user settings file that is plain JSON.

Usage: vscode_settings.py state FILE   prints absent, unset, true, false, other or invalid
       vscode_settings.py add FILE     sets the key to true when it is absent (creates the file)
       vscode_settings.py remove FILE  removes the key when it is true; deletes the file when
                                       told it was created and nothing else remains
"""
import json
import os
import stat
import sys
import tempfile

KEY = "chat.useAgentsMdFile"


def load(path):
    with open(path, encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError("settings are not an object")
    return value


def state(path):
    if not os.path.exists(path):
        return "absent"
    try:
        settings = load(path)
    except (OSError, ValueError):
        return "invalid"
    if KEY not in settings:
        return "unset"
    return {True: "true", False: "false"}.get(settings[KEY], "other")


def write(path, settings):
    directory = os.path.dirname(path)
    mode = stat.S_IMODE(os.stat(path).st_mode) if os.path.exists(path) else 0o644
    fd, temporary = tempfile.mkstemp(prefix=".tack-", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            os.fchmod(stream.fileno(), mode)
            json.dump(settings, stream, indent=4)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def add(path):
    current = state(path)
    if current not in ("absent", "unset"):
        raise SystemExit(f"refusing to change settings in state {current}")
    settings = load(path) if current == "unset" else {}
    settings[KEY] = True
    write(path, settings)


def remove(path, created, dry_run=False):
    if state(path) != "true":
        return "preserved"
    settings = load(path)
    del settings[KEY]
    if not settings and created:
        if not dry_run:
            os.unlink(path)
        return "deleted"
    if not dry_run:
        write(path, settings)
    return "removed"


if __name__ == "__main__":
    action, target = sys.argv[1], sys.argv[2]
    if action == "state":
        print(state(target))
    elif action == "add":
        add(target)
    elif action == "remove":
        print(remove(target, len(sys.argv) > 3 and sys.argv[3] == "created"))
    else:
        raise SystemExit("unknown action")
