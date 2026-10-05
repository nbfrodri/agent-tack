#!/usr/bin/env bash
# `tack trace [PLAN]`: checks that every requirement the plan numbers (R1, R2…) has a test
# that names it, and warns about tests naming a requirement the plan no longer has.
# PLAN defaults to the newest file in docs/plans/. Exit codes: 0 all covered, 1 a requirement
# lacks a test, 2 usage (not a repository, no plan).
set -u
export LC_ALL=C

root="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "tack: not inside a git repository" >&2; exit 2; }
plan="${1:-}"
# A relative plan path is relative to where the user is, not to the repository root.
case "$plan" in '' | /*) ;; *) plan="$PWD/$plan" ;; esac
cd "$root" || exit 2
if [ -z "$plan" ]; then
  plan="$(find docs/plans -maxdepth 1 -name '*.md' 2>/dev/null | sort | tail -n 1)"
  [ -n "$plan" ] || { echo "tack: no plan in docs/plans/; pass one: tack trace PLAN" >&2; exit 2; }
fi
[ -f "$plan" ] || { echo "tack: plan not found: $plan" >&2; exit 2; }

# A requirement is defined where a line starts with its ID, after an optional bullet, number or
# checkbox: "- R1: text", "**R2**: text", "- [ ] R3: text", "1. R4: text".
definitions="$(sed -nE 's/^[[:space:]]*([-*][[:space:]]*|[0-9]+\.[[:space:]]*)?(\[[ xX]\][[:space:]]*)?[*_]*(R[0-9]+)[*_]*[:.)][[:space:]]*(.*)$/\3|\4/p' "$plan" | awk -F'|' '!seen[$1]++')"
[ -n "$definitions" ] || { echo "tack: $plan numbers no requirements (lines like '- R1: ...')" >&2; exit 2; }

# Test files by the usual conventions of the common ecosystems; other files never count.
tests="$(git ls-files | grep -E '(^|/)(tests?|specs?|__tests__)/|(^|/)test_[^/]*$|[._-](test|spec)\.[A-Za-z]+$|_test\.[A-Za-z]+$')"

# An ID counts when no letter or digit touches it, so test_login_R1 and "R1:" name R1; R10 and
# R1a do not.
ID_BEFORE='(^|[^A-Za-z0-9])'
ID_AFTER='([^A-Za-z0-9]|$)'

files_naming() {
  local id="$1" file found=''
  while IFS= read -r file; do
    if [ -z "$file" ] || [ ! -f "$file" ]; then continue; fi
    if grep -qE -- "$ID_BEFORE$id$ID_AFTER" "$file"; then found="${found:+$found, }$file"; fi
  done <<EOF
$tests
EOF
  printf '%s' "$found"
}

missing=0
echo "Requirements in $plan:"
while IFS='|' read -r id text; do
  found="$(files_naming "$id")"
  if [ -n "$found" ]; then
    printf '%-6s covered  %s\n' "$id" "$found"
  else
    printf '%-6s MISSING  %s\n' "$id" "$text"
    missing=1
  fi
done <<EOF
$definitions
EOF

# Tests that name a requirement the plan does not define, for example one that was dropped.
defined="$(printf '%s\n' "$definitions" | cut -d'|' -f1)"
while IFS= read -r file; do
  if [ -z "$file" ] || [ ! -f "$file" ]; then continue; fi
  grep -oE "${ID_BEFORE}R[0-9]+" "$file" | sed 's/^[^R]*//' | sort -u | while IFS= read -r id; do
    if ! printf '%s\n' "$defined" | grep -qx -- "$id"; then
      echo "Warning: $id is named in $file but not in the plan"
    fi
  done
done <<EOF
$tests
EOF

exit "$missing"
