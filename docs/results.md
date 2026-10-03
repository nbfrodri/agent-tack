# Results

What the harness changes in practice, measured on real sessions: the same tasks with and without it.

## Method
- **Scenarios:** create a small Python library from scratch (`new-project`), fix a reported bug (`bug-fix`), and prepare a release (`release`), with the same repo and prompt in both conditions.
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
