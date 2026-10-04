#!/usr/bin/env bash
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/harness-settings.XXXXXX")" || exit 1
trap 'rm -rf "$WORK"' EXIT
export HOME="$WORK/home" XDG_CONFIG_HOME="$WORK/home/.config" GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL="$WORK/home/gitconfig"
mkdir -p "$HOME"
cat > "$WORK/base.json" <<'JSON'
{"theme":"dark","hooks":{"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"command","command":"echo user-hook"},{"type":"command","command":"echo old #harness"}]}]}}
JSON
PASSED=0 FAILED=0
for backend in python jq; do
  [ "$backend" != jq ] || command -v jq >/dev/null 2>&1 || continue
  if [ "$backend" = python ]; then
    python3 "$REPO/lib/settings-merge.py" "$WORK/base.json" "$REPO/claude/settings.json" > "$WORK/result.json"
  else
    jq -s -f "$REPO/lib/settings-merge.jq" "$WORK/base.json" "$REPO/claude/settings.json" > "$WORK/result.json"
  fi
  if python3 - "$WORK/result.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
groups = d['hooks']['PreToolUse']
commands = [h['command'] for g in groups for h in g['hooks']]
assert 'echo user-hook' in commands
assert 'echo old #harness' not in commands
assert any(g.get('matcher') == 'Bash' and any(h['command'] == 'echo user-hook' for h in g['hooks']) for g in groups)
assert d['theme'] == 'dark'
assert sum('#tack' in c for c in commands) == 2  # guard and budget
PY
  then PASSED=$((PASSED + 1)); printf '  ✔ %s preserves mixed user hook groups\n' "$backend"
  else FAILED=$((FAILED + 1)); printf '  ✘ %s preserves mixed user hook groups\n' "$backend"; fi
done
printf '\n%s passed, %s failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
