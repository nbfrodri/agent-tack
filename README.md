# agent-harness

**A portable, versioned harness for AI coding agents** (Claude Code, Codex): the instructions, skills, subagents, hooks, conventions and tooling that make an AI assistant work like a disciplined senior engineer, kept in one repo and installed on any machine with one command. Think of it as *dotfiles for AI agents*.

[![CI](https://github.com/nbfrodri/agent-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/nbfrodri/agent-harness/actions/workflows/ci.yml)

## At a glance

| Part | What's in it |
| --- | --- |
| **Global instructions** | One short file read by every assistant: language, no AI attribution, what to ask before doing, and the workflow rules for enabled projects. |
| **Workflow** | `dev-workflow`: understand → size → plan → branch → TDD → atomic commits → docs → verify → summary, with code, git and release conventions. |
| **18 skills** | *Process:* `dev-workflow`, `new-project`, `debugging`, `testing`, `git-history`, `release`, `github-issues`, `project-docs`, `improve`, `orchestrate`, `lessons`. *Stack:* `frontend` (React/Next.js), `api-design` (FastAPI, Django, Laravel, Node), `database` (PostgreSQL, MySQL, MongoDB), `auth`, `e2e-testing` (Playwright), `deployment` (Vercel, VPS + Docker, AWS), `observability`. |
| **9 agents** | `planner`, `implementer`, `code-reviewer`, `test-writer`, `docs-writer`, `architecture-reviewer`, `security-auditor`, `performance-analyzer`, `ui-reviewer`. |
| **Hooks (enforced)** | Git, for every tool and for you: Conventional Commits, AI attribution removed, `main` and release tags protected, per-repo hooks kept working. Claude Code: a command guard that blocks or asks before dangerous commands, auto-formatting with the project's formatter, and the project's status at session start. |
| **Per-project switch** | `harness enable / disable / status`: the full workflow only where you want it; the safety net everywhere. |
| **Conventions** | Conventional Commits, squash-merged PRs, SemVer with annotated `vX.Y.Z` tags and release-please, English code without comment noise, pnpm / uv / Composer, formatter defaults. |
| **Docs system** | `README` for humans, `AGENTS.md` for AIs, and `docs/` with a technical sheet, architecture, ADRs, plans, audits, continuous handoffs and an AI work log, with templates. |
| **Project templates** | `.editorconfig`, issue forms, a PR template, Dependabot and release-please, ready for new projects. |
| **Plugins** | `context7` (up-to-date library docs) and `frontend-design`, installed and kept up to date. |
| **Installer** | `install.sh`: idempotent, backs up instead of overwriting, merges settings without touching yours, works on Linux and macOS. |
| **Quality** | ~250 tests and CI on Linux and macOS, a validator for skills and cross-references, behaviour evals with real AI sessions, GitHub rulesets on `main` and tags. |

## Why this exists

### The problem
AI coding assistants are fast, but out of the box they're inconsistent teammates:
- **Every session starts from zero.** The conventions you explained yesterday are gone today, and Claude and Codex each behave differently.
- **Good practice is optional for them.** They skip tests, write one giant commit, sign commits as "Co-Authored-By: Claude", over-comment the code, forget the README, and stop halfway without leaving notes.
- **Some mistakes are expensive:** a force-push to `main`, `rm -rf` in the wrong place, a `--no-verify` that skips the checks, a migration run against the wrong database.
- **Prompt rules get forgotten.** Instructions in a chat or a long system prompt are suggestions; nothing stops the model when it ignores them.
- **Setup doesn't travel.** Each machine and each tool ends up with its own half-remembered configuration.

### The solution
One versioned repo that turns an AI assistant into a teammate that works like a disciplined senior engineer, on any machine, with any assistant:
- **One way of working, everywhere:** plan → TDD → small Conventional Commits → docs → review, the same in Claude Code and Codex, installed with one command.
- **Rules that are enforced, not just written:** git hooks and Claude Code hooks apply the rules that matter whatever the model does, so a forgotten instruction can't become a broken `main`.
- **Expert knowledge on demand:** 18 skills (frontend, APIs, databases, auth, testing, deployment, releases…) and 9 specialised agents load only when a task needs them.
- **You stay in control:** it's opt-in per project, asks before anything outward-facing (push, PRs, releases), and asks you scope and focus before reviewing or delegating.

### Strengths
| | What you get |
| --- | --- |
| **Consistency** | The same workflow and conventions in every project and every session: plans, tests first, atomic commits, squash-merged PRs, SemVer releases, docs for humans and for AIs. |
| **Safety net** | Blocks force-pushes and deletion of `main`, catastrophic `rm -rf`, hook bypasses and published-tag rewrites; asks before discarding work or wiping a database. Works for Claude, Codex, any other tool and your own commands. |
| **Clean history** | Conventional Commits enforced, AI attribution removed automatically, one commit per logical change, changelogs and versions computed from commits. |
| **Better code** | TDD, SOLID/DDD where it fits, self-explanatory code without comment noise, stack-specific best practices instead of generic answers. |
| **Continuity** | Continuous handoffs, so a session cut off by usage limits resumes exactly where it stopped, even in another tool or on another machine; plans, audits and an AI work log in `docs/`. |
| **It learns** | Corrections become versioned rules (`lessons`), so the same mistake isn't made twice, on any machine. |
| **Scales up when needed** | Reviews with parallel specialised reviewers (`improve`), and multi-agent delegation with a model and effort recommended per task (`orchestrate`), only with your OK. |
| **Low overhead** | Opt-in per project; skill descriptions are kept to a budget (~1.2k tokens per session) and details load only when used. |
| **Proven** | ~250 automated tests on Linux and macOS (installer, hooks, validator), behaviour evals with real Claude and Codex sessions, and its own improvement audit with every finding fixed. |

### Why use it
- **For you:** less time correcting the AI and re-explaining conventions; more time reviewing good changes. Nothing to remember: the rules apply themselves.
- **For your projects:** a readable history, tests that exist, docs that match the code and releases that are boring, in the best sense.
- **For a team:** everyone's assistant follows the same playbook, so AI-written code looks like the team's code. New members get the conventions on day one by running one command.
- **Against risk:** the dangerous mistakes are blocked at the git and tool level, not left to the model's judgement.

### Limits (honestly)
Skills and instructions guide the model; only the hooks guarantee. The command guard reads commands like a shell but is a safety net, not a sandbox. Subagents cost extra tokens, which is why delegation is always your call. Codex gets the skills and instructions, but not the Claude-specific agents and hooks; the git hooks apply to both.

## Install

1. **Check the requirements.** `git` and `bash` (macOS's bash 3.2 is fine); `python3` or `jq`; Claude Code and/or Codex. Optional but recommended: the GitHub CLI `gh`, logged in (`gh auth login`), for issues, PRs and releases.
2. **Clone the repo** anywhere; `~/Projects` is the convention:
   ```bash
   git clone https://github.com/nbfrodri/agent-harness.git ~/Projects/agent-harness
   ```
3. **Run the installer:**
   ```bash
   ~/Projects/agent-harness/install.sh
   ```
   It ends with `done with N warning(s)`. Read any warning. If a step failed it says how to fix it, and re-running is always safe. Use `--skip-plugins` when offline.
4. **Make sure `~/.local/bin` is in your `PATH`** (the installer warns if it isn't), so the `harness` command works.
5. **Restart Claude Code and Codex** so they load the skills, agents, hooks and instructions.
6. **Verify:**
   ```bash
   harness status                  # inside any repo: prints enabled or disabled
   git config --global core.hooksPath   # → ~/Projects/agent-harness/git-hooks
   ```
   In Claude Code, `/agents` lists `planner`, `code-reviewer`… and `/hooks` shows the hooks tagged `#harness`.

## How to use

1. **Enable the workflow in a project.** It's off everywhere by default; only the safety net is always on (see [On/off per project](#onoff-per-project)).
   ```bash
   cd ~/Projects/my-app
   harness enable            # only on this machine
   harness enable --shared   # or: commit a .harness file so it's on for every clone
   ```
   Projects created through the AI with "crea un proyecto…" are enabled automatically.
2. **Start a new session** in that project and work as usual, in Spanish. Some examples:
   | You say | What happens |
   | --- | --- |
   | "Añade login con Google" | Plan (waits for your OK if it's large) → branch → TDD → small Conventional Commits → docs → summary. It asks before pushing. |
   | "Trabaja en el issue #12" | Reads the issue, uses its acceptance criteria, opens a PR that closes it (after asking). |
   | "No funciona el checkout" | Reproduces the bug, writes a failing test, fixes the root cause. |
   | "¿Qué mejorarías de este módulo?" | Asks you the scope and focus areas, runs read-only reviewers, gives a prioritised report. |
   | "Hazlo con subagentes" | Splits the plan across agents, recommending a model and effort per task for you to confirm. On large divisible tasks the AI suggests this itself, but never starts without your OK. |
   | "Haz una release" | Works out the SemVer version; with release-please, reviews and merges the release PR (after asking). |
   | "Haz un handoff" | Writes the state of the work to `docs/handoffs/` so any AI or person can continue. |
   | "No, así no: usa pnpm" | Fixes it and saves the rule (`lessons`) so it doesn't happen again. |
3. **Disable it** where you don't want the ceremony: `harness disable`.
4. **Keep it up to date** on each machine:
   ```bash
   cd ~/Projects/agent-harness && git pull && ./install.sh
   ```
5. **Change the rules** by editing the files here (or by telling the AI, which uses `lessons`), then commit and push. Changes apply immediately on this machine through the symlinks; restart the tool for new skills or agents.

## Using it on someone else's machine

This repo is personal (private, with its owner's preferences), so another person should run **their own copy**:

1. **Get access.** The owner either invites them as a collaborator (*Settings → Collaborators*), or makes the repo public or a template (*Settings → Template repository*).
2. **Create their own copy:** *Use this template* (or fork) on GitHub, so they can push their own changes and keep their rules versioned.
3. **Clone their copy and install:**
   ```bash
   git clone https://github.com/<their-user>/agent-harness.git ~/Projects/agent-harness
   ~/Projects/agent-harness/install.sh
   ```
4. **Adapt the personal bits:**
   | File | What to change |
   | --- | --- |
   | `global/AGENTS.md` | The language the AI talks in (Spanish here) and the "ask before" rules. Every agent and skill uses the language set here. |
   | `skills/dev-workflow/references/conventions.md` | Stack choices made for this owner: pnpm, kebab-case files, squash merge, release-please, comment policy… |
   | `plugins.txt` | Claude Code plugins to install. |
   | `claude/settings.json` | Claude Code settings and hooks merged into theirs (their own keys and hooks are kept). |
   | `README.md`, `bin/harness` | The repo URL (badge, clone command, `.harness` marker text). |
5. **Restart Claude Code and Codex, and enable it in a project:** `harness enable`.
6. **Keep it theirs:** they can pull improvements from the original with `git remote add upstream <original-url>` and `git pull upstream main`, then re-run `./install.sh`.

Things that are already per-user and need no changes: the git identity (commits use their `git config user.name/email`), existing `~/.claude/settings.json` keys and hooks (merged, never overwritten), and any global `core.hooksPath` of their own (left alone).

## What the installer does

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
harness enable            # this clone only (git config; nothing added to the repo)
harness enable --shared   # commit a .harness file so it travels with the repo
harness disable
harness status            # enabled / disabled
git config --global harness.enabled true   # enable everywhere (a local `disable` still wins)
```

| | Enabled project | Any other repo |
| --- | --- | --- |
| Command guard, protection of `main` | ✔ | ✔ |
| AI attribution removed from commits | ✔ | ✔ |
| Conventional Commits enforced | ✔ | — |
| Full workflow and auto-format | ✔ | — |

Claude Code is told the status at session start (`SessionStart` hook); Codex checks `harness status` as its instructions say. `new-project` enables new projects automatically.

## Enforced rules (hooks)

Skills and instructions guide the AI; hooks **enforce** the rules that matter, whatever the AI (or you) does.

| Hook | Where | What it does |
| --- | --- | --- |
| `commit-msg` | git (global) | Removes AI attribution (`Co-Authored-By` of Claude, Codex, Copilot…, "Generated with…") everywhere, and in enabled projects rejects subjects that aren't Conventional Commits. Merge, revert and `fixup!`/`squash!` messages are accepted. |
| `pre-push` | git (global) | Refuses force-pushes and deletions of `main`/`master` on any remote (override: `HARNESS_ALLOW_FORCE_PUSH=1`). In enabled projects, only lets annotated `vX.Y.Z` tags through and never moves or deletes a published tag (override: `HARNESS_ALLOW_TAG=1`). |
| Other git hooks | git (global) | Pass through to each repository's own `.git/hooks/*` (client and server side, e.g. `post-receive` in local bare repos), so pre-commit, lefthook or custom hooks keep working. |
| `session-context.sh` | Claude Code `SessionStart` | Tells Claude whether the project is enabled. |
| `guard-bash.sh` | Claude Code `PreToolUse` | **Blocks** force-pushing main, `--no-verify`, `rm -rf` of `/`, `~` or `..`. **Asks first** for `reset --hard`, `clean -f`, discarding changes, deleting branches, force-pushing other branches, recursive deletes outside the project, and dropping/resetting databases. |
| `format-file.sh` | Claude Code `PostToolUse` | In enabled projects, formats each edited file with the formatter the project already has configured (Biome, Prettier, Ruff, Black, Pint, gofmt, rustfmt). Projects without one are left alone. |

Git hooks apply to Claude, Codex, any other tool and your own commits. Notes:

- In a repository with different commit conventions: `git config harness.conventionalCommits false` (AI attribution is still removed).
- Repositories that set their own local `core.hooksPath` (e.g. Husky) use only their hooks; there, Claude's `attribution` setting still prevents its trailers.
- Claude hooks are tagged `#harness` in `settings.json`; re-installing replaces only those.

## Structure

```
global/AGENTS.md      # global instructions for every AI assistant
bin/harness      # per-project switch, linked into ~/.local/bin
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
| Releases | SemVer, annotated `vX.Y.Z` tags, release-please, `CHANGELOG.md` + GitHub Release |
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
shellcheck -x install.sh bin/harness tests/*.sh evals/run.sh git-hooks/_chain git-hooks/commit-msg git-hooks/pre-push hooks/claude/*.sh
tests/validate.sh                  # validate skills, agents, cross-references, README coverage, plugins.txt
tests/validate.test.sh             # prove the validator catches each kind of error
tests/install.test.sh              # test the installer in throwaway HOME directories
tests/hooks.test.sh                # test git and Claude Code hooks in throwaway repositories
```
