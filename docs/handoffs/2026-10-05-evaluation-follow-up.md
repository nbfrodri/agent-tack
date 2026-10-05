# Evaluation follow-up

- Status: in progress (PR 1: guard safety)
- Branch: `feat/guard-safety` from `main` at `fa47728`
- Plan: `docs/plans/2026-10-05-evaluation-follow-up.md` (approved; seven PRs, merge on green CI authorised)
- Evaluation: 7.1/10 by the evaluator agent; findings became issues #67–#75. Verified by hand: the guard allowed `rm -rf ../../..`, `find / -delete`, `curl … | bash`, `rm -rf .git`, `gh repo delete`.
- Side fix: PR #66 (usage band showed `tack · off` when its call to tack failed; now `?` with a reason and retries; mod 0.4.1).
- Next: #67 tests and fix, then #68.
