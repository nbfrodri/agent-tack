# strict
When: several modules, architecture or public API changes, migrations, deletions, auth, payments or security, debatable design, or anything the user calls important or risky.
Scope: any
Context: full

- Plan: written plan saved in `docs/plans/`; wait for the user's approval before changing code.
- Tests: TDD (red, green, refactor).
- Docs: the full checklist in `dev-workflow` references, plus ADRs for significant decisions.
- Handoff: only when the work spans sessions, is delegated, or context or usage looks low; updated at milestones (a merged PR, a plan step), not every commit. AI log: one row in `docs/ai/log.md`, committed with the change it records.
- Review: `code-reviewer` before offering to push.
- CI: after a push or a new pull request, wait for CI in the background, report the result and fix failures from the log before continuing.
- Delegation: automatic for separable work after approval, unless `tack config delegation` is `off`.
