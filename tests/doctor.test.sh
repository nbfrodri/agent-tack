#!/usr/bin/env bash
set -uo pipefail
umask 077
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/harness-doctor-test.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
export HOME="$WORK/home" XDG_CONFIG_HOME="$WORK/home/.config"
export XDG_STATE_HOME="$HOME/.local/state"
export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL="$HOME/.gitconfig"
unset GIT_DIR GIT_WORK_TREE GIT_CONFIG_COUNT
mkdir -p "$HOME" "$WORK/outside" "$WORK/bin"
PASSED=0 FAILED=0
check() {
  local name="$1"
  shift
  if "$@"; then printf '  ✔ %s\n' "$name"; PASSED=$((PASSED + 1))
  else printf '  ✘ %s\n' "$name"; FAILED=$((FAILED + 1)); fi
}
for tool in bash env mkdir dirname readlink ln rm mv date cp cmp mktemp sed basename git jq python3 chmod cat find grep tr wc head; do
  path="$(command -v "$tool" 2>/dev/null || true)"
  [ -z "$path" ] || ln -s "$path" "$WORK/bin/$tool"
done
export PATH="$WORK/bin"
run_doctor() {
  (cd "$WORK/outside" && bash "$REPO/lib/doctor.sh" "$REPO" "$@") >"$WORK/report" 2>&1
  RC=$?
}
run_doctor
check 'missing installation is an error' [ "$RC" -eq 1 ]
"$REPO/install.sh" --skip-plugins >"$WORK/install.log" 2>&1 || exit 1
run_doctor
check 'installed links are healthy outside Git' [ "$RC" -eq 0 ]
check 'optional absent tools are warnings' grep -q "WARN.*claude" "$WORK/report"
check 'outside Git is accepted' grep -q "outside a Git repository" "$WORK/report"
mkdir -p "$XDG_STATE_HOME/agent-tack/budget"
: > "$XDG_STATE_HOME/agent-tack/budget/s1"
: > "$XDG_STATE_HOME/agent-tack/budget/s2"
run_doctor
check 'the per-session state is reported with its file count' grep -q "OK   per-session state: 2 file(s)" "$WORK/report"
git config --global tack.skillGroups process
"$REPO/install.sh" --skip-plugins >"$WORK/install.log" 2>&1
run_doctor
check 'skills of a deselected group are not reported missing' [ "$RC" -eq 0 ]
check 'the installed skill groups are reported' grep -q "OK   skill groups: core, process" "$WORK/report"
git config --global --unset tack.skillGroups
"$REPO/install.sh" --skip-plugins >"$WORK/install.log" 2>&1
rm "$HOME/.agents/harness"
ln -s "$WORK/missing" "$HOME/.agents/harness"
run_doctor
check 'broken canonical link is an error' [ "$RC" -eq 1 ]
ln -sf "$REPO" "$HOME/.agents/harness"
rm "$HOME/.codex/AGENTS.md"
printf 'unmanaged\n' > "$HOME/.codex/AGENTS.md"
run_doctor
check 'plain file cannot masquerade as a managed link' [ "$RC" -eq 1 ]
rm "$HOME/.codex/AGENTS.md"
ln -s "$REPO/global/AGENTS.md" "$HOME/.codex/AGENTS.md"
rm "$HOME/.claude/skills/testing"
run_doctor
check 'missing required skill is an error' [ "$RC" -eq 1 ]
ln -s "$REPO/skills/testing" "$HOME/.claude/skills/testing"
ln -s "$REPO/skills/removed-skill" "$HOME/.agents/skills/removed-skill"
run_doctor
check 'stale managed skill links are errors' [ "$RC" -eq 1 ]
rm "$HOME/.agents/skills/removed-skill"
run_doctor unexpected
check 'unsupported arguments return 2' [ "$RC" -eq 2 ]
printf '#!/bin/sh\nexit 13\n' > "$WORK/bin/gemini"
chmod +x "$WORK/bin/gemini"
run_doctor
check 'new optional CLI does not imply an existing managed installation' [ "$RC" -eq 0 ]
check 'new optional CLI missing configuration is a warning' grep -q 'WARN.*gemini.*not configured' "$WORK/report"
mkdir -p "$HOME/.gemini"
printf 'user rules\n' > "$HOME/.gemini/GEMINI.md"
run_doctor
check 'unmanaged optional instructions do not imply a managed installation' [ "$RC" -eq 0 ]
rm "$HOME/.gemini/GEMINI.md"
rm "$WORK/bin/gemini"
mkdir -p "$HOME/.gemini"
ln -s "$WORK/missing" "$HOME/.gemini/GEMINI.md"
run_doctor
check 'optional configured broken links fail even with absent CLI' [ "$RC" -eq 1 ]
rm "$HOME/.gemini/GEMINI.md"
cp "$HOME/.claude/settings.json" "$WORK/settings-good"
printf '{broken' > "$HOME/.claude/settings.json"
run_doctor
check 'malformed settings are an error' [ "$RC" -eq 1 ]
cp "$WORK/settings-good" "$HOME/.claude/settings.json"
python3 - "$HOME/.claude/settings.json" <<'JSON'
import json,sys
p=sys.argv[1]; d=json.load(open(p)); d['hooks']['PreToolUse'][0]['matcher']='Read'; json.dump(d,open(p,'w'))
JSON
run_doctor
check 'managed hooks require the expected matcher' [ "$RC" -eq 1 ]
cp "$WORK/settings-good" "$HOME/.claude/settings.json"
git config --global core.hooksPath /my/deliberate/hooks
run_doctor
check 'deliberate unrelated hooksPath warns without failing' [ "$RC" -eq 0 ]
check 'unrelated hooks warning is explicit' grep -q 'WARN.*global Git hooks' "$WORK/report"
mkdir -p "$WORK/custom/git-hooks"
printf '# user helper\n' > "$WORK/custom/git-hooks/_chain"
git config --global core.hooksPath "$WORK/custom/git-hooks"
run_doctor
check 'foreign git-hooks directory and _chain do not establish ownership' [ "$RC" -eq 0 ]
check 'foreign git-hooks directory receives an explicit warning' grep -q 'WARN.*global Git hooks' "$WORK/report"
git config --global core.hooksPath "$WORK/moved/git-hooks"
run_doctor
check 'unrecorded missing git-hooks path is an optional warning' [ "$RC" -eq 0 ]
git config --global core.hooksPath "$REPO/git-hooks"
git -C "$WORK/outside" init -q
(cd "$WORK/outside" && "$REPO/bin/tack" enable >/dev/null && "$REPO/bin/tack" trust >/dev/null)
run_doctor
check 'project enabled state is reported' grep -q 'workflow: enabled' "$WORK/report"
check 'project local trust is reported' grep -q 'formatter: trusted' "$WORK/report"
(cd "$WORK/outside" && "$REPO/bin/tack" disable >/dev/null && "$REPO/bin/tack" trust --revoke >/dev/null)
run_doctor
check 'disabled untrusted project is healthy' [ "$RC" -eq 0 ]
check 'disabled state is reported' grep -q 'workflow: disabled' "$WORK/report"
check 'untrusted state is reported' grep -q 'formatter: untrusted' "$WORK/report"
check 'project workflow mode is reported' grep -q 'OK   current project mode: auto (default)' "$WORK/report"
git -C "$WORK/outside" config harness.mode turbo
run_doctor
check 'invalid workflow mode is a warning' [ "$RC" -eq 0 ]
check 'invalid workflow mode warning names the value' grep -q 'WARN current project mode: auto (invalid local value: turbo)' "$WORK/report"
git -C "$WORK/outside" config harness.mode unleash
run_doctor
check 'unleash mode is a visible warning' grep -q 'WARN current project mode: unleash (local); autonomous' "$WORK/report"
check 'unleash on the main branch is flagged' grep -q 'WARN current branch is .* in a project-only mode' "$WORK/report"
git -C "$WORK/outside" config --unset harness.mode
git -C "$WORK/outside" config core.hooksPath /project/deliberate/hooks
run_doctor
check 'local unrelated hooksPath is a warning' [ "$RC" -eq 0 ]
check 'effective hooksPath is checked separately' grep -q 'WARN.*effective Git hooks' "$WORK/report"
git -C "$WORK/outside" config --unset core.hooksPath
if [ -x "$WORK/bin/jq" ]; then
  mv "$WORK/bin/python3" "$WORK/python3"
  run_doctor
  check 'jq alone verifies valid managed settings' [ "$RC" -eq 0 ]
  printf '[1,2]' > "$HOME/.claude/settings.json"
  run_doctor
  check 'jq alone rejects non-object settings' [ "$RC" -eq 1 ]
  cp "$WORK/settings-good" "$HOME/.claude/settings.json"
  mv "$WORK/python3" "$WORK/bin/python3"
fi
mv "$WORK/bin/python3" "$WORK/python3"
if [ -x "$WORK/bin/jq" ]; then mv "$WORK/bin/jq" "$WORK/jq"; fi
run_doctor
check 'missing JSON validators leave explicit optional warning' [ "$RC" -eq 0 ]
check 'unverified settings are reported honestly' grep -q 'settings and managed hooks were not verified' "$WORK/report"
mv "$WORK/python3" "$WORK/bin/python3"
if [ -x "$WORK/jq" ]; then mv "$WORK/jq" "$WORK/bin/jq"; fi
mv "$WORK/bin/git" "$WORK/git"
run_doctor
check 'missing essential Git is an error' [ "$RC" -eq 1 ]
mv "$WORK/git" "$WORK/bin/git"
STATE="$XDG_STATE_HOME/agent-tack/ownership"
rm -rf "$STATE"
mkdir -p "$STATE/entries/1"
printf '1\n' > "$STATE/version"
printf '%s\n' "$REPO" > "$STATE/repo"
printf '%s\n' "$HOME" > "$STATE/home"
printf 'link\n' > "$STATE/entries/1/kind"
printf '%s\n' "$HOME/.gemini/GEMINI.md" > "$STATE/entries/1/path"
printf '%s\n' "$HOME/.gemini" > "$STATE/entries/1/parent"
printf '%s\n' "$REPO/global/AGENTS.md" > "$STATE/entries/1/target"
printf 'absent\n' > "$STATE/entries/1/before_kind"
printf '%s\n' "$REPO" > "$STATE/entries/1/repo"
python3 - "$HOME/.gemini" <<'IDENTITY' > "$STATE/entries/1/parent_identity"
import os,sys
info=os.stat(sys.argv[1]); print(str(info.st_dev)+':'+str(info.st_ino))
IDENTITY
run_doctor
check 'recorded optional target missing is an error even when CLI is absent' [ "$RC" -eq 1 ]
ln -s "$REPO/global/AGENTS.md" "$HOME/.gemini/GEMINI.md"
run_doctor
check 'valid ownership metadata and recorded links are healthy' [ "$RC" -eq 0 ]
mkdir -p "$STATE/entries/2"
printf 'git\n' > "$STATE/entries/2/kind"
printf '%s\n' "$HOME/.gitconfig" > "$STATE/entries/2/path"
printf '%s\n' "$HOME" > "$STATE/entries/2/parent"
printf '%s\n' "$WORK/moved/git-hooks" > "$STATE/entries/2/target"
printf '' > "$STATE/entries/2/before"
printf '%s\n' "$WORK/moved" > "$STATE/entries/2/repo"
python3 - "$HOME" <<'IDENTITY' > "$STATE/entries/2/parent_identity"
import os,sys
info=os.stat(sys.argv[1]); print(str(info.st_dev)+':'+str(info.st_ino))
IDENTITY
git config --global core.hooksPath "$WORK/moved/git-hooks"
run_doctor
check 'recorded managed Git hooksPath missing is an error' [ "$RC" -eq 1 ]
git config --global core.hooksPath "$REPO/git-hooks"
printf '99\n' > "$STATE/version"
run_doctor
check 'unsupported ownership version is an error' [ "$RC" -eq 1 ]
printf '1\n' > "$STATE/version"
printf '%s\n' "$WORK/another-repo" > "$STATE/repo"
run_doctor
check 'ownership from another checkout is an error' [ "$RC" -eq 1 ]
printf '%s\n' "$REPO" > "$STATE/repo"
run_doctor
check 'complete ownership schema remains valid after restored Git configuration' [ "$RC" -eq 0 ]
snapshot() {
  python3 - "$HOME" "$WORK/outside" <<'SNAPSHOT'
import hashlib,os,sys
for root in sys.argv[1:]:
    for parent,dirs,files in os.walk(root):
        for name in sorted(dirs+files):
            path=os.path.join(parent,name)
            if os.path.islink(path): value='link:'+os.readlink(path)
            elif os.path.isfile(path): value=hashlib.sha256(open(path,'rb').read()).hexdigest()
            else: value='dir'
            print(path,oct(os.lstat(path).st_mode),value)
SNAPSHOT
}
snapshot > "$WORK/before"
run_doctor
snapshot > "$WORK/after"
check 'doctor preserves files, links and Git configuration' cmp -s "$WORK/before" "$WORK/after"
printf '\n%s passed, %s failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
