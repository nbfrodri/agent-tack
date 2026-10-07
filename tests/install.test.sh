#!/usr/bin/env bash
# Tests install.sh against throwaway HOME directories. Never touches the real HOME.
# Usage: tests/install.test.sh
set -uo pipefail
unset XDG_STATE_HOME GIT_CONFIG_GLOBAL

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/agent-harness-test.XXXXXX")"
trap 'if [ "${KEEP_TEST_WORK:-0}" != 1 ]; then rm -rf "$WORK"; else echo "Test artifacts: $WORK"; fi' EXIT
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

# Counts hook groups tagged #tack for an event
count_ours() {
  python3 -c '
import json, sys
d = json.load(open(sys.argv[1]))
print(sum(1 for g in d.get("hooks", {}).get(sys.argv[2], []) if any("#tack" in h.get("command", "") for h in g.get("hooks", []))))
' "$1" "$2" 2>/dev/null || jq --arg e "$2" '[.hooks[$e][]? | select(any(.hooks[]?; .command | contains("#tack")))] | length' "$1"
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
check "canonical ~/.agents/tack link to the repo" "[ \"\$(readlink '$H/.agents/tack')\" = '$REPO' ]"
check "tack command linked into ~/.local/bin" "[ \"\$(readlink '$H/.local/bin/tack')\" = '$REPO/bin/tack' ]"
check "no links under the former harness name" "[ ! -e '$H/.agents/harness' ] && [ ! -L '$H/.local/bin/harness' ]"
H_FORMER="$WORK/former-links"
mkdir -p "$H_FORMER/.local/bin" "$H_FORMER/.agents"
ln -s "$REPO/bin/harness" "$H_FORMER/.local/bin/harness" && ln -s "$REPO" "$H_FORMER/.agents/harness"
check "links an earlier install made under the former name are removed" "run_install '$H_FORMER' && [ ! -L '$H_FORMER/.local/bin/harness' ] && [ ! -L '$H_FORMER/.agents/harness' ]"
ln -s /somewhere/else "$H_FORMER/.local/bin/harness"
check "a harness link that is not this checkout's is left alone" "run_install '$H_FORMER' && [ \"\$(readlink '$H_FORMER/.local/bin/harness')\" = /somewhere/else ]"
check "settings.json disables AI attribution" "[ \"\$(json_get '$H/.claude/settings.json' attribution.commit)\" = '\"\"' ]"

check "fresh install creates no backups" "! find '$H' -name '*.bak-*' | grep -q ."
check "fresh install counts links instead of listing them" "grep -qE '✔ [0-9]+ new$' '$H.log' && ! grep -q -- ' -> ' '$H.log'"
check "fresh install output stays short" "[ \"\$(wc -l < '$H.log')\" -lt 80 ]"
H_VERBOSE="$WORK/verbose"
check "--verbose lists every link" "run_install '$H_VERBOSE' --verbose && grep -q -- '/.claude/CLAUDE.md -> ' '$H_VERBOSE.log'"

echo "Idempotent"
check "second run exits 0" "run_install '$H'"
check "second run creates no backups" "! find '$H' -name '*.bak-*' | grep -q ."
check "second run changes nothing" "! grep -qE 'backed up|merged|created|removed|->|[0-9]+ new' '$H.log'"

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
      { "matcher": "Bash", "hooks": [{ "type": "command", "command": "bash '/old/path/hooks/claude/guard-bash.sh' #harness" }] }
    ],
    "Notification": [
      { "hooks": [{ "type": "command", "command": "bash '/old/path/hooks/claude/removed.sh' #harness" }] }
    ]
  }
}
JSON
check "exits 0" "run_install '$H'"
S="$H/.claude/settings.json"
check "repo path substituted (no __REPO__ left)" "! grep -q __REPO__ '$S'"
check "guard hook points at this repo" "grep -q \"$REPO/hooks/claude/guard-bash.sh\" '$S'"
C="$H/.codex/hooks.json"
check "codex: hooks are registered in ~/.codex/hooks.json" "[ -f '$C' ] && ! grep -q __REPO__ '$C'"
check "codex: the guard runs in Codex mode" "grep -q \"guard-bash.sh' --codex #tack\" '$C'"
check "codex: session context and stop check are registered" "grep -q 'session-context.sh' '$C' && grep -q 'stop-check.sh' '$C'"
check "your own hooks are kept" "grep -q my-own-hook '$S'"
check "outdated tagged hooks are replaced" "! grep -q /old/path '$S'"
check "events left empty are removed" "! grep -q '\"Notification\"' '$S'"
check "one guard and one budget hook" "[ \"\$(count_ours '$S' PreToolUse)\" = 2 ]"
check "one format and one fast-check hook" "[ \"\$(count_ours '$S' PostToolUse)\" = 2 ]"
check "exactly one session-start hook" "[ \"\$(count_ours '$S' SessionStart)\" = 1 ]"
run_install "$H"
check "no duplicates after re-running" "[ \"\$(count_ours '$S' PreToolUse)\" = 2 ] && [ \"\$(count_ours '$S' PostToolUse)\" = 2 ]"

echo "Settings merge with jq only (no python3)"
if command -v jq >/dev/null 2>&1; then
  BIN="$WORK/bin-jq-only"
  mkdir -p "$BIN"
  for tool in bash env mkdir dirname readlink ln rm mv date cp cmp mktemp sed basename git jq stat chmod cat find grep tr wc head; do
    [ -x "$(command -v "$tool")" ] && ln -s "$(command -v "$tool")" "$BIN/$tool"
  done
  H="$WORK/jq-only"
  mkdir -p "$H/.claude"
  cp "$WORK/hooks/.claude/settings.json" "$H/.claude/settings.json"
  # Re-add a stale tagged hook and a user hook to the copied (already merged) settings
  jq '.hooks.PreToolUse += [{"matcher":"Bash","hooks":[{"type":"command","command":"bash /old/x.sh #harness"}]}] | .theme = "dark"' \
    "$H/.claude/settings.json" >"$H/s.tmp" && mv "$H/s.tmp" "$H/.claude/settings.json"
  check "exits 0 without python3" "HOME='$H' XDG_CONFIG_HOME='$H/.config' GIT_CONFIG_NOSYSTEM=1 PATH='$BIN' '$REPO/install.sh' --skip-plugins >'$H.log' 2>&1"
  check "jq merge keeps your keys" "[ \"\$(jq -r .theme '$H/.claude/settings.json')\" = dark ]"
  check "jq merge keeps your hooks" "grep -q my-own-hook '$H/.claude/settings.json'"
  check "jq merge replaces tagged hooks" "! grep -q /old/x.sh '$H/.claude/settings.json'"
  check "jq merge leaves the guard and budget hooks once" "[ \"\$(count_ours '$H/.claude/settings.json' PreToolUse)\" = 2 ]"
else
  echo "  - skipped (jq not installed)"
fi

echo "Migration from the old agent-config names"
H="$WORK/migration"
mkdir -p "$H/.claude" "$H/.local/bin" "$H/.agents"
OLD="$WORK/old-checkout/agent-config"
mkdir -p "$OLD/bin" "$OLD/git-hooks"
touch "$OLD/bin/agent-config" "$OLD/git-hooks/_chain"
ln -s "$OLD/bin/agent-config" "$H/.local/bin/agent-config"
ln -s "$OLD" "$H/.agents/agent-config"
cat >"$H/.claude/settings.json" <<JSON
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash", "hooks": [{ "type": "command", "command": "bash '$OLD/hooks/claude/guard-bash.sh' #agent-config" }] },
      { "matcher": "Bash", "hooks": [{ "type": "command", "command": "echo my-own-hook" }] }
    ]
  }
}
JSON
git_global "$H" core.hooksPath "$OLD/git-hooks"
check "exits 0" "run_install '$H'"
check "hooks tagged with the old name are replaced" "! grep -q '#agent-config' '$H/.claude/settings.json' && [ \"\$(count_ours '$H/.claude/settings.json' PreToolUse)\" = 2 ]"
check "the user's own hooks survive the migration" "grep -q my-own-hook '$H/.claude/settings.json'"
check "old agent-config command link removed" "[ ! -L '$H/.local/bin/agent-config' ]"
check "old ~/.agents/agent-config link removed" "[ ! -L '$H/.agents/agent-config' ]"
check "core.hooksPath moved from the old checkout" "[ \"\$(git_global '$H' --get core.hooksPath)\" = '$REPO/git-hooks' ]"

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
mkdir -p "$H/.agents"
ln -s "$WORK/old-location/agent-config" "$H/.agents/agent-config"
check "exits 0 when the repo was moved" "run_install '$H'"
check "a hooksPath into a moved (missing) agent-config is updated" "[ \"\$(git_global '$H' --get core.hooksPath)\" = '$REPO/git-hooks' ]"
H="$WORK/git-other-checkout"
OTHER="$WORK/other-checkout"
mkdir -p "$OTHER/git-hooks" "$OTHER/bin" "$H"
touch "$OTHER/git-hooks/_chain" "$OTHER/bin/harness"
git_global "$H" core.hooksPath "$OTHER/git-hooks"
check "exits 0 with another agent-harness checkout" "run_install '$H'"
check "a hooksPath into another agent-harness checkout is updated" "[ \"\$(git_global '$H' --get core.hooksPath)\" = '$REPO/git-hooks' ]"

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
# Compare against the normalised path (macOS TMPDIR ends in '/', so WORK may contain '//')
SPACED_REAL="$(cd "$SPACED" && pwd)"
check "hooks point at the spaced repo path" "grep -qF \"$SPACED_REAL/hooks/claude/guard-bash.sh\" '$H/.claude/settings.json'"

echo "Plugins step (fake claude CLI)"
# A minimal PATH without the real claude, so the real CLI can never run here
MINBIN="$WORK/bin-min"
mkdir -p "$MINBIN"
for tool in bash env mkdir dirname readlink ln rm mv date cp cmp mktemp sed basename git jq python3 stat chmod cat find grep tr wc head; do
  [ -x "$(command -v "$tool")" ] && ln -sf "$(command -v "$tool")" "$MINBIN/$tool"
done
FAKE="$WORK/fake-claude"
mkdir -p "$FAKE"
cat > "$FAKE/claude" <<'STUB'
#!/usr/bin/env bash
echo "$*" >> "$CLAUDE_LOG"
case "$*" in
  "plugin list --json") printf '%s\n' "$FAKE_PLUGINS" ;;
  "plugin marketplace list --json") printf '%s\n' "$FAKE_MARKETPLACES" ;;
  "plugin install "*) cat > /dev/null; [ "${FAKE_FAIL_INSTALL:-0}" = 1 ] && exit 1 ;;
esac
exit 0
STUB
chmod +x "$FAKE/claude"
run_plugins() {
  local home="$1"
  shift
  mkdir -p "$home"
  : > "$home.calls"
  env "$@" HOME="$home" XDG_CONFIG_HOME="$home/.config" GIT_CONFIG_NOSYSTEM=1 PATH="$FAKE:$MINBIN" \
    CLAUDE_LOG="$home.calls" "$REPO/install.sh" --skip-mods >"$home.log" 2>&1
}
called() { grep -qxF -- "$2" "$1.calls"; }

H="$WORK/plugins"
check "exits 0" "run_plugins '$H' FAKE_MARKETPLACES='[]' FAKE_PLUGINS='[{\"id\":\"context7@claude-plugins-official\",\"enabled\":false}]'"
check "adds the missing marketplace" "called '$H' 'plugin marketplace add anthropics/claude-plugins-official'"
check "refreshes the marketplace" "called '$H' 'plugin marketplace update claude-plugins-official'"
check "updates an installed plugin" "called '$H' 'plugin update context7@claude-plugins-official'"
check "re-enables a disabled plugin" "called '$H' 'plugin enable context7@claude-plugins-official'"
check "installs a missing plugin" "called '$H' 'plugin install frontend-design@claude-plugins-official'"
check "every plugin in plugins.txt is processed" "[ \"\$(grep -c '^plugin \\(install\\|update\\)' '$H.calls')\" = \"\$(grep -c '^plugin ' '$REPO/plugins.txt')\" ]"
H="$WORK/plugins-known-marketplace"
run_plugins "$H" FAKE_MARKETPLACES='[{"name":"claude-plugins-official"}]' FAKE_PLUGINS='[]'
check "doesn't re-add a known marketplace" "! grep -q '^plugin marketplace add' '$H.calls'"
H="$WORK/plugins-fail"
check "a failed install makes the run fail" "! run_plugins '$H' FAKE_MARKETPLACES='[]' FAKE_PLUGINS='[]' FAKE_FAIL_INSTALL=1"
check "and says which plugin" "grep -q 'could not install frontend-design' '$H.log'"
H="$WORK/no-claude"
mkdir -p "$H"
check "without claude: exits 0" "HOME='$H' XDG_CONFIG_HOME='$H/.config' GIT_CONFIG_NOSYSTEM=1 PATH='$MINBIN' '$REPO/install.sh' >'$H.log' 2>&1"
check "without claude: warns" "grep -q 'claude CLI not found' '$H.log'"

echo "Other AI tools (targets.txt)"
TOOLS="$WORK/fake-tools"
mkdir -p "$TOOLS"
for tool in gemini copilot cursor-agent; do
  printf '#!/bin/sh\nexit 0\n' > "$TOOLS/$tool"
  chmod +x "$TOOLS/$tool"
done
H="$WORK/tools"
mkdir -p "$H"
check "exits 0 with gemini, copilot and cursor installed" "HOME='$H' XDG_CONFIG_HOME='$H/.config' GIT_CONFIG_NOSYSTEM=1 PATH='$TOOLS:$MINBIN' '$REPO/install.sh' --skip-plugins >'$H.log' 2>&1"
check "gemini: global instructions in ~/.gemini/GEMINI.md" "[ \"\$(readlink '$H/.gemini/GEMINI.md')\" = '$REPO/global/AGENTS.md' ]"
check "copilot: global instructions in ~/.copilot/copilot-instructions.md" "[ \"\$(readlink '$H/.copilot/copilot-instructions.md')\" = '$REPO/global/AGENTS.md' ]"
check "copilot: skills in ~/.copilot/skills" "[ \"\$(find '$H/.copilot/skills' -maxdepth 1 -type l | wc -l | tr -d ' ')\" = '$skill_count' ]"
check "cursor: told how to add the global instructions" "grep -q 'cursor: no file for global instructions' '$H.log'"
cursor_guards() { python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(sum("#tack" in h.get("command","") for h in d.get("hooks",{}).get("beforeShellExecution",[])))' "$1"; }
check "cursor: the command guard is registered in ~/.cursor/hooks.json" "[ \"\$(cursor_guards '$H/.cursor/hooks.json')\" = 1 ] && grep -q 'hooks/cursor/guard.sh' '$H/.cursor/hooks.json'"
python3 -c 'import json,sys; p=sys.argv[1]; d=json.load(open(p)); d["hooks"]["beforeShellExecution"].append({"command":"./my-own-check.sh"}); json.dump(d,open(p,"w"))' "$H/.cursor/hooks.json"
HOME="$H" XDG_CONFIG_HOME="$H/.config" GIT_CONFIG_NOSYSTEM=1 PATH="$TOOLS:$MINBIN" "$REPO/install.sh" --skip-plugins >"$H.log" 2>&1
check "cursor: a reinstall keeps one guard and the user's own hooks" "[ \"\$(cursor_guards '$H/.cursor/hooks.json')\" = 1 ] && grep -q 'my-own-check.sh' '$H/.cursor/hooks.json'"
cursor_record_keeps_targets() {
  local entry
  entry="$(grep -lx "$H/.cursor/hooks.json" "$H"/.local/state/agent-tack/ownership/entries/*/path 2>/dev/null | head -n 1)"
  [ -n "$entry" ] && [ -f "$(dirname "$entry")/targets" ]
}
check "cursor: its settings record keeps the tool list it was installed from" cursor_record_keeps_targets
HOME="$H" XDG_CONFIG_HOME="$H/.config" GIT_CONFIG_NOSYSTEM=1 PATH="$TOOLS:$MINBIN" "$REPO/uninstall.sh" >"$H.uninstall.log" 2>&1
check "cursor: uninstall removes tack's guard and keeps the user's own hooks" "[ \"\$(cursor_guards '$H/.cursor/hooks.json')\" = 0 ] && grep -q 'my-own-check.sh' '$H/.cursor/hooks.json'"
H="$WORK/no-cursor"
mkdir -p "$H"
HOME="$H" XDG_CONFIG_HOME="$H/.config" GIT_CONFIG_NOSYSTEM=1 PATH="$MINBIN" "$REPO/install.sh" --skip-plugins >"$H.log" 2>&1
check "cursor not installed: no Cursor hooks file is created" "[ ! -e '$H/.cursor/hooks.json' ]"
H="$WORK/cursor-no-hooks"
mkdir -p "$H"
HOME="$H" XDG_CONFIG_HOME="$H/.config" GIT_CONFIG_NOSYSTEM=1 PATH="$TOOLS:$MINBIN" "$REPO/install.sh" --skip-plugins --no-hooks >"$H.log" 2>&1
check "cursor with --no-hooks: no empty hooks file is created" "[ ! -e '$H/.cursor/hooks.json' ]"
check "opencode not installed: nothing created for it" "[ ! -e '$H/.config/opencode' ]"
check "crush not installed: ~/.config/AGENTS.md not created" "[ ! -e '$H/.config/AGENTS.md' ]"
check "claude and codex are always configured" "[ -L '$H/.claude/CLAUDE.md' ] && [ -L '$H/.codex/AGENTS.md' ]"
check "every tool gets the shared ~/.agents/skills" "[ \"\$(find '$H/.agents/skills' -maxdepth 1 -type l | wc -l | tr -d ' ')\" = '$skill_count' ]"

echo "VS Code without the Copilot CLI"
VSCODE_TOOLS="$WORK/fake-vscode"
mkdir -p "$VSCODE_TOOLS"
printf '#!/bin/sh\nexit 0\n' > "$VSCODE_TOOLS/code"
chmod +x "$VSCODE_TOOLS/code"
H="$WORK/vscode"
mkdir -p "$H"
check "exits 0 with only VS Code installed" "HOME='$H' XDG_CONFIG_HOME='$H/.config' GIT_CONFIG_NOSYSTEM=1 PATH='$VSCODE_TOOLS:$MINBIN' '$REPO/install.sh' --skip-plugins >'$H.log' 2>&1"
check "vscode: Copilot Chat gets the global instructions" "[ \"\$(readlink '$H/.copilot/copilot-instructions.md')\" = '$REPO/global/AGENTS.md' ]"
check "vscode: Copilot Chat gets the skills" "[ \"\$(find '$H/.copilot/skills' -maxdepth 1 -type l | wc -l | tr -d ' ')\" = '$skill_count' ]"

echo "Rejects unknown options"
check "exits 2" "HOME='$WORK/opt' XDG_CONFIG_HOME='$WORK/opt/.config' GIT_CONFIG_NOSYSTEM=1 '$REPO/install.sh' --nope >/dev/null 2>&1; [ \$? -eq 2 ]"

echo "First install explains the hooks; --no-hooks installs none"
H="$WORK/explain"
run_install "$H"
check "first install lists what each hook does" "grep -q 'Hooks installed' '$H.log' && grep -q 'command guard' '$H.log'"
check "the summary says how to opt out" "grep -q -- '--no-hooks' '$H.log' && grep -q 'disabled-hooks' '$H.log'"
run_install "$H"
check "reinstalls stay quiet about the hooks" "! grep -q 'Hooks installed' '$H.log'"
H="$WORK/no-hooks"
run_install "$H" --no-hooks
check "--no-hooks registers no Claude Code hooks" "[ \"\$(count_ours '$H/.claude/settings.json' PreToolUse)\" = 0 ] && [ \"\$(count_ours '$H/.claude/settings.json' SessionStart)\" = 0 ]"
check "--no-hooks still writes the other Claude Code settings" "[ \"\$(json_get '$H/.claude/settings.json' attribution.commit)\" = '\"\"' ]"
check "--no-hooks registers no Codex hooks" "[ ! -e '$H/.codex/hooks.json' ] || [ \"\$(count_ours '$H/.codex/hooks.json' PreToolUse)\" = 0 ]"
check "--no-hooks leaves git's hooksPath alone" "! git_global '$H' --get core.hooksPath >/dev/null"
check "--no-hooks still installs skills" "[ -e '$H/.agents/skills/dev-workflow' ]"
check "--no-hooks is reported" "grep -q 'skipped (--no-hooks)' '$H.log'"
check "--no-hooks shows no hook summary" "! grep -q 'Hooks installed' '$H.log'"
run_install "$H"
check "the first install that registers hooks explains them, even after --no-hooks" "grep -q 'Hooks installed' '$H.log'"
run_install "$H" --no-hooks
check "--no-hooks over an install removes tack's Claude Code hooks" "[ \"\$(count_ours '$H/.claude/settings.json' PreToolUse)\" = 0 ]"
check "--no-hooks over an install removes tack's Codex hooks too" "[ \"\$(count_ours '$H/.codex/hooks.json' PreToolUse)\" = 0 ]"
check "--no-hooks over an install says how to remove the git hooks" "grep -q 'uninstall.sh' '$H.log' && git_global '$H' --get core.hooksPath >/dev/null"
H="$WORK/broken-first"
mkdir -p "$H/.claude"
echo '{broken' > "$H/.claude/settings.json"
run_install "$H"
check "no hook summary when registering the hooks failed" "! grep -q 'Hooks installed' '$H.log'"

echo "Skill groups (tack config skill-groups)"
H="$WORK/groups"
run_install "$H"
check "by default every skill group is installed" "[ -L '$H/.agents/skills/frontend' ] && [ -L '$H/.agents/skills/improve' ] && [ -L '$H/.agents/skills/dev-workflow' ]"
git_global "$H" tack.skillGroups process
run_install "$H"
check "a deselected group's skills are removed" "[ ! -e '$H/.agents/skills/frontend' ] && [ ! -e '$H/.claude/skills/frontend' ]"
check "selected groups stay" "[ -L '$H/.agents/skills/improve' ]"
check "core skills including onboarding are always installed" "[ -L '$H/.agents/skills/dev-workflow' ] && [ -L '$H/.agents/skills/lessons' ] && [ -L '$H/.agents/skills/new-project' ]"
check "the installer says which groups it installed" "grep -q 'skill groups: core, process' '$H.log'"
H2="$WORK/groups-own"
mkdir -p "$H2/.agents/skills/frontend"
printf 'my own frontend notes\n' > "$H2/.agents/skills/frontend/SKILL.md"
run_install "$H2"
check "a skill of the user's is backed up when tack's takes its name" "[ -L '$H2/.agents/skills/frontend' ]"
git_global "$H2" tack.skillGroups core
run_install "$H2" --dry-run
check "a dry run says the link that replaced the user's skill stays" "grep -q 'would keep $H2/.agents/skills/frontend' '$H2.log' && ! grep -q 'would remove $H2/.agents/skills/frontend' '$H2.log'"
run_install "$H2"
check "the link that replaced the user's skill stays until uninstall" "[ -L '$H2/.agents/skills/frontend' ] && grep -q 'kept $H2/.agents/skills/frontend' '$H2.log'"
check "links that took nothing's place are removed" "[ ! -e '$H2/.claude/skills/frontend' ]"
check "uninstall gives the user's own skill back" "HOME='$H2' XDG_CONFIG_HOME='$H2/.config' GIT_CONFIG_NOSYSTEM=1 '$REPO/uninstall.sh' >'$H2.uninstall.log' 2>&1 && grep -q 'my own frontend notes' '$H2/.agents/skills/frontend/SKILL.md'"
git_global "$H" --unset tack.skillGroups
run_install "$H"
check "selecting a group again installs it again" "[ -L '$H/.agents/skills/frontend' ]"
check "uninstall still restores after groups changed" "HOME='$H' XDG_CONFIG_HOME='$H/.config' GIT_CONFIG_NOSYSTEM=1 '$REPO/uninstall.sh' >'$H.uninstall.log' 2>&1 && [ ! -e '$H/.agents/skills/dev-workflow' ]"

echo "Windows (Git Bash) without symlink permission"
H="$WORK/windows"
WINBIN="$WORK/bin-windows"
mkdir -p "$H" "$WINBIN"
printf '#!/bin/sh\necho MINGW64_NT-10.0-26200\n' > "$WINBIN/uname"
printf '#!/bin/sh\necho "ln: Operation not permitted" >&2\nexit 1\n' > "$WINBIN/ln"
chmod +x "$WINBIN/uname" "$WINBIN/ln"
check "stops before changing anything" "! HOME='$H' XDG_CONFIG_HOME='$H/.config' GIT_CONFIG_NOSYSTEM=1 PATH='$WINBIN:$PATH' '$REPO/install.sh' --skip-plugins >'$H.log' 2>&1 && [ ! -e '$H/.claude' ]"
check "names Developer Mode and WSL2" "grep -q 'Developer Mode' '$H.log' && grep -q 'WSL2' '$H.log'"

echo
echo "$PASSED passed, $FAILED failed"
if [ "$FAILED" -gt 0 ]; then
  echo "Logs: re-run with the failing scenario to inspect output." >&2
  exit 1
fi
