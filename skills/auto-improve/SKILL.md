---
name: auto-improve
description: Improve a project through bounded rounds of verified findings and fixes. Use only for an explicit request for autonomous improvement; respect scope and publication permission.
---

# Auto-improve

Find defects or costly friction, fix the most useful items, and verify the result. Scores are optional summaries when the user requests them; raising a score is not the objective.

## Agree on the bounds

Use the user's existing scope, priorities, authorization and budget. Ask only for missing decisions that materially change the work. If no round limit was given, use at most three rounds and state that limit. Define observable completion criteria, such as correcting reproduced failures or making documented setup work in a fresh clone.

Check the working tree and use a separate branch. Keep a plan or handoff in the configured project locations when work spans sessions. Explain model costs before extra paid runs; local tests do not require a new model budget.

## Each round

1. Inspect relevant code and docs. Reproduce suspected problems or cite concrete evidence. Separate verified findings, hypotheses and preferences.
2. Select a small coherent set of fixes within scope. Give each an observable expected result and a regression check when behavior changes. Prefer existing extension points to new machinery.
3. Implement and verify. Delegate only useful independent work when authorized by the active policy. A role definition does not require launching an agent.
4. Review the diff, run affected checks and broaden verification when project requirements or risk justify it. Do not repeat unchanged passing checks without a reason. Report checks that could not run.
5. Commit a verified milestone. Record what improved, the evidence, remaining findings and changed assumptions.

Stop when completion criteria hold, the round or budget limit is reached, a round yields no new actionable evidence, or further work requires an unresolved consequential decision. Do not create work just to fill another round.

## Constraints

- Keep protections, tests and meaningful lint rules. Do not hide failures, remove tests to improve a metric or claim behavior the code does not provide.
- Public API breaks, migrations and changes outside approved scope require a separate decision unless already authorized.
- Preserve unrelated work. Diagnose failures and repair or revert only your own changes when appropriate.
- Push, PR and merge actions require user authorization, which may already have been given. Do not ask again for authorized actions. Follow the project's CI and integration policy.

## Report

For a substantial audit, save `docs/audits/YYYY-MM-DD-auto-improve.md` or the project's established equivalent. Include findings before and after, commits, actual checks, deferred items and the reason for stopping. If scores were requested, use a stable rubric with evidence and state their subjective limits. Close or archive the plan and handoff when their work is complete.
