# Adaptive workflow modes

- Status: in progress (PR open; merge awaits CI and the owner's choice of method)
- Branch: `feat/adaptive-workflow-modes`, pushed; [PR #33](https://github.com/nbfrodri/agent-harness/pull/33). Recommended merge method: merge commit (each commit is a verified milestone).
- Plan: `docs/plans/2026-10-04-adaptive-workflow-modes.md` (includes the approved next phase)
- Done: modes CLI, mode-aware and indexed startup context, handoff freshness check, workflow levels, impact/minimal-change rules, eval conditions per mode, docs. Pilot benchmark found an eval permission defect (`3cb889e`) and a core-rules regression (`a572920`), both fixed; see `docs/benchmarks/2026-10-04-modes-pilot.md`.
- Owner decision: integrate this branch, implement the next phase on a new branch (strict plan, approval first), then run one benchmark over everything.
- Pending owner request: Claude Code mods (live 5h/weekly usage display; a second "show what's behind" mod to clarify), possibly shipped by the harness.
- Process note: avoid interpreter heredocs and shell loops in Bash calls; the guard asks about both.
