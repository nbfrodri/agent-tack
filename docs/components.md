# Components

Every skill, agent and plugin, in one line each.

## Skills
Open Agent Skills format (`SKILL.md`), read by every supported tool.

| Skill | Purpose |
| --- | --- |
| `dev-workflow` | The workflow at lite, standard or strict level: impact mapping, minimal modular changes, architecture fit, plan, TDD, SOLID/DDD, code, git and release conventions, docs |
| `new-project` | Scaffold a project with tests, lint, CI, docs, templates, release-please |
| `debugging` | Reproduce → regression test → isolate → verify → fix the root cause |
| `testing` | What and how to test per layer; pytest, Pest/PHPUnit, Vitest/Jest |
| `git-history` | Amend, fixup, squash, undo and recover commits |
| `release` | SemVer, tags, CHANGELOG, GitHub Releases, release-please |
| `github-issues` | From an issue to a PR that closes it; writing and splitting issues |
| `project-docs` | Docs for humans and AIs, ADRs, plans, audits, handoffs, AI log |
| `improve` | Prioritised improvement review with read-only reviewers |
| `orchestrate` | Multi-agent delegation with model and effort per task; automatic only for strict-level work |
| `auto-improve` | Autonomous score → fix → re-score loop up to a target score |
| `lessons` | Turn corrections into versioned rules |
| `frontend` | React/Next.js components, state, forms, accessibility |
| `api-design` | REST, errors, validation, OpenAPI; Python, Laravel, Node |
| `database` | Modelling, safe migrations, indexes; PostgreSQL, MySQL, MongoDB |
| `auth` | Sessions vs tokens, OAuth, hashing, CSRF, RBAC |
| `e2e-testing` | Playwright end-to-end tests |
| `deployment` | Docker, CI/CD; Vercel, VPS, AWS |
| `observability` | Logs, request IDs, Sentry, health checks, alerts |

## Agents
Claude Code subagents (`~/.claude/agents`); other tools follow the same files as instructions.

| Agent | Purpose |
| --- | --- |
| `planner` | Read-only plan: design, tests first, commits, optional delegation |
| `implementer` | Implements one task on its own branch or worktree |
| `code-reviewer` | Reviews a diff, branch or whole scope |
| `test-writer` | Adds tests to existing code; never touches production code |
| `docs-writer` | Keeps docs in sync and logs AI work; runs on an economical model and takes doc updates spanning 3 or more files |
| `evaluator` | Scores a project 0–10 per dimension with evidence (`auto-improve`) |
| `architecture-reviewer` | Layering, coupling, boundaries, debt hot spots |
| `security-auditor` | OWASP Top 10, auth, secrets, dependencies, CI |
| `performance-analyzer` | Measures and ranks performance problems |
| `ui-reviewer` | Reviews a running app at mobile and desktop widths |

## Plugins
| Plugin | Purpose |
| --- | --- |
| `context7` | Up-to-date library documentation |
| `frontend-design` | Polished UI design |

## Mods
Claude Code mods shipped in `plugins/` and installed by `./install.sh` (opt out with `--skip-mods`).

| Mod | Purpose |
| --- | --- |
| `usage-band` | Band above the prompt with the active tack mode, the 5-hour and weekly limits, context fill and session cost; `/usage-band` toggles it |
| `agent-activity` | Live pane of tool calls, skills, subagents and permission decisions; `/activity` opens it |

Browser control is built into Claude Code and Codex, so no browser MCP is installed. Read-only database MCP servers are set up per project (`skills/database/references/mcp.md`).
