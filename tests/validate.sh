#!/usr/bin/env bash
# Validates the repo's content: skill and agent frontmatter, description budget, cross-references
# between skills, agents and docs, components list coverage, plugins.txt and git-hooks/.
# Usage: tests/validate.sh [repo dir]   (defaults to this repo)
set -uo pipefail

REPO="$(cd "${1:-$(dirname "${BASH_SOURCE[0]}")/..}" && pwd)"
ERRORS=0
err() { printf '  ✘ %s\n' "$1"; ERRORS=$((ERRORS + 1)); }

# Prints the value of a frontmatter field (single-line values only).
field() {
  awk -v key="$2" '
    NR == 1 && $0 != "---" { exit }
    NR > 1 && $0 == "---" { exit }
    NR > 1 && index($0, key ": ") == 1 { print substr($0, length(key) + 3); exit }
  ' "$1"
}

# Descriptions of every skill and agent load in every session, so they're kept within a budget
SKILL_DESC_MAX=400
AGENT_DESC_MAX=300
SKILLS_TOTAL_MAX=6000
SKILLS_TOTAL=0

check_file() {
  local file="$1" expected_name="$2" max="$3" name description
  if [ "$(head -n 1 "$file")" != "---" ]; then
    err "$file: missing frontmatter"
    return
  fi
  if ! awk 'NR > 1 && $0 == "---" { found = 1; exit } END { exit !found }' "$file"; then
    err "$file: frontmatter is not closed with ---"
    return
  fi
  name="$(field "$file" name)"
  description="$(field "$file" description)"
  [ "$name" = "$expected_name" ] || err "$file: name '$name' should be '$expected_name'"
  case "$description" in
    '' ) err "$file: missing description" ;;
    '>'* | '|'*) err "$file: description must be on a single line" ;;
  esac
  [ "${#description}" -le "$max" ] || err "$file: description is ${#description} chars (max $max): say what it does and when to use it"
  case "$file" in */SKILL.md) SKILLS_TOTAL=$((SKILLS_TOTAL + ${#description})) ;; esac
  case "$name" in
    *[!a-z0-9-]*) err "$file: name must be lowercase letters, digits and hyphens" ;;
  esac
}

echo "Skills"
for skill in "$REPO"/skills/*/; do
  name="$(basename "$skill")"
  if [ ! -f "$skill/SKILL.md" ]; then
    err "skills/$name: missing SKILL.md"
    continue
  fi
  check_file "$skill/SKILL.md" "$name" "$SKILL_DESC_MAX"
  echo "  ✔ $name"
done

echo "Agents"
for agent in "$REPO"/agents/*.md; do
  [ -e "$agent" ] || continue
  check_file "$agent" "$(basename "$agent" .md)" "$AGENT_DESC_MAX"
  echo "  ✔ $(basename "$agent" .md)"
done
# Every supported tool has a row in the capability map, marked with its targets.txt name.
while read -r tool _; do
  case "$tool" in '' | '#'*) continue ;; esac
  grep -qE "^\| [^|]*\(\`$tool\`" "$REPO/docs/editors.md" || err "docs/editors.md has no row for '$tool' in the capability map"
done < "$REPO/targets.txt"
# One lint command and one test runner, used by AGENTS.md and CI, that cover every suite.
grep -q 'tests/lint.sh' "$REPO/AGENTS.md" || err "AGENTS.md does not call tests/lint.sh"
grep -q 'run: tests/lint.sh' "$REPO/.github/workflows/ci.yml" || err ".github/workflows/ci.yml does not call tests/lint.sh"
suites=" $("$REPO/tests/run-all.sh" --list | tr '\n' ' ') "
for suite in "$REPO"/tests/*.test.sh; do
  case "$suites" in *" $(basename "$suite") "*) ;; *) err "tests/$(basename "$suite") is not run by tests/run-all.sh" ;; esac
done
# CI pins a ShellCheck version; the development docs name the same one for local use.
ci_shellcheck="$(sed -n 's/^ *SHELLCHECK_VERSION: *v\{0,1\}//p' "$REPO/.github/workflows/ci.yml")"
grep -q "ShellCheck ${ci_shellcheck:-missing} " "$REPO/docs/development.md" \
  || err "ShellCheck v${ci_shellcheck:-?} in CI does not match docs/development.md"
# CI and tests/lint.sh pin the same ruff release.
ci_ruff="$(sed -n 's/.*pipx install ruff==\([0-9.]*\).*/\1/p' "$REPO/.github/workflows/ci.yml")"
grep -qx "RUFF_VERSION=${ci_ruff:-missing}" "$REPO/tests/lint.sh" \
  || err "ruff ${ci_ruff:-?} in CI does not match tests/lint.sh"
# The project is tack: the former command, git keys, marker, directories and override variables
# appear only in compatibility code (a line saying legacy, former or renamed), the deprecated
# alias, dated records, tests and the upgrade section of docs/usage.md.
former_keys="$(awk '$2 ~ /^tack\./ { sub(/^tack\./, "", $2); printf "%s|", $2 }' "$REPO/features.txt")"
former_names="harness\.(${former_keys}enabled|mode)([^A-Za-z]|$)|harness (help|status|enable|disable|config|doctor|mode|context|log|init|models|lesson|lessons|trace|trust|trusted)([^a-z-]|$)|agent-harness|HARNESS_ALLOW_|(^|[^A-Za-z/])\.harness([^A-Za-z]|$)|#harness"
if [ -e "$REPO/.git" ]; then tracked=(git -C "$REPO" ls-files); else tracked=(find . -type f -not -path './.git/*'); fi
name_files=()
while IFS= read -r file; do
  file="${file#./}"
  case "$file" in
    tests/* | docs/plans/* | docs/audits/* | docs/handoffs/* | docs/benchmarks/* | docs/archive/* | docs/ai/* | bin/harness | lib/keys.sh | node_modules/* | */node_modules/*) ;;
    *) name_files+=("$file") ;;
  esac
done < <(cd "$REPO" && "${tracked[@]}")
upgrade_notes="$(awk '/^### Upgrading from agent-harness/ { start = NR; next } start && !end && /^#{1,3} / { end = NR - 1 } END { if (start) print start ":" (end ? end : NR) }' "$REPO/docs/usage.md")"
old_names=''
if [ "${#name_files[@]}" -gt 0 ]; then
  old_names="$(cd "$REPO" && grep -nIHE -- "$former_names" "${name_files[@]}" | awk -v notes="$upgrade_notes" '
    BEGIN { split(notes, range, ":") }
    {
      path = $0; sub(/:.*/, "", path); rest = substr($0, length(path) + 2)
      line = rest; sub(/:.*/, "", line); text = tolower(substr(rest, length(line) + 2))
      if (path == "docs/usage.md" && line + 0 >= range[1] + 0 && line + 0 <= range[2] + 0) next
      if (text ~ /(^|[^a-z])(legacy|former|formerly|rename|renamed)([^a-z]|$)/) next
      print
    }')"
fi
if [ -n "$old_names" ]; then
  while IFS= read -r line; do err "${line%%:*}: names the former 'harness' (use tack): ${line#*:}"; done <<EOF_NAMES
$old_names
EOF_NAMES
fi
# docs/plans and docs/handoffs show only open work; finished ones live in docs/archive/.
for kind in plans handoffs; do
  for doc in "$REPO/docs/$kind"/*.md; do
    [ -f "$doc" ] || continue
    case "$(basename "$doc")" in template.md) continue ;; esac
    if grep -qiE '^[-[:space:]]*(\*\*)?Status(\*\*)?:(\*\*)?[[:space:]]*(done|complete|completed|implemented|abandoned|superseded|merged|closed|finished)' "$doc"; then
      err "docs/$kind/$(basename "$doc") is closed; move it to docs/archive/$kind/"
    fi
  done
done
# The ShellCheck on CI's runners reports SC2015 for "[ a ] && [ b ] || command" even where newer
# local versions do not; only exit, return and assignments may follow. Write the rest as if.
sc2015="$(cd "$REPO" && grep -nE '\] && \[[^]]*\] \|\| ' install.sh uninstall.sh bin/tack bin/harness lib/*.sh tests/*.sh evals/run.sh hooks/claude/*.sh hooks/claude/lib/*.sh hooks/cursor/*.sh git-hooks/_chain git-hooks/commit-msg git-hooks/pre-push git-hooks/pre-commit 2>/dev/null \
  | grep -vE '^tests/validate(\.test)?\.sh:|^[^:]*:[0-9]+:[[:space:]]*#|\|\| (exit|return)([ ;]|$)|\|\| [A-Za-z_][A-Za-z0-9_]*=')"
[ -z "$sc2015" ] || err "use if instead of '[ a ] && [ b ] || command' (CI's ShellCheck rejects it):
$sc2015"
# Every tool that gets agents maps all three tiers, and agents name only inherit or a mapped model.
while read -r tool _ _ _ _ agents_dir _; do
  case "$tool" in '' | '#'*) continue ;; esac
  [ "${agents_dir:--}" != - ] || continue
  for tier in economical balanced strongest; do
    grep -qE "^${tool}[[:space:]]+${tier}[[:space:]]+[^[:space:]]" "$REPO/model-tiers.txt" \
      || err "model-tiers.txt: $tool has no '$tier' tier"
  done
done < "$REPO/targets.txt"
for agent in "$REPO"/agents/*.md; do
  agent_model="$(sed -n 's/^model: *//p' "$agent" | head -n 1)"
  [ -z "$agent_model" ] || [ "$agent_model" = inherit ] \
    || grep -qE "^claude[[:space:]]+[a-z]+[[:space:]]+$agent_model$" "$REPO/model-tiers.txt" \
    || err "agents/$(basename "$agent"): model '$agent_model' is not a Claude Code tier model (model-tiers.txt)"
done
# Every skill belongs to a group the installer knows; the core workflow can never be left out.
for skill_dir in "$REPO"/skills/*/; do
  skill_name="$(basename "$skill_dir")"
  skill_group="$(sed -n "s/^${skill_name}[[:space:]][[:space:]]*\([a-z]*\).*/\1/p" "$REPO/skill-groups.txt")"
  case "$skill_group" in
    core | process | stack) ;;
    '') err "skill-groups.txt: skill '$skill_name' has no group" ;;
    *) err "skill-groups.txt: '$skill_name' is in unknown group '$skill_group'" ;;
  esac
done
grep -qE '^dev-workflow[[:space:]]+core$' "$REPO/skill-groups.txt" || err "skill-groups.txt: dev-workflow must be core"
# Tests never touch the real HOME: one that moves HOME must also move or unset XDG_STATE_HOME,
# which many desktops set and which the hooks and tack write to.
for test_file in "$REPO"/tests/*.test.sh; do
  grep -qE '^[[:space:]]*export HOME=' "$test_file" || continue
  grep -qE 'XDG_STATE_HOME=|unset XDG_STATE_HOME' "$test_file" \
    || err "tests/$(basename "$test_file"): exports HOME but not XDG_STATE_HOME, so a user's real state directory would be written"
done
# tack config prints names in a 24-character column; a longer name runs into its value.
while read -r feature _; do
  case "$feature" in '' | '#'*) continue ;; esac
  [ "${#feature}" -le 23 ] || err "features.txt: name '$feature' is over 23 characters and breaks the tack config table"
done < "$REPO/features.txt"
# Large doc updates are delegated to docs-writer to save tokens: it runs on Claude Code's
# economical tier (model-tiers.txt), not the main model.
economical_model="$(sed -n 's/^claude[[:space:]][[:space:]]*economical[[:space:]][[:space:]]*\([^[:space:]]*\).*/\1/p' "$REPO/model-tiers.txt")"
[ "$(sed -n 's/^model: *//p' "$REPO/agents/docs-writer.md")" = "${economical_model:-missing}" ] \
  || err "agents/docs-writer.md: docs-writer must use the economical tier's model (${economical_model:-none} in model-tiers.txt)"
# Global instructions load in every session, so the skills they name must always be installed.
# shellcheck disable=SC2016 # The backticks are Markdown code spans, not command substitution.
for named in $(grep -oE '`[a-z0-9-]+`' "$REPO/global/AGENTS.md" | tr -d '`' | sort -u); do
  [ -d "$REPO/skills/$named" ] || continue
  grep -qE "^${named}[[:space:]]+core$" "$REPO/skill-groups.txt" \
    || err "global/AGENTS.md names '$named', which is not in the core group (skill-groups.txt) and may not be installed"
done
# Every group line names a skill that exists.
while read -r grouped _; do
  case "$grouped" in '' | '#'*) continue ;; esac
  [ -d "$REPO/skills/$grouped" ] || err "skill-groups.txt: '$grouped' has no folder in skills/"
done < "$REPO/skill-groups.txt"

echo "Cross-references and components list"
# Paths like ~/.agents/skills/<skill>/... and ~/.agents/tack/... (or the former ~/.agents/harness/...) are what agents and skills
# read at runtime; references/x.md belongs to the skill it's written in unless another skill is
# named next to it ("`dev-workflow` → `references/x.md`" or "dev-workflow/references/x.md").
if problems="$(python3 - "$REPO" <<'PY'
import re, sys
from pathlib import Path

repo = Path(sys.argv[1])
skills = {p.name for p in (repo / "skills").iterdir() if (p / "SKILL.md").exists()}
agents = {p.stem for p in (repo / "agents").glob("*.md")}
docs = list((repo / "skills").glob("*/SKILL.md")) + list((repo / "skills").glob("*/references/*.md")) \
    + list((repo / "agents").glob("*.md")) + [repo / "global" / "AGENTS.md"]

for doc in docs:
    rel = doc.relative_to(repo)
    own = doc.parts[len(repo.parts) + 1] if rel.parts[0] == "skills" else None
    for n, line in enumerate(doc.read_text().splitlines(), 1):
        for m in re.finditer(r"~/\.agents/skills/([a-z0-9-]+)(/[A-Za-z0-9_./-]*)?", line):
            target = repo / "skills" / m.group(1) / (m.group(2) or "").lstrip("/")
            if not target.exists():
                print(f"{rel}:{n}: {m.group(0)} does not exist")
        for m in re.finditer(r"~/\.agents/(?:tack|harness)(/[A-Za-z0-9_./-]*)?", line):
            if not (repo / (m.group(1) or "").lstrip("/")).exists():
                print(f"{rel}:{n}: {m.group(0)} does not exist")
        for m in re.finditer(r"(?:`([a-z0-9-]+)` → `|([a-z0-9-]+)/)?references/([a-z0-9-]+\.md)", line):
            owner = m.group(1) or m.group(2) or own
            if owner is None or owner not in skills:
                continue
            if not (repo / "skills" / owner / "references" / m.group(3)).exists():
                print(f"{rel}:{n}: {owner}/references/{m.group(3)} does not exist")

components = (repo / "docs/components.md").read_text()
for name in sorted(skills | agents):
    if f"`{name}`" not in components:
        print(f"docs/components.md: `{name}` is not documented")
PY
)"; then
  while IFS= read -r problem; do
    [ -n "$problem" ] && err "$problem"
  done <<EOF
$problems
EOF
  echo "  ✔ checked"
else
  err "cross-reference checker failed"
fi

echo "plugins.txt"
while read -r kind id source _; do
  case "$kind" in
    '' | '#'*) ;;
    marketplace) [ -n "${source:-}" ] || err "plugins.txt: marketplace '$id' needs a source" ;;
    plugin) case "$id" in *@*) ;; *) err "plugins.txt: '$id' should be plugin@marketplace" ;; esac ;;
    *) err "plugins.txt: unknown line type '$kind'" ;;
  esac
done <"$REPO/plugins.txt"

echo "git-hooks/"
for hook in "$REPO"/git-hooks/*; do
  # Windows checkouts without symlink support turn a symlink into a text file git cannot run
  if [ -L "$hook" ]; then
    err "git-hooks/$(basename "$hook"): must be a file, not a symlink (source _chain instead)"
  elif [ ! -x "$hook" ]; then
    err "git-hooks/$(basename "$hook"): not executable"
  fi
done

[ "$SKILLS_TOTAL" -le "$SKILLS_TOTAL_MAX" ] \
  || err "skill descriptions total $SKILLS_TOTAL chars (max $SKILLS_TOTAL_MAX): shorten some"
echo "Skill descriptions: $SKILLS_TOTAL / $SKILLS_TOTAL_MAX chars"

if [ "$ERRORS" -gt 0 ]; then
  echo "$ERRORS error(s)"
  exit 1
fi
echo "All valid"
