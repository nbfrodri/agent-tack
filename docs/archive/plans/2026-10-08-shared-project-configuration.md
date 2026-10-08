# Shared project configuration and task-scaled engineering

Status: implemented and locally verified. CI and integration status are recorded by the pull request.

The owner authorized auditing obsolete behavior, writing this plan and executing improvements autonomously with Conventional Commits, no AI attribution, CI review and merges only when green. The [audit](../../audits/2026-10-08-product-direction.md) is the basis. Individual use and team use are equally valid; a fork is optional.

## Acceptance criteria

- R1: An optional versioned `tack.json` supplies project mode and selected preferences. `tack config NAME VALUE --shared`, `tack config NAME --unset --shared` and `tack mode MODE --shared` manage it without overwriting unrelated accepted entries. No file is needed for personal/local use.
- R2: Effective preferences resolve local project override, shared project value, global personal default, then shipped default. Conversation-level instructions still control the current task; `auto` remains the normal default. A read interface exposes values/origins without forcing hooks to parse presentation strings.
- R3: Shared data cannot grant execution trust, activate unrestricted autonomy, import credentials/private memory, or silently change global installation settings. Allowed settings are declared through data. Invalid versions, values, unknown keys, unsafe paths and symlink configurations fail clearly without executing project commands.
- R4: Architecture, plan and handoff locations can be configured with current paths as defaults. Startup context, relevant readiness/scaffolding and tracing use the same agreed locations. Existing projects and established layouts remain usable; no empty artifact trees are generated.
- R5: A teammate cloning project files receives shared choices without rewriting local/global Git config; local overrides remain visible and can be removed. Setup explains what exists and what remains local. Instructions and README cover personal use, team adoption and actual daily tasks with `auto`.
- R6: Formal traceability and documentation delegation are optional and need-based; change `trace`'s textual success label from covered to linked with an explicit semantic limit. Eliminate file-count and numeric visual-score triggers; bounded improvement uses verified findings rather than score inflation. Respect explicit requests for strict workflows, scoring or delegation.
- R7: Consolidate command-execution behavior where it preserves the existing contract: local trust, bounded timeouts, pipeline failures and explicit errors. Do not reuse stale verification results or introduce an automatic cache. Keep legacy commands compatible or document a migration with regression coverage.
- R8: Meaningful tests cover clone sharing, precedence, invalid data, local privacy, path safety, configuration preservation and affected hooks. Run pinned lint, full suites, native Windows checks and CI. Update architecture, usage, sharing, examples and the audit's status. Preserve commits in green-only merges.

- R9: Audit human documentation for stale behavior, conflicting guidance, repetition and broken local links. Keep a short README, a single owning guide per topic, plain English instructions and clear separation from dated evidence.
- R10: During requested onboarding, offer selected external skills from Addy Osmani or Matt Pocock only for a demonstrated gap. Reuse an existing installer, preserve project choices, record origin/revision and dependencies, and document updates. No automatic download or new package manager.

## Implementation milestones

1. Commit the audit and plan. Keep PR #131 independent; merge it once its current CI is green.
2. Implement validated project configuration and stable reads behind the existing CLI. Centralize resolution; update runtime consumers and their tests. Keep trust/activation ownership separate.
3. Configure context locations and connect setup/readiness/scaffolding and tracing. Add realistic two-clone tests and individual-use regressions.
4. Simplify workflow and specialist guidance, clarify trace evidence, and unify bounded command execution only where existing behavior can be retained. Do not add new agents or skills for this work.
5. Rewrite the examples for the delivered behavior, validate all affected paths and checks, publish the next PR and merge after CI. Archive this plan only when implemented work is complete and remaining experiments are clearly listed.

## Deliberate limits

No centralized team service, package-manager distribution, cloud synchronization, automatic specialist router, new model benchmark, blind capability deletion or change to private user settings is required. Do not change installed capability defaults without migration/discovery evidence. Safe deduplication of verification across independent invocations and model-outcome comparisons remain follow-ups unless implementation provides a complete freshness contract. Report deferred items honestly rather than claiming the entire roadmap is solved.


## Delivery and verification

- R1-R5: optional typed project preferences, local/shared/global precedence, stable reads and shared paths are implemented. Clone tests cover propagation while keeping execution trust local; solo use needs no profile.
- R6: formal trace IDs, three-file documentation delegation and numeric visual gates are removed as universal requirements. Trace labels describe textual links; improvement rounds use verified findings and explicit limits.
- R7: verifier and legacy fast/Stop checks share bounded Bash execution and pipeline failure behavior. Independent invocations still rerun commands; no unsafe cache was added.
- R8: all 24 suites were exercised locally. The remaining single-manual documentation assumption was corrected and the CLI suite rerun: 394 checks passed. Pinned lint and content validation passed. Configuration has 17 behavioral cases; native Windows passed with two symlink-permission skips, and verification passed 23 cases with one such skip. CI includes the new suite on Linux, macOS and Windows.
- R9: the documentation audit records twelve findings. README is 114 lines rather than 379; daily usage is 75 rather than 508. The content validator now checks local human-document links and anchors. The new logo and README were inspected in light/dark desktop previews; no mobile-browser coverage is claimed.
- R10: external skill selection is part of requested onboarding, with a dedicated guide and origin/revision/dependency policy. The base installer makes no added downloads. Prepared model-evaluation cases remain unrun; no third-party collection is bundled or claimed universally compatible.

Deferred experiments: real-model quality/cost comparison for the new direction, lighter installation profiles and cross-invocation verification scheduling. They require evidence and a freshness contract, not another generic workflow rule. No additional paid-model benchmark was run for this implementation.
