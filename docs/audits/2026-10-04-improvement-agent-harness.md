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

Independent review reproduced five defects in the unpublished doctor/lifecycle candidate. These are distinct from the previously closed findings. Issues were deduplicated against all existing issues and created automatically under the approved audit workflow.

| Finding | Priority | Issue | Resolution |
| --- | --- | --- | --- |
| Doctor infers ownership from a `git-hooks` directory name or `_chain` file, causing false errors for deliberate foreign hooks | Medium | [#27](https://github.com/nbfrodri/agent-harness/issues/27) | Fixed locally in `818ffb9`; regression requires actual checkout or validated ownership evidence |
| Selective uninstall loses displaced original hooks when a user appends another command to the installed group | Medium | [#28](https://github.com/nbfrodri/agent-harness/issues/28) | Fixed locally in `a8fd642` and `e0d5277`; original hooks restored alongside later additions, including retired events, without overwriting edited commands |
| An absent explicit `GIT_CONFIG_GLOBAL` plus an existing XDG config records ownership in the wrong file, leaving installed hooks active after uninstall | Medium | [#29](https://github.com/nbfrodri/agent-harness/issues/29) | Fixed locally in `a8fd642`; explicit global config override determines both write and ownership paths |
| Mutable `targets.txt` declarations invalidate historical ownership after customization | Medium | [#30](https://github.com/nbfrodri/agent-harness/issues/30) | Fixed locally in `485a368`; new link records retain private installation-time declarations |
| Installer replaces an unrecorded missing foreign hooksPath merely named `git-hooks` | Medium | [#31](https://github.com/nbfrodri/agent-harness/issues/31) | Fixed locally in `485a368`; migration requires checkout, recorded ownership or prior canonical-link evidence |

The owner authorised publication of the feature branch after verification. Fix commits are published; the owner subsequently authorised [PR #32](https://github.com/nbfrodri/agent-harness/pull/32) and integration preserving commits. The PR closes the five findings when merged. The fifth finding is preexisting in the published baseline; the other four were identified before publishing the new features.

## Approved improvement work

The [implementation plan](../plans/2026-10-04-lifecycle-and-delegation.md) covers read-only doctor diagnostics, installation preview, private ownership and conservative uninstall, automatic complexity-based delegation, contextual PR integration choices and reproducible eval metadata. It preserves verified commits as work progresses and leaves publication decisions to the owner.

Automatic model routing is instruction-driven and bounded by the current runtime's actual capabilities. It does not guarantee a particular model, subagent availability or cost. Project `harness.delegation=off` opts out; small and coupled tasks stay direct.

## Final local assessment

The implemented project scores **8.7/10**, the rounded unweighted mean below. An independent reviewer proposed the scores using the same rubric and the parent confirmed the relevant integrated checks. The interrupted benchmark does not contribute to the score.

| Dimension | Final | Change from baseline | Evidence |
| --- | --- | --- | --- |
| Architecture | 8.8 | +0.3 | Installation capture, validation/restoration and diagnostics have separate owners; CLI dispatch stays small; architecture documents actual dependencies |
| Code quality | 8.5 | — | Explicit ownership boundaries and failure handling; selective JSON restoration remains necessarily more complex than the earlier installer |
| Tests | 8.8 | +0.3 | 560 automated checks pass across verified milestones: 12 validator, 87 installer, 177 hooks, 63 CLI, 2 settings, 42 security, 56 guard, 17 offline eval, 39 doctor and 65 lifecycle; confirmed RED/GREEN reproductions for the new defects |
| Security | 8.5 | +0.5 | Private snapshots, declared destinations, physical parent identity, user-edit preservation and evidence-based migration; no broad project/plugin removal |
| Performance | 8.5 | — | Bounded parser behavior retained; no new timing claim or live-model speed advantage inferred |
| Documentation | 8.8 | +0.3 | Installation/removal, customization, architecture, on/off modes, model fallbacks and contextual integration choices documented in English; interrupted benchmark clearly distinguished from results |
| Tooling | 8.8 | +0.3 | CI includes lifecycle/doctor suites; eval metadata records model/hash/revision/permissions; ShellCheck 0.9 and 0.11 pass locally |

The remaining improvement is empirical: finish the paused benchmark before claiming new process, correctness or cost advantages. Two of six authorised attempts hit Claude's session limit; there are zero completed samples. Four attempts remain under the owner's instruction to save and resume after reset. The original six-attempt budget does not authorise replacing the two failures. [Checkpoint and limits](../results.md#current-reevaluation-checkpoint).

The temporary launcher also inherited XDG_STATE_HOME in its first attempt and created a benchmark-only ownership record in the real HOME. Automatic review rejected deleting it. A safer reversible rename was subsequently approved: all 96 temporary-home records and private snapshots were preserved under `benchmark-ownership-20261004`, clearing the active ownership path. Pending runs isolate all XDG directories. Raw authentication files and transcripts remain excluded from publication.

These scores are for the inspected repository and personal-use scope, not a certification that the shell guard is a sandbox or that instructions will always be followed. Uninstall deliberately preserves conflicting edits and cannot infer legacy ownership. Local Linux checks alone do not establish macOS behavior; Linux/macOS CI and the authorised integration are tracked in [PR #32](https://github.com/nbfrodri/agent-harness/pull/32). The owner requested preserving the verified milestone commits, and the PR closes the five tracking issues when integrated.
