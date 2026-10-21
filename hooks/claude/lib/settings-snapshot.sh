#!/usr/bin/env bash
# Read effective settings once per caller. No persistent cache or Git-config shortcuts.
# load_settings_snapshot DIR [CLI] always succeeds; failures leave every setting empty.
# settings_snapshot_failed lets CLI callers retain their configuration-error exit status.
# shellcheck disable=SC2034
load_settings_snapshot() {
  local cli json
  settings_snapshot=''
  settings_snapshot_failed=1
  cli="${2:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../bin" 2>/dev/null && pwd)/tack}"
  json="$(cd "$1" 2>/dev/null && "$cli" config --json 2>/dev/null)" || return 0
  if command -v jq >/dev/null 2>&1; then
    settings_snapshot="$(printf '%s' "$json" | jq -r '.[] | .name + "=" + (.value | tostring | gsub("\\\\"; "\\\\") | gsub("\n"; "\\n"))' 2>/dev/null)" || { settings_snapshot=''; return 0; }
  elif command -v python3 >/dev/null 2>&1; then
    settings_snapshot="$(printf '%s' "$json" | python3 -c 'import json, sys
records = json.load(sys.stdin)
def encode(value):
    text = str(value).lower() if isinstance(value, bool) else str(value)
    return text.replace("\\", "\\\\").replace("\n", "\\n")
print("\n".join(record["name"] + "=" + encode(record["value"]) for record in records))' 2>/dev/null)" || { settings_snapshot=''; return 0; }
  else
    return 0
  fi
  settings_snapshot_failed=0
}

setting() {
  local value
  # Feature names contain only letters and hyphens; reject patterns before using sed.
  case "${1:-}" in '' | *[!a-z-]*) return 0 ;; esac
  # Decode only the selected record; multiline text cannot add settings to the snapshot.
  value="$(printf '%s\n' "${settings_snapshot:-}" | sed -n "s/^$1=//p" 2>/dev/null)" || return 0
  [ -z "$value" ] || printf '%b\n' "$value"
}
