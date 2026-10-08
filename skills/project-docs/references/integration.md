# Producer and consumer context

Use when one part of a project changes behavior that another person or assistant must consume. Prefer the project's existing contract and collaboration notes. Do not make a second API specification or a mandatory handoff for every task.

The producing assistant updates schemas, generated types and relevant tests in the implementation PR. If a decision or dependency cannot be understood from those sources, add a short handoff using `../assets/docs/handoffs/integration.md` in the configured handoffs directory. Index the useful paths from AGENTS.md or an existing component guide. Keep secrets, copied payloads with personal data and private machine paths out of shared notes.

Include only useful facts:

- Component and consumer; links to canonical OpenAPI/GraphQL/schema/types and relevant code.
- Source branch, PR and observed commit/reference. Mark each dependency **planned**, **branch-only** or **verified in the known base**. Record when the local base was observed; do not imply a fetch happened.
- Consumer actions and decisions the schema does not explain. Include auth/error behavior or examples only where needed, preferably by linking existing tests.
- Checks actually run and their results, unresolved assumptions and next owner/action.

The consuming assistant reads the referenced contract at the intended revision before coding. Compare notes with current files and Git history; ancestry is not proof that behavior survived later changes. If an endpoint is only planned or on an unmerged branch, state the dependency and do not invent an available API. If proceeding with a mock is agreed, keep it explicitly temporary and test against the real contract before integration.

After changes merge, verify against the intended base and update availability in the existing PR/handoff. Archive a completed handoff when it no longer helps; durable decisions stay in the architecture/ADR or canonical contract. A human should not have to rewrite backend implementation notes for the frontend assistant after every change.
