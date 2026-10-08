---
name: new-project
description: "Bootstrap a project or add missing foundations: structure, tests, tooling, CI and docs. Use when starting, scaffolding or initializing a repository."
---

# New project

A new project should have clear instructions and reproducible checks appropriate to its purpose. For new repositories and existing projects adopting tack, first follow [references/onboarding.md](references/onboarding.md): inspect the project, select optional additions with the user, and remember the choices. The checklist below is a menu for the approved scope, not a set of mandatory files. References to other skills are optional shortcuts when those skills are installed; otherwise use the project's existing tooling and conventions. Do not install a catalog to complete a routine setup.

## 1. Clarify (one round of questions, with defaults)
Infer established choices from the repository and conversation. Ask only about unresolved language/runtime, project type, services and deployment choices. When services or the deployment target justify Docker, offer:
- **Local development with docker-compose** (the app plus its services: database, cache…), so the project runs with one command on any machine;
- **a production image** as well (multi-stage Dockerfile), for VPS or AWS deploys;
- **no Docker**, e.g. for a library, a CLI or a Vercel-only frontend.

Recommend the option that fits. Present concrete optional files and their purpose before creating them; reuse prior explicit approval instead of asking again. Continue authorized independent work while unresolved choices are pending.

Follow `dev-workflow` → `references/conventions.md` and the stack's file in `references/languages/` (pnpm for JS/TS, uv for Python, Composer + Pint for PHP, English code, kebab-case files in TS). Prefer the ecosystem's official generator (e.g. `npm create vite`, `uv init`, `cargo new`, `go mod init`, `dotnet new`) over writing boilerplate by hand, and current stable versions of tools.

## 2. Foundations checklist
Keep the initial capability catalog empty unless concrete project work justifies a procedure or role. When it does, define its trigger, bounded instructions and validation in the project; index local definitions in AGENTS.md for later sessions. Creating a role does not itself authorize delegation.

- `git init -b main`, plus a `.gitignore` for the language, editor and OS. Ignore `.env`.
- Enable and create the common base: `tack enable --shared --scaffold` (creates a `.tack` marker to commit with the repo). For local activation use `tack enable --scaffold`. Review the four generated files against the project; commands are detected, not executed.
- `.editorconfig` copied from this skill's `assets/editorconfig`.
- Folder structure:
  - with a real domain: `domain/`, `application/`, `infrastructure/`, `interfaces/` (see `dev-workflow` → `references/design.md`);
  - otherwise the framework's standard layout.
- Test framework configured, with one passing sample test, and a single command to run it.
- Linter and formatter with the ecosystem's standard tool (ruff, eslint + prettier or biome, pint, clippy + rustfmt, golangci-lint…), plus scripts/commands to run them. Keep the formatter's defaults (no overrides for quotes, semicolons or line width).
- Type checking where the language supports it (strict mode for TypeScript, mypy/pyright for Python).
- `.env.example` with every variable documented and no real values.
- Documentation following `project-docs`: start with the common base; propose a README, index or development guide when useful, and add other documents only when there is concrete content and they are in the selected scope.
- CI in `.github/workflows/ci.yml`: install, lint, type-check and test on push and pull requests.
- Issue forms and a PR template: reuse existing templates; add missing ones from the `github-issues` skill's `assets/` into `.github/`, adapted to the project's validation commands. PR drafting follows `dev-workflow` → `references/git-github.md`.
- Docker, if chosen: following `deployment` → `references/docker-vps.md`: a multi-stage, non-root `Dockerfile` with a healthcheck, a `.dockerignore` (`.git`, `.env`, dependencies, build output, tests), `compose.yaml` for the services plus `compose.override.yaml` for local development, the env vars in `.env.example`, and the Docker commands in the README and `AGENTS.md`. Build the image in CI.
- Releases: release-please from the `release` skill's `assets/` (workflow, config with the stack's `release-type`, manifest at `0.1.0`), plus an empty `CHANGELOG.md`. Tags and versions follow `conventions.md` → "Releases and tags".
- Dependabot: `.github/dependabot.yml` with weekly updates for the project's package ecosystems and for `github-actions` (see the example below).
- Optional, if the user wants them: commit-msg hook with commitlint (or equivalent) to enforce Conventional Commits; a pre-commit hook for lint/format; a `LICENSE` (ask which one); `docs/adr/0001-record-architecture-decisions.md`.

Dependabot example (keep only the ecosystems the project uses, e.g. `npm`, `uv`, `pip`, `composer`, `docker`; check the current list of supported ecosystems if unsure):
```yaml
version: 2
updates:
  - package-ecosystem: npm
    directory: /
    schedule: { interval: weekly }
    groups:
      minor-and-patch: { update-types: [minor, patch] }
    commit-message: { prefix: chore, prefix-development: chore, include: scope }
  - package-ecosystem: github-actions
    directory: /
    schedule: { interval: weekly }
    commit-message: { prefix: ci }
```
Grouping minor and patch updates keeps the PR count manageable; the commit-message prefixes keep Dependabot's commits in Conventional Commits format.

## 3. Commits
Build the scaffold in a few logical commits, for example:
1. `chore: initialize project with <tool>`
2. `build: configure linting and formatting`
3. `test: set up <framework> with sample test`
4. `ci: add GitHub Actions workflow`
5. `docs: add README, AGENTS.md and project docs`
6. `chore(github): add issue templates and Dependabot`
7. `ci: add release-please`
8. `build: add Docker setup` (if chosen)

Run lint and tests before finishing. Ask the user before creating the GitHub repo and pushing, and ask whether it should be public or private (`gh repo create <name> --private --source . --push`). With permission, enable both merge methods so the user can choose from a contextual recommendation, as in `conventions.md`:
```bash
gh repo edit --enable-merge-commit --enable-squash-merge \
  --enable-rebase-merge=false --delete-branch-on-merge
```
