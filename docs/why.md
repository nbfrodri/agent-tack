# Why agent-tack

tack helps developers and teams define a common way of working with AI: project conventions, relevant context, agreed locations for work artifacts, useful capabilities and checks that travel across supported tools. Configure those choices once with the assistant, version them and share them with the team. It also provides concrete safeguards around Git operations and the configuration it installs.

## What is useful today

- Shared project guidance reduces the need to repeat conventions in every tool and session. Teammates review changes to that guidance alongside the code.
- Git hooks inspect staged secrets and commit/push rules. Native adapters add command, formatting and completion checks where supported. These controls have specific limits; they are not a sandbox or universal policy enforcement.
- Existing project commands can be detected or configured with `check-fast`, and run automatically only within local execution trust.
- Installation preserves user configuration and tracks what can safely be restored on removal. Project activation and personal trust are separate.
- Local skills and specialist roles can retain a useful project procedure or responsibility. They are useful when needed, not because a large catalog is inherently better.

## Why the focus is changing

The [Codex comparison](benchmarks/2026-10-08-codex.md) found that mandatory process added time and tokens without improving the original acceptance outcomes on these small tasks. Luna gained regression tests, but a separate review also found a Unicode limitation in its auto outputs. Earlier Haiku experiments showed a security gain on one scenario. Those results justify selective use and further measurement, not a promise to make every model produce better code.

The accepted direction is **less generic instruction and more concrete project verification**, supporting a shared way of working with AI. `tack verify` selects checks relevant to changed files, reuses the project's tools, exposes failures and states what remains unverified. Plans, reviews and documentation should answer a concrete need. [ADR 0003](adr/0003-project-verification-over-generic-process.md) records the decision and transition; the first verification increment has local behavior tests, with real-model outcome measurement still pending.

## Team alignment and limits

Versioned conventions and capabilities help a team align across editors, while credentials, private memory, execution trust and personal settings stay local. Sharing configuration is not centralized administration, and instruction-following varies by model. [Tool support](editors.md) distinguishes executable checks from instruction-only behavior.

Success means fewer faulty deliveries, clearer verification and less human rework at an acceptable time/token cost. Branches, commits, extra tests or more agents do not establish that on their own. [Measured results](results.md) retain successes, null results and limitations; no significant general quality improvement is claimed yet.
