# Evaluation follow-up

- Status: in progress (PR 6 shared memory: review running)
- Branch: `feat/shared-memory` from `main` after PR #80
- Plan: `docs/plans/2026-10-05-evaluation-follow-up.md` (approved; seven PRs, merge on green CI authorised)
- Evaluation: 7.1/10 by the evaluator agent; findings became issues #67–#75. Verified by hand: the guard allowed `rm -rf ../../..`, `find / -delete`, `curl … | bash`, `rm -rf .git`, `gh repo delete`.
- Side fix: PR #66 (usage band showed `tack · off` when its call to tack failed; now `?` with a reason and retries; mod 0.4.1).
- PR 1 (#76, merged): closes #67 and #68 (delete targets resolved, find -delete, code piped into shells and interpreters, infrastructure rules; docs list what the guard does not cover).
- PR 2 (#77, merged): closes #69 (mods' unit tests with Node), #73 (`tests/lint.sh`, `tests/run-all.sh`) and #72 (guard about 110 ms per compound command).
- PR 3 (#78, merged): closes #74 (README matches the capability map; results.md trimmed), #70 (tack names, `TACK_ALLOW_*`, validate check for former names) and #75 (`docs/archive/`, lighter handoff and AI-log rules).
- PR 4 (#79, merged): closes #71; the guard dispatches to `hooks/claude/lib/guard-{git,files,exec,infra,wrappers}.sh`, no behaviour change, a missing library asks.
- PR 5 (#80, merged): closes #63; hidden acceptance tests, `evals/outcomes.py`, outcome benchmark (hidden tests 4/4 in both conditions, 2.6–3.3× cost), step-value note.
- PR 6 (`feat/shared-memory`): closes #44; `tack memory` (`~/.config/agent-tack/memory.md`), loaded at session start by Claude Code and Codex, ADR 0002.
- PR 7 (#54) design choice: screenshots go to `.tack-screenshots/` (self-ignored), because `.tack` is the shared marker file and cannot also be a folder.
- Next: review fixes, PR, CI, merge #44; then PR 7 (#54 `tack shots`).
