# Review: configuration, feedback and robustness branch

- Date: 2026-10-04. Reviewer: `code-reviewer` agent on `main...feat/config-feedback-robustness` (head `a04f81f`).
- Verdict before fixes: not ready to push (one blocking guard bypass). All findings below were fixed in `48f141f` unless noted.

| Severity | Finding | Resolution |
| --- | --- | --- |
| Blocking | In project-only modes the local-ask waiver ignored the target: `cd ~ && rm -rf *`, `cd / && rm -rf ./*`, `git -C /other reset --hard` and `git --git-dir/--work-tree … clean -fdx` ran without review | Commands that change directory or point git elsewhere never get the waiver; tests for each probe |
| Important | An autonomous agent could lift its own limits or leave its mode (`harness config … 999999`, `--unset`, `harness mode`, `trust`, raw `git config harness.*`) | Refused by the guard in project-only modes; reads stay allowed |
| Important | Missing tests: waiver outside the project, user policy relaxing a shipped ask, skipped user rules, invalid mode in an unleash project | Added to `tests/guard.test.sh` |
| Suggestion | `harness config` matched feature names as regular expressions | Literal match with `awk` |
| Suggestion | Values starting with `-` and `--` were rejected | `--` ends options |
| Suggestion | Stop hook: fast check without a timeout, glob expansion of docs entries, renames | 60-second timeout, globbing disabled, renames use the new path |
| Suggestion | `unleash` allowed on `main`; `branch -D main` waived | Refused on `main`/`master`, doctor warns later; deleting `main` still asks |
| Suggestion | Budget counter not atomic under parallel tool calls | Documented as a safety net rather than an exact quota (not changed) |
| Note | One `tests/lifecycle.test.sh` failure while suites ran concurrently; a rerun passed | Watched in later full runs |
