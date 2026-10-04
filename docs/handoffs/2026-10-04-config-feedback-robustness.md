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
- Usage note (2026-10-04): the owner's session auto-resumes after a usage reset, so keep working. The benchmark launcher is resumable: `scratchpad/run-final-benchmark.py <frozen> <rev> <out> claude-sonnet-5-5` skips completed sessions and exits 3 on a usage limit; relaunch it after the reset.
- Review done: findings fixed in `48f141f` (unleash waiver never applies after a directory change or `git -C/--git-dir/--work-tree`; settings writes refused in project-only modes; unleash refused on main; config literal match and `--`; stop-check timeout, no globbing, renames); recorded in `docs/audits/2026-10-04-review-config-feedback-robustness.md` (`845a648`). Full suite running after the fixes.
- Resume steps, in order:
  1. Done: full suite green at `93dc7ef` (820 checks + evals).
  2. Running: benchmark from frozen worktree `scratchpad/frozen-final` (`93dc7ef`), output `scratchpad/bench-final/` (log `launcher.log`). If it stopped (exit 3 or interrupted), relaunch the same command; completed sessions are skipped:
     `python3 scratchpad/run-final-benchmark.py scratchpad/frozen-final 93dc7ef scratchpad/bench-final claude-sonnet-5-5`
     Protocol: freeze the branch head in a scratchpad worktree; reuse the launcher pattern from the pilot (private HOME and XDG paths per session, `install.sh --skip-plugins`, `EVALS_MODEL=claude-sonnet-5-5`); `bug-fix` ×2 and `new-project` ×1 for baseline, lite, standard, strict, auto; stop on a usage limit. Watch the Stop hook's extra turns.
  3. Grade, update `docs/results.md`, the README results table and the AI log; mark the plan done.
  4. Ask the owner before push and PR.
- Avoid commands the guard asks about (interpreter heredocs, shell loops, chained opaque commands); the owner wants no confirmations.
- Cleanup done with the owner's approval: mod prototypes in `~/.claude/dev-mods/<session>/`, agent worktrees and the five merged local branches deleted. Older Codex-era branches and `/tmp` worktrees remain (not yet asked).
- Process: avoid interpreter heredocs and shell loops in Bash calls; `git add` explicit paths (agent worktrees live in `.claude/worktrees/`, now ignored).
