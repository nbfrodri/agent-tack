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
  local file="$1" expected_name="$2" max="$3" description issues
  if ! issues="$(python3 "$REPO/lib/capability_validation.py" file "$file" "$expected_name" "$max" 2>&1)"; then
    err "${issues:-capability validator failed}"
  fi
  description="$(field "$file" description)"
  case "$file" in */SKILL.md) SKILLS_TOTAL=$((SKILLS_TOTAL + ${#description})) ;; esac
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
# Suites covered outside the install job: validation runs in lint, mods unit tests in mods.
while IFS= read -r suite; do
  case "$suite" in validate.sh | validate.test.sh | mods-unit.sh) continue ;; esac
  grep -qF "tests/$suite" "$REPO/.github/workflows/ci.yml" \
    || err "tests/$suite is not run by .github/workflows/ci.yml"
done < <("$REPO/tests/run-all.sh" --list)
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
# alias, dated records, tests and the upgrade section of docs/installation.md.
former_keys="$(awk '$2 ~ /^tack\./ { sub(/^tack\./, "", $2); printf "%s|", $2 }' "$REPO/features.txt")"
former_names="harness\.(${former_keys}enabled|mode)([^A-Za-z]|$)|harness (help|status|enable|disable|config|doctor|mode|context|log|init|models|lesson|lessons|trace|trust|trusted)([^a-z-]|$)|agent-harness|HARNESS_ALLOW_|(^|[^A-Za-z/])\.harness([^A-Za-z]|$)|#harness"
if [ -e "$REPO/.git" ]; then tracked=(git -C "$REPO" ls-files); else tracked=(find . -type f -not -path './.git/*'); fi
name_files=()
while IFS= read -r file; do
  file="${file#./}"
  case "$file" in
    tests/* | docs/plans/* | docs/audits/* | docs/handoffs/* | docs/benchmarks/* | docs/archive/* | docs/ai/* | lib/keys.sh | node_modules/* | */node_modules/*) ;;
    *) name_files+=("$file") ;;
  esac
done < <(cd "$REPO" && "${tracked[@]}")
upgrade_notes="$(awk '/^### Upgrading from agent-harness/ { start = NR; next } start && !end && /^#{1,3} / { end = NR - 1 } END { if (start) print start ":" (end ? end : NR) }' "$REPO/docs/installation.md")"
old_names=''
if [ "${#name_files[@]}" -gt 0 ]; then
  old_names="$(cd "$REPO" && grep -nIHE -- "$former_names" "${name_files[@]}" | awk -v notes="$upgrade_notes" '
    BEGIN { split(notes, range, ":") }
    {
      path = $0; sub(/:.*/, "", path); rest = substr($0, length(path) + 2)
      line = rest; sub(/:.*/, "", line); text = tolower(substr(rest, length(line) + 2))
      if (path == "docs/installation.md" && line + 0 >= range[1] + 0 && line + 0 <= range[2] + 0) next
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
sc2015="$(cd "$REPO" && grep -nE '\] && \[[^]]*\] \|\| ' install.sh uninstall.sh bin/tack lib/*.sh tests/*.sh hooks/claude/*.sh hooks/claude/lib/*.sh hooks/cursor/*.sh git-hooks/_chain git-hooks/commit-msg git-hooks/pre-push git-hooks/pre-commit 2>/dev/null \
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
# Validate repository defaults using the same resolver, without real HOME or machine overrides.
model_home="$(mktemp -d "${TMPDIR:-/tmp}/tack-validate-models.XXXXXX")" || exit 1
tier_models="$(HOME="$model_home" XDG_CONFIG_HOME="$model_home/.config" \
  XDG_STATE_HOME="$model_home/.local/state" GIT_CONFIG_NOSYSTEM=1 \
  GIT_CONFIG_GLOBAL="$model_home/gitconfig" "$REPO/bin/tack" models)"
rm -rf "$model_home"
claude_models="$(printf '%s\n' "$tier_models" | awk '$1 == "claude" { print $3 }')"
for agent in "$REPO"/agents/*.md; do
  agent_model="$(sed -n 's/^model: *//p' "$agent" | head -n 1)"
  [ -z "$agent_model" ] || [ "$agent_model" = inherit ] \
    || printf '%s\n' "$claude_models" | grep -qxF -- "$agent_model" \
    || err "agents/$(basename "$agent"): model '$agent_model' is not a Claude Code tier model (model-tiers.txt)"
done
# Sets are the only way a skill or an agent role gets installed, so each one is in some set, and
# the workflow is in the set that is always active.
for skill_dir in "$REPO"/skills/*/; do
  skill_name="$(basename "$skill_dir")"
  grep -qE "^[a-z0-9-]+[[:space:]]+skill[[:space:]]+${skill_name}([[:space:]]|\$)" "$REPO/sets.txt" \
    || err "sets.txt: skill '$skill_name' is in no set"
done
for agent in "$REPO"/agents/*.md; do
  agent_name="$(basename "$agent" .md)"
  grep -qE "^[a-z0-9-]+[[:space:]]+agent[[:space:]]+${agent_name}([[:space:]]|\$)" "$REPO/sets.txt" \
    || err "sets.txt: agent '$agent_name' is in no set"
done
grep -qE '^core[[:space:]]+skill[[:space:]]+dev-workflow([[:space:]]|$)' "$REPO/sets.txt" || err "sets.txt: dev-workflow must be in the core set"
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
economical_model="$(printf '%s\n' "$tier_models" | awk '$1 == "claude" && $2 == "economical" { print $3 }')"
[ "$(sed -n 's/^model: *//p' "$REPO/agents/docs-writer.md")" = "${economical_model:-missing}" ] \
  || err "agents/docs-writer.md: docs-writer must use the economical tier's model (${economical_model:-none} in model-tiers.txt)"
# Global instructions load in every session, so the skills they name must always be installed.
# shellcheck disable=SC2016 # The backticks are Markdown code spans, not command substitution.
for named in $(grep -oE '`[a-z0-9-]+`' "$REPO/global/AGENTS.md" | tr -d '`' | sort -u); do
  [ -d "$REPO/skills/$named" ] || continue
  grep -qE "^core[[:space:]]+skill[[:space:]]+${named}([[:space:]]|\$)" "$REPO/sets.txt" \
    || err "global/AGENTS.md names '$named', which is not in the core set (sets.txt) and may not be installed"
done
echo "Cross-references and components list"
# Paths like ~/.agents/tack/skills/<skill>/... (or the former ~/.agents/harness/...) are what agents and skills
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
    for n, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1):
        # ~/.agents/skills/<skill> exists only while a set active everywhere lists that skill, so
        # a file that must be readable whatever sets are active is reached through the checkout.
        for m in re.finditer(r"~/\.agents/skills/([a-z0-9-]+)(/[A-Za-z0-9_./-]*)?", line):
            if m.group(1) not in skills:
                print(f"{rel}:{n}: {m.group(0)} does not exist")
            else:
                print(f"{rel}:{n}: use ~/.agents/tack/skills/{m.group(1)} instead of {m.group(0)}: "
                      "the installed path exists only while a set active everywhere lists the skill")
        for m in re.finditer(r"~/\.agents/(?:tack|harness)(/[A-Za-z0-9_./-]*)?", line):
            if not (repo / (m.group(1) or "").lstrip("/")).exists():
                print(f"{rel}:{n}: {m.group(0)} does not exist")
        for m in re.finditer(r"(?:`([a-z0-9-]+)` → `|([a-z0-9-]+)/)?references/([a-z0-9-]+\.md)", line):
            owner = m.group(1) or m.group(2) or own
            if owner is None or owner not in skills:
                continue
            if not (repo / "skills" / owner / "references" / m.group(3)).exists():
                print(f"{rel}:{n}: {owner}/references/{m.group(3)} does not exist")

components = (repo / "docs/components.md").read_text(encoding="utf-8")
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

echo "Documentation links"
if ! python3 "$REPO/tests/docs-links.py" "$REPO"; then err 'documentation link checker failed'; fi

echo "plugins.txt"
while read -r kind id source _; do
  case "$kind" in
    '' | '#'*) ;;
    marketplace) [ -n "${source:-}" ] || err "plugins.txt: marketplace '$id' needs a source" ;;
    plugin) case "$id" in *@*) ;; *) err "plugins.txt: '$id' should be plugin@marketplace" ;; esac ;;
    *) err "plugins.txt: unknown line type '$kind'" ;;
  esac
done <"$REPO/plugins.txt"

echo "Modes"
# lib/modes.sh reads Scope (project makes a mode project-only) and Context (startup detail), and
# `tack mode list` shows When, so a mode that loses one is wrong without any other test noticing.
for mode in "$REPO"/modes/*.md; do
  [ -e "$mode" ] || continue
  name="$(basename "$mode" .md)"
  [ "$(head -n 1 "$mode")" = "# $name" ] || err "modes/$name.md: the first line must be '# $name'"
  for key in When Scope Context; do
    grep -q "^$key: ." "$mode" || err "modes/$name.md: missing a '$key:' line"
  done
  case "$(sed -n 's/^Scope: //p' "$mode" | head -n 1)" in any | project | '') ;; *) err "modes/$name.md: Scope must be any or project" ;; esac
  case "$(sed -n 's/^Context: //p' "$mode" | head -n 1)" in minimal | index | full | '') ;; *) err "modes/$name.md: Context must be minimal, index or full" ;; esac
done

echo "Reply styles"
# lib/reply-style.sh falls back to brief for an unknown profile and prints no guidance when brief
# is missing too, so a lost or mangled profile would go unnoticed.
styles_allowed="$(awk '$1 == "reply-style" { print $4 }' "$REPO/features.txt")"
styles_default="$(awk '$1 == "reply-style" { print $3 }' "$REPO/features.txt")"
styles_seen=""
while read -r style guidance; do
  case "$style" in '' | '#'*) continue ;; esac
  [ -n "$guidance" ] || err "reply-styles.txt: '$style' has no guidance"
  case "|$styles_allowed|" in *"|$style|"*) ;; *) err "reply-styles.txt: '$style' is not a value of the reply-style feature in features.txt" ;; esac
  case " $styles_seen " in *" $style "*) err "reply-styles.txt: '$style' is defined twice" ;; esac
  styles_seen="$styles_seen $style"
done <"$REPO/reply-styles.txt"
case " $styles_seen " in *" ${styles_default:-brief} "*) ;; *) err "reply-styles.txt has no '${styles_default:-brief}' profile, the default reply style and the fallback" ;; esac

echo "sets.txt and sources.txt"
python3 "$REPO/lib/sets.py" "$REPO" check >/dev/null || err 'sets.txt or sources.txt is invalid (tack set check)'
while read -r set kind item _; do
  [ "$kind" = plugin ] || continue
  grep -qE "^marketplace[[:space:]]+${item#*@}[[:space:]]" "$REPO/plugins.txt" \
    || err "sets.txt: set '$set' uses $item, whose marketplace is not in plugins.txt"
done <"$REPO/sets.txt"

echo "git-hooks/"
for hook in "$REPO"/git-hooks/*; do
  # Windows checkouts without symlink support turn a symlink into a text file git cannot run
  if [ -L "$hook" ]; then
    err "git-hooks/$(basename "$hook"): must be a file, not a symlink (source _chain instead)"
  elif [ ! -x "$hook" ]; then
    err "git-hooks/$(basename "$hook"): not executable"
  fi
done

# The guard stays readable: no function longer than 60 lines in the dispatcher or its libraries.
echo "Guard function length"
long_functions="$(
  for guard_file in "$REPO/hooks/claude/guard-bash.sh" "$REPO"/hooks/claude/lib/guard-*.sh; do
    awk -v file="$(basename "$guard_file")" '
      /^[A-Za-z_][A-Za-z0-9_]*\(\) *\{/ {
        if ($0 ~ /\}[ ]*$/) { name = "" } else { name = $1; sub(/\(\).*/, "", name); start = NR }
      }
      /^}$/ { if (name != "" && NR - start + 1 > 60) print file ":" name " (" NR - start + 1 " lines)"; name = "" }
    ' "$guard_file"
  done
)"
[ -z "$long_functions" ] || err "guard functions longer than 60 lines: $(printf '%s' "$long_functions" | tr '\n' ' ')"

# The user picks each subagent's model and effort; guard-agent.sh refuses launches without them.
echo "Model and effort choice"
for chooser in orchestrate cross-delegate; do
  grep -qi 'offer the user' "$REPO/skills/$chooser/SKILL.md" \
    || err "skills/$chooser/SKILL.md: must offer the user a model and effort choice before delegating"
done

[ "$SKILLS_TOTAL" -le "$SKILLS_TOTAL_MAX" ] \
  || err "skill descriptions total $SKILLS_TOTAL chars (max $SKILLS_TOTAL_MAX): shorten some"
echo "Skill descriptions: $SKILLS_TOTAL / $SKILLS_TOTAL_MAX chars"

if [ "$ERRORS" -gt 0 ]; then
  echo "$ERRORS error(s)"
  exit 1
fi
echo "All valid"
