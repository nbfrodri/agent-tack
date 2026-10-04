# Adaptive workflow modes

- Status: in progress
- Branch: `feat/adaptive-workflow-modes` (local only; not pushed)
- Plan: `docs/plans/2026-10-04-adaptive-workflow-modes.md`
- Milestones: `a8b2431` plan; `afbc3ee` harness mode; `b16bd7f` mode-aware session context; `03265a3` workflow levels; `78bc3e1` stack conventions on demand; `ad70d4e` eval conditions per mode; `d056b35` docs; `9d2236f` eval prompts waive questions.
- Verified: validate, lifecycle (65), doctor (42), install (87), cli, hooks, evals suites and ShellCheck passed at their milestones.
- Pending owner decisions: (1) index-only startup context for auto/standard (lazy loading) before the benchmark; (2) installer robustness work for tool churn, proposed for the next phase.
- Next: after (1), run the benchmark (bug-fix ×2 and new-project ×1 for baseline, lite, standard, strict, auto; 15 sessions, Sonnet), isolate HOME and all XDG paths, then update `docs/results.md` and the README results table.
