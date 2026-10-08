---
name: dev-workflow
description: "Apply tack's task-sized workflow for implementation, debugging and Git/PR work in enabled projects: relevant context, meaningful tests and verified delivery."
---

# Development workflow

Use in enabled projects (`tack status`). Follow the project's own instructions, commands and conventions. Read only the references needed for this task; installing a skill does not make every procedure mandatory.

## Choose the effort

Read the active `tack mode` from startup context, or query it once. In `auto`, state the chosen level and reason once (`Level: standard (bounded behavior change)`). A conversational override applies to this task; shared defaults stay unchanged.

| Level | When | Work required |
| --- | --- | --- |
| lite | Questions, docs, configuration and small low-risk changes | Inspect relevant code, check the change, review the diff. No plan file or extra agent. |
| standard | Bounded behavior changes with established patterns | A short task list, red/green/refactor for behavior, affected checks and docs. |
| strict | Consequential uncertainty, incompatible interfaces, migrations, data loss, auth, payments or security | A durable plan, risk-specific tests and review; record significant design decisions. |

File count, team membership and a new feature alone do not make work strict. Raise effort when consequences require it; explain changes. Fixed/custom modes and explicit project requirements still apply. Mode files own their detailed requirements; `unleash` remains a separate opt-in autonomous mode.

## Complete the task

1. **Understand.** Establish the requested outcome and observable acceptance criteria. Read relevant code and project guidance. Reuse settled decisions; ask only about missing information that changes the result. Brainstorm alternatives for unresolved design, not for a clear routine request. On resume, compare this task's handoff with Git; never resume unrelated branch work.
2. **Choose the smallest complete change.** Search callers, tests, configuration and docs affected by the behavior. Reuse existing code, standard libraries and installed tools. KISS/YAGNI apply to workflow as well as code. SOLID means useful responsibilities and boundaries, not speculative interfaces or layers. Preserve error handling and validation. Keep unrelated refactors out.
3. **Work on a branch.** Inspect status and preserve unrelated changes. Branch off protected trunks for changes. Use a worktree when concurrent writers or dirty unrelated work need isolation; a serial task does not require one.
4. **Implement and verify.** Use TDD for behavior at standard/strict and useful regression tests for defects. Existing tests may sufficiently verify a trivial change; do not create a test just to change a filename. Run the project's affected checks or `tack verify`, inspect failures/skips/unmapped paths, and broaden when required by risk or project policy. Repeat a passing check after relevant changes or new evidence, not merely to repeat a workflow step.
5. **Deliver.** Review the final diff, update guidance made inaccurate, and commit coherent verified changes using Conventional Commits, without AI attribution. A plan, ADR, handoff or AI log needs a durable purpose or project requirement. Lead the reply with the original task's outcome, actual verification and unresolved limits, even after a completion-hook repair.

Respect existing authorization for pushes, GitHub writes and merges. Prepare requested PRs from the project's template; `Closes` means fully resolved, `Refs` means partial. After publishing, follow CI unless `ci-watch` is false; inspect the current PR head before merging. Never bypass a rejected hook or describe instructions, a passing score or a clean Git merge as proof of correctness.

## Load detail only when useful

| Need | Reference |
| --- | --- |
| Git, publication or merge policy | `references/git-github.md` |
| Code conventions | `references/conventions.md`; only the relevant `references/languages/` file |
| Design tradeoffs or TDD details | `references/design.md`, `references/tdd.md` |
| Changed documentation | `references/documentation.md`; `project-docs` for substantial documentation work |
| Parallel team dependencies | `references/teamwork.md` |
| Public contracts, configuration or producer/consumer changes | `references/contract-review.md` |
| Concurrent working directories | `references/worktrees.md` |
| Reply presentation | `references/communication.md` |
| Explicit requirement IDs | `references/requirements.md`; trace is optional text linkage, not coverage |

Use `debugging` for an unexplained failure, `github-issues` for issues/reviews, and `new-project` for requested setup. Reuse project-local skills; create a capability only for a demonstrated reusable gap (`lessons` → `references/project-capabilities.md`). An independent reviewer is useful for consequential or difficult-to-assess changes; do not launch one solely because a diff is long. Delegate only useful separable work under the active policy (`orchestrate`). Stack skills and specialist agents remain available when their expertise is needed.

Search before reading; batch independent calls, trim output and avoid rereading context. Measure useful outcomes rather than document, agent or tool-call counts.
