# Git and GitHub

## Conventional Commits

Format:
```
<type>(<optional scope>): <subject>

<optional body: the why, not the what>

<optional footer: BREAKING CHANGE: …, Closes #123>
```

| Type | Use |
| --- | --- |
| `feat` | A new feature for users |
| `fix` | A bug fix |
| `refactor` | Code change without behaviour change |
| `test` | Adding or fixing tests |
| `docs` | Documentation only |
| `style` | Formatting, whitespace; no logic change |
| `perf` | Performance improvement |
| `build` | Build system, dependencies |
| `ci` | CI configuration |
| `chore` | Maintenance that fits nothing above |
| `revert` | Reverts an earlier commit |

Subject: imperative ("add", not "added"), lowercase start, no final period, **≤ 72 characters** (the `commit-msg` hook only rejects subjects over 100, as a backstop). Breaking change: `feat(api)!: …` and a `BREAKING CHANGE: …` footer.

Examples:
- `feat(auth): add JWT refresh token rotation`
- `fix(cart): prevent negative quantities on update`
- `refactor(orders): extract pricing policy into domain service`
- `test(orders): cover discount edge cases`
- `docs(readme): document required environment variables`

With TDD, a test and the code that makes it pass usually share a commit (`feat`/`fix`); the refactor that follows goes in its own `refactor` commit.

## No AI attribution

No `Co-Authored-By` trailers for any AI, no "🤖 Generated with …" lines and no mentions of Claude/Codex/ChatGPT as authors, in commits, PRs, issues, tags, release notes or changelogs. Use the user's git identity (`git config user.name/user.email`) and never change it. The global `commit-msg` hook removes AI trailers anyway; never bypass hooks with `--no-verify`.

## Branches

- `main` (or `master`) is always deployable; no direct commits for non-trivial changes.
- Names: `<type>/<kebab-case-description>`, e.g. `feat/order-discounts`, `fix/login-redirect-loop`; with an issue: `feat/123-order-discounts`.
- Short-lived; update from main with `git rebase` while the branch is local only.

## What to do without asking, and what not

This is the single, detailed list; the global instructions summarise it.

**Without asking:** `status`, `diff`, `log`, creating branches, `add`, `commit`, `stash`, rebasing local unpublished commits.

**Ask first:**
- `push`;
- creating or editing PRs and issues, or commenting on them (the `improve` audit workflow already authorises creation of verified finding issues unless the user requests no publication);
- `merge`;
- rebasing or amending published commits;
- deleting branches;
- creating tags and releases;
- any force-push. Never to `main`/`master` (the `pre-push` hook and the GitHub ruleset block it); on other branches, only `--force-with-lease`.

Before committing: review `git diff --staged` so no secrets, generated files or unrelated changes get in. Don't `git add -A` blindly.

## Pull requests

PRs are integrated with **squash merge**: the PR title becomes the commit on `main`, so it must be a valid Conventional Commit (see `conventions.md`). Body:
```markdown
## Summary
What changes and why (1-3 sentences).

## Changes
- …

## How to test
Steps or commands to verify.

## Notes
Risks, follow-ups, screenshots if UI.

Closes #123
```
Keep PRs small and reviewable; split them when they grow. Create them with `gh pr create --title … --body …`, always with the user's permission. To work from issues, write them or split a plan into issues, follow `github-issues`.

## Versions and releases

SemVer: `fix` → patch, `feat` → minor, breaking → major. If the project has a CHANGELOG, update it following Keep a Changelog. For a release (version, tag, GitHub Release, automation), follow the `release` skill.
