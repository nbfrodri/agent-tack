#!/usr/bin/env bash
# Internal hook adapter. Project commands require trust even if called directly.
set -eu
source_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$1"
"$source_root/bin/tack" trusted --quiet || { echo 'Project command needs local tack trust.' >&2; exit 2; }
bash_path="$(command -v bash)"
if command -v cygpath >/dev/null 2>&1; then bash_path="$(cygpath -w "$bash_path")"; fi
export TACK_VERIFY_BASH="$bash_path"
exec python3 "$source_root/lib/run_check.py" "$@"
