#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python3 "$ROOT/tests/evals.test.py"
python3 "$ROOT/tests/value.test.py"
python3 "$ROOT/tests/lifecycle-eval.test.py"
python3 "$ROOT/tests/lifecycle-report.test.py"
