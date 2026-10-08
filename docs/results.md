# Results

What tack changes in practice, measured on real sessions: matched tasks with and without tack, or between versions.

## Value-first preflight (2026-10-08)

A shorter workflow completed eight implementation sessions and two independent blind reviews. It was **59.0% slower and used 41.5% more input tokens** than current tack on these two tasks. A conventional project-only AGENTS.md produced the best settings implementation; shipment quality tied across all four conditions. Review found real settings defects that the original passing checks missed. The larger proposed screen was stopped at its evidence gate; no general productivity gain is claimed. [Full results, supplemental probes and decisions](benchmarks/2026-10-08-value-first.md).

## Backend/frontend integration pilot (2026-10-08)

Four fresh Codex sessions compared a backend/consumer pair on the previous and team-coordination versions. **Both passed 7/7 cross-language integration checks; the candidate took 5.5% longer.** Both wrote useful tests and understood the branch dependency. The pilot exposed an unrelated-handoff completion reminder, now covered by a regression and corrected for team projects. [Protocol, all attempts, code review and limits](benchmarks/2026-10-08-teamwork.md). This small two-version comparison does not establish a productivity or quality gain and is not pooled with earlier batches.

## Minimal requests and independent code review (2026-10-08)

The latest comparison completed **93 sessions**: 5 pilot, 48 coding, 32 blind reviews and 8 setups. Plain projects received ordinary product requests without custom instructions to write tests, use TDD/SOLID or follow a Git workflow. GPT-6 Luna and GPT-6.1 Sol each solved four tasks twice with plain projects, current tack and a frozen candidate. Two fresh GPT-6 Astra reviews scored each anonymous triplet; the orchestrator inspected every delivery and saved its assessment before labels were revealed.

The candidate passed 16/16 frozen acceptance checks; current tack and plain projects each passed 15/16. This small difference does not establish a quality advantage: plain projects had slightly higher mean blind grades, and review found additional defects in every condition. Luna's tests rejected the original defect in **8/8 runs with either tack version, versus 1/8 without tack**. Sol already did so in every condition. All selected settings transferred in all eight setups, with local trust kept private. No recorded red/green sequence demonstrated TDD in this batch.

The speed targets were missed. Candidate coding time changed by **+7.7% for Luna and -1.6% for Sol** versus current tack; setup took **11.7% and 12.8% longer**. Compared with plain projects, candidate coding took 1.86x and 1.40x the time. Keep the new atomic configuration flow for explicit, validated choices, without claiming a measured speed gain. [Protocol, all attempts, code-quality grades, source findings and limitations](benchmarks/2026-10-08-quality-efficiency.md).

## Project adoption comparison (2026-10-08)

The new shared-configuration/verifier version completed eight three-session journeys: setup, a second clone's bug fix and a feature. The baseline received the same useful project instructions and engineering requirements. **Both conditions passed 8/8 code tasks and caught 12/12 injected faults with their tests.** All 24 sessions completed, with red/green evidence in every code task.

Shared mode, context paths and reply style transferred in all four tack journeys; trust remained local. Luna omitted an explicit shared Conventional Commit value in both runs and inherited the current default, an adoption gap. Tack took **2.11x total session time with Luna and 1.96x with Sol**; excluding setup, the ratios were 1.80x and 1.71x. Input-token ratios were 3.19x and 2.33x, with most input cached. No code-quality or productivity advantage was established on this small synthetic fixture. [Protocol, detailed results, code review and all-run facts](benchmarks/2026-10-08-adoption.md).

## Codex subscription comparison (2026-10-08)

GPT-6 Luna and GPT-6.1 Sol, medium effort, Codex CLI 0.160.1: **24/24 runs pass the hidden acceptance tests**, with two runs per model/condition on bug-fix, attachments and search. There is no acceptance gain in this sample. tack adds regression tests to Luna's outputs and branch/commit discipline to both models; Sol already writes useful tests without it. A separate review/probe found Unicode search failures in both Luna auto runs that the original ASCII-focused hidden tests miss.

For the fixed three-task mix, auto uses 4.54x input tokens and 2.27x session time with Luna; 3.49x input and 2.38x time with Sol. Most input is cached. These are subscription token/time observations, not dollar charges. [Full tables, all-run facts, code-quality review and qualification limitations](benchmarks/2026-10-08-codex.md). The small samples, post-hoc review and incomplete first-pilot archive are explicit; results are not pooled with historical Claude runs.

## Context reduction and new measurement support (2026-10-07)

The 19 shipped skill descriptions were shortened from 4,879 to 3,038 characters (37.7%). Purposes and activation boundaries remain; installed groups, safety controls and the 23 configuration options keep their existing behavior. This measures description characters, not tokens or monetary savings. The [component decision record](audits/2026-10-07-capability-simplification.md) explains why no component was removed without usage evidence.

The runner now isolates both conditions, preserves prior outputs and records comparison fingerprints. Bounded batch manifests and JavaScript/fresh-session capability scenarios are available. Their automated tests validate the infrastructure; no new paid-model outcome comparison is claimed here. The historical tables below retain their original method and limitations and are not pooled with metric version 3.

> **Model and tool.** The outcome, workflow-modes and lean benchmarks ran in Claude Code 2.1.288 with `claude-sonnet-5-5` (Claude Sonnet 5.5). Results depend on the model and the tool: another model (a different Claude model, GPT, DeepSeek, Qwen and others) or another AI tool can follow instructions more or less closely, take more or fewer turns and cost differently, so treat these numbers as one measurement, not a guarantee. Git hooks behave the same with any model; instruction-based rules vary.

## Security-sensitive input (2026-10-06)

The first scenario where tack changed the outcome, with the smaller model ([details](benchmarks/2026-10-06-attachments.md)): reading a user's attachment by a name taken from a URL, with seven hidden tests on the feature and the path traversal traps.

| All 7 hidden tests pass | Baseline | Auto | Auto, risk rule (#119) |
| --- | --- | --- | --- |
| `claude-haiku-4-5` (5 runs each) | 0/5 (mean 4.6 of 7) | 2/5 (6.0) | 4/5 (6.4) |
| `claude-opus-5-5` (2 runs each) | 2/2 | 2/2 | – |
| Cost, Haiku (mean) | $0.058 (1×) | $0.070 (1.2×) | $0.086 (1.5×) |

The larger model got it right without tack; the smaller one did not, and tack's process (a level picked by risk, tests first, review) closed most of the gap. Five runs per condition: a first signal, not a measured effect size.

A second hidden-risk scenario did not repeat the gain ([details](benchmarks/2026-10-06-search.md)): in a product search on what the user types, all 15 Haiku runs, with tack or without, avoided SQL injection and missed the `LIKE` wildcards (6 of 8 hidden tests). tack helps the model test what it thinks of, not what it does not know; asking auto for a `security-auditor` review changed nothing, as Haiku never called the agent.

### The smaller model on every scenario

`claude-haiku-4-5`, same day and tack revision (main plus the open pull requests):

| Scenario (runs each) | Hidden tests all pass: baseline | auto | Branch: baseline | auto | Cost |
| --- | --- | --- | --- | --- | --- |
| attachments (5) | 0/5 | 4/5 with the risk rule (5/5 in a later batch) | 0/5 | 5/5 | 1.5× |
| search (5) | 0/5 | 0/5 | 0/5 | 5/5 | 1.9× |
| bug-fix (5) | 5/5 | 5/5 | 0/5 | 5/5 | 1.13× |
| new-project (5) | 5/5 | 5/5 | – | – | 1.46× |
| conventions (2) | 2/2 | 2/2 | 0/2 | 2/2 | 1.4× |

In new-project, 5 of 10 runs (both conditions) created the package in a `cart/` subfolder although the prompt asks for this directory; their code passed every hidden test once found there, so the table counts code correctness. tack's gain is where the task hides a risk the prompt does not spell out; on plain tasks it changes the process at a modest cost.

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
