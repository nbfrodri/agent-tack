# Changelog

All notable changes are documented here. Versions follow Semantic Versioning.

## [Unreleased]

### Changed

- `tests/run-all.sh` accepts suite names after its options and runs only those; an unknown name exits 2. In this repository's `checks-map.json`, edits to `sets.txt` or `sources.txt` now select a `data` check (the `cli`, `completion` and `native-agents` suites, about 90 s) instead of the full 20-minute suite, which `tack verify` could never finish. The other data files and `modes/*` still select the full suite (#190).

## [0.2.0] - 2026-10-23

### Added

- The `critic` agent role (set `review`): a read-only adversarial review of a proposal or plan before code is written. It looks for hidden assumptions, failure modes, over-engineering and a simpler option, and ends with questions for the user, who decides. At strict level the plan goes to the critic before any code (#180).
- Audits created by `improve` label each issue with a MoSCoW priority (`must`, `should`, `could`, `wont`), creating the missing labels unless the repository already ranks priority another way (#180).
- `docs/comparison.md`: how tack differs from Everything Claude Code, with dated figures and no quality claims (#183).
- A 37-second terminal demo GIF in the README, made from real command output in throwaway directories (#184).
- Opt-in live behavior trials in `tests/trials/run-trials.sh` for catalog discovery, set suggestions, usage offers, role routing and cross-delegation, with retained session files for investigating misses.
- `clear-hint-percent` (60 by default, 1–100 or `off`): the Stop hook uses fresh per-directory context fill from the `usage-band` mod or a status line running `tack usage statusline`; without them or a fresh reading, `clear-hint-tokens` applies. `tack usage set|get context` stores or reads fill, `tack usage context` returns it only while at most 600 seconds old, and status lines show `ctx N%` first. Percentage recording in usage-band 0.6.0 works independently of delegation offers.
- Offer to delegate to Codex when the 5-hour or weekly usage runs high: the `usage-band` mod records the readings (`tack usage`), or without the mod a Claude Code status line running `tack usage statusline` (or `tack usage record` inside your own script), and once per window, past `delegate-usage-percent` (50 by default, `off` to disable), the hook that runs with each message shows an on-screen notice (a `systemMessage`, independent of the assistant) and tells the assistant to end its reply with an offer to hand bounded tasks to Codex. Needs `codex` on PATH and `cross-delegation` not `off`.
- Explicit delegation model and effort announcements and recorded-setting reports; `tack codex-used SESSION_ID` reads Codex's actual model and effort from local session metadata. Interrupted runs report the cause and offer direct completion, resuming after the usage reset, or discarding the worktree; partial work stays unverified until checked. Writing delegations in enabled projects keep a handoff record so another session can recover if the delegating assistant is cut off; Codex follow-ups and resumes explicitly enter the delegation worktree.
- `tack set agent ROLE`: read-only role availability from active project and global sets, with providing sets and an activation command when inactive. Orchestration checks availability before delegating and reports a fallback when a role is missing.
- `tack models` resolves `family:NAME` to the visible Codex catalog model with the lowest priority (ties: last lexical slug), with an optional pinned fallback or `inherit` when codex is unavailable. The family-to-tier map stays manual; Claude aliases already follow the latest model. Plain model names in machine overrides remain exact pins.
- Widened the vocabulary of the `ask` rules for `performance`, `testing`, `review`, `security`, `architecture`, `planning`, `git-release`, `orchestration`, `modernization`, `agent-tooling`, `devops` and `writing`. The startup index no longer tells the assistant to browse `tack set list`: in trials with two models, none of 8 sessions did.
- The command guard asks before `codex exec` (including `e` and `exec resume`) with an explicit writing sandbox runs in a repository's main working tree. Use a linked worktree through `-C`/`--cd`, or launch resume from that worktree. `--dangerously-bypass-approvals-and-sandbox` always asks, including outside Git and in unleash mode.
- Dynamic bash, fish and zsh shell completion through `tack completion SHELL`; the installer manages bash and available fish scripts with checksum ownership, enabled by the global `completions` feature.
- `tack branches [--apply]`: lists the local branches whose work is already merged (an ancestor of main, or a merged GitHub PR whose head is still the branch tip) and deletes them with `--apply`. The branch in use, a branch with commits made after its PR merged and unmerged branches stay; without `gh` a squash-merged branch stays too.
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

- `tack verify` and `tack team --verify`: a check that ran out of time or budget now ends `incomplete` (exit 3) instead of `failed` (exit 1) and prints `Not completed (out of time, nothing failed)` with how to continue. The Stop hook reports it as a note instead of blocking; a failure, an unmapped path or edited inputs still block. The full suite takes about 20 minutes, longer than the hook's budget and the 600 s cap, so it could only ever time out. Scripts that read exit codes: a timeout used to exit 1 (#186, refs #181).
- `dev-workflow`: for an unresolved design choice the assistant presents two or three genuinely different options with their tradeoffs and a recommendation, and the user decides (#180).
- Practices adapted from Everything Claude Code into the files that already cover each topic, instead of pinning the collection: tests for assistant-written code (`testing`), one machine-checkable contract for parallel consumer and provider work (`api-design`), a wider search before writing code (`dev-workflow`), exemplar files for legacy style, an impact and rollback list before risky changes, and two independent reviews for output that ships without human review (strict mode) (#182).
- The weekly tools compatibility workflow validates and tests every mod with the latest Claude Code, so a release that makes the engine refuse a mod shows up as a failed run.

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

- The `usage-band` mod loads again. Claude Code refused it at startup (`$ is passed to "refreshChip", which is not a function declared at the top of this file`) because two helpers that take `$` were declared inside `register`, so since 0.4.2 there was no usage band, no context or 5-hour and weekly readings, and no offer to delegate. They are module-level now (0.6.2). The `mods` CI job missed it because it skipped validation when the Claude Code CLI was absent; it now installs a pinned CLI and always runs `claude plugin validate` and `claude plugin test`.
- Asking for the `code-reviewer` agent or for a review of the last commit now suggests the `review` set: its `ask` words lacked `code reviewer`, `review my last commit` and the Spanish equivalents. The `roles` trial showed the assistant noticing the missing agent but never saying how to enable it.
- CI now runs the completion, usage, Codex session metadata, branch cleanup and cross-delegation suites on Linux and macOS; validation rejects runner suites missing from CI, and Linux installs zsh and fish for completion syntax checks.
- The hook overview now describes mapped verification and fallback test commands using the remaining Stop hook budget instead of promising a 120-second timeout.
- `usage-band` 0.6.1 refreshes unchanged context readings every two minutes, keeping percentage-based Stop hints fresh during long sessions and retrying failed recordings.
- Mapped verification, fallback tests and the slop scan now share the remaining Stop hook timeout, shortening or explicitly skipping checks so completion advice can be delivered.
- The native-agent installer regression now isolates `XDG_DATA_HOME`, keeping shell completions out of a developer's inherited data directory.
- Writing Codex commands after a shell directory change now require review without an inspectable absolute directory override; main-tree overrides still require review.
- A request such as "make the page load faster" now suggests the `performance` set: its `ask` words lacked `load faster`, `loading faster` and `run faster`, found by a trial whose prompt matched none of them.
- The check before stopping no longer loses the `/clear` hint in a project with `checks-map.json`: verification now gets only the time left before the hook's 90-second timeout (`tack verify --budget-seconds`), so a slow suite is reported as timed out instead of killing the hook, and the hint travels with the block when other findings are reported.
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

### Security

- The CI workflow token is read-only (`permissions: contents: read`); no job writes to the repository. This closes four CodeQL alerts (#185).

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
