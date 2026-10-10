<p align="center">
  <img src="docs/assets/tack-logo.png" alt="tack geometric t mark" width="144" height="144">
</p>
<h1 align="center">tack</h1>
<p align="center"><strong>My AI coding configuration, in one repository.</strong></p>
<p align="center">The same instructions, skills, agents, hooks and checks on every machine and in every AI tool.</p>
<p align="center">
  <a href="https://github.com/nbfrodri/agent-tack/actions/workflows/ci.yml"><img src="https://github.com/nbfrodri/agent-tack/actions/workflows/ci.yml/badge.svg" alt="CI status"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-0d9488" alt="MIT license"></a>
  <a href="docs/editors.md"><img src="https://img.shields.io/badge/AI_tools-7-0d9488" alt="Seven supported AI tools"></a>
  <img src="https://img.shields.io/badge/runtime-Bash%20%2B%20Python-334155" alt="Bash and Python">
</p>

---

This is a personal configuration, kept in Git so that a new machine or another AI tool works the way the last one did. Installing it links the repository into each tool's own folders; nothing is copied, so an edit here applies everywhere.

It is public so you can read it or fork it. It is not a product: defaults follow one person's preferences and change without notice.

## What it holds

| Piece | Where | Reaches |
| --- | --- | --- |
| Global instructions | `global/AGENTS.md` | Every tool in `targets.txt` |
| Skills and agent roles | `skills/`, `agents/` | Every tool that supports them |
| Sets of skills, agents and plugins for one kind of work | `sets.txt`, with external collections pinned in `sources.txt` | Every tool for skills; Claude Code for plugins |
| Workflow modes and reply styles | `modes/`, `reply-styles.txt` | Enabled projects |
| Git hooks: staged secrets, no AI attribution, Conventional Commits, protected `main` | `git-hooks/` | Every repository |
| Command guard, startup context and completion checks | `hooks/` | Claude Code, Codex and the tools with native hooks |
| Claude Code plugins and mods | `plugins.txt`, `plugins/` | Claude Code |
| Project checks selected from changed paths | `tack verify`, optional `checks-map.json` | Any project, with or without an AI tool |

## Install on a machine

Requires Git, Bash 3.2+ and Python 3.9+. Platform notes are in [tool and platform support](docs/editors.md).

```bash
# Keep this checkout: installed files link to it.
git clone https://github.com/nbfrodri/agent-tack.git ~/Projects/agent-tack
~/Projects/agent-tack/install.sh
```

The installer is idempotent, backs up what it would replace and records what it changed so `./uninstall.sh` can restore it. `tack doctor` reports the state of an installation. [Installation details](docs/installation.md).

## Sets

A set bundles the skills, agents and plugins for one kind of work, such as `design`, `testing`, `security` or `backend`. Skills from other repositories are pinned to a commit and linked for every tool.

```bash
tack set list                 # every set, and where it is active
tack set use design           # this project only
tack set use review --global  # every project, applied by ./install.sh
tack set update               # move pins and see which used skills changed
```

Every active skill adds its description to each session, so activate a set where the work happens. [Sets guide](docs/sets.md).

## In a project

```bash
cd ~/Projects/my-app
tack enable       # local to this clone; adds no project files
tack setup        # clone settings, local differences and existing guidance
```

An enabled project gets the workflow mode (`auto` picks lite, standard or strict per task), startup context and completion checks. `tack verify --plan` shows which declared checks a change selects; `tack trust` allows running them. [Setup](docs/setup.md) | [Daily use](docs/usage.md) | [Verification](docs/verification.md).

Preferences can also be committed for other clones or collaborators with `--shared`. [Sharing](docs/sharing.md) | [Team workflow](docs/teamwork.md).

## Learn more

| I want to... | Guide |
| --- | --- |
| Activate sets of skills, agents and plugins | [Sets](docs/sets.md) |
| Change what this configuration contains | [Customization](docs/customization.md) |
| See the available skills, agents and mods | [Components](docs/components.md) |
| Change settings and context locations | [Configuration](docs/configuration.md) |
| Copy one external skill into an application repository | [External skills](docs/external-skills.md) |
| Understand the implementation | [Architecture](docs/architecture.md) |

[All documentation](docs/README.md).

## Working on this repository

Read [AGENTS.md](AGENTS.md) and [Development](docs/development.md).

```bash
tests/validate.sh
tests/lint.sh
tests/run-all.sh -j 4
```

Tests use temporary homes and repositories. Code and original project assets use the [MIT license](LICENSE); external collections keep their own.
