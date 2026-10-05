#!/usr/bin/env bash
# `tack shots`: before and after screenshots of a visual change, at mobile and desktop widths.
#   shots [--before|--after] [--name NAME] URL...   capture each URL (default --after)
#   shots --index                                   rebuild index.html (after writing score.md)
#   shots --dir                                     print this branch's folder
# Files go to <repo>/.tack-screenshots/<date>-<branch>/{before,after}/<name>-{mobile,desktop}.png
# with an index.html showing them side by side; the folder ignores itself in git. (.tack is the
# shared marker file, so the screenshots cannot live under it.) A branch keeps the folder of its
# first capture, so before and after pair up across days. A page is named by its path and query,
# not its host, so before on one port and after on another still pair; --name overrides it.
# Playwright's CLI captures them: the project's own (npx --no-install playwright), or the
# command in TACK_PLAYWRIGHT (split on spaces). The mobile shot is a 390x844 viewport, not a
# full device emulation.
# Usage: lib/shots.sh TACK_ROOT [OPTIONS] [URL...]
set -u

root="$1"
shift
usage_error() { printf 'tack: %s (see --help)\n' "$1" >&2; exit 2; }

phase='' name='' action=capture urls=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --before | --after)
      [ -z "$phase" ] || [ "$phase" = "${1#--}" ] || usage_error 'shots takes --before or --after, not both'
      phase="${1#--}" ;;
    --name) [ "$#" -ge 2 ] || usage_error 'shots --name needs a value'; name="$2"; shift ;;
    --index) action=index ;;
    --dir) action=dir ;;
    -*) usage_error "unknown option for shots: $1" ;;
    *) urls+=("$1") ;;
  esac
  shift
done
phase="${phase:-after}"
if [ "$action" != capture ] && [ "${#urls[@]}" -gt 0 ]; then usage_error "shots --$action takes no URL"; fi

repo="$(git rev-parse --show-toplevel 2>/dev/null)" || usage_error 'shots needs a git repository'
# symbolic-ref also names a branch with no commits yet.
branch="$(git symbolic-ref --short -q HEAD 2>/dev/null)" || branch="$(git rev-parse --short HEAD 2>/dev/null)" || branch=detached
branch="$(printf '%s' "$branch" | tr -c 'A-Za-z0-9._-' '-')"
base="$repo/.tack-screenshots"
dir="$base/$(date +%Y-%m-%d)-$branch"
for existing in "$base"/????-??-??-"$branch"; do
  # Dates sort as text, so the last match is the newest folder of this branch.
  [ ! -d "$existing" ] || dir="$existing"
done

index() { python3 "$root/lib/shots-index.py" "$dir" || { echo "tack: cannot write $dir/index.html" >&2; exit 1; }; }

case "$action" in
  dir) printf '%s\n' "$dir"; exit 0 ;;
  index) [ -d "$dir" ] || { echo "tack: no screenshots yet in $dir" >&2; exit 1; }; index; exit 0 ;;
esac
[ "${#urls[@]}" -gt 0 ] || usage_error 'shots needs at least one URL'
if [ -n "$name" ] && [ "${#urls[@]}" -gt 1 ]; then usage_error 'shots --name takes one URL'; fi

# A file-safe name: letters, digits, dots, dashes and underscores only, never a path.
clean() { printf '%s' "$1" | tr -c 'A-Za-z0-9._' '-' | tr -s '-' | sed 's/^[-.]*//; s/-*$//' | cut -c1-80; }
slug() {
  local rest="${1#*://}" path
  case "$1" in
    file://*) path="$(basename "${rest%%[?#]*}")"; path="${path%.*}" ;;
    *://*) path="${rest#*/}"; [ "$path" != "$rest" ] || path=''; path="${path%%#*}" ;;
    *) path="$1" ;;
  esac
  path="$(clean "$path")"
  printf '%s' "${path:-index}"
}

shots=()
for url in "${urls[@]}"; do
  shot="$(clean "${name:-$(slug "$url")}")"
  shot="${shot:-page}"
  case " ${shots[*]+"${shots[*]}"} " in *" $shot "*) usage_error "two URLs are both named '$shot'; capture them separately with --name" ;; esac
  shots+=("$shot")
done

set -f
# shellcheck disable=SC2206 # TACK_PLAYWRIGHT may be a command with arguments.
playwright=(${TACK_PLAYWRIGHT:-npx --no-install playwright})
set +f
if [ "${#playwright[@]}" -eq 0 ] || ! (cd "$repo" && "${playwright[@]}" --version) >/dev/null 2>&1; then
  echo "tack: Playwright is not available. Install it in the project (npm i -D playwright && npx playwright install chromium) or set TACK_PLAYWRIGHT to its command." >&2
  exit 1
fi

mkdir -p "$dir/$phase" || { echo "tack: cannot write $dir" >&2; exit 1; }
[ -f "$base/.gitignore" ] || printf '# Written by tack shots: local screenshots, never committed.\n*\n' > "$base/.gitignore"
errors="$(mktemp "${TMPDIR:-/tmp}/tack-shots.XXXXXX")" || exit 1
trap 'rm -f "$errors"' EXIT

# Playwright's most useful line is its error, not the last one; colours are dropped.
reason() {
  local plain
  plain="$(tr -d '\033' < "$1" | sed 's/\[[0-9;]*m//g' | grep -v '^[[:space:]]*$')"
  printf '%s\n' "$plain" | grep -iE 'error' | head -n 1 | grep . || printf '%s\n' "$plain" | tail -n 1
}

status=0 k=0
for url in "${urls[@]}"; do
  shot="${shots[$k]}"
  k=$((k + 1))
  for size in mobile:390,844 desktop:1440,900; do
    file="$dir/$phase/$shot-${size%%:*}.png"
    # A failed capture must not leave an older screenshot behind as if it were current.
    rm -f "$file"
    if (cd "$repo" && "${playwright[@]}" screenshot --full-page --viewport-size="${size#*:}" "$url" "$file") >/dev/null 2>"$errors" && [ -s "$file" ]; then
      printf '%s\n' "$file"
    else
      printf 'tack: could not capture %s at %s width: %s\n' "$url" "${size%%:*}" "$(reason "$errors")" >&2
      status=1
    fi
  done
done
index
printf 'Open %s/index.html to compare.\n' "$dir"
exit "$status"
