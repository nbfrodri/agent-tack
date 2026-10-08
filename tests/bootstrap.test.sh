#!/usr/bin/env bash
set -eu
REPO="$(cd "$(dirname "$0")/.." && pwd)"
python3 "$REPO/tests/bootstrap.test.py"
