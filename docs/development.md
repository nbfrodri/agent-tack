# Development

How to change this repo safely: commands, adding skills or agents, and measuring behaviour.

## Commands
```bash
shellcheck -x install.sh uninstall.sh bin/harness lib/*.sh tests/*.sh evals/run.sh git-hooks/_chain git-hooks/commit-msg git-hooks/pre-push git-hooks/pre-commit hooks/claude/*.sh hooks/claude/lib/*.sh
tests/validate.sh        # skills, agents, cross-references, components list coverage, budgets
tests/validate.test.sh   # the validator catches each kind of error
tests/install.test.sh    # installer, in throwaway HOME directories
tests/lifecycle.test.sh  # ownership, previews and safe uninstall
tests/doctor.test.sh     # read-only installation diagnostics
tests/tools.test.sh      # targets.txt columns, `doctor --tools` and the weekly workflow
tests/mods.test.sh       # mods step: install, opt-outs, dry run, uninstall and doctor (fake claude CLI)
tests/vscode.test.sh     # VS Code step: chat.useAgentsMdFile install, opt-out, dry run, uninstall and doctor
claude plugin validate plugins && claude plugin test plugins/usage-band && claude plugin test plugins/agent-activity   # the mods themselves (needs the claude CLI)
tests/hooks.test.sh      # git and Claude Code hooks, in throwaway repos
tests/cli.test.sh        # activation, modes, config, startup context and the help-vs-docs drift check
tests/settings.test.sh   # mixed user and harness hook groups in Python and jq
tests/safety.test.sh     # final index scanning, exact paths and formatter trust
tests/guard.test.sh      # executable shell syntax, boundaries and long inputs
tests/evals.test.sh      # offline runner, transcript metrics and report fixtures
```
CI runs ShellCheck and content validation on Linux, the installer and hook regression suites on Linux and macOS, and `claude plugin validate`/`test` for each mod on Linux when the claude CLI is available (it skips otherwise). Rules for contributors (bash 3.2, isolated tests…) are in [`AGENTS.md`](../AGENTS.md).

## Adding a skill, agent or tool
1. Create `skills/<name>/SKILL.md` or `agents/<name>.md` with `name` and `description` (what it does and when to use it, within the budget `validate.sh` enforces), or add a line to `targets.txt` for a new AI tool.
2. List it in [components](components.md) (the validator requires it); mention it in the README only if it changes what a newcomer needs to know.
3. Run `tests/validate.sh` and `./install.sh`, then commit and push.

## Tools compatibility (weekly)
`.github/workflows/tools-compat.yml` runs every Monday (and on demand from the Actions tab). It installs the latest Claude Code and Codex with npm, runs `./install.sh --skip-plugins` in a temporary HOME and then `harness doctor --tools`. It uses no credentials. A failure means a new tool release changed something the installer relies on: read the log, then adjust `targets.txt` or the installer.

## Behaviour evals
Real sessions on throwaway repos, comparing the harness with a plain assistant. They use tokens, so run them by hand after changing skills.
```bash
evals/run.sh <new-project|bug-fix|release> <baseline|auto|lean|lite|standard|strict> [repetition]   # harness = auto
evals/grade.py $EVALS_OUT/<scenario>/<condition>-<rep>    # writes metrics.json
evals/report.py                                          # Markdown tables
```
Latest results: [results](results.md).

Metrics version 2 separates Claude and Codex transcript formats, preserves unknown evidence as `null` and distinguishes test-file order from a verified red/green test run. Reports group runs by provider and metrics version rather than combining incompatible measurements.

Codex baseline runs use temporary HOME, XDG and CODEX_HOME directories. Only `auth.json` is copied with private permissions and removed afterward; API authentication through environment variables also works. Keyring-only authentication or credentials defined only in `config.toml` need a compatible authentication method before running the baseline. No global instructions, skills or Codex configuration are copied.


Each eval writes `metadata.json` with the scenario, condition, workflow mode, repetition, prompt SHA-256, harness revision, provider/CLI version, metric version and permission allowlist. Set `EVALS_MODEL` to request an explicit model; the resolved model is recorded only when observed in the transcript. A missing observation remains unknown. Do not publish raw transcripts or authentication files. Freeze the harness checkout before comparing runs so instruction edits cannot alter one condition mid-experiment.

For an isolated comparison, set private HOME, XDG_CONFIG_HOME, XDG_STATE_HOME, XDG_DATA_HOME, XDG_CACHE_HOME, provider config/auth directories and Git configuration **before** installing either condition. Merely changing HOME does not override inherited XDG paths. Copy only required authentication files with private permissions and remove those temporary copies after each attempt. Keep failed or interrupted attempts separate from completed samples; runner exit status and provider errors take precedence over an artifact-only score.
