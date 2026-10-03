# Sharing it with someone else

The repo holds its owner's preferences, so another person runs their own copy.

1. **Get access:** the owner invites them as a collaborator, or makes the repo public or a template.
2. **Create their copy:** *Use this template* or fork, so their rules stay versioned in their own repo.
3. **Install:**
   ```bash
   git clone https://github.com/<their-user>/agent-harness.git ~/Projects/agent-harness
   ~/Projects/agent-harness/install.sh
   ```
4. **Adapt the personal bits:**
   | File | What to change |
   | --- | --- |
   | `global/AGENTS.md` | The language the AI speaks and the "ask before" rules (every agent and skill follows it) |
   | `skills/dev-workflow/references/conventions.md` | Stack choices: pnpm, kebab-case, squash merge, release-please… |
   | `plugins.txt`, `claude/settings.json` | Claude Code plugins and settings |
   | `README.md`, `bin/harness` | The repo URL |
5. **Restart the tools and enable a project:** `harness enable`.
6. **Get updates from the original:** `git remote add upstream <original-url>`, then `git pull upstream main` and `./install.sh`.

Already per-user, no changes needed: the git identity, existing Claude Code settings and hooks (merged), and any global `core.hooksPath` of their own (left alone).
