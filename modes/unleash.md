# unleash
When: only when the user selects it: long autonomous work without confirmations, on a branch, accepting the risks.
Scope: project
Context: full

- Autonomy: do not wait for plan approval and do not ask questions; choose the reasonable option and record every assumption in the handoff and in the final summary.
- Safety floor: never merge to main, create tags or releases, rewrite published history, force-push, bypass hooks, or delete outside the project; the command guard still refuses or asks about these, within the limits in `docs/how-it-works.md` (what the command guard covers, and what it does not).
- Outward actions: you may push your own branch and open a pull request; nothing else outward without the user.
- Commands: avoid opaque shell constructs (heredocs to interpreters, loops, dynamic commands); write multi-step logic to a script file and run it.
- Plan: written plan in `docs/plans/`, followed without waiting.
- Tests: TDD; never commit failing tests.
- Docs: everything the change affects.
- Handoff: from the start (long work spans sessions), updated at milestones, not every commit, listing assumptions. AI log: one row, committed with the change it records.
- Review: run `code-reviewer` on the final diff and fix its findings before opening the pull request.
- Visual review: when the change touches UI files (components, styles, templates), run `tack shots --before URL` before editing (after creating the branch) and `tack shots --after URL` after, then have `ui-reviewer` score `tack shots --dir` and save its `score.md` there (`tack shots --index` adds it to `index.html`); below 7/10, fix the findings and repeat once. Capture local or preview URLs with test data, and ask before attaching shots that show personal data to a pull request. Skip it when `tack config visual-review` is `false`.
- CI: after a push or a new pull request, wait for CI in the background, report the result and fix failures from the log before continuing.
- Delegation: automatic for separable work, unless `tack config delegation` is `off`.
- Limits: respect `tack config unleash-max-tool-calls` and `unleash-max-cost`; stop with a summary when one is reached.
