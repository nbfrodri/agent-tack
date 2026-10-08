# 0003: Shared project configuration and evidence-based verification

- Status: accepted (2026-10-08); first verification increment implemented. Real-model outcome measurement remains pending.
- Evidence: [Codex comparison](../benchmarks/2026-10-08-codex.md), [code-quality review](../benchmarks/2026-10-08-codex-quality.md), [audit round 8](../audits/2026-10-08-evidence-review.md).
- Delivery: [implementation plan](../plans/2026-10-08-project-verification-implementation.md).
- External ideas: [upstream research and adoption decisions](../audits/2026-10-08-upstream-design-research.md).

## Context

tack began as portable AI dotfiles with an opinionated workflow: plans, tests, commits, documentation and reviews, scaled by mode. Sharing that configuration between tools and team members remains useful. However, following the same process is not evidence of better code.

In the 24-run Codex comparison, both conditions passed the original hidden tests. tack produced useful regression tests with Luna and branch/commit discipline, but used more tokens and about 2.3x session time across the task mix. A supplementary review found Unicode search failures in both Luna auto runs. Historical Haiku results show a security benefit in one scenario, not a universal improvement. The owner explicitly prioritized significant practical value over adding process.

## Decision

Make **quickly configurable, shared ways of working with AI** the center of tack: conventions, context entrypoints, agreed locations for useful artifacts and concrete verification. The owner clarified that team alignment is the primary product value; verification supports it. Supply less generic guidance; select relevant checks from the project, run them within existing trust boundaries, and expose failures and verification gaps before work is handed back.

- Share versioned configuration: project instructions, conventions, check definitions and justified local capabilities. Each teammate installs tack in their own environment. Credentials, private memory, execution trust and personal settings are not synchronized by repository adoption.
- Reuse the project's context and storage layout. Keep a concise entrypoint that tells assistants what to read and where to save necessary decisions, plans or handoffs. Guided setup should ask only unresolved questions and retain agreed choices. Local Git configuration is not automatically shared; a portable team profile remains future work.
- Prefer executable evidence: existing tests, type/lint checks, API/schema compatibility checks and domain invariants. Reuse project tools rather than introducing a new framework or treating a reviewer score as proof.
- Scale added work by demonstrated need. Create a skill for a reusable project procedure, an agent role for a distinct review responsibility, and a document for information someone needs to use or maintain. File counts, agent counts, branches and commits are not quality metrics.
- Keep deterministic safeguards and configuration preservation. User-selected strict workflows and explicitly requested plans/reviews remain valid. The new direction does not silently remove protections or rewrite local preferences.
- Report what was actually checked, what failed and what remains unknown. Path-based check selection is routing, not a complete dependency graph or proof of correctness. No checks is not a successful verification.

## Before and after

| Previous emphasis | New emphasis |
| --- | --- |
| Apply a general development playbook | Supply project conventions and select checks relevant to the change |
| Prove the assistant followed the workflow | Show defects detected, useful regressions and remaining gaps |
| Add plans, reviews or documentation by workflow habit | Add them for a concrete decision, risk or maintenance need |
| Discover project setup during routine implementation | Reuse existing choices; keep optional onboarding out of focused tasks |
| Compare branch/commit compliance | Compare delivered correctness, maintainability, human effort, latency and usage |

For example, an API change should select the project's compatibility check if one exists; a persistence change should select its migration/restore tests. tack must report a missing mapping instead of claiming that a generic test command proves compatibility or data safety.

## Delivery and non-goals

The first increment provides a shared verification command with optional project check mappings and a read-only plan, connected to existing completion adapters. Activation does not create optional files or grant execution trust. More precise dependency analysis, portable team preferences, shared remote configuration, centralized team policy management and automatic specialist routing are outside that increment.

Existing modes, safeguards and installed capabilities continue during the transition. Changes to defaults must be backed by measurement, preserve explicit user choices and be documented separately. Team alignment means common configuration and checks; tool support and model compliance still vary.

## Measuring success

Compare plain assistants, current tack and the candidate on held-out real repository tasks with acceptance criteria fixed in advance. Assess actual defects, code review findings, useful tests, human interventions, total time and token usage. Keep functional tests and subjective review separate, publish negative results, and do not equate subscription tokens with dollar charges.

A future comparison must fix its acceptance criteria and experiment thresholds before running. They are targets to validate, not marketing claims. Retain a new step only when it catches meaningful defects, reduces work or provides a concrete safety guarantee; remove or simplify steps whose overhead has no demonstrated benefit.
