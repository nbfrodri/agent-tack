# Documentation

tack is a personal configuration: the [README](../README.md) says what it holds and how to install it on a machine. Read [setup](setup.md) for a project, [sets](sets.md) for skills by kind of work, then [daily use](usage.md).

## Use tack

| I want to... | Read |
| --- | --- |
| Install and enable a new or existing project | [Setup](setup.md) |
| Choose task modes and reply styles | [Daily use](usage.md) |
| Commit a project's setup for other clones or collaborators, or fork tack | [Sharing](sharing.md) |
| Coordinate parallel branches and check a merge before making it | [Parallel branches](teamwork.md) |
| Save defaults and choose document locations | [Configuration](configuration.md) |
| Keep personal task notes out of Git | [Private notes](private-notes.md) |
| Select checks and understand their results | [Verification](verification.md) |
| Group skills, agents and plugins by kind of work | [Sets](sets.md) |
| Add selected third-party skills | [External skills](external-skills.md) |
| Disable tack or tidy old project records | [Leaving a project](leaving.md) |
| Use a particular tool or platform | [Editors and AI tools](editors.md) |

## Go deeper when needed

| Topic | Reference |
| --- | --- |
| Updates, diagnosis, install options and removal | [Installation](installation.md) |
| Delegation, screenshots, memory, logs and autonomous modes | [Optional features](advanced.md) |
| Change tack itself or add a capability | [Customization](customization.md) |
| Available skills, agents and mods | [Components](components.md) |
| Portable engineering principles | [Engineering practices](engineering-practices.md) |
| Project conventions and precedence | [Conventions](conventions.md) |
| Installer and hook behavior | [How it works](how-it-works.md) |
| Components, dependencies and execution flows | [Architecture](architecture.md) |
| Contributor commands and tests | [Development](development.md) |

## Decisions and history

[ADRs](adr/) explain design decisions; [0004](adr/0004-personal-configuration-with-sets.md) records why this repository is a personal configuration. [AI work records](ai/README.md) log assisted changes. Benchmarks, audits and archived plans from the period when tack was evaluated as a general product were removed from the tree and remain in the Git history.

## Keep these guides current

Each topic has one owning guide in the tables above. Summarize briefly elsewhere and link to that guide instead of copying the whole procedure. Update affected docs with behavior changes. `tests/validate.sh` checks local links and heading anchors, but factual accuracy still requires comparing prose with code and examples.
