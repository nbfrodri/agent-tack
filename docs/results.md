# Results

What tack changes in practice, measured on real sessions: the same tasks with and without it.

> **Model and tool.** The outcome, workflow-modes and lean benchmarks ran in Claude Code 2.1.288 with `claude-sonnet-5-5` (Claude Sonnet 5.5). Results depend on the model and the tool: another model (a different Claude model, GPT, DeepSeek, Qwen and others) or another AI tool can follow instructions more or less closely, take more or fewer turns and cost differently, so treat these numbers as one measurement, not a guarantee. Git hooks behave the same with any model; instruction-based rules vary.

## Security-sensitive input (2026-10-06)

The first scenario where tack changed the outcome, with the smaller model ([details](benchmarks/2026-10-06-attachments.md)): reading a user's attachment by a name taken from a URL, with seven hidden tests on the feature and the path traversal traps.

| All 7 hidden tests pass | Baseline | Auto | Auto, risk rule (#119) |
| --- | --- | --- | --- |
| `claude-haiku-4-5` (5 runs each) | 0/5 (mean 4.6 of 7) | 2/5 (6.0) | 4/5 (6.4) |
| `claude-opus-5-5` (2 runs each) | 2/2 | 2/2 | – |
| Cost, Haiku (mean) | $0.058 (1×) | $0.070 (1.2×) | $0.086 (1.5×) |

The larger model got it right without tack; the smaller one did not, and tack's process (a level picked by risk, tests first, review) closed most of the gap. Five runs per condition: a first signal, not a measured effect size.

## Conventions (2026-10-06)

A feature in a project whose `AGENTS.md` sets rules the prompt does not repeat, with eight hidden tests on the feature and those rules ([details](benchmarks/2026-10-06-conventions.md)). Claude Code 2.1.290 with `claude-opus-5-5`, two runs each.

| | Baseline | Auto |
| --- | --- | --- |
| Hidden acceptance tests all pass | 2/2 | 2/2 |
| Branch and Conventional Commit | 0/2 | 2/2 |
| Cost (mean) | $0.154 (1×) | $0.259 (1.7×) |

Claude Code kept the project's conventions without tack; tack again changed the process, not the outcome.

## Outcomes (2026-10-05)

Process compliance is not quality, so the evals now also run hidden acceptance tests the agent never sees, and `evals/outcomes.py` reads defects from git history ([benchmark](benchmarks/2026-10-05-outcomes.md), [what each step caught](benchmarks/2026-10-05-step-value.md)).

| Outcome (8 sessions, `claude-sonnet-5-5`) | Baseline | Auto |
| --- | --- | --- |
| bug-fix: hidden acceptance tests all pass (5 tests) | 2/2 | 2/2 |
| new-project: hidden acceptance tests all pass (6 tests) | 2/2 | 2/2 |
| Branch and commit | 0/4 | 4/4 |
| Cost (mean) | $0.05 (1×) | $0.13–0.18 (2.6–3.3×) |

- On these small tasks the plain assistant's code was already correct: tack changed the process, not the outcome. Harder scenarios are needed before claiming a quality gain or ruling one out.
- In this repository (`main` at `fa069ff`), 14 of 103 features (14%) needed a `fix:` after reaching `main`, linked by the lines the fix changed; 16 fixes landed on the feature's own branch before its merge, after review or CI.

Limits: two runs per condition, one model, two Python scenarios; the history covers one repository and three days.

## Workflow modes (2026-10-04)

15 sessions on revision `93dc7ef`: `bug-fix` twice and `new-project` once for the plain assistant (baseline) and each mode, with Claude Code 2.1.288 and `claude-sonnet-5-5`. [Full tables and method](benchmarks/2026-10-04-modes-final.md).

| bug-fix (2 runs each) | Baseline | Lite | Auto | Standard | Strict |
| --- | --- | --- | --- | --- | --- |
| Branch and `fix:` commit | 0/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| Regression test | 1/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| Tests pass | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| Plan, docs and AI log | – | – | – | – | 2/2 |
| Cost | $0.062 (1×) | $0.116 (1.9×) | $0.128 (2.1×) | $0.124 (2.0×) | $0.215 (3.5×) |
| Duration | 10 s | 18 s | 24 s | 25 s | 32 s |

| new-project (1 run each) | Baseline | Lite | Auto | Standard | Strict |
| --- | --- | --- | --- | --- | --- |
| Branch and commit | 0/1 | 1/1 | 1/1 | 1/1 | plan only |
| Tests | 7, not runnable by the grader | 11 pass | 12 pass | 10 pass | – |
| Cost | $0.087 (1×) | $0.208 (2.4×) | $0.190 (2.2×) | $0.196 (2.3×) | $0.137 |

**Reading it:**
- Every mode kept the discipline the plain assistant skips: a branch, a `fix:` Conventional Commit and a regression test. Correctness was the same.
- Lighter modes cost about 2× baseline; strict costs 3.5× in a bug fix because it also writes a plan, docs and an AI log row. `auto` picked its level per task and landed at lite or standard cost.
- A new project in `auto` cost 2.2× baseline; the earlier single workflow cost 6.6× there (different model and prompts, so indicative only).
- strict stopped a new project after committing its plan, waiting for approval as designed: use `unleash` for unattended work.
- The Stop hook fired in 2 of 12 sessions with tack, adding one turn each.

Limits: one or two runs per condition, one model, Python scenarios and automatic grading.

### Lean mode

A follow-up of 9 sessions compared `lean` with `lite` and the plain assistant ([details](benchmarks/2026-10-04-lean.md)). Lean cost the same as lite on a bug fix and about 10% less on a new project, with the same branch, commit and regression test. The startup context adds only about 7,000 input tokens; most of the overhead is the extra turns the discipline needs (branch, test run, commit) plus probing for the test command. Stating the test command in the project's `AGENTS.md`, or setting `tack config check-fast`, avoids that probing.

A 15-session [pilot](benchmarks/2026-10-04-modes-pilot.md) before these fixes is kept as evidence and is not a valid comparison; an earlier single-workflow comparison was superseded before completion ([attempt evidence](benchmarks/2026-10-04-bug-fix-attempts.json)).

## Earlier single-workflow comparison (2026-10-03)

Twelve sessions compared the first, single workflow with the plain assistant on a new project, a bug fix and a release ([full tables and method](benchmarks/2026-10-03-single-workflow.md)). With tack the assistant committed its work in 6 of 6 runs (2 of 6 without), wrote the test first and used a branch in 4 of 4 (0 of 4 without) and never left AI attribution (2 of 6 without); tests passed in every run of both. It cost about 2× on focused tasks and 6.6× on a new project, where it also built CI, docs, templates and release setup. Two runs per condition and an unrecorded model: read it as direction, not exact numbers.
