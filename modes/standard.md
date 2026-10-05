# standard
When: a bounded feature or bug fix inside one area, following existing patterns.
Scope: any
Context: index

- Plan: a short plan in the tool's task list; not saved.
- Tests: TDD (red, green, refactor).
- Docs: everything the changed behaviour affects; `docs/architecture.md` if structure changes.
- Handoff: only if the work spans sessions or context or usage looks low. AI log: none.
- Review: `code-reviewer` for large or risky diffs.
- Visual review: when the change touches UI files (components, styles, templates), run `tack shots --before URL` before editing (after creating the branch) and `tack shots --after URL` after, then have `ui-reviewer` score `tack shots --dir` and save its `score.md` there (`tack shots --index` adds it to `index.html`); below 7/10, fix the findings and repeat once. Capture local or preview URLs with test data, and ask before attaching shots that show personal data to a pull request. Skip it when `tack config visual-review` is `false`.
- CI: after a push or a new pull request, wait for CI in the background, report the result and fix failures from the log before continuing.
- Delegation: suggest it and wait for approval.
