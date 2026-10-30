#!/usr/bin/env bash
# get.sh and tack update against a local Git repository standing in for GitHub: no network.
# Usage: tests/update.test.sh
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/tack-update.XXXXXX")" || exit 1
trap 'rm -rf "$WORK"' EXIT
export HOME="$WORK/home" XDG_CONFIG_HOME="$WORK/home/.config" XDG_STATE_HOME="$WORK/home/.local/state"
export XDG_DATA_HOME="$WORK/home/.local/share" GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL="$WORK/home/gitconfig"
unset GIT_CONFIG_COUNT GIT_CONFIG_SYSTEM TACK_DIR
mkdir -p "$HOME"
git config --global user.email test@example.com
git config --global user.name test
git config --global init.defaultBranch main
export INSTALL_LOG="$WORK/install.log" TACK_REPO_URL="$WORK/remote"
PASSED=0 FAILED=0
check() {
  local label="$1"
  shift
  if "$@"; then PASSED=$((PASSED + 1)); printf '  ✔ %s\n' "$label"
  else FAILED=$((FAILED + 1)); printf '  ✘ %s\n' "$label"; fi
}
expect_exit() {
  local expected="$1" actual
  shift
  "$@" > "$WORK/output" 2>&1
  actual=$?
  [ "$actual" -eq "$expected" ] || { printf '    exit %s, expected %s:\n' "$actual" "$expected"; sed 's/^/    /' "$WORK/output"; return 1; }
}
contains() { grep -qF -- "$1" "$WORK/output"; }
lacks() { ! grep -qF -- "$1" "$WORK/output"; }
at_version() { [ "$(git -C "$1" describe --tags --exact-match HEAD 2>/dev/null)" = "$2" ]; }
on_branch() { git -C "$1" symbolic-ref -q HEAD >/dev/null; }
detached() { ! git -C "$1" symbolic-ref -q HEAD >/dev/null; }
installed() { [ "$(tail -n 1 "$INSTALL_LOG" 2>/dev/null)" = "$1" ]; }
not_installed() { [ ! -s "$INSTALL_LOG" ]; }

# The fake upstream: this working tree's CLI, a stub installer that records its version and
# options, and a changelog per release. A prerelease and an unreleased commit follow the latest.
SRC="$WORK/remote"
mkdir -p "$SRC/bin"
cp "$REPO/bin/tack" "$SRC/bin/tack"
cp -R "$REPO/lib" "$SRC/lib"
printf '__pycache__/\n' > "$SRC/.gitignore"
cat > "$SRC/install.sh" <<'STUB'
#!/usr/bin/env bash
echo "$(git -C "$(dirname "$0")" describe --tags --always) $*" >> "$INSTALL_LOG"
STUB
chmod +x "$SRC/install.sh" "$SRC/bin/tack"
echo 'readme' > "$SRC/README.md"
release() {
  local version="$1" note="$2"
  { printf '# Changelog\n\n## [Unreleased]\n\n## [%s] - 2026-01-01\n\n### Added\n\n- %s\n' "$version" "$note"
    [ ! -f "$SRC/CHANGELOG.md" ] || sed '1,/^## \[Unreleased\]/d' "$SRC/CHANGELOG.md"; } > "$WORK/changelog"
  mv "$WORK/changelog" "$SRC/CHANGELOG.md"
  git -C "$SRC" add -A && git -C "$SRC" commit -qm "chore(release): v$version" && git -C "$SRC" tag -a -m "v$version" "v$version"
}
git init -q "$SRC"
release 1.0.0 'First feature.'
release 1.1.0 'Second feature.'
release 1.2.0-rc1 'Prerelease feature.'
echo unreleased >> "$SRC/README.md"
git -C "$SRC" commit -qam 'feat: unreleased work'

echo "get.sh"
check "fails clearly without the remote's releases" expect_exit 1 env TACK_REPO_URL="$WORK/missing" bash "$REPO/get.sh"
check "names the repository it could not read" contains "$WORK/missing"
DEFAULT="$XDG_DATA_HOME/agent-tack/release"
check "installs the latest release" expect_exit 0 bash "$REPO/get.sh" --skip-plugins
check "into the data folder by default" at_version "$DEFAULT" v1.1.0
check "skipping prereleases and unreleased work" lacks 'rc1'
check "without Git warnings about the annotated release tag" lacks 'warning:'
check "as a detached release checkout" detached "$DEFAULT"
check "and runs its installer with the options given" installed 'v1.1.0 --skip-plugins'
check "says how to update later" contains 'tack update'
: > "$INSTALL_LOG"
check "a second run delegates to tack update" expect_exit 0 bash "$REPO/get.sh"
check "which reports the release is current" contains 'up to date'
check "and does not reinstall" not_installed

MANAGED="$WORK/managed dir"
check "TACK_DIR chooses the folder" expect_exit 0 env TACK_DIR="$MANAGED" bash "$REPO/get.sh"
check "the chosen folder holds the release" at_version "$MANAGED" v1.1.0
mkdir -p "$WORK/other"
check "refuses a folder that is not a tack checkout" expect_exit 1 env TACK_DIR="$WORK/other" bash "$REPO/get.sh"
check "and explains why" contains 'not a tack checkout'
mkdir -p "$WORK/nopython"
for tool in bash env git sed awk grep mkdir mv rm dirname cat head; do
  ln -s "$(command -v "$tool")" "$WORK/nopython/$tool"
done
check "fails without python3" expect_exit 1 env PATH="$WORK/nopython" TACK_DIR="$WORK/new" bash "$REPO/get.sh"
check "naming python3" contains 'python3'
check "before creating anything" test ! -e "$WORK/new"
if command -v dash >/dev/null 2>&1; then
  check "fails under a shell that is not bash" expect_exit 1 dash "$REPO/get.sh"
  check "asking for bash" contains 'bash'
else
  echo '  - not-bash check skipped (dash not installed)'
fi

echo "tack update"
OLD="$WORK/old"
git -c advice.detachedHead=false clone -q --branch v1.0.0 "$SRC" "$OLD"
: > "$INSTALL_LOG"
check "--check succeeds" expect_exit 0 "$OLD/bin/tack" update --check
check "--check names the installed release" contains 'v1.0.0'
check "--check names the latest release" contains 'v1.1.0'
check "--check lists the new changelog entries" contains 'Second feature.'
check "--check leaves out entries already installed" lacks 'First feature.'
check "--check changes nothing" at_version "$OLD" v1.0.0
check "--check runs no installer" not_installed
check "rejects an unknown option" expect_exit 2 "$OLD/bin/tack" update --bogus
check "rejects it before changing anything" at_version "$OLD" v1.0.0
check "updates to the latest release" expect_exit 0 "$OLD/bin/tack" update --skip-mods
check "the checkout is at the latest release" at_version "$OLD" v1.1.0
check "shows the previous and new release" contains 'v1.0.0 -> v1.1.0'
check "shows the new changelog entries" contains 'Second feature.'
check "reruns the new release's installer with the options" installed 'v1.1.0 --skip-mods'
: > "$INSTALL_LOG"
check "a current checkout is left alone" expect_exit 0 "$OLD/bin/tack" update
check "and says so" contains 'up to date'
check "without reinstalling" not_installed

DIRTY="$WORK/dirty"
git -c advice.detachedHead=false clone -q --branch v1.0.0 "$SRC" "$DIRTY"
echo 'my edit' >> "$DIRTY/README.md"
check "refuses a checkout with local changes" expect_exit 1 "$DIRTY/bin/tack" update
check "suggests updating it by hand" contains 'git pull && ./install.sh'
check "names the explicit override" contains '--force'
check "and leaves it unchanged" at_version "$DIRTY" v1.0.0
check "--check still reports on it" expect_exit 0 "$DIRTY/bin/tack" update --check
check "--force updates it" expect_exit 0 "$DIRTY/bin/tack" update --force
check "keeping the local change" grep -q 'my edit' "$DIRTY/README.md"
check "at the latest release" at_version "$DIRTY" v1.1.0

DEV="$WORK/dev"
git clone -q "$SRC" "$DEV"
: > "$INSTALL_LOG"
check "refuses a development branch" expect_exit 1 "$DEV/bin/tack" update
check "naming the branch" contains 'main'
check "and suggests git pull" contains 'git pull && ./install.sh'
check "never switches it to a release" expect_exit 0 "$DEV/bin/tack" update --force
check "when it already includes the release" contains 'already includes v1.1.0'
check "the branch stays checked out" on_branch "$DEV"
check "without reinstalling" not_installed
git -C "$DEV" switch -q -c behind v1.0.0
check "--force moves a branch behind the release to it" expect_exit 0 "$DEV/bin/tack" update --force
check "the checkout is at the latest release" at_version "$DEV" v1.1.0

printf '\n%s passed, %s failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
