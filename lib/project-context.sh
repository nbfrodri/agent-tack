#!/usr/bin/env bash
set -uo pipefail
export LC_ALL=C

root="$1"
mode="${2:-auto}"
remaining=6000

include() {
  local path="$1" limit="$2" line count=0 resolved_dir
  [ -f "$root/$path" ] && [ ! -L "$root/$path" ] || return 0
  resolved_dir="$(cd "$(dirname "$root/$path")" && pwd -P)" || return 0
  case "$resolved_dir/" in "$root/"*) ;; *) return 0 ;; esac
  [ "$remaining" -gt 0 ] || return 0
  printf '\n--- %s ---\n' "$path"
  while IFS= read -r line || [ -n "$line" ]; do
    if [ "$count" -ge "$limit" ] || [ "${#line}" -ge "$remaining" ]; then
      printf '[Context truncated; read %s for the full document.]\n' "$path"
      break
    fi
    printf '%s\n' "$line"
    remaining=$((remaining - ${#line} - 1))
    count=$((count + 1))
  done < "$root/$path"
}

safe_file() {
  [ -f "$root/$1" ] && [ ! -L "$root/$1" ] || return 1
  case "$(cd "$(dirname "$root/$1")" && pwd -P)/" in "$root/"*) return 0 ;; *) return 1 ;; esac
}

include AGENTS.md 45
# Lite tasks rarely need architecture or handoffs; skipping them keeps startup cheap.
[ "$mode" != lite ] || exit 0
active=''
for file in "$root"/docs/handoffs/*.md; do
  if [ ! -f "$file" ] || [ -L "$file" ]; then continue; fi
  if grep -qiE '^[-[:space:]]*(\*\*)?Status:(\*\*)?[[:space:]]*(in progress|paused)' "$file"; then
    active="${file#"$root"/}"
  fi
done
if [ "$mode" = strict ]; then
  include docs/architecture.md 45
  [ -z "$active" ] || include "$active" 40
  exit 0
fi
# Other modes load documents on demand: an index costs a few lines instead of full excerpts.
printf '\n--- Index: read these in full only when the task needs them ---\n'
if safe_file docs/architecture.md; then
  printf -- '- docs/architecture.md (%s lines)\n' "$(wc -l < "$root/docs/architecture.md" | tr -d ' ')"
fi
if [ -n "$active" ] && safe_file "$active"; then
  printf -- '- Active handoff: %s\n' "$active"
  grep -iE '^[-[:space:]]*(\*\*)?(Status|Next):' "$root/$active" | head -n 4 | cut -c1-300
fi
