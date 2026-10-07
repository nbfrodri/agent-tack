# lite
When: questions, typos, renames, config tweaks, small fixes, small scripts or prototypes, and small well-defined tasks when tokens matter; never for risky or multi-module work or code that handles untrusted input.
Scope: any
Context: minimal

- Self-contained: these rules are complete; do not load the `dev-workflow` skill or other skills unless the task cannot be done without one.
- Git: branch off `main`/`master`/`develop`; one Conventional Commit per verified change; never commit failing tests.
- Tests: add or update a test when logic changes; run only the affected tests, with the test command from `AGENTS.md` or the startup context. If none is known, find it once and add it to `AGENTS.md` so later sessions do not probe.
- Reading: search before reading, read only the needed lines, never re-read what is in context.
- Review: read your own diff before committing.
- Replies: follow the selected reply-style (brief by default); a visual or detailed reply does not add workflow steps. Include the outcome, relevant verification and anything pending.
- Docs: only if the change makes them wrong.
- No plan file, handoff, AI log, review agent or delegation; suggest delegation and wait if the work would benefit from it.
- Ask only when a wrong guess would be costly; otherwise pick the conventional option and say so in one line.
- If the task turns out risky or spans several modules, stop and suggest `standard` or `strict`.
