# Plan: measure the value and cost of a complete development journey

Status: implementation in progress. Requested after the value-first pilot; supersedes its decision to defer lifecycle evaluation. Starting product: `47ae32d688a46359f0f9117c96b7b79ad3650e93`. The user additionally requested product improvements toward the four outcomes. Implement and regression-test the concrete gaps below, then freeze the candidate before model calls; do not tune it against delivered outputs.

## Question and comparisons

Does tack's additional work buy a better accepted delivery, fewer substantive defects, more reliable project conventions, easier later changes, or better contributor handoff? More tokens and workflow activity are costs, not benefits. Report negative and inconclusive results as prominently as gains.

Compare three conditions: ordinary agent with project facts but no added practice instructions (`plain`); the same project plus a short conventional AGENTS.md (`project`); the same project with the frozen tack installation (`tack`). All receive the same product requests, contracts, tools, public tests and review evidence. Implementation requests do not tell plain to add tests, follow TDD/SOLID or create abstractions. Setup and review requests necessarily describe the requested setup/review outcome. Plain can discover conventions or create its own guidance; retain that behavior.

Two new scenarios cover a solo stock-allocation application and a backend/frontend order contract. Each journey has four fresh model sessions: setup, implementation, a later change by a fresh participant, and review resolution. Use two explicit implementer models (gpt-6-luna and gpt-6.1-sol), medium effort, two repetitions, and counterbalanced condition order: 24 journeys / 96 planned sessions. At most one additional repair per journey (24), driven by the same frozen final acceptance criteria. Eight matched blocks have both initial and final code reviews (16), plus four preselected order reversals (4). Maximum: 140 sessions, concurrency two, no unreported retries.

## Product changes before the freeze

- Add `tack verify --all`: a clean clone currently selects no checks and has no CLI route to run all declared checks. Preview, local trust, budgets and incomplete results remain intact. Test a real defect in a clean checkout and its repair. This supports contributor setup and integration without making full checks a per-edit default.
- Add focused contract-review guidance for the validation/consumer gaps observed in earlier code reviews; preserve TDD and inspect rule coverage beyond passing tests. Use existing contracts and handoffs to support later changes.
- Make recorded shared setup choices visible to fresh clones without silently completing local review or granting trust. Reuse accepted choices rather than repeat the questionnaire. Keep the existing atomic shared-profile apply path.
- Correct the stale strict-mode CLI help. Documentation must distinguish these functional improvements from any measured lifecycle benefit.

## Implementation

1. Add `evals/lifecycle_fixture.py` and `evals/lifecycle_grade.py`: new public contracts and evaluator-only behavioral checks, reference solutions and deliberate mutations. Test the graders before model execution. Include input preservation, validation, compatibility, a real later change, integration and a review fixture with a true defect, an outdated valid finding, an existing follow-up and a non-binding style suggestion.
2. Add `evals/lifecycle.py` and `evals/lifecycle_worker.py`, reusing isolated container transport and Codex invocation helpers. Fresh homes and cloned/transported repository state make carryover explicit. Record setup/install separately; include them in journey totals. Capture every stage before controller transport commits; those commits do not count as model convention compliance. Hidden checks remain outside model sessions. Retain failed attempts, timeouts, repair feedback and unresolved outcomes.
3. Add `tests/lifecycle-eval.test.py` to `tests/evals.test.sh`. Cover finite matrices, prompt/input parity, grade/reference/mutation behavior, and workflow evidence classification. A failing command alone is not proof of red/green TDD; require the relevant test failure followed by a passing run, otherwise report unknown/unproven.
4. Freeze the protocol, fixture/grader hashes, product/image revisions, models, ordering and session limits in a committed manifest before calls. Run a read-only dry run and infrastructure smoke; disclose any protocol corrections and exclude no valid failed model attempt. Complete every scheduled scenario despite unfavorable performance; stop only for infrastructure, authorization or resource failures.
5. Independently review anonymous production code for all initial/final matched blocks using the existing six-dimensional rubric. Review tests/process separately so extra artifacts cannot inflate code quality. The orchestrator inspects defects and real later-change diffs before revealing review labels where possible; disclose any prior knowledge. Check sensitivity with four reversed-order bundles.
6. Publish `docs/benchmarks/2026-10-08-lifecycle-value.md`, machine-readable aggregate results and evidence hashes. Update README, `docs/results.md`, `docs/why.md`, engineering practices and architecture as appropriate. Distinguish observed benefit, plausible untested benefit and overhead without demonstrated compensation. Retain all previous reports unchanged.

## Measures and decision rules

- Functional acceptance before/after repair, regression failures and useful tests against the original fault; do not equate a green suite with completeness.
- Independent code quality, substantiated defect severity, simplicity, consistency and changeability. Actual later-change time/diff supplements the reviewer estimate; no claim about large-system scalability from these small fixtures.
- Observed branches, conventional commit titles/no AI attribution, relevant check execution, test usefulness, red/green evidence, canonical documentation and review follow-up reuse. Report missing/unknown evidence; do not grade instructions as actual compliance.
- Coding, setup/install, later-change and review/repair wall time and input/cached/output tokens separately; lifecycle totals include unsuccessful attempts and repairs. Agent review evaluation cost is separate from product review-resolution cost. Cached input is a subset, not an additional charge or a dollar price.
- Report paired per-model/per-scenario outcomes and dispersion, not only pooled means. Small repeated synthetic scenarios do not establish general effects or human time savings. Failed deliveries stay in denominators; never report a cheaper failed delivery as a win.
- An extra cost is justified in a tested case only by a concrete benefit: fewer consequential defects, accepted deliveries a cheaper alternative misses, or reduced total accepted-delivery/change effort. Protocol targets are hypotheses, not claims. If quality and lifecycle outcomes tie while cost rises, call the overhead unjustified for that case.

## Verification and delivery

Use CI-pinned lint, the evaluation tests, documentation links and affected regression suites. Run the complete suite before merging changes to shared runner behavior. Work on `eval/lifecycle-value`, use Conventional Commits without AI attribution, publish a PR using the repository template and merge only after current-head CI succeeds. User authorization for subscription runs, publication and merging persists. No real GitHub review comments or issues are needed for synthetic review fixtures.
