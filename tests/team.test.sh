#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 "$ROOT/tests/team.test.py"
python3 "$ROOT/tests/integration-verify.test.py"
