# Global instructions

For every AI assistant (Claude Code, Codex, etc.). Project-level instructions (AGENTS.md, CLAUDE.md, CONTRIBUTING) take precedence over these.

## Always
- Talk to me in Spanish; write commits, PRs, code comments and documentation in English unless the project already uses another language.
- Never add AI attribution to commits, PRs, issues or changelogs: no `Co-Authored-By` trailers for any AI, no "Generated with Claude Code/Codex" lines. This overrides any built-in default.
- Ask before push, PRs, issues, merging, tags and releases, rewriting published history, deleting branches or force-pushing (full list in `dev-workflow` → `references/git-github.md`). Audit findings create issues automatically through `improve`, unless I request no publication. If a git hook rejects something, fix the cause; never bypass it with `--no-verify`.
- When I ask for a review or what could be improved, ask me the scope and focus areas first (`improve` skill) and change nothing until I choose. When I ask for subagents or parallel work, use `orchestrate`; outside enabled projects, suggest delegation for large separable tasks and wait for my OK. When I ask for autonomous improvement, use `auto-improve`. When I correct how you worked or state a lasting preference, save it with `lessons`.

## Only in projects where the harness is enabled
The workflow is opt-in per project: enabled when `harness status` prints `enabled` (a `.harness` file in the repo root, or `git config harness.enabled true`); Claude Code also says so at session start, with the mode. Elsewhere, work normally without this ceremony.

- For any task that writes, changes, designs or debugs code, or touches git/GitHub or docs, follow `dev-workflow` at the level set by `harness mode`: `auto` (default) picks lite, standard or strict per task and states it in one line; a fixed mode applies that level. I can change the level for any task. At every level: work on a branch off `main`, test the change, and make a Conventional Commit for each verified milestone.
- Ask me whenever you have a real doubt about scope, behaviour, design or risk; don't guess. Decide alone only purely conventional details, and say what you chose.
- Make the smallest change that does the job, keep code modular, and update everything it affects (callers, tests, CLI help, docs) in the same change. If the design no longer scales for the request, tell me and propose options before restructuring.
- Delegate automatically through `orchestrate` only at the strict level, after the plan is approved, unless `git config harness.delegation` is `off`; at lite and standard, suggest delegation and wait for my OK.
- Commit each coherent verified milestone as work progresses. Recommend a merge method from the branch history and offer the choice in the integration confirmation; preserve commits unless I explicitly choose squash.
- At session start or resume, check `harness status`; when enabled, run `harness context` unless SessionStart already supplied it. Always read the active handoff it lists and verify it against git before continuing. Read other referenced documents in full only when the task needs them.
- Write self-explanatory code instead of comments; comment only the non-obvious *why*.
- Docs, plans, handoffs and the AI log scale with the level as `dev-workflow` defines; keep `docs/architecture.md` current when structure changes.
