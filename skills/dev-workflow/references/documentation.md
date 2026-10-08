# Documentation checklist

Docs are updated in the same change as the code that affects them; outdated docs are worse than none. Structure, templates, docs for humans and AIs, plans, audits and handoffs: `project-docs` skill. Paths below are defaults; use configured architecture, plan and handoff locations when different.

Reuse existing document locations and recorded setup choices. The checklist identifies information to maintain, not mandatory new files. Propose additions outside the authorized scope through `new-project` → `references/onboarding.md`; do not recreate declined scaffolding.

## Before closing a task
- Is architecture guidance accurate and linked from the README/docs index when they exist? → maintain it from code evidence; propose missing guidance according to the project's setup choices.
- Did installing, configuring or running change? → `README.md`, `docs/development.md` and `AGENTS.md` (commands).
- New environment variables or config? → `.env.example` (no real values) and `docs/development.md`.
- Did a public API, CLI or endpoint change? → `docs/api.md` or the generated reference, and examples.
- A user-visible change? → `CHANGELOG.md` (if it exists; Keep a Changelog format, see `release`).
- Did the architecture change (components, flows, external dependencies)? → `docs/architecture.md` and `docs/overview.md`.
- A significant or hard-to-reverse architecture decision? → an ADR in `docs/adr/`.
- A new domain concept? → `docs/glossary.md`.
- Was there a plan? → update its status in `docs/plans/`.
- Does project policy require an AI log, or is there useful evidence beyond Git/PR history? → a concise row in `docs/ai/log.md`.
- Left unfinished? → a handoff in `docs/handoffs/`.

Comments and docstrings in code: see `conventions.md` (no comments by default; only the non-obvious why, and docstrings on the public API).
