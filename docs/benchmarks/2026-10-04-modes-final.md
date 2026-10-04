# Workflow modes benchmark

- Date: 2026-10-04. Frozen revision `93dc7ef` (branch `feat/config-feedback-robustness`); Claude Code 2.1.288; requested model `claude-sonnet-5-5`; private HOME and XDG paths per session; core install with `--skip-plugins` (no mods); metrics version 2.
- Sessions: `bug-fix` ×2 and `new-project` ×1 for baseline, lite, standard, strict and auto (15). One session (`bug-fix` strict-2) hit the usage limit and was rerun after the reset with the resumable launcher; no other retries.
- Prompts waive questions because sessions are non-interactive.

## bug-fix (2 runs per condition)

| Metric | Baseline | Auto | Lite | Standard | Strict |
| --- | --- | --- | --- | --- | --- |
| Commits (mean) | 0 | 1 | 1 | 1 | 1.5 |
| Conventional Commits | – | 100% | 100% | 100% | 100% |
| Worked on a branch | 0/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| `fix:` commit | 0/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| Regression test for the bug | 1/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| Tests pass | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| Plan written, `docs/`, AI log | – | – | – | – | 2/2 each |
| AI attribution in history | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| Duration (s) | 10.3 | 23.8 | 17.9 | 25.0 | 31.7 |
| Turns | 4.5 | 12.0 | 10.5 | 12.0 | 8.5 |
| Output tokens | 770 | 1778 | 1596 | 1984 | 2388 |
| Cost (USD) | 0.062 | 0.128 | 0.116 | 0.124 | 0.215 |

## new-project (1 run per condition)

| Metric | Baseline | Auto | Lite | Standard | Strict |
| --- | --- | --- | --- | --- | --- |
| Commits | 0 | 1 | 1 | 1 | 1 (plan only) |
| Worked on a branch | 0/1 | 1/1 | 1/1 | 1/1 | 1/1 |
| Tests pass (grader) | 0/1* | 1/1 | 1/1 | 1/1 | – (no code yet) |
| Tests | 7 (reported)* | 12 | 11 | 10 | – |
| README | 1/1 | 1/1 | 1/1 | 1/1 | 0/1 |
| Duration (s) | 12.9 | 56.1 | 49.8 | 50.1 | 27.0 |
| Turns | 3 | 12 | 16 | 16 | 7 |
| Cost (USD) | 0.087 | 0.190 | 0.208 | 0.196 | 0.137 |

\*Baseline reported 7 passing tests but declared no pytest dependency, so the grader's `uv run pytest` could not run them.

## Observations

- The pilot's regression is gone: every harness mode branched and committed a `fix:` with a regression test in `bug-fix`; baseline never committed or branched.
- Cost scales with the level: lite and auto cost about 1.9–2.1× baseline in `bug-fix`, strict 3.5× (it also writes a plan, docs and an AI log row). In `new-project`, auto costs 2.2× baseline; the earlier single workflow cost 6.6× there (different model and prompts, so indicative only).
- `auto` chose its level per task and landed at lite/standard cost.
- strict in `new-project` stopped after committing a written plan on a branch: its rule to wait for plan approval outweighed the prompt's "no questions". This is the designed behaviour for strict, but it means strict is unsuited to unattended creation tasks (use `unleash` for those).
- The Stop hook fired in 2 of 12 harness sessions (one uncommitted change each), adding one turn.
- Limits: two runs per condition at most, one model, Python scenarios, automatic grading; the numbers will vary.
