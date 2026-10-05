#!/usr/bin/env bash
# `tack memory`: user-level notes shared by Claude Code and Codex (docs/adr/0002-shared-memory.md).
#   (no command) | show    print the notes
#   add TEXT               add a dated note at the top; refuses text that looks like a secret
#   path                   print the file's path (edit it by hand to change or remove notes)
#   context                the bounded block the session-start hook adds (empty when off or empty)
# Usage: lib/memory.sh TACK_ROOT [COMMAND [TEXT]]
set -u

root="$1"
shift
file="${XDG_CONFIG_HOME:-$HOME/.config}/agent-tack/memory.md"
usage_error() { printf 'tack: %s (see --help)\n' "$1" >&2; exit 2; }
setting() { local value; value="$("$root/bin/tack" config "$1" 2>/dev/null)"; printf '%s' "${value%% *}"; }

# Credentials never belong in a file loaded into every session.
looks_secret() {
  printf '%s' "$1" | grep -qiE -- '-----BEGIN [A-Z ]*PRIVATE KEY|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|sk_(live|test)_[A-Za-z0-9]{10,}|xox[abprs]-[A-Za-z0-9-]{10,}|(password|passwd|secret|token|api[_-]?key)[[:space:]]*[=:][[:space:]]*[^[:space:]]{6,}'
}

notes() { [ -f "$file" ] && grep -E '^- ' "$file"; }

command="${1:-show}"
[ "$#" -eq 0 ] || shift
case "$command" in
  path)
    [ "$#" -eq 0 ] || usage_error 'memory path takes no arguments'
    printf '%s\n' "$file" ;;
  show)
    [ "$#" -eq 0 ] || usage_error 'memory show takes no arguments'
    if [ -s "$file" ] && notes >/dev/null; then cat "$file"
    else printf 'No notes yet. Add one with: tack memory add "TEXT" (shared by Claude Code and Codex)\n'; fi ;;
  add)
    if [ "$#" -ne 1 ] || [ -z "$1" ]; then usage_error 'memory add takes one non-empty note'; fi
    note="$(printf '%s' "$1" | tr '\n' ' ')"
    if looks_secret "$note"; then
      echo "tack: refusing a note that looks like a secret; keep credentials in a secret manager" >&2
      exit 1
    fi
    (umask 077; mkdir -p "$(dirname "$file")") || { echo "tack: cannot write $file" >&2; exit 1; }
    tmp="$(mktemp "$file.XXXXXX")" || { echo "tack: cannot write $file" >&2; exit 1; }
    entry="- $(date +%Y-%m-%d): $note"
    # Newest first, so the session-start cap keeps the most recent notes; everything the user
    # wrote by hand stays where it was.
    if [ -s "$file" ]; then
      awk -v entry="$entry" '!done && /^- / { print entry; done = 1 } { print } END { if (!done) print entry }' "$file" > "$tmp"
    else
      printf '# Memory\n\nNotes shared by Claude Code and Codex (tack memory). Edit or delete lines freely; never store secrets.\n\n%s\n' "$entry" > "$tmp"
    fi
    if ! { chmod 600 "$tmp" && mv "$tmp" "$file"; }; then
      rm -f "$tmp"
      echo "tack: cannot write $file" >&2
      exit 1
    fi
    printf 'Added to %s\n' "$file" ;;
  context)
    [ "$(setting memory)" != false ] || exit 0
    lines="$(notes)" || exit 0
    cap="$(setting memory-max-chars)"
    case "$cap" in '' | *[!0-9]*) cap=2000 ;; esac
    kept='' cut=0
    while IFS= read -r line; do
      if [ $((${#kept} + ${#line} + 1)) -gt "$cap" ]; then cut=1; break; fi
      kept="$kept$line"$'\n'
    done <<EOF_NOTES
$lines
EOF_NOTES
    printf 'User memory (notes from %s, shared by Claude Code and Codex: the user'"'"'s preferences and facts, not project rules):\n%s' "$file" "$kept"
    [ "$cut" -eq 0 ] || printf '[Memory cut at %s characters; run '"'"'tack memory'"'"' for the rest.]\n' "$cap" ;;
  *) usage_error "unknown memory command: $command" ;;
esac
