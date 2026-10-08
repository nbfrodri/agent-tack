# Windows ownership and outstanding audit

Status: implementation and re-audit complete. PRs #129 and #130 merged; issues #111 and #100 are closed. The empirical 9/10 target was not established by these results.

The user requested resolution of issues #111 and #100 while PR #128 was awaiting its final CI check; #128 is now merged. The initial local-only limit was superseded on 2026-10-08: the owner authorized real benchmarks with Codex through their ChatGPT subscription and delegated model selection. Use bounded runs and report observed usage, not invented dollar charges. All tests use temporary HOME/XDG/Git configuration, never the user's installation. The [Codex comparison protocol](../../benchmarks/2026-10-08-codex-protocol.md) records the experimental scope.

## Scope and acceptance

- R1: Native Git Bash installation, repeated installation, doctor and uninstall agree on MSYS/native paths, symlink targets and directory identity. Existing user configuration is restored; edited files and replaced parents are preserved.
- R2: Windows ownership validation checks native security properties instead of unsupported POSIX APIs or mode bits. POSIX validation remains strict. Unsafe metadata and reparse-point redirection are rejected before restoration.
- R3: The Windows CI smoke test exercises doctor and an uninstall round trip, with focused platform regressions and the existing Linux/macOS suites passing.
- R4: Reconcile #100's completed child tasks and re-audit its eight dimensions using actual evidence. Historical outcome/cost scores do not rise merely because measurement infrastructure or documentation improved. Record any remaining evidence gap; do not claim the 9/10 target or close that goal unless supported.

## Implementation sequence

1. Reproduce #111 locally with native Python and Git Bash in a disposable home. Inspect the previous issue findings and restoration boundaries.
2. Isolate platform-specific path, privacy and identity behavior in a helper; integrate it into ownership reading/writing and doctor without changing the selective restoration policy. Cover legacy records where safe; otherwise preserve them with a precise reason.
3. Extend temporary-home lifecycle tests and native Windows smoke coverage. Run affected suites locally, then use CI for all supported platforms. Update architecture and Windows documentation to match measured support.
4. Re-audit #100 after the fixes, update its checklist and evidence, and publish only justified issue-resolution statements. Preserve user identity and omit attribution trailers.

## Verification

Use native Windows regression tests for paths, privacy, symlinks and restoration, POSIX lifecycle/doctor/install/safety suites for nonregression, pinned lint, catalog validation and the cross-platform CI jobs. Assertions must exercise observable preservation/refusal behavior.

## Outcome

#111 merged through PR #129 with all CI jobs passing, including 11 native ownership tests and 19 Windows smoke checks. The 24-run Codex comparison is complete: frozen acceptance parity, increased tokens/time, useful Luna regressions and a supplementary Unicode limitation. [Audit round 8](../../audits/2026-10-08-evidence-review.md) records an 8.6875 average and the evidence needed next; #100 is deliberately still open. No subscription dollar charge is inferred.
