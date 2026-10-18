#!/usr/bin/env bash
# Regression tests for `tack usage`: the 5-hour usage the usage band records, and the one offer
# to delegate to Codex per window once it passes delegate-usage-percent.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/tack-usage.XXXXXX")" || exit 1
trap 'rm -rf "$WORK"' EXIT
PASSED=0
FAILED=0
pass() { printf '  ✔ %s\n' "$1"; PASSED=$((PASSED + 1)); }
fail() { printf '  ✘ %s\n' "$1"; FAILED=$((FAILED + 1)); }
check() { local name="$1"; shift; if "$@"; then pass "$name"; else fail "$name"; fi; }

export HOME="$WORK/home" XDG_CONFIG_HOME="$WORK/home/.config" XDG_STATE_HOME="$WORK/home/.local/state" GIT_CONFIG_NOSYSTEM=1
mkdir -p "$HOME"
git config --global user.name 'Test User'
git config --global user.email 'test@example.com'

# A fake codex on PATH, and a PATH without any codex for the missing case.
FAKEBIN="$WORK/fake-codex"
mkdir -p "$FAKEBIN"
printf '#!/usr/bin/env bash\nexit 0\n' > "$FAKEBIN/codex"
chmod +x "$FAKEBIN/codex"
MINBIN="$WORK/bin-min"
mkdir -p "$MINBIN"
for tool in bash env mkdir dirname readlink ln rm mv date cp cmp mktemp sed basename git jq python3 stat chmod cat find grep tr wc head uname; do
  [ ! -x "$(command -v "$tool")" ] || ln -sf "$(command -v "$tool")" "$MINBIN/$tool"
done

usage() { env PATH="$FAKEBIN:$PATH" "$REPO/bin/tack" usage "$@" 2>&1; }
fails() { ! "$@" > /dev/null; }
usage_without_codex() { env PATH="$MINBIN" "$REPO/bin/tack" usage "$@" 2>&1; }

echo "tack usage set and get"
check "set records a percentage" usage set five_hour 62 2026-10-18T20:00:00Z
check "get prints it" test "$(usage get five_hour)" = 62
check "a percentage above 100 is refused" fails usage set five_hour 101
check "a non-number is refused" fails usage set five_hour lots
check "an unknown window is refused" fails usage set hourly 10

echo "tack usage hint"
usage set five_hour 30 2026-10-18T20:00:00Z >/dev/null
check "below the threshold there is no hint" test -z "$(usage hint)"
usage set five_hour 62 2026-10-18T20:00:00Z >/dev/null
hint="$(usage hint)"
check "past 50% the hint offers Codex" grep -q 'Codex' <<< "$hint"
check "the hint names the usage and the skill" grep -q '62%.*cross-delegate' <<< "$hint"
check "the same window is offered once" test -z "$(usage hint)"
usage set five_hour 80 2026-10-18T20:00:00Z >/dev/null
check "a higher reading in the same window stays silent" test -z "$(usage hint)"
usage set five_hour 55 2026-10-19T01:00:00Z >/dev/null
check "the next window is offered again" grep -q 'Codex' <<< "$(usage hint)"

echo "tack usage: the weekly window"
check "set records the weekly reading" usage set seven_day 58 2026-10-25T00:00:00Z
check "get prints the weekly reading" test "$(usage get seven_day)" = 58
usage set five_hour 10 2026-10-19T09:00:00Z >/dev/null
weekly="$(usage hint)"
check "weekly usage past 50% offers Codex and says it is the weekly limit" grep -q 'weekly limit is at 58%.*Codex' <<< "$weekly"
lacks() { ! grep -q -- "$1" <<< "$2"; }
check "the 5-hour window below the threshold is not mentioned" lacks '5-hour' "$weekly"
check "the same week is offered once" test -z "$(usage hint)"
usage set seven_day 70 2026-10-25T00:00:00Z >/dev/null
check "a higher weekly reading in the same week stays silent" test -z "$(usage hint)"
usage set seven_day 52 2026-11-01T00:00:00Z >/dev/null
check "the next week is offered again" grep -q 'weekly limit' <<< "$(usage hint)"
usage set five_hour 80 2026-10-19T14:00:00Z >/dev/null
usage set seven_day 90 2026-11-08T00:00:00Z >/dev/null
both="$(usage hint)"
offers_both() { grep -q '5-hour' <<< "$both" && grep -q 'weekly' <<< "$both"; }
check "both windows past the threshold are both offered" offers_both
usage set seven_day 30 2026-11-15T00:00:00Z >/dev/null

echo "tack usage record and statusline (Claude Code's status line input, no mod)"
STATUS='{"rate_limits":{"five_hour":{"used_percentage":23.5,"resets_at":1738425600},"seven_day":{"used_percentage":41.2,"resets_at":1738857600}}}'
status_in() { printf '%s' "$STATUS" | usage "$@"; }
status_in record > /dev/null
check "record stores the 5-hour reading, rounded" test "$(usage get five_hour)" = 24
check "record stores the weekly reading" test "$(usage get seven_day)" = 41
check "record prints nothing" test -z "$(status_in record)"
check "statusline prints both windows" test "$(status_in statusline)" = "5h 24% · 7d 41%"
check "no rate limits: statusline prints an empty line" test -z "$(printf '{"model":{}}' | usage statusline)"
# The status line runs in the project's directory: a json.py planted there must not be imported.
PLANT="$WORK/planted"
mkdir -p "$PLANT"
printf 'open("%s/pwned", "w").close()\n' "$WORK" > "$PLANT/json.py"
planted_in() { (cd "$PLANT" && printf '%s' "$STATUS" | env PATH="$FAKEBIN:$PATH" "$REPO/bin/tack" usage record > /dev/null 2>&1); }
planted_in
check "a json.py in the working directory is not imported" test ! -e "$WORK/pwned"
garbage_in() { printf 'not json' | usage statusline > /dev/null; }
check "garbage input is ignored and succeeds" garbage_in
STATUS='{"rate_limits":{"five_hour":{"used_percentage":64,"resets_at":1738512000}}}'
status_in record > /dev/null
check "a recorded reading past the threshold is offered" grep -q '5-hour limit is at 64%' <<< "$(usage hint)"
STATUS='{"rate_limits":{"five_hour":{"used_percentage":"lots","resets_at":1}}}'
status_in record > /dev/null
check "a non-numeric percentage is not recorded" test "$(usage get five_hour)" = 64

echo "tack usage context"
check "set context records a percentage" usage set context 60
check "get context prints it" test "$(usage get context)" = 60
check "fresh context prints it" test "$(usage context)" = 60
context_key="$(printf %s "$(pwd -P)" | cksum | cut -d ' ' -f1)"
context_file="$XDG_STATE_HOME/agent-tack/usage/context/$context_key"
check "context rejects percentages above 100" fails usage set context 101
check "context rejects non-numeric percentages" fails usage set context lots
# shellcheck disable=SC2016 # These are awk fields, not shell variables.
check "context uses three columns with empty resets" awk -F '\t' 'NF != 3 || $2 != "" {exit 1}' "$context_file"
ln -s "$PWD" "$WORK/project-link"
check "a symlink uses the physical directory key" test "$(cd "$WORK/project-link" && usage context)" = 60
mkdir -p "$(dirname "$context_file")"
printf '60\t\t%s\n' "$(( $(date +%s) - 601 ))" > "$context_file"
check "context older than 600 seconds is silent" test -z "$(usage context)"
check "get still prints stale context" test "$(usage get context)" = 60
printf '60\t\t%s\n' "$(date +%s)" > "$context_file"
OTHER="$WORK/other project"
mkdir -p "$OTHER"
check "another directory has no context" test -z "$(cd "$OTHER" && usage context)"
STATUS="{\"workspace\":{\"current_dir\":\"$OTHER\"},\"context_window\":{\"used_percentage\":61.8},\"rate_limits\":{\"five_hour\":{\"used_percentage\":24},\"seven_day\":{\"used_percentage\":41}}}"
check "statusline puts context first" test "$(status_in statusline)" = 'ctx 62% · 5h 24% · 7d 41%'
check "statusline keys context by workspace directory" test "$(cd "$OTHER" && usage context)" = 62
check "workspace reading leaves process directory unchanged" test "$(usage context)" = 60
STATUS='{"workspace":{"current_dir":"/nonexistent/tack-context"},"context_window":{"used_percentage":72.7}}'
check "context alone has no separator" test "$(status_in statusline)" = 'ctx 73%'
check "invalid workspace falls back to working directory" test "$(usage get context)" = 73
for value in null '"lots"' true '{}' '[]' NaN Infinity; do
  STATUS="{\"context_window\":{\"used_percentage\":$value}}"
  check "invalid context $value prints nothing" test -z "$(status_in statusline)"
  check "invalid context $value preserves previous reading" test "$(usage get context)" = 73
done
STATUS='{"workspace":{"current_dir":42},"context_window":{"used_percentage":12.8}}'
status_in record >/dev/null
check "non-string workspace falls back to working directory" test "$(usage context)" = 13
STATUS='{"context_window":{"used_percentage":140}}'
status_in record >/dev/null
check "record clamps context to 100" test "$(usage context)" = 100
STATUS='{"context_window":{"used_percentage":-2}}'
status_in record >/dev/null
check "record clamps context to zero" test "$(usage context)" = 0

echo "tack usage hint: when it stays silent"
usage set five_hour 90 2026-10-19T06:00:00Z >/dev/null
check "no codex installed: silent" test -z "$(usage_without_codex hint)"
git config --global tack.crossDelegation off
check "cross-delegation off: silent" test -z "$(usage hint)"
git config --global --unset tack.crossDelegation
git config --global tack.delegateUsagePercent off
check "delegate-usage-percent off: silent" test -z "$(usage hint)"
git config --global tack.delegateUsagePercent 95
check "a higher threshold is respected" test -z "$(usage hint)"
git config --global tack.delegateUsagePercent 85
check "a lower threshold offers" grep -q 'Codex' <<< "$(usage hint)"
git config --global --unset tack.delegateUsagePercent
usage set five_hour 90 2026-10-19T12:00:00Z >/dev/null
old=$(( $(date +%s) - 7200 ))
printf '90\t2026-10-19T12:00:00Z\t%s\n' "$old" > "$XDG_STATE_HOME/agent-tack/usage/five_hour"
check "a stale reading is not offered" test -z "$(usage hint)"

echo "tack usage threshold"
check "threshold prints the number the mod toasts at" test "$(usage threshold)" = 50
git config --global tack.delegateUsagePercent off
check "threshold is empty when the offer is off" test -z "$(usage threshold)"
git config --global --unset tack.delegateUsagePercent
check "threshold is empty without codex" test -z "$(usage_without_codex threshold)"

printf '\n%s passed, %s failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
