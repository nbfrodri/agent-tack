#!/usr/bin/env bash
# Tests for the targets.txt capability columns and 'harness doctor --tools'.
set -uo pipefail
umask 077
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/harness-tools-test.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
export HOME="$WORK/home" XDG_CONFIG_HOME="$WORK/home/.config" XDG_STATE_HOME="$WORK/home/.local/state"
export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL="$HOME/.gitconfig"
unset GIT_DIR GIT_WORK_TREE GIT_CONFIG_COUNT
mkdir -p "$HOME" "$WORK/bin" "$WORK/stubs"
PASSED=0 FAILED=0
check() {
  local name="$1"
  shift
  if "$@"; then printf '  ✔ %s\n' "$name"; PASSED=$((PASSED + 1))
  else printf '  ✘ %s\n' "$name"; FAILED=$((FAILED + 1)); fi
}
for tool in bash env mkdir dirname readlink ln rm mv date cp cmp mktemp sed basename git jq python3 chmod cat find grep tr wc head sort cut awk stat; do
  path="$(command -v "$tool" 2>/dev/null || true)"
  [ -z "$path" ] || ln -s "$path" "$WORK/bin/$tool"
done
BASE_PATH="$WORK/bin"
export PATH="$WORK/stubs:$BASE_PATH"

# stub NAME VERSION SMOKE_RC: prints a version, and a secret-looking line on any other call
stub() {
  printf '#!/bin/sh\nif [ "$1" = --version ]; then echo "%s (stub)"; exit 0; fi\necho "token=SECRET123 path=$HOME"\nexit %s\n' "$2" "$3" > "$WORK/stubs/$1"
  chmod +x "$WORK/stubs/$1"
}
column_count_ok() { test -z "$(grep -v '^#' "$REPO/targets.txt" | grep -v '^$' | awk 'NF != 9')"; }

echo "targets.txt columns"
check 'every tool row has the 9 columns' column_count_ok
check 'claude declares agents and hooks' grep -Eq '^claude .*~/.claude/agents +~/.claude/settings.json ' "$REPO/targets.txt"

echo "legacy five-column targets.txt still installs"
mkdir -p "$WORK/legacy"
cp -R "$REPO/." "$WORK/legacy/"
grep -v '^#' "$REPO/targets.txt" | awk 'NF {print $1, $2, $3, $4, $5}' > "$WORK/legacy/targets.txt"
check 'install succeeds' bash -c "cd '$WORK/legacy' && ./install.sh --skip-plugins >'$WORK/legacy.log' 2>&1"
check 'codex instructions linked' test -L "$HOME/.codex/AGENTS.md"
check 'claude agents linked' test -n "$(find "$HOME/.claude/agents" -type l | head -1)"

doctor_tools() {
  (cd "$WORK" && bash "${ROOT:-$REPO}/lib/doctor.sh" "${ROOT:-$REPO}" --tools) >"$WORK/report" 2>&1
  RC=$?
}

echo "doctor --tools"
rm -rf "$HOME"
mkdir -p "$HOME"
"$REPO/install.sh" --skip-plugins >"$WORK/install.log" 2>&1
doctor_tools
check 'no installed tools: healthy' test "$RC" -eq 0
check 'absent tools are skipped explicitly' grep -q 'claude: not installed, skipped' "$WORK/report"

stub claude 2.1.288 0
stub codex 0.160.0 0
doctor_tools
check 'healthy tools exit 0' test "$RC" -eq 0
check 'version is detected' grep -q 'OK   claude: version 2.1.288' "$WORK/report"
check 'capabilities are listed' grep -q 'claude: capabilities instructions skills agents hooks' "$WORK/report"
check 'unsupported capabilities are omitted' grep -q 'codex: capabilities instructions skills$' "$WORK/report"
check 'smoke check passes' grep -q 'OK   codex: smoke check passed' "$WORK/report"
check 'tool output and secrets are never printed' test -z "$(grep -E 'SECRET123|token=' "$WORK/report")"

stub codex 0.160.0 3
doctor_tools
check 'failing smoke check is only a warning' test "$RC" -eq 0
check 'failing smoke check is reported' grep -q 'WARN codex: smoke check failed' "$WORK/report"

stub codex 0.160.0 0
mkdir -p "$WORK/minroot"
cp -R "$REPO/lib" "$WORK/minroot/"
ln -s "$REPO/global" "$WORK/minroot/global"
ln -s "$REPO/skills" "$WORK/minroot/skills"
ln -s "$REPO/agents" "$WORK/minroot/agents"
sed 's/ - \{1,\}doctor,--summary$/ 0.200.0 doctor,--summary/' "$REPO/targets.txt" > "$WORK/minroot/targets.txt"
ROOT="$WORK/minroot" doctor_tools
check 'version below minimum is not an error' test -z "$(grep 'FAIL.*older' "$WORK/report")"
check 'below-minimum message' grep -q 'WARN codex: version 0.160.0 is older than the minimum 0.200.0' "$WORK/report"
sed 's/0\.200\.0/0.100.0/' "$WORK/minroot/targets.txt" > "$WORK/minroot/targets.new"
mv "$WORK/minroot/targets.new" "$WORK/minroot/targets.txt"
ROOT="$WORK/minroot" doctor_tools
check 'version meeting the minimum is ok' grep -q 'OK   codex: version 0.160.0 meets the minimum 0.100.0' "$WORK/report"

rm "$HOME/.claude/CLAUDE.md"
doctor_tools
check 'broken managed capability is an error' test "$RC" -eq 1
check 'broken capability names the tool' grep -q 'FAIL claude' "$WORK/report"
ln -s "$REPO/global/AGENTS.md" "$HOME/.claude/CLAUDE.md"

check 'harness doctor --tools is wired' bash -c "'$REPO/bin/harness' doctor --tools | grep -q 'claude: version'"
check 'help documents --tools' bash -c "'$REPO/bin/harness' help | grep -q -- '--tools'"
check 'doctor rejects unknown options' bash -c "'$REPO/bin/harness' doctor --nope >/dev/null 2>&1; [ \$? -eq 2 ]"

printf '\n%s passed, %s failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
