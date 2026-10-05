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
key='' text='' scope='' explicit_global=0
for arg in "$@"; do
  case "$arg" in
    --global) scope=global explicit_global=1 ;;
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

# Values reach awk through the environment: `awk -v` would turn "\n" in a rule into a newline.
# rewrite AWK_PROGRAM: applies an awk program to the store through a private temp file.
rewrite() {
  local tmp
  tmp="$(mktemp "$store.XXXXXX")" || exit 1
  if ! LESSON_KEY="$key" LESSON_SCOPE="$scope" LESSON_TEXT="$text" LESSON_NOW="$(date -u +%Y-%m-%d)" \
      awk -F'\t' -v OFS='\t' "$1" "$store" > "$tmp" || ! mv "$tmp" "$store"; then
    rm -f "$tmp"
    exit 1
  fi
  chmod 600 "$store" 2>/dev/null
}

# exists SCOPE: succeeds when KEY is stored under exactly that scope.
exists() {
  LESSON_KEY="$key" LESSON_SCOPE="$1" awk -F'\t' \
    '$1 == ENVIRON["LESSON_KEY"] && $2 == ENVIRON["LESSON_SCOPE"] { found = 1 } END { exit !found }' "$store"
}

# find_scope: a key named without --global is looked up in this project first, then user-wide.
find_scope() {
  exists "$scope" && return 0
  if [ "$explicit_global" -eq 0 ] && [ "$scope" != global ] && exists global; then scope=global; return 0; fi
  echo "tack: no candidate lesson '$key' in this project or user-wide" >&2
  exit 1
}

MATCH='$1 == ENVIRON["LESSON_KEY"] && $2 == ENVIRON["LESSON_SCOPE"]'
MINE='$2 == "global" || $2 == ENVIRON["LESSON_PROJECT"]'
export LESSON_PROJECT="$project"

case "$command" in
  note)
    need_key
    text="$(printf '%s' "$text" | tr '\t\n\r' '   ')"
    [ -n "$text" ] || usage_error 'lesson note needs the rule text'
    ensure_store
    rewrite "$MATCH"' { $3 += 1; $5 = ENVIRON["LESSON_NOW"]; $6 = ENVIRON["LESSON_TEXT"]; found = 1 } { print }
      END { if (!found) print ENVIRON["LESSON_KEY"], ENVIRON["LESSON_SCOPE"], 1, 0, ENVIRON["LESSON_NOW"], ENVIRON["LESSON_TEXT"] }'
    ;;
  contradict)
    need_key
    ensure_store
    find_scope
    rewrite "$MATCH"' { $4 += 1; $5 = ENVIRON["LESSON_NOW"] } { print }'
    ;;
  forget)
    need_key
    ensure_store
    find_scope
    rewrite '!('"$MATCH"') { print }'
    ;;
  list)
    [ -f "$store" ] || touch "$store" 2>/dev/null
    awk -F'\t' -v seen="$READY_SEEN" -v score="$READY_SCORE" "$MINE"' {
        if (!shown++) printf "%-24s%-9s%-6s%-9s%s\n", "KEY", "SCOPE", "SEEN", "AGAINST", "TEXT"
        ready = ($3 >= seen && $3 - 2 * $4 >= score) ? "ready " : ""
        printf "%-24s%-9s%-6s%-9s%s%s\n", $1, ($2 == "global" ? "global" : "project"), $3, $4, ready, $6
      }
      END { if (!shown) print "No candidate lessons. The lessons skill notes repeated corrections with: tack lesson note KEY \"rule\"" }' \
      "$store" 2>/dev/null || echo 'No candidate lessons.'
    ;;
  top)
    [ -s "$store" ] || exit 0
    case "$key" in '' | *[!0-9]*) usage_error 'lesson top needs a number' ;; esac
    awk -F'\t' -v OFS='\t' -v min="$SHOWN_SCORE" '('"$MINE"') && $3 - 2 * $4 >= min { print $3 - 2 * $4, $3, $6 }' "$store" \
      | sort -t "$(printf '\t')" -k1,1nr | head -n "$key" | awk -F'\t' '{ printf "- %s (seen %s times)\n", $3, $2 }'
    ;;
  *) usage_error "unknown lesson command: $command (note, contradict, list, forget)" ;;
esac
