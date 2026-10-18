#!/usr/bin/env bash
# Completion data queries (bin/tack) and generated-file installation (install.sh).

completion_candidates() {
  local kind="${1:-}" file name values
  case "$kind" in
    commands) completion_commands ;;
    set-commands) printf '%s\n' list show use drop sync update suggest index skip reminder plan check agent ;;
    sets-all|sets-active|sets-inactive)
      command -v python3 >/dev/null 2>&1 || return 0
      case "$kind" in
        sets-all) set -- ;;
        sets-active) set -- --active ;;
        sets-inactive) set -- --inactive ;;
      esac
      python3 -I -S "$TACK_ROOT/lib/sets.py" "$TACK_ROOT" names "$@"
      ;;
    roles) awk '$1 !~ /^#/ && $2 == "agent" && !seen[$3]++ { print $3 }' "$TACK_ROOT/sets.txt" ;;
    features) awk 'NF && $1 !~ /^#/ { print $1 }' "$TACK_ROOT/features.txt" ;;
    feature-values)
      while read -r name _ _ values _; do
        [ "$name" = "${2:-}" ] || continue
        case "$values" in
          bool) printf '%s\n' true false ;;
          list:*) ;;
          *'|'*) printf '%s\n' "$values" | tr '|' '\n' ;;
        esac
        break
      done < "$TACK_ROOT/features.txt"
      ;;
    modes)
      {
        echo auto
        for file in "$TACK_ROOT"/modes/*.md "$(user_modes_dir)"/*.md; do
          [ -f "$file" ] || continue
          name="${file##*/}"
          printf '%s\n' "${name%.md}"
        done
      } | awk '!seen[$0]++'
      ;;
    tiers) printf '%s\n' economical balanced strongest ;;
    usage-kinds) printf '%s\n' five_hour seven_day context ;;
    *) echo 'tack: usage: tack __complete KIND [NAME]' >&2; return 2 ;;
  esac
}

completion_sha256() {
  python3 -I -c 'import hashlib, sys; print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())' "$1"
}

install_completions() {
  # Keep the installer's concise output within its existing line budget.
  flush_items
  printf '%s== Shell completions ==%s\n' "${C_HEAD:-}" "${C_OFF:-}"
  if [ "$(key_get --bool global completions || true)" = false ]; then
    ok "skipped (git config tack.completions is false)"
    return
  fi
  local shell target recorded
  for shell in bash fish; do
    [ "$shell" != fish ] || has fish || continue
    case "$shell" in
      bash) target="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/tack" ;;
      fish) target="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/tack.fish" ;;
    esac
    ownership_find generated "$target"
    recorded=""
    [ -z "$OWN_ENTRY" ] || recorded="$(cat "$OWN_ENTRY/sha256" 2>/dev/null)"
    if [ -L "$target" ] || { [ -e "$target" ] && [ -z "$recorded" ]; }; then
      warn "$target exists and is not managed by tack; left untouched"
      continue
    fi
    if ! has python3; then
      warn "python3 not found: $shell completion not generated"
      continue
    fi
    if [ -n "$recorded" ] && [ -e "$target" ] && [ "$(completion_sha256 "$target")" != "$recorded" ]; then
      warn "$target was edited; kept your version"
      continue
    fi
    if [ -e "$target" ] && cmp -s "$REPO/completions/tack.$shell" "$target"; then
      item_kept "$shell completion up to date"
      continue
    fi
    if [ "$DRY_RUN" -eq 1 ]; then
      ok "would write $shell completion $target"
      continue
    fi
    if mkdir -p "$(dirname "$target")" && cp "$REPO/completions/tack.$shell" "$target" &&
      ownership_generated "$target" "$(completion_sha256 "$target")"; then
      item_new "$shell completion written"
    else
      fail "could not write $target"
    fi
  done
}
