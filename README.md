# agent-harness

**A portable, versioned harness for AI coding agents.** The instructions, skills, agents, hooks and conventions that make Claude Code, Codex, Cursor, Copilot, Gemini, OpenCode or Crush work like a disciplined senior engineer, installed on any machine with one command. Think of it as *dotfiles for AI agents*.

[![CI](https://github.com/nbfrodri/agent-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/nbfrodri/agent-harness/actions/workflows/ci.yml)

## Why
Out of the box, AI assistants forget your conventions every session, skip tests, write giant commits signed by the AI, and can force-push `main`. This harness gives them one consistent workflow (plan → TDD → small commits → docs → review) and **enforces** the rules that matter with hooks, opt-in per project. [More →](docs/why.md)

## At a glance
| | |
| --- | --- |
| **Workflow** | `dev-workflow` with code, git and release conventions |
| **Process skills** | `new-project`, `debugging`, `testing`, `git-history`, `release`, `github-issues`, `project-docs`, `improve`, `orchestrate`, `auto-improve`, `lessons` |
| **Stack skills** | `frontend`, `api-design`, `database`, `auth`, `e2e-testing`, `deployment`, `observability` |
| **Agents** | `planner`, `implementer`, `code-reviewer`, `test-writer`, `docs-writer`, `evaluator`, `architecture-reviewer`, `security-auditor`, `performance-analyzer`, `ui-reviewer` |
| **Enforced by hooks** | Conventional Commits, no AI attribution, protected `main` and tags, a guard against dangerous commands, auto-format |
| **Tools** | Claude Code, Codex, Cursor, GitHub Copilot CLI, Gemini CLI, OpenCode, Crush |
| **Quality** | ~260 tests on Linux and macOS; [measured results](docs/results.md) |

Details: [components](docs/components.md) · [how it works](docs/how-it-works.md) · [conventions](docs/conventions.md).

## Install
1. Requirements: Linux, macOS or Windows with WSL; `git`, `bash`, `python3` or `jq`, and at least one supported AI tool. Recommended: `gh`, logged in.
2. Clone and install:
   ```bash
   git clone https://github.com/nbfrodri/agent-harness.git ~/Projects/agent-harness
   ~/Projects/agent-harness/install.sh
   ```
3. Read any warning it prints (e.g. Cursor needs its global rules pasted once), and make sure `~/.local/bin` is in your `PATH`.
4. Restart your AI tools.

## Use
```bash
cd ~/Projects/my-app
harness enable      # turn the full workflow on for this project (off by default)
```
Then work as usual: "Añade login con Google", "Trabaja en el issue #12", "¿Qué mejorarías?", "Mejóralo solo hasta un 8", "Haz una release". `harness disable` turns it off. [Usage →](docs/usage.md)

Update with `git pull && ./install.sh`. Sharing it with someone else: [sharing](docs/sharing.md).

## Results
Same tasks, same tool, 12 real sessions ([method and full tables](docs/results.md)):

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
| [Components](docs/components.md) | Every skill, agent and plugin |
| [Conventions](docs/conventions.md) | Commits, PRs, releases, code, docs |
| [Results](docs/results.md) | Measured with vs without the harness |
| [Sharing](docs/sharing.md) | Using it on someone else's machine |
| [Development](docs/development.md) | Tests, evals, adding skills and tools |
| [AI usage](docs/ai/README.md) | How AI is used to build this project |
