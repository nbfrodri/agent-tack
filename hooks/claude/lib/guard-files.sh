#!/usr/bin/env bash
# Guard rules for deleting files: path resolution, rm -r and find -delete. Sourced by
# guard-bash.sh, which defines deny, ask, ask_local, normalize_abs, $cwd and $HOME_DIR.
# shellcheck disable=SC2034,SC2154 # The decision state and $cwd are shared with guard-bash.sh.

# resolve_path PATH: prints PATH made absolute against $cwd with ".", ".." and a leading ~ or
# $HOME resolved lexically (the disk is not read); glob characters are kept as typed. Prints
# nothing for a path whose value is only known when the shell runs it: substitutions, other
# variables, brace expansion, backticks or another user's home (~user).
resolve_path() {
  local path="$1"
  # shellcheck disable=SC2016 # $HOME is matched as typed, not expanded.
  case "$path" in
    *__subst__* | *'{'* | *'}'* | *'`'* | '~'[!/]*) return 0 ;;
    *'$'*) case "$path" in '$HOME' | '$HOME/'* | '${HOME}' | '${HOME}/'*) ;; *) return 0 ;; esac ;;
  esac
  # shellcheck disable=SC2016,SC2088
  case "$path" in
    '~' | '$HOME' | '${HOME}') path="$HOME" ;;
    '~/'*) path="$HOME/${path#'~/'}" ;;
    '$HOME/'*) path="$HOME/${path#'$HOME/'}" ;;
    '${HOME}/'*) path="$HOME/${path#'${HOME}/'}" ;;
    /*) ;;
    *) path="$cwd/$path" ;;
  esac
  normalize_abs "$path"
}

# fixed_part PATH: the folder a glob path starts from (the path itself when it has no glob).
fixed_part() {
  local path="$1"
  case "$path" in *'*'* | *'?'* | *'['*) ;; *) printf '%s\n' "$path"; return ;; esac
  path="${path%%[*?[]*}"
  path="${path%/*}"
  printf '%s\n' "${path:-/}"
}

# Deny a recursive delete of the filesystem root, of HOME or of any folder that holds HOME.
too_broad() {
  case "$HOME_DIR/" in "${1%/}/"*) return 0 ;; esac
  return 1
}

# project_dir: the working directory, or a placeholder when it is HOME or above it (no project).
project_dir() {
  if too_broad "${cwd%/}"; then printf '//no-project\n'; else printf '%s\n' "${cwd%/}"; fi
}

# place_of REAL: project-root, project, home (outside the project), temp or outside. A temp
# folder itself (/tmp) is outside; only what is inside it counts as temp.
place_of() {
  local real="${1%/}" project tmp="${TMPDIR:-/tmp}"
  project="$(project_dir)"
  tmp="${tmp%/}"
  case "$real" in
    "$project") echo project-root ;;
    "$project"/*) echo project ;;
    # Inside HOME but outside the project is never temp, even when HOME sits under /tmp.
    "${HOME_DIR%/}"/*) echo home ;;
    /tmp/* | /var/tmp/* | "$tmp"/*) echo temp ;;
    *) echo outside ;;
  esac
}

# judge_delete TARGET WHAT: the shared decision for rm -r and find -delete on one target.
judge_delete() {
  # A third argument "root-ok" accepts the project root itself (find . -name x -delete).
  local t="$1" what="$2" root="${3:-}" real fixed
  real="$(resolve_path "$t")"
  if [ -z "$real" ]; then
    ask "$what of '$t', which the guard cannot resolve before the shell expands it: confirm what it deletes."
    return
  fi
  fixed="$(fixed_part "$real")"
  if too_broad "$real" || too_broad "$fixed"; then
    # find narrows what it deletes with its tests (-name ...), so a broad start asks rather than denies.
    [ "$root" = root-ok ] || deny "$what of '$t' is too broad. Delete specific paths instead."
    ask "$what outside the project directory: $t"
    return
  fi
  # Losing .git loses every commit not pushed; no mode waives that question.
  case "$real" in
    */.git | */.git/*) ask "$what of the git history ($t): commits that were not pushed are lost." ;;
  esac
  case "$(place_of "$fixed")" in
    project-root) [ "$root" = root-ok ] || ask_local "$what of everything in the current directory ($t)." ;;
    project | temp) ;;
    *) ask "$what outside the project directory: $t" ;;
  esac
}

# find ... -delete, or -exec rm, removes what matches under its start paths.
check_find() {
  local args=("$@") i=0 n=$# starts=() deletes=0 exec_command start
  # Global options come before the start paths: -H, -L, -P, -D debugopts, -Olevel.
  while [ "$i" -lt "$n" ]; do
    case "${args[$i]}" in
      -H | -L | -P | -O*) i=$((i + 1)) ;;
      -D) i=$((i + 2)) ;;
      *) break ;;
    esac
  done
  while [ "$i" -lt "$n" ]; do
    case "${args[$i]}" in -* | '(' | '!' | ')') break ;; esac
    starts+=("${args[$i]}")
    i=$((i + 1))
  done
  while [ "$i" -lt "$n" ]; do
    case "${args[$i]}" in
      -delete) deletes=1 ;;
      -exec | -execdir | -ok | -okdir)
        exec_command="${args[$((i + 1))]:-}"
        case "${exec_command##*/}" in rm | unlink | shred) deletes=1 ;; esac ;;
    esac
    i=$((i + 1))
  done
  [ "$deletes" -eq 1 ] || return 0
  [ "${#starts[@]}" -gt 0 ] || starts=(.)
  for start in "${starts[@]}"; do
    judge_delete "$start" "find deleting" root-ok
  done
}

check_rm() {
  local recursive=0 after_dashdash=0 targets=() a t
  for a in "$@"; do
    if [ "$after_dashdash" -eq 1 ]; then targets+=("$a"); continue; fi
    case "$a" in
      --) after_dashdash=1 ;;
      --no-preserve-root) deny "rm --no-preserve-root is never needed." ;;
      --recursive | -r | -R) recursive=1 ;;
      --*) ;;
      -*) case "$a" in *[rR]*) recursive=1 ;; esac ;;
      *) targets+=("$a") ;;
    esac
  done
  [ "$recursive" -eq 1 ] || return 0

  # Targets are matched literally as typed (~, $HOME), so these patterns must not expand
  # shellcheck disable=SC2016,SC2088
  for t in "${targets[@]+"${targets[@]}"}"; do
    case "$t" in
      '/' | '/*' | '/.' | '~' | '~/' | '~/*' | '$HOME' | '$HOME/' | '$HOME/*' | '${HOME}' | '${HOME}/' | '${HOME}/*' | '..' | '../' | '../*' | "$HOME" | "$HOME/")
        deny "Recursive delete of '$t' is too broad. Delete specific paths instead." ;;
    esac
    judge_delete "$t" "Recursive delete"
  done
}
