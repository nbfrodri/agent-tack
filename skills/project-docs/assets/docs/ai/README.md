# AI in this project

## Assistants
| Tool | Model | Configuration |
| --- | --- | --- |
| Claude Code | | Global config: agent-tack (skills, hooks); project: `AGENTS.md`, `.mcp.json` |
| Codex | | Global config: agent-tack (skills, AGENTS.md) |

## What the AI does on its own
- Plans, code, tests and docs on feature branches, with Conventional Commits and git hooks enforcing the rules.

## What needs a human
- Push, PRs and merges; anything touching production, secrets, payments or data deletion; dependency additions; final review of every PR.

## Records
- [log.md](log.md): what the AI did, task by task.
- [prompts.md](prompts.md): requests that worked well here.
