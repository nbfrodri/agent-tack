---
name: dev-workflow
description: The user's engineering workflow for projects with tack enabled, scaled by workflow level (lite, standard, strict): planning, TDD, SOLID/DDD, code and git conventions (Conventional Commits, branches, PRs) and docs. Use whenever writing, changing or debugging code, committing or opening PRs in such projects (implement, fix, commit).
---

# Dev Workflow

Applies in projects where tack is enabled (`tack status`; Claude Code says so at session start). Elsewhere, work normally without this ceremony unless the user asks for it.

The goal: every request ends as a small, tested change in a clean git history, with only as much process as the task deserves. It works the same with any assistant (Claude, Codex or another).

- **Language, attribution and what to ask before doing:** as in the global instructions; the git details are in `references/git-github.md`.
- **Code and git conventions:** `references/conventions.md` (style, naming, formatting, PR merging).
- **The project's own conventions win.** If the repo has its own CONTRIBUTING, AGENTS.md, CLAUDE.md, linter, commit format or folder structure, follow them over this guide. This skill fills the gaps; it doesn't override what exists.

## Workflow levels

`tack mode` sets the level: `auto` (the default) picks one per task; `lite`, `standard` or `strict` fix it for every task. A project setting overrides the user's global default (`tack mode --global`). The user can change the level for any task in conversation ("do this in strict"). Each mode's rules live in a file (`modes/<name>.md` in tack, or the user's own in `~/.config/agent-tack/modes/`); SessionStart supplies the active one, and `tack mode show` prints it. A user mode overrides the table below where it differs. Two built-in modes sit outside the table: `lean` (self-contained minimal rules to save tokens; this skill is not loaded) and `unleash` (autonomous, project-only).

In `auto`, classify each request before acting and state it in one line, for example `Level: standard (bounded bug fix in one module)`; keep that shape (a one-word label, a colon, the mode name, the reason) in any language, because the activity log records it:
- **lite:** questions, typos, renames, config tweaks, a one-line fix, small scripts or prototypes.
- **standard:** a bounded feature or bug fix inside one area, following existing patterns.
- **strict:** several modules, architecture or public API changes, data migrations, deleting things, auth, payments or security, debatable design, or anything the user calls important or risky.

If a task turns out larger or riskier than its level, say so and move up before continuing; never move down silently.

| | lite | standard | strict |
| --- | --- | --- | --- |
| Plan | none | short plan in the tool's task list; not saved | written plan saved in `docs/plans/`; **wait for approval** |
| Branch | off `main`/`master`/`develop` for any change | same | same |
| Commits | Conventional Commits | each verified milestone | each verified milestone, SHAs in the handoff |
| Tests | a test for changed logic; run the affected suite | TDD: red, green, refactor | TDD |
| Docs | only if the change contradicts existing docs | docs affected by changed behaviour; `docs/architecture.md` if structure changes | full checklist in `references/documentation.md`, ADRs |
| Handoff | none | only if work spans sessions or context or usage looks low | from the start, updated every milestone |
| AI log | none | none | one row in `docs/ai/log.md` |
| Review | read your own diff | `code-reviewer` for large or risky diffs | `code-reviewer` before offering to push |
| CI | none | after a push or new PR, wait for CI in the background, report it and fix failures from the log | same |
| Delegation | suggest and wait | suggest and wait | automatic after approval unless `tack.delegation` is `off` |

Every level keeps the hooks' guarantees (Conventional Commits, no AI attribution, no secrets, protected `main` and tags) and the rules on what to ask before doing.

## Token efficiency (every level)

- Search before reading: locate with grep or glob, then read only the needed line range, not whole files.
- Do not re-read what is already in context, and do not re-verify an edit the tool reported as applied.
- Batch independent tool calls in one response; run long commands in the background instead of polling.
- Trim output: `tail`, quiet flags and summaries instead of full logs; never paste large outputs back.
- Run the affected tests first and the full suite once, before committing or closing. Use the commands in the project's `AGENTS.md`; if they are missing, find them once and add them there instead of probing in every session.
- Keep replies, handoffs and docs concise: state what changed and what is pending, not the whole history.
- Delegate only separable work, with self-contained prompts and the most economical model that can do it.
- Avoid commands the command guard asks about (heredocs to interpreters, shell loops, dynamic commands): put multi-step logic in a script file and run it. Each confirmation costs the user time and a turn.

## The flow for every request

### 1. Understand
When starting or resuming a session, always look for an in-progress or paused handoff in `docs/handoffs/` (startup context lists it with a freshness check). Read it, then check it against `git log`, `git status` and the current branch: if work happened after its last update or it names another branch, tell the user what differs and refresh it before continuing. If the request comes from a GitHub issue ("issue #12", an issue URL), read it with its comments and use its acceptance criteria as the definition of done (`github-issues` skill).

Read the relevant code, tests and docs before proposing anything. **Ask whenever you have a real doubt** about scope, behaviour, design or risk, grouping all questions in one round; don't guess. Decide alone only purely conventional details, and say what you chose.

### 2. Map the impact
Before changing anything, list what the change touches beyond the obvious file: callers and dependants, tests, CLI help and usage text, README and `docs/` pages that describe the behaviour, `docs/architecture.md`, configuration and its examples, schemas and migrations, installer or setup steps, CI, translations. Search for the names you are changing (`grep` for the function, flag, setting or command) rather than relying on memory. Every affected item is updated in the same change or listed as pending; adding a mode to a CLI, for example, also means its `--help`, its validation, its tests and its usage docs. At lite this is a quick search; at standard and strict, put the list in the plan.

Aim for the **smallest change that does the job**: touch as few files and lines as possible, extend through the existing extension points (data files, interfaces, registries, configuration) instead of editing many call sites, and keep unrelated refactors out (note them as suggestions). If the smallest correct change still has to touch many files, that is a design signal: see step 3.

### 3. Check that the design still fits
While reading the code, look for signs that the architecture will not scale with this request or the project's growth: a change that needs edits in many places, files or functions with too many responsibilities, duplicated logic, dependencies pointing the wrong way, hard-coded variation that should be data, hot paths or data volumes the current design cannot handle. Don't restructure silently: tell the user what you found, its cost now and later, and the options (do the minimal change now, or refactor first), and ask. At strict, record an accepted architecture change as an ADR and update `docs/architecture.md`. Details: `references/design.md`.

### 4. Pick the level and plan
Apply the level from `tack mode`, or classify the task in `auto`. Plan as the table says: ordered steps, each ending in a commit; tests first; docs to update; risks and open questions. A strict plan that splits into independent parts also has a delegation section with file ownership and model/effort per task, as in `orchestrate`.

### 5. Branch
Check `git status` first so unrelated changes don't get mixed in, then branch: `feat/short-description`, `fix/…`, `refactor/…`, `docs/…`, `chore/…`.

### 6. Implement
At standard and strict, red → green → refactor for all logic with behaviour. At lite, add or update a test when logic changes. Keep code modular so future changes touch few files: SOLID and, where there's a real business domain, DDD; follow `references/conventions.md` and only the stack file you touch in `references/languages/`. Details: `references/tdd.md` and `references/design.md`.

### 7. Commit
Commit each coherent verified milestone immediately in Conventional Commits. Recommend an integration method from the branch history in the existing merge confirmation; preserve commits unless the user explicitly chooses squash. Details: `references/git-github.md`.

### 8. Document
Update everything on the impact list, plus what the level requires, following `project-docs`. When a committed change leaves docs pending in 3 or more files, delegate them to `docs-writer` (it runs on an economical model) with the diff range and the list of files; keep smaller updates, ADRs and design decisions yourself, and review its result before committing. Every enabled project should have `docs/architecture.md`; if it is missing, add it during the first strict task after reading the code.

### 9. Verify
Run the project's tests, linter, formatter and type checker. Re-run the impact search on the final diff to catch help text, docs or callers that still describe the old behaviour. Never say something works without having checked it; if something fails or couldn't run, say so clearly, with the output.

### 10. Close
Summarise briefly: what changed, the commits, what else the change affected and how it was covered, how it was verified and what's pending. Offer to push or open the PR where it applies. After a push, follow the CI row unless `tack config ci-watch` is `false`; the guard refuses `gh pr merge` while checks fail or are pending (`merge-requires-green`).

## Related skills and agents
Use them when the current tool has them:
- `new-project`: a project from scratch, or adding missing basics (tests, CI, lint, README).
- `debugging`: any bug, error, failing test or failing CI.
- `git-history`: fixing, combining or undoing commits; tidying history before a push.
- `testing`: how to write good tests in pytest, Pest/PHPUnit and Vitest/Jest (step 5).
- `release`: SemVer versioning, CHANGELOG, tags and GitHub Releases.
- `github-issues`: working from an issue, writing issues, splitting a plan into issues, recording bugs found along the way.
- `project-docs`: `docs/` structure, templates, technical sheet, architecture, plans, audits, handoffs and the AI usage log.
- `improve`: reviewing existing code or projects and proposing prioritised improvements; always asks scope and focus first.
- `orchestrate`: for explicit requests, or automatically for separable strict work; routes by complexity using available models and verifies the integrated result.
- `auto-improve`: only when the user asks for autonomous improvement; an evaluator scores the project and you lead agents until a target score, on its own branch.
- `lessons`: when the user corrects you or sets a lasting preference, save it as a rule.
- Stack skills when the task touches that layer: `frontend`, `api-design`, `database`, `auth`, `e2e-testing`, `deployment`, `observability`.
- Agent `planner`: for strict tasks that need a deep plan (step 4).
- Agent `code-reviewer`: as the level's review row says (between steps 9 and 10).
- Agent `docs-writer`: strict tasks whose change affects several documents (step 8).
- Agent `security-auditor`: before releases and after changes to auth, payments, file uploads or input handling.
- Agent `performance-analyzer`: when something is slow, or before launching something performance-sensitive.
- Agent `test-writer`: adding tests to existing untested code or before refactoring it. Not for new code: there you write the test first (TDD).

## General good practice
- Small, focused changes; don't slip unrelated refactors into a task (note them as suggestions).
- Names that express intent in the domain's language; short functions with one responsibility.
- Handle errors explicitly; never swallow exceptions silently.
- Never commit secrets (.env, keys, tokens); respect and extend `.gitignore`.
- Don't add dependencies without a reason; when you do, justify it in the commit or PR.
- Follow the style of the surrounding code over your own preferences.
- Secure by default: validate input at the boundaries, parameterised queries, least privilege.
