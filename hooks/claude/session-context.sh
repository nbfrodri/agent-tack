#!/usr/bin/env bash
# Claude Code SessionStart hook: tells the model whether the tack workflow is
# enabled for the project it starts in. Never fails the session.
set -u

input="$(cat)"
field() {
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
cwd="$(field .cwd)"
[ -n "$cwd" ] && [ -d "$cwd" ] || cwd="$PWD"

client=claude
[ "${1:-}" != --codex ] || client=codex
# shellcheck source=SCRIPTDIR/lib/activity-log.sh
. "$(dirname "$0")/lib/activity-log.sh"
cli="$(cd "$(dirname "$0")/../../bin" && pwd)/tack"

# Per-session state (tool-call counters) is pruned here: SessionStart is the one hook every
# tool runs, whether or not the project is enabled. It is maintenance, so it runs even when
# the session-context hook is turned off, and its period is user-wide because the state is.
retention="$(cd "$cwd" && "$cli" config state-retention-days 2>/dev/null)"
retention="${retention%% *}"
case "$retention" in '' | *[!0-9]*) retention=30 ;; esac
for state_dir in budget turns; do
  state_dir="${XDG_STATE_HOME:-$HOME/.local/state}/agent-tack/$state_dir"
  [ ! -d "$state_dir" ] || find "$state_dir" -type f -mtime +"$retention" -exec rm -f {} + 2>/dev/null
done
# Turn metrics start counting from here, so earlier history is not logged as new work.
start_turns "$cwd" "$client" "$(field .session_id)" "$(field .transcript_path)"

# shellcheck source=SCRIPTDIR/lib/hook-control.sh
. "$(dirname "$0")/lib/hook-control.sh"
! hook_disabled "$cwd" session-context || exit 0

# The user's own notes, shared with Codex; loaded in every project (docs/adr/0002-shared-memory.md).
memory="$(cd "$cwd" && "$cli" memory context 2>/dev/null)" || memory=''

if (cd "$cwd" && "$cli" status --quiet); then
  mode="$(cd "$cwd" && "$cli" mode)" || mode=auto
  mode="${mode%% *}"
  if [ "$mode" = auto ]; then
    level="Before each task, pick the workflow level from the modes below and dev-workflow, and state it in one line; the user can override it."
  else
    level="Apply the $mode mode rules below to every task unless the user asks for another mode."
  fi
  head="tack: ENABLED for this project (mode: $mode). $level At every level: work on a branch off main, test the change, and make a Conventional Commit for each verified milestone. Ask the user whenever you have a real doubt."
  mode_rules="$(cd "$cwd" && "$cli" mode show)" || mode_rules=''
  setting() { local value; value="$(cd "$cwd" && "$cli" config "$1" 2>/dev/null)"; printf '%s' "${value%% *}"; }
  tokens=''
  [ "$(setting skill-loading)" != minimal ] || tokens="$tokens Load a skill only when the task cannot be done without it; prefer the rules already in context."
  [ "$(setting subagent-model)" != economical ] || tokens="$tokens When delegating, use the most economical model that can do the task."
  workflow=''
  [ "$(setting ci-watch)" != false ] || workflow="$workflow Do not wait for CI after a push unless the user asks; merges still need green checks."
  [ "$(setting visual-review)" != false ] || workflow="$workflow Skip the visual review (tack shots and the ui-reviewer score) for UI changes."
  settings="$(bash "${cli%/bin/tack}/lib/reply-style.sh" "$(setting reply-style)")"
  [ -z "$tokens" ] || settings="${settings:+$settings$'\n'}Token settings:$tokens"
  [ -z "$workflow" ] || settings="${settings:+$settings$'\n'}Workflow settings:$workflow"
  activity_log "$cwd" "$client" session-start "mode=$mode"
  project_context="$(cd "$cwd" && "$cli" context)" || project_context=''
  # Corrections seen repeatedly but not yet saved as rules (docs/adr/0001-candidate-lessons.md).
  lessons="$(cd "$cwd" && "$cli" lesson top 3 2>/dev/null)" || lessons=''
  [ -z "$lessons" ] || lessons="Candidate lessons (corrections seen repeatedly, not yet confirmed as rules; follow them when they fit and ask before saving one):"$'\n'"$lessons"

  context="$head"
  for part in "$mode_rules" "$settings" "$memory" "$project_context" "$lessons"; do
    [ -z "$part" ] || context="$context"$'\n'"$part"
  done
  # context-max-chars: past the cap, keep parts by priority (activation line, settings, mode
  # rules, user memory, project context, candidate lessons), trim the first that does not fit and say where the rest is. The
  # activation line always stays; the pointer is dropped when even it does not fit.
  cap="$(setting context-max-chars)"
  case "$cap" in '' | *[!0-9]*) cap=0 ;; esac
  if [ "$cap" -gt 0 ] && [ "${#context}" -gt "$cap" ]; then
    pointer="[Context capped at $cap characters by tack config context-max-chars; run 'tack mode show', 'tack memory' and 'tack context' for the rest.]"
    [ $((${#head} + ${#pointer} + 1)) -le "$cap" ] || pointer=''
    remaining=$((cap - ${#head} - ${#pointer} - 1))
    context="$head"
    for part in "$settings" "$mode_rules" "$memory" "$project_context" "$lessons"; do
      if [ -z "$part" ] || [ "$remaining" -le 1 ]; then continue; fi
      if [ $((${#part} + 1)) -le "$remaining" ]; then
        context="$context"$'\n'"$part"
        remaining=$((remaining - ${#part} - 1))
      else
        context="$context"$'\n'"${part:0:$((remaining - 1))}"
        remaining=0
      fi
    done
    [ -z "$pointer" ] || context="$context"$'\n'"$pointer"
  fi
else
  context="tack: NOT enabled for this project. Work normally without the workflow ceremony; only the always-on rules apply (no AI attribution, safety). The user can enable it with 'tack enable'."
  [ -z "$memory" ] || context="$context"$'\n'"$memory"
fi
if command -v jq >/dev/null 2>&1; then
  jq -cn --arg context "$context" '{hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:$context}}'
elif command -v python3 >/dev/null 2>&1; then
  python3 -c 'import json,sys; print(json.dumps({"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":sys.argv[1]}}))' "$context"
else
  printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"tack: context unavailable; install python3 or jq."}}\n'
fi
