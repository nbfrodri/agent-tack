#!/usr/bin/env bash
# Claude Code PreToolUse hook for Bash.
# Denies commands that are catastrophic or bypass safety nets, and asks for confirmation
# for commands that destroy work or data. Everything else is left to the normal permission flow.
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

decide() {
  local decision="$1" reason="$2"
  # Reasons are fixed strings below, so they need no JSON escaping beyond quotes
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"%s","permissionDecisionReason":"%s"}}\n' \
    "$decision" "${reason//\"/\'}"
  exit 0
}
deny() { decide deny "$1"; }
ask() { decide ask "$1"; }

command="$(json_field .tool_input.command)"
cwd="$(json_field .cwd)"
[ -n "$command" ] || exit 0
[ -n "$cwd" ] && [ -d "$cwd" ] || cwd="$PWD"

# Avoid glob expansion while splitting words below
set -f

current_branch() {
  git -C "$cwd" branch --show-current 2>/dev/null
}

# Checks one simple command (no ; && || |)
check_segment() {
  local seg="$1" words=() i
  read -r -a words <<<"$seg"
  [ "${#words[@]}" -gt 0 ] || return 0

  # Skip leading env assignments and sudo
  i=0
  while [ "$i" -lt "${#words[@]}" ]; do
    case "${words[$i]}" in
      *=*|sudo|command|exec|nohup|time) i=$((i + 1)) ;;
      *) break ;;
    esac
  done
  [ "$i" -lt "${#words[@]}" ] || return 0
  local cmd="${words[$i]}"
  local args=("${words[@]:$((i + 1))}")

  case "$cmd" in
    git)
      check_git "${args[@]+"${args[@]}"}"
      ;;
    rm)
      check_rm "${args[@]+"${args[@]}"}"
      ;;
  esac

  # Destructive database operations, from any tool
  case "$seg" in
    *[Dd][Rr][Oo][Pp]\ [Dd][Aa][Tt][Aa][Bb][Aa][Ss][Ee]*|*[Dd][Rr][Oo][Pp]\ [Ss][Cc][Hh][Ee][Mm][Aa]*|*[Dd][Rr][Oo][Pp]\ [Tt][Aa][Bb][Ll][Ee]*|*[Tt][Rr][Uu][Nn][Cc][Aa][Tt][Ee]\ [Tt][Aa][Bb][Ll][Ee]*|*"TRUNCATE "*)
      ask "This command drops or truncates database objects. Confirm it targets a local/dev database." ;;
    *dropDatabase*|*migrate:fresh*|*migrate:reset*|*db:wipe*|*"prisma migrate reset"*|*"prisma db push --force-reset"*|*"alembic downgrade base"*|*"manage.py flush"*)
      ask "This command wipes or resets a database. Confirm it targets a local/dev database." ;;
  esac
}

check_git() {
  # Drop global options such as -C <path> and -c <key=value> to find the subcommand
  local sub="" rest=() skip_next=0 a r
  for a in "$@"; do
    if [ "$skip_next" -eq 1 ]; then skip_next=0; continue; fi
    if [ -z "$sub" ]; then
      case "$a" in
        -C|-c|--git-dir|--work-tree|--namespace) skip_next=1 ;;
        -*) ;;
        *) sub="$a" ;;
      esac
    else
      rest+=("$a")
    fi
  done

  local joined=" ${rest[*]+"${rest[*]}"} "
  case "$joined" in
    *" --no-verify "*)
      deny "--no-verify skips the git hooks that enforce commit conventions and protect main. Fix the reported problem instead." ;;
  esac

  case "$sub" in
    push)
      local force=0 targets_main=0 explicit_ref=0 positional=0
      for r in "${rest[@]+"${rest[@]}"}"; do
        case "$r" in
          --force|-f|--force-with-lease|--force-with-lease=*|--force-if-includes|--mirror) force=1 ;;
          -*f*) case "$r" in --*) ;; *) force=1 ;; esac ;;
          +*) force=1; explicit_ref=1 ;;
          --delete|-d) force=1 ;;
          -*) ;;
          *)
            positional=$((positional + 1))
            # The first positional argument is the remote; the rest are refspecs
            [ "$positional" -ge 2 ] && explicit_ref=1
            ;;
        esac
        case "$r" in
          main|master|+main|+master|*:main|*:master|*:refs/heads/main|*:refs/heads/master)
            targets_main=1 ;;
        esac
      done
      if [ "$force" -eq 1 ]; then
        if [ "$targets_main" -eq 1 ]; then
          deny "Force-pushing or deleting main/master is not allowed. Use git revert to undo published commits."
        fi
        if [ "$explicit_ref" -eq 0 ]; then
          case "$(current_branch)" in
            main|master) deny "Force-pushing the current branch (main/master) is not allowed. Use git revert to undo published commits." ;;
          esac
        fi
        ask "This push rewrites or deletes history on the remote. Confirm the branch is yours and not shared."
      fi
      ;;
    reset)
      case "$joined" in
        *" --hard"*) ask "git reset --hard discards uncommitted changes permanently." ;;
      esac
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
    checkout|restore)
      # Unstaging only (restore --staged without --worktree) keeps the working tree intact
      case "$joined" in
        *" --staged "*|*" -S "*)
          case "$joined" in *" --worktree "*|*" -W "*) ;; *) return 0 ;; esac ;;
      esac
      case "$joined" in
        *" -- . "*|*" . "*|*" --worktree "*|*" -W "*) ask "This discards uncommitted changes in the working tree." ;;
      esac
      ;;
    branch)
      case "$joined" in
        *" -D "*|*" --delete --force "*|*" -d --force "*) ask "Force-deleting a branch can lose unmerged commits." ;;
      esac
      ;;
    stash)
      case "$joined" in
        *" clear "*|*" drop "*) ask "This permanently deletes stashed changes." ;;
      esac
      ;;
    filter-branch|filter-repo)
      ask "This rewrites the whole repository history." ;;
  esac
}

check_rm() {
  local recursive=0 targets=() a
  for a in "$@"; do
    case "$a" in
      --recursive|-r|-R) recursive=1 ;;
      --*) ;;
      -*) case "$a" in *[rR]*) recursive=1 ;; esac ;;
      *) targets+=("$a") ;;
    esac
  done
  [ "$recursive" -eq 1 ] || return 0

  local t real
  # The patterns below match the literal text Claude typed (~, $HOME), so they must not expand
  # shellcheck disable=SC2016,SC2088
  for t in "${targets[@]+"${targets[@]}"}"; do
    case "$t" in
      '/'|'/*'|'/.'|'~'|'~/'|'~/*'|'$HOME'|'$HOME/'|'$HOME/*'|'${HOME}'|'${HOME}/'|'${HOME}/*'|'..'|'../'|'../*')
        deny "Recursive delete of '$t' is too broad. Delete specific paths instead." ;;
      '.'|'./'|'*'|'./*')
        ask "Recursive delete of everything in the current directory ($t)." ;;
    esac
    case "$t" in
      "$HOME"|"$HOME/") deny "Recursive delete of the home directory is not allowed." ;;
    esac
    # Absolute paths outside the project and the temp dirs need confirmation
    case "$t" in
      /*)
        real="${t%/}"
        case "$real" in
          "$cwd"/*|/tmp/*|/var/tmp/*|"${TMPDIR:-/tmp}"/*) ;;
          *) ask "Recursive delete outside the project directory: $t" ;;
        esac
        ;;
      "~/"*|'$HOME/'*|'${HOME}/'*)
        ask "Recursive delete outside the project directory: $t" ;;
    esac
  done
}

# Split compound commands on ; && || | and newlines, then check each part
segments="$(printf '%s\n' "$command" | awk '{ gsub(/&&|\|\||;|\|/, "\n"); print }')"
while IFS= read -r segment; do
  # Strip leading subshell/grouping characters
  segment="${segment#"${segment%%[![:space:]({]*}"}"
  [ -n "$segment" ] && check_segment "$segment"
done <<EOF
$segments
EOF

exit 0
