# Adoption readiness implementation

Status: in progress

## Starting point and scope

Baseline: `b462710` (PR #138). The small-core evaluation did not establish a
general quality or productivity advantage over a short project guide. This work
focuses on two observed adoption problems, using tack itself for validation.
It does not introduce a service, another configuration format or a larger catalog.

- `setup --check` requires all four scaffold files even when the user deliberately
  chooses a smaller setup. Optional templates should not become prerequisites.
- A collaborator must combine setup, configuration, mode and trust queries to
  understand a clone. Local overrides are easy to miss among unrelated settings.
- Tack has no check map of its own. Its canonical commands already exist, so
  routing those checks needs project data rather than another executor.

## Intended behavior

1. `tack setup` remains read-only. Its JSON report includes effective preferences
   with origins, shared/local differences, mode, activation and local trust. Its
   human output highlights useful settings and a concrete next step. It reuses
   the canonical configuration resolver and CLI activation/mode/trust decisions.
2. Missing optional scaffold files are suggestions, not failures. Existing broken
   guidance, review markers and an explicitly selected missing architecture file
   remain failures. A successful structural check does not mean tests passed.
3. Cloning reuses shared choices without copying trust or personal settings.
   Differences are visible but intentional overrides do not fail structural checks.
4. Repository checks reuse existing scripts. Documentation-only work avoids the
   runtime suite; runtime changes retain broad regression coverage. Unmapped
   changes and manual semantic review remain explicit.

## Ordered work

1. Add regressions to `tests/project-setup.test.py` for minimal adoption, explicit
   context paths, malformed guidance, clone inheritance, overrides and no writes
   or execution. Establish the failure before updating the implementation.
2. Update `lib/project_setup.py`, reuse `lib/project_config.py`, and adapt
   `bin/tack` for portable CLI state queries. Keep Bash 3.2 and Python 3.9 support.
3. Add `checks-map.json` for tack's existing commands and document its conservative
   selection in `AGENTS.md` and `docs/development.md`. Test selection on actual
   documentation/runtime paths and keep CI authoritative for platform coverage.
4. Simplify `docs/setup.md` and the collaborator section of `docs/sharing.md`;
   update onboarding instructions, CLI help, architecture and stale references.
5. Exercise the before/after adoption path on isolated clones, run selected checks
   on this real change, and review code independently. Record observations,
   corrections and maintenance costs in a dated report. No invented session token
   measurements or causal with/without-AI claims from one implementation.
6. Commit conventionally without AI attribution, open a PR, fix relevant failures,
   and merge only when checks for the current head pass. Confirm main CI.

## Verification and evidence gate

Use isolated HOME/XDG/Git configuration. Run project setup and config regressions,
CLI tests, content validation and pinned lint. Run the full suite for the shared
CLI change; CI covers Linux/macOS and native Windows. Use existing local Docker
images when native tooling cannot run all suites.

Publish reproducible command counts/timings for the same information, structural
defects caught and remaining gaps. Keep timing measurements separate from human
onboarding or model token savings. Compare the resulting code for complexity and
maintenance, not only test counts. Stop expanding this change if convenience
requires a parallel resolver, mandatory templates or a new orchestration layer.
Broader defect/rework/onboarding claims require later real usage evidence.
