#!/usr/bin/env bash
# Claude Code PreToolUse hook for the Agent tool: refuses a subagent launched without an explicit
# model and effort, so the assistant offers the user the choice (orchestrate) instead of
# inheriting the main model by accident. A fork is exempt: it inherits both and cannot set them.
# Silent in disabled projects, when listed in `tack config disabled-hooks`, and whenever it cannot
# read the input; never fails the call because of its own errors.
set -u

input="$(cat)"
field() {
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$input" | jq -r --arg k "$1" '(if $k == "cwd" then .cwd else .tool_input[$k] end) // empty | strings' 2>/dev/null
  elif command -v python3 >/dev/null 2>&1; then
    printf '%s' "$input" | python3 -c 'import json, sys
try:
    data = json.load(sys.stdin)
    value = data.get("cwd") if sys.argv[1] == "cwd" else data.get("tool_input", {}).get(sys.argv[1])
except Exception:
    value = None
print(value if isinstance(value, str) else "")' "$1" 2>/dev/null
  fi
}

cwd="$(field cwd)"
[ -n "$cwd" ] && [ -d "$cwd" ] || exit 0
# shellcheck source=SCRIPTDIR/lib/hook-control.sh
. "$(dirname "$0")/lib/hook-control.sh"
! hook_disabled "$cwd" agent-model || exit 0
cli="$(cd "$(dirname "$0")/../../bin" && pwd)/tack"
cd "$cwd" || exit 0
"$cli" status --quiet || exit 0

[ "$(field subagent_type)" != fork ] || exit 0
[ -z "$(field model)" ] || [ -z "$(field effort)" ] || exit 0

reason="Subagents need an explicit model and effort. Before launching, load the orchestrate skill, offer the user options for each subagent (tier, its model from tack models TIER, and effort low, medium or high), recommend one, and launch with the model and effort the user picks."
if command -v jq >/dev/null 2>&1; then
  jq -cn --arg r "$reason" '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "deny", permissionDecisionReason: $r}}'
else
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$reason"
fi
