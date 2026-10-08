# Project-aware verification

Status: implemented and locally verified. The pull request records CI and integration results.

The owner approved emphasizing shared team configuration in README and shifting tack toward fewer generic instructions and concrete project checks. The first iteration builds on existing command detection, execution trust and Stop adapters. It does not claim improved model outcomes before a new controlled comparison.

## Acceptance

- R1: README explains sharing versioned instructions, project-local capabilities and checks across a team, while local execution trust and private user settings remain local. Shared rules do not guarantee identical model behavior.
- R2: `tack verify --plan` inspects changed tracked/untracked/deleted paths, including branch changes, and selects explicit project checks without executing project code. JSON output supports every adapter. Invalid configuration fails clearly.
- R3: `tack verify` runs selected checks once each, only with local trust, bounded timeouts and preserved command failure status. It reports command/source, result, bounded failure output and unmatched paths. No checks or unmatched paths are never described as proof that the change is correct.
- R4: Optional `checks-map.json` declares named checks, path patterns, commands and timeouts. It is not created by activation/scaffolding. Without it, reuse the existing canonical test/check-fast detector and explicitly report detection gaps. No new framework, model call or dependency is required.
- R5: The shared Stop hook uses mapped verification when a project opts in; otherwise its current test behavior remains compatible. Startup context points to the shared command rather than loading a separate workflow. All installer/hook behavior changes have tests.
- R6: Pending onboarding does not interrupt a focused task with unrelated setup work. Initialization requests still propose optional files and remember user choices. Skills, specialist roles and process documents require a concrete task need; do not disable existing safeguards or rewrite user-selected strict modes.

## Implementation

1. Add shared `lib/verification.py`, a thin `bin/tack verify` command and behavioral tests in `tests/verification.test.py`/`.sh`. Use NUL-delimited Git paths and a bounded, validated configuration. No cached success: each execution verifies current inputs.
2. Integrate mapped checks into `hooks/claude/stop-check.sh`, retaining trust and one-retry semantics. Add integration regressions for failures, untrusted projects and configuration errors. Preserve `fast-check` compatibility.
3. Tighten focused-task/onboarding guidance in `global/AGENTS.md`, startup output and the onboarding/workflow references. The project can still request full setup, strict documentation or explicit delegation.
4. Update README, CLI/usage, architecture and component docs. Include a realistic API/database check-map example whose commands must exist in the adopting project.
5. Run pinned lint, catalog validation, verification and hook suites; then full local/CI checks for hook integration. Verify native Windows command/path behavior. Publish under existing push/merge authorization, without attribution trailers.

## Limits and follow-up

Local validation: all 23 suites were exercised. The initial full run exposed a startup wording regression; its corrected hook suite passes 369 checks. Verification passes 23 behavioral tests on Linux and native Windows (one Windows symlink test skipped for local permissions). Pinned lint and catalog validation pass. Staged-only change selection and checks modifying the Git index have red/green regressions. README uses GitHub-rendered Markdown, a new project logo, an end-to-end team example and the owner-selected MIT license.

The owner clarified that easy shared configuration is the primary value: conventions, context entrypoints and artifact locations should be agreed once and reused across the team. The README and sharing guide now lead with that flow and use `auto` to select a level per task. Portable versioned preferences for `tack config`/`tack mode` and simplified adoption remain separate follow-up work; current Git config is local/global, not committed project data.

Path routing is declared coverage, not a dependency graph or proof of semantic correctness. Unknown checks stay unknown. Automatic inference initially reuses the canonical test command; richer lint/type/schema routing requires explicit project mappings. Tests verify actual defect detection and command behavior. A held-out real-model comparison remains necessary before claiming quality or cost improvements; the earlier benchmark stays unchanged.
