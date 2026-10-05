#!/usr/bin/env bash
# Guard rules for code that a shell or interpreter runs: -c strings are analysed, standard input
# is not visible and asks. Sourced by guard-bash.sh, which defines ask and analyze.

# reads_stdin PATH: succeeds for the names of standard input itself.
reads_stdin() {
  case "$1" in - | /dev/stdin | /dev/fd/0 | /proc/self/fd/0) return 0 ;; esac
  return 1
}

# A shell runs the string after -c, a script file, or whatever reaches its standard input: a
# heredoc, a here-string or a download piped into it (curl ... | bash).
check_shell() {
  local args=("$@") k=0 n=$# string=0 stdin=0 script=0 a
  while [ "$k" -lt "$n" ]; do
    a="${args[$k]}"
    case "$a" in
      --version | --help) return 0 ;;
      -o | -O | +o | +O | --rcfile | --init-file) k=$((k + 2)); continue ;;
      --*) ;;
      -* | +*)
        # Short options combine (-euo pipefail, -ec): o and O take the next word, c a command
        # string after the options, s reads the script from standard input.
        case "$a" in *[oO]*) k=$((k + 1)) ;; esac
        case "$a" in -*c*) string=1 ;; esac
        case "$a" in -*s*) stdin=1 ;; esac ;;
      *)
        if [ "$string" -eq 1 ]; then analyze "$a"; return 0; fi
        if [ "$stdin" -eq 1 ] || reads_stdin "$a"; then break; fi
        script=1
        break ;;
    esac
    k=$((k + 1))
  done
  if [ "$string" -eq 1 ]; then ask "Missing shell command string requires review."; return 0; fi
  [ "$script" -eq 1 ] || ask "A shell reading a script from standard input (a pipe, heredoc or here-string) requires review."
}

# source or . with standard input runs whatever was piped in.
check_source() {
  if [ "$#" -eq 0 ] || reads_stdin "$1"; then
    ask "Sourcing a script from standard input (a pipe) requires review."
  fi
}

# Interpreters run inline code (visible to the guard), a script file, or standard input (not
# visible). Each lists its options that take a value, so the value is not mistaken for a script.
check_interpreter() {
  local name="$1" with_value inline benign a k=0 n
  shift
  local args=("$@")
  n=$#
  case "$name" in
    python*) with_value='-X -W -Q'; inline='-c -m'; benign='--version -V -h --help' ;;
    node) with_value='-r --require --import --loader -C --conditions'; inline='-e --eval -p --print'; benign='-v --version -h --help --test -c --check' ;;
    perl) with_value='-I -M -m'; inline='-e -E'; benign='-v --version -V -h' ;;
    ruby) with_value='-I -r -C -E'; inline='-e'; benign='-v --version -h --help' ;;
    php) with_value='-d -c -z'; inline='-r'; benign='-v --version -h --help -l -m -i' ;;
  esac
  while [ "$k" -lt "$n" ]; do
    a="${args[$k]}"
    case " $benign $inline " in *" $a "*) return 0 ;; esac
    case " $with_value " in *" $a "*) k=$((k + 2)); continue ;; esac
    if reads_stdin "$a"; then break; fi
    case "$a" in
      --*) ;;
      -?*)
        # Attached inline code such as -cprint(1) or -mpytest is visible too.
        case " $inline " in *" ${a:0:2} "*) return 0 ;; esac ;;
      *) return 0 ;;
    esac
    k=$((k + 1))
  done
  ask "$name reading code from standard input (a pipe or heredoc) requires review."
}
