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
printf '\n%s passed, %s failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
