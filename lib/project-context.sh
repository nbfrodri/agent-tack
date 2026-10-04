#!/usr/bin/env bash
set -uo pipefail
export LC_ALL=C

root="$1"
level="${2:-index}"
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

modified_at() { stat -c %Y "$1" 2>/dev/null || stat -f %m "$1"; }

# Compares the handoff with git so a resumed session knows whether it can trust it.
handoff_freshness() {
  local path="$root/$1" since committed commits named current
  since="$(modified_at "$path")" || return 0
  # A commit that includes the handoff updates it too, whatever the file's mtime says.
  committed="$(git -C "$root" log -1 --format=%ct -- "$1" 2>/dev/null)"
  [ -z "$committed" ] || [ "$committed" -le "$since" ] || since="$committed"
  # Commits that only touch plans or handoffs record decisions about the work, not new work.
  commits="$(git -C "$root" rev-list --count --since="@$((since + 1))" HEAD -- . \
    ':(exclude)docs/plans' ':(exclude)docs/handoffs' 2>/dev/null)" || commits=0
  # shellcheck disable=SC2016 # The backticks are literal Markdown, not command substitution.
  named="$(sed -n 's/^[-[:space:]]*\**Branch:\**[[:space:]]*`\{0,1\}\([^`[:space:]]*\).*/\1/p' "$path" | head -n 1)"
  current="$(git -C "$root" branch --show-current 2>/dev/null)"
  if [ -n "$named" ] && [ -n "$current" ] && [ "$named" != "$current" ]; then
    printf 'Handoff check: handoff names branch %s; current branch is %s. Confirm which work to resume.\n' "$named" "$current"
  elif [ "$commits" -gt 0 ]; then
    printf 'Handoff check: may be stale: %s commit(s) since its last update. Compare it with git log and git status, and refresh it before continuing.\n' "$commits"
  else
    printf 'Handoff check: up to date: no commits since its last update. Still compare it with git status before continuing.\n'
  fi
}

include AGENTS.md 45
active=''
for file in "$root"/docs/handoffs/*.md; do
  if [ ! -f "$file" ] || [ -L "$file" ]; then continue; fi
  if grep -qiE '^[-[:space:]]*(\*\*)?Status:(\*\*)?[[:space:]]*(in progress|paused)' "$file"; then
    active="${file#"$root"/}"
  fi
done
if [ "$level" = full ]; then
  include docs/architecture.md 45
  if [ -n "$active" ]; then include "$active" 40; handoff_freshness "$active"; fi
  exit 0
fi
# The minimal and index levels load documents on demand: an index costs a few lines, not full excerpts.
printf '\n--- Index: read these in full only when the task needs them ---\n'
if [ "$level" != minimal ] && safe_file docs/architecture.md; then
  printf -- '- docs/architecture.md (%s lines)\n' "$(wc -l < "$root/docs/architecture.md" | tr -d ' ')"
fi
if [ -n "$active" ] && safe_file "$active"; then
  printf -- '- Active handoff: %s\n' "$active"
  grep -iE '^[-[:space:]]*(\*\*)?(Status|Next):' "$root/$active" | head -n 4 | cut -c1-300
  handoff_freshness "$active"
fi
