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
- Next: WS3 (help/docs drift test; opt-in fast check after edits; Stop hook for uncommitted work, failing check, stale handoff and docs map), WS4 token-efficiency rules, then full suite, review, PR (ask), WS7 benchmark.
- Pending owner questions: delete the mod prototypes in `~/.claude/dev-mods/<session>/` before installing this branch (they would duplicate the installed mods); delete the merged local branches (`feat/adaptive-workflow-modes`, `feat/installer-robustness`, `feat/harness-mods`, `worktree-agent-*`) and agent worktrees.
- Process: avoid interpreter heredocs and shell loops in Bash calls; `git add` explicit paths (agent worktrees live in `.claude/worktrees/`, now ignored).
