# Minimal requests, code quality and setup time

The candidate completed **16/16 frozen coding acceptance checks**, versus 15/16 for current tack and 15/16 for plain projects. That small difference does not establish a general quality advantage. Independent review found defects beyond the frozen checks, and plain projects had slightly higher mean code-quality grades. **Neither speed target was met.**

The clearest observed benefit was more useful regression tests from Luna: 8/8 deliveries with either tack version rejected the original defect, versus 1/8 without tack. Sol already did this in all conditions. Shared choices transferred correctly in every setup, with execution trust kept local.

[Frozen protocol](2026-10-08-quality-efficiency-protocol.md) | [Code-quality review](2026-10-08-quality-efficiency-review.md) | [All attempts, code, grades and hashes](2026-10-08-quality-efficiency-facts.json)

## What was compared

Current tack is `8470e487527954304a8e4c5a80bf3420b85725bc`; candidate is `e3d788b6aec92e8d73343673f873a48a9a240e27`. The candidate adds atomic application of selected shared preferences and shorter onboarding/testing guidance. Product revisions were frozen before confirmation and remained unchanged during every session.

GPT-6 Luna (`gpt-6-luna`) and GPT-6.1 Sol (`gpt-6.1-sol`) implemented four small Node/Python tasks twice in each condition. Requests described the product change, without telling the plain arm to add tests, follow TDD/SOLID, use branches or make commits. Existing public tests, commands and domain contracts were available to all arms. Provider built-in instructions remained common.

Two fresh GPT-6 Astra (`gpt-6-astra`) reviews judged each anonymous triplet, with reversed presentation order and new labels. The orchestrator inspected every production candidate and both judgments before opening condition mappings or correctness results. All models used medium effort through Codex CLI 0.160.1 and the ChatGPT subscription. Runtime observations matched requested models and effort.

All **93 sessions completed**: 5 pilot, 48 coding, 32 review and 8 setup. There were no retries, timeouts or missing grades. Each session used a separate container without host mounts; hidden checks stayed outside implementer and reviewer environments. The pilot is excluded from confirmation results. An initial output-directory error occurred before any model call and was fixed in `ac22028`; no candidate or confirmation task was changed.

## Coding results

Acceptance means passing the frozen assertions, not every possible interpretation or boundary of the contract. Quality is the mean of two subjective production-only grades, weighted by the predeclared rubric. Neither tests nor process artifacts contribute to that grade.

| Model | Condition | Accepted | Code grade /10 | Mean seconds | Median seconds | Seconds per accepted delivery |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Luna | Plain | 7/8 | 9.58 | 18.71 | 17.76 | 21.38 |
| Luna | Current tack | 7/8 | 8.93 | 32.37 | 28.89 | 37.00 |
| Luna | Candidate | 8/8 | 9.27 | 34.88 | 31.58 | 34.88 |
| Sol | Plain | 8/8 | 9.74 | 54.43 | 50.92 | 54.43 |
| Sol | Current tack | 8/8 | 9.55 | 77.66 | 69.41 | 77.66 |
| Sol | Candidate | 8/8 | 9.70 | 76.45 | 74.82 | 76.45 |

All failed-attempt time stays in the denominator for seconds per accepted delivery. Luna's plain settings run reversed environment precedence; a current-tack CLI run omitted required error handling. Both failures were independently identified in blind review.

Compared with current tack, candidate mean coding time changed by **+7.7% for Luna and -1.6% for Sol**. Compared with plain projects, the candidate took **1.86x and 1.40x** the time. The goal was a 20% reduction versus current tack: a 100-second task becoming 80 seconds. It was a provisional target, not an existing result or a promise about human development time.

Two repetitions per cell; means below expose the different task outcomes rather than hiding them in one total. Exact repetitions are in the facts file.

| Model / task | Plain seconds | Current seconds | Candidate seconds | Plain / current / candidate accepted |
| --- | ---: | ---: | ---: | --- |
| Luna / pagination | 16.03 | 34.01 | 26.31 | 2/2, 2/2, 2/2 |
| Luna / shipment | 15.71 | 28.89 | 32.83 | 2/2, 2/2, 2/2 |
| Luna / settings | 24.33 | 40.81 | 49.36 | 1/2, 2/2, 2/2 |
| Luna / CLI | 18.74 | 25.78 | 31.03 | 2/2, 1/2, 2/2 |
| Sol / pagination | 40.71 | 54.45 | 52.40 | 2/2, 2/2, 2/2 |
| Sol / shipment | 49.32 | 63.24 | 74.19 | 2/2, 2/2, 2/2 |
| Sol / settings | 72.04 | 116.02 | 102.47 | 2/2, 2/2, 2/2 |
| Sol / CLI | 55.66 | 76.93 | 76.73 | 2/2, 2/2, 2/2 |

## Setup and sharing

Each model performed two setups per revision using already agreed choices. Only committed files passed into a real second clone with a fresh home and a deliberately conflicting personal Conventional Commit default.

| Model | Current mean seconds | Candidate mean seconds | Change | Selected preferences shared correctly |
| --- | ---: | ---: | ---: | --- |
| Luna | 63.24 | 70.61 | +11.7% | 2/2 current; 2/2 candidate |
| Sol | 84.90 | 95.76 | +12.8% | 2/2 current; 2/2 candidate |

All eight setups preserved production code and tests, added a PR template, transferred activation and auto mode, and stored the five selected preferences with `shared` origins. A teammate's local reply override won; execution trust did not transfer. The earlier omission of an explicit shared default did not recur in either condition of this batch.

All four candidate setups used the new preview/apply flow. Its one validated write is an interface and configuration-safety improvement, but did not shorten these sessions. The goal was 30% less guided-setup session time versus current tack: 100 seconds becoming 70 seconds. Installation and human decision time are outside this measure.

## Tests and observed workflow

| Model | Condition | Delivered public suite passes | Tests reject original defect | Branch and local commit |
| --- | --- | ---: | ---: | ---: |
| Luna | Plain | 8/8 | 1/8 | 0/8 |
| Luna | Current tack | 8/8 | 8/8 | 8/8 |
| Luna | Candidate | 8/8 | 8/8 | 8/8 |
| Sol | Plain | 8/8 | 8/8 | 0/8 |
| Sol | Current tack | 8/8 | 8/8 | 8/8 |
| Sol | Candidate | 8/8 | 8/8 | 8/8 |

The probe restores the original production files in a disposable copy and runs delivered tests. It covers one defect family per task, not general mutation coverage. A passing public suite can still miss contract failures: Luna's incomplete current-tack CLI is an example.

The orchestrator separately inspected delivered tests and documentation after sealing production judgments. Luna's tack tests usually cover the requested regression and several boundaries; Sol writes broader boundary, identity, mutation and CLI subprocess checks in all arms. Its candidate settings test explicitly covers a 5,001-digit leading-zero input that the hidden suite omitted. No coding session changed the supplied product README or architecture/contract docs; these already described the target behavior, so this gives no documentation-upkeep benefit to either arm.

Recorded file-change events put a test edit before a production edit in 23/32 tack runs, but **no recorded failing-test run established red/green TDD**. The only nonzero shell event containing a test command had passing unit tests followed by an intentionally invalid CLI invocation. Do not count it as a red test. Arbitrary shell edits are not fully described by file-change events; the [workflow observations](2026-10-08-quality-efficiency-workflow.json) preserve that limit. Tack guides TDD; this experiment does not show that it reliably enforces it.

## Tokens and overhead

Totals for the eight coding sessions in each cell:

| Model | Condition | Input tokens | Cached input | Output tokens |
| --- | --- | ---: | ---: | ---: |
| Luna | Plain | 654,152 | 581,376 | 9,061 |
| Luna | Current tack | 1,421,342 | 1,255,936 | 16,032 |
| Luna | Candidate | 1,512,125 | 1,334,528 | 17,050 |
| Sol | Plain | 625,962 | 564,352 | 14,510 |
| Sol | Current tack | 1,397,413 | 1,209,344 | 17,869 |
| Sol | Candidate | 1,364,465 | 1,143,680 | 18,239 |

Cached input is a subset of input, not an additional total. These are subscription observations, not dollar costs. Coding sessions total 2,355.98 seconds; setup totals 629.03 seconds. The 32 reviewer sessions add 1,708.25 seconds of evaluation work, not ordinary tack latency. Session totals are not elapsed batch time because two sessions ran concurrently.

Installation in coding runs took 1.66–2.20 seconds and is recorded separately. Checks performed by the assistant remain inside session time. Frozen post-delivery grading ran separately; its wall time was not captured, so no reasoning/check-time decomposition is claimed. The supplementary probes record their own duration.

Recognizable shell-event counts fell from 7.13 to 6.50 per Luna coding session and 8.00 to 7.38 for Sol, while check-containing events rose slightly. During setup, Luna's counts rose from 14 to 19 and Sol's fell from 16.5 to 11. Commands can combine operations; counts neither measure reasoning time nor establish why latency changed. Fewer invocations did not reliably mean faster sessions.

## Decision and next evidence

Keep atomic shared-profile application for explicit, portable choices and retain guidance against demonstrably redundant checks. Do not advertise either as a measured speed optimization. Relevant regression suites and CI pass; no frozen acceptance regression or newly introduced severe design defect appeared versus current tack. The candidate did duplicate defaults in one Luna settings delivery, a concrete minor maintainability regression recorded in the review. Mean grades did not breach the predeclared 0.5-point regression trigger, but they cannot prove noninferiority.

Tack's supported value here is repeatable project policy, local trust, reviewable Git work and regression-test creation where the model would otherwise omit it. A general code-quality, productivity or cost advantage remains unproven. Useful next experiments should target a real repository's verification gaps and repeated setup work, including task mixes where domain-specific checks can catch otherwise missed failures. Another broad instruction layer, mandatory extra agents or a proprietary skill service is not justified by this evidence.

Before another batch, clarify ambiguous array/Unicode contract boundaries, add the independently discovered failure combinations, calibrate identical-code judgments, and measure the checks or decisions that actually consume time. Do not retrofit those changes into this frozen comparison or run extra best-of attempts.

## Limits and reproducibility

This is a small synthetic study: two repetitions, one provider, two implementers and two fresh judgments from the same reviewer model. Shared setup uses fixed decisions, not live human onboarding. Grades have ceiling effects and contextual drift: identical production code under the same contract spans **0.8/10** across reviews. Relative preferences agree in 15/16 triplets, but that does not make absolute grades objective. The orchestrator designed the experiment, so blinding does not eliminate expectation bias.

The development pilot's three identical implementations fixed the empty-list case but omitted other validation; all failed frozen acceptance. Both reviewers and the orchestrator recognized that defect despite high style/design totals. It is calibration evidence, not an improvement result.

The manifest, controller/product hashes, common fixture hashes, runtime observations, production bundles, original grades and adjudication are in the [facts file](2026-10-08-quality-efficiency-facts.json). The [sealed orchestrator assessment](2026-10-08-quality-efficiency-orchestrator.json) has SHA-256 `1f3ea85502add2278a3f7dd6b117edf95d5c0a6b3135332f59e10fd3bff374aa`. No condition mapping or acceptance result was opened before it was saved.

Runtime: Python 3.12.3, Node 18.19.1, Git 2.43.0, Codex CLI 0.160.1. Container image: `sha256:b3595972953b86399133c40386256f2b00facc6170d9be05a70891f24615963e`. The public Docker recipe pins base and Codex versions; rebuilding apt packages may produce a different image.

Raw local transcripts/snapshots are retained in ignored `evals/out/quality-20261008/raw-evidence.tar.gz`, SHA-256 `633af3d6812fa859d66457dc1f4faa22c9a15ff57a809986e5230a178f69c206`. Authentication and private homes were never exported; the local archive retains controller paths, which are excluded from public facts. The [exporter](support/summarize-quality.py) produces the public facts, and the [development guide](../development.md#minimal-requests-and-independent-code-review) describes the runners. [Supplementary probes](2026-10-08-quality-efficiency-supplement.json) were chosen from blind-review findings and executed after delivery; they are not part of frozen acceptance. Their [source](support/probe-quality.py) is public.
