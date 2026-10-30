#!/usr/bin/env bash
# tack update: move the checkout tack runs from to the latest release tag and rerun its installer.
# Usage: lib/update.sh TACK_ROOT [--check] [--force] [INSTALL_OPTION...]
# Exit codes: 0 updated, current or checked; 1 refused or failed; 2 invalid arguments.
set -uo pipefail

update_usage() {
  echo 'tack: usage: tack update [--check] [--force] [--skip-plugins] [--skip-mods] [--no-hooks] [--verbose]' >&2
  exit 2
}

# Release tags only (vMAJOR.MINOR.PATCH, no prerelease), newest first.
latest_release() {
  git -C "$1" tag --list 'v*' --sort=-v:refname | awk '/^v[0-9]+\.[0-9]+\.[0-9]+$/ && !found { print; found = 1 }'
}

# The changelog sections of the releases after FROM, read from TAG's CHANGELOG.md.
changelog_since() {
  local root="$1" tag="$2" from="${3#v}"
  git -C "$root" show "$tag:CHANGELOG.md" 2>/dev/null | awk -v from="$from" '
    /^## \[/ { if (index($0, "## [" from "]") == 1) exit; printing = ($0 !~ /^## \[Unreleased\]/) }
    printing'
}

# The whole run is one function, so a checkout that replaces this file cannot change it mid-run.
main() {
  local root="$1" check=0 force=0 arg branch latest current base refusal=''
  local install_args=()
  shift
  for arg in "$@"; do
    case "$arg" in
      --check | --dry-run) check=1 ;;
      --force) force=1 ;;
      --skip-plugins | --skip-mods | --no-hooks | --verbose) install_args+=("$arg") ;;
      *) update_usage ;;
    esac
  done
  if [ ! -e "$root/.git" ]; then
    echo "tack: $root is not a Git checkout; reinstall with get.sh (see docs/installation.md)" >&2
    exit 1
  fi
  git -C "$root" fetch --quiet --tags origin || { echo "tack: cannot fetch release tags from origin in $root" >&2; exit 1; }
  latest="$(latest_release "$root")"
  [ -n "$latest" ] || { echo "tack: no release tags found in $root" >&2; exit 1; }
  current="$(git -C "$root" describe --tags --always HEAD)"
  base="$(git -C "$root" describe --tags --abbrev=0 HEAD 2>/dev/null || true)"

  if [ "$(git -C "$root" rev-parse HEAD)" = "$(git -C "$root" rev-parse "$latest^{commit}")" ]; then
    echo "tack is up to date ($latest) in $root."
    exit 0
  fi

  # A development clone or local edits are the user's to update; --force proceeds anyway, and
  # Git still refuses to overwrite a local change that conflicts with the release.
  branch="$(git -C "$root" symbolic-ref -q --short HEAD || true)"
  if [ -n "$branch" ]; then
    refusal="is on branch $branch, not a release checkout"
  elif [ -n "$(git -C "$root" status --porcelain --untracked-files=no)" ]; then
    refusal='has local changes'
  fi
  if [ -n "$refusal" ] && [ "$force" -eq 0 ] && [ "$check" -eq 0 ]; then
    echo "tack: $root $refusal." >&2
    echo "Update it yourself with: cd \"$root\" && git pull && ./install.sh" >&2
    echo "or move it to $latest anyway with: tack update --force" >&2
    exit 1
  fi

  if git -C "$root" merge-base --is-ancestor "$latest" HEAD; then
    echo "tack in $root ($current) already includes $latest; nothing to update."
    exit 0
  fi

  if [ "$check" -eq 1 ]; then
    echo "tack $current is installed in $root; $latest is available."
    [ -z "$base" ] || changelog_since "$root" "$latest" "$base"
    if [ -n "$refusal" ]; then echo "The checkout $refusal: update it with git pull && ./install.sh, or tack update --force."
    else echo "Run tack update to install it."; fi
    exit 0
  fi

  git -C "$root" -c advice.detachedHead=false checkout --quiet "$latest" \
    || { echo "tack: cannot check out $latest in $root; nothing was reinstalled" >&2; exit 1; }
  echo "Updated tack in $root: $current -> $latest"
  [ -z "$base" ] || changelog_since "$root" "$latest" "$base"
  bash "$root/install.sh" ${install_args[@]+"${install_args[@]}"}
  exit
}

main "$@"
