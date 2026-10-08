# Working across branches

Use when `tack config collaboration --get` is `team`, or a task explicitly coordinates parallel work. This preference is separate from task mode; a small team bug can still be lite. Solo work needs no coordination ceremony, and can use `tack team` when useful.

## Before changing a shared interface

Read the canonical contract and the handoff relevant to this task. Several active handoffs are an index of parallel work, not instructions to resume somebody else's task. Check branch, current code and known base history before trusting a claim. A commit merged long ago may have been reverted.

Identify which component consumes the change, the owner/PR of overlapping work and whether a dependency is planned, implemented on a branch or available in the known base. Reuse existing issue/PR discussion and contracts. Ask about unresolved interface decisions; do not create a new diary for every task. Producing and consuming assistants follow `project-docs/references/integration.md` when a handoff is useful.

## Before opening or integrating a PR

Keep one coherent change per branch and preserve unrelated work. Refresh remote knowledge when authorized and appropriate, then run:

```bash
tack team --base origin/main --against origin/feat/frontend
```

Use the real integration/parallel refs; the example does not imply those branches exist. The diagnostic never fetches. Its successful exit means inspection finished; read each `merge.status` (`clean`, `conflict`, `unknown`) and the uncommitted-change notice. Overlapping files need review even when Git merges cleanly. An unknown probe needs a supported Git version, missing history or manual inspection; never describe it as conflict-free.

Run relevant project checks, including actual contract/integration tests when a producer changes a consumer's assumptions. For two committed branches, preview `tack team --plan --against REF`, then use `tack team --verify --against REF` after local trust. This runs declared checks in a temporary prospective merge, without modifying the source branch or index. It requires a clean source worktree; ignored files and installed dependencies are not copied or installed. Missing checks or dependencies remain gaps/failures. Inspect tested commit IDs and results. For working-tree changes, `tack verify --plan --base REF` selects checks. Metadata checks and a clean Git merge are not compatibility tests.

Use the project's CI and existing protection or merge queue. Recheck after base/head changes; do not merge using results for an old candidate. Enabling team coordination does not configure GitHub repository rules, publish messages or authorize history rewrites.

## When conflicts occur

Inspect the base and both branches to understand intent. Resolve each conflict so both intended behaviors survive; never use blanket ours/theirs. If the behaviors contradict each other, resolve the product/API decision with the people involved before claiming completion. Follow the project's merge/rebase policy and preserve shared-branch history unless rewriting was explicitly authorized.

Run affected checks after resolution, inspect the final diff and record the decision, source refs and checks in the existing PR or relevant handoff. Update the canonical contract and consumer guidance in the same change. Mention remaining compatibility gaps. Tack can expose known conflicts and guide recovery; concurrent pushes, unseen branches and semantic disagreements can still produce conflicts.
