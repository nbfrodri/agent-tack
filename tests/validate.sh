#!/usr/bin/env bash
# Validates skills and agents: frontmatter present, name matches, description within limits,
# and every referenced file under references/ exists.
# Usage: tests/validate.sh
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
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
  name="$(field "$file" name)"
  description="$(field "$file" description)"
  [ "$name" = "$expected_name" ] || err "$file: name '$name' should be '$expected_name'"
  [ -n "$description" ] || err "$file: missing description"
  [ "${#description}" -le "$max" ] || err "$file: description is ${#description} chars (max $max): say what it does and when to use it"
  case "$file" in */SKILL.md) SKILLS_TOTAL=$((SKILLS_TOTAL + ${#description})) ;; esac
  case "$name" in
    *[!a-z0-9-]*) err "$file: name must be lowercase letters, digits and hyphens" ;;
  esac
}

echo "Skills"
for skill in "$REPO"/skills/*/; do
  name="$(basename "$skill")"
  file="$skill/SKILL.md"
  if [ ! -f "$file" ]; then
    err "skills/$name: missing SKILL.md"
    continue
  fi
  check_file "$file" "$name" "$SKILL_DESC_MAX"
  while read -r ref; do
    [ -n "$ref" ] || continue
    # A reference can point to this skill's own file or to another skill's (e.g. dev-workflow's)
    [ -f "$skill/$ref" ] || ls "$REPO"/skills/*/"$ref" >/dev/null 2>&1 \
      || err "skills/$name: references missing file $ref"
  done <<EOF
$(grep -o 'references/[a-z0-9-]*\.md' "$file" | sort -u)
EOF
  echo "  ✔ $name"
done

echo "Agents"
for agent in "$REPO"/agents/*.md; do
  [ -e "$agent" ] || continue
  check_file "$agent" "$(basename "$agent" .md)" "$AGENT_DESC_MAX"
  echo "  ✔ $(basename "$agent" .md)"
done

echo "plugins.txt"
while read -r kind id _; do
  case "$kind" in
    ''|'#'*) ;;
    marketplace) ;;
    plugin) case "$id" in *@*) ;; *) err "plugins.txt: '$id' should be plugin@marketplace" ;; esac ;;
    *) err "plugins.txt: unknown line type '$kind'" ;;
  esac
done <"$REPO/plugins.txt"

[ "$SKILLS_TOTAL" -le "$SKILLS_TOTAL_MAX" ] \
  || err "skill descriptions total $SKILLS_TOTAL chars (max $SKILLS_TOTAL_MAX): shorten some"
echo "Skill descriptions: $SKILLS_TOTAL / $SKILLS_TOTAL_MAX chars"

if [ "$ERRORS" -gt 0 ]; then
  echo "$ERRORS error(s)"
  exit 1
fi
echo "All valid"
