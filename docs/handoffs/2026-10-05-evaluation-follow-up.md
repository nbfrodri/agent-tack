# Evaluation follow-up

- Status: in progress (PR 5 #80 open, CI running; review findings fixed)
- Branch: `feat/outcome-metrics` from `main` (main merged in after PR #79)
- Plan: `docs/plans/2026-10-05-evaluation-follow-up.md` (approved; seven PRs, merge on green CI authorised)
- Evaluation: 7.1/10 by the evaluator agent; findings became issues #67–#75. Verified by hand: the guard allowed `rm -rf ../../..`, `find / -delete`, `curl … | bash`, `rm -rf .git`, `gh repo delete`.
- Side fix: PR #66 (usage band showed `tack · off` when its call to tack failed; now `?` with a reason and retries; mod 0.4.1).
- PR 1 (#76, merged): closes #67 and #68 (delete targets resolved, find -delete, code piped into shells and interpreters, infrastructure rules; docs list what the guard does not cover).
- PR 2 (#77, merged): closes #69 (mods' unit tests with Node), #73 (`tests/lint.sh`, `tests/run-all.sh`) and #72 (guard about 110 ms per compound command).
- PR 3 (#78, merged): closes #74 (README matches the capability map; results.md trimmed), #70 (tack names, `TACK_ALLOW_*`, validate check for former names) and #75 (`docs/archive/`, lighter handoff and AI-log rules).
- PR 4 (#79, merged): closes #71; the guard dispatches to `hooks/claude/lib/guard-{git,files,exec,infra,wrappers}.sh`, no behaviour change, a missing library asks.
- PR 5 (`feat/outcome-metrics`): hidden acceptance tests (`evals/hidden/`), `evals/outcomes.py` (SZZ-style escaped defects), 8 eval sessions in `docs/benchmarks/2026-10-05-outcomes.md` (hidden tests 4/4 in both conditions; 2.6–3.3× cost), step note in `docs/benchmarks/2026-10-05-step-value.md`, results.md section.
- Next: review, PR, CI, merge; then PR 6 (#44 shared memory) and PR 7 (#54 screenshots).
