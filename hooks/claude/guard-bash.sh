#!/usr/bin/env bash
# Claude Code PreToolUse hook for Bash.
# Denies commands that are catastrophic or bypass safety nets, and asks for confirmation
# for commands that destroy work or data. Everything else is left to the normal permission flow.
#
# The command is parsed like a shell would: quotes, escapes, separators, heredoc bodies,
# $(…)/backticks and `bash -c`/`eval` strings, so quoted text is never mistaken for commands
# and quoted targets are still recognised.
#
# Input: the hook JSON on stdin. Output: a permission decision as JSON, or nothing.
# Fails open (allows) if the input can't be parsed, so a broken hook never blocks work.
set -u

input="$(cat)"

json_field() {
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$input" | jq -r "$1 // empty" 2>/dev/null
  elif command -v python3 >/dev/null 2>&1; then
    printf '%s' "$input" | python3 -c '
import json, sys
data = json.load(sys.stdin)
for key in sys.argv[1].lstrip(".").split("."):
    data = data.get(key) if isinstance(data, dict) else None
print(data if isinstance(data, str) else "")
' "$1" 2>/dev/null
  fi
}

emit() {
  local decision="$1" reason="$2"
  if command -v jq >/dev/null 2>&1; then
    jq -cn --arg d "$decision" --arg r "$reason" \
      '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: $d, permissionDecisionReason: $r}}'
  else
    reason="${reason//\\/\\\\}"
    reason="${reason//\"/\\\"}"
    reason="$(printf '%s' "$reason" | tr -d '\000-\037')"
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"%s","permissionDecisionReason":"%s"}}\n' \
      "$decision" "$reason"
  fi
}

ASK_REASON=""
deny() { emit deny "$1"; exit 0; }
# Remember the first reason to ask; a later deny in the same command still wins
ask() { [ -n "$ASK_REASON" ] || ASK_REASON="$1"; }

command="$(json_field .tool_input.command)"
cwd="$(json_field .cwd)"
[ -n "$command" ] || exit 0
[ -n "$cwd" ] && [ -d "$cwd" ] || cwd="$PWD"

SEP=$'\x1f'
REDIR=$'\x1e'

# Splits a command line into TOKENS (unquoted words), with SEP between simple commands and REDIR
# before redirection targets. Command substitutions are collected in SUBS to be checked too.
tokenize() {
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

current_branch() {
  git -C "$cwd" branch --show-current 2>/dev/null
}

is_main() {
  case "$1" in
    main | master | refs/heads/main | refs/heads/master) return 0 ;;
  esac
  return 1
}

check_git() {
  local sub="" rest=() skip_next=0 a prev=""
  for a in "$@"; do
    if [ "$skip_next" -eq 1 ]; then
      skip_next=0
      case "$prev" in
        -c) case "$(printf '%s' "$a" | tr '[:upper:]' '[:lower:]')" in
              core.hookspath=*) deny "Overriding core.hooksPath disables the git hooks that enforce the user's rules." ;;
            esac ;;
      esac
      continue
    fi
    if [ -z "$sub" ]; then
      case "$a" in
        -C | -c | --git-dir | --work-tree | --namespace | --config-env) prev="$a"; skip_next=1 ;;
        --config-env=*) case "$(printf '%s' "$a" | tr '[:upper:]' '[:lower:]')" in
                          *core.hookspath*) deny "Overriding core.hooksPath disables the git hooks that enforce the user's rules." ;;
                        esac ;;
        -*) ;;
        *) sub="$a" ;;
      esac
    else
      rest+=("$a")
    fi
  done

  local joined=" ${rest[*]+"${rest[*]}"} " r
  case "$sub" in
    commit) check_git_commit "${rest[@]+"${rest[@]}"}" ;;
    push) check_git_push "${rest[@]+"${rest[@]}"}" ;;
    config)
      case "$(printf '%s' "$joined" | tr '[:upper:]' '[:lower:]')" in
        *core.hookspath*)
          case "$joined" in
            *" --get"* | *" -l "* | *" --list "*) ;;
            *) deny "Changing core.hooksPath disables the git hooks that enforce the user's rules." ;;
          esac ;;
      esac
      ;;
    reset)
      case "$joined" in *" --hard"*) ask "git reset --hard discards uncommitted changes permanently." ;; esac
      ;;
    clean)
      for r in "${rest[@]+"${rest[@]}"}"; do
        case "$r" in
          --force) ask "git clean -f deletes untracked files permanently." ;;
          --*) ;;
          -*f*) ask "git clean -f deletes untracked files permanently." ;;
        esac
      done
      ;;
    restore)
      case "$joined" in
        *" --worktree "* | *" -W "*) ask "git restore discards uncommitted changes in the working tree." ;;
        *" --staged "* | *" -S "*) ;;
        *) ask "git restore discards uncommitted changes in the working tree." ;;
      esac
      ;;
    checkout)
      case "$joined" in
        *" -- "* | *" . "* | *" -f "* | *" --force "*) ask "This checkout discards uncommitted changes." ;;
      esac
      ;;
    switch)
      case "$joined" in
        *" -f "* | *" --force "* | *" --discard-changes "*) ask "This switch discards uncommitted changes." ;;
      esac
      ;;
    branch)
      for r in "${rest[@]+"${rest[@]}"}"; do
        case "$r" in
          --*) ;;
          -*D*) ask "Force-deleting a branch can lose unmerged commits." ;;
        esac
      done
      case "$joined" in
        *" --delete "*" --force "* | *" --force "*" --delete "* | *" -d "*" -f "* | *" -d --force "*)
          ask "Force-deleting a branch can lose unmerged commits." ;;
      esac
      ;;
    stash)
      case "$joined" in *" clear "* | *" drop "*) ask "This permanently deletes stashed changes." ;; esac
      ;;
    filter-branch | filter-repo)
      ask "This rewrites the whole repository history."
      ;;
  esac
}

check_git_commit() {
  local a letters k letter skip_next=0 rest
  for a in "$@"; do
    if [ "$skip_next" -eq 1 ]; then skip_next=0; continue; fi
    case "$a" in
      --) break ;;
      --no-verify) deny "--no-verify skips the git hooks that enforce commit conventions. Fix the reported problem instead." ;;
      --message | --file | --reuse-message | --reedit-message | --author | --date | --template | --trailer | --cleanup | --fixup | --squash)
        skip_next=1 ;;
      --*) ;;
      -*)
        # Short options can be combined (-am, -nm); m, F, C, c and t take the rest as their value
        letters="${a#-}"
        k=0
        while [ "$k" -lt "${#letters}" ]; do
          letter="${letters:k:1}"
          case "$letter" in
            n) deny "git commit -n is --no-verify: it skips the git hooks that enforce commit conventions." ;;
            m | F | C | c | t)
              rest="${letters:k+1}"
              [ -z "$rest" ] && skip_next=1
              break ;;
          esac
          k=$((k + 1))
        done
        ;;
    esac
  done
}

check_git_push() {
  local force=0 delete=0 targets_main=0 refspecs=0 positional=0 a dest current
  for a in "$@"; do
    case "$a" in
      --no-verify) deny "--no-verify skips the git hooks that protect main. Fix the reported problem instead." ;;
      --mirror) deny "git push --mirror can overwrite or delete every branch on the remote, including main." ;;
      --force | --force-with-lease | --force-with-lease=* | --force-if-includes) force=1 ;;
      --delete) delete=1 ;;
      --*) ;;
      -*)
        case "$a" in *f*) force=1 ;; esac
        case "$a" in *d*) delete=1 ;; esac
        ;;
      *)
        positional=$((positional + 1))
        # The first positional argument is the remote; the rest are refspecs
        [ "$positional" -ge 2 ] || continue
        refspecs=$((refspecs + 1))
        case "$a" in +*) force=1 ;; :*) delete=1 ;; esac
        dest="${a#+}"
        dest="${dest##*:}"
        if [ "$dest" = "HEAD" ]; then dest="$(current_branch)"; fi
        is_main "$dest" && targets_main=1
        ;;
    esac
  done
  if [ "$force" -eq 1 ] || [ "$delete" -eq 1 ]; then
    if [ "$targets_main" -eq 1 ]; then
      deny "Force-pushing or deleting main/master is not allowed. Use git revert to undo published commits."
    fi
    if [ "$refspecs" -eq 0 ]; then
      current="$(current_branch)"
      is_main "$current" && deny "Force-pushing the current branch ($current) is not allowed. Use git revert to undo published commits."
    fi
    ask "This push rewrites or deletes history on the remote. Confirm the branch is yours and not shared."
  fi
}

check_rm() {
  local recursive=0 after_dashdash=0 targets=() a t real
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
      '.' | './' | '*' | './*') ask "Recursive delete of everything in the current directory ($t)." ;;
      /*)
        real="${t%/}"
        case "$real" in
          "$cwd"/* | /tmp/* | /var/tmp/* | "${TMPDIR:-/tmp}"/*) ;;
          *) ask "Recursive delete outside the project directory: $t" ;;
        esac
        ;;
      '~/'* | '$HOME/'* | '${HOME}/'* | "$HOME"/*)
        ask "Recursive delete outside the project directory: $t" ;;
    esac
  done
}

check_database() {
  local joined="$1" upper
  upper="$(printf '%s' "$joined" | tr '[:lower:]' '[:upper:]')"
  case "$upper" in
    *"DROP DATABASE"* | *"DROP SCHEMA"* | *"DROP TABLE"* | *"TRUNCATE "*)
      ask "This drops or truncates database objects. Confirm it targets a local/dev database." ;;
  esac
  case "$joined" in
    *dropDatabase* | *"deleteMany({})"*)
      ask "This deletes database data. Confirm it targets a local/dev database." ;;
  esac
}

# Checks one simple command given as words
check_command() {
  local words=() w skip_redir=0 i=0 cmd base
  for w in "$@"; do
    if [ "$skip_redir" -eq 1 ]; then skip_redir=0; continue; fi
    if [ "$w" = "$REDIR" ]; then skip_redir=1; continue; fi
    words+=("$w")
  done
  [ "${#words[@]}" -gt 0 ] || return 0

  # Skip env assignments and wrappers that run the rest as a command
  while [ "$i" -lt "${#words[@]}" ]; do
    w="${words[$i]}"
    case "$w" in
      *=*) case "$w" in -*) break ;; esac; i=$((i + 1)) ;;
      sudo | doas | command | exec | nohup | time | builtin) i=$((i + 1)) ;;
      env | nice | stdbuf | ionice)
        i=$((i + 1))
        while [ "$i" -lt "${#words[@]}" ]; do
          case "${words[$i]}" in
            -u | -n | -c | -C | -o | -e) i=$((i + 2)) ;;
            -*) i=$((i + 1)) ;;
            *=*) i=$((i + 1)) ;;
            *) break ;;
          esac
        done
        ;;
      timeout)
        i=$((i + 1))
        while [ "$i" -lt "${#words[@]}" ]; do
          case "${words[$i]}" in
            -s | -k | --signal | --kill-after) i=$((i + 2)) ;;
            -*) i=$((i + 1)) ;;
            *) i=$((i + 1)); break ;;
          esac
        done
        ;;
      xargs)
        i=$((i + 1))
        while [ "$i" -lt "${#words[@]}" ]; do
          case "${words[$i]}" in
            -I | -n | -L | -P | -d | -E | -s | -a) i=$((i + 2)) ;;
            -*) i=$((i + 1)) ;;
            *) break ;;
          esac
        done
        ;;
      *) break ;;
    esac
  done
  [ "$i" -lt "${#words[@]}" ] || return 0

  cmd="${words[$i]}"
  base="${cmd##*/}"
  local args=("${words[@]:$((i + 1))}")

  case "$base" in
    git) check_git "${args[@]+"${args[@]}"}" ;;
    rm) check_rm "${args[@]+"${args[@]}"}" ;;
    bash | sh | zsh | dash | ksh)
      local k=0
      while [ "$k" -lt "${#args[@]}" ]; do
        case "${args[$k]}" in
          -c | -*c) [ $((k + 1)) -lt "${#args[@]}" ] && analyze "${args[$((k + 1))]}" ; break ;;
          -*) ;;
          *) break ;;
        esac
        k=$((k + 1))
      done
      ;;
    eval) analyze "${args[*]+"${args[*]}"}" ;;
  esac

  local joined="${words[*]}"
  case " $joined " in
    *" psql "* | *" mysql "* | *" mariadb "* | *" sqlite3 "* | *" sqlcmd "* | *" mongosh "* | *" mongo "* | *" pgcli "* | *" mycli "* | */psql\ * | */mysql\ *)
      check_database "$joined" ;;
  esac
  case "$joined" in
    *migrate:fresh* | *migrate:reset* | *db:wipe* | *"db:drop"* | *"prisma migrate reset"* | *"prisma db push --force-reset"* | *"alembic downgrade base"* | *"manage.py flush"*)
      ask "This wipes or resets a database. Confirm it targets a local/dev database." ;;
  esac
}

DEPTH=0
analyze() {
  [ "$DEPTH" -lt 4 ] || return 0
  DEPTH=$((DEPTH + 1))
  local TOKENS SUBS t segment=() sub
  set -f
  tokenize "$1"
  for t in "${TOKENS[@]+"${TOKENS[@]}"}"; do
    if [ "$t" = "$SEP" ]; then
      check_command "${segment[@]+"${segment[@]}"}"
      segment=()
    else
      segment+=("$t")
    fi
  done
  check_command "${segment[@]+"${segment[@]}"}"
  local subs=("${SUBS[@]+"${SUBS[@]}"}")
  for sub in "${subs[@]+"${subs[@]}"}"; do
    analyze "$sub"
  done
  DEPTH=$((DEPTH - 1))
}

analyze "$command"
[ -n "$ASK_REASON" ] && emit ask "$ASK_REASON"
exit 0
