# Engineering practices with tack

tack helps an individual or team make its engineering practices explicit, reusable and checkable across AI coding tools. The intended result is less repeated setup, clearer ownership of context and fewer preventable defects. Those are goals to measure; sharing instructions or passing a selected check does not establish overall code quality.

## From a problem to an observable practice

| Problem | Practice | How tack supports it |
| --- | --- | --- |
| Every session rediscovers conventions and file locations | One versioned entrypoint, with links to detailed context | Project AGENTS.md, guided setup and indexed startup context |
| A small request grows into unrelated refactoring | One coherent change with an explicit outcome | Task-scaled workflow guidance and a focused PR description |
| A fix passes shallow tests but misses the actual bug | Reproduce the failure, then verify the changed behavior and relevant edge cases | Existing project tests, optional check maps and failure output from `tack verify` |
| A change breaks callers or stored settings | Treat public interfaces and persisted formats as contracts | Design guidance to check compatibility, malformed inputs and recovery when relevant; the project supplies executable tests |
| A tool reports success after doing nothing or testing stale inputs | Distinguish passed, missing, skipped, failed and changed-input results | Explicit verifier statuses; commands that modify repository inputs cannot produce an unchanged-input pass |
| Tests and automation hang or pollute developer machines | Bounded commands and isolated fixtures | Verification timeouts; tack's own tests use temporary homes and repositories |
| Rules diverge between editors | Central policy with thin tool adapters | Shared instructions and verification CLI; executable integration varies by tool |
| Documentation drifts from the code | Keep affected guidance alongside the change | `docs-map.txt`, PR evidence and architecture updates when structure changes |
| More process costs time without improving delivery | Retain steps that solve a demonstrated problem | Task modes, on-demand capabilities and published positive, null and adverse benchmark results |

Guidance still depends on the assistant following it. Runtime checks cover only their declared behavior, and a human review remains useful for design and semantic gaps. See [tool coverage](editors.md) and [verification limits](verification.md).

## Scale by task and risk

### Practices that remain part of tack

TDD and maintainable design remain core guidance. At standard and strict, use red, green, refactor for behavior: reproduce a bug or specify a new outcome with a failing test, implement it, then improve the structure with tests passing. Lite still requires useful tests for changed logic; a documentation-only edit does not need a new test. SOLID guides responsibilities, interfaces and dependencies together with KISS and YAGNI. It does not require classes, extra layers or an interface for every function.

Choose tests by the failure they can catch: unit tests for rules, integration tests for boundaries, contract tests for interfaces, a few end-to-end tests for critical flows, and security, accessibility, performance or recovery tests when relevant. More test types or higher coverage are not substitutes for assertions about real behavior.

The delivery workflow also remains: work on branches, use Conventional Commits without AI attribution, keep changes reviewable, reuse issue and PR templates, include actual validation evidence, follow CI before merging, and update affected documentation with the code. Issues are useful for agreed work and tracking findings; every tiny task does not need a new issue. Existing authorization still applies to publishing and merging.

These are recommendations for the assistant plus selected executable checks, not proof that every generated change used TDD or satisfies SOLID. The [workflow](../skills/dev-workflow/SKILL.md), [testing guidance](../skills/testing/SKILL.md) and [design reference](../skills/dev-workflow/references/design.md) retain the detailed procedures.

### What changed in the transition

| Treatment | What changed |
| --- | --- |
| Removed mandatory behavior | Delegation after three documentation files, numeric visual-score redo gates, formal requirement IDs for ordinary tasks and unconditional repeated full-suite runs in the main workflow. |
| Kept | TDD, SOLID with pragmatic design, relevant test types, task modes, branches, Conventional Commits, no AI attribution, issue/PR workflows and templates, documentation upkeep, installer preservation and protections. |
| Improved | Task-risk selection, bounded improvement loops, common check execution, project context discovery, tool adapters, documentation ownership and explicit verification limits. |
| Added | Optional shared `tack.json`, stable config reads, configurable architecture/plan/handoff paths, `tack verify` and check maps, guided project onboarding and optional external-skill selection. |

No whole specialist catalog was removed. Skills and roles remain available when their procedure or responsibility is useful. Smaller installation profiles and avoiding duplicate checks across separate invocations still need evaluation.

Use `auto` as the usual preference, then select the level for the current task. A bounded low-risk fix needs a focused change and relevant verification. A change to authentication, migrations or a public API needs deeper compatibility and failure-case analysis. A new feature is not automatically strict, and a one-line change can still be high risk.

Use an ADR for a consequential design choice with alternatives; a handoff for work another session must resume; a skill for a useful reusable procedure; a specialist role for a distinct review responsibility. Strict no longer requires an AI log or independent reviewer solely because of its level: project policy or a concrete need decides. Explicit project requirements remain valid. Empty artifacts and agent counts are not engineering outcomes. File count and team membership alone do not determine task risk.

## Applied to tack itself

- The verifier separates CLI dispatch, selection/execution and tool adapters. Check selection is project data rather than one hard-coded branch per stack.
- Configuration is versioned and validated before execution. Invalid data, missing checks and untrusted execution are explicit results.
- Regression tests exercise real commands and defects, including pipeline failures, timeouts, staged-only changes and a check that mutates the Git index. The latter cases were reproduced as failures before the fixes.
- Installer ownership/restoration tests protect independent user settings. Trust stays local; project adoption cannot grant it.
- CI checks shell/Python lint, Bash compatibility and native Windows behavior. A passing Linux test does not substitute for a claimed Windows capability.
- Public benchmarks retain failed and adverse outcomes. The [adoption comparison](benchmarks/2026-10-08-adoption.md) found useful configuration transfer, tied correctness and higher time cost; it does not establish reduced defect rates or improved productivity.

The [development guide](development.md) gives the commands contributors use. The [team example](sharing.md#example-a-team-building-with-ai) shows adoption and daily use. Shared project preferences now live in optional `tack.json`; local overrides and personal defaults remain separate. See [configuration](configuration.md).

## Sources and adaptation

Google's review guidance emphasizes useful tests, understandable design, appropriate complexity and documentation. Its small-change guidance favors coherent changes that reviewers can assess. tack uses those principles as review questions, without imposing a line-count quota or importing another organization's workflow. [Code review guidance](https://google.github.io/eng-practices/review/reviewer/looking-for.html), [small changes](https://google.github.io/eng-practices/review/developer/small-cls.html).

DORA's testing guidance emphasizes fast, reliable feedback and maintaining test suites as products evolve. For tack, that means testing actual failure cases and measuring overhead, rather than increasing test counts or replaying an entire suite after every small edit. These sources do not establish tack's effectiveness. [Test automation](https://dora.dev/capabilities/test-automation/).
