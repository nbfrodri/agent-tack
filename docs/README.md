# Documentation

New to tack? Read [setup](setup.md), then [daily use](usage.md). You do not need the advanced pages to get started.

## Use tack

| I want to... | Read |
| --- | --- |
| Understand the purpose and limits | [Why tack](why.md) |
| Install and enable a new or existing project | [Setup](setup.md) |
| Choose task modes and reply styles | [Daily use](usage.md) |
| Work alone, share a project or maintain a fork | [Sharing](sharing.md) |
| Save defaults and choose document locations | [Configuration](configuration.md) |
| Select checks and understand their results | [Verification](verification.md) |
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
| Measured outcomes and limitations | [Results](results.md) |

## Decisions and history

[The quality and efficiency comparison](benchmarks/2026-10-08-quality-efficiency.md) reports the completed experiment, independent code review and unmet speed targets. Its [archived implementation plan](archive/plans/2026-10-08-quality-and-efficiency-implementation.md) records the intended work and completion decisions.

[ADRs](adr/) explain design decisions. [Audits](audits/) record findings against a dated revision; they are not the current usage manual. [Archived plans and handoffs](archive/) preserve completed work. Historical benchmarks describe the version tested, including old names and behavior.

The [direction audit](audits/2026-10-08-product-direction.md) and [documentation audit](audits/2026-10-08-documentation.md) record this transition. [AI work records](ai/README.md) and the [onboarding evaluation protocol](../evals/project-onboarding.md) are supporting material.

## Keep these guides current

Each topic has one owning guide in the tables above. Summarize briefly elsewhere and link to that guide instead of copying the whole procedure. Update affected docs with behavior changes. `tests/validate.sh` checks local links and heading anchors, but factual accuracy still requires comparing prose with code and examples.
