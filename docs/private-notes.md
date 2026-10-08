# Keep personal notes local

Use `.private/tack/` for rough investigation notes or personal task context that teammates do not need. It is optional. Keep shared contracts, decisions, setup commands and useful team handoffs in the project's versioned documentation.

During setup, ask your assistant:

> Set up private working notes for this repository. Preview the files first. Keep notes out of Git and keep shared contracts in our existing docs.

The supplied helper can also be run directly from the repository root. Replace `/path/to/agent-tack` with your tack checkout:

```bash
python3 /path/to/agent-tack/skills/project-docs/assets/setup-private.py . --dry-run
python3 /path/to/agent-tack/skills/project-docs/assets/setup-private.py .
```

By default it adds `/.private/` to Git's local exclude file. Add `--shared-ignore` to use the project's `.gitignore`, so the team shares the convention. It preserves existing notes, refuses tracked private files and linked destinations, and does not remove anything. If a project rule overrides the local exclusion, it reports the conflict before creating notes; review the rule or choose the shared convention.

Git ignore does not encrypt notes or prevent an AI tool from reading them. Do not store credentials here. The assistant should read only relevant notes and avoid including them in shared context, reviews or reports. Teammates must be able to work without your private folder.

Each worktree has separate note files, although its Git exclude settings may be shared. Preserve useful notes before removing a worktree. Disabling or uninstalling tack does not delete them; review them manually when tidying a project.
