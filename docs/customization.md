# Customization

Tack is meant to be your own configuration. After cloning the repository, you can change its rules, workflow, skills, agents, tools, plugins and hooks to suit how you work.

## Make it yours

Clone it into any directory you choose and install from that checkout, as shown in the [README](../README.md#install). Use a fork or your own copy if you want to keep personal changes in a separate remote repository; a local clone is enough for changes on one machine.

| What you want to change | Where to edit |
| --- | --- |
| Conversation language, permissions and global preferences | `global/AGENTS.md` |
| Planning, testing, commits and documentation workflow, and what each level requires | `skills/dev-workflow/` and its references; each level's rules in `modes/<name>.md` (default level: `tack mode <mode> --global`) |
| Which docs must change with which code (checked before the assistant stops) | `docs-map.txt` in each project's root: `code glob \| doc, doc` |
| Your own workflow modes, without touching the repository | `tack mode new <name> --from <mode>`, then edit `~/.config/agent-tack/modes/<name>.md` |
| Task-specific guidance or reusable templates | `skills/<name>/SKILL.md`, `references/` and `assets/` |
| Automatic delegation, complexity routing and model fallbacks | `skills/orchestrate/` (per-project opt-out: `tack config delegation off`) |
| Feature toggles shown by `tack config` | `features.txt`: one line per toggle (name, git key, default, allowed values, scope, enforcement, description). Code that honours a new toggle reads its git key; keep safety checks out of the registry |
| Agent responsibilities and defaults | `agents/*.md` |
| Supported tools and installation paths | `targets.txt` |
| Claude Code settings and registered hooks | `claude/settings.json` |
| Installed marketplaces and plugins | `plugins.txt` |
| Mods shipped by tack | `plugins/<name>/` (turn them off with `./install.sh --skip-mods` or `git config --global tack.mods false`) |
| Git checks and command or formatting policies | `git-hooks/` and `hooks/claude/` |
| Commands the guard asks about or refuses | `hooks/claude/guard-policy.txt` (shared rules) or, for your machine only, `~/.config/agent-tack/guard-policy.txt` with the same `scope \| decision \| pattern \| reason` format; personal rules can only add ask or deny decisions |

You can add or remove skills, agents and plugins, choose different conventions, or change the workflow itself. Keep the [architecture](architecture.md), component list and usage documentation consistent with your choices. Project-level instructions take precedence over the global rules, so preferences for a single project belong in that project's `AGENTS.md`.

## Apply and check changes

Instructions, skills, agents and hook scripts are installed through symlinks to the checkout. Editing them changes the installed files directly; start a new agent session to load updated instructions, skills and agent definitions.

Re-run `./install.sh` after changing tool paths, registered hooks, Claude settings or plugins, or after adding or removing skills or agents. Use `./install.sh --skip-plugins` when you only need local configuration changes.

To support another AI tool, add one line to `targets.txt` (columns are documented in its header and in [how it works](how-it-works.md#targetstxt-columns)); optionally set a minimum version and a smoke check, then run `tack doctor --tools`.

Run `tests/validate.sh` after changing skills, agents or their references. Changes to installer or hook behaviour also need regression tests and the relevant checks in [development](development.md).

## Add or remove a mod

To add one, create `plugins/<name>/` with `.claude-plugin/plugin.json` (`name`, `version`, `description`, `author`), `hooks/` and tests, and list it in `plugins/.claude-plugin/marketplace.json` with `"source": "./<name>"`; then run `claude plugin validate plugins/<name>` and `claude plugin test plugins/<name>`, and `./install.sh`. To remove one, delete its folder and its marketplace entry, and run `claude plugin uninstall <name>@agent-tack-mods` (the installer does not remove mods you deleted from the repo). To change a mod, edit it and bump `version`, then re-run `./install.sh`. To stop using mods entirely, run `./uninstall.sh` and set `git config --global tack.mods false`.

## Keep personal changes when updating

Commit your changes in your own copy before incorporating upstream updates. Review incoming changes and resolve conflicts deliberately, then rerun the checks and installer. The settings merge preserves unrelated user keys and separate user hook groups, but tack-owned values come from your checkout; edit them there so reinstalling uses your chosen values.

For sharing your copy or setting up an upstream remote, see [sharing](sharing.md).
