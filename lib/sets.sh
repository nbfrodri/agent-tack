#!/usr/bin/env bash
# Sets (sets.txt): named bundles of skills, agents and Claude plugins, active everywhere through
# `tack set use NAME --global`. Sourced by install.sh and lib/doctor.sh after lib/keys.sh and
# lib/skill-groups.sh. What needs a checkout of sources.txt is in lib/sets.py; this file reads
# sets.txt in plain bash so tack's own skills, agents and plugins install without python.

# sets_global: the sets active everywhere, comma-separated without spaces; empty when none.
sets_global() { key_get global sets 2>/dev/null | tr -d ' '; }

sets_store() { printf '%s/agent-tack/sources' "${XDG_DATA_HOME:-$HOME/.local/share}"; }

# set_items KIND: prints the items of that kind listed by the sets active everywhere.
set_items() {
  local set kind item _rest
  # Read the setting once per run: this is called for every skill and agent.
  [ -n "${SETS_GLOBAL_CACHE+x}" ] || SETS_GLOBAL_CACHE="$(sets_global)"
  [ -n "$SETS_GLOBAL_CACHE" ] && [ -f "$REPO/sets.txt" ] || return 0
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

# agent_selected NAME: the whole catalog is on (agent-roles), or an active set lists the role.
agent_selected() { roles_enabled || set_selected agent "$1"; }

# install_set_skills DIRS: links the skills that active sets take from sources.txt into every
# skills folder (one per line), and removes its own links to skills no active set lists any more.
# Caller provides section, ok, warn, fail, has, link, DRY_RUN, WORKDIR and the ownership helpers.
install_set_skills() {
  local dirs="$1" store plan="$WORKDIR/set-skills" name path dir entry target fetch=''
  store="$(sets_store)"
  section "Sets"
  : > "$plan"
  if [ -z "$(sets_global)" ]; then
    ok "no set is active everywhere (tack set list, tack set use NAME --global)"
  else
    ok "active everywhere: $(sets_global)"
    if ! has python3 || ! has git; then
      warn "python3 and git are needed for the skills that sets take from sources.txt"
      return
    fi
    [ "$DRY_RUN" -eq 0 ] || fetch=--no-fetch
    if ! python3 "$REPO/lib/sets.py" --root "$REPO" plan $fetch > "$plan" 2> "$WORKDIR/set-errors"; then
      fail "sets: $(head -n 3 "$WORKDIR/set-errors" | tr '\n' ' ')"
      return
    fi
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
