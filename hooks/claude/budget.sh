#!/usr/bin/env bash
# Claude Code PreToolUse hook for every tool: in a project-only mode such as unleash, refuses
# tool calls once the session passes `tack config unleash-max-tool-calls`.
# Silent and allowing in every other case; never fails the call because of its own errors.
set -u

input="$(cat)"
json_field() {
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$input" | jq -r "$1 // empty" 2>/dev/null
  elif command -v python3 >/dev/null 2>&1; then
    printf '%s' "$input" | python3 -c 'import json, sys
try:
    value = json.load(sys.stdin).get(sys.argv[1].lstrip("."))
except Exception:
    value = None
print(value if isinstance(value, str) else "")' "$1" 2>/dev/null
  fi
}

session="$(json_field .session_id)"
cwd="$(json_field .cwd)"
case "$session" in '' | *[!A-Za-z0-9_-]*) exit 0 ;; esac
[ -n "$cwd" ] && [ -d "$cwd" ] || exit 0

cli="$(cd "$(dirname "$0")/../../bin" && pwd)/tack"
cd "$cwd" || exit 0
"$cli" status --quiet || exit 0
case "$("$cli" mode show 2>/dev/null)" in WARNING:*) ;; *) exit 0 ;; esac
limit="$("$cli" config unleash-max-tool-calls 2>/dev/null)"
limit="${limit%% *}"
case "$limit" in '' | *[!0-9]*) exit 0 ;; esac

dir="${XDG_STATE_HOME:-$HOME/.local/state}/agent-harness/budget"
mkdir -p "$dir" 2>/dev/null || exit 0
count="$(cat "$dir/$session" 2>/dev/null || echo 0)"
case "$count" in '' | *[!0-9]*) count=0 ;; esac
count=$((count + 1))
printf '%s\n' "$count" > "$dir/$session" 2>/dev/null || exit 0
[ "$count" -gt "$limit" ] || exit 0

reason="This autonomous session reached its limit of $limit tool calls (tack config unleash-max-tool-calls). Stop, update the handoff and summarise what is done, what is pending and the assumptions made."
if command -v jq >/dev/null 2>&1; then
  jq -cn --arg r "$reason" '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "deny", permissionDecisionReason: $r}}'
else
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$reason"
fi
