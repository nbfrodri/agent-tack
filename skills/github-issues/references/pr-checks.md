# Minimum PR checks

Offer when PR checks are requested or selected during onboarding. Inspect existing CI and templates first; adapt them instead of installing duplicate checks.

Copy `../assets/check-pr.py` to `scripts/check-pr.py` and `../assets/pr-policy.yml` to `.github/workflows/pr-policy.yml`. The standalone script needs only Python. Review the workflow and paths before committing. It runs on PR metadata edits, code updates and readiness changes, with read-only permissions and no secrets, model calls or comments. It uses `pull_request`, not `pull_request_target`.

Defaults require a Conventional Commit title and nonempty `## Summary` and `## Validation` prose. HTML comments, fenced code and bare placeholders do not fill a section. Validation can say what was not run and why. Drafts defer checks until ready for review. Local use:

```bash
python3 scripts/check-pr.py --event /path/to/pr-event.json
```

Adapt existing headings with `--summary-heading "Change" --validation-heading "Checks"`; `--title-policy any` allows the project's own title convention. Optional `--require-issue` requires prose such as `Refs #42` or `Closes owner/repo#42`. It checks syntax only, not issue existence, ownership or completion. Do not enable it where issue-free maintenance PRs are allowed.

Pair metadata with real project tests, lint, type checks and relevant contracts. Passing prose cannot prove checks ran or code is good. The checker is ordinary PR CI, not a tamper-proof policy service: a PR can change its workflow/script and those changes need review. A maintainer can make the check required through repository rules; copying a workflow does not do that. Use existing protection/merge queues where configured, and document the selected names in the contribution guide.

For audit findings, first verify and deduplicate, then create independently shippable issues when already authorized. Each records evidence, impact, observable acceptance criteria and dependencies. Implement through the issue workflow in `../SKILL.md`; close only completely resolved issues. Include conflict-resolution decisions and checks in the PR when relevant. Do not require an issue for every small change unless the project does.
