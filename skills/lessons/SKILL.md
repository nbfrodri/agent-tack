---
name: lessons
description: Turn the user's corrections and lasting preferences into versioned rules in the right file, so mistakes don't repeat. Use when the user corrects how you worked or states a rule (corrections, always, never, from now on, remember this).
---

# Lessons

When the user corrects you, the expensive part was the mistake; the cheap part is making sure it never repeats. Every lasting correction becomes a rule written down in the right place, committed and versioned, so it applies to every assistant (Claude, Codex…) on every machine.

## 1. Decide whether it's a lesson
It is a lesson if it would apply again in a future, different task: a convention, a preference, a recurring mistake, or a gap in a skill. It is **not** a lesson if it only concerns this task ("this endpoint should return 404 here"); just apply it.

When unsure, apply the fix, then ask in one line: "Should I save this as a rule for future tasks?".

## 2. Choose where it belongs
| The lesson is about… | Write it in |
| --- | --- |
| One project only (its folders, commands, naming, domain terms, quirks) | That repo's `AGENTS.md` (create it if missing, plus a `CLAUDE.md` containing `@AGENTS.md`), committed in that repo |
| How the user works everywhere (language, git, communication, approvals) | `global/AGENTS.md` in the user's config repo |
| How to do something in a domain the skills cover (testing, API, DB, deploy…) | The relevant `skills/<name>/SKILL.md` or its `references/*.md` |
| A recurring task that no skill covers yet | Propose a new skill to the user before creating it |

The user's config repo is where the skills live:
```bash
CONFIG_REPO="$(cd ~/.agents/harness && pwd -P)"   # canonical link created by install.sh
```

## 3. Write it well
- **Search first.** Grep the target file (and related skills) for an existing rule on the topic. Update or replace it instead of appending a second, contradictory one.
- **One short rule, with the reason.** For example: "Use `pnpm`, not `npm`: the monorepo's lockfile and workspaces depend on it." The reason lets future readers apply it sensibly to cases the rule didn't foresee.
- **Generalise, don't overfit.** Capture the principle behind the correction, not the literal case. Example: "use `Decimal` for money in every language", not "use Decimal in cart.py".
- **Match the file's language and style.** Skills and docs, including trigger phrases, are in English; keep tables and lists consistent.
- **Keep global instructions short.** `global/AGENTS.md` loads in every session; if it grows past ~40 lines, move detail into the relevant skill and leave a one-line pointer.
- If the lesson contradicts something the user said before, point out the conflict and ask which wins.

## 4. Verify and commit
In the config repo:
```bash
tests/validate.sh                      # skills still valid
git add <files> && git commit -m "docs(<skill or agents>): <rule in a few words>"
```
In a project repo: `git commit -m "docs(agents): <rule in a few words>"`.

Follow the user's git rules: committing is fine, **ask before pushing**. Changes to skills apply immediately on this machine through the symlinks; other machines get them after `git pull`.

## 5. Tell the user
One or two lines: what rule you saved, where, and the commit. For example:
"Saved in `skills/testing/references/python.md`: always use `pytest-randomly` (commit `a1b2c3d`). Should I push?"
