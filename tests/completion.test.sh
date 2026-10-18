#!/usr/bin/env bash
# Completion queries, shell contexts and installer ownership in an isolated HOME.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/tack-completion.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
export HOME="$WORK/home" XDG_CONFIG_HOME="$WORK/config" XDG_STATE_HOME="$WORK/state" XDG_DATA_HOME="$WORK/data"
export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL="$HOME/.gitconfig"
unset GIT_CONFIG_COUNT GIT_CONFIG_SYSTEM
mkdir -p "$HOME" "$WORK/project" "$WORK/bin"
export PATH="$WORK/bin:$REPO/bin:$PATH"
cd "$WORK/project" || exit 1
git init -q
PASSED=0 FAILED=0
check() {
  if "$@"; then PASSED=$((PASSED + 1)); printf '  ✔ %s\n' "$*"
  else FAILED=$((FAILED + 1)); printf '  ✘ %s\n' "$*"; fi
}
has_line() { printf '%s\n' "$1" | grep -qxF -- "$2"; }
query_has() { has_line "$(tack __complete "$1" "${@:3}")" "$2"; }
reply() {
  bash -c 'source "$1/completions/tack.bash" || exit; shift; COMP_WORDS=("$@"); COMP_CWORD=$((${#COMP_WORDS[@]} - 1)); _tack; printf "%s\n" "${COMPREPLY[@]}"' _ "$REPO" "$@"
}
reply_has() { local wanted="$1"; shift; has_line "$(reply "$@")" "$wanted"; }
reply_lacks() { local wanted="$1"; shift; ! has_line "$(reply "$@")" "$wanted"; }
install_run() { bash "$REPO/install.sh" --skip-plugins --skip-mods --no-hooks "$@" > "$WORK/install.log" 2>&1; }
check reply_has set tack se
for word in list show use drop sync update suggest index skip reminder plan check agent; do
  check reply_has "$word" tack set ''
done
check reply_has writing tack set use ''
# tack-agents uses only local files; it never fetches or invokes an agent.
check tack set use tack-agents
check reply_lacks tack-agents tack set use ''
check reply_has tack-agents tack set drop ''
check reply_has --global tack set use ''
check reply_has writing tack set show ''
check reply_has writing tack set skip ''
check reply_has planner tack set agent ''
check reply_has writing tack set use --global ''
check reply_has reply-style tack config ''
for word in brief visual detailed normal terse; do check reply_has "$word" tack config reply-style ''; done
for word in --get --unset --global; do check reply_has "$word" tack config ''; done
check reply_has standard tack mode ''
for word in economical balanced strongest; do check reply_has "$word" tack models ''; done
for word in set get record statusline threshold hint; do check reply_has "$word" tack usage ''; done
for word in five_hour seven_day context; do check reply_has "$word" tack usage get ''; done
check reply_has --apply tack branches ''
for word in bash zsh fish; do check reply_has "$word" tack completion ''; done
check test -z "$(reply tack unknown '')"
check test -z "$(reply tack models balanced '')"
check test -z "$(reply tack set unknown '')"
check query_has commands completion
check query_has set-commands agent
check query_has sets-all core
check query_has sets-active tack-agents
check query_has sets-inactive writing
check query_has roles planner
check query_has features reply-style
check query_has feature-values visual reply-style
check query_has feature-values true completions
check test -z "$(tack __complete feature-values context-max-chars)"
check query_has modes auto
mkdir -p "$XDG_CONFIG_HOME/agent-tack/modes"
printf '# Custom\n' > "$XDG_CONFIG_HOME/agent-tack/modes/custom.md"
check query_has modes custom
check query_has tiers balanced
check query_has usage-kinds seven_day
check tack set skip writing
check test -z "$(tack __complete sets-inactive | grep -xE 'core|tack-skills|tack-agents|writing')"
git config --global tack.sets shell
check query_has sets-active shell
check test -z "$(tack __complete sets-inactive | grep -x shell)"
git config --global --unset tack.sets
check python3 -I - "$REPO/bin/tack" <<'PY'
import subprocess
import sys
import time
start = time.monotonic()
for _ in range(5):
    subprocess.run([sys.argv[1], '__complete', 'sets-inactive'], check=True, capture_output=True)
elapsed = (time.monotonic() - start) / 5
print(f'sets-inactive: {elapsed * 1000:.1f} ms average (5 runs)')
assert elapsed < 0.5, elapsed
for kind in ('commands', 'set-commands', 'sets-all', 'sets-active', 'roles',
             'features', 'feature-values', 'modes', 'tiers', 'usage-kinds'):
    start = time.monotonic()
    subprocess.run([sys.argv[1], '__complete', kind, 'reply-style'], check=True, capture_output=True)
    assert time.monotonic() - start < 0.5, kind
PY
for shell in bash fish zsh; do
  tack completion "$shell" > "$WORK/printed"
  check cmp -s "$WORK/printed" "$REPO/completions/tack.$shell"
done
invalid_shell() { tack completion invalid > "$WORK/invalid" 2>&1; [ "$?" -eq 2 ] && grep -q usage "$WORK/invalid"; }
check invalid_shell
check bash -n "$REPO/completions/tack.bash"
if command -v fish >/dev/null 2>&1; then check fish --no-execute "$REPO/completions/tack.fish"; else echo 'fish syntax: skipped (fish not installed)'; fi
if command -v zsh >/dev/null 2>&1; then check zsh -n "$REPO/completions/tack.zsh"; else echo 'zsh syntax: skipped (zsh not installed)'; fi
printf '#!/usr/bin/env bash\nexit 0\n' > "$WORK/bin/fish"
chmod +x "$WORK/bin/fish"
BASH_TARGET="$XDG_DATA_HOME/bash-completion/completions/tack"
FISH_TARGET="$XDG_CONFIG_HOME/fish/completions/tack.fish"
check install_run --dry-run
check test ! -e "$BASH_TARGET"
check test ! -e "$FISH_TARGET"
check grep -q 'would write.*completion' "$WORK/install.log"
check install_run
check cmp -s "$BASH_TARGET" "$REPO/completions/tack.bash"
check cmp -s "$FISH_TARGET" "$REPO/completions/tack.fish"
cp "$BASH_TARGET" "$WORK/before"
check install_run
check cmp -s "$BASH_TARGET" "$WORK/before"
printf '\n# personal edit\n' >> "$BASH_TARGET"
check install_run
check grep -q 'personal edit' "$BASH_TARGET"
check grep -q 'was edited' "$WORK/install.log"
check bash "$REPO/uninstall.sh"
check test ! -e "$FISH_TARGET"
check grep -q 'personal edit' "$BASH_TARGET"
rm "$BASH_TARGET"
check install_run
check bash "$REPO/uninstall.sh"
check test ! -e "$BASH_TARGET"
check test ! -e "$FISH_TARGET"
printf '# foreign\n' > "$BASH_TARGET"
check install_run
check grep -qx '# foreign' "$BASH_TARGET"
check grep -q 'not managed' "$WORK/install.log"
check bash "$REPO/uninstall.sh"
rm "$BASH_TARGET"
git config --global tack.completions false
check install_run
check test ! -e "$BASH_TARGET"
check test ! -e "$FISH_TARGET"
git config --global --unset tack.completions
# Exercise the step with fish absent, independently of the host's installed shells.
# shellcheck disable=SC2016
check bash -c '
  REPO="$1"; DRY_RUN=0; WORKDIR="$2"; source "$REPO/lib/keys.sh"; source "$REPO/lib/ownership.sh"; source "$REPO/lib/completion.sh" || exit
  flush_items() { :; }; ok() { :; }; warn() { :; }; fail() { return 1; }; item_new() { :; }; item_kept() { :; }
  has() { [ "$1" != fish ] && command -v "$1" >/dev/null; }
  ownership_init && install_completions
' _ "$REPO" "$WORK"
check test -f "$BASH_TARGET"
check test ! -e "$FISH_TARGET"
rm "$BASH_TARGET"
# shellcheck disable=SC2016
check bash -c '
  REPO="$1"; DRY_RUN=0; source "$REPO/lib/completion.sh" || exit
  flush_items() { :; }; ok() { :; }; warn() { printf "%s\n" "$*"; }; fail() { return 1; }
  key_get() { return 1; }; ownership_find() { OWN_ENTRY=""; }
  has() { [ "$1" != python3 ] && [ "$1" != fish ]; }
  install_completions
' _ "$REPO"
check test ! -e "$BASH_TARGET"
printf '\n%s passed, %s failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
