#!/usr/bin/env bash
# `harness config`: list, read and write the feature toggles declared in features.txt.
set -u

registry="$1/features.txt"
shift

usage_error() { printf 'harness: %s (see --help)\n' "$1" >&2; exit 2; }
fail() { printf 'harness: %s\n' "$1" >&2; exit 1; }
in_repo() { git rev-parse --show-toplevel >/dev/null 2>&1; }

# Sets name, key, default, values, scope, enforcement and description for one feature.
load_feature() {
  local line
  line="$(awk -v wanted="$1" '$1 == wanted && $1 !~ /^#/ { print; exit }' "$registry")"
  [ -n "$line" ] || return 1
  read -r name key default values scope enforcement description <<EOF
$line
EOF
}

# Prints "value (source)": a project setting wins over the global one, then the default.
current() {
  local value
  if [ "$scope" != global ] && in_repo && value="$(git config --local --get "$key" 2>/dev/null)"; then
    printf '%s (local)\n' "$value"
  elif value="$(git config --global --get "$key" 2>/dev/null)"; then
    printf '%s (global)\n' "$value"
  else
    printf '%s (default)\n' "$default"
  fi
}

is_allowed() {
  case "$values" in
    bool) case "$1" in true | false) return 0 ;; *) return 1 ;; esac ;;
    number) printf '%s' "$1" | grep -qE '^[1-9][0-9]*$'; return ;;
    decimal) printf '%s' "$1" | grep -qE '^[0-9]+(\.[0-9]+)?$' && printf '%s' "$1" | grep -qE '[1-9]'; return ;;
    text) [ -n "$1" ]; return ;;
  esac
  case "|$values|" in *"|$1|"*) return 0 ;; *) return 1 ;; esac
}

allowed_text() {
  case "$values" in
    bool) echo 'true|false' ;;
    number) echo 'a positive integer' ;;
    decimal) echo 'a positive amount such as 5 or 2.50' ;;
    text) echo 'any non-empty value' ;;
    *) echo "$values" ;;
  esac
}

list() {
  local shown source name key default values scope enforcement description
  printf '%-24s%-10s%-9s%-12s%s\n' NAME VALUE SOURCE ENFORCEMENT DESCRIPTION
  while read -r name key default values scope enforcement description; do
    case "$name" in '' | '#'*) continue ;; esac
    shown="$(current)"
    source="${shown##*(}"
    printf '%-24s%-10s%-9s%-12s%s\n' "$name" "${shown% (*}" "${source%)}" "$enforcement" "$description"
  done < "$registry"
}

target_scope=local unset=false feature='' value='' options_done=false
for arg in "$@"; do
  if [ "$options_done" = false ]; then
    case "$arg" in
      --) options_done=true; continue ;;
      --global) target_scope=global; continue ;;
      --unset) unset=true; continue ;;
      -*) usage_error "unknown option for config: $arg (use -- before a value that starts with a dash)" ;;
    esac
  fi
  if [ -z "$feature" ]; then feature="$arg"
  elif [ -z "$value" ]; then value="$arg"
  else usage_error 'too many arguments for config'; fi
done

if [ -z "$feature" ]; then
  if [ "$unset" = true ] || [ "$target_scope" = global ]; then usage_error 'config needs a feature name'; fi
  list
  exit 0
fi
load_feature "$feature" || usage_error "unknown feature: $feature (run 'harness config' to list them)"
[ "$unset" = false ] || [ -z "$value" ] || usage_error '--unset takes no value'

if [ "$unset" = false ] && [ -z "$value" ]; then
  current
  exit 0
fi
if [ "$scope" = global ] && [ "$target_scope" = local ]; then
  usage_error "$name is a user-wide setting; add --global"
fi
if [ "$target_scope" = local ] && ! in_repo; then
  echo "harness: not inside a git repository" >&2
  exit 2
fi

if [ "$unset" = true ]; then
  if git config "--$target_scope" --get "$key" >/dev/null 2>&1; then
    git config "--$target_scope" --unset-all "$key" || fail "cannot unset $name"
  fi
  printf 'Removed the %s setting for %s; now %s.\n' "$target_scope" "$name" "$(current)"
  exit 0
fi
is_allowed "$value" || usage_error "invalid value for $name: $value (allowed: $(allowed_text))"
git config "--$target_scope" "$key" "$value" || fail "cannot set $name"
printf 'Set %s to %s (%s).\n' "$name" "$value" "$target_scope"
