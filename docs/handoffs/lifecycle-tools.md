# Installer lifecycle implementation

Approved scope: read-only install preview, private ownership records, and conservative uninstall. Worktree: `/tmp/harness-lifecycle-20261004`; branch: `feat/lifecycle-tools`.

## Milestone 1

- Added `install.sh --dry-run` to describe links, migration, settings, Git hooks and plugin actions without calling the plugin CLI or changing installed state.
- Lifecycle tests observed red (2 expected failures), then green (3 checks). Existing baseline: 87 installer checks pass.
- Next: private ownership state at `${XDG_STATE_HOME:-$HOME/.local/state}/agent-harness/ownership`, first-install baselines across reinstalls, selective settings reversal, safe link and Git restoration.
- Safety: no plugin uninstall, project deletion or broad directory cleanup. Refuse invalid ownership state and preserve user edits. JSON reversal requires Python; jq-only install remains supported.

## Milestone 2

- Added private version-1 ownership records, shell capture in `lib/ownership.sh`, Python validation/reversal in `lib/ownership.py`, and `uninstall.sh [--dry-run]`.
- Reinstalls preserve original links and settings snapshots. Reversal compares owned values, retains user additions and edited hooks, and preserves changed link targets or physical parent paths.
- No Python is required to install; uninstall requires Python before mutation. No plugin uninstall or shared-directory deletion occurs.
- Lifecycle checks: 24 pass, including observed failing tests for reversibility and settings edits across reinstall. ShellCheck passes for changed shell files. Full installer regression is running.
- Next: adversarial metadata, repository-permission/plugin dry-run checks, Git restoration variations and dependency failures.

## Milestone 3

- Ownership now records each entry's source `repo` and physical `parent_identity` (`device:inode`). Changed physical parents and symlink parents are preserved, while stable ancestors outside HOME (including macOS temporary-directory aliases) are supported.
- Link records are restricted to paths declared by `targets.txt`, shared skills, subagents and the two canonical harness links. Unsupported schema, public metadata and arbitrary HOME destinations fail validation before uninstall changes anything.
- Independent review found two undo gaps. Regression tests first failed, then passed for restoring displaced tagged hooks alongside appended user hooks and honoring a previously absent explicit `GIT_CONFIG_GLOBAL` over an existing XDG config.
- Conservative legacy behavior: pre-existing paths already matching the desired configuration are not claimed. Reinstalling an older unmanaged installation does not retroactively authorize removal of every existing path.
- If neither `stat` nor Python can identify a parent during install, the entry records `unavailable` and uninstall preserves it. JSON restoration requires Python. Metadata retained for conflicts includes private snapshots; no values are printed.
- Final targeted regression and invariant checks are running; no publish operations performed.
- Final results: 44 lifecycle checks and all 87 existing installer checks pass; changed shell files pass ShellCheck. The last test-stub change replaced an equivalent quoted printf with a heredoc to satisfy lint.
