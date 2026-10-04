# agent-tack

**Dotfiles for AI coding agents** (formerly agent-harness). One install gives Claude Code, Codex, Copilot, Cursor, Gemini, OpenCode and Crush the same instructions, skills and safety rules, so they work like a disciplined senior engineer in every project.

[![CI](https://github.com/nbfrodri/agent-tack/actions/workflows/ci.yml/badge.svg)](https://github.com/nbfrodri/agent-tack/actions/workflows/ci.yml)

## What it does

- **One workflow, scaled to the task:** plan, test first, small commits, docs, review; light for a typo, thorough for a risky change.
- **Rules that are enforced, not just suggested:** git and Claude Code hooks block AI attribution, committed secrets, force-pushes to `main`, dangerous commands and merges with red or unfinished CI.
- **Opt-in per project:** everywhere else the assistant works normally with only the safety net on.
- **Yours to change:** rules, skills, modes and toggles are plain files and commands. [Why →](docs/why.md)

## Quick start

Requirements: Linux, macOS or Windows with WSL2; `git`, `bash`, `python3` or `jq`; at least one supported AI tool.

```bash
git clone https://github.com/nbfrodri/agent-tack.git ~/Projects/agent-tack
~/Projects/agent-tack/install.sh      # keep the checkout there: installed files link to it

cd ~/Projects/my-app
tack enable                           # turn the workflow on for this project
```

Restart your AI tools, then work as usual: *"Add Google login"*, *"Fix issue #12"*, *"What would you improve?"*, *"Prepare a release"*.

Preview with `./install.sh --dry-run`, check with `tack doctor`, update with `git pull && ./install.sh`, remove with `./uninstall.sh`. [Installation details →](docs/usage.md#installation-diagnostics-and-removal) · [Editors and WSL →](docs/editors.md)

## Modes

The mode decides how much process each task gets. `auto` is the default and picks a level per task.

| Mode | For | What the assistant does |
| --- | --- | --- |
| `lean` | Small tasks when tokens matter most | Minimal self-contained rules, terse replies; still branch, commit and test ([measured](docs/benchmarks/2026-10-04-lean.md): about lite cost, ~10% less on new projects) |
| `lite` | Typos, config, one-line fixes | Branch, commit, a test when logic changes |
| `standard` | A bounded feature or bug fix | Adds TDD, a short plan and the affected docs |
| `strict` | Risky or multi-module work | Adds a saved plan you approve, handoffs, review and delegation |
| `unleash` | Unattended work on a branch | Works without asking; the guard still blocks dangerous commands ([risks](docs/usage.md#unleash-autonomous-work)) |

```bash
tack mode strict            # this project
tack mode lite --global     # your default everywhere
tack mode new spike --from lite   # your own mode, in ~/.config/agent-tack/modes/
```

[Modes in detail →](docs/usage.md#workflow-modes)

## Everyday commands

| Command | What it does |
| --- | --- |
| `tack status` | Is the workflow on, which mode, is the formatter trusted |
| `tack config` | List and change feature toggles (delegation, fast check, limits…) |
| `tack doctor` / `--tools` | Diagnose the installation / each installed AI tool |
| `tack log` | What the hooks did recently (opt in with `tack config activity-log true`) |
| `tack trust` | Allow automatic formatting and the fast check in this checkout |
| `tack disable` | Turn the workflow off for this project |

Run `tack help` for everything. [Usage →](docs/usage.md)

## What's included

- **Skills:** a core workflow (`dev-workflow`) plus process skills (debugging, testing, releases, issues, reviews, delegation) and stack skills (frontend, APIs, databases, auth, deployment…).
- **Agents:** planner, implementer, reviewers (code, security, performance, architecture, UI), test and docs writers.
- **Hooks:** commit conventions, secret scanning, a command guard (including green-only merges), auto-format, a fast check after edits, a check before the assistant stops and an opt-in activity log.
- **Claude Code mods:** a usage band with the active tack mode and your 5-hour and weekly limits, and a live pane of what the agent is doing.

[Full list →](docs/components.md) · [How it works →](docs/how-it-works.md)

## How it compares

Other ways to shape an AI coding agent, and where agent-tack differs (as of October 2026):

| | A hand-written `AGENTS.md` / `CLAUDE.md` | Large plugin collections (e.g. [ECC](https://github.com/affaan-m/ECC)) | agent-tack |
| --- | --- | --- | --- |
| Approach | Instructions per project | A broad catalog: hundreds of skills, agents and commands you pick from and invoke | One opinionated workflow applied automatically, scaled per task by mode |
| How you use it | The model reads it | You start workflows with commands (`/plan`, `/code-review`…) and install the parts you need | `tack enable`, then ask as usual; the mode decides the process |
| Enforcement | None | Claude Code hooks, configured with environment variables | Git hooks (any tool, even manual commits) plus a command guard in Claude Code and Codex; toggles per project with `tack config` |
| Tools | One file per tool | Claude Code first, adapters for many others | Claude Code, Codex, Copilot, Cursor, Gemini, OpenCode and Crush from one install; rules in `AGENTS.md`, agent hooks in Claude Code and Codex |
| Context cost | What you write | Grows with what you install; selective install recommended | Small core; documents and skills load on demand |
| Footprint | None | Node.js runtime and packages | Bash and git, plus `python3` or `jq` |

Pick a catalog when you want breadth and choose workflows yourself; pick agent-tack when you want the same disciplined process enforced in every project and tool with little setup. They are not meant to be installed together: both add session hooks and overlapping rules.

## Results

Measured on real sessions with Claude Sonnet 5.5 in Claude Code, plain assistant versus tack. Other models and tools can give different numbers ([method and limits](docs/results.md)):

| | Plain assistant | Lite / Auto | Strict |
| --- | --- | --- | --- |
| Bug fix on a branch with a `fix:` commit and a regression test | 0/2 | 2/2 | 2/2 |
| Cost of a bug fix | 1× | ~2× | 3.5× |
| Cost of a new project | 1× | ~2.2× | waits for your plan approval |

## Learn more

| | |
| --- | --- |
| [Usage](docs/usage.md) | Modes, toggles, startup context, delegation, overrides |
| [Editors and AI tools](docs/editors.md) | VS Code, Cursor, JetBrains, each AI tool, WSL |
| [Customization](docs/customization.md) | Change rules, skills, modes, guard rules and supported tools |
| [How it works](docs/how-it-works.md) · [Architecture](docs/architecture.md) | Installer, hooks, components and flows |
| [Components](docs/components.md) · [Conventions](docs/conventions.md) | Every skill, agent and mod; commit, PR and release rules |
| [Results](docs/results.md) · [Development](docs/development.md) | Benchmarks; tests, evals and contributing |
| [Sharing](docs/sharing.md) · [AI usage](docs/ai/README.md) | Using it on another machine; how AI builds this project |
