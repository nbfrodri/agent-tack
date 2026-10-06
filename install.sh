#!/usr/bin/env bash
# Installs this repo's configuration for Claude Code and Codex:
#   - global instructions and skills for every AI tool in targets.txt, and Claude Code
#     subagents (as symlinks into this repo)
#   - Claude Code settings and hooks from claude/settings.json (merged, your other keys kept)
#   - global git hooks from git-hooks/ (Conventional Commits, no AI attribution, protect main)
#   - Claude Code marketplaces and plugins from plugins.txt (installed or updated to latest)
#   - Claude Code mods from plugins/ through a local marketplace (opt out with --skip-mods or
#     git config --global tack.mods false; --skip-plugins skips them too)
#   - when VS Code is installed, "chat.useAgentsMdFile": true in its user settings so Copilot Chat
#     loads each project's AGENTS.md (opt out with git config --global tack.vscodeAgentsMd false)
#   - --no-hooks installs instructions, skills, agents and settings but no git, Claude Code or Codex
#     hooks, removing tack's agent hooks from an earlier install (git hooks: ./uninstall.sh)
#
# Safe to re-run at any time. Existing files are backed up with a timestamp,
# never overwritten. A failing step is reported and the rest still runs.
#
# Usage: ./install.sh [--dry-run] [--verbose] [--skip-plugins] [--skip-mods] [--no-hooks] [--help]
# Links and generated files already in place are counted per section; --verbose lists each one.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAMP="$(date +%Y%m%d-%H%M%S)"
WORKDIR="$(mktemp -d "${TMPDIR:-/tmp}/agent-tack.XXXXXX")" || { echo "cannot create a temp dir" >&2; exit 1; }
trap 'rm -rf "$WORKDIR"' EXIT
SKIP_PLUGINS=0
SKIP_MODS=0
NO_HOOKS=0
DRY_RUN=0
VERBOSE=0
FAILURES=0
WARNINGS=0

for arg in "$@"; do
  case "$arg" in
    --skip-plugins) SKIP_PLUGINS=1 ;;
    --skip-mods) SKIP_MODS=1 ;;
    --no-hooks) NO_HOOKS=1 ;;
    --dry-run) DRY_RUN=1 ;;
    --verbose) VERBOSE=1 ;;
    -h|--help)
      sed -n '2,19p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      echo "Unknown option: $arg (see --help)" >&2
      exit 2
      ;;
  esac
done

if [ -t 1 ]; then
  C_OK=$'\033[32m' C_WARN=$'\033[33m' C_FAIL=$'\033[31m' C_HEAD=$'\033[1m' C_OFF=$'\033[0m'
else
  C_OK='' C_WARN='' C_FAIL='' C_HEAD='' C_OFF=''
fi
# Per-item results are counted, not listed, unless --verbose; section() prints the previous
# section's counts before its own heading.
ITEMS_NEW=0 ITEMS_KEPT=0
item_new()  { ITEMS_NEW=$((ITEMS_NEW + 1)); [ "$VERBOSE" -eq 0 ] || ok "$1"; }
item_kept() { ITEMS_KEPT=$((ITEMS_KEPT + 1)); [ "$VERBOSE" -eq 0 ] || ok "$1"; }
flush_items() {
  if [ "$VERBOSE" -eq 0 ]; then
    if [ "$ITEMS_NEW" -gt 0 ] && [ "$ITEMS_KEPT" -gt 0 ]; then ok "$ITEMS_NEW new, $ITEMS_KEPT already in place"
    elif [ "$ITEMS_NEW" -gt 0 ]; then ok "$ITEMS_NEW new"
    elif [ "$ITEMS_KEPT" -gt 0 ]; then ok "$ITEMS_KEPT already in place"; fi
  fi
  ITEMS_NEW=0 ITEMS_KEPT=0
}
section() { flush_items; printf '\n%s== %s ==%s\n' "$C_HEAD" "$1" "$C_OFF"; }
ok()      { printf '  %s✔%s %s\n' "$C_OK" "$C_OFF" "$1"; }
warn()    { printf '  %s!%s %s\n' "$C_WARN" "$C_OFF" "$1"; WARNINGS=$((WARNINGS + 1)); }
fail()    { printf '  %s✘%s %s\n' "$C_FAIL" "$C_OFF" "$1"; FAILURES=$((FAILURES + 1)); }
has()     { command -v "$1" >/dev/null 2>&1; }

# shellcheck source=lib/ownership.sh
source "$REPO/lib/ownership.sh"
# shellcheck source=lib/keys.sh
source "$REPO/lib/keys.sh"
# shellcheck source=lib/mods.sh
source "$REPO/lib/mods.sh"
# shellcheck source=lib/skill-groups.sh
source "$REPO/lib/skill-groups.sh"
# shellcheck source=lib/vscode.sh
source "$REPO/lib/vscode.sh"
# shellcheck source=lib/codex.sh
source "$REPO/lib/codex.sh"

# Moves an existing file or directory aside instead of overwriting it.
backup() {
  local target="$1" dest="${2:-$1.bak-$STAMP}" n=1
  while [ -e "$dest" ] || [ -L "$dest" ]; do
    dest="$1.bak-$STAMP-$n"
    n=$((n + 1))
  done
  if mv "$target" "$dest"; then
    warn "backed up $target -> $dest"
  else
    fail "could not back up $target"
    return 1
  fi
}

# Creates dest -> src, replacing an old symlink and backing up a real file.
link() {
  local src="$1" dest="$2" displaced n=1
  if [ "$DRY_RUN" -eq 1 ]; then
    ok "would link $dest -> $src (preserve displaced files)"
    return
  fi
  if ! mkdir -p "$(dirname "$dest")"; then
    fail "cannot create $(dirname "$dest")"
    return
  fi
  displaced="$dest.bak-$STAMP"
  while [ -e "$displaced" ] || [ -L "$displaced" ]; do
    displaced="$dest.bak-$STAMP-$n"; n=$((n + 1))
  done
  if [ -L "$dest" ]; then
    if [ "$(readlink "$dest")" = "$src" ]; then
      item_kept "$dest"
      return
    fi
    ownership_link "$dest" "$src" "$displaced" || { fail "cannot record $dest"; return; }
    rm -f "$dest" || { fail "cannot replace symlink $dest"; return; }
  elif [ -e "$dest" ]; then
    ownership_link "$dest" "$src" "$displaced" || { fail "cannot record $dest"; return; }
    backup "$dest" "$displaced" || return
  else
    ownership_link "$dest" "$src" "$displaced" || { fail "cannot record $dest"; return; }
  fi
  if ln -s "$src" "$dest"; then
    item_new "$dest -> $src"
  else
    fail "cannot link $dest"
  fi
}

# Removes symlinks into this repo whose target no longer exists (deleted skills or agents).
prune() {
  local dir="$1" entry target
  [ -d "$dir" ] || return 0
  for entry in "$dir"/*; do
    [ -L "$entry" ] || continue
    target="$(readlink "$entry")"
    case "$target" in
      "$REPO"/*)
        if [ ! -e "$target" ]; then
          if [ "$DRY_RUN" -eq 1 ]; then ok "would remove stale link $entry"
          else rm -f "$entry" && ok "removed stale link $entry"; fi
        fi
        ;;
    esac
  done
}

# Expands a leading ~ in a path from targets.txt
expand_home() {
  case "$1" in
    "~"/*) printf '%s/%s' "$HOME" "${1#\~/}" ;;
    *) printf '%s' "$1" ;;
  esac
}

# True when a tool from targets.txt should be configured on this machine
tool_wanted() {
  local when="$1" commands="$2" cmd
  [ "$when" = always ] && return 0
  for cmd in $(printf '%s' "$commands" | tr ',' ' '); do
    has "$cmd" && return 0
  done
  return 1
}

install_links() {
  local tool when commands instructions skills_dir dir skill name skill_dirs=""
  section "AI tools"
  # fd 3 so that nothing inside the loop can consume the file's lines
  while read -r tool when commands instructions skills_dir _ <&3; do
    case "$tool" in '' | '#'*) continue ;; esac
    if ! tool_wanted "$when" "$commands"; then
      ok "$tool: not installed, skipped"
      continue
    fi
    if [ "$instructions" = "-" ]; then
      warn "$tool: no file for global instructions; paste $REPO/global/AGENTS.md into its user rules once (Cursor: Customize → Rules)"
    else
      link "$REPO/global/AGENTS.md" "$(expand_home "$instructions")"
    fi
    [ "$skills_dir" = "-" ] || skill_dirs="$skill_dirs
$(expand_home "$skills_dir")"
  done 3< "$REPO/targets.txt"

  section "Skills"
  skill_dirs="$HOME/.agents/skills$skill_dirs"
  while IFS= read -r dir; do
    prune "$dir"
  done <<EOF
$skill_dirs
EOF
  ok "skill groups: $(skill_groups_selected) (tack config skill-groups --global)"
  for skill in "$REPO"/skills/*/; do
    [ -f "$skill/SKILL.md" ] || { warn "skipping $skill (no SKILL.md)"; continue; }
    name="$(basename "$skill")"
    while IFS= read -r dir; do
      if skill_selected "$name"; then
        link "${skill%/}" "$dir/$name"
      elif [ -L "$dir/$name" ] && [ "$(readlink "$dir/$name")" = "${skill%/}" ]; then
        # Only tack's own link to a skill of a deselected group is removed, and only where it
        # took nothing's place; one that replaced the user's skill waits for uninstall.
        if ownership_link_replaced "$dir/$name"; then
          if [ "$DRY_RUN" -eq 1 ]; then ok "would keep $dir/$name: it replaced a skill of yours, which ./uninstall.sh restores"
          else warn "kept $dir/$name: it replaced a skill of yours, which ./uninstall.sh restores"; fi
        elif [ "$DRY_RUN" -eq 1 ]; then
          ok "would remove $dir/$name (group not selected)"
        elif ownership_release_link "$dir/$name"; then
          rm -f "$dir/$name" && ok "removed $dir/$name (group not selected)"
        fi
      fi
    done <<EOF
$skill_dirs
EOF
  done

  section "Old names (agent-config, harness)"
  # Links left by versions of this repo named agent-config
  local old
  for old in "$HOME/.local/bin/agent-config" "$HOME/.agents/agent-config"; do
    if [ -L "$old" ]; then
      if [ "$DRY_RUN" -eq 1 ]; then ok "would remove old link $old"
      else rm -f "$old" && ok "removed old link $old"; fi
    fi
  done
  # Links to this checkout under the former harness name; one that took the place of a file of
  # yours stays until ./uninstall.sh restores that file.
  for old in "$HOME/.local/bin/harness" "$HOME/.agents/harness"; do
    [ -L "$old" ] || continue
    case "$(readlink "$old")" in "$REPO" | "$REPO/bin/harness") ;; *) continue ;; esac
    if [ "$DRY_RUN" -eq 1 ]; then ok "would remove old link $old"
    elif ownership_release_link "$old"; then rm -f "$old" && ok "removed old link $old"
    else warn "kept $old: it replaced a file of yours, which ./uninstall.sh restores"; fi
  done

  section "Config repo link"
  # Canonical path skills and agents use to reach this repo, wherever it is cloned
  link "$REPO" "$HOME/.agents/tack"

  section "Command"
  [ "$DRY_RUN" -eq 1 ] || chmod +x "$REPO/bin/tack" 2>/dev/null
  link "$REPO/bin/tack" "$HOME/.local/bin/tack"
  case ":$PATH:" in
    *":$HOME/.local/bin:"*) ;;
    *) warn "$HOME/.local/bin is not in PATH: add it to use 'tack enable|disable|status'" ;;
  esac

  section "Subagents (Claude Code)"
  prune "$HOME/.claude/agents"
  local agent
  for agent in "$REPO"/agents/*.md; do
    [ -e "$agent" ] || continue
    link "$agent" "$HOME/.claude/agents/$(basename "$agent")"
  done
}

# Merges claude/settings.json into ~/.claude/settings.json:
#   - objects are deep-merged and the repo's values win; your other keys are kept
#   - hooks: entries tagged "#tack" (or the former "#harness") are replaced by the repo's, your own hooks are kept
#   - __REPO__ in the repo file is replaced with this repo's path
# without_hooks SRC DEST: copies a settings template without its "hooks" key. Merging it
# removes tack's tagged hooks from the destination and keeps the user's own.
without_hooks() {
  if has python3; then
    python3 -c 'import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8")); d.pop("hooks", None); json.dump(d, open(sys.argv[2], "w", encoding="utf-8"), indent=2)' "$1" "$2"
  else
    jq 'del(.hooks)' "$1" > "$2"
  fi
}

# only_version FILE: succeeds when a JSON settings file holds nothing but a "version" key.
only_version() {
  if has python3; then
    python3 -c 'import json, sys; sys.exit(0 if set(json.load(open(sys.argv[1], encoding="utf-8"))) <= {"version"} else 1)' "$1" 2>/dev/null
  else
    jq -e 'del(.version) == {}' "$1" >/dev/null 2>&1
  fi
}

# Registers each tool's hooks from targets.txt: a tool with a hooks file there and a template at
# <tool>/<same file name> in the repo, when the tool is wanted. Adding a tool is data only.
merge_settings() {
  local tool when commands hooks_file template dest
  while read -r tool when commands _ _ _ hooks_file _ <&3; do
    case "$tool" in '' | '#'*) continue ;; esac
    [ "${hooks_file:--}" != - ] || continue
    template="$REPO/$tool/$(basename "$hooks_file")"
    [ -f "$template" ] || continue
    tool_wanted "$when" "$commands" || continue
    dest="$(expand_home "$hooks_file")"
    if [ "$NO_HOOKS" -eq 1 ]; then
      # Other settings (Claude Code's attribution, permissions) still apply without hooks.
      without_hooks "$template" "$WORKDIR/$tool-no-hooks.json" || { fail "cannot prepare $tool settings without hooks"; continue; }
      template="$WORKDIR/$tool-no-hooks.json"
      # A file that would hold nothing but its format version is not created.
      if [ ! -e "$dest" ] && only_version "$template"; then continue; fi
    fi
    merge_json "$tool hooks and settings" "$template" "$dest"
  done 3< "$REPO/targets.txt"
}

# Explains the hooks the first time an install registers them (hooks/summary.txt), unless
# registering them failed.
explain_hooks() {
  local where name what
  [ "$HAD_HOOKS" -eq 0 ] && [ "$NO_HOOKS" -eq 0 ] && [ "$DRY_RUN" -eq 0 ] && [ "$HOOK_FAILURES" -eq 0 ] || return 0
  section "Hooks installed"
  while IFS='|' read -r where name what; do
    case "$where" in '' | '#'*) continue ;; esac
    printf '  - %s (%s): %s\n' "$(printf '%s' "$name" | sed 's/^ *//; s/ *$//')" \
      "$(printf '%s' "$where" | sed 's/^ *//; s/ *$//')" "$(printf '%s' "$what" | sed 's/^ *//')"
  done < "$REPO/hooks/summary.txt"
  printf '  Turn off advisory hooks with tack config disabled-hooks, or install without any with ./install.sh --no-hooks.\n'
}

# Merges a repo template (with __REPO__ placeholders) into a JSON settings file, keeping the
# user's own keys and hooks and recording ownership so uninstall can reverse it.
merge_json() {
  section "$1"
  local src="$2" dest="$3"
  local base rendered tmp line rc=0
  [ -f "$src" ] || { ok "no ${src#"$REPO"/} in repo, nothing to merge"; return; }
  case "$REPO" in
    *\'*|*\"*|*\\*) fail "the repo path contains quotes or backslashes; move it to a simpler path"; return ;;
  esac
  if [ "$DRY_RUN" -eq 1 ]; then
    ok "would merge $src into $dest"
    return
  fi
  mkdir -p "$(dirname "$dest")"
  [ ! -L "$dest" ] || { fail "settings symlink left untouched: $dest"; return; }

  base="$WORKDIR/settings-base.json"
  rendered="$WORKDIR/settings-repo.json"
  tmp="$WORKDIR/settings-merged.json"

  if [ -s "$dest" ]; then cp "$dest" "$base"; else printf '{}\n' > "$base"; fi
  while IFS= read -r line || [ -n "$line" ]; do
    printf '%s\n' "${line//__REPO__/$REPO}"
  done < "$src" > "$rendered"

  if has python3; then
    python3 "$REPO/lib/settings-merge.py" "$base" "$rendered" > "$tmp" 2>/dev/null
    rc=$?
  elif has jq; then
    jq -s -f "$REPO/lib/settings-merge.jq" "$base" "$rendered" > "$tmp" 2>/dev/null
    rc=$?
  else
    warn "python3 and jq not found: merge $src into $dest by hand"
    return
  fi

  if [ "$rc" -ne 0 ] || [ ! -s "$tmp" ]; then
    fail "$dest is not valid JSON; left untouched. Fix it and re-run"
    return
  fi
  if [ -s "$dest" ] && cmp -s "$tmp" "$dest"; then
    ok "$dest already up to date"
    return
  fi
  ownership_settings "$dest" "$tmp" "$rendered" || { fail "cannot record settings ownership"; return; }
  if [ ! -s "$dest" ]; then
    if cp "$tmp" "$dest"; then ok "created $dest"; else fail "could not create $dest"; fi
    return
  fi
  if cp "$dest" "$dest.bak-$STAMP" && cp "$tmp" "$dest"; then
    ok "merged into $dest (previous copy: $dest.bak-$STAMP)"
  else
    fail "could not write $dest"
  fi
}

# Capture canonical link evidence before installation migrates or repairs those links.
capture_tack_hooks() {
  local link_path root target entry
  : > "$WORKDIR/prior-tack-hooks"
  for link_path in "$HOME/.agents/tack" "$HOME/.agents/harness" "$HOME/.agents/agent-config" \
    "$HOME/.local/bin/tack" "$HOME/.local/bin/harness" "$HOME/.local/bin/agent-config"; do
    [ -L "$link_path" ] || continue
    target="$(readlink "$link_path")"
    ownership_plain_path "$target" || continue
    case "$link_path" in
      "$HOME/.agents/"*) root="${target%/}" ;;
      *)
        case "$target" in
          */bin/tack|*/bin/harness|*/bin/agent-config) root="$(dirname "$(dirname "$target")")" ;;
          *) continue ;;
        esac
        ;;
    esac
    printf '%s/git-hooks\n' "$root" >> "$WORKDIR/prior-tack-hooks"
  done
  for entry in "$OWNERSHIP"/entries/*; do
    [ -d "$entry" ] || continue
    [ "$(cat "$entry/kind")" = git ] || continue
    cat "$entry/target" >> "$WORKDIR/prior-tack-hooks"
  done
}

# Missing checkouts require recorded ownership or a prior canonical link (tack or a former name).
is_tack_hooks() {
  local path="$1" known
  if [ -d "$path" ]; then
    [ -e "$path/_chain" ] && { [ -e "$path/../bin/tack" ] || [ -e "$path/../bin/harness" ] || [ -e "$path/../bin/agent-config" ]; }
    return
  fi
  while IFS= read -r known; do
    [ "$known" != "$path" ] || return 0
  done < "$WORKDIR/prior-tack-hooks"
  return 1
}

# Points git's global core.hooksPath at git-hooks/ (commit-msg, pre-push and pass-through hooks).
# Never overrides a hooksPath you configured for other hooks.
install_git_hooks() {
  section "Git hooks (global)"
  if [ "$NO_HOOKS" -eq 1 ]; then
    # Restoring the user's former hooksPath is uninstall's job, from its ownership records.
    if has git && same_dir "$(git config --global --get core.hooksPath 2>/dev/null)" "$REPO/git-hooks"; then
      warn "skipped (--no-hooks), but the global git hooks from an earlier install remain; ./uninstall.sh removes them"
    else
      ok "skipped (--no-hooks)"
    fi
    return
  fi
  if ! has git; then
    warn "git not found: skipping global git hooks"
    return
  fi
  local current target="$REPO/git-hooks" config_file
  config_file="${GIT_CONFIG_GLOBAL:-$HOME/.gitconfig}"
  if [ -z "${GIT_CONFIG_GLOBAL+x}" ] && [ ! -e "$config_file" ] && [ -e "${XDG_CONFIG_HOME:-$HOME/.config}/git/config" ]; then
    config_file="${XDG_CONFIG_HOME:-$HOME/.config}/git/config"
  fi
  if ! ownership_plain_path "$config_file" || ! ownership_no_symlinks "$config_file"; then
    fail "Git config path is unsafe for ownership tracking"; return
  fi
  [ "$DRY_RUN" -eq 1 ] || chmod +x "$target"/_chain "$target"/commit-msg "$target"/pre-push 2>/dev/null
  current="$(git config --global --get core.hooksPath 2>/dev/null || true)"
  if same_dir "$current" "$target"; then
    ok "core.hooksPath already set to $target"
  elif [ -z "$current" ] || is_tack_hooks "$current"; then
    if [ "$DRY_RUN" -eq 1 ]; then
      ok "would set core.hooksPath to $target"
    else
      mkdir -p "$(dirname "$config_file")" || { fail "cannot create Git config parent"; return; }
      ownership_git "$config_file" "$target" "$current" || { fail "cannot record Git ownership"; return; }
      if git config --global core.hooksPath "$target"; then
        ok "core.hooksPath set to $target${current:+ (was $current)}"
      else
        fail "could not set core.hooksPath"
      fi
    fi
  else
    warn "core.hooksPath is already set to $current; not changing it. To use these hooks: git config --global core.hooksPath '$target'"
  fi
}

# Prints "enabled", "disabled" or "missing" for a plugin id, or "unknown" if it can't tell.
plugin_state() {
  local id="$1" json
  json="$(claude plugin list --json </dev/null 2>/dev/null)" || { echo unknown; return; }
  if has jq; then
    printf '%s' "$json" | jq -r --arg id "$id" \
      '(map(select(.id == $id)) | first) as $p
       | if $p == null then "missing" elif $p.enabled then "enabled" else "disabled" end' 2>/dev/null \
      || echo unknown
  elif has python3; then
    printf '%s' "$json" | python3 -c '
import json, sys
plugins = [p for p in json.load(sys.stdin) if p.get("id") == sys.argv[1]]
print("missing" if not plugins else ("enabled" if plugins[0].get("enabled") else "disabled"))
' "$id" 2>/dev/null || echo unknown
  else
    echo unknown
  fi
}

marketplace_exists() {
  local name="$1" json
  json="$(claude plugin marketplace list --json </dev/null 2>/dev/null)" || return 2
  if has jq; then
    printf '%s' "$json" | jq -e --arg n "$name" 'any(.[]; .name == $n)' >/dev/null 2>&1
  elif has python3; then
    printf '%s' "$json" | python3 -c '
import json, sys
sys.exit(0 if any(m.get("name") == sys.argv[1] for m in json.load(sys.stdin)) else 1)
' "$name"
  else
    return 2
  fi
}

install_plugins() {
  section "Claude Code plugins"
  if [ "$SKIP_PLUGINS" -eq 1 ]; then
    ok "skipped (--skip-plugins)"
    return
  fi
  if [ "$DRY_RUN" -eq 1 ]; then
    while read -r kind name source _; do
      case "$kind" in
        marketplace) ok "would ensure marketplace $name ($source) and refresh its catalog" ;;
        plugin) ok "would ensure plugin $name is installed, updated and enabled" ;;
      esac
    done < "$REPO/plugins.txt"
    return
  fi
  if ! has claude; then
    warn "claude CLI not found: install Claude Code, then re-run ./install.sh"
    return
  fi
  if [ ! -f "$REPO/plugins.txt" ]; then
    ok "no plugins.txt, nothing to install"
    return
  fi

  local kind name source state rc
  # fd 3 so that commands inside the loop can't consume the file's lines
  while read -r kind name source _ <&3; do
    case "$kind" in
      ''|'#'*) continue ;;
      marketplace)
        marketplace_exists "$name"
        rc=$?
        if [ "$rc" -eq 1 ]; then
          if claude plugin marketplace add "$source" </dev/null >/dev/null 2>&1; then
            ok "marketplace $name added"
          else
            fail "could not add marketplace $name ($source)"
            continue
          fi
        elif [ "$rc" -eq 2 ]; then
          # Can't tell: adding an existing marketplace is harmless if it fails
          claude plugin marketplace add "$source" </dev/null >/dev/null 2>&1 || true
        fi
        if claude plugin marketplace update "$name" </dev/null >/dev/null 2>&1; then
          ok "marketplace $name refreshed"
        else
          warn "could not refresh marketplace $name; using its cached catalog"
        fi
        ;;
      plugin)
        state="$(plugin_state "$name")"
        case "$state" in
          missing|unknown)
            if claude plugin install "$name" </dev/null >/dev/null 2>&1; then
              ok "$name installed"
            else
              fail "could not install $name (try: claude plugin install $name)"
              continue
            fi
            ;;
          *)
            if claude plugin update "$name" </dev/null >/dev/null 2>&1; then
              ok "$name up to date"
            else
              warn "could not update $name; keeping the installed version"
            fi
            ;;
        esac
        if [ "$(plugin_state "$name")" = "disabled" ]; then
          if claude plugin enable "$name" </dev/null >/dev/null 2>&1; then
            ok "$name enabled"
          else
            fail "could not enable $name"
          fi
        fi
        ;;
      *)
        warn "plugins.txt: unknown line type '$kind'"
        ;;
    esac
  done 3< "$REPO/plugins.txt"
}

# Git Bash on Windows copies files for `ln -s` unless asked for real symlinks, which Windows
# grants only with Developer Mode or as administrator; a copy would silently go stale.
windows_symlinks() {
  case "$(uname -s)" in MINGW* | MSYS* | CYGWIN*) ;; *) return 0 ;; esac
  export MSYS="${MSYS:+$MSYS }winsymlinks:nativestrict"
  export CYGWIN="${CYGWIN:+$CYGWIN }winsymlinks:nativestrict"
  ln -s "$REPO/README.md" "$WORKDIR/symlink-check" 2>/dev/null && return 0
  fail "Windows refused to create a symlink: turn on Developer Mode (Settings > System > For developers) and re-run, or install inside WSL2 (docs/editors.md#windows)"
  exit 1
}

main() {
  printf '%sInstalling tack from %s%s\n' "$C_HEAD" "$REPO" "$C_OFF"
  windows_symlinks
  if [ "$DRY_RUN" -eq 0 ]; then
    migrate_tool_dir "${XDG_STATE_HOME:-$HOME/.local/state}" || { fail "cannot move the former state directory to agent-tack"; exit 1; }
    migrate_tool_dir "${XDG_CONFIG_HOME:-$HOME/.config}" || warn "could not move ~/.config/agent-harness (the former name) to agent-tack; it is still read"
  fi
  # The hooks are explained the first time they are registered: no tagged hooks exist yet.
  HAD_HOOKS=0
  grep -qsE '#(tack|harness)' "$HOME/.claude/settings.json" "$HOME/.codex/hooks.json" && HAD_HOOKS=1
  ownership_init || exit 1
  capture_tack_hooks
  install_links
  HOOK_FAILURES="$FAILURES"
  merge_settings
  install_git_hooks
  HOOK_FAILURES=$((FAILURES - HOOK_FAILURES))
  install_plugins
  install_mods
  install_vscode
  install_codex_agents
  explain_hooks

  section "Summary"
  if [ "$FAILURES" -gt 0 ]; then
    fail "$FAILURES step(s) failed, $WARNINGS warning(s). Fix the errors above and re-run; it's safe."
    exit 1
  fi
  ok "done with $WARNINGS warning(s). Restart Claude Code and Codex to load the changes."
}

main
