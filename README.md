# agent-config

My personal configuration for AI coding assistants (Claude Code, Codex): skills, subagents and global instructions, kept in one place and linked into each tool.

## Structure

```
global/AGENTS.md   # global instructions -> ~/.claude/CLAUDE.md and ~/.codex/AGENTS.md
skills/<name>/     # Agent Skills (SKILL.md + references) -> ~/.agents/skills, ~/.claude/skills, ~/.codex/skills
agents/<name>.md   # Claude Code subagents -> ~/.claude/agents
install.sh         # creates the symlinks (idempotent)
```

## Skills

| Skill | Purpose |
| --- | --- |
| `dev-workflow` | Plan first, TDD, SOLID/DDD, Conventional Commits, GitHub flow, keep docs up to date |
| `git-history` | Amend, fixup, squash, undo and recover commits; tidy a branch before push |
| `debugging` | Reproduce → regression test → isolate → verify hypothesis → fix the root cause |
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
| `docs-writer` | Updates README, .env.example, CHANGELOG and ADRs to match the changes |
| `security-auditor` | Read-only full-stack security audit: OWASP Top 10, auth, injection, secrets, dependencies, infra |
| `performance-analyzer` | Measures and ranks performance problems: Web Vitals, bundle, API latency, DB queries, caching |

Agents use the Claude Code subagent format and are installed to `~/.claude/agents`.

## Install on a new machine

```bash
git clone https://github.com/nbfrodri/agent-config.git ~/agent-config
~/agent-config/install.sh
```

Existing files that would be replaced are moved to `*.bak`.

## Adding a skill or agent

1. Create `skills/<name>/SKILL.md` (or `agents/<name>.md`).
2. Run `./install.sh` to link it.
3. Commit and push.

Because the tools read through symlinks, editing files here takes effect immediately.
