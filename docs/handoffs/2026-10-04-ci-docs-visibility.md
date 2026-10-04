# CI watching, delegated docs and visibility

- Status: in progress (not started beyond the plan)
- Branch: `feat/ci-docs-visibility` from `main` at `447d228` (after PR #40, the rename to tack)
- Plan: `docs/plans/2026-10-04-ci-docs-visibility.md` (approved, owner answers recorded there)
- Context: the GitHub repository is now `nbfrodri/agent-tack`; the local checkout stays at `~/Projects/agent-harness` (installed links point to that path). The owner's machine was reinstalled from `447d228`: `tack` works, state moved to `~/.local/state/agent-tack`, hooks tagged `#tack`, Codex agents generated. The owner must approve the new Codex hooks with `/hooks`.
- Work, in order:
  1. Guard rule for `gh pr merge`: deny when checks fail or are pending (toggle `merge-requires-green`, default true); ask when `gh` cannot tell. Tests in `tests/guard.test.sh` with a stub `gh` (green, failing, pending, no gh, toggle off, `--codex`).
  2. `ci-watch` toggle (instruction, default true) and its rule in `dev-workflow` and the mode files (`standard`, `strict`, `unleash`; not `lite`, `lean`); SessionStart passes non-default values.
  3. `docs-writer` on an economical model by default; rule: delegate when a committed change leaves docs pending in 3+ files; never ADRs or design decisions.
  4. Visibility: `tack · <mode>` chip in the usage band (bump the mod version); opt-in activity log (`tack config activity-log true`, `tack log`) written by the hooks for Claude Code and Codex.
  5. Docs (usage, editors, customization, architecture, how-it-works), full suite, PR, CI, merge (owner authorised push and merge when done).
- Follow-ups noted: rename the repo's own `.harness` marker to `.tack`; the `harness` alias will be removed in a later release.
- Process: avoid commands the guard asks about; stage explicit paths; run the full ShellCheck command and every suite before pushing.
