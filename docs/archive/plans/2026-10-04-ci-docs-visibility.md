# CI watching, green-only merges and delegated docs

- Status: done (approved 2026-10-04; owner answers below)
- Goal: never integrate red or unfinished CI, let the assistant fix CI failures itself, and spend fewer tokens on large documentation updates.

## Decisions

- `merge-requires-green` (hook, default true): the guard checks `gh pr checks` before `gh pr merge`; failing **or pending** checks deny the merge with the reason, so the assistant waits and retries. Without `gh` or a resolvable PR, it asks.
- `ci-watch` (instruction, default true): after a push or a new PR, the assistant waits for CI in the background, reports the result and fixes failures from the log before continuing. Applies in every mode except `lite` and `lean`.
- Docs delegation: when a committed change leaves documentation pending in 3 or more files, delegate it to `docs-writer` on an economical model; smaller updates, ADRs and design decisions stay with the main assistant. `docs-writer` defaults to an economical model.

- Visibility (approved): the usage band shows a `tack · <mode>` chip (`tack · off` when the project is not enabled); an opt-in activity log (`tack config activity-log true`, read with `tack log`) records hook runs, guard decisions and Stop findings with timestamps, for Claude Code and Codex.

## Work

1. Guard rule for `gh pr merge` with tests (green, failing, pending, no `gh`, toggle off, Codex mode).
2. `ci-watch` and `merge-requires-green` in `features.txt`; mode files and `dev-workflow` rules; SessionStart passes non-default values.
3. `docs-writer` model and the delegation rule in `dev-workflow` and `project-docs`.
4. Docs: usage (CI section), editors (Codex note), customization.
