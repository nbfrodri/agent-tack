# Lifecycle and delegation checkpoint

- Status: paused at the owner's request for the benchmark; implementation complete.
- Branch: `feat/lifecycle-doctor-and-auto-delegation`.
- Plan: `docs/plans/2026-10-04-lifecycle-and-delegation.md`.
- Evaluation: `docs/audits/2026-10-04-improvement-agent-harness.md`; initial 7.4, published baseline 8.4, final local 8.7/10.
- Implemented: `harness doctor`, installation preview, private ownership and safe uninstall, automatic complexity-based delegation, contextual merge/squash choice and reproducible eval metadata.
- User preferences: commit each coherent verified milestone; recommend integration method from branch history in the existing approval, preserving commits unless squash explicitly chosen. Project delegation absent/auto is automatic; off disables automatic delegation.
- Key milestones: `2b1faa4` contextual merge; `cb9b7aa` automatic routing; `28d1722` doctor CLI; `a8fd642` lifecycle boundaries; `485a368` customized targets/moved-hook evidence; `e0d5277` retired hook restoration; `027ba67` interrupted eval evidence/recovery; `c3b320b` isolated CLI state.
- Verification: 560 checks across verified milestones; ShellCheck 0.9/0.11 and content validation. No new macOS/remote CI run; feature pushes do not trigger the current main/PR workflow.
- Issues #27–#31: verified, created through the approved audit workflow, fix commits published; remain open pending owner-authorised closure.
- Owner authorised push after implementation; branch published to origin through `2188188`. PR, merge, tag and release are not authorised. Recommend preserving commits for this branch's independent verified milestones; offer available methods when integration is requested.

## Remaining benchmark work

Read `docs/handoffs/2026-10-04-benchmark.md` before resuming. Two Claude attempts hit the session limit, zero completed samples, four authorised attempts remain. User chose save/resume after the provider-reported 2026-10-04 01:50 Europe/Madrid reset. Do not replace the failed attempts or exceed six without new authorisation.

Use the detached frozen checkout `a8fd642a2aa0197e152b12e42f1755a9fa89e6e9`, core installation without plugins and the same observed model/permissions/prompt. Subsequent changes affect ownership edge handling/tests/docs; do not change the frozen experiment mid-comparison. Scripts and private outputs remain in /tmp; preserve or reconstruct them before reboot. Only sanitized attempt metadata/metrics are tracked under `docs/benchmarks/`.

The first launcher inherited real XDG_STATE_HOME and created a benchmark-only ownership record. All 96 recorded paths were verified inside its temporary HOME. Deletion was rejected by automatic review; a safer atomic rename was approved and preserved every record under `/home/phobos/.local/state/agent-harness/benchmark-ownership-20261004`. The active ownership path is clear. Do not delete that private backup without permission. Remaining runs isolate all XDG paths and remove temporary authentication copies.
