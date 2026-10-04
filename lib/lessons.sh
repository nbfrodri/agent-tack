#!/usr/bin/env bash
# `tack lesson`: candidate lessons counted across sessions (docs/adr/0001-candidate-lessons.md).
#   note KEY TEXT [--global]       record a sighting of a correction (a repeat adds to its count)
#   contradict KEY [--global]      record evidence against it
#   list                           this project's and the user-wide candidates
#   forget KEY [--global]          remove one (after it was saved as a rule or declined)
#   top N                          the N strongest candidates, for the session start context
# Storage: one tab-separated line per candidate (key, scope, seen, against, updated, text) in
# the state directory, private to the user.
# shellcheck disable=SC2016 # The single-quoted arguments are awk programs; $1 is an awk field.
set -u
export LC_ALL=C

usage_error() { printf 'tack: %s (see --help)\n' "$1" >&2; exit 2; }
store="${XDG_STATE_HOME:-$HOME/.local/state}/agent-tack/lessons.tsv"
READY_SEEN=3
READY_SCORE=3
SHOWN_SCORE=2

command="${1:-list}"
[ "$#" -eq 0 ] || shift
key='' text='' scope=''
for arg in "$@"; do
  case "$arg" in
    --global) scope=global ;;
    -*) usage_error "unknown option for lesson: $arg" ;;
    *) if [ -z "$key" ]; then key="$arg"; elif [ -z "$text" ]; then text="$arg"; else usage_error 'too many arguments for lesson'; fi ;;
  esac
done
if [ -z "$scope" ]; then
  scope="$(git rev-parse --show-toplevel 2>/dev/null)" || scope=global
fi
project="$(git rev-parse --show-toplevel 2>/dev/null)" || project=''

ensure_store() {
  (umask 077; mkdir -p "$(dirname "$store")" && touch "$store") || { echo "tack: cannot write $store" >&2; exit 1; }
  chmod 600 "$store" 2>/dev/null
}

need_key() {
  [ -n "$key" ] || usage_error "lesson $command needs a key"
  case "$key" in *[!a-z0-9-]* | -* ) usage_error "lesson keys are kebab-case, such as use-pnpm: $key" ;; esac
}

# rewrite AWK_PROGRAM: applies an awk program to the store through a private temp file.
rewrite() {
  local tmp
  tmp="$(mktemp "$store.XXXXXX")" || exit 1
  if ! awk -F'\t' -v OFS='\t' -v key="$key" -v scope="$scope" -v text="$text" -v now="$(date -u +%Y-%m-%d)" "$1" "$store" > "$tmp" \
    || ! mv "$tmp" "$store"; then
    rm -f "$tmp"
    exit 1
  fi
  chmod 600 "$store" 2>/dev/null
}

case "$command" in
  note)
    need_key
    text="$(printf '%s' "$text" | tr '\t\n\r' '   ')"
    [ -n "$text" ] || usage_error 'lesson note needs the rule text'
    ensure_store
    rewrite '$1 == key && $2 == scope { $3 += 1; $5 = now; $6 = text; found = 1 } { print }
             END { if (!found) print key, scope, 1, 0, now, text }'
    ;;
  contradict)
    need_key
    ensure_store
    grep -q "^$key	$scope	" "$store" || { echo "tack: no candidate lesson '$key' here" >&2; exit 1; }
    rewrite '$1 == key && $2 == scope { $4 += 1; $5 = now } { print }'
    ;;
  forget)
    need_key
    ensure_store
    grep -q "^$key	$scope	" "$store" || { echo "tack: no candidate lesson '$key' here" >&2; exit 1; }
    rewrite '!($1 == key && $2 == scope) { print }'
    ;;
  list)
    [ -s "$store" ] || { echo "No candidate lessons. The lessons skill notes repeated corrections with: tack lesson note KEY \"rule\""; exit 0; }
    printf '%-24s%-9s%-6s%-9s%s\n' KEY SCOPE SEEN AGAINST TEXT
    awk -F'\t' -v project="$project" -v seen="$READY_SEEN" -v score="$READY_SCORE" '
      $2 == "global" || $2 == project {
        ready = ($3 >= seen && $3 - 2 * $4 >= score) ? "ready " : ""
        printf "%-24s%-9s%-6s%-9s%s%s\n", $1, ($2 == "global" ? "global" : "project"), $3, $4, ready, $6
      }' "$store"
    ;;
  top)
    [ -s "$store" ] || exit 0
    case "$key" in '' | *[!0-9]*) usage_error 'lesson top needs a number' ;; esac
    awk -F'\t' -v OFS='\t' -v project="$project" -v min="$SHOWN_SCORE" '
      ($2 == "global" || $2 == project) && $3 - 2 * $4 >= min { print $3 - 2 * $4, $3, $6 }' "$store" \
      | sort -t "$(printf '\t')" -k1,1nr | head -n "$key" | awk -F'\t' '{ printf "- %s (seen %s times)\n", $3, $2 }'
    ;;
  *) usage_error "unknown lesson command: $command (note, contradict, list, forget)" ;;
esac
