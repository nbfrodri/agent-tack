#!/usr/bin/env bash
set -uo pipefail
export LC_ALL=C

root="$(cd "$1" && pwd -P)" || exit 2
level="${2:-index}"
remaining=6000
source_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root" || exit 2
# shellcheck source=SCRIPTDIR/project-paths.sh
. "$source_root/lib/project-paths.sh"
load_project_paths "$source_root" || exit 2

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
  # Commits that only touch plans, handoffs or the archive record decisions about the work, not new work.
  commits="$(git -C "$root" rev-list --count --since="@$((since + 1))" HEAD -- . \
    ":(exclude)$TACK_PLANS" ":(exclude)$TACK_HANDOFFS" ':(exclude)docs/archive' 2>/dev/null)" || commits=0
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

if safe_file AGENTS.md; then
  printf 'Project instructions: AGENTS.md (reuse if already loaded; otherwise read for the task).\n'
fi
active=''
active_count=0
matching_count=0
matching=''
current_branch="$(git branch --show-current 2>/dev/null)"
handoffs=()
for file in "$root/$TACK_HANDOFFS"/*.md; do
  relative="${file#"$root"/}"
  safe_file "$relative" || continue
  if grep -qiE '^[-[:space:]]*(\*\*)?Status:(\*\*)?[[:space:]]*(in progress|paused)' "$file"; then
    active="$relative"
    active_count=$((active_count + 1))
    if [ "${#handoffs[@]}" -lt 5 ]; then handoffs+=("$relative"); fi
    # shellcheck disable=SC2016 # Literal Markdown backticks.
    named="$(sed -n 's/^[-[:space:]]*\**Branch:\**[[:space:]]*`\{0,1\}\([^`[:space:]]*\).*/\1/p' "$file" | head -n 1)"
    if [ -n "$current_branch" ] && [ "$named" = "$current_branch" ]; then
      matching="$relative"
      matching_count=$((matching_count + 1))
    fi
  fi
done
if [ "$active_count" -gt 1 ]; then
  active=''
  [ "$matching_count" -ne 1 ] || active="$matching"
  printf '\nParallel work: choose context for this task, not work to resume automatically.\n'
  for file in "${handoffs[@]}"; do
    label="- Active handoff: $file"
    if [ "${#label}" -lt "$remaining" ]; then
      printf '%s\n' "$label"
      remaining=$((remaining - ${#label} - 1))
    fi
  done
  if [ "$active_count" -gt 5 ]; then printf 'More active handoffs: inspect %s as needed.\n' "$TACK_HANDOFFS"; fi
  [ -n "$active" ] || printf 'Choose the handoff relevant to the task; no unique current-branch match.\n'
fi
if [ "$level" = full ]; then
  include "$TACK_ARCHITECTURE" 45
  if [ -n "$active" ]; then include "$active" 40; handoff_freshness "$active"; fi
  exit 0
fi
# The minimal and index levels load documents on demand: an index costs a few lines, not full excerpts.
printf '\n--- Index: read these in full only when the task needs them ---\n'
if [ "$level" != minimal ] && safe_file "$TACK_ARCHITECTURE"; then
  printf -- '- %s (%s lines)\n' "$TACK_ARCHITECTURE" "$(wc -l < "$root/$TACK_ARCHITECTURE" | tr -d ' ')"
fi
if [ -n "$active" ] && safe_file "$active"; then
  printf -- '- Active handoff: %s\n' "$active"
  grep -iE '^[-[:space:]]*(\*\*)?(Status|Next):' "$root/$active" | head -n 4 | cut -c1-300
  handoff_freshness "$active"
fi
