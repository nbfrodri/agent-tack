#!/usr/bin/env bash
# `tack usage`: the 5-hour and weekly usage the Claude Code usage band records, and the one offer
# per window to delegate to Codex once one passes `tack config delegate-usage-percent`.
#   usage set KIND PERCENT [RESETS_AT]   record a reading, KIND five_hour or seven_day (the usage
#                                        band calls this)
#   usage get KIND                       print the last percentage
#   usage threshold                      print the percentage the offer starts at, or nothing when
#                                        the offer is off (setting, cross-delegation, no codex)
#   usage hint                           print the offer for each window past the threshold that
#                                        has not been offered yet, else nothing
set -u

TACK_ROOT="$1"
shift
cli="$TACK_ROOT/bin/tack"
dir="${XDG_STATE_HOME:-$HOME/.local/state}/agent-tack/usage"
FRESH_SECONDS=1800

die() { printf 'tack: %s\n' "$1" >&2; exit 2; }

# percent_ok VALUE: a whole number from 0 to 100.
percent_ok() {
  case "$1" in '' | *[!0-9]*) return 1 ;; esac
  [ "${#1}" -le 3 ] && [ "$1" -le 100 ]
}

kind_ok() { case "$1" in five_hour | seven_day) return 0 ;; esac; return 1; }

# threshold: the percentage to offer from, or empty.
threshold() {
  local value cross
  value="$("$cli" config delegate-usage-percent --get 2>/dev/null)"
  value="${value%% *}"
  percent_ok "$value" && [ "$value" -gt 0 ] || return 0
  cross="$("$cli" config cross-delegation --get 2>/dev/null)"
  [ "${cross%% *}" != off ] || return 0
  command -v codex >/dev/null 2>&1 || return 0
  printf '%s\n' "$value"
}

# offer KIND FROM: prints the offer when KIND's fresh reading is at least FROM and its window has
# not been offered yet, and remembers the window.
offer() {
  local kind="$1" from="$2" label span percent resets seen now window
  case "$kind" in five_hour) label='5-hour' span=18000 ;; *) label=weekly span=604800 ;; esac
  [ -r "$dir/$kind" ] || return 0
  IFS="$(printf '\t')" read -r percent resets seen < "$dir/$kind" || return 0
  percent_ok "$percent" && [ "$percent" -ge "$from" ] || return 0
  case "$seen" in '' | *[!0-9]*) return 0 ;; esac
  now="$(date +%s)"
  [ $((now - seen)) -le "$FRESH_SECONDS" ] || return 0
  # The window is told by its reset time; without one, by the slot the reading falls in.
  window="${resets:-slot$((seen / span))}"
  [ "$(cat "$dir/$kind.offered" 2>/dev/null)" != "$window" ] || return 0
  printf '%s\n' "$window" > "$dir/$kind.offered"
  printf 'Usage: the %s limit is at %s%%. Offer the user, in one line, to hand bounded tasks (wide reading, mechanical edits, a review) to Codex with the cross-delegate skill so this window lasts longer; do it only if they say yes.\n' "$label" "$percent"
}

case "${1:-}" in
  set)
    kind_ok "${2:-}" || die 'usage set takes five_hour|seven_day PERCENT [RESETS_AT]'
    percent_ok "${3:-}" || die 'usage set needs a whole percentage from 0 to 100'
    resets="$(printf '%s' "${4:-}" | tr -cd 'A-Za-z0-9:.+-')"
    (umask 077; mkdir -p "$dir") || die "cannot create $dir"
    tmp="$dir/$2.$$.tmp"
    printf '%s\t%s\t%s\n' "$3" "$resets" "$(date +%s)" > "$tmp" && mv "$tmp" "$dir/$2"
    ;;
  get)
    kind_ok "${2:-}" || die 'usage get takes five_hour|seven_day'
    [ -r "$dir/$2" ] || exit 1
    IFS="$(printf '\t')" read -r percent _ < "$dir/$2" && printf '%s\n' "$percent"
    ;;
  threshold)
    threshold
    ;;
  hint)
    from="$(threshold)"
    [ -n "$from" ] || exit 0
    offer five_hour "$from"
    offer seven_day "$from"
    ;;
  *)
    die 'usage takes set, get, threshold or hint (see --help)'
    ;;
esac
