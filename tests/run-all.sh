#!/usr/bin/env bash
# Runs every test suite, several at a time, and prints one line per suite plus a summary. Each
# suite already works in its own temp HOME, so they can run side by side.
# Usage: tests/run-all.sh [-j N] [--list]   (N defaults to the number of CPUs, at least 1)
# Exit codes: 0 every suite passed, 1 a suite failed (its log is kept), 2 bad options.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SUITES=(validate.sh validate.test.sh lifecycle.test.sh doctor.test.sh install.test.sh tools.test.sh
hooks.test.sh mods.test.sh vscode.test.sh codex.test.sh cli.test.sh settings.test.sh safety.test.sh
guard.test.sh project-capabilities.test.sh native-agents.test.sh project-setup.test.sh verification.test.sh project-config.test.sh bootstrap.test.sh team.test.sh sets.test.sh pr-policy.test.sh ownership-platform.test.sh smoke.test.sh mods-unit.sh)

jobs="$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 2)"
while [ "$#" -gt 0 ]; do
  case "$1" in
    -j) jobs="${2:-}"; shift ;;
    --list) printf '%s\n' "${SUITES[@]}"; exit 0 ;;
    *) echo "run-all: unknown option $1 (use -j N or --list)" >&2; exit 2 ;;
  esac
  shift
done
case "$jobs" in '' | *[!0-9]* | 0) echo "run-all: -j needs a positive number" >&2; exit 2 ;; esac

LOGS="$(mktemp -d "${TMPDIR:-/tmp}/tack-run-all.XXXXXX")" || exit 1
# Suites share the CPUs here, so the guard's latency test gets the wider budget CI uses.
export TACK_GUARD_BUDGET_MS="${TACK_GUARD_BUDGET_MS:-500}"
start=$(date +%s)

# Batches of N: bash 3.2 has no `wait -n`, so each batch finishes before the next starts.
running=0
for suite in "${SUITES[@]}"; do
  ( "$REPO/tests/$suite" > "$LOGS/$suite.log" 2>&1; echo $? > "$LOGS/$suite.rc" ) &
  running=$((running + 1))
  if [ "$running" -ge "$jobs" ]; then wait; running=0; fi
done
wait

failed=0
for suite in "${SUITES[@]}"; do
  rc="$(cat "$LOGS/$suite.rc" 2>/dev/null || echo 1)"
  if [ "$rc" -eq 0 ]; then
    printf '%-20s %s\n' "$suite" "$(tail -n 1 "$LOGS/$suite.log")"
  else
    failed=1
    printf '%-20s FAILED (exit %s)\n' "$suite" "$rc"
    # Failure markers when the suite printed them, else the end of its output (a crash, set -e).
    if grep -qE '✘|FAIL|ERROR' "$LOGS/$suite.log"; then
      grep -E '✘|FAIL|ERROR' "$LOGS/$suite.log" | head -n 10 | sed 's/^/    /'
    else
      tail -n 20 "$LOGS/$suite.log" | sed 's/^/    /'
    fi
  fi
done
if [ "$failed" -eq 0 ]; then
  rm -rf "$LOGS"
  printf 'all suites passed in %ss\n' "$(( $(date +%s) - start ))"
else
  printf 'some suites failed in %ss; full logs in %s\n' "$(( $(date +%s) - start ))" "$LOGS"
fi
exit "$failed"
