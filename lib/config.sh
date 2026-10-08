#!/usr/bin/env bash
# CLI adapter; validation, shared preferences and source resolution live in project_config.py.
set -eu
source_root="$1"
shift
command -v python3 >/dev/null 2>&1 || { echo 'tack: config needs python3' >&2; exit 2; }
exec python3 "$source_root/lib/project_config.py" "$source_root" config "$@"
