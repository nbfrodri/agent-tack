#!/usr/bin/env bash
# Lifecycle operations use only throwaway homes and repositories.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/harness-lifecycle.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
PASSED=0 FAILED=0
check() { if eval "$2"; then printf '  ✔ %s\n' "$1"; PASSED=$((PASSED + 1)); else printf '  ✘ %s\n' "$1"; FAILED=$((FAILED + 1)); fi; }
run() {
  HOME="$H" XDG_CONFIG_HOME="$H/.config" GIT_CONFIG_NOSYSTEM=1 \
    "$REPO/$1" "${@:2}" > "$WORK/output" 2>&1
}
H="$WORK/preview"
mkdir -p "$H/.claude"
printf '{"theme":"dark"}\n' > "$H/.claude/settings.json"
cp "$H/.claude/settings.json" "$WORK/before"
check 'install dry-run succeeds' 'run install.sh --dry-run'
check 'dry-run describes links, settings, Git and plugins' "grep -q 'would link' '$WORK/output' && grep -q 'would merge' '$WORK/output' && grep -q 'would set core.hooksPath' '$WORK/output' && grep -q 'would ensure plugin' '$WORK/output'"
check 'dry-run preserves HOME' "[ ! -e '$H/.local' ] && [ ! -e '$H/.gitconfig' ] && [ ! -e '$H/.claude/CLAUDE.md' ] && cmp -s '$WORK/before' '$H/.claude/settings.json'"
printf '\n%s passed, %s failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
