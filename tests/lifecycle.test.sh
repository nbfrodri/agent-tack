#!/usr/bin/env bash
# Lifecycle operations use only throwaway homes and repositories.
set -uo pipefail
unset XDG_STATE_HOME GIT_CONFIG_GLOBAL
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/harness-lifecycle.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
PASSED=0 FAILED=0
check() { if eval "$2"; then printf '  ✔ %s\n' "$1"; PASSED=$((PASSED + 1)); else printf '  ✘ %s\n' "$1"; FAILED=$((FAILED + 1)); fi; }
run() {
  HOME="$H" XDG_CONFIG_HOME="$H/.config" GIT_CONFIG_NOSYSTEM=1 \
    "$REPO/$1" "${@:2}" > "$WORK/output" 2>&1
}
H="$WORK/preview"
mkdir -p "$H/.claude"
printf '{"theme":"dark"}\n' > "$H/.claude/settings.json"
cp "$H/.claude/settings.json" "$WORK/before"
check 'install dry-run succeeds' 'run install.sh --dry-run'
check 'dry-run describes links, settings, Git and plugins' "grep -q 'would link' '$WORK/output' && grep -q 'would merge' '$WORK/output' && grep -q 'would set core.hooksPath' '$WORK/output' && grep -q 'would ensure plugin' '$WORK/output'"
check 'dry-run preserves HOME' "[ ! -e '$H/.local' ] && [ ! -e '$H/.gitconfig' ] && [ ! -e '$H/.claude/CLAUDE.md' ] && cmp -s '$WORK/before' '$H/.claude/settings.json'"

H="$WORK/owned"
mkdir -p "$H/.claude" "$H/.codex"
printf 'original notes\n' > "$H/.claude/CLAUDE.md"
ln -s "$WORK/original-rules" "$H/.codex/AGENTS.md"
printf '{"theme":"dark","attribution":{"commit":"original"}}\n' > "$H/.claude/settings.json"
check 'install records ownership' 'run install.sh --skip-plugins'
STATE="$H/.local/state/agent-harness/ownership"
check 'private ownership schema exists' "[ \"\$(cat '$STATE/version' 2>/dev/null)\" = 1 ]"
check 'reinstall succeeds' 'run install.sh --skip-plugins'
check 'uninstall preview succeeds' 'run uninstall.sh --dry-run'
check 'uninstall preview preserves managed links' "[ -L '$H/.claude/CLAUDE.md' ]"
check 'uninstall succeeds' 'run uninstall.sh'
check 'original instruction file restored after reinstall' "[ ! -L '$H/.claude/CLAUDE.md' ] && grep -q 'original notes' '$H/.claude/CLAUDE.md'"
check 'displaced original symlink restored' "[ \"\$(readlink '$H/.codex/AGENTS.md')\" = '$WORK/original-rules' ]"
check 'only original settings remain' "python3 -c 'import json,sys; assert json.load(open(sys.argv[1])) == {\"theme\":\"dark\",\"attribution\":{\"commit\":\"original\"}}' '$H/.claude/settings.json'"
check 'owned Git hooks entry removed' "! HOME='$H' XDG_CONFIG_HOME='$H/.config' GIT_CONFIG_NOSYSTEM=1 git config --global --get core.hooksPath"
check 'uninstall does not delete the project' "[ -f '$REPO/install.sh' ]"


H="$WORK/modified"
mkdir -p "$H/.claude"
printf '{"attribution":{"commit":"original"},"theme":"dark"}\n' > "$H/.claude/settings.json"
run install.sh --skip-plugins
python3 - "$H/.claude/settings.json" <<'PYTEST'
import json,sys
p=sys.argv[1]
d=json.load(open(p)); d['theme']='light'; d['newPreference']='keep'
d['attribution']['custom']='keep'
d['hooks']['PreToolUse'][0]['hooks'].append({'type':'command','command':'echo custom'})
json.dump(d,open(p,'w'))
PYTEST
check 'reinstall with user additions succeeds' 'run install.sh --skip-plugins'
rm "$H/.codex/AGENTS.md"
ln -s "$WORK/user-rules" "$H/.codex/AGENTS.md"
check 'uninstall preserves user changes' 'run uninstall.sh'
check 'changed link target survives' "[ \"\$(readlink '$H/.codex/AGENTS.md')\" = '$WORK/user-rules' ]"
check 'unrelated and nested settings edits survive reinstall/uninstall' "python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d[\"theme\"] == \"light\" and d[\"newPreference\"] == \"keep\" and d[\"attribution\"] == {\"commit\":\"original\",\"custom\":\"keep\"}' '$H/.claude/settings.json'"
check 'custom hook remains while unchanged harness command is removed' "grep -q 'echo custom' '$H/.claude/settings.json' && ! grep -q '#harness' '$H/.claude/settings.json'"
H="$WORK/changed-parent"
run install.sh --skip-plugins
mv "$H/.codex" "$H/original-codex"
mkdir "$H/replacement"
ln -s "$REPO/global/AGENTS.md" "$H/replacement/AGENTS.md"
ln -s "$H/replacement" "$H/.codex"
check 'uninstall handles changed parent safely' 'run uninstall.sh'
check 'link under replaced symlink parent survives' "[ -L '$H/replacement/AGENTS.md' ]"
H="$WORK/custom-state"
mkdir -p "$H"
check 'custom XDG state is supported' "XDG_STATE_HOME='$H/private-state' run install.sh --skip-plugins"
check 'custom ownership metadata is private' "python3 -c 'import pathlib,stat,sys; p=pathlib.Path(sys.argv[1]); assert all(stat.S_IMODE(q.stat().st_mode)&0o077 == 0 for q in [p,*p.rglob(\"*\")])' '$H/private-state/agent-harness/ownership'"
check 'custom state can uninstall' "XDG_STATE_HOME='$H/private-state' run uninstall.sh"


H="$WORK/physical-parent"
run install.sh --skip-plugins
mv "$H/.codex" "$H/old-codex"
mkdir "$H/.codex"
ln -s "$REPO/global/AGENTS.md" "$H/.codex/AGENTS.md"
check 'uninstall handles a replaced physical directory' 'run uninstall.sh'
check 'link under replaced physical parent survives' "[ -L '$H/.codex/AGENTS.md' ]"
ln -s "$WORK" "$WORK/alias"
H="$WORK/alias/aliased-home"
mkdir -p "$H"
check 'install accepts stable symlink ancestors outside HOME' 'run install.sh --skip-plugins'
check 'uninstall accepts stable symlink ancestors outside HOME' 'run uninstall.sh'
H="$WORK/integrity"
run install.sh --skip-plugins
STATE="$H/.local/state/agent-harness/ownership"
printf '2\n' > "$STATE/version"
check 'unsupported ownership version refuses all changes' '! run uninstall.sh'
check 'invalid ownership preserves installed links' "[ -L '$H/.claude/CLAUDE.md' ]"
printf '1\n' > "$STATE/version"
printf '%s\n' "$H/.ssh" > "$STATE/entries/1/path"
check 'ownership cannot target arbitrary HOME paths' '! run uninstall.sh'
printf '%s\n' "$H/.claude/CLAUDE.md" > "$STATE/entries/1/path"
chmod 644 "$STATE/home"
check 'readable ownership state is rejected' '! run uninstall.sh'
chmod 600 "$STATE/home"
H="$WORK/git-original"
mkdir -p "$H"
HOME="$H" XDG_CONFIG_HOME="$H/.config" GIT_CONFIG_NOSYSTEM=1 git config --global core.hooksPath "$WORK/missing/git-hooks"
mkdir -p "$H/.agents"
ln -s "$WORK/missing" "$H/.agents/agent-config"
HOME="$H" XDG_CONFIG_HOME="$H/.config" GIT_CONFIG_NOSYSTEM=1 git config --global user.name 'Keep User'
run install.sh --skip-plugins
check 'uninstall restores prior Git hooks path' 'run uninstall.sh'
check 'Git restoration keeps unrelated values' "[ \"\$(HOME='$H' XDG_CONFIG_HOME='$H/.config' GIT_CONFIG_NOSYSTEM=1 git config --global --get core.hooksPath)\" = '$WORK/missing/git-hooks' ] && [ \"\$(HOME='$H' XDG_CONFIG_HOME='$H/.config' GIT_CONFIG_NOSYSTEM=1 git config --global --get user.name)\" = 'Keep User' ]"
H="$WORK/missing-state"
mkdir -p "$H/.claude"
printf 'user notes\n' > "$H/.claude/CLAUDE.md"
check 'uninstall without ownership is a no-op' 'run uninstall.sh'
check 'unmanaged configuration survives' "grep -q 'user notes' '$H/.claude/CLAUDE.md'"


H="$WORK/previous-hook"
mkdir -p "$H/.claude"
printf '{"hooks":{"SessionStart":[{"hooks":[{"type":"command","command":"echo original #harness"}]}]}}\n' > "$H/.claude/settings.json"
run install.sh --skip-plugins
python3 - "$H/.claude/settings.json" <<'PYTEST'
import json,sys
p=sys.argv[1]; d=json.load(open(p))
d['hooks']['SessionStart'][0]['hooks'].append({'type':'command','command':'echo new-user-hook'})
json.dump(d,open(p,'w'))
PYTEST
check 'uninstall restores displaced hook alongside later additions' 'run uninstall.sh'
check 'original and appended hooks both survive' "grep -q 'echo original #harness' '$H/.claude/settings.json' && grep -q 'echo new-user-hook' '$H/.claude/settings.json' && ! grep -q 'session-context.sh' '$H/.claude/settings.json'"
H="$WORK/explicit-git"
mkdir -p "$H/.config/git"
printf '[user]\n\tname = Preserve Me\n' > "$H/.config/git/config"
check 'install honors missing explicit global Git config' "GIT_CONFIG_GLOBAL='$H/explicit-gitconfig' run install.sh --skip-plugins"
check 'uninstall honors explicit global Git config' "GIT_CONFIG_GLOBAL='$H/explicit-gitconfig' run uninstall.sh"
check 'explicit managed Git entry is removed and XDG preserved' "! HOME='$H' XDG_CONFIG_HOME='$H/.config' GIT_CONFIG_GLOBAL='$H/explicit-gitconfig' GIT_CONFIG_NOSYSTEM=1 git config --global --get core.hooksPath && grep -q 'Preserve Me' '$H/.config/git/config'"


H="$WORK/preview-all"
mkdir -p "$H" "$WORK/fake-cli" "$WORK/repo-preview"
cp -R "$REPO/bin" "$REPO/git-hooks" "$REPO/lib" "$REPO/global" "$REPO/skills" "$REPO/agents" "$REPO/claude" "$WORK/repo-preview/"
cp "$REPO/install.sh" "$REPO/uninstall.sh" "$REPO/targets.txt" "$REPO/plugins.txt" "$WORK/repo-preview/"
chmod -x "$WORK/repo-preview/bin/harness" "$WORK/repo-preview/git-hooks/_chain" "$WORK/repo-preview/git-hooks/commit-msg" "$WORK/repo-preview/git-hooks/pre-push"
cat > "$WORK/fake-cli/claude" <<'STUB'
#!/bin/sh
echo invoked >> "$HOME/plugin-calls"
STUB
chmod +x "$WORK/fake-cli/claude"
check 'dry-run with available plugin CLI succeeds' "HOME='$H' XDG_CONFIG_HOME='$H/.config' GIT_CONFIG_NOSYSTEM=1 PATH='$WORK/fake-cli:$PATH' '$WORK/repo-preview/install.sh' --dry-run > '$WORK/preview-output'"
check 'dry-run never invokes plugins or creates HOME state' "[ ! -e '$H/plugin-calls' ] && [ -z \"\$(find '$H' -mindepth 1 -print)\" ]"
check 'dry-run never changes repository executable permissions' "[ ! -x '$WORK/repo-preview/bin/harness' ] && [ ! -x '$WORK/repo-preview/git-hooks/_chain' ] && [ ! -x '$WORK/repo-preview/git-hooks/commit-msg' ] && [ ! -x '$WORK/repo-preview/git-hooks/pre-push' ]"


H="$WORK/changed-targets"
mkdir -p "$H"
check 'install with initial target declarations succeeds' "HOME='$H' XDG_CONFIG_HOME='$H/.config' GIT_CONFIG_NOSYSTEM=1 '$WORK/repo-preview/install.sh' --skip-plugins > '$WORK/changed-targets.log' 2>&1"
python3 - "$WORK/repo-preview/targets.txt" <<'PYTEST'
import pathlib,sys
p=pathlib.Path(sys.argv[1]); p.write_text(p.read_text().replace('~/.claude/CLAUDE.md', '~/.claude/RENAMED.md'))
PYTEST
check 'reinstall accepts historical target destinations' "HOME='$H' XDG_CONFIG_HOME='$H/.config' GIT_CONFIG_NOSYSTEM=1 '$WORK/repo-preview/install.sh' --skip-plugins > '$WORK/changed-targets.log' 2>&1"
check 'renamed target is installed and previous link remains recorded' "[ -L '$H/.claude/RENAMED.md' ] && [ -L '$H/.claude/CLAUDE.md' ]"
python3 - "$WORK/repo-preview/targets.txt" <<'PYTEST'
import pathlib,sys
p=pathlib.Path(sys.argv[1]); p.write_text('\n'.join(line for line in p.read_text().splitlines() if not line.startswith('claude '))+'\n')
PYTEST
check 'uninstall accepts removed target declarations' "HOME='$H' XDG_CONFIG_HOME='$H/.config' GIT_CONFIG_NOSYSTEM=1 '$WORK/repo-preview/uninstall.sh' > '$WORK/changed-targets.log' 2>&1"
check 'both recorded instruction destinations are removed' "[ ! -L '$H/.claude/CLAUDE.md' ] && [ ! -L '$H/.claude/RENAMED.md' ]"
H="$WORK/foreign-missing-hooks"
mkdir -p "$H"
HOME="$H" XDG_CONFIG_HOME="$H/.config" GIT_CONFIG_NOSYSTEM=1 git config --global core.hooksPath "$WORK/foreign/missing/git-hooks"
check 'install tolerates an unowned missing hooks directory' 'run install.sh --skip-plugins'
check 'missing directory basename does not prove harness ownership' "[ \"\$(HOME='$H' XDG_CONFIG_HOME='$H/.config' GIT_CONFIG_NOSYSTEM=1 git config --global --get core.hooksPath)\" = '$WORK/foreign/missing/git-hooks' ]"


H="$WORK/recorded-move"
mkdir -p "$H"
check 'install records Git source for a later checkout move' "HOME='$H' XDG_CONFIG_HOME='$H/.config' GIT_CONFIG_NOSYSTEM=1 '$WORK/repo-preview/install.sh' --skip-plugins > '$WORK/recorded-move.log' 2>&1"
mv "$WORK/repo-preview" "$WORK/repo-moved"
rm "$H/.agents/harness" "$H/.local/bin/harness"
check 'ownership record proves a moved checkout without canonical links' 'run install.sh --skip-plugins'
check 'recorded moved Git hooks migrate to the current checkout' "[ \"\$(HOME='$H' XDG_CONFIG_HOME='$H/.config' GIT_CONFIG_NOSYSTEM=1 git config --global --get core.hooksPath)\" = '$REPO/git-hooks' ]"


for edit in theme added-hook modified-command; do
  H="$WORK/retired-event-$edit"
  mkdir -p "$H/.claude"
  printf '{"theme":"dark","hooks":{"Notification":[{"matcher":"original","hooks":[{"type":"command","command":"echo retired-original #harness","timeout":12}]}]}}\n' > "$H/.claude/settings.json"
  check "install retires original event ($edit)" 'run install.sh --skip-plugins'
  python3 - "$H/.claude/settings.json" "$edit" <<'PYTEST'
import json,sys
p=sys.argv[1]; settings=json.load(open(p))
assert 'Notification' not in settings['hooks']
settings['theme']='light'
if sys.argv[2] == 'added-hook':
    settings['hooks']['Notification']=[{'matcher':'user','hooks':[{'type':'command','command':'echo new-stop-user-hook'}]}]
if sys.argv[2] == 'modified-command':
    settings['hooks']['SessionStart'][0]['hooks'][0]['command']='echo modified-by-user #harness'
json.dump(settings,open(p,'w'))
PYTEST
  check "uninstall restores retired event ($edit)" 'run uninstall.sh'
  check "original hook metadata and theme edit survive ($edit)" "python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d[\"theme\"] == \"light\" and {\"matcher\":\"original\",\"hooks\":[{\"type\":\"command\",\"command\":\"echo retired-original #harness\",\"timeout\":12}]} in d.get(\"hooks\",{}).get(\"Notification\",[])' '$H/.claude/settings.json'"
  if [ "$edit" = added-hook ]; then
    check 'later user Notification hook remains intact' "grep -q 'echo new-stop-user-hook' '$H/.claude/settings.json'"
  elif [ "$edit" = modified-command ]; then
    check 'modified installed command remains intact' "grep -q 'echo modified-by-user #harness' '$H/.claude/settings.json'"
  fi
done

printf '\n%s passed, %s failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
