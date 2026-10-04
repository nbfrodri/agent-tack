---
name: dev-workflow
description: The user's engineering workflow for projects with harness enabled, scaled by workflow level (lite, standard, strict): planning, TDD, SOLID/DDD, code and git conventions (Conventional Commits, branches, PRs) and docs. Use whenever writing, changing or debugging code, committing or opening PRs in such projects (implement, fix, commit).
---

# Dev Workflow

Applies in projects where the harness is enabled (`harness status`; Claude Code says so at session start). Elsewhere, work normally without this ceremony unless the user asks for it.

The goal: every request ends as a small, tested change in a clean git history, with only as much process as the task deserves. It works the same with any assistant (Claude, Codex or another).

- **Language, attribution and what to ask before doing:** as in the global instructions; the git details are in `references/git-github.md`.
- **Code and git conventions:** `references/conventions.md` (style, naming, formatting, PR merging).
- **The project's own conventions win.** If the repo has its own CONTRIBUTING, AGENTS.md, CLAUDE.md, linter, commit format or folder structure, follow them over this guide. This skill fills the gaps; it doesn't override what exists.

## Workflow levels

`harness mode` sets the level: `auto` (the default) picks one per task; `lite`, `standard` or `strict` fix it for every task. A project setting overrides the user's global default (`harness mode --global`). The user can change the level for any task in conversation ("do this in strict").

In `auto`, classify each request before acting and state it in one line, for example `Level: standard (bounded bug fix in one module)`:
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
| Delegation | suggest and wait | suggest and wait | automatic after approval unless `harness.delegation` is `off` |

Every level keeps the hooks' guarantees (Conventional Commits, no AI attribution, no secrets, protected `main` and tags) and the rules on what to ask before doing.

## The flow for every request

### 1. Understand
If `docs/handoffs/` has an in-progress handoff for this branch or task, read it first and continue from there. If the request comes from a GitHub issue ("issue #12", an issue URL), read it with its comments and use its acceptance criteria as the definition of done (`github-issues` skill).

Read the relevant code, tests and docs before proposing anything. **Ask whenever you have a real doubt** about scope, behaviour, design or risk, grouping all questions in one round; don't guess. Decide alone only purely conventional details, and say what you chose.

### 2. Pick the level and plan
Apply the level from `harness mode`, or classify the task in `auto`. Plan as the table says: ordered steps, each ending in a commit; tests first; docs to update; risks and open questions. A strict plan that splits into independent parts also has a delegation section with file ownership and model/effort per task, as in `orchestrate`.

### 3. Branch
Check `git status` first so unrelated changes don't get mixed in, then branch: `feat/short-description`, `fix/…`, `refactor/…`, `docs/…`, `chore/…`.

### 4. Implement
At standard and strict, red → green → refactor for all logic with behaviour. At lite, add or update a test when logic changes. Design with SOLID and, where there's a real business domain, DDD; follow `references/conventions.md` and only the stack file you touch in `references/languages/`. Details: `references/tdd.md` and `references/design.md`.

### 5. Commit
Commit each coherent verified milestone immediately in Conventional Commits. Recommend an integration method from the branch history in the existing merge confirmation; preserve commits unless the user explicitly chooses squash. Details: `references/git-github.md`.

### 6. Document
As the level requires, following `project-docs`. Every enabled project should have `docs/architecture.md`; if it is missing, add it during the first strict task after reading the code.

### 7. Verify
Run the project's tests, linter, formatter and type checker. Never say something works without having checked it; if something fails or couldn't run, say so clearly, with the output.

### 8. Close
Summarise briefly: what changed, the commits, how it was verified and what's pending. Offer to push or open the PR where it applies.

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
- Agent `planner`: for strict tasks that need a deep plan (step 2).
- Agent `code-reviewer`: as the level's review row says (between steps 7 and 8).
- Agent `docs-writer`: strict tasks whose change affects several documents (step 6).
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
