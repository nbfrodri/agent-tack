#!/usr/bin/env bash
# Sets (sets.txt): named bundles of skills, agents and Claude plugins. They are the one way a
# skill or an agent role gets installed: the `core` set is always active, and the rest through
# `tack set use NAME --global`. Sourced by install.sh and lib/doctor.sh after lib/keys.sh. What
# needs a checkout of sources.txt is in lib/sets.py; this file reads sets.txt in plain bash so
# this repository's own skills, agents and plugins install without python.

# sets_global: the sets active everywhere, comma-separated without spaces, core first.
sets_global() {
  local chosen
  chosen="$(key_get global sets 2>/dev/null | tr -d ' ')"
  printf 'core%s\n' "${chosen:+,$chosen}"
}

sets_store() { printf '%s/agent-tack/sources' "${XDG_DATA_HOME:-$HOME/.local/share}"; }

# set_items KIND: prints the items of that kind listed by the sets active everywhere.
set_items() {
  local set kind item _rest
  [ -f "$REPO/sets.txt" ] || return 0
  # Read the setting once per run: this is called for every skill and agent.
  [ -n "${SETS_GLOBAL_CACHE:-}" ] || SETS_GLOBAL_CACHE="$(sets_global)"
  # IFS is set here: a caller may hold a different one (doctor's tool checks split on commas).
  while IFS=$' \t' read -r set kind item _rest; do
    [ "$kind" = "$1" ] || continue
    case ",$SETS_GLOBAL_CACHE," in *",$set,"*) printf '%s\n' "$item" ;; esac
  done < "$REPO/sets.txt"
}

# set_selected KIND NAME: succeeds when a set active everywhere lists that item.
set_selected() {
  local item
  while IFS= read -r item; do
    [ "$item" != "$2" ] || return 0
  done <<EOF
$(set_items "$1")
EOF
  return 1
}

# skill_selected NAME, agent_selected NAME: a set active everywhere lists this repository's
# skill or agent role.
skill_selected() { set_selected skill "$1"; }
agent_selected() { set_selected agent "$1"; }

# sets_legacy_notice: skill groups and the agent-roles switch were replaced by sets and are no
# longer read. Says so while a former choice is still saved, because it now installs nothing.
# Caller provides warn.
sets_legacy_notice() {
  if key_scope global skillGroups || key_scope global agentRoles; then
    warn "the former skill-groups and agent-roles settings are no longer read: run tack migrate to turn them into sets"
  fi
}

# install_set_skills DIRS: links the skills that active sets take from sources.txt into every
# skills folder (one per line), and removes its own links to skills no active set lists any more.
# Caller provides section, ok, warn, fail, has, link, DRY_RUN, WORKDIR and the ownership helpers.
install_set_skills() {
  local dirs="$1" store plan="$WORKDIR/set-skills" name path dir entry target fetch=''
  store="$(sets_store)"
  section "Skills from other collections"
  : > "$plan"
  # Only a skill taken from sources.txt (SOURCE:PATH) needs a checkout, and so python and git.
  if set_items skill | grep -q ':'; then
    if ! has python3 || ! has git; then
      warn "python3 and git are needed for the skills that sets take from sources.txt"
      return
    fi
    [ "$DRY_RUN" -eq 0 ] || fetch=--no-fetch
    if ! python3 "$REPO/lib/sets.py" "$REPO" plan $fetch > "$plan" 2> "$WORKDIR/set-errors"; then
      fail "sets: $(head -n 3 "$WORKDIR/set-errors" | tr '\n' ' ')"
      return
    fi
  else
    ok "no active set takes a skill from sources.txt"
  fi
  while IFS=$'\t' read -r name path; do
    [ -n "$name" ] || continue
    while IFS= read -r dir; do
      link "$path" "$dir/$name"
    done <<EOF
$dirs
EOF
  done < "$plan"
  while IFS= read -r dir; do
    for entry in "$dir"/*; do
      [ -L "$entry" ] || continue
      target="$(readlink "$entry")"
      case "$target" in "$store"/*) ;; *) continue ;; esac
      ! grep -qxF "${entry##*/}	$target" "$plan" || continue
      if [ "$DRY_RUN" -eq 1 ]; then ok "would remove $entry (no active set lists it)"
      elif ownership_link_replaced "$entry"; then warn "kept $entry: it replaced a skill of yours, which ./uninstall.sh restores"
      elif ownership_release_link "$entry"; then rm -f "$entry" && ok "removed $entry (no active set lists it)"; fi
    done
  done <<EOF
$dirs
EOF
}
