# Results

What tack changes in practice, measured on real sessions: the same tasks with and without it.

> **Model and tool.** The workflow-modes and lean benchmarks ran in Claude Code 2.1.288 with `claude-sonnet-5-5` (Claude Sonnet 5.5). Results depend on the model and the tool: another model (a different Claude model, GPT, DeepSeek, Qwen and others) or another AI tool can follow instructions more or less closely, take more or fewer turns and cost differently, so treat these numbers as one measurement, not a guarantee. Git hooks behave the same with any model; instruction-based rules vary.

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
