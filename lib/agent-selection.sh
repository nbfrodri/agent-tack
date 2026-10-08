#!/usr/bin/env bash
# Remove only unchanged installer-owned roles when their optional catalog is deselected.
# Caller provides REPO, HOME, DRY_RUN, ownership helpers, logging and file_sha256.
deselect_agent() {
  local kind="$1" source="$2" target="$3" parent recorded
  parent="$(dirname "$target")"
  while [ "$parent" != "$HOME" ] && [ "$parent" != / ]; do
    if [ -L "$parent" ]; then warn "kept $target: symlink parent"; return; fi
    parent="$(dirname "$parent")"
  done
  [ "$parent" = "$HOME" ] || { warn "kept $target: outside HOME"; return; }
  if [ "$kind" = link ]; then
    [ -L "$target" ] && [ "$(readlink "$target")" = "$source" ] || return 0
    if ownership_link_replaced "$target"; then
      warn "kept $target: it replaced your file; uninstall restores it"
    elif [ "$DRY_RUN" -eq 1 ]; then ok "would remove $target (agent roles disabled)"
    elif ownership_release_link "$target"; then
      rm -f "$target" && ok "removed $target (agent roles disabled)"
    fi
    return
  fi
  [ -f "$target" ] && [ ! -L "$target" ] || return 0
  ownership_find generated "$target"
  [ -n "$OWN_ENTRY" ] || return 0
  if [ "$(cat "$OWN_ENTRY/repo" 2>/dev/null)" != "$REPO" ] ||
     [ "$(ownership_parent_identity "$(dirname "$target")")" != "$(cat "$OWN_ENTRY/parent_identity" 2>/dev/null)" ]; then
    warn "kept $target: ownership location changed"
    return
  fi
  recorded="$(cat "$OWN_ENTRY/sha256" 2>/dev/null)"
  if [ "$(file_sha256 "$target")" != "$recorded" ]; then
    warn "kept $target: edited agent"
  elif [ "$DRY_RUN" -eq 1 ]; then ok "would remove $target (agent roles disabled)"
  else rm -f "$target" && ok "removed $target (agent roles disabled)"; fi
  # Preserve ownership metadata: reinstall can update it; uninstall handles absent files.
}
