# unleash
When: only when the user selects it: long autonomous work without confirmations, on a branch, accepting the risks.
Scope: project
Context: full

- Autonomy: do not wait for plan approval and do not ask questions; choose the reasonable option and record every assumption in the handoff and in the final summary.
- Safety floor: never merge to main, create tags or releases, rewrite published history, force-push, bypass hooks, or delete outside the project; the command guard still refuses or asks about these.
- Outward actions: you may push your own branch and open a pull request; nothing else outward without the user.
- Commands: avoid opaque shell constructs (heredocs to interpreters, loops, dynamic commands); write multi-step logic to a script file and run it.
- Plan: written plan in `docs/plans/`, followed without waiting.
- Tests: TDD; never commit failing tests.
- Docs: everything the change affects.
- Handoff: from the start, updated at every milestone, listing assumptions. AI log: one row.
- Review: run `code-reviewer` on the final diff and fix its findings before opening the pull request.
- Delegation: automatic for separable work, unless `tack config delegation` is `off`.
- Limits: respect `tack config unleash-max-tool-calls` and `unleash-max-cost`; stop with a summary when one is reached.
