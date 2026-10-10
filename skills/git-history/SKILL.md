---
name: git-history
description: "Repair or tidy Git history: amend, fixup, squash, split, reword, undo, recover commits and resolve rebases. Use for commit corrections or work on the wrong branch."
---

# Git history

A clean history is one where each commit is a single logical change with a Conventional Commit message, tests pass at every commit, and nothing like "wip", "fix typo" or "oops" reaches the shared branch. Rewriting is how you get there, but it's only safe on commits nobody else has.

## First: is it published?

Before rewriting, check whether the commits are already on the remote:
```bash
git fetch
git status -sb                         # "ahead N" = N local-only commits
git log --oneline @{u}..HEAD           # commits not pushed yet
```
- **Local only:** rewrite freely.
- **Pushed to a branch only the user works on:** rewriting is fine, then `git push --force-with-lease` (ask the user first).
- **Pushed to `main`/`master` or a shared branch:** do not rewrite. Use `git revert <hash>` instead, which adds a new commit undoing the old one.

Before any non-trivial rewrite, leave a safety net: `git branch backup/<branch>-<date>`. Remind the user that `git reflog` can recover almost anything for ~90 days.

## Recipes

**Fix the last commit** (message or forgotten files):
```bash
git add <files>
git commit --amend            # or --no-edit to keep the message
```

**Fix an older commit:**
```bash
git add <files>
git commit --fixup <hash>
git rebase -i --autosquash <hash>~1
```
In non-interactive environments, use `GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash <hash>~1` so the todo list is accepted as-is.

**Squash several commits into one:** `git reset --soft <base>` then a single `git commit`, or interactive rebase with `squash`/`fixup`. If interactive mode is unavailable, prefer the `reset --soft` approach.

**Reword a message:** last one with `git commit --amend`; older ones via rebase with `reword`, or `--fixup=reword:<hash>` + autosquash.

**Split a commit:** `git reset HEAD~1` (keeps changes unstaged), then stage and commit in logical pieces with `git add -p`.

**Undo commits:**
| Goal | Command |
| --- | --- |
| Undo, keep changes staged | `git reset --soft HEAD~N` |
| Undo, keep changes unstaged | `git reset HEAD~N` |
| Undo and discard changes (ask first; destructive) | `git reset --hard HEAD~N` |
| Undo a published commit | `git revert <hash>` |

**Committed on the wrong branch:**
```bash
git branch feat/new-thing        # keep the commits on a new branch
git reset --hard origin/main     # only if the commits are not pushed, and after confirming
git switch feat/new-thing
```

**Recover lost work:** `git reflog` → find the hash → `git branch rescue <hash>`.

**Update a feature branch with main:** local-only branch → `git rebase origin/main`; already shared → `git merge origin/main`.

## Before push / PR checklist
1. `git log --oneline origin/main..HEAD`: each commit is one logical change with a proper Conventional Commit message, and none has AI attribution trailers.
2. Squash "wip", "fix typo", "address review" commits into the commits they belong to.
3. Tests pass on the final commit (ideally on every commit).
4. No secrets, build artefacts or unrelated changes: `git diff origin/main...HEAD --stat`.
5. Ask the user before pushing.

## Conflicts during rebase
Resolve file by file, keeping the intent of both sides; run tests; `git add` + `git rebase --continue`. If it gets messy, `git rebase --abort` returns to the starting state. Explain the conflict to the user if the right resolution isn't obvious.
