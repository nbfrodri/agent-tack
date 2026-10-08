# Example: several teams in one repository

Adapt this example after inspecting real packages and agreeing responsibilities. Reuse existing directories and files; it is not a scaffold to copy wholesale.

```text
tack.json                  shared preferences and default mode
AGENTS.md                  commands and links to area instructions
apps/api/AGENTS.md          API conventions and focused checks
apps/web/AGENTS.md          UI conventions and focused checks
packages/contracts/        canonical producer/consumer contract
.github/CODEOWNERS          review ownership, if the project uses it
checks-map.json             existing commands selected by changed paths
.private/tack/              optional ignored personal notes
```

One root `tack.json` can select `collaboration: team`, `mode: auto` and shared document locations. Do not introduce area tack.json files; tack does not resolve nested profiles. Task effort remains a per-task decision.

The root AGENTS.md should point to the API and web instructions and say when to read them. This explicit index helps tools whose nested instruction discovery differs. Child instructions add relevant conventions without silently overriding shared contracts or required checks. An assistant changing a shared interface reads both producer and consumer guidance.

Use the existing issue tracker for task ownership and dependencies. An API issue describes its observable contract; the frontend issue links the dependency and whether it is planned, available on a branch or present in the current base. A PR links the relevant issue, contract and actual verification. Do not create duplicate per-team diaries.

For example, a project already providing these scripts can declare:

```json
{
  "version": 1,
  "checks": [
    {"id": "api", "paths": ["apps/api/*", "packages/contracts/*", "package.json", "package-lock.json"], "command": "npm run test:api"},
    {"id": "web", "paths": ["apps/web/*", "packages/contracts/*", "package.json", "package-lock.json"], "command": "npm run test:web"},
    {"id": "integration", "paths": ["packages/contracts/*"], "command": "npm run test:integration"}
  ]
}
```

These commands are illustrative; only map commands that exist and test relevant behavior. A shared-contract change selects both consumers and the integration check. An isolated web change selects web checks. Review unmapped files and dependencies; a mapping is not inferred semantic coverage.

CODEOWNERS routes review requests; it does not lock files or guarantee every listed team approves. Use GitHub's own matching/approval rules and the project's repository protections. A clean `tack team` merge probe still needs contract tests. If integration fails, understand both intents, repair the contract/consumers, verify, and record the resolution in the PR or useful shared handoff.
