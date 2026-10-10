#!/usr/bin/env bash
# Install native roles declared in targets.txt; preserve foreign and edited files.
install_native_agents() {
  local tool when commands dir extension agent name target rendered recorded parent safe
  while read -r tool when commands _ _ dir _ <&3; do
    case "$tool" in '' | '#'* | claude | codex) continue ;; esac
    [ "${dir:--}" != - ] || continue
    tool_wanted "$when" "$commands" || continue
    if ! has python3; then warn "python3 not found: $tool agents not generated"; continue; fi
    extension="$(python3 "$REPO/lib/native_agents.py" --extension "$tool")" || { fail "unsupported agent format: $tool"; continue; }
    dir="$(expand_home "$dir")"
    safe=true parent="$dir"
    while [ "$parent" != "$HOME" ] && [ "$parent" != / ]; do
      if [ -L "$parent" ]; then safe=false; break; fi
      parent="$(dirname "$parent")"
    done
    if [ "$parent" != "$HOME" ] || [ "$safe" = false ]; then
      warn "$tool agents directory is outside HOME or has symlink parents; left untouched"
      continue
    fi
    section "$tool agents"
    for agent in "$REPO"/agents/*.md; do
      name="$(basename "$agent" .md)"
      target="$dir/$name$extension"
      if ! agent_selected "$name"; then deselect_agent generated "$agent" "$target"; continue; fi
      [ "$DRY_RUN" -eq 1 ] || mkdir -p "$dir" || { fail "cannot create $dir"; break; }
      rendered="$WORKDIR/$tool-agent-$name$extension"
      python3 "$REPO/lib/native_agents.py" "$tool" "$agent" > "$rendered" || { fail "cannot render $agent for $tool"; continue; }
      ownership_find generated "$target"
      recorded=''
      [ -z "$OWN_ENTRY" ] || recorded="$(cat "$OWN_ENTRY/sha256" 2>/dev/null)"
      if [ -L "$target" ] || { [ -e "$target" ] && [ -z "$recorded" ]; }; then
        warn "$target exists and is not managed by tack; left untouched"; continue
      fi
      if [ -e "$target" ] && [ "$(file_sha256 "$target")" != "$recorded" ]; then
        warn "$target was edited; kept your version"; continue
      fi
      if [ -e "$target" ] && cmp -s "$rendered" "$target"; then
        item_kept "$tool agent $name up to date"; continue
      fi
      if [ "$DRY_RUN" -eq 1 ]; then ok "would write $tool agent $target"; continue; fi
      if cp "$rendered" "$target" && ownership_generated "$target" "$(file_sha256 "$target")"; then
        item_new "$tool agent $name written"
      else fail "could not write $target"; fi
    done
  done 3< "$REPO/targets.txt"
}
