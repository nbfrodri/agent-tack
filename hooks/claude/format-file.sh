#!/usr/bin/env bash
# Claude Code PostToolUse hook for Write/Edit/MultiEdit.
# Formats the edited file with the formatter the project already uses, only in projects where
# the harness is enabled and explicitly trusted in local git config, and only
# when the project has the formatter configured, so other repositories never get noisy diffs.
# Never blocks: always exits 0.
set -u

input="$(cat)"

file=""
if command -v jq >/dev/null 2>&1; then
  file="$(printf '%s' "$input" | jq -r '.tool_input.file_path // .tool_response.filePath // empty' 2>/dev/null)"
elif command -v python3 >/dev/null 2>&1; then
  file="$(printf '%s' "$input" | python3 -c '
import json, sys
d = json.load(sys.stdin)
print((d.get("tool_input") or {}).get("file_path") or (d.get("tool_response") or {}).get("filePath") or "")
' 2>/dev/null)"
fi
[ -n "$file" ] && [ -f "$file" ] || exit 0

cli="$(cd "$(dirname "$0")/../../bin" && pwd)/harness"
dir="$(cd "$(dirname "$file")" && pwd)" || exit 0
root="$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null)" || exit 0
(cd "$root" && "$cli" status --quiet && "$cli" trusted --quiet) || exit 0

has_file() {
  local f
  for f in "$@"; do
    [ -e "$root/$f" ] && return 0
  done
  return 1
}

# Runs a formatter quietly from the project root; failures are ignored on purpose
run() { (cd "$root" && "$@" >/dev/null 2>&1) || true; }

uses_prettier() {
  has_file .prettierrc .prettierrc.json .prettierrc.yaml .prettierrc.yml .prettierrc.json5 \
    .prettierrc.js .prettierrc.cjs .prettierrc.mjs .prettierrc.toml \
    prettier.config.js prettier.config.cjs prettier.config.mjs prettier.config.ts && return 0
  [ -f "$root/package.json" ] && grep -q '"prettier"[[:space:]]*:[[:space:]]*[{"]' "$root/package.json"
}

uses_ruff() {
  has_file ruff.toml .ruff.toml && return 0
  [ -f "$root/pyproject.toml" ] && grep -q '^\[tool\.ruff' "$root/pyproject.toml"
}

uses_black() {
  [ -f "$root/pyproject.toml" ] && grep -q '^\[tool\.black\]' "$root/pyproject.toml"
}

find_tool() {
  # Project-local binaries first, then PATH
  local name="$1" candidate
  for candidate in "$root/node_modules/.bin/$name" "$root/.venv/bin/$name" "$root/vendor/bin/$name"; do
    [ -x "$candidate" ] && { printf '%s' "$candidate"; return 0; }
  done
  command -v "$name" 2>/dev/null
}

case "$file" in
  *.js|*.jsx|*.ts|*.tsx|*.mjs|*.cjs|*.mts|*.cts|*.json|*.jsonc|*.css|*.scss|*.less|*.html|*.vue|*.svelte|*.astro|*.md|*.mdx|*.yaml|*.yml|*.graphql)
    if has_file biome.json biome.jsonc && [ -x "$root/node_modules/.bin/biome" ]; then
      run "$root/node_modules/.bin/biome" format --write "$file"
    elif uses_prettier && [ -x "$root/node_modules/.bin/prettier" ]; then
      run "$root/node_modules/.bin/prettier" --write --ignore-unknown "$file"
    fi
    ;;
  *.py|*.pyi)
    if uses_ruff && tool="$(find_tool ruff)" && [ -n "$tool" ]; then
      run "$tool" format "$file"
    elif uses_black && tool="$(find_tool black)" && [ -n "$tool" ]; then
      run "$tool" --quiet "$file"
    fi
    ;;
  *.php)
    if [ -x "$root/vendor/bin/pint" ]; then
      run "$root/vendor/bin/pint" "$file"
    fi
    ;;
  *.go)
    if command -v gofmt >/dev/null 2>&1; then
      run gofmt -w "$file"
    fi
    ;;
  *.rs)
    # rustfmt on the file only: `cargo fmt` would reformat the whole crate
    if [ -f "$root/Cargo.toml" ] && command -v rustfmt >/dev/null 2>&1; then
      edition="$(sed -n 's/^[[:space:]]*edition[[:space:]]*=[[:space:]]*"\([0-9]*\)".*/\1/p' "$root/Cargo.toml" | head -n 1)"
      run rustfmt --edition "${edition:-2021}" "$file"
    fi
    ;;
esac

exit 0
