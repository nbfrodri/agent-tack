#!/usr/bin/env bash
# Tests the VS Code step of install.sh, uninstall.sh and doctor against throwaway HOME
# directories and fake editor commands. Never touches the real HOME or VS Code settings.
# Usage: tests/vscode.test.sh
set -uo pipefail
unset XDG_STATE_HOME GIT_CONFIG_GLOBAL XDG_CONFIG_HOME

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/agent-harness-vscode-test.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
PASSED=0
FAILED=0

check() {
  if eval "$2"; then printf '  ✔ %s\n' "$1"; PASSED=$((PASSED + 1)); else printf '  ✘ %s\n' "$1"; FAILED=$((FAILED + 1)); fi
}

MINBIN="$WORK/bin-min"
mkdir -p "$MINBIN"
for tool in bash env mkdir dirname readlink ln rm mv date cp cmp mktemp sed basename git jq python3 stat chmod cat find grep tr wc head sort uname; do
  [ -x "$(command -v "$tool")" ] && ln -sf "$(command -v "$tool")" "$MINBIN/$tool"
done
EDITORS="$WORK/bin-editors"
mkdir -p "$EDITORS"
for editor in code code-insiders codium; do
  printf '#!/usr/bin/env bash\nexit 0\n' > "$EDITORS/$editor"
  chmod +x "$EDITORS/$editor"
done
# Pin the platform: the settings path depends on uname, and CI also runs on macOS.
rm -f "$MINBIN/uname"
printf '#!/usr/bin/env bash\necho Linux\n' > "$MINBIN/uname"
chmod +x "$MINBIN/uname"
DARWIN="$WORK/bin-darwin"
mkdir -p "$DARWIN"
printf '#!/usr/bin/env bash\necho Darwin\n' > "$DARWIN/uname"
chmod +x "$DARWIN/uname"

fresh_home() {
  H="$WORK/$1"
  mkdir -p "$H"
  SETTINGS="$H/.config/Code/User/settings.json"
}
run() {
  local path="$1"; shift
  env HOME="$H" XDG_CONFIG_HOME="$H/.config" GIT_CONFIG_NOSYSTEM=1 PATH="$path" "$@" >"$H.log" 2>&1
}
# shellcheck disable=SC2119,SC2120
install() { run "$EDITORS:$MINBIN" "$REPO/install.sh" --skip-plugins "$@"; }
# shellcheck disable=SC2119,SC2120
uninstall() { run "$EDITORS:$MINBIN" "$REPO/uninstall.sh" "$@"; }
doctor() { run "$EDITORS:$MINBIN" bash "$REPO/lib/doctor.sh" "$REPO"; }
git_global() { HOME="$H" XDG_CONFIG_HOME="$H/.config" GIT_CONFIG_NOSYSTEM=1 git config --global "$@"; }
value() { python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get(sys.argv[2], "MISSING"))' "$1" "$2"; }
key_count() { python3 -c 'import json,sys; print(len(json.load(open(sys.argv[1]))))' "$1"; }
owned() { grep -rlxF -- "$SETTINGS" "$H"/.local/state/agent-tack/ownership/entries/*/path >/dev/null 2>&1; }
prepare() { mkdir -p "$(dirname "$SETTINGS")"; printf '%s\n' "$1" > "$SETTINGS"; }

echo "Absent file"
fresh_home absent
check "install exits 0" "install"
check "creates the settings file with the key" "[ \"\$(value '$SETTINGS' chat.useAgentsMdFile)\" = True ]"
check "the file holds only that key" "[ \"\$(key_count '$SETTINGS')\" = 1 ]"
check "records ownership" "owned"
check "second run changes nothing and exits 0" "install && [ \"\$(value '$SETTINGS' chat.useAgentsMdFile)\" = True ]"
check "second run reports it as already set" "grep -q 'already' '$H.log'"

echo "Plain JSON"
fresh_home plain
prepare '{"editor.fontSize": 14, "files.autoSave": "afterDelay"}'
check "install exits 0" "install"
check "adds the key" "[ \"\$(value '$SETTINGS' chat.useAgentsMdFile)\" = True ]"
check "keeps the other keys" "[ \"\$(value '$SETTINGS' editor.fontSize)\" = 14 ] && [ \"\$(value '$SETTINGS' files.autoSave)\" = afterDelay ]"

echo "Existing values"
fresh_home has-true
prepare '{"chat.useAgentsMdFile": true}'
cp "$SETTINGS" "$H.before"
check "true is left untouched" "install && cmp -s '$SETTINGS' '$H.before'"
check "true is not recorded as owned" "! owned"
fresh_home has-false
prepare '{"chat.useAgentsMdFile": false}'
cp "$SETTINGS" "$H.before"
check "false is left untouched" "install && cmp -s '$SETTINGS' '$H.before'"
check "false is not recorded as owned" "! owned"

echo "Settings with comments"
fresh_home jsonc
prepare '{
  // my editor
  "editor.fontSize": 14,
}'
cp "$SETTINGS" "$H.before"
check "install exits 0" "install"
check "the file is untouched" "cmp -s '$SETTINGS' '$H.before'"
check "warns with the manual step" "grep -q 'chat.useAgentsMdFile' '$H.log' && grep -qi 'comments' '$H.log'"
check "records nothing" "! owned"

echo "Dry run"
fresh_home dry
check "exits 0" "install --dry-run"
check "reports the action" "grep -q 'would set chat.useAgentsMdFile' '$H.log'"
check "writes nothing" "[ ! -e '$SETTINGS' ]"

echo "Toggle"
fresh_home toggle-off
git_global harness.vscodeAgentsMd false
check "exits 0" "install"
check "false skips the step" "[ ! -e '$SETTINGS' ] && grep -q 'tack.vscodeAgentsMd' '$H.log'"
fresh_home toggle-on
git_global harness.vscodeAgentsMd true
check "true applies the step, even with --skip-plugins" "install && [ -f '$SETTINGS' ]"

echo "Editors and platforms"
fresh_home none
check "no VS Code on PATH: exits 0" "run '$MINBIN' '$REPO/install.sh' --skip-plugins"
check "no VS Code on PATH: creates nothing" "[ ! -e '$H/.config/Code' ] && [ ! -e '$H/.config/VSCodium' ]"
fresh_home all
check "all editors: exits 0" "install"
check "Insiders settings are written" "[ -f '$H/.config/Code - Insiders/User/settings.json' ]"
check "VSCodium settings are written" "[ -f '$H/.config/VSCodium/User/settings.json' ]"
fresh_home mac
check "macOS paths: exits 0" "run '$DARWIN:$EDITORS:$MINBIN' '$REPO/install.sh' --skip-plugins"
check "macOS writes under Library/Application Support" "[ -f '$H/Library/Application Support/Code/User/settings.json' ] && [ ! -e '$SETTINGS' ]"

echo "Uninstall"
fresh_home un-created
install
check "preview exits 0 and keeps the key" "uninstall --dry-run && [ -f '$SETTINGS' ]"
check "uninstall exits 0" "uninstall"
check "deletes a file it created when nothing else is in it" "[ ! -e '$SETTINGS' ]"
fresh_home un-merged
prepare '{"editor.fontSize": 14}'
install
uninstall
check "removes only the installed key" "[ \"\$(value '$SETTINGS' chat.useAgentsMdFile)\" = MISSING ] && [ \"\$(value '$SETTINGS' editor.fontSize)\" = 14 ]"
fresh_home un-extra
install
printf '{"chat.useAgentsMdFile": true, "editor.fontSize": 14}\n' > "$SETTINGS"
uninstall
check "keeps a created file that gained other settings" "[ -f '$SETTINGS' ] && [ \"\$(value '$SETTINGS' editor.fontSize)\" = 14 ] && [ \"\$(value '$SETTINGS' chat.useAgentsMdFile)\" = MISSING ]"
fresh_home un-changed
install
printf '{"chat.useAgentsMdFile": false}\n' > "$SETTINGS"
uninstall
check "keeps the key when the user changed its value" "[ \"\$(value '$SETTINGS' chat.useAgentsMdFile)\" = False ]"
fresh_home un-preexisting
prepare '{"chat.useAgentsMdFile": true}'
install
uninstall
check "never removes a key it did not add" "[ \"\$(value '$SETTINGS' chat.useAgentsMdFile)\" = True ]"

echo "Doctor"
fresh_home doctor
check "unset: warns" "doctor; grep -q 'WARN VS Code (Code): chat.useAgentsMdFile is not set' '$H.log'"
install
check "set: reports ok" "doctor; grep -q 'OK   VS Code (Code): chat.useAgentsMdFile is true' '$H.log'"
printf '{"chat.useAgentsMdFile": false}\n' > "$SETTINGS"
check "false: warns" "doctor; grep -q 'WARN VS Code (Code): chat.useAgentsMdFile is false' '$H.log'"
printf '{ // c\n}\n' > "$SETTINGS"
check "unparsable: warns" "doctor; grep -q 'WARN VS Code (Code): settings.json is not plain JSON' '$H.log'"
git_global harness.vscodeAgentsMd false
check "toggle off is noted" "doctor; grep -q 'VS Code setting disabled' '$H.log'"

echo
echo "$PASSED passed, $FAILED failed"
[ "$FAILED" -eq 0 ]
