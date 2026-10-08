# A shared way of working with AI

Use tack to agree on conventions, context entrypoints, locations for useful work artifacts and verification commands. Keep those choices versioned so teammates and supported coding tools start from the same foundation. Sharing instructions does not guarantee identical model behavior.

## Start with one project

1. Install tack on each developer's machine using the [quick start](../README.md#quick-start).
2. In the project, run `tack enable --shared` when the team wants versioned activation. Add `--scaffold` only when you want missing base guidance files created; existing files are preserved.
3. Ask the assistant to configure the project for the team. It runs `tack setup`, reads the existing guidance and proposes concrete choices. Reuse conventions and tools that already work; answer only unresolved questions and select optional additions.
4. Review and commit the agreed project files. Record accepted and deferred setup choices in AGENTS.md so later sessions do not repeat the same questions.
5. Teammates pull those files, restart their AI tools and inspect `tack context` and `tack verify --plan`. Each clone grants its own execution trust with `tack trust` after reviewing the project commands.

| Decision | Shared source of truth |
| --- | --- |
| Coding, testing, review and Git conventions | Project `AGENTS.md`, with links to detailed guides when useful |
| Context entrypoints and where artifacts belong | A short AGENTS.md index linking architecture, decisions, plans and handoffs in the agreed locations |
| Checks required for changed paths | Existing scripts/test/CI configuration and optional `checks-map.json` |
| Documentation affected by code changes | `docs-map.txt` |
| Reusable project procedures and specialist roles | `.agents/skills/` and `.agents/agents/`, indexed from AGENTS.md, or the project's established layout |
| PR evidence expected by the team | Existing repository or organization PR template |

Create files when they hold useful information, not to fill a template tree. The standard context renderer knows `AGENTS.md`, `docs/architecture.md` and `docs/handoffs/`; it does not automatically discover arbitrary directories. Link an existing layout from AGENTS.md for the assistant to read on demand. See [context behavior](usage.md#startup-context-and-formatter-trust) and [project initialization](usage.md#project-initialization).

## Know what is local

`tack mode` and `tack config` store preferences in local or user-wide Git configuration. They are **not synchronized by committing project files**. Agree on any team defaults in project instructions; teammates apply relevant CLI preferences locally. There is currently no import/export wizard for a portable team profile, and instruction-only defaults do not replace hook configuration.

Execution trust, credentials, private memory, Git identity and personal settings stay local. A shared `.tack` marker enables the workflow but never grants command execution trust. Do not commit installation ownership snapshots or private configuration.

## Share configuration across several projects

For common skills, modes, tool integrations or organization-wide guidance, maintain one team-owned fork of tack. Teammates clone the same repository and install from their checkout:

```bash
git clone https://github.com/<team>/agent-tack.git ~/Projects/agent-tack
~/Projects/agent-tack/install.sh
```

Keep that checkout: installed files link to it. Review shared changes through PRs. Put conventions for just one project in that project's AGENTS.md; use the common fork only for cross-project choices. The [customization map](customization.md) identifies where each setting lives.

After pulling a reviewed update to the common fork, rerun `./install.sh` and start a new AI session. If the team tracks upstream tack, a maintainer reviews and merges upstream changes into the common fork before teammates update. Installation preserves independent user settings, but tack-owned values come from that checkout.

## Keep setup useful

Team alignment should reduce repeated decisions and discovery. Measure whether a new teammate can find the right context, put work in the agreed place and run the required checks without reconstructing the workflow. These are product goals, not measured onboarding-time claims. Add skills, roles or extra documents only when they solve a recurring need.
