# Conventions

The conventions the harness applies, at a glance. Source of truth: [`skills/dev-workflow/references/conventions.md`](../skills/dev-workflow/references/conventions.md).

| | |
| --- | --- |
| Commits | Conventional Commits, English, no AI attribution (enforced by hooks) |
| PRs | Squash merge; the PR title becomes the commit on `main` |
| Releases | SemVer, annotated `vX.Y.Z` tags, release-please, `CHANGELOG.md` + GitHub Release |
| Code | English; formatter defaults; functional first; no unnecessary comments |
| JS/TS | pnpm, TypeScript strict, kebab-case files, named exports |
| Python | uv, Ruff, mypy/pyright |
| PHP | Composer, Pint, Larastan, Pest |
| Docs | Short and precise; `AGENTS.md` for AIs, `docs/` shared; plans, audits, handoffs and AI log in `docs/` |
