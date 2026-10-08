# Team onboarding and integration context

Status: in progress. Starting revision: `f4b88b447b533d7bf02d445994fbf0ad5065827e` (PR #134, including passing post-merge CI). The owner approved optional collaborator setup and described a concrete coordination problem: backend work must be understandable to a frontend developer's assistant without repeatedly writing explanatory documents by hand.

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

The repository topology is an open user question: frontend/backend directories in one repository, or separate repositories. Continue bootstrap work while waiting; do not assume access to the other developer's repository or install anything there.

Concrete acceptance example: after backend changes order creation, the frontend assistant can find the request/response shape, authentication and error behavior, examples or existing generated types, verification commands, consumer action items and the evidence for availability. Future endpoints remain explicitly planned. An old handoff must not become proof that a feature is still available after later changes or a revert.

Design constraints to resolve against the topology:

- Prefer existing OpenAPI/GraphQL/schema/types and tests as the contract. Use short Markdown only for decisions, pending work and consumer-specific guidance that those sources do not express.
- Index relevant integration context from project instructions. Avoid loading every team's notes into every task, or selecting an unrelated handoff merely because its filename sorts last.
- Record a source repository, revision and relevant paths where useful. Validate observations against available Git objects/current files. Commit ancestry alone does not prove current behavior after a revert.
- Distinguish observed local references from live remote state. Do not claim remote freshness without fetching, and do not fetch implicitly during a read-only context command.
- In separate repositories, use explicit shared contracts/references or selected exports. Do not scan unrelated directories, publish private code, create a synchronization service or assume cross-repository access.
- Extend the existing documentation and API workflows so the producing assistant maintains the contract and handoff in the same change, and the consuming assistant verifies it before implementation. Add executable checks only when they can establish a concrete fact.

Before implementing this part, record the selected design and owning files here. Test stale evidence, missing references, parallel handoffs, planned-only behavior and already-merged/reverted work as relevant to that design. An AI-written summary is guidance, not an executable proof of compatibility.

## 3. Owning documentation and delivery

Update `docs/setup.md`, `docs/sharing.md`, `docs/installation.md`, `docs/usage.md`, `docs/architecture.md`, `docs/development.md`, the documentation index and changelog where behavior changes. Keep the README short: explain collaborator onboarding and link to the complete backend/frontend walkthrough. Record proposed CLI commands as proposals until implemented.

Use the existing PR template. Make conventional commits without AI attribution, run focused behavioral tests and pinned lint/validation, then required cross-platform CI. Publish and merge only after the exact candidate passes. Archive this plan on completion and report limitations explicitly.

The 93-session quality experiment is complete and remains frozen. This work does not rerun or reinterpret it, and has no authorization to extend that batch. No new real-model benchmark is required to validate bootstrap or Git/context behavior.
