# Rename to agent-tack (repository) and tack (command)

- Status: done (PR #40, merged as `447d228`; GitHub repository renamed to nbfrodri/agent-tack). A separate `tack migrate` command proved unnecessary: legacy keys are read indefinitely and every write moves the key.
- Level: strict (every component, user installations and other machines are affected)
- Goal: a distinctive tool name without breaking existing installations or projects.

## Scope (measured 2026-10-04)

97 tracked files mention "harness"; 45 mention "agent-harness"; about 140 references to `harness.*` git keys across 17 keys.

| Name today | New name | Compatibility |
| --- | --- | --- |
| Command `harness` | `tack` | `harness` stays as a deprecated alias symlink for a transition period; it prints a one-line notice on stderr |
| Repository `nbfrodri/agent-harness` | `nbfrodri/agent-tack` | GitHub redirects the old URL; docs use the new one |
| Git keys `harness.*` (enabled, mode, trusted, toggles) | `tack.*` | Readers check `tack.*` first, then `harness.*`; the installer migrates global keys once; `tack migrate` migrates a project's local keys; old keys keep working during the transition |
| Project marker `.harness` | `.tack` | Both recognised; `tack enable --shared` writes `.tack` |
| `~/.agents/harness`, `~/.config/agent-harness/`, `~/.local/state/agent-harness/` | `~/.agents/tack`, `~/.config/agent-tack/`, `~/.local/state/agent-tack/` | Installer moves user modes, guard policy and ownership state; old paths read if present |
| Hook tag `#harness` in settings | `#tack` | The settings merge replaces both tags (as it did for `#agent-config`) |
| Marketplace `agent-harness-mods` | `agent-tack-mods` | Installer adds the new one and removes the old one it owns |
| Words "harness" in docs and skills | "tack" where it names the tool | The concept may still be described as a harness |

## Order

1. Compatibility layer first: readers accept both key prefixes, markers and paths (tests for each).
2. CLI rename with the `harness` alias; help, docs and the drift test.
3. Installer migration of global keys, paths, marketplace and hook tags, with dry-run and uninstall support; tests on a home installed by the old version.
4. Docs, skills, agents and README rename; validator and drift checks.
5. GitHub repository rename (owner action through `gh repo rename`, with confirmation), then update the remote and links.
6. Full suite, review, PR, merge; announce the alias removal for a later release.

## Risks

- Other machines with the old checkout keep working through the alias and old keys until they update.
- Codex hooks change their command path, so Codex asks to re-approve them with `/hooks`.
- Claude Code plugin caches keep the old marketplace until reinstall; the installer handles it.
