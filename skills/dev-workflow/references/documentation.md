# Documentation checklist

Docs are updated in the same change as the code that affects them; outdated docs are worse than none. Structure, templates, docs for humans and AIs, plans, audits and handoffs: `project-docs` skill.

## Before closing a task
- Did installing, configuring or running change? → `README.md`, `docs/development.md` and `AGENTS.md` (commands).
- New environment variables or config? → `.env.example` (no real values) and `docs/development.md`.
- Did a public API, CLI or endpoint change? → `docs/api.md` or the generated reference, and examples.
- A user-visible change? → `CHANGELOG.md` (if it exists; Keep a Changelog format, see `release`).
- Did the architecture change (components, flows, external dependencies)? → `docs/architecture.md` and `docs/overview.md`.
- A significant or hard-to-reverse architecture decision? → an ADR in `docs/adr/`.
- A new domain concept? → `docs/glossary.md`.
- Was there a plan? → update its status in `docs/plans/`.
- A significant AI-assisted task? → a row in `docs/ai/log.md`.
- Left unfinished? → a handoff in `docs/handoffs/`.

Comments and docstrings in code: see `conventions.md` (no comments by default; only the non-obvious why, and docstrings on the public API).
