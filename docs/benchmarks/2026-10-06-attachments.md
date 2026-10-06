# Attachments scenario (security-sensitive input)

- Date: 2026-10-06. Claude Code 2.1.290 in a Linux container; tack from the integration of the open pull requests (main plus #83–#118); `claude-opus-5-5` (two runs per condition) and `claude-haiku-4-5` (five runs per condition).
- Scenario (`evals/run.sh attachments`): add `read_attachment(user_root, name)` to a small `storage` package, where the name "comes straight from a download URL". Seven hidden tests check the feature and the path traversal traps: `../`, absolute names, a sibling folder sharing the prefix (`alice` vs `alice2`, which defeats a `startswith` check), a symlink pointing outside, and a missing file.
- Grading: the hidden tests run on the work wherever the agent left it. One tack run moved its commit to a branch after the `commit-msg` warning (#118) and switched back to `main`; the grader now picks the branch that holds the work (#113).

| `claude-haiku-4-5`, 5 runs each | Hidden tests passed (of 7), per run | Mean | All 7 | Branch | Cost (mean) |
| --- | --- | --- | --- | --- | --- |
| Baseline | 3, 4, 6, 6, 4 | 4.6 | 0/5 | 0/5 | $0.058 (1×) |
| Auto | 6, 6, 7, 4, 7 | 6.0 | 2/5 | 5/5 | $0.070 (1.2×) |
| Auto with the risk rule (#119) | 7, 7, 4, 7, 7 | 6.4 | 4/5 | 5/5 | $0.086 (1.5×) |

| `claude-opus-5-5`, 2 runs each | Hidden tests passed | Branch | Cost (mean) |
| --- | --- | --- | --- |
| Baseline | 7, 7 | 0/2 | $0.146 (1×) |
| Auto | 7, 7 | 2/2 | $0.283 (1.9×) |

## Reading it
- With the smaller model, tack changed the outcome: no baseline run handled every traversal trap, against 2 of 5 with tack and 4 of 5 once auto was told to pick the level by risk. The runs that failed with tack missed one or two traps; baseline runs missed one to four.
- Before the risk rule, Haiku picked `lite` for this task in 3 of 5 runs; with it, `standard` in 4 of 5.
- The larger model handled every trap without tack, as in the other scenarios: there tack only adds the branch, the commit and tests, at about twice the cost.

Limits: five runs per condition for Haiku and two for Opus, one scenario, automatic grading; the risk-rule runs came after the other two, on the same day and tack revision plus #119. Treat it as a first signal to confirm with more scenarios, not as a measured effect size.
