#!/usr/bin/env bash
# Tests the Codex agents step of install.sh and uninstall.sh against throwaway HOME directories.
# Never touches the real HOME or Codex configuration.
# Usage: tests/codex.test.sh
set -uo pipefail
unset XDG_STATE_HOME GIT_CONFIG_GLOBAL XDG_CONFIG_HOME

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/agent-harness-codex-test.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
PASSED=0
FAILED=0
check() {
  if eval "$2"; then printf '  ✔ %s\n' "$1"; PASSED=$((PASSED + 1)); else printf '  ✘ %s\n' "$1"; FAILED=$((FAILED + 1)); fi
}
run() {
  HOME="$H" XDG_CONFIG_HOME="$H/.config" XDG_STATE_HOME="$H/.local/state" GIT_CONFIG_NOSYSTEM=1 \
    GIT_CONFIG_GLOBAL="$H/.gitconfig" bash "$REPO/$1" "${@:2}" > "$WORK/out.log" 2>&1
}
toml_field() {
  python3 -c 'import sys, tomllib; print(tomllib.load(open(sys.argv[1], "rb")).get(sys.argv[2], ""))' "$1" "$2"
}
agent_count="$(find "$REPO/agents" -maxdepth 1 -name '*.md' | wc -l | tr -d ' ')"

echo "Codex agents"
H="$WORK/home"
mkdir -p "$H/.codex/agents"
run bin/tack config agent-roles true --global
printf 'name = "planner"\ndescription = "my own planner"\ndeveloper_instructions = "mine"\n' > "$H/.codex/agents/planner.toml"
check "dry run succeeds" "run install.sh --skip-plugins --dry-run"
check "dry run writes no agents" "[ \"\$(find '$H/.codex/agents' -name '*.toml' | wc -l | tr -d ' ')\" = 1 ]"
check "dry run reports the agents step" "grep -q 'would write Codex agent' '$WORK/out.log'"
check "install succeeds" "run install.sh --skip-plugins"
check "one agent file per harness agent" "[ \"\$(find '$H/.codex/agents' -name '*.toml' | wc -l | tr -d ' ')\" = '$agent_count' ]"
check "agents are valid TOML with the required fields" "[ \"\$(toml_field '$H/.codex/agents/code-reviewer.toml' name)\" = code-reviewer ] && [ -n \"\$(toml_field '$H/.codex/agents/code-reviewer.toml' description)\" ] && toml_field '$H/.codex/agents/code-reviewer.toml' developer_instructions | grep -q 'meticulous senior reviewer'"
check "read-only agents run in a read-only sandbox" "[ \"\$(toml_field '$H/.codex/agents/code-reviewer.toml' sandbox_mode)\" = read-only ]"
check "editing agents inherit the sandbox" "[ -z \"\$(toml_field '$H/.codex/agents/implementer.toml' sandbox_mode)\" ]"
check "an existing user agent is not overwritten" "grep -q 'my own planner' '$H/.codex/agents/planner.toml'"
check "the skipped user agent is reported" "grep -q 'planner.toml exists and is not managed' '$WORK/out.log'"
cp "$H/.codex/agents/docs-writer.toml" "$WORK/docs-writer.before"
check "reinstall succeeds" "run install.sh --skip-plugins"
check "reinstall leaves unchanged agents identical" "cmp -s '$WORK/docs-writer.before' '$H/.codex/agents/docs-writer.toml'"
printf '\n# my tweak\n' >> "$H/.codex/agents/test-writer.toml"
check "reinstall after a user edit succeeds" "run install.sh --skip-plugins"
check "a user-edited agent is preserved on reinstall" "grep -q 'my tweak' '$H/.codex/agents/test-writer.toml'"

run bin/tack config agent-roles false --global
check "disabling roles previews removals without changing files" "run install.sh --skip-plugins --dry-run && [ -e '$H/.codex/agents/code-reviewer.toml' ]"
check "disabling roles removes unchanged generated files" "run install.sh --skip-plugins && [ ! -e '$H/.codex/agents/code-reviewer.toml' ]"
check "disabling roles preserves user and edited definitions" "grep -q 'my tweak' '$H/.codex/agents/test-writer.toml' && grep -q 'my own planner' '$H/.codex/agents/planner.toml'"
run bin/tack config agent-roles true --global
check "re-enabling roles restores missing managed definitions" "run install.sh --skip-plugins && [ -e '$H/.codex/agents/code-reviewer.toml' ]"
echo "Shared user memory at Codex session start"
mkdir -p "$H/.config/agent-tack"
printf -- '- 2026-10-05: Runs the checks with make check.\n' > "$H/.config/agent-tack/memory.md"
codex_session_start() {
  local command
  command="$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))["hooks"]["SessionStart"][0]["hooks"][0]["command"])' "$H/.codex/hooks.json")"
  printf '{"cwd":"%s"}' "$WORK" | HOME="$H" XDG_CONFIG_HOME="$H/.config" XDG_STATE_HOME="$H/.local/state" \
    GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL="$H/.gitconfig" bash -c "$command"
}
check "the installed Codex SessionStart hook loads the shared memory" "codex_session_start | grep -q 'make check'"
check "uninstall succeeds" "run uninstall.sh"
check "unchanged agents are removed" "[ ! -e '$H/.codex/agents/code-reviewer.toml' ] && [ ! -e '$H/.codex/agents/docs-writer.toml' ]"
check "a user-edited agent is kept on uninstall" "grep -q 'my tweak' '$H/.codex/agents/test-writer.toml'"
check "the user's own agent is kept on uninstall" "grep -q 'my own planner' '$H/.codex/agents/planner.toml'"

printf '\n%s passed, %s failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
