# Configuration as data, feedback loops and tool robustness

- Status: in progress (implementation, review fixes and benchmark done; awaiting the owner's approval for push and PR)
- Branch: `feat/config-feedback-robustness` (from `main` at `4a7b55f`); local only
- Plan: `docs/plans/2026-10-04-config-feedback-robustness.md`
- Review: `docs/audits/2026-10-04-review-config-feedback-robustness.md` (all findings fixed in `48f141f` except the documented budget-counter approximation)
- Benchmark: `docs/benchmarks/2026-10-04-modes-final.md`, published in `docs/results.md` and the README (`b78f9c5`)
- Verified: 820 checks + evals and ShellCheck green at `93dc7ef`; later commits are docs only.
- Installed on the real HOME from this branch (mods `usage-band` 0.2.0, `agent-activity` 0.1.0).
- Pushed with the owner's approval; [PR #34](https://github.com/nbfrodri/agent-harness/pull/34). First CI run failed (older ShellCheck SC2015 in `bin/harness` and `lib/config.sh`; bash 3.2 misparsed a `case` inside `$( )` in `stop-check.sh`); fixed in `4f9d46f`, CI rerunning.
- Next: when CI is green, ask the owner to merge (recommend a merge commit). After merge, delete this handoff.
- Process: avoid commands the guard asks about; the owner wants no confirmations.
