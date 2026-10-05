# What each workflow step caught

- Date: 2026-10-05. Sources: this repository's history (`evals/outcomes.py`, 14-day window), its CI runs on GitHub, and the `code-reviewer` reports and Stop-check messages of pull requests #76–#79. The activity log was off, so guard and Stop-check counts before #76 are not available.
- Purpose: find the steps that cost time without catching anything, as candidates to trim from their workflow level (#63).

| Step | What it caught | Verdict |
| --- | --- | --- |
| `code-reviewer` before push | #76: guard bypasses, some older than the pull request (options before `-c`, `bash -s`, `find` global options, `-exec rm`). #77: a latency test that would flake under load, logs deleted on failure, a network dependence, an unpinned ruff, a stale doc. #78: an unmet acceptance criterion, contradictory rules, commits that broke bisect. #79: nothing blocking (it verified 0 behaviour differences on 93 commands). | Keep at strict; it found real defects in 3 of 4 pull requests. |
| CI | 12 of 47 pull-request runs failed, all before merge, among them ShellCheck differences between local and CI versions and macOS paths; 1 failure on `main` in 32 pushes. Since #77 pins ShellCheck and ruff and `tests/lint.sh` runs the same checks locally, no pull request failed lint. | Keep. The macOS job takes about 14 minutes against 5 on Ubuntu; it caught the `//` temp-path bug once. |
| Fixes before merge | 16 of 37 `fix:` commits corrected a feature on its own branch before it merged (review or CI); 14 of 104 features (13%) needed a fix after reaching `main`. | The review-and-CI loop catches about half of the defects that get fixed. |
| Stop check | In #77–#79 it flagged a stale handoff twice and an uncommitted change once, all acted on. Its docs-map warning fired for 4 files in #78; one led to a doc change, three were edits to messages and comments that no doc describes. | Keep; the docs-map check needs fewer false positives. |
| Handoffs and AI log | 63 of 297 commits (21%) were bookkeeping (`docs(handoffs)`, `docs(plans)`, `docs(ai)`) before #75 made handoffs milestone-only and moved the AI log row into the change's commit. | Already trimmed in #75; measure the share again after a few weeks. |
| Process on small tasks | Hidden acceptance tests passed in 4 of 4 runs with and without tack ([outcomes](2026-10-05-outcomes.md)); tack added a branch, a commit and more tests at 2.6–3.3× the cost. | No quality gain shown on easy tasks; the measurement needs harder scenarios. |

## Proposed trims

1. **Docs-map warnings:** ignore a change whose added and removed lines are only comments or quoted messages, or warn once per file per session instead of at every stop.
2. **macOS CI job:** run it only when shell scripts, hooks or the installer change; documentation-only pull requests would finish in about 5 minutes instead of 14.
3. **Small tasks in `auto`:** prefer `lite` for one-line fixes and small scripts, where the evals show no outcome difference and most of the cost is the extra turns.
4. **Re-measure:** turn the activity log on (`tack config activity-log true`) for a few weeks to count guard asks and Stop-check findings per step, then repeat this note.

Limits: one repository with a single maintainer, three days of history, four reviewed pull requests and two small eval scenarios. Escaped defects are linked by the lines a fix changes (`git blame`), which misses fixes that only add code.
