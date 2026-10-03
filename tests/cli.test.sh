#!/usr/bin/env bash
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/harness-cli.XXXXXX")" || exit 1
trap 'rm -rf "$WORK"' EXIT
export HOME="$WORK/home" XDG_CONFIG_HOME="$WORK/home/.config" GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL="$WORK/home/gitconfig"
mkdir -p "$HOME" "$WORK/project/docs/handoffs"
git init -q "$WORK/project"
cd "$WORK/project" || exit 1
CLI="$REPO/bin/harness"
PASSED=0 FAILED=0
check() {
  local label="$1"
  shift
  if "$@"; then PASSED=$((PASSED + 1)); printf '  ✔ %s\n' "$label"
  else FAILED=$((FAILED + 1)); printf '  ✘ %s\n' "$label"; fi
}
expect_exit() {
  local expected="$1" actual
  shift
  "$@" > "$WORK/output" 2>&1
  actual=$?
  [ "$actual" -eq "$expected" ]
}
contains() { grep -qF -- "$1" "$WORK/output"; }
excludes_completed() { ! grep -qF 'Do not include completed work' "$WORK/output"; }
bounded_context() { [ "$(wc -c < "$WORK/output")" -le 7000 ]; }
session() {
  python3 -c 'import json,sys; print(json.dumps({"cwd":sys.argv[1]}))' "$PWD" | bash "$REPO/hooks/claude/session-context.sh"
}
session_has_instructions() {
  python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert "Project \"instructions\"\\path" in d["hookSpecificOutput"]["additionalContext"]' "$WORK/output"
}

: > .git/config.lock
check "enable reports config write failure" expect_exit 1 "$CLI" enable
check "disable reports config write failure" expect_exit 1 "$CLI" disable
rm .git/config.lock
mkdir .harness
git config --global harness.enabled true
git config --local harness.enabled false
check "local opt-out overrides global activation" expect_exit 1 "$CLI" status --quiet
check "shared marker write failure is reported" expect_exit 1 "$CLI" enable --shared
check "failed shared enable preserves disabled status" expect_exit 1 "$CLI" status --quiet
check "failed shared enable preserves local opt-out" test "$(git config --local --get harness.enabled)" = false
git config --global --unset harness.enabled
rmdir .harness
check "unknown enable options are rejected" expect_exit 2 "$CLI" enable --typo
check "shared enable succeeds" expect_exit 0 "$CLI" enable --shared
check "shared marker grants no execution trust" expect_exit 1 "$CLI" trusted --quiet
git config --global harness.trusted true
check "global trust grants no execution trust" expect_exit 1 "$CLI" trusted --quiet
check "local trust can be granted" expect_exit 0 "$CLI" trust
check "trusted status succeeds" expect_exit 0 "$CLI" trusted --quiet
check "trust can be revoked" expect_exit 0 "$CLI" trust --revoke
check "revoked trust refuses execution" expect_exit 1 "$CLI" trusted --quiet

printf 'Project "instructions"\\path\n' > AGENTS.md
printf 'Architecture context\n' > docs/architecture.md
printf '# Handoff\nStatus: in progress\nNext: implement feature\n' > docs/handoffs/2026-10-03-active.md
printf '# Old handoff\nStatus: complete\nDo not include completed work\n' > docs/handoffs/2026-10-04-complete.md
check "context succeeds in enabled projects" expect_exit 0 "$CLI" context
check "context includes project instructions" contains 'Project "instructions"'
check "context includes architecture" contains 'Architecture context'
check "context includes an active handoff" contains 'Next: implement feature'
check "context excludes completed handoffs" excludes_completed
check "SessionStart returns valid JSON with project context" expect_exit 0 session
check "SessionStart preserves quotes and backslashes" session_has_instructions
mkdir -p "$HOME/.local/bin"
ln -s "$CLI" "$HOME/.local/bin/harness"
check "context works through the installed symlink" expect_exit 0 "$HOME/.local/bin/harness" context
mkdir nested
cd nested || exit 1
check "context finds root from a nested directory" expect_exit 0 "$CLI" context
check "nested context includes architecture" contains 'Architecture context'
cd .. || exit 1
git config harness.context false
check "context can be disabled independently" expect_exit 0 "$CLI" context
check "opt-out emits no context" test ! -s "$WORK/output"
git config --unset harness.context
python3 - <<'PY' > AGENTS.md
print('x' * 20000)
PY
check "long context succeeds" expect_exit 0 "$CLI" context
check "context has a bounded size" bounded_context
python3 - <<'PY' > AGENTS.md
print('\u2603' * 4000)
PY
check "Unicode context succeeds" expect_exit 0 "$CLI" context
check "Unicode context respects the byte budget" bounded_context
rm AGENTS.md docs/architecture.md
check "missing documents are accepted" expect_exit 0 "$CLI" context
check "disabled project succeeds with no context" expect_exit 0 "$CLI" disable
check "disabled context succeeds" expect_exit 0 "$CLI" context
check "disabled context is empty" test ! -s "$WORK/output"

printf '\n%s passed, %s failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
