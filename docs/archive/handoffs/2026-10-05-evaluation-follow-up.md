# Evaluation follow-up

- Status: done (PRs #76–#82 merged; every issue from the evaluation closed)
- Branch: `feat/visual-review` (last PR), from `main` after PR #81
- Plan: `docs/archive/plans/2026-10-05-evaluation-follow-up.md` (approved; seven PRs, merge on green CI authorised)
- Evaluation: 7.1/10 by the evaluator agent; findings became issues #67–#75. Verified by hand: the guard allowed `rm -rf ../../..`, `find / -delete`, `curl … | bash`, `rm -rf .git`, `gh repo delete`.
- Side fix: PR #66 (usage band showed `tack · off` when its call to tack failed; now `?` with a reason and retries; mod 0.4.1).
- PR 1 (#76, merged): closes #67 and #68 (delete targets resolved, find -delete, code piped into shells and interpreters, infrastructure rules; docs list what the guard does not cover).
- PR 2 (#77, merged): closes #69 (mods' unit tests with Node), #73 (`tests/lint.sh`, `tests/run-all.sh`) and #72 (guard about 110 ms per compound command).
- PR 3 (#78, merged): closes #74 (README matches the capability map; results.md trimmed), #70 (tack names, `TACK_ALLOW_*`, validate check for former names) and #75 (`docs/archive/`, lighter handoff and AI-log rules).
- PR 4 (#79, merged): closes #71; the guard dispatches to `hooks/claude/lib/guard-{git,files,exec,infra,wrappers}.sh`, no behaviour change, a missing library asks.
- PR 5 (#80, merged): closes #63; hidden acceptance tests, `evals/outcomes.py`, outcome benchmark (hidden tests 4/4 in both conditions, 2.6–3.3× cost), step-value note.
- PR 6 (#81, merged): closes #44; `tack memory` (`~/.config/agent-tack/memory.md`), loaded at session start by Claude Code and Codex, ADR 0002.
- PR 7 (`feat/visual-review`): closes #54; `tack shots` into `.tack-screenshots/` (self-ignored, since `.tack` is the marker file), side-by-side `index.html`, `ui-reviewer` rubric, `visual-review` toggle for standard, strict and unleash; verified with real Playwright 1.63.
- Next: nothing in this plan. Follow-ups proposed in `docs/benchmarks/2026-10-05-step-value.md` (docs-map false positives, macOS CI only for shell changes, lite for one-line fixes, re-measure with the activity log).
