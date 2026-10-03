#!/usr/bin/env bash
set -uo pipefail
export LC_ALL=C

root="$1"
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

include AGENTS.md 45
include docs/architecture.md 45
active=''
for file in "$root"/docs/handoffs/*.md; do
  [ -f "$file" ] && [ ! -L "$file" ] || continue
  if grep -qiE '^[-[:space:]]*(\*\*)?Status:(\*\*)?[[:space:]]*(in progress|paused)' "$file"; then
    active="${file#"$root"/}"
  fi
done
[ -z "$active" ] || include "$active" 40
