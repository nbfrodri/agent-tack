#!/usr/bin/env bash
# Workflow modes as data: built-in files in modes/, user files in the user's config directory.
# Sourced by bin/tack, which sets TACK_ROOT to the checkout.

user_modes_dir() { printf '%s/modes\n' "$(tool_dir "${XDG_CONFIG_HOME:-$HOME/.config}")"; }

# Prints the file that defines a mode; built-in names cannot be shadowed by user files.
mode_file() {
  case "$1" in '' | *[!a-z0-9-]*) return 1 ;; esac
  # lean was merged into lite (#99); the name keeps working until tack migrate rewrites it.
  [ "$1" != lean ] || set -- lite
  if [ -f "$TACK_ROOT/modes/$1.md" ]; then printf '%s\n' "$TACK_ROOT/modes/$1.md"
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

# Local override, shared project choice, then personal default. Invalid legacy Git
# values fall back to auto; invalid shared profiles report an error.
effective_mode() {
  local scope value
  [ "$#" -gt 0 ] || set -- local shared global
  for scope in "$@"; do
    if [ "$scope" = shared ]; then
      local project status
      project="$(git rev-parse --show-toplevel 2>/dev/null)" || continue
      if [ ! -e "$project/tack.json" ] && [ ! -L "$project/tack.json" ]; then continue; fi
      value="$(python3 "$TACK_ROOT/lib/project_config.py" "$TACK_ROOT" shared-mode)"
      status=$?
      [ "$status" -ne 1 ] || continue
      [ "$status" -eq 0 ] || return 2
    else
      value="$(key_get "$scope" mode)" || continue
    fi
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
  for file in "$TACK_ROOT"/modes/*.md "$(user_modes_dir)"/*.md; do
    [ -f "$file" ] || continue
    name="$(basename "$file" .md)"
    case "$file" in "$TACK_ROOT"/*) source_label=built-in ;; *) source_label=user ;; esac
    printf '%-10s%-10s%s\n' "$name" "$source_label" "$(mode_field "$file" When)"
  done
}

# How much startup context the effective mode wants: minimal, index (default) or full.
context_level() {
  local mode file level
  mode="$(effective_mode)"
  mode="${mode%% *}"
  file="$(mode_file "$mode" 2>/dev/null)" || { echo index; return; }
  level="$(mode_field "$file" Context)"
  case "$level" in minimal | index | full) echo "$level" ;; *) echo index ;; esac
}

# The rules of the effective mode for startup context; auto lists every mode to choose from.
show_mode() {
  local mode file
  mode="$(effective_mode)"
  mode="${mode%% *}"
  if [ "$mode" = auto ]; then
    echo 'Modes to choose from:'
    for file in "$TACK_ROOT"/modes/*.md "$(user_modes_dir)"/*.md; do
      [ -f "$file" ] || continue
      printf -- '- %s: %s\n' "$(basename "$file" .md)" "$(mode_field "$file" When)"
    done
    # Small models judged a URL-to-file-path task "small and well defined" and picked lite.
    echo 'Pick by risk, not size: code that handles untrusted input (URLs, file paths, uploads, queries, shell commands), auth, payments or deleting data is never lite or lean.'
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
  case "$name" in '' | auto | *[!a-z0-9-]*) echo "tack: mode names use lowercase letters, digits and dashes" >&2; return 2 ;; esac
  if mode_file "$name" >/dev/null; then echo "tack: mode '$name' already exists" >&2; return 2; fi
  source="$(mode_file "$from")" || { echo "tack: unknown source mode '$from'" >&2; return 2; }
  mkdir -p "$(user_modes_dir)" || return 1
  target="$(user_modes_dir)/$name.md"
  { printf '# %s\n' "$name"; sed '1d' "$source"; } > "$target" || return 1
  echo "Created $target from $from; edit it, then run 'tack mode $name'."
}
