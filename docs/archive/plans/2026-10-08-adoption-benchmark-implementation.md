# Project adoption benchmark implementation

Status: implementation and experiment complete; integration is tracked by the PR checks. Product under test: `a54eda9`, before this benchmark's documentation changes.

## Outcome

Explain which engineering practices remain, what changed, and what `tack verify` reports. Execute a bounded subscription comparison of complete adoption: configure an existing project, transfer the setup to a second clone, then fix a bug and add a feature in fresh AI sessions. Preserve null and adverse results.

## Delivery

1. Clarify TDD, SOLID, test selection and Git/documentation workflow in the owning human guide; summarize removed mandates, retained practices and delivered features. Add a concrete verification example.
2. Freeze a protocol, fixture, hidden acceptance checks and manifest before model execution. Compare native project guidance without tack against tack auto with identical project requirements. Use Luna and Sol at medium effort, two repetitions per condition, eight journeys / 24 sessions maximum, two journeys concurrently and 600 seconds per session.
3. Implement a dedicated multi-stage runner beside the existing single-scenario runner. Isolate homes and Git state, record setup cost separately, preserve setup failures, clone only committed files and keep hidden checks outside the model environment. Reuse the pinned Codex launcher and existing source fingerprinting.
4. Verify the runner offline: no inherited Git configuration, only committed settings cross clones, grading rejects defective implementations and accepts a reference implementation, transcripts distinguish successful completion from transport failure, and timeout cleanup is bounded.
5. Run the comparison on the frozen product checkout in a disposable container without host mounts. Review all resulting production/test diffs using predeclared criteria. Publish per-journey facts, limitations, actual verifier examples and evidence hashes without credentials or private session records.
6. Run relevant tests, lint and documentation validation; commit conventionally without AI attribution, open a PR, monitor CI and merge only when green under the owner's existing authorization.

## Evidence boundaries

This is a small synthetic adoption experiment, not a field study or proof of general quality improvement. Both conditions receive useful project guidance and equal engineering requirements. Branches, commits, test counts and file creation do not earn correctness points. Hidden acceptance, regression sensitivity, reuse across clones and observed time/tokens are reported separately. External skill downloads, live GitHub issue/PR creation, editor diversity and human decision time are outside this experiment.

## Delivery evidence

- All 24 sessions completed on the frozen product; 16/16 code tasks passed hidden acceptance and both conditions detected 12/12 injected faults. Configuration transfer and the two missing explicit shared defaults are reported separately.
- All production/test diffs and red/green sequences reviewed; runtime model and medium-effort observations confirmed. Raw evidence archived locally with its published hash; temporary authentication removed.
- Offline evidence tests: 15 existing plus eight adoption regressions passed. Pinned lint and documentation validation passed. CI remains the final integration gate.
- Results, protocol, all-run facts, code review, architecture, README and owning engineering/verification guides updated. No runtime product behavior was changed or tuned during this comparison.
