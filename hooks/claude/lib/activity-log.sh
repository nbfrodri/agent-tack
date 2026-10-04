#!/usr/bin/env bash
# Opt-in activity log shared by the hooks (`tack config activity-log true`, read with `tack log`).
# activity_log CWD CLIENT EVENT DETAIL appends one tab-separated line; it never fails the hook.

ACTIVITY_LOG_MAX_LINES=20000

# activity_log_enabled DIR: succeeds when `tack config activity-log` is true for DIR.
activity_log_enabled() {
  local cli setting
  cli="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../bin" 2>/dev/null && pwd)/tack"
  [ -x "$cli" ] || return 1
  setting="$(cd "$1" 2>/dev/null && "$cli" config activity-log 2>/dev/null)" || return 1
  [ "${setting%% *}" = true ]
}

# start_turns DIR CLIENT SESSION TRANSCRIPT: at session start, marks where the transcript ends,
# so record_turn counts only what this session adds.
start_turns() {
  local session="$3" transcript="$4" dir
  case "$session" in '' | *[!A-Za-z0-9_-]*) return 0 ;; esac
  [ -f "$transcript" ] && command -v python3 >/dev/null 2>&1 || return 0
  activity_log_enabled "$1" || return 0
  dir="${XDG_STATE_HOME:-$HOME/.local/state}/agent-tack/turns"
  (umask 077; mkdir -p "$dir") 2>/dev/null || return 0
  python3 "$(dirname "${BASH_SOURCE[0]}")/turn-report.py" "$transcript" "$2" fixed "$dir/$session" --init 2>/dev/null
  return 0
}

# record_turn DIR CLIENT SESSION TRANSCRIPT: logs tokens, skills, agents and the stated level
# from the transcript lines added since the last stop of SESSION (lib/turn-report.py).
record_turn() {
  local cwd="$1" client="$2" session="$3" transcript="$4" cli mode=fixed dir event detail
  case "$session" in '' | *[!A-Za-z0-9_-]*) return 0 ;; esac
  [ -f "$transcript" ] && command -v python3 >/dev/null 2>&1 || return 0
  activity_log_enabled "$cwd" || return 0
  cli="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../bin" 2>/dev/null && pwd)/tack"
  # Only an enabled project in auto expects a stated level per task.
  if (cd "$cwd" && "$cli" status --quiet) 2>/dev/null; then
    mode="$(cd "$cwd" && "$cli" mode 2>/dev/null)"
    mode="${mode%% *}"
  fi
  dir="${XDG_STATE_HOME:-$HOME/.local/state}/agent-tack/turns"
  (umask 077; mkdir -p "$dir") 2>/dev/null || return 0
  python3 "$(dirname "${BASH_SOURCE[0]}")/turn-report.py" "$transcript" "$client" "${mode:-fixed}" "$dir/$session" 2>/dev/null \
    | while IFS="$(printf '\t')" read -r event detail; do
        activity_log "$cwd" "$client" "$event" "$detail"
      done
  return 0
}

activity_log() {
  local cwd="$1" client="$2" event="$3" detail="$4" dir file lines
  activity_log_enabled "$cwd" || return 0
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
