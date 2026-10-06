# Conventions scenario

- Date: 2026-10-06. Claude Code 2.1.290, `claude-opus-5-5` (observed in every transcript), Linux container, tack at `improve/round-2` (main plus the open pull requests #83–#87, #101, #104, #105). Two runs per condition.
- Scenario (`evals/run.sh conventions`): a small `cart` package whose `AGENTS.md` sets rules the prompt does not repeat (amounts rounded once to cents with `ROUND_HALF_UP`, inputs validated with `_check`, invalid arguments raise `ValueError`). The prompt asks for discount codes in a new `total(items, code=None)`. Eight hidden tests check the codes and the conventions: half-up rounding of 10% off 0.05, negative quantities and unknown codes raising `ValueError`, the existing subtotal unchanged.

| Metric | Baseline | Auto |
| --- | --- | --- |
| Hidden acceptance tests: all pass (8) | 2/2 | 2/2 |
| Worked on a branch | 0/2 | 2/2 |
| Commits (Conventional) | 0 | 1 (100%) |
| Tests in the repo (mean) | 10.5 | 12.5 |
| Turns (mean) | 4 | 10 |
| Duration (mean) | 27 s | 52 s |
| Cost (mean) | $0.154 (1×) | $0.259 (1.7×) |

## Reading it
- Claude Code read `AGENTS.md` on its own and kept every convention without tack, so this scenario does not separate the conditions on outcome either. Following project instructions is no longer something tack has to add for Claude Code.
- tack again added the branch, a Conventional Commit and more tests, at 1.7× the cost (lower than the 2.6–3.3× measured with Sonnet on smaller tasks).
- The evals ran without `tack trust`, so the Stop check's test gate (#103) did not run; the test-change check (#102) had nothing to report because both conditions changed tests.

Limits: two runs per condition, one model, one Python scenario. A gain on outcomes still needs a scenario that a careful model fails without verification; the deterministic gates (#102, #103) do not depend on the model following instructions and are covered by the hook tests instead.
