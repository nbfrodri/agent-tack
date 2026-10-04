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
  file="$dir/activity.log"
  detail="$(printf '%s' "$detail" | tr '\t\n\r' '   ' | cut -c1-300)"
  # Logged commands may carry tokens, so the log is private to the user. The subshell keeps
  # the umask from leaking into the hook.
  (
    umask 077
    mkdir -p "$dir" 2>/dev/null || exit 0
    [ ! -e "$file" ] || chmod 600 "$file" 2>/dev/null
    printf '%s\t%s\t%s\t%s\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$client" "$cwd" "$event" "$detail" >> "$file" 2>/dev/null || exit 0
    # Keep the log bounded: once it passes the cap, keep the newest half. A per-process temp
    # file keeps hooks that run in parallel from overwriting each other's copy.
    lines="$(wc -l < "$file" | tr -d ' ')"
    if [ "$lines" -gt "$ACTIVITY_LOG_MAX_LINES" ]; then
      tail -n $((ACTIVITY_LOG_MAX_LINES / 2)) "$file" > "$file.$$.tmp" 2>/dev/null && mv "$file.$$.tmp" "$file"
      rm -f "$file.$$.tmp"
    fi
  )
  return 0
}
