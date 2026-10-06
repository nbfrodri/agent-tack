# Usage

Day-to-day use: switching tack on and off, what to ask, and keeping it up to date.

## CLI help

Run `tack help`, `tack --help` or `tack -h` for command syntax, options, exit codes and examples. Help also works outside a Git repository. Running `tack` without a command displays project status.

## Installation, diagnostics and removal

Clone into any directory you choose and run `./install.sh` from that checkout. Installation exposes global configuration through symlinks; you can enable the workflow in any Git project, independently of where tack repository lives. Keep the checkout available or reinstall after moving it.

```bash
./install.sh --dry-run                 # preview links, settings, Git, plugin and mod actions
./install.sh --dry-run --skip-plugins  # preview local configuration only
./install.sh --skip-plugins            # apply local configuration only (also skips mods)
./install.sh --skip-mods               # apply everything except the Claude Code mods
./install.sh --no-hooks                # instructions, skills, agents and settings, but no hooks
tack doctor                        # check installation and current project; no writes
tack doctor --tools                # check each installed AI tool instead of the project
./uninstall.sh --dry-run               # preview safe restoration
./uninstall.sh                         # restore recorded unchanged state
```

Skills come in groups (`skill-groups.txt`): `core` (the workflow, reviews and delegation, always installed), `process` (releases, new projects) and `stack` (frontend, APIs, databases, auth, end-to-end tests, deployment, observability). Fewer skills mean fewer descriptions in every session of every tool. Choose the optional groups once, then re-run the installer; it removes only its own links to the skills you left out:

```bash
tack config skill-groups process --global   # core and process; or core, stack, or all (the default)
./install.sh
```

The first install that registers hooks ends with a short list of them and what each does (from `hooks/summary.txt`), and how to turn them off; later installs skip it. `--no-hooks` registers no git, Claude Code or Codex hooks and removes tack's Claude Code and Codex hooks from an earlier install (your own hooks stay); global git hooks from an earlier install remain until `./uninstall.sh`, which restores your former `core.hooksPath`. Without hooks the rules apply only as instructions.

Doctor checks required tools, managed links, Claude settings and hook registration, ownership metadata, effective Git hooks, project activation and formatter trust. Missing optional CLIs and deliberate foreign hooks paths produce warnings. Broken managed components produce errors (exit 1); a healthy checked installation exits 0. Doctor works outside Git and never runs plugins or prints restoration snapshots or credentials. It diagnoses configuration rather than proving every external tool works. Doctor also warns when the claude CLI is missing or a tack mod is not installed or is disabled, and reports `chat.useAgentsMdFile` for each VS Code install it finds.

`tack doctor --tools` checks each installed AI tool listed in `targets.txt`: version, configured capabilities, minimum version and a non-interactive smoke check (`claude doctor`, `codex doctor --summary`). It prints no tool output or credentials. A failed smoke check or an old version is a warning; a broken managed link is an error. A weekly CI workflow installs the latest Claude Code and Codex and runs the same check, so breaking changes in either tool surface early.

Installation records changes privately under `${XDG_STATE_HOME:-$HOME/.local/state}/agent-tack/ownership`. Original state and installation-time tool declarations survive reinstallations, so later customization does not invalidate historical ownership. These snapshots may include private settings: do not commit or share them. Uninstall needs Python to validate ownership and selectively restore settings. It removes unchanged recorded links, restores safely displaced original files or links, and reverses unchanged owned settings and Git hooks. Changed links, parent directories, settings and hooks are preserved conservatively; retained records allow a later retry.

Uninstall never deletes project files, project activation/trust configuration or shared plugins. It removes only the mods and local marketplace recorded by the installer; plugins from `plugins.txt`, and mods or marketplaces you already had, are kept.

## Claude Code mods

The installer adds two mods to Claude Code (other tools do not support mods):

| Mod | What it shows | Command |
| --- | --- | --- |
| `usage-band` | A band above the prompt: the active tack mode (`tack · <mode>`, `tack · off` when the project is not enabled, or `tack · ?` when tack could not answer: `/usage-band` says why), 5-hour and weekly usage with reset times, context fill and session cost; toasts at 80% and 90%. Limits appear after the first response and only on a subscription | `/usage-band` hides or shows it |
| `agent-activity` | A live pane of tool calls, skills, subagents (with their model) and permission prompts or denials; subagent actions are marked `↳` | `/activity` opens it, or closes it when it is open (it opens by itself on terminals at least 144 columns wide) |

Opt out with `./install.sh --skip-mods` or `tack config mods false --global`, then rerun the installer; `./uninstall.sh` removes them. To change a mod, edit it under `plugins/`, bump `version` in its `plugin.json` and rerun `./install.sh` (Claude Code caches installed plugins). It cannot infer ownership of legacy configuration: paths already identical before recording began are preserved. Installation and uninstall previews make no persistent changes. Installation accepts paths with spaces; use absolute paths without tabs, newlines or dot components, and keep the checkout path free of quotes and backslashes for Claude hook command substitution.

## On/off per project
The workflow (planning, TDD, conventions, docs, Conventional Commits, auto-format) is opt-in per project, and its weight follows the [workflow mode](#workflow-modes). Everywhere else the AI works normally and only the safety net stays on.

```bash
tack doctor            # read-only installation and project diagnostics
tack help              # CLI reference; aliases: --help and -h
tack status            # workflow activation, mode and local formatter trust
tack status --quiet    # no output; exit 0 when enabled, 1 when disabled
tack enable            # this clone only (git config; nothing added to the repo)
tack enable --scaffold # also add the missing AGENTS.md, CLAUDE.md, docs/architecture.md, docs-map.txt,
                       # and plan, handoff and AI-log templates, never overwriting a file
                       # (CLAUDE.md only points to AGENTS.md, so it is harmless for other tools)
tack enable --shared   # commit a .tack file so every clone has it
tack disable
tack mode              # effective mode and its source
tack mode lite         # set the mode for this project
tack mode strict --global   # set your default for every project
tack mode --unset      # go back to the global default
tack config            # feature toggles with value, source and enforcement
tack config delegation off            # set a toggle for this project
tack config context false --global    # set it for every project
tack config delegation --unset        # go back to the global value or default
tack context           # project instructions plus an index of architecture and active handoff
tack trust             # permit automatic project formatter execution in this clone
tack trust --revoke     # revoke execution permission without disabling the workflow
tack trusted           # trusted / untrusted; exit 0 when trusted, 1 otherwise
tack trusted --quiet   # the same trust check without output
git config --global tack.enabled true   # every repo (a local disable still wins)
```

| | Enabled project | Any other repo |
| --- | --- | --- |
| Command guard, protection of `main` and tags | ✔ | ✔ (tags: enabled only) |
| No `.env` files or credentials committed | ✔ | ✔ |
| AI attribution removed from commits | ✔ | ✔ |
| Conventional Commits enforced | ✔ | — |
| Workflow at the configured mode | ✔ | — |
| Claude Code auto-format | With explicit local trust | — |

Start a new session after switching. Claude Code is told the status at session start; other tools check `tack status` as their instructions say. Projects created with "create a project…" are enabled automatically.

## Feature toggles

`tack config` turns individual features on or off without editing files. It lists every toggle declared in `features.txt` with its current value, where that value comes from (`local`, `global` or `default`) and how it is enforced:

| Enforcement | Meaning |
| --- | --- |
| `hook` | A hook guarantees it (for example `conventional-commits`) |
| `instruction` | The assistant follows it; guided, not forced (for example `delegation`, `context`) |
| `installer` | `install.sh` reads it; user-wide only (for example `mods`, `vscode-agents-md`) |

A project value wins over the global one, which wins over the default. Values are validated: booleans take `true` or `false`, others list their alternatives. User-wide features refuse a project value. Secret scanning, the command guard and the protection of `main` and tags are not toggles; they keep their [one-off overrides](#overrides). Add a toggle by adding a line to `features.txt` ([customization](customization.md)).

### Turning off individual hooks

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

### Fast check after edits

```bash
tack trust                                    # the check runs project code, like the formatter
tack config check-fast "uv run pytest -q -x"  # or: npm test -- --bail, make lint, ...
```

Without it, tack detects the project's test command (a `make test` target, the `package.json` test script with npm, pnpm, yarn or bun, pytest with or without uv, `cargo test` or `go test ./...`). `tack enable`, `tack status` and the startup context name it (`tack enable` also suggests `tack trust` when the project is not trusted yet), so the assistant runs it instead of searching for one, and in trusted projects the check before stopping runs it whenever source or test files changed.

With `check-fast` set, after each file edit Claude Code runs the command from the repository root. When it fails, the assistant sees the exit code and the last 40 lines of output and fixes the problem before continuing. Keep it fast (a focused test target or a linter); it times out after 60 seconds where `timeout` is available. Remove it with `tack config check-fast --unset`.

### Check before stopping and the docs map

Before Claude Code's assistant ends a turn in an enabled project, a Stop hook looks for unfinished business: uncommitted changes, failing tests (the fast check or the detected test command, in trusted projects), source files changed on the branch while no test changed (only in projects that have tests; docs, config and deletions do not count), a stale handoff, and code changed on the branch without the docs that `docs-map.txt` pairs with it. If it finds any, the assistant gets the list once and either fixes it or explains why it stays; the next stop always goes through. Turn it off with `tack config stop-check false`.

A handoff a commit or two behind is normal mid-task, so it is reported only once it is `handoff-stale-commits` code commits behind (default 3; commits that only touch plans, handoffs or `docs/archive/` do not count), or as soon as that work is pushed, or when it names another branch:

```bash
tack config handoff-stale-commits 5   # ask less often in this project
```

`docs-map.txt` lives in the project root, one rule per line:

```text
# code glob | docs that should change with it
src/api/* | docs/api.md, README.md
bin/mycli | docs/usage.md
```

A rule is satisfied when any of its docs changed on the branch or in the working tree.

### CI: wait for it, merge only when green

In `standard`, `strict` and `unleash`, after a push or a new pull request the assistant waits for CI in the background, reports the result and fixes failures from the failed job's log before continuing (`ci-watch`, default `true`; `lite` and `lean` skip it). Independently, in enabled projects the command guard refuses `gh pr merge` while the pull request's checks fail or are still running, so the assistant waits and retries. `--auto` may go ahead with pending checks, because GitHub then waits for them, and `--disable-auto` is never checked. When the checks cannot be read (no `gh`, no checks reported, a slow `gh`, or a merge after `cd` or with `GH_REPO`), it asks you; in Codex that becomes a refusal. A project without CI therefore asks on every merge: turn the rule off there (`merge-requires-green`, default `true`):

```bash
tack config ci-watch false               # do not wait for CI after a push in this project
tack config merge-requires-green false   # let gh pr merge through without checking CI
```

### Activity log

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

## Workflow modes

The mode decides how much process each task gets. `auto` is the default: before each task the assistant picks a level, states it in one line (for example `Level: standard (bounded bug fix)`) and moves up if the task grows. You can change the level for one task ("do this in strict") or fix it with `tack mode`.

| | lite | standard | strict |
| --- | --- | --- | --- |
| Typical task | Question, typo, config tweak, one-line fix, small script | Bounded feature or bug fix in one area | Several modules, architecture, migrations, security, risky or debatable design |
| Plan | None | Short plan in the task list | Saved in `docs/plans/`; waits for your approval |
| Tests | For changed logic | TDD | TDD |
| Docs | Only if they become wrong | What changed behaviour affects | Full checklist and ADRs |
| Handoff | None | Only for multi-session work or low context | Only for multi-session or delegated work, updated at milestones |
| AI log | None | None | One row per task, in the same commit as the change |
| Review | Self-review | `code-reviewer` for large or risky diffs | `code-reviewer` before offering to push |
| Delegation | Suggested, waits for OK | Suggested, waits for OK | Automatic after approval |

In every mode the hooks still enforce Conventional Commits, no AI attribution, no secrets and protected `main` and tags; the assistant works on a branch, asks before anything outward-facing and **asks whenever it has a real doubt** instead of guessing (except in `unleash`, below). It also follows token-efficiency rules: search before reading, read only the needed ranges, batch tool calls, trim output and avoid commands the guard would ask about.

A project setting (`tack mode lite`) overrides your global default (`tack mode lite --global`); with neither, the mode is `auto`. Invalid values behave as `auto` and are reported by `tack status` and `tack doctor`. Lighter modes cost fewer tokens and less time; [results](results.md) compares them.

### Lean: save tokens

`tack mode lean` is for small, well-defined tasks when tokens matter more than process. Its rules are self-contained, so the assistant does not load `dev-workflow`; it starts with only `AGENTS.md` as context, reads only the lines it needs, runs only the affected tests and replies in a few lines. It still branches, adds a test for changed logic and makes a Conventional Commit, and the hooks apply as in every mode. It skips plans, handoffs, the AI log, review agents and delegation, and suggests `standard` or `strict` when a task turns out risky.

The same savings are available one by one in any mode:

```bash
tack config reply-style terse          # short replies (output tokens)
tack config skill-loading minimal      # load skills only when needed (input tokens)
tack config subagent-model economical  # cheapest capable model when delegating
tack config context false              # no startup context at all
tack config stop-check false           # no extra turn before stopping
```

Add `--global` to make any of them your default. [Results](results.md) compares `lean` with `lite` and the plain assistant.

### Unleash: autonomous work

`tack mode unleash` lets the assistant work without asking: it follows its plan without waiting for approval, decides instead of asking (recording every assumption in the handoff and final summary), may push its branch and open a pull request, and the command guard stops asking about explicit local data loss in the current project (`git reset --hard`, `clean -f`, `restore`, discarding checkouts, `branch -D`, `stash drop`, `rm -rf .`). That waiver never applies to a command that changes directory (`cd`, `pushd`, `popd`) or points git elsewhere (`-C`, `--git-dir`, `--work-tree`), nor to deleting `main` or `master`. The assistant also cannot change tack's settings in this mode: `tack config` writes, `tack mode`, `trust`, `enable`, `disable` and `git config tack.*` (or former `harness.*`) writes are refused, so it cannot lift its own limits or leave the mode.

What stays, whatever the mode:

- every `deny` rule: hook bypasses, `core.hooksPath` overrides, force-push to `main`, tag changes, catastrophic deletes;
- asks about deleting outside the project (paths with `..` are resolved) or the `.git` folder, rewriting remote history, database and infrastructure commands, code piped into a shell, your own guard rules, and opaque or unanalysable commands (heredocs to interpreters, loops, dynamic commands), because hiding a command inside them would otherwise skip the deny rules;
- never merging to `main`, tagging, releasing or rewriting published history.

It is project-only and branch-only: `tack mode unleash --global` is refused, a global value set by hand is ignored, and selecting it on `main` or `master` is refused (`tack doctor` warns if you switch back to them later). Session start shows a warning and `tack doctor` reports it. Claude Code's own permission prompts are separate: for unattended runs also choose a permissive permission mode in Claude Code.

Optional limits, none by default; set either, both or neither, per project or with `--global`:

```bash
tack config unleash-max-tool-calls 300   # a hook refuses tool calls past 300 in one session
tack config unleash-max-cost 5           # the usage mod refuses tool calls once the session passes 5 USD
```

When a limit is reached, tool calls are refused with an instruction to update the handoff and summarise. The tool-call limit is enforced by a Claude Code hook and counts every tool call per session (counters live in `${XDG_STATE_HOME:-~/.local/state}/agent-tack/budget/`, are deleted at session start once older than `tack config state-retention-days --global` (default 30; user-wide, because the state is) and are counted by `tack doctor`; parallel tool calls can make the count slightly low, so treat it as a safety net rather than an exact quota); the cost limit needs the `usage-band` mod and a session that reports its cost.

Risks you accept: wrong decisions nobody stops in time, lost uncommitted work, unbounded token use unless you set a limit, and above all prompt injection: text in the repository, an issue or a web page can steer an agent that no longer asks. Prefer a container or an isolated machine without important credentials, and review the assumptions and the pull request before merging.

### Your own modes

Each mode is a short file of rules: the built-in ones in `modes/`, yours in `~/.config/agent-tack/modes/` (outside the repository, so updates never overwrite them).

```bash
tack mode list                   # built-in and user modes, with when to use each
tack mode new spike --from lite  # copy lite into ~/.config/agent-tack/modes/spike.md
$EDITOR ~/.config/agent-tack/modes/spike.md
tack mode spike                  # use it in this project (or --global)
tack mode show                   # the rules the assistant receives at session start
```

A mode file has a `# name` title, a `When:` line (used by `auto` to choose and by `mode list`), a `Scope:` line and `- ` rule lines. Built-in names cannot be reused. In `auto`, the assistant chooses among all modes, yours included. If a selected user mode is deleted, the mode falls back to `auto` and `status` reports it.

## Startup context and formatter trust

Claude Code's SessionStart hook supplies the activation status and mode plus the project's `AGENTS.md`. Documents load on demand: `auto` and `standard` add an index with the path of `docs/architecture.md` and the newest active or paused handoff, including its status and next step; `strict` adds bounded excerpts of both; `lite` lists only the handoff. Every mode adds a handoff check: it compares the handoff with git and says whether it is up to date, may be stale (commits after its last update, not counting commits that only touch `docs/plans/` or `docs/handoffs/`) or names another branch, so a resumed session verifies and refreshes it before continuing. Other tools follow the global instructions to run `tack context` at session start. This is an instruction-driven startup step for tools without a SessionStart hook.

The combined document content is capped at 6,000 bytes, with per-file line limits. Claude Code also receives it again after compacting the conversation. Missing files and symlinks outside the checkout are skipped. Read the referenced documents in full when needed. Disable the extra context with `git config tack.context false`; activation messages remain available.

To bound everything SessionStart adds (activation line, mode rules, settings and project context), set a character cap, useful for small-context or local models. Past the cap the project context goes first, then the mode rules; the activation line always stays, and a final line points to `tack mode show` and `tack context` for the rest:

```bash
tack config context-max-chars 4000 --global
```

A shared `.tack` file enables workflow instructions but does not authorise execution of project code. Run `tack trust` only for a checkout whose formatter binaries and configuration you trust. Formatting requires both activation and explicit local trust; global trust settings are ignored. `tack trust --revoke` removes that execution permission.

`tack status` shows both settings, for example:

```text
enabled
mode: auto (default)
formatter trust: trusted
```

The first line and exit status describe workflow activation; the mode line shows its source (`local`, `global` or `default`); formatter trust is independent and can remain configured while the workflow is disabled. `tack trusted` checks only trust and prints `trusted` or `untrusted`. Both queries support `--quiet` for scripts. Trust permits Claude Code's formatter hook to run project formatters; it is not a general permission for the AI to execute commands.

## Candidate lessons

When you correct the assistant, `lessons` saves a lasting rule in the right file. A correction it does not save yet is counted instead, so a repeat is noticed ([ADR 0001](adr/0001-candidate-lessons.md)):

```bash
tack lesson list                          # this project's and your user-wide candidates
tack lesson note use-pnpm "Use pnpm, not npm."   # what the assistant runs; a repeat adds to the count
tack lesson contradict use-pnpm           # evidence against a candidate
tack lesson forget use-pnpm               # after it was saved as a rule, or declined
```

After three sightings with little against it, a candidate is marked `ready` and the assistant asks you whether to save it as a rule. Session start shows up to three of the strongest as unconfirmed hints, last in priority under `context-max-chars`. Candidates live only on this machine, in `~/.local/state/agent-tack/lessons.tsv` (readable only by you); the rules you approve are what travel, through the config repository.

## Shared memory

Notes about you that are not rules and not about one project (your machine, your accounts, a preference you have not made a rule) live in one Markdown file that Claude Code and Codex both read at session start, in every project ([ADR 0002](adr/0002-shared-memory.md)):

```bash
tack memory                                # print the notes
tack memory add "Runs Arch Linux; use pacman, not apt."   # a dated note at the top
tack memory path                           # ~/.config/agent-tack/memory.md: edit it to change or remove notes
```

Only lines starting with `- ` are loaded; other text you write in the file is kept but not loaded. The assistant shows you a note and waits for your OK before adding it. Each tool keeps its own memory too; this file is the part they share. Notes that look like credentials are refused, and the file is readable only by you. Session start adds the newest notes up to `memory-max-chars` (2000 by default) and says where the rest is; `tack config memory false --global` turns it off. Rules that should apply everywhere still belong in `global/AGENTS.md`, through `lessons`.

## Requirements and traceability

At standard and strict, the plan or issue numbers each acceptance criterion (`R1`, `R2`…) and checks them for verifiability, consistency, completeness and traceability before any code (`dev-workflow` → `references/requirements.md`); each test names the requirement it proves (`test_lockout_R2`, or a `R2` comment), and the pull request lists requirement → tests → commit. `tack trace` checks the result in any language:

```bash
tack trace                               # the newest plan in docs/plans/
tack trace docs/plans/2026-10-01-login.md
```

It lists each requirement as `covered` with the test files that name it, or `MISSING` with its text, warns about tests naming a requirement the plan no longer has, and exits 1 when one is missing, so CI can run it. Test files are found by the usual conventions (`tests/`, `spec/`, `test_*`, `*.test.*`, `*_test.*`).

## Visual review of UI changes

At standard and strict, a change to UI files (components, styles, templates) gets before and after screenshots and an independent score. The assistant captures the affected pages before editing and again after, at mobile (390×844) and desktop (1440×900) widths:

```bash
tack shots --before http://localhost:3000/          # before changing anything
tack shots --after http://localhost:3000/ --name home
tack shots --dir                                    # this branch's folder for today
tack shots --index                                  # rebuild index.html after score.md is written
```

Everything goes to `.tack-screenshots/<date>-<branch>/` in the repository, with `before/`, `after/` and an `index.html` that shows them side by side; open that file in a browser. The folder ignores itself in git, so nothing is committed; the assistant may attach the after shots to the pull request. (`.tack` is the shared marker file, so the screenshots cannot live under it.)

`ui-reviewer`, in a fresh context, scores the after shots on a fixed rubric (hierarchy, consistency, spacing and alignment, accessibility signals, responsiveness) and the assistant saves its `score.md` next to them; below 7/10 it fixes the findings and captures and scores once more before reporting. Tools without subagents run the scoring as a separate prompt over the same folder. `standard`, `strict` and `unleash` do it; `lite` and `lean` skip it, and `tack config visual-review false` turns it off. Capture local or preview URLs with test data: the assistant asks before attaching shots that show personal data to a pull request.

A branch keeps the folder of its first capture, so before and after pair up even on different days; take the before shots after creating the branch. A page is named by its path and query, not its host, so before on one port and after on another still pair; two URLs that would share a name are refused (use `--name`). The mobile shot is a 390×844 viewport, not a full device emulation. Add `.tack-screenshots/` to `.dockerignore` or a package's `files` list if those do not already exclude dot folders.

Capturing needs Playwright in the project (`npm i -D playwright && npx playwright install chromium`); `TACK_PLAYWRIGHT` names another command, split on spaces. Without it, `tack shots` says how to install it and exits 1; a capture that fails shows Playwright's last error line and exits 1.

## What to ask
Talk normally, in your language:

| You say | What happens |
| --- | --- |
| "Add Google login" | States the level, maps what the change affects (callers, tests, CLI help, docs), flags design that no longer scales, then plans as the level requires (waits for your OK at strict) → branch → smallest change with tests → Conventional Commits → affected docs → summary. Asks before pushing. |
| "Work on issue #12" | Reads the issue and its acceptance criteria; the PR closes it (after asking). |
| "Checkout is broken" | Reproduces the bug, writes a failing test, fixes the root cause. |
| "What would you improve in this module?" | Asks scope and focus, runs read-only reviewers, gives a prioritised report and creates deduplicated GitHub issues for verified findings unless you request no publication. |
| "Use subagents" | Splits the approved plan across agents using available models and effort by complexity. |
| "Improve it autonomously until it scores 8/10" | `auto-improve`: asks scope and focus, then scores, fixes and re-scores on its own branch until 8/10 or 5 iterations. Never pushes. |
| "Prepare a release" | SemVer version from commits; with release-please, reviews and merges the release PR (after asking). |
| "Write a handoff" | Writes the state of the work to `docs/handoffs/` so anyone can continue. |
| "Use pnpm from now on" | Fixes it and saves the rule (`lessons`). |

## Automatic delegation and integration choices

In enabled projects, complex strict-level work with independent parts is delegated automatically after the plan is approved; at lite and standard the assistant suggests delegation and waits for your OK, because each subagent starts cold and costs extra tokens. Small or tightly coupled tasks stay with the main assistant. Tack recommends available models and effort according to complexity; the actual selection depends on the tool's supported controls. Tools without subagents perform the plan sequentially.

```bash
tack config delegation off     # disable automatic delegation in this project
tack config delegation --unset # restore the default automatic policy
tack config delegation         # shows auto (default) when unset
```

Delegation picks a tier, never a vendor's model: `economical` for mechanical work, `balanced` for standard implementation, `strongest` for design-heavy or risky work. `tack models` shows the model each tool uses for each tier, from `model-tiers.txt`; Codex tiers say `inherit` until you name your account's models in `~/.config/agent-tack/model-tiers.txt` (same columns; your lines win):

```bash
tack models              # every tool and tier
tack models economical   # one tier
```

Documentation is delegated separately, at every level: when a committed change leaves docs pending in 3 or more files, the assistant hands them to the `docs-writer` agent, which runs on an economical model, then reviews its result. Smaller updates, ADRs and design decisions stay with the main assistant.

Explicitly asking for subagents authorises them for that task even when automatic mode is off. Disabling the workflow with `tack disable` also removes automatic delegation from the enabled-project policy. Delegation is driven by instructions, not enforced by a process scheduler, and can consume more tokens. Values set directly in git config that are neither `auto` nor `off` are treated as off and reported.

The assistant commits coherent verified milestones as it works. Before integrating a PR, it inspects the history, recommends preserving useful milestones with a merge commit or combining temporary intermediate commits with squash, and offers the available methods in the existing integration confirmation. Commits are preserved unless you explicitly choose squash; a choice already given for that integration is respected without asking again.

## Moving between tools and machines

Every supported tool reads the same installed instructions and skills, so you can switch tools mid-task. Before switching, ask for a handoff (or let the mode keep one when the work spans sessions); the next tool reads it at session start.

- **Claude Code to Codex:** the installer already configures Codex. Codex's own `/import` can bring recent chats and projects from Claude Code; when it offers configuration, skills, agents or hooks, skip them, because copies would duplicate tack's symlinked versions and would not update with `git pull` or be recognised by `doctor` and `uninstall.sh`.
- **Windows:** use WSL2. Clone inside the Linux file system (for example `~/Projects`, not `/mnt/c`), install the AI tools inside WSL and run `./install.sh` there. Native Windows shells are not supported.
- **Unfinished branches** must be pushed (the assistant asks first) to continue on another machine.

## Overrides
| Situation | Command |
| --- | --- |
| A repo with other commit conventions | `tack config conventional-commits false` |
| A deliberate force-push to `main` | `TACK_ALLOW_FORCE_PUSH=1 git push --force …` |
| A deliberate tag change | `TACK_ALLOW_TAG=1 git push …` |
| A false positive in the secrets check | `TACK_ALLOW_SECRETS=1 git commit …` |

Secret scanning runs after the local pre-commit hook and keeps the added-line policy. Renamed files are treated as new content, so moving a file containing an old credential can also be refused. Git inspection errors block the commit rather than silently accepting it.

## Updating
```bash
cd /path/to/your/agent-tack && git pull && ./install.sh
```
Replace the path with the directory you chose during installation.
To change a rule, edit the files here or tell the AI (it uses `lessons`), then commit and push. Changes apply at once on this machine through the symlinks; restart the tool for new skills or agents.

### Upgrading from agent-harness

The project was called agent-harness and its command `harness`. After `git pull && ./install.sh`:

- `tack` is the command; `harness` remains as an alias that prints a notice when you run it yourself, and will be removed in a later release.
- Settings move from `harness.*` to `tack.*` git keys. Old keys keep working: the new one wins when both exist, and changing a setting writes the new key and removes the old one in that scope.
- A project's `.harness` marker and `harness.*` settings still work, but a later release stops reading them: `tack doctor` warns when they are in use, and `tack migrate` moves this clone's and your user-wide settings to `tack.*` (a `tack.*` value already set wins) and renames `.harness` to `.tack`.
- The installer moves `~/.config/agent-harness` (your modes and guard rules) and `~/.local/state/agent-harness` (installation records) to `agent-tack`, re-tags hooks from `#harness` to `#tack`, and replaces the `agent-harness-mods` marketplace with `agent-tack-mods`.
- The git hooks' overrides are `TACK_ALLOW_*`; the former `HARNESS_ALLOW_*` variables still work.
- Codex sees new hook commands, so run `/hooks` in Codex and approve them again.
- Other machines keep working with the old names until you update them the same way.
