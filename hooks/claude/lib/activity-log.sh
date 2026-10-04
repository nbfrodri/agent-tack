#!/usr/bin/env bash
# Opt-in activity log shared by the hooks (`tack config activity-log true`, read with `tack log`).
# activity_log CWD CLIENT EVENT DETAIL appends one tab-separated line; it never fails the hook.

ACTIVITY_LOG_MAX_LINES=5000

activity_log() {
  local cwd="$1" client="$2" event="$3" detail="$4" cli setting dir file lines
  cli="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../bin" 2>/dev/null && pwd)/tack"
  [ -x "$cli" ] || return 0
  setting="$(cd "$cwd" 2>/dev/null && "$cli" config activity-log 2>/dev/null)" || return 0
  [ "${setting%% *}" = true ] || return 0
  dir="${XDG_STATE_HOME:-$HOME/.local/state}/agent-tack"
  mkdir -p "$dir" 2>/dev/null || return 0
  file="$dir/activity.log"
  detail="$(printf '%s' "$detail" | tr '\t\n\r' '   ' | cut -c1-300)"
  printf '%s\t%s\t%s\t%s\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$client" "$cwd" "$event" "$detail" >> "$file" 2>/dev/null || return 0
  # Keep the log bounded: once it passes the cap, keep the newest half.
  lines="$(wc -l < "$file" | tr -d ' ')"
  if [ "$lines" -gt "$ACTIVITY_LOG_MAX_LINES" ]; then
    tail -n $((ACTIVITY_LOG_MAX_LINES / 2)) "$file" > "$file.tmp" 2>/dev/null && mv "$file.tmp" "$file"
  fi
  return 0
}
