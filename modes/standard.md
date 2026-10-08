# standard
When: a bounded feature or bug fix inside one area, following existing patterns.
Scope: any
Context: index

- Plan: a short plan in the tool's task list; not saved.
- Tests: TDD (red, green, refactor).
- Docs: everything the changed behaviour affects; the configured architecture document if structure changes.
- Handoff: only if the work spans sessions or context or usage looks low. AI log: none.
- Review: `code-reviewer` for large or risky diffs.
- Visual review: for visible UI changes, use `tack shots --before URL` and `tack shots --after URL` when capture is available. Review hierarchy, readability, states, responsiveness and accessibility; fix concrete blockers and verify affected views. Use `ui-reviewer` only when delegation is appropriate. Screenshots cannot prove interaction or accessibility behavior. No numeric score is required. Use local or preview URLs with test data; ask before publishing private screenshots. Skip when `tack config visual-review` is `false`.
- CI: after a push or a new pull request, wait for CI in the background, report the result and fix failures from the log before continuing.
- Delegation: suggest it and wait for approval.
