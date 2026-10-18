#!/usr/bin/env bash
# `tack models [TIER]`: the model each tool uses for a provider-neutral tier, from model-tiers.txt
# overridden by the user's ~/.config/agent-tack/model-tiers.txt.
set -u

repo="$1"
shift
tier="${1:-}"
case "$tier" in
  '' | economical | balanced | strongest) ;;
  *) printf 'tack: unknown tier: %s (economical, balanced, strongest)\n' "$tier" >&2; exit 2 ;;
esac
user_file="${XDG_CONFIG_HOME:-$HOME/.config}/agent-tack/model-tiers.txt"

# Fetch once per invocation, only if a selected Codex family needs it. The catalog is fast
# enough to avoid a persistent cache. Python also bounds the call when timeout is unavailable.
catalog_models() {
  command -v codex >/dev/null 2>&1 || return 0
  command -v python3 >/dev/null 2>&1 || return 0
  python3 -I -c '
import json
import shutil
import subprocess

try:
    command = ["codex", "debug", "models"]
    if shutil.which("timeout"):
        command = ["timeout", "10"] + command
    result = subprocess.run(command, capture_output=True, timeout=10, check=True)
    models = json.loads(result.stdout)["models"]
    candidates = []
    for entry in models:
        slug, priority = entry.get("slug"), entry.get("priority")
        if (entry.get("visibility") == "list" and isinstance(slug, str)
                and slug and not any(c.isspace() for c in slug)
                and type(priority) is int):
            candidates.append((priority, slug))
    for priority, slug in sorted(candidates, key=lambda item: (-item[0], item[1]), reverse=True):
        print(slug)
except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError, AttributeError):
    pass
'
}

# The user's lines come last, so for each tool and tier the last one read wins.
{ cat "$repo/model-tiers.txt"; [ ! -f "$user_file" ] || cat "$user_file"; } | while read -r tool name model fallback _; do
  case "$tool" in '' | '#'*) continue ;; esac
  # A line without a model or with an unknown tier would blank or invent a tier; skip it.
  case "$name" in
    economical | balanced | strongest) ;;
    *) printf 'tack: ignored model-tiers line with unknown tier: %s %s\n' "$tool" "$name" >&2; continue ;;
  esac
  if [ -z "$model" ]; then printf 'tack: ignored model-tiers line without a model: %s %s\n' "$tool" "$name" >&2; continue; fi
  printf '%s %s %s %s\n' "$tool" "$name" "$model" "${fallback:-inherit}"
done | awk -v tier="$tier" '
  { key = $1 " " $2; if (!(key in model)) order[++n] = key; model[key] = $3; fallback[key] = $4 }
  END {
    for (i = 1; i <= n; i++) {
      split(order[i], part, " ")
      if (tier == "" || part[2] == tier) print part[1], part[2], model[order[i]], fallback[order[i]]
    }
  }' | {
  printf '%-10s%-12s%s\n' TOOL TIER MODEL
  catalog_ready=false catalog=''
  while read -r tool name model fallback; do
    case "$model" in
      family:*)
        family="${model#family:}"
        model="$fallback"
        if [ "$tool" = codex ]; then
          if [ "$catalog_ready" = false ]; then
            catalog="$(catalog_models)"
            catalog_ready=true
          fi
          resolved="$(printf '%s\n' "$catalog" | awk -v suffix="-$family" '
            length($0) >= length(suffix) && substr($0, length($0) - length(suffix) + 1) == suffix { print; exit }')"
          [ -z "$resolved" ] || model="$resolved"
        fi
        ;;
    esac
    printf '%-10s%-12s%s\n' "$tool" "$name" "$model"
  done
}
