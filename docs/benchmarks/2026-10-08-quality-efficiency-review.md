# Independent code-quality review

The candidate does not show a general code-quality advantage over plain projects. It fixes some failures seen with current tack, but has weaker design in another delivery, and every condition retains uncovered boundaries. The useful result is a set of concrete findings supported by source inspection, not a quality certificate.

Two fresh GPT-6 Astra sessions reviewed each of 16 anonymous triplets under the [frozen rubric](2026-10-08-quality-efficiency-protocol.md#independent-code-review). They saw production code, the request and domain contract, with no tests, process files, conditions, implementation model names or outcomes. The orchestrator inspected all 48 production deliveries and both judgments, then saved [its assessment](2026-10-08-quality-efficiency-orchestrator.json) before revealing mappings. Test/documentation inspection came afterward and did not alter production grades.

[Results and timing](2026-10-08-quality-efficiency.md) | [Production bundles, original grades, citations and adjudication](2026-10-08-quality-efficiency-facts.json)

## Scores by dimension

Means on a 0–10 scale, using two judgments per delivery and eight deliveries per column. A 10 means no substantiated issue within that review's interpreted scope; it does not mean perfect software. The weighted totals remain separate from functional acceptance.

| Dimension (weight) | Luna plain | Luna current | Luna candidate | Sol plain | Sol current | Sol candidate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Responsibilities (25%) | 9.75 | 9.50 | 9.50 | 9.88 | 9.88 | 9.88 |
| Readability (20%) | 9.75 | 9.44 | 9.56 | 9.81 | 9.81 | 9.75 |
| Robustness (20%) | 9.13 | 7.25 | 8.38 | 9.44 | 8.44 | 9.25 |
| Changeability (15%) | 9.56 | 9.00 | 9.19 | 9.63 | 9.69 | 9.56 |
| Simplicity (10%) | 9.69 | 9.69 | 9.50 | 9.81 | 9.81 | 9.94 |
| Existing interface/style fit (10%) | 9.69 | 9.00 | 9.75 | 10.00 | 10.00 | 10.00 |
| **Weighted total** | **9.58** | **8.93** | **9.27** | **9.74** | **9.55** | **9.70** |

## Findings that matter

The labels below were revealed only after adjudication. Exact source and line citations are preserved in the facts file under each review ID.

| Delivery / anonymous group | Confirmed finding | Evidence and consequence |
| --- | --- | --- |
| Luna current, CLI repetition 2 / 10 | Incomplete error handling | `options.py:4–8` ignores unknown arguments, accepts invalid keys and indexes missing operands; `__main__.py:6` lets exceptions escape. Both judges flag major defects, and frozen acceptance fails. |
| Luna plain, settings repetition 2 / 13 | Reversed layer precedence | `settings.py:67–82` applies environment before overrides. Both judges and the orchestrator identify the wrong result; frozen acceptance fails. |
| Luna current and candidate, settings repetition 2 / 13 | Invalid overrides can be masked | Valid environment values replace invalid supplied endpoint/attempts before validation. Both judges flag it; the supplementary probe confirms it. Frozen acceptance missed this combination. |
| Luna current, settings repetition 1 / 12 | Mapping interface narrowed to dict | `settings.py:49` rejects `UserDict` and other documented mappings. The candidate accepts them. Both judges and the supplementary probe confirm the difference. |
| Luna candidate, settings repetition 2 / 13 | Defaults duplicated | The loader's helper repeats literal defaults instead of reading exported `DEFAULTS`. Both judges and the orchestrator identify a minor maintenance regression versus current tack. A change to defaults can drift between two places. |
| Settings deliveries / 01, 08, 12, 13 | Long valid decimal strings | Whole-string `int()` rejects more than 4,300 digits under this runtime's limit, including leading zeros representing 1. Eleven of twelve implementations fail the supplementary case. Sol candidate repetition 1 uses bounded accumulation and has a test for it. |
| Shipment deliveries / 02, 06, 09, 11 | Weak event-envelope checks | All plain deliveries reject a function carrying event fields, versus 0/4 current and 2/4 candidate deliveries. This is an inherited boundary weakness; it is not a general architecture difference. |
| All shipment deliveries | Inherited IDs disappear | Validation can read an inherited ID, but spread omits it and dispatch reads the copied payload's ID. All twelve fail that supplementary non-JSON-object case. The original code also had this limitation. |

The [supplementary results](2026-10-08-quality-efficiency-supplement.json) preserve every probed attempt. These cases came from blind source review, not a revised hidden acceptance suite. They show why “passes all frozen tests” must stay narrower than “fully correct.”

## Where the judge disagrees or overstates certainty

The two reviews chose the same preferred candidate set in 15/16 triplets. In group 01, one narrowly preferred explicit validation/merge structure and the other a more compact flow. Both are proportionate; the orchestrator found no decisive winner.

Identical pagination code under an identical contract receives weighted scores from **9.2 to 10.0** across bundles. When every candidate assumes array input, judges accept that precondition. When another candidate adds `Array.isArray`, they interpret the contract more broadly and call the missing guard a major defect. The observable behavior is real, but the wording does not explicitly define non-array handling. The orchestrator retains the defensive preference while qualifying the severity and rejecting a precise causal quality claim from those scores.

Shipment judgments differ over whether inherited/non-enumerable fields fall within scope; that changes robustness by two points in groups 02 and 11. The orchestrator confirms the source behavior and records the scope assumption. A function-envelope issue is minor in one group-02 judgment and major in the other; it is retained as a narrow input-validation defect rather than a newly introduced severe design regression.

For group 10's incomplete CLI, responsibilities differs by two points: one judge rewards the existing module split while the other penalizes the missing error boundary. Both agree on all major failures. The orchestrator prioritizes those shared findings; raw scores remain untouched.

Unicode decimal digits and decorated arrays are other contract ambiguities. ASCII-only settings parsers differ from Unicode-aware ones, but the experiment did not explicitly resolve that requirement. Supplementary observations expose the difference without retroactively changing acceptance.

## Separate review of tests, docs and process

All tack coding deliveries added tests and made a branch plus a local Conventional Commit. Luna's plain condition added tests in 1/8 runs; Sol's plain condition did so in 8/8. Restoring the original defect makes all 32 tack suites fail while their delivered suites pass. That is useful regression protection, not evidence of complete coverage.

Inspection found meaningful assertions about boundary values, input mutation, object identity, ordered CLI operations and clean subprocess errors. Luna's current CLI repetition 2 covers only happy paths, explaining how a passing suite misses its error contract. Sol's tests are generally broader with or without tack. No coding delivery modified the already supplied product documentation; there is no measured documentation advantage.

File-edit ordering alone does not prove TDD. No failing-test execution was recorded before a later fix in this batch. The one nonzero check-containing shell event ended with a deliberately invalid CLI call after passing unit tests. Tack's TDD guidance remains useful, but its reliable execution is an unresolved behavior gap.

## Orchestrator conclusion

Against current tack, the candidate improves one CLI delivery and mapping support, retains a shared validation gap and introduces one minor defaults-duplication weakness. Against plain projects, it increases Luna's regression protection and adds Git discipline, while the production-code advantage is unproven. Extra files, tests, commits or helper functions did not earn production-quality points.

Retain TDD and practical design guidance, but improve actual project checks and inspect their coverage. Future evaluation should make ambiguous contracts explicit and check reviewer consistency before using small numeric differences to justify product changes. The orchestrator designed the study and may recognize implementation patterns; concealed condition mappings reduce, but do not remove, expectation bias.
