# agent-harness

**Dotfiles for AI coding agents.** One install gives Claude Code, Codex, Copilot, Cursor, Gemini, OpenCode and Crush the same instructions, skills and safety rules, so they work like a disciplined senior engineer in every project.

[![CI](https://github.com/nbfrodri/agent-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/nbfrodri/agent-harness/actions/workflows/ci.yml)

## What it does

- **One workflow, scaled to the task:** plan, test first, small commits, docs, review; light for a typo, thorough for a risky change.
- **Rules that are enforced, not just suggested:** git and Claude Code hooks block AI attribution, committed secrets, force-pushes to `main` and dangerous commands.
- **Opt-in per project:** everywhere else the assistant works normally with only the safety net on.
- **Yours to change:** rules, skills, modes and toggles are plain files and commands. [Why →](docs/why.md)

## Quick start

Requirements: Linux, macOS or Windows with WSL2; `git`, `bash`, `python3` or `jq`; at least one supported AI tool.

```bash
git clone https://github.com/nbfrodri/agent-harness.git ~/Projects/agent-harness
~/Projects/agent-harness/install.sh      # keep the checkout there: installed files link to it

cd ~/Projects/my-app
harness enable                           # turn the workflow on for this project
```

Restart your AI tools, then work as usual: *"Add Google login"*, *"Fix issue #12"*, *"What would you improve?"*, *"Prepare a release"*.

Preview with `./install.sh --dry-run`, check with `harness doctor`, update with `git pull && ./install.sh`, remove with `./uninstall.sh`. [Installation details →](docs/usage.md#installation-diagnostics-and-removal) · [Editors and WSL →](docs/editors.md)

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
harness mode strict            # this project
harness mode lite --global     # your default everywhere
harness mode new spike --from lite   # your own mode, in ~/.config/agent-harness/modes/
```

[Modes in detail →](docs/usage.md#workflow-modes)

## Everyday commands

| Command | What it does |
| --- | --- |
| `harness status` | Is the workflow on, which mode, is the formatter trusted |
| `harness config` | List and change feature toggles (delegation, fast check, limits…) |
| `harness doctor` / `--tools` | Diagnose the installation / each installed AI tool |
| `harness trust` | Allow automatic formatting and the fast check in this checkout |
| `harness disable` | Turn the workflow off for this project |

Run `harness help` for everything. [Usage →](docs/usage.md)

## What's included

- **Skills:** a core workflow (`dev-workflow`) plus process skills (debugging, testing, releases, issues, reviews, delegation) and stack skills (frontend, APIs, databases, auth, deployment…).
- **Agents:** planner, implementer, reviewers (code, security, performance, architecture, UI), test and docs writers.
- **Hooks:** commit conventions, secret scanning, a command guard, auto-format, a fast check after edits and a check before the assistant stops.
- **Claude Code mods:** a usage band with your 5-hour and weekly limits, and a live pane of what the agent is doing.

[Full list →](docs/components.md) · [How it works →](docs/how-it-works.md)

## Results

Measured on real sessions, plain assistant versus the harness ([method and limits](docs/results.md)):

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
