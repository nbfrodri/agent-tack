# Customization

The harness is meant to be your own configuration. After cloning the repository, you can change its rules, workflow, skills, agents, tools, plugins and hooks to suit how you work.

## Make it yours

Clone it into any directory you choose and install from that checkout, as shown in the [README](../README.md#install). Use a fork or your own copy if you want to keep personal changes in a separate remote repository; a local clone is enough for changes on one machine.

| What you want to change | Where to edit |
| --- | --- |
| Conversation language, permissions and global preferences | `global/AGENTS.md` |
| Planning, testing, commits and documentation workflow, and what each level requires | `skills/dev-workflow/` and its references (default level: `harness mode <mode> --global`) |
| Task-specific guidance or reusable templates | `skills/<name>/SKILL.md`, `references/` and `assets/` |
| Automatic delegation, complexity routing and model fallbacks | `skills/orchestrate/` (per-project opt-out: `harness config delegation off`) |
| Feature toggles shown by `harness config` | `features.txt`: one line per toggle (name, git key, default, allowed values, scope, enforcement, description). Code that honours a new toggle reads its git key; keep safety checks out of the registry |
| Agent responsibilities and defaults | `agents/*.md` |
| Supported tools and installation paths | `targets.txt` |
| Claude Code settings and registered hooks | `claude/settings.json` |
| Installed marketplaces and plugins | `plugins.txt` |
| Git checks and command or formatting policies | `git-hooks/` and `hooks/claude/` |
| Commands the guard asks about or refuses | `hooks/claude/guard-policy.txt` (shared rules) or, for your machine only, `~/.config/agent-harness/guard-policy.txt` with the same `scope \| decision \| pattern \| reason` format; personal rules can only add ask or deny decisions |

You can add or remove skills, agents and plugins, choose different conventions, or change the workflow itself. Keep the [architecture](architecture.md), component list and usage documentation consistent with your choices. Project-level instructions take precedence over the global rules, so preferences for a single project belong in that project's `AGENTS.md`.

## Apply and check changes

Instructions, skills, agents and hook scripts are installed through symlinks to the checkout. Editing them changes the installed files directly; start a new agent session to load updated instructions, skills and agent definitions.

Re-run `./install.sh` after changing tool paths, registered hooks, Claude settings or plugins, or after adding or removing skills or agents. Use `./install.sh --skip-plugins` when you only need local configuration changes.

To support another AI tool, add one line to `targets.txt` (columns are documented in its header and in [how it works](how-it-works.md#targetstxt-columns)); optionally set a minimum version and a smoke check, then run `harness doctor --tools`.

Run `tests/validate.sh` after changing skills, agents or their references. Changes to installer or hook behaviour also need regression tests and the relevant checks in [development](development.md).

## Keep personal changes when updating

Commit your changes in your own copy before incorporating upstream updates. Review incoming changes and resolve conflicts deliberately, then rerun the checks and installer. The settings merge preserves unrelated user keys and separate user hook groups, but harness-owned values come from your checkout; edit them there so reinstalling uses your chosen values.

For sharing your copy or setting up an upstream remote, see [sharing](sharing.md).
