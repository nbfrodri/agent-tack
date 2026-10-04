#!/usr/bin/env bash
# Claude Code SessionStart hook: tells the model whether the tack workflow is
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

client=claude
[ "${1:-}" != --codex ] || client=codex
# shellcheck source=SCRIPTDIR/lib/activity-log.sh
. "$(dirname "$0")/lib/activity-log.sh"

cli="$(cd "$(dirname "$0")/../../bin" && pwd)/tack"

# Per-session state (tool-call counters) is pruned here: SessionStart is the one hook every
# tool runs, whether or not the project is enabled.
retention="$(cd "$cwd" && "$cli" config state-retention-days 2>/dev/null)"
retention="${retention%% *}"
case "$retention" in '' | *[!0-9]*) retention=30 ;; esac
state_dir="${XDG_STATE_HOME:-$HOME/.local/state}/agent-tack/budget"
[ ! -d "$state_dir" ] || find "$state_dir" -type f -mtime +"$retention" -exec rm -f {} + 2>/dev/null

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
  workflow=''
  [ "$(setting ci-watch)" != false ] || workflow="$workflow Do not wait for CI after a push unless the user asks; merges still need green checks."
  [ -z "$workflow" ] || context="$context"$'\n'"Workflow settings:$workflow"
  activity_log "$cwd" "$client" session-start "mode=$mode"
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
