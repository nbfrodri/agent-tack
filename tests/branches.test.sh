#!/usr/bin/env bash
# Regression tests for `tack branches`: local branches whose work is already merged.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/tack-branches.XXXXXX")" || exit 1
trap 'rm -rf "$WORK"' EXIT
PASSED=0
FAILED=0
pass() { printf '  ✔ %s\n' "$1"; PASSED=$((PASSED + 1)); }
fail() { printf '  ✘ %s\n' "$1"; FAILED=$((FAILED + 1)); }
check() { local name="$1"; shift; if "$@"; then pass "$name"; else fail "$name"; fi; }

export HOME="$WORK/home" XDG_CONFIG_HOME="$WORK/home/.config" XDG_STATE_HOME="$WORK/home/.local/state" GIT_CONFIG_NOSYSTEM=1
mkdir -p "$HOME"
git config --global user.name 'Test User'
git config --global user.email 'test@example.com'
git config --global init.defaultBranch main
git config --global commit.gpgsign false

# A fake gh answers `pr list --state merged --head NAME` from a fixture file named after the branch.
FIXTURES="$WORK/fixtures"
FAKEBIN="$WORK/fake-gh"
mkdir -p "$FIXTURES" "$FAKEBIN"
cat > "$FAKEBIN/gh" <<'STUB'
#!/usr/bin/env bash
head=""
while [ "$#" -gt 0 ]; do
  [ "$1" != --head ] || head="$2"
  shift
done
file="$GH_FIXTURES/${head//\//_}"
if [ -f "$file" ]; then cat "$file"; else echo '[]'; fi
STUB
chmod +x "$FAKEBIN/gh"
# A PATH without any gh, so the real one can never answer.
MINBIN="$WORK/bin-min"
mkdir -p "$MINBIN"
for tool in bash env mkdir dirname readlink ln rm mv date cp cmp mktemp sed basename git jq python3 stat chmod cat find grep tr wc head uname; do
  [ ! -x "$(command -v "$tool")" ] || ln -sf "$(command -v "$tool")" "$MINBIN/$tool"
done

R="$WORK/repo"
git init -q "$R"
git -C "$R" commit -q --allow-empty -m 'chore: initial commit'
commit() { printf '%s\n' "$2" > "$R/$2.txt"; git -C "$R" add "$2.txt"; git -C "$R" commit -q -m "$1"; }

# Merged with a merge commit: an ancestor of main.
git -C "$R" switch -q -c merged-ff
commit 'feat: ff work' ff
git -C "$R" switch -q main
git -C "$R" merge -q --no-ff merged-ff -m 'Merge merged-ff'
# Squash-merged: main has the change under another commit; the PR's head is the branch tip.
git -C "$R" switch -q -c squashed
commit 'feat: squashed work' squashed
squashed_tip="$(git -C "$R" rev-parse HEAD)"
git -C "$R" switch -q main
git -C "$R" merge -q --squash squashed
git -C "$R" commit -q -m 'feat: squashed work (#1)'
printf '[{"number":1,"headRefOid":"%s"}]\n' "$squashed_tip" > "$FIXTURES/squashed"
# Squash-merged, then kept working on: the extra commit is not on main.
git -C "$R" switch -q -c late
commit 'feat: late work' late
late_tip="$(git -C "$R" rev-parse HEAD)"
git -C "$R" switch -q main
git -C "$R" merge -q --squash late
git -C "$R" commit -q -m 'feat: late work (#2)'
printf '[{"number":2,"headRefOid":"%s"}]\n' "$late_tip" > "$FIXTURES/late"
git -C "$R" switch -q late
commit 'feat: after the merge' after
# Never merged.
git -C "$R" switch -q main
git -C "$R" switch -q -c open
commit 'feat: open work' open
# Merged but checked out: the branch in use stays.
git -C "$R" switch -q main
git -C "$R" switch -q -c in-use
git -C "$R" switch -q main
git -C "$R" merge -q in-use
git -C "$R" switch -q in-use

tack() { (cd "$R" && env GH_FIXTURES="$FIXTURES" PATH="$FAKEBIN:$PATH" "$REPO/bin/tack" branches "$@" 2>&1); }
has_branch() { git -C "$R" show-ref --verify --quiet "refs/heads/$1"; }
lacks_branch() { ! has_branch "$1"; }
refuses_option() { ! (cd "$R" && "$REPO/bin/tack" branches --nope >/dev/null 2>&1); }

echo "tack branches"
plan="$(tack)"
check "plan: a branch merged into main is marked delete" grep -Eq '^delete +merged-ff' <<< "$plan"
check "plan: a squash-merged branch is marked delete with its PR" grep -Eq '^delete +squashed .*#1' <<< "$plan"
check "plan: commits made after the PR was merged keep the branch" grep -Eq '^keep +late' <<< "$plan"
check "plan: an unmerged branch is kept" grep -Eq '^keep +open' <<< "$plan"
check "plan: the checked-out branch is kept" grep -Eq '^keep +in-use' <<< "$plan"
check "plan: nothing is deleted without --apply" has_branch merged-ff
check "plan: it says how to apply" grep -q -- '--apply' <<< "$plan"

applied="$(tack --apply)"
check "apply: the merged branch is deleted" lacks_branch merged-ff
check "apply: the squash-merged branch is deleted" lacks_branch squashed
check "apply: the branch with later commits survives" has_branch late
check "apply: the unmerged branch survives" has_branch open
check "apply: the checked-out branch survives" has_branch in-use
check "apply: it reports what it deleted" grep -Eq '^deleted +merged-ff' <<< "$applied"

# Without gh a squash-merged branch cannot be told from unmerged work, so it stays.
git -C "$R" switch -q main
git -C "$R" branch -q squashed2 "$squashed_tip"
printf '[{"number":3,"headRefOid":"%s"}]\n' "$squashed_tip" > "$FIXTURES/squashed2"
without_gh="$(cd "$R" && env PATH="$MINBIN" "$REPO/bin/tack" branches --apply 2>&1)"
check "no gh: a squash-merged branch is kept" has_branch squashed2
check "no gh: it says gh is missing" grep -q 'gh' <<< "$without_gh"

check "an unknown option is refused" refuses_option

printf '\n%s passed, %s failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
