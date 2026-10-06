# lean
When: small, well-defined tasks when saving tokens matters more than process; never for risky or multi-module work or code that handles untrusted input.
Scope: any
Context: minimal

- Self-contained: these rules are complete; do not load the `dev-workflow` skill or other skills unless the task cannot be done without one.
- Git: branch off `main`/`master`/`develop`; one Conventional Commit per verified change; never commit failing tests.
- Tests: add or update a test when logic changes; run only the affected tests, with the test command from `AGENTS.md`. If it is missing, find it once and add it to `AGENTS.md` so later sessions do not probe.
- Reading: search before reading, read only the needed lines, never re-read what is in context.
- Replies: terse; what changed, the commit and anything pending, in a few lines.
- Docs: only if the change makes them wrong.
- No plan file, handoff, AI log, review agent or delegation.
- Ask only when a wrong guess would be costly; otherwise pick the conventional option and say so in one line.
- If the task turns out risky or spans several modules, stop and suggest `standard` or `strict`.
