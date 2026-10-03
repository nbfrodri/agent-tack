#!/usr/bin/env bash
# Tests install.sh against throwaway HOME directories. Never touches the real HOME.
# Usage: tests/install.test.sh
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/agent-config-test.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
PASSED=0
FAILED=0

pass() { printf '  ✔ %s\n' "$1"; PASSED=$((PASSED + 1)); }
fail() { printf '  ✘ %s\n' "$1"; FAILED=$((FAILED + 1)); }
check() { if eval "$2"; then pass "$1"; else fail "$1"; fi; }

# Runs the installer with HOME pointed at a fresh directory; extra args are passed through.
run_install() {
  local home="$1"
  shift
  HOME="$home" "$REPO/install.sh" --skip-plugins "$@" >"$home.log" 2>&1
}

# Reads a JSON value with python3 or jq.
json_get() {
  if command -v python3 >/dev/null 2>&1; then
    python3 -c 'import json,sys; d=json.load(open(sys.argv[1]))
for k in sys.argv[2].split("."): d=d[k]
print(json.dumps(d))' "$1" "$2"
  else
    jq -c ".$2" "$1"
  fi
}

skill_count="$(find "$REPO/skills" -mindepth 2 -maxdepth 2 -name SKILL.md | wc -l | tr -d ' ')"
agent_count="$(find "$REPO/agents" -maxdepth 1 -name '*.md' | wc -l | tr -d ' ')"

echo "Fresh machine"
H="$WORK/fresh"
mkdir -p "$H"
check "exits 0" "run_install '$H'"
check "CLAUDE.md links to global/AGENTS.md" "[ \"\$(readlink '$H/.claude/CLAUDE.md')\" = '$REPO/global/AGENTS.md' ]"
check "Codex AGENTS.md links to global/AGENTS.md" "[ \"\$(readlink '$H/.codex/AGENTS.md')\" = '$REPO/global/AGENTS.md' ]"
for dir in .agents/skills .claude/skills .codex/skills; do
  check "all $skill_count skills linked in ~/$dir" "[ \"\$(find '$H/$dir' -maxdepth 1 -type l | wc -l | tr -d ' ')\" = '$skill_count' ]"
done
check "all $agent_count agents linked" "[ \"\$(find '$H/.claude/agents' -maxdepth 1 -type l | wc -l | tr -d ' ')\" = '$agent_count' ]"
check "settings.json disables AI attribution" "[ \"\$(json_get '$H/.claude/settings.json' attribution.commit)\" = '\"\"' ]"

check "fresh install creates no backups" "! find '$H' -name '*.bak-*' | grep -q ."

echo "Idempotent"
check "second run exits 0" "run_install '$H'"
check "second run creates no backups" "! find '$H' -name '*.bak-*' | grep -q ."
check "second run changes nothing" "! grep -qE 'backed up|merged|created|removed|->' '$H.log'"

echo "Existing files are backed up, never overwritten"
H="$WORK/existing"
mkdir -p "$H/.claude/skills/testing"
echo "my notes" >"$H/.claude/CLAUDE.md"
echo "mine" >"$H/.claude/skills/testing/SKILL.md"
check "exits 0" "run_install '$H'"
check "old CLAUDE.md kept as backup" "grep -q 'my notes' '$H'/.claude/CLAUDE.md.bak-*"
check "old skill folder kept as backup" "grep -q mine '$H'/.claude/skills/testing.bak-*/SKILL.md"
check "CLAUDE.md is now the link" "[ -L '$H/.claude/CLAUDE.md' ]"

echo "Settings are merged, not replaced"
H="$WORK/settings"
mkdir -p "$H/.claude"
echo '{"theme":"dark","env":{"A":"1"},"attribution":{"commit":"AI"}}' >"$H/.claude/settings.json"
check "exits 0" "run_install '$H'"
check "keeps unrelated keys" "[ \"\$(json_get '$H/.claude/settings.json' theme)\" = '\"dark\"' ]"
check "keeps nested unrelated keys" "[ \"\$(json_get '$H/.claude/settings.json' env.A)\" = '\"1\"' ]"
check "overrides attribution" "[ \"\$(json_get '$H/.claude/settings.json' attribution.commit)\" = '\"\"' ]"

echo "Invalid settings.json is left untouched"
H="$WORK/broken"
mkdir -p "$H/.claude"
echo '{broken' >"$H/.claude/settings.json"
check "exits non-zero" "! run_install '$H'"
check "file unchanged" "[ \"\$(cat '$H/.claude/settings.json')\" = '{broken' ]"
check "links still installed" "[ -L '$H/.claude/CLAUDE.md' ]"

echo "Stale links to deleted skills are removed"
H="$WORK/stale"
mkdir -p "$H/.claude/skills"
ln -s "$REPO/skills/deleted-skill" "$H/.claude/skills/deleted-skill"
ln -s /somewhere/else "$H/.claude/skills/foreign"
check "exits 0" "run_install '$H'"
check "stale repo link removed" "[ ! -L '$H/.claude/skills/deleted-skill' ]"
check "links not owned by the repo are kept" "[ -L '$H/.claude/skills/foreign' ]"

echo "Rejects unknown options"
check "exits 2" "HOME='$WORK/opt' '$REPO/install.sh' --nope >/dev/null 2>&1; [ \$? -eq 2 ]"

echo
echo "$PASSED passed, $FAILED failed"
if [ "$FAILED" -gt 0 ]; then
  echo "Logs: re-run with the failing scenario to inspect output." >&2
  exit 1
fi
