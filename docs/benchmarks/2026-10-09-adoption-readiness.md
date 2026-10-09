# Adoption readiness: real repository checks, narrow results

Date: 2026-10-09. Baseline: `b462710` (PR #138). Candidate runtime: `693445f`.
This is a before/after CLI measurement and an implementation review on tack's own
repository. It is **not** a new model benchmark or evidence of better AI coding.

## What changed and why

The adoption audit found two concrete problems. A deliberately small setup could
not pass `setup --check` without four scaffold files, and a collaborator needed
separate queries for project discovery, preferences, mode and trust.

The candidate makes missing optional templates advisory. Existing broken guidance,
review markers, unsafe destinations and a missing explicitly chosen architecture
document still fail. `setup` now reports effective preferences, their origins,
local differences from shared values, activation and trust in one read-only call.
It does not infer that a shared profile accurately represents human intent.

The repository also declares its existing content, lint and regression commands in
`checks-map.json`. Documentation-only changes select content validation. Runtime
changes conservatively select the full parallel suite. This deliberately avoids
claiming dependency-aware test selection. Mixed changes repeat the short content
validator because the full suite includes it; there is no second test runner.

## Equivalent clone inspection

We cloned the actual tack candidate repository into a disposable owner checkout,
added a small shared profile, committed it, and cloned it again. The owner was
trusted; the colleague was not. The colleague had intentional mode/reply overrides.
Both versions inspected the same repository, preferences and local Git config.

Eight repetitions alternated execution order on Linux in a local Docker container
(Python 3.12.3). All samples, inspected source hashes and commands are in
[the facts file](2026-10-09-adoption-readiness-facts.json).

| Observable | Previous commands | Candidate |
| --- | ---: | ---: |
| CLI calls for discovery, preferences, mode origin and trust | 4 | 1 |
| Median elapsed time for those calls | 192.6 ms | 81.8 ms |
| Combined stdout size | 7,443 bytes | 4,889 bytes |
| Effective preference values and origins | Same | Same |
| Trust inherited from the owner | No | No |
| Changes to project files or local config during inspection | None | None |

The absolute median saving is **110.8 ms**. Output bytes are not token counts.
The smaller summary omits the feature descriptions and sharing/enforcement
metadata still available through `tack config --json`.
This measures command orchestration, not user understanding, total installation,
model behavior, end-to-end development time or cold-start performance. Someone
who only needed the old discovery command did not need four calls; the comparison
is for the combined information now returned. There is still subprocess overhead
inside the candidate because canonical CLI decisions remain authoritative.

To reproduce with local baseline/candidate checkouts and a committed project:

```bash
python3 docs/benchmarks/support/measure-setup.py \
  /path/to/baseline /path/to/candidate /path/to/project
```

The script creates isolated HOME and Git configuration, temporary local clones,
and synthetic shared choices only inside those clones. It invokes no models and
does not install tack globally. Use the revisions above to reproduce this case.

## Correctness and code review

Five new regression cases failed before the implementation changed. The revised
setup suite has 14 cases; it checks minimal adoption, selected context paths,
fresh-clone inheritance, visible overrides, no writes/execution, invalid profiles,
scaffold preservation and unsafe destinations. Separate verifier regressions
check documentation-only selection, executable skill assets and unmapped work.

An independent agent reviewed the code rather than assigning points for test count
or workflow artifacts. It found two real implementation defects before delivery:

- The initial check map omitted executable Python helpers shipped inside skills.
  Broad Python/shell runtime patterns and a regression now include them.
- Extending the simple link scanner to arbitrary CLAUDE.md content misread titled
  links and fenced import examples. Validation is now limited to tack's exact
  `@AGENTS.md` bridge; existing tool-specific content remains the tool's concern.

The reviewer independently confirmed both corrections and reported no remaining
blocking findings in the reviewed diff. Its qualitative assessment was **B+ for
this revision, versus B− for the previous adoption implementation**: optional
templates, clearer local/shared state, existing resolver reuse and bounded changes.
The grade is subjective, from one informed review, not blind replication or a
with/without-tack code-quality result. The orchestrator agrees with the limited
assessment; the extra reporting logic and check-map upkeep are real costs.

Initial Linux validation passed all 27 suites in 228 seconds. After review fixes,
focused setup/private-note and verification suites, pinned lint and content checks
passed again. Native Windows setup ran 14 cases: 12 passed and two symlink cases
were skipped because this machine lacks the privilege. Those cases ran on Linux;
Windows CI now includes setup coverage. Test portability fixes use the resolved
Git Bash executable and portable path comparisons.

Final verification used `bin/tack verify --budget-seconds 600 --json` on the real
candidate branch: **passed**, 15 changed paths, no unmapped paths and unchanged
inputs. Content validation took 1.268 seconds, lint 8.643 seconds and the complete
27-suite regression command 227.132 seconds. The full result is in the facts file.
This is about four minutes for broad runtime validation, not a new per-edit step
or evidence that the map understands every dependency. PR CI remains the merge
gate for Linux, macOS and Windows.

## Keep, simplify and defer

| Decision | Reason |
| --- | --- |
| Keep shared preferences and local overrides/trust | They transfer useful choices without copying personal execution consent. |
| Keep engineering guidance and optional strict workflows | This change does not justify removing practices selected for real risks. |
| Simplify setup discovery and readiness | Fewer separate queries; optional documents stop being artificial prerequisites. |
| Use the existing verifier on tack itself | Existing commands gain an inspectable selection; CI still covers platforms. |
| Keep full checks for runtime changes | A broad suite is safer here than maintaining a speculative dependency graph. |
| Defer more catalogs, orchestration and repeated coding benchmarks | Existing evidence has not justified their general overhead. |

## What remains unproven

There is no new evidence that tack beats a short guide plus CI at preventing
important application defects, reducing real review/integration rework, making
future changes cheaper or saving human onboarding time. No implementation-session
token metric was collected, so none is inferred from output size or timings.
The previous negative/mixed model results remain unchanged.

The next evidence gate is actual use: record setup questions, duplicated steps,
missed project checks and maintenance effort during ordinary project changes.
Retain an extra step only when that record shows a specific benefit worth its
cost. Prefer a short guide plus CI when they already meet the need. This work
delivers narrower adoption fixes; it does not declare the broader value goals met.
