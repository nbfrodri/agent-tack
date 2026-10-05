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
# The directory was agent-harness before the rename; use it while it is the only one.
STATE_BASE="${XDG_STATE_HOME:-$HOME/.local/state}"
FORMER_DIR=agent-harness
if [ -d "$STATE_BASE/agent-tack" ] || [ ! -d "$STATE_BASE/$FORMER_DIR" ]; then STATE="$STATE_BASE/agent-tack/ownership"
else STATE="$STATE_BASE/$FORMER_DIR/ownership"; fi
if [ ! -e "$STATE" ] && [ ! -L "$STATE" ]; then
  echo 'No ownership record; nothing removed. Pre-existing configuration is never inferred to be owned.'
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
