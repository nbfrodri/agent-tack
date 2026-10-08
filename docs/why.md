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

The accepted direction is **less generic instruction and more concrete project verification**, supporting a shared way of working with AI. `tack verify` selects checks relevant to changed files, reuses the project's tools, exposes failures and states what remains unverified. Plans, reviews and documentation should answer a concrete need. [ADR 0003](adr/0003-project-verification-over-generic-process.md) records the transition. The later [adoption comparison](benchmarks/2026-10-08-adoption.md) confirmed configuration transfer but found tied correctness and higher session time against good native project guidance. TDD, pragmatic SOLID and the delivery workflow [remain part of tack](engineering-practices.md#practices-that-remain-part-of-tack).

## Team alignment and limits

Versioned conventions and capabilities help a team align across editors, while credentials, private memory, execution trust and personal settings stay local. Sharing configuration is not centralized administration, and instruction-following varies by model. [Tool support](editors.md) distinguishes executable checks from instruction-only behavior.

Success means fewer faulty deliveries, clearer verification and less human rework at an acceptable time/token cost. Branches, commits, extra tests or more agents do not establish that on their own. [Measured results](results.md) retain successes, null results and limitations; no significant general quality improvement is claimed yet.

The [value-first preflight](benchmarks/2026-10-08-value-first.md) explicitly compared tack with ordinary project instructions. That cheaper baseline did best on one task and tied code quality on the other. Choose it when it meets your needs. Tack's optional coordination helpers may solve different problems, but their lifecycle benefit must be measured rather than inferred from more workflow activity.

## When the extra work is worthwhile

Use these four outcomes to decide what to enable. A longer conversation, a larger test suite or more documents is not the outcome.

| Outcome | Put in place | Evidence to look for |
| --- | --- | --- |
| Catch important defects before delivery | Real project checks for contracts, invalid inputs and affected callers; inspect what those checks do not cover | A consequential defect caught before delivery that the cheaper setup missed |
| Need fewer corrections and integration fixes | Shared contracts, branch availability, focused handoffs and review follow-up reuse | Fewer failed deliveries, correction rounds or broken consumer integrations |
| Make the next change easier | Small responsibilities, compatible interfaces and useful regression tests | Less effort for a later change without losing behavior; inspect the code as well as tests |
| Bring another contributor up to speed | Versioned choices and context paths; a fresh clone reuses them, with execution trust still local | Successful setup and task completion with less repeated configuration or clarification |

For a fresh clone or an integration check, `tack verify --all --plan` previews all declared checks even when the working tree is clean. After local trust is granted, `tack verify --all` runs them. This closes a concrete verification gap; it cannot detect behavior the project's checks do not cover. Recorded setup choices tell the assistant what to reuse, but do not silently approve execution. See [verification](verification.md) and [setup](setup.md).

Compare a complete piece of work against a short project AGENTS.md: setup, delivery, review, corrections and a later change. Count failed attempts and the cost of maintaining the guidance. Extra instructions, context reads, check runs and Git operations can add time and tokens; these are possible cost sources, not a measured breakdown. A doubled cost needs a concrete compensating benefit. If accepted behavior and code quality tie while total effort rises, the extra work has not earned its cost in that case. Keep the useful checks and shared facts, and simplify the rest.

Token counts on a subscription are not dollar charges. Cached input is part of input, not an additional amount. Independent benchmark reviewers are evaluation overhead; reviews performed to finish a real delivery belong in that delivery's cost. Do not infer human onboarding savings or large-system scalability from a small agent-only test.
