# Worktrees for concurrent work

Use when parallel writers need independent working directories, when unrelated dirty work must remain untouched, or when another branch needs inspection. Existing serial work can stay in its current checkout.

Inspect `git status` and `git worktree list --porcelain`. Choose an existing worktree or an unused branch/location based on the task. For example, from the project root:

```bash
git worktree add ../app-api -b feat/api-contract main
```

Substitute the real base and destination. Give each writer its branch, directory, scope and shared-contract dependencies. Do not run overlapping writers in one working directory. In-repository worktrees must be ignored before use. Independent directories do not isolate databases, ports, dependencies, credentials or external services.

Tack's local Git settings and execution trust are clone-wide: linked worktrees share them by default. Run `tack status`, `tack mode` and relevant `tack config ... --get` queries in the intended directory. Use a conversational task mode rather than changing shared local defaults underneath concurrent work. The root `tack.json` is the version from that branch. Do not enable Git's worktree configuration extension or transfer trust automatically.

Keep this task's handoff tied to its branch. Use `tack team --base REF --against REF` for known branch comparisons and contract/integration tests for behavior. A clean merge does not prove compatibility. On a conflict, understand both changes, preserve both intended behaviors, and document the resolution and checks in the relevant PR/handoff.

Before cleanup, inspect status including ignored/private notes and unmerged commits. Use normal `git worktree remove PATH` only after useful work is preserved and removal is authorized. Never force-delete dirty worktrees or remove another task's branch. Retain an explicit limitation when remote/base knowledge is stale.
