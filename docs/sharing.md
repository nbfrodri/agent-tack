# Use tack alone, with a team or from a fork

All three are supported. Start with project settings; use a fork when you want to change tack's own defaults or capabilities across several projects.

## Work on your own

Install tack, run `tack enable` in a project and keep preferences local:

```bash
tack config reply-style brief
tack mode auto
```

You need no team, shared profile or fork. You can still commit useful project instructions and checks so another clone or a future session can reuse them.

## Example: a team building with AI

Maya and Leo maintain a Python service. Maya uses Codex; Leo uses Claude Code. The repository already has tests, CI and a PR template. They want both assistants to use the same conventions and check commands.

### 1. Agree on the project setup

Each developer [installs tack](setup.md). Maya works on a branch in the service repository and runs:

```bash
tack enable --shared
tack mode auto --shared
tack config reply-style brief --shared
tack config collaboration team --shared
tack config architecture-path docs/system.md --shared
tack setup
```

She asks the assistant to reuse the existing files, inspect the service and propose only missing guidance. They agree on:

| Decision | Saved in |
| --- | --- |
| Python conventions, commands and review expectations | `AGENTS.md`, linking existing guides |
| Shared mode, reply style and context locations | `tack.json` |
| What docs need review after an API change | `docs-map.txt` |
| Which checks to run for API changes | `checks-map.json` |
| What evidence a PR should include | The existing PR template |

For example, their `AGENTS.md` includes:

```markdown
# Project instructions

- Use the Python version and dependencies in pyproject.toml.
- Test with uv run pytest; lint with uv run ruff check .
- Keep API compatibility unless the issue explicitly changes it.
- Architecture: [system guide](docs/system.md).
- Put multi-session plans in docs/plans and handoffs in docs/handoffs.
- Follow the existing PR template and wait for green CI before merging.

## Setup choices

Reuse the current test suite, CI and PR template. No new agent roles are needed.
```

Their existing `tests/api` suite checks API behavior. They add:

```json
{
  "version": 1,
  "checks": [
    {
      "id": "api",
      "paths": ["src/api/*", "tests/api/*"],
      "command": "uv run pytest tests/api",
      "timeout_seconds": 60
    }
  ]
}
```

This is one example rule, not complete coverage for the service. They review unmapped paths with `tack verify --plan` and add relevant existing checks as needed.

### 2. Review and share

If some collaborators do not have tack, Maya can offer [optional pinned setup files](installation.md#optional-setup-for-collaborators) with `tack bootstrap`. Collaborators choose whether to install; existing personal installations are preserved.

Maya reviews the generated changes and commits `.tack`, `tack.json` and the agreed guidance/maps through a PR. She keeps credentials, private memory and local trust out of Git.

Leo pulls the change and runs:

```bash
tack mode                       # auto (shared)
tack config reply-style         # brief (shared)
tack context
tack verify --plan
tack trust                      # after reviewing the commands in his clone
```

He starts a new AI session. Shared defaults work without importing Maya's Git config. If Leo has an old local override, `tack config` shows it; `tack config reply-style --unset` removes it.

### 3. Work on real tasks

For a small bug, Leo says: "Fix the empty search result error and add a regression test." `auto` scales the work to the task. The assistant uses existing conventions and checks.

For a risky data migration, Maya says: "Use strict for this task. Plan the migration and recovery before implementing it." The task gets more review without changing the team's usual default.

Both assistants use the same project evidence. Their models can still behave differently; shared configuration is not a guarantee of identical output. Review the diff, meaningful tests and actual CI results.

For backend and frontend developers working on separate branches in one repository, continue with [team coordination](teamwork.md): canonical contracts, useful handoffs, branch diagnostics, conflict recovery and optional PR checks.

## Use a fork for deeper customization

A fork is appropriate for a personal setup or a team that wants different cross-project rules, skills, agents, modes or integrations. It is optional for ordinary project configuration.

1. Fork the tack repository into your own GitHub account or organization.
2. Make and review changes using the [customization map](customization.md).
3. Teammates clone and install that fork:

```bash
git clone https://github.com/YOUR-TEAM/agent-tack.git ~/Projects/agent-tack
~/Projects/agent-tack/install.sh
```

Keep the checkout. Commit customizations there so reinstalls use them. A maintainer can add upstream tack as a remote, review incoming changes and integrate selected updates through PRs. Teammates pull reviewed updates, rerun `./install.sh` and start new AI sessions. See [update behavior](installation.md#updating).

A fork controls common defaults; each application's `AGENTS.md` and `tack.json` still describe that application. Selected [external skills](external-skills.md) can also be committed per project. No central account or service is required.
