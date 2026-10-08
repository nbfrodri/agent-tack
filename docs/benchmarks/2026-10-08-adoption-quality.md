# Adoption comparison: code and workflow review

Reviewed all eight journeys' setup and final code/test diffs against the same predeclared criteria: readability, appropriate modularity, robustness, useful regression tests and scope discipline. Findings below supplement [automatic results](2026-10-08-adoption.md); this review is unblinded, by the same assistant and not independent. No aggregate subjective score is used as an outcome.

## Shared findings

Every implementation kept validation and routing in their existing modules, used `Number.isSafeInteger` with the correct positive/nonnegative boundaries, preserved IDs and caller inputs, and rejected unknown types at the routing boundary. No added dependency, broad refactor or speculative class hierarchy was needed. Tests exercised behavior rather than mocks of the implementation. All delivered snapshots were committed and clean; histories used Conventional Commits without AI coauthor trailers.

All 16 code tasks showed an expected red test before the first production edit and a subsequent green suite or passed verifier checks. The three sessions whose green evidence came through `tack verify` were inspected directly, rather than requiring a literal TAP summary. This is evidence of the observed red/green sequence; a commit's claim alone was not treated as proof.

## Per-journey observations

`m0` is Luna, `m1` is Sol. Each row covers both the bug and feature delivery.

| Journey | Code and regression-test evidence | Workflow finding or limit |
| --- | --- | --- |
| m0-baseline-1 | Small validation/topic-map changes; table-driven quantity/amount boundaries and payload-copy assertions. | Native guidance was enough for this task. No additional routing-level invalid-amount test; validator and mutation checks still cover the tested failure. |
| m0-baseline-2 | Focused zero/unsafe quantity regressions; invoice validation, routing, whitespace ID and unknown-type checks. | Added direct unknown-type rejection to validation as well as routing; no abstraction growth. Valid uppercase PR template. |
| m0-tack-1 | Equally small production changes; zero/unsafe quantity and invoice amount boundaries; valid invoice routing and payload-copy tests. | Shared Conventional Commit setting omitted in favor of its current default. Feature expanded the map to the catalog; routing tests do not inspect catalog prose. |
| m0-tack-2 | Added maximum-safe positive quantity coverage; invoice amount boundary table and payload/ID preservation checks. | Same missing explicit shared Conventional Commit value. A green map reports declared command coverage, not documentation accuracy. |
| m1-baseline-1 | Broad table-driven boundaries, missing values and IDs; routing rejection and input-preservation tests. | Focused delivery with catalog update. Clear contracts and native instructions already supported the practices. |
| m1-baseline-2 | Broad boundaries and unknown/prototype-named routes; original-ID and frozen-payload assertions. | Catalog repeats some contract wording, adding another place to maintain; no observed functional defect. |
| m1-tack-1 | Broad unit/routing boundaries and unknown-type rejection; 65 passing public tests after the feature. | Shared settings explicit. A plan and work log add evidence and overhead; verifier correctly reports their unmapped paths. |
| m1-tack-2 | Broad unit/routing boundaries, negative zero, metadata preservation and event-specific field checks; 68 public tests. | Shared settings explicit. Plan uses the agreed path; verifier keeps that manual-review gap visible. |

No correctness advantage or clear general maintainability advantage was observed for tack on this fixture. Sol produced broader explicit boundary tests in both conditions. Test quantity, extra plans and extra commands were not scored as quality by themselves. All tests caught the deliberately reintroduced validation/routing faults, but only those fault families were probed.

## Setup and verification gaps

All journeys preserved the initial implementation during setup, reused the architecture location, added a valid PR template and respected declined capabilities. Tack's mode, context paths and reply style survived cloning with local trust separated. Luna's two unpinned Conventional Commit preferences remain an adoption gap: a current default is not an explicitly shared policy.

Some maps select both focused tests and the full suite for the same production change. Command-string deduplication cannot infer that one command contains another's tests. Mapping a guide to a related code suite may be useful routing, but it does not validate the guide's content. The assistant should describe what was actually checked and review prose directly.

These findings favor improving setup precision and reducing unnecessary work while retaining engineering guidance. They do not support removing TDD, SOLID, branches, PR templates or meaningful tests.
