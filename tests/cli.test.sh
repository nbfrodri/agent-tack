#!/usr/bin/env bash
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/harness-cli.XXXXXX")" || exit 1
trap 'rm -rf "$WORK"' EXIT
export HOME="$WORK/home" XDG_CONFIG_HOME="$WORK/home/.config" XDG_STATE_HOME="$WORK/home/.local/state" GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL="$WORK/home/gitconfig"
mkdir -p "$HOME" "$WORK/project/docs/handoffs"
git init -q "$WORK/project"
cd "$WORK/project" || exit 1
CLI="$REPO/bin/tack"
PASSED=0 FAILED=0
check() {
  local label="$1"
  shift
  if "$@"; then PASSED=$((PASSED + 1)); printf '  ✔ %s\n' "$label"
  else FAILED=$((FAILED + 1)); printf '  ✘ %s\n' "$label"; fi
}
expect_exit() {
  local expected="$1" actual
  shift
  "$@" > "$WORK/output" 2>&1
  actual=$?
  [ "$actual" -eq "$expected" ]
}
contains() { grep -qF -- "$1" "$WORK/output"; }
output_is() { [ "$(cat "$WORK/output")" = "$1" ]; }
expect_mode() { expect_exit 0 "$CLI" mode && output_is "$1"; }
expect_mode_like() { local expected="$1"; shift; expect_exit 0 "$@" && output_is "$expected"; }
expect_status() {
  local expected_exit="$1" workflow="$2" trust="$3" expected
  shift 3
  expect_exit "$expected_exit" "$CLI" "$@" || return 1
  expected="$(printf '%s\nmode: %s\nformatter trust: %s' "$workflow" "${EXPECTED_MODE:-auto (default)}" "$trust")"
  [ "$(cat "$WORK/output")" = "$expected" ]
}
excludes_completed() { ! grep -qF 'Do not include completed work' "$WORK/output"; }
bounded_context() { [ "$(wc -c < "$WORK/output")" -le 7000 ]; }
session() {
  python3 -c 'import json,sys; print(json.dumps({"cwd":sys.argv[1]}))' "$PWD" | bash "$REPO/hooks/claude/session-context.sh"
}
session_has_instructions() {
  python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert "Project \"instructions\"\\path" in d["hookSpecificOutput"]["additionalContext"]' "$WORK/output"
}

check "status shows disabled and untrusted independently" expect_status 1 disabled untrusted status
check "default command shows combined status" expect_status 1 disabled untrusted
check "disabled quiet status keeps its activation exit code" expect_exit 1 "$CLI" status --quiet
check "disabled quiet status emits no output" test ! -s "$WORK/output"
git config --local tack.enabled true
check "status shows enabled without formatter trust" expect_status 0 enabled untrusted status
check "enabled quiet status keeps its activation exit code" expect_exit 0 "$CLI" status --quiet
check "enabled quiet status emits no output" test ! -s "$WORK/output"
git config --local tack.trusted true
check "status shows enabled and locally trusted" expect_status 0 enabled trusted status
git config --local tack.enabled false
check "disabled workflow can retain local formatter trust" expect_status 1 disabled trusted status
git config --local --unset tack.enabled
git config --local --unset tack.trusted
cd "$WORK" || exit 1
check "outside a repository status is disabled and untrusted" expect_status 1 disabled untrusted status
check "help works outside a Git repository" expect_exit 0 "$CLI" help
check "help shows CLI invocation syntax" contains 'Usage: tack [command] [options]'
check "help documents the default command" contains 'Default command: status'
check "help lists both global help flags" contains '-h, --help'
cp "$WORK/output" "$WORK/help-output"
check "long help flag succeeds outside Git" expect_exit 0 "$CLI" --help
check "long help flag matches the help command" cmp -s "$WORK/output" "$WORK/help-output"
check "short help flag succeeds outside Git" expect_exit 0 "$CLI" -h
check "short help flag matches the help command" cmp -s "$WORK/output" "$WORK/help-output"
check "help rejects unsupported arguments" expect_exit 2 "$CLI" help unexpected
check "unknown command fails with a usage error" expect_exit 2 "$CLI" unknown-command
check "unknown command includes CLI invocation syntax" contains 'Usage: tack [command] [options]'
cd "$WORK/project" || exit 1

: > .git/config.lock
check "enable reports config write failure" expect_exit 1 "$CLI" enable
check "disable reports config write failure" expect_exit 1 "$CLI" disable
rm .git/config.lock
mkdir .tack
git config --global tack.enabled true
git config --local tack.enabled false
check "local opt-out overrides global activation" expect_exit 1 "$CLI" status --quiet
check "shared marker write failure is reported" expect_exit 1 "$CLI" enable --shared
check "failed shared enable preserves disabled status" expect_exit 1 "$CLI" status --quiet
check "failed shared enable preserves local opt-out" test "$(git config --local --get tack.enabled)" = false
git config --global --unset tack.enabled
rmdir .tack
check "unknown enable options are rejected" expect_exit 2 "$CLI" enable --typo
check "shared enable succeeds" expect_exit 0 "$CLI" enable --shared
check "shared marker grants no execution trust" expect_exit 1 "$CLI" trusted --quiet
git config --global tack.trusted true
check "global trust grants no execution trust" expect_exit 1 "$CLI" trusted --quiet
check "status ignores global formatter trust" expect_status 0 enabled untrusted status
check "local trust can be granted" expect_exit 0 "$CLI" trust
check "trusted status succeeds" expect_exit 0 "$CLI" trusted --quiet
check "standalone trusted query keeps its output and exit code" expect_exit 0 "$CLI" trusted
check "standalone trusted query prints trusted" test "$(cat "$WORK/output")" = trusted
check "trust can be revoked" expect_exit 0 "$CLI" trust --revoke
check "revoked trust refuses execution" expect_exit 1 "$CLI" trusted --quiet

check "mode defaults to auto" expect_mode 'auto (default)'
check "global mode can be set" expect_exit 0 "$CLI" mode lite --global
check "global mode applies to the project" expect_mode 'lite (global)'
check "project mode can be set" expect_exit 0 "$CLI" mode strict
check "project mode is stored locally" test "$(git config --local --get tack.mode)" = strict
check "project mode overrides the global default" expect_mode 'strict (local)'
check "global query ignores the project mode" expect_exit 0 "$CLI" mode --global
check "global query shows the global default" output_is 'lite (global)'
EXPECTED_MODE='strict (local)'
check "status shows the effective mode and its source" expect_status 0 enabled untrusted status
unset EXPECTED_MODE
check "project mode can be unset" expect_exit 0 "$CLI" mode --unset
check "unset project mode falls back to the global default" expect_mode 'lite (global)'
check "global option may come first" expect_exit 0 "$CLI" mode --global standard
check "global mode can be changed" expect_mode 'standard (global)'
check "global mode can be unset" expect_exit 0 "$CLI" mode --unset --global
check "unset global mode falls back to auto" expect_mode 'auto (default)'
check "unknown modes are rejected" expect_exit 2 "$CLI" mode turbo
check "rejected mode is not stored" test -z "$(git config --get tack.mode)"
check "extra mode arguments are rejected" expect_exit 2 "$CLI" mode lite strict
check "unknown mode options are rejected" expect_exit 2 "$CLI" mode --typo
git config --local tack.mode turbo
check "invalid stored mode behaves as auto and is reported" expect_mode "auto (invalid local value: turbo)"
git config --local --unset tack.mode
: > .git/config.lock
check "mode reports config write failure" expect_exit 1 "$CLI" mode lite
rm .git/config.lock
cd "$WORK" || exit 1
check "project mode requires a repository" expect_exit 2 "$CLI" mode lite
check "global mode works outside a repository" expect_exit 0 "$CLI" mode strict --global
check "mode outside a repository shows the global default" expect_mode 'strict (global)'
git config --global --unset tack.mode
check "help documents mode" expect_exit 0 "$CLI" help
check "help includes mode syntax" contains 'mode [MODE] [--global]'
check "help documents config" contains 'config [NAME [VALUE]] [--global]'
check "help documents user modes" contains 'mode new NAME --from MODE'
cd "$WORK/project" || exit 1

USER_MODES="$XDG_CONFIG_HOME/agent-tack/modes"
git config --local harness.mode strict
check "legacy harness.* keys are still honoured" expect_mode 'strict (local)'
git config --local tack.mode lite
check "tack.* keys win over legacy harness.* keys" expect_mode 'lite (local)'
check "setting a value succeeds" expect_exit 0 "$CLI" mode standard
check "writes go to the tack.* key" test "$(git config --local --get tack.mode)" = standard
check "writes remove the legacy key in that scope" test -z "$(git config --local --get harness.mode)"
git config --local --unset tack.mode
git config --local harness.delegation off
check "config reads legacy keys" expect_mode_like 'off (local)' "$CLI" config delegation
git config --local --unset harness.delegation
mkdir -p "$XDG_CONFIG_HOME/agent-harness/modes"
printf '# legacy\nWhen: an old user mode\nScope: any\n\n- Plan: none.\n' > "$XDG_CONFIG_HOME/agent-harness/modes/legacy.md"
check "user modes in the former config directory are still found" expect_exit 0 "$CLI" mode legacy
git config --local --unset tack.mode
rm -rf "$XDG_CONFIG_HOME/agent-harness"
check "mode list shows built-in modes" expect_exit 0 "$CLI" mode list
check "mode list shows each mode's purpose" contains 'lite      built-in  questions, typos'
check "mode list includes auto" contains 'auto      built-in'
check "a user mode can be created from another" expect_exit 0 "$CLI" mode new spike --from lite
check "the user mode lives in the user's config" test -f "$USER_MODES/spike.md"
check "the user mode is renamed" grep -q '^# spike$' "$USER_MODES/spike.md"
check "the user mode keeps the source rules" grep -q '^- Plan: none.$' "$USER_MODES/spike.md"
check "mode list includes user modes" expect_exit 0 "$CLI" mode list
check "user modes are labelled" contains 'spike     user'
check "a user mode can be selected" expect_exit 0 "$CLI" mode spike
check "the selected user mode is effective" expect_mode 'spike (local)'
git config --local --unset tack.mode
check "built-in names cannot be reused" expect_exit 2 "$CLI" mode new lite --from strict
check "existing user modes are not overwritten" expect_exit 2 "$CLI" mode new spike --from strict
check "mode names must be simple words" expect_exit 2 "$CLI" mode new 'bad/name' --from lite
check "the source mode must exist" expect_exit 2 "$CLI" mode new other --from nowhere
check "mode new needs --from" expect_exit 2 "$CLI" mode new other
git switch -q -c main 2>/dev/null || git switch -q main
check "unleash is refused on the main branch" expect_exit 2 "$CLI" mode unleash
git switch -q -c feat/autonomous
check "unleash can be selected for a project" expect_exit 0 "$CLI" mode unleash
check "unleash is effective locally" expect_mode 'unleash (local)'
git config --local --unset tack.mode
check "unleash refuses to become the global default" expect_exit 2 "$CLI" mode unleash --global
check "the refused global default is not stored" test -z "$(git config --global --get tack.mode)"
git config --global tack.mode unleash
check "an unleash default set by hand is ignored" expect_mode 'auto (unleash is project-only; global value ignored)'
git config --global --unset tack.mode
# shellcheck disable=SC2016 # Expanded by eval inside check.
check "user modes copied from unleash stay project-only" eval '"$CLI" mode new wild --from unleash >/dev/null && ! "$CLI" mode wild --global >/dev/null 2>&1'
# shellcheck disable=SC2016 # Expanded by eval inside check.
check "a deleted user mode falls back to auto" eval 'git config --local tack.mode gone && "$CLI" mode | grep -q "auto (invalid local value: gone)"'
git config --local --unset tack.mode

check "config lists every registered feature" expect_exit 0 "$CLI" config
check "config listing shows value, source and enforcement" contains 'conventional-commits    true      default  hook'
check "config listing includes instruction toggles" contains 'delegation              auto      default  instruction'
check "config listing includes installer toggles" contains 'mods                    true      default  installer'
check "config shows one feature" expect_exit 0 "$CLI" config delegation
check "config shows the default value and source" output_is 'auto (default)'
check "config sets a project value" expect_exit 0 "$CLI" config delegation off
check "config stores the project value under its git key" test "$(git config --local --get tack.delegation)" = off
check "config reports the project value" expect_mode_like 'off (local)' "$CLI" config delegation
check "config sets a global value" expect_exit 0 "$CLI" config context false --global
check "config stores the global value" test "$(git config --global --get tack.context)" = false
check "config reports the global source" expect_mode_like 'false (global)' "$CLI" config context
check "config unsets a project value" expect_exit 0 "$CLI" config delegation --unset
check "unset project value falls back to the default" expect_mode_like 'auto (default)' "$CLI" config delegation
check "config unsets a global value" expect_exit 0 "$CLI" config context --unset --global
check "config rejects unknown features" expect_exit 2 "$CLI" config turbo
check "feature names are matched literally, not as patterns" expect_exit 2 "$CLI" config '.*'
check "values may start with a dash after --" expect_exit 0 "$CLI" config check-fast -- "-x test"
check "the dash value is stored" test "$(git config --local --get tack.checkFast)" = "-x test"
git config --local --unset tack.checkFast
check "config rejects invalid values" expect_exit 2 "$CLI" config delegation sometimes
check "rejected value is not stored" test -z "$(git config --get tack.delegation)"
check "config rejects non-boolean values for boolean features" expect_exit 2 "$CLI" config context maybe
check "limits default to none" expect_mode_like 'none (default)' "$CLI" config unleash-max-tool-calls
check "number features accept positive integers" expect_exit 0 "$CLI" config unleash-max-tool-calls 200
check "number features reject decimals" expect_exit 2 "$CLI" config unleash-max-tool-calls 2.5
check "number features reject zero" expect_exit 2 "$CLI" config unleash-max-tool-calls 0
check "decimal features accept amounts" expect_exit 0 "$CLI" config unleash-max-cost 4.50
check "decimal features reject text" expect_exit 2 "$CLI" config unleash-max-cost cheap
check "decimal features reject zero" expect_exit 2 "$CLI" config unleash-max-cost 0.0
check "list features accept known items" expect_exit 0 "$CLI" config disabled-hooks "fast-check, stop-check"
check "list features reject an unknown item" expect_exit 2 "$CLI" config disabled-hooks "fast-check,fastcheck"
# shellcheck disable=SC2016 # Expanded by eval inside check; the command exits 2 by design.
check "list features name the allowed items" eval '[ -n "$("$CLI" config disabled-hooks nope 2>&1 | grep format-file)" ]'
check "list features reject the guard, which cannot be turned off" expect_exit 2 "$CLI" config disabled-hooks guard
git config --local --unset tack.disabledHooks
git config --local --unset tack.unleashMaxToolCalls
git config --local --unset tack.unleashMaxCost
check "global-only features refuse a project value" expect_exit 2 "$CLI" config mods false
check "global-only features accept a global value" expect_exit 0 "$CLI" config mods false --global
git config --global --unset tack.mods
# shellcheck disable=SC2016 # Expanded by eval inside check.
# Counts toggle names only, from the complete output: grep -q could stop the listing early and,
# under pipefail, a SIGPIPE in tack would hide a match.
check "config does not expose safety checks as toggles" eval '[ "$("$CLI" config | awk "NR > 1 { print \$1 }" | grep -ci "secret\|guard")" = 0 ]'
cd "$WORK" || exit 1
check "project config requires a repository" expect_exit 2 "$CLI" config delegation off
cd "$WORK/project" || exit 1

printf 'Project "instructions"\\path\n' > AGENTS.md
printf 'Architecture context\n' > docs/architecture.md
printf '# Handoff\nStatus: in progress\nNext: implement feature\n' > docs/handoffs/2026-10-03-active.md
printf '# Old handoff\nStatus: complete\nDo not include completed work\n' > docs/handoffs/2026-10-04-complete.md
check "context succeeds in enabled projects" expect_exit 0 "$CLI" context
check "context includes project instructions" contains 'Project "instructions"'
check "auto context indexes architecture instead of loading it" contains '- docs/architecture.md (1 lines)'
check "auto context omits architecture text" eval '! contains "Architecture context"'
check "auto context indexes the active handoff" contains '- Active handoff: docs/handoffs/2026-10-03-active.md'
check "auto context shows the handoff's next step" contains 'Next: implement feature'
check "auto context omits the handoff body" eval '! contains "# Handoff"'
check "context excludes completed handoffs" excludes_completed
git config --local tack.mode standard
check "standard context succeeds" expect_exit 0 "$CLI" context
check "standard context is an index too" contains '- docs/architecture.md (1 lines)'
git config --local --unset tack.mode
git config --local tack.mode lite
check "lite context succeeds" expect_exit 0 "$CLI" context
check "lite context keeps project instructions" contains 'Project "instructions"'
check "lite context skips architecture" eval '! contains "Architecture context"'
check "lite context still indexes the active handoff" contains '- Active handoff: docs/handoffs/2026-10-03-active.md'
check "lite context skips the handoff body" eval '! contains "# Handoff"'
git config --local tack.mode strict
check "strict context includes architecture" expect_exit 0 "$CLI" context
check "strict context includes architecture text" contains 'Architecture context'
check "strict context includes the handoff body" contains '# Handoff'
check "strict context reports handoff freshness" contains 'up to date: no commits since its last update'
git config --local --unset tack.mode
"$CLI" mode new deep --from lite >/dev/null
sed 's/^Context: minimal$/Context: full/' "$XDG_CONFIG_HOME/agent-tack/modes/deep.md" > "$WORK/deep.md" && mv "$WORK/deep.md" "$XDG_CONFIG_HOME/agent-tack/modes/deep.md"
git config --local tack.mode deep
check "a mode file's Context line decides the startup context" expect_exit 0 "$CLI" context
check "a user mode asking for full context gets excerpts" contains 'Architecture context'
git config --local tack.mode lean
check "lean context succeeds" expect_exit 0 "$CLI" context
check "lean context skips architecture" eval '! contains "Architecture context"'
git config --local --unset tack.mode
check "fresh handoff is reported up to date" expect_exit 0 "$CLI" context
check "fresh handoff says so" contains 'up to date: no commits since its last update'
touch -t 202001010000 docs/handoffs/2026-10-03-active.md
echo work > later-work.txt
git add later-work.txt
git -c user.name=T -c user.email=t@example.com commit -q -m 'feat: later work'
check "handoff older than new commits is flagged" expect_exit 0 "$CLI" context
check "stale handoff names the commit count" contains 'may be stale: 1 commit(s) since its last update'
touch -t 202001010000 docs/handoffs/2026-10-03-active.md
git add docs/handoffs/2026-10-03-active.md
git -c user.name=T -c user.email=t@example.com commit -q -m 'docs(handoffs): refresh'
check "committing the handoff itself counts as an update" expect_exit 0 "$CLI" context
check "committed handoff is up to date" contains 'up to date: no commits since its last update'
mkdir -p docs/plans
echo plan > docs/plans/2026-10-03-plan.md
git add docs/plans/2026-10-03-plan.md
GIT_COMMITTER_DATE="2030-01-01T00:00:00" git -c user.name=T -c user.email=t@example.com commit -q -m 'docs(plans): note a decision'
check "context after a plans-only commit succeeds" expect_exit 0 "$CLI" context
check "a commit that only touches plans or handoffs keeps the handoff up to date" contains 'up to date: no commits since its last update'
git rm -q docs/plans/2026-10-03-plan.md
GIT_COMMITTER_DATE="2030-01-01T00:00:01" git -c user.name=T -c user.email=t@example.com commit -q -m 'docs(plans): drop the note'
touch docs/handoffs/2026-10-03-active.md
# shellcheck disable=SC2016 # Literal Markdown backticks.
printf 'Branch: `feat/other`\n' >> docs/handoffs/2026-10-03-active.md
check "handoff for another branch is flagged" expect_exit 0 "$CLI" context
check "branch mismatch names both branches" contains "handoff names branch feat/other; current branch is $(git branch --show-current)"
printf '# Handoff\nStatus: in progress\nNext: implement feature\n' > docs/handoffs/2026-10-03-active.md
check "SessionStart returns valid JSON with project context" expect_exit 0 session
check "SessionStart preserves quotes and backslashes" session_has_instructions
mkdir -p "$HOME/.local/bin"
ln -s "$CLI" "$HOME/.local/bin/harness"
check "context works through the installed symlink" expect_exit 0 "$HOME/.local/bin/harness" context
check "the legacy harness alias runs tack" expect_exit 0 "$REPO/bin/harness" status --quiet
check "the alias stays silent when not run by a person" test ! -s "$WORK/output"
mkdir nested
cd nested || exit 1
check "context finds root from a nested directory" expect_exit 0 "$CLI" context
check "nested context indexes architecture" contains '- docs/architecture.md'
cd .. || exit 1
git config tack.context false
check "context can be disabled independently" expect_exit 0 "$CLI" context
check "opt-out emits no context" test ! -s "$WORK/output"
git config --unset tack.context
python3 - <<'PY' > AGENTS.md
print('x' * 20000)
PY
check "long context succeeds" expect_exit 0 "$CLI" context
check "context has a bounded size" bounded_context
python3 - <<'PY' > AGENTS.md
print('\u2603' * 4000)
PY
check "Unicode context succeeds" expect_exit 0 "$CLI" context
check "Unicode context respects the byte budget" bounded_context
rm AGENTS.md docs/architecture.md
check "missing documents are accepted" expect_exit 0 "$CLI" context
check "disabled project succeeds with no context" expect_exit 0 "$CLI" disable
check "disabled context succeeds" expect_exit 0 "$CLI" context
check "disabled context is empty" test ! -s "$WORK/output"

# Drift: every command the help lists must be documented, so docs cannot fall behind the CLI.
"$CLI" help | awk '/^Commands:/ { listing = 1; next } /^Global options:/ { listing = 0 }
  listing && /^  [a-z]/ { name = $1; if ($2 ~ /^(list|show|new|--[a-z]+)$/) name = name " " $2; print name }' > "$WORK/help-commands"
check "help lists commands for the drift check" test -s "$WORK/help-commands"
while IFS= read -r help_command; do
  check "usage docs cover 'tack $help_command'" grep -qF "tack $help_command" "$REPO/docs/usage.md"
done < "$WORK/help-commands"
check "usage docs cover 'tack doctor --tools'" grep -qF "tack doctor --tools" "$REPO/docs/usage.md"

check "doctor rejects unsupported arguments" expect_exit 2 "$CLI" doctor --quiet
check "help documents doctor" expect_exit 0 "$CLI" help
check "help includes doctor syntax" contains 'doctor'
cd "$HOME" || exit 1
check "doctor dispatches installation diagnostics outside Git" expect_exit 1 "$CLI" doctor
check "doctor diagnoses missing installed canonical link" contains "missing managed symlink: $HOME/.agents/harness"

# Reports over the activity log: a fixture with today's turns and one from long ago.
out_matches() { grep -Eq -- "$1" "$WORK/output"; }
out_lacks() { ! grep -q -- "$1" "$WORK/output"; }
LOG_FILE="$XDG_STATE_HOME/agent-tack/activity.log"
rm -f "$LOG_FILE"
check "reports without a log say how to turn it on" expect_exit 0 "$CLI" log --cost
check "the missing-log message names the setting" contains 'tack config activity-log true'
mkdir -p "$(dirname "$LOG_FILE")"
now="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
day="${now%%T*}"
{
  printf '%s\tclaude\t/p/app\tturn\tmodel=m1 input=500000 output=500000 cache_read=0 cache_write=0\n' "$now"
  printf '%s\tclaude\t/p/app\tturn\tmodel=m1 input=500000 output=500000 cache_read=0 cache_write=0\n' "$now"
  printf '%s\tcodex\t/p/app\tturn\tmodel=g1 input=10 output=20 cache_read=0 cache_write=0\n' "$now"
  printf '%s\tclaude\t/p/app\tskill\tdev-workflow\n' "$now"
  printf '%s\tclaude\t/p/app\tskill\tdev-workflow\n' "$now"
  printf '%s\tclaude\t/p/app\tagent\tcode-reviewer\n' "$now"
  printf '%s\tclaude\t/p/app\tlevel\tstrict touches auth\n' "$now"
  printf '%s\tclaude\t/p/app\tlevel\tmissing\n' "$now"
  printf '%s\tclaude\t/p/app\tguard deny\tgit commit --no-verify\n' "$now"
  printf '2020-01-01T00:00:00Z\tclaude\t/p/app\tturn\tmodel=m1 input=999 output=0 cache_read=0 cache_write=0\n'
} > "$LOG_FILE"
check "cost report runs" expect_exit 0 "$CLI" log --cost
check "cost report sums tokens per day, project, tool and model" out_matches "^$day +/p/app +claude +m1 +1000000 +1000000 +0 +0 +-"
check "cost report keeps other tools and models apart" out_matches "^$day +/p/app +codex +g1 +10 +20"
check "cost report covers the last 30 days by default" out_lacks "2020-01-01"
check "cost report reaches further back with --days" expect_exit 0 "$CLI" log --cost --days 100000
check "older turns appear with a wider window" contains '2020-01-01'
check "a window wider than the log says where the log starts" contains 'The log only goes back to 2020-01-01'
mkdir -p "$XDG_CONFIG_HOME/agent-tack"
printf '# model | input | output | cache read | cache write (USD per million tokens)\nm1 | 1 | 2 | 0.1 | 1.25\n' > "$XDG_CONFIG_HOME/agent-tack/pricing.txt"
check "cost report with user prices runs" expect_exit 0 "$CLI" log --cost
check "user prices turn tokens into dollars" out_matches "^$day +/p/app +claude +m1 .* 3\.00$"
check "models without a price show no amount" out_matches "^$day +/p/app +codex +g1 .* -$"
check "cost report as CSV runs" expect_exit 0 "$CLI" log --cost --csv
check "CSV starts with its header" out_matches "^day_utc,project,tool,model,input,output,cache_read,cache_write,usd$"
check "skills report runs" expect_exit 0 "$CLI" log --skills
check "skills report counts each skill" out_matches "^skill +dev-workflow +2$"
check "skills report counts subagents" out_matches "^agent +code-reviewer +1$"
check "skills report lists what was never used" out_matches "^Never used.*testing"
check "levels report runs" expect_exit 0 "$CLI" log --levels
check "levels report counts levels per project" out_matches "^/p/app +strict +1$"
check "levels report shows turns without a stated level" out_matches "^/p/app +missing +1$"
check "reports reject a bad window" expect_exit 2 "$CLI" log --cost --days soon
check "log rejects unknown options" expect_exit 2 "$CLI" log --bogus
check "log rejects --csv without a report" expect_exit 2 "$CLI" log --csv
check "log rejects a count with a report" expect_exit 2 "$CLI" log 5 --cost
check "log rejects two counts" expect_exit 2 "$CLI" log 5 6
printf 'm1 | \377 | 2 | 0 | 0\n' > "$XDG_CONFIG_HOME/agent-tack/pricing.txt"
check "a price file in another encoding never crashes the report" expect_exit 0 "$CLI" log --cost
rm -f "$LOG_FILE" "$XDG_CONFIG_HOME/agent-tack/pricing.txt"

# tack lesson: candidate lessons counted across sessions (docs/adr/0001-candidate-lessons.md).
LESSONS="$XDG_STATE_HOME/agent-tack/lessons.tsv"
is_private() { [ -n "$(find "$1" -perm 600 2>/dev/null)" ]; }
rm -f "$LESSONS"
cd "$WORK/project" || exit 1
check "a first note records a candidate" expect_exit 0 "$CLI" lesson note use-pnpm "Use pnpm, not npm: the workspace depends on it."
check "notes are private to the user" is_private "$LESSONS"
check "listing shows the candidate once seen" expect_exit 0 "$CLI" lesson list
check "a candidate shows its count and text" out_matches "^use-pnpm +project +1 +0 +Use pnpm, not npm"
"$CLI" lesson note use-pnpm "Use pnpm, not npm: the workspace depends on it." >/dev/null
"$CLI" lesson note use-pnpm "Use pnpm, not npm, in this monorepo." >/dev/null
check "repeats add up and keep the newest wording" expect_exit 0 "$CLI" lesson list
check "three sightings make a candidate ready to promote" out_matches "^use-pnpm +project +3 +0 +ready +Use pnpm, not npm, in this monorepo\.$"
check "contradicting a candidate records evidence against it" expect_exit 0 "$CLI" lesson contradict use-pnpm
check "listing after a contradiction runs" expect_exit 0 "$CLI" lesson list
check "contradicted candidates are no longer ready" out_matches "^use-pnpm +project +3 +1 +Use pnpm"
check "user-wide notes are kept apart from project ones" expect_exit 0 "$CLI" lesson note terse-replies "Keep replies short." --global
check "listing with a user-wide note runs" expect_exit 0 "$CLI" lesson list
check "user-wide notes are listed as global" out_matches "^terse-replies +global +1"
check "keys must be kebab-case" expect_exit 2 "$CLI" lesson note "Use pnpm" "text"
check "a note needs its text" expect_exit 2 "$CLI" lesson note use-pnpm
check "forgetting removes a candidate" expect_exit 0 "$CLI" lesson forget use-pnpm
check "listing after forgetting runs" expect_exit 0 "$CLI" lesson list
check "a forgotten candidate is gone" out_lacks "use-pnpm"
check "forgetting an unknown key fails" expect_exit 1 "$CLI" lesson forget nope
check "unknown lesson commands are rejected" expect_exit 2 "$CLI" lesson teach
check "backslashes in a rule are kept as written" expect_exit 0 "$CLI" lesson note win-paths 'Use C:\new\temp and \\server paths.'
line_count_is() { [ "$(grep -c "" "$1")" = "$2" ]; }
check "the store keeps one line per candidate" line_count_is "$LESSONS" 2
check "listing a backslash rule runs" expect_exit 0 "$CLI" lesson list
check "a backslash rule is listed verbatim" contains 'Use C:\new\temp and \\server paths.'
check "contradict finds a user-wide candidate without --global" expect_exit 0 "$CLI" lesson contradict terse-replies
check "forget finds a user-wide candidate without --global" expect_exit 0 "$CLI" lesson forget terse-replies
"$CLI" lesson forget win-paths >/dev/null
printf 'other-key\t/elsewhere/repo\t3\t0\t2026-10-01\tSomeone else.\n' >> "$LESSONS"
check "listing with only other projects' candidates runs" expect_exit 0 "$CLI" lesson list
check "a project without candidates says so" contains 'No candidate lessons'
# $WORK holds a dot; the same path with that dot replaced only matches if the scope is a regex.
printf 'dot-key\t%s\t1\t0\t2026-10-01\tA lookalike path.\n' "$(printf '%s' "$WORK/project" | tr '.' 'x')" >> "$LESSONS"
check "a scope that only matches as a pattern is not this project's" expect_exit 1 "$CLI" lesson forget dot-key
rm -f "$LESSONS"
cd "$HOME" || exit 1

# tack trace: requirement IDs in the plan against the tests that name them.
TRACE="$WORK/trace-repo"
git init -q "$TRACE"
mkdir -p "$TRACE/docs/plans" "$TRACE/tests" "$TRACE/src"
cat > "$TRACE/docs/plans/2026-10-01-login.md" <<'EOF'
# Login
## Acceptance criteria
- R1: a wrong password is rejected with 401
- **R2**: five failures lock the account for 15 minutes
- R3: a locked account says when it unlocks
Later prose mentions R1 again; that is not a new requirement.
EOF
printf 'def test_wrong_password_R1():\n    pass\n' > "$TRACE/tests/test_login.py"
printf '// R2: lockout after five failures\ntest("locks", () => {})\n' > "$TRACE/tests/lockout.test.js"
printf '# R3 is mentioned in code, not in a test\n' > "$TRACE/src/login.py"
printf 'def test_old_R9():\n    pass\n' > "$TRACE/tests/test_legacy.py"
git -C "$TRACE" add -A
trace() { (cd "$TRACE" && "$CLI" trace "$@"); }
check "trace fails when a requirement has no test" expect_exit 1 trace
check "trace lists covered requirements with their tests" out_matches "^R1 +covered +tests/test_login.py"
check "trace lists every test that names a requirement" out_matches "^R2 +covered +tests/lockout.test.js"
check "trace names the requirement without a test" out_matches "^R3 +MISSING +a locked account says when it unlocks"
check "trace ignores IDs outside test files" out_lacks "src/login.py"
check "trace warns about tests tied to a requirement the plan lacks" contains 'R9 is named in tests/test_legacy.py but not in the plan'
printf 'def test_unlock_message_R3():\n    pass\n' > "$TRACE/tests/test_unlock.py"
git -C "$TRACE" add -A
check "trace passes once every requirement has a test" expect_exit 0 trace
check "trace takes a plan path" expect_exit 0 trace docs/plans/2026-10-01-login.md
check "trace rejects a missing plan" expect_exit 2 trace docs/plans/nope.md
trace_from_docs() { (cd "$TRACE/docs" && "$CLI" trace "$@"); }
check "trace resolves a relative plan from the current directory" expect_exit 0 trace_from_docs plans/2026-10-01-login.md
cat > "$TRACE/docs/plans/2026-10-02-checklist.md" <<'EOF'
## Acceptance criteria
- [ ] R1: a wrong password is rejected with 401
- [x] **R2**: five failures lock the account
1. R3: a locked account says when it unlocks
EOF
check "trace reads checkbox and numbered requirements" expect_exit 0 trace docs/plans/2026-10-02-checklist.md
check "checkbox requirements are listed" out_matches "^R1 +covered"
printf 'def test_R4a_variant():\n    pass\n' > "$TRACE/tests/test_variant.py"
printf -- '- R4: exports a report\n' >> "$TRACE/docs/plans/2026-10-02-checklist.md"
git -C "$TRACE" add -A
check "an ID followed by a letter does not cover the requirement" expect_exit 1 trace docs/plans/2026-10-02-checklist.md
rm -rf "$TRACE/docs/plans"
check "trace without a plan explains itself" expect_exit 2 trace

printf '\n%s passed, %s failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
