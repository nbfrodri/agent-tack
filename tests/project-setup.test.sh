#!/usr/bin/env bash
set -eu
REPO="$(cd "$(dirname "$0")/.." && pwd)"
python3 "$REPO/tests/project-setup.test.py"
python3 "$REPO/tests/private-notes.test.py"
