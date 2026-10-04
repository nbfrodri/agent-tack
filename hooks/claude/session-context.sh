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

cli="$(cd "$(dirname "$0")/../../bin" && pwd)/tack"
if (cd "$cwd" && "$cli" status --quiet); then
  mode="$(cd "$cwd" && "$cli" mode)" || mode=auto
  mode="${mode%% *}"
  if [ "$mode" = auto ]; then
    level="Before each task, pick the workflow level from the modes below and dev-workflow, and state it in one line; the user can override it."
  else
    level="Apply the $mode mode rules below to every task unless the user asks for another mode."
  fi
  context="tack: ENABLED for this project (mode: $mode). $level At every level: work on a branch off main, test the change, and make a Conventional Commit for each verified milestone. Ask the user whenever you have a real doubt."
  mode_rules="$(cd "$cwd" && "$cli" mode show)" || mode_rules=''
  [ -z "$mode_rules" ] || context="$context"$'\n'"$mode_rules"
  setting() { local value; value="$(cd "$cwd" && "$cli" config "$1" 2>/dev/null)"; printf '%s' "${value%% *}"; }
  tokens=''
  [ "$(setting reply-style)" != terse ] || tokens="$tokens Keep replies terse: what changed, the commit and what is pending, in a few lines."
  [ "$(setting skill-loading)" != minimal ] || tokens="$tokens Load a skill only when the task cannot be done without it; prefer the rules already in context."
  [ "$(setting subagent-model)" != economical ] || tokens="$tokens When delegating, use the most economical model that can do the task."
  [ -z "$tokens" ] || context="$context"$'\n'"Token settings:$tokens"
  project_context="$(cd "$cwd" && "$cli" context)" || project_context=''
  [ -z "$project_context" ] || context="$context"$'\n'"$project_context"
else
  context="tack: NOT enabled for this project. Work normally without the workflow ceremony; only the always-on rules apply (no AI attribution, safety). The user can enable it with 'tack enable'."
fi
if command -v jq >/dev/null 2>&1; then
  jq -cn --arg context "$context" '{hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:$context}}'
elif command -v python3 >/dev/null 2>&1; then
  python3 -c 'import json,sys; print(json.dumps({"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":sys.argv[1]}}))' "$context"
else
  printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"tack: context unavailable; install python3 or jq."}}\n'
fi
