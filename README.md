# agent-harness

**A portable, versioned harness for AI coding agents.** The instructions, skills, agents, hooks and conventions that make Claude Code, Codex, Cursor, Copilot, Gemini, OpenCode or Crush work like a disciplined senior engineer, installed on any machine with one command. Think of it as *dotfiles for AI agents*.

[![CI](https://github.com/nbfrodri/agent-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/nbfrodri/agent-harness/actions/workflows/ci.yml)

## Why
Out of the box, AI assistants forget your conventions every session, skip tests, write giant commits signed by the AI, and can force-push `main`. This harness gives them one consistent workflow (plan → TDD → small commits → docs → review), scaled to each task, and **enforces** the rules that matter with hooks, opt-in per project. [More →](docs/why.md)

## At a glance
| | |
| --- | --- |
| **Workflow** | `dev-workflow` with lite, standard and strict levels (auto-selected by default) and code, git and release conventions |
| **Process skills** | `new-project`, `debugging`, `testing`, `git-history`, `release`, `github-issues`, `project-docs`, `improve`, `orchestrate`, `auto-improve`, `lessons` |
| **Stack skills** | `frontend`, `api-design`, `database`, `auth`, `e2e-testing`, `deployment`, `observability` |
| **Agents** | `planner`, `implementer`, `code-reviewer`, `test-writer`, `docs-writer`, `evaluator`, `architecture-reviewer`, `security-auditor`, `performance-analyzer`, `ui-reviewer` |
| **Enforced by hooks** | Conventional Commits, no AI attribution, no secrets or `.env` committed, protected `main` and tags, a guard against dangerous commands, auto-format |
| **Tools** | Claude Code, Codex, Cursor, GitHub Copilot CLI, Gemini CLI, OpenCode, Crush |
| **Quality** | 560 automated checks; CI targets Linux and macOS; [measured results](docs/results.md) |

Details: [architecture](docs/architecture.md) · [components](docs/components.md) · [how it works](docs/how-it-works.md) · [conventions](docs/conventions.md).

## Install
1. Requirements: Linux, macOS or Windows with WSL; `git`, `bash`, `python3` or `jq`, and at least one supported AI tool. Recommended: `gh`, logged in.
2. Clone and install. The path below is an example; replace `~/Projects/agent-harness` in both commands with any directory where you want to keep the repository:
   ```bash
   git clone https://github.com/nbfrodri/agent-harness.git ~/Projects/agent-harness
   ~/Projects/agent-harness/install.sh
   ```
   Keep the repository at that path after installation: the installed files are symlinks to it. If you move it, run `install.sh` again from its new location.
   Preview changes with `./install.sh --dry-run`; add `--skip-plugins` to configure local files without plugin operations. Run `harness doctor` after installation to diagnose links, settings, Git hooks and project state without changing anything.
3. Read any warning it prints (e.g. Cursor needs its global rules pasted once), and make sure `~/.local/bin` is in your `PATH`.
4. Restart your AI tools.

To uninstall, run `./uninstall.sh --dry-run` first, then `./uninstall.sh` from the checkout. Uninstall requires `python3`; it restores only recorded, unchanged harness-owned state and preserves user edits, project files and shared plugins. Existing configuration from installations without ownership records is not automatically claimed. [Installation and removal →](docs/usage.md#installation-diagnostics-and-removal)

## Use
```bash
cd ~/Projects/my-app
harness enable      # turn the workflow on for this project (off by default)
harness mode        # auto by default; also lite, standard or strict
```
**Workflow modes:** in `auto` the assistant picks a level per task (lite for small changes, standard for bounded features and fixes, strict for risky or multi-module work) and says which. Lighter levels skip plans, handoffs, logs and subagents to save tokens and time; hooks enforce the same safety rules in every mode. Set your default with `harness mode lite --global` and override it per project with `harness mode strict`. [Modes →](docs/usage.md#workflow-modes)
Project instructions, architecture and an active handoff are loaded as bounded startup context. Automatic formatting also needs `harness trust` for the local checkout; `harness status` shows both activation and formatter trust. Run `harness help` for commands and examples. [Context and trust →](docs/usage.md#startup-context-and-formatter-trust)
Complex independent strict-level tasks are delegated automatically after plan approval; lighter levels suggest delegation and ask. Disable it with `git config harness.delegation off`. [Delegation and integration choices →](docs/usage.md#automatic-delegation-and-integration-choices)
Then work as usual: "Add Google login", "Work on issue #12", "What would you improve?", "Improve it autonomously until it scores 8/10", "Prepare a release". `harness disable` turns it off. [Usage →](docs/usage.md)

Update with `git pull && ./install.sh`. Sharing it with someone else: [sharing](docs/sharing.md).

## Customize
Make the harness your own after cloning it: change the rules, workflow, skills, agents, supported tools, plugins and hooks to fit your preferences. Keep personal changes in your own clone or fork. [Customization guide →](docs/customization.md)

## Results
Historical results from 12 real sessions with the original grading heuristics (including a test-order metric since corrected) ([method, full tables and limitations](docs/results.md)):

| | Plain assistant | With the harness |
| --- | --- | --- |
| Committed its work | 2/6 runs | 6/6 |
| Test written before the code | 0/4 | 4/4 |
| AI attribution left in history | 2/6 | 0/6 |
| New project with CI, docs for humans and AIs, release setup | 0/2 | 2/2 |
| Cost and time | 1× | ~2× focused tasks, ~6× a new project |

## Documentation
| Doc | |
| --- | --- |
| [Why](docs/why.md) | The problem, the solution, strengths and limits |
| [Usage](docs/usage.md) | On/off, what to ask, overrides, updating |
| [How it works](docs/how-it-works.md) | Supported tools, installer, hooks, layout |
| [Architecture](docs/architecture.md) | Components, dependencies, installation and runtime flows |
| [Customization](docs/customization.md) | Adapt the harness to your preferences and keep personal changes |
| [Components](docs/components.md) | Every skill, agent and plugin |
| [Conventions](docs/conventions.md) | Commits, PRs, releases, code, docs |
| [Results](docs/results.md) | Measured with vs without the harness |
| [Sharing](docs/sharing.md) | Using it on someone else's machine |
| [Development](docs/development.md) | Tests, evals, adding skills and tools |
| [AI usage](docs/ai/README.md) | How AI is used to build this project |
