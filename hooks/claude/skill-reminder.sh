#!/usr/bin/env bash
# UserPromptSubmit hook: with each message, names the skills of the project's active sets and asks
# the assistant to load the ones that match. Measured on small real tasks, an assistant that only
# has the skills listed at session start does not open them, and one reminded next to the request
# loads the matching ones. Also says which sets fit the project's files, or the words of the
# message (`ask` rules in sets.txt), and are not active, for the assistant to tell the user.
# Also carries the once-per-window offer to delegate to Codex when the 5-hour usage runs high
# (`tack usage hint`).
# Advisory: silent in disabled projects, when listed in `tack config disabled-hooks`, and when
# there is nothing to say. Never fails the message.
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
[ -n "$cwd" ] && [ -d "$cwd" ] || exit 0
command -v python3 >/dev/null 2>&1 || exit 0
# shellcheck source=SCRIPTDIR/lib/hook-control.sh
. "$(dirname "$0")/lib/hook-control.sh"
! hook_disabled "$cwd" skill-reminder || exit 0
root="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$cwd" || exit 0
"$root/bin/tack" status --quiet || exit 0

reminder="$(printf '%s' "$input" | python3 "$root/lib/sets.py" "$root" reminder --stdin 2>/dev/null)"
# Once per 5-hour window past delegate-usage-percent: offer the user to hand tasks to Codex.
offer="$("$root/bin/tack" usage hint 2>/dev/null)"
[ -z "$offer" ] || reminder="${reminder:+$reminder }$offer"
[ -n "$reminder" ] || exit 0
python3 -c 'import json, sys
print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": sys.argv[1]}}, separators=(",", ":")))' "$reminder"
