# Usage

Day-to-day use: switching the harness on and off, what to ask, and keeping it up to date.

## CLI help

Run `harness help`, `harness --help` or `harness -h` for command syntax, options, exit codes and examples. Help also works outside a Git repository. Running `harness` without a command displays project status.

## Installation, diagnostics and removal

Clone into any directory you choose and run `./install.sh` from that checkout. Installation exposes global configuration through symlinks; you can enable the workflow in any Git project, independently of where the harness repository lives. Keep the checkout available or reinstall after moving it.

```bash
./install.sh --dry-run                 # preview links, settings, Git and plugin actions
./install.sh --dry-run --skip-plugins  # preview local configuration only
./install.sh --skip-plugins            # apply local configuration only
harness doctor                        # check installation and current project; no writes
./uninstall.sh --dry-run               # preview safe restoration
./uninstall.sh                         # restore recorded unchanged state
```

Doctor checks required tools, managed links, Claude settings and hook registration, ownership metadata, effective Git hooks, project activation and formatter trust. Missing optional CLIs and deliberate foreign hooks paths produce warnings. Broken managed components produce errors (exit 1); a healthy checked installation exits 0. Doctor works outside Git and never runs plugins or prints restoration snapshots or credentials. It diagnoses configuration rather than proving every external tool works.

Installation records changes privately under `${XDG_STATE_HOME:-$HOME/.local/state}/agent-harness/ownership`. Original state and installation-time tool declarations survive reinstallations, so later customization does not invalidate historical ownership. These snapshots may include private settings: do not commit or share them. Uninstall needs Python to validate ownership and selectively restore settings. It removes unchanged recorded links, restores safely displaced original files or links, and reverses unchanged owned settings and Git hooks. Changed links, parent directories, settings and hooks are preserved conservatively; retained records allow a later retry.

Uninstall never deletes project files, project activation/trust configuration or shared plugins. It cannot infer ownership of legacy configuration: paths already identical before recording began are preserved. Installation and uninstall previews make no persistent changes. Installation accepts paths with spaces; use absolute paths without tabs, newlines or dot components, and keep the checkout path free of quotes and backslashes for Claude hook command substitution.

## On/off per project
The workflow (planning, TDD, conventions, docs, Conventional Commits, auto-format) is opt-in per project, and its weight follows the [workflow mode](#workflow-modes). Everywhere else the AI works normally and only the safety net stays on.

```bash
harness doctor            # read-only installation and project diagnostics
harness help              # CLI reference; aliases: --help and -h
harness status            # workflow activation, mode and local formatter trust
harness status --quiet    # no output; exit 0 when enabled, 1 when disabled
harness enable            # this clone only (git config; nothing added to the repo)
harness enable --shared   # commit a .harness file so every clone has it
harness disable
harness mode              # effective mode and its source
harness mode lite         # set the mode for this project
harness mode strict --global   # set your default for every project
harness mode --unset      # go back to the global default
harness context           # project instructions plus an index of architecture and active handoff
harness trust             # permit automatic project formatter execution in this clone
harness trust --revoke     # revoke execution permission without disabling the workflow
harness trusted           # trusted / untrusted; exit 0 when trusted, 1 otherwise
harness trusted --quiet   # the same trust check without output
git config --global harness.enabled true   # every repo (a local disable still wins)
```

| | Enabled project | Any other repo |
| --- | --- | --- |
| Command guard, protection of `main` and tags | ✔ | ✔ (tags: enabled only) |
| No `.env` files or credentials committed | ✔ | ✔ |
| AI attribution removed from commits | ✔ | ✔ |
| Conventional Commits enforced | ✔ | — |
| Workflow at the configured mode | ✔ | — |
| Claude Code auto-format | With explicit local trust | — |

Start a new session after switching. Claude Code is told the status at session start; other tools check `harness status` as their instructions say. Projects created with "create a project…" are enabled automatically.

## Workflow modes

The mode decides how much process each task gets. `auto` is the default: before each task the assistant picks a level, states it in one line (for example `Level: standard (bounded bug fix)`) and moves up if the task grows. You can change the level for one task ("do this in strict") or fix it with `harness mode`.

| | lite | standard | strict |
| --- | --- | --- | --- |
| Typical task | Question, typo, config tweak, one-line fix, small script | Bounded feature or bug fix in one area | Several modules, architecture, migrations, security, risky or debatable design |
| Plan | None | Short plan in the task list | Saved in `docs/plans/`; waits for your approval |
| Tests | For changed logic | TDD | TDD |
| Docs | Only if they become wrong | What changed behaviour affects | Full checklist and ADRs |
| Handoff | None | Only for multi-session work or low context | Kept from the start |
| AI log | None | None | One row per task |
| Review | Self-review | `code-reviewer` for large or risky diffs | `code-reviewer` before offering to push |
| Delegation | Suggested, waits for OK | Suggested, waits for OK | Automatic after approval |

In every mode the hooks still enforce Conventional Commits, no AI attribution, no secrets and protected `main` and tags; the assistant works on a branch, asks before anything outward-facing and **asks whenever it has a real doubt** instead of guessing.

A project setting (`harness mode lite`) overrides your global default (`harness mode lite --global`); with neither, the mode is `auto`. Invalid values behave as `auto` and are reported by `harness status` and `harness doctor`. Lighter modes cost fewer tokens and less time; [results](results.md) compares them.

## Startup context and formatter trust

Claude Code's SessionStart hook supplies the activation status and mode plus the project's `AGENTS.md`. Documents load on demand: `auto` and `standard` add an index with the path of `docs/architecture.md` and the newest active or paused handoff, including its status and next step; `strict` adds bounded excerpts of both; `lite` adds nothing. Other tools follow the global instructions to run `harness context` at session start. This is an instruction-driven startup step for tools without a SessionStart hook.

The combined document content is capped at 6,000 bytes, with per-file line limits. Claude Code also receives it again after compacting the conversation. Missing files and symlinks outside the checkout are skipped. Read the referenced documents in full when needed. Disable the extra context with `git config harness.context false`; activation messages remain available.

A shared `.harness` file enables workflow instructions but does not authorise execution of project code. Run `harness trust` only for a checkout whose formatter binaries and configuration you trust. Formatting requires both activation and explicit local trust; global trust settings are ignored. `harness trust --revoke` removes that execution permission.

`harness status` shows both settings, for example:

```text
enabled
mode: auto (default)
formatter trust: trusted
```

The first line and exit status describe workflow activation; the mode line shows its source (`local`, `global` or `default`); formatter trust is independent and can remain configured while the workflow is disabled. `harness trusted` checks only trust and prints `trusted` or `untrusted`. Both queries support `--quiet` for scripts. Trust permits Claude Code's formatter hook to run project formatters; it is not a general permission for the AI to execute commands.

## What to ask
Talk normally, in your language:

| You say | What happens |
| --- | --- |
| "Add Google login" | States the level, then plans as that level requires (waits for your OK at strict) → branch → tests → Conventional Commits → docs → summary. Asks before pushing. |
| "Work on issue #12" | Reads the issue and its acceptance criteria; the PR closes it (after asking). |
| "Checkout is broken" | Reproduces the bug, writes a failing test, fixes the root cause. |
| "What would you improve in this module?" | Asks scope and focus, runs read-only reviewers, gives a prioritised report and creates deduplicated GitHub issues for verified findings unless you request no publication. |
| "Use subagents" | Splits the approved plan across agents using available models and effort by complexity. |
| "Improve it autonomously until it scores 8/10" | `auto-improve`: asks scope and focus, then scores, fixes and re-scores on its own branch until 8/10 or 5 iterations. Never pushes. |
| "Prepare a release" | SemVer version from commits; with release-please, reviews and merges the release PR (after asking). |
| "Write a handoff" | Writes the state of the work to `docs/handoffs/` so anyone can continue. |
| "Use pnpm from now on" | Fixes it and saves the rule (`lessons`). |

## Automatic delegation and integration choices

In enabled projects, complex strict-level work with independent parts is delegated automatically after the plan is approved; at lite and standard the assistant suggests delegation and waits for your OK, because each subagent starts cold and costs extra tokens. Small or tightly coupled tasks stay with the main assistant. The harness recommends available models and effort according to complexity; the actual selection depends on the tool's supported controls. Tools without subagents perform the plan sequentially.

```bash
git config --local harness.delegation off    # disable automatic delegation in this clone
git config --local harness.delegation auto   # restore the default automatic policy
git config --get harness.delegation          # absent means auto
```

Explicitly asking for subagents authorises them for that task even when automatic mode is off. Disabling the workflow with `harness disable` also removes automatic delegation from the enabled-project policy. Delegation is driven by instructions, not enforced by a process scheduler, and can consume more tokens. Invalid mode values are treated as off and reported.

The assistant commits coherent verified milestones as it works. Before integrating a PR, it inspects the history, recommends preserving useful milestones with a merge commit or combining temporary intermediate commits with squash, and offers the available methods in the existing integration confirmation. Commits are preserved unless you explicitly choose squash; a choice already given for that integration is respected without asking again.

## Moving between tools and machines

Every supported tool reads the same installed instructions and skills, so you can switch tools mid-task. Before switching, ask for a handoff (or let the strict level keep one); the next tool reads it at session start.

- **Claude Code to Codex:** the installer already configures Codex. Codex's own `/import` can bring recent chats and projects from Claude Code; when it offers configuration, skills, agents or hooks, skip them, because copies would duplicate the harness's symlinked versions and would not update with `git pull` or be recognised by `doctor` and `uninstall.sh`.
- **Windows:** use WSL2. Clone inside the Linux file system (for example `~/Projects`, not `/mnt/c`), install the AI tools inside WSL and run `./install.sh` there. Native Windows shells are not supported.
- **Unfinished branches** must be pushed (the assistant asks first) to continue on another machine.

## Overrides
| Situation | Command |
| --- | --- |
| A repo with other commit conventions | `git config harness.conventionalCommits false` |
| A deliberate force-push to `main` | `HARNESS_ALLOW_FORCE_PUSH=1 git push --force …` |
| A deliberate tag change | `HARNESS_ALLOW_TAG=1 git push …` |
| A false positive in the secrets check | `HARNESS_ALLOW_SECRETS=1 git commit …` |

Secret scanning runs after the local pre-commit hook and keeps the added-line policy. Renamed files are treated as new content, so moving a file containing an old credential can also be refused. Git inspection errors block the commit rather than silently accepting it.

## Updating
```bash
cd /path/to/your/agent-harness && git pull && ./install.sh
```
Replace the path with the directory you chose during installation.
To change a rule, edit the files here or tell the AI (it uses `lessons`), then commit and push. Changes apply at once on this machine through the symlinks; restart the tool for new skills or agents.
