#!/usr/bin/env bash
# hook_disabled DIR ID: succeeds when ID is listed in `tack config disabled-hooks` for the
# project at DIR. Only advisory hooks call it; the guard and the tool-call limit never do.

hook_disabled() {
  local cli list
  cli="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../bin" 2>/dev/null && pwd)/tack"
  [ -x "$cli" ] || return 1
  list="$(cd "$1" 2>/dev/null && "$cli" config disabled-hooks --get 2>/dev/null)" || return 1
  list="${list% (*}"
  list="$(printf '%s' "$list" | tr -d ' ')"
  case ",$list," in *",$2,"*) return 0 ;; esac
  return 1
}
