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

# The user's lines come last, so for each tool and tier the last one read wins.
{ cat "$repo/model-tiers.txt"; [ ! -f "$user_file" ] || cat "$user_file"; } | while read -r tool name model _; do
  case "$tool" in '' | '#'*) continue ;; esac
  # A line without a model or with an unknown tier would blank or invent a tier; skip it.
  case "$name" in
    economical | balanced | strongest) ;;
    *) printf 'tack: ignored model-tiers line with unknown tier: %s %s\n' "$tool" "$name" >&2; continue ;;
  esac
  if [ -z "$model" ]; then printf 'tack: ignored model-tiers line without a model: %s %s\n' "$tool" "$name" >&2; continue; fi
  printf '%s %s %s\n' "$tool" "$name" "$model"
done | awk -v tier="$tier" '
  { key = $1 " " $2; if (!(key in model)) order[++n] = key; model[key] = $3 }
  END {
    printf "%-10s%-12s%s\n", "TOOL", "TIER", "MODEL"
    for (i = 1; i <= n; i++) {
      split(order[i], part, " ")
      if (tier == "" || part[2] == tier) printf "%-10s%-12s%s\n", part[1], part[2], model[order[i]]
    }
  }'
