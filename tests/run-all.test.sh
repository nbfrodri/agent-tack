#!/usr/bin/env bash
# Tests tests/run-all.sh suite selection against a copy with two stand-in suites, so no real suite
# runs. Usage: tests/run-all.test.sh
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/tack-run-all-test.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
PASSED=0
FAILED=0

mkdir -p "$WORK/tests"
awk '/^jobs=/ { print "SUITES=(one.test.sh two.test.sh)" } { print }' "$REPO/tests/run-all.sh" > "$WORK/tests/run-all.sh"
printf '#!/usr/bin/env bash\necho one ran\n' > "$WORK/tests/one.test.sh"
printf '#!/usr/bin/env bash\necho two ran\n' > "$WORK/tests/two.test.sh"
chmod +x "$WORK/tests/"*.sh

# expect <description> <exit code> <output fragment or ""> <fragment that must be absent or ""> <args...>
expect() {
  local description="$1" code="$2" fragment="$3" absent="$4" out rc
  shift 4
  out="$("$WORK/tests/run-all.sh" "$@" 2>&1)"
  rc=$?
  if [ "$rc" -ne "$code" ]; then
    printf '  ✘ %s (exit %s, wanted %s)\n%s\n' "$description" "$rc" "$code" "$out"
    FAILED=$((FAILED + 1))
  elif [ -n "$fragment" ] && ! printf '%s' "$out" | grep -qF -- "$fragment"; then
    printf '  ✘ %s (no output containing "%s")\n%s\n' "$description" "$fragment" "$out"
    FAILED=$((FAILED + 1))
  elif [ -n "$absent" ] && printf '%s' "$out" | grep -qF -- "$absent"; then
    printf '  ✘ %s (output contains "%s")\n%s\n' "$description" "$absent" "$out"
    FAILED=$((FAILED + 1))
  else
    printf '  ✔ %s\n' "$description"
    PASSED=$((PASSED + 1))
  fi
}

echo "Suite selection"
expect "no name runs every suite" 0 "two.test.sh" ""
expect "a name runs that suite alone" 0 "one.test.sh" "two.test.sh" one.test.sh
expect "several names run just those" 0 "two.test.sh" "" two.test.sh one.test.sh
expect "a name can follow -j" 0 "two.test.sh" "one.test.sh" -j 1 two.test.sh
expect "an unknown name exits 2 and names it" 2 "unknown suite nope.test.sh" "one.test.sh" one.test.sh nope.test.sh
expect "a bad option still exits 2" 2 "unknown option --bogus" "" --bogus

echo
echo "$PASSED passed, $FAILED failed"
[ "$FAILED" -eq 0 ]
