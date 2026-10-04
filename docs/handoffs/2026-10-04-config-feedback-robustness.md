# Configuration as data, feedback loops and tool robustness

- Status: in progress
- Branch: `feat/config-feedback-robustness` (from `main` at `4a7b55f`, after PR #33); local only
- Plan: `docs/plans/2026-10-04-config-feedback-robustness.md` (approved; unleash mode added)
- Done:
  - WS1: `449664b` feature registry and `harness config`; `53b3ad9` guard pattern rules in `guard-policy.txt` plus user additions.
  - WS5 (subagent): `af49ea1` merge of `feat/installer-robustness` (doctor `--tools`, targets capability columns, weekly compatibility CI). Codex agents/hooks adapters not written: formats known (agents TOML in `~/.codex/agents/`, hooks in `~/.codex/hooks.json`) but need a converter, ownership and payload checks.
  - WS6 (subagent): `e77f02b` merge of `feat/harness-mods` (mods in `plugins/`, local marketplace, `--skip-mods`, uninstall, doctor, CI).
  - Docs: `da8d0bf`, `4caa4f8`. Full suite green after both merges (705 checks + evals).
- Next: WS2 in order: modes as files and user modes; unleash (project-only, guard relaxation of local asks); tool-call budget hook; cost limit in usage-band; docs. Then WS3 feedback hooks, WS4 token efficiency, WS7 benchmark.
- Pending owner questions: delete the mod prototypes in `~/.claude/dev-mods/<session>/` before installing this branch (they would duplicate the installed mods); delete the merged local branches (`feat/adaptive-workflow-modes`, `feat/installer-robustness`, `feat/harness-mods`, `worktree-agent-*`) and agent worktrees.
- Process: avoid interpreter heredocs and shell loops in Bash calls; `git add` explicit paths (agent worktrees live in `.claude/worktrees/`, now ignored).
