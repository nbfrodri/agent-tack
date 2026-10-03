# Usage

Day-to-day use: switching the harness on and off, what to ask, and keeping it up to date.

## On/off per project
The full workflow (plan, TDD, conventions, docs, handoffs, AI log, Conventional Commits, auto-format) is opt-in per project. Everywhere else the AI works normally and only the safety net stays on.

```bash
harness status            # enabled / disabled
harness enable            # this clone only (git config; nothing added to the repo)
harness enable --shared   # commit a .harness file so every clone has it
harness disable
harness context           # bounded project instructions, architecture and active handoff
harness trust             # permit automatic project formatter execution in this clone
harness trust --revoke     # revoke execution permission without disabling the workflow
git config --global harness.enabled true   # every repo (a local disable still wins)
```

| | Enabled project | Any other repo |
| --- | --- | --- |
| Command guard, protection of `main` and tags | ✔ | ✔ (tags: enabled only) |
| No `.env` files or credentials committed | ✔ | ✔ |
| AI attribution removed from commits | ✔ | ✔ |
| Conventional Commits enforced | ✔ | — |
| Full workflow and auto-format | ✔ | — |

Start a new session after switching. Claude Code is told the status at session start; other tools check `harness status` as their instructions say. Projects created with "create a project…" are enabled automatically.

## Startup context and formatter trust

Claude Code's SessionStart hook supplies the activation status plus bounded excerpts from the project's `AGENTS.md`, `docs/architecture.md` and the newest active or paused handoff. Other tools follow the global instructions to run `harness context` at session start. This is an instruction-driven startup step for tools without a SessionStart hook.

The combined document content is capped at 6,000 bytes, with per-file line limits. Missing files and symlinks outside the checkout are skipped. Read the referenced documents in full when needed. Disable the extra context with `git config harness.context false`; activation messages remain available.

A shared `.harness` file enables workflow instructions but does not authorise execution of project code. Run `harness trust` only for a checkout whose formatter binaries and configuration you trust. Formatting requires both activation and explicit local trust; global trust settings are ignored. `harness trust --revoke` removes that execution permission.

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

## Updating
```bash
cd /path/to/your/agent-harness && git pull && ./install.sh
```
Replace the path with the directory you chose during installation.
To change a rule, edit the files here or tell the AI (it uses `lessons`), then commit and push. Changes apply at once on this machine through the symlinks; restart the tool for new skills or agents.
