# strict
When: several modules, architecture or public API changes, migrations, deletions, auth, payments or security, debatable design, or anything the user calls important or risky.
Scope: any

- Plan: written plan saved in `docs/plans/`; wait for the user's approval before changing code.
- Tests: TDD (red, green, refactor).
- Docs: the full checklist in `dev-workflow` references, plus ADRs for significant decisions.
- Handoff: from the start, updated at every milestone. AI log: one row in `docs/ai/log.md`.
- Review: `code-reviewer` before offering to push.
- Delegation: automatic for separable work after approval, unless `harness config delegation` is `off`.
