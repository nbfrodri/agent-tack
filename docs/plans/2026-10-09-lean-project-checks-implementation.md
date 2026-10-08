# Plan: a smaller default and executable project agreements

Status: in progress. Baseline: `d6fe887a405d5d0a22d3071b7e0f3d3f2d18cb2d` (PR #137). The user approved the proposed direction and authorized implementation and controlled Codex evaluation. They declined using their other repository; do not claim measurements of their team or human onboarding.

## Outcomes and gates

The previous lifecycle study found no general advantage over a short project guide. More workflow is not an outcome. This change must produce observable benefits before larger model experiments:

1. A fresh default installation exposes only workflow/onboarding skills and no specialist agent catalog. Preserve explicit full-install choices and user-owned/edited files. Record exact default context/catalog sizes against the baseline; do not label characters as tokens.
2. An approved version-1 selection can be checked against both the shared profile and effective local configuration, read-only, with a nonzero exit for missing explicit values or overrides. This detects the observed team-to-solo mistake rather than merely printing configuration.
3. A committed backend change and a committed frontend change can merge cleanly yet fail a real consumer check. An explicit integration verification command must reveal that failure before changing the source branch/index/worktree, show the tested revisions and selected commands, and pass after a compatible fix. No automatic fetching, dependency installation or execution without local trust; missing dependencies/refs/checks remain failures or unknowns.
4. Keep safety controls, relevant tests, pragmatic TDD/SOLID, branches, conventional history and no AI attribution. Load detail only when needed. Avoid repeating project instructions already loaded natively. Do not introduce a general success cache: ignored dependencies and external state make invalidation unreliable without a declared input contract.
5. Compare components against the same short-guide baseline, with ordinary task prompts and independent production-code review. Keep failed attempts, time, token uncertainty and unfavourable outcomes. Retain a change for a proven narrower benefit even if generic code-quality gains remain absent; say exactly which benefit was measured.

## Implementation sequence

1. Reduce `global/AGENTS.md`, `skill-groups.txt` and installer defaults in `features.txt`/`lib/skill-groups.sh`. Add an opt-in specialist-role setting to the existing installer/native adapters and doctor, with safe deselection and migration tests. Keep optional skills in the repository and document re-enabling them. Adapt core references so missing optional skills never block a task.
2. Extend `lib/project_config.py` and CLI help with read-only `tack config --check FILE [--json]`, reusing the validated selection format. Test wrong/missing shared choices, defaults, local overrides, mode and a fresh clone. Onboarding verifies the agreed selection instead of asking settled questions again.
3. Extend `tack team` with explicit `--verify` and `--plan` for one `--against` ref. Use a focused new `lib/integration_verify.py`, the existing Git merge probe primitives and the canonical verifier. Preview and execution inspect the same pinned prospective merge; every command runs in its temporary checkout. Reject dirty input rather than silently claiming it was included. Default `team` stays a read-only diagnostic. Test clean/conflicting/missing refs, semantic failure, correction, no checks, local trust, budgets and preservation of source Git state.
4. Simplify startup context and workflow reads; measure duplicate context removed. Do not weaken guard/secret checks or manufacture tests/documents for file-count compliance. Update architecture and owning human guides, keeping README brief.
5. Run offline acceptance, install/uninstall preservation, pinned lint and the complete suite. Record before/after footprint and a deterministic three-way integration example where branch tests pass and the merged consumer check fails.
6. Freeze candidate, fixture and controller hashes before model calls. Run a bounded component comparison using existing isolated Codex helpers (plain guide, previous tack, reduced core), counterbalanced repeated ordinary requests and identical public facts/checks. Evaluate targeted integration and setup-check correctness directly without model calls: this isolates executable checks from prompting the assistant to use them and avoids a fourth speculative model condition. Use independent anonymous code review and a held-out numeric-unit integration variant; no tuning against measured deliveries or selective retries. The fixed scope and limitations are in `evals/lean-protocol.md`. Publish the complete outcome and decide whether the default earns its cost.
7. Conventional commits without AI attribution, PR with concrete validation, current-head CI, merge when green. Update the delivery record with actual results and unresolved outcome goals.

## Scope and migration

No hosted service, skill registry, broad autonomous orchestrator, automatic clone execution or promise to prevent all conflicts. Existing shared project settings and per-task modes remain supported. Reinstall applies the new default only where the user did not save a different choice; document how to keep the full catalog. Removed managed links must not erase user content or lose uninstall restoration metadata.

The real-repository pilot is unavailable by the user's choice. Controlled examples establish executable behavior, not measured human savings. A faster model run alone does not establish better code; a green merge alone does not establish consumer compatibility.
