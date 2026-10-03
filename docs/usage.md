# Usage

Day-to-day use: switching the harness on and off, what to ask, and keeping it up to date.

## On/off per project
The full workflow (plan, TDD, conventions, docs, handoffs, AI log, Conventional Commits, auto-format) is opt-in per project. Everywhere else the AI works normally and only the safety net stays on.

```bash
harness status            # enabled / disabled
harness enable            # this clone only (git config; nothing added to the repo)
harness enable --shared   # commit a .harness file so every clone has it
harness disable
git config --global harness.enabled true   # every repo (a local disable still wins)
```

| | Enabled project | Any other repo |
| --- | --- | --- |
| Command guard, protection of `main` and tags | ✔ | ✔ (tags: enabled only) |
| No `.env` files or credentials committed | ✔ | ✔ |
| AI attribution removed from commits | ✔ | ✔ |
| Conventional Commits enforced | ✔ | — |
| Full workflow and auto-format | ✔ | — |

Start a new session after switching. Claude Code is told the status at session start; other tools check `harness status` as their instructions say. Projects created with "crea un proyecto…" are enabled automatically.

## What to ask
Talk normally, in your language:

| You say | What happens |
| --- | --- |
| "Añade login con Google" | Plan (waits for your OK if large; may suggest subagents) → branch → TDD → Conventional Commits → docs → summary. Asks before pushing. |
| "Trabaja en el issue #12" | Reads the issue and its acceptance criteria; the PR closes it (after asking). |
| "No funciona el checkout" | Reproduces the bug, writes a failing test, fixes the root cause. |
| "¿Qué mejorarías de este módulo?" | Asks scope and focus, runs read-only reviewers, gives a prioritised report. |
| "Hazlo con subagentes" | Splits the plan across agents with a model and effort per task, after your OK. |
| "Mejóralo solo hasta un 8" | `auto-improve`: asks scope and focus, then scores, fixes and re-scores on its own branch until 8/10 or 5 iterations. Never pushes. |
| "Haz una release" | SemVer version from commits; with release-please, reviews and merges the release PR (after asking). |
| "Haz un handoff" | Writes the state of the work to `docs/handoffs/` so anyone can continue. |
| "No, así no: usa pnpm" | Fixes it and saves the rule (`lessons`). |

## Overrides
| Situation | Command |
| --- | --- |
| A repo with other commit conventions | `git config harness.conventionalCommits false` |
| A deliberate force-push to `main` | `HARNESS_ALLOW_FORCE_PUSH=1 git push --force …` |
| A deliberate tag change | `HARNESS_ALLOW_TAG=1 git push …` |
| A false positive in the secrets check | `HARNESS_ALLOW_SECRETS=1 git commit …` |

## Updating
```bash
cd ~/Projects/agent-harness && git pull && ./install.sh
```
To change a rule, edit the files here or tell the AI (it uses `lessons`), then commit and push. Changes apply at once on this machine through the symlinks; restart the tool for new skills or agents.
