# Sharing it with someone else

The repo holds its owner's preferences, so another person runs their own copy.

You can customize every part of your copy to fit your own workflow; see [customization](customization.md) for the file map and how changes are applied.

1. **Get access:** the owner invites them as a collaborator, or makes the repo public or a template.
2. **Create their copy:** *Use this template* or fork, so their rules stay versioned in their own repo.
3. **Install:**
   ```bash
   git clone https://github.com/<their-user>/agent-tack.git ~/Projects/agent-tack
   ~/Projects/agent-tack/install.sh
   ```
   The directory is your choice; replace the example path in both commands. Keep the checkout there because installed files link to it, or re-run `install.sh` after moving it.
4. **Adapt the personal bits:**
   | File | What to change |
   | --- | --- |
   | `global/AGENTS.md` | The "ask before" rules (every agent and skill follows it). The assistant already replies in the language you write in; other personal preferences fit in `tack memory add`, which Claude Code and Codex load every session |
   | `skills/dev-workflow/references/conventions.md` | Stack choices: pnpm, kebab-case, merge commits, release-please… |
   | `plugins.txt`, `claude/settings.json` | Claude Code plugins and settings |
   | `README.md`, `bin/tack` | The repo URL |
5. **Restart the tools and enable a project:** `tack enable`.
6. **Get updates from the original:** `git remote add upstream <original-url>`, then `git pull upstream main` and `./install.sh`.

Already per-user, no changes needed: the git identity, existing Claude Code settings and hooks (merged), and any global `core.hooksPath` of their own (left alone).
