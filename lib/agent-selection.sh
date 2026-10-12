#!/usr/bin/env bash
# Remove only unchanged installer-owned roles when their optional catalog is deselected.
# Caller provides REPO, HOME, DRY_RUN, ownership helpers, logging and file_sha256.
deselect_agent() {
  local kind="$1" source="$2" target="$3" parent recorded recorded_repo
  parent="$(dirname "$target")"
  while [ "$parent" != "$HOME" ] && [ "$parent" != / ]; do
    if [ -L "$parent" ]; then warn "kept $target: symlink parent"; return; fi
    parent="$(dirname "$parent")"
  done
  [ "$parent" = "$HOME" ] || { warn "kept $target: outside HOME"; return; }
  if [ "$kind" = link ]; then
    [ -L "$target" ] && [ "$(readlink "$target")" = "$source" ] || return 0
    if ownership_link_replaced "$target" && ! ownership_original_gone "$target"; then
      warn "kept $target: it replaced your file; uninstall restores it"
    elif [ "$DRY_RUN" -eq 1 ]; then ok "would remove $target (no active set lists it)"
    elif ownership_release_link "$target" || ownership_release_dangling "$target"; then
      rm -f "$target" && ok "removed $target (no active set lists it)"
    fi
    return
  fi
  [ -f "$target" ] && [ ! -L "$target" ] || return 0
  ownership_find generated "$target"
  [ -n "$OWN_ENTRY" ] || return 0
  # A record from a checkout that no longer exists is this configuration's former location, moved
  # or deleted since; one from another checkout that is still there belongs to that installation.
  recorded_repo="$(cat "$OWN_ENTRY/repo" 2>/dev/null)"
  if { [ "$recorded_repo" != "$REPO" ] && [ -d "$recorded_repo" ]; } ||
     ! ownership_same_identity "$(cat "$OWN_ENTRY/parent_identity" 2>/dev/null)" "$(ownership_parent_identity "$(dirname "$target")")"; then
    warn "kept $target: ownership location changed"
    return
  fi
  recorded="$(cat "$OWN_ENTRY/sha256" 2>/dev/null)"
  if [ "$(file_sha256 "$target")" != "$recorded" ]; then
    warn "kept $target: edited agent"
  elif [ "$DRY_RUN" -eq 1 ]; then ok "would remove $target (no active set lists it)"
  else rm -f "$target" && ok "removed $target (no active set lists it)"; fi
  # Preserve ownership metadata: reinstall can update it; uninstall handles absent files.
}
