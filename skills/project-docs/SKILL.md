---
name: project-docs
description: Project docs for humans (README, docs/) and AIs (AGENTS.md): technical sheet, architecture, ADRs, plans, audits, continuous handoffs, AI usage log, templates. Use when writing or updating docs, saving plans or audits, or for a handoff (document, write a handoff, summarise progress).
---

# Project documentation

Documentation exists so that someone new, whether a person or an AI, can understand the project and work on it without asking. That only works if it's **short, precise and current**. A page nobody reads, or one that's out of date, is worse than none.

## Writing rules
- **Simple, precise, concise.** Short sentences, lists and tables over paragraphs, one topic per file. Each document starts with one or two lines saying what it is for.
- **Show, don't narrate.** Use a diagram (Mermaid), a table or a command instead of a paragraph describing them. Use real, copy-pasteable commands that you've run.
- **No filler.** No marketing, no restating the code, no generic advice ("write clean code"). If a section has nothing specific to say, leave it out.
- **One source of truth.** Each fact lives in one place; other docs link to it instead of repeating it.
- **Same change, same PR.** Docs are updated in the change that makes them outdated (see the checklist in `dev-workflow` → `references/documentation.md`).
- English (as decided in `conventions.md`), Markdown, file names in kebab-case.

## Two audiences, one set of docs
| Entry point | For | Content |
| --- | --- | --- |
| `README.md` | Humans | What it is, quick start, links into `docs/`. Readable in two minutes. |
| `AGENTS.md` (+ `CLAUDE.md` containing `@AGENTS.md`) | AI assistants | Terse and imperative: commands, architecture in five lines, conventions and rules specific to this repo, a map of `docs/`. Under ~100 lines. |
| `docs/` | Both | The detail. Written for humans, structured enough for an AI to navigate (clear headings, tables, consistent file names). |

## Structure
```
README.md
AGENTS.md
CLAUDE.md                 # contains: @AGENTS.md
docs/
  README.md               # index: one line per document
  overview.md             # technical sheet
  architecture.md         # components, data flow, decisions, with Mermaid diagrams
  development.md          # setup, commands, tests, project structure, conventions specific to this repo
  deployment.md           # environments, how to deploy and roll back
  glossary.md             # domain terms (English term, original term, meaning)
  api.md / api/           # API reference, or a link to the generated OpenAPI
  adr/NNNN-title.md       # architecture decision records
  runbooks/<task>.md      # step-by-step operational procedures (incidents, restores, rotations)
  plans/YYYY-MM-DD-slug.md
  audits/YYYY-MM-DD-<type>-slug.md     # security, performance, code review, accessibility…
  handoffs/YYYY-MM-DD-slug.md
  ai/README.md            # AI policy for this project
  ai/log.md               # AI work log
  ai/prompts.md           # prompts that worked well here
  assets/screenshots/YYYY-MM-DD-slug.png
  assets/diagrams/        # only for diagrams that can't be Mermaid
```
**Create documents when there's something to put in them**, not empty placeholders. Minimum for a new project: `README.md`, `AGENTS.md`, `CLAUDE.md`, `docs/README.md`, `docs/overview.md`, `docs/architecture.md`, `docs/development.md`, and `docs/ai/README.md`. Add the rest as the project needs them.

Templates for every document are in this skill's `assets/` (`assets/README.md`, `assets/AGENTS.md`, `assets/docs/...`). Copy them, fill them in, and delete any section that doesn't apply.

## Working documents (plans, audits, handoffs)
These are committed so the reasons behind the work stay in history and anyone can pick the work up from another machine.
- **Plans:** at the strict workflow level, when a plan is approved (from you or the `planner` agent), save it to `docs/plans/` with `Status: approved`. Update the status to `done` (or `abandoned`, with the reason) when the work finishes. Commit as `docs(plans): …`.
- **Audits:** reports from `code-reviewer`, `security-auditor` and `performance-analyzer` (or manual reviews) that matter beyond the current conversation, such as pre-release audits or large reviews, go to `docs/audits/`, with findings and their status. The agents are read-only, so the main agent saves the file. Commit as `docs(audits): …`.
- **Handoffs (continuous checkpoints):** a session can stop at any moment (usage limits, context running out, a crash), and the AI cannot query the remaining usage, so don't wait until the end to write the handoff:
  - At the strict workflow level, create `docs/handoffs/YYYY-MM-DD-slug.md` when the work starts (template in `assets/`), with `Status: in progress`.
  - At the standard level, create one only when the work will span sessions or context or usage looks low; lite never needs one.
  - Update it at every milestone (each commit or plan step): done, next step, open questions, how to verify. This is just a file edit, with no commit each time; the file survives on disk even if the session dies.
  - Refresh it **immediately** when there are signs the session may end soon: a low remaining-context or token budget, a usage-limit warning, a very long session, or before a risky or long-running step.
  - Commit it (`docs(handoffs): …`) when stopping without finishing, before switching machine or AI tool, or when the user asks for a handoff.
  - When the task is finished, delete it: the plan, the commits and `docs/ai/log.md` keep the record.
  - Another AI or person must be able to continue from it alone.
- **Screenshots:** UI changes, bugs and audits can include screenshots in `docs/assets/screenshots/`, referenced from the relevant document. Never include real personal data in screenshots.

## AI usage
The project documents how AI is used. This is the place for it: commits stay free of AI attribution (as the user decided), and this log is where AI involvement is recorded.
- `docs/ai/README.md`: which assistants are used and with which configuration (skills, hooks, MCP servers), what the AI may do on its own and what needs human review.
- `docs/ai/log.md`: after each strict-level task (and any audit), append one row: date, tool and model, task, outcome (with links to PRs and commits), what a human reviewed. Keep the newest entries at the top.
- `docs/ai/prompts.md`: when a prompt or request worked notably well for this project, offer to save it (one line saying when to use it, then the prompt).

## Architecture docs
Every tack-enabled project must document its actual architecture in `docs/architecture.md` and link it from `README.md` and `docs/README.md`. In an existing project without it, create it during the first significant task after inspecting the code. Keep it current in the same change that alters components, dependencies or flows.

Use Mermaid, which GitHub renders, and keep each diagram small:
- a **context** diagram: the system, its users and the external systems it talks to;
- a **container** diagram: the apps and services, databases and queues, and how they communicate;
- a **sequence** diagram only for the one or two flows that are hard to follow in code (checkout, auth).
Below the diagrams, write a short list per component: responsibility, technology, where its code is. Explain significant decisions in ADRs and link to them.
