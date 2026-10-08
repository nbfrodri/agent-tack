# Verify a changed contract

Use for public interfaces, configuration, persistence or producer/consumer changes. A green existing suite may omit the new requirement. Keep the review in the task or PR; no separate checklist document is required.

Read the canonical contract and affected callers. For each changed rule, identify the production path and a meaningful example that would fail without the change. Inspect invalid and boundary inputs as well as the happy path. Validate each supplied input before normalization or precedence can hide an invalid value; preserve documented error types and avoid mutating caller state.

Check compatibility at the consumer boundary, including serialization when it crosses a transport. Read the dependency at the actual branch/revision; distinguish planned, branch-only and merged behavior. Select both sides' contract/integration commands when a shared interface changes. When requirements change, update stale assertions instead of hiding fields or weakening behavior to make old tests pass. A clean Git merge is not an integration test.

Use red/green for the behavioral change and inspect the assertion that failed. A syntax/import failure or unrelated failing command is not evidence that the regression test detected the defect. After implementation, compare the actual code and tests with the changed rules; add missing consequential coverage rather than relying on test count or a numeric review score.

For a new clone or completed integration with no diff to select from, `tack verify --all --plan` previews all declared project checks; after local trust, `tack verify --all` runs them within the normal budget. This is optional full verification, not a per-edit default. Missing checks, skipped consumers and unavailable dependencies remain explicit limitations.

When handing work to another participant, update the canonical contract and existing change notes with the interface, availability and actual verification. Add a short handoff only for information those sources do not carry. A teammate should not need a second private explanation to make the next change.
