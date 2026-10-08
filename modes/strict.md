# strict
When: consequential uncertainty, incompatible interfaces, migrations, data loss, auth, payments or security, or work the user explicitly calls risky. File count and team membership alone do not require strict.
Scope: any
Context: full

- Plan: written plan saved in the configured `plans-path` (default `docs/plans`); confirm the plan before changing code unless the user already authorized that scope.
- Tests: TDD (red, green, refactor).
- Docs: the full checklist in `dev-workflow` references, plus ADRs for significant decisions.
- Handoff: only when the work spans sessions, is delegated, or context or usage looks low; updated at milestones, not every commit. AI log: only when project policy requires it or it records useful evidence beyond Git/PR history.
- Review: inspect the final diff and risk-specific evidence. Use `code-reviewer` when independent assessment is needed for consequential changes or project policy requires it, respecting delegation settings.
- Visual review: for visible UI changes, use `tack shots --before URL` and `tack shots --after URL` when capture is available. Review hierarchy, readability, states, responsiveness and accessibility; fix concrete blockers and verify affected views. Use `ui-reviewer` only when delegation is appropriate. Screenshots cannot prove interaction or accessibility behavior. No numeric score is required. Use local or preview URLs with test data; ask before publishing private screenshots. Skip when `tack config visual-review` is `false`.
- CI: after a push or a new pull request, wait for CI in the background, report the result and fix failures from the log before continuing.
- Delegation: automatic for separable work after approval, unless `tack config delegation` is `off`.
