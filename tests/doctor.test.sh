#!/usr/bin/env bash
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/harness-doctor-test.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
export HOME="$WORK/home" XDG_CONFIG_HOME="$WORK/home/.config"
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
run_doctor unexpected
check 'unsupported arguments return 2' [ "$RC" -eq 2 ]
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
git config --global core.hooksPath "$WORK/moved/git-hooks"
run_doctor
check 'missing managed Git hooks are an error' [ "$RC" -eq 1 ]
git config --global core.hooksPath "$REPO/git-hooks"
git -C "$WORK/outside" init -q
(cd "$WORK/outside" && "$REPO/bin/harness" enable >/dev/null && "$REPO/bin/harness" trust >/dev/null)
run_doctor
check 'project enabled state is reported' grep -q 'workflow: enabled' "$WORK/report"
check 'project local trust is reported' grep -q 'formatter: trusted' "$WORK/report"
(cd "$WORK/outside" && "$REPO/bin/harness" disable >/dev/null && "$REPO/bin/harness" trust --revoke >/dev/null)
run_doctor
check 'disabled untrusted project is healthy' [ "$RC" -eq 0 ]
check 'disabled state is reported' grep -q 'workflow: disabled' "$WORK/report"
check 'untrusted state is reported' grep -q 'formatter: untrusted' "$WORK/report"
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
