# Backend and frontend, with separate assistants

Use this guide when people work in different folders and branches of the same repository. Tack helps them share the right context and check integration risks. It cannot see unfetched work or prevent every merge conflict.

## Choose team coordination

After the [shared setup](sharing.md), save the team's choice:

```bash
tack config collaboration team --shared
tack mode auto --shared
```

Commit `tack.json`. Team coordination adds guidance about contracts, parallel branches and conflict recovery. `auto` still chooses the effort for each task: a small fix need not become strict. The default collaboration setting is `solo`; it keeps individual work lightweight. A shared `.tack` marker alone does not select team coordination.

New collaborators can use the [optional one-command setup](installation.md#optional-setup-for-collaborators). Cloning the application does not install tools or grant execution trust automatically.

## Example: add order creation

Maya changes `backend/`; Leo works in `frontend/`. Their existing schema is `contracts/openapi.yaml` and their contract tests already cover both components. They link these paths and the real check commands from `AGENTS.md`.

1. Maya asks her assistant: **“Add order creation.”** The assistant reads the issue and existing contract, creates a focused branch and updates implementation, schema and relevant tests together.
2. The endpoint needs one decision Leo cannot infer from the schema: when to retry a pending order. Maya's assistant records it in a short integration handoff, linking the schema, branch/PR, observed commit, checks and Leo's next action. It marks availability **branch-only** until checked against the integration base. Maya need not rewrite the implementation as a separate briefing.
3. Leo asks his assistant: **“Connect the order form to the backend.”** It finds the relevant handoff, reads the contract at the intended revision and checks availability. An unmerged dependency stays explicit. It does not treat a planned endpoint as already available in main.
4. The team integrates the dependency first, or agrees on a dependent branch/mock. After integration, the assistant verifies the actual current contract, runs the real consumer checks and updates or archives the handoff.

Use the [integration template](../skills/project-docs/assets/docs/handoffs/integration.md) only when notes add useful information beyond schemas, generated types and existing docs. Keep the canonical API specification in one place. Old notes and commit ancestry cannot establish that a feature survived later changes or a revert.

## Inspect branch overlap

Once the relevant remote refs are available locally:

```bash
tack team --base origin/main --against origin/feat/frontend
tack team --base origin/main --against origin/feat/frontend --json
```

Replace those example refs with your real branches. The command works in solo projects too and never fetches, changes your branches, stages files or edits your working tree. A temporary local bare clone contains the merge probe and any Git objects it creates. Custom merge drivers and hooks are excluded.

| Result | Meaning | Next step |
| --- | --- | --- |
| Ahead / behind | Commit difference from the locally known reference | Refresh remote knowledge when appropriate; review new base changes |
| Overlap | Both branches changed these paths since their common ancestor | Review shared ownership and interface assumptions |
| `clean` | Git can combine the committed trees using its built-in drivers | Still run relevant tests and inspect compatibility |
| `conflict` | Git detected a merge conflict | Resolve the competing changes and test the result |
| `unknown` | Missing history/ref, unsupported Git or failed probe | Inspect the reason; do not assume a clean merge |

Git 2.38+ is needed for the merge probe. Dirty files are listed but excluded from it. JSON includes commit IDs, both path lists and conflicting paths where Git supplies them. Exit 0 means the diagnostic completed, even if it reports conflicts; exit 2 means inspection or arguments failed. This is a review aid, not a merge authorization or compatibility gate.

## Resolve conflicts without losing intent

The assistant reads both changes and their base, follows your merge/rebase policy and preserves both intended behaviors. If those behaviors disagree, the team resolves that decision before calling the work done. Avoid blanket “take ours” or “take theirs.” Published shared branches are not rewritten without authorization.

After resolving, run affected unit, contract and integration checks. Record the decision and results in the existing PR or useful handoff, and update the canonical contract in the same change. Check the latest candidate/base before merging. Existing branch protection or a merge queue helps serialize integration; tack does not configure either automatically.

## From audit findings to reviewed PRs

The issue workflow already connects verified findings to implementation: search for duplicates, record evidence and acceptance criteria, identify dependencies, create a focused branch, implement and open a PR using the project's template. GitHub publication follows your prior authorization. `Closes #42` is for a fully resolved issue; use `Refs #42` for partial work. Small changes need no issue unless your project requires one.

For automatic minimum review information, optionally copy:

| Tack asset | Destination in your project |
| --- | --- |
| `skills/github-issues/assets/check-pr.py` | `scripts/check-pr.py` |
| `skills/github-issues/assets/pr-policy.yml` | `.github/workflows/pr-policy.yml` |

The **PR policy / metadata** job checks Conventional Commit titles and filled **Summary** and **Validation** sections. It detects common placeholders, ignores template comments and defers drafts until ready. It runs on PR creation, edits, code updates and readiness changes with read-only permissions, no secrets and no model costs.

Adapt existing headings or title conventions; an issue reference can be required where useful. [Checker options and limits](../skills/github-issues/references/pr-checks.md). Passing metadata does not prove checks ran. Keep real CI tests, lint and contract checks alongside it. A maintainer must select the check in repository rules to make it required; the workflow alone does not enforce merging policy, and changes to the checker/workflow need review.

## Several teams in one repository

Keep one root `tack.json` for shared defaults. Link area instructions from the root `AGENTS.md`: for example API conventions in `apps/api/AGENTS.md` and UI conventions in `apps/web/AGENTS.md`. Tack does not read nested tack.json profiles. `tack setup` reports detected package areas and suggests scoped guidance when several exist; it does not assign teams or change collaboration settings automatically.

Use existing CODEOWNERS for review ownership and issues for assignments/dependencies. Keep a shared contract in versioned files. Changes to that contract should select producer, consumer and integration checks through `checks-map.json`. An area change should load the guidance it needs. [Complete multi-team example](../skills/new-project/assets/examples/multi-team.md).

## Work in separate worktrees

Use a worktree when parallel tasks need independent working directories or unrelated edits must be left alone. Inspect existing worktrees first. A serial small change needs no new checkout. Each writer receives a branch, directory and clear scope. [Procedure and cleanup](../skills/dev-workflow/references/worktrees.md).

Git shares local repository settings across linked worktrees by default, including tack's local preferences and execution trust. Use conversational task modes for concurrent work. Worktrees do not isolate databases or ports and do not prevent semantic conflicts. Preserve ignored/private notes and unmerged work before removing one. [Private notes](private-notes.md).

## Address PR feedback

Ask the assistant to read reviews and comments, verify findings against the current head, fix in-scope defects and identify genuine follow-ups. The optional `skills/github-issues/assets/read-pr-reviews.py OWNER/REPO NUMBER` script collects inline threads, review summaries and conversation comments through `gh`, including pagination. It makes no GitHub writes and fails explicitly on incomplete reads or a changed head/base.

The [review-resolution procedure](../skills/github-issues/references/review-resolution.md) keeps evidence with each finding, reuses existing issues/replies and respects publication permissions. Creating an issue does not resolve a blocking defect. Resolve a thread only when addressed under the project's review policy; reread findings and CI before merging. Metadata checks continue to cover PR information separately from code and approval.
