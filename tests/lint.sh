#!/usr/bin/env bash
# The one lint command, used by AGENTS.md and CI: ShellCheck on every shell script and ruff on
# every Python file, at the versions CI pins.
# Usage: tests/lint.sh   Exit codes: 0 clean, 1 findings, 2 a linter is missing.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUFF_VERSION=0.14.0
cd "$REPO" || exit 2

status=0
if ! command -v shellcheck >/dev/null 2>&1; then
  echo "lint: shellcheck is missing (CI pins the version in .github/workflows/ci.yml)" >&2
  exit 2
fi
shellcheck -x install.sh uninstall.sh bin/tack bin/harness lib/*.sh tests/*.sh evals/run.sh \
  git-hooks/_chain git-hooks/commit-msg git-hooks/pre-push git-hooks/pre-commit \
  hooks/claude/*.sh hooks/claude/lib/*.sh hooks/cursor/*.sh || status=1

# ruff: the installed one, or the pinned release through uvx.
if command -v ruff >/dev/null 2>&1; then
  ruff=(ruff)
elif command -v uvx >/dev/null 2>&1; then
  ruff=(uvx "ruff@$RUFF_VERSION")
else
  echo "lint: ruff is missing; install ruff $RUFF_VERSION or uv" >&2
  exit 2
fi
python_files=()
while IFS= read -r file; do python_files+=("$file"); done < <(git ls-files '*.py')
"${ruff[@]}" check --output-format concise "${python_files[@]}" || status=1

[ "$status" -ne 0 ] || echo "lint: clean"
exit "$status"
