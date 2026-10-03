#!/usr/bin/env bash
# Claude Code SessionStart hook: tells the model whether the full agent-harness workflow is
# enabled for the project it starts in. Never fails the session.
set -u

input="$(cat)"
cwd=""
if command -v jq >/dev/null 2>&1; then
  cwd="$(printf '%s' "$input" | jq -r '.cwd // empty' 2>/dev/null)"
elif command -v python3 >/dev/null 2>&1; then
  cwd="$(printf '%s' "$input" | python3 -c 'import json, sys; print(json.load(sys.stdin).get("cwd") or "")' 2>/dev/null)"
fi
[ -n "$cwd" ] && [ -d "$cwd" ] || cwd="$PWD"

cli="$(cd "$(dirname "$0")/../../bin" && pwd)/harness"
if (cd "$cwd" && "$cli" status --quiet); then
  context="harness: ENABLED for this project. Apply the full workflow from your global instructions (dev-workflow, TDD, conventions, docs, handoffs, AI log)."
  project_context="$(cd "$cwd" && "$cli" context)" || project_context=''
  [ -z "$project_context" ] || context="$context"$'\n'"$project_context"
else
  context="harness: NOT enabled for this project. Work normally without the workflow ceremony; only the always-on rules apply (no AI attribution, safety). The user can enable it with 'harness enable'."
fi
if command -v jq >/dev/null 2>&1; then
  jq -cn --arg context "$context" '{hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:$context}}'
elif command -v python3 >/dev/null 2>&1; then
  python3 -c 'import json,sys; print(json.dumps({"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":sys.argv[1]}}))' "$context"
else
  printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"harness: context unavailable; install python3 or jq."}}\n'
fi
