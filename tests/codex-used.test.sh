#!/usr/bin/env bash
# Session metadata lookup uses only isolated rollout fixtures.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/tack-codex-used.XXXXXX")" || exit 1
trap 'rm -rf "$WORK"' EXIT
export HOME="$WORK/home" XDG_CONFIG_HOME="$WORK/home/.config"
export XDG_STATE_HOME="$WORK/home/.local/state"
export CODEX_HOME="$WORK/codex" GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL="$WORK/gitconfig"
SESSIONS="$CODEX_HOME/sessions"
DAY="$SESSIONS/2026/10/18"
mkdir -p "$HOME" "$XDG_CONFIG_HOME" "$XDG_STATE_HOME" "$DAY"
PASSED=0 FAILED=0
check() {
  local label="$1"
  shift
  if "$@"; then PASSED=$((PASSED + 1)); printf '  ✔ %s\n' "$label"
  else FAILED=$((FAILED + 1)); printf '  ✘ %s\n' "$label"; fi
}
expect() {
  local rc="$1" output="$2" actual
  shift 2
  "$REPO/bin/tack" codex-used "$@" > "$WORK/out" 2> "$WORK/err"
  actual=$?
  [ "$actual" -eq "$rc" ] && [ "$(cat "$WORK/out")" = "$output" ]
}
cat > "$DAY/rollout-timestamp-valid-123.jsonl" <<'JSON'
garbage
{"type":"session_meta","payload":{"id":"valid-123","cwd":"/fixture"}}
{"type":"turn_context","payload":{"model":"fixture-model","effort":"medium"}}
{"type":"turn_context","payload":{"model":"later-model","effort":"high"}}
JSON
check 'finds session and uses its first turn context despite garbage' expect 0 'model=fixture-model effort=medium' valid-123
check 'missing session is silent' expect 1 '' missing
printf '%s\n' '{"type":"session_meta","payload":{"id":"no-turn"}}' > "$DAY/rollout-timestamp-no-turn.jsonl"
check 'no turn context is silent' expect 1 '' no-turn
printf '%s\n' 'garbage' '{bad json' 'null' '[]' > "$DAY/rollout-timestamp-garbage.jsonl"
check 'garbage JSON is ignored' expect 1 '' garbage
printf '%s\n' '{"type":"turn_context","payload":{"model":"fixture-model"}}' '{"type":"turn_context","payload":{"model":"later-model","effort":"high"}}' > "$DAY/rollout-timestamp-incomplete.jsonl"
check 'missing fields in first context are silent' expect 1 '' incomplete
for invalid in '../valid-123' 'with/slash' '.' 'with.dot' '' 'with space' 'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklm'; do
  check "invalid id is refused: $invalid" expect 2 '' "$invalid"
  check 'invalid id has a diagnostic' test -s "$WORK/err"
done
check 'missing argument is refused' expect 2 ''
check 'extra argument is refused' expect 2 '' valid-123 extra
cp "$DAY/rollout-timestamp-valid-123.jsonl" "$WORK/outside.jsonl"
ln -s "$WORK/outside.jsonl" "$DAY/rollout-timestamp-linked.jsonl"
check 'rollout symlink outside sessions is ignored' expect 1 '' linked
mkdir -p "$WORK/outside"
cp "$WORK/outside.jsonl" "$WORK/outside/rollout-timestamp-dirlink.jsonl"
ln -s "$WORK/outside" "$SESSIONS/linked-directory"
check 'directory symlink outside sessions is ignored' expect 1 '' dirlink
mkdir -p "$HOME/.codex"
mv "$SESSIONS" "$HOME/.codex/sessions"
unset CODEX_HOME
check 'defaults to HOME/.codex' expect 0 'model=fixture-model effort=medium' valid-123
printf '%s passed, %s failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
