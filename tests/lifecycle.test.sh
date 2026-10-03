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

printf '\n%s passed, %s failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
