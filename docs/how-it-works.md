# How it works

What the installer sets up, which tools it supports, and which rules are enforced by hooks.

Internal component responsibilities and execution flows: [architecture](architecture.md).

## Supported tools
Paths come from each tool's documentation and live in `targets.txt` (add a line to support another tool).

| Tool | Global instructions | Skills | Agents and hooks |
| --- | --- | --- | --- |
| Claude Code | `~/.claude/CLAUDE.md` | `~/.claude/skills` | ✔ |
| Codex | `~/.codex/AGENTS.md` | `~/.codex/skills` | ✔ (generated `~/.codex/agents/*.toml`, hooks in `~/.codex/hooks.json`) |
| Gemini CLI | `~/.gemini/GEMINI.md` | `~/.agents/skills` | — |
| GitHub Copilot (CLI, and Copilot Chat in VS Code) | `~/.copilot/copilot-instructions.md` | `~/.copilot/skills` | — |
| OpenCode | `~/.config/opencode/AGENTS.md` | `~/.agents/skills` | — |
| Crush | `~/.config/AGENTS.md` | `~/.agents/skills` | — |
| Cursor (editor and CLI) | none on disk: paste `global/AGENTS.md` in *Customize → Rules* once | `~/.agents/skills` | — |

Claude Code and Codex are always configured; the others only when installed. The Copilot line is detected through the `copilot` CLI or VS Code (`code`, `code-insiders`, `codium`). Git hooks apply to every tool.

### VS Code

- **Claude Code and Codex extensions** use the same configuration as their CLIs (`~/.claude`, `~/.codex`), so they get tack's instructions, skills, agents, hooks and mods without extra steps.
- **GitHub Copilot Chat** reads the user instructions in `~/.copilot/copilot-instructions.md` and the skills in `~/.agents/skills`, `~/.claude/skills` and `~/.copilot/skills`, all installed by tack. In a project, it also reads `AGENTS.md` when the `chat.useAgentsMdFile` setting is on, which the installer turns on. Claude Code hooks, mods and subagents do not apply to Copilot; the git hooks still do.

### `targets.txt` columns
One line per tool; `-` means unsupported or none. Files with only the first five columns still work.

| Column | Meaning |
| --- | --- |
| `tool`, `when`, `commands` | Name, `always` or `detect`, and the commands that detect it |
| `instructions`, `skills` | Global instructions file and extra skills directory |
| `agents`, `hooks` | Subagents directory and hooks file the installer fills (Claude Code only today) |
| `min_version` | Oldest supported version; older ones only produce a warning |
| `smoke` | Arguments of a non-interactive diagnostic (`doctor`, `doctor,--summary`) |

`tack doctor --tools` reads these columns: for each installed tool it prints the version, the configured capabilities, whether the minimum is met and the result of the smoke check. Missing tools are skipped; a failed smoke check or an old version is a warning; a broken managed link is an error. Tool output is never printed, so credentials and config values stay out of reports.

### Codex agents and hooks
Codex 0.160.0 supports both (`codex features list`: `hooks` and `multi_agent` stable). Per its official documentation, agents are TOML files in `~/.codex/agents/` (`name`, `description`, `developer_instructions`) and hooks live in `~/.codex/hooks.json` or `config.toml`. Tack agents are Markdown with Claude frontmatter and the hook scripts expect Claude Code's payload, so the installer does not write either for Codex yet; the `agents` and `hooks` columns stay `-` until a converter and a payload check exist.

**Platforms:** Linux and macOS (tested in CI). On Windows, use it inside WSL, where it works as on Linux; native Windows (PowerShell/CMD) isn't supported yet.

## What the installer does
| Step | Details |
| --- | --- |
| Instructions and skills | Links `global/AGENTS.md` and every skill of the selected groups (`skill-groups.txt`, `tack config skill-groups`) into each tool's paths (above) and into `~/.agents/skills`; removes its own links to skills of deselected groups. |
| Agents | Links `agents/*.md` into `~/.claude/agents`. |
| Settings | Deep-merges `claude/settings.json` into `~/.claude/settings.json`; your keys and your own hooks are kept, hooks tagged `#tack` are replaced. |
| Git hooks | Points the global `core.hooksPath` at `git-hooks/`, unless you use a different one. |
| Command | Links `bin/tack` into `~/.local/bin`, and the repo into `~/.agents/tack`. |
| Plugins | Adds the marketplaces in `plugins.txt` and installs or updates each plugin. |
| Mods | Adds the local marketplace `agent-tack-mods` (the repo's `plugins/` folder) and installs or updates each mod in it, so Claude Code loads them in every session without flags. |
| VS Code | When `code`, `code-insiders` or `codium` is on `PATH`, adds `"chat.useAgentsMdFile": true` to that editor's user `settings.json` so Copilot Chat loads each project's `AGENTS.md`. It creates the file if absent, never changes an existing value, and leaves a file with comments or trailing commas alone (with a warning). Skip it with `git config --global tack.vscodeAgentsMd false`; `--skip-plugins` does not skip it. Uninstall removes the key only if it still holds the installed value, and deletes a file the installer created only if nothing else is in it. |
| Migration | Cleans up installs from when the project was called agent-config. |

Safety: existing files are moved to `<name>.bak-<timestamp>`, never overwritten; an invalid `settings.json` is left untouched; links of deleted skills are pruned; missing tools are skipped with a warning; a failed step doesn't stop the rest and makes the exit code non-zero. Re-running is always safe. `--skip-plugins` works offline.

## Mods
Mods are small Claude Code plugins that change its interface; this repo ships two in `plugins/` (see [components](components.md#mods)). The installer registers `plugins/` as a local marketplace (`claude plugin marketplace add`) and installs each mod from it with `claude plugin install`, which survives `git pull` and needs no `--plugin-dir` flag. Claude Code copies a mod when it installs it, so after changing a mod bump its `version` in `plugin.json` and re-run `./install.sh` to update it. If the checkout moved, the installer notices that the marketplace points to the old folder and re-adds it from the new one.

- Mods install by default. Skip them with `./install.sh --skip-mods`, or for good with `git config --global tack.mods false` (absent means enabled). `--skip-plugins` skips mods too, so an offline or local-only run never calls the Claude CLI.
- `--dry-run` lists what would happen without calling Claude.
- Only what the installer installed is recorded as owned. A mod or marketplace you already had is updated but never removed. `./uninstall.sh` uninstalls the recorded mods, then the marketplace if the installer added it.
- `tack doctor` warns when the claude CLI is missing, a mod is not installed or disabled, and notes when mods are turned off by configuration.

## Enforced rules (hooks)
| Hook | Where | What it does |
| --- | --- | --- |
| `pre-commit` | git (global) | Runs the repo's local pre-commit, then refuses `.env` files (not `.env.example`) and well-known credential formats in the final staged changes. Handles exact filenames and blocks commits when inspection fails. |
| `commit-msg` | git (global) | Removes AI attribution everywhere; in enabled projects, rejects subjects that aren't Conventional Commits. |
| `pre-push` | git (global) | Refuses force-pushes and deletions of `main`/`master`. In enabled projects, only annotated `vX.Y.Z` tags, never moved or deleted. |
| Other git hooks | git (global) | Pass through to each repo's own `.git/hooks/*` (client and server side). |

A deliberate one-off override is an environment variable on the command: `TACK_ALLOW_SECRETS=1` (pre-commit), `TACK_ALLOW_FORCE_PUSH=1` and `TACK_ALLOW_TAG=1` (pre-push). `git-hooks/_chain` checks them, and the former `HARNESS_ALLOW_*` names still work.
| `fast-check.sh` | Claude Code `PostToolUse` (`Write`, `Edit`, `MultiEdit`) | In an enabled and locally trusted project with `tack config check-fast` set, runs that command from the repository root (60-second timeout where `timeout` exists) and returns a failure with the last 40 output lines to the assistant. |
| `stop-check.sh` | Claude Code `Stop` | In an enabled project (unless `tack config stop-check false`), asks the assistant once to continue when there is uncommitted work, a failing fast check, a handoff that is `handoff-stale-commits` (3) code commits behind or behind pushed work, or a changed file whose docs in `docs-map.txt` did not change on the branch; a second stop is never blocked. |
| `budget.sh` | Claude Code `PreToolUse` (every tool) | In an enabled project running a project-only mode such as `unleash`, counts the session's tool calls and refuses them past `tack config unleash-max-tool-calls`; silent otherwise. |
| `session-context.sh` | Claude Code `SessionStart` | Supplies activation status, the workflow mode and its rules (`tack mode show`), non-default token settings (`reply-style`, `skill-loading`, `subagent-model`) and workflow settings (`ci-watch`), up to three candidate lessons as unconfirmed hints (`tack lesson`), and the startup context the mode's `Context:` line asks for through `tack context` (project instructions; an index or excerpts of architecture and the active handoff); runs again after context compaction. |
| `guard-bash.sh` | Claude Code `PreToolUse` | Performs bounded shell analysis. Blocks recognised catastrophic commands and hook bypasses; asks before destructive operations, unsupported executable constructs or exceeded parsing limits. Structural rules (git, `rm`, wrappers, shells) live in `hooks/claude/lib/guard-*.sh`, one library per family of commands; pattern rules (database clients, destructive SQL, database resets) live in `guard-policy.txt`, and users can add ask or deny rules in `~/.config/agent-tack/guard-policy.txt`. In enabled projects, before `gh pr merge` it reads the pull request's checks with `gh` (4-second limit): failing checks deny the merge, pending ones deny unless `--auto` is used, and checks it cannot read, or a merge after `cd` or with `GH_REPO`, ask (`tack config merge-requires-green`). |
| `hooks/cursor/guard.sh` | Cursor `beforeShellExecution` | Adapter: passes the command to `guard-bash.sh` and returns its decision as Cursor's `permission` (`allow`, `ask` or `deny`) with the reason; allows when it cannot read the input. |
| `format-file.sh` | Claude Code `PostToolUse` | In enabled, locally trusted projects, formats each edited file with the project's own formatter. |

The advisory hooks (`session-context`, `fast-check`, `stop-check`, `format-file`) first ask `hooks/claude/lib/hook-control.sh` whether `tack config disabled-hooks` lists them; the guard and `budget.sh` never ask.

With `tack config activity-log true`, `session-context.sh`, `guard-bash.sh` and `stop-check.sh` also append what they did (session start and mode, deny or ask decisions, Stop findings) to `${XDG_STATE_HOME:-~/.local/state}/agent-tack/activity.log` through `hooks/claude/lib/activity-log.sh`, labelled `claude` or `codex` (Codex runs them with `--codex`); `tack log` prints the newest entries. At each stop, `stop-check.sh` also passes the transcript to `hooks/claude/lib/turn-report.py`, which reads only the lines added since the session's last stop (offsets in the state directory's `turns/`) and returns tokens per model, skills, subagents and the stated level for the log; `lib/log-report.py` turns the log into `tack log --cost`, `--skills` and `--levels`.

Repos with their own local `core.hooksPath` (e.g. Husky) use only their hooks; there, Claude's `attribution` setting still prevents its trailers.

### What the command guard covers, and what it does not

The guard is a safety net for an assistant's mistakes, not a sandbox against a determined one. It judges each shell command before it runs:

- **Refuses:** hook bypasses (`--no-verify`, `core.hooksPath`), force-pushing or deleting `main`, recursive deletes of `/`, `HOME` or a folder that holds it (paths are resolved, so `rm -rf ../../..` counts).
- **Asks:** recursive deletes, `find -delete` or `find -exec rm` outside the project, deletes whose target only the shell can work out (`$(…)`, variables, `{a,b}`, `~user`), anything inside `.git`, rewriting remote history, merges with red or pending CI, database wipes, infrastructure and device commands (`gh repo delete`, `terraform`/`tofu destroy` and `apply -destroy`, `kubectl delete`, `mkfs`, `dd` to a device), code a shell or interpreter reads from standard input (`curl … | bash`, `bash -s`, `| python3`, `source /dev/stdin`), your own rules, and commands it cannot analyse (loops, dynamic commands).

It does **not** cover: overwriting files through redirection (`> ~/.bashrc`, `truncate`, `cp /dev/null …`), moving files out of the way (`mv ~/.ssh …`), `rsync --delete`, destructive commands of tools it does not know, interpreters outside its list (`deno`, `bun`, `pypy`, `fish`, `busybox sh`), anything run inside a script file, and actions taken through tools other than the shell (editors, MCP servers). Add rules for your own risky commands in `~/.config/agent-tack/guard-policy.txt`; for untrusted work, use a container or VM.

## Repository layout
```
global/AGENTS.md      # global instructions for every AI tool
skills/<name>/        # Agent Skills (SKILL.md + references/ + assets/)
agents/<name>.md      # Claude Code subagents
targets.txt           # supported AI tools and their paths
claude/settings.json  # Claude Code settings and hooks
hooks/claude/         # Claude hooks (lib/shell-parse.py plus .sh bridge/fallback: parsing)
git-hooks/            # global git hooks
bin/tack           # per-project switch
plugins.txt           # Claude Code plugins
plugins/<name>/       # mods shipped with tack (local marketplace)
install.sh            # installer (lib/: settings merge in Python and jq)
tests/  evals/        # automated tests and behaviour evals
docs/                 # this documentation, audits and AI log
```

The guard's Python parser supports commands up to 65,536 characters, with limits on tokens, substitutions, policy checks and nesting. The Bash-only fallback accepts short inputs up to 1,024 characters and asks for review of uncertain syntax. These checks supplement normal tool permissions; they do not execute or fully interpret arbitrary shell programs. The guard runs before every shell command, so it is kept fast: about 110 ms for a compound command on Linux, and `tests/guard.test.sh` fails when the median of five runs exceeds 200 ms (`TACK_GUARD_BUDGET_MS`; CI and `tests/run-all.sh` allow 500 ms for slower or busy machines).
