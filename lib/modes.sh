#!/usr/bin/env bash
# Workflow modes as data: built-in files in modes/, user files in the user's config directory.
# Sourced by bin/harness, which sets HARNESS_ROOT to the checkout.

user_modes_dir() { printf '%s/agent-harness/modes\n' "${XDG_CONFIG_HOME:-$HOME/.config}"; }

# Prints the file that defines a mode; built-in names cannot be shadowed by user files.
mode_file() {
  case "$1" in '' | *[!a-z0-9-]*) return 1 ;; esac
  if [ -f "$HARNESS_ROOT/modes/$1.md" ]; then printf '%s\n' "$HARNESS_ROOT/modes/$1.md"
  elif [ -f "$(user_modes_dir)/$1.md" ]; then printf '%s\n' "$(user_modes_dir)/$1.md"
  else return 1; fi
}

is_mode() { [ "$1" = auto ] || mode_file "$1" >/dev/null; }

mode_field() { sed -n "s/^$2:[[:space:]]*//p" "$1" | head -n 1; }

# Project-only modes (Scope: project) are too risky to apply to every repository at once.
is_project_only() {
  local file
  file="$(mode_file "$1")" || return 1
  [ "$(mode_field "$file" Scope)" = project ]
}

# Prints the effective mode and where it comes from: a project setting wins over the
# user's global default. Invalid values behave as auto so a typo never blocks work.
effective_mode() {
  local scope value
  [ "$#" -gt 0 ] || set -- local global
  for scope in "$@"; do
    value="$(git config "--$scope" --get harness.mode 2>/dev/null)" || continue
    if [ "$scope" = global ] && is_project_only "$value"; then
      printf 'auto (%s is project-only; global value ignored)\n' "$value"
    elif is_mode "$value"; then printf '%s (%s)\n' "$value" "$scope"
    else printf 'auto (invalid %s value: %s)\n' "$scope" "$value"; fi
    return
  done
  echo 'auto (default)'
}

list_modes() {
  local file name
  printf '%-10s%-10s%s\n' auto built-in 'the assistant picks a mode per task and states it'
  for file in "$HARNESS_ROOT"/modes/*.md "$(user_modes_dir)"/*.md; do
    [ -f "$file" ] || continue
    name="$(basename "$file" .md)"
    case "$file" in "$HARNESS_ROOT"/*) source_label=built-in ;; *) source_label=user ;; esac
    printf '%-10s%-10s%s\n' "$name" "$source_label" "$(mode_field "$file" When)"
  done
}

# The rules of the effective mode for startup context; auto lists every mode to choose from.
show_mode() {
  local mode file
  mode="$(effective_mode)"
  mode="${mode%% *}"
  if [ "$mode" = auto ]; then
    echo 'Modes to choose from:'
    for file in "$HARNESS_ROOT"/modes/*.md "$(user_modes_dir)"/*.md; do
      [ -f "$file" ] || continue
      printf -- '- %s: %s\n' "$(basename "$file" .md)" "$(mode_field "$file" When)"
    done
    return
  fi
  file="$(mode_file "$mode")" || return 0
  if is_project_only "$mode"; then
    printf 'WARNING: %s mode is active: autonomous work without confirmations in this project. The command guard still refuses dangerous commands; keep to the safety floor below.\n' "$mode"
  fi
  printf 'Mode %s rules:\n' "$mode"
  sed -n '/^- /p' "$file" | head -n 30 | cut -c1-400
}

new_mode() {
  local name="$1" from="$2" source target
  case "$name" in '' | auto | *[!a-z0-9-]*) echo "harness: mode names use lowercase letters, digits and dashes" >&2; return 2 ;; esac
  if mode_file "$name" >/dev/null; then echo "harness: mode '$name' already exists" >&2; return 2; fi
  source="$(mode_file "$from")" || { echo "harness: unknown source mode '$from'" >&2; return 2; }
  mkdir -p "$(user_modes_dir)" || return 1
  target="$(user_modes_dir)/$name.md"
  { printf '# %s\n' "$name"; sed '1d' "$source"; } > "$target" || return 1
  echo "Created $target from $from; edit it, then run 'harness mode $name'."
}
