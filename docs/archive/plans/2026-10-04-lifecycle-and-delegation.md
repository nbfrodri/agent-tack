# Lifecycle tools, automatic delegation and reevaluation

- Status: done (implementation complete; the paused benchmark was replaced by the workflow-modes benchmark)
- Approval: owner requested a new evaluation and implementation of doctor, installation preview, safe uninstall and a new benchmark; chose automatic delegation by complexity and six real runs of one representative scenario.
- Baseline: `422cfd4`; previous initial audit score 7.4/10. Reevaluation must score current evidence, not planned work.

## Work and acceptance criteria

1. Evaluate the current whole repository for architecture, code, tests, security, performance, docs and tooling. Keep the earlier personal-use, incremental-change focus. Save an evidence-based scorecard and create deduplicated issues for verified findings.
2. Implement read-only `harness doctor`: tool availability, installed symlinks, Claude settings validity, effective Git hooks and current project activation/trust. Missing optional tools are warnings; invalid or broken managed installation components cause a nonzero result. No secrets or configuration values are printed beyond managed paths/states.
3. Add `install.sh --dry-run`: report planned links, backups, settings, Git and plugin operations without modifying HOME, repository permissions, Git config or plugin state. Temporary scratch files may be used.
4. Add reversible installation metadata and `uninstall.sh [--dry-run]`: remove only unchanged harness-owned links/settings/Git configuration, restore displaced user state where safe, preserve changes made after installation, and never remove project files or uninstall shared plugins automatically. All mutation tests use isolated HOME/XDG/Git configuration.
5. Change global/workflow/orchestration guidance to automatic delegation for complex separable tasks, with capability-aware model/effort routing and isolated worktrees. Keep small tasks direct. Explain instruction-driven behavior and tool capability limits. Add per-project enable/disable guidance and a delegation opt-out.
6. Freeze the final configuration and run three harness and three baseline executions of one representative bug-fix scenario. Record model/provider/CLI versions, prompt and harness revisions, metric version and conditions. Use real sessions only when credentials work; report unavailable evidence accurately. Do not publish raw credentials or transcripts.
7. Integrate focused commits, review the combined diff, run all suites and ShellCheck, update architecture, README, usage and AI log. Re-score after verification. No push, PR, merge or release is requested for this task yet.

## Ownership and sequence

- Lifecycle agent (GPT-6 Astra, high): `install.sh`, `uninstall.sh`, installation ownership helpers and lifecycle tests. Preserve existing Python/jq fallback behavior. Define and document the ownership manifest interface before dependent diagnostics are integrated.
- Diagnostics agent (GPT-6.1 Sol, medium): `lib/doctor.sh`, doctor tests. Parent owns `bin/harness` dispatch/help. Test the library directly with the checkout root as its argument.
- Benchmark agent (GPT-6.1 Sol, medium): eval metadata/reproducibility and tests, then real benchmark after parent signals a frozen revision. Parent owns published result docs.
- Parent: CLI dispatch, delegation policy, documentation, audit issues, integration and final evaluation.

Uninstall must not assume that any path containing "harness" is owned. Keep original ownership evidence across reinstallations and defend against changed link targets and parent directories. Benchmark runs must not observe configuration edits mid-run.

## Outcome

Lifecycle tools, automatic delegation, contextual integration choices, documentation and all five verified findings are implemented in focused local commits. The [audit](../audits/2026-10-04-improvement-agent-harness.md) records the final score and checks. The six-run benchmark has two interrupted attempts and four pending; the owner chose to save and resume when Claude's session limit resets. No new comparison is claimed. The [benchmark handoff](https://github.com/nbfrodri/agent-harness/blob/4a7b55f/docs/handoffs/2026-10-04-benchmark.md) retains the exact frozen revision, protocol and remaining authorisation. The owner subsequently authorised pushing the feature branch, creating [PR #32](https://github.com/nbfrodri/agent-harness/pull/32) and integrating it after CI passes, preserving the separate commits.
