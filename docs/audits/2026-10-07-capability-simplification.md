# Capability simplification decisions

- Date: 2026-10-07; starting revision `8c23eba`.
- Evidence: catalog inspection, before/after description counts, existing dependency checks and offline regression tests. `tack log --skills --days 14` reported no activity recorded on the reviewed machine. No absence-of-use conclusion is supported.
- Goal: reduce routine context cost while preserving useful behavior and existing configuration.

| Component | Evidence and dependencies | Decision |
| --- | --- | --- |
| 19 skill descriptions | 4,879 characters; repeated keywords and long inventories duplicated their bodies | Shorten to 3,038 characters, a 37.7% reduction; retain purpose and activation boundaries |
| Core workflow, testing, debugging and docs | Required by enabled projects and role definitions | Keep; add one shared reference for local capability creation |
| Reviews, delegation and improvement | Named by global instructions and validated as core dependencies | Keep in core until controlled comparisons justify changing routing |
| Process and stack groups | Existing opt-in selection already supports a smaller installation | Keep the existing group mechanism and `all` default; document the smaller selections |
| 23 feature toggles | Existing users may rely on explicit settings; no representative use data | Keep compatibility; put common settings first in usage guidance; add no new creation toggle |
| Guard, Git checks and ownership/restoration | Concrete safety and configuration-preservation guarantees | Keep regardless of invocation frequency |
| Mods, visual review, memory and tracing | No local recorded usage sample; rare use can still matter | Do not remove or disable from absence of observations |
| Project-capability authoring | Existing lessons responsibility covers persistent project knowledge | Extend lessons through a focused reference; no new global skill or always-running agent |
| Capability validation | Catalog checks already exist | Share structural checks with project validation; keep behavior evaluation separate |

The initial plan considered reducing installed groups by default. Inspection found that a description-only reduction already exceeds its 20% context target without migration or losing existing discovery. The first implementation therefore keeps group selection and installation semantics intact. More aggressive catalog pruning remains an evidence-dependent decision.

Characters are not measured tokens, latency, correctness or spend. Offline tests verify structure and runner behavior. Fresh-session model experiments are prepared separately; until run, effectiveness and trigger retention under real models remain unmeasured. Usage reports now say "No observed use" and state logging limitations.
