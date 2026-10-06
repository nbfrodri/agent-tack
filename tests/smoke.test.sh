#!/usr/bin/env bash
# End-to-end smoke test: install into a temporary HOME, commit through the global git hooks, ask the
# command guard and run the doctor. Portable on purpose: CI runs it on Linux, macOS and Windows
# (Git Bash), where the other suites rely on tools or symlink behaviour Windows lacks.
# Usage: tests/smoke.test.sh
set -uo pipefail
unset XDG_STATE_HOME GIT_CONFIG_GLOBAL

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/agent-tack-smoke.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
export HOME="$WORK/home" XDG_CONFIG_HOME="$WORK/home/.config" GIT_CONFIG_NOSYSTEM=1
mkdir -p "$HOME"
PASSED=0
FAILED=0
check() {
  if eval "$2"; then printf '  ✔ %s\n' "$1"; PASSED=$((PASSED + 1))
  else printf '  ✘ %s\n' "$1"; FAILED=$((FAILED + 1)); fi
}

echo "Install"
check "install.sh succeeds in a temporary HOME" "'$REPO/install.sh' --skip-plugins >'$WORK/install.log' 2>&1 || { cat '$WORK/install.log'; false; }"
check "global instructions are linked" "[ -L '$HOME/.claude/CLAUDE.md' ]"
check "git uses tack's hooks" "[ \"\$(cd \"\$(git config --global core.hooksPath)\" && pwd -P)\" = \"\$(cd '$REPO/git-hooks' && pwd -P)\" ]"
case "$(uname -s)" in
  # Doctor and uninstall still misjudge paths and permissions there (#111).
  MINGW* | MSYS* | CYGWIN*) echo "  - doctor skipped on native Windows (#111)" ;;
  *) check "the doctor reports no errors" "bash '$REPO/lib/doctor.sh' '$REPO' >'$WORK/doctor.log' 2>&1 || { grep -v '^OK' '$WORK/doctor.log'; false; }" ;;
esac

echo "Commits through the global hooks"
P="$WORK/project"
git init -q -b main "$P"
git -C "$P" config user.name Smoke
git -C "$P" config user.email smoke@example.com
git -C "$P" switch -q -c feat/x
printf 'x\n' > "$P/a.txt" && git -C "$P" add a.txt
check "a commit runs every hook without error" "git -C '$P' commit -q -m 'feat: add a' -m 'Co-Authored-By: Claude <noreply@anthropic.com>'"
check "commit-msg removed the AI attribution" "! git -C '$P' log -1 --format=%B | grep -qi 'co-authored-by'"
(cd "$P" && "$REPO/bin/tack" enable >/dev/null)
printf 'y\n' > "$P/b.txt" && git -C "$P" add b.txt
check "an enabled project rejects a non-conventional subject" "! git -C '$P' commit -q -m 'added b' 2>/dev/null"
printf 'AWS_SECRET_ACCESS_KEY=1\n' > "$P/.env" && git -C "$P" add -f .env
check "pre-commit refuses a .env file" "! git -C '$P' commit -q -m 'chore: add env' 2>/dev/null"

echo "Command guard"
decision() {
  printf '{"tool_input":{"command":"%s"},"cwd":"%s"}' "$1" "$P" | bash "$REPO/hooks/claude/guard-bash.sh" \
    | grep -o '"permissionDecision":"[a-z]*"' | cut -d'"' -f4
}
check "allows a harmless command" "[ -z \"\$(decision 'ls -la')\" ]"
check "denies a force-push to main" "[ \"\$(decision 'git push --force origin main')\" = deny ]"
check "denies deleting the root directory" "[ \"\$(decision 'rm -rf /')\" = deny ]"
check "asks before a hard reset" "[ \"\$(decision 'git reset --hard HEAD~1')\" = ask ]"

echo
echo "$PASSED passed, $FAILED failed"
[ "$FAILED" -eq 0 ]
