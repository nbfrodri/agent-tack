#!/usr/bin/env bash
# Tests the global git hooks (git-hooks/) and the Claude Code hooks (hooks/claude/).
# Uses throwaway repositories and an isolated git config; never touches the real HOME.
# Usage: tests/hooks.test.sh
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/agent-config-hooks.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
PASSED=0
FAILED=0

pass() { printf '  ✔ %s\n' "$1"; PASSED=$((PASSED + 1)); }
fail() { printf '  ✘ %s\n' "$1"; FAILED=$((FAILED + 1)); }
check() { if eval "$2"; then pass "$1"; else fail "$1"; fi; }

# Isolated git environment using the global hooks under test
export HOME="$WORK/home" XDG_CONFIG_HOME="$WORK/home/.config" GIT_CONFIG_NOSYSTEM=1
mkdir -p "$HOME"
git config --global user.name "Test User"
git config --global user.email "test@example.com"
git config --global init.defaultBranch main
git config --global core.hooksPath "$REPO/git-hooks"
git config --global commit.gpgsign false

new_repo() {
  rm -rf "$1"
  git init -q "$1"
  git -C "$1" commit -q --allow-empty -m "chore: initial commit"
}

commit() { git -C "$R" commit -q --allow-empty -m "$1" >/dev/null 2>&1; }
last_message() { git -C "$R" log -1 --format=%B; }

echo "commit-msg: Conventional Commits"
R="$WORK/repo"
new_repo "$R"
check "accepts 'feat(auth): add login'" "commit 'feat(auth): add login'"
check "accepts breaking change 'feat!: drop v1 API'" "commit 'feat!: drop v1 API'"
check "accepts 'fix: handle empty cart'" "commit 'fix: handle empty cart'"
check "rejects 'added login'" "! commit 'added login'"
check "rejects unknown type 'feature: x'" "! commit 'feature: add x'"
check "rejects missing description 'fix:'" "! commit 'fix:'"
check "rejects subject over 100 chars" "! commit \"fix: $(printf 'x%.0s' $(seq 1 100))\""
check "accepts autosquash 'fixup! feat: x'" "commit 'fixup! feat(auth): add login'"
check "accepts merge messages" "commit \"Merge branch 'feature'\""
check "accepts revert messages" "commit 'Revert \"feat: x\"'"

echo "commit-msg: AI attribution is removed"
commit "$(printf 'feat: add export\n\nExports orders as CSV.\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n')"
check "Co-Authored-By Claude removed" "! last_message | grep -qi 'co-authored-by'"
check "body is kept" "last_message | grep -q 'Exports orders as CSV.'"
commit "$(printf 'fix: x\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n')"
check "'Generated with Claude Code' line removed" "! last_message | grep -qi 'generated with'"
commit "$(printf 'fix: y\n\nCo-authored-by: Codex <codex@openai.com>\nCo-authored-by: Ana Dev <ana@example.com>\n')"
check "Codex trailer removed" "! last_message | grep -qi codex"
check "human co-author kept" "last_message | grep -q 'Ana Dev'"

echo "commit-msg: per-repo opt-out"
git -C "$R" config agentconfig.conventionalCommits false
check "free-form message allowed after opt-out" "commit 'Update stuff'"
commit "$(printf 'Update more\n\nCo-Authored-By: Claude <noreply@anthropic.com>\n')"
check "AI attribution still removed after opt-out" "! last_message | grep -qi claude"
git -C "$R" config --unset agentconfig.conventionalCommits

echo "Local repository hooks keep working (chaining)"
cat > "$R/.git/hooks/pre-commit" <<EOF
#!/usr/bin/env bash
echo ran > "$WORK/pre-commit-ran"
EOF
cat > "$R/.git/hooks/commit-msg" <<EOF
#!/usr/bin/env bash
echo "\$1" > "$WORK/commit-msg-ran"
EOF
chmod +x "$R/.git/hooks/pre-commit" "$R/.git/hooks/commit-msg"
commit "docs: chained hooks"
check "local pre-commit ran" "[ -f '$WORK/pre-commit-ran' ]"
check "local commit-msg ran with the message file" "[ -s '$WORK/commit-msg-ran' ]"
cat > "$R/.git/hooks/pre-commit" <<'EOF'
#!/usr/bin/env bash
echo "lint failed" >&2
exit 1
EOF
check "a failing local pre-commit still blocks the commit" "! commit 'docs: blocked'"
rm -f "$R/.git/hooks/pre-commit" "$R/.git/hooks/commit-msg"

echo "pre-push: main is protected"
REMOTE="$WORK/remote.git"
git init -q --bare "$REMOTE"
R="$WORK/pusher"
new_repo "$R"
git -C "$R" remote add origin "$REMOTE"
push() { git -C "$R" push -q "$@" >/dev/null 2>&1; }
check "normal push to main works" "push origin main"
commit "feat: second"
check "fast-forward push to main works" "push origin main"
before="$(git -C "$R" rev-parse HEAD)"
git -C "$R" commit -q --amend --allow-empty -m "feat: second (amended)" >/dev/null 2>&1
check "history was rewritten locally (test precondition)" "[ \"\$(git -C '$R' rev-parse HEAD)\" != '$before' ]"
check "force push to main is refused" "! push --force origin main"
check "force-with-lease to main is refused" "! push --force-with-lease origin main"
check "override variable allows it" "AGENT_CONFIG_ALLOW_FORCE_PUSH=1 push --force origin main"
check "deleting main on the remote is refused" "! push origin :main"
git -C "$R" switch -q -c feat/x
commit "feat: on branch"
check "push of a feature branch works" "push origin feat/x"
before="$(git -C "$R" rev-parse HEAD)"
git -C "$R" commit -q --amend --allow-empty -m "feat: on branch (amended)" >/dev/null 2>&1
check "feature branch rewritten locally (test precondition)" "[ \"\$(git -C '$R' rev-parse HEAD)\" != '$before' ]"
check "force push to a feature branch is allowed" "push --force origin feat/x"

echo "pre-push: local pre-push hook receives stdin"
cat > "$R/.git/hooks/pre-push" <<EOF
#!/usr/bin/env bash
cat > "$WORK/pre-push-stdin"
EOF
chmod +x "$R/.git/hooks/pre-push"
commit "feat: more"
push origin feat/x
check "local pre-push ran with the ref list" "grep -q 'refs/heads/feat/x' '$WORK/pre-push-stdin'"
check "ref list keeps its trailing newline" "[ \"\$(tail -c 1 '$WORK/pre-push-stdin' | od -An -c | tr -d ' ')\" = '\\n' ]"
# The usual hook shape (as in git's pre-push.sample) must see every ref
cat > "$R/.git/hooks/pre-push" <<EOF
#!/usr/bin/env bash
n=0
while read -r _local_ref _local_sha _remote_ref _remote_sha; do n=\$((n + 1)); done
echo "\$n" > "$WORK/pre-push-count"
EOF
commit "feat: even more"
push origin feat/x
check "local pre-push 'while read' loop sees the pushed ref" "[ \"\$(cat '$WORK/pre-push-count')\" = 1 ]"
printf '#!/usr/bin/env bash\nexit 1\n' > "$R/.git/hooks/pre-push"
commit "feat: blocked push"
check "a failing local pre-push still blocks the push" "! push origin feat/x"
rm -f "$R/.git/hooks/pre-push"

echo "Claude hook: guard-bash"
GUARD="$REPO/hooks/claude/guard-bash.sh"
R="$WORK/guard"
new_repo "$R"
guard() {
  local cmd="$1" json
  if command -v jq >/dev/null 2>&1; then
    json="$(jq -n --arg c "$cmd" --arg d "$R" '{tool_name:"Bash",tool_input:{command:$c},cwd:$d}')"
  else
    json="$(python3 -c 'import json,sys; print(json.dumps({"tool_name":"Bash","tool_input":{"command":sys.argv[1]},"cwd":sys.argv[2]}))' "$cmd" "$R")"
  fi
  printf '%s' "$json" | bash "$GUARD"
}
decision() {
  local out
  out="$(guard "$1")"
  case "$out" in
    *'"deny"'*) echo deny ;;
    *'"ask"'*) echo ask ;;
    '') echo allow ;;
    *) echo "unexpected: $out" ;;
  esac
}
expect() { check "$2 → $1" "[ \"\$(decision $(printf '%q' "$2"))\" = '$1' ]"; }

expect allow "ls -la"
expect allow "git status && git diff"
expect allow "git push origin feat/login"
expect allow "git commit -m 'fix: x'"
expect allow "rm -rf node_modules dist"
expect allow "rm -rf /tmp/build-cache"
expect allow "truncate -s 0 app.log"
expect allow "git restore --staged src/app.ts"
expect allow "git clean -n"
expect deny "git push --force origin main"
expect deny "git push -f origin master"
expect deny "git push origin +main"
expect deny "git push origin --delete main"
expect deny "git -C /some/path push --force-with-lease origin main"
expect deny "git commit --no-verify -m 'feat: x'"
expect deny "git push --no-verify origin feat/x"
expect deny "rm -rf /"
expect deny "rm -rf ~"
expect deny "rm -rf \$HOME"
expect deny "rm -rf .."
expect deny "cd src && rm -rf ../*"
expect deny "rm -fr ~/"
expect ask "git push --force origin feat/x"
expect ask "git reset --hard HEAD~2"
expect ask "git clean -fd"
expect ask "git checkout -- ."
expect ask "git branch -D old-feature"
expect ask "git stash clear"
expect ask "rm -rf ./*"
expect ask "rm -rf /etc/nginx"
expect ask "rm -rf ~/projects/old"
expect ask "psql -c 'DROP DATABASE app'"
expect ask "mysql -e 'TRUNCATE TABLE users'"
expect ask "php artisan migrate:fresh --seed"
expect ask "npx prisma migrate reset"
expect deny "git push --force"
expect deny "git push --force-with-lease"
git -C "$R" switch -q -c feat/y
expect ask "git push --force-with-lease"
expect ask "git push --force"
check "invalid JSON input is allowed (fails open)" "[ -z \"\$(printf 'not json' | bash '$GUARD')\" ]"

echo "Claude hook: format-file"
FORMAT="$REPO/hooks/claude/format-file.sh"
P="$WORK/project"
mkdir -p "$P/node_modules/.bin" "$P/src"
git init -q "$P"
cat > "$P/node_modules/.bin/prettier" <<'EOF'
#!/usr/bin/env bash
for a in "$@"; do case "$a" in -*) ;; *) echo "// formatted" >> "$a" ;; esac; done
EOF
chmod +x "$P/node_modules/.bin/prettier"
echo "const a=1" > "$P/src/a.ts"
format() { printf '{"tool_name":"Edit","tool_input":{"file_path":"%s"}}' "$1" | bash "$FORMAT"; }
format "$P/src/a.ts"
check "no formatter config → file untouched" "! grep -q formatted '$P/src/a.ts'"
echo '{}' > "$P/.prettierrc"
format "$P/src/a.ts"
check "prettier configured → file formatted" "grep -q formatted '$P/src/a.ts'"
echo "x = 1" > "$P/src/a.py"
format "$P/src/a.py"
check "python file without ruff/black config untouched" "[ \"\$(cat '$P/src/a.py')\" = 'x = 1' ]"
check "missing file is ignored" "format '$P/nope.ts'"
check "always exits 0" "printf 'garbage' | bash '$FORMAT'"

echo
echo "$PASSED passed, $FAILED failed"
[ "$FAILED" -eq 0 ]
