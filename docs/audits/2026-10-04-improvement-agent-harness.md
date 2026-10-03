# Lifecycle and workflow reevaluation

Whole-repository review for personal use, prioritising incremental improvements across architecture, code quality, tests, security, performance, documentation and tooling. The owner retained the previous scope and authorised lifecycle tools, automatic delegation and one representative benchmark with three runs per condition. No application UI applies.

## Baseline assessment

The initial audit at `f93cb50` scored 7.4/10. The integrated baseline `422cfd4` scores **8.4/10**, the unweighted mean of the seven dimensions below, rounded to one decimal. This uses the evaluator's same anchors: 6–7 means solid with clear gaps; 8–9 means consistent good practice. Scores assess demonstrated behavior rather than planned work.

| Dimension | Initial | Integrated baseline | Evidence for change |
| --- | --- | --- | --- |
| Architecture | 8.5 | 8.5 | Existing installer/parser/settings boundaries retained; activation and trust centralised in `bin/harness`; `docs/architecture.md` describes actual dependencies |
| Code quality | 7.0 | 8.5 | CLI and validator failures propagate; settings merging preserves independent hook commands; regression suites exercise failure paths |
| Tests | 7.5 | 8.5 | All 450 baseline checks passed: 12 validator, 87 installer, 177 hooks, 58 CLI, 2 settings, 42 security, 56 guard and 16 offline eval checks |
| Security | 5.5 | 8.0 | `tests/safety.test.sh` verifies final-index scanning and exact paths; formatter requires local trust; unsupported executable syntax requests review |
| Performance | 6.5 | 8.5 | Bounded parser replaces the previous timeout-prone analysis; guard suite covers 50k input, deep nesting and oversized inputs; earlier measured timings are recorded in the prior audit |
| Documentation | 8.5 | 8.5 | English README, architecture/customization and context/trust/help guides; historical benchmark limits are stated in `docs/results.md` |
| Tooling | 8.0 | 8.5 | Offline metric/runner tests now exist; Linux/macOS CI passed for the published baseline; ShellCheck passes locally |

The [previous audit](2026-10-03-improvement-agent-harness.md) records all ten original findings and their fixes. This evaluation does not assume the historical test-order metric is reliable: metric version 2 changed its evidence rules.

## Verified findings during feature integration

Independent review reproduced three defects in the unpublished doctor/lifecycle candidate. These are distinct from the previously closed findings. Issues were deduplicated against all existing issues and created automatically under the approved audit workflow.

| Finding | Priority | Issue | Resolution |
| --- | --- | --- | --- |
| Doctor infers ownership from a `git-hooks` directory name or `_chain` file, causing false errors for deliberate foreign hooks | Medium | [#27](https://github.com/nbfrodri/agent-harness/issues/27) | Fixed locally in `818ffb9`; regression requires actual checkout or validated ownership evidence |
| Selective uninstall loses displaced original hooks when a user appends another command to the installed group | Medium | [#28](https://github.com/nbfrodri/agent-harness/issues/28) | Correction and isolated regression in progress |
| An absent explicit `GIT_CONFIG_GLOBAL` plus an existing XDG config records ownership in the wrong file, leaving installed hooks active after uninstall | Medium | [#29](https://github.com/nbfrodri/agent-harness/issues/29) | Correction and isolated regression in progress |

Issues remain open while the feature branch is local; publication and issue closure require the owner's next instruction. No new baseline safety bypass was reproduced in this review.

## Approved improvement work

The [implementation plan](../plans/2026-10-04-lifecycle-and-delegation.md) covers read-only doctor diagnostics, installation preview, private ownership and conservative uninstall, automatic complexity-based delegation, contextual PR integration choices and reproducible eval metadata. It preserves verified commits as work progresses and leaves publication decisions to the owner.

Automatic model routing is instruction-driven and bounded by the current runtime's actual capabilities. It does not guarantee a particular model, subagent availability or cost. Project `harness.delegation=off` opts out; small and coupled tasks stay direct.

## Verification limits and final assessment

Final lifecycle regressions, integrated review and the six-session benchmark are pending. Final scores and benchmark observations will be recorded after verification. Raw authentication files and transcripts are excluded from publication. Linux checks cannot independently establish macOS behavior for the unpublished changes; CI is configured to run the lifecycle and doctor suites on both operating systems when published.
