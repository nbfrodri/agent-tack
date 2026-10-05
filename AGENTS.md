# AGENTS.md

This repo is the user's AI configuration (skills, agents, hooks, installer). Human docs: `README.md`.
Architecture and execution flows: `docs/architecture.md`; keep it current when components, dependencies or flows change.

## Commands
- Lint shell and Python: `tests/lint.sh` (ShellCheck and ruff at the versions CI pins; CI runs the same script)
- Run every suite in parallel: `tests/run-all.sh` (`-j N` to limit it; about half the serial time)
- Validate skills, agents and cross-references alone: `tests/validate.sh` (its own tests: `tests/validate.test.sh`)
- One suite at a time: `tests/<name>.test.sh` (`tests/run-all.sh --list` names them)
- Apply locally: `./install.sh` (idempotent)

## Rules for this repo
- Keep all repository content in English, including documentation, examples, skill trigger phrases and eval prompts, so it stays consistent for readers. Conversation language follows the global instructions.
- Shell scripts must run on bash 3.2 (macOS): no associative arrays, `mapfile`, `${var,,}` or `sed -i`.
- Tests never touch the real HOME or git config: use a temp HOME plus `XDG_CONFIG_HOME` and `GIT_CONFIG_NOSYSTEM=1`.
- A skill's `name` must match its folder. Descriptions say what it does and when to use it, within the budget `tests/validate.sh` enforces (they load in every session).
- Keep `global/AGENTS.md` short (it loads in every session); put detail in skills.
- Every change to the installer or hooks needs a test in `tests/`.

## Design
- tack must serve any model and any editor or agent: put rules in `AGENTS.md` and skills, enforcement in tool-neutral scripts with thin per-tool adapters, and never name a vendor's model in workflow rules.
- One responsibility per file: `install.sh` orchestrates steps; JSON merging lives in `lib/settings-merge.{py,jq}`; command parsing in `hooks/claude/lib/shell-parse.{py,sh}` and the guard dispatches from `guard-bash.sh` to structural rules in `hooks/claude/lib/guard-{git,files,exec,infra,wrappers}.sh` and pattern rules in `guard-policy.txt`; startup rendering in `lib/project-context.sh`.
- Extend through data, not code: AI tools in `targets.txt`, plugins in `plugins.txt`, feature toggles in `features.txt`, workflow modes in `modes/`, skills and agents as folders and files.
- Hooks ask `bin/tack status` whether a project is enabled and `bin/tack mode` for its workflow mode; nothing else reads the markers or `tack.mode` directly.
