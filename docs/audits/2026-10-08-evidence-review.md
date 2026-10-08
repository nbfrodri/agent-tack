# Audit round 8: Windows support and Codex outcomes

This is a judgment against #100's existing eight-dimension rubric, supported by the changes and measurements below. Scores are not an independent certification. All child issues #88-#99 are closed and the parent checklist now reflects that. #111 is fixed and closed by [PR #129](https://github.com/nbfrodri/agent-tack/pull/129); #100 remains open because neither its average target nor every-dimension target is met.

| Dimension | Round 7 | Round 8 | Evidence / remaining limitation |
| --- | --- | --- | --- |
| Correctness and tests | 9 | 9 | All five CI jobs passed for #129; local 22-suite verification and native Windows regression coverage. Successful example benchmarks do not prove arbitrary task correctness. |
| Safety | 9 | 9 | Ownership path/ACL validation and original-state restoration now work natively on Windows, with refusal/preservation tests. Model instructions still provide weaker guarantees than executable checks. |
| Maintainability and simplicity | 8.5 | 8.5 | Platform behavior isolated in shared helpers; descriptions shortened and capability policy shared. The generated plan/log overhead in the new comparison argues against declaring simplicity solved. |
| Portability | 8 | 9 | Native Windows CI: 11 ownership tests, no skips; 19 smoke checks covering install/reinstall/doctor/uninstall and restoration. Native sessions in every supported editor remain unmeasured. |
| Documentation | 9.5 | 9.5 | Protocol, public per-run diffs/counters, supplementary quality review and negative results are published, including the incomplete first-pilot archive. |
| Onboarding and UX | 9 | 9 | Guided optional setup, reusable choices and reply styles shipped in #128. Repeated setup discovery during focused Codex tasks remains a friction/cost candidate. |
| Performance and cost | 8 | 7.5 | In the fixed Codex task mix, auto takes 2.27x/2.38x session time and 4.54x/3.49x input tokens for Luna/Sol, without an acceptance gain. Cached input and subscription billing prevent interpreting token ratios as dollar ratios. |
| Evidence of value | 8 | 8 | Historical Haiku security gains remain evidence. New Codex runs broaden coverage but show acceptance parity and a supplementary Unicode regression; stronger general quality claims are not justified. |
| **Average** | **8.625** | **8.6875** | **About 8.69/10; target not reached.** |

The performance score reduction reflects newly exposed overhead, not a measured regression against an earlier Codex version: there was no compatible earlier Codex cohort. See [full benchmark](../benchmarks/2026-10-08-codex.md) and [artifact review](../benchmarks/2026-10-08-codex-quality.md). The latter's task-specific code scores are separate from this harness audit.

## Product direction after these results

The owner wants a harness that adds significant value, not ceremony. Three viable directions have different promises:

| Direction | Benefit | Limitation |
| --- | --- | --- |
| Portable configuration and safeguards | Predictable cross-tool setup and configuration preservation | Useful infrastructure, but does not itself establish better generated code |
| Mandatory workflow orchestration | More consistent tests, branches, commits and documentation | Current Codex evidence shows substantial overhead and no acceptance advantage |
| Project-aware verification with minimal default guidance | Reuse real project checks to catch concrete mistakes, retaining evidence for each result | Requires incremental routing, trustworthy command selection and stronger evaluations before claiming success |

Recommend the third direction, retaining the first as the foundation. This is a proposed direction, not a claim that it is implemented or effective:

1. Measure and remove redundant discovery on already configured tasks. Supply one compact context containing relevant conventions and known checks; avoid repeated onboarding, generic skill loading and process documents when no concrete task need exists. Preserve existing optional setup choices and safeguards.
2. Select verification from changed files and project configuration: existing tests, type checks, lint, API/schema checks and project-specific invariants. Reuse proven tools; do not invent a universal checker. Missing mappings are reported as gaps, never as a passing check. Cache results only while checked inputs remain unchanged. Respect trust boundaries for repository commands.
3. Create a skill only for a reusable project procedure that current instructions cannot express well; invoke a specialist only for a concrete review question and supported delegation scope. Measure defects found versus added latency, rather than rewarding agent count.
4. Evaluate the thin variant against plain Codex and current tack on held-out real repository tasks, with acceptance criteria fixed before execution. Review code independently and blind where feasible; count actual defects, useful regression tests, maintainability, human interventions, token usage and end-to-end time. Explicitly test Unicode, encoding and filesystem assumptions without retroactively changing this published batch.

Proposed decision gates for that experiment: no added critical defects; demonstrate fewer faulty deliveries on difficult tasks; keep easy-task median time within 15% of baseline. A 20% relative reduction in faulty deliveries is a candidate useful effect size to test, not a promised outcome. Choose sample size after a difficulty pilot; the current two repetitions cannot establish it. Reject extra process that fails to deliver a measured benefit.

The two-issue work delivered the Windows fix and an honest re-audit. #100's remaining evidence/performance objective is a product experiment, not an unchecked merge or an unimplemented portability fix.
