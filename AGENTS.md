# AGENTS.md

This repo is the user's AI configuration (skills, agents, hooks, installer). Human docs: `README.md`.

## Commands
- Lint: `shellcheck -x install.sh bin/harness tests/*.sh evals/run.sh git-hooks/_chain git-hooks/commit-msg git-hooks/pre-push git-hooks/pre-commit hooks/claude/*.sh hooks/claude/lib/*.sh`
- Validate skills, agents and cross-references: `tests/validate.sh` (its own tests: `tests/validate.test.sh`)
- Test installer and hooks: `tests/install.test.sh && tests/hooks.test.sh`
- Apply locally: `./install.sh` (idempotent)

## Rules for this repo
- Shell scripts must run on bash 3.2 (macOS): no associative arrays, `mapfile`, `${var,,}` or `sed -i`.
- Tests never touch the real HOME or git config: use a temp HOME plus `XDG_CONFIG_HOME` and `GIT_CONFIG_NOSYSTEM=1`.
- A skill's `name` must match its folder. Descriptions say what it does and when to use it, within the budget `tests/validate.sh` enforces (they load in every session).
- Keep `global/AGENTS.md` short (it loads in every session); put detail in skills.
- Every change to the installer or hooks needs a test in `tests/`.

## Design
- One responsibility per file: `install.sh` orchestrates steps; JSON merging lives in `lib/settings-merge.{py,jq}`; command parsing in `hooks/claude/lib/shell-parse.sh` and the guard's policy in `guard-bash.sh`.
- Extend through data, not code: AI tools in `targets.txt`, plugins in `plugins.txt`, skills and agents as folders and files.
- Hooks ask `bin/harness status` whether a project is enabled; nothing else reads the markers directly.
