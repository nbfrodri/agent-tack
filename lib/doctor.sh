#!/usr/bin/env bash
# Diagnose the current installation without changing files, Git config or plugins.
set -uo pipefail
if [ "$#" -ne 1 ] || [ ! -d "$1" ]; then
  echo 'Usage: doctor.sh CHECKOUT_ROOT' >&2
  exit 2
fi
REPO="$(cd "$1" && pwd)" || exit 2
FAILURES=0 WARNINGS=0
ok() { printf 'OK   %s\n' "$1"; }
warn() { printf 'WARN %s\n' "$1"; WARNINGS=$((WARNINGS + 1)); }
fail() { printf 'FAIL %s\n' "$1"; FAILURES=$((FAILURES + 1)); }
has() { command -v "$1" >/dev/null 2>&1; }
expand_home() {
  case "$1" in '~'/*) printf '%s/%s' "$HOME" "${1#\~/}" ;; *) printf '%s' "$1" ;; esac
}
check_link() {
  local source="$1" dest="$2"
  if [ ! -L "$dest" ]; then
    fail "missing managed symlink: $dest"
  elif [ ! -e "$dest" ]; then
    fail "broken managed symlink: $dest"
  elif [ "$(readlink "$dest")" != "$source" ]; then
    fail "managed symlink points to a different source: $dest"
  else
    ok "managed symlink: $dest"
  fi
}
check_skills() {
  local dir="$1" source
  for source in "$REPO"/skills/*; do
    [ -f "$source/SKILL.md" ] || continue
    check_link "$source" "$dir/${source##*/}"
  done
}
selected_tool() {
  local when="$1" commands="$2" command
  [ "$when" = always ] && return 0
  local IFS=,
  for command in $commands; do has "$command" && return 0; done
  return 1
}
check_tools_and_links() {
  local tool when commands instructions skills_dir source
  for tool in bash git readlink; do
    if has "$tool"; then ok "required tool: $tool"
    else fail "required tool unavailable: $tool"; fi
  done
  has readlink || return
  check_link "$REPO" "$HOME/.agents/harness"
  check_link "$REPO/bin/harness" "$HOME/.local/bin/harness"
  [ -x "$REPO/bin/harness" ] || fail 'harness CLI is not executable'
  check_skills "$HOME/.agents/skills"
  while read -r tool when commands instructions skills_dir _ <&3; do
    case "$tool" in ''|'#'*) continue ;; esac
    if ! selected_tool detect "$commands"; then warn "optional CLI unavailable: $tool"; fi
    selected_tool "$when" "$commands" || continue
    if [ "$instructions" != - ]; then
      check_link "$REPO/global/AGENTS.md" "$(expand_home "$instructions")"
    else
      warn "$tool user rules require manual verification"
    fi
    [ "$skills_dir" = - ] || check_skills "$(expand_home "$skills_dir")"
  done 3< "$REPO/targets.txt"
  for source in "$REPO"/agents/*.md; do
    [ -f "$source" ] || continue
    check_link "$source" "$HOME/.claude/agents/${source##*/}"
  done
}
check_project() {
  has git || return
  if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
    ok 'current directory: outside a Git repository (project checks not applicable)'
    return
  fi
  if "$REPO/bin/harness" status --quiet; then ok 'current project workflow: enabled'
  else ok 'current project workflow: disabled'; fi
  if "$REPO/bin/harness" trusted --quiet; then ok 'current project formatter: trusted'
  else ok 'current project formatter: untrusted'; fi
}
if [ ! -f "$REPO/targets.txt" ] || [ ! -f "$REPO/bin/harness" ]; then
  fail 'checkout is missing required harness files'
else
  check_tools_and_links
  check_project
fi
printf 'Summary: %s error(s), %s warning(s); only checked installation components are reported.\n' "$FAILURES" "$WARNINGS"
[ "$FAILURES" -eq 0 ]
