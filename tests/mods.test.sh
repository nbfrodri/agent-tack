#!/usr/bin/env bash
# Tests the mods step of install.sh, uninstall.sh and doctor against throwaway HOME
# directories and a stateful fake claude CLI. Never touches the real HOME or plugins.
# Usage: tests/mods.test.sh
set -uo pipefail
unset XDG_STATE_HOME GIT_CONFIG_GLOBAL

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/agent-harness-mods-test.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
PASSED=0
FAILED=0
MARKET=agent-tack-mods

check() {
  if eval "$2"; then printf '  ✔ %s\n' "$1"; PASSED=$((PASSED + 1)); else printf '  ✘ %s\n' "$1"; FAILED=$((FAILED + 1)); fi
}

MINBIN="$WORK/bin-min"
mkdir -p "$MINBIN"
for tool in bash env mkdir dirname readlink ln rm mv date cp cmp mktemp sed basename git jq python3 stat chmod cat find grep tr wc head sort; do
  [ -x "$(command -v "$tool")" ] && ln -sf "$(command -v "$tool")" "$MINBIN/$tool"
done

FAKE="$WORK/fake-claude"
mkdir -p "$FAKE"
cat > "$FAKE/claude" <<'STUB'
#!/usr/bin/env bash
# Stateful stand-in for the claude CLI: markets and plugins live in $FAKE_STATE.
echo "$*" >> "$FAKE_STATE/calls"
touch "$FAKE_STATE/markets" "$FAKE_STATE/plugins" "$FAKE_STATE/enabled"
json_list() {
  local first=1 line
  printf '['
  while read -r line; do
    [ -n "$line" ] || continue
    [ "$first" = 1 ] || printf ','
    first=0
    printf '%s' "$(printf "$2" "$line")"
  done < "$1"
  printf ']\n'
}
case "$*" in
  "plugin list --json") json_list "$FAKE_STATE/plugins" '{"id":"%s","enabled":true}' ;;
  "plugin marketplace list --json")
    # The local marketplace reports the directory it was added from, like the real CLI.
    path="$(cat "$FAKE_STATE/market-path" 2>/dev/null)"
    json_list "$FAKE_STATE/markets" '{"name":"%s"}' | sed "s#{\"name\":\"agent-tack-mods\"}#{\"name\":\"agent-tack-mods\",\"source\":\"directory\",\"path\":\"$path\"}#" ;;
  "plugin marketplace add "*/plugins) echo agent-tack-mods >> "$FAKE_STATE/markets"; printf '%s\n' "$4" > "$FAKE_STATE/market-path" ;;
  "plugin marketplace add "*) echo claude-plugins-official >> "$FAKE_STATE/markets" ;;
  "plugin marketplace remove "*) grep -vxF "${4}" "$FAKE_STATE/markets" > "$FAKE_STATE/markets.new"; mv "$FAKE_STATE/markets.new" "$FAKE_STATE/markets" ;;
  "plugin install "*)
    [ "${FAKE_FAIL_INSTALL:-}" != "" ] && [[ "$3" == "$FAKE_FAIL_INSTALL"* ]] && exit 1
    echo "$3" >> "$FAKE_STATE/plugins" ;;
  "plugin uninstall "*) grep -vxF "$3" "$FAKE_STATE/plugins" > "$FAKE_STATE/plugins.new"; mv "$FAKE_STATE/plugins.new" "$FAKE_STATE/plugins" ;;
esac
exit 0
STUB
chmod +x "$FAKE/claude"

# fresh_home NAME: creates an isolated HOME and a fresh fake CLI state; sets H and STATE.
fresh_home() {
  H="$WORK/$1"
  STATE="$H.state"
  mkdir -p "$H" "$STATE"
}
run_with_claude() {
  env HOME="$H" XDG_CONFIG_HOME="$H/.config" GIT_CONFIG_NOSYSTEM=1 PATH="$FAKE:$MINBIN" FAKE_STATE="$STATE" "$@" \
    >"$H.log" 2>&1
}
# shellcheck disable=SC2119,SC2120
install() { run_with_claude "$REPO/install.sh" "$@"; }
# shellcheck disable=SC2119,SC2120
uninstall() { run_with_claude "$REPO/uninstall.sh" "$@"; }
doctor() { run_with_claude bash "$REPO/lib/doctor.sh" "$REPO"; }
called() { grep -qxF -- "$1" "$STATE/calls"; }
installed() { grep -qxF -- "$1" "$STATE/plugins"; }
git_global() { HOME="$H" XDG_CONFIG_HOME="$H/.config" GIT_CONFIG_NOSYSTEM=1 git config --global "$@"; }
mod_names="$(for d in "$REPO"/plugins/*/; do basename "$d"; done | tr '\n' ' ')"

echo "Shipped mods"
check "both mods ship with an author" "[ \"\$(grep -l '\"author\"' '$REPO'/plugins/*/.claude-plugin/plugin.json | wc -l | tr -d ' ')\" = 2 ]"
check "local marketplace lists every mod folder" "for m in $mod_names; do grep -q \"\\\"./\$m\\\"\" '$REPO/plugins/.claude-plugin/marketplace.json' || exit 1; done"

echo "Default install"
fresh_home default
check "exits 0" "install"
check "adds the local marketplace from the repo" "called 'plugin marketplace add $REPO/plugins'"
check "installs usage-band" "installed usage-band@$MARKET"
check "installs agent-activity" "installed agent-activity@$MARKET"
check "records the marketplace and each mod as owned" "[ \"\$(grep -l -x 'mod.*' '$H'/.local/state/agent-tack/ownership/entries/*/kind | wc -l | tr -d ' ')\" = 3 ]"
: > "$STATE/calls"
check "second run exits 0" "install"
check "second run does not re-add or re-install" "! grep -q '^plugin marketplace add $REPO/plugins' '$STATE/calls' && ! grep -q '^plugin install .*@$MARKET' '$STATE/calls'"
check "second run updates the mods" "called 'plugin update usage-band@$MARKET'"

echo "Opt-outs"
fresh_home skip-flag
check "--skip-mods exits 0" "install --skip-mods"
check "--skip-mods installs no mod" "! grep -q '$MARKET' '$STATE/calls' && ! installed usage-band@$MARKET"
check "--skip-mods still installs plugins.txt plugins" "installed context7@claude-plugins-official"
check "--skip-mods says so" "grep -q 'skipped (--skip-mods)' '$H.log'"
fresh_home skip-config
git_global harness.mods false
check "harness.mods false exits 0" "install"
check "harness.mods false installs no mod" "! grep -q '$MARKET' '$STATE/calls'"
check "harness.mods false says so" "grep -q 'harness.mods' '$H.log'"
fresh_home config-true
git_global harness.mods true
check "harness.mods true installs the mods" "install && installed usage-band@$MARKET"
fresh_home skip-plugins
check "--skip-plugins exits 0" "install --skip-plugins"
check "--skip-plugins also skips the mods" "[ ! -s '$STATE/calls' ]"
fresh_home no-claude
check "without claude: exits 0" "env HOME='$H' XDG_CONFIG_HOME='$H/.config' GIT_CONFIG_NOSYSTEM=1 PATH='$MINBIN' '$REPO/install.sh' >'$H.log' 2>&1"
check "without claude: warns about the mods" "grep -q 'claude CLI not found' '$H.log'"

echo "Dry run"
fresh_home dry
check "exits 0" "install --dry-run"
check "reports the mod actions" "grep -q 'would ensure mod usage-band' '$H.log' && grep -q 'would ensure mod agent-activity' '$H.log'"
check "calls nothing" "[ ! -s '$STATE/calls' ]"
check "records no ownership" "[ ! -e '$H/.local/state/agent-tack/ownership' ]"

echo "Failures"
fresh_home failing
check "a failed mod install makes the run fail" "! run_with_claude env FAKE_FAIL_INSTALL=agent-activity '$REPO/install.sh'"
check "and names the mod" "grep -q 'could not install mod agent-activity' '$H.log'"
check "the other mod is still installed" "installed usage-band@$MARKET"
check "no ownership is recorded for the failed mod" "! grep -rq 'agent-activity@' '$H/.local/state/agent-tack/ownership/entries'"

echo "Uninstall"
fresh_home uninstall
install
: > "$STATE/calls"
check "preview exits 0" "uninstall --dry-run"
check "preview changes nothing" "installed usage-band@$MARKET && ! grep -q 'plugin uninstall' '$STATE/calls'"
check "uninstall exits 0" "uninstall"
check "removes the mods it installed" "! installed usage-band@$MARKET && ! installed agent-activity@$MARKET"
check "removes the marketplace it added" "! grep -qxF $MARKET '$STATE/markets'"
check "keeps the plugins.txt plugins" "installed context7@claude-plugins-official"

fresh_home preexisting
echo "usage-band@$MARKET" > "$STATE/plugins"
echo "$MARKET" > "$STATE/markets"
install
check "pre-existing mod is updated, not reinstalled" "called 'plugin update usage-band@$MARKET' && ! called 'plugin install usage-band@$MARKET'"
check "mods and marketplace you already had are not recorded as owned" "! grep -rq 'usage-band@' '$H/.local/state/agent-tack/ownership/entries'"
uninstall
check "uninstall leaves what it did not install" "installed usage-band@$MARKET && grep -qxF $MARKET '$STATE/markets'"
check "uninstall removes the mod it did install" "! installed agent-activity@$MARKET"

echo "Doctor"
fresh_home doctor
env HOME="$H" XDG_CONFIG_HOME="$H/.config" GIT_CONFIG_NOSYSTEM=1 PATH="$MINBIN" bash "$REPO/lib/doctor.sh" "$REPO" >"$H.nocli" 2>&1
check "without claude: warns" "grep -q 'WARN mods: claude CLI not found' '$H.nocli'"
install
check "installed mods are reported" "doctor; grep -q 'OK   mod installed: usage-band' '$H.log' && grep -q 'OK   mod installed: agent-activity' '$H.log'"
echo "" > "$STATE/plugins"
check "missing mods are a warning" "doctor; grep -q 'WARN mod not installed: usage-band' '$H.log'"
git_global harness.mods false
check "disabled mods are reported as such" "doctor; grep -q 'mods disabled' '$H.log'"

echo "Former marketplace name"
fresh_home legacy
printf 'agent-harness-mods\n' > "$STATE/markets"
printf 'usage-band@agent-harness-mods\nagent-activity@agent-harness-mods\n' > "$STATE/plugins"
check "install over the former marketplace succeeds" "install"
check "mods from the former marketplace are uninstalled" "! grep -q '@agent-harness-mods' '$STATE/plugins'"
check "the former marketplace is removed" "! grep -qx 'agent-harness-mods' '$STATE/markets'"
check "the mods come from the new marketplace" "grep -qx 'usage-band@agent-tack-mods' '$STATE/plugins'"

echo "Moved checkout"
fresh_home moved
install
check "a fresh install registers this checkout's plugins folder" "grep -qxF '$REPO/plugins' '$STATE/market-path'"
: > "$STATE/calls"
install
check "a reinstall from the same checkout keeps the marketplace" "! called 'plugin marketplace remove $MARKET'"
printf '%s\n' "$WORK/old-checkout/plugins" > "$STATE/market-path"
: > "$STATE/calls"
check "install after moving the checkout succeeds" "install"
check "the marketplace registered at the old path is removed" "called 'plugin marketplace remove $MARKET'"
check "the marketplace is re-added from the new checkout" "grep -qxF '$REPO/plugins' '$STATE/market-path' && grep -qx '$MARKET' '$STATE/markets'"
check "the install reports the move" "grep -q 'the checkout moved' '$H.log'"

echo
echo "$PASSED passed, $FAILED failed"
[ "$FAILED" -eq 0 ]
