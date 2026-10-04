#!/usr/bin/env bash
# Claude Code PreToolUse hook for Bash.
# Denies commands that are catastrophic or bypass safety nets, and asks for confirmation
# for commands that destroy work or data. Everything else is left to the normal permission flow.
#
# Supported shell words, bash -c/eval strings and substitutions are inspected. Unsupported
# executable syntax and analysis limits require review. Quoted data stays data.
# This file holds only the policy: what to deny and what to ask about.
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

# Codex treats an "ask" answer as a failed hook and runs the command, so for Codex every
# ask becomes a deny that tells the assistant to leave the command to the user.
CLIENT=claude
[ "${1:-}" != --codex ] || CLIENT=codex

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
# Writes to the harness's own settings; refused in project-only modes so an autonomous
# agent cannot lift its limits or leave its mode.
SETTINGS_WRITE=""

command="$(json_field .tool_input.command)"
cwd="$(json_field .cwd)"
[ -n "$command" ] || exit 0
[ -n "$cwd" ] && [ -d "$cwd" ] || cwd="$PWD"

# shellcheck source=SCRIPTDIR/lib/shell-parse.sh
. "$(dirname "$0")/lib/shell-parse.sh"
# The bare-script copy in the guard tests has no log library; logging is optional.
# shellcheck source=SCRIPTDIR/lib/activity-log.sh
. "$(dirname "$0")/lib/activity-log.sh" 2>/dev/null || activity_log() { :; }

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
        -c | --config-env) case "$(printf '%s' "$a" | tr '[:upper:]' '[:lower:]')" in
              core.hookspath=*) deny "Overriding core.hooksPath disables the git hooks that enforce the user's rules." ;;
            esac ;;
      esac
      continue
    fi
    if [ -z "$sub" ]; then
      case "$a" in
        -C | --git-dir | --work-tree) ACTS_ELSEWHERE=1; prev="$a"; skip_next=1 ;;
        --git-dir=* | --work-tree=*) ACTS_ELSEWHERE=1 ;;
        -c | --namespace | --config-env) prev="$a"; skip_next=1 ;;
        -c?* | --config-env=*) case "$(printf '%s' "$a" | tr '[:upper:]' '[:lower:]')" in
                          -ccore.hookspath=* | --config-env=core.hookspath=*) deny "Overriding core.hooksPath disables the git hooks that enforce the user's rules." ;;
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
        *" harness."* | *" tack."*)
          case "$joined" in
            *" --get"* | *" -l "* | *" --list "*) ;;
            *) SETTINGS_WRITE="Changing tack's settings is the user's decision in this mode." ;;
          esac ;;
      esac
      ;;
    reset)
      case "$joined" in *" --hard"*) ask_local "git reset --hard discards uncommitted changes permanently." ;; esac
      ;;
    clean)
      for r in "${rest[@]+"${rest[@]}"}"; do
        case "$r" in
          --force) ask_local "git clean -f deletes untracked files permanently." ;;
          --*) ;;
          -*f*) ask_local "git clean -f deletes untracked files permanently." ;;
        esac
      done
      ;;
    restore)
      case "$joined" in
        *" --worktree "* | *" -W "*) ask_local "git restore discards uncommitted changes in the working tree." ;;
        *" --staged "* | *" -S "*) ;;
        *) ask_local "git restore discards uncommitted changes in the working tree." ;;
      esac
      ;;
    checkout)
      case "$joined" in
        *" -- "* | *" . "* | *" -f "* | *" --force "*) ask_local "This checkout discards uncommitted changes." ;;
      esac
      ;;
    switch)
      case "$joined" in
        *" -f "* | *" --force "* | *" --discard-changes "*) ask_local "This switch discards uncommitted changes." ;;
      esac
      ;;
    branch)
      for r in "${rest[@]+"${rest[@]}"}"; do
        case "$r" in
          --*) ;;
          -*D*) ask_local "Force-deleting a branch can lose unmerged commits." ;;
        esac
      done
      case "$joined" in
        *" --delete "*" --force "* | *" --force "*" --delete "* | *" -d "*" -f "* | *" -d --force "*)
          ask_local "Force-deleting a branch can lose unmerged commits." ;;
      esac
      for r in "${rest[@]+"${rest[@]}"}"; do
        if is_main "$r" && [ -n "$LOCAL_ASK_REASON" ]; then ask "Force-deleting the main branch."; fi
      done
      ;;
    stash)
      case "$joined" in *" clear "* | *" drop "*) ask_local "This permanently deletes stashed changes." ;; esac
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
          if [ "$k" -ge 128 ]; then
            ask "Compact git option exceeds the analysis limit; review the complete command."
            break
          fi
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

# Flags harness subcommands that change settings; reads (status, show, list, a lone name) pass.
check_harness() {
  local positional=0 a
  case "${1:-}" in
    trust | enable | disable) SETTINGS_WRITE="Changing tack's settings is the user's decision in this mode."; return ;;
    mode)
      case "${2:-}" in '' | list | show | new) return ;; esac
      SETTINGS_WRITE="Changing the workflow mode is the user's decision in this mode." ;;
    config)
      shift
      for a in "$@"; do
        case "$a" in --unset) positional=2 ;; --global) ;; *) positional=$((positional + 1)) ;; esac
      done
      [ "$positional" -lt 2 ] || SETTINGS_WRITE="Changing tack's settings is the user's decision in this mode." ;;
  esac
}

# Prints the PR's check buckets, or nothing when gh fails or takes over about 4 seconds, which
# leaves room within the hook's 10-second timeout on slower machines. Without timeout(1)
# (stock macOS), a background watchdog stops gh instead.
pr_buckets() {
  local out pid n=0
  if command -v timeout >/dev/null 2>&1; then
    (cd "$cwd" && timeout 4 gh pr checks "$@" --json bucket --jq '.[].bucket' 2>/dev/null)
    return 0
  fi
  out="$(mktemp "${TMPDIR:-/tmp}/tack-guard.XXXXXX")" || return 0
  (cd "$cwd" && exec gh pr checks "$@" --json bucket --jq '.[].bucket' >"$out" 2>/dev/null) &
  pid=$!
  while kill -0 "$pid" 2>/dev/null && [ "$n" -lt 20 ]; do sleep 0.2; n=$((n + 1)); done
  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null
  else
    cat "$out"
  fi
  rm -f "$out"
}

# merge-requires-green: in enabled projects `gh pr merge` waits for green CI. Failing or pending
# checks deny, so the assistant fixes or waits and retries; when the checks cannot be read for
# the pull request being merged, the user decides. --auto lets GitHub wait for pending checks.
GH_REPO_FROM_ENV=0
check_gh() {
  [ "${1:-}" = pr ] && [ "${2:-}" = merge ] || return 0
  shift 2
  local selector=() repo=() skip_next=0 prev="" a setting buckets auto=0 cli
  for a in "$@"; do
    if [ "$skip_next" -eq 1 ]; then
      skip_next=0
      case "$prev" in -R | --repo) repo=(--repo "$a") ;; esac
      continue
    fi
    case "$a" in
      -R | --repo | -b | --body | -F | --body-file | -t | --subject | -A | --author-email | --match-head-commit)
        prev="$a"; skip_next=1 ;;
      --repo=*) repo=(--repo "${a#--repo=}") ;;
      --disable-auto) return 0 ;;
      --auto) auto=1 ;;
      -*) ;;
      *) [ "${#selector[@]}" -gt 0 ] || selector=("$a") ;;
    esac
  done
  # Absolute, because it runs after cd "$cwd" and the hook may be started with a relative path.
  cli="$(cd "$(dirname "$0")/../../bin" && pwd)/tack"
  (cd "$cwd" && "$cli" status --quiet) 2>/dev/null || return 0
  setting="$(cd "$cwd" && "$cli" config merge-requires-green 2>/dev/null)"
  [ "${setting%% *}" != false ] || return 0
  case "${selector[*]-} ${repo[*]-}" in
    *'__subst__'* | *'$'* | *'`'*) ask "Cannot confirm CI for a pull request chosen at run time; check that its checks passed before merging."; return 0 ;;
  esac
  if [ "$ACTS_ELSEWHERE" -eq 1 ] || [ "$GH_REPO_FROM_ENV" -eq 1 ]; then
    ask "Cannot confirm the CI checks of a pull request in another directory or repository; check them before merging."
    return 0
  fi
  if ! command -v gh >/dev/null 2>&1; then
    ask "Cannot confirm the pull request's CI checks passed (gh is not available); check them before merging."
    return 0
  fi
  buckets="$(pr_buckets ${selector[@]+"${selector[@]}"} ${repo[@]+"${repo[@]}"})"
  case "$buckets" in
    '') ask "Cannot confirm the pull request's CI checks passed (gh reported none or timed out); check them before merging." ;;
    *fail* | *cancel*) deny "The pull request's CI checks are failing. Read the failed job's log (gh run view --log-failed), fix it and push before merging." ;;
    *pending*)
      [ "$auto" -eq 1 ] || deny "The pull request's CI checks are still running. Wait for them (gh pr checks --watch) and merge once they pass." ;;
  esac
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
      '.' | './' | '*' | './*') ask_local "Recursive delete of everything in the current directory ($t)." ;;
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

POLICY_SCOPES=() POLICY_DECISIONS=() POLICY_PATTERNS=() POLICY_REASONS=()
trim() { local value="$1"; value="${value#"${value%%[![:space:]]*}"}"; printf '%s' "${value%"${value##*[![:space:]]}"}"; }

# Loads "scope | decision | pattern | reason" rules; malformed lines and relaxing rules are skipped.
load_policy() {
  local file="$1" scope decision pattern reason
  while IFS='|' read -r scope decision pattern reason; do
    scope="$(trim "$scope")" decision="$(trim "$decision")" pattern="$(trim "$pattern")" reason="$(trim "$reason")"
    case "$scope" in client) ;; sql | data | command) case "$decision" in ask | deny) ;; *) continue ;; esac ;; *) continue ;; esac
    [ -n "$pattern" ] || continue
    POLICY_SCOPES+=("$scope") POLICY_DECISIONS+=("$decision") POLICY_PATTERNS+=("$pattern") POLICY_REASONS+=("${reason:-Matches a guard policy rule: $pattern}")
  done < "$file"
}

POLICY_FILE="$(dirname "$0")/guard-policy.txt"
if [ -f "$POLICY_FILE" ]; then load_policy "$POLICY_FILE"
else ask "The guard policy file is missing; review the command."; fi
# User rules: agent-tack, plus the directory from before the rename if it is still there.
for USER_POLICY in "${XDG_CONFIG_HOME:-$HOME/.config}"/agent-tack/guard-policy.txt "${XDG_CONFIG_HOME:-$HOME/.config}"/agent-harness/guard-policy.txt; do
  [ ! -f "$USER_POLICY" ] || load_policy "$USER_POLICY"
done

apply_rule() {
  if [ "${POLICY_DECISIONS[$1]}" = deny ]; then deny "${POLICY_REASONS[$1]}"; fi
  ask "${POLICY_REASONS[$1]}"
}

check_policy() {
  local joined="$1" upper i has_client=0
  # bash 3.2 treats expanding an empty array under set -u as an unbound variable
  [ "${#POLICY_SCOPES[@]}" -gt 0 ] || return 0
  for i in "${!POLICY_SCOPES[@]}"; do
    [ "${POLICY_SCOPES[$i]}" = client ] || continue
    case " $joined " in *" ${POLICY_PATTERNS[$i]} "* | */"${POLICY_PATTERNS[$i]} "*) has_client=1; break ;; esac
  done
  upper="$(printf '%s' "$joined" | tr '[:lower:]' '[:upper:]')"
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

# Checks one simple command given as words
check_command() {
  COMMAND_COUNT=$((COMMAND_COUNT + 1))
  if [ "$COMMAND_COUNT" -gt 256 ]; then
    ask "Shell command count limit exceeded; review the complete command."
    return 0
  fi
  local words=() w skip_redir=0 has_redir=0 i=0 cmd base
  for w in "$@"; do
    if [ "$skip_redir" -eq 1 ]; then skip_redir=0; continue; fi
    if [ "$w" = "$REDIR" ]; then skip_redir=1; has_redir=1; continue; fi
    words+=("$w")
  done
  [ "${#words[@]}" -gt 0 ] || return 0

  # Skip env assignments and wrappers that run the rest as a command
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
      sudo | doas)
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
            -*) ask "Unsupported privilege-wrapper option requires review."; return 0 ;;
            *=*) i=$((i + 1)) ;;
            *) break ;;
          esac
        done
        ;;
      command | exec | nohup | time | builtin)
        i=$((i + 1))
        while [ "$i" -lt "${#words[@]}" ]; do
          case "${words[$i]}" in
            -- | -p) i=$((i + 1)) ;;
            -v | -V) return 0 ;;
            -*) ask "Unsupported command-wrapper option requires review."; return 0 ;;
            *) break ;;
          esac
        done
        ;;
      env)
        i=$((i + 1))
        while [ "$i" -lt "${#words[@]}" ]; do
          case "${words[$i]}" in
            --) i=$((i + 1)); break ;;
            -S | --split-string)
              if [ $((i + 1)) -ge "${#words[@]}" ]; then
                ask "Missing env split string requires review."; return 0
              fi
              check_env_split "${words[$((i + 1))]}" "${words[@]:$((i + 2))}"
              return 0 ;;
            -S?*) check_env_split "${words[$i]#-S}" "${words[@]:$((i + 1))}"; return 0 ;;
            --split-string=*) check_env_split "${words[$i]#--split-string=}" "${words[@]:$((i + 1))}"; return 0 ;;
            -u | --unset | -C | --chdir) i=$((i + 2)) ;;
            -i | --ignore-environment | -0 | --null | --unset=* | --chdir=*) i=$((i + 1)) ;;
            -*) ask "Unsupported env option requires review."; return 0 ;;
            *=*) i=$((i + 1)) ;;
            *) break ;;
          esac
        done
        ;;
      nice | stdbuf | ionice)
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
    *'__subst__'* | *'$'* | *'`'*) ask "Dynamic executable name requires review." ;;
    git) check_git "${args[@]+"${args[@]}"}" ;;
    rm) check_rm "${args[@]+"${args[@]}"}" ;;
    gh) check_gh "${args[@]+"${args[@]}"}" ;;
    cd | pushd | popd) ACTS_ELSEWHERE=1 ;;
    harness | tack) check_harness "${args[@]+"${args[@]}"}" ;;
    bash | sh | zsh | dash | ksh)
      local k=0 shell_string=0
      while [ "$k" -lt "${#args[@]}" ]; do
        case "${args[$k]}" in
          -c | -*c)
            shell_string=1
            if [ $((k + 1)) -lt "${#args[@]}" ]; then
              analyze "${args[$((k + 1))]}"
            else
              ask "Missing shell command string requires review."
            fi
            break ;;
          -*) ;;
          *) break ;;
        esac
        k=$((k + 1))
      done
      if [ "$shell_string" -eq 0 ] && [ "$has_redir" -eq 1 ]; then
        ask "Shell stdin script or here-string requires review."
      fi
      ;;
    eval) analyze "${args[*]+"${args[*]}"}" ;;
  esac

  check_policy "${words[*]}"
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
  cli="$(dirname "$0")/../../bin/tack"
  (cd "$cwd" && "$cli" status --quiet) || return 1
  mode="$(cd "$cwd" && "$cli" mode show 2>/dev/null)" || return 1
  [ -z "${mode##WARNING:*}" ]
}

analyze "$command"
if [ -n "$SETTINGS_WRITE" ] && waives_local_asks; then
  deny "$SETTINGS_WRITE"
fi
if [ -n "$ASK_REASON" ]; then
  emit ask "$ASK_REASON"
elif [ -n "$LOCAL_ASK_REASON" ]; then
  if [ "$ACTS_ELSEWHERE" -eq 1 ] || ! waives_local_asks; then emit ask "$LOCAL_ASK_REASON"; fi
fi
exit 0
