# Private working notes

Use when the user selects local scratch context during setup or asks to keep personal notes outside versioned documentation. Prefer an existing project convention. Otherwise use `.private/tack/`; do not create it during ordinary activation.

Preview the supplied `assets/setup-private.py` with the repository root and `--dry-run`. After selection, run it without that flag. The default uses Git's local exclude; `--shared-ignore` appends `/.private/` to the project's `.gitignore` so contributors share the convention. It refuses tracked private files, linked destinations and incompatible paths, and preserves existing notes. Check the resulting ignore rule and diff. It does not untrack existing history.

Save rough investigation notes and personal task context here. Keep canonical contracts, decisions, commands and handoffs required by teammates in their versioned locations. A private note is read only for a relevant task; never sweep the folder into startup context, public reports, review bundles or shared handoffs. Git ignore is not encryption or an AI access control. Do not store credentials here.

Each worktree has its own notes directory; a local exclude can be shared through Git's common directory. Before removing a worktree, inspect private/untracked contents and preserve useful notes. Never automatically remove this folder at task completion, uninstall or archive time. Copy only selected reviewed facts into shared documentation.
