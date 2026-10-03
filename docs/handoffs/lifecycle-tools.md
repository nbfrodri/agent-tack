# Installer lifecycle implementation

Approved scope: read-only install preview, private ownership records, and conservative uninstall. Worktree: `/tmp/harness-lifecycle-20261004`; branch: `feat/lifecycle-tools`.

## Milestone 1

- Added `install.sh --dry-run` to describe links, migration, settings, Git hooks and plugin actions without calling the plugin CLI or changing installed state.
- Lifecycle tests observed red (2 expected failures), then green (3 checks). Existing baseline: 87 installer checks pass.
- Next: private ownership state at `${XDG_STATE_HOME:-$HOME/.local/state}/agent-harness/ownership`, first-install baselines across reinstalls, selective settings reversal, safe link and Git restoration.
- Safety: no plugin uninstall, project deletion or broad directory cleanup. Refuse invalid ownership state and preserve user edits. JSON reversal requires Python; jq-only install remains supported.
