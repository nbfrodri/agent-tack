# agent-config

My personal configuration for AI coding assistants (Claude Code, Codex): skills, subagents, global instructions, settings and plugins, kept in one place and installed with one command.

[![CI](https://github.com/nbfrodri/agent-config/actions/workflows/ci.yml/badge.svg)](https://github.com/nbfrodri/agent-config/actions/workflows/ci.yml)

## Install on a new machine

```bash
git clone https://github.com/nbfrodri/agent-config.git ~/Projects/agent-config
~/Projects/agent-config/install.sh
```

Then restart Claude Code and Codex. Re-run `./install.sh` at any time (after `git pull`, or after adding a skill): it's idempotent.

What it does:

| Step | Details |
| --- | --- |
| Global instructions | Links `global/AGENTS.md` to `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md` |
| Skills | Links each `skills/<name>/` into `~/.agents/skills`, `~/.claude/skills` and `~/.codex/skills` |
| Subagents | Links each `agents/<name>.md` into `~/.claude/agents` |
| Settings | Deep-merges `claude/settings.json` into `~/.claude/settings.json` (your other keys and your own hooks are kept) |
| Git hooks | Sets the global `core.hooksPath` to `git-hooks/` (unless you already use a different one) |
| Plugins | Adds the marketplaces in `plugins.txt`, refreshes them, and installs or **updates to the latest version** each plugin, enabling it if it was disabled |

Safety guarantees:

- Existing files and folders are never overwritten. They're moved to `<name>.bak-<timestamp>`.
- An invalid `settings.json` is left untouched and reported.
- Links left behind by skills or agents deleted from this repo are removed. Links that don't point into this repo are never touched.
- Missing tools don't break the install:
  - without `claude`, the plugins step is skipped with a warning;
  - without `python3`, settings are merged with `jq`, and if neither is available you get a warning.
- A failing step is reported, the rest still runs, and the exit code is non-zero, so you know to re-run.
- `./install.sh --skip-plugins` skips the plugin step, e.g. when offline.
- Works on Linux and macOS (including macOS's bash 3.2). CI tests both on every push.

## On/off per project

The full workflow (plan, TDD, conventions, docs, handoffs, AI log, Conventional Commits, auto-format) is **opt-in per project**. Everywhere else the AI works normally and only the safety net stays on.

```bash
agent-config enable            # this clone only (git config; nothing added to the repo)
agent-config enable --shared   # commit a .agent-config file so it travels with the repo
agent-config disable
agent-config status            # enabled / disabled
git config --global agentconfig.enabled true   # enable everywhere (a local `disable` still wins)
```

| | Enabled project | Any other repo |
| --- | --- | --- |
| Command guard, protection of `main` | ✔ | ✔ |
| AI attribution removed from commits | ✔ | ✔ |
| Conventional Commits enforced | ✔ | — |
| Full workflow and auto-format | ✔ | — |

Claude Code is told the status at session start (`SessionStart` hook); Codex checks `agent-config status` as its instructions say. `new-project` enables new projects automatically.

## Enforced rules (hooks)

Skills and instructions guide the AI; hooks **enforce** the rules that matter, whatever the AI (or you) does.

| Hook | Where | What it does |
| --- | --- | --- |
| `commit-msg` | git (global) | Removes AI attribution (`Co-Authored-By` of Claude, Codex, Copilot…, "Generated with…") everywhere, and in enabled projects rejects subjects that aren't Conventional Commits. Merge, revert and `fixup!`/`squash!` messages are accepted. |
| `pre-push` | git (global) | Refuses force-pushes and deletions of `main`/`master` on any remote. One-off override: `AGENT_CONFIG_ALLOW_FORCE_PUSH=1 git push …` |
| Other git hooks | git (global) | Pass through to each repository's own `.git/hooks/*` (client and server side, e.g. `post-receive` in local bare repos), so pre-commit, lefthook or custom hooks keep working. |
| `session-context.sh` | Claude Code `SessionStart` | Tells Claude whether the project is enabled. |
| `guard-bash.sh` | Claude Code `PreToolUse` | **Blocks** force-pushing main, `--no-verify`, `rm -rf` of `/`, `~` or `..`. **Asks first** for `reset --hard`, `clean -f`, discarding changes, deleting branches, force-pushing other branches, recursive deletes outside the project, and dropping/resetting databases. |
| `format-file.sh` | Claude Code `PostToolUse` | In enabled projects, formats each edited file with the formatter the project already has configured (Biome, Prettier, Ruff, Black, Pint, gofmt, rustfmt). Projects without one are left alone. |

Git hooks apply to Claude, Codex, any other tool and your own commits. Notes:

- In a repository with different commit conventions: `git config agentconfig.conventionalCommits false` (AI attribution is still removed).
- Repositories that set their own local `core.hooksPath` (e.g. Husky) use only their hooks; there, Claude's `attribution` setting still prevents its trailers.
- Claude hooks are tagged `#agent-config` in `settings.json`; re-installing replaces only those.

## Structure

```
global/AGENTS.md      # global instructions for every AI assistant
bin/agent-config      # per-project switch, linked into ~/.local/bin
skills/<name>/        # Agent Skills (SKILL.md + references/), used by Claude Code and Codex
agents/<name>.md      # Claude Code subagents
claude/settings.json  # Claude Code settings and hooks merged into ~/.claude/settings.json
hooks/claude/         # Claude Code hook scripts
git-hooks/            # global git hooks (commit-msg, pre-push, pass-through)
plugins.txt           # Claude Code marketplaces and plugins
install.sh            # installer (idempotent)
tests/                # installer, hooks and skill/agent tests, run in CI
evals/                # behaviour evals with real Claude/Codex sessions (manual, uses tokens)
```

## Skills

| Skill | Purpose |
| --- | --- |
| `dev-workflow` | Plan first, TDD, SOLID/DDD, Conventional Commits, GitHub flow, docs; code and git conventions in `references/conventions.md` |
| `project-docs` | Docs for humans (`README`, `docs/`) and AIs (`AGENTS.md`): technical sheet, architecture, ADRs, plans, audits, handoffs, AI usage log; templates |
| `github-issues` | Work from an issue to a PR that closes it, write issues, split plans into issues; issue and PR templates |
| `lessons` | Turn corrections and preferences into versioned rules in the right file |
| `orchestrate` | On request: split a plan into tasks for subagents in isolated worktrees, recommend model and effort per task, integrate and review |
| `improve` | Review existing code or a project and propose prioritised improvements; always asks scope and focus first, then runs the reviewers |
| `git-history` | Amend, fixup, squash, undo and recover commits; tidy a branch before push |
| `release` | SemVer, next version from commits, CHANGELOG, tags, GitHub Releases, release-please |
| `debugging` | Reproduce → regression test → isolate → verify hypothesis → fix the root cause |
| `testing` | What and how to test per layer; references for pytest, Pest/PHPUnit and Vitest/Jest |
| `new-project` | Scaffold a project with tests, lint, CI, README, AGENTS.md and Conventional Commits |
| `frontend` | React/Next.js components, Server vs Client Components, state, forms, accessibility, component tests |
| `api-design` | REST conventions, errors, validation, pagination, OpenAPI; references for Python, Laravel and Node |
| `database` | Modelling, safe migrations, indexes, N+1, transactions; references for PostgreSQL, MySQL and MongoDB |
| `auth` | Sessions vs tokens, OAuth, password hashing, CSRF, RBAC, multi-tenancy, auth tests |
| `e2e-testing` | Playwright: resilient locators, auth state, test data, flaky tests, CI |
| `deployment` | Docker, CI/CD, environments, migrations on deploy, rollbacks; references for Vercel, VPS and AWS |
| `observability` | Structured logs, request IDs, Sentry, health checks, metrics, alerts |

Skills use the open Agent Skills format (`SKILL.md`), so both Claude Code and Codex can use them.

## Agents

| Agent | Purpose |
| --- | --- |
| `planner` | Read-only architect: plan, DDD model, test strategy and commit breakdown before coding |
| `code-reviewer` | Read-only review of the diff/branch: bugs, security, tests, SOLID/DDD, conventions, docs |
| `test-writer` | Adds tests to existing code (coverage gaps, characterisation tests); never edits production code |
| `docs-writer` | Keeps README, AGENTS.md, docs/, .env.example, CHANGELOG and ADRs in sync; logs AI work |
| `security-auditor` | Read-only full-stack security audit: OWASP Top 10, auth, injection, secrets, dependencies, infra |
| `performance-analyzer` | Measures and ranks performance problems: Web Vitals, bundle, API latency, DB queries, caching |
| `implementer` | Implements one planned task in its own branch/worktree following the workflow; used by `orchestrate` |
| `architecture-reviewer` | Read-only architecture review of existing code: layering, coupling, boundaries, debt hot spots |
| `ui-reviewer` | Reviews a running app in the browser at mobile and desktop widths: hierarchy, consistency, states, accessibility |

Agents use the Claude Code subagent format and are installed to `~/.claude/agents`.

## Plugins

| Plugin | Purpose |
| --- | --- |
| `context7` | Up-to-date library documentation, so the AI doesn't rely on outdated APIs |
| `frontend-design` | Distinctive, polished UI design |

Browser control is already built in (Claude in Chrome for Claude Code, the browser tools bundled with Codex), so no browser MCP is installed. For databases, see `skills/database/references/mcp.md` (read-only, per project).

To add one, add a `plugin <name>@<marketplace>` line to `plugins.txt` (and a `marketplace` line if it comes from a new marketplace), then run `./install.sh`.

## Adding a skill or agent

1. Create `skills/<name>/SKILL.md` (or `agents/<name>.md`) with `name` and `description` frontmatter; the name must match the folder or file name.
2. Run `tests/validate.sh` and `./install.sh`.
3. Commit and push. CI validates it and tests the installer.

Because the tools read through symlinks, editing files here takes effect immediately (restart the tool for new skills or agents).

## Conventions at a glance

| | |
| --- | --- |
| Commits | Conventional Commits, English, no AI attribution (enforced by hooks) |
| PRs | Squash merge; the PR title is the commit on `main` |
| Code | English; formatter defaults; functional first; no unnecessary comments |
| JS/TS | pnpm, TypeScript strict, kebab-case files, named exports |
| Python | uv, Ruff, mypy/pyright |
| PHP | Composer, Pint, Larastan, Pest |
| Docs | Simple and concise; `AGENTS.md` for AIs, `docs/` shared; plans, audits, handoffs and AI log in `docs/` |

Full details: `skills/dev-workflow/references/conventions.md`.

## Behaviour evals

`evals/run.sh <scenario>` runs a real Claude Code or Codex session on a throwaway repo, and `evals/grade.py` checks what it did (commits, TDD order, tests, docs, release steps). They use real tokens, so run them by hand after changing skills.

## Development

```bash
shellcheck -x install.sh bin/agent-config tests/*.sh evals/run.sh git-hooks/_chain git-hooks/commit-msg git-hooks/pre-push hooks/claude/*.sh
tests/validate.sh                  # validate skills, agents and plugins.txt
tests/install.test.sh              # test the installer in throwaway HOME directories
tests/hooks.test.sh                # test git and Claude Code hooks in throwaway repositories
```
