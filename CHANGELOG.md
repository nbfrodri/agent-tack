# Changelog

All notable changes are documented here. Versions follow Semantic Versioning.

## [Unreleased]

### Added

- The startup set index tells the assistant what to do when a task needs a kind of work no active set covers and the rules named nothing: run `tack set list` once, read what each set is for and tell the user which one fits. The user still decides.
- `clear-hint-tokens` (150000 by default, `off` to disable): once per session, when the context passes the set size, the check before stopping makes sure the handoff is current and tells the user `/clear` is safe, because the handoff reloads at session start. Claude Code only.
- Documented `/model opusplan` (Opus in plan mode, Sonnet otherwise) and how it fits the workflow modes (`docs/advanced.md`).
- `cross-delegate` skill and `cross-delegation` setting (`off`, `one-way`, `both`): one assistant hands a bounded task to the other installed one (`codex exec`, `claude -p`) and reads back a short fixed-shape report, continuing the same session for follow-ups, so long work stays out of its context. Strict and unleash delegate automatically; lite and standard suggest.
- Sets reach the work in three measured steps. A set may declare `match` rules for the files that give a project away; `tack set suggest` lists the sets that fit, `--apply` activates them and `--skip` declines them. A reminder with each message (the `skill-reminder` hook in Claude Code, the startup context elsewhere) names the active sets' skills so the assistant loads the matching ones first, and the fitting sets so it tells the user. Sets for a kind of task, which no file gives away, declare `ask` terms in English and Spanish instead; a message that says one gets the set named the same way, and `tack set skip NAME` stops the suggestion. In trials with a small model, skill use with an active set went from 0 of 10 to 6 of 6.
- An optional slop check: when [aislop](https://github.com/scanaislop/aislop) is installed and the project is trusted, the check before the assistant stops scans the code the branch changed and reports the findings on changed lines. Advisory, with aislop's telemetry and update checks turned off; `tack config slop-check false` turns it off.
- Sets: named bundles of skills, agents and Claude Code plugins in `sets.txt`, with external skill collections pinned to a full commit in `sources.txt`. `tack set use NAME` links a set into one project for every tool; `--global` applies it everywhere through `./install.sh`; `tack set update` moves a pin and reports which used skills changed. 51 sets in ten categories are declared: `core`, two compatibility sets, 41 over 24 skill collections and seven `agents-*` sets of subagent plugins from the VoltAgent and wshobson marketplaces.
- A set index in the startup context of enabled projects: one line naming every set by category and the active ones, so the assistant can activate a set in the project when a task needs it and drop one the work no longer needs. `tack config set-index false` turns it off; in a mode such as `unleash` the guard lets the assistant read sets but not change them.
- An audit of the external skills and subagent plugins used by sets (`docs/audits/2026-10-11-external-skills.md`).
- Shared `collaboration` choice (`solo` or `team`), isolated `tack team` branch diagnostics and focused producer/consumer guidance for monorepos.
- Optional, configurable PR metadata checks and a read-only GitHub Actions asset, also used by tack's own PRs.
- Batch application of selected shared preferences and mode with `tack config --shared --apply FILE`, including a read-only preview and effective-origin reporting.
- A bounded minimal-request benchmark with isolated Codex sessions, blind agent grades and a sealed orchestrator assessment. Published results retain all attempts, discovered defects and unmet speed targets; production-code scores remain separate from tests and workflow compliance.
- A reproducible adoption benchmark covering setup, a second clone and fresh-session changes, with published null quality results, configuration-transfer evidence and time/token overhead.
- Optional versioned `tack.json` preferences and mode through `--shared`, with local overrides and private execution trust. Shared context paths are used by setup, scaffolding, context and trace discovery.
- Stable `tack config --get` and `--json` reads, plus clone-to-clone and native Windows regressions.
- Guided selection of external skills during requested onboarding, using existing installers and recording source, revision, references and local adaptations.

### Changed

- `web-design-guidelines` and `writing-guidelines` leave the `design` and `writing` sets: both download their rules at run time, so their pinned commit did not determine what they instruct. `engineering-lifecycle` moves to the compatibility sets, out of the startup index: it is an alternative method for a whole project, for the user to choose.
- Sets keep one voice per job: thirteen external items that competed with this repository's workflow or duplicated another collection's reference material were removed from `testing`, `planning`, `orchestration`, `writing`, `review`, `backend`, `monitoring` and `agent-tooling`.
- Sets are now the only way a skill or an agent role is installed. The `core` set (`dev-workflow`, `new-project`) is always active; every other skill and agent of this repository comes with a set, per project or everywhere. `tack-skills` and `tack-agents` bring them all at once.
- The setup, sharing and parallel-branch guides, the documentation index and `AGENTS.md` describe tack as a personal configuration whose shared project setup and branch coordination are optional.
- tack is now positioned as a personal configuration rather than a general product ([ADR 0004](docs/adr/0004-personal-configuration-with-sets.md)). The README describes what the repository holds and how to install it on another machine.
- `plugins.txt` installs `claude-code-setup` and `security-guidance` for every project; `frontend-design` moved to the `design` set as a skill, so tools other than Claude Code receive it.
- Startup indexes parallel handoffs and selects a full excerpt only for a single active handoff or a unique current-branch match.
- Onboarding saves agreed shared defaults explicitly; testing and setup guidance avoid redundant checks while preserving relevant verification and manual-review gaps.
- README explains the everyday value for individuals and teams; a project departure guide separates disabling tack, archiving old work and uninstalling machine integrations.
- Engineering guidance explicitly records retained TDD, pragmatic SOLID and Git/PR practices; verification documentation includes a concrete incomplete-result example.
- README and human guides are organized around setup, daily use, configuration, verification and sharing, including personal use and custom forks. Local documentation links and anchors are checked during validation.
- Formal trace links, documentation delegation and numeric review scores are optional. `tack trace` reports textual links rather than claiming test coverage; autonomous improvement uses bounded, observable findings.
- Fast and Stop fallback checks use the verifier's bounded executor with pipeline failure detection, without requiring an external timeout utility.

### Fixed

- Installed files are recognised again after a reboot on filesystems that change a folder's device number (btrfs subvolumes, overlays, network mounts): the folder's inode identifies it. Before, dropping a set kept generated agents as "ownership location changed" and uninstall skipped what it could restore.
- Agents and skills read each other's files through the checkout (`~/.agents/tack/skills/...`) instead of the installed path, which exists only while a set active everywhere lists that skill; the validator rejects the old form.
- The `performance-analyzer` description no longer carries Spanish trigger phrases.
- The PR metadata check accepts a pull request from an automated author such as Dependabot on its title alone, instead of failing it for lacking the template's sections.
- `tack memory add` refuses environment-style assignments whose variable names a credential, such as `DB_PASS=...` or `AWS_SECRET_ACCESS_KEY=...`.
- Skill descriptions holding `": "` are quoted and agent descriptions reworded, so strict YAML readers no longer skip `api-design`, `auth`, `e2e-testing`, `frontend` and `git-history`; the validator rejects a new unquoted one.
- The installer removes a link whose replaced original pointed into a checkout that no longer exists, instead of keeping it for an uninstall that has nothing to restore: links under the former `harness` name, and skill and agent links no active set lists.
- Windows collaborator setup selects Git Bash explicitly instead of the System32 WSL launcher.
- Collaborator setup isolates inherited Git directory/index overrides and rejects junctions on older supported Python versions.
- Team completion checks no longer ask to refresh another branch's handoff merely because its branch differs.
- Project context resolves native Windows paths consistently, and configuration output uses LF records for Bash consumers.
- Doctor retains partial diagnostics when Python is unavailable and reports malformed shared profiles when validation is available.

### Removed

- Skill groups (`skill-groups.txt`) and the `skill-groups` and `agent-roles` settings. `tack migrate` turns a former choice into the `tack-skills` and `tack-agents` sets; until then the installer and doctor say the settings are no longer read.
- `tack bootstrap` and its generated collaborator setup script, added and removed before a release: it only served teams adopting tack.
- The evaluation harness (`evals/`), benchmark reports, product audits, archived plans and their offline test suites. They remain in the Git history; no runtime capability was removed.
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
