---
name: auto-improve
description: Autonomous improvement loop: an evaluator scores the project, you act as team lead delegating fixes to agents, then re-score, until the target score or a limit is reached; works on its own branch and never pushes. Use only when the user asks for it (autonomous mode, auto-improve, iterate until a target score).
---

# Auto-improve

You are the team lead. The `evaluator` agent scores the project; you turn its findings into tasks, delegate them, verify the result and repeat. The user gets a better project on a separate branch and a report showing how the score changed, and decides what to keep.

## 1. Set up (ask once, in one question round)
- **Scope and focus areas:** as in `improve`: whole project, a module, recent work or a screen; and which rubric dimensions (see `~/.agents/tack/agents/evaluator.md`).
- **Stop criteria**, proposing the defaults: overall score **≥ 8.0** with **no dimension under 6**; at most **5 iterations**; stop early if an iteration doesn't raise the overall score.
- **Model policy:** the evaluator runs on the most capable model; each task gets a model and effort by complexity (`orchestrate` table). The user confirms the policy once; don't ask again every round.
- Mention the cost: each iteration runs one evaluation plus several agents.

Then create the branch `improve/auto-YYYY-MM-DD` from an up-to-date main branch with a clean working tree, and start a handoff (`project-docs` → continuous handoffs).

## 2. The loop
For each iteration (1..max):
1. **Score:** run `evaluator` with the scope, the dimensions and the previous scorecard. Record the scorecard.
2. **Check the stop criteria.** Stop if they're met, if the limit is reached, or if the score didn't improve over the previous iteration (report why).
3. **Plan:** take the issues holding back the lowest dimensions first, and pick 3–5 tasks with the best impact for their effort. Each task is small, independent, with acceptance criteria and a regression test where it applies. Prefer fixes over rewrites.
4. **Delegate:** follow `orchestrate`: `implementer` for code (in isolated worktrees when tasks run in parallel), `test-writer` for missing tests, `docs-writer` for docs, each with the confirmed model policy. Do simple tasks yourself instead of delegating.
5. **Integrate and verify:** merge the task branches into the improve branch, then run the full test suite, lint and type checks; run `code-reviewer` on the iteration's diff and fix blocking findings. Revert any task that breaks the suite instead of patching around it.
6. **Record:** append the iteration to the report (score before → after, tasks done with commits, anything reverted) and update the handoff.

## 3. Rules
- Work only on the improve branch, with the user's workflow and conventions: TDD, Conventional Commits, docs. **Never push, merge, delete branches, or touch production, secrets or data.**
- Don't game the score: no deleting tests, no lowering lint rules, no disabling checks, and no docs that claim what the code doesn't do. The evaluator checks results, and you must too.
- Avoid risky changes the user hasn't approved: public API breaks, data migrations, dependency upgrades with breaking changes, large refactors. List them in the report as proposals instead.
- If two iterations in a row don't move the score, stop: the remaining issues likely need a human decision.

## 4. Report
Save `docs/audits/YYYY-MM-DD-auto-improve.md` on the branch:
- the scorecard per iteration (a table, dimension × iteration) and the final overall score;
- what changed, with commits;
- what was reverted or deliberately not done (proposals for the user);
- how to review: `git log main..improve/auto-YYYY-MM-DD`, then the commands to test.

Log the run in `docs/ai/log.md`, delete the handoff, and tell the user in a few lines: start → end score, iterations, the branch, and the open proposals. Offer to open a PR, after their OK.
