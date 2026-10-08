# Changelog

All notable changes are documented here. Versions follow Semantic Versioning.

## [Unreleased]

### Added

- Batch application of selected shared preferences and mode with `tack config --shared --apply FILE`, including a read-only preview and effective-origin reporting.
- A bounded minimal-request benchmark with isolated Codex sessions, blind agent grades and a sealed orchestrator assessment. Published results retain all attempts, discovered defects and unmet speed targets; production-code scores remain separate from tests and workflow compliance.
- A reproducible adoption benchmark covering setup, a second clone and fresh-session changes, with published null quality results, configuration-transfer evidence and time/token overhead.
- Optional versioned `tack.json` preferences and mode through `--shared`, with local overrides and private execution trust. Shared context paths are used by setup, scaffolding, context and trace discovery.
- Stable `tack config --get` and `--json` reads, plus clone-to-clone and native Windows regressions.
- Guided selection of external skills during requested onboarding, using existing installers and recording source, revision, references and local adaptations.

### Changed

- Onboarding saves agreed shared defaults explicitly; testing and setup guidance avoid redundant checks while preserving relevant verification and manual-review gaps.
- README explains the everyday value for individuals and teams; a project departure guide separates disabling tack, archiving old work and uninstalling machine integrations.
- Engineering guidance explicitly records retained TDD, pragmatic SOLID and Git/PR practices; verification documentation includes a concrete incomplete-result example.
- README and human guides are organized around setup, daily use, configuration, verification and sharing, including personal use and custom forks. Local documentation links and anchors are checked during validation.
- Formal trace links, documentation delegation and numeric review scores are optional. `tack trace` reports textual links rather than claiming test coverage; autonomous improvement uses bounded, observable findings.
- Fast and Stop fallback checks use the verifier's bounded executor with pipeline failure detection, without requiring an external timeout utility.

### Fixed

- Project context resolves native Windows paths consistently, and configuration output uses LF records for Bash consumers.
- Doctor retains partial diagnostics when Python is unavailable and reports malformed shared profiles when validation is available.

### Removed

- Runtime reads of the former `harness.*` settings and `.harness` markers, the `harness` command and its managed links. Upgrade through v0.1.0 and follow its per-clone migration steps before installing this change ([#122](https://github.com/nbfrodri/agent-tack/pull/122)).

## [0.1.0] - 2026-10-06

### Added

- `tack migrate` moves former `harness.*` settings and `.harness` markers to the current names. It preserves effective values, whitespace, multiline commands and existing `tack.*` settings. `tack doctor` reports clones that need migration ([#114](https://github.com/nbfrodri/agent-tack/pull/114)).
- Test-command detection, test results before stopping in trusted projects, and a reminder when source code changes without tests ([#104](https://github.com/nbfrodri/agent-tack/pull/104), [#105](https://github.com/nbfrodri/agent-tack/pull/105), [#124](https://github.com/nbfrodri/agent-tack/pull/124)).
- A portable installation and hook smoke test on Linux, macOS and experimental Windows Git Bash ([#83](https://github.com/nbfrodri/agent-tack/pull/83), [#108](https://github.com/nbfrodri/agent-tack/pull/108)).
- Evaluation scenarios covering project conventions, path traversal and SQL search; published results include both improvements and cases without gains ([#107](https://github.com/nbfrodri/agent-tack/pull/107), [#120](https://github.com/nbfrodri/agent-tack/pull/120), [#126](https://github.com/nbfrodri/agent-tack/pull/126)).

### Changed

- `lite` now includes the self-contained rules of `lean`; `lean` remains a working alias. `tack migrate` rewrites stored `lean` selections to `lite` ([#121](https://github.com/nbfrodri/agent-tack/pull/121)).
- Automatic workflow selection considers risk, including untrusted input, before task size ([#119](https://github.com/nbfrodri/agent-tack/pull/119)).
- Installation output summarizes managed files, doctor skips absent optional tools, and commits directly to main receive guidance ([#101](https://github.com/nbfrodri/agent-tack/pull/101), [#106](https://github.com/nbfrodri/agent-tack/pull/106), [#118](https://github.com/nbfrodri/agent-tack/pull/118)).
- Replies follow the user's language. Documentation explains per-tool enforcement and guard limitations ([#85](https://github.com/nbfrodri/agent-tack/pull/85), [#86](https://github.com/nbfrodri/agent-tack/pull/86)).

### Fixed

- Reduced command-guard process starts and corrected heredoc consumer detection ([#84](https://github.com/nbfrodri/agent-tack/pull/84), [#112](https://github.com/nbfrodri/agent-tack/pull/112), [#116](https://github.com/nbfrodri/agent-tack/pull/116)).
- Evaluation grading finds work committed on another branch ([#120](https://github.com/nbfrodri/agent-tack/pull/120)).

### Security

- The command guard refuses assistant-set `TACK_ALLOW_*` overrides. The former `HARNESS_ALLOW_*` overrides no longer bypass git-hook checks ([#110](https://github.com/nbfrodri/agent-tack/pull/110)).

### Deprecated

- Runtime support for the former `harness.*`, `.harness` and the `harness` command is retained in this transition release. Migrate every existing clone before updating beyond this release to a version that removes those names ([#122](https://github.com/nbfrodri/agent-tack/pull/122)).

### Migration before updating beyond v0.1.0

1. Update the tack checkout to this tag: `git fetch origin --tags && git switch --detach v0.1.0`.
2. Run `./install.sh` from the tack checkout to update managed links and migrate old configuration/state directories.
3. In every project clone that used the former name, run `tack migrate` and `tack doctor`. Global settings migrate too; each clone's local settings must be migrated separately.
4. If the project tracked the former `.harness` marker, commit its replacement with `.tack`. Update scripts that invoke `harness` to use `tack`.
5. Only after those steps, update the tack checkout to a later release and rerun `./install.sh`.

Native Windows Git Bash remains experimental: doctor and uninstall still have the limitations tracked in [#111](https://github.com/nbfrodri/agent-tack/issues/111). WSL2 remains the supported Windows path.

[0.1.0]: https://github.com/nbfrodri/agent-tack/releases/tag/v0.1.0
