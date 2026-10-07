# agent-tack

**Dotfiles for AI coding agents** (formerly agent-harness). One install gives Claude Code, Codex, Copilot, Cursor, Gemini, OpenCode and Crush the same instructions and skills (Cursor needs its global rules pasted once). Git-level safety applies to every tool; runtime hooks cover Claude Code, Codex, Gemini CLI and Copilot CLI, plus the command guard in Cursor ([what each tool gets](docs/editors.md#what-each-tool-receives)).

[![CI](https://github.com/nbfrodri/agent-tack/actions/workflows/ci.yml/badge.svg)](https://github.com/nbfrodri/agent-tack/actions/workflows/ci.yml)

## What it does

- **One workflow, scaled to the task:** plan, test first, small commits, docs, review; light for a typo, thorough for a risky change.
- **Rules that are enforced, not just suggested:** git hooks (every tool) and the Claude Code and Codex hooks block AI attribution, committed secrets, force-pushes to `main`, dangerous commands and merges with red or unfinished CI. The command guard catches an assistant's mistakes; it is not a sandbox against a determined one, so run untrusted or fully unattended work in a container or VM ([what it covers](docs/how-it-works.md#what-the-command-guard-covers-and-what-it-does-not)).
- **Enforcement depends on the tool:** Claude Code gets everything; Codex, Gemini CLI and Copilot CLI get shared runtime checks through native adapters; Cursor gets the command guard; OpenCode and Crush rely on instructions and git hooks ([per tool](docs/editors.md#what-each-tool-receives)).
- **Opt-in per project:** everywhere else the assistant works normally with only the safety net on.
- **Yours to change:** rules, skills, modes and toggles are plain files and commands. [Why →](docs/why.md)
- **Learns project procedures:** during authorized implementation, the assistant can create useful local skills and specialist roles, index them for later sessions and reuse what already exists. Shared-catalog promotion stays separate. [Project capabilities →](docs/usage.md#project-skills-and-roles)

## Quick start

Requirements: Linux, macOS or Windows with WSL2; `git`, `bash`, `python3` or `jq`; at least one supported AI tool.

```bash
git clone https://github.com/nbfrodri/agent-tack.git ~/Projects/agent-tack
~/Projects/agent-tack/install.sh      # keep the checkout there: installed files link to it

cd ~/Projects/my-app
tack enable                           # turn the workflow on; add --scaffold for four base guidance files
```

Restart your AI tools, then work as usual: *"Add Google login"*, *"Fix issue #12"*, *"What would you improve?"*, *"Prepare a release"*.

For initialization, `tack enable --scaffold` creates missing guidance from repository evidence. The assistant then analyzes the project, asks which useful optional files to add and remembers your choices. `tack setup` shows the inventory; `tack setup --check` finds incomplete guidance. Plain activation creates no project files. [Project initialization →](docs/usage.md#project-initialization)

Preview with `./install.sh --dry-run` (the first install lists every hook it adds; `--no-hooks` adds none), check with `tack doctor`, update with `git pull && ./install.sh`, remove with `./uninstall.sh`. [Installation details →](docs/usage.md#installation-diagnostics-and-removal) · [Editors and WSL →](docs/editors.md)

## Modes

The mode decides how much process each task gets. `auto` is the default and picks a level per task.

| Mode | For | What the assistant does |
| --- | --- | --- |
| `lite` | Typos, config, small fixes; small tasks when tokens matter | Minimal self-contained rules, selected reply style (brief by default); still branch, commit and test (it absorbed the former `lean` mode, [measured](docs/benchmarks/2026-10-04-lean.md) at the same cost) |
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
| `tack setup` / `--check` | Inspect project foundations / check guidance readiness without running project code |
| `tack log` | What the hooks did recently (opt in with `tack config activity-log true`) |
| `tack trust` | Allow automatic formatting and the fast check in this checkout |
| `tack disable` | Turn the workflow off for this project |

Run `tack help` for everything. [Usage →](docs/usage.md)

## What's included

- **Skills:** a core workflow (`dev-workflow`) plus process skills (debugging, testing, releases, issues, reviews, delegation) and stack skills (frontend, APIs, databases, auth, deployment…).
- **Agents:** planner, implementer, reviewers (code, security, performance, architecture, UI), test and docs writers.
- **Hooks:** commit conventions, secret scanning, a command guard (including green-only merges), auto-format, a fast check after edits, a check before the assistant stops (uncommitted work, code changed without a test, failing tests in trusted projects) and an opt-in activity log.
- **Claude Code mods:** a usage band with the active tack mode and your 5-hour and weekly limits, and a live pane of what the agent is doing.

[Full list →](docs/components.md) · [How it works →](docs/how-it-works.md)

## How it compares

Other ways to shape an AI coding agent, and where agent-tack differs (as of October 2026):

| | A hand-written `AGENTS.md` / `CLAUDE.md` | Large plugin collections (e.g. [ECC](https://github.com/affaan-m/ECC)) | agent-tack |
| --- | --- | --- | --- |
| Approach | Instructions per project | A broad catalog: hundreds of skills, agents and commands you pick from and invoke | One opinionated workflow applied automatically, scaled per task by mode |
| How you use it | The model reads it | You start workflows with commands (`/plan`, `/code-review`…) and install the parts you need | `tack enable`, then ask as usual; the mode decides the process |
| Enforcement | None | Claude Code hooks, configured with environment variables | Git hooks (any tool, even manual commits) plus a command guard in Claude Code and Codex (Cursor: the command guard); toggles per project with `tack config` |
| Tools | One file per tool | Claude Code first, adapters for many others | Claude Code, Codex, Copilot, Cursor, Gemini, OpenCode and Crush from one install (Cursor's global rules pasted once); rules in `AGENTS.md`, agent hooks in Claude Code and Codex, the command guard in Cursor |
| Context cost | What you write | Grows with what you install; selective install recommended | Small core; documents and skills load on demand |
| Footprint | None | Node.js runtime and packages | Bash and git, plus `python3` or `jq` |

Pick a catalog when you want breadth and choose workflows yourself; pick agent-tack when you want the same disciplined process in every project and tool, enforced by git everywhere and by agent hooks where the tool supports them, with little setup. They are not meant to be installed together: both add session hooks and overlapping rules.

## Results

Measured on real Claude Code sessions, plain assistant versus tack, with hidden acceptance tests the assistant never sees. Other models and tools can give different numbers ([method, limits and every table](docs/results.md)):

| | Plain assistant | tack (`auto`) |
| --- | --- | --- |
| Path traversal from user input, smaller model (`claude-haiku-4-5`, 5 runs): every trap handled | 0/5 | 4/5 |
| Path traversal, larger model (`claude-opus-5-5`, 2 runs) | 2/2 | 2/2 |
| SQL search on user input, smaller model (5 runs): every trap handled | 0/5 | 0/5 |
| Bug fix, new project and project conventions (Haiku and Opus): hidden tests pass | all | all |
| Work on a branch with Conventional Commits | no run | every Opus run; most Haiku runs |
| Cost | 1× | 1.1–1.9× |

tack changed the outcome in one of two hidden-risk scenarios: the smaller model handled path traversal once tack had it pick the level by risk, while in a SQL search both conditions missed the same `LIKE` wildcard trap. On plain tasks it changes the process (branch, commits, tests) at a modest cost.

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
