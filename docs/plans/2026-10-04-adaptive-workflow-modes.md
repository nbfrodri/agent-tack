# Adaptive workflow modes

- Status: implemented; the owner chose to run the benchmark once, after the next phase (pilot results in `docs/benchmarks/2026-10-04-modes-pilot.md`)
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
- Installer robustness for tool churn: `harness doctor --tools` smoke test against installed CLIs; weekly CI job installing the latest Claude Code and Codex to run it; per-tool adapters as data with minimum versions and capabilities (start with Codex hooks and agents if confirmed).

- Customization from the CLI: `harness config` to list and set feature toggles (value, source, description, whether a hook enforces it or it is an instruction) declared in a data file; safety checks (secrets, guard, protected `main`) stay outside general toggles and keep their one-off overrides. User-defined modes as data files (`modes/<name>.md`), created with `harness mode new <name> --from <mode>`, injected at session start and selectable by `auto`. Shares the configuration-as-data mechanism with the guard policy.

- Token efficiency rules for every level in `dev-workflow` (plus one line in the global instructions): search before reading and read only needed ranges, no re-reading or re-verifying, batch independent tool calls, trim command output, targeted tests before one full run, concise replies and docs, economical models for mechanical delegated work, avoid commands the guard asks about. Measure with the next benchmark against this phase's results.

- Documentation drift: a per-project impact map as data (e.g. `docs-map.txt`: code paths → docs to review); a non-blocking pre-commit or Stop hook compares the diff with the map and tells the agent which docs it left untouched, so it updates them in the same commit; drift tests for generated parts (e.g. `harness help` against the CLI section of `docs/usage.md`). No AI runs inside git hooks.

- Claude Code mods shipped by the harness: a usage band (5-hour and weekly limits, context fill, cost) and an agent activity pane (tool calls, skills, subagents, permission decisions), prototyped outside the repo on 2026-10-04; install them as plugins through the installer, with tests in CI.

## Added during implementation (approved)

- Startup context loads documents on demand: `auto` and `standard` index architecture and the active handoff; `strict` keeps excerpts.
- The workflow maps each change's impact (callers, tests, CLI help, docs), prefers the smallest modular change and raises architecture or scalability concerns before restructuring.
