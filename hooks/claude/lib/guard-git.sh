#!/usr/bin/env bash
# Guard rules for git, gh and tack's own settings. Sourced by guard-bash.sh, which defines
# deny, ask, ask_local, the decision state and $cwd.

current_branch() {
  # shellcheck disable=SC2154 # cwd is set by guard-bash.sh.
  git -C "$cwd" branch --show-current 2>/dev/null
}

is_main() {
  case "$1" in
    main | master | refs/heads/main | refs/heads/master) return 0 ;;
  esac
  return 1
}

# git_split_options ARGS: sets the caller's sub (the subcommand) and rest (its arguments), denying
# a hooks-path override in the global options and noting options that act in another repository.
git_split_options() {
  local skip_next=0 a prev=""
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
}

check_git() {
  local sub="" rest=()
  git_split_options "$@"
  local joined=" ${rest[*]+"${rest[*]}"} " r
  case "$sub" in
    commit) check_git_commit "${rest[@]+"${rest[@]}"}" ;;
    push) check_git_push "${rest[@]+"${rest[@]}"}" ;;
    config) check_git_config "$joined" ;;
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
    branch) check_git_branch "$joined" "${rest[@]+"${rest[@]}"}" ;;
    stash)
      case "$joined" in *" clear "* | *" drop "*) ask_local "This permanently deletes stashed changes." ;; esac
      ;;
    filter-branch | filter-repo)
      ask "This rewrites the whole repository history."
      ;;
  esac
}

# check_git_config JOINED: changing core.hooksPath is denied; changing tack's own keys is a
# settings write. Reads (--get, --list) pass.
check_git_config() {
  case "$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')" in
    *core.hookspath*)
      case "$1" in
        *" --get"* | *" -l "* | *" --list "*) ;;
        *) deny "Changing core.hooksPath disables the git hooks that enforce the user's rules." ;;
      esac ;;
    *" tack."*)
      case "$1" in
        *" --get"* | *" -l "* | *" --list "*) ;;
        *) SETTINGS_WRITE="Changing tack's settings is the user's decision in this mode." ;;
      esac ;;
  esac
}

# check_git_branch JOINED ARGS: force-deleting a branch asks, and always asks for main.
check_git_branch() {
  local joined="$1" r
  shift
  for r in "$@"; do
    case "$r" in
      --*) ;;
      -*D*) ask_local "Force-deleting a branch can lose unmerged commits." ;;
    esac
  done
  case "$joined" in
    *" --delete "*" --force "* | *" --force "*" --delete "* | *" -d "*" -f "* | *" -d --force "*)
      ask_local "Force-deleting a branch can lose unmerged commits." ;;
  esac
  for r in "$@"; do
    if is_main "$r" && [ -n "$LOCAL_ASK_REASON" ]; then ask "Force-deleting the main branch."; fi
  done
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

# Flags tack subcommands that change settings; reads (status, show, list, a lone name) pass.
check_tack() {
  local positional=0 a
  case "${1:-}" in
    trust | enable | disable | migrate) SETTINGS_WRITE="Changing tack's settings is the user's decision in this mode."; return ;;
    set)
      # A set in this project is the assistant's to activate; everywhere, and moving pins, is not.
      case "${2:-}" in
        update) SETTINGS_WRITE="Moving pinned skill sources is the user's decision in this mode." ;;
        use | drop)
          for a in "$@"; do
            [ "$a" != --global ] || SETTINGS_WRITE="Changing the sets active everywhere is the user's decision in this mode."
          done ;;
      esac ;;
    mode)
      case "${2:-}" in '' | list | show | new) return ;; esac
      SETTINGS_WRITE="Changing the workflow mode is the user's decision in this mode." ;;
    config)
      shift
      for a in "$@"; do
        case "$a" in --unset) positional=2 ;; --global | --shared | --get | --json) ;; *) positional=$((positional + 1)) ;; esac
      done
      # shellcheck disable=SC2034 # Read by guard-bash.sh after the analysis.
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
check_gh() {
  if [ "${1:-}" = repo ] && [ "${2:-}" = delete ]; then
    ask "This deletes a GitHub repository with its issues and pull requests. Confirm the repository."
    return 0
  fi
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
  cli="$(cd "$GUARD_DIR/../../bin" && pwd)/tack"
  (cd "$cwd" && "$cli" status --quiet) 2>/dev/null || return 0
  setting="$(cd "$cwd" && "$cli" config merge-requires-green --get 2>/dev/null)"
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
