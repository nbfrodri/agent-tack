# agent-config

My personal configuration for AI coding assistants (Claude Code, Codex): skills, subagents and global instructions, kept in one place and linked into each tool.

## Structure

```
global/AGENTS.md   # global instructions -> ~/.claude/CLAUDE.md and ~/.codex/AGENTS.md
skills/<name>/     # Agent Skills (SKILL.md + references) -> ~/.agents/skills, ~/.claude/skills, ~/.codex/skills
agents/<name>.md   # Claude Code subagents -> ~/.claude/agents
install.sh         # creates the symlinks (idempotent)
```

## Skills

| Skill | Purpose |
| --- | --- |
| `dev-workflow` | Plan first, TDD, SOLID/DDD, Conventional Commits, GitHub flow, keep docs up to date |

## Install on a new machine

```bash
git clone https://github.com/<user>/agent-config.git ~/agent-config
~/agent-config/install.sh
```

Existing files that would be replaced are moved to `*.bak`.

## Adding a skill or agent

1. Create `skills/<name>/SKILL.md` (or `agents/<name>.md`).
2. Run `./install.sh` to link it.
3. Commit and push.

Because the tools read through symlinks, editing files here takes effect immediately.
