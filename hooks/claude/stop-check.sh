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
    printf '%s' "$input" | python3 -I -c 'import json, sys
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
  *"handoff names branch"*)
    # Parallel work belongs to its own task; a different branch is expected in team projects.
    if [ "$("$cli" config collaboration --get 2>/dev/null)" != team ]; then
      add "the handoff may be stale: refresh it before stopping."
    fi
    ;;
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

# clear-hint-percent, with a token fallback: once per session, the handoff must be current so
# /clear loses nothing (session start reloads it). A current handoff only needs the user told;
# a missing or stale one is the assistant's to write first.
hint=""
size=""
threshold="$("$cli" config clear-hint-percent --get 2>/dev/null)"
threshold="${threshold%% *}"
case "$threshold" in '' | *[!0-9]*) threshold=0 ;; esac
if [ "${#threshold}" -le 3 ] && [ "$threshold" -ge 1 ] && [ "$threshold" -le 100 ]; then
  size="$(cd "$cwd" && "$cli" usage context 2>/dev/null)"
fi
description="$size% full"
if [ -z "$size" ]; then
  threshold="$("$cli" config clear-hint-tokens --get 2>/dev/null)"
  threshold="${threshold%% *}"
fi
case "$threshold" in '' | *[!0-9]*) threshold=0 ;; esac
session="$(field .session_id)"
case "$session" in '' | *[!A-Za-z0-9_-]*) threshold=0 ;; esac
if [ "$client" = claude ] && [ "$threshold" -gt 0 ]; then
  if [ -z "$size" ]; then
    if command -v python3 >/dev/null 2>&1; then
      size="$(python3 -I "$(dirname "$0")/lib/context-size.py" "$(field .transcript_path)" 2>/dev/null)"
    fi
    description="$size tokens"
  fi
  hint_dir="${XDG_STATE_HOME:-$HOME/.local/state}/agent-tack/clear-hint"
  case "$size" in '' | *[!0-9]*) size=0 ;; esac
  if [ "$size" -ge "$threshold" ] && [ ! -e "$hint_dir/$session" ]; then
    (umask 077; mkdir -p "$hint_dir" && : > "$hint_dir/$session") 2>/dev/null
    case "$handoff_check" in
      *"up to date"*)
        hint="tack: the context is about $description. The handoff is current, so /clear is safe: the next session reloads it." ;;
      *)
        add "the context is about $description. Write or refresh the active handoff so a fresh session can resume from it, then tell the user in one line that /clear is safe because the handoff reloads at session start." ;;
    esac
  fi
fi

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
remaining_budget() {
  budget=$(( ${TACK_STOP_TIMEOUT:-90} - SECONDS - 10 ))
  [ "$budget" -le 120 ] || budget=120
  [ "$budget" -gt 0 ]
}
if [ -e checks-map.json ] || [ -L checks-map.json ]; then
  # The hook is killed at its timeout (settings.json: 90 s), so verification gets what is left,
  # minus a margin to print the result; otherwise a slow suite would also swallow the /clear hint.
  if remaining_budget; then
    verification="$("$cli" verify --budget-seconds "$budget" 2>&1)"
    verification_status=$?
    # A check that only ran out of time failed nothing: say so as a note instead of blocking the
    # stop. Any other gap (a failure, an unmapped path, edited inputs) still blocks.
    out_of_time="$(printf '%s\n' "$verification" | grep '^Not completed (out of time, nothing failed)')"
    if [ "$verification_status" -eq 3 ] && [ -n "$out_of_time" ] \
      && ! printf '%s\n' "$verification" | grep -qE '^(No check selected for|Checks changed repository inputs)'; then
      hint="${hint:+$hint }tack: $out_of_time"
    elif [ "$verification_status" -ne 0 ]; then
      add "project verification needs attention:
$verification"
    fi
  else
    # Nothing failed and the user cannot act on a block, so a skipped step is a note.
    hint="${hint:+$hint }tack: project verification skipped: the Stop hook time budget is exhausted; run tack verify."
  fi
elif "$cli" trusted --quiet; then
  IFS="$(printf '\t')" read -r check check_source <<EOF
$(bash "$(dirname "$0")/../../lib/test-command.sh" "$(dirname "$0")/../.." "$root")
EOF
  if [ -n "$check" ] && { [ "$check_source" = 'tack config check-fast' ] \
    || printf '%s\n' "$changed" | grep -qE "$SOURCE_FILES|$TEST_FILES"; }; then
    if remaining_budget; then
      bash "$(dirname "$cli")/../lib/run-check.sh" "$root" "$budget" "$check" >/dev/null 2>&1
      case $? in
      0) ;;
      124) add "the tests did not finish within $budget s (remaining Stop hook budget): $check (set a faster target with tack config check-fast)" ;;
      *) add "the tests fail: $check (from $check_source): fix them, or tell the user why they fail." ;;
      esac
    else
      hint="${hint:+$hint }tack: the tests were skipped: the Stop hook time budget is exhausted; run $check."
    fi
  fi
fi

# aislop, when installed: a deterministic scan of the changed code for what assistants leave
# behind. It reads the project's own configuration and may run its linters, so it needs local
# trust like the tests; lib/slop_check.py turns its telemetry off and prints only findings.
if command -v python3 >/dev/null 2>&1 && "$cli" trusted --quiet \
  && [ "$("$cli" config slop-check --get 2>/dev/null)" != "false" ] \
  && printf '%s\n' "$changed" | grep -E "$SOURCE_FILES" | grep -qvE "$TEST_FILES"; then
  if remaining_budget; then
    slop="$(python3 -I "$(dirname "$cli")/../lib/slop_check.py" "$root" "$base" "$budget" 2>/dev/null)"
    slop_status=$?
    if [ "$slop_status" -eq 3 ]; then
      # The scanner could not run (a broken install, a missing runtime): nothing in the code
      # failed and the user cannot act on a block, so it is a note.
      hint="${hint:+$hint }tack: $slop"
    else
      [ -z "$slop" ] || add "$slop"
    fi
  else
    # Nothing was found and nothing failed: the user cannot act on a block, so it is a note.
    hint="${hint:+$hint }tack: aislop scan skipped: the Stop hook time budget is exhausted; run aislop scan --changes."
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

if [ -z "$findings" ]; then
  if [ -n "$hint" ]; then
    if command -v jq >/dev/null 2>&1; then
      jq -cn --arg m "$hint" '{systemMessage: $m}'
    else
      python3 -I -c 'import json, sys; print(json.dumps({"systemMessage": sys.argv[1]}))' "$hint"
    fi
  fi
  exit 0
fi
reason="Before stopping, check:$findings"
activity_log "$root" "$client" stop-check "$findings"
# The hint is recorded as shown once per session, so it travels with the block too.
if command -v jq >/dev/null 2>&1; then
  jq -cn --arg r "$reason" --arg m "$hint" '{decision: "block", reason: $r} + (if $m == "" then {} else {systemMessage: $m} end)'
else
  python3 -I -c 'import json, sys
out = {"decision": "block", "reason": sys.argv[1]}
if sys.argv[2]:
    out["systemMessage"] = sys.argv[2]
print(json.dumps(out))' "$reason" "$hint"
fi
