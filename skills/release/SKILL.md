---
name: release
description: Versioning and releases: SemVer from Conventional Commits, CHANGELOG, tags, GitHub Releases, release automation and hotfixes. Use when releasing, tagging or writing a changelog (publish a version, prepare a release, choose the next version).
---

# Releases and versioning

A release is a promise to the people who use your code: the version says how risky the upgrade is, and the changelog says what changed. Both come straight from the commit history, which is why commits follow Conventional Commits and PRs are squash-merged with Conventional Commit titles.

**The convention** (versioning, tag format, method, changelog) is defined in `dev-workflow` → `references/conventions.md` → "Releases and tags". In short: SemVer, annotated `vX.Y.Z` tags, **release-please by default**, `CHANGELOG.md` plus the GitHub Release.

## Working out the next version
`fix`/`perf` → patch; any `feat` → minor; any breaking change (`feat!:`, `BREAKING CHANGE:`) → major. While at `0.y.z`, breaking changes bump the minor. `docs`, `chore`, `test`, `ci`, `refactor` and `style` alone don't need a release.
```bash
git describe --tags --abbrev=0                                   # last tag, e.g. v1.4.2
git log v1.4.2..HEAD --pretty='%s%n%b' | grep -E '^(feat|fix|perf)(\(.+\))?!?:|BREAKING CHANGE'
```
Always tell the user the version and why.

## Default: release-please

### Setup (new projects get it from `new-project`)
Copy this skill's `assets/`:
| Asset | Goes to |
| --- | --- |
| `assets/release-please.yml` | `.github/workflows/release-please.yml` |
| `assets/release-please-config.json` | `release-please-config.json` |
| `assets/release-please-manifest.json` | `.release-please-manifest.json` |

Set `release-type` in the config to the stack: `node` (`package.json`), `python` (`pyproject.toml`), `php` (`composer.json`), `rust`, `go`, or `simple` (a `version.txt`) for anything else. Set the manifest to the current version (`"0.1.0"` for a new project). Commit as `ci: add release-please`.

**Required CI checks:** PRs opened with the default `GITHUB_TOKEN` don't trigger other workflows, so if `main` requires CI checks the release PR can't be merged normally. Either add a fine-grained token (contents, pull requests, issues: read and write) as the repo secret `RELEASE_PLEASE_TOKEN`, which the workflow already prefers, or merge release PRs as an admin. Tell the user when you set it up.

### Releasing
1. Merging feature and fix PRs into `main` makes release-please open or update a PR titled `chore(main): release X.Y.Z`, with the version bump and the CHANGELOG entries.
2. Review it with the user: is the version right, and are the notes understandable for users? Edit the PR's CHANGELOG text if needed.
3. Merging it (after asking the user, like any merge) creates the annotated tag `vX.Y.Z` and the GitHub Release.
4. Deploy or publish according to `deployment` (npm, PyPI, Packagist via the tag, a Docker image tagged `X.Y.Z` and `latest`), then smoke-test.

To force a specific version (e.g. `1.0.0`), add a commit with the footer `Release-As: 1.0.0`.

## Manual release (only where release-please isn't set up)
1. On an up-to-date `main` with a clean tree and green CI: `git pull --ff-only`.
2. Work out the version (above). If the user only asked what the next version would be, stop and propose it. If they asked you to prepare the release, go ahead and state the version and the reason: the commit and tag are local and easy to undo (`git tag -d`, `git reset`); the push is the irreversible step.
3. Bump the version where it lives: `package.json` (`npm version <x> --no-git-tag-version`), `pyproject.toml` (`uv version <x>`), app constants, Helm/Docker labels. `composer.json` usually has none: the tag is the version.
4. Update `CHANGELOG.md` (below).
5. Commit `chore(release): vX.Y.Z` and tag it: `git tag -a vX.Y.Z -m "vX.Y.Z"`.
6. **Ask the user**, then `git push origin main --follow-tags`.
7. `gh release create vX.Y.Z --title "vX.Y.Z" --notes-file <the new CHANGELOG section>` (add `--prerelease` for alpha/beta/rc).
8. Deploy or publish and smoke-test.

## Changelog
`CHANGELOG.md` in Keep a Changelog style, written for the project's users, not as a commit dump: sections `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`; each entry describes the impact and links the PR or issue; newest version first, with an `[Unreleased]` section in manual mode. release-please generates the sections from commit types, so good commit subjects make good release notes.

## Tags
- Format: `vX.Y.Z`, or `vX.Y.Z-alpha.N` / `-beta.N` / `-rc.N` for pre-releases. Always annotated.
- Never move or delete a published tag. If a release is bad, ship a new patch (or revert and release), and mark the bad version in the CHANGELOG and on its GitHub Release.
- In enabled projects the `pre-push` hook rejects tags that don't follow the format or aren't annotated.

## Hotfixes
Fix on `main` with a `fix:` commit and release a patch. Only when `main` holds unreleasable work: branch from the tag (`git switch -c hotfix/1.5.1 v1.5.0`), fix, release `v1.5.1` from that branch manually, then bring the fix back to `main` (cherry-pick or merge).

Release commits, tags and notes carry no AI attribution, like every commit.
