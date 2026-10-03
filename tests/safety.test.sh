#!/usr/bin/env bash
# Regression tests for staged secret scanning and project formatter trust.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/agent-harness-safety.XXXXXX")" || exit 1
trap 'rm -rf "$WORK"' EXIT
PASSED=0
FAILED=0
pass() { printf '  ✔ %s\n' "$1"; PASSED=$((PASSED + 1)); }
fail() { printf '  ✘ %s\n' "$1"; FAILED=$((FAILED + 1)); }
check() { local name="$1"; shift; if "$@"; then pass "$name"; else fail "$name"; fi; }

export HOME="$WORK/home" XDG_CONFIG_HOME="$WORK/home/.config" GIT_CONFIG_NOSYSTEM=1
mkdir -p "$HOME"
git config --global user.name 'Test User'
git config --global user.email 'test@example.com'
git config --global init.defaultBranch main
git config --global core.hooksPath "$REPO/git-hooks"
git config --global commit.gpgsign false
KEY="AKIA$(printf '%016d' 0)"

new_repo() {
  R="$WORK/$1"
  git init -q "$R" || exit 1
  git -C "$R" commit -q --allow-empty -m 'chore: initial commit' || exit 1
}
stage() {
  mkdir -p "$(dirname "$R/$1")" || exit 1
  printf '%s\n' "$2" > "$R/$1"
  git --literal-pathspecs -C "$R" add -f -- "$1" || exit 1
}
commit() { git -C "$R" commit -q --allow-empty -m 'chore: test' > "$WORK/commit-output" 2>&1; }
refuses_secret() { ! commit && grep -q 'refusing to commit secrets' "$WORK/commit-output"; }
reset() { git -C "$R" reset -q && git -C "$R" clean -qfdx; }
hook_status() { (cd "$R" && bash "$REPO/git-hooks/pre-commit") > "$WORK/hook-output" 2>&1; }
status_is() { local expected="$1" rc; hook_status; rc=$?; [ "$rc" -eq "$expected" ]; }
status_with_env() {
  local expected="$1" rc
  shift
  (cd "$R" && env "$@" bash "$REPO/git-hooks/pre-commit") > "$WORK/hook-output" 2>&1
  rc=$?
  [ "$rc" -eq "$expected" ]
}

echo 'pre-commit: scan the index after the local hook'
new_repo local-stage
cat > "$R/.git/hooks/pre-commit" <<'HOOK'
#!/usr/bin/env bash
printf 'TOKEN=fixture\n' > .env
git add -f .env
HOOK
chmod +x "$R/.git/hooks/pre-commit"
check 'a local hook staging .env blocks an actual commit' refuses_secret
check 'the initial commit remains the tip' test "$(git -C "$R" log -1 --format=%s)" = 'chore: initial commit'
printf '#!/usr/bin/env bash\nexit 42\n' > "$R/.git/hooks/pre-commit"
check 'local hook failures preserve their exit status' status_is 42
check 'the deliberate override still respects local hook failure' status_with_env 42 HARNESS_ALLOW_SECRETS=1
rm "$R/.git/hooks/pre-commit"

echo 'pre-commit: filenames are exact and do not depend on diff headers'
new_repo exact-paths
for path in 'café.txt' 'with"quote.txt' $'with\ttab.txt' $'with\nnewline.txt' $'trailing-newline.txt\n' '*.txt' '[fixture].txt' ':fixture.txt' '-fixture.txt'; do
  stage "$path" "$KEY"
  check "credential in $(printf '%q' "$path") is refused" refuses_secret
  reset || exit 1
done
for path in 'café/.env' 'with"quote/.env.production' $'with\ttab/.env.local' $'with\nnewline/.env'; do
  stage "$path" 'TOKEN=fixture'
  check "environment file $(printf '%q' "$path") is refused" refuses_secret
  reset || exit 1
done
for suffix in example sample template dist; do
  stage "café/.env.$suffix" 'TOKEN='
  check "the .$suffix environment template remains allowed" commit
  reset || exit 1
done
stage 'custom-prefix.txt' "$KEY"
git -C "$R" config diff.mnemonicPrefix true
git -C "$R" config diff.noprefix true
check 'custom diff prefixes cannot hide credentials' refuses_secret
reset || exit 1
stage '.gitattributes' '*.txt -diff'
stage 'binary-attribute.txt' "$KEY"
check 'binary diff attributes cannot hide added credentials' refuses_secret
reset || exit 1
stage 'nul-content.txt' 'safe data'
printf 'prefix\000%s\n' "$KEY" > "$R/nul-content.txt"
git -C "$R" add nul-content.txt
check 'a NUL byte in staged content cannot hide credentials' refuses_secret
reset || exit 1
stage 'staged.txt' "$KEY"
printf 'safe working tree\n' > "$R/staged.txt"
check 'the staged data is inspected rather than the working tree' refuses_secret
reset || exit 1
stage 'unstaged.txt' 'safe staged data'
printf '%s\n' "$KEY" > "$R/unstaged.txt"
check 'unstaged credentials do not block safe staged data' commit
reset || exit 1
stage 'historical.txt' "$KEY"
HARNESS_ALLOW_SECRETS=1 commit || exit 1
printf 'safe new line\n' >> "$R/historical.txt"
git -C "$R" add historical.txt
check 'an unchanged historical credential is outside the added-content policy' commit
printf 'safe replacement\n' > "$R/historical.txt"
git -C "$R" add historical.txt
check 'removing a historical credential remains allowed' commit

new_repo type-change
ln -s safe-target "$R/kind.txt"
git -C "$R" add kind.txt
commit || exit 1
rm "$R/kind.txt"
stage 'kind.txt' "$KEY"
check 'a staged symlink-to-file change cannot hide credentials' refuses_secret
reset || exit 1
stage "name-$KEY.txt" 'safe content'
check 'credential-shaped text in a filename is not scanned as content' commit
reset || exit 1
stage 'external.txt' "$KEY"
cat > "$WORK/external-diff" <<'DIFF'
#!/usr/bin/env bash
printf 'ran\n' > "$HARNESS_TEST_EXTERNAL_CALLS"
exit 0
DIFF
chmod +x "$WORK/external-diff"
export HARNESS_TEST_EXTERNAL_CALLS="$WORK/external-calls"
check 'external diff helpers cannot suppress the scan' status_with_env 1 "GIT_EXTERNAL_DIFF=$WORK/external-diff"
check 'the scanner never executes an external diff helper' test ! -e "$WORK/external-calls"

echo 'pre-commit: Git read errors fail closed'
new_repo git-errors
stage safe.txt 'safe data'
REAL_GIT="$(command -v git)"
export HARNESS_TEST_REAL_GIT="$REAL_GIT"
mkdir "$WORK/bin"
cat > "$WORK/bin/git" <<'STUB'
#!/usr/bin/env bash
arguments=()
for argument in "$@"; do
  case "$HARNESS_TEST_GIT_FAIL:$argument" in
    names:--name-only|content:--unified=0|content:-U0) exit 42 ;;
  esac
  arguments+=("$argument")
  if [ "$HARNESS_TEST_GIT_FAIL:$argument" = display:diff ]; then
    arguments+=(--src-prefix=custom-old/ --dst-prefix=custom-new/ --output-indicator-new='!')
  fi
done
exec "$HARNESS_TEST_REAL_GIT" "${arguments[@]}"
STUB
chmod +x "$WORK/bin/git"
for operation in names content; do
  check "$operation read failure blocks scanning" status_with_env 1 "PATH=$WORK/bin:$PATH" "HARNESS_TEST_GIT_FAIL=$operation"
done
stage 'display.txt' "$KEY"
check 'custom diff prefixes and indicators cannot hide credentials' status_with_env 1 "PATH=$WORK/bin:$PATH" HARNESS_TEST_GIT_FAIL=display
check 'the scan recognises credentials with custom diff display settings' grep -q 'AWS access key' "$WORK/hook-output"

echo
echo "$PASSED passed, $FAILED failed"
[ "$FAILED" -eq 0 ]
