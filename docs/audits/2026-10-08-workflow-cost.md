# Workflow cost observations

The offline scan of the 48 coding transcripts from the [quality comparison](../benchmarks/2026-10-08-quality-efficiency.md) found:

| Condition | Sessions | Completed shell commands | Output characters | Commands mentioning checks | Workflow/context reads | Git write commands |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Plain | 16 | 62 | 45,399 | 9 | 17 | 0 |
| Current | 16 | 121 | 296,797 | 19 | 32 | 33 |
| Previous candidate | 16 | 111 | 296,562 | 21 | 35 | 34 |

Reproduce with `python3 evals/value.py --observe evals/out/quality-20261008/coding` when the ignored raw evidence is available. Categories overlap and use command-text patterns. Reading AGENTS.md counts as a context read even in plain. Output characters are not injected-context or billable tokens. These counts do not identify elapsed-time causes; missing per-stage timings remain unknown.

The large output/read difference supports testing a shorter workflow entrypoint and conditional detail. Git commits and useful checks also explain some extra actions but do not by themselves demonstrate value. Repeated checks may be justified by edits or red/green TDD; no success cache is introduced from these counts.

Implementation removes duplicated workflow prose, file-count risk escalation and unconditional strict AI logs/review agents. It retains task-specific tests, TDD, explicit project requirements and the existing safety hooks. The [value protocol](../../evals/value-protocol.md) compares this candidate with both plain and conventional project-only instructions before larger experiments.
