# Project adoption comparison protocol

Status: fixed before model execution; results will be linked after the batch.

## Question and conditions

Does tack help carry an agreed engineering setup into a new clone and deliver correct changes at an acceptable cost? Product revision: `a54eda9b934f76e03071c2e6a80f5d4daee3d07f`.

- Baseline: Codex with a clean personal configuration and the same useful project `AGENTS.md`, contracts, architecture, tests and contribution instructions. The assistant can improve project guidance during setup.
- Tack: the same fixture and prompts, plus the default tack installation with plugins skipped and local activation before setup. The assistant configures the shared profile, mappings and setup choices using tack's workflow.
- `gpt-6-luna` and `gpt-6.1-sol`, medium reasoning, two repetitions per condition: eight journeys and at most 24 model sessions. Ordering seed 20261008; concurrency two journeys; 600 seconds per session. No retries replace failed attempts.
- One-time installation and clone setup durations are separate from model-session time. There is no API billing key; observed subscription tokens are not USD charges.

## Three stages per journey

1. **Adopt:** inspect an existing Node event service. Keep its conventions and `guide/architecture.md`, `work/plans` and `work/handoffs` locations. The user has already selected brief replies, task-scaled effort, TDD for behavior, SOLID with KISS/YAGNI, Conventional Commits without AI attribution, branches, meaningful tests and same-change docs. Add a PR template and document commands; decline external skills, additional agents, release automation and new dependencies. Commit the setup locally without changing production behavior. Tack should share its selected preferences; baseline should use native project guidance.
2. **Second clone / bug:** clone the committed setup into a new home and start a fresh session. Fix acceptance of zero order quantity, following the existing full domain contract. Keep the shared setup. Execution trust is inspected before the harness grants fixture-local trust for the authorized checks.
3. **Feature:** a fresh session in the second clone adds `invoice.paid` using the documented invoice contract. Keep order behavior, input immutability and event catalog current. No interactive memory from the previous session is resumed.

The runner does not repair missing commits or configuration. The next clone receives only committed files. A runtime failure is retained; later stages are not silently substituted. The runner may snapshot the complete worktree for grading without committing it into the handoff.

The committed setup becomes the teammate's local trunk. After the bug session, the runner advances that local trunk only to delivered descendant commits before the feature session; uncommitted edits remain visible and are never silently committed. This is local integration bookkeeping, not a simulated GitHub review.

## Predeclared outcomes

- Functional correctness: hidden checks of order quantity boundaries, invoice amount boundaries, routing, unknown types, preserved IDs and caller immutability. Public checks are reported separately. Hidden checks are not copied into the container until every model session has finished.
- Adoption: actual shared profile values/origins in the second clone for tack; project instructions, commands, preserved context location, PR template, existing file preservation and no declined additions for both. Baseline is not penalized for lacking tack-specific files.
- Trust separation: the second tack clone must initially be untrusted. Shared setup must not grant trust.
- Regression sensitivity: after delivery, independently replace validation with a permissive copy and invoice routing with a wrong topic in disposable copies; report whether the model's tests catch these faults. This measures those faults only.
- Quality review: readability, appropriate modularity, robustness, useful regression tests and scope discipline. Record concrete findings per journey. Review is by the same assistant, unblinded and not independent; no aggregate subjective score is a primary outcome.
- Time, observed input/cache/output tokens, failed or timed-out sessions, installation cost and verification commands. Report models separately; small samples do not establish statistical significance. A command called `verify` is not evidence of its success or of a defect caught; inspect its output.

## Environment and reproducibility

Use Codex CLI 0.160.1 and the existing [subscription launcher](support/codex-subscription.py). Each participant has its own HOME, XDG paths, Codex state and Git configuration. Only subscription authentication is copied, with private permissions. The disposable Linux container has no host mounts; its seccomp setting permits the workspace sandbox. Fixture Git writes are explicitly permitted. Neither fixture can publish remote changes; no GitHub credentials are provided.

The product is extracted from the declared Git revision, excluding `evals`, `tests` and `docs/benchmarks` from the model-visible installation. Runtime files and guides are unchanged. The runner records the resulting tree hash and checks it again after the batch. Evaluator self-tests run first; their grading files are removed from the container before model execution.

Record fixture, prompt, source, configuration and hidden-check hashes, versions, exact prompts, transcripts, commit histories and artifact snapshots. Publish only non-secret summaries and diffs after review. Retain raw evidence locally as an ignored archive, remove temporary authentication, and preserve failed attempts rather than rerunning until green. Test the environment before the comparison; any model-consuming qualification is reported separately.

Codex execution uses the documented [non-interactive JSON event stream](https://learn.chatgpt.com/docs/non-interactive-mode), inspected on 2026-10-08. Runtime model observations are configuration evidence, not independent server-side model identification.

## Evaluator corrections

During artifact inspection, before final grading, the PR-template detector was corrected to accept uppercase `PULL_REQUEST_TEMPLATE.md` in standard locations, with an offline regression test. The original lowercase-only implementation would incorrectly reject a valid template. The predeclared criterion (a suitable PR template), model prompts, product files and behavioral acceptance tests are unchanged; every journey uses the corrected detector.

Final infrastructure review also isolated HOME/XDG/Git for every evaluator self-test and post-run npm mutation probe. Model sessions already had private homes; the original grading occurred in the disposable container. The correction prevents npm cache writes to a developer's home when running the evaluator locally. Acceptance criteria and mutants are unchanged; offline grading is repeated against the saved snapshots without new model sessions.
