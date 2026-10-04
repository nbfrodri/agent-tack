#!/usr/bin/env bash
# Tests tests/validate.sh: each case copies the repo, breaks one thing and expects a failure
# naming it. Usage: tests/validate.test.sh
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/agent-harness-validate.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
PASSED=0
FAILED=0

# expect_failure <description> <expected message fragment> <shell code that breaks the copy>
expect_failure() {
  local description="$1" fragment="$2" breakage="$3" copy out
  copy="$WORK/case-$((PASSED + FAILED))"
  mkdir -p "$copy"
  (cd "$REPO" && tar cf - --exclude .git .) | (cd "$copy" && tar xf -)
  (cd "$copy" && eval "$breakage")
  if out="$("$REPO/tests/validate.sh" "$copy" 2>&1)"; then
    printf '  ✘ %s (validate.sh passed)\n' "$description"
    FAILED=$((FAILED + 1))
  elif ! printf '%s' "$out" | grep -qF -- "$fragment"; then
    printf '  ✘ %s (no message containing "%s")\n' "$description" "$fragment"
    FAILED=$((FAILED + 1))
  else
    printf '  ✔ %s\n' "$description"
    PASSED=$((PASSED + 1))
  fi
}

echo "Unmodified repo"
if "$REPO/tests/validate.sh" "$REPO" >/dev/null 2>&1; then
  printf '  ✔ passes\n'
  PASSED=$((PASSED + 1))
else
  printf '  ✘ passes\n'
  FAILED=$((FAILED + 1))
fi

echo "Detects"
expect_failure "a checker exception fails validation" "cross-reference checker failed" "rm docs/components.md"
# Expected messages quote paths literally, as written in the docs
# shellcheck disable=SC2088
{
expect_failure "a name that doesn't match its folder" "should be 'testing'" \
  "sed 's/^name: testing\$/name: tests/' skills/testing/SKILL.md > x && mv x skills/testing/SKILL.md"
expect_failure "an unclosed frontmatter" "not closed" \
  "printf -- '---\nname: broken\ndescription: x\n' > skills/testing/SKILL.md && mkdir -p skills/broken && cp skills/testing/SKILL.md skills/broken/"
expect_failure "a description over budget" "max 400" \
  "python3 -c \"import re;p='skills/testing/SKILL.md';s=open(p).read();open(p,'w').write(re.sub(r'^description: .*\$','description: '+'x'*401,s,count=1,flags=re.M))\""
expect_failure "docs-writer inheriting the main model" "docs-writer must pin an economical model" \
  "sed 's/^model: .*/model: inherit/' agents/docs-writer.md > agents/tmp && mv agents/tmp agents/docs-writer.md"
expect_failure "a missing references/ file of the skill itself" "testing/references/python.md" \
  "rm skills/testing/references/python.md"
expect_failure "a missing file referenced from another skill" "dev-workflow/references/tdd.md" \
  "rm skills/dev-workflow/references/tdd.md"
expect_failure "an agent citing a skill path that doesn't exist" "~/.agents/skills/nope/SKILL.md" \
  "echo 'See ~/.agents/skills/nope/SKILL.md' >> agents/planner.md"
expect_failure "a path in the canonical repo link that doesn't exist" "~/.agents/tack/agents/nope.md" \
  "echo 'See ~/.agents/tack/agents/nope.md' >> skills/improve/SKILL.md"
expect_failure "a skill missing from the components list" "docs/components.md: \`brand-new\` is not documented" \
  "mkdir skills/brand-new && printf -- '---\nname: brand-new\ndescription: New skill. Use when testing.\n---\n' > skills/brand-new/SKILL.md"
expect_failure "a marketplace line without source" "needs a source" \
  "echo 'marketplace lonely' >> plugins.txt"
expect_failure "a git hook that isn't executable" "not executable" \
  "printf '#!/bin/sh\n' > git-hooks/pre-foo && chmod -x git-hooks/pre-foo"
}

echo
echo "$PASSED passed, $FAILED failed"
[ "$FAILED" -eq 0 ]
