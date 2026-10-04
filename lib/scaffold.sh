#!/usr/bin/env bash
# `tack enable --scaffold`: copies the minimal docs structure from the project-docs templates
# into the repository root, creating only files that do not exist yet.
set -u

repo="$1" root="$2"
assets="$repo/skills/project-docs/assets"
# destination | template (relative to the assets folder); CLAUDE.md only points to AGENTS.md.
plan="AGENTS.md|AGENTS.md
docs/architecture.md|docs/architecture.md
docs-map.txt|docs-map.txt
docs/plans/template.md|docs/plans/template.md
docs/handoffs/template.md|docs/handoffs/template.md
docs/ai/log.md|docs/ai/log.md
CLAUDE.md|-"

while IFS='|' read -r dest template; do
  if [ -e "$root/$dest" ] || [ -L "$root/$dest" ]; then
    echo "kept $dest"
    continue
  fi
  mkdir -p "$(dirname "$root/$dest")" || { echo "tack: cannot create $(dirname "$dest")" >&2; exit 1; }
  if [ "$template" = - ]; then
    printf '@AGENTS.md\n' > "$root/$dest"
  else
    cp "$assets/$template" "$root/$dest" || { echo "tack: cannot copy $template" >&2; exit 1; }
  fi
  echo "created $dest"
done <<EOF
$plan
EOF
echo "Next: ask the assistant to fill AGENTS.md and docs/architecture.md from the code, or to run the new-project skill for tests, lint and CI."
