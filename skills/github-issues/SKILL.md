---
name: github-issues
description: GitHub issues with gh: work an issue end to end (linked branch, PR that closes it), write bug reports and feature requests, split plans into issues, triage, templates. Use when an issue or ticket is mentioned (issue #12, create an issue, list pending work).
---

# GitHub issues

Issues are the project's to-do list and its memory: why something was built, what was decided and what's still pending. Good issues are small, specific and have acceptance criteria, so anyone (a person or an AI) can pick one up and know when it's done.

Creating, editing, commenting on, labelling or closing issues is visible to other people, so **ask the user before any write** to GitHub unless already authorised. The `improve` audit workflow authorises creation of issues for verified findings, without a second confirmation, except when the user requests no publication. This exception does not authorise comments, closing issues or unrelated writes. Reading (`gh issue list/view`) is always fine.

## Working on an issue ("work on issue #12")
1. **Read it whole:** `gh issue view 12 --comments`, including linked issues/PRs and any screenshots or logs. Check it's still open and not already being worked on (assignee, linked branches: `gh issue develop --list 12`).
2. **Clarify:** if the acceptance criteria are missing or ambiguous, propose them to the user (and, with permission, as a comment on the issue) before coding.
3. **Plan** as usual (`dev-workflow`), with the issue's acceptance criteria as the definition of done.
4. **Branch linked to the issue:** `gh issue develop 12 --name feat/12-short-slug --checkout` (it shows up on the issue), or plain `git switch -c feat/12-short-slug`. Use `fix/` for bugs, etc.
5. **Commits:** Conventional Commits as always; reference the issue in the footer when useful: `Refs #12`.
6. **PR** (after asking): title in Conventional Commit format, body with `Closes #12` so merging closes the issue automatically. Don't close issues by hand when a PR will do it.
7. Anything out of scope that you notice stays out of the PR: propose a new issue for it (below).

## Writing a good issue
Before creating one, search for duplicates: `gh issue list --search "<keywords>" --state all`.

**Bug report**
```markdown
## Description
What is wrong, in one or two sentences.

## Steps to reproduce
1. …
2. …

## Expected behaviour
## Actual behaviour
(error message, logs, screenshot)

## Environment
Version/commit, OS, browser, relevant config.
```

**Feature / task**
```markdown
## Problem
Who needs what, and why (the user value, not the solution).

## Proposal
How it could work. Alternatives considered, if relevant.

## Acceptance criteria
- [ ] R1: concrete, testable condition
- [ ] R2: …

## Out of scope
```

Title: short and specific, in the imperative or as a symptom ("Cart total ignores volume discount for 10+ units", not "Bug"). Language: as the repo's existing issues (English by default).

```bash
gh issue create --title "…" --body-file /tmp/issue.md --label bug [--milestone v1.2] [--assignee @me]
```

## Splitting a big plan into issues
For work that spans several PRs (a feature, a migration, the `planner` agent's output):
- One issue per independently shippable slice (ideally one PR each), each with its own acceptance criteria. Prefer vertical slices (a thin end-to-end feature) over layers ("all the models", "all the endpoints").
- A parent issue (epic) with a task list linking the children (`- [ ] #45`), or GitHub sub-issues if the repo uses them.
- Note dependencies ("blocked by #45") and suggested order.
- Show the user the proposed list first; create the issues only after they approve.

## Bugs and follow-ups found along the way
Don't silently fix unrelated problems inside the current change, and don't forget them either. Mention them in your summary and offer to open an issue with what you know (location, reproduction, suspected cause).

## Labels, milestones, triage
- Use the repo's existing labels (`gh label list`). For new repos, a minimal set: `bug`, `enhancement`, `documentation`, `chore`, `good first issue`, `priority: high`.
- Milestones group the issues of a release (pairs well with the `release` skill).
- "What is pending?": `gh issue list --state open --limit 50` (filter with `--label`, `--assignee @me`, `--milestone`), then summarise by priority and suggest what to tackle next and why.

## Templates for a repository
To give a repo issue forms and a PR template, copy this skill's `assets/`:
```
assets/ISSUE_TEMPLATE/bug_report.yml       -> .github/ISSUE_TEMPLATE/bug_report.yml
assets/ISSUE_TEMPLATE/feature_request.yml  -> .github/ISSUE_TEMPLATE/feature_request.yml
assets/ISSUE_TEMPLATE/config.yml           -> .github/ISSUE_TEMPLATE/config.yml
assets/pull_request_template.md            -> .github/pull_request_template.md
```
Commit them as `chore(github): add issue and PR templates`.
