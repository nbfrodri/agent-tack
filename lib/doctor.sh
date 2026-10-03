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
check_settings() {
  local dest="$HOME/.claude/settings.json" rc source
  if [ ! -f "$dest" ]; then fail 'Claude settings are missing'; return; fi
  for source in "$REPO"/hooks/claude/*.sh; do
    [ -r "$source" ] || fail 'managed Claude hook script is unreadable'
  done
  if has python3; then
    python3 - "$dest" "$REPO/claude/settings.json" "$REPO" <<'PYTHON' >/dev/null 2>&1
import json,sys
try:
    current=json.load(open(sys.argv[1]))
    expected=json.load(open(sys.argv[2]))
except (OSError,ValueError):
    sys.exit(2)
if not isinstance(current,dict): sys.exit(2)
hooks=current.get('hooks',{})
if not isinstance(hooks,dict): sys.exit(1)
for event,groups in expected.get('hooks',{}).items():
    candidates=hooks.get(event,[])
    if not isinstance(candidates,list): sys.exit(1)
    for group in groups:
        for hook in group['hooks']:
            command=hook['command'].replace('__REPO__',sys.argv[3])
            matches=0
            for candidate in candidates:
                if not isinstance(candidate,dict) or candidate.get('matcher')!=group.get('matcher'):
                    continue
                entries=candidate.get('hooks',[])
                if not isinstance(entries,list): continue
                matches+=sum(isinstance(entry,dict) and entry.get('type')==hook['type']
                             and entry.get('command')==command for entry in entries)
            if matches!=1: sys.exit(1)
PYTHON
    rc=$?
  elif has jq; then
    jq -e --arg root "$REPO" --slurpfile expected "$REPO/claude/settings.json" '
      if type != "object" then error("invalid settings") else
      . as $current | all($expected[0].hooks | to_entries[];
        .key as $event | all(.value[];
          . as $group | all(.hooks[];
            . as $hook | ($hook.command | split("__REPO__") | join($root)) as $command |
            [$current.hooks[$event][]? | select(.matcher == $group.matcher) |
             .hooks[]? | select(.type == $hook.type and .command == $command)] | length == 1)))
      end' "$dest" >/dev/null 2>&1
    rc=$?
    [ "$rc" -eq 0 ] || { [ "$rc" -eq 1 ] && rc=1 || rc=2; }
  else
    warn 'python3 and jq unavailable: Claude settings and managed hooks were not verified'
    return
  fi
  case "$rc" in
    0) ok 'Claude settings: valid JSON and expected managed hooks present' ;;
    1) fail 'Claude settings: managed hooks are missing, duplicated or differ from this checkout' ;;
    *) fail 'Claude settings: invalid or unreadable JSON object' ;;
  esac
}
check_hooks_path() {
  local scope="$1" path="$2" source
  if [ "$path" = "$REPO/git-hooks" ]; then
    for source in _chain commit-msg pre-push pre-commit; do
      [ -x "$path/$source" ] || fail "$scope Git hook is missing or not executable: $source"
    done
    ok "$scope Git hooks: configured for this checkout"
  elif [ -z "$path" ]; then
    fail "$scope Git hooks: no hooksPath configured"
  elif [ "${path##*/}" = git-hooks ] && { [ ! -d "$path" ] || [ -f "$path/_chain" ]; }; then
    fail "$scope Git hooks: managed hooksPath points to another or missing checkout"
  else
    warn "$scope Git hooks: deliberate non-harness hooksPath; managed hooks are not active"
  fi
}
check_git_hooks() {
  has git || return
  local path rc
  path="$(git config --global --path --get core.hooksPath 2>/dev/null)"; rc=$?
  if [ "$rc" -gt 1 ]; then fail 'global Git hooks: configuration could not be read'; return; fi
  check_hooks_path global "$path"
  if git rev-parse --show-toplevel >/dev/null 2>&1; then
    path="$(git config --path --get core.hooksPath 2>/dev/null)"; rc=$?
    if [ "$rc" -gt 1 ]; then fail 'effective Git hooks: configuration could not be read'; return; fi
    check_hooks_path effective "$path"
  fi
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
  check_settings
  check_git_hooks
  check_project
fi
printf 'Summary: %s error(s), %s warning(s); only checked installation components are reported.\n' "$FAILURES" "$WARNINGS"
[ "$FAILURES" -eq 0 ]
