#compdef tack
# Save as _tack in a directory on fpath, then run compinit.
_tack() {
  local command=${words[2]} kind='' extra='' word
  local -a args candidates
  local i
  args=()
  candidates=()
  if (( CURRENT == 2 )); then
    kind=commands
  else
    for ((i=3; i<CURRENT; i++)); do
      word=${words[i]}
      case "$command:$word" in
        config:--get|config:--unset|config:--global|set:--global) continue ;;
      esac
      args+=("$word")
    done
    case "$command:${#args}" in
      set:0) kind=set-commands ;;
      set:1)
        case ${args[1]} in
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
        case ${args[1]} in set|get|record|statusline|threshold|hint) kind=usage-kinds ;; esac ;;
      branches:0) extra=--apply ;;
      completion:0) extra='bash zsh fish' ;;
    esac
  fi
  if [[ -n $kind ]]; then
    candidates=("${(@f)$(tack __complete "$kind" "${args[1]:-}" 2>/dev/null)}")
  fi
  candidates+=(${=extra})
  compadd -- "${candidates[@]}"
}
compdef _tack tack
# An autoloaded _tack must also answer its first completion request.
if [[ ${funcstack[1]:-} == _tack ]]; then _tack "$@"; fi
