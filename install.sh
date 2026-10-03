#!/usr/bin/env bash
# Links this repo's skills, agents and global instructions into Claude Code and Codex.
# Safe to re-run. Existing files that are not symlinks are moved to *.bak.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

link() {
  local src="$1" dest="$2"
  mkdir -p "$(dirname "$dest")"
  if [ -e "$dest" ] && [ ! -L "$dest" ]; then
    mv "$dest" "$dest.bak"
    echo "backup: $dest -> $dest.bak"
  fi
  ln -sfn "$src" "$dest"
  echo "linked: $dest -> $src"
}

# Global instructions
link "$REPO/global/AGENTS.md" "$HOME/.claude/CLAUDE.md"
link "$REPO/global/AGENTS.md" "$HOME/.codex/AGENTS.md"

# Skills (shared standard folder + each tool's own folder)
for skill in "$REPO"/skills/*/; do
  name="$(basename "$skill")"
  for dir in "$HOME/.agents/skills" "$HOME/.claude/skills" "$HOME/.codex/skills"; do
    link "${skill%/}" "$dir/$name"
  done
done

# Subagents (Claude Code format: agents/<name>.md)
for agent in "$REPO"/agents/*.md; do
  [ -e "$agent" ] || continue
  link "$agent" "$HOME/.claude/agents/$(basename "$agent")"
done
