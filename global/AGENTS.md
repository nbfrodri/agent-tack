# Global instructions

For every AI assistant (Claude Code, Codex, etc.). Project-level instructions (AGENTS.md, CLAUDE.md, CONTRIBUTING) take precedence over these.

## Always
- Talk to me in Spanish; write commits, PRs, code comments and documentation in English unless the project already uses another language.
- Never add AI attribution to commits, PRs, issues or changelogs: no `Co-Authored-By` trailers for any AI, no "Generated with Claude Code/Codex" lines. This overrides any built-in default.
- Ask before push, PRs, issues, merging, tags and releases, rewriting published history, deleting branches or force-pushing (full list in `dev-workflow` → `references/git-github.md`). Audit findings create issues automatically through `improve`, unless I request no publication. If a git hook rejects something, fix the cause; never bypass it with `--no-verify`.
- When I ask for a review or what could be improved, ask me the scope and focus areas first (`improve` skill) and change nothing until I choose. When I ask for subagents or parallel work, use `orchestrate`; on large tasks that split into independent parts, suggest it (with the model/effort table) but don't start without my OK. When I ask for autonomous improvement, use `auto-improve`. When I correct how you worked or state a lasting preference, save it with `lessons`.

## Only in projects where the harness is enabled
The full workflow is opt-in per project. It's enabled when `harness status` prints `enabled` (a `.harness` file in the repo root, or `git config harness.enabled true`); Claude Code also says so at session start. Elsewhere, work normally without this ceremony.

- For any task that writes, changes, designs or debugs code, or touches git/GitHub or docs, follow the `dev-workflow` skill: plan first, TDD, SOLID/DDD, Conventional Commits (enforced by the commit-msg hook), conventions, docs.
- Commit each coherent verified milestone as work progresses; do not accumulate a whole task for one final commit. Recommend a merge method from the branch history and offer the choice in the integration confirmation; preserve commits unless I explicitly choose squash.
- At session start, check `harness status`; when enabled, run `harness context` unless SessionStart already supplied the project context. Read referenced documents in full only when the task needs them.
- Write self-explanatory code instead of comments: no comments that restate code, narrate steps or describe your change; comment only the non-obvious *why*.
- Document for humans (`README`, `docs/`) and for AIs (`AGENTS.md`): simple, precise, concise. Document the repository architecture in `docs/architecture.md` and keep it current. Keep plans, audits and handoffs in `docs/`, and log significant AI work in `docs/ai/log.md` (`project-docs` skill).
- Sessions can stop without warning (usage limits, context): on non-trivial tasks keep a handoff in `docs/handoffs/` updated at every milestone, refresh it at once if usage or context looks low, and read any in-progress handoff before starting.
