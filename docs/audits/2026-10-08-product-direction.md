# Audit: fit with tack's new direction

Status: the configuration, process and documentation improvements below are implemented; see the [delivery plan](../archive/plans/2026-10-08-shared-project-configuration.md).

Reviewed revision: `df979a7` (PR #131), 2026-10-08. Scope: product fit, configuration, instructions, modes, capabilities, verification and adoption. This audit proposes changes; it does not remove components or claim a new quality score.

## Product criterion

**Help an individual or team quickly configure a consistent way of developing with AI: conventions, relevant context, agreed places to save useful work, and concrete verification.** A personal project must remain a complete use case. Sharing extends that same foundation; it must not require a team service or fork. The usual mode is `auto`, selecting effort per task rather than treating every new feature as strict.

## Evidence and limits

- Inventory: 19 skills, 10 agent definitions, four fixed modes plus `auto`, and 24 feature toggles (18 project/global, six global-only). Skill bodies total 103,695 characters; global instructions total 3,843. Skill bodies are on-demand references, **not** proof that all these characters load into every request.
- The [Codex comparison](../benchmarks/2026-10-08-codex.md) found original acceptance parity with roughly 2.3x session time and materially higher token counts. It does not identify the causal cost or value of each component. The [quality review](../benchmarks/2026-10-08-codex-quality.md) also found adverse Unicode outcomes.
- Two isolated probes used temporary repositories and existing test fixtures. A real positive-value invariant passed through `tack verify`; invoking Stop on unchanged inputs ran the same command again and still reported that no test file changed. A separate empty test containing only an `R1` reference made `tack trace` print `covered` and exit 0 without executing that test.
- Earlier [catalog analysis](2026-10-07-capability-simplification.md) found no representative activity sample. Lack of telemetry is not evidence that a capability is useless. No new model calls, field-adoption study or independent review were performed for this audit.

## Findings and decisions

| ID | Priority | Evidence and product mismatch | Recommendation |
| --- | --- | --- | --- |
| F1 | P1 | `lib/config.sh` and `lib/modes.sh` resolve only local/global Git preferences. A teammate receives the instructions but not the same configured defaults. Forking tack is excessive for one project's preferences. | Add an optional versioned project configuration, shared mode/settings commands and visible origins. Preserve local overrides and keep execution trust, credentials and private settings local. Support solo use without any shared file. |
| F2 | P1 | Some consumers parse human output. `hooks/claude/stop-check.sh` recognizes only exact `false (local)` and `false (global)` strings. Adding a new source would silently change behavior unless callers are updated. | Provide a stable value/structured read interface and use it in runtime consumers. Keep human output readable. Validate shared settings centrally and declare which settings may be shared. |
| F3 | P1 | `lib/project-context.sh` and `lib/trace.sh` assume `docs/architecture.md`, `docs/handoffs/` and `docs/plans/`, while guidance says an existing layout can be reused. An AGENTS.md link helps the model but does not configure discovery. | Make the relevant context locations configurable with existing defaults, safe project-relative paths and readiness checks. Scaffolding and runtime discovery must agree. |
| F4 | P1 | `skills/dev-workflow/SKILL.md` mandates numbered requirements/tracing at standard and strict, full-suite repetition and delegation after three pending documentation files. `project-docs` repeats the file-count trigger. These are process proxies, not demonstrated task needs. | Keep acceptance criteria and meaningful tests; make formal tracing optional. Choose documentation/review/delegation by actual risk and separable work, respecting prior authorization and delegation settings. Remove the three-file rule and unconditional repeat-testing language. |
| F5 | P1 | `auto-improve` centers its loop on raising a subjective score and contains conflicting stagnation stop rules (one versus two rounds). Modes require visual scores of 7/10 as a redo gate. These can reward scoring/process without finding defects. | Center improvement on verified findings and bounded acceptance criteria. Keep scores as optional explanatory summaries. Replace numeric visual gates with concrete blocking findings and relevant accessibility/usability checks. Preserve screenshot capture where useful. |
| F6 | P2 | The isolated Stop probe reran a passing check and warned about unchanged tests. `fast-check.sh`, the unmapped Stop path and `verification.py` also have different command/timeout semantics; legacy hooks depend on an external `timeout` binary. | Consolidate execution semantics before optimizing scheduling. Treat test-file churn as advice, not coverage. Do not introduce an unsafe success cache: ignored dependencies, external state and changed commands need explicit invalidation design. |
| F7 | P2 | `skill-groups.txt` makes improvement and orchestration core; the default installs all groups. Native installers iterate over every agent definition independently of skill groups. Many roles may help occasionally but are not required to adopt shared conventions. | Keep existing installs compatible. Move towards a small explicit installation profile with optional specialist packs only after discovery/dependency checks and an adoption experiment. Do not delete rarely used security, debugging or review capabilities based on missing usage logs. |
| F8 | P2 | General conventions contain personal defaults: release automation, universal SemVer, formatter preferences and rigid function-shape rules. The opening project-precedence rule helps, but these can still be mistaken for universally required engineering. | Separate portable engineering principles from selectable defaults. Reuse existing project tools and conventions; require release machinery only for an actual distribution need. Keep this owner's Conventional Commits and attribution preferences. |
| F9 | P2 | The installation path depends on a retained checkout and optional vendor plugins/mods; the sharing guide was historically framed around personal forks. `activity-log`, private memory and Claude mods serve personal/runtime needs rather than shared project policy. | Keep personal capabilities available and explain their boundary. Make project adoption use the same upstream installation plus project data. Do not require a fork or add a second package manager merely for onboarding. Review optional install profiles separately. |
| F10 | P2 | `tack trace` checks textual references; `docs-map.txt` checks changed filenames. Neither establishes semantic test coverage or documentation accuracy. The new check map also declares routing rather than dependency completeness. | Retain these useful navigation/advisory mechanisms with precise labels and limits. Use `linked` for textual traceability; test executed behavior and review documentation meaning separately. |

## What remains useful

| Treatment | Components | Reason |
| --- | --- | --- |
| Keep as foundation | Activation, local trust, installer ownership/restoration, guard/Git protections, tool adapters, project instructions and discovery | Concrete control, portability and preservation guarantees; lower invocation frequency does not make them dispensable |
| Strengthen | Shared project preferences, configured context locations, setup/doctor, verification evidence, PR templates | Directly serves both repeatable personal work and team adoption |
| Simplify | Workflow references, formal tracing requirements, automatic documentation delegation, score-driven loops, universal stack/release preferences | Preserve useful engineering while removing triggers disconnected from the task |
| Optional specialist capability | Agent roles, orchestration, auto-improvement, visual review, language/stack skills, release workflow | Useful for demonstrated needs; installation/discovery should not imply invocation |
| Keep personal/runtime-specific | Memory, activity logging, model tier overrides, Claude mods | Valuable individual customization; not automatically synchronized with a project |
| Investigate before removal | `check-fast` versus mapped verification, broad install defaults, mode-specific AI logs | Real compatibility and scheduling tradeoffs remain; no evidence supports wholesale deletion |

The strongest removal candidates are **mandatory behaviors**, not entire subsystems: the three-document delegation trigger, numeric score gates and compulsory formal tracing for ordinary work. Do not remove security controls, tests or useful adapters to make the product look smaller.

## Proposed delivery order

1. Versioned project configuration, stable reads and configurable context locations, with clone-to-clone and precedence tests. Update the README for **individual and team** use.
2. Remove contradictory process mandates and misleading trace wording; keep optional capabilities and explicit user choices. Document how mode selection follows task risk.
3. Consolidate bounded check execution where compatibility can be retained; keep explicit gaps and avoid stale-success caching.
4. Measure adoption effort, repeated setup, runtime overhead and meaningful defects on frozen scenarios. Evaluate slimmer installation profiles with evidence before changing defaults.

Success measures: a second clone gets the same project defaults and context locations without manual repetition; a solo clone works without a project profile; local overrides and trust stay local; malformed configuration never executes code; skipped/unavailable checks remain visible. Real-model defect rates, human rework and time/token costs require a separate controlled comparison. No new 0–10 score is assigned.


## Implementation disposition

F1-F5 and F8-F10 are addressed by shared preferences/paths, stable runtime reads, simpler guidance and corrected documentation. F6 now uses a common bounded executor; independent invocations can still repeat checks, and test-file reminders remain advisory. No success cache was added. F7's smaller installation profiles remain deferred until discovery and adoption evidence justify a default change. Personal capabilities, existing tool integrations and deterministic protections remain available.

The [documentation audit](2026-10-08-documentation.md) records stale and repeated content and its owning guides. The [delivery record](../archive/plans/2026-10-08-shared-project-configuration.md) lists local verification and deferred experiments. External skill selection uses existing installers through optional onboarding; it does not add an automatic catalog download or a second package manager.
