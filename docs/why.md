# Why agent-harness

What problem it solves, how, and why it's worth using.

## The problem
AI coding assistants are fast, but out of the box they're inconsistent teammates:
- **Every session starts from zero.** Conventions explained yesterday are gone today, and each tool (Claude, Codex, Cursor, Copilot, Gemini…) behaves differently.
- **Good practice is optional for them.** They skip tests, write one giant commit, sign commits as "Co-Authored-By: Claude", over-comment, forget the README, and stop halfway without notes.
- **Some mistakes are expensive:** a force-push to `main`, `rm -rf` in the wrong place, a `--no-verify`, a migration against the wrong database.
- **Prompt rules get forgotten.** Instructions in a chat are suggestions; nothing stops the model when it ignores them.
- **Setup doesn't travel.** Each machine and each tool ends up with its own half-remembered configuration.

## The solution
One versioned repo that makes any AI assistant work like a disciplined senior engineer, on any machine:
- **One way of working:** plan → TDD → small Conventional Commits → docs → review, the same in every supported tool, installed with one command.
- **Rules that are enforced:** git hooks and Claude Code hooks apply the rules that matter whatever the model does.
- **Expert knowledge on demand:** 19 skills and 10 agents that load only when a task needs them.
- **You stay in control:** opt-in per project; it asks before anything outward-facing, and asks scope and focus before reviewing, delegating or improving autonomously.

## Strengths
| | What you get |
| --- | --- |
| **Consistency** | The same workflow and conventions in every project and session: plans, tests first, frequent atomic commits preserved through PR integration, SemVer releases, docs for humans and AIs. |
| **Safety net** | Blocks force-pushes and deletion of `main`, catastrophic `rm -rf`, hook bypasses and tag rewrites; asks before discarding work or wiping a database. Git-level rules apply to every tool and to you. |
| **Clean history** | Conventional Commits enforced, AI attribution removed, changelogs and versions computed from commits. |
| **Better code** | TDD, SOLID/DDD where it fits, self-explanatory code, stack-specific best practices. |
| **Continuity** | Continuous handoffs, so a session cut off by usage limits resumes where it stopped, in any tool or machine. |
| **It learns** | Corrections become versioned rules (`lessons`). |
| **Scales up** | Parallel reviewers (`improve`), multi-agent delegation with per-task models (`orchestrate`), and an autonomous improvement loop with a scored target (`auto-improve`), always with your OK. |
| **Low overhead** | Opt-in per project; skill descriptions kept to a budget (~1.2k tokens per session). |
| **Proven** | ~260 automated tests on Linux and macOS, and [measured results](results.md) against a plain assistant. |

## Why use it
- **For you:** less time correcting the AI and re-explaining conventions, more time reviewing good changes.
- **For your projects:** readable history, tests that exist, docs that match the code, boring releases.
- **For a team:** everyone's assistant follows the same playbook; new members get it with one command.
- **Against risk:** dangerous mistakes are blocked at the git and tool level, not left to the model's judgement.

## Limits
Skills and instructions guide the model; only the hooks guarantee. The command guard reads commands like a shell but is a safety net, not a sandbox. Subagents cost extra tokens, which is why delegation is always your call. Tools other than Claude Code get the instructions and skills but not the Claude-specific agents and hooks; git hooks apply to all of them.
