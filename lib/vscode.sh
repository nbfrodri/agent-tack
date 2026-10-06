#!/usr/bin/env bash
# VS Code: turns on chat.useAgentsMdFile so Copilot Chat loads each project's AGENTS.md.
# Sourced by install.sh (install_vscode) and lib/doctor.sh (check_vscode); defines functions only.

VSCODE_KEY=chat.useAgentsMdFile

vscode_has() { command -v "$1" >/dev/null 2>&1; }

# Success unless the global tack.vscodeAgentsMd is false.
vscode_enabled() {
  local value
  vscode_has git || return 0
  value="$(key_get --bool global vscodeAgentsMd || true)"
  [ "$value" != false ]
}

# Command and product folder name, one product per line, separated by "|".
vscode_products() {
  printf '%s\n' 'code|Code' 'code-insiders|Code - Insiders' 'codium|VSCodium'
}

vscode_settings_path() {
  if [ "$(uname 2>/dev/null)" = Darwin ]; then
    printf '%s/Library/Application Support/%s/User/settings.json' "$HOME" "$1"
  else
    printf '%s/%s/User/settings.json' "${XDG_CONFIG_HOME:-$HOME/.config}" "$1"
  fi
}

# Prints absent, unset, true, false, other or invalid for a settings file.
vscode_state() {
  python3 "$REPO/lib/vscode_settings.py" state "$1" 2>/dev/null || echo invalid
}

install_vscode() {
  section "VS Code Copilot Chat"
  if ! vscode_enabled; then
    ok "skipped (git config tack.vscodeAgentsMd is false)"
    return
  fi
  local command product path state created found=0
  while IFS='|' read -r command product <&4; do
    vscode_has "$command" || continue
    found=1
    path="$(vscode_settings_path "$product")"
    if [ "$DRY_RUN" -eq 1 ]; then
      ok "would set $VSCODE_KEY in $path unless it is already set"
      continue
    fi
    if ! vscode_has python3; then
      warn "python3 not found: set \"$VSCODE_KEY\": true in $path yourself"
      continue
    fi
    state="$(vscode_state "$path")"
    case "$state" in
      true|false|other) ok "$product: $VSCODE_KEY is already set; left as is" ;;
      invalid)
        warn "$product: $path has comments, trailing commas or invalid JSON, so it was not changed; add \"$VSCODE_KEY\": true there yourself" ;;
      absent|unset)
        created=0
        [ "$state" = absent ] && created=1
        if ! mkdir -p "$(dirname "$path")" || ! python3 "$REPO/lib/vscode_settings.py" add "$path"; then
          fail "$product: could not set $VSCODE_KEY in $path"
          continue
        fi
        ownership_vscode "$path" "$created" || { fail "cannot record $path"; continue; }
        ok "$product: $VSCODE_KEY set to true in $path"
        ;;
    esac
  done 4< <(vscode_products)
  [ "$found" -eq 1 ] || ok "no VS Code found (code, code-insiders or codium)"
}
