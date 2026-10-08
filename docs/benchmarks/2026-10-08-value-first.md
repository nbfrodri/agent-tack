# Value-first preflight: a shorter workflow did not make these tasks faster

Eight implementation sessions and two independent blind reviews completed through Codex using the existing subscription. All sessions finished without infrastructure errors or retries. The lean candidate did not meet the speed/token targets. A short project-only AGENTS.md produced the best settings implementation in this sample, while shipment implementations were effectively equivalent.

## Protocol and versions

- Implementer: `gpt-6-luna`, medium effort. Independent reviewer: `gpt-6-astra`, medium effort. Runtime records confirmed the requested models and effort.
- Current tack: `ff53cef1fe2d38f1ba29b495f4ca16e627137a94`. Lean candidate: `cbbdae94506a792086c0e561a5b57ed1efdae513`.
- Image: `sha256:b3595972953b86399133c40386256f2b00facc6170d9be05a70891f24615963e`; separate disposable containers, no host mounts. Both product snapshots remained unchanged.
- Tasks: existing settings and shipment fixtures. Identical product-only requests, contracts, available commands and public seed tests. Plain did not receive engineering practices in its request. Project-only received the short `PROJECT_GUIDE` in `evals/value_fixture.py`, without tack installation.
- One repetition per task/condition, rotated order, at most two concurrent sessions. The five-minute per-session timeout was not reached. Implementation/setup collection and reviewer costs remain separate; no monetary price is inferred from subscription tokens.
- [Manifest](../../evals/batches/value-first.json), [protocol](../../evals/value-protocol.md), [cost observations](../audits/2026-10-08-workflow-cost.md). This preflight reused known tasks; it is not a held-out confirmation experiment.

## Results

Times and tokens below are **totals across two implementation sessions**, excluding installation and independent review. Cached input is already included in input tokens.

| Condition | Seconds | Input tokens | Cached input subset | Output tokens | Original hidden acceptance | Useful seed-defect tests | Blind quality mean /10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Plain | 40.239 | 160,200 | 144,640 | 2,250 | 1/2 | 0/2 | 8.40 |
| Project-only guidance | 56.839 | 243,782 | 221,440 | 4,445 | 2/2 | 2/2 | 9.50 |
| Current tack | 59.041 | 324,236 | 283,648 | 3,932 | 2/2 | 2/2 | 8.55 |
| Lean tack | 93.886 | 458,766 | 401,664 | 5,717 | 2/2 | 2/2 | 8.65 |

Lean took 59.0% more time and 41.5% more input tokens than current tack. Against project-only it took 65.2% more time and 88.2% more input. The proposed 25% reduction and 20% maximum overhead targets were missed. Both task times increased: settings 34.060 → 63.742 seconds; shipment 24.981 → 30.144 seconds.

The lean settings session contained a malformed branch command and a rejected non-conventional commit, then recovered. The commit hook provided concrete feedback, but those events do not explain all elapsed time or establish a general cause. A shorter skill entrypoint is a maintenance simplification, not proof of lower runtime cost.

## Independent review found gaps in the tests

The reviewer received randomly labeled production snapshots and requirements, without transcripts or condition identities. Each four-way bundle received one review, without the order-reversal checks proposed for a larger screen. The orchestrator inspected anonymous code and recorded an assessment before opening the mapping, but had already seen labeled runtime and acceptance summaries. This is not a fully blinded human study.

Settings scores were plain 7.2, project-only 9.4, current 7.5 and lean 7.7. The project-only code validated override values before applying environment values. Current and lean instead allowed invalid overrides to be hidden by valid environment replacements. Plain reversed the required precedence. Shipment scored 9.6 in every condition; changes were behaviorally equivalent apart from formatting.

The original hidden checks missed several settings defects. Separately recorded, **post-review supplemental probes** confirmed:

| Settings behavior | Plain | Project-only | Current | Lean |
| --- | --- | --- | --- | --- |
| Reject invalid endpoint even with valid environment replacement | Pass | Pass | Fail | Fail |
| Reject invalid attempts even with valid environment replacement | Pass | Pass | Fail | Fail |
| Accept a supplied non-dict mapping | Fail | Pass | Fail | Pass |
| Accept valid Unicode decimal digits | Fail | Pass | Fail | Fail |

These probes were added after reviewing outputs; they are not preregistered acceptance results and do not replace the original grades. They demonstrate why passing tests and numeric scores alone are insufficient. The reviewer also identified potential wrong exception types from deep-copying invalid values; that observation was inspected in code but not included in the four executable supplemental probes.

## Product decision

Do not expand automatically to the proposed 66-session screen. Do not advertise faster tasks or better general code quality. The smaller workflow remains useful as a clearer, less duplicated instruction source, but its runtime benefit is unproven. Keep explicit project policy and meaningful TDD/checks; do not add mandatory logs, reviewers, new hooks or whole external skill collections to compensate for these results.

For a project already served by a short AGENTS.md and CI, that simpler setup is a credible alternative. Tack's remaining proposition is portable preferences, relevant context and optional coordination/check helpers. The private-notes, review-collection and multi-team changes delivered after the frozen candidate were checked functionally; this pilot does not measure their adoption or productivity benefit.

A larger experiment should proceed only with a narrower hypothesis: real integration defects, a measured onboarding problem or a later-change task. It needs new held-out fixtures, repetitions and relevant lifecycle outcomes. Two small tasks with one model cannot establish population effects, scalability, setup amortization or human review savings.

## Evidence

Local raw evidence is retained under ignored `evals/out/value-20261008/`: transcripts, condition metadata, product/fixture hashes, snapshots, original grades, independent reviews, supplemental probes and the pre-unblinding root assessment. Credentials and participant homes were not exported. The root assessment SHA-256 is `01b0bf410bbc2d0d5b0406c6c8f7e16fcefdd682337ff45260a28c903139e8fe`.

The local `raw-evidence.tar.gz` contains 183 files (2,212,864 bytes); SHA-256: `489a4588ce425c7bec0f823c05aaeab014156b8ea1554c01ed2f4282695a1a3e`. No old benchmark evidence was edited or relabeled. Functional validation of the delivery is recorded separately from this frozen experiment.
