---
name: new-project
description: Bootstrap a new software project with good foundations - git repo, structure by layers or DDD contexts, test framework ready for TDD, linter/formatter, .gitignore, .env.example, README, AGENTS.md, CI on GitHub Actions and Conventional Commits. Use whenever the user wants to start, create, scaffold, initialise or set up a new project, app, API, library, CLI or repo ("crea un proyecto", "empieza una app", "inicializa un repo"), or to add missing basics (tests, CI, linting, README) to an existing project.
---

# New project

A new project should be ready for the `dev-workflow` from its first commit: tests run with one command, lint runs with one command, CI checks both, and the README explains how to run everything.

## 1. Clarify (one round of questions, with defaults)
Language/runtime and framework, project type (API, web, CLI, library), database if any, and whether the domain is complex enough for DDD layers. Propose sensible defaults and the plan, then wait for approval, since scaffolding is a big change.

Follow `dev-workflow` → `references/conventions.md` (pnpm for JS/TS, uv for Python, Composer + Pint for PHP, English code, kebab-case files in TS). Prefer the ecosystem's official generator (e.g. `npm create vite`, `uv init`, `cargo new`, `go mod init`, `dotnet new`) over writing boilerplate by hand, and current stable versions of tools.

## 2. Foundations checklist
- `git init -b main`, plus a `.gitignore` for the language, editor and OS. Ignore `.env`.
- `.editorconfig` copied from this skill's `assets/editorconfig`.
- Folder structure:
  - with a real domain: `domain/`, `application/`, `infrastructure/`, `interfaces/` (see `dev-workflow` → `references/design.md`);
  - otherwise the framework's standard layout.
- Test framework configured, with one passing sample test, and a single command to run it.
- Linter and formatter with the ecosystem's standard tool (ruff, eslint + prettier or biome, pint, clippy + rustfmt, golangci-lint…), plus scripts/commands to run them. Keep the formatter's defaults (no overrides for quotes, semicolons or line width).
- Type checking where the language supports it (strict mode for TypeScript, mypy/pyright for Python).
- `.env.example` with every variable documented and no real values.
- `README.md` following `dev-workflow` → `references/documentation.md`.
- `AGENTS.md` for AI assistants: how to install, test, lint and run; the architecture in a few lines; and project conventions. Add a `CLAUDE.md` containing just `@AGENTS.md` so Claude Code reads the same file.
- CI in `.github/workflows/ci.yml`: install, lint, type-check and test on push and pull requests.
- Issue forms and a PR template: copy them from the `github-issues` skill's `assets/` into `.github/`.
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
5. `docs: add README and AGENTS.md`
6. `chore(github): add issue templates and Dependabot`

Run lint and tests before finishing. Ask the user before creating the GitHub repo and pushing, and ask whether it should be public or private (`gh repo create <name> --private --source . --push`). Once created, configure squash merging as in `conventions.md`:
```bash
gh repo edit --enable-squash-merge --squash-merge-commit-message pr-title-description \
  --enable-merge-commit=false --enable-rebase-merge=false --delete-branch-on-merge
```
