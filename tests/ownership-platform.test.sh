#!/usr/bin/env bash
# Native Windows and POSIX ownership boundaries, always in a disposable HOME.
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/tack-platform.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
export HOME="$WORK/home" XDG_CONFIG_HOME="$WORK/home/.config" GIT_CONFIG_NOSYSTEM=1
unset XDG_STATE_HOME GIT_CONFIG_GLOBAL GIT_CONFIG_COUNT
mkdir -p "$HOME"
python3 "$REPO/tests/ownership_platform_test.py"

# Exercise the Bash writer as well as native Python, including CRLF command substitution.
DRY_RUN=0
has() { command -v "$1" >/dev/null 2>&1; }
fail() { printf '%s\n' "$*" >&2; }
# shellcheck source=lib/keys.sh
source "$REPO/lib/keys.sh"
# shellcheck source=lib/ownership.sh
source "$REPO/lib/ownership.sh"
mkdir -p "$HOME/.codex/agents"
ownership_init
printf 'installed\n' > "$HOME/.codex/agents/reviewer.toml"
sha="$(python3 -c 'import hashlib; print(hashlib.sha256(b"installed\n").hexdigest())')"
sha="${sha%$'\r'}"
ownership_generated "$HOME/.codex/agents/reviewer.toml" "$sha"
python3 "$REPO/lib/ownership.py" validate "$OWNERSHIP" "$HOME"
ownership_init
"$REPO/uninstall.sh"
[ ! -f "$HOME/.codex/agents/reviewer.toml" ]
[ ! -d "$OWNERSHIP" ]
echo 'ownership platform tests and shell-writer round trip passed'
