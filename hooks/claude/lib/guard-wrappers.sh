#!/usr/bin/env bash
# Guard rules for wrappers that run the rest of the line as a command (sudo, env, timeout, xargs...)
# and for environment assignments before it. Sourced by guard-bash.sh, which defines ask,
# check_command, tokenize and the analysis limits.
# The skip_* functions work on the caller's words array and index i (bash's dynamic scope): they
# move i past the wrapper and its options, and return 1 when the command needs no further checks.
# shellcheck disable=SC2034,SC2154 # words and i belong to check_command; the rest is shared with guard-bash.sh.

# skip_wrappers: moves i to the command that the assignments and wrappers at words[i] run.
skip_wrappers() {
  local w
  while [ "$i" -lt "${#words[@]}" ]; do
    w="${words[$i]}"
    # An assignment is recognised by its name: its value may hold slashes (X=a/b).
    case "$w" in
      [A-Za-z_]*=*)
        case "${w%%=*}" in
          *[!A-Za-z0-9_]*) ;;
          *)
            case "${w%%=*}" in GH_REPO | GH_HOST) GH_REPO_FROM_ENV=1 ;; esac
            i=$((i + 1))
            continue ;;
        esac ;;
    esac
    case "${w##*/}" in
      *=*) case "$w" in -*) break ;; esac; i=$((i + 1)) ;;
      sudo | doas) skip_sudo || return 1 ;;
      command | exec | nohup | time | builtin) skip_command_wrapper || return 1 ;;
      env) skip_env || return 1 ;;
      nice | stdbuf | ionice) skip_nice ;;
      timeout) skip_timeout ;;
      xargs) skip_xargs ;;
      *) break ;;
    esac
  done
}

skip_sudo() {
  i=$((i + 1))
  while [ "$i" -lt "${#words[@]}" ]; do
    case "${words[$i]}" in
      --) i=$((i + 1)); break ;;
      -u | -g | -h | -p | -C | -T | -R | -D | -a | --user | --group | --host | --prompt | --close-from | --command-timeout | --chroot | --chdir)
        i=$((i + 2)) ;;
      -n | -E | -H | -S | -b | -k | -K | -A | --non-interactive | --preserve-env | --set-home | --stdin | --background | --reset-timestamp)
        i=$((i + 1)) ;;
      --user=* | --group=* | --host=* | --prompt=* | --preserve-env=* | --chdir=* | --chroot=* | -u?* | -g?*)
        i=$((i + 1)) ;;
      -*) ask "Unsupported privilege-wrapper option requires review."; return 1 ;;
      *=*) i=$((i + 1)) ;;
      *) break ;;
    esac
  done
}

skip_command_wrapper() {
  i=$((i + 1))
  while [ "$i" -lt "${#words[@]}" ]; do
    case "${words[$i]}" in
      -- | -p) i=$((i + 1)) ;;
      -v | -V) return 1 ;;
      -*) ask "Unsupported command-wrapper option requires review."; return 1 ;;
      *) break ;;
    esac
  done
}

# env -S splits its string into words, which are checked as their own command.
skip_env() {
  i=$((i + 1))
  while [ "$i" -lt "${#words[@]}" ]; do
    case "${words[$i]}" in
      --) i=$((i + 1)); break ;;
      -S | --split-string)
        if [ $((i + 1)) -ge "${#words[@]}" ]; then
          ask "Missing env split string requires review."; return 1
        fi
        check_env_split "${words[$((i + 1))]}" "${words[@]:$((i + 2))}"
        return 1 ;;
      -S?*) check_env_split "${words[$i]#-S}" "${words[@]:$((i + 1))}"; return 1 ;;
      --split-string=*) check_env_split "${words[$i]#--split-string=}" "${words[@]:$((i + 1))}"; return 1 ;;
      -u | --unset | -C | --chdir) i=$((i + 2)) ;;
      -i | --ignore-environment | -0 | --null | --unset=* | --chdir=*) i=$((i + 1)) ;;
      -*) ask "Unsupported env option requires review."; return 1 ;;
      *=*) i=$((i + 1)) ;;
      *) break ;;
    esac
  done
}

skip_nice() {
  i=$((i + 1))
  while [ "$i" -lt "${#words[@]}" ]; do
    case "${words[$i]}" in
      -u | -n | -c | -C | -o | -e) i=$((i + 2)) ;;
      -*) i=$((i + 1)) ;;
      *=*) i=$((i + 1)) ;;
      *) break ;;
    esac
  done
}

# timeout's first word after its options is the duration, not the command.
skip_timeout() {
  i=$((i + 1))
  while [ "$i" -lt "${#words[@]}" ]; do
    case "${words[$i]}" in
      -s | -k | --signal | --kill-after) i=$((i + 2)) ;;
      -*) i=$((i + 1)) ;;
      *) i=$((i + 1)); break ;;
    esac
  done
}

skip_xargs() {
  i=$((i + 1))
  while [ "$i" -lt "${#words[@]}" ]; do
    case "${words[$i]}" in
      -I | -n | -L | -P | -d | -E | -s | -a) i=$((i + 2)) ;;
      -*) i=$((i + 1)) ;;
      *) break ;;
    esac
  done
}

check_env_split() {
  local split="$1" token TOKENS SUBS PARSE_ERROR
  shift
  if [ "$DEPTH" -ge 4 ]; then
    ask "Shell analysis depth limit exceeded; review the complete command."
    return 0
  fi
  case "$split" in
    *\\* | *'$'* | *'`'*) ask "Unsupported env split-string expansion requires review."; return 0 ;;
  esac
  tokenize "$split"
  if [ -n "$PARSE_ERROR" ]; then ask "$PARSE_ERROR"; return 0; fi
  for token in "${TOKENS[@]+"${TOKENS[@]}"}"; do
    case "$token" in
      "$SEP" | "$REDIR") ask "Unsupported env split-string syntax requires review."; return 0 ;;
    esac
  done
  DEPTH=$((DEPTH + 1))
  check_command env "${TOKENS[@]+"${TOKENS[@]}"}" "$@"
  DEPTH=$((DEPTH - 1))
}
