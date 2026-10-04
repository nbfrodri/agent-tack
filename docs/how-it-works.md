# How it works

What the installer sets up, which tools it supports, and which rules are enforced by hooks.

Internal component responsibilities and execution flows: [architecture](architecture.md).

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

### `targets.txt` columns
One line per tool; `-` means unsupported or none. Files with only the first five columns still work.

| Column | Meaning |
| --- | --- |
| `tool`, `when`, `commands` | Name, `always` or `detect`, and the commands that detect it |
| `instructions`, `skills` | Global instructions file and extra skills directory |
| `agents`, `hooks` | Subagents directory and hooks file the installer fills (Claude Code only today) |
| `min_version` | Oldest supported version; older ones only produce a warning |
| `smoke` | Arguments of a non-interactive diagnostic (`doctor`, `doctor,--summary`) |

`harness doctor --tools` reads these columns: for each installed tool it prints the version, the configured capabilities, whether the minimum is met and the result of the smoke check. Missing tools are skipped; a failed smoke check or an old version is a warning; a broken managed link is an error. Tool output is never printed, so credentials and config values stay out of reports.

### Codex agents and hooks
Codex 0.160.0 supports both (`codex features list`: `hooks` and `multi_agent` stable). Per its official documentation, agents are TOML files in `~/.codex/agents/` (`name`, `description`, `developer_instructions`) and hooks live in `~/.codex/hooks.json` or `config.toml`. The harness agents are Markdown with Claude frontmatter and the hook scripts expect Claude Code's payload, so the installer does not write either for Codex yet; the `agents` and `hooks` columns stay `-` until a converter and a payload check exist.

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
| `pre-commit` | git (global) | Runs the repo's local pre-commit, then refuses `.env` files (not `.env.example`) and well-known credential formats in the final staged changes. Handles exact filenames and blocks commits when inspection fails. |
| `commit-msg` | git (global) | Removes AI attribution everywhere; in enabled projects, rejects subjects that aren't Conventional Commits. |
| `pre-push` | git (global) | Refuses force-pushes and deletions of `main`/`master`. In enabled projects, only annotated `vX.Y.Z` tags, never moved or deleted. |
| Other git hooks | git (global) | Pass through to each repo's own `.git/hooks/*` (client and server side). |
| `session-context.sh` | Claude Code `SessionStart` | Supplies activation status, workflow mode, project instructions and an index (excerpts in strict mode) of architecture and the active handoff through `harness context`; runs again after context compaction. |
| `guard-bash.sh` | Claude Code `PreToolUse` | Performs bounded shell analysis. Blocks recognised catastrophic commands and hook bypasses; asks before destructive operations, unsupported executable constructs or exceeded parsing limits. Structural rules (git, `rm`, wrappers, shells) live in the script; pattern rules (database clients, destructive SQL, database resets) live in `guard-policy.txt`, and users can add ask or deny rules in `~/.config/agent-harness/guard-policy.txt`. |
| `format-file.sh` | Claude Code `PostToolUse` | In enabled, locally trusted projects, formats each edited file with the project's own formatter. |

Repos with their own local `core.hooksPath` (e.g. Husky) use only their hooks; there, Claude's `attribution` setting still prevents its trailers.

## Repository layout
```
global/AGENTS.md      # global instructions for every AI tool
skills/<name>/        # Agent Skills (SKILL.md + references/ + assets/)
agents/<name>.md      # Claude Code subagents
targets.txt           # supported AI tools and their paths
claude/settings.json  # Claude Code settings and hooks
hooks/claude/         # Claude hooks (lib/shell-parse.py plus .sh bridge/fallback: parsing)
git-hooks/            # global git hooks
bin/harness           # per-project switch
plugins.txt           # Claude Code plugins
install.sh            # installer (lib/: settings merge in Python and jq)
tests/  evals/        # automated tests and behaviour evals
docs/                 # this documentation, audits and AI log
```

The guard's Python parser supports commands up to 65,536 characters, with limits on tokens, substitutions, policy checks and nesting. The Bash-only fallback accepts short inputs up to 1,024 characters and asks for review of uncertain syntax. These checks supplement normal tool permissions; they do not execute or fully interpret arbitrary shell programs.
