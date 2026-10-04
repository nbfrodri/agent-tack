#!/usr/bin/env bash
# Claude Code mods shipped in plugins/: a local marketplace in this checkout, one plugin per mod.
# Sourced by install.sh (install_mods) and lib/doctor.sh (check_mods); defines functions only.

MODS_MARKETPLACE=agent-tack-mods
# Name used before the rename; installs from that time are retired so mods do not load twice.
MODS_LEGACY_MARKETPLACE=agent-harness-mods

mods_has() { command -v "$1" >/dev/null 2>&1; }

# Success unless the global tack.mods (or legacy harness.mods) is false.
mods_enabled() {
  local value
  mods_has git || return 0
  value="$(key_get --bool global mods || true)"
  [ "$value" != false ]
}

mods_list() {
  local manifest
  for manifest in "$1"/plugins/*/.claude-plugin/plugin.json; do
    [ -f "$manifest" ] || continue
    basename "$(dirname "$(dirname "$manifest")")"
  done
}

# Prints "enabled", "disabled" or "missing" for a plugin id, or "unknown".
mods_plugin_state() {
  local id="$1" json
  json="$(claude plugin list --json </dev/null 2>/dev/null)" || { echo unknown; return; }
  if mods_has jq; then
    printf '%s' "$json" | jq -r --arg id "$id" \
      '(map(select(.id == $id)) | first) as $p
       | if $p == null then "missing" elif $p.enabled then "enabled" else "disabled" end' 2>/dev/null \
      || echo unknown
  elif mods_has python3; then
    printf '%s' "$json" | python3 -c '
import json, sys
plugins = [p for p in json.load(sys.stdin) if p.get("id") == sys.argv[1]]
print("missing" if not plugins else ("enabled" if plugins[0].get("enabled") else "disabled"))
' "$id" 2>/dev/null || echo unknown
  else
    echo unknown
  fi
}

# Success when the marketplace exists, 1 when it does not, 2 when that cannot be told.
mods_marketplace_exists() {
  local json
  json="$(claude plugin marketplace list --json </dev/null 2>/dev/null)" || return 2
  if mods_has jq; then
    printf '%s' "$json" | jq -e --arg n "$1" 'any(.[]; .name == $n)' >/dev/null 2>&1
  elif mods_has python3; then
    printf '%s' "$json" | python3 -c '
import json, sys
sys.exit(0 if any(m.get("name") == sys.argv[1] for m in json.load(sys.stdin)) else 1)
' "$1"
  else
    return 2
  fi
}

# Prints the directory a marketplace was added from (empty for remote ones or when unknown).
mods_marketplace_path() {
  local json
  json="$(claude plugin marketplace list --json </dev/null 2>/dev/null)" || return 0
  if mods_has jq; then
    printf '%s' "$json" | jq -r --arg n "$1" 'map(select(.name == $n)) | first | .path // empty' 2>/dev/null
  elif mods_has python3; then
    printf '%s' "$json" | python3 -c '
import json, sys
found = [m for m in json.load(sys.stdin) if m.get("name") == sys.argv[1]]
print(found[0].get("path") or "" if found else "")
' "$1" 2>/dev/null
  fi
}

mods_skip_reason() {
  if [ "$SKIP_MODS" -eq 1 ]; then echo "--skip-mods"; return 0; fi
  if [ "$SKIP_PLUGINS" -eq 1 ]; then echo "--skip-plugins"; return 0; fi
  if ! mods_enabled; then echo "git config harness.mods is false"; return 0; fi
  return 1
}

# Removes the mods and marketplace installed under the name used before the rename. The name is
# this project's own, so its presence is enough evidence that this installer added it.
mods_retire_legacy() {
  local mod
  mods_marketplace_exists "$MODS_LEGACY_MARKETPLACE" || return 0
  for mod in $(mods_list "$REPO"); do
    claude plugin uninstall "$mod@$MODS_LEGACY_MARKETPLACE" </dev/null >/dev/null 2>&1 || true
  done
  if claude plugin marketplace remove "$MODS_LEGACY_MARKETPLACE" </dev/null >/dev/null 2>&1; then
    ok "retired the former mods marketplace $MODS_LEGACY_MARKETPLACE"
  else
    warn "could not remove the former marketplace $MODS_LEGACY_MARKETPLACE; remove it if the mods appear twice"
  fi
}

install_mods() {
  section "Claude Code mods"
  local reason mod id state rc path
  if reason="$(mods_skip_reason)"; then
    ok "skipped ($reason)"
    return
  fi
  if [ "$DRY_RUN" -eq 1 ]; then
    ok "would ensure local marketplace $MODS_MARKETPLACE ($REPO/plugins)"
    for mod in $(mods_list "$REPO"); do
      ok "would ensure mod $mod is installed, updated and enabled"
    done
    return
  fi
  if ! has claude; then
    warn "claude CLI not found: install Claude Code, then re-run ./install.sh to load the mods"
    return
  fi

  mods_retire_legacy
  mods_marketplace_exists "$MODS_MARKETPLACE"
  rc=$?
  # A checkout moved elsewhere leaves the marketplace pointing at a folder that no longer
  # serves the mods, so refreshes and updates fail; re-add it from this checkout.
  if [ "$rc" -eq 0 ]; then
    path="$(mods_marketplace_path "$MODS_MARKETPLACE")"
    if [ -n "$path" ] && [ "${path%/}" != "$REPO/plugins" ]; then
      if claude plugin marketplace remove "$MODS_MARKETPLACE" </dev/null >/dev/null 2>&1 \
        && claude plugin marketplace add "$REPO/plugins" </dev/null >/dev/null 2>&1; then
        ok "marketplace $MODS_MARKETPLACE re-added from $REPO/plugins (the checkout moved from $path)"
      else
        fail "could not re-add marketplace $MODS_MARKETPLACE from $REPO/plugins (it points to $path)"
        return
      fi
    fi
  fi
  if [ "$rc" -eq 1 ]; then
    if claude plugin marketplace add "$REPO/plugins" </dev/null >/dev/null 2>&1; then
      ownership_modmarket "$MODS_MARKETPLACE" || { fail "cannot record marketplace $MODS_MARKETPLACE"; return; }
      ok "local marketplace $MODS_MARKETPLACE added"
    else
      fail "could not add local marketplace $MODS_MARKETPLACE ($REPO/plugins)"
      return
    fi
  elif [ "$rc" -eq 2 ]; then
    claude plugin marketplace add "$REPO/plugins" </dev/null >/dev/null 2>&1 || true
  fi
  claude plugin marketplace update "$MODS_MARKETPLACE" </dev/null >/dev/null 2>&1 \
    || warn "could not refresh marketplace $MODS_MARKETPLACE; using its cached catalog"

  for mod in $(mods_list "$REPO"); do
    id="$mod@$MODS_MARKETPLACE"
    state="$(mods_plugin_state "$id")"
    case "$state" in
      missing|unknown)
        if claude plugin install "$id" </dev/null >/dev/null 2>&1; then
          ownership_mod "$id" || { fail "cannot record mod $mod"; continue; }
          ok "mod $mod installed"
        else
          fail "could not install mod $mod (try: claude plugin install $id)"
          continue
        fi
        ;;
      *)
        if claude plugin update "$id" </dev/null >/dev/null 2>&1; then
          ok "mod $mod up to date"
        else
          warn "could not update mod $mod; keeping the installed version"
        fi
        ;;
    esac
    if [ "$(mods_plugin_state "$id")" = disabled ]; then
      if claude plugin enable "$id" </dev/null >/dev/null 2>&1; then ok "mod $mod enabled"
      else fail "could not enable mod $mod"; fi
    fi
  done
}
