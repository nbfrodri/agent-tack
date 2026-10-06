#!/usr/bin/env bash
# Claude Code PreToolUse hook for Bash.
# Denies commands that are catastrophic or bypass safety nets, and asks for confirmation
# for commands that destroy work or data. Everything else is left to the normal permission flow.
#
# Supported shell words, bash -c/eval strings and substitutions are inspected. Unsupported
# executable syntax and analysis limits require review. Quoted data stays data.
# This file reads the input, holds the decision state and dispatches each simple command to the
# rules in lib/guard-*.sh (git, files, exec, infra, wrappers); pattern rules come from guard-policy.txt.
#
# Input: the hook JSON on stdin. Output: a permission decision as JSON, or nothing.
# Fails open (allows) if the input can't be parsed, so broken input never blocks work; a missing
# or broken rule library fails safe instead and every command asks.
set -u

# Builtins instead of cat and dirname: every process start costs tens of milliseconds on Windows.
IFS= read -r -d '' input || true
case "$0" in */*) GUARD_DIR="${0%/*}" ;; *) GUARD_DIR=. ;; esac
case "$GUARD_DIR" in /*) ;; *) GUARD_DIR="$PWD/$GUARD_DIR" ;; esac
# On Windows python3 is often the Microsoft Store alias, which starts several times slower than python.
TACK_PYTHON=python3
case "${OSTYPE:-}" in
  msys* | cygwin*) case "$(command -v python3)" in *WindowsApps*) ! command -v python >/dev/null || TACK_PYTHON=python ;; esac ;;
esac

# Prints .tool_input.command and .cwd, each followed by a NUL, from one process: a process start
# costs tens of milliseconds, up to hundreds on Windows. A missing or non-string value prints as
# empty; NULs inside a value and trailing newlines are dropped, as command substitution did.
read_input() {
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$input" | jq -j '(.tool_input.command, .cwd)
      | (if type == "string" then gsub("\u0000"; "") | sub("\n+$"; "") else "" end) + "\u0000"' 2>/dev/null
  elif command -v "$TACK_PYTHON" >/dev/null 2>&1; then
    printf '%s' "$input" | "$TACK_PYTHON" -S -c '
import json, sys
data = json.loads(sys.stdin.buffer.read())
tool_input = data.get("tool_input") if isinstance(data, dict) else None
values = [tool_input.get("command") if isinstance(tool_input, dict) else None, data.get("cwd") if isinstance(data, dict) else None]
for value in values:
    text = value.replace("\0", "").rstrip("\n") if isinstance(value, str) else ""
    sys.stdout.buffer.write(text.encode("utf-8", "surrogateescape") + b"\0")
' 2>/dev/null
  fi
}

# Codex treats an "ask" answer as a failed hook and runs the command, so for Codex every
# ask becomes a deny that tells the assistant to leave the command to the user.
CLIENT=claude
[ "${1:-}" != --codex ] || CLIENT=codex
# Cursor can ask the user, so it keeps asks; the flag only labels its activity log entries.
[ "${1:-}" != --cursor ] || CLIENT=cursor

emit() {
  local decision="$1" reason="$2"
  if [ "$CLIENT" = codex ] && [ "$decision" = ask ]; then
    decision=deny
    reason="Needs the user's confirmation, which Codex hooks cannot ask for: $reason Ask the user to run it or to approve it."
  fi
  activity_log "$cwd" "$CLIENT" "guard $decision" "${command:0:120} -- $reason"
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
# Explicit local data loss inside the project: the only asks a project-only mode such as
# unleash may waive. Opaque syntax and analysis limits keep asking, so the deny rules hold.
LOCAL_ASK_REASON=""
ask_local() { [ -n "$LOCAL_ASK_REASON" ] || LOCAL_ASK_REASON="$1"; }
# A command that changes directory or points git elsewhere may act outside the project,
# so its local asks are never waived.
ACTS_ELSEWHERE=0
# Writes to tack's own settings; refused in project-only modes so an autonomous
# agent cannot lift its limits or leave its mode.
SETTINGS_WRITE=""
# Set when GH_REPO or GH_HOST points gh at another repository.
GH_REPO_FROM_ENV=0

command="" cwd=""
{ IFS= read -r -d '' command; IFS= read -r -d '' cwd; } < <(read_input)
[ -n "$command" ] || exit 0
[ -n "$cwd" ] && [ -d "$cwd" ] || cwd="$PWD"

# normalize_abs PATH: collapses "//", "." and ".." in an absolute path, without reading the disk.
normalize_abs() {
  local segment out='' IFS=/
  set -f
  for segment in $1; do
    case "$segment" in
      '' | .) ;;
      ..) out="${out%/*}" ;;
      *) out="$out/$segment" ;;
    esac
  done
  set +f
  printf '%s\n' "${out:-/}"
}
# Delete targets are compared after normalisation, so the working directory and HOME are too:
# macOS's TMPDIR ends in "/" and leaves "//" in temp paths.
cwd="$(normalize_abs "$cwd")"
# shellcheck disable=SC2034 # Read by too_broad and place_of in lib/guard-files.sh.
HOME_DIR="$(normalize_abs "$HOME")"

# shellcheck source=SCRIPTDIR/lib/shell-parse.sh
. "$GUARD_DIR/lib/shell-parse.sh"
# The bare-script copy in the guard tests has no log library; logging is optional.
# shellcheck source=SCRIPTDIR/lib/activity-log.sh
. "$GUARD_DIR/lib/activity-log.sh" 2>/dev/null || activity_log() { :; }

# The rules live in libraries next to the parser. A missing or broken one fails safe: every command asks.
GUARD_LIB_MISSING=""
GUARD_LIB_DIR="$GUARD_DIR/lib"
# shellcheck source=SCRIPTDIR/lib/guard-git.sh
. "$GUARD_LIB_DIR/guard-git.sh" 2>/dev/null || GUARD_LIB_MISSING=lib/guard-git.sh
# shellcheck source=SCRIPTDIR/lib/guard-files.sh
. "$GUARD_LIB_DIR/guard-files.sh" 2>/dev/null || GUARD_LIB_MISSING=lib/guard-files.sh
# shellcheck source=SCRIPTDIR/lib/guard-exec.sh
. "$GUARD_LIB_DIR/guard-exec.sh" 2>/dev/null || GUARD_LIB_MISSING=lib/guard-exec.sh
# shellcheck source=SCRIPTDIR/lib/guard-infra.sh
. "$GUARD_LIB_DIR/guard-infra.sh" 2>/dev/null || GUARD_LIB_MISSING=lib/guard-infra.sh
# shellcheck source=SCRIPTDIR/lib/guard-wrappers.sh
. "$GUARD_LIB_DIR/guard-wrappers.sh" 2>/dev/null || GUARD_LIB_MISSING=lib/guard-wrappers.sh

POLICY_SCOPES=() POLICY_DECISIONS=() POLICY_PATTERNS=() POLICY_REASONS=()
# trim NAME: strips surrounding whitespace from the variable NAME in place; no subshell, since the
# policy file is read before every command and a subshell per field cost about 90 ms.
trim() { local value="${!1}"; value="${value#"${value%%[![:space:]]*}"}"; printf -v "$1" '%s' "${value%"${value##*[![:space:]]}"}"; }

# Loads "scope | decision | pattern | reason" rules; malformed lines and relaxing rules are skipped.
load_policy() {
  local file="$1" scope decision pattern reason
  while IFS='|' read -r scope decision pattern reason; do
    trim scope; trim decision; trim pattern; trim reason
    case "$scope" in client) ;; sql | data | command) case "$decision" in ask | deny) ;; *) continue ;; esac ;; *) continue ;; esac
    [ -n "$pattern" ] || continue
    POLICY_SCOPES+=("$scope") POLICY_DECISIONS+=("$decision") POLICY_PATTERNS+=("$pattern") POLICY_REASONS+=("${reason:-Matches a guard policy rule: $pattern}")
  done < "$file"
}

POLICY_FILE="$GUARD_DIR/guard-policy.txt"
if [ -f "$POLICY_FILE" ]; then load_policy "$POLICY_FILE"
else ask "The guard policy file is missing or failed to load; review the command."; fi
# User rules: agent-tack, plus the directory from before the rename if it is still there.
# The directory's former name is still read until the installer moves it.
FORMER_CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/agent-harness"
for USER_POLICY in "${XDG_CONFIG_HOME:-$HOME/.config}"/agent-tack/guard-policy.txt "$FORMER_CONFIG/guard-policy.txt"; do
  [ ! -f "$USER_POLICY" ] || load_policy "$USER_POLICY"
done

apply_rule() {
  if [ "${POLICY_DECISIONS[$1]}" = deny ]; then deny "${POLICY_REASONS[$1]}"; fi
  ask "${POLICY_REASONS[$1]}"
}

check_policy() {
  local joined="$1" upper="" i has_client=0
  # bash 3.2 treats expanding an empty array under set -u as an unbound variable
  [ "${#POLICY_SCOPES[@]}" -gt 0 ] || return 0
  for i in "${!POLICY_SCOPES[@]}"; do
    [ "${POLICY_SCOPES[$i]}" = client ] || continue
    case " $joined " in *" ${POLICY_PATTERNS[$i]} "* | */"${POLICY_PATTERNS[$i]} "*) has_client=1; break ;; esac
  done
  # SQL rules apply only to a database client's command, so only then is it upper-cased.
  [ "$has_client" -eq 0 ] || upper="$(printf '%s' "$joined" | tr '[:lower:]' '[:upper:]')"
  for i in "${!POLICY_SCOPES[@]}"; do
    case "${POLICY_SCOPES[$i]}" in
      command) case "$joined" in *"${POLICY_PATTERNS[$i]}"*) apply_rule "$i" ;; esac ;;
      data) [ "$has_client" -eq 0 ] || case "$joined" in *"${POLICY_PATTERNS[$i]}"*) apply_rule "$i" ;; esac ;;
      sql)
        [ "$has_client" -eq 1 ] || continue
        case "$upper" in *"$(printf '%s' "${POLICY_PATTERNS[$i]}" | tr '[:lower:]' '[:upper:]')"*) apply_rule "$i" ;; esac ;;
    esac
  done
}

deny_override() {
  deny "The ${1%%=*} override is for the user to set. Fix what the hook refuses, or ask the user to run the command."
}

# Checks one simple command given as words
check_command() {
  COMMAND_COUNT=$((COMMAND_COUNT + 1))
  if [ "$COMMAND_COUNT" -gt 256 ]; then
    ask "Shell command count limit exceeded; review the complete command."
    return 0
  fi
  local words=() w skip_redir=0 i=0 cmd base
  for w in "$@"; do
    if [ "$skip_redir" -eq 1 ]; then skip_redir=0; continue; fi
    if [ "$w" = "$REDIR" ]; then skip_redir=1; continue; fi
    # The hooks' overrides are the user's deliberate choice, like --no-verify: an assignment,
    # env, export or declare of one would let the assistant bypass them.
    case "$w" in
      TACK_ALLOW_*=*) deny_override "$w" ;;
      TACK_ALLOW_*)
        case "${words[0]:-}" in export | declare | typeset | readonly | local) deny_override "$w" ;; esac ;;
    esac
    words+=("$w")
  done
  [ "${#words[@]}" -gt 0 ] || return 0

  # Skip env assignments and wrappers that run the rest as a command
  skip_wrappers || return 0
  [ "$i" -lt "${#words[@]}" ] || return 0

  cmd="${words[$i]}"
  base="${cmd##*/}"
  local args=("${words[@]:$((i + 1))}")

  case "$base" in
    *'__subst__'* | *'$'* | *'`'*) ask "Dynamic executable name requires review." ;;
    git) check_git "${args[@]+"${args[@]}"}" ;;
    rm) check_rm "${args[@]+"${args[@]}"}" ;;
    find) check_find "${args[@]+"${args[@]}"}" ;;
    gh) check_gh "${args[@]+"${args[@]}"}" ;;
    cd | pushd | popd) ACTS_ELSEWHERE=1 ;;
    tack) check_tack "${args[@]+"${args[@]}"}" ;;
    bash | sh | zsh | dash | ksh) check_shell "${args[@]+"${args[@]}"}" ;;
    source | .) check_source "${args[@]+"${args[@]}"}" ;;
    python | python2 | python3 | python3.* | node | perl | ruby | php) check_interpreter "$base" "${args[@]+"${args[@]}"}" ;;
    kubectl) check_kubectl "${args[@]+"${args[@]}"}" ;;
    terraform | tofu) check_terraform "$base" "${args[@]+"${args[@]}"}" ;;
    dd) check_dd "${args[@]+"${args[@]}"}" ;;
    mkfs | mkfs.* | mke2fs | mkswap | wipefs) ask "$base formats or wipes a disk or partition and erases what is on it. Confirm the device." ;;
    eval) analyze "${args[*]+"${args[*]}"}" ;;
  esac

  check_policy "${words[*]}"
}

DEPTH=0
COMMAND_COUNT=0
ANALYSIS_COUNT=0
analyze() {
  ANALYSIS_COUNT=$((ANALYSIS_COUNT + 1))
  if [ "$ANALYSIS_COUNT" -gt 64 ]; then
    ask "Shell analysis count limit exceeded; review the complete command."
    return 0
  fi
  if [ "$DEPTH" -ge 4 ]; then
    ask "Shell analysis depth limit exceeded; review the complete command."
    return 0
  fi
  if [ "${#1}" -gt 65536 ]; then
    ask "Command size exceeds the 65536-character analysis limit; review the complete command."
    return 0
  fi
  DEPTH=$((DEPTH + 1))
  local TOKENS SUBS PARSE_ERROR t segment=() sub
  set -f
  tokenize "$1"
  if [ -n "$PARSE_ERROR" ]; then
    ask "$PARSE_ERROR"
    DEPTH=$((DEPTH - 1))
    return 0
  fi
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

waives_local_asks() {
  local cli mode
  cli="$GUARD_DIR/../../bin/tack"
  (cd "$cwd" && "$cli" status --quiet) || return 1
  mode="$(cd "$cwd" && "$cli" mode show 2>/dev/null)" || return 1
  [ -z "${mode##WARNING:*}" ]
}

if [ -n "$GUARD_LIB_MISSING" ]; then ask "The guard library $GUARD_LIB_MISSING is missing; review the command."
else analyze "$command"; fi
if [ -n "$SETTINGS_WRITE" ] && waives_local_asks; then
  deny "$SETTINGS_WRITE"
fi
if [ -n "$ASK_REASON" ]; then
  emit ask "$ASK_REASON"
elif [ -n "$LOCAL_ASK_REASON" ]; then
  if [ "$ACTS_ELSEWHERE" -eq 1 ] || ! waives_local_asks; then emit ask "$LOCAL_ASK_REASON"; fi
fi
exit 0
