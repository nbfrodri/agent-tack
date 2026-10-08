#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python3 "$ROOT/tests/evidence.test.py"
python3 "$ROOT/tests/adoption.test.py"
python3 "$ROOT/tests/quality.test.py"
