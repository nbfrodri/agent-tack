# Set up tack

Install tack once, enable a project and reuse its existing guidance. The same setup works for personal projects and teams. Extra templates are optional.

Joining a project that already uses tack? Run its documented installer (such as `python3 scripts/setup-tack.py`), then **`tack setup`**. It shows the shared choices, local differences and execution trust. Reuse the recorded decisions; you do not need to configure the project again. Cloning alone does not install tack.

If you only want to run project checks, you can [use the CLI directly](verification.md#use-the-checks-without-installing-ai-guidance) without installing AI guidance or enabling the workflow.

## 1. Install

You need Git, Bash 3.2+ and Python 3.9+. Use Linux, macOS, WSL2 or native Windows with Git Bash. See [platform details](editors.md#windows), including native Windows symlink requirements.

```bash
git clone https://github.com/nbfrodri/agent-tack.git ~/Projects/agent-tack
~/Projects/agent-tack/install.sh --skip-plugins
```

Keep the checkout: installed instructions and scripts link to it. The installer exposes `tack` in `~/.local/bin`; add that directory to your PATH if your shell cannot find it. It configures AI tools and Git hooks on this machine. It does not turn on the full workflow in every project.

This command installs the core integrations without downloading Claude plugins or mods. Preview changes with `--dry-run`. Optional catalogs, plugins, updates and removal are in the [installation reference](installation.md).

## 2. Enable a project

For your current clone:

```bash
cd ~/Projects/my-app
tack enable
```

This changes local Git configuration and adds no project files. For activation that travels with the repository:

```bash
tack enable --shared
```

This creates **`.tack`, a small marker file**. Commit it to enable tack for teammates who have installed it. It is not a folder or a settings file; it does not install tack or grant command execution trust. A local disable overrides shared activation. `tack disable` also removes the shared marker in the working tree, so review that deletion before committing it.

## 3. Review the project once

```bash
tack setup
```

Setup shows activation, mode, local trust, effective preferences and their origins. It highlights differences from shared choices and how to remove a local override if you want the shared value. Overrides are allowed; setup never removes them. It also lists detected stacks, declared commands, existing guidance and optional additions. Discovery is bounded, so a large monorepo still needs inspection of the relevant packages.

Setup does not write files, run project commands, install dependencies or grant trust. Use `--json` for the same information as data; `tack config --json` adds feature descriptions and sharing/enforcement metadata when needed. Check the guidance with:

```bash
tack setup --check  # or --check --json for scripts
```

Exit 0 means no structural problems were found in inspected guidance. Exit 1 means a broken link, unfinished generated guidance, unsafe file or missing explicitly configured architecture document needs attention. Missing optional templates do not fail the check. Link checks cover AGENTS.md and the architecture document; for CLAUDE.md, only tack's exact `@AGENTS.md` bridge is checked. Existing tool-specific imports remain the tool's responsibility. Passing does not prove the prose is accurate, the app works or every package was inspected.

Ask your assistant:

> Set up tack for this project. Read the existing conventions and tools first. Propose useful additions with their exact paths and purpose, and let me choose what to create. Keep the setup small.

In an existing project, the assistant reuses what is already there. In a new project, it asks about the intended application and stack. It can propose tests, CI, a PR template, a development guide, a check map or a reusable skill when there is a reason for one. It can also offer individual [external skills](external-skills.md) after checking for overlap with existing guidance. Nothing from those collections is downloaded by the base installer. Previous answers and approvals count; focused tasks do not need unrelated onboarding.

For team preferences, the assistant can [preview and apply the selected values together](configuration.md#apply-several-selected-preferences), including values that match current defaults. This keeps the choices portable without copying personal settings. Local-only setup remains available.

Keep agreed decisions in an existing `AGENTS.md` when useful. Finish local review with `tack config setup-review done`, including when no new files are needed. Use `deferred` to postpone or `pending` to revisit it. A fresh clone reuses shared decisions but keeps its own review state and trust.

## 4. Add base guidance if you want it

```bash
tack enable --scaffold
# Or: tack enable --shared --scaffold
```

Scaffold creates only missing files:

| File | Why it exists |
| --- | --- |
| `AGENTS.md` | Commands, conventions, links to context and recorded setup choices for the assistant |
| `CLAUDE.md` | A short `@AGENTS.md` bridge for Claude |
| `docs/architecture.md` | An initial inventory to turn into a description of real components and flows |
| `docs-map.txt` | Reminders about which docs may need review when source paths change |

The architecture location can be [configured](configuration.md#reuse-your-documentation-layout) first. Scaffold preserves existing files and rejects symlink destinations before writing. It does not generate empty plans, handoffs, agents, CI or a full application.

Generated guidance has review markers. Check it against the code, fill real information, remove the markers and repeat `tack setup --check`. A deliberately small setup can omit all four files; selecting `architecture-path` explicitly makes that file an expected part of your guidance.

## 5. Review execution and start working

```bash
tack verify --all --plan  # inspect declared checks, including on a clean clone
tack trust               # after reviewing the project's commands
tack verify --all        # run the declared checks to establish a starting point
```

Trust is local to this clone. It permits tack to run project formatters and checks; it is separate from activation and the AI tool's own permissions. Revoke it with `tack trust --revoke`.

For scripts, `tack trusted --quiet` exits 0 when locally trusted and 1 otherwise. `tack status --quiet` checks activation with the same exit-code convention; it does not check trust.

Start a new AI session to load saved choices. Leave the mode at `auto` for most work. See [daily use](usage.md), the [team walkthrough](sharing.md) or [configuration](configuration.md) for the next step.

For daily changes, use `tack verify --plan` and `tack verify` to select checks from changed paths. A clean checkout may select nothing without `--all`. Missing checks, failures, timeouts and unmapped work remain visible; review the project's documented budget and prerequisites. [Understanding verification results](verification.md#read-a-result).

To stop using tack or retire old plans, see [leaving and tidying a project](leaving.md). Disabling a workflow and deleting project knowledge are separate decisions.
