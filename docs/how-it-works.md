# How it works

What the installer sets up, which tools it supports, and which rules are enforced by hooks.

## Supported tools
Paths come from each tool's documentation and live in `targets.txt` (add a line to support another tool).

| Tool | Global instructions | Skills | Agents and hooks |
| --- | --- | --- | --- |
| Claude Code | `~/.claude/CLAUDE.md` | `~/.claude/skills` | ✔ |
| Codex | `~/.codex/AGENTS.md` | `~/.codex/skills` | — |
| Gemini CLI | `~/.gemini/GEMINI.md` | `~/.agents/skills` | — |
| GitHub Copilot CLI | `~/.copilot/copilot-instructions.md` | `~/.copilot/skills` | — |
| OpenCode | `~/.config/opencode/AGENTS.md` | `~/.agents/skills` | — |
| Crush | `~/.config/AGENTS.md` | `~/.agents/skills` | — |
| Cursor (editor and CLI) | none on disk: paste `global/AGENTS.md` in *Customize → Rules* once | `~/.agents/skills` | — |

Claude Code and Codex are always configured; the others only when installed. Git hooks apply to every tool.

**Platforms:** Linux and macOS (tested in CI). On Windows, use it inside WSL, where it works as on Linux; native Windows (PowerShell/CMD) isn't supported yet.

## What the installer does
| Step | Details |
| --- | --- |
| Instructions and skills | Links `global/AGENTS.md` and every skill into each tool's paths (above) and into `~/.agents/skills`. |
| Agents | Links `agents/*.md` into `~/.claude/agents`. |
| Settings | Deep-merges `claude/settings.json` into `~/.claude/settings.json`; your keys and your own hooks are kept, hooks tagged `#harness` are replaced. |
| Git hooks | Points the global `core.hooksPath` at `git-hooks/`, unless you use a different one. |
| Command | Links `bin/harness` into `~/.local/bin`, and the repo into `~/.agents/harness`. |
| Plugins | Adds the marketplaces in `plugins.txt` and installs or updates each plugin. |
| Migration | Cleans up installs from when the project was called agent-config. |

Safety: existing files are moved to `<name>.bak-<timestamp>`, never overwritten; an invalid `settings.json` is left untouched; links of deleted skills are pruned; missing tools are skipped with a warning; a failed step doesn't stop the rest and makes the exit code non-zero. Re-running is always safe. `--skip-plugins` works offline.

## Enforced rules (hooks)
| Hook | Where | What it does |
| --- | --- | --- |
| `commit-msg` | git (global) | Removes AI attribution everywhere; in enabled projects, rejects subjects that aren't Conventional Commits. |
| `pre-push` | git (global) | Refuses force-pushes and deletions of `main`/`master`. In enabled projects, only annotated `vX.Y.Z` tags, never moved or deleted. |
| Other git hooks | git (global) | Pass through to each repo's own `.git/hooks/*` (client and server side). |
| `session-context.sh` | Claude Code `SessionStart` | Tells Claude whether the project is enabled. |
| `guard-bash.sh` | Claude Code `PreToolUse` | Parses commands like a shell. Blocks force-pushing main, `--no-verify`, hook-path overrides and `rm -rf` of `/`, `~` or `..`; asks before discarding work, deleting branches, force-pushing other branches or wiping databases. |
| `format-file.sh` | Claude Code `PostToolUse` | In enabled projects, formats each edited file with the project's own configured formatter. |

Repos with their own local `core.hooksPath` (e.g. Husky) use only their hooks; there, Claude's `attribution` setting still prevents its trailers.

## Repository layout
```
global/AGENTS.md      # global instructions for every AI tool
skills/<name>/        # Agent Skills (SKILL.md + references/ + assets/)
agents/<name>.md      # Claude Code subagents
targets.txt           # supported AI tools and their paths
claude/settings.json  # Claude Code settings and hooks
hooks/claude/         # Claude Code hook scripts
git-hooks/            # global git hooks
bin/harness           # per-project switch
plugins.txt           # Claude Code plugins
install.sh            # installer
tests/  evals/        # automated tests and behaviour evals
docs/                 # this documentation, audits and AI log
```
