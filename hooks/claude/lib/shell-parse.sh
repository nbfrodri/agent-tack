# Shell command parser for the Claude Code hooks (sourced, not executed).
#
# tokenize <command> splits a command line the way a shell would: quotes and escapes, the
# separators ; & | && || ( ) and newlines, heredocs and
# redirections. It sets:
#   TOKENS  the unquoted words, with SEP between simple commands and REDIR before redirection targets
#   SUBS    the bodies of $(…) and `…` substitutions, to be checked as commands too
# shellcheck shell=bash disable=SC2034

SEP=$'\x1f'
REDIR=$'\x1e'

# Splits a command line into TOKENS (unquoted words), with SEP between simple commands and REDIR
# before redirection targets. Command substitutions are collected in SUBS to be checked too.
tokenize_bash() {
  local s="$1" len=${#1} i=0 c tok="" has_tok=0 quote="" heredoc="" strip_tabs=0 j depth rest
  TOKENS=()
  SUBS=()

  flush() {
    if [ "$has_tok" -eq 1 ]; then TOKENS+=("$tok"); fi
    tok=""
    has_tok=0
  }

  # Reads a $( … ) or ` … ` starting at index i into SUBS and moves i to its end
  read_substitution() {
    if [ "$1" = backtick ]; then
      j=$((i + 1))
      while [ "$j" -lt "$len" ] && [ "${s:j:1}" != '`' ]; do j=$((j + 1)); done
      SUBS+=("${s:i+1:j-i-1}")
    else
      j=$((i + 2))
      depth=1
      while [ "$j" -lt "$len" ] && [ "$depth" -gt 0 ]; do
        case "${s:j:1}" in
          '(') depth=$((depth + 1)) ;;
          ')') depth=$((depth - 1)) ;;
        esac
        j=$((j + 1))
      done
      SUBS+=("${s:i+2:j-i-3}")
      j=$((j - 1))
    fi
    tok+="__subst__"
    has_tok=1
    i=$j
  }

  while [ "$i" -lt "$len" ]; do
    c="${s:i:1}"
    if [ "$quote" = "'" ]; then
      if [ "$c" = "'" ]; then quote=""; else tok+="$c"; fi
      i=$((i + 1))
      continue
    fi
    if [ "$quote" = '"' ]; then
      case "$c" in
        '"') quote="" ;;
        "\\") i=$((i + 1)); tok+="${s:i:1}" ;;
        '`') read_substitution backtick ;;
        '$')
          if [ "${s:i+1:1}" = "(" ]; then read_substitution paren; else tok+="$c"; fi
          ;;
        *) tok+="$c" ;;
      esac
      i=$((i + 1))
      continue
    fi

    case "$c" in
      "'" | '"') quote="$c"; has_tok=1 ;;
      "\\") i=$((i + 1)); tok+="${s:i:1}"; has_tok=1 ;;
      ' ' | $'\t') flush ;;
      ';' | '&' | '|' | '(' | ')')
        flush
        TOKENS+=("$SEP")
        ;;
      $'\n')
        flush
        TOKENS+=("$SEP")
        if [ -n "$heredoc" ]; then
          # Skip the heredoc body: it is data, not commands
          rest="${s:i+1}"
          if [ "$strip_tabs" -eq 1 ]; then
            rest="${rest%%$'\n'$'\t'"$heredoc"*}"
          fi
          rest="${rest%%$'\n'"$heredoc"*}"
          if [ "${s:i+1:${#heredoc}}" = "$heredoc" ]; then rest=""; fi
          i=$((i + 1 + ${#rest} + ${#heredoc}))
          heredoc=""
          strip_tabs=0
        fi
        ;;
      '`') read_substitution backtick ;;
      '$')
        if [ "${s:i+1:1}" = "(" ]; then
          read_substitution paren
        else
          tok+="$c"
          has_tok=1
        fi
        ;;
      '<')
        flush
        if [ "${s:i+1:1}" = "<" ] && [ "${s:i+2:1}" != "<" ]; then
          i=$((i + 2))
          if [ "${s:i:1}" = "-" ]; then strip_tabs=1; i=$((i + 1)); fi
          while [ "${s:i:1}" = " " ]; do i=$((i + 1)); done
          heredoc=""
          while [ "$i" -lt "$len" ]; do
            c="${s:i:1}"
            case "$c" in
              ' ' | $'\t' | $'\n' | ';' | '&' | '|' | '<' | '>') break ;;
              "'" | '"' | "\\") ;;
              *) heredoc+="$c" ;;
            esac
            i=$((i + 1))
          done
          continue
        fi
        TOKENS+=("$REDIR")
        ;;
      '>')
        flush
        while [ "${s:i+1:1}" = ">" ] || [ "${s:i+1:1}" = "&" ]; do i=$((i + 1)); done
        TOKENS+=("$REDIR")
        ;;
      *) tok+="$c"; has_tok=1 ;;
    esac
    i=$((i + 1))
  done
  flush
}

case "${BASH_SOURCE[0]}" in */*) SHELL_PARSE_HELPER="${BASH_SOURCE[0]%/*}/shell-parse.py" ;; *) SHELL_PARSE_HELPER=shell-parse.py ;; esac

tokenize() {
  TOKENS=()
  SUBS=()
  PARSE_ERROR=""
  if command -v "${TACK_PYTHON:-python3}" >/dev/null 2>&1; then
    local kind value complete=0
    while IFS= read -r -d '' kind && IFS= read -r -d '' value; do
      case "$kind" in
        T) TOKENS+=("$value") ;;
        S) SUBS+=("$value") ;;
        E) PARSE_ERROR="$value" ;;
        Z) complete=1 ;;
      esac
    done < <(printf '%s' "$1" | "${TACK_PYTHON:-python3}" -S "$SHELL_PARSE_HELPER" 2>/dev/null)
    [ "$complete" -eq 1 ] || PARSE_ERROR="Shell parser failed; review the complete command."
    return 0
  fi
  if [ "${#1}" -gt 1024 ]; then
    PARSE_ERROR="Command size exceeds the Bash fallback limit without Python; review the complete command."
    return 0
  fi
  # The fallback has no full shell grammar; every uncertain input must be reviewed.
  case "$1" in
    *'<<'* | *\$* | *'`'* | *'('* | *')'* | *'{'* | *'}'*)
      PARSE_ERROR="Shell syntax requires review because Python is unavailable."
      return 0 ;;
  esac
  tokenize_bash "$1"
  local token start=1
  for token in "${TOKENS[@]+"${TOKENS[@]}"}"; do
    if [ "$token" = "$SEP" ]; then start=1; continue; fi
    if [ "$start" -eq 1 ]; then
      case "$token" in
        '!' | if | then | elif | else | fi | for | while | until | do | done | case | 'esac' | select | function)
          PARSE_ERROR="Shell control flow requires review because Python is unavailable."
          return 0 ;;
      esac
    fi
    start=0
  done
}
