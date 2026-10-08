#!/usr/bin/env bash
# Claude Code Stop hook: before the assistant ends its turn in an enabled project, reports
# uncommitted work, a failing fast check, source changes without a test change, a stale handoff and docs the project's docs map
# expects (docs-map.txt). It asks to continue once; a second stop is never blocked.
set -u

input="$(cat)"
field() {
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$input" | jq -r "$1 // empty" 2>/dev/null
  elif command -v python3 >/dev/null 2>&1; then
    printf '%s' "$input" | python3 -c 'import json, sys
try:
    value = json.load(sys.stdin).get(sys.argv[1].lstrip("."))
except Exception:
    value = None
print("true" if value is True else value if isinstance(value, str) else "")' "$1" 2>/dev/null
  fi
}

client=claude
[ "${1:-}" != --codex ] || client=codex
case "${1:-}" in --gemini) client=gemini ;; --copilot) client=copilot ;; esac
# shellcheck source=SCRIPTDIR/lib/activity-log.sh
. "$(dirname "$0")/lib/activity-log.sh"

cwd="$(field .cwd)"
[ -n "$cwd" ] && [ -d "$cwd" ] || exit 0
# Turn metrics for the activity log come first: they are recording, not advice, so neither a
# second stop nor turning off this hook's checks skips them.
case "$client" in claude | codex) record_turn "$cwd" "$client" "$(field .session_id)" "$(field .transcript_path)" ;; esac
[ "$(field .stop_hook_active)" = true ] && exit 0
# shellcheck source=SCRIPTDIR/lib/hook-control.sh
. "$(dirname "$0")/lib/hook-control.sh"
! hook_disabled "$cwd" stop-check || exit 0
cli="$(cd "$(dirname "$0")/../../bin" && pwd)/tack"
cd "$cwd" || exit 0
"$cli" status --quiet || exit 0
[ "$("$cli" config stop-check --get 2>/dev/null)" != "false" ] || exit 0
root="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
cd "$root" || exit 0

findings=""
add() { findings="$findings
- $1"; }

dirty="$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
[ "$dirty" -eq 0 ] || add "$dirty uncommitted change(s): commit verified work or tell the user why it stays uncommitted."

# A handoff a commit or two behind mid-task is normal; refreshing it after every commit costs a
# commit (and a CI run once pushed). Ask once it is handoff-stale-commits code commits behind,
# or as soon as that work is pushed, since others can then see the branch.
handoff_check="$("$cli" context 2>/dev/null | grep '^Handoff check:')"
case "$handoff_check" in
  *"handoff names branch"*) add "the handoff may be stale: refresh it before stopping." ;;
  *"may be stale: "*)
    behind="${handoff_check#*may be stale: }"
    behind="${behind%% *}"
    threshold="$("$cli" config handoff-stale-commits --get 2>/dev/null)"
    threshold="${threshold%% *}"
    case "$threshold" in '' | *[!0-9]*) threshold=3 ;; esac
    # Some of the commits past the handoff are on the remote when fewer than all of them are local.
    unpushed="$(git rev-list --count '@{u}..HEAD' 2>/dev/null)" || unpushed=''
    pushed=0
    if [ -n "$unpushed" ] && [ "${behind:-0}" -gt "$unpushed" ] 2>/dev/null; then pushed=1; fi
    if [ "${behind:-0}" -ge "$threshold" ] 2>/dev/null || [ "$pushed" -eq 1 ]; then
      add "the handoff may be stale: refresh it before stopping."
    fi
    ;;
esac

# Kept out of $( ) because bash 3.2 misparses a case pattern's ")" inside command substitution.
first_match() {
  local file
  while IFS= read -r file; do
    # shellcheck disable=SC2254 # The map's globs are patterns by design.
    case "$file" in $1) printf '%s\n' "$file"; return ;; esac
  done <<EOF
$changed
EOF
}

# Files changed on this branch (since it left main or master) and in the working tree.
base=""
current="$(git branch --show-current 2>/dev/null)"
for trunk in main master; do
  [ "$current" != "$trunk" ] || break
  base="$(git merge-base HEAD "$trunk" 2>/dev/null)" && break
done
# A rename shows as "old -> new"; the new path is the one that exists now.
changed="$( { [ -z "$base" ] || git diff --name-only "$base" HEAD; git status --porcelain --untracked-files=all | cut -c4- | sed 's/.* -> //'; } 2>/dev/null | sort -u)"

# Every mode asks for a test when logic changes. Source changes with no test change are reported,
# in projects that have tests at all; deleted files do not count.
TEST_FILES='(^|/)(tests?|spec|__tests__)/|(^|/)test_[^/]*\.py$|_test\.[^/]+$|\.(test|spec)\.[^/]+$|_spec\.[^/]+$|Tests?\.(java|kt|cs|scala)$'
SOURCE_FILES='\.(py|js|jsx|ts|tsx|mjs|cjs|go|rs|java|kt|rb|php|cs|swift|c|h|cc|cpp|hpp|scala|ex|exs|vue|svelte|dart|sh)$'
if ! printf '%s\n' "$changed" | grep -qE "$TEST_FILES" && git ls-files | grep -qE "$TEST_FILES"; then
  sources=0 first=""
  while IFS= read -r file; do
    [ -e "$file" ] || continue
    sources=$((sources + 1))
    [ -n "$first" ] || first="$file"
  done <<EOF
$(printf '%s\n' "$changed" | grep -E "$SOURCE_FILES" | grep -vE "$TEST_FILES")
EOF
  [ "$sources" -eq 0 ] || add "$sources source file(s) changed ($first first) but no test did: check whether existing tests cover the changed behavior; add a regression test for a gap, or explain why the existing checks are sufficient."
fi

# The project's tests must pass before the turn ends. It runs project code, so only in trusted
# projects; a detected command runs only when source or test files changed, an explicit
# check-fast always does.
if [ -e checks-map.json ] || [ -L checks-map.json ]; then
  verification="$("$cli" verify 2>&1)"
  verification_status=$?
  [ "$verification_status" -eq 0 ] || add "project verification needs attention:
$verification"
elif "$cli" trusted --quiet; then
  IFS="$(printf '\t')" read -r check check_source <<EOF
$(bash "$(dirname "$0")/../../lib/test-command.sh" "$(dirname "$0")/../.." "$root")
EOF
  if [ -n "$check" ] && { [ "$check_source" = 'tack config check-fast' ] \
    || printf '%s\n' "$changed" | grep -qE "$SOURCE_FILES|$TEST_FILES"; }; then
    bash "$(dirname "$cli")/../lib/run-check.sh" "$root" 120 "$check" >/dev/null 2>&1
    case $? in
      0) ;;
      124) add "the tests did not finish within 120 s: $check (set a faster target with tack config check-fast)" ;;
      *) add "the tests fail: $check (from $check_source): fix them, or tell the user why they fail." ;;
    esac
  fi
fi

if [ -f docs-map.txt ]; then
  while IFS='|' read -r pattern docs; do
    pattern="$(printf '%s' "$pattern" | tr -d '[:space:]')"
    case "$pattern" in '' | '#'*) continue ;; esac
    matched="$(first_match "$pattern")"
    [ -n "$matched" ] || continue
    covered=false missing=""
    # Doc names are literal paths: disable globbing so an entry like "*" is not expanded.
    set -f
    for doc in $(printf '%s' "$docs" | tr ',' ' '); do
      if printf '%s\n' "$changed" | grep -qxF "$doc"; then covered=true; else missing="$missing $doc"; fi
    done
    set +f
    missing="${missing# }"
    [ "$covered" = true ] || add "$matched changed but ${missing// / and } did not (docs-map.txt): update them or explain why not."
  done < docs-map.txt
fi

[ -n "$findings" ] || exit 0
reason="Before stopping, check:$findings"
activity_log "$root" "$client" stop-check "$findings"
if command -v jq >/dev/null 2>&1; then
  jq -cn --arg r "$reason" '{decision: "block", reason: $r}'
else
  python3 -c 'import json, sys; print(json.dumps({"decision": "block", "reason": sys.argv[1]}))' "$reason"
fi
