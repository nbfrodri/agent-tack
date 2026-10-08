# Set up tack

Install tack once on your machine, then enable it in the projects where you want to use it. The same setup works for personal projects and team repositories.

## 1. Install

You need Git, Bash 3.2+ and Python 3.9+. Use Linux, macOS, WSL2 or native Windows with Git Bash. See [platform details](editors.md#windows), including native Windows symlink requirements.

```bash
git clone https://github.com/nbfrodri/agent-tack.git ~/Projects/agent-tack
~/Projects/agent-tack/install.sh
```

Keep the checkout: installed instructions and scripts link to it. The installer exposes `tack` in `~/.local/bin`; add that directory to your PATH if your shell cannot find it. It configures AI tools and Git hooks on this machine. It does not turn on the full workflow in every project.

For a local installation without downloading Claude plugins or mods, use `install.sh --skip-plugins`. Preview changes with `--dry-run`. More options, diagnostics, updates and removal are in the [installation reference](installation.md).

## 2. Enable a project

If your project already includes `scripts/setup-tack.py`, use its documented setup instead of a separate install. Owners can offer [optional pinned collaborator setup](installation.md#optional-setup-for-collaborators); cloning alone does not install tack.

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

## 3. Inspect what the project already has

```bash
tack setup
```

Setup lists detected stacks, declared commands, existing skills and roles, PR templates and missing base guidance. It does not run project code or create optional files. Discovery is bounded, so a large monorepo still needs inspection of the relevant packages.

Ask your assistant:

> Set up tack for this project. Read the existing conventions and tools first. Propose useful additions with their exact paths and purpose, and let me choose what to create. Keep the setup small.

In an existing project, the assistant reuses what is already there. In a new project, it asks about the intended application and stack. It can propose tests, CI, a PR template, a development guide, a check map or a reusable skill when there is a reason for one. It can also offer individual [external skills](external-skills.md) after checking for overlap with existing guidance. Nothing from those collections is downloaded by the base installer. Previous answers and approvals count; focused tasks do not need unrelated onboarding.

For team preferences, the assistant can [preview and apply the selected values together](configuration.md#apply-several-selected-preferences), including values that match current defaults. This keeps the choices portable without copying personal settings. Local-only setup remains available.

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

Generated guidance has review markers. The assistant should check it against the code, fill real information and remove the markers. Then run:

```bash
tack setup --check
tack config setup-review done
```

`--check` reports missing base files, review markers and broken local links or docs-map targets. It does not prove the prose is accurate. If you intentionally skip setup, use `tack config setup-review deferred`; use `pending` to revisit it. Record agreed choices in `AGENTS.md` so another session can reuse them.

## 5. Review execution and start working

```bash
tack verify --plan  # inspect selected commands without executing them
tack trust          # after reviewing the project's commands
tack status
```

Trust is local to this clone. It permits tack to run project formatters and checks; it is separate from activation and the AI tool's own permissions. Revoke it with `tack trust --revoke`.

For scripts, `tack trusted --quiet` exits 0 when locally trusted and 1 otherwise. `tack status --quiet` checks activation with the same exit-code convention; it does not check trust.

Start a new AI session to load saved choices. Leave the mode at `auto` for most work. See [daily use](usage.md), the [team walkthrough](sharing.md) or [configuration](configuration.md) for the next step.

On a fresh clone, use `tack verify --all --plan` to inspect all declared checks, then `tack verify --all` after local trust to establish a tested starting point. Ordinary `verify` may select nothing on an unchanged checkout. If AGENTS.md has a `Setup choices` section, startup points the assistant to those decisions so it can reuse them; this does not grant trust or mark local review complete.

To stop using tack or retire old plans, see [leaving and tidying a project](leaving.md). Disabling a workflow and deleting project knowledge are separate decisions.
