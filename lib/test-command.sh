#!/usr/bin/env bash
# Prints the project's test command and where it came from, as "COMMAND<TAB>SOURCE", or nothing.
# An explicit `tack config check-fast` wins; otherwise the command is detected from the project's
# own files, so the assistant does not have to probe for it.
# Usage: lib/test-command.sh TACK_ROOT PROJECT_ROOT
set -u
tack_root="$1"
root="$2"
cd "$root" 2>/dev/null || exit 0

explicit="$("$tack_root/bin/tack" config check-fast --get)" || exit 2
case "$explicit" in
  none | '') ;;
  *) printf '%s\ttack config check-fast\n' "$explicit"; exit 0 ;;
esac

found() { printf '%s\t%s\n' "$1" "$2"; exit 0; }

# A make target usually wraps the project's canonical command, so it comes first.
for makefile in Makefile makefile GNUmakefile; do
  [ -f "$makefile" ] && grep -qE '^test:' "$makefile" && found 'make test' "$makefile test target"
done
if [ -f package.json ] && grep -qE '"test"[[:space:]]*:' package.json \
  && ! grep -qE '"test"[[:space:]]*:[[:space:]]*"echo \\?"Error: no test specified' package.json; then
  if [ -f pnpm-lock.yaml ]; then found 'pnpm test' 'package.json test script'
  elif [ -f yarn.lock ]; then found 'yarn test' 'package.json test script'
  elif [ -f bun.lockb ] || [ -f bun.lock ]; then found 'bun run test' 'package.json test script'
  else found 'npm test' 'package.json test script'; fi
fi
if [ -f pytest.ini ] || [ -f conftest.py ] || [ -f tests/conftest.py ] \
  || grep -qsE 'pytest' pyproject.toml setup.cfg tox.ini requirements*.txt; then
  # uv runs a pyproject.toml project without a lockfile too; python3 may lack its dev dependencies.
  if [ -f uv.lock ] || { [ -f pyproject.toml ] && command -v uv >/dev/null 2>&1; }; then
    found 'uv run pytest -q' 'pytest configuration'
  else found 'python3 -m pytest -q' 'pytest configuration'; fi
fi
[ -f Cargo.toml ] && found 'cargo test -q' Cargo.toml
[ -f go.mod ] && found 'go test ./...' go.mod
exit 0
