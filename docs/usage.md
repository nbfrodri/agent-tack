# Daily use

After [setup](setup.md), work in your usual AI coding tool. tack supplies the project's conventions and context; you describe the task as normal.

## A typical task

1. Ask for the change and describe its expected behavior.
2. The assistant reads relevant project guidance and chooses the amount of planning and review the task needs.
3. It makes a focused change and runs the appropriate project checks.
4. It reports what changed, what was verified and anything still unresolved. PRs use the repository's template.

For example:

> Fix the checkout error when the cart is empty. Add a regression test and keep the change small.

For a bigger change:

> Add account deletion. Use strict for this task, cover recovery and data retention, and prepare a plan before implementation.

## Workflow modes

`auto` is the default. It lets the assistant choose a level for each task:

| Level | Typical use | Expected effort |
| --- | --- | --- |
| `lite` | Small, clear changes | Focused edit, relevant checks, brief summary |
| `standard` | A feature or bug fix within one area | Short plan, behavior tests, affected docs and review where useful |
| `strict` | Broad or risky changes, such as auth or migrations | Written plan, deeper verification and review, useful decision records |

A new feature is not automatically strict. A one-line security fix can be. Explicit strict preferences remain supported. Plan approval already given by the user does not need to be requested again.

```bash
tack mode              # effective saved mode and its source
tack mode auto         # keep task-based selection in this clone
tack mode strict       # persistent local override
tack mode --unset      # inherit shared or personal defaults
```

A conversational choice applies to the requested task. It does not edit saved configuration unless you ask. See [configuration](configuration.md) for shared defaults and [optional modes](advanced.md#your-own-modes) for personal variants. `unleash` is an explicit advanced choice, never a shared default.

## Reply styles

| Style | What you receive |
| --- | --- |
| `brief` (default) | Outcome, relevant verification and pending work |
| `visual` | Lists and tables when they make information easier to scan |
| `detailed` | More explanation, tradeoffs and examples |

```bash
tack config reply-style visual
tack config reply-style brief --shared
tack config reply-style detailed --global
```

You can also say "keep this answer brief" or "explain this in detail." Reply style does not change the tests, review or permissions required by the task. `normal` and `terse` remain legacy aliases for `brief`.

## Context and continuity

`tack context` shows project instructions and relevant context. `auto` and `standard` index architecture and active handoffs; `strict` includes bounded excerpts; `lite` keeps handoff pointers. With parallel work, it lists up to five active handoffs and focuses an excerpt only when one matches the current branch or there is just one active handoff. Otherwise the assistant chooses context for the actual task. The locations come from [configuration](configuration.md#reuse-your-documentation-layout).

An active handoff records work another session needs to resume. tack compares it with the branch and recent commits, but the assistant must still check `git status` and current code. A handoff is useful for interrupted work, not every small edit. Restart the AI session after changing saved settings; state immediate preferences in conversation.

## Useful commands

| Command | Purpose |
| --- | --- |
| `tack status` | Activation, saved mode and local trust |
| `tack setup` | Read-only project inventory and setup gaps |
| `tack bootstrap --dry-run` | Preview optional pinned collaborator setup files |
| `tack team --base origin/main --against REF` | Inspect known branch overlap and merge conflicts without fetching; [team guide](teamwork.md) |
| `tack config` | Effective settings and their sources |
| `tack verify --plan` | Selected checks without running commands |
| `tack verify` | Execute selected checks with local trust |
| `tack doctor` | Diagnose installation and project configuration |
| `tack help` | Full CLI syntax |

See [verification](verification.md) for check maps, docs reminders and optional requirement links. [Optional features](advanced.md) covers delegation, screenshots, private memory and logs. [Installation](installation.md) covers updates and removal.
