# standard
When: a bounded feature or bug fix inside one area, following existing patterns.
Scope: any
Context: index

- Plan: a short plan in the tool's task list; not saved.
- Tests: TDD (red, green, refactor).
- Docs: everything the changed behaviour affects; `docs/architecture.md` if structure changes.
- Handoff: only if the work spans sessions or context or usage looks low. AI log: none.
- Review: `code-reviewer` for large or risky diffs.
- CI: after a push or a new pull request, wait for CI in the background, report the result and fix failures from the log before continuing.
- Delegation: suggest it and wait for approval.
