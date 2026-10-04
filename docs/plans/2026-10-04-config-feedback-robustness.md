# Configuration as data, feedback loops and tool robustness

- Status: approved 2026-10-04 (including the proposed delegation); mods install by default for Claude Code with `--skip-mods` and `harness config` opt-outs
- Level: strict (several modules, installer and hooks)
- Goal: make the harness configurable without code edits, give the agent fast deterministic feedback, survive AI tool changes, and measure the result once.
- Base: `main` after PR #33.

## Workstreams and acceptance criteria

1. **Configuration as data** (`harness config`)
   - A feature registry file (`features.txt`): name, git key, default, enforcement (`hook` or `instruction`), description.
   - `harness config` lists every feature with value, source (local, global, default) and enforcement; `harness config <name> <value> [--global]` sets, `--unset` removes. Existing keys (`context`, `delegation`, `conventionalCommits`) move behind it unchanged.
   - Secret scanning, the command guard and protected `main` are not general toggles; their one-off overrides stay.
   - Guard policy rules move to a versioned data file read by `guard-bash.sh`; behaviour unchanged, proven by the existing 56 guard tests.
2. **User-defined modes**
   - Each level is a short data file (`modes/lite.md`, `standard.md`, `strict.md`); `dev-workflow` keeps the shared flow.
   - User modes live in `~/.config/agent-harness/modes/` (outside the repo, survive updates); `harness mode new <name> --from <mode>` creates one; `harness mode <name>` validates against built-in and user files.
   - SessionStart injects the active mode's file; `auto` chooses among all modes, using each file's one-line "when to use".
3. **Feedback hooks**
   - PostToolUse after edits: run the project's fast check (`harness config check.fast "<command>"`, off by default, needs local trust like the formatter) and return failures to the agent.
   - Stop hook: warn about uncommitted work, a failing fast check, a stale handoff, or docs left untouched by the docs map.
   - Docs map (`docs-map.txt` per project: code globs → docs to review); drift test for `harness help` vs the CLI section of `docs/usage.md`.
4. **Token efficiency rules** in `dev-workflow` plus one global line (search before reading, read ranges, no re-reading, batch tool calls, trim output, targeted tests first, concise docs, economical delegated models, avoid guard-prompting commands).
5. **Installer robustness**
   - Research (2026-10-04, Codex 0.160.0, `codex features list`): `hooks` stable and on, `multi_agent` stable and on, `plugins` stable and on; `codex doctor` diagnoses installation, config and auth non-interactively. Add Codex hook and agent adapters where their formats are documented; confirm formats before writing them.
   - `targets.txt` gains capability columns (instructions, skills, agents, hooks) and an optional minimum version; adapters stay data.
   - `harness doctor --tools`: for each installed tool, version, configured capabilities and a non-interactive smoke check where the tool offers one.
   - Weekly CI workflow installing the latest Claude Code and Codex and running the smoke checks (no credentials; config discovery only).
6. **Mods shipped by the harness**
   - `usage-band` and `agent-activity` move into `plugins/` with their tests; the installer registers them for Claude Code; `uninstall.sh` and `doctor` know them; `claude plugin test` runs in CI when the CLI is available.
7. **Benchmark** (after 1–6): `bug-fix` ×2 and `new-project` ×1 for baseline, lite, standard, strict and auto, isolated as in the pilot; publish `docs/results.md` and the README table, including failures.

## Order and delegation

- Sequence: 1 → 2 (both touch `bin/harness`; one owner) → 3 → 4; 5 and 6 are independent of 1–4 after research.
- Proposed delegation after approval (strict level): main agent owns 1–4 (shared CLI and hooks); one implementer worktree for 5 (installer, `targets.txt`, doctor, CI); one for 6 (plugins, installer registration). Medium effort for 5 and 6, economical model for research. Integration, review and docs by the main agent.
- Each workstream ends in focused commits with tests first; handoff updated at every milestone.

## Risks

- Moving guard rules to data must not weaken the policy: no rule changes in the same commit as the move.
- Codex and Claude Code APIs change; research results are dated and the weekly CI is the safety net.
- Feedback hooks cost time per edit: fast check is opt-in and bounded by a timeout.
