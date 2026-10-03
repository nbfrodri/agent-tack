# Development

How to change this repo safely: commands, adding skills or agents, and measuring behaviour.

## Commands
```bash
shellcheck -x install.sh bin/harness tests/*.sh evals/run.sh git-hooks/_chain git-hooks/commit-msg git-hooks/pre-push hooks/claude/*.sh
tests/validate.sh        # skills, agents, cross-references, README coverage, budgets
tests/validate.test.sh   # the validator catches each kind of error
tests/install.test.sh    # installer, in throwaway HOME directories
tests/hooks.test.sh      # git and Claude Code hooks, in throwaway repos
```
CI runs all of them on Linux and macOS. Rules for contributors (bash 3.2, isolated tests…) are in [`AGENTS.md`](../AGENTS.md).

## Adding a skill, agent or tool
1. Create `skills/<name>/SKILL.md` or `agents/<name>.md` with `name` and `description` (what it does and when to use it, within the budget `validate.sh` enforces), or add a line to `targets.txt` for a new AI tool.
2. List it in the README and [components](components.md).
3. Run `tests/validate.sh` and `./install.sh`, then commit and push.

## Behaviour evals
Real sessions on throwaway repos, comparing the harness with a plain assistant. They use tokens, so run them by hand after changing skills.
```bash
evals/run.sh <new-project|bug-fix|release> <harness|baseline> [repetition]
evals/grade.py $EVALS_OUT/<scenario>/<condition>-<rep>    # writes metrics.json
evals/report.py                                          # Markdown tables
```
Latest results: [results](results.md).
