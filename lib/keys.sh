#!/usr/bin/env bash
# The one place that reads and writes the tool's git config keys, all under `tack.`. Settings
# under the former `harness.` prefix are no longer read: `tack migrate` moves them, and
# `tack doctor` says when it is needed.

# key_get [--bool] [local|global ...] NAME: prints the first value found, project before global.
# Fails when no scope has it.
key_get() {
  local type=() name scope value
  if [ "${1:-}" = --bool ]; then type=(--bool); shift; fi
  name="${!#}"
  [ "$#" -gt 1 ] || set -- local global "$name"
  while [ "$#" -gt 1 ]; do
    scope="$1"; shift
    if value="$(git config "--$scope" ${type[@]+"${type[@]}"} --get "tack.$name" 2>/dev/null)"; then
      printf '%s\n' "$value"
      return 0
    fi
  done
  return 1
}

# key_scope SCOPE NAME: succeeds when SCOPE holds the key.
key_scope() { git config "--$1" --get "tack.$2" >/dev/null 2>&1; }

# tool_dir BASE: the tool's directory under an XDG base (config or state).
tool_dir() { printf '%s/agent-tack\n' "$1"; }

# migrate_tool_dir BASE: moves BASE/agent-harness to BASE/agent-tack when only the former exists.
migrate_tool_dir() {
  [ -d "$1/agent-harness" ] && [ ! -e "$1/agent-tack" ] || return 0
  mv "$1/agent-harness" "$1/agent-tack"
}

key_set() { git config "--$1" "tack.$2" "$3"; }

key_unset() {
  if git config "--$1" --get "tack.$2" >/dev/null 2>&1; then git config "--$1" --unset-all "tack.$2"; fi
}

# same_dir A B: both name the same existing directory. Git for Windows stores a path set from Git
# Bash as D:/x, which a string comparison with /d/x would miss.
same_dir() {
  [ -d "$1" ] && [ -d "$2" ] && [ "$(cd "$1" && pwd -P)" = "$(cd "$2" && pwd -P)" ]
}
