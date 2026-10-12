# Installation reference

Clone into any directory you choose and run `./install.sh` from that checkout. Installation exposes global configuration through symlinks; you can enable the workflow in any Git project, independently of where tack repository lives. Keep the checkout available or reinstall after moving it.

```bash
./install.sh --dry-run                 # preview links, settings, Git, plugin and mod actions
./install.sh --dry-run --skip-plugins  # preview local configuration only
./install.sh --skip-plugins            # apply local configuration only (also skips mods)
./install.sh --skip-mods               # apply everything except the Claude Code mods
./install.sh --no-hooks                # instructions, skills, agents and settings, but no hooks
tack doctor                        # check installation and current project; no writes
tack doctor --tools                # check each installed AI tool instead of the project
./uninstall.sh --dry-run               # preview safe restoration
./uninstall.sh                         # restore recorded unchanged state
```

A fresh installation has one set active, `core`, with two skills: `dev-workflow` and `new-project`. Every other skill and every agent role comes with a [set](sets.md), which you activate in one project or everywhere:

```bash
tack set list                      # what exists and where it is active
tack set use testing               # in this project
tack set use review --global       # everywhere, applied by ./install.sh
tack set use tack-skills --global   # every skill of this repository at once
tack set use tack-agents --global   # every agent role at once
```

Dropping a set and reinstalling removes only tack's own skill links and unchanged generated roles; edited and foreign files stay, and a link that displaced a file of yours remains until uninstall can restore it. Which sets are active is a personal choice saved in Git config, not a shared project setting.

Upgrading from a version with skill groups: the `skill-groups` and `agent-roles` settings are no longer read. Run `tack migrate` once; a choice of optional groups becomes `tack-skills`, enabled roles become `tack-agents`, and `./install.sh` then leaves your installation as it was.

## Updating
```bash
cd /path/to/your/agent-tack && git pull && ./install.sh
```
Replace the path with the directory you chose during installation.
To change a rule, edit the files here or tell the AI (it uses `lessons`), then commit and push. Changes apply at once on this machine through the symlinks; restart the tool for new skills or agents.

### Upgrading from agent-harness

The project was called agent-harness and its command `harness`. Before updating an existing installation beyond [v0.1.0](https://github.com/nbfrodri/agent-tack/releases/tag/v0.1.0), use that transition release to run `./install.sh`, then run `tack migrate` and `tack doctor` in every old project clone. Commit shared marker renames and update scripts to invoke `tack`. See the [release migration steps](../CHANGELOG.md#migration-before-updating-beyond-v010).

After migration, update tack and run `./install.sh`:

- `tack` is the command; the `harness` alias is gone, and the installer removes its links.
- Settings under `harness.*` and a project's `.harness` marker are no longer read. `tack doctor` warns when they are in use; run `tack migrate` in each such clone (it also moves your user-wide settings) to move them to `tack.*` (a `tack.*` value already set wins) and rename `.harness` to `.tack`.
- The installer moves `~/.config/agent-harness` (your modes and guard rules) and `~/.local/state/agent-harness` (installation records) to `agent-tack`, re-tags hooks from `#harness` to `#tack`, and replaces the `agent-harness-mods` marketplace with `agent-tack-mods`. Until it runs, the guard still reads your rules from the former folder.
- The git hooks' overrides are `TACK_ALLOW_*`; the former `HARNESS_ALLOW_*` variables no longer work.
- Codex sees new hook commands, so run `/hooks` in Codex and approve them again.
- Other machines keep working with the old names until you update them the same way.
