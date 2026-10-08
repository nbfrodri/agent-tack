# Plan: prove tack's value and simplify its workflow

Status: implemented; the larger conditional experiment was stopped at its evidence gate. Prepared on 2026-10-08 against `ff53cef1fe2d38f1ba29b495f4ca16e627137a94`. The delivery record distinguishes shipped changes from the original proposals below.

## Outcome

### Delivery record

- Implemented cost observations and a bounded four-condition preflight; [results](../../benchmarks/2026-10-08-value-first.md) show missed speed/token targets and stronger project-only output on settings. Eight implementation and two blind-review sessions completed. The larger conditional screen is deferred by the planned evidence gate, not reported as completed.
- Simplified the workflow entrypoint and risk selection; retained TDD, project requirements and existing safety checks. Strict no longer unconditionally requires logs or an extra reviewer. Fixed orchestration's preference read to respect shared configuration.
- Added optional private-note setup with preservation checks, worktree scope/lifecycle guidance and linked-worktree regression coverage.
- Added read-only paginated PR-review collection and a procedure for evidence, in-scope fixes, deduplicated follow-ups and authorized resolution. Live read smoke-tested on PR #135; no review comments/issues were published by the helper.
- Added package-area discovery and a multi-team example using root preferences, scoped instructions, existing ownership and contract checks. Tested shared-contract routing and a clean merge with a real consumer failure/recovery.
- Evaluated Aislop locally; offer advisory project-selected scans, not score gates or per-edit hooks. Documented selected Ponytail/Superpowers adoption and alternatives. No default bundle, new service or additional mandatory Git hook was justified. [Tool decisions](../../audits/2026-10-08-external-checks.md).
- Updated human guides, product positioning and GitHub description/topics; no release tags were changed. Local lint, validation and the full suite run were followed by passing affected-suite reruns after corrections. Publication and CI results are recorded on the delivery PR.

The sections below preserve the approved design. Proposed files/scenarios for the larger conditional experiment were not all created: the implemented gate runner is intentionally smaller.

Help individuals and teams agree on how their AI tools work, find the relevant project context, and verify changes with less coordination effort. Each additional instruction, hook, skill or command must solve an observed problem. More workflow activity is not itself a better outcome.

This plan covers cost reduction, optional external tools, private working notes, PR review resolution, multiple teams in one repository, worktrees, and clearer product positioning. It preserves useful testing, TDD, maintainable design, Conventional Commits, branches, PR templates, documentation maintenance and the prohibition on AI attribution. It does not promise that installing instructions guarantees those practices or better code.

The user confirmed that the proposed sources are `scanaislop/aislop` and `DietrichGebert/ponytail`, and that `.private` means local, Git-ignored notes and AI context. Solo use remains a complete use case. Team configuration must not make every task strict.

## What the evidence currently supports

The [quality comparison](../../benchmarks/2026-10-08-quality-efficiency.md) contains 93 sessions, including independent blind code reviews. The tested candidate used approximately 2.31 times the plain condition's input tokens with Luna and 2.18 times with Sol. Coding time was 1.86 and 1.40 times plain, respectively. Cached input is a subset of input; subscription token counts are not dollar prices.

Candidate acceptance was 16/16, against 15/16 for current and plain. The sample is too small to establish a general improvement. Independent review did not establish better overall code quality; identical-code scores varied by as much as 0.8/10. The useful-test gain was concentrated in the weaker model. Setup time also increased, missing the previous provisional targets.

The separate [teamwork pilot](../../benchmarks/2026-10-08-teamwork.md) passed 7/7 checks in both conditions and took 5.5% longer with the candidate. It exposed an unrelated-handoff completion reminder, subsequently fixed. Its four sessions did not demonstrate a productivity or code-quality gain. These experiments predate the current main revision; their figures must not be relabeled as measurements of this plan or today's complete product.

Extra cost could be worthwhile if it prevents consequential defects, reduces review/rework, makes later changes easier, or amortizes setup across contributors and tasks. Those are hypotheses to test. Workflow compliance, more files, more tests, or a higher scanner score do not justify twice the tokens on their own.

## Existing foundations and actual gaps

| Area | Already present | Gap to address |
| --- | --- | --- |
| Simplicity | KISS/YAGNI in design guidance; affected checks and concise replies | Broad triggers, repeated guidance and process requirements still need cost analysis |
| Workflow | Task modes, project precedence, TDD, branch/commit/PR guidance | Make the common path smaller and distinguish judgment from executable enforcement |
| Verification | `tack verify`, path-based `checks-map.json`, explicit trust and incomplete results | Assess repeated invocation cost and concrete checks that existing tools miss |
| Teams | Shared `tack.json`, solo/team preference, handoffs, `tack team`, bootstrap | Several teams/areas need scoped guidance, ownership and shared-contract examples |
| Worktrees | Isolation instructions in `skills/orchestrate/SKILL.md` | Ordinary developer use, configuration scope and lifecycle need coverage |
| GitHub | Issue workflow, PR templates and optional PR metadata checks | Complete lifecycle for review findings and follow-up issues |
| Hooks | Secret/commit/history checks and chaining through `git-hooks/` | Decide which additional checks earn their delay; hook filenames are not new features |
| External skills | Optional project-scoped selection and provenance guidance | Evaluate the named sources without installing overlapping workflows |
| Private notes | Configurable document locations and local state | An explicit optional convention for personal scratch context |

## Approach and boundaries

Three approaches were considered:

1. **Add all requested tools to the default install.** Fast to assemble, but increases overlap, maintenance and context cost before showing value. Reject.
2. **Keep a smaller core and add capabilities for demonstrated project needs.** Reuse existing configuration, checks, native Git and GitHub. Recommended.
3. **Reduce tack to a starter template and configuration distribution.** A valid fallback if the smaller core cannot beat ordinary project instructions and CI on any useful outcome.

The workflow should remain instructions for decisions: understand the request, inspect relevant context, make a coherent change, verify and report. Deterministic checks belong in scripts/hooks/CI. Merge protection belongs in repository rules. Instructions cannot ensure TDD, prevent every conflict, or establish semantic compatibility.

Keep shared preferences in the existing root `tack.json`. Reuse project scripts, scoped instructions, `CODEOWNERS`, issue/PR discussions and contracts before adding new registries. No custom package manager, hosted coordination service, scheduler or mandatory agent group is planned.

## Delivery order

Each row is a separately reviewable slice. Product work begins only when implementation of this plan is requested. During implementation, use coherent Conventional Commits, no AI attribution, and existing authorization for publication/merging; passing CI applies to the actual PR head.

| Step | Priority | Deliverable | Dependency |
| --- | --- | --- | --- |
| 1 | P0 | Cost attribution and a frozen value-comparison protocol | None |
| 2 | P0 | Smaller workflow and conditional process | Step 1 |
| 3 | P1 | Optional private notes and verified worktree behavior | Step 2 |
| 4 | P1 | PR review-to-resolution procedure | Step 2 |
| 5 | P1 | Several teams in one repository using existing primitives | Steps 2–3 |
| 6 | P1 | Selective external-tool and hook experiments | Steps 1–2; use steps 4–5 where relevant |
| 7 | P0 gate | Comparative results and keep/change/remove decisions | Evaluate each completed candidate incrementally |
| 8 | P2 | Updated positioning, description and topics | State measured results from step 7 |

Run the early comparison after step 2, before building the full optional backlog. A failure to show value redirects the remaining work toward simplification. Do not delay feedback until every feature exists.

## 1. Attribute cost and define what success means

**Existing files:** `evals/quality.py`, `evals/quality_worker.py`, `evals/quality_review.py`, `evals/quality_grade.py`, `evals/adoption.py`, `evals/teamwork.py`, `evals/teamwork_fixture.py`, `evals/teamwork_worker.py`, `tests/quality.test.py`, `tests/evals.test.py` and the frozen benchmark reports.

**New files:** `evals/value.py`, `evals/value_fixture.py`, `evals/batches/value-first.json`, `evals/value-protocol.md`, `tests/value.test.py`. Keep this a bounded experiment using existing runners/helpers, not a generic evaluation platform. Preserve the old runner's fixed 93-session protocol and evidence.

1. Examine existing traces offline. Count injected context, skill reads, tool output, model turns, check invocations, doc/commit work and completion-repair loops. Separate measured durations from intervals that cannot be attributed. Do not infer elapsed cost from command counts alone.
2. Record startup and task-context size, original/latest user request, chosen mode and why it changed. Compare the loaded content, not the installed collection's total size.
3. Define four conditions: plain agent; ordinary project `AGENTS.md` plus native CI/templates/scripts; current tack pinned to this plan's starting revision; lean tack pinned to the candidate revision. This tests tack's incremental value over a credible cheap alternative.
4. Use the same product request, repository snapshot, tools and existing public tests. Do not put TDD, tests, SOLID, planning, commits or modularity instructions into the plain user prompt. Record provider-supplied instructions that remain common to all conditions. Preserve comparable project facts, APIs and command documentation in all conditions.
5. Predeclare acceptance criteria and evaluator-only checks before running the variants. Randomize/counterbalance order, preserve failures and timeouts, record model/effort/version and separate warm/cold setup. Freeze external-tool versions and record cache behavior.
6. Measure task time/tokens, setup time, useful defects prevented, independent quality findings, review/rework time and a later modification. Report success-adjusted and all-attempt totals. Measure setup over actual repeated tasks before presenting amortized savings. Human review-time claims require timed human participation; label agent review/repair time separately and never substitute a reviewer's estimate of minutes saved.

**Completion:** a dry run enumerates all jobs, validates the caps and input hashes, and performs no model calls. Fixture tests detect deliberately broken implementations. Plain requests contain only product requirements. Old reports and evidence hashes remain unchanged.

### Proposed experiment and decision rules

Start with an offline trace review. Then use one economical available model, pinned explicitly in the experiment manifest; no product workflow rule names a model. The initial live preflight is eight implementation sessions: two scenarios across four conditions. Stop for fixture/runner failures and report the preflight separately.

If the lean candidate is viable, the bounded screen is:

| Part | Proposed sessions | Purpose |
| --- | ---: | --- |
| Four scenarios × four conditions × two repetitions | 32 | Small bug, feature, cross-area contract change, PR review resolution |
| Follow-up change to the feature outputs | 8 | Maintainability: actual effort to change the result later |
| Project-only/current/lean setup × two repetitions | 6 | Installation, configuration and contributor onboarding |
| Independent blind review | 12 | Eight four-way coding comparisons, two preselected order reversals, two follow-up comparisons |
| Initial preflight | 8 | Validate execution and data collection |
| **Maximum for this first screen** | **66** | Separate implementation/setup and evaluation costs |

An episode must not silently expand into unlimited repair/model sessions. Define time/token/session ceilings and count retries before execution. Mock GitHub for the review fixture; live public comments are unnecessary for this benchmark. The second model and a larger held-out sample are follow-ups only if the screen supports a useful hypothesis.

Reviewers see anonymized code and requirements, without tack/process labels or transcripts. Strip irrelevant branding while retaining behaviorally relevant files. Ask for concrete defects, unnecessary complexity, clarity, test usefulness and changeability; a score is secondary. The orchestrator examines the findings and later-change diffs before unblinding. Disagreement and order sensitivity are reported. These small samples support screening decisions, not broad statistical claims.

Provisional design targets, not promised results:

- On routine tasks, aim for at least 25% less wall time and input tokens than current tack, and no more than 20% overhead relative to project-only instructions. Report each model/task class rather than hiding regressions in one average.
- Do not accept a new critical correctness/security regression in the candidate; investigate all lesser regressions. Passing a small sample is not proof of population-level noninferiority.
- For optional coordination/checks, require reproducible useful defects caught or a meaningful reduction in review/rework or later-change effort, with its added cost visible. A 20% lifecycle-time reduction is a useful target; missed targets remain missed.
- If quality and lifecycle outcomes are equal or worse at greater cost, remove the default requirement or recommend the cheaper alternative. Do not justify it with theoretical scalability or a scanner score.
- Ablate one suspected source at a time: workflow text, context selection, completion checks, or an external tool. Run only the ablations needed to choose an action; do not launch every possible combination.

## 2. Reduce workflow cost while keeping engineering discipline

**Existing files:** `global/AGENTS.md`, `lib/modes.sh`, `modes/lite.md`, `modes/standard.md`, `modes/strict.md`, `skills/dev-workflow/SKILL.md`, `skills/dev-workflow/references/design.md`, `skills/dev-workflow/references/tdd.md`, `skills/dev-workflow/references/documentation.md`, `skills/project-docs/SKILL.md`, `skills/orchestrate/SKILL.md`, `lib/project-context.sh`, `features.txt`, `docs/engineering-practices.md`, `docs/usage.md`. Auto selection is built in; there is no `modes/auto.md`.

1. Make one short workflow the canonical entry point. Load detailed procedures only for the task's risk or an observed gap. Remove conflicting duplicate requirements across modes and skill prose.
2. Classify by consequences and uncertainty. Several files, a new feature, or team membership alone must not force strict. Preserve explicit project/user requirements and explain any material risk-based escalation.
3. Keep TDD for behavior work at standard/strict, useful regression tests for bugs, and existing required checks. Do not manufacture new test files when existing tests already verify a trivial change. Do not claim test counts or a filename change prove quality or TDD.
4. Apply SOLID through clear responsibilities and boundaries, together with KISS/YAGNI. Prefer existing code and standard tools. Do not create interfaces, configuration, layers or dependencies for a hypothetical future need; do not delete validation/error handling to shorten a diff.
5. Retain branches, coherent Conventional Commits, no AI attribution and meaningful PR bodies. Scope plans, ADRs, AI logs, handoffs and review agents to actual coordination, risk or project policy. Review the current unconditional strict log/reviewer requirements as candidates for becoming conditional.
6. Use brainstorming when unresolved requirements or consequential alternatives need a decision. Reuse settled answers and authorization. A clear small request should not trigger a separate spec, repeated approvals or an obligatory planning skill.
7. Profile repeated `fast-check`/manual verify/Stop runs. First remove overlapping configuration and unnecessary triggers. Reusing successful results requires a separately tested validity contract; a HEAD-only or diff-only cache is insufficient for dependencies, commands and external state. Preserve required checks until an equivalent safe scheduling design exists.

**Acceptance:** a bounded bug fix follows a short path with a useful check and no gratuitous plan/log/handoff/review-agent artifacts. A migration still gets a plan, relevant tests and review. Shared defaults and local overrides retain their documented precedence. The early comparison reports whether the changes actually saved work.

**Verification:** `tests/validate.sh`, relevant mode/context/config tests, and the step 1 paired task probe. Instruction changes need observed task behavior, not tests that merely match prose.

## 3. Add optional private notes and make worktrees predictable

**Existing files:** `skills/new-project/references/onboarding.md`, `lib/project_setup.py`, `lib/project_config.py`, `lib/project-context.sh`, `lib/keys.sh`, `bin/tack`, `skills/orchestrate/SKILL.md`, `skills/dev-workflow/references/teamwork.md`, `docs/configuration.md`, `docs/teamwork.md`, `docs/leaving.md`.

**New references:** `skills/project-docs/references/private-notes.md` and `skills/dev-workflow/references/worktrees.md`. Extend existing setup/config/team tests; add a focused worktree suite only if behavior changes need it.

### Private context

- Offer `.private/tack/` during the existing setup conversation when local notes are useful. Create it only when selected; reuse existing local conventions. The initial implementation is a storage convention and optional setup action, not a new database or memory service.
- Keep rough plans, personal notes and temporary investigation context there. Keep shared contracts, durable decisions, required setup instructions and relevant team handoffs versioned. A teammate must not need somebody else's private folder to finish a task.
- Add `/.private/` to the project's `.gitignore` when adopting the shared convention; for a personal-only choice, use Git's local exclude location resolved through Git. Preserve existing content, ignore rules and ownership. Detect already tracked private files and report them; an ignore entry does not untrack history.
- Do not load every private note at startup. Read a task-relevant note only when selected or explicitly indexed locally. Exclude it from shared reports, generated public context and benchmark/review bundles unless deliberately selected and reviewed.
- The name and Git ignore rule are not encryption or a guarantee that an AI tool cannot read files. Do not use the folder as a secret store. Cleanup previews exact owned paths and preserves user notes; removal is never triggered simply because a task or worktree ends.

### Worktrees

- Reuse native `git worktree` for concurrent writers, isolation from unrelated dirty work, or testing another branch. A serial small task does not need a new worktree.
- Inspect existing worktrees before creating one, name the base/branch, pass the correct working directory to the agent, and use a separate branch per writer. Prefer a user-selected sibling location; an in-repository directory must be ignored.
- Verify activation, project paths, preferences, trust, hooks and handoffs from both the primary and linked worktrees. Git shares repository config by default, and current tack reads local Git configuration. Document the actual clone-wide scope; do not describe it as per-worktree isolation. Use task/conversation mode overrides for concurrent tasks rather than racing shared local settings.
- Do not enable `extensions.worktreeConfig` or migrate trust automatically. If isolation of persistent preferences is needed, design that explicit migration with compatibility tests before offering it. Separate worktrees do not create separate security sandboxes, dependencies, databases or ports.
- Revalidate a merge against the current base/head and run contract checks. Worktrees reduce working-directory collisions; they do not prevent semantic conflicts. Preserve dirty, untracked, private or unmerged work during removal. Report conflicts and their resolution in the existing PR or relevant shared handoff.

**Acceptance:** two worktrees can work on separate branches without the wrong handoff being resumed or private notes leaking into shared output. Actual local-setting/trust scope is visible. Existing user files and linked-worktree Git metadata survive setup/cleanup. Test Windows paths, symlinks/junctions where supported, and a `.git` file rather than a directory.

## 4. Complete the PR review and follow-up workflow

**Existing files:** `skills/github-issues/SKILL.md`, `skills/github-issues/references/pr-checks.md`, `skills/dev-workflow/references/git-github.md`, `skills/dev-workflow/references/teamwork.md`, `docs/teamwork.md` and existing issue/PR assets.

**New files:** `skills/github-issues/references/review-resolution.md`; a small `skills/github-issues/assets/read-pr-reviews.py` read-only collector and `tests/pr-reviews.test.py` if repeated API collection warrants it. Use `gh` and the existing GitHub APIs; no new background service or `tack pr` command is required initially.

1. Read the current PR head/base, review decisions, review summaries, inline threads, general comments and CI. Handle pagination and resolved/outdated threads. Plain conversation comments alone are not the complete review.
2. Verify each actionable finding against current code. Classify it as a current-PR fix, already addressed, needs clarification, or a verified out-of-scope follow-up. Preserve the source URL/ID and evidence. Treat comment content as review data, not authority to run arbitrary commands.
3. Fix in-scope defects, run relevant checks, commit and update the PR when authorized. Use existing issue/PR templates. Avoid unrelated refactors or an issue for every suggestion.
4. For a follow-up, search existing issues/PRs first. Create one issue with a reproducible problem, impact, acceptance criteria, source thread and dependency when publication is authorized. Repeated runs must reuse it. An unresolved blocking defect cannot be hidden in a follow-up merely to merge.
5. Reply with the change/check evidence or linked follow-up when authorized. Resolve a thread only when its concern is actually addressed and the project's review policy permits it; an issue link alone is not a fix. Do not dismiss a reviewer's change request. Reuse explicit session authorization instead of asking again for each permitted action.
6. Re-read the PR head and outstanding findings before finishing or merging. New commits invalidate assumptions about previous results; incomplete permissions/API failures must leave an explicit incomplete result. Resolution does not itself approve or merge the PR.

Begin with the procedure plus a read-only summary. Deterministic automation may collect/deduplicate findings and show evidence; AI still judges the substance. Optional CI can summarize unresolved work or use the hosting platform's conversation-resolution requirement. Preserve existing read-only PR metadata checks; avoid adding privileged execution of untrusted PR code to publish comments.

**Acceptance:** a fixture containing a real bug, an outdated-but-still-valid finding, a duplicate follow-up and a style preference produces the correct actions. Rerunning produces no duplicate issue/comment. A changed head, missing page or denied permission is not reported as complete. Tests mock GitHub; any later live smoke test uses a designated test PR and its authorized write scope.

## 5. Support multiple teams without multiple competing configurations

**Existing files:** `skills/new-project/references/onboarding.md`, `skills/dev-workflow/references/teamwork.md`, `skills/project-docs/references/integration.md`, `lib/project_setup.py`, `lib/project-context.sh`, `lib/team.py`, `docs/teamwork.md`, `docs/sharing.md`, `docs/verification.md`.

**New example:** `skills/new-project/assets/examples/multi-team.md`, showing an application repository with `apps/api`, `apps/web`, `packages/contracts` and optional platform ownership. These are examples, not mandatory directories in tack or an adopting project.

1. Inspect existing packages, workspace scripts, scoped instructions, contracts and ownership before proposing area setup. Ask about unknown responsibilities in the existing onboarding conversation; contributor count alone must not silently change solo/team settings.
2. Keep one root `tack.json` for shared defaults and one root instruction index. Area `AGENTS.md` files supply relevant conventions and commands. Index them explicitly for tools whose nested-file discovery differs. Do not introduce nested `tack.json` precedence in this first version.
3. Reuse `CODEOWNERS` for GitHub review ownership and the existing issue tracker for assignments/dependencies. Respect actual CODEOWNERS semantics; ownership is not task locking or an instruction override, and listing two owners does not guarantee two approvals. Use repository rules for required approvals when the project requests them.
4. Map producer and consumer paths into `checks-map.json` so shared-contract changes select both sides' checks. Reuse workspace dependency tools where available. Root dependency/config changes select the broader required checks. Avoid adding a second dependency graph solely for tack.
5. Keep canonical contracts versioned. A useful integration handoff links the producer/consumer issues or PRs, exact refs, expected contract, dependency state and checks. Distinguish planned work, branch implementation and behavior actually available in the current base.
6. Use task branches/worktrees for parallel implementation. Run `tack team` when coordination requires it, interpret conflicts/unknown results, and verify actual integration behavior. Do not promise conflict-free merges or require every team to share a fixed task mode.

**Acceptance:** two teams independently implement backend/frontend work using the same defaults and their relevant area instructions. A third contributor can identify the contract and availability from versioned context. A shared-contract change selects both consumers' checks, while an isolated area change avoids unrelated workflow/doc churn. No new ownership registry, service or per-team mode is needed.

**Verification:** extend `tests/project-setup.test.py`, `tests/team.test.py` and `tests/verification.test.py` for actual implementation changes. Extend the teamwork fixture to include a real semantic incompatibility with a clean Git merge, an ordinary textual conflict, and successful conflict recovery. Validate relevant tools' scoped-context behavior without assuming identical native discovery.

## 6. Evaluate external tools and hooks selectively

These primary repositories were inspected on 2026-10-08. The shortlist is research, not an installation list. All were unarchived at inspection. Maintenance activity is not proof of quality or compatibility. Preserve the reviewed revision, license and required notices for any copied material; retain local adaptations and review updates.

| Repository | Potential contribution | Proposed decision | License observed |
| --- | --- | --- | --- |
| [scanaislop/aislop](https://github.com/scanaislop/aislop) | Deterministic code diagnostics and changed-file scan/CI modes | Trial as an optional existing command through `checks-map.json`; compare unique useful findings with current linters | MIT |
| [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | Guidance against unnecessary implementation | Compare a selected skill with the lean workflow; adopt only useful differences, without stacking session modes or reply rules | MIT |
| [obra/superpowers](https://github.com/obra/superpowers) | Brainstorming, design and development procedures | Reuse selective ideas and offer a scoped external skill where useful; no wholesale mandatory workflow | MIT |
| [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | Engineering procedures | Keep current optional selection; check overlap and supporting-file dependencies | MIT |
| [mattpocock/skills](https://github.com/mattpocock/skills) | Focused engineering skills | Keep current project-scoped selection and preserve project conventions | MIT |
| [vercel-labs/skills](https://github.com/vercel-labs/skills) | External skill installation | Reuse the existing installer path; no tack package manager | MIT |
| [pre-commit/pre-commit](https://github.com/pre-commit/pre-commit) | Existing hook management | Integrate with a project's chosen runner rather than build another | MIT |
| [reviewdog/reviewdog](https://github.com/reviewdog/reviewdog) | Present static-analysis findings in reviews | Optional reporting when it improves review; no autonomous issue creation by default | MIT |
| [max-sixty/worktrunk](https://github.com/max-sixty/worktrunk) | Worktree management | Document as an optional alternative; native Git first | MIT or Apache-2.0 |
| [github/spec-kit](https://github.com/github/spec-kit) | An alternative spec-driven workflow | Include in replacement/overlap analysis; do not layer a second complete lifecycle onto tack | MIT |

The three named sources resolved to these main-branch revisions during research: aislop `ec7589f9a97ef6905c0930fcad6e1eeeecd7efb5`, Ponytail `9cc65d03aa2da1db7121b912d03596409ee340b8`, Superpowers `8ca22dba9a94f28898bbce59f2537ff4d87c747d`. Verify the selected content at those commits before adoption; the inspected web pages can move.

Ponytail's [skill](https://github.com/DietrichGebert/ponytail/blob/9cc65d03aa2da1db7121b912d03596409ee340b8/skills/ponytail/SKILL.md) overlaps tack's simplicity guidance and defines its own persistent levels and response rules. Its published savings are upstream claims, not evidence of gains in tack. Compare measured outcomes; shortest diff alone is not quality.

Superpowers' [brainstorming procedure](https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/brainstorming/SKILL.md) distinguishes task sizes but still has explicit approval stages. Adopt useful requirement/alternative exploration deliberately; do not silently replace tack's existing authorization behavior or introduce a second mandatory document hierarchy.

**Existing files:** `docs/external-skills.md`, `skills/lessons/references/external-skills.md`, `skills/new-project/references/onboarding.md`, `docs/verification.md`, `git-hooks/_chain`, `git-hooks/pre-commit`, `git-hooks/pre-push`, `hooks/claude/fast-check.sh`, `hooks/claude/stop-check.sh`, `lib/check_execution.py`, `lib/verification.py`. New examples/tests only for integrations selected after the trial.

### Aislop trial

Use a pinned local scanner dependency selected for the project's languages. Start with machine-readable scan output on a controlled fixture/current diff. Measure findings that Ruff, ShellCheck, type checks or existing project checks did not already catch; manually classify false positives. Preserve unsupported-language and skipped-engine limitations.

If useful, expose the existing command through `checks-map.json` and optionally CI. Missing installation reports unavailable, not success or an automatic download. Start advisory; make individual reliable rules blocking only after calibration. Do not install per-edit hooks, run autonomous fixes/repair agents, upload code, or chase a global score as part of the initial integration. A repeated clean scan is not a reason to rerun after every tool action.

### Git hooks

Prefer existing pre-commit/lint/format/type/test commands, preserving local-hook chaining and failures. First measure latency and reject duplicated checks. Candidate additions must name a real failure they catch, such as staged conflict markers with correct fixture exclusions or a missing required generated-contract update. Check staged content for commit gates, including partially staged files; a clean working copy can differ from the index.

Keep expensive integration checks in pre-push/CI when the project chooses them. No mandatory model calls, network fetches, full test suite on every edit or automatic issue creation in a Git hook. Hooks are local and bypassable; repository CI/rules enforce shared merge requirements. Cover empty changes, renames, deleted files, absent tools, timeouts and existing hook-runner composition.

**Completion:** every proposed integration has a keep/reject decision with useful findings, false-positive rate and measured time/context cost. Installer/hook changes have meaningful tests in `tests/`. If an existing tool solves the need, tack documents or calls it instead of reimplementing it.

## 7. Decide what remains in tack

**Existing files:** `docs/results.md`, `docs/why.md`, `docs/components.md`, `docs/engineering-practices.md`, and the owning usage guides. **New report:** `docs/benchmarks/2026-10-08-value-first.md` if run that day; otherwise use the actual experiment date.

For each capability, record its user problem, simpler alternative, measured benefit/cost, maintenance burden and decision: core, optional, simplify, deprecate, or remove. Include unflattering and null results. Do not remove safeguards or advanced features merely because no representative usage data exists.

The first likely core is portable project defaults, relevant context and concrete verification. PR coordination, external skills and extra checks are candidates for optional use. Generic instruction packs that cannot demonstrate an advantage should shrink. If project-only instructions and CI do equally well for a user's work, explicitly recommend that simpler setup.

Preserve existing configuration and explicit preferences when defaults change. Document changes and migration; do not delete installed skills, custom workflows, hooks or user documents silently. Deprecate commands/settings with compatibility coverage when removal is warranted. Revert or disable only tack-owned additions if an integration fails.

**Completion:** published conclusions identify the tested versions, limitations, costs, useful outcomes and a concrete product decision. Claims of improved quality or speed link to supporting results. Further work is justified by a remaining problem, not by finishing every optional idea in this plan.

## 8. Update product presentation and repository metadata

**Existing files:** `README.md`, `docs/README.md`, `docs/why.md`, `docs/teamwork.md`, `docs/external-skills.md`, `docs/architecture.md`, and release documentation if a release is actually prepared.

- Keep the README short: intended user, shared/solo configuration, a small real workflow, and evidence/limits. Link to the owning guide for setup, private notes, teams and advanced integrations.
- Explain that tack can be used individually, shared through a project's configuration, or forked for a deeper custom distribution. Configuration portability is useful, but not exclusive or proof of faster coding.
- Suggested GitHub description: **"Shared project conventions, context and checks for AI-assisted development — for solo developers and teams, across coding tools."** It describes the current direction without a performance promise.
- Proposed topics: `ai-agents`, `agent-skills`, `developer-tools`, `developer-experience`, `team-collaboration`, `code-quality`, `git-workflow`, plus supported-tool topics that help discovery. Review `dotfiles` and `harness` against positioning rather than adding every keyword.
- Interpret the user's metadata "tags" as GitHub topics. Version tags are different: do not move or rewrite published tags. A new SemVer tag belongs to a tested release, with the existing release procedure.
- Update architecture only for implemented component/flow changes. Plans and experiments must remain visibly distinct from shipped usage instructions.

**Completion:** documentation links pass, examples match actual commands, and the About text/topics describe shipped behavior. Metadata updates and publication occur during authorized implementation, not this planning task.

## Validation and handoff

For this plan: check referenced existing paths and run `python3 tests/docs-links.py`; review coverage of every user idea. No model benchmark, dependency installation, product change, GitHub write or release is part of preparing it.

For implementation: run the affected suites after each meaningful change; installer and hook behavior always receives regression coverage. Before merging a product change run `tests/lint.sh`, `tests/validate.sh` and `tests/run-all.sh -j N` with the CI-pinned tool versions. Tests use temporary HOME/XDG configuration and `GIT_CONFIG_NOSYSTEM=1`; shell changes remain Bash 3.2 compatible. Inspect CI for the actual candidate and preserve the final task outcome in the user summary.

The recommended first implementation slice is steps 1–2 plus its early comparison. Continue private/worktree, review and multi-team improvements as scoped additions supported by that result, then trial external checks individually. This order gives tack a chance to become smaller and more useful before it becomes larger.

## Supporting platform references

- [Git worktree configuration and lifecycle](https://git-scm.com/docs/git-worktree): worktrees share repository configuration by default; per-worktree configuration is an explicit extension.
- [GitHub CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners): ownership matching and review behavior belong to the platform.
- [GitHub review conversations](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/commenting-on-a-pull-request): distinguishes general comments, review discussions and follow-up issues.
