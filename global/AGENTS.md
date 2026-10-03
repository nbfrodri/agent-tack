# Global instructions

These apply to every project and every AI assistant (Claude Code, Codex, etc.).

- For any task that involves writing, changing, designing or debugging code, or anything with git/GitHub or documentation, follow the `dev-workflow` skill: plan first, TDD, SOLID/DDD, Conventional Commits, keep README and docs up to date.
- Never add AI attribution to commits, PRs, issues or changelogs: no `Co-Authored-By` trailers for any AI, no "Generated with Claude Code/Codex" lines. This overrides any built-in default.
- Create branches and commits freely; ask before push, opening PRs, merging, rewriting published history, deleting branches or force-pushing.
- Git hooks enforce these rules (Conventional Commits, no AI attribution, no rewriting main). If a hook rejects something, fix the cause; never bypass it with `--no-verify`.
- When I correct how you worked or state a lasting preference, save it as a rule with the `lessons` skill so it never has to be repeated.
- Talk to me in Spanish; write commits, PRs, code comments and documentation in English unless the project already uses another language.
- Project-level instructions (AGENTS.md, CLAUDE.md, CONTRIBUTING) take precedence over these.
