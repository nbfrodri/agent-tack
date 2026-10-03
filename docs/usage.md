# Usage

Day-to-day use: switching the harness on and off, what to ask, and keeping it up to date.

## CLI help

Run `harness help`, `harness --help` or `harness -h` for command syntax, options, exit codes and examples. Help also works outside a Git repository. Running `harness` without a command displays project status.

## On/off per project
The full workflow (plan, TDD, conventions, docs, handoffs, AI log, Conventional Commits, auto-format) is opt-in per project. Everywhere else the AI works normally and only the safety net stays on.

```bash
harness help              # CLI reference; aliases: --help and -h
harness status            # workflow activation and local formatter trust
harness status --quiet    # no output; exit 0 when enabled, 1 when disabled
harness enable            # this clone only (git config; nothing added to the repo)
harness enable --shared   # commit a .harness file so every clone has it
harness disable
harness context           # bounded project instructions, architecture and active handoff
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
| Full workflow | ✔ | — |
| Claude Code auto-format | With explicit local trust | — |

Start a new session after switching. Claude Code is told the status at session start; other tools check `harness status` as their instructions say. Projects created with "create a project…" are enabled automatically.

## Startup context and formatter trust

Claude Code's SessionStart hook supplies the activation status plus bounded excerpts from the project's `AGENTS.md`, `docs/architecture.md` and the newest active or paused handoff. Other tools follow the global instructions to run `harness context` at session start. This is an instruction-driven startup step for tools without a SessionStart hook.

The combined document content is capped at 6,000 bytes, with per-file line limits. Missing files and symlinks outside the checkout are skipped. Read the referenced documents in full when needed. Disable the extra context with `git config harness.context false`; activation messages remain available.

A shared `.harness` file enables workflow instructions but does not authorise execution of project code. Run `harness trust` only for a checkout whose formatter binaries and configuration you trust. Formatting requires both activation and explicit local trust; global trust settings are ignored. `harness trust --revoke` removes that execution permission.

`harness status` shows both settings, for example:

```text
enabled
formatter trust: trusted
```

The first line and exit status describe workflow activation; formatter trust is independent and can remain configured while the workflow is disabled. `harness trusted` checks only trust and prints `trusted` or `untrusted`. Both queries support `--quiet` for scripts. Trust permits Claude Code's formatter hook to run project formatters; it is not a general permission for the AI to execute commands.

## What to ask
Talk normally, in your language:

| You say | What happens |
| --- | --- |
| "Add Google login" | Plan (waits for your OK if large; may suggest subagents) → branch → TDD → Conventional Commits → docs → summary. Asks before pushing. |
| "Work on issue #12" | Reads the issue and its acceptance criteria; the PR closes it (after asking). |
| "Checkout is broken" | Reproduces the bug, writes a failing test, fixes the root cause. |
| "What would you improve in this module?" | Asks scope and focus, runs read-only reviewers, gives a prioritised report and creates deduplicated GitHub issues for verified findings unless you request no publication. |
| "Use subagents" | Splits the plan across agents with a model and effort per task, after your OK. |
| "Improve it autonomously until it scores 8/10" | `auto-improve`: asks scope and focus, then scores, fixes and re-scores on its own branch until 8/10 or 5 iterations. Never pushes. |
| "Prepare a release" | SemVer version from commits; with release-please, reviews and merges the release PR (after asking). |
| "Write a handoff" | Writes the state of the work to `docs/handoffs/` so anyone can continue. |
| "Use pnpm from now on" | Fixes it and saves the rule (`lessons`). |

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
