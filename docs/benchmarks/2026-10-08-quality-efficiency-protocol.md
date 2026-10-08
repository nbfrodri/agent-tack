# Minimal-request quality and efficiency comparison

Status: protocol frozen before model execution. Results will be reported separately, including failed attempts and unmet goals.

## Questions

Does tack improve delivered code or observed engineering behavior when the user asks only for a product change? Does the candidate reduce time relative to current tack without observed correctness, design or configuration regressions? These are separate comparisons. The [earlier adoption batch](2026-10-08-adoption.md) compared tack with strong native project guidance and remains historical evidence; its results will not be pooled with this batch.

Current product: `8470e487527954304a8e4c5a80bf3420b85725bc`. Candidate product: `e3d788b` (the full commit is recorded in `evals/batches/quality-efficiency.json`). Candidate changes are batch profile application, shorter setup guidance, and removal of redundant full-suite mandates in the testing skill. Core engineering practices, verification exit semantics and startup context limits remain intact.

Exploratory inspection of the four prior tack setup transcripts found 23, 42, 13 and 18 completed shell-command events. Respectively 2, 5, 4 and 3 included recognizable reads/searches of tack's CLI/config/setup implementation. These are overlapping command categories, not measured reasoning time or proof of the cause of overhead. The exact archived transcripts and the previous report's hashes remain available.

## Conditions and tasks

Every matched triplet starts with identical production code, existing public tests, README, architecture index, domain contract and task text from `evals/quality_fixture.py`.

| Condition | Additional setup |
| --- | --- |
| Plain project | No tack, custom process instructions, user skill catalog or injected engineering-policy AGENTS.md. |
| Current tack | Install the frozen current product with plugins skipped; enable and locally trust it; use auto, brief replies, explicit shared conventions/context paths and completed setup review. |
| Improved tack | Equivalent selected preferences using the frozen candidate product. |

The coding-stage tack profile is prepared deterministically to isolate daily work from setup variability. It includes a short AGENTS.md containing only the project command and neutral contract/architecture links, plus its Claude bridge. The existing public test command is explicitly shared as `check-fast` so unsupported command detection does not manufacture an incomplete setup. No additional check map or local skill is preseeded. Shared setup transfer is measured separately. Installation and deterministic preparation are timed outside model sessions; all work/checks performed by the model remain inside its session time.

Four confirmation tasks: Node pagination boundary handling; a new shipment cancellation event across validation and dispatch; Python layered settings with mutable-state isolation; Python CLI assignment parsing and unset behavior. At least two span modules. Public contracts define observable behavior, not requirements to write tests or use a specific design. A separate small Python total-function task is the development pilot.

The prompts ask for the change only. Audit all visible files for process leakage, including README and parent/home configuration. The provider's built-in instructions remain common to every condition. Existing tests and documented commands remain available to the plain project; adding tests or commits is not a hidden functional acceptance requirement.

## Runtime and budget

Implementers: `gpt-6-luna` and `gpt-6.1-sol`. Reviewer: `gpt-6-astra`. All request medium effort through Codex CLI 0.160.1 and the owner's ChatGPT subscription. Record model/effort observations from runtime context; absent observations remain unknown, and client observations are not independent server-side identification. API keys are not used.

| Stage | Sessions |
| --- | ---: |
| Pilot: three implementations, two reviews | 5 |
| Setup: two models x two product revisions x two repetitions | 8 |
| Coding: two models x four tasks x three conditions x two repetitions | 48 |
| Review: two fresh judgments of each of 16 matched triplets | 32 |
| Maximum | 93 |

Ordering seed is 20261008. Shuffle model/task/repetition blocks and rotate condition order. Use at most two concurrent sessions, 600 seconds per implementation/setup and 300 seconds per review. Bound setup, copying and local grading separately. No automatic retry or best-of selection; retain timeouts and failed/incomplete attempts. Stop new implementation calls after infrastructure failure. A pilot failure may correct evaluator infrastructure before confirmation, but any further model calls need a separately declared amendment within the total cap. Do not tune the product against confirmation outcomes.

Each session runs as an unprivileged user in a fresh Linux container without host mounts. The public build recipe is `evals/quality.Dockerfile`; record the resolved image ID and tool versions because apt packages can change on rebuild. The host controller copies only that run's fixture, the relevant product archive when applicable, a private subscription login and the generic session worker. Hidden checks and reference implementations stay outside these containers. Separate containers prevent a plain implementer or reviewer from inspecting other conditions or the controller's label map.

Codex uses a workspace sandbox with explicit fixture `.git` write permission for implementations, with agent-tool network access disabled. The container seccomp setting permits Codex's own sandbox. Only the locally installed, reviewed tack hooks receive invocation trust; no blanket sandbox bypass is used. Common developer restrictions prohibit publication, dependency installation, external services, questions and delegated implementers. Reviews use the read-only sandbox and no tack installation. API transport can reach the subscription service; it is distinct from agent-tool network access.

Capture committed and uncommitted delivery, including untracked/deleted files. Do not repair or auto-commit solutions. Only committed setup crosses into the second clone. Probe configuration values and origins with a fresh HOME, a deliberately conflicting personal Conventional Commit default, an intentional local reply-style override and initially untrusted execution. No live human onboarding time is measured.

## Independent code review

`evals/quality_review.py` constructs anonymous production-only bundles. The reviewer receives the user request, public contract, original code and three final candidates. It does not receive condition/model names, Git history, process documents, tests, timing, acceptance results or the label mapping. Include new production helpers as well as initial files. Keep exact production text; report any visible origin hint rather than rewriting code to hide it.

Use `evals/prompts/code-quality-review.md` and `evals/schemas/code-quality-review.json`. Two fresh sessions of the same reviewer model use changed labels and reversed presentation order. These measure repeatability/order sensitivity, not independence between model families. Each candidate gets six 0-10 scores with file/line evidence:

| Dimension | Weight |
| --- | ---: |
| Responsibilities and dependencies | 25% |
| Readability | 20% |
| Robustness | 20% |
| Ease of future changes | 15% |
| Scope and simplicity | 10% |
| Fit with existing interfaces and style | 10% |

Use anchored scores from unusable (0) to no substantiated issue within scope (10), with 5 representing workable code with material weaknesses and 7 sound code with concrete improvements. Do not reward additional classes, files, dependencies or process artifacts. Record dimension scores before comparative preference; allow ties. Validate candidate identities, numbers, evidence paths and line ranges. Preserve invalid/missing reviews without fabricating scores.

The orchestrator reviews every blinded code set and both judgments, checks cited findings, and records its own assessment before opening the label map or joining correctness/time results. Explicitly resolve severe-defect disagreements and differences of at least two points. Keep the raw judgments and adjudication separately. The orchestrator built the experiment and may infer origins; disclose that residual bias. Test usefulness and product documentation are assessed separately after production grades are frozen.

Structured rubric-based Codex passes and JSONL capture follow the approach described in [OpenAI's skill-evaluation guide](https://developers.openai.com/blog/eval-skills). This supports the evaluator mechanics, not a claim that model judges are objective or that tack improves code.

## Other outcomes and decision rules

After delivery, `evals/quality_grade.py` runs hidden functional assertions in another isolated environment. It also restores each task's originally defective production files in a disposable copy to check whether the delivered tests reject that seeded regression. Count probe results only alongside a passing delivered public suite; a broken test suite is not defect sensitivity. These probes cover one defect family per task, not general mutation coverage.

Report acceptance and completion counts, per-dimension/weighted code scores, preferences/ties, reviewer disagreement, orchestrator findings, setup portability and all attempts. Keep useful tests, observed workflow, documentation and Git behavior separate from production-code scores. A failed implementation cannot become a successful delivery through a good style grade.

Report model-session elapsed time by task/model/condition, install/setup preparation separately, tool/check counts where observed, and input/cached/output tokens. Runtime transcripts do not expose a reliable reasoning-time breakdown. Reviewer time is evaluation overhead, not ordinary tack latency. Include failed-attempt time in total time per accepted delivery; also show completion rates and completed-session distributions. Do not interpret token ratios as dollar costs or latency as human time saved.

Targets are 20% less mean coding-session time and 30% less mean guided-setup time for candidate versus current tack, per model. They are provisional goals, not previous results. Flag a mean blind score drop exceeding 0.5/10, any new severe design finding, or observed functional/trust/portability regression for investigation before accepting an optimization. Local regressions and required CI must pass. A small synthetic batch cannot establish statistical significance, noninferiority, productivity gains or performance on production repositories.

## Evidence retention

Commit the protocol, task/runner/reviewer assets and offline tests before paid/subscription model execution. Record fixture, prompt, product archive, controller and review-bundle hashes. Raw transcripts/snapshots stay under ignored `evals/out/`; publish sanitized facts and selected review evidence with hashes. Private homes/authentication are never copied back from model containers. Remove each owned container after collecting evidence. Freeze and archive the completed orchestrator assessment before revealing labels.
