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

Use `auto` as the usual preference, then select the level for the current task. A bounded low-risk fix needs a focused change and relevant verification. A change to authentication, migrations or a public API needs deeper compatibility and failure-case analysis. A new feature is not automatically strict, and a one-line change can still be high risk.

Use an ADR for a consequential design choice with alternatives; a handoff for work another session must resume; a skill for a useful reusable procedure; a specialist role for a distinct review responsibility. Existing strict preferences remain valid, but empty artifacts and agent counts are not engineering outcomes.

## Applied to tack itself

- The verifier separates CLI dispatch, selection/execution and tool adapters. Check selection is project data rather than one hard-coded branch per stack.
- Configuration is versioned and validated before execution. Invalid data, missing checks and untrusted execution are explicit results.
- Regression tests exercise real commands and defects, including pipeline failures, timeouts, staged-only changes and a check that mutates the Git index. The latter cases were reproduced as failures before the fixes.
- Installer ownership/restoration tests protect independent user settings. Trust stays local; project adoption cannot grant it.
- CI checks shell/Python lint, Bash compatibility and native Windows behavior. A passing Linux test does not substitute for a claimed Windows capability.
- Public benchmarks retain failed and adverse outcomes. The new verifier still needs a real-model comparison before claiming reduced defect rates or cost.

The [development guide](development.md) gives the commands contributors use. The [team example](sharing.md#example-a-team-building-with-ai) shows adoption and daily use. Shared project preferences now live in optional `tack.json`; local overrides and personal defaults remain separate. See [configuration](configuration.md).

## Sources and adaptation

Google's review guidance emphasizes useful tests, understandable design, appropriate complexity and documentation. Its small-change guidance favors coherent changes that reviewers can assess. tack uses those principles as review questions, without imposing a line-count quota or importing another organization's workflow. [Code review guidance](https://google.github.io/eng-practices/review/reviewer/looking-for.html), [small changes](https://google.github.io/eng-practices/review/developer/small-cls.html).

DORA's testing guidance emphasizes fast, reliable feedback and maintaining test suites as products evolve. For tack, that means testing actual failure cases and measuring overhead, rather than increasing test counts or replaying an entire suite after every small edit. These sources do not establish tack's effectiveness. [Test automation](https://dora.dev/capabilities/test-automation/).
