#!/usr/bin/env bash
# Private, non-executable ownership records shared by installer and uninstaller.

ownership_plain_path() {
  case "$1" in
    /*) ;;
    *) return 1 ;;
  esac
  case "$1" in *$'\n'*|*$'\r'*|*$'\t'*|*/../*|*/./*|*/..|*/.) return 1 ;; esac
}

ownership_no_symlinks() {
  local path="$1" floor="${2:-$HOME}"
  while [ "$path" != / ] && [ "$path" != "$floor" ]; do
    [ ! -L "$path" ] || return 1
    path="$(dirname "$path")"
  done
}

ownership_init() {
  local entry state_base="${XDG_STATE_HOME:-$HOME}"
  OWN_PATHS=() OWN_KINDS=() OWN_ENTRIES=()
  OWN_COUNT=0
  OWNERSHIP="${XDG_STATE_HOME:-$HOME/.local/state}/agent-harness/ownership"
  if ! ownership_plain_path "$HOME" || ! ownership_plain_path "$REPO" || ! ownership_plain_path "$OWNERSHIP"; then
    fail 'ownership requires absolute paths without tabs, newlines or dot components'; return 1
  fi
  ownership_no_symlinks "$OWNERSHIP" "$state_base" || { fail 'ownership state must not have symlink ancestors'; return 1; }
  if [ -e "$OWNERSHIP" ]; then
    if [ ! -d "$OWNERSHIP" ] || [ ! -f "$OWNERSHIP/version" ] || [ "$(cat "$OWNERSHIP/version")" != 1 ] ||
      [ "$(cat "$OWNERSHIP/home")" != "$HOME" ] || [ ! -d "$OWNERSHIP/entries" ]; then
      fail 'invalid ownership state; installation stopped'; return 1
    fi
    [ -z "$(find "$OWNERSHIP" -type l -print)" ] || { fail 'ownership state contains symlinks'; return 1; }
    [ -z "$(find "$OWNERSHIP" \( -type f ! -perm 0600 \) -o \( -type d ! -perm 0700 \))" ] || {
      fail 'ownership state permissions are not private'; return 1;
    }
    for entry in "$OWNERSHIP"/* "$OWNERSHIP"/entries/* "$OWNERSHIP"/entries/*/*; do
      [ ! -e "$entry" ] || [ -O "$entry" ] || { fail 'ownership state has another owner'; return 1; }
    done
    if has python3; then
      python3 "$REPO/lib/ownership.py" validate "$OWNERSHIP" "$HOME" || {
        fail 'ownership state failed integrity checks'; return 1;
      }
    fi
  fi
  for entry in "$OWNERSHIP"/entries/*; do
    [ -d "$entry" ] || continue
    OWN_PATHS[OWN_COUNT]="$(cat "$entry/path")"
    OWN_KINDS[OWN_COUNT]="$(cat "$entry/kind")"
    OWN_ENTRIES[OWN_COUNT]="$entry"
    OWN_COUNT=$((OWN_COUNT + 1))
  done
  [ "$DRY_RUN" -eq 0 ] || return 0
  (umask 077; mkdir -p "$OWNERSHIP/entries" && printf '1\n' > "$OWNERSHIP/version" &&
    printf '%s\n' "$HOME" > "$OWNERSHIP/home" && printf '%s\n' "$REPO" > "$OWNERSHIP/repo") || {
      fail 'cannot initialize ownership state'; return 1;
    }
}

ownership_find() {
  local kind="$1" path="$2" index=0
  OWN_ENTRY=''
  while [ "$index" -lt "$OWN_COUNT" ]; do
    if [ "${OWN_KINDS[$index]}" = "$kind" ] && [ "${OWN_PATHS[$index]}" = "$path" ]; then
      OWN_ENTRY="${OWN_ENTRIES[$index]}"
      return
    fi
    index=$((index + 1))
  done
}

ownership_begin() {
  local kind="$1" path="$2" n=1
  ownership_find "$kind" "$path"
  [ -z "$OWN_ENTRY" ] || return 0
  while [ -e "$OWNERSHIP/entries/$n" ]; do n=$((n + 1)); done
  OWN_ENTRY="$OWNERSHIP/entries/$n"
  OWN_PATHS[OWN_COUNT]="$path"
  OWN_KINDS[OWN_COUNT]="$kind"
  OWN_ENTRIES[OWN_COUNT]="$OWN_ENTRY"
  OWN_COUNT=$((OWN_COUNT + 1))
  (umask 077; mkdir "$OWN_ENTRY" && printf '%s\n' "$kind" > "$OWN_ENTRY/kind" &&
    printf '%s\n' "$path" > "$OWN_ENTRY/path" &&
    (cd "$(dirname "$path")" && pwd -P) > "$OWN_ENTRY/parent" &&
    ownership_parent_identity "$(cat "$OWN_ENTRY/parent")" > "$OWN_ENTRY/parent_identity" &&
    printf '%s\n' "$REPO" > "$OWN_ENTRY/repo" &&
    { [ "$kind" != link ] || cp "$REPO/targets.txt" "$OWN_ENTRY/targets"; })
}

ownership_parent_identity() {
  if has stat; then
    stat -c '%d:%i' "$1" 2>/dev/null || stat -f '%d:%i' "$1" 2>/dev/null
  elif has python3; then
    python3 -c 'import os,sys; s=os.stat(sys.argv[1]); print(str(s.st_dev)+":"+str(s.st_ino))' "$1"
  else
    printf 'unavailable\n'
  fi
}

ownership_link() {
  local path="$1" target="$2" backup_path="$3"
  ownership_begin link "$path" || return 1
  (umask 077
    if [ ! -f "$OWN_ENTRY/before_kind" ]; then
      if [ -L "$path" ]; then
        printf 'symlink\n' > "$OWN_ENTRY/before_kind"
        readlink "$path" > "$OWN_ENTRY/before_target"
      elif [ -e "$path" ]; then
        printf 'backup\n' > "$OWN_ENTRY/before_kind"
        printf '%s\n' "$backup_path" > "$OWN_ENTRY/backup"
      else
        printf 'absent\n' > "$OWN_ENTRY/before_kind"
      fi
    fi
    printf '%s\n' "$target" > "$OWN_ENTRY/target"
    printf '%s\n' "$REPO" > "$OWN_ENTRY/repo"
  )
}

ownership_settings() {
  local path="$1" merged="$2" managed="$3"
  ownership_begin settings "$path" || return 1
  (umask 077
    if [ ! -f "$OWN_ENTRY/before" ]; then
      if [ -e "$path" ]; then cp "$path" "$OWN_ENTRY/before"
      else printf '{}\n' > "$OWN_ENTRY/before"; printf '1\n' > "$OWN_ENTRY/was_absent"; fi
    fi
    [ -f "$OWN_ENTRY/after" ] || cp "$merged" "$OWN_ENTRY/after"
    cp "$managed" "$OWN_ENTRY/managed"
  )
}

ownership_git() {
  local path="$1" target="$2" previous="$3"
  ownership_begin git "$path" || return 1
  (umask 077
    if [ ! -f "$OWN_ENTRY/before" ]; then
      printf '%s' "$previous" > "$OWN_ENTRY/before"
      if git config --file "$path" --get core.hooksPath >/dev/null 2>&1; then
        printf '1\n' > "$OWN_ENTRY/before_present"
      fi
    fi
    printf '%s\n' "$target" > "$OWN_ENTRY/target"
  )
}
