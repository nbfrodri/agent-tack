#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 "$REPO/tests/native-agents.test.py"
python3 "$REPO/tests/native-hooks.test.py"
