# AI in this project

How AI assistants are used to build and maintain agent-tack. Records: [log.md](log.md).

## How it's used
- **Tack builds itself.** This repo is enabled (`.tack`), so assistants working here follow its own workflow: plan, tests first, Conventional Commits, docs, reviews.
- **What the AI does:** implements changes and their tests, reviews and audits the repo with read-only reviewer agents, runs the behaviour evals, and keeps these docs up to date.
- **What a person does:** decides scope, conventions and trade-offs (every design decision here was chosen by the owner through explicit questions), approves pushes, merges, releases and GitHub settings, and reviews the result.

## Rules
- Commits carry no AI attribution; AI involvement is recorded in [log.md](log.md) instead.
- The AI asks before anything outward-facing: push, PRs, issues, releases, repository settings.
- Changes to the installer or hooks come with tests (`tests/`), and CI must pass on Linux and macOS.
- Claims in the docs are backed by evidence: test counts from the suites, results from the [evals](../results.md).

## Records
| Record | Where |
| --- | --- |
| Work log | [log.md](log.md) |
| Audits and their fixes | [../archive/audits/](../archive/audits/) |
| Handoffs of unfinished work | [../handoffs/](../handoffs/) |
| Measured behaviour | [../results.md](../results.md) |
