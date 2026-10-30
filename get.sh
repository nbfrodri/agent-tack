#!/usr/bin/env bash
# Installs tack from its latest release without a manual clone:
#   curl -fsSL https://raw.githubusercontent.com/nbfrodri/agent-tack/main/get.sh | bash
#   curl -fsSL .../get.sh | bash -s -- --skip-plugins     (options go to install.sh)
# Checks the latest release tag out into TACK_DIR (default: ${XDG_DATA_HOME:-~/.local/share}/agent-tack/release)
# and runs its install.sh. Run again, or use tack update, to move to a newer release.
# TACK_REPO_URL overrides the repository (tests use a local one).

# Plain POSIX syntax until bash is confirmed, so another shell gets this message instead of an error.
if [ -z "${BASH_VERSION:-}" ]; then
  echo 'get.sh: bash is required; run it with: curl -fsSL <url> | bash' >&2
  exit 1
fi
set -uo pipefail

die() { printf 'get.sh: %s\n' "$1" >&2; exit 1; }

# The whole script is one function, so a partial download runs nothing.
main() {
  local tool dir url tag partial
  for tool in git python3; do
    command -v "$tool" >/dev/null 2>&1 || die "$tool is required; install it and run this again"
  done
  dir="${TACK_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/agent-tack/release}"
  url="${TACK_REPO_URL:-https://github.com/nbfrodri/agent-tack.git}"

  if [ -e "$dir" ]; then
    { [ -d "$dir/.git" ] && [ -f "$dir/bin/tack" ]; } \
      || die "$dir exists and is not a tack checkout; move it away or choose another folder with TACK_DIR"
    [ -f "$dir/lib/update.sh" ] \
      || die "the release in $dir predates tack update; run: git -C \"$dir\" fetch --tags, check out the newest tag and run $dir/install.sh"
    exec bash "$dir/bin/tack" update "$@"
  fi

  tag="$(git ls-remote --tags --refs --sort=-v:refname "$url" 'v*' 2>/dev/null \
    | awk '{ sub("^refs/tags/", "", $2) } $2 ~ /^v[0-9]+\.[0-9]+\.[0-9]+$/ && !found { print $2; found = 1 }')"
  [ -n "$tag" ] || die "cannot read release tags from $url"

  # Clone beside the target and move it into place, so a failed clone leaves nothing behind.
  mkdir -p "$(dirname "$dir")" || die "cannot create $(dirname "$dir")"
  partial="$dir.partial.$$"
  # --branch with an annotated tag makes Git warn that the tag "is not a commit", so check it out after.
  { git clone --quiet --no-checkout "$url" "$partial" \
    && git -C "$partial" -c advice.detachedHead=false checkout --quiet "$tag"; } \
    || { rm -rf "$partial"; die "cannot clone $tag from $url"; }
  mv "$partial" "$dir" || { rm -rf "$partial"; die "cannot move the checkout to $dir"; }
  echo "Downloaded tack $tag to $dir; running its install.sh. Update it later with: tack update"
  exec bash "$dir/install.sh" "$@"
}

main "$@"
