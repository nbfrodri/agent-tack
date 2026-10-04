#!/usr/bin/env bash
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/harness-cli.XXXXXX")" || exit 1
trap 'rm -rf "$WORK"' EXIT
export HOME="$WORK/home" XDG_CONFIG_HOME="$WORK/home/.config" XDG_STATE_HOME="$WORK/home/.local/state" GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL="$WORK/home/gitconfig"
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
output_is() { [ "$(cat "$WORK/output")" = "$1" ]; }
expect_mode() { expect_exit 0 "$CLI" mode && output_is "$1"; }
expect_status() {
  local expected_exit="$1" workflow="$2" trust="$3" expected
  shift 3
  expect_exit "$expected_exit" "$CLI" "$@" || return 1
  expected="$(printf '%s\nmode: %s\nformatter trust: %s' "$workflow" "${EXPECTED_MODE:-auto (default)}" "$trust")"
  [ "$(cat "$WORK/output")" = "$expected" ]
}
excludes_completed() { ! grep -qF 'Do not include completed work' "$WORK/output"; }
bounded_context() { [ "$(wc -c < "$WORK/output")" -le 7000 ]; }
session() {
  python3 -c 'import json,sys; print(json.dumps({"cwd":sys.argv[1]}))' "$PWD" | bash "$REPO/hooks/claude/session-context.sh"
}
session_has_instructions() {
  python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert "Project \"instructions\"\\path" in d["hookSpecificOutput"]["additionalContext"]' "$WORK/output"
}

check "status shows disabled and untrusted independently" expect_status 1 disabled untrusted status
check "default command shows combined status" expect_status 1 disabled untrusted
check "disabled quiet status keeps its activation exit code" expect_exit 1 "$CLI" status --quiet
check "disabled quiet status emits no output" test ! -s "$WORK/output"
git config --local harness.enabled true
check "status shows enabled without formatter trust" expect_status 0 enabled untrusted status
check "enabled quiet status keeps its activation exit code" expect_exit 0 "$CLI" status --quiet
check "enabled quiet status emits no output" test ! -s "$WORK/output"
git config --local harness.trusted true
check "status shows enabled and locally trusted" expect_status 0 enabled trusted status
git config --local harness.enabled false
check "disabled workflow can retain local formatter trust" expect_status 1 disabled trusted status
git config --local --unset harness.enabled
git config --local --unset harness.trusted
cd "$WORK" || exit 1
check "outside a repository status is disabled and untrusted" expect_status 1 disabled untrusted status
check "help works outside a Git repository" expect_exit 0 "$CLI" help
check "help shows CLI invocation syntax" contains 'Usage: harness [command] [options]'
check "help documents the default command" contains 'Default command: status'
check "help lists both global help flags" contains '-h, --help'
cp "$WORK/output" "$WORK/help-output"
check "long help flag succeeds outside Git" expect_exit 0 "$CLI" --help
check "long help flag matches the help command" cmp -s "$WORK/output" "$WORK/help-output"
check "short help flag succeeds outside Git" expect_exit 0 "$CLI" -h
check "short help flag matches the help command" cmp -s "$WORK/output" "$WORK/help-output"
check "help rejects unsupported arguments" expect_exit 2 "$CLI" help unexpected
check "unknown command fails with a usage error" expect_exit 2 "$CLI" unknown-command
check "unknown command includes CLI invocation syntax" contains 'Usage: harness [command] [options]'
cd "$WORK/project" || exit 1

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
check "status ignores global formatter trust" expect_status 0 enabled untrusted status
check "local trust can be granted" expect_exit 0 "$CLI" trust
check "trusted status succeeds" expect_exit 0 "$CLI" trusted --quiet
check "standalone trusted query keeps its output and exit code" expect_exit 0 "$CLI" trusted
check "standalone trusted query prints trusted" test "$(cat "$WORK/output")" = trusted
check "trust can be revoked" expect_exit 0 "$CLI" trust --revoke
check "revoked trust refuses execution" expect_exit 1 "$CLI" trusted --quiet

check "mode defaults to auto" expect_mode 'auto (default)'
check "global mode can be set" expect_exit 0 "$CLI" mode lite --global
check "global mode applies to the project" expect_mode 'lite (global)'
check "project mode can be set" expect_exit 0 "$CLI" mode strict
check "project mode is stored locally" test "$(git config --local --get harness.mode)" = strict
check "project mode overrides the global default" expect_mode 'strict (local)'
check "global query ignores the project mode" expect_exit 0 "$CLI" mode --global
check "global query shows the global default" output_is 'lite (global)'
EXPECTED_MODE='strict (local)'
check "status shows the effective mode and its source" expect_status 0 enabled untrusted status
unset EXPECTED_MODE
check "project mode can be unset" expect_exit 0 "$CLI" mode --unset
check "unset project mode falls back to the global default" expect_mode 'lite (global)'
check "global option may come first" expect_exit 0 "$CLI" mode --global standard
check "global mode can be changed" expect_mode 'standard (global)'
check "global mode can be unset" expect_exit 0 "$CLI" mode --unset --global
check "unset global mode falls back to auto" expect_mode 'auto (default)'
check "unknown modes are rejected" expect_exit 2 "$CLI" mode turbo
check "rejected mode is not stored" test -z "$(git config --get harness.mode)"
check "extra mode arguments are rejected" expect_exit 2 "$CLI" mode lite strict
check "unknown mode options are rejected" expect_exit 2 "$CLI" mode --typo
git config --local harness.mode turbo
check "invalid stored mode behaves as auto and is reported" expect_mode "auto (invalid local value: turbo)"
git config --local --unset harness.mode
: > .git/config.lock
check "mode reports config write failure" expect_exit 1 "$CLI" mode lite
rm .git/config.lock
cd "$WORK" || exit 1
check "project mode requires a repository" expect_exit 2 "$CLI" mode lite
check "global mode works outside a repository" expect_exit 0 "$CLI" mode strict --global
check "mode outside a repository shows the global default" expect_mode 'strict (global)'
git config --global --unset harness.mode
check "help documents mode" expect_exit 0 "$CLI" help
check "help includes mode syntax" contains 'mode [MODE] [--global]'
cd "$WORK/project" || exit 1

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

check "doctor rejects unsupported arguments" expect_exit 2 "$CLI" doctor --quiet
check "help documents doctor" expect_exit 0 "$CLI" help
check "help includes doctor syntax" contains 'doctor'
cd "$HOME" || exit 1
check "doctor dispatches installation diagnostics outside Git" expect_exit 1 "$CLI" doctor
check "doctor diagnoses missing installed canonical link" contains "missing managed symlink: $HOME/.agents/harness"

printf '\n%s passed, %s failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
