#!/usr/bin/env bash
# Claude Code Stop hook: before the assistant ends its turn in an enabled project, reports
# uncommitted work, a failing fast check, a stale handoff and docs the project's docs map
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

cwd="$(field .cwd)"
[ "$(field .stop_hook_active)" = true ] && exit 0
[ -n "$cwd" ] && [ -d "$cwd" ] || exit 0
cli="$(cd "$(dirname "$0")/../../bin" && pwd)/harness"
cd "$cwd" || exit 0
"$cli" status --quiet || exit 0
[ "$("$cli" config stop-check 2>/dev/null)" != "false (local)" ] || exit 0
[ "$("$cli" config stop-check 2>/dev/null)" != "false (global)" ] || exit 0
root="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
cd "$root" || exit 0

findings=""
add() { findings="$findings
- $1"; }

dirty="$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
[ "$dirty" -eq 0 ] || add "$dirty uncommitted change(s): commit verified work or tell the user why it stays uncommitted."

if "$cli" trusted --quiet; then
  check="$("$cli" config check-fast 2>/dev/null)"
  check="${check% (*}"
  if [ -n "$check" ] && [ "$check" != none ] && ! bash -c "$check" >/dev/null 2>&1; then
    add "the fast check fails: $check"
  fi
fi

case "$("$cli" context 2>/dev/null)" in
  *"Handoff check: may be stale"* | *"Handoff check: handoff names branch"*) add "the handoff may be stale: refresh it before stopping." ;;
esac

if [ -f docs-map.txt ]; then
  base=""
  current="$(git branch --show-current 2>/dev/null)"
  for trunk in main master; do
    [ "$current" != "$trunk" ] || break
    base="$(git merge-base HEAD "$trunk" 2>/dev/null)" && break
  done
  changed="$( { [ -z "$base" ] || git diff --name-only "$base" HEAD; git status --porcelain | cut -c4-; } 2>/dev/null | sort -u)"
  while IFS='|' read -r pattern docs; do
    pattern="$(printf '%s' "$pattern" | tr -d '[:space:]')"
    case "$pattern" in '' | '#'*) continue ;; esac
    # shellcheck disable=SC2254 # The map's globs are patterns by design.
    matched="$(printf '%s\n' "$changed" | while IFS= read -r file; do case "$file" in $pattern) printf '%s\n' "$file" ;; esac; done | head -n 1)"
    [ -n "$matched" ] || continue
    covered=false missing=""
    for doc in $(printf '%s' "$docs" | tr ',' ' '); do
      if printf '%s\n' "$changed" | grep -qxF "$doc"; then covered=true; else missing="$missing $doc"; fi
    done
    missing="${missing# }"
    [ "$covered" = true ] || add "$matched changed but ${missing// / and } did not (docs-map.txt): update them or explain why not."
  done < docs-map.txt
fi

[ -n "$findings" ] || exit 0
reason="Before stopping, check:$findings"
if command -v jq >/dev/null 2>&1; then
  jq -cn --arg r "$reason" '{decision: "block", reason: $r}'
else
  python3 -c 'import json, sys; print(json.dumps({"decision": "block", "reason": sys.argv[1]}))' "$reason"
fi
