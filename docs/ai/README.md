# AI in this project

How AI assistants are used to build and maintain agent-tack. Records: [log.md](log.md).

## How it's used
- **Tack builds itself.** This repo is enabled (`.tack`), so assistants working here follow its own workflow: plan, tests first, Conventional Commits, docs, reviews.
- **What the AI does:** implements changes and their tests, reviews and audits the repo with read-only reviewer agents, and keeps these docs up to date.
- **What a person does:** decides scope, conventions and trade-offs (consequential choices follow the owner's direction; routine implementation stays with the assistant), approves pushes, merges, releases and GitHub settings, and reviews the result.

## Rules
- Commits carry no AI attribution; AI involvement is recorded in [log.md](log.md) instead.
- Outward-facing work needs authorization: push, PRs, issues, releases and repository settings. Prior authorization counts; do not ask again for the same scope.
- Changes to the installer or hooks come with tests (`tests/`), and the relevant Linux, macOS and native Windows CI checks must pass.
- Claims in the docs are backed by evidence: test counts from the suites and commands that were run.

## Records
| Record | Where |
| --- | --- |
| Work log | [log.md](log.md) |
| Handoffs of unfinished work | Created under `docs/handoffs/` when needed and moved to `docs/archive/handoffs/` when finished |
