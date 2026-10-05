#!/usr/bin/env bash
# `tack shots`: before and after screenshots of a visual change, at mobile and desktop widths.
#   shots [--before|--after] [--name NAME] URL...   capture each URL (default --after)
#   shots --index                                   rebuild index.html (after writing score.md)
#   shots --dir                                     print this branch's folder for today
# Files go to <repo>/.tack-screenshots/<date>-<branch>/{before,after}/<name>-{mobile,desktop}.png
# with an index.html showing them side by side; the folder ignores itself in git. (.tack is the
# shared marker file, so the screenshots cannot live under it.)
# Playwright's CLI captures them: the project's own (npx --no-install playwright), or the
# command in TACK_PLAYWRIGHT.
# Usage: lib/shots.sh TACK_ROOT [OPTIONS] [URL...]
set -u

root="$1"
shift
usage_error() { printf 'tack: %s (see --help)\n' "$1" >&2; exit 2; }

phase=after name='' action=capture urls=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --before) phase=before ;;
    --after) phase=after ;;
    --name) [ "$#" -ge 2 ] || usage_error 'shots --name needs a value'; name="$2"; shift ;;
    --index) action=index ;;
    --dir) action=dir ;;
    -*) usage_error "unknown option for shots: $1" ;;
    *) urls+=("$1") ;;
  esac
  shift
done

repo="$(git rev-parse --show-toplevel 2>/dev/null)" || usage_error 'shots needs a git repository'
# symbolic-ref also names a branch with no commits yet.
branch="$(git symbolic-ref --short -q HEAD 2>/dev/null)" || branch="$(git rev-parse --short HEAD 2>/dev/null)" || branch=detached
base="$repo/.tack-screenshots"
dir="$base/$(date +%Y-%m-%d)-$(printf '%s' "$branch" | tr -c 'A-Za-z0-9._-' '-')"

index() { python3 "$root/lib/shots-index.py" "$dir" || { echo "tack: cannot write $dir/index.html" >&2; exit 1; }; }

case "$action" in
  dir) printf '%s\n' "$dir"; exit 0 ;;
  index) [ -d "$dir" ] || { echo "tack: no screenshots yet in $dir" >&2; exit 1; }; index; exit 0 ;;
esac
[ "${#urls[@]}" -gt 0 ] || usage_error 'shots needs at least one URL'
if [ -n "$name" ] && [ "${#urls[@]}" -gt 1 ]; then usage_error 'shots --name takes one URL'; fi

# shellcheck disable=SC2206 # TACK_PLAYWRIGHT may be a command with arguments.
playwright=(${TACK_PLAYWRIGHT:-npx --no-install playwright})
if ! (cd "$repo" && "${playwright[@]}" --version) >/dev/null 2>&1; then
  echo "tack: Playwright is not available. Install it in the project (npm i -D playwright && npx playwright install chromium) or set TACK_PLAYWRIGHT to its command." >&2
  exit 1
fi

mkdir -p "$dir/$phase" || { echo "tack: cannot write $dir" >&2; exit 1; }
[ -f "$base/.gitignore" ] || printf '# Written by tack shots: local screenshots, never committed.\n*\n' > "$base/.gitignore"

slug() {
  local path="${1#*://}"
  path="${path%%[?#]*}"
  case "$1" in file://*) path="$(basename "$path")"; path="${path%.*}" ;; esac
  path="$(printf '%s' "$path" | tr -c 'A-Za-z0-9' '-' | tr -s '-')"
  path="${path#-}"
  printf '%s' "${path%-}" | cut -c1-60
}

status=0
for url in "${urls[@]}"; do
  shot="${name:-$(slug "$url")}"
  [ -n "$shot" ] || shot=page
  for size in mobile:390,844 desktop:1440,900; do
    file="$dir/$phase/$shot-${size%%:*}.png"
    if (cd "$repo" && "${playwright[@]}" screenshot --full-page --viewport-size="${size#*:}" "$url" "$file") >/dev/null 2>&1 && [ -s "$file" ]; then
      printf '%s\n' "$file"
    else
      echo "tack: could not capture $url at ${size%%:*} width" >&2
      status=1
    fi
  done
done
index
printf 'Open %s/index.html to compare.\n' "$dir"
exit "$status"
