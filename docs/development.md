# Development

How to change this repo safely: commands and adding skills, agents or tools.

The [engineering practices](engineering-practices.md) connect conventions to concrete failure cases, compatibility, recovery and measured outcomes. Keep one responsibility per component, reuse project commands across local checks and CI, and include tests that would fail for the defect being fixed. A new configuration format needs explicit version/validation behavior; a persistent-state change needs a recovery strategy and relevant tests.

## Commands

This repository uses its own `checks-map.json`. Run `bin/tack verify --plan` to see
the selection, review the commands and grant `bin/tack trust` locally before
`bin/tack verify --budget-seconds 600`. Use `--all` for a clean-clone baseline.
No global installation or workflow activation is required for these manual checks.

Documentation-only changes select content validation. Runtime, installer, hook and
test changes conservatively select the full parallel suite; shell/Python changes
also select lint. The full suite includes content validation, so mixed changes can
repeat that short check. We accept this small duplication instead of maintaining
a second test runner. Keep Node, cached/downloadable esbuild and the pinned linters
available as described below. The 600-second budget is explicit because the
default 120 seconds may not fit the full suite. CI still checks platform behavior;
a mapped path does not mean every semantic risk is covered. Review docs manually.

```bash
tests/lint.sh            # ShellCheck on every script and ruff on the Python (ruff through uvx at the pinned version when uv is installed)
tests/run-all.sh         # every suite below, in parallel (-j N), with a one-line summary each
tests/validate.sh        # skills, agents, references, budgets, former names, closed docs and local human-doc links/anchors
tests/validate.test.sh   # the validator catches each kind of error
tests/install.test.sh    # installer, in throwaway HOME directories
tests/lifecycle.test.sh  # ownership, previews and safe uninstall
tests/doctor.test.sh     # read-only installation diagnostics
tests/tools.test.sh      # targets.txt columns, `doctor --tools` and the weekly workflow
tests/mods.test.sh       # mods step: install, opt-outs, dry run, uninstall and doctor (fake claude CLI)
tests/vscode.test.sh     # VS Code step: chat.useAgentsMdFile install, opt-out, dry run, uninstall and doctor
claude plugin validate plugins && claude plugin test plugins/usage-band && claude plugin test plugins/agent-activity   # the mods themselves (needs the claude CLI)
tests/mods-unit.sh                    # the mods' unit tests with Node only (esbuild via npx), as CI runs them
tests/hooks.test.sh      # git and Claude Code hooks, in throwaway repos
tests/cli.test.sh        # activation, modes, config, startup context and the help-vs-docs drift check
tests/settings.test.sh   # mixed user and tack hook groups in Python and jq
tests/safety.test.sh     # final index scanning, exact paths and formatter trust
tests/guard.test.sh      # executable shell syntax, boundaries and long inputs
tests/project-capabilities.test.sh # project definitions, references and discovery index
tests/project-setup.test.sh # read-only discovery, minimal scaffold, readiness and remembered review state
tests/project-config.test.sh # shared preferences, clone propagation, local trust, paths and hook consumers
tests/bootstrap.test.sh  # optional pinned installation, consent, existing installs and cache failures
tests/team.test.sh       # branch overlap, isolated merge conflicts and parallel handoff context
tests/sets.test.sh       # set declarations, pinned sources, project links and the installer's set step
tests/pr-policy.test.sh  # offline PR metadata, drafts, project conventions and inert event input
tests/verification.test.sh # path-selected checks, real failure detection, trust, timeouts and Stop integration
tests/native-agents.test.sh # native formats, installation preservation and Gemini/Copilot hook protocols
tests/smoke.test.sh      # portable installation and hook smoke checks
```
CI runs ShellCheck 0.11.0 (pinned by checksum in `.github/workflows/ci.yml`; use the same version locally, as the runner's default one reports different warnings) and content validation on Linux, the installer and hook regression suites on Linux and macOS, and `claude plugin validate`/`test` for each mod on Linux when the claude CLI is available (it skips otherwise). Rules for contributors (bash 3.2, isolated tests…) are in [`AGENTS.md`](../AGENTS.md).

Native Windows CI also checks ownership/restoration, the verifier, shared project configuration and the portable smoke flow. Symlink tests that need unavailable local privileges report an explicit skip. Keep command examples in their owning guide; the CLI drift check searches the current setup, usage, configuration, verification, installation and advanced guides.

## Adding a skill, agent or tool
1. Create `skills/<name>/SKILL.md` or `agents/<name>.md` with `name` and `description` (what it does and when to use it, within the budget `validate.sh` enforces), or add a line to `targets.txt` for a new AI tool.
2. List it in [components](components.md) (the validator requires it); mention it in the README only if it changes what a newcomer needs to know.
3. Run `tests/validate.sh` and `./install.sh`, then commit and push.

## Tools compatibility (weekly)
`.github/workflows/tools-compat.yml` runs every Monday (and on demand from the Actions tab). It installs the latest Claude Code and Codex with npm, runs `./install.sh --skip-plugins` in a temporary HOME and then `tack doctor --tools`. It uses no credentials. A failure means a new tool release changed something the installer relies on: read the log, then adjust `targets.txt` or the installer.
