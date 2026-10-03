---
name: dev-workflow
description: The user's engineering workflow for projects with harness enabled: plan first, TDD, SOLID/DDD, code and git conventions (Conventional Commits, branches, PRs) and docs. Use whenever writing, changing or debugging code, committing or opening PRs in such projects (implement, fix, commit).
---

# Dev Workflow

Applies in projects where the harness is enabled (`harness status`; Claude Code says so at session start). Elsewhere, work normally without this ceremony unless the user asks for it.

The goal: every request ends as a small change that is tested, documented and recorded in a clean git history anyone can follow later. It works the same with any assistant (Claude, Codex or another).

- **Language, attribution and what to ask before doing:** as in the global instructions; the git details are in `references/git-github.md`.
- **Code and git conventions:** `references/conventions.md` (style, naming, formatting, PR merging).
- **The project's own conventions win.** If the repo has its own CONTRIBUTING, AGENTS.md, CLAUDE.md, linter, commit format or folder structure, follow them over this guide. This skill fills the gaps; it doesn't override what exists.

## The flow for every request

### 1. Understand
If `docs/handoffs/` has an in-progress handoff for this branch or task, read it first and continue from there. If the request comes from a GitHub issue ("issue #12", an issue URL), read it with its comments and use its acceptance criteria as the definition of done (`github-issues` skill).

Read the relevant code, tests and docs before proposing anything. If the request is ambiguous in a way that changes the result, ask, grouping all questions in one round. If there's a reasonable default, use it and say so.

### 2. Size the task
- **Trivial** (typo, rename, one-line tweak, a question): just do it, no formal plan.
- **Normal** (a bounded feature or bug): write a short plan and carry it out without waiting.
- **Large or risky** (several modules, architecture changes, data migrations, deleting things, public API changes, debatable design decisions): present the plan and **wait for the user's approval** before touching code. If the plan splits into independent parts, suggest delegating them to subagents (`orchestrate`, with its model and effort recommendation) as an option; never start it without the user's OK.

### 3. Plan
Short and concrete, using the tool's task or plan feature if there is one (TodoWrite, plan mode, update_plan…):
- the goal in one sentence and acceptance criteria ("done when…");
- ordered steps, each ending in a commit;
- which tests come first;
- which docs need updating;
- risks and open questions;
- for large plans that split into independent parts: an optional delegation section (subagents, with model and effort per task, as in `orchestrate`), offered to the user, never started without their OK.

For normal or large tasks, also create the task's handoff and keep it current at every milestone (`project-docs` → continuous handoffs), in case the session stops.

### 4. Branch
On `main`/`master`/`develop` with a non-trivial change, create a branch: `feat/short-description`, `fix/…`, `refactor/…`, `docs/…`, `chore/…`. Check `git status` first so unrelated changes don't get mixed in.

### 5. Implement with TDD
Red → green → refactor for all logic with behaviour: a test that fails for the right reason, the minimal code to pass it, then clean up. Design with SOLID and, where there's a real business domain, DDD. Write code following `references/conventions.md`. Be pragmatic: one-off scripts, config and prototypes don't need the full ceremony, but they still need some test or verification. Details: `references/tdd.md` and `references/design.md`.

### 6. Atomic commits
Commit each coherent verified milestone immediately, in Conventional Commits: tests plus the behavior they verify, a focused refactor, or related documentation. Do not wait for the task to finish before committing all its changes. Record milestone SHAs in the handoff. Recommend an integration method from the branch history and offer the user a choice in the existing merge confirmation; preserve commits unless the user explicitly chooses squash. Details: `references/git-github.md`.

### 7. Document
Simple, precise and concise docs for humans (`README`, `docs/`) and AIs (`AGENTS.md`), following `project-docs`. Save approved plans, relevant audits and, if the task is left unfinished, a handoff in `docs/`; add a row to `docs/ai/log.md` for each significant task. Go through the checklist in `references/documentation.md` before closing the task, and record significant architecture decisions as ADRs.

Every enabled project should have `docs/architecture.md`, linked from its README and documentation index. If it is missing in an existing project, add it during the first significant task after reading the code. Document the actual components, responsibilities, dependency direction and key flows; update it whenever those change. Use `project-docs` for the format.

### 8. Verify
Run the project's tests, linter, formatter and type checker. Never say something works without having checked it; if something fails or couldn't run, say so clearly, with the output.

### 9. Close
Summarise for the user: what changed, in which commits, how it was verified, which docs were updated, and what's pending or risky. Offer to push or open the PR where it applies.

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
- `orchestrate`: only when the user asks for subagents or parallel work; splits the plan among agents and asks model and effort per task.
- `auto-improve`: only when the user asks for autonomous improvement; an evaluator scores the project and you lead agents until a target score, on its own branch.
- `lessons`: when the user corrects you or sets a lasting preference, save it as a rule.
- Stack skills when the task touches that layer: `frontend`, `api-design`, `database`, `auth`, `e2e-testing`, `deployment`, `observability`.
- Agent `planner`: delegate the plan for normal or large tasks (step 3).
- Agent `code-reviewer`: review the diff before offering to push (between steps 8 and 9).
- Agent `docs-writer`: update docs (step 7) when a change affects several documents.
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
