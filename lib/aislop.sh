#!/usr/bin/env bash
# aislop: installs the scanner the completion hook's slop check runs, when tack.installAislop is true.
# Sourced by install.sh (install_aislop); defines functions only.

# Pinned like sources.txt: moving it is a reviewed change.
AISLOP_VERSION=0.20.0

install_aislop() {
  section "aislop"
  if [ "$(key_get --bool global installAislop || true)" != true ]; then
    ok "skipped (git config --global tack.installAislop true installs it)"
    return
  fi
  if has aislop; then
    ok "aislop found"
    return
  fi
  local command
  if has mise; then command="mise use -g npm:aislop@$AISLOP_VERSION"
  elif has npm; then command="npm install -g aislop@$AISLOP_VERSION"
  else
    warn "aislop not installed: install mise or npm, then re-run ./install.sh"
    return
  fi
  if [ "$DRY_RUN" -eq 1 ]; then
    ok "would install aislop: $command"
    return
  fi
  # shellcheck disable=SC2086 # command is one of the two fixed lines above
  if $command >/dev/null 2>&1; then ok "installed aislop $AISLOP_VERSION ($command)"
  else warn "could not install aislop: run $command"; fi
}
