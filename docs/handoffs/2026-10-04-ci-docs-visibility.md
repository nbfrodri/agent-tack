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
  7. `code-reviewer` findings fixed: `bf98a6d` closes a pre-existing guard bypass (an assignment with a slash, `X=a/b cmd`, hid the command) and hardens the merge check (enabled projects only, `--auto` may wait, `--disable-auto` skipped, asks after `cd` or with `GH_REPO`, watchdog without `timeout(1)`); `506e590` makes the activity log private (600), rotates it per process, keeps the mode chip in an atom and realigns `tack help`.
  8. `61e368e` docs gaps closed at the owner's request: README feature lists, editors, why and the docs delegation note in usage.
- Issues opened at the owner's request from a review of affaan-m/ECC: #41–#53 (enhancements; #53 covers support for any editor through thin adapters). #54: screenshots of visual changes in `.tack/screenshots/` (git-ignored) scored by a fresh-context subagent (owner's choices).
- Verified: full ShellCheck and all 15 suites pass locally on the final tree. Pushed; PR #55 open.
- CI run 1 failed `install (ubuntu-latest)` on a racy cli check (`grep -q` plus `pipefail` passed locally by SIGPIPE timing); fixed in `8e94736` by counting toggle names from the full listing.
- CI run 2 failed `install (macos-latest)`: without `timeout(1)` the 6-second watchdog plus startup passed the test's 8 seconds and neared the hook's 10. `c188f17` bounds both paths to about 4 seconds and resolves `bin/tack` absolutely (a guard started by a relative path let merges through).
- Next: wait for CI on #55 (fix failures from the log), merge with a merge commit (owner authorised), delete the branch locally and remotely, mark this handoff done.
- Follow-ups noted: rename the repo's own `.harness` marker to `.tack`; the `harness` alias will be removed in a later release; the owner asked about shipping tack as a Claude Code plugin (proposed: a plugin for the Claude part next to `install.sh`; no issue yet).
