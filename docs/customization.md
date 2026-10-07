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
| Task-specific guidance or reusable templates | `skills/<name>/SKILL.md`, `references/` and `assets/`; a new skill also needs a line in `skill-groups.txt` (`core`, `process` or `stack`) |
| Which skills are installed | `tack config skill-groups --global` (`all`, or `core` plus `process` and/or `stack`), then `./install.sh` |
| Automatic delegation, complexity routing and model fallbacks | `skills/orchestrate/` (per-project opt-out: `tack config delegation off`) |
| Feature toggles shown by `tack config` | `features.txt`: one line per toggle (name of at most 23 characters, git key, default, allowed values such as `bool`, `number`, `text`, `auto|off` or `list:a|b` for a comma-separated list, scope, enforcement, description). Code that honours a new toggle reads its git key; keep safety checks out of the registry |
| Agent responsibilities and defaults | `agents/*.md` (`model:` is `inherit` or a Claude Code model from `model-tiers.txt`; `docs-writer` uses the `economical` tier because large doc updates are delegated to it) |
| Which model each tool uses for a tier | `model-tiers.txt` (`economical`, `balanced`, `strongest` per tool), or for your machine only `~/.config/agent-tack/model-tiers.txt`; check with `tack models` |
| Before and after screenshots of UI changes, scored by `ui-reviewer` | `tack config visual-review` ([usage](usage.md#visual-review-of-ui-changes)) |
| CI after a push, green-only merges and the activity log | `tack config ci-watch`, `merge-requires-green` and `activity-log` ([usage](usage.md#ci-wait-for-it-merge-only-when-green)) |
| Supported tools and installation paths | `targets.txt`; a tool whose hooks column names a file gets the template at `<tool>/<that file name>` merged by the installer (for example `cursor/hooks.json`), with a thin adapter in `hooks/<tool>/` when its hook format differs from the shared scripts |
| Claude Code settings and registered hooks | `claude/settings.json` |
| Installed marketplaces and plugins | `plugins.txt` |
| Mods shipped by tack | `plugins/<name>/` (turn them off with `./install.sh --skip-mods` or `git config --global tack.mods false`) |
| Git checks and command or formatting policies | `git-hooks/` and `hooks/claude/` |
| Commands the guard asks about or refuses | `hooks/claude/guard-policy.txt` (shared rules) or, for your machine only, `~/.config/agent-tack/guard-policy.txt` with the same `scope \| decision \| pattern \| reason` format; personal rules can only add ask or deny decisions. When you tell the assistant "never run X", the `lessons` skill proposes such a line and adds it once you agree |

You can add or remove skills, agents and plugins, choose different conventions, or change the workflow itself. Keep the [architecture](architecture.md), component list and usage documentation consistent with your choices. Project-level instructions take precedence over the global rules, so preferences for a single project belong in that project's `AGENTS.md`.

## Project capabilities

Local capabilities adapt one project without extending the shared catalog. The policy lives in `skills/lessons/references/project-capabilities.md`; the short global rule applies even when lite does not load the full workflow.

| Artifact | Purpose | Discovery |
| --- | --- | --- |
| `.agents/skills/<name>/SKILL.md` | A reusable project procedure and its checks | Native skill discovery where available, otherwise an explicit read through the project's AGENTS.md index |
| `.agents/agents/<name>.md` | A role's responsibility, context, boundaries and output | A portable instruction file; pass it to an authorized delegation tool or perform the checks sequentially |

Both need `name` and a single-line `description` in YAML frontmatter; the name matches the folder or role filename. Descriptions are limited to 400 and 300 characters respectively. Link real project commands and references instead of copying general manuals. Reuse an existing definition rather than creating a suffixed duplicate.

Run `python3 ~/.agents/tack/lib/capability_validation.py project .` to check definitions, reference paths and discovery from AGENTS.md. For an existing layout, specify `--skills-dir` and `--agents-dir` relative to the project. Validation does not execute scripts or prove that the model will use the instructions correctly; verify the actual procedure or review on its task.

The assistant can make these local additions during authorized implementation, but a review or plan does not authorize unrelated writes. Native agent registration and automatic reload are not assumed. Promotion to `skills/` or `agents/` in tack is a separate reviewed change, justified by cross-project reuse and followed by catalog validation.

## Apply and check changes

Instructions, skills, Claude agents and hook scripts are linked to the checkout. Other native agent definitions are generated; rerun the installer to refresh them. Edited generated files are preserved. Start a new agent session to load updated instructions, skills and agents.

Re-run `./install.sh` after changing tool paths, registered hooks, Claude settings or plugins, or after adding or removing skills or agents. Use `./install.sh --skip-plugins` when you only need local configuration changes.

To support another AI tool, add one line to `targets.txt` (columns are documented in its header and in [how it works](how-it-works.md#targetstxt-columns)); optionally set a minimum version and a smoke check, then run `tack doctor --tools`.

Run `tests/validate.sh` after changing skills, agents or their references. Changes to installer or hook behaviour also need regression tests and the relevant checks in [development](development.md).

## Add or remove a mod

To add one, create `plugins/<name>/` with `.claude-plugin/plugin.json` (`name`, `version`, `description`, `author`), `hooks/` and tests, and list it in `plugins/.claude-plugin/marketplace.json` with `"source": "./<name>"`; then run `claude plugin validate plugins/<name>` and `claude plugin test plugins/<name>`, and `./install.sh`. To remove one, delete its folder and its marketplace entry, and run `claude plugin uninstall <name>@agent-tack-mods` (the installer does not remove mods you deleted from the repo). To change a mod, edit it and bump `version`, then re-run `./install.sh`. To stop using mods entirely, run `./uninstall.sh` and set `git config --global tack.mods false`.

## Keep personal changes when updating

Commit your changes in your own copy before incorporating upstream updates. Review incoming changes and resolve conflicts deliberately, then rerun the checks and installer. The settings merge preserves unrelated user keys and separate user hook groups, but tack-owned values come from your checkout; edit them there so reinstalling uses your chosen values.

For sharing your copy or setting up an upstream remote, see [sharing](sharing.md).
