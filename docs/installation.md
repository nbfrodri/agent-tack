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

Skills come in groups (`skill-groups.txt`): `core` (workflow, onboarding, reviews and delegation, always installed), `process` (releases) and `stack` (frontend, APIs, databases, auth, end-to-end tests, deployment, observability). Fewer skills mean fewer descriptions in every session of every tool. Choose the optional groups once, then re-run the installer; it removes only its own links to the skills you left out:

```bash
tack config skill-groups process --global   # core and process; or core, stack, or all (the default)
./install.sh
```

The first install that registers hooks ends with a short list of them and what each does (from `hooks/summary.txt`), and how to turn them off; later installs skip it. `--no-hooks` registers no git, Claude Code or Codex hooks and removes tack's Claude Code and Codex hooks from an earlier install (your own hooks stay); global git hooks from an earlier install remain until `./uninstall.sh`, which restores your former `core.hooksPath`. Without hooks the rules apply only as instructions.

Doctor checks required tools, managed links, Claude settings and hook registration, ownership metadata, effective Git hooks, project activation and formatter trust. Missing optional CLIs and deliberate foreign hooks paths produce warnings. Broken managed components produce errors (exit 1); a healthy checked installation exits 0. Doctor works outside Git and never runs plugins or prints restoration snapshots or credentials. It diagnoses configuration rather than proving every external tool works. Doctor also warns when the claude CLI is missing or a tack mod is not installed or is disabled, and reports `chat.useAgentsMdFile` for each VS Code install it finds.

`tack doctor --tools` checks each installed AI tool listed in `targets.txt`: version, configured capabilities, minimum version and a non-interactive smoke check (`claude doctor`, `codex doctor --summary`). It prints no tool output or credentials. A failed smoke check or an old version is a warning; a broken managed link is an error. A weekly CI workflow installs the latest Claude Code and Codex and runs the same check, so breaking changes in either tool surface early.

Installation records changes privately under `${XDG_STATE_HOME:-$HOME/.local/state}/agent-tack/ownership`. Original state and installation-time tool declarations survive reinstallations, so later customization does not invalidate historical ownership. These snapshots may include private settings: do not commit or share them. Uninstall needs Python to validate ownership and selectively restore settings. It removes unchanged recorded links, restores safely displaced original files or links, and reverses unchanged owned settings and Git hooks. Changed links, parent directories, settings and hooks are preserved conservatively; retained records allow a later retry.

Uninstall never deletes project files, project activation/trust configuration or shared plugins. It removes only the mods and local marketplace recorded by the installer; plugins from `plugins.txt`, and mods or marketplaces you already had, are kept.

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
