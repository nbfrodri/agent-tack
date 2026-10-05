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
expect_failure "a suite run-all.sh does not know" "tests/new.test.sh is not run by tests/run-all.sh" \
  "printf '#!/usr/bin/env bash\n' > tests/new.test.sh"
expect_failure "CI linting with its own command instead of tests/lint.sh" "ci.yml does not call tests/lint.sh" \
  "sed 's#run: tests/lint.sh#run: shellcheck install.sh#' .github/workflows/ci.yml > tmp && mv tmp .github/workflows/ci.yml"
expect_failure "a supported tool missing from the capability map" "docs/editors.md has no row for 'crush'" \
  "grep -v '(\`crush\`' docs/editors.md > tmp && mv tmp docs/editors.md"
expect_failure "CI and the development docs naming different ShellCheck versions" "ShellCheck v0.10.0 in CI" \
  "sed 's/SHELLCHECK_VERSION: v0.11.0/SHELLCHECK_VERSION: v0.10.0/' .github/workflows/ci.yml > tmp && mv tmp .github/workflows/ci.yml"
expect_failure "global instructions naming a skill that may not be installed" "global/AGENTS.md names 'release'" \
  "printf -- '- Releases: \`release\`.\n' >> global/AGENTS.md"
expect_failure "a group line for a skill that no longer exists" "skill-groups.txt: 'gone-skill' has no folder" \
  "printf 'gone-skill       stack\n' >> skill-groups.txt"
expect_failure "docs-writer off the economical tier" "docs-writer must use the economical tier" \
  "sed 's/^model: .*/model: opus/' agents/docs-writer.md > tmp && mv tmp agents/docs-writer.md"
expect_failure "a test chain ending in a command that CI's ShellCheck rejects" "lib/keys.sh:" \
  "printf '[ -n \"\$x\" ] && [ -f \"\$x\" ] || continue\n' >> lib/keys.sh"
expect_failure "a tool with agents but a tier left out" "model-tiers.txt: claude has no 'balanced' tier" \
  "grep -v '^claude *balanced' model-tiers.txt > tmp && mv tmp model-tiers.txt"
expect_failure "an agent naming a model outside the tiers" "agents/planner.md: model 'gpt-9' is not a Claude Code tier model" \
  "sed 's/^model: .*/model: gpt-9/' agents/planner.md > tmp && mv tmp agents/planner.md"
expect_failure "a skill without a group" "skill-groups.txt: skill 'testing' has no group" \
  "grep -v '^testing ' skill-groups.txt > tmp && mv tmp skill-groups.txt"
expect_failure "a skill in an unknown group" "skill-groups.txt: 'frontend' is in unknown group 'ui'" \
  "sed 's/^frontend .*/frontend ui/' skill-groups.txt > tmp && mv tmp skill-groups.txt"
expect_failure "the core workflow made optional" "skill-groups.txt: dev-workflow must be core" \
  "sed 's/^dev-workflow .*/dev-workflow process/' skill-groups.txt > tmp && mv tmp skill-groups.txt"
expect_failure "a test that moves HOME but leaves the real state directory" "tests/leaky.test.sh: exports HOME" \
  "printf 'export HOME=/tmp/x\n' > tests/leaky.test.sh"
expect_failure "a toggle name too long for the tack config table" "features.txt: name" \
  "printf 'a-toggle-name-far-too-long tack.x none bool any hook Too long\n' >> features.txt"
expect_failure "docs-writer inheriting the main model" "docs-writer must use the economical tier" \
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
