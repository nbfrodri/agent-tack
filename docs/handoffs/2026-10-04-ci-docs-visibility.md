# CI watching, delegated docs and visibility

- Status: in progress (implementation and docs done; pushing, PR, CI and merge next)
- Branch: `feat/ci-docs-visibility` from `main` at `447d228` (after PR #40, the rename to tack)
- Plan: `docs/plans/2026-10-04-ci-docs-visibility.md` (approved, owner answers recorded there)
- Context: the GitHub repository is `nbfrodri/agent-tack` and the checkout lives in `~/Projects/agent-tack`. The rules delete merged branches locally and remotely without asking (`c8341ba`, `33895e3`). The owner must approve the Codex hooks again with `/hooks`: the Stop and SessionStart commands now pass `--codex`.
- Done:
  1. `629a9b2` guard: `gh pr merge` denied while checks fail or are pending, asks when `gh` cannot tell (`merge-requires-green`, default true).
  2. `42b368a` `ci-watch` (instruction, default true) in `standard`, `strict`, `unleash` and `dev-workflow`; SessionStart says so when it is off.
  3. `1cdc58c` docs delegation to `docs-writer` (3+ files; never ADRs or design); validation keeps it on `sonnet` or `haiku`.
  4. `8338f39` `tack · <mode>` chip in the usage band (mod 0.4.0); `f545d52` opt-in activity log (`tack config activity-log true`, `tack log`) from SessionStart, the guard and the Stop check, for Claude Code and Codex.
  5. `fd04fc1` installer re-adds the mods marketplace when it points to a former checkout path.
  6. Docs: usage (CI, activity log), editors, customization, components, how-it-works, architecture; README "How it compares" section (requested by the owner); `AGENTS.md` rule that tack must serve any model and editor.
- Issues opened at the owner's request from a review of affaan-m/ECC: #41–#53 (enhancements; #53 covers support for any editor through thin adapters).
- Next: full ShellCheck and every suite, push, PR, wait for CI, merge with a merge commit (owner authorised), delete the branch, mark this handoff done.
- Follow-ups noted: rename the repo's own `.harness` marker to `.tack`; the `harness` alias will be removed in a later release; the owner asked about shipping tack as a Claude Code plugin (proposed: a plugin for the Claude part next to `install.sh`; no issue yet).
