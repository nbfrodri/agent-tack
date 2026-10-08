# Stop using tack or tidy old project records

Your code and project documentation remain yours. You can disable tack without deleting either. Completing a feature does not require removing its architecture notes, tests or development guide.

## Stop using it in your clone

Keep the team's shared activation file and opt out locally:

```bash
git config --local tack.enabled false
tack trust --revoke
tack status
```

`status` returns exit code 1 for a disabled project. Other clones are unaffected. Installed global instructions and always-on Git protections still exist; project instructions in AGENTS.md remain available to your AI tool. To use tack again, run `tack enable` and grant execution trust separately when appropriate.

## Retire it for the project

```bash
tack disable
tack trust --revoke
git diff -- .tack
```

`disable` sets local activation to false and removes the shared `.tack` marker. Review and commit that removal when the team agrees. Teammates with an explicit local enable must also disable their own clones. Trust is local and must be revoked in each clone where that is desired.

Review remaining files individually:

| Item | What to consider |
| --- | --- |
| `tack.json`, `checks-map.json`, `docs-map.txt` | Remove if no remaining automation uses them; check callers and references first. |
| `AGENTS.md`, `CLAUDE.md` | Keep useful project conventions. Remove tack-specific instructions or a bridge only when no tool needs them. |
| Architecture, setup guides and ADRs | Keep maintained project knowledge regardless of which assistant created it. |
| Plans, handoffs and AI logs | Archive completed work that is still useful; remove obsolete records after checking links and active work. |
| Project-local skills and agents | Keep useful procedures or remove selected definitions and their index entries. Preserve any shared references still in use. |

Tack does not own a project file merely because it initially scaffolded it. There is no automatic project purge command: current scaffolding does not keep the provenance needed to decide which edited documents are safe to delete. The machine installer's ownership records cover machine integrations, not project documentation.

## Reduce old documentation

Ask the assistant for a bounded cleanup:

> Review completed plans and handoffs in this project's configured locations. Propose an exact list to archive or remove, explain what is obsolete, and check incoming links. Keep active work, current conventions, architecture and relevant decisions. Show the proposal before deleting anything.

Archive retained history outside active plan/handoff locations and update links. Remove misleading instructions from active entrypoints rather than expecting the assistant to read all historical documents. Tack's startup context is already bounded and loads additional documents as needed: total Markdown size alone is not session context size.

## Remove the machine installation

From your tack checkout:

```bash
./uninstall.sh --dry-run
./uninstall.sh
```

This restores recorded unchanged machine integrations and preserves independently changed files. It does not delete project files, activation settings or local trust. See the [installation reference](installation.md) for restoration limits, and review project choices separately.

Private working notes are preserved too. Review [`.private/tack/`](private-notes.md) manually, including ignored files before removing a worktree. Uninstalling tack does not make these notes safe to delete.
