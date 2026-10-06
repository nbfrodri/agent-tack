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
shellcheck -x install.sh uninstall.sh bin/tack lib/*.sh tests/*.sh evals/run.sh \
  git-hooks/* \
  hooks/claude/*.sh hooks/claude/lib/*.sh hooks/cursor/*.sh || status=1

# ruff: the pinned release through uvx when uv is there, otherwise the installed one (a warning
# when its version differs, since findings can change between releases).
if command -v uvx >/dev/null 2>&1; then
  ruff=(uvx "ruff@$RUFF_VERSION")
elif command -v ruff >/dev/null 2>&1; then
  ruff=(ruff)
  case "$(ruff --version 2>/dev/null)" in
    *" $RUFF_VERSION") ;;
    *) echo "lint: warning: ruff is not $RUFF_VERSION, the version CI pins; findings may differ" >&2 ;;
  esac
else
  echo "lint: ruff is missing; install ruff $RUFF_VERSION or uv" >&2
  exit 2
fi
python_files=()
while IFS= read -r file; do python_files+=("$file"); done < <(git ls-files '*.py')
if [ "${#python_files[@]}" -gt 0 ]; then
  "${ruff[@]}" check --output-format concise "${python_files[@]}" || status=1
fi
# Python that runs on users' machines names its text encoding: Windows defaults to its ANSI code
# page, which garbles the UTF-8 in skills and settings.
"${ruff[@]}" check --output-format concise --preview --select PLW1514 lib hooks || status=1

[ "$status" -ne 0 ] || echo "lint: clean"
exit "$status"
