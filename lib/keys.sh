#!/usr/bin/env bash
# The one place that reads and writes the tool's git config keys. Keys live under `tack.`;
# the former `harness.` prefix is still read so older installations and projects keep working,
# and every write removes the legacy key in the same scope.

# key_get [--bool] [local|global ...] NAME: prints the first value found, project before global,
# the current prefix before the legacy one in each scope. Fails when no scope has it.
key_get() {
  local type=() name scope prefix value
  if [ "${1:-}" = --bool ]; then type=(--bool); shift; fi
  name="${!#}"
  [ "$#" -gt 1 ] || set -- local global "$name"
  while [ "$#" -gt 1 ]; do
    scope="$1"; shift
    for prefix in tack harness; do
      if value="$(git config "--$scope" ${type[@]+"${type[@]}"} --get "$prefix.$name" 2>/dev/null)"; then
        printf '%s\n' "$value"
        return 0
      fi
    done
  done
  return 1
}

# key_scope SCOPE NAME: succeeds when SCOPE holds the key under either prefix.
key_scope() {
  git config "--$1" --get "tack.$2" >/dev/null 2>&1 || git config "--$1" --get "harness.$2" >/dev/null 2>&1
}

# tool_dir BASE: the tool's directory under an XDG base (config or state). agent-tack, unless only
# the directory from before the rename exists; the installer moves that one to agent-tack.
tool_dir() {
  if [ -d "$1/agent-tack" ] || [ ! -d "$1/agent-harness" ]; then printf '%s/agent-tack\n' "$1"
  else printf '%s/agent-harness\n' "$1"; fi
}

# migrate_tool_dir BASE: moves BASE/agent-harness to BASE/agent-tack when only the former exists.
migrate_tool_dir() {
  [ -d "$1/agent-harness" ] && [ ! -e "$1/agent-tack" ] || return 0
  mv "$1/agent-harness" "$1/agent-tack"
}

key_set() {
  git config "--$1" "tack.$2" "$3" || return 1
  if git config "--$1" --get "harness.$2" >/dev/null 2>&1; then git config "--$1" --unset-all "harness.$2"; fi
  return 0
}

key_unset() {
  local prefix
  for prefix in tack harness; do
    if git config "--$1" --get "$prefix.$2" >/dev/null 2>&1; then
      git config "--$1" --unset-all "$prefix.$2" || return 1
    fi
  done
}
