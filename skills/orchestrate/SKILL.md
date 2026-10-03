---
name: orchestrate
description: Split an approved plan among subagents in isolated worktrees, recommending model and effort per task, then integrate, test and review. Use when the user asks for subagents or parallel work (use subagents, work in parallel, orchestrate this); for large divisible tasks, only suggest it.
---

# Orchestrate

You become the orchestrator: you plan, delegate, integrate and verify, and the subagents do the focused work. This pays off when a task splits into parts that are **independent** (different modules, layers or files) or that need a lot of reading, since each subagent has its own context. It costs more tokens and adds integration work, so it runs only when the user asks for it; for a large task that splits into independent parts you may suggest it, showing the breakdown and the model and effort table, and wait for a yes. If the task is small or tightly coupled, say so and suggest doing it directly.

## 1. Plan and split
- Start from an approved plan (`dev-workflow`; the `planner` agent can produce it). If there isn't one, make it first and get approval.
- Split it into tasks that can be done and tested on their own, with **clear contracts** between them: shared types, API shapes, function signatures and file ownership. Each file has one owner, so no two agents edit the same file.
- Decide the order: independent tasks run in parallel; dependent ones wait for what they need. Shared groundwork, such as types, the contract or a migration, is usually done first by you or by one agent.
- 2 to 5 agents in parallel is a sensible maximum; more means more conflicts and more cost.
- Show the user the breakdown (task → agent → files → order), together with the model and effort question below, and wait for their OK.

### Model and effort per task
Always ask the user which model and effort to use for the subagents, **recommending one per task** based on its complexity, in a single question round (a table plus the choice "accept the recommendation / use the most capable model for everything / use the cheapest that fits / adjust per task"):

| Task complexity | Examples | Recommended model | Effort |
| --- | --- | --- | --- |
| Low: mechanical, well specified | Docs updates, renames, boilerplate, adding fixtures, searching or collecting information | Haiku (fast and cheap) | low |
| Medium: standard implementation | A feature slice following existing patterns, tests for existing code, a typical bug fix | Sonnet | medium |
| High: design-heavy or risky | Architecture, tricky bugs, concurrency, security, data migrations, unfamiliar code, integrating others' work | The most capable model available (Opus or newer) | high |

Explain each recommendation in a few words ("touches auth, so high"). Bump one level up for code with no tests, unclear requirements or high cost of mistakes.

How it applies:
- **Model:** pass it per delegation (the `model` parameter of the Agent tool in Claude Code).
- **Effort:** in Claude Code it can't be set per delegation; it comes from the agent definition's `effort:` field (`low`, `medium`, `high`, `xhigh`, `max`; absent means the session's effort). If the chosen effort differs from the agent's, tell the user and offer to set it in that agent's file (it then becomes that agent's default) or to proceed with the agent's current effort. Never claim an effort was applied when it wasn't.
- Record the chosen model and effort per task in the orchestration handoff and in `docs/ai/log.md`.
- Keep a handoff for the whole orchestration (`project-docs` → continuous handoffs) listing each task, its agent, branch or worktree, and status (pending, running, done, merged). Update it as agents report, so the work can be resumed if the session stops.

## 2. Delegate
Pick the agent for each task:
| Task | Agent |
| --- | --- |
| Implement a feature slice, fix or refactor | `implementer` (in its own worktree) |
| Add tests to existing code | `test-writer` (in its own worktree) |
| Docs | `docs-writer` |
| Research, read-only analysis | `architecture-reviewer`, `security-auditor`, `performance-analyzer`, `ui-reviewer`, or a general-purpose/Explore agent |

Every implementing agent runs **isolated in its own git worktree** (`isolation: "worktree"` in Claude Code), on its own branch `type/<slug>`, so parallel agents never step on each other.

Each agent starts with no context, so its prompt must be self-contained:
- the goal and the acceptance criteria of its task;
- the contract it must respect and the files it owns (and must not touch);
- the relevant skills to follow (e.g. `api-design` + `database` for a backend slice) and the project's `AGENTS.md`;
- the expected output: commits on its branch, tests passing, and a short report (what was done, files, commits, open issues).

## 3. Integrate and verify
1. When each agent reports, read its report and check its branch: diff, commits (Conventional Commits) and tests.
2. Merge the branches into the integration branch in dependency order, resolving conflicts yourself. Run the **full** test suite, lint and type checks after each merge.
3. Run `code-reviewer` on the integrated diff, and the specialist reviewers if the change touches their area (auth → `security-auditor`, UI → `ui-reviewer`).
4. Fix what they find (directly, or with another agent round), then update docs (`project-docs`) and log the multi-agent work in `docs/ai/log.md`.
5. Report to the user: what each agent did, the integrated result, how it was verified, and anything pending. Push or open a PR only after asking, as always.

If an agent fails or goes off track, don't merge its work blindly: inspect it, then retry with a clearer prompt, do it yourself, or drop it.

## Tools without subagents
Codex and other tools without subagents follow the same plan sequentially: one task at a time, on its own branch, with the same contracts and the same integration checks. The model and effort recommendation still applies; the user switches them in that tool (e.g. Codex's model and reasoning-effort settings) between tasks.
