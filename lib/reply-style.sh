#!/usr/bin/env bash
# Render one reply profile for any startup adapter; legacy and invalid values use brief.
set -uo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
style="${1:-brief}"
guidance() {
  awk -v wanted="$1" '$1 == wanted && $1 !~ /^#/ { $1 = ""; sub(/^[[:space:]]+/, ""); print; exit }' "$root/reply-styles.txt"
}
text="$(guidance "$style")"
if [ -z "$text" ]; then
  style=brief
  text="$(guidance "$style")"
fi
printf 'Reply style: %s. %s A conversational style request takes precedence; this changes presentation, not workflow checks.\n' "$style" "$text"
