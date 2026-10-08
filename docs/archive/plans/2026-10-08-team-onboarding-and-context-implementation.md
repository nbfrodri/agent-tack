# Team onboarding and integration context

Status: implementation complete. Starting revision: `f4b88b447b533d7bf02d445994fbf0ad5065827e` (PR #134, including passing post-merge CI). Delivery and exact-head cross-platform CI are tracked in [PR #135](https://github.com/nbfrodri/agent-tack/pull/135); integration remains gated on passing checks. The owner approved optional collaborator setup and described a concrete coordination problem: backend work must be understandable to a frontend developer's assistant without repeatedly writing explanatory documents by hand.

## Completion record

Implemented optional pinned bootstrap, shared solo/team selection, isolated branch diagnostics, parallel handoff discovery, producer/consumer references, minimum PR metadata checks and their human guides. The four-file scaffold is unchanged. Existing issue workflows now link audit findings, implementation and selected PR checks without new publication approval gates.

All local suites passed across disposable Linux environments. Focused coverage includes 12 bootstrap cases (with platform-dependent skips), 10 team/context/Stop and 6 PR metadata tests. Native Windows checks pass too (two bootstrap symlink cases need privileges unavailable locally); CI initially found bare Bash selecting WSL, corrected by choosing Git Bash explicitly. A native junction regression also covers older supported Python versions without Path.is_junction. Pinned lint, reference and human-link validation pass. GitHub CI remains the final delivery gate.

The separate four-session Codex pilot completed without retries: both versions passed 7/7 integration checks, with the candidate 5.5% slower overall. Review found unnecessary completion repairs caused by unrelated handoffs. A failing regression reproduced the issue before the team-specific Stop fix; final-reply guidance now keeps the original task outcome after repairs. These follow-ups were not re-benchmarked. Frozen products, all attempts and limitations are published in `docs/benchmarks/2026-10-08-teamwork.md`; the previous 93-session batch is unchanged.

## Intended outcome

- A collaborator can run one explicit project setup command to install a selected tack revision when needed, then reuse the repository's existing shared choices.
- Existing personal installations and team forks remain under the collaborator's control. Project activation, machine installation and local execution trust remain separate.
- Assistants find the canonical interface contract, relevant decisions and a concise integration handoff. They distinguish planned behavior, work available on a branch and behavior verified against the known main reference.
- Context is maintained with the implementation and reviewed with the change. Do not create a second API specification, a generic documentation tree, a background synchronizer or a hosted service.

## Existing behavior and gaps

- `.tack` shares activation and `tack.json` shares selected preferences. Neither installs tack. `install.sh` changes machine integrations and links to a persistent checkout.
- `tack setup` is read-only discovery. Optional additions are selected through `skills/new-project/references/onboarding.md`; the four-file default scaffold must remain unchanged.
- `lib/project-context.sh` currently selects one active handoff and compares its branch/date with local Git history. It does not provide a multi-component integration view or establish whether described behavior is present in main.
- `skills/project-docs` already provides handoffs, architecture, plans and a docs-map. `checks-map.json` can select real contract checks supplied by the project. Reuse these mechanisms instead of introducing another general documentation system.
- Git does not transfer local hooks through a clone. A setup command needs explicit invocation; a selected Dev Container can run installation when that environment is created.

## 1. Optional collaborator setup

Add a focused project-bootstrap helper and CLI entry in `bin/tack`. The CLI prepares reviewable project files only when selected; it does not itself install on a collaborator's machine. Keep ordinary `tack setup` read-only.

Proposed user flow:

1. The owner selects a reviewed source repository and full commit, using the current tack checkout as the default source when its origin and revision are available.
2. The owner previews, then creates a small setup script plus a versioned installation recipe, and commits them with the project guidance.
3. A collaborator runs the script. It describes the source, pinned revision and installation scope. If tack is missing, confirmation precedes downloading and installing it. A clearly named noninteractive opt-in supports an already approved development-container setup.
4. An existing installation is detected and reported. Do not silently replace another checkout, upgrade a fork or change its settings. Report a revision mismatch instead of claiming that the requested version is installed.
5. Reuse the existing installer with optional plugins excluded by default. Keep its checkout in a persistent user location, since installed links depend on it. Do not grant project trust or copy another developer's local settings.

Implementation files: new `lib/project_bootstrap.py`, a standalone bootstrap asset under `skills/new-project/assets/`, a new behavior suite `tests/bootstrap.test.py` with its shell entrypoint, and thin dispatch/help in `bin/tack`. Confirm final file names and arguments against the existing CLI before implementation. Generated files must be complete without an existing tack installation.

Required behavior:

- Read-only preview; no overwrite of existing or edited project files; safe project-relative destinations without symlink traversal.
- A bounded, strictly validated recipe. Source and full revision are data; never interpolate them into shell command text. Reject credential-bearing URLs and unsupported options.
- Download only after installation is selected. Verify the fetched commit matches the recipe before invoking its installer. Preserve existing caches/checkouts on a mismatch or failed installation.
- Existing installations, declined installation, noninteractive invocation without consent, missing prerequisites and partial failures have clear outcomes.
- Preserve local trust, activation and project preferences. Do not run discovered project commands as part of bootstrap.
- Bash 3.2 and supported Python compatibility; native Windows paths where applicable. No new runtime dependency.

Tests use disposable HOME/XDG/Git configuration and a local fixture source, without external downloads or real machine changes. Cover preview and no-overwrite behavior, source/revision validation, refusal before consent, pinned installation, repeat invocation, existing custom installation, mismatched or dirty cache, failed installer and unchanged trust/preferences. Add the suite to relevant CI and `tests/run-all.sh` discovery as required.

## 2. Shared integration context

The owner confirmed a monorepo: frontend and backend are separate directories in the same repository. This iteration targets that concrete arrangement. Cross-repository synchronization is outside scope; do not assume access to another repository or install anything there.

Concrete acceptance example: after backend changes order creation, the frontend assistant can find the request/response shape, authentication and error behavior, examples or existing generated types, verification commands, consumer action items and the evidence for availability. Future endpoints remain explicitly planned. An old handoff must not become proof that a feature is still available after later changes or a revert.

Design constraints to resolve against the topology:

- Prefer existing OpenAPI/GraphQL/schema/types and tests as the contract. Use short Markdown only for decisions, pending work and consumer-specific guidance that those sources do not express.
- Index relevant integration context from project instructions. Avoid loading every team's notes into every task, or selecting an unrelated handoff merely because its filename sorts last.
- Record a source repository, revision and relevant paths where useful. Validate observations against available Git objects/current files. Commit ancestry alone does not prove current behavior after a revert.
- Distinguish observed local references from live remote state. Do not claim remote freshness without fetching, and do not fetch implicitly during a read-only context command.
- In separate repositories, use explicit shared contracts/references or selected exports. Do not scan unrelated directories, publish private code, create a synchronization service or assume cross-repository access.
- Extend the existing documentation and API workflows so the producing assistant maintains the contract and handoff in the same change, and the consuming assistant verifies it before implementation. Add executable checks only when they can establish a concrete fact.

Selected approach: extend `skills/project-docs` with an integration handoff reference/template that links existing contracts, implementation/PR references, planned changes and consumer action items. Extend `skills/api-design` and the development workflow to maintain these only when a change has another consumer. Improve `lib/project-context.sh` to index several active handoffs within its existing context budget, so simultaneous work is discoverable without assuming the last filename is the only task. Keep full excerpts focused and distinguish an index from an instruction to resume unrelated work. Test parallel handoffs, bounded output and branch/freshness notices. An AI-written summary is guidance, not an executable proof of compatibility; verify its claims against the contract/code in the relevant Git revision.

## 3. Explicit solo/team coordination

The owner approved adapting tack to individual or team development. Add a shared `collaboration` preference (`solo` by default, `team` when selected), separate from task effort (`auto`, `lite`, `standard`, `strict`). Shared activation and multiple commit authors are not sufficient authorization to change the workflow; onboarding may suggest team coordination from concrete project evidence and reuse a recorded selection.

Add a focused `tack team` diagnostic with `--base REF`, repeatable `--against REF` and `--json`. It reads known local Git references, reports the branch/commit, uncommitted changes, ahead/behind counts, changed paths and overlapping files. Resolve the default base from the known origin HEAD/main/master or local main/master; missing or unborn references stay explicitly unknown. Do not fetch implicitly or imply that local remote-tracking references are current.

Probe Git mergeability using a temporary local clone with shared objects, so the user's branches, index and worktree remain unchanged. Ignore global/system configuration in the probe and prevent custom merge drivers or hooks from executing. Resolve refs to commit IDs before passing them to commands. Use Git's supported merge-tree operation; unsupported Git versions or probe failures report unknown instead of a clean merge. Git mergeability is separate from API compatibility and tests. Do not claim to prevent every conflict or to prove that an old feature remains implemented merely because a commit is an ancestor.

Owning implementation: new `lib/team.py`, thin dispatch in `bin/tack`, a data entry in `features.txt`, and focused tests in new `tests/team.test.py` plus its shell entrypoint. Cover clean/diverged branches, overlapping files without a text conflict, actual conflicts, deleted/renamed files as supported by Git, missing refs, malicious-looking arguments, dirty worktrees, unsupported merge probes, no source-repository mutations and no execution of configured drivers. Use temporary HOME/XDG/Git environments.

Team workflow guidance belongs in a focused `skills/dev-workflow/references/teamwork.md`, linked only when team coordination is relevant:

- Check shared contracts and relevant parallel handoffs before consumer-facing work. Identify dependencies on other branches or PRs; distinguish planned, branch-only and merged behavior.
- Keep changes focused and communicate overlapping ownership before independently changing a shared interface. Do not require a new coordination document for every small task.
- Refresh remote knowledge when appropriate before a PR/merge, using the user's existing authorization and Git workflow; run branch diagnostics against the actual intended integration reference.
- Treat file overlap as a review signal and detected conflicts as required resolution. Use existing branch protection/CI or a merge queue when the project has one; do not add hosting services or change repository protection implicitly.
- Resolve conflicts by preserving both changes' intended behavior, never by a blanket ours/theirs choice. Respect shared-branch history, run relevant contract/integration checks and record the decision and actual verification in the PR or relevant handoff.
- Team coordination does not force strict mode, extra agents, a service or a mandatory diary. Solo mode keeps the existing lightweight workflow, and explicit diagnostics remain usable by an individual.

## 4. Issues and automatic PR checks

The owner also requested a clear audit-to-issue-to-branch-to-PR workflow and automatic minimum PR checks beyond a template. Preserve the existing issue skill's duplicate search, acceptance criteria, dependencies and prior-publication authorization. Link independently shippable findings to focused issues; use closing references only for fully completed work, and references for partial work. Keep conflict-resolution notes in the relevant PR/handoff instead of another mandatory log.

Add a standalone, standard-library PR metadata checker and a GitHub Actions example under `skills/github-issues/assets/`. Default checks cover a Conventional Commit title, meaningful Summary and Validation sections, and unfilled template placeholders. Validation may honestly describe skipped checks with a reason; metadata cannot prove the checks ran or the code is correct. Make section headings/title policy configurable, with an optional required-issue-reference rule. Validate reference syntax only unless an actual API lookup is implemented; do not claim an issue exists or is complete from a number in prose.

The workflow runs on PR creation, updates, reopening, edited metadata and readiness changes. Use read-only permissions, no secrets, no model calls, no comments and no mutation of the PR. Treat event contents as data, never shell interpolation. Existing project tests/type/contract checks remain separate. Adding this optional asset does not configure branch protection or make the check required by itself. Reuse a project's existing workflow/template and document how a maintainer can select the check in repository rules.

Exercise the checker with offline event fixtures: valid/draft PRs, missing or placeholder sections, malformed titles, honest unrun-check reports, alternate headings, issue references, and hostile-looking strings that remain inert. Dogfood the checker in tack's own PR workflow, with the existing template, after its tests pass.

## 5. Owning documentation and delivery

Update `docs/setup.md`, `docs/sharing.md`, `docs/installation.md`, `docs/usage.md`, `docs/architecture.md`, `docs/development.md`, the documentation index and changelog where behavior changes. Keep the README short: explain collaborator onboarding and link to the complete backend/frontend walkthrough. Record proposed CLI commands as proposals until implemented.

Use the existing PR template. Make conventional commits without AI attribution, run focused behavioral tests and pinned lint/validation, then required cross-platform CI. Publish and merge only after the exact candidate passes. Archive this plan on completion and report limitations explicitly.

The 93-session quality experiment is complete and remains frozen. The owner subsequently authorized a relevant follow-up benchmark after implementation. First run local integration cases covering bootstrap, branch overlap/conflicts, handoff discovery and PR metadata. If a real-model comparison can establish additional collaboration behavior, freeze a separate protocol before execution: current tack at this plan's starting revision versus the completed candidate, the same minimal backend/frontend requests, fresh isolated Codex sessions, and at most eight implementation sessions for a small two-person handoff comparison. Record all attempts, concrete integration outcomes, time and limitations; do not extend or reinterpret the old batch or claim general productivity from a small pilot.
