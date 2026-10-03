#!/usr/bin/env bash
# Safely restore unchanged paths recorded by install.sh; preserve user modifications.
# Usage: ./uninstall.sh [--dry-run] [--help]
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    -h|--help) sed -n '2,3p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) printf 'Unknown option: %s (see --help)\n' "$arg" >&2; exit 2 ;;
  esac
done
STATE="${XDG_STATE_HOME:-$HOME/.local/state}/agent-harness/ownership"
if [ ! -e "$STATE" ] && [ ! -L "$STATE" ]; then
  echo 'No ownership record; nothing removed. Install once to record managed changes.'
  exit 0
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Uninstall requires python3 for safe ownership validation and selective settings restoration; nothing changed.' >&2
  exit 1
fi
if [ "$DRY_RUN" -eq 1 ]; then
  exec python3 "$REPO/lib/ownership.py" uninstall "$STATE" "$HOME" --dry-run
fi
exec python3 "$REPO/lib/ownership.py" uninstall "$STATE" "$HOME"
