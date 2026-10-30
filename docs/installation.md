# Installation reference

Installation exposes global configuration through symlinks into a checkout of this repository; you can enable the workflow in any Git project, independently of where that checkout lives. Keep it available or reinstall after moving it. There are two ways to get one:

- **Release install** (no manual clone): `curl -fsSL https://raw.githubusercontent.com/nbfrodri/agent-tack/main/get.sh | bash`. It needs Git, Bash and Python 3, checks the latest release tag out into `${XDG_DATA_HOME:-~/.local/share}/agent-tack/release` (set `TACK_DIR` to choose another folder) and runs that release's `install.sh`. Installer options follow `bash -s --`, for example `| bash -s -- --skip-plugins`. Running it again updates an existing release install through `tack update`.
- **Working clone**: clone into any directory you choose and run `./install.sh` from it. Use this to change tack itself.

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

A fresh installation has one set active, `core`, with three skills: `dev-workflow`, `new-project` and `tack`. Every other skill and every agent role comes with a [set](sets.md), which you activate in one project or everywhere:

```bash
tack set list                      # what exists and where it is active
tack set use testing               # in this project
tack set use review --global       # everywhere, applied by ./install.sh
tack set use tack-skills --global   # every skill of this repository at once
tack set use tack-agents --global   # every agent role at once
```

Dropping a set and reinstalling removes only tack's own skill links and unchanged generated roles; edited and foreign files stay, and a link that displaced a file of yours remains until uninstall can restore it. Which sets are active is a personal choice saved in Git config, not a shared project setting.

Upgrading from a version with skill groups: the `skill-groups` and `agent-roles` settings are no longer read. Run `tack migrate` once; a choice of optional groups becomes `tack-skills`, enabled roles become `tack-agents`, and `./install.sh` then leaves your installation as it was.

## Shell completions

The installer writes bash completion to `${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/tack`
and, when `fish` is on PATH, fish completion to `${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/tack.fish`.
Bash loads it lazily when bash-completion is enabled; fish loads its completion directory automatically.
Candidates come from tack's commands, sets, features and built-in/user modes at completion time.
Edited files and foreign files are kept with a warning; uninstall removes only unchanged files it owns.
The step also runs with `--skip-plugins`, `--skip-mods` and `--no-hooks`. `--dry-run` previews writes.
Disable future installation with `tack config completions false --global` (default: true),
then run `./uninstall.sh` if you also want to remove previously installed files.

For bash without bash-completion, add this manual alternative to your shell startup file:

```bash
eval "$(tack completion bash)"
```

`tack completion fish` prints the fish script. Zsh is manual: save `tack completion zsh` as
`_tack` in a directory on `fpath`, adding that directory before `compinit`:

```zsh
mkdir -p ~/.local/share/zsh/site-functions
tack completion zsh > ~/.local/share/zsh/site-functions/_tack
fpath=(~/.local/share/zsh/site-functions $fpath)
autoload -Uz compinit && compinit
```

## Updating

A release install updates itself:

```bash
tack update --check                 # installed and latest release, with the new changelog entries; no changes (also --dry-run)
tack update                         # check out the latest release and rerun its install.sh
tack update --skip-plugins          # install.sh options are passed on (--skip-plugins, --skip-mods, --no-hooks, --verbose)
```

`tack update` works on the checkout `tack` runs from, fetches its release tags (`vMAJOR.MINOR.PATCH`; prereleases are skipped) and prints the previous and new version. It does nothing when the checkout is at the latest release or already contains it. It refuses a checkout on a branch, such as a working clone, or one with local changes to tracked files, and suggests `git pull && ./install.sh` instead; `--force` moves it to the release anyway, and Git still refuses to overwrite a local change that conflicts with it.

A working clone is updated with Git:

```bash
cd /path/to/your/agent-tack && git pull && ./install.sh
```
Replace the path with the directory you chose during installation. Running `get.sh` on a machine with a working clone installed makes the release checkout the one the links point to; run the clone's `./install.sh` to switch back.
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
