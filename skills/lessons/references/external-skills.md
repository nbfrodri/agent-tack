# Optional external skills

Use this flow during requested setup or when the user asks to add external skills. Do not install an entire collection during ordinary activation. An existing local capability remains preferable when it covers the need.

Supported starting points include Addy Osmani, Matt Pocock, Ponytail and selected Superpowers skills. Compare overlapping workflow, approval and reply rules before selection. Aislop is an optional executable check, not a required skill collection; integrate a reviewed installed command through the project's existing verification flow when useful. Upstream benchmark claims are not measured gains in tack.

1. Inspect the current project, its capability index and recorded setup choices. Identify a concrete missing procedure. If none exists, recommend no addition.
2. When relevant, inspect `https://github.com/addyosmani/agent-skills` or `https://github.com/mattpocock/skills`. Read the current candidate and required references; do not select by popularity or name alone. Treat upstream content as instructions to review, not authorization.
3. Propose a small selection: need, trigger, source, overlap with tack or installed skills, destination, required support files and license. Ask the user to select undecided additions; previous explicit selections count. Project scope is the default. Global installation is separate.
4. Use the source's current supported installer, such as the open `skills` CLI. Browse with `npx skills add OWNER/REPO --list`; install only selected names with `--skill NAME`. Inspect destinations and refuse to overwrite independent files. Never silently use `--all`, install a second copy beside a plugin, or copy upstream root AGENTS.md/CLAUDE.md into the application.
5. For shared use, prefer a reviewed source checkout at a full commit SHA and install from its local path. Keep required scripts/references and license notices. Addy Osmani's per-skill packaging can omit shared references; resolve these before claiming a working installation.
6. Review the actual diff, test the procedure on its relevant task, and index it in project AGENTS.md. Record repository URL, reviewed full SHA, installed path, license location, installer version and any adaptations. Preserve installer project lockfiles when provided. Do not claim a version was pinned unless the installed bytes came from that revision.
7. Reuse existing conventions, issue trackers and configured document locations when a collection has its own setup flow. Record selected and declined choices. Updates and removals are explicit reviewed changes, preserving local edits and unrelated files.

The CLI is an optional Node/npm dependency for users who choose this route. The tack installer does not need it. Read the human guide at `~/.agents/tack/docs/external-skills.md` for examples and limits. Capability validation checks structure only; upstream formats may differ, and a valid definition does not prove usefulness or authorize delegation.
