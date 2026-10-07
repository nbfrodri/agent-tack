#!/usr/bin/env bash
# `tack enable --scaffold`: create missing, evidence-based project guidance.
set -u

command -v python3 >/dev/null 2>&1 || { echo 'tack: scaffolding needs python3' >&2; exit 1; }
exec python3 "$1/lib/project_setup.py" "$2" --scaffold
