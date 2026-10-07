# Codex code-quality review

This supplementary review covers all 24 final diffs in [the public facts](2026-10-08-codex-facts.json). It was requested during the batch, after 16 runs had completed. One assistant reviewed production code, tests and documentation; the review was neither independent nor blinded. Scores are judgments about these small tasks, not model rankings or proof of a general quality improvement.

Each criterion receives 0 (material problems), 1 (adequate with the stated limitation), or 2 (strong for this task): **R** readability, **S** simplicity, **B** robustness/security, **T** regression-test quality, **F** focus/scope. A 10 means no deduction under this narrow rubric, not production certification. Existing fixture tests do not replace a regression test for new behavior. Branches, commits and test counts are not scoring criteria.

| Run | R | S | B | T | F | /10 | Evidence and deductions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| r0-attachments-baseline-1 | 2 | 1 | 1 | 0 | 1 | 5 | Adds a full URL parser and strips leading slashes, so absolute names are reinterpreted instead of rejected. No new tests; expands the input contract beyond a file name. Containment still prevents the tested leaks. |
| r0-attachments-baseline-2 | 2 | 2 | 2 | 0 | 2 | 8 | Clear decoding and resolved containment; no new regression tests for path handling. |
| r0-attachments-auto-1 | 2 | 2 | 2 | 2 | 2 | 10 | Small containment helper; nested reads, traversal, absolute paths and escaping symlink tests. |
| r0-attachments-auto-2 | 2 | 2 | 2 | 1 | 2 | 9 | Concise resolved containment; tests omit symlink/absolute-path cases and the added URL-decoding behavior. |
| r0-bug-fix-baseline-1 | 2 | 2 | 2 | 0 | 2 | 8 | Minimal correct empty-input guard; no regression test. |
| r0-bug-fix-baseline-2 | 2 | 2 | 2 | 0 | 2 | 8 | Same production fix and same missing regression test. |
| r0-bug-fix-auto-1 | 2 | 2 | 2 | 2 | 2 | 10 | Same minimal guard plus a focused empty-input regression. |
| r0-bug-fix-auto-2 | 2 | 2 | 2 | 2 | 2 | 10 | Same minimal guard plus a focused empty-input regression. |
| r0-search-baseline-1 | 2 | 2 | 2 | 0 | 2 | 8 | Literal Unicode casefold matching and parameterized price filter; no regression tests. |
| r0-search-baseline-2 | 2 | 1 | 2 | 0 | 2 | 7 | Correct Unicode matching; materializes rows and a second matching list before sorting in Python. No new tests. |
| r0-search-auto-1 | 2 | 2 | 1 | 1 | 2 | 8 | SQLite lower/instr misses Unicode case pairs. Its price-limit test would still pass if the filter were removed: no matching row lies above the cap. |
| r0-search-auto-2 | 2 | 2 | 1 | 1 | 2 | 8 | Escaped LIKE handles literal wildcards, but misses Unicode case pairs. Added tests miss that limitation and cover only percent among special input cases. |
| r1-attachments-baseline-1 | 2 | 2 | 2 | 2 | 2 | 10 | Documented decoding boundary, containment, encoded-input and symlink tests. |
| r1-attachments-baseline-2 | 2 | 2 | 2 | 2 | 2 | 10 | Similar scoped helper and useful unsafe-input, symlink and filesystem-error tests. |
| r1-attachments-auto-1 | 2 | 2 | 2 | 2 | 1 | 9 | Clear helper and broad behavioral tests. Plan and AI log add maintenance to a small isolated API, beyond useful README documentation. |
| r1-attachments-auto-2 | 2 | 2 | 2 | 2 | 1 | 9 | Documents the stable-tree assumption and exercises containment. Same extra plan/log overhead. |
| r1-bug-fix-baseline-1 | 2 | 2 | 2 | 2 | 2 | 10 | Minimal guard and focused regression. |
| r1-bug-fix-baseline-2 | 2 | 2 | 2 | 2 | 2 | 10 | Minimal guard and focused regression. |
| r1-bug-fix-auto-1 | 2 | 2 | 2 | 2 | 2 | 10 | Minimal guard, updated docstring and regression. |
| r1-bug-fix-auto-2 | 2 | 2 | 2 | 2 | 2 | 10 | Also verifies the returned Decimal type. |
| r1-search-baseline-1 | 2 | 2 | 2 | 2 | 2 | 10 | Parameterized filtering, literal Unicode matching, meaningful special-input and boundary tests. |
| r1-search-baseline-2 | 2 | 2 | 2 | 2 | 2 | 10 | Same strengths, with documented/tested equal-price ordering. |
| r1-search-auto-1 | 2 | 2 | 2 | 2 | 2 | 10 | Comparable implementation and tests, with concise API documentation. |
| r1-search-auto-2 | 2 | 2 | 2 | 2 | 2 | 10 | Comparable Unicode, literal-input and price-boundary coverage. |

`r0` is GPT-6 Luna; `r1` is GPT-6.1 Sol. Both use medium effort. Mean review scores: Luna baseline **7.33**, auto **9.17**; Sol baseline **10.00**, auto **9.67**. These coarse, subjective averages are driven largely by Luna's missing baseline tests and Sol's added process documents. They do not override the concrete Unicode regression or establish a causal effect from two runs per scenario.

## Follow-up probes and common limits

The [reproducible Unicode probe](support/probe-codex-search.py) imports each completed search artifact and searches for `café` in `CAFÉ`, and `STRASSE` in `Straße`. [Recorded results](2026-10-08-codex-unicode.json): both Luna auto artifacts fail both checks; the other six search artifacts pass. The frozen hidden suite checks ASCII case matching only. These observations supplement it without changing its original 8/8 verdicts.

Every attachment implementation checks a resolved path and subsequently reads it. None provides race-free containment against a concurrently hostile filesystem. That threat was not tested or explicitly required; successful static symlink tests do not establish protection against it. Sol auto's second run documents this assumption. The original prompt also leaves URL decoding ambiguous: some artifacts decode once, others expect a decoded filename. Review does not select one contract after the fact to manufacture a winner.

All final working trees retain an untracked `uv.lock` produced by test execution. This is common to both conditions and not counted as an added feature or as evidence that every task ended with a clean working tree. Python-side substring filtering handles Unicode but scans candidate rows; no workload-scale performance test was run on the generated libraries.
