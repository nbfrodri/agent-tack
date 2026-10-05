# Evaluation follow-up

- Status: in progress (PR 1 guard safety: review and full suite running)
- Branch: `feat/guard-safety` from `main` at `fa47728`
- Plan: `docs/plans/2026-10-05-evaluation-follow-up.md` (approved; seven PRs, merge on green CI authorised)
- Evaluation: 7.1/10 by the evaluator agent; findings became issues #67–#75. Verified by hand: the guard allowed `rm -rf ../../..`, `find / -delete`, `curl … | bash`, `rm -rf .git`, `gh repo delete`.
- Side fix: PR #66 (usage band showed `tack · off` when its call to tack failed; now `?` with a reason and retries; mod 0.4.1).
- PR 1 (`feat/guard-safety`): `50daa10` closes #67 (rm -r targets resolved, HOME and ancestors denied, outside the project asks, HOME as working directory is not a project) and #68 (find -delete outside the project, .git, code piped into a shell or interpreter, infrastructure and device rules as policy data; docs list what the guard does not cover). PR #66 merged as `a7ecc84`.
- Next: review fixes, PR, CI, merge; then PR 2 (#69, #73, #72).
