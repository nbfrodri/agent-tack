#!/usr/bin/env bash
# Codex custom agents: renders agents/*.md as ~/.codex/agents/<name>.toml. Sourced by install.sh,
# which provides section, ok, warn, fail, has, DRY_RUN, REPO and the ownership helpers.

file_sha256() { python3 -c 'import hashlib, sys; print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())' "$1"; }

install_codex_agents() {
  section "Codex agents"
  local dir="$HOME/.codex/agents" agent name target rendered recorded
  if ! has python3; then
    warn "python3 not found: Codex agents not generated"
    return
  fi
  for agent in "$REPO"/agents/*.md; do
    name="$(basename "$agent" .md)"
    target="$dir/$name.toml"
    if ! agent_selected "$name"; then deselect_agent generated "$agent" "$target"; continue; fi
    [ "$DRY_RUN" -eq 1 ] || mkdir -p "$dir" || { fail "cannot create $dir"; return; }
    rendered="$WORKDIR/codex-agent-$name.toml"
    python3 "$REPO/lib/codex_agents.py" "$agent" > "$rendered" 2>/dev/null || { fail "cannot render $agent"; continue; }
    ownership_find generated "$target"
    recorded=""
    [ -z "$OWN_ENTRY" ] || recorded="$(cat "$OWN_ENTRY/sha256" 2>/dev/null)"
    if [ -e "$target" ] && [ -z "$recorded" ]; then
      warn "$target exists and is not managed by tack; left untouched"
      continue
    fi
    if [ -n "$recorded" ] && [ -e "$target" ] && [ "$(file_sha256 "$target")" != "$recorded" ]; then
      warn "$target was edited; kept your version"
      continue
    fi
    if [ -e "$target" ] && cmp -s "$rendered" "$target"; then
      item_kept "Codex agent $name up to date"
      continue
    fi
    if [ "$DRY_RUN" -eq 1 ]; then
      ok "would write Codex agent $target"
      continue
    fi
    if cp "$rendered" "$target" && ownership_generated "$target" "$(file_sha256 "$target")"; then
      item_new "Codex agent $name written"
    else
      fail "could not write $target"
    fi
  done
}
