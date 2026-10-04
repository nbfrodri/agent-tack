# Adaptive workflow modes

- Status: in progress
- Branch: `feat/adaptive-workflow-modes` (local only; not pushed)
- Plan: `docs/plans/2026-10-04-adaptive-workflow-modes.md`
- Milestones: `a8b2431` plan; `afbc3ee` harness mode; `b16bd7f` mode-aware session context; `03265a3` workflow levels; `78bc3e1` stack conventions on demand; `ad70d4e` eval conditions per mode; `d056b35` docs; `9d2236f` eval prompts waive questions.
- Verified: validate, lifecycle (65), doctor (42), install (87), cli, hooks, evals suites and ShellCheck passed at their milestones.
- Since then: `847f38e` indexed startup context; `41e5ca5` impact mapping and minimal-change rules. Next phase recorded in the plan.
- Process note: avoid `python3 - <<heredoc` and shell `for` loops in Bash calls; the command guard asks for review on both. Use Edit/Write.
- `754e91c` handoff freshness check at session start.
- Benchmark running from frozen worktree `754e91c` (scratchpad `frozen/`), model `claude-sonnet-5-5`, launcher `scratchpad/run-modes-benchmark.py`, output `scratchpad/bench/` (raw transcripts private; report.md when complete). It stops on a provider usage limit.
- Next phase also includes CLI toggles (`harness config`) and user-defined modes (approved; see plan).
- Next (after benchmark): grade/report, then (bug-fix ×2 and new-project ×1 for baseline, lite, standard, strict, auto; 15 sessions, Sonnet), isolate HOME and all XDG paths, then update `docs/results.md` and the README results table.
