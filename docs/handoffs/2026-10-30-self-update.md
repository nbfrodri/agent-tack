# Release install and self-update

- Status: paused (implemented and verified; waiting for the user's go-ahead to push and open a PR)
- Branch: `feat/self-update` from `main`, commit e125b92
- Goal: install and update tack without a manual clone. `get.sh` (curl | bash) checks the latest `vX.Y.Z` tag out into `TACK_DIR`, default `${XDG_DATA_HOME:-~/.local/share}/agent-tack/release` (not `agent-tack` itself, which holds `sources/`; the user chose this), and runs its `install.sh`; a second run hands over to `tack update` (`lib/update.sh`): fetch tags, refuse a branch or local changes unless `--force`, check out the newest release, print changelog entries, rerun `install.sh`; `--check` (alias `--dry-run`) only reports.
- Verification: `tests/update.test.sh` 52/0 against a local fake remote; full `tests/run-all.sh` passed, 31 suites in 3196 s; lint and validate clean. The not-bash check runs only where `dash` exists (CI Ubuntu).
- Docs updated: README, docs/installation.md, setup.md, usage.md, architecture.md, CHANGELOG, skills/tack, completions.
- Limit: the latest release (v0.2.0) predates `tack update`; it works only after a release (v0.3.0) that includes this branch.
- Next: on the user's word, push and open a PR from the repo template (Summary + Validation); then cut v0.3.0.
- Not part of this work: `docs/archive/` is untracked and must stay untouched.
