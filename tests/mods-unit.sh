#!/usr/bin/env bash
# Runs the mods' unit tests (plugins/*/tests/*.test.ts) with Node, without the Claude Code CLI:
# esbuild bundles each test file with 'claude-code' mapped to tests/mod-shim, then Node runs it.
# Usage: tests/mods-unit.sh [PLUGIN_DIR...]   (default: every folder in plugins/)
# Exit codes: 0 all passed, 1 a test failed or did not build, 2 node or npx is missing.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ESBUILD_VERSION=0.25.10
WORK="$(mktemp -d "${TMPDIR:-/tmp}/tack-mods-unit.XXXXXX")" || exit 1
trap 'rm -rf "$WORK"' EXIT

if ! command -v node >/dev/null 2>&1 || ! command -v npx >/dev/null 2>&1; then
  echo "mods-unit: node and npx are required" >&2
  exit 2
fi

[ "$#" -gt 0 ] || set -- "$REPO"/plugins/*/
failed=0
ran=0
for plugin in "$@"; do
  for test_file in "${plugin%/}"/tests/*.test.ts; do
    [ -f "$test_file" ] || continue
    ran=$((ran + 1))
    echo "${test_file#"$REPO"/}"
    bundle="$WORK/$ran.mjs"
    if ! npx --yes "esbuild@$ESBUILD_VERSION" "$test_file" --bundle --platform=node --format=esm \
        --jsx-factory=h --log-level=warning --alias:claude-code="$REPO/tests/mod-shim/claude-code" \
        --outfile="$bundle"; then
      echo "  ✘ did not build"
      failed=1
      continue
    fi
    # A file that registers no tests exits 0 silently; the shim's summary line proves they ran.
    if ! node "$bundle" > "$WORK/out" 2>&1; then failed=1; fi
    cat "$WORK/out"
    if ! grep -qE '^[0-9]+ passed, [0-9]+ failed$' "$WORK/out"; then
      echo "  ✘ ran no tests"
      failed=1
    fi
  done
done
if [ "$ran" -eq 0 ]; then
  echo "mods-unit: no tests found" >&2
  exit 1
fi
exit "$failed"
