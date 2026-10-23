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
| `strict` | Broad or risky changes, such as auth or migrations | Written plan challenged by the `critic` role, deeper verification and review (two independent reviews for unreviewed output), useful decision records |

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

An active handoff records work another session needs to resume. tack compares it with the branch and recent commits, but the assistant must still check `git status` and current code. A handoff is useful for interrupted work, not every small edit. A long conversation costs tokens on every turn; the check before stopping says, once per session at `clear-hint-percent` (60 by default, 1–100 or `off`), that `/clear` is safe because the handoff reloads at session start, and has the assistant write the handoff first when it is missing or stale. The percentage needs the `usage-band` mod or a status line running `tack usage statusline`; without them or a reading at most 600 seconds old, `clear-hint-tokens` (150000 by default) applies. `clear-hint-percent off` keeps the token fallback; `clear-hint-tokens off` disables that fallback (Claude Code; a hook cannot run `/clear` itself). Restart the AI session after changing saved settings; state immediate preferences in conversation.

## Useful commands

| Command | Purpose |
| --- | --- |
| `tack status` | Activation, saved mode and local trust |
| `tack setup` | Read-only project inventory and setup gaps |
| `tack setup --apply` | Create the missing base guidance files; never overwrites |
| `tack branches [--apply]` | List local branches whose work is already merged (into main, or a merged GitHub PR whose head is still the branch tip); `--apply` deletes them. The branch in use and unmerged branches stay |
| `tack usage get five_hour` | The last 5-hour (or `seven_day`, weekly) usage the usage band mod or a status line running `tack usage statusline` recorded; `usage hint` and `usage threshold` drive the once-per-window offer to delegate to Codex ([delegation](advanced.md#delegating-to-the-other-assistant)) |
| `tack usage context` | Context fill for the current directory, only when at most 600 seconds old; `usage get context` also prints stale readings, and `usage set context N` records one. The mod or status line supplies this percentage; otherwise the clear hint uses tokens |
| `tack team --base origin/main --against REF` | Inspect known branch overlap and merge conflicts without fetching; [parallel branches](teamwork.md) |
| `tack set list` | Sets of skills, agents and plugins, and where each is active; [sets guide](sets.md) |
| `tack set show NAME` | What a set contains |
| `tack set agent ROLE` | Whether a role is active and which sets provide it; read-only, exits 0 active, 1 inactive, 2 unknown |
| `tack set use NAME` | Activate a set in this project; add `--global` for every project, then run `./install.sh` |
| `tack set drop NAME` | Deactivate a set |
| `tack set suggest` | Sets that fit this project's files; `--apply` activates them, `--skip` declines them |
| `tack set skip NAME` | Stop suggesting one set in this project |
| `tack set update` | Move pinned skill collections to their upstream head and report what changed |
| `tack mode [MODE]` | Show or set the workflow mode (`auto`, `lite`, `standard`, `strict`) |
| `tack config` | Effective settings and their sources |
| `tack codex-used SESSION_ID` | Model and effort recorded for a local Codex delegation session; exit 1 when unavailable, 2 for invalid ids |
| `tack verify --plan` | Selected checks without running commands |
| `tack verify` | Execute selected checks with local trust |
| `tack doctor` | Diagnose installation and project configuration |
| `tack help` | Full CLI syntax |
| `tack completion bash\|zsh\|fish` | Print a shell completion script; see [installation](installation.md#shell-completions) for automatic and manual setup |

See [verification](verification.md) for check maps, docs reminders and optional requirement links. [Optional features](advanced.md) covers delegation, screenshots, private memory and logs. [Installation](installation.md) covers updates and removal.
