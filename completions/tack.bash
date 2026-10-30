# tack completion: source this file or let bash-completion load it lazily.
_tack() {
  local current="${COMP_WORDS[COMP_CWORD]}" command="${COMP_WORDS[1]:-}" kind='' extra='' word
  local args=() i
  COMPREPLY=()
  if [ "$COMP_CWORD" -eq 1 ]; then
    kind=commands
  else
    # Ignore supported switches when locating the positional argument.
    for ((i=2; i<COMP_CWORD; i++)); do
      word="${COMP_WORDS[i]}"
      case "$command:$word" in
        config:--get|config:--unset|config:--global|set:--global) continue ;;
      esac
      args+=("$word")
    done
    case "$command:${#args[@]}" in
      set:0) kind=set-commands ;;
      set:1)
        case "${args[0]}" in
          use) kind=sets-inactive; extra=--global ;;
          drop) kind=sets-active; extra=--global ;;
          show|skip) kind=sets-all ;;
          agent) kind=roles ;;
        esac ;;
      config:0) kind=features; extra='--get --unset --global' ;;
      config:1) kind=feature-values; extra='--get --unset --global' ;;
      mode:0) kind=modes ;;
      models:0) kind=tiers ;;
      usage:0) extra='set get record statusline threshold hint' ;;
      usage:1)
        case "${args[0]}" in set|get|record|statusline|threshold|hint) kind=usage-kinds ;; esac ;;
      branches:0) extra=--apply ;;
      update:*) extra='--check --force --skip-plugins --skip-mods --no-hooks --verbose' ;;
      completion:0) extra='bash zsh fish' ;;
    esac
  fi
  # Read lines without eval or word splitting; only fixed flags use splitting below.
  if [ -n "$kind" ]; then
    while IFS= read -r word; do
      case "$word" in "$current"*) COMPREPLY+=("$word") ;; esac
    done < <(tack __complete "$kind" "${args[0]:-}" 2>/dev/null)
  fi
  for word in $extra; do
    case "$word" in "$current"*) COMPREPLY+=("$word") ;; esac
  done
  return 0
}
complete -F _tack tack
