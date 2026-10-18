#!/usr/bin/env bash
# Read recorded Codex metadata without following session symlinks.
set -uo pipefail
if [ "$#" -ne 1 ]; then
  echo 'tack: codex-used requires one session id' >&2
  exit 2
fi
session_id="$1"
case "$session_id" in
  '' | *[!0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-]*)
    echo 'tack: invalid Codex session id (letters, digits and hyphens only)' >&2
    exit 2 ;;
esac
if [ "${#session_id}" -gt 64 ]; then
  echo 'tack: invalid Codex session id (at most 64 characters)' >&2
  exit 2
fi
python3 -I - "${CODEX_HOME:-$HOME/.codex}/sessions" "$session_id" <<'PY'
import json
import os
import stat
import sys

sessions, session_id = sys.argv[1:]
try:
    root_fd = os.open(sessions, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
except OSError:
    sys.exit(1)
try:
    # Descriptor-relative traversal also avoids directory symlink races.
    for _, _, files, directory_fd in os.fwalk(".", dir_fd=root_fd, follow_symlinks=False):
        for name in sorted(files):
            if not (name.startswith("rollout-") and name.endswith(f"-{session_id}.jsonl")):
                continue
            try:
                fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd)
                with os.fdopen(fd, "rb") as rollout:
                    if not stat.S_ISREG(os.fstat(rollout.fileno()).st_mode):
                        continue
                    for line in rollout:
                        try:
                            event = json.loads(line)
                        except (ValueError, UnicodeError, RecursionError):
                            continue
                        if not isinstance(event, dict) or event.get("type") != "turn_context":
                            continue
                        payload = event.get("payload")
                        if not isinstance(payload, dict):
                            sys.exit(1)
                        model, effort = payload.get("model"), payload.get("effort")
                        if not all(isinstance(v, str) and v and not any(c.isspace() for c in v)
                                   for v in (model, effort)):
                            sys.exit(1)
                        print(f"model={model} effort={effort}")
                        sys.exit(0)
            except OSError:
                continue
except OSError:
    pass
finally:
    os.close(root_fd)
sys.exit(1)
PY
