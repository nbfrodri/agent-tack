# Documentation audit

Date: 2026-10-08. Baseline: `a07e26d`. Status: corrections implemented and locally checked; validation details are in the [delivery plan](../archive/plans/2026-10-08-shared-project-configuration.md).

## Scope and method

Inventory Markdown files; compare current human guides with CLI behavior, settings, setup, hooks and workflow instructions; check repeated procedures, navigation, historical records and local links. Before this report the tree contained 149 Markdown files, including 64 human documents under README/docs. Detailed review focused on current adoption and runtime guidance; language/framework references were not revalidated version by version.

The review also used the [product direction audit](2026-10-08-product-direction.md). Historical benchmark results remain evidence for their tested versions. Local link checks do not establish factual accuracy or external URL availability.

## Findings and changes

| ID | Priority | Finding | Correction |
| --- | --- | --- | --- |
| D1 | P1 | README was 379 lines, including a long tutorial and repeated setup. | Reduced to 114 lines. Keep purpose, quick start, flow, evidence limits and links; the full team example belongs in sharing. |
| D2 | P1 | Usage was 508 lines mixing first use, restoration, settings, models, logs, modes and checks. | Daily use is 75 lines. Separate setup, configuration, verification, installation and optional features. |
| D3 | P1 | Sharing and engineering guidance still called shared CLI preferences future work. Reusing a doc layout conflicted with hard-coded discovery paths. | Document and test `tack.json` precedence and configurable paths. Changing locations does not move files; trust stays local. |
| D4 | P1 | Formal tracing, delegation after three doc files and numeric visual gates imposed unrelated process. Trace said `covered` for ID mentions. | Use need-based delegation, optional trace links and concrete findings. CLI says `linked` with an explicit limit; update modes, skills and agent guidance together. |
| D5 | P1 | Auto-improvement had conflicting stagnation limits and treated higher scores as completion. | Use observable criteria, bounded rounds and a single no-new-evidence stop rule. Scores remain available on request. |
| D6 | P1 | Tool-switching guidance said native Windows was unsupported; trust was often formatter-only in prose. | Link to the platform guide, distinguish Git Bash from PowerShell, and explain trust for project formatters and checks. |
| D7 | P2 | Several pages repeated setup and tool tables; the index omitted newer material. | Assign one owner per topic, keep the support matrix in editors and organize navigation around reader tasks. |
| D8 | P2 | A completed Windows/benchmark plan remained active and said an issue was open. AI records linked a nonexistent handoff directory. | Archive the plan, distinguish issue closure from the unproven score target, and link existing history without creating empty documents. |
| D9 | P2 | Team-heavy framing obscured local use and the choice between a project profile and a fork. | Give all three clear paths, including a two-developer walkthrough and optional personal/team forks. |
| D10 | P2 | The convention summary presented stack/release preferences as universal requirements. | Separate project precedence and useful principles from selectable tooling defaults. |
| D11 | P2 | Moving sections could silently break local links and anchors. | Add `tests/docs-links.py` to content validation, regression cases for broken targets/headings, and update moved links. |
| D12 | P2 | External skills lacked an adoption boundary, risking duplicates and missing references. | Add optional onboarding selection and one guide covering need, conflicts, source/revision/license, dependencies and explicit updates through existing installers. |

## Owning guides

| Topic | Current source |
| --- | --- |
| Installation, activation, scaffold and setup choices | [Setup](../setup.md) |
| Tasks, modes and replies | [Daily use](../usage.md) |
| Preference precedence and context locations | [Configuration](../configuration.md) |
| Personal use, teams and forks | [Sharing](../sharing.md) |
| Checks, docs reminders and trace links | [Verification](../verification.md) |
| External skills | [External skills](../external-skills.md) |
| Tool/platform support | [Editors](../editors.md) |
| Lifecycle options and removal | [Installation](../installation.md) |
| Optional runtime features | [Advanced](../advanced.md) |
| Internal responsibilities and flows | [Architecture](../architecture.md) |

## Verification and limits

The link checker reads README and every Markdown document under docs, including dated records. It skips fenced examples and external URLs, and checks local targets and heading anchors. It is a repository-oriented parser, not a complete Markdown implementation. Content still needs review against code.

Behavioral tests cover sharing across clones, local overrides and trust, configured context/scaffold/trace paths, invalid data and hook consumers. Native Windows testing exposed a path-format mismatch in context discovery; the implementation was corrected. The delivery plan records final suite and CI outcomes.

External collection procedures were checked against upstream documentation. No collection is bundled, installed globally or automatically updated. This audit does not establish live-model onboarding quality or compatibility of every third-party skill with every tool. Smaller installation profiles and reduced end-to-end overhead remain follow-ups requiring evidence.
