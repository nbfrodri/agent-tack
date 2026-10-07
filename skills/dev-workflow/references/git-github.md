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

Commit at each coherent verified milestone while working, rather than collecting every feature, fix and document in a final bulk commit. Do not leave failing regression tests as the final branch state; keep the passing test and fix together.

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
- deleting unmerged branches (a branch whose PR is merged is deleted locally and on the remote without asking);
- creating tags and releases;
- any force-push. Never to `main`/`master` (the `pre-push` hook and the GitHub ruleset block it); on other branches, only `--force-with-lease`.

Before committing: review `git diff --staged` so no secrets, generated files or unrelated changes get in. Don't `git add -A` blindly.

## Pull requests

Before requesting integration approval, inspect the branch commits and recommend a method with a short reason:
- **Merge commit** when the commits are coherent, verified milestones worth retaining individually.
- **Squash** when the branch represents one change and its history contains temporary fixes, repeated corrections or work in progress that would obscure that change.

In the existing integration confirmation, offer both available methods and let the user choose. Preserve commits by default; squash requires the user's explicit choice. If the user already specified a method for this integration, follow it without asking again. Do not add a separate approval step or rewrite published commits to prepare the choice. Explain repository constraints when a method is unavailable; changing repository settings requires permission.

Every branch commit and the PR title follow Conventional Commits (see `conventions.md`). When squashing, the resulting commit must also follow Conventional Commits and describe the complete change.

### Prepare the PR body

1. Read the final diff against the intended base and the project's contribution instructions. Look for `pull_request_template.md` (including uppercase names) in `.github/`, the root and `docs/`, and for named templates in `PULL_REQUEST_TEMPLATE/` within those directories. Reuse an applicable known organization default when the project inherits one. Select the template matching the change; clarify only when the choice is consequential and ambiguous.
2. Follow the selected template's required sections and checks. If none exists, use `github-issues` → `assets/pull_request_template.md` as the drafting fallback. Add a repository template when requested or when setting up a new project's GitHub basics; drafting a PR alone does not require adding one. Preserve existing templates.
3. Lead with the concrete problem and resulting behavior. Explain the final change for a reviewer who has not read the conversation; include a short before/after example when it helps. Rewrite the title and body if scope changed. Scale detail to the diff rather than copying the work log or listing every file.
4. Record the checks actually run and their results. Identify failed or unrun checks with reasons. Mark checklist items complete only with evidence. Include compatibility changes, risks, screenshots or rollout/rollback notes when relevant. Retain required sections; remove optional empty sections and draft placeholders. Add `Closes #123` only for an actual issue fully resolved by this PR; use `Refs #123` for partial work.
5. Prepare the exact title, base/head branches and body locally before asking for publication approval when it is still needed. With `gh`, write the body to a temporary UTF-8 file and use `gh pr create --title '…' --body-file <path>` after authorization. This preserves real newlines; do not rely on automatic template insertion when supplying a body, or on commit autofill as the final description. `gh pr create --dry-run` may push changes, so preview the local file instead. Reuse existing authorization and do not open a duplicate PR.

Keep PRs small and reviewable; split them when they grow. Creating or editing templates does not publish a PR. To work from issues, write them or split a plan into issues, follow `github-issues`. See [GitHub's template locations](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository) and [GitHub CLI options](https://cli.github.com/manual/gh_pr_create).

## Versions and releases

SemVer: `fix` → patch, `feat` → minor, breaking → major. If the project has a CHANGELOG, update it following Keep a Changelog. For a release (version, tag, GitHub Release, automation), follow the `release` skill.
