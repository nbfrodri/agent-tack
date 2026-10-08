# lite
When: questions, typos, renames, config tweaks, small fixes, small scripts or prototypes, and small well-defined tasks when tokens matter; never for consequential risk or code that handles untrusted input. File count alone does not determine risk.
Scope: any
Context: minimal

- Self-contained: these rules are complete; do not load the `dev-workflow` skill or other skills unless the task cannot be done without one.
- Git: branch off `main`/`master`/`develop`; one Conventional Commit per verified change; never commit failing tests.
- Tests: verify changed logic with useful affected tests; add a regression test for a defect when existing tests do not cover it. A trivial change already checked by existing tests needs no artificial test-file edit. Use known project commands; discover missing commands once and record them when useful.
- Reading: search before reading, read only the needed lines, never re-read what is in context.
- Review: read your own diff before committing.
- Replies: follow the selected reply-style (brief by default); a visual or detailed reply does not add workflow steps. Include the outcome, relevant verification and anything pending.
- Docs: only if the change makes them wrong.
- No plan file, handoff, AI log, review agent or delegation; suggest delegation and wait if the work would benefit from it.
- Ask only when a wrong guess would be costly; otherwise pick the conventional option and say so in one line.
- If behavior changes or consequential risk emerges, explain and move to the appropriate level. File count alone does not determine risk.
