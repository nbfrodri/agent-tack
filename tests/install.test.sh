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
# Fully isolated: git's global config is read from and written to the fake HOME only
run_install() {
  local home="$1"
  shift
  mkdir -p "$home"
  HOME="$home" XDG_CONFIG_HOME="$home/.config" GIT_CONFIG_NOSYSTEM=1 \
    "$REPO/install.sh" --skip-plugins "$@" >"$home.log" 2>&1
}

git_global() {
  HOME="$1" XDG_CONFIG_HOME="$1/.config" GIT_CONFIG_NOSYSTEM=1 git config --global "${@:2}"
}

# Counts hook groups tagged #agent-config for an event
count_ours() {
  python3 -c '
import json, sys
d = json.load(open(sys.argv[1]))
print(sum(1 for g in d.get("hooks", {}).get(sys.argv[2], []) if any("#agent-config" in h.get("command", "") for h in g.get("hooks", []))))
' "$1" "$2" 2>/dev/null || jq --arg e "$2" '[.hooks[$e][]? | select(any(.hooks[]?; .command | contains("#agent-config")))] | length' "$1"
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
check "agent-config command linked into ~/.local/bin" "[ \"\$(readlink '$H/.local/bin/agent-config')\" = '$REPO/bin/agent-config' ]"
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

echo "Claude Code hooks"
H="$WORK/hooks"
mkdir -p "$H/.claude"
cat >"$H/.claude/settings.json" <<'JSON'
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash", "hooks": [{ "type": "command", "command": "echo my-own-hook" }] },
      { "matcher": "Bash", "hooks": [{ "type": "command", "command": "bash '/old/path/hooks/claude/guard-bash.sh' #agent-config" }] }
    ],
    "Stop": [
      { "hooks": [{ "type": "command", "command": "bash '/old/path/hooks/claude/removed.sh' #agent-config" }] }
    ]
  }
}
JSON
check "exits 0" "run_install '$H'"
S="$H/.claude/settings.json"
check "repo path substituted (no __REPO__ left)" "! grep -q __REPO__ '$S'"
check "guard hook points at this repo" "grep -q \"$REPO/hooks/claude/guard-bash.sh\" '$S'"
check "your own hooks are kept" "grep -q my-own-hook '$S'"
check "outdated tagged hooks are replaced" "! grep -q /old/path '$S'"
check "events left empty are removed" "! grep -q '\"Stop\"' '$S'"
check "exactly one guard hook" "[ \"\$(count_ours '$S' PreToolUse)\" = 1 ]"
check "exactly one format hook" "[ \"\$(count_ours '$S' PostToolUse)\" = 1 ]"
check "exactly one session-start hook" "[ \"\$(count_ours '$S' SessionStart)\" = 1 ]"
run_install "$H"
check "no duplicates after re-running" "[ \"\$(count_ours '$S' PreToolUse)\" = 1 ] && [ \"\$(count_ours '$S' PostToolUse)\" = 1 ]"

echo "Settings merge with jq only (no python3)"
if command -v jq >/dev/null 2>&1; then
  BIN="$WORK/bin-jq-only"
  mkdir -p "$BIN"
  for tool in bash env mkdir dirname readlink ln rm mv date cp cmp mktemp sed basename git jq chmod cat find grep tr wc head; do
    [ -x "$(command -v "$tool")" ] && ln -s "$(command -v "$tool")" "$BIN/$tool"
  done
  H="$WORK/jq-only"
  mkdir -p "$H/.claude"
  cp "$WORK/hooks/.claude/settings.json" "$H/.claude/settings.json"
  # Re-add a stale tagged hook and a user hook to the copied (already merged) settings
  jq '.hooks.PreToolUse += [{"matcher":"Bash","hooks":[{"type":"command","command":"bash /old/x.sh #agent-config"}]}] | .theme = "dark"' \
    "$H/.claude/settings.json" >"$H/s.tmp" && mv "$H/s.tmp" "$H/.claude/settings.json"
  check "exits 0 without python3" "HOME='$H' XDG_CONFIG_HOME='$H/.config' GIT_CONFIG_NOSYSTEM=1 PATH='$BIN' '$REPO/install.sh' --skip-plugins >'$H.log' 2>&1"
  check "jq merge keeps your keys" "[ \"\$(jq -r .theme '$H/.claude/settings.json')\" = dark ]"
  check "jq merge keeps your hooks" "grep -q my-own-hook '$H/.claude/settings.json'"
  check "jq merge replaces tagged hooks" "! grep -q /old/x.sh '$H/.claude/settings.json'"
  check "jq merge leaves one guard hook" "[ \"\$(count_ours '$H/.claude/settings.json' PreToolUse)\" = 1 ]"
else
  echo "  - skipped (jq not installed)"
fi

echo "Global git hooks"
H="$WORK/git"
check "exits 0" "run_install '$H'"
check "core.hooksPath points at git-hooks/" "[ \"\$(git_global '$H' --get core.hooksPath)\" = '$REPO/git-hooks' ]"
H="$WORK/git-existing"
mkdir -p "$H"
git_global "$H" core.hooksPath /my/own/hooks
check "exits 0 with your own hooksPath" "run_install '$H'"
check "your own hooksPath is not overridden" "[ \"\$(git_global '$H' --get core.hooksPath)\" = /my/own/hooks ]"
check "and it tells you" "grep -q 'already set to /my/own/hooks' '$H.log'"
H="$WORK/git-moved"
mkdir -p "$H"
git_global "$H" core.hooksPath "$WORK/old-location/agent-config/git-hooks"
check "exits 0 when the repo was moved" "run_install '$H'"
check "a hooksPath into a moved (missing) agent-config is updated" "[ \"\$(git_global '$H' --get core.hooksPath)\" = '$REPO/git-hooks' ]"
H="$WORK/git-other-checkout"
OTHER="$WORK/other-checkout"
mkdir -p "$OTHER/git-hooks" "$OTHER/bin" "$H"
touch "$OTHER/git-hooks/_chain" "$OTHER/bin/agent-config"
git_global "$H" core.hooksPath "$OTHER/git-hooks"
check "exits 0 with another agent-config checkout" "run_install '$H'"
check "a hooksPath into another agent-config checkout is updated" "[ \"\$(git_global '$H' --get core.hooksPath)\" = '$REPO/git-hooks' ]"

echo "Paths with spaces"
H="$WORK/home with space"
check "exits 0 with spaces in HOME" "run_install '$H'"
for dir in .agents/skills .claude/skills .codex/skills; do
  check "all skills linked in ~/$dir with spaces in HOME" "[ \"\$(find '$H/$dir' -maxdepth 1 -type l | wc -l | tr -d ' ')\" = '$skill_count' ]"
done
check "nothing created next to HOME" "[ ! -e '$WORK/home' ]"
SPACED="$WORK/repo copy"
mkdir -p "$SPACED"
(cd "$REPO" && tar cf - --exclude .git .) | (cd "$SPACED" && tar xf -)
H="$WORK/spaced-repo-home"
mkdir -p "$H"
check "installer works from a repo path with spaces" "HOME='$H' XDG_CONFIG_HOME='$H/.config' GIT_CONFIG_NOSYSTEM=1 '$SPACED/install.sh' --skip-plugins >'$H.log' 2>&1"
check "hooks point at the spaced repo path" "grep -q \"$SPACED/hooks/claude/guard-bash.sh\" '$H/.claude/settings.json'"

echo "Rejects unknown options"
check "exits 2" "HOME='$WORK/opt' '$REPO/install.sh' --nope >/dev/null 2>&1; [ \$? -eq 2 ]"

echo
echo "$PASSED passed, $FAILED failed"
if [ "$FAILED" -gt 0 ]; then
  echo "Logs: re-run with the failing scenario to inspect output." >&2
  exit 1
fi
