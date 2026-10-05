# strict
When: several modules, architecture or public API changes, migrations, deletions, auth, payments or security, debatable design, or anything the user calls important or risky.
Scope: any
Context: full

- Plan: written plan saved in `docs/plans/`; wait for the user's approval before changing code.
- Tests: TDD (red, green, refactor).
- Docs: the full checklist in `dev-workflow` references, plus ADRs for significant decisions.
- Handoff: only when the work spans sessions, is delegated, or context or usage looks low; updated at milestones (a merged PR, a plan step), not every commit. AI log: one row in `docs/ai/log.md`, committed with the change it records.
- Review: `code-reviewer` before offering to push.
- Visual review: when the change touches UI files (components, styles, templates), run `tack shots --before URL` before editing (after creating the branch) and `tack shots --after URL` after, then have `ui-reviewer` score `tack shots --dir` and save its `score.md` there (`tack shots --index` adds it to `index.html`); below 7/10, fix the findings and repeat once. Capture local or preview URLs with test data, and ask before attaching shots that show personal data to a pull request. Skip it when `tack config visual-review` is `false`.
- CI: after a push or a new pull request, wait for CI in the background, report the result and fix failures from the log before continuing.
- Delegation: automatic for separable work after approval, unless `tack config delegation` is `off`.
