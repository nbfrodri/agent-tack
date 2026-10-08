# Project configuration

Use `AGENTS.md` for project conventions and `tack config` for settings the CLI and hooks read. Both can travel with the project. You do not need a fork to share them.

## Choose where a preference belongs

| Scope | Command | Where it is saved | Who receives it |
| --- | --- | --- | --- |
| This clone | `tack config reply-style visual` | Local Git config | You, in this clone |
| Shared project | `tack config reply-style brief --shared` | Project `tack.json` | Anyone who pulls the committed file |
| Personal default | `tack config reply-style detailed --global` | User Git config | You, across projects |

The order is **local override → shared project value → personal default → tack default**. A request in conversation can change how the assistant handles that task without changing saved settings. It cannot alter executable hook settings by itself.

```bash
tack config                         # settings, values, sources and enforcement
tack config reply-style             # for example: brief (shared)
tack config reply-style --get       # raw value for scripts
tack config reply-style --json      # value, source and sharing metadata
tack config reply-style --unset     # remove this clone's override
tack config reply-style --unset --shared
```

`--global` and `--shared` can also read only that scope. They cannot be combined. Removing a setting restores the next applicable value.

## Shared mode

```bash
tack mode auto --shared  # usual team default, selected per task
tack mode strict        # persistent override in this clone
tack mode --unset       # inherit the shared mode again
```

Shared modes are `auto`, `lite`, `standard` and `strict`. Personal custom modes and `unleash` cannot be put in `tack.json`. See [daily mode choices](usage.md#workflow-modes).

## What tack.json contains

The commands above create this optional file. You can review and edit it like other project data:

```json
{
  "version": 1,
  "mode": "auto",
  "config": {
    "reply-style": "brief",
    "conventional-commits": true,
    "architecture-path": "docs/architecture.md",
    "plans-path": "docs/plans",
    "handoffs-path": "docs/handoffs"
  }
}
```

Keep the file in the repository root and commit it when you want to share it. Plain `tack enable` does not create it. A profile does not activate tack or grant trust: [setup](setup.md) explains those separate choices.

Only settings marked `shared: true` in `tack config --json` may go here. Execution trust, private memory, activity logs, installation choices, disabled hooks and guard overrides remain local or user-wide. A shared `check-fast` command can be declared, but each clone still has to grant local execution trust before tack runs it.

The reader rejects unknown fields, unsupported versions, duplicate JSON keys, invalid value types and symlink profiles. The file is limited to 64 KiB. Writes preserve other accepted entries and refuse a file that changed during the update. Invalid profiles need correction; they are not silently replaced with defaults.

## Apply several selected preferences

For team setup, save every agreed value explicitly, even if it matches tack's default. Otherwise a teammate's different personal default can take its place.

Put the selected values in a temporary JSON file using the `version`, `mode` and `config` shape above, then run:

```bash
tack config --shared --apply selected-profile.json --dry-run
tack config --shared --apply selected-profile.json
```

The preview shows additions, changes and local overrides. Apply validates everything before updating `tack.json` once, preserves unselected settings and leaves an unchanged file untouched. It rejects unsupported/private settings, invalid or duplicate keys, unsafe paths and conflicting context locations. Use `--unset` separately to remove a setting. Do not export all your personal defaults as project policy.

Commit `tack.json`; remove the temporary input when finished. This does not activate tack, create scaffolding, grant execution trust or complete setup review. Existing single-setting commands remain available, and personal projects can continue using local preferences without a profile.

## Reuse your documentation layout

```bash
tack config architecture-path guide/system.md --shared
tack config plans-path work/plans --shared
tack config handoffs-path work/handoffs --shared
```

These paths are relative to the project root. Context, setup and plan discovery use the same choices. Set the architecture path before scaffolding if your project already keeps it elsewhere. Changing a path does not move existing files. Plans and handoffs are created when needed, not as empty directories during activation.

Absolute paths, parent traversal and symlink paths are rejected when these locations are used. Keep different locations for the architecture file, plan directory and handoff directory. Link other useful guides from `AGENTS.md`; tack does not automatically load every Markdown file.

## What features.txt is for

[`features.txt`](../features.txt) is tack's own registry of settings. It declares each name, Git key, default, allowed values, scope, enforcement and whether sharing is allowed. Most users never edit it: use `tack config` in your project instead.

A `hook` setting affects executable behavior in supported integrations. An `instruction` setting guides the assistant. An `installer` setting takes effect when the installer runs; a `mod` setting needs the relevant Claude Code mod. These are different guarantees. See [customization](customization.md) if you are extending tack itself.
