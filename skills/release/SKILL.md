---
name: release
description: Versioning and releases: SemVer from Conventional Commits, CHANGELOG, tags, GitHub Releases, release automation and hotfixes. Use when releasing, tagging or writing a changelog (saca una versión, haz una release, qué versión toca).
---

# Releases and versioning

A release is a promise to the people who use your code: the version number tells them how risky the upgrade is, and the changelog tells them what changed. Both should come straight from the commit history, which is why the commits follow Conventional Commits.

## Semantic Versioning
`MAJOR.MINOR.PATCH`:
- **PATCH** (`1.4.2 → 1.4.3`): only `fix` / `perf` changes, backwards compatible.
- **MINOR** (`1.4.3 → 1.5.0`): at least one `feat`, backwards compatible.
- **MAJOR** (`1.5.0 → 2.0.0`): any breaking change (`feat!:`, `BREAKING CHANGE:` footer).
- While at `0.y.z` the API is considered unstable: breaking changes bump the minor version. Move to `1.0.0` once the project is used in production or has a stable public API.
- Pre-releases: `2.0.0-rc.1`, `1.5.0-beta.2`. Build metadata (`+sha.abc123`) doesn't affect precedence.
- Apps that are deployed rather than consumed as libraries can use SemVer too, or calendar versioning (`2026.10.1`) if the project prefers it. Follow what exists.

## Working out the next version
```bash
git describe --tags --abbrev=0                       # last tag, e.g. v1.4.2
git log v1.4.2..HEAD --pretty='%s%n%b' | grep -E '^(feat|fix|perf)(\(.+\))?!?:|BREAKING CHANGE'
```
Any breaking change → major; otherwise any `feat` → minor; otherwise `fix`/`perf` → patch. `docs`, `chore`, `test`, `ci`, `refactor` and `style` alone don't need a release. Tell the user the proposed version and why.

## Changelog
`CHANGELOG.md` in Keep a Changelog format, written for humans (users of the project), not as a commit dump:
```markdown
## [Unreleased]

## [1.5.0] - 2026-10-03
### Added
- Export orders as CSV (#42)
### Fixed
- Totals no longer round incorrectly for bulk discounts (#45)
### Changed / Deprecated / Removed / Security
```
Group by the type of change, describe the impact, link PRs or issues, and keep comparison links at the bottom (`[1.5.0]: https://github.com/<owner>/<repo>/compare/v1.4.2...v1.5.0`). Move the `[Unreleased]` entries under the new version when releasing.

## Manual release checklist
1. On an up-to-date `main` with a clean working tree; CI green; `git pull --ff-only`.
2. Decide the version (above). If the user only asked what the next version would be, stop and propose it. If they asked you to prepare the release, go ahead and state the version and the reason in your summary: the commit and tag are local and easy to undo (`git tag -d`, `git reset`). Pushing is the irreversible step, and it always needs the user's confirmation.
3. Bump the version wherever it lives: `package.json` (`npm version <x> --no-git-tag-version`), `pyproject.toml` (`uv version <x>`, or edit it), `composer.json` (usually no version field; the git tag is the version), app constants, Helm/Docker labels.
4. Update `CHANGELOG.md`.
5. Commit: `chore(release): v1.5.0`.
6. Annotated tag: `git tag -a v1.5.0 -m "v1.5.0"`.
7. **Ask the user**, then push: `git push origin main --follow-tags`.
8. GitHub Release: `gh release create v1.5.0 --title "v1.5.0" --notes-file <notes>` (or `--generate-notes`), adding `--prerelease` for rc/beta versions and attaching build artefacts if any.
9. Deploy or publish (npm, PyPI, Packagist via the tag, Docker image tagged `1.5.0` plus `latest`) according to the `deployment` skill; smoke test.

Tags are immutable promises: never move or delete a published tag. If a release is bad, ship a new patch version (or revert and release), and mark the bad release in the changelog or on GitHub.

## Automating it
Suggest automation once releases become regular:
- **release-please** (GitHub Action, any language): keeps a release PR open with the version bump and changelog generated from Conventional Commits; merging it creates the tag and the GitHub Release. A good default.
- **semantic-release**: fully automatic release on every push to `main`. Mostly for JS libraries.
- **Changesets**: for JS monorepos with several packages, where contributors write the changeset notes explicitly.
- Enforce the commit format in CI (commitlint on PR titles when squash-merging) so the automation has good input.

## Hotfixes
Branch from the release tag (`git switch -c hotfix/1.5.1 v1.5.0`) only when `main` already contains unreleasable work; otherwise fix on `main` and release a patch. Cherry-pick the fix back to `main` if it was made on the hotfix branch, and release `1.5.1` the same way as above.

## Git attribution
Release commits, tags and release notes follow the same rule as every commit: no AI attribution lines.
