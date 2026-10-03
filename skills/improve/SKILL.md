---
name: improve
description: Review existing code or a project, propose prioritised improvements and create deduplicated GitHub issues for verified findings through read-only reviews. Always asks scope and focus first. Use for review, audit or improvement requests on existing work.
---

# Improve

The goal is a short, prioritised list of improvements that are worth doing, backed by evidence, so the user can decide what to act on. It's not a list of everything that could be different. "This is fine as it is" is a valid and useful finding.

**Nothing is changed during the review.** Reviewers only read, run and measure. The user picks what to implement, and that work then follows `dev-workflow`.

## 1. Always ask scope and focus first
Even when the request seems clear, ask both questions before reviewing anything, in a single question round (use the question tool if available), proposing defaults based on what you see in the repo:

**Scope** (single choice):
- the whole project;
- a module, feature or folder (name the candidates you found, e.g. `src/orders/`, the checkout flow);
- recent work (a branch, the last N commits, since a tag);
- a specific screen or user flow (for UI reviews).

**Focus areas** (multiple choice; preselect the ones that fit the scope):
| Focus | Reviewer |
| --- | --- |
| Architecture: structure, layering, coupling, DDD boundaries | `architecture-reviewer` agent |
| Code quality: duplication, complexity, naming, dead code, conventions | `code-reviewer` agent in project mode |
| Performance | `performance-analyzer` agent |
| Security | `security-auditor` agent |
| UI/UX and visual design, accessibility | `ui-reviewer` agent (needs the app running) |
| Tests: gaps, weak or brittle tests | `test-writer` agent in report-only mode |
| Docs and developer experience: README, AGENTS.md, setup, scripts, CI | the main agent, using `project-docs` |

Also ask, if it isn't obvious, about context that changes priorities: is it a prototype or production? Is a big refactor acceptable, or only incremental changes?

## 2. Run the reviewers
- Give each reviewer the agreed scope, the focus and the project context, and tell it to **only report, not edit**. Where subagents aren't available (e.g. in Codex), do each review yourself, one focus at a time, following the corresponding agent definition in `~/.agents/harness/agents/`.
- Independent reviewers can run in parallel.
- For UI reviews, make sure the app is running locally (or ask for a URL) before starting the `ui-reviewer`.

## 3. Merge into one report
- Deduplicate overlapping findings and discard the ones without evidence.
- Score each finding: **impact** (user-facing bugs, risk, cost of change, speed) × **effort** (S/M/L). Sort by impact ÷ effort.
- Keep the **top 10** in the main list; mention briefly that there are more, if there are.
- For each finding give: what's wrong and where (`file:line` or a screenshot), why it matters (a concrete consequence), the proposed change, effort, and any risk. If tests are missing where a refactor is proposed, say that characterisation tests come first (`test-writer`).
- Add a short **"What's good"** section: what to keep doing, so it doesn't get "improved" away.

## 4. Create GitHub issues automatically

An audit request authorises creating issues for its verified findings in the project's GitHub repository. Do this after assembling the report, without asking for another confirmation; an explicit user request for no publication takes precedence. Reviewers remain read-only; the main agent performs the writes using `github-issues`.

- Confirm the repository with `gh repo view` and search both open and closed issues. Link an existing open issue when it already tracks the same unresolved problem. A closed issue is evidence to review, not a reason to discard a reproduced regression.
- Create one issue per independently fixable finding, with evidence, reproduction, impact, proposed change and acceptance criteria. Save body text to a temporary file and use `--body-file`.
- Do not turn optional feature suggestions or unverified concerns into issues unless the user asks for them.
- If GitHub is unavailable, no GitHub remote exists or creation is denied, report what remains untracked and keep the local audit. Do not invent issue URLs or repeatedly retry writes with uncertain results; check whether an issue was created first.
- Record issue links and status in the audit and include them in the report to the user. Pushes, PRs, merges and other writes still follow their own approval rules.

Show the report and issue links to the user in their language (global instructions), concisely, then offer:
1. to save it to `docs/audits/YYYY-MM-DD-improvement-<scope>.md` (template in `project-docs`);
2. to start work on the created or existing issues they choose;
3. to start implementing the ones they choose, via `dev-workflow`, one finding per branch or PR.

## Principles
- Evidence over opinion: every finding points to code, a measurement or a screenshot.
- Respect the project's choices and conventions; suggest changing them only with a strong, explained reason.
- Prefer incremental, low-risk improvements over rewrites. Propose a rewrite only when you can show incremental change won't get there.
- Don't recommend new dependencies, frameworks or patterns unless they clearly solve a problem the project actually has.
