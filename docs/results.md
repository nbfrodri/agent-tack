# Results

What the harness changes in practice, measured on real sessions: the same tasks with and without it.

> **Model and tool.** The workflow-modes and lean benchmarks ran in Claude Code 2.1.288 with `claude-sonnet-5-5` (Claude Sonnet 5.5). The earlier single-workflow tables below used Claude Code's default model at the time, which was not recorded. Results depend on the model and the tool: another model (a different Claude model, GPT, DeepSeek, Qwen and others) or another AI tool can follow instructions more or less closely, take more or fewer turns and cost differently, so treat these numbers as one measurement, not a guarantee. Git hooks behave the same with any model; instruction-based rules vary.

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
- The Stop hook fired in 2 of 12 harness sessions, adding one turn each.

Limits: one or two runs per condition, one model, Python scenarios and automatic grading.

### Lean mode

A follow-up of 9 sessions compared `lean` with `lite` and the plain assistant ([details](benchmarks/2026-10-04-lean.md)). Lean cost the same as lite on a bug fix and about 10% less on a new project, with the same branch, commit and regression test. The startup context adds only about 7,000 input tokens; most of the overhead is the extra turns the discipline needs (branch, test run, commit) plus probing for the test command. Stating the test command in the project's `AGENTS.md`, or setting `harness config check-fast`, avoids that probing.

A 15-session [pilot](benchmarks/2026-10-04-modes-pilot.md) before these fixes is kept as evidence and is not a valid comparison; an earlier single-workflow comparison was superseded before completion ([attempt evidence](benchmarks/2026-10-04-bug-fix-attempts.json)). The sections below describe the earlier single-workflow harness.

## Historical method
- **Scenarios:** create a small Python library from scratch (`new-project`), fix a reported bug (`bug-fix`), and prepare a release (`release`), with the same repo and prompt in both conditions. A fourth scenario, `vague-requirement` ("make the cart faster and more robust"), checks whether measurable criteria come before code; it has no published results yet.
- **Conditions:**
  - *Harness*: the full setup, with the project enabled.
  - *Baseline*: Claude Code as shipped, without user settings, skills or instructions, and with a git config without the harness hooks.
  - Same tool, model and permissions in both.
- **Runs:** 2 repetitions per scenario and condition (12 sessions, 2026-10-03), graded automatically by `evals/grade.py` from each repo and transcript.
- **Prompt language:** the published runs used Spanish prompts. The runner now uses English prompts; rerun both conditions before comparing new measurements with these results.
- **Metric version:** these tables use the original grading heuristics. Version 2 fixes implementation-order false positives and distinguishes file order from evidence of a failing test followed by a passing test. Historical tables remain unchanged; rerun both conditions with the new grader before drawing updated conclusions.
- **Reproduce:** `evals/run.sh <scenario> <harness|baseline> <rep>`, then `evals/grade.py` and `evals/report.py` (see [development](development.md)).

## Key results
| Metric | Baseline | Harness |
| --- | --- | --- |
| Committed its work (runs) | 2/6 | 6/6 |
| Commits in Conventional Commits format | 100% (of the 3 made) | 100% (of the 31 made) |
| AI attribution left in history (runs) | 2/6 | 0/6 |
| Test written before the code (new project and bug fix) | 0/4 | 4/4 |
| Worked on a feature branch (new project and bug fix) | 0/4 | 4/4 |
| Tests passing at the end | 6/6 | 6/6 |
| Tests in the new project (mean) | 14 | 23.5 |
| New project ready for others: `AGENTS.md`, `docs/`, CI, issue templates, release setup | 0/2 | 2/2 |
| AI work logged in `docs/ai/log.md` (new project and release) | 0/4 | 4/4 |
| Pushed or bypassed hooks | 0/6 | 0/6 |

### Cost
| Scenario | Duration (s) | Turns | Cost* |
| --- | --- | --- | --- |
| Bug fix | 13 → 33 (2.5×) | 6 → 15 | $0.13 → $0.27 (2.1×) |
| Release | 37 → 56 (1.5×) | 12 → 15 | $0.18 → $0.31 (1.8×) |
| New project | 52 → 328 (6.3×) | 11 → 97 | $0.24 → $1.60 (6.6×) |

\*Estimated at API prices; on a subscription it counts towards usage instead.

## Reading the results
- **Process quality is where it changes most.** Without the harness the assistant left its work uncommitted in 4 of 6 runs, never wrote the test first and never used a branch. With it, every run was committed in small Conventional Commits on a branch, test first.
- **Attribution and history:** the plain assistant signed its release commits with an AI co-author; the harness never did.
- **Correctness was already good:** both conditions ended with passing tests and a correct release (0.2.0, CHANGELOG, annotated tag). The harness adds discipline and context rather than fixing broken code.
- **It costs more, by design:** about 2× for focused tasks and 6.6× for a new project, where it builds what the baseline skips: CI, docs for humans and AIs, templates, release automation, a plan and a handoff. Use `harness disable` for throwaway work.

## Limits
Two runs per condition and three Python scenarios: the direction is clear, but the exact numbers will vary. One tool and one model. Metrics are automatic checks on the repo and transcript, not a human review of code quality. The baseline still includes Claude Code's built-in behaviour.

## Full tables
### Scenario: bug-fix (2 runs per condition)

| Metric | Baseline | Harness |
| --- | --- | --- |
| Commits | 0.0 | 1.0 |
| Conventional Commits (%) | – | 100 |
| AI attribution in history | 0/2 | 0/2 |
| Tests pass | 2/2 | 2/2 |
| Tests | 3.0 | 3.0 |
| Test written before code | 0/2 | 2/2 |
| Wrote a plan | 0/2 | 0/2 |
| Worked on a branch | 0/2 | 2/2 |
| README | 2/2 | 2/2 |
| AGENTS.md | 0/2 | 0/2 |
| docs/ | 0/2 | 0/2 |
| AI work logged (docs/ai/log.md) | 0/2 | 0/2 |
| Handoff kept during the task | 0/2 | 0/2 |
| Regression test for the bug | 2/2 | 2/2 |
| fix: commit | 0/2 | 2/2 |
| Pushed or bypassed hooks | 0/2 | 0/2 |
| Duration (s) | 12.9 | 32.8 |
| Turns | 6.0 | 15.0 |
| Output tokens | 1223 | 3012 |
| Cost (USD) | 0.1295 | 0.2715 |

### Scenario: new-project (2 runs per condition)

| Metric | Baseline | Harness |
| --- | --- | --- |
| Commits | 0.0 | 12.0 |
| Conventional Commits (%) | – | 100 |
| AI attribution in history | 0/2 | 0/2 |
| Tests pass | 2/2 | 2/2 |
| Tests | 14.0 | 23.5 |
| Test written before code | 0/2 | 2/2 |
| Wrote a plan | 0/2 | 1/2 |
| Worked on a branch | 0/2 | 2/2 |
| README | 2/2 | 2/2 |
| AGENTS.md | 0/2 | 2/2 |
| docs/ | 0/2 | 2/2 |
| AI work logged (docs/ai/log.md) | 0/2 | 2/2 |
| Handoff kept during the task | 0/2 | 2/2 |
| Pushed or bypassed hooks | 0/2 | 0/2 |
| Duration (s) | 51.7 | 328 |
| Turns | 11.0 | 96.5 |
| Output tokens | 5994 | 27628 |
| Cost (USD) | 0.2409 | 1.6 |

### Scenario: release (2 runs per condition)

| Metric | Baseline | Harness |
| --- | --- | --- |
| Commits | 1.5 | 2.5 |
| Conventional Commits (%) | 100 | 100 |
| AI attribution in history | 2/2 | 0/2 |
| Tests pass | 2/2 | 2/2 |
| Tests | 3.0 | 5.0 |
| Wrote a plan | 0/2 | 0/2 |
| Worked on a branch | 0/2 | 0/2 |
| README | 2/2 | 2/2 |
| AGENTS.md | 0/2 | 0/2 |
| docs/ | 0/2 | 2/2 |
| AI work logged (docs/ai/log.md) | 0/2 | 2/2 |
| Handoff kept during the task | 0/2 | 0/2 |
| Version bumped to 0.2.0 | 2/2 | 2/2 |
| CHANGELOG updated | 2/2 | 2/2 |
| Annotated v0.2.0 tag | 2/2 | 2/2 |
| Pushed or bypassed hooks | 0/2 | 0/2 |
| Duration (s) | 37.1 | 55.5 |
| Turns | 12.0 | 15.0 |
| Output tokens | 3030 | 4208 |
| Cost (USD) | 0.1770 | 0.3132 |
