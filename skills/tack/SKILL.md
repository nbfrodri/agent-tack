---
name: tack
description: "Operate tack itself: sets, modes, trust, checks, doctor and settings. Use when the user asks how to use, configure, diagnose or update tack, or when a tack hook or doctor message needs explaining."
---

# Operating tack

Read the environment before answering from memory: `tack status` (activation, mode, trust), `tack help` (full syntax), `tack doctor` (diagnosis of the installation and the project), `tack setup` (read-only inventory of a project).

## Who decides

Reading is yours: `status`, `mode`, `set list|show|suggest|agent`, `verify --plan`, `config`, `setup`, `doctor`, `context`.

Changing is the user's: `enable`, `trust`, `mode NAME`, `set use|drop`, `setup --apply`. Leave `--global` and `tack set update` to the user as well: the first affects every project, the second moves the pinned third-party skills. A rejected hook or guard stays rejected; ask for the allowed alternative.

## Traps

- `tack verify` without `tack trust` runs nothing and says so (exit 2) whenever it has checks to run. `--plan` never runs commands.
- `Not completed (out of time, nothing failed)` means a check hit its time limit, not that it failed (exit 3; a failure exits 1). `tack verify` and each check stop at 600 s at most and the Stop hook has about 80 s, so a long suite needs `tests/run-all.sh` run by hand or CI.
- After a project's set gains a skill or an agent role in the checkout, `tack set sync` links it into the project. What is active everywhere, `core` included, arrives through `./install.sh`, not through sync. `tack set agent ROLE` says whether a role is active and which set provides it.
- Every active skill adds its description to each session: activate a set where the work happens.
- `./install.sh` is idempotent; Claude Code and Codex need a restart afterwards. Cursor has no global instructions file: paste `global/AGENTS.md` into its user rules once. `doctor` keeps warning that those user rules need manual verification, because it cannot read them.
- `tack doctor` warnings are not all errors: read each line before acting.

## Where it is documented

| Question | Read |
| --- | --- |
| Install, update, remove | `docs/installation.md` |
| Enable and set up a project | `docs/setup.md` |
| Modes and daily use | `docs/usage.md` |
| Sets of skills, agents and plugins | `docs/sets.md` |
| Checks, budgets and results | `docs/verification.md` |
| Settings and where they live | `docs/configuration.md` |
| Another AI tool or platform | `docs/editors.md` |
| Turn tack off in a project | `docs/leaving.md` |
| Change tack itself | `AGENTS.md`, `docs/customization.md` |
