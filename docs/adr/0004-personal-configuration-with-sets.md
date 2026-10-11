# 0004: A personal configuration, with sets of pinned skills

- Status: accepted (2026-10-11). Supersedes the product positioning of [0003](0003-project-verification-over-generic-process.md); its preference for the project's own executable checks stands.

## Context

tack was evaluated as a general product: would its workflow make any model produce better code for anyone? Six comparisons between 2026-10-03 and 2026-10-09 did not show that. Against a short project `AGENTS.md`, the last one measured 5% to 62% more time and 25% to 68% more input tokens, with no better code quality. Concrete, deterministic pieces did work: selecting a project's checks from changed paths, comparing agreed settings and testing a prospective merge.

The owner's actual need is narrower and does not depend on that proof: the same instructions, skills, agents, hooks and checks on every machine and in every AI tool, including collections of skills written by other people.

## Decision

Treat this repository as one person's configuration, public to read or fork, with no adoption or general-quality claims.

- Remove the evaluation harness (`evals/`), the benchmark reports, the product audits and the archived plans from the tree. They remain in the Git history before this change.
- Keep every runtime capability: skills, agents, modes, hooks, the guard, verification, shared project preferences and the installer with its ownership records.
- Add **sets**: named bundles of skills, agents and Claude Code plugins (`sets.txt`). External skill collections are declared in `sources.txt`, each pinned to a full commit, checked out under the user's data directory and linked rather than copied. A set is active in one project or everywhere.
- The installer may now download the collections that an active set uses. The earlier rule that the base installer downloads no external collection protected third parties from defaults they had not chosen; it does not apply to the owner's own selection.

## Consequences

- Defaults follow the owner's preferences and may change without a migration path for other users. A fork is the supported way to diverge.
- Cost remains real: every active skill adds its description to each session. Sets are activated per project by default, and only on purpose everywhere.
- Skills run with the assistant's permissions. Pinning controls when a skill changes, not what it says; reviewing a collection before pinning it stays a manual step.
- Skills reach every tool in `targets.txt`. Plugins, and agents at project scope, reach Claude Code only.
- Capabilities that were built for other adopters (collaborator bootstrap, native Windows support, adapters for tools the owner does not use) stay until their use is known. Removing one is a separate decision.
