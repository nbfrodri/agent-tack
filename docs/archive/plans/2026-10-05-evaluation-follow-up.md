# Evaluation follow-up and remaining issues

- Status: done (approved 2026-10-05; PRs #76–#82 merged)
- Goal: act on the project evaluation (score 7.1/10; security 6, code quality, performance, docs and tooling 7, architecture and tests 8) and close the remaining open issues.

## Decisions
- Seven pull requests, in this order, each merged with a merge commit once CI is green (the owner authorised push, PR and merge):
  1. Guard safety: #67 normalise `..` in `rm -r`; #68 state the guard's limits and cover infrastructure destruction, pipes into shells, `find -delete` and `rm -r .git`.
  2. CI and tooling: #69 run the mod tests for real in CI; #73 one lint script with ruff and a parallel test runner; #72 measure and bound the guard's latency.
  3. Cleanup: #70 finish the rename to tack; #74 README matching the capability map and a trimmed `docs/results.md`; #75 lighter process artifacts.
  4. #71 split the guard into per-command libraries, no behaviour change.
  5. #63 outcome quality: hidden acceptance tests in the evals, escaped-defect and rework metrics.
  6. #44 user-level memory shared by Claude Code and Codex.
  7. #54 before and after screenshots of visual changes, scored by a fresh-context subagent (Playwright optional).
- Each PR: tests first, `code-reviewer` before pushing, full ShellCheck and every suite, docs in the same PR.
