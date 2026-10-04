# Configuration as data, feedback loops and tool robustness

- Status: in progress
- Branch: `feat/config-feedback-robustness` (from `main` at `4a7b55f`, after PR #33); local only
- Plan: `docs/plans/2026-10-04-config-feedback-robustness.md` (approved; unleash mode added)
- Done:
  - WS1: `449664b` feature registry and `harness config`; `53b3ad9` guard pattern rules in `guard-policy.txt` plus user additions.
  - WS5 (subagent): `af49ea1` merge of `feat/installer-robustness` (doctor `--tools`, targets capability columns, weekly compatibility CI). Codex agents/hooks adapters not written: formats known (agents TOML in `~/.codex/agents/`, hooks in `~/.codex/hooks.json`) but need a converter, ownership and payload checks.
  - WS6 (subagent): `e77f02b` merge of `feat/harness-mods` (mods in `plugins/`, local marketplace, `--skip-mods`, uninstall, doctor, CI).
  - Docs: `da8d0bf`, `4caa4f8`. Full suite green after both merges (705 checks + evals).
  - WS2: `fba60c7` modes as files and user modes; `a7d6fc0` unleash (project-only; guard waives only `ask_local`); `b4c95fa` tool-call limit hook (`budget.sh`); `19081f9` cost limit in usage-band 0.2.0.
  - WS3: `574f484` help-vs-docs drift test; `d73b1b5` opt-in fast check after edits; `043c2d8` Stop hook (uncommitted work, failing check, stale handoff, docs map) with `docs-map.txt`.
  - WS4: `9d4d648` token-efficiency rules (dev-workflow, global line, orchestrate worktree lesson).
- Verified: full suite green at `df349d0` (797 checks + evals); ShellCheck clean. Installed on the real HOME from this branch (mods `usage-band` 0.2.0, `agent-activity` 0.1.0; doctor OK).
- Paused 2026-10-04 at the owner's request: 5-hour usage at 85%. Do not start the benchmark until usage resets.
- Resume steps, in order:
  1. Read the `code-reviewer` findings on `main...feat/config-feedback-robustness` (rerun the review if its result is lost); fix verified findings with tests, full suite and full ShellCheck.
  2. Benchmark: freeze the branch head in a scratchpad worktree; reuse the launcher pattern from the pilot (private HOME and XDG paths per session, `install.sh --skip-plugins`, `EVALS_MODEL=claude-sonnet-5-5`); `bug-fix` ×2 and `new-project` ×1 for baseline, lite, standard, strict, auto; stop on a usage limit. Watch the Stop hook's extra turns.
  3. Grade, update `docs/results.md`, the README results table and the AI log; mark the plan done.
  4. Ask the owner before push and PR.
- Avoid commands the guard asks about (interpreter heredocs, shell loops, chained opaque commands); the owner wants no confirmations.
- Cleanup done with the owner's approval: mod prototypes in `~/.claude/dev-mods/<session>/`, agent worktrees and the five merged local branches deleted. Older Codex-era branches and `/tmp` worktrees remain (not yet asked).
- Process: avoid interpreter heredocs and shell loops in Bash calls; `git add` explicit paths (agent worktrees live in `.claude/worktrees/`, now ignored).
