# Adaptive workflow modes

- Status: approved, in progress
- Approval: owner approved on 2026-10-04 after reviewing the cost data in `docs/results.md` (2× focused tasks, 6.6× a new project).
- Goal: scale the workflow's ceremony to each task so small work costs less, with an automatic level as the default.

## Decisions

- Levels: `lite`, `standard`, `strict`; mode `auto` (default) picks a level per request and announces it in one line. The user can override it in conversation.
- Configuration through the CLI: `harness mode [auto|lite|standard|strict] [--global]`. Global git config sets the user's default; local git config overrides it per project. Invalid values behave as `auto` and are reported by `status` and `doctor`.
- Hooks are unchanged in every level: Conventional Commits, no AI attribution, no secrets, protected `main` and tags, command guard.
- Delegation follows the level: automatic only in `strict`; `lite` and `standard` suggest it and ask. `harness.delegation off` disables it everywhere.
- In every level the assistant asks whenever it has a real doubt; it only decides alone on purely conventional choices.
- Benchmark after implementation: `bug-fix` with 2 runs and `new-project` with 1 run for each of `baseline`, `lite`, `standard`, `strict`, `auto` (15 sessions).

## Commits

1. `feat(harness): add workflow mode command` — CLI, status, doctor, CLI tests.
2. `feat(hooks): tailor session context to workflow mode` — SessionStart message and context budget per mode, hook tests.
3. `feat(workflow): define adaptive workflow levels` — global instructions, `dev-workflow`, `project-docs`, `orchestrate`; ask-when-in-doubt rule.
4. `refactor(workflow): trim always-loaded instructions` — short core in `dev-workflow`, detail in references.
5. `test(evals): run conditions per workflow mode` — runner, metadata, grading, eval tests.
6. `docs: …` — README, usage, why, how-it-works, architecture, components, customization, development, AGENTS.md; close stale handoffs.
7. Benchmark, then `docs/results.md` and the README results table.

## Acceptance criteria

- `harness mode` reads and writes local and global modes; `status` shows the effective mode and its source.
- SessionStart reports the effective mode; `lite` loads only `AGENTS.md` as startup context.
- All suites, ShellCheck and `tests/validate.sh` pass; bash 3.2 compatible; tests use isolated HOME and git config.
- Documentation describes the modes accurately; benchmark results reported as measured, including failures.

## Next phase (approved, after the benchmark)

- Guard policy as versioned data (e.g. a policy file read by `guard-bash.sh`) so rules change without code edits.
- Feedback hooks: PostToolUse running fast lint/tests and returning failures to the agent; Stop hook warning about uncommitted work or failing tests.
