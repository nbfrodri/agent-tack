---
name: orchestrate
description: Delegate complex separable tasks using available models and isolated worktrees, then integrate and verify. Use for subagents or parallel work, or automatically for complex independent strict-level tasks in enabled projects unless harness.delegation is off.
---

# Orchestrate

You plan, delegate, integrate and verify. Delegation pays off when a complex task splits into independent parts with clear file ownership, or needs substantial independent research. Keep small or tightly coupled work direct: extra agents consume tokens and require integration.

## 1. Check mode, plan and split

In an enabled project, automatic delegation applies only to tasks at the strict workflow level (`dev-workflow`); at lite and standard, suggest it and wait for approval. Then read `git config --get harness.delegation`: absent or `auto` allows automatic delegation; `off` disables it. Treat any other value as off and explain the invalid setting. Outside enabled projects, suggest delegation and wait for approval unless the user requested it. An explicit request for subagents authorises delegation for that task even when automatic mode is off.

- Follow the approved scope and planning requirements in `dev-workflow`. Automatic delegation does not authorise an unapproved large or risky implementation plan.
- After the plan is approved, automatically delegate complex separable work in auto mode. Show the task, owner, files, model, effort and reason in a concise progress update; do not ask again for delegation approval.
- Give each task acceptance criteria and clear contracts: shared types, API shapes, function signatures and file ownership. Each file has one owner.
- Independent tasks may run in parallel; dependent tasks wait for their prerequisites. Establish shared contracts first.
- Prefer two or three workers and stay within the runtime's concurrency limit. Delegate only when the expected benefit justifies the added token and integration cost.
- In off mode, work directly; if delegation would help substantially, suggest it and wait for approval. Respect explicit cost limits or model preferences.

### Model and effort per task

Inspect the current tool's actual model and reasoning controls before choosing. Use available capabilities, not hardcoded provider names or assumptions about a product. Apply these recommendations automatically in auto mode, unless the user specified another policy:

| Task complexity | Examples | Model capability | Effort |
| --- | --- | --- | --- |
| Low: mechanical, well specified | Docs, renames, fixtures, collecting information | Fast economical model that supports the task | low |
| Medium: standard implementation | A feature following existing patterns, tests, typical bug fixes | Balanced coding model | medium |
| High: design-heavy or risky | Architecture, security, migrations, tricky bugs, integration | Most capable suitable model available | high |

Bump the recommendation for unclear requirements, missing tests or costly mistakes. If the runtime exposes no model choice, inherit the available model. If a model or effort cannot be set, report the actual fallback; do not claim a selection was applied. Do not rewrite shared agent definitions just to change one invocation's effort. Ask only when an unresolved choice materially affects the approved budget or scope.

Record actual models, effort settings, fallbacks, branches/worktrees and task status in the orchestration handoff and `docs/ai/log.md`. Keep the handoff current as agents report so work can resume after interruption.

## 2. Delegate
Pick the agent for each task:
| Task | Agent |
| --- | --- |
| Implement a feature slice, fix or refactor | `implementer` (in its own worktree) |
| Add tests to existing code | `test-writer` (in its own worktree) |
| Docs | `docs-writer` |
| Research, read-only analysis | `architecture-reviewer`, `security-auditor`, `performance-analyzer`, `ui-reviewer`, or a general-purpose/Explore agent |

Every implementing agent works in its own Git worktree and branch `type/<slug>`. Use native worktree isolation when supported; otherwise create the worktree before delegation and explicitly pass its path. Shared working directories require disjoint read-only tasks; do not run overlapping writers. Worktrees created inside the repository (such as `.claude/worktrees/`) must be in `.gitignore` before delegating, and the integrating agent stages explicit paths rather than `git add -A`. Tell each agent which branch to start from and give it the approved plan's path.

Regardless of whether the tool inherits conversation context, make each task prompt self-contained:
- the goal and the acceptance criteria of its task;
- the contract it must respect and the files it owns (and must not touch);
- the relevant skills to follow (e.g. `api-design` + `database` for a backend slice) and the project's `AGENTS.md`;
- the expected output: commits on its branch, tests passing, and a short report (what was done, files, commits, open issues).

## 3. Integrate and verify
1. When each agent reports, read its report and check its branch: diff, commits (Conventional Commits) and tests.
2. Integrate local task commits in dependency order, resolving conflicts yourself. Run affected checks after each integration and the full required suite once the combined change is ready. Preserve verified milestones and follow the contextual merge choice for PR integration.
3. Run `code-reviewer` on the integrated diff, and the specialist reviewers if the change touches their area (auth → `security-auditor`, UI → `ui-reviewer`).
4. Fix what they find (directly, or with another agent round), then update docs (`project-docs`) and log the multi-agent work in `docs/ai/log.md`.
5. Report to the user: what each agent did, the integrated result, how it was verified, and anything pending. Push or open a PR only after asking, as always.

If an agent fails or goes off track, don't merge its work blindly: inspect it, then retry with a clearer prompt, do it yourself, or drop it.

## Tools without subagents

Check runtime capabilities rather than assuming that a named product supports or lacks subagents. If delegation is unavailable, carry out the same plan sequentially with the same contracts and checks. Explain the fallback and record the actual model; never imply that background agents or model switching occurred when they did not.
