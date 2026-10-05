# Evaluation follow-up

- Status: in progress (PR 2 #77 open, CI running)
- Branch: `feat/ci-tooling` from `main` after PR #76
- Plan: `docs/plans/2026-10-05-evaluation-follow-up.md` (approved; seven PRs, merge on green CI authorised)
- Evaluation: 7.1/10 by the evaluator agent; findings became issues #67–#75. Verified by hand: the guard allowed `rm -rf ../../..`, `find / -delete`, `curl … | bash`, `rm -rf .git`, `gh repo delete`.
- Side fix: PR #66 (usage band showed `tack · off` when its call to tack failed; now `?` with a reason and retries; mod 0.4.1).
- PR 1 (#76, merged): closes #67 and #68 (delete targets resolved, find -delete, code piped into shells and interpreters, infrastructure rules; docs list what the guard does not cover).
- PR 2 (`feat/ci-tooling`): `f552e45` closes #69 (mods' unit tests run with Node through esbuild and a shim), `277706c` closes #73 (`tests/lint.sh` with pinned ShellCheck and ruff, `tests/run-all.sh` parallel runner), `ba810a5` closes #72 (guard about 110 ms per compound command, from about 250 ms; latency test with `TACK_GUARD_BUDGET_MS`).
- Review fixes in `fix(ci)` commit (median latency, kept logs, offline skip, ruff pin check). Next: CI green, merge #77; then PR 3 (#70, #74, #75).
