# Optional features

Start with [setup](setup.md) and [daily use](usage.md). These features are available when needed; you do not need to configure every item.

## Claude Code mods

The installer adds two mods to Claude Code (other tools do not support mods):

| Mod | What it shows | Command |
| --- | --- | --- |
| `usage-band` | A band above the prompt: the active tack mode (`tack · <mode>`, `tack · off` when the project is not enabled, or `tack · ?` when tack could not answer: `/usage-band` says why), 5-hour and weekly usage with reset times, context fill and session cost; toasts at 80% and 90%. Limits appear after the first response and only on a subscription | `/usage-band` hides or shows it |
| `agent-activity` | A live pane of tool calls, skills, subagents (with their model) and permission prompts or denials; subagent actions are marked `↳` | `/activity` opens it, or closes it when it is open (it opens by itself on terminals at least 144 columns wide) |

Opt out with `./install.sh --skip-mods` or `tack config mods false --global`, then rerun the installer; `./uninstall.sh` removes them. To change a mod, edit it under `plugins/`, bump `version` in its `plugin.json` and rerun `./install.sh` (Claude Code caches installed plugins). It cannot infer ownership of legacy configuration: paths already identical before recording began are preserved. Installation and uninstall previews make no persistent changes. Installation accepts paths with spaces; use absolute paths without tabs, newlines or dot components, and keep the checkout path free of quotes and backslashes for Claude hook command substitution.

## Candidate lessons

When you correct the assistant, `lessons` saves a lasting rule in the right file. A correction it does not save yet is counted instead, so a repeat is noticed ([ADR 0001](adr/0001-candidate-lessons.md)):

```bash
tack lesson list                          # this project's and your user-wide candidates
tack lesson note use-pnpm "Use pnpm, not npm."   # what the assistant runs; a repeat adds to the count
tack lesson contradict use-pnpm           # evidence against a candidate
tack lesson forget use-pnpm               # after it was saved as a rule, or declined
```

After three sightings with little against it, a candidate is marked `ready` and the assistant asks you whether to save it as a rule. Session start shows up to three of the strongest as unconfirmed hints, last in priority under `context-max-chars`. Candidates live only on this machine, in `~/.local/state/agent-tack/lessons.tsv` (readable only by you); the rules you approve are what travel, through the project or a reviewed tack fork.

## Shared memory

Notes about you that are not rules and not about one project (your machine, your accounts, a preference you have not made a rule) live in one Markdown file that Claude Code and Codex both read at session start, in every project ([ADR 0002](adr/0002-shared-memory.md)):

```bash
tack memory                                # print the notes
tack memory add "Runs Arch Linux; use pacman, not apt."   # a dated note at the top
tack memory path                           # ~/.config/agent-tack/memory.md: edit it to change or remove notes
```

Only lines starting with `- ` are loaded; other text you write in the file is kept but not loaded. The assistant shows you a note and waits for your OK before adding it. Each tool keeps its own memory too; this file is the part they share. Notes that look like credentials are refused, and the file is readable only by you. Session start adds the newest notes up to `memory-max-chars` (2000 by default) and says where the rest is; `tack config memory false --global` turns it off. Rules that should apply everywhere still belong in `global/AGENTS.md`, through `lessons`.

## Visual review of UI changes

At standard and strict, visible UI changes get before and after screenshots when capture is available. Review concrete usability and visual findings; a score or separate reviewer is not required. The assistant captures affected pages at useful sizes, such as mobile (390×844) and desktop (1440×900):

```bash
tack shots --before http://localhost:3000/          # before changing anything
tack shots --after http://localhost:3000/ --name home
tack shots --dir                                    # this branch's folder for today
tack shots --index                                  # rebuild index.html after score.md is written
```

Everything goes to `.tack-screenshots/<date>-<branch>/` in the repository, with `before/`, `after/` and an `index.html` that shows them side by side; open that file in a browser. The folder ignores itself in git, so nothing is committed; the assistant may attach the after shots to the pull request. (`.tack` is the shared marker file, so the screenshots cannot live under it.)

Review screenshots for concrete regressions and fix blocking findings. Use `ui-reviewer` only when delegation is appropriate; the current assistant can perform the review. Numeric scores are optional. The screenshot index can display notes from `score.md`. `standard`, `strict` and `unleash` do it; `lite` and `lean` skip it, and `tack config visual-review false` turns it off. Capture local or preview URLs with test data: the assistant asks before attaching shots that show personal data to a pull request.

A branch keeps the folder of its first capture, so before and after pair up even on different days; take the before shots after creating the branch. A page is named by its path and query, not its host, so before on one port and after on another still pair; two URLs that would share a name are refused (use `--name`). The mobile shot is a 390×844 viewport, not a full device emulation. Add `.tack-screenshots/` to `.dockerignore` or a package's `files` list if those do not already exclude dot folders.

Capturing needs Playwright in the project (`npm i -D playwright && npx playwright install chromium`); `TACK_PLAYWRIGHT` names another command, split on spaces. Without it, `tack shots` says how to install it and exits 1; a capture that fails shows Playwright's last error line and exits 1.

## Automatic delegation and integration choices

In enabled projects, complex strict-level work with independent parts is delegated automatically after the plan is approved; at lite and standard the assistant suggests delegation and waits for your OK, because each subagent starts cold and costs extra tokens. Small or tightly coupled tasks stay with the main assistant. Tack recommends available models and effort according to complexity; the actual selection depends on the tool's supported controls. Tools without subagents perform the plan sequentially.

```bash
tack config delegation off     # disable automatic delegation in this project
tack config delegation --unset # restore the default automatic policy
tack config delegation         # shows auto (default) when unset
```

Delegation picks a tier, never a vendor's model: `economical` for mechanical work, `balanced` for standard implementation, `strongest` for design-heavy or risky work. `tack models` shows each tool's mapping from `model-tiers.txt`. Codex defaults are `gpt-6-luna`, `gpt-6.1-sol` and `gpt-6-astra` respectively ([model guidance](https://learn.chatgpt.com/docs/models), checked 2026-10-07). Other tool mappings may inherit the active model. Override for your account in `~/.config/agent-tack/model-tiers.txt` (same columns; your lines win):

```bash
tack models              # every tool and tier
tack models economical   # one tier
```

Documentation follows the same delegation policy as other work. Delegate only useful independent tasks; a number of changed files does not trigger an agent.

Explicitly asking for subagents authorises them for that task even when automatic mode is off. Disabling the workflow with `tack disable` also removes automatic delegation from the enabled-project policy. Delegation is driven by instructions, not enforced by a process scheduler, and can consume more tokens. Values set directly in git config that are neither `auto` nor `off` are treated as off and reported.

The assistant commits coherent verified milestones as it works. Before integrating a PR, it inspects the history, recommends preserving useful milestones with a merge commit or combining temporary intermediate commits with squash, and offers the available methods in the existing integration confirmation. Commits are preserved unless you explicitly choose squash; a choice already given for that integration is respected without asking again.

## Overrides
| Situation | Command |
| --- | --- |
| A repo with other commit conventions | `tack config conventional-commits false` |
| A deliberate force-push to `main` | `TACK_ALLOW_FORCE_PUSH=1 git push --force …` |
| A deliberate tag change | `TACK_ALLOW_TAG=1 git push …` |
| A false positive in the secrets check | `TACK_ALLOW_SECRETS=1 git commit …` |

Secret scanning runs after the local pre-commit hook and keeps the added-line policy. Renamed files are treated as new content, so moving a file containing an old credential can also be refused. Git inspection errors block the commit rather than silently accepting it.

## Turning off individual hooks

Skip advisory hooks by ID, for one project or everywhere. The command guard and the tool-call limit of project-only modes always run, whatever the list says, and the git hooks are separate (see [overrides](#overrides)):

```bash
tack config disabled-hooks "fast-check,stop-check"   # this project
tack config disabled-hooks format-file --global      # everywhere
tack config disabled-hooks --unset                   # all hooks again
```

| ID | Hook |
| --- | --- |
| `session-context` | Startup context, mode rules and state pruning (without it the assistant does not know tack is on) |
| `fast-check` | The fast check after edits |
| `stop-check` | The check before stopping |
| `format-file` | Automatic formatting of edited files |

## CI: wait for it, merge only when green

In `standard`, `strict` and `unleash`, after a push or a new pull request the assistant waits for CI in the background, reports the result and fixes failures from the failed job's log before continuing (`ci-watch`, default `true`; `lite` and `lean` skip it). Independently, in enabled projects the command guard refuses `gh pr merge` while the pull request's checks fail or are still running, so the assistant waits and retries. `--auto` may go ahead with pending checks, because GitHub then waits for them, and `--disable-auto` is never checked. When the checks cannot be read (no `gh`, no checks reported, a slow `gh`, or a merge after `cd` or with `GH_REPO`), it asks you; in Codex that becomes a refusal. A project without CI therefore asks on every merge: turn the rule off there (`merge-requires-green`, default `true`):

```bash
tack config ci-watch false               # do not wait for CI after a push in this project
tack config merge-requires-green false   # let gh pr merge through without checking CI
```

## Activity log

An opt-in log of what the hooks did, for Claude Code and Codex: session starts with their mode, every guard decision (deny or ask) with the command, and the findings of the check before stopping. At each stop it also reads the turn from the tool's transcript and records the tokens used per model, the skills loaded, the subagents started and the workflow level the assistant stated (`level missing` when an `auto` turn edited files without stating one), so you can audit how tasks were classified. Lines are tab-separated (UTC time, tool, project, event, detail) in `~/.local/state/agent-tack/activity.log`, kept to the newest 20,000 lines or so. The file is readable only by you, because logged commands may contain tokens; it never leaves your machine.

```bash
tack config activity-log true --global   # record in every project (or drop --global for one)
tack log                                 # the last 20 entries
tack log 100                             # the last 100
tack log --cost                          # tokens (and USD with your prices) per day, project, tool and model
tack log --skills --days 90              # how often each skill and agent was used, and which never were
tack log --levels                        # the level stated per task, per project, and turns without one
tack log --cost --csv > usage.csv        # any report as CSV
```

Transcripts carry tokens, not prices, and tack ships no price list because prices change and differ by provider. To see amounts in USD, list your prices per million tokens in `~/.config/agent-tack/pricing.txt`; models without a line show `-`:

```text
# model | input | output | cache read | cache write
claude-sonnet-5-5 | 3 | 15 | 0.3 | 3.75
```

How the numbers are counted, and their limits:

- Counting starts when a session starts (or resumes) with the log on, so earlier history is never logged as new work; input tokens exclude cached ones for every tool, and repeated counts are skipped.
- Claude Code subagents add their tokens from their own transcripts; Codex subagents (`spawn_agent`) keep separate rollouts that tack does not read yet, so Codex totals leave them out.
- A task is a person's prompt; hook feedback, notifications and agent messages are not. A short follow-up ("yes, go on") counts as a new task, so `level missing` is an upper bound.
- Days are UTC (`day_utc`); projects are shown by path. When a report's period reaches past the oldest kept entry, it says where the log starts.
- Tools that do not pass a transcript to their Stop hook, or whose format tack does not recognise, record `turn unknown` instead of guessing.

## Unleash: autonomous work

`tack mode unleash` lets the assistant work without asking: it follows its plan without waiting for approval, decides instead of asking (recording every assumption in the handoff and final summary), may push its branch and open a pull request, and the command guard stops asking about explicit local data loss in the current project (`git reset --hard`, `clean -f`, `restore`, discarding checkouts, `branch -D`, `stash drop`, `rm -rf .`). That waiver never applies to a command that changes directory (`cd`, `pushd`, `popd`) or points git elsewhere (`-C`, `--git-dir`, `--work-tree`), nor to deleting `main` or `master`. The assistant also cannot change tack's settings in this mode: `tack config` writes, `tack mode`, `trust`, `enable`, `disable` and `git config tack.*` (or former `harness.*`) writes are refused, so it cannot lift its own limits or leave the mode.

What stays, whatever the mode:

- every `deny` rule: hook bypasses, `core.hooksPath` overrides, force-push to `main`, tag changes, catastrophic deletes;
- asks about deleting outside the project (paths with `..` are resolved) or the `.git` folder, rewriting remote history, database and infrastructure commands, code piped into a shell, your own guard rules, and opaque or unanalysable commands (heredocs to interpreters, loops, dynamic commands), because hiding a command inside them would otherwise skip the deny rules;
- never merging to `main`, tagging, releasing or rewriting published history.

It cannot be shared in `tack.json`. It is project-only and branch-only: `tack mode unleash --global` is refused, a global value set by hand is ignored, and selecting it on `main` or `master` is refused (`tack doctor` warns if you switch back to them later). Session start shows a warning and `tack doctor` reports it. Claude Code's own permission prompts are separate: for unattended runs also choose a permissive permission mode in Claude Code.

Optional limits, none by default; set either, both or neither, per project or with `--global`:

```bash
tack config unleash-max-tool-calls 300   # a hook refuses tool calls past 300 in one session
tack config unleash-max-cost 5           # the usage mod refuses tool calls once the session passes 5 USD
```

When a limit is reached, tool calls are refused with an instruction to update the handoff and summarise. The tool-call limit is enforced by a Claude Code hook and counts every tool call per session (counters live in `${XDG_STATE_HOME:-~/.local/state}/agent-tack/budget/`, are deleted at session start once older than `tack config state-retention-days --global` (default 30; user-wide, because the state is) and are counted by `tack doctor`; parallel tool calls can make the count slightly low, so treat it as a safety net rather than an exact quota); the cost limit needs the `usage-band` mod and a session that reports its cost.

Risks you accept: wrong decisions nobody stops in time, lost uncommitted work, unbounded token use unless you set a limit, and above all prompt injection: text in the repository, an issue or a web page can steer an agent that no longer asks. Prefer a container or an isolated machine without important credentials, and review the assumptions and the pull request before merging.

## Your own modes

Each mode is a short file of rules: the built-in ones in `modes/`, yours in `~/.config/agent-tack/modes/` (outside the repository, so updates never overwrite them).

```bash
tack mode list                   # built-in and user modes, with when to use each
tack mode new spike --from lite  # copy lite into ~/.config/agent-tack/modes/spike.md
$EDITOR ~/.config/agent-tack/modes/spike.md
tack mode spike                  # use it in this project (or --global)
tack mode show                   # the rules the assistant receives at session start
```

A mode file has a `# name` title, a `When:` line (used by `auto` to choose and by `mode list`), a `Scope:` line and `- ` rule lines. Built-in names cannot be reused. In `auto`, the assistant chooses among all modes, yours included. If a selected user mode is deleted, the mode falls back to `auto` and `status` reports it.

## Moving between tools and machines

Every supported tool reads the same installed instructions and skills, so you can switch tools mid-task. Before switching, ask for a handoff (or let the mode keep one when the work spans sessions); the next tool reads it at session start.

- **Claude Code to Codex:** the installer already configures Codex. Codex's own `/import` can bring recent chats and projects from Claude Code; when it offers configuration, skills, agents or hooks, skip them, because copies would duplicate tack's symlinked versions and would not update with `git pull` or be recognised by `doctor` and `uninstall.sh`.
- **Windows:** use WSL2. Clone inside the Linux file system (for example `~/Projects`, not `/mnt/c`), install the AI tools inside WSL and run `./install.sh` there. Native Git Bash is also supported with the limits in [Windows setup](editors.md#windows); PowerShell is not the script runtime.
- **Unfinished branches** must be pushed (the assistant asks first) to continue on another machine.
