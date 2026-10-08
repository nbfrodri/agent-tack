# Faster adoption and independent code-quality evaluation

Status: in progress. Shared-profile application, onboarding/testing guidance, README improvements and the departure guide are implemented. The new evaluator is under local validation; live outcomes are not yet reported here.

Starting revision: `8470e487527954304a8e4c5a80bf3420b85725bc` (PR #133). Conversation decisions: support individual and team use, retain practical engineering guidance, reduce avoidable overhead, and compare ordinary requests with and without tack. An independent agent must grade the delivered code, with evidence reviewed by the orchestrator.

## Outcomes and limits

1. Save every explicitly selected shared preference, even when it equals today's default. A teammate should inherit the decision, not accidentally inherit a conflicting personal default.
2. Make setup and daily work shorter without removing useful checks, project context, local trust or engineering guidance.
3. Measure correctness, code quality, workflow and time separately. Passing tests alone is not a quality score; an attractive design alone is not proof of correctness.
4. Evaluate a minimal user request without injecting TDD, tests, SOLID, modularity or Git practices into the untreated condition. Let tack supply its normal guidance in the treated conditions.
5. Publish adverse and inconclusive outcomes as readily as improvements. Tack guides practices and enforces selected checks; it cannot guarantee that a model follows every recommendation.

The earlier [adoption experiment](../benchmarks/2026-10-08-adoption.md) remains a valid comparison against good native project guidance. Do not rewrite its prompts, evidence or conclusions. The new experiment answers a different question.

External skills keep their existing optional, assistant-guided selection and reviewed installation through an existing installer. A proprietary package manager or background update service is outside this work. If repeated adoption failures justify more automation later, first consider bounded checks for provenance, duplicates and missing references, or a thin installer wrapper. Preserve explicit selection, project scope and reviewed updates.

## Starting evidence

- The previous setup prompts and fixture AGENTS.md explicitly supplied engineering practices to both conditions. Inspect `evals/adoption_fixture.py` before reusing any prompt or seed data.
- Quality review was by the same assistant, unblinded, without numeric scores. All 16 code tasks passed; tack took 2.11x and 1.96x total session time with the two tested models. This does not isolate the cause of the overhead.
- Two setups omitted the shared Conventional Commit preference because its default already matched. `lib/project_config.py` preserves explicitly written defaults correctly; the omission happened during assistant-led setup.
- `tack config --json` already reports all setting values and origins. `tack setup --json` already provides bounded discovery. Reuse them rather than introduce another configuration store.
- `lib/verification.py` deduplicates identical command strings, but cannot infer that a full suite contains a focused suite. It deliberately reruns checks rather than reuse cached success.
- Startup context already has a bounded, on-demand index in `lib/project-context.sh`. Do not assume that removing more context is an improvement without measurement.

## 1. Freeze the comparison and collect an overhead breakdown

Create `docs/benchmarks/2026-10-08-quality-efficiency-protocol.md` before live evaluation. It will own the exact hypotheses, task contracts, prompts, rubric, source hashes, runtime settings, ordering seed, budgets and decision rules described below. Keep this implementation plan separate from the result report.

Use the archived adoption transcripts for exploratory profiling. Extend the existing metrics/export helpers only where necessary. Record setup commands, repeated help/source discovery, context reads, tool calls, check invocations and check durations when observable. Keep an `unknown` category: command counts and elapsed gaps are not reliable measures of model reasoning time or causal attribution.

Separate installation, guided setup, coding, checks performed inside the coding session, post-delivery grading and reviewer time. Do not subtract checks from agent wall time and then count them twice. Record input, cached input and output tokens separately; subscription use does not imply a measured dollar price.

Completion: a frozen current-product reference, a reproducible measurement schema and a short list of observed overhead candidates. No performance claim yet.

## 2. Make shared setup explicit and shorter

Existing files: `bin/tack`, `lib/project_config.py`, `lib/project_setup.py`, `skills/new-project/references/onboarding.md`, `tests/project-config.test.py`, `tests/project-setup.test.py`, `tests/cli.test.sh`.

Proposed CLI addition:

```bash
tack config --shared --apply selected-profile.json --dry-run
tack config --shared --apply selected-profile.json
```

These flags do not exist yet. The input uses the existing version-1 `tack.json` shape, including an optional shared mode. It contains only decisions already selected by the user or authorized plan.

- Reuse the existing registry and validators; extract reusable profile validation inside `lib/project_config.py` rather than duplicate it in setup.
- Validate the entire input and merged result before writing. Merge only supplied mode/config keys; preserve other accepted project values. Keep current single-setting commands and precedence unchanged.
- Store explicit values even when they equal defaults. Do not copy all ambient/global values into the project. Retain `--unset` as the separate removal operation.
- The preview reports added/changed/unchanged selections and local overrides that will shadow them. Apply performs one validated profile write and reports saved scope plus effective origins. A no-op leaves the file unchanged.
- Reuse atomic replacement, file-size bounds and concurrent-edit detection. Reject duplicate keys, unsupported versions, unsafe files, invalid values and nonshareable settings without partial updates. Check the merged context paths for conflicts and unsafe locations before saving.
- Applying preferences does not activate tack, grant trust, execute discovered commands, create optional scaffolding or mark setup review complete.
- Make `tack setup` output a short sequence of next steps with the existing machine-readable discovery data. The onboarding guidance reads discovery and current preferences once, presents unresolved choices together, applies accepted preferences together, then checks readiness and origins.
- Keep individual/local setup equally documented; using tack alone must not require a shared profile. Respect declined additions and existing configuration.

Behavioral tests must include a second clone whose personal Conventional Commit default is `false`: a selected shared `true` must still read as `true (shared)`. Also cover a local override that intentionally wins, repeated application, preservation of unrelated keys, invalid input with no writes, changed-input refusal, path conflicts, and trust remaining local.

Completion: selected policy survives a clone with conflicting personal defaults; the ordinary setup path is possible from CLI help and owning docs without reading implementation files. Fewer invocations are a mechanism to test, not a promised speedup.

## 3. Remove redundant work without weakening verification

Existing files: `skills/new-project/references/onboarding.md`, `skills/dev-workflow/SKILL.md`, `skills/testing/SKILL.md`, `lib/project-context.sh`, `lib/verification.py`, `docs/verification.md`, `tests/verification.test.py`.

- Reconcile affected-check guidance across the workflow and testing skill. Keep TDD for behavior at standard/strict, pragmatic SOLID with KISS/YAGNI, meaningful tests, branches, Conventional Commits, no AI attribution, PR templates and affected documentation.
- Avoid repeating a just-passed check during the same task without relevant edits, new evidence or a project requirement. Keep mandatory project/CI checks. Reusing an assistant's observed result is distinct from adding a verifier cache.
- During setup, inspect what existing commands actually run. Prefer a single useful suite for a small project, or focused maps where checks are genuinely separate. Do not automatically map one change to a focused suite and a full suite that repeats it.
- Keep exact-command deduplication. Do not introduce heuristic command containment, a new map schema or automatic cross-session success caching in this iteration.
- Keep document paths visibly pending manual review when no meaningful executable check exists. Do not map prose to unrelated tests just to get `passed`; do not change `incomplete` exit semantics.
- Change startup code only if profiling finds a concrete duplicated read/process cost. Preserve bounded context, configuration origins, handoff freshness and discovery of existing project instructions. Add regression coverage for any changed hook or startup behavior.

Completion: offline cases still detect failing, timed-out, stale-input and unmapped checks. Inspect representative generated maps and session traces for repeated work. Code changes to the verifier are conditional on an observed issue, not a quota of features to add.

## 4. Build an uncontaminated task benchmark

Create `evals/quality_fixture.py`, `evals/quality.py` and `evals/batches/quality-efficiency.json`. Reuse the isolation, source hashing, subscription launcher and transcript metrics in `evals/adoption.py` where their contracts fit. Parameterize invocation narrowly if required; do not build a second generic agent framework or change old manifest meaning.

### Conditions

| Condition | Agent receives |
| --- | --- |
| Plain project | The task, ordinary source/tests and product documentation; no tack installation, injected practice guide or inherited personal skills/instructions. |
| Current tack | The same task and project plus tack from the frozen starting revision, with a reproducible normal activation/profile. |
| Improved tack | The same task and project plus the candidate revision, with equivalent selected preferences and setup complete. |

All three receive exactly the same task text. Example: `Add invoice.paid support according to the event contract.` Another: `The CLI drops values containing an equals sign. Fix it.` The contract supplies expected product behavior; it must not smuggle in instructions to write tests, refactor, use SOLID, make commits or update process documents.

Audit the full visible input, not just the final prompt: AGENTS.md/CLAUDE.md, parent directories, provider settings, HOME, skill catalogs, README and fixtures. The plain project retains existing tests, commands and domain facts, but receives no custom engineering-policy text. All arms still share the provider's built-in instructions; the experiment cannot remove or claim to remove those.

Use common runner-level restrictions for isolation, no publishing/network services and bounded execution. Do not give only one arm special tooling permissions. For this attribution experiment, implementers work without delegated implementers in every arm; the independently authorized grading agents run after delivery. Record this limit on generalization to delegated workflows.

Proposed task families, with public contracts and initial files frozen before execution:

1. A bounded validation bug in an existing Node service: retain valid behavior while fixing a boundary condition.
2. A multi-module event feature: validation, routing and a documented public interface, with no prescribed implementation structure.
3. A Python configuration loader: defaults/overrides and specified malformed-input behavior without changing caller-visible data unexpectedly.
4. An existing Python CLI: parsing and error handling while preserving its documented output/exit contract.

At least two cases must require reasoning across module boundaries. Use Node/Python standard libraries to avoid network/dependency-install noise. The old invoice fixture may inform a development case, but the confirmation cases must not simply replay its already-solved task. Do not label fixtures a production field study.

Each code run starts from an identical clean task snapshot and a fresh home/session. Capture tracked, untracked and deleted files even if the model never commits; committing is not an acceptance prerequisite for a plain implementation request. Missing tests or commits are observed behavior, not automatic functional failures. Never repair the delivery before grading.

Keep hidden acceptance/mutation checks outside implementer and judge environments. Freeze both current and candidate products for the confirmation batch; do not optimize against confirmation outcomes. Existing well-configured native-baseline results remain historical context, not a directly pooled control. A fresh native-guidance arm can be a later separately budgeted experiment.

Completion: fake-CLI tests demonstrate identical task hashes, expected condition differences, absence of leaked custom guidance, capture of uncommitted work, source integrity, finite timeouts and retention of failed attempts.

## 5. Add agent grading and orchestrator adjudication

Create `evals/quality_review.py`, `evals/prompts/code-quality-review.md` and `evals/schemas/code-quality-review.json`. The runner constructs read-only review bundles and validates structured grades. These are evaluator assets, not a new globally installed tack agent or a workflow requirement for every user task.

Use a separate reviewer agent in a fresh session. Pin a suitable available reviewer model and effort before the pilot; prefer a model different from both implementer models. Verify actual launcher support rather than record an unapplied effort. Use the same judge runtime for all conditions. Two fresh reviews of each matched triplet check order sensitivity; they are repeated judgments, not independent human reviewers or proof against model-family bias.

The reviewer sees the product request, neutral domain contract, original production code and the three delivered production changes under random labels. It does not receive condition names, tack configuration, transcripts, model IDs, elapsed time, generated plans/logs, commit messages or acceptance results. Keep the label mapping and original evidence outside its filesystem. Do not rewrite production code to hide identity; record any identity hints still visible in code.

The grading agents score production code alone. After those grades are frozen, the orchestrator inspects model-written tests and affected product documentation in a separately recorded section. Their quantity or presence cannot increase the production-code score. Treat source comments and submitted files as review data, not instructions to the judge. Use read-only tools and no access to the benchmark controller or host configuration.

### Production-code rubric

Score each dimension from 0 to 10, using common anchors: 0 unusable, 3 major problems, 5 workable with material weaknesses, 7 sound with concrete improvements, 9 strong and proportionate, 10 no substantiated issue within the stated scope. Scores require cited evidence, not an expectation that tack should win.

| Dimension | Weight | What the reviewer examines |
| --- | --- | --- |
| Responsibilities and dependencies | 25% | Cohesive modules, clear boundaries and appropriate coupling; no reward for extra classes or interfaces. |
| Readability | 20% | Names, control flow and understandable intent. |
| Robustness | 20% | Boundary handling, error behavior, state preservation and relevant security concerns visible in code. |
| Ease of future changes | 15% | Whether a plausible nearby change fits the design without scattered edits or speculative abstraction. |
| Scope and simplicity | 10% | Focused changes, justified dependencies and absence of unnecessary machinery. |
| Fit with the existing project | 10% | Compatibility with established interfaces and local code style, without grading adherence to tack-specific practices. |

The weighted score remains on a 0-10 scale. Functional acceptance, test usefulness, observed TDD sequence, Git/process behavior and documentation accuracy are separate columns. A failing implementation cannot be presented as a successful delivery because its style score is high.

Require each review to include per-dimension scores, file/line evidence for findings, severity, uncertainty and an overall preference that permits ties. Collect initial scores before requesting the comparative preference. Change presentation order and labels for the second fresh review. Validate score ranges, weights, candidate IDs and cited paths; preserve invalid or missing reviews rather than silently replacing them with favorable grades.

The orchestrator then reads every matched code set and both reviews while condition labels remain concealed, confirms or rejects cited findings, and records its own assessment. Inspect score differences of at least two points and disagreements about severe defects explicitly. Only then reveal labels and join acceptance/time results. Preserve both raw agent grades and the orchestrator's adjudication with reasons; never rewrite the original scores. The orchestrator designed the experiment, so disclose residual expectation bias and any condition it inferred.

Completion: a report can show a grade with supporting code evidence for each candidate, reviewer disagreement and the orchestrator's decision. Agent opinion is supplementary evidence, not an objective quality certificate.

## 6. Run a finite pilot, setup comparison and confirmation batch

Use the existing Codex subscription authorization. No additional budget permission is needed for the bounded batch below. Before calls, resolve the available implementer models used previously, pin exact IDs, a supported effort, CLI/launcher versions, reviewer settings, product hashes and tool permissions in the protocol. Any unavailable runtime produces an explicit manifest revision before execution, not a silent substitution.

| Stage | Matrix | Maximum model sessions |
| --- | --- | ---: |
| Development pilot | One separate development task, one implementer, three conditions; two blind reviewer sessions | 5 |
| Setup comparison | Two implementer models x current/improved tack x two repetitions; one setup session each | 8 |
| Coding confirmation | Two implementer models x four tasks x three conditions x two repetitions | 48 |
| Code review | Sixteen matched triplets, each reviewed twice with changed presentation order | 32 |
| Total | Orchestrator assessment and local automated checks are separate | 93 |

Use no more than two concurrent model sessions, 600 seconds per implementer/setup session and 300 seconds per reviewer session. This caps model-session time at 12 hours 40 minutes before local preparation/checks; with two slots the wall time is not guaranteed. It is a ceiling, not an expected duration. Apply bounded timeouts to all grading commands as well. Record aggregate elapsed time and token use as work proceeds.

The pilot checks the runner, isolation, rubric calibration and review format. It is not evidence of improvement and is excluded from confirmation aggregates. Freeze the candidate and held-out task snapshots after development and before the confirmation batch. No automatic retries or best-of selection; provider failures, timeouts and incomplete deliveries remain in attempt counts. Stop new calls on an isolation failure or exhausted cap, preserving the partial report. Any extension requires a new declared batch rather than silently growing this one.

In the eight setup sessions, reuse agreed choices rather than test a live human conversation. Verify the committed configuration in a second real clone with a fresh home and deliberately conflicting personal defaults using deterministic probes. Check effective values and origins, local override behavior and absence of inherited trust. This isolates setup transfer; it does not measure human decision time or a second model's interactive onboarding.

Randomize implementation order within model/task/repetition blocks and balance condition order across the schedule. Preserve cache counters and concurrency; identical settings do not remove service load or caching variability. Report task-level results and per-model ratios, not only a pooled average.

## 7. Decide from separate quality, correctness and speed evidence

Report:

- Hidden functional acceptance with failed/incomplete attempts included, plus defect-sensitive tests where applicable.
- Blind production-code scores by dimension, supporting findings, preferences/ties and disagreements; orchestrator adjudication alongside raw grades.
- Useful test behavior and observed workflow as separate outcomes, without treating test counts or extra artifacts as quality.
- Setup transfer values/origins and elapsed time; coding session elapsed time and token use; reviewer and post-delivery grading overhead separately.
- Completed-run time distributions alongside timeout/completion counts. Include failed-attempt time in total time per accepted delivery so an early failure cannot appear to be an efficiency gain.

Provisional performance goals are at least 20% less mean coding-session time and 30% less mean setup time for improved versus current tack, reported per model with paired task details. They are targets, not promised effects. A result versus the plain project answers a different question from improvement over current tack.

Accept an optimization only when local regressions pass and it introduces no observed functional, trust, portability or severe design regression. Flag a mean blind quality-score drop greater than 0.5/10 for review even if time improves. Small samples cannot establish equivalence or statistical significance; do not translate this decision rule into a general noninferiority claim. Report mixed outcomes, including ties or speed gains without a quality gain.

## 8. Tests, documentation and delivery

Extend `tests/project-config.test.py`, `tests/project-setup.test.py` and their shell suites for shared setup. Add `tests/quality.test.py` and wire it into `tests/evidence.test.sh` for offline benchmark/reviewer regression coverage. Keep the original adoption tests passing. Add installer/hook tests only if those components actually change.

Offline evaluator cases: matrix/session caps, reproducible order, prompt/input isolation, fresh HOME/XDG/Git/provider state, npm cache isolation, honest missing runtime observations, uncommitted snapshot capture, hidden-check separation, label mapping inaccessible to reviewers, changed review order, invalid judge JSON and citations, timeouts, unchanged frozen source and preserved failure evidence. Test real behavior rather than matching implementation wording.

Verification during implementation:

```bash
tests/project-config.test.sh
tests/project-setup.test.sh
tests/verification.test.sh
tests/evidence.test.sh
tests/cli.test.sh
tests/validate.sh
tests/lint.sh
```

Run suites relevant to each change first; run the full required suite before integration, and avoid repeating passed suites without new changes or evidence. ShellCheck 0.11.0 and ruff 0.14.0 match CI. Real subscription runs need the pinned Codex launcher and a disposable Linux environment on this Windows workstation; deterministic product tests must also retain native Windows/macOS coverage. Tests use temporary HOME, XDG_CONFIG_HOME and GIT_CONFIG_NOSYSTEM=1.

Update owning guides with behavior changes: `docs/configuration.md`, `docs/setup.md`, `docs/verification.md`, `docs/development.md` and `docs/architecture.md`. Keep examples in their owning guide and link from sharing/usage only when needed. Publish protocol, quality evidence and measured results under `docs/benchmarks/`, link from `docs/results.md`, and add only a short accurate result to README and CHANGELOG. Raw transcripts/authentication do not belong in commits; keep sanitized facts and evidence hashes.

Suggested coherent commits/PRs, in dependency order:

1. Shared-profile application, onboarding guidance, regression tests and owning docs.
2. Measured reductions in repeated work, preserving verification semantics.
3. Frozen evaluation protocol, fixtures, blind review runner and offline tests.
4. Complete confirmation results, orchestrator review, limitations and subsequent improvement candidates.

Use branches and Conventional Commits without AI attribution. Follow the existing authorization for publication and merge only after the relevant CI checks pass. Revert an optimization independently if it fails the safety/quality gates; do not discard experimental evidence. No tack.json format migration, global installation-profile removal or change to default trust is planned.

## Done means

- Selected shared preferences remain explicit and portable, with precedence and local trust preserved.
- Setup and runtime optimizations are documented with measured outcomes, including an unmet speed target if that is the result.
- Minimal requests are compared without injected practice guidance, under controlled environments and frozen revisions.
- Every delivered code candidate has functional evidence and a separately recorded independent-agent review; missing reviews remain visible.
- The orchestrator has checked review evidence, documented disagreements and disclosed the limits of blinding.
- Reports preserve all attempts, raw reviewer grades, adverse results and meaningful limitations; engineering guidance remains intact.
