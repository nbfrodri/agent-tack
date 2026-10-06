#!/usr/bin/env bash
# Diagnose the current installation without changing files, Git config or plugins.
set -uo pipefail
TOOLS_MODE=0
if [ "$#" -eq 2 ] && [ "$2" = --tools ]; then TOOLS_MODE=1; set -- "$1"; fi
if [ "$#" -ne 1 ] || [ ! -d "$1" ]; then
  echo 'Usage: doctor.sh CHECKOUT_ROOT [--tools]' >&2
  exit 2
fi
REPO="$(cd "$1" && pwd)" || exit 2
FAILURES=0 WARNINGS=0 OWNERSHIP_VALID=0 QUIET=0
ok() { [ "$QUIET" -eq 1 ] || printf 'OK   %s\n' "$1"; }
warn() { [ "$QUIET" -eq 1 ] || printf 'WARN %s\n' "$1"; WARNINGS=$((WARNINGS + 1)); }
fail() { [ "$QUIET" -eq 1 ] || printf 'FAIL %s\n' "$1"; FAILURES=$((FAILURES + 1)); }
has() { command -v "$1" >/dev/null 2>&1; }
# shellcheck source=lib/keys.sh
source "$REPO/lib/keys.sh"
# shellcheck source=lib/mods.sh
source "$REPO/lib/mods.sh"
# shellcheck source=lib/skill-groups.sh
source "$REPO/lib/skill-groups.sh"
# shellcheck source=lib/vscode.sh
source "$REPO/lib/vscode.sh"
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
check_stale_links() {
  local dir="$1" entry target
  for entry in "$dir"/*; do
    [ -L "$entry" ] || continue
    target="$(readlink "$entry")"
    case "$target" in
      "$REPO"/*) [ -e "$entry" ] || fail "stale managed symlink: $entry" ;;
    esac
  done
}
check_skills() {
  local dir="$1" source
  check_stale_links "$dir"
  for source in "$REPO"/skills/*; do
    [ -f "$source/SKILL.md" ] || continue
    # Skills of a group the user did not select are left out on purpose.
    skill_selected "${source##*/}" || continue
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
optional_target_configured() {
  local instructions="$1" skills_dir="$2" source dir
  if [ "$instructions" != - ] && [ -L "$(expand_home "$instructions")" ]; then return 0; fi
  [ "$skills_dir" != - ] || return 1
  dir="$(expand_home "$skills_dir")"
  for source in "$REPO"/skills/*; do
    [ -f "$source/SKILL.md" ] || continue
    [ -L "$dir/${source##*/}" ] && return 0
  done
  return 1
}
check_tools_and_links() {
  local tool when commands instructions skills_dir source
  for tool in bash git readlink; do
    if has "$tool"; then ok "required tool: $tool"
    else fail "required tool unavailable: $tool"; fi
  done
  has readlink || return
  check_link "$REPO" "$HOME/.agents/tack"
  check_link "$REPO" "$HOME/.agents/harness"
  check_link "$REPO/bin/tack" "$HOME/.local/bin/tack"
  check_link "$REPO/bin/harness" "$HOME/.local/bin/harness"
  [ -x "$REPO/bin/tack" ] || fail 'tack CLI is not executable'
  ok "skill groups: $(skill_groups_selected)"
  check_skills "$HOME/.agents/skills"
  while read -r tool when commands instructions skills_dir _ <&3; do
    case "$tool" in ''|'#'*) continue ;; esac
    if ! selected_tool detect "$commands"; then warn "optional CLI unavailable: $tool"; fi
    if [ "$when" != always ]; then
      if ! optional_target_configured "$instructions" "$skills_dir"; then
        if selected_tool detect "$commands"; then warn "$tool: detected but not configured by this installation"; fi
        continue
      fi
    fi
    if [ "$instructions" != - ]; then
      check_link "$REPO/global/AGENTS.md" "$(expand_home "$instructions")"
    else
      warn "$tool user rules require manual verification"
    fi
    [ "$skills_dir" = - ] || check_skills "$(expand_home "$skills_dir")"
  done 3< "$REPO/targets.txt"
  check_stale_links "$HOME/.claude/agents"
  for source in "$REPO"/agents/*.md; do
    [ -f "$source" ] || continue
    check_link "$source" "$HOME/.claude/agents/${source##*/}"
  done
}
# Returns 0 when version $1 is at least version $2 (both x.y.z)
version_at_least() {
  local a="$1" b="$2" i x y
  for i in 1 2 3; do
    x="$(printf '%s' "$a" | cut -d. -f"$i")"
    y="$(printf '%s' "$b" | cut -d. -f"$i")"
    [ "${x:-0}" -gt "${y:-0}" ] && return 0
    [ "${x:-0}" -lt "${y:-0}" ] && return 1
  done
  return 0
}
first_command() {
  local command
  local IFS=,
  for command in $1; do has "$command" && { printf '%s' "$command"; return 0; }; done
  return 1
}
tool_version() {
  "$1" --version 2>/dev/null </dev/null | head -1 |
    sed -n 's/.*\([0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\).*/\1/p'
}
run_smoke() {
  local command="$1" smoke="$2"
  local -a args
  IFS=, read -r -a args <<< "$smoke"
  if has timeout; then timeout 60 "$command" "${args[@]}" </dev/null >/dev/null 2>&1
  else "$command" "${args[@]}" </dev/null >/dev/null 2>&1; fi
}
check_tool_capabilities() {
  local tool="$1" when="$2" instructions="$3" skills_dir="$4" agents_dir="$5" before="$FAILURES" source name
  QUIET=1
  if [ "$instructions" != - ]; then
    if [ -L "$(expand_home "$instructions")" ] || [ "$when" = always ]; then
      check_link "$REPO/global/AGENTS.md" "$(expand_home "$instructions")"
    fi
  fi
  if [ "$skills_dir" != - ] && [ -d "$(expand_home "$skills_dir")" ]; then check_skills "$(expand_home "$skills_dir")"; fi
  if [ "$agents_dir" != - ] && [ -d "$(expand_home "$agents_dir")" ]; then
    check_stale_links "$(expand_home "$agents_dir")"
    # Agents are symlinked Markdown for Claude Code and generated TOML for Codex.
    for source in "$REPO"/agents/*.md; do
      [ -f "$source" ] || continue
      name="${source##*/}"
      [ -f "$(expand_home "$agents_dir")/${name%.md}.toml" ] && continue
      check_link "$source" "$(expand_home "$agents_dir")/$name"
    done
  fi
  QUIET=0
  if [ "$FAILURES" -gt "$before" ]; then
    printf 'FAIL %s: a managed capability is broken (run tack doctor for details)\n' "$tool"
  else
    ok "$tool: managed links intact"
  fi
}
check_tools() {
  local tool when commands instructions skills_dir agents_dir hooks min_version smoke
  local command version caps
  while read -r tool when commands instructions skills_dir agents_dir hooks min_version smoke _ <&3; do
    case "$tool" in ''|'#'*) continue ;; esac
    if ! command="$(first_command "$commands")"; then
      ok "$tool: not installed, skipped"
      continue
    fi
    : "${skills_dir:=-}" "${agents_dir:=-}" "${hooks:=-}" "${min_version:=-}" "${smoke:=-}"
    version="$(tool_version "$command")"
    if [ -z "$version" ]; then warn "$tool: version could not be detected"
    else ok "$tool: version $version"; fi
    caps=''
    [ "$instructions" = - ] || caps="$caps instructions"
    [ "$skills_dir" = - ] || caps="$caps skills"
    [ "$agents_dir" = - ] || caps="$caps agents"
    [ "$hooks" = - ] || caps="$caps hooks"
    ok "$tool: capabilities${caps:- none}"
    if [ "$min_version" != - ] && [ -n "$version" ]; then
      if version_at_least "$version" "$min_version"; then ok "$tool: version $version meets the minimum $min_version"
      else warn "$tool: version $version is older than the minimum $min_version"; fi
    fi
    check_tool_capabilities "$tool" "$when" "$instructions" "$skills_dir" "$agents_dir"
    if [ "$smoke" != - ]; then
      if run_smoke "$command" "$smoke"; then ok "$tool: smoke check passed"
      else warn "$tool: smoke check failed ($command ${smoke//,/ })"; fi
    fi
  done 3< "$REPO/targets.txt"
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
recorded_git_hooks_path() {
  local path="$1" state entry
  state="$(tool_dir "${XDG_STATE_HOME:-$HOME/.local/state}")/ownership"
  [ "$OWNERSHIP_VALID" -eq 1 ] || return 1
  for entry in "$state"/entries/*; do
    if [ ! -f "$entry/kind" ] || [ ! -f "$entry/target" ]; then continue; fi
    if [ "$(< "$entry/kind")" = git ] && [ "$(< "$entry/target")" = "$path" ]; then return 0; fi
  done
  return 1
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
  elif recorded_git_hooks_path "$path"; then
    fail "$scope Git hooks: managed hooksPath points to another or missing checkout"
  else
    warn "$scope Git hooks: deliberate hooksPath of your own; managed hooks are not active"
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
check_ownership() {
  local state field entry kind path target
  state="$(tool_dir "${XDG_STATE_HOME:-$HOME/.local/state}")/ownership"
  if [ ! -e "$state" ] && [ ! -L "$state" ]; then
    warn 'installation ownership is unrecorded (legacy install); uninstall restoration is not verified'
    return
  fi
  if [ ! -d "$state" ] || [ -L "$state" ]; then fail 'installation ownership metadata is invalid'; return; fi
  for field in version repo home; do
    if [ ! -f "$state/$field" ] || [ ! -r "$state/$field" ] || [ -L "$state/$field" ]; then
      fail 'installation ownership metadata is incomplete or unreadable'
      return
    fi
  done
  if [ "$(< "$state/version")" != 1 ]; then fail 'installation ownership version is unsupported'; return; fi
  if [ "$(< "$state/repo")" != "$REPO" ] || [ "$(< "$state/home")" != "$HOME" ]; then
    fail 'installation ownership belongs to another checkout or home'
    return
  fi
  if has python3 && [ -f "$REPO/lib/ownership.py" ]; then
    if ! python3 "$REPO/lib/ownership.py" validate "$state" "$HOME" >/dev/null 2>&1; then
      fail 'installation ownership schema or permissions are invalid'
      return
    fi
  else
    warn 'complete ownership schema and permissions were not verified'
  fi
  OWNERSHIP_VALID=1
  for entry in "$state"/entries/*; do
    [ -d "$entry" ] || continue
    if [ ! -f "$entry/kind" ]; then fail 'installation ownership entry is incomplete'; continue; fi
    kind="$(< "$entry/kind")"
    case "$kind" in
      link)
        if [ ! -f "$entry/path" ] || [ ! -f "$entry/target" ]; then
          fail 'installation ownership link entry is incomplete'
          continue
        fi
        path="$(< "$entry/path")"; target="$(< "$entry/target")"
        case "$path" in "$HOME"/*) ;; *) fail 'installation ownership destination is outside this home'; continue ;; esac
        case "$target" in "$REPO"|"$REPO"/*) ;; *) fail 'installation ownership source is outside this checkout'; continue ;; esac
        check_link "$target" "$path"
        ;;
      settings|git|mod|modmarket|vscode|generated) ;;
      *) fail 'installation ownership entry type is unsupported' ;;
    esac
  done
  ok 'installation ownership metadata checked; restoration snapshots remain private'
}
check_mods() {
  local mod id state
  if ! mods_enabled; then ok 'mods disabled (git config tack.mods is false)'; return; fi
  if ! has claude; then warn 'mods: claude CLI not found; the mods in plugins/ cannot be installed or checked'; return; fi
  for mod in $(mods_list "$REPO"); do
    id="$mod@$MODS_MARKETPLACE"
    state="$(mods_plugin_state "$id")"
    case "$state" in
      enabled) ok "mod installed: $mod" ;;
      disabled) warn "mod disabled: $mod (claude plugin enable $id)" ;;
      missing) warn "mod not installed: $mod (run ./install.sh, or skip mods on purpose)" ;;
      *) warn "mod state unknown: $mod (claude plugin list failed)" ;;
    esac
  done
}
check_vscode() {
  local command product path state found=0
  if ! vscode_enabled; then ok 'VS Code setting disabled (git config tack.vscodeAgentsMd is false)'; return; fi
  while IFS='|' read -r command product <&4; do
    has "$command" || continue
    found=1
    path="$(vscode_settings_path "$product")"
    if ! has python3; then warn "VS Code ($product): python3 not found; settings not checked"; continue; fi
    state="$(vscode_state "$path")"
    case "$state" in
      true) ok "VS Code ($product): $VSCODE_KEY is true" ;;
      false) warn "VS Code ($product): $VSCODE_KEY is false; Copilot Chat ignores AGENTS.md (your choice, or set it to true)" ;;
      absent|unset) warn "VS Code ($product): $VSCODE_KEY is not set; run ./install.sh" ;;
      *) warn "VS Code ($product): settings.json is not plain JSON (comments?) or the value is unusual; set \"$VSCODE_KEY\": true yourself" ;;
    esac
  done 4< <(vscode_products)
  [ "$found" -eq 1 ] || ok 'VS Code: not installed, skipped'
}
check_project() {
  has git || return
  ! git config --global --get-regexp '^harness\.' >/dev/null 2>&1 \
    || warn 'user-wide settings use the former harness name: run tack migrate'
  if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
    ok 'current directory: outside a Git repository (project checks not applicable)'
    return
  fi
  if "$REPO/bin/tack" status --quiet; then ok 'current project workflow: enabled'
  else ok 'current project workflow: disabled'; fi
  if git config --local --get-regexp '^harness\.' >/dev/null 2>&1 || [ -f "$(git rev-parse --show-toplevel)/.harness" ]; then
    warn 'current project uses the former harness name: run tack migrate'
  fi
  mode="$("$REPO/bin/tack" mode)"
  if [ -z "${mode##*invalid*}" ] || [ -z "${mode##*ignored*}" ]; then
    warn "current project mode: $mode"
  elif "$REPO/bin/tack" mode show | grep -q '^WARNING:'; then
    warn "current project mode: $mode; autonomous mode without confirmations is active"
    case "$(git branch --show-current 2>/dev/null)" in
      main | master) warn "current branch is $(git branch --show-current) in a project-only mode; switch to a branch or worktree" ;;
    esac
  else
    ok "current project mode: $mode"
  fi
  if "$REPO/bin/tack" trusted --quiet; then ok 'current project formatter: trusted'
  else ok 'current project formatter: untrusted'; fi
}
# Per-session counters are pruned at session start (tack config state-retention-days).
check_state() {
  local dir count size
  dir="${XDG_STATE_HOME:-$HOME/.local/state}/agent-tack/budget"
  [ -d "$dir" ] || return 0
  count="$(find "$dir" -type f | wc -l | tr -d ' ')"
  size="$(du -sk "$dir" 2>/dev/null | cut -f1)"
  ok "per-session state: $count file(s), ${size:-?} KB in $dir"
}
if [ "$TOOLS_MODE" -eq 1 ]; then
  [ -f "$REPO/targets.txt" ] || { echo 'doctor: targets.txt is missing' >&2; exit 1; }
  check_tools
elif [ ! -f "$REPO/targets.txt" ] || [ ! -f "$REPO/bin/tack" ]; then
  fail 'checkout is missing required tack files'
else
  check_tools_and_links
  check_ownership
  check_settings
  check_git_hooks
  check_mods
  check_vscode
  check_state
  check_project
fi
printf 'Summary: %s error(s), %s warning(s); only checked installation components are reported.\n' "$FAILURES" "$WARNINGS"
[ "$FAILURES" -eq 0 ]
