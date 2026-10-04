#!/usr/bin/env bash
# Claude Code PostToolUse hook after edits: runs the project's fast check
# (`tack config check-fast`) and shows its failures to the assistant.
# Runs project code, so it needs both activation and local trust, like the formatter.
set -u

input="$(cat)"
cwd=""
if command -v jq >/dev/null 2>&1; then
  cwd="$(printf '%s' "$input" | jq -r '.cwd // empty' 2>/dev/null)"
elif command -v python3 >/dev/null 2>&1; then
  cwd="$(printf '%s' "$input" | python3 -c 'import json, sys
try:
    print(json.load(sys.stdin).get("cwd") or "")
except Exception:
    print("")' 2>/dev/null)"
fi
[ -n "$cwd" ] && [ -d "$cwd" ] || exit 0
# shellcheck source=SCRIPTDIR/lib/hook-control.sh
. "$(dirname "$0")/lib/hook-control.sh"
! hook_disabled "$cwd" fast-check || exit 0

cli="$(cd "$(dirname "$0")/../../bin" && pwd)/tack"
cd "$cwd" || exit 0
"$cli" status --quiet && "$cli" trusted --quiet || exit 0
check="$("$cli" config check-fast 2>/dev/null)"
check="${check% (*}"
[ -n "$check" ] && [ "$check" != none ] || exit 0
root="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0

limit=()
command -v timeout >/dev/null 2>&1 && limit=(timeout 60)
output="$(cd "$root" && ${limit[@]+"${limit[@]}"} bash -c "$check" 2>&1)"
status=$?
[ "$status" -ne 0 ] || exit 0

reason="The fast check failed after this edit (exit $status): $check
$(printf '%s\n' "$output" | tail -n 40)
Fix it before continuing, or tell the user why it fails."
if command -v jq >/dev/null 2>&1; then
  jq -cn --arg r "$reason" '{decision: "block", reason: $r}'
else
  python3 -c 'import json, sys; print(json.dumps({"decision": "block", "reason": sys.argv[1]}))' "$reason"
fi
