#!/usr/bin/env bash
# Claude Code SessionStart hook: tells the model whether the full agent-config workflow is
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

cli="$(cd "$(dirname "$0")/../../bin" && pwd)/agent-config"
if (cd "$cwd" && "$cli" status --quiet); then
  context="agent-config: ENABLED for this project. Apply the full workflow from your global instructions (dev-workflow, TDD, conventions, docs, handoffs, AI log)."
else
  context="agent-config: NOT enabled for this project. Work normally without the workflow ceremony; only the always-on rules apply (no AI attribution, safety). The user can enable it with 'agent-config enable'."
fi
printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$context"
