# Plan: evidence, simplification and project capabilities

- **Date:** 2026-10-07
- **Status:** completed (authorized local implementation; real-model experiments deferred)
- **Starting revision:** `8c23eba`
- **Scope:** improve measured usefulness, reduce maintenance and context cost, and let the assistant create useful project skills and agent definitions.
- **Confirmed decision:** create capabilities in the project first; consider global promotion later when reuse justifies it.
- **Delivery:** implementation authorized on 2026-10-07. The user selected local tests only and prepared benchmarks; real-model runs are explicitly deferred. No global installation or external publication is included.

## Goal

Make tack easier to maintain and demonstrably useful while allowing it to learn reusable, project-specific procedures and roles during authorized work.

## Starting point

- `evals/run.sh`, `grade.py`, `metadata.py` and `report.py` already provide scenarios, hidden acceptance tests, transcript metrics and reports. Extend them instead of building another evaluation system.
- The report groups by scenario, metric version and provider, but not model, CLI version, prompt or tack revision. The runner couples the Codex provider to `codex-new-project`, inherits parts of the user's environment, and removes an existing output directory when the same run is repeated. These must be addressed before collecting larger comparisons.
- `tack log --skills`, `--cost` and `--levels` already exist. Logging is opt-in, observed usage is incomplete, and absence from a transcript does not establish that a capability was unnecessary.
- The current catalog contains 19 skills, 10 agents and 23 feature toggles; skill descriptions total 4,879 characters. `skill-groups.txt` supports optional groups but the default installs all groups.
- `lessons` currently requires proposing every new skill first; it has no autonomous project-capability lifecycle. `orchestrate` controls delegation independently. `lite` is self-contained and does not normally load `dev-workflow`.
- The former lean mode has already been merged into lite. Do not repeat completed cleanup from older audits.

## Acceptance criteria

The checklist reflects the user's final local-only scope. Behavioral efficacy, model trigger retention and actual cross-session model reuse remain future experiments, not acceptance claims from simulated CLIs.

- [x] **R1 — Reproducible comparisons:** each run has an isolated environment, immutable identity and comparison metadata; incompatible or unknown configurations cannot silently share a result column.
- [x] **R2 — Useful outcome reporting:** reports separate acceptance-test success, task completion and regressions from process compliance; show sample size, uncertainty, time, tokens, cost and missing observations.
- [x] **R3 — Evidence-led simplification:** published a component decision table and reduced description characters by 37.7%, preserving installed groups, references and existing safety checks. Real-model trigger retention is unmeasured.
- [x] **R4 — Autonomous local creation:** added policy allowing relevant local skills and roles during authorized implementation, with read-only and planning boundaries preserved.
- [x] **R5 — Controlled growth:** policy requires search, reuse, specific triggers and task verification; validation and negative-case benchmarks are implemented. Global promotion remains separate.
- [x] **R6 — Reuse evaluation prepared:** two fresh CLI invocations, completed-read evidence and functional acceptance checks are tested offline. Definition creation, sequential reading and subagent invocation are distinct observations; no real-model reuse result is claimed.
- [x] **R7 — Portable behavior:** retained Bash 3.2 syntax, English content, isolated test homes and Git configuration, tool-neutral rules and delegation boundaries. Native discovery has an explicit reading fallback.
- [x] **R8 — Verified integration:** all 19 Linux suites, pinned lint and content validation pass. macOS/Windows CI coverage remains configured; those remote jobs and optional native plugin checks were not executed locally.

## Design

### Measurement before broad pruning

Keep the existing evaluation pipeline. Separate scenario selection from provider selection, freeze the source revision and effective configuration, and run both baseline and tack conditions in independent homes. Compare a frozen current version with candidate simplifications; do not optimize against hidden acceptance tests and then present the same tests as independent confirmation.

Record a batch ID, run ID, source revision and dirty state, effective configuration hash, prompt and fixture hashes, hidden-test version, provider, CLI version, requested and observed model, relevant effort settings, permissions, timeouts, condition and repetition. Unknown model or cost stays unknown. Reports may compare declared experiment conditions, but must not pool different prompts, models or revisions accidentally.

A new, small `evals/batch.py` will orchestrate the existing runner from a JSON manifest under `evals/batches/`. It has a dry run listing the run count and cost estimate when supplied pricing supports one. Resume skips only completed matching runs; mismatched or existing run IDs are never overwritten. Use bounded concurrency, per-run timeouts and a configured experiment budget. If spend cannot be observed, describe the limit as an estimate and retain enforceable run-count/time limits.

First pilot: five existing acceptance-tested scenarios, baseline versus current tack, two explicit runtime/model configurations and three repetitions per cell (60 sessions). The pilot validates the experiment, not a universal quality claim. A later confirmation compares baseline, current tack and the candidate on a frozen manifest; ten repetitions per cell would be 300 sessions with the same matrix. Select the actual batch size from the available budget before launching; do not launch these sessions as part of this plan or ordinary CI.

Add at least one non-Python, multi-file scenario and held-out variants for confirmation. Alternate or randomize condition order with a recorded seed. Keep the runtime/model configurations separate in analysis. Report confidence intervals for success rates and observed cost/time distributions; small or inconclusive samples remain inconclusive. Infrastructure failures, skipped cases and failed tasks remain visible with their denominators.

### A smaller shared core

Use existing local usage reports and controlled comparisons to classify each component as keep in core, optional, merge or remove. Assess installed availability, dependencies, maintenance burden and observable benefit together; never delete a safety control because it was rarely triggered.

Prioritize these candidates:

1. Reassess which skills truly need to be in `core`; use the existing `process` and `stack` groups for optional procedures. A skill named unconditionally by global instructions must stay installed or have its routing rewritten with a valid fallback.
2. Remove duplicated procedural text and route to existing references only when needed. Keep lite self-contained and avoid making small tasks load the full workflow.
3. Put common settings first in help and usage documentation. Preserve advanced options until evidence supports merging or removing them; do not replace 23 switches with additional presets and another configuration layer.
4. Assess mods, visual review, memory, lessons and requirement tracing from real use and controlled tasks before changing defaults. Unobserved use is not proof of no value.

Do not change every user's installation implicitly. Preserve explicit `skill-groups` choices; retain the previous effective group selection during upgrades, and apply any smaller default to fresh installs or an intentional switch. Test how selected groups, global instructions and doctor agree. Preserve displaced user files and existing ownership behavior. Simplification must not remove the guard, secret checks, protected refs or restoration safety.

### Project skills and agents

Implement this as a focused extension of `lessons`, with a new `skills/lessons/references/project-capabilities.md`, rather than a new always-loaded authoring skill or a plugin marketplace. Add a short rule to `global/AGENTS.md` under enabled projects so it also reaches lite. Route `dev-workflow` and `orchestrate` to the same reference where relevant.

The assistant chooses among four outcomes:

| Need | Action |
| --- | --- |
| A short project convention or command | Update the relevant project instruction or documentation |
| An existing skill or role already covers the task | Reuse it; refine a local definition only if needed |
| A reusable procedure containing project knowledge that would otherwise be rediscovered | Create or update a project skill |
| A reusable specialist role with a distinct responsibility, context and output contract | Create or update a project agent definition |

A repeat occurrence, planned repeated work, or a substantial procedure established during the task can justify persistence. Generic knowledge, speculative future uses and a single trivial subtask do not. Record the reason briefly in the normal change summary; no new mandatory diary or approval ritual.

Proposed canonical storage in a consuming project:

- `.agents/skills/<name>/SKILL.md`, with references or scripts only when useful.
- `.agents/agents/<name>.md` for tool-neutral role definitions. This is a tack convention, not a claim that every tool natively discovers it.
- A short capability index in the project's existing `AGENTS.md`, linking only names, triggers and paths. Preserve unrelated project instructions and any established capability layout.

Search project and installed capabilities before creating files. Use project-specific names, concise English descriptions, and references to the project's actual commands and architecture. A skill specifies trigger, procedure and success checks. An agent specifies role, boundaries, inputs, outputs and the permissions its work needs. Re-running the workflow updates or reuses the same definition; it must not generate suffixed duplicates or overwrite unrelated files.

Local creation does not activate extra tools, permit remote actions or relax safeguards. Creating an agent does not itself authorize spawning it: invocation still follows the user's instructions, runtime availability and `tack.delegation`. If a runtime cannot register a new native agent during the current session, use the role text through the existing delegation interface when allowed, or carry out its checks sequentially and report that fallback. Do not promise automatic reload.

Native registration is optional in the initial delivery. Only add a thin adapter after checking the target runtime's actual project-level format and discovery behavior; reuse `lib/codex_agents.py` where compatible. No change to the global installer is required merely to create or use local Markdown capabilities.

Promotion is a separate change to the shared catalog after evidence of cross-project usefulness. Remove project-specific assumptions, search for overlap, update grouping and component docs, and validate the proposed diff. A local task does not authorize a global installation or publication; apply promotion within the user's authorized scope.

## Implementation sequence

### 1. Make comparisons reproducible — R1, R2

- **Existing files:** `evals/run.sh`, `evals/metadata.py`, `evals/grade.py`, `evals/report.py`, `tests/evals.test.py`, `docs/development.md`.
- Decouple provider from scenario while preserving existing invocations as compatibility aliases. Isolate HOME, XDG directories, provider configuration and Git before preparing either condition. Supply authentication through supported means without importing unrelated instructions, hooks or persistent memory; clean temporary credentials on success and interruption.
- Add experiment identity and configuration fingerprints. Refuse collisions instead of deleting previous output. Keep legacy reports readable and visibly separated from comparable new data.
- Add tests for inherited-config contamination, incompatible grouping, unknown metadata, duplicate IDs, interruption and preservation of previous results. Use fake CLIs and temporary credentials; no real model calls in tests.
- **Done when:** changing a model, prompt, revision or effective config prevents accidental pooling, and repeated invocations cannot erase prior evidence.

### 2. Run bounded experiments and publish useful metrics — R1, R2

- **New files:** `evals/batch.py`, `evals/batches/core-comparison.json`, and a focused non-Python scenario with hidden checks under `evals/hidden/`.
- **Existing files:** `evals/run.sh`, `evals/grade.py`, `evals/report.py`, `tests/evals.test.py`, `docs/results.md`, `docs/development.md`.
- Add manifest validation, dry run, resume, ordering, run limits and timeouts. Avoid a second scenario framework; extract scenario setup from `run.sh` only where needed to keep orchestration readable.
- Report correctness and completion before branch/commit compliance. Include success counts, uncertainty, cost of failed attempts, total spend per successful outcome, and explicit unavailable costs. Separate setup time from agent time.
- Build offline fixtures with known outcomes, invalid manifests, timeout failures and partial batches. Verify that changing the presentation cannot turn failures or missing evidence into successes.
- **Done when:** a pilot can be reproduced from its manifest and revision, and a report makes positive, negative and inconclusive findings equally visible. Real sessions require configured CLIs, credentials and an agreed run budget at execution time.

### 3. Measure and simplify the existing catalog — R3, R7

- **Existing files:** `lib/log-report.py`, `hooks/claude/lib/turn-report.py`, `features.txt`, `skill-groups.txt`, `global/AGENTS.md`, affected `skills/` and `modes/`, `lib/skill-groups.sh`, `install.sh`, `lib/doctor.sh`, `docs/usage.md`, `docs/customization.md`, `docs/components.md`.
- Use `tack log --skills --days 14` and corresponding cost/level reports when representative opted-in data exists. With absent or partial logs, mark evidence unavailable and use a deliberately selected task corpus. Do not add network telemetry.
- Publish a decision table at the new `docs/audits/2026-10-07-capability-simplification.md`: component, observed use and coverage limits, recurring cost, dependencies, decision and supporting task results.
- Deliver one coherent reduction first: lower the default description load through existing groups and remove duplicated guidance. Treat the 20% goal as a measured target, not a reason to hide descriptions or discard useful capabilities.
- Preserve existing users' effective selections before changing defaults. Add regressions to `tests/install.test.sh`, `tests/lifecycle.test.sh`, `tests/doctor.test.sh`, `tests/cli.test.sh`, `tests/validate.test.sh` and hook tests only where their behavior changes.
- **Done when:** before/after context measurements and configuration migration results are recorded, affected tasks still work, and every removed or optional component has a reason beyond line count.

### 4. Teach autonomous project-capability creation — R4, R5, R7

- **Existing files:** `global/AGENTS.md`, `skills/lessons/SKILL.md`, `skills/dev-workflow/SKILL.md`, `skills/orchestrate/SKILL.md`, `skills/new-project/SKILL.md`, `docs/customization.md`, `docs/usage.md`, `docs/editors.md`.
- **New file:** `skills/lessons/references/project-capabilities.md`.
- Replace the blanket propose-first rule for new skills with the confirmed project-first policy. Preserve separate rules for global preferences and memory. Make the lessons description discoverable for concrete reusable project procedures and roles without triggering on every coding task.
- Provide one procedure example, one specialist-role example, and counterexamples for a typo, an existing matching skill and a read-only review. Explain discovery, validation, duplicate avoidance and fallback without reproducing whole templates.
- Check that the short global rule also applies with lite's minimal skill loading and does not force new artifacts for routine work.
- **Done when:** one clear policy governs creation across modes, local creation needs no extra permission round during authorized changes, and global promotion remains separate.

### 5. Validate local capabilities and prove reuse — R5, R6, R7

- **Existing files:** `tests/validate.sh`, `tests/validate.test.sh`, `tests/run-all.sh`, `.github/workflows/ci.yml`, `evals/run.sh`, `evals/grade.py`, `tests/evals.test.py`.
- **New files:** `lib/capability_validation.py`, `tests/project-capabilities.test.sh`, and behavioral fixtures/hidden checks under `evals/hidden/project-capabilities/`.
- Extract only reusable frontmatter, name, description-budget and reference checks from the current validator into the shared Python helper. Keep catalog grouping and full-repository checks in `tests/validate.sh`. The helper validates a specified project's capabilities without changing files or requiring that project to look like tack's own repository.
- Cover malformed definitions, missing references, collisions, unchanged existing files and files outside the chosen project scope. Native registration, if added, must preserve unrelated definitions and have separate adapter tests.
- Add fresh-session evaluation cases: create a useful procedure and reuse it; create a justified role and use its contract; reuse an existing capability without duplication; leave a trivial task and a read-only review free of unsolicited capability writes; respect disabled delegation; use an explicit sequential fallback when native agents are unavailable.
- Verify task outcomes and trace evidence of use, not just the existence of Markdown or a self-reported claim. The reviewer does not expose hidden checks to the working session.
- **Done when:** local files validate, a subsequent session uses them successfully, and negative cases show that the catalog does not grow automatically on unrelated tasks.

### 6. Compare the combined change and close the documentation — R2, R3, R6, R8

- **Existing files:** `docs/architecture.md`, `docs/results.md`, `docs/development.md`, `docs/components.md`, `README.md`, `.github/workflows/ci.yml`, `tests/run-all.sh`.
- Compare frozen baseline/current/candidate conditions, including the cost of creating capabilities and their reuse in later tasks. Attribute gains to simplification or local capabilities with smaller focused comparisons when needed; do not claim causation from the combined variant alone.
- Publish per-scenario correctness and cost, creation frequency, duplicate/unnecessary creations, successful later reuse and runtime limitations. Extend sampling only where the value of resolving uncertainty justifies it.
- Reconcile `tests/run-all.sh` with CI, including `tests/mods-unit.sh` and the new capability suite; document Node/esbuild prerequisites and any skipped optional native checks explicitly.
- Update architecture only when the corresponding implementation lands. Keep Windows doctor/uninstall work as a separate follow-up; this iteration does not claim native Windows support.
- **Done when:** shipped behavior, executed checks and published evidence agree. Archive this plan only after implementation is complete or explicitly abandoned.

## Verification and environment

Run focused suites after each behavioral change, then `tests/lint.sh`, `tests/run-all.sh` and content validation as the final supported-platform checks. The lint prerequisites are ShellCheck 0.11.0 and Ruff 0.14.0 as currently pinned. Register new shell tests in both the runner and CI; every installer or hook change gets a behavior regression test in `tests/`.

Use Linux or macOS for the complete suite; Bash 3.2 compatibility remains required. Native Windows is experimental. The initial review lacked active Docker, ShellCheck and Windows symlink privileges. Implementation verification used a temporary Linux container with the pinned lint tools and Node; the results below supersede that initial environment limitation.

All executable tests use temporary HOME, XDG configuration/state and isolated Git settings. No test runs the installer against the real user configuration. Paid sessions remain manual experiments, separate from deterministic CI.

## Dependencies and remaining execution choices

- Steps 1 and 2 establish trustworthy measurements; step 3 uses their evidence. Steps 4 and 5 define and verify the requested local behavior; step 6 measures the integrated candidate.
- Fix runtime/model selections and the token or spend budget when scheduling the paid batch; there is no assumed budget in this plan.
- Decide the exact components to move or remove from step 3's evidence. The project-first policy is already decided and does not need to be reopened.
- Confirm any native project-agent format against the actual installed runtime before implementing an adapter. The initial Markdown-plus-explicit-reading path remains usable without that adapter.
- Confidence intervals, usage counts and test passes each answer different questions. Keep observed facts, inference and missing evidence separate in the final report.


## Implementation record (2026-10-07)

- The user selected **local tests only; prepare the benchmarks**. Real-model sampling, model selection, spend budgets and empirical claims are outside this delivery.
- Implemented isolated evaluations, immutable run outputs, metric version 3, comparison fingerprints, bounded manifests, resume checks and interruption cleanup.
- Added JavaScript and two-session capability fixtures, hidden acceptance checks, completed-read evidence, scope checks and combined session costs. Fake CLIs prove runner behavior; they do not establish real-model effectiveness.
- Reduced all 19 skill descriptions from 4,879 to 3,038 characters (37.7%). No representative usage log exists locally. Kept all existing installation selections, 23 settings and safety controls; the component decision record explains this narrower first simplification instead of changing defaults.
- Extended lessons and workflow routing with autonomous project-local skills and roles, a discovery index, explicit invocation boundaries and a shared read-only validator. No native project-agent adapter or new always-loaded skill was added.
- Integrated the new suites and mods unit tests in the complete runner. Mods tests now isolate HOME, XDG, Git and the npm cache.
- Linux verification uses a temporary Docker container and a copied checkout with Git-recorded file modes. Windows source permissions initially caused ownership failures; these disappeared after normalizing the copy. No installer change was made to suppress the checks.
- Final Linux verification: all 19 suites passed in 189 seconds, including 51 evaluation tests, 15 evidence tests and 8 project-capability tests. `tests/lint.sh` passed with ShellCheck 0.11.0 and Ruff 0.14.0; content validation passed. Focused evidence tests also passed after the final comparison-identity fix.
- Both benchmark manifests passed dry-run: 60 core-comparison runs and 48 capability runs. Model placeholders prevent accidental execution before deliberate selection. No real-model calls, global installation or publication were performed.
- Real-model effectiveness and trigger-retention measurements remain explicitly unmeasured. Native CLI plugin validation and remote macOS/Windows CI were not run in this local delivery.
