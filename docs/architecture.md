# Architecture

How the repository's components fit together, from installation to an agent session or a git operation. Supported tools and installed paths are listed in [how it works](how-it-works.md).

## Context and installation

Tack is a local collection of instructions and scripts. AI tools read its installed configuration; git and Claude Code invoke its executable hooks.

```mermaid
flowchart LR
  owner[Repository owner] --> installer[install.sh]
  data[targets.txt and plugins.txt] --> installer
  config[Global instructions, skills and agents] --> installer
  installer --> links[Symlinks in the user's home]
  links --> tools[AI tools]
  installer --> merge[lib/settings-merge.py or .jq]
  merge --> settings[Claude Code settings]
  installer --> gitconfig[Global git core.hooksPath]
  installer --> plugins[Claude plugin CLI]
  installer --> mods[lib/mods.sh]
  mods --> plugins
  mods --> modsrc[plugins/ local marketplace]
  installer --> vscode[lib/vscode.sh]
  vscode --> vscodesettings[VS Code user settings.json]
```

`install.sh` configures tools, links content, merges settings, installs git hooks, updates plugins, installs mods and enables VS Code's AGENTS.md loading in that order. It counts failures while continuing other steps, then exits non-zero if any step failed. Links point to the checkout, so its location must remain available; re-running the installer repairs links after a move.

## Components and dependency direction

| Component | Responsibility | Dependencies |
| --- | --- | --- |
| `global/AGENTS.md` | Always-on preferences and the workflow for enabled projects | Skills for detailed instructions |
| `skills/` | Task-specific procedures, references and reusable assets | Global preferences and project conventions |
| `agents/` | Role-specific instructions for planning, implementation and review | Skills; native definitions where supported, otherwise role instructions for the current runtime |
| `targets.txt`, `plugins.txt` | Declare supported tools and Claude plugins | Read by the installer |
| `plugins/`, `lib/mods.sh` | Claude Code mods (`usage-band`, `agent-activity`) in a local marketplace; the installer step adds the marketplace (re-adding it when it points to a former checkout path), installs each mod and records only what it installed; doctor reports their state | Claude CLI (`claude plugin ...`), `lib/ownership.sh`; opt-outs `--skip-mods` and `tack.mods` |
| `lib/vscode.sh`, `lib/vscode_settings.py` | Detect VS Code (`code`, `code-insiders`, `codium`), add `chat.useAgentsMdFile: true` to its user settings only when the file is absent or plain JSON and the key is unset, and record that (`vscode` ownership entry holding whether the file was created); doctor reports the state; `ownership.py` removes the key on uninstall only while it still holds the installed value | Python standard library, `lib/ownership.sh`; opt-out `tack.vscodeAgentsMd` |
| `install.sh` | Orchestrate installation and migration; skip every hook with `--no-hooks`; after a first install, explain the hooks from `hooks/summary.txt` | Data files, settings merge, git and Claude CLI |
| `lib/ownership.sh`, `lib/ownership.py`, `uninstall.sh` | Record private installation ownership and restore unchanged managed state without removing project files or shared plugins | Bash records and Python standard library validation/restoration |
| `lib/doctor.sh` | Diagnose managed links, settings, ownership, Git hooks and project state without writes | Installer data, private metadata, Git and `bin/tack` queries |
| `lib/settings-merge.py`, `.jq` | Merge settings and replace tack-tagged (and former harness-tagged) commands while preserving user commands and group metadata | Python standard library or jq |
| `bin/tack` | Manage activation, workflow mode and local formatter trust; provide bounded startup context | Git repository root and configuration; `lib/project-context.sh`, `lib/config.sh` and `lib/doctor.sh` |
| `codex/hooks.json`, `lib/codex.sh`, `lib/codex_agents.py` | Register the shared hooks in Codex (the guard runs with `--codex`, turning asks into denials because Codex runs a command when a hook asks) and generate Codex agents from `agents/*.md`, recorded as generated files with checksums | `install.sh`, the settings merge and the ownership records |
| `modes/`, `lib/modes.sh` | Define each workflow mode as data; resolve, list, create and show modes (built-in first, then the user's `~/.config/agent-tack/modes/`) | Sourced by `bin/tack`; read by SessionStart through `tack mode show` |
| `features.txt`, `lib/config.sh` | Declare feature toggles; list, validate, read and write them for `tack config` (project value, then global, then default) | Git configuration; consumers read each toggle's git key |
| `git-hooks/` | Check staged secrets, commit messages and pushed refs; delegate local hooks | `bin/tack`, git and `_chain` |
| `hooks/claude/` | Supply session context, assess Bash commands (including CI checks before `gh pr merge`), limit autonomous tool calls, format edited files, run the opt-in fast check, review unfinished work before stopping and append to the opt-in activity log | `bin/tack`; the guard sources `lib/shell-parse.sh`, which uses its Python parser when available, and calls `gh pr checks` for merges; `lib/activity-log.sh` writes `activity.log` in the state directory, with per-turn metrics from `lib/turn-report.py` (Python, Claude Code and Codex transcript formats); `tack log` reads it, and `lib/log-report.py` (repo root) builds its reports |
| `tests/`, `.github/workflows/ci.yml` | Validate content and exercise installation and hooks in temporary environments | Bash, git, Python, jq and ShellCheck |
| `evals/` | Run agent scenarios, grade artifacts and transcripts, and aggregate results | Claude or Codex CLI; grading also runs `uv run pytest` |

The installer does not implement hook policy. Git hooks share only their local-hook delegation library; Claude's shell parser tokenizes commands and its guard decides what to deny or ask about: structural rules in `guard-bash.sh`, pattern rules as data in `hooks/claude/guard-policy.txt`, plus optional user rules in `${XDG_CONFIG_HOME:-~/.config}/agent-tack/guard-policy.txt` that can only add ask or deny decisions. A missing shipped policy makes every command ask for review. Explicit local data-loss asks are recorded separately (`ask_local`); only an enabled project in a project-only mode (`Scope: project`, such as `unleash`) waives them, which the guard learns from `tack mode show`, and never for a command that changes directory or points git at another repository. In that mode the guard also refuses writes to tack's own settings (`tack config`, `mode`, `trust`, `enable`, `disable`, `git config tack.*` and the former `harness.*`). Every deny rule and every other ask applies in all modes.

The shell parser uses Python's standard library for bounded lexical analysis and communicates with Bash through NUL-delimited records. A conservative Bash fallback handles short commands when Python is unavailable. Unsupported executable constructs and exceeded limits request review rather than being silently skipped.

## Installation ownership and diagnostics

`install.sh --dry-run` reports intended operations without changing HOME, Git configuration, checkout permissions or plugin state. Applying changes records private versioned ownership evidence through `lib/ownership.sh`: destination, installed target/value, original state, installation-time tool declarations and physical parent path/device/inode identity. Private declaration snapshots keep historical destinations valid after customization; missing Git paths migrate only with recorded or canonical-link evidence. The first baseline survives reinstallations; already-identical legacy configuration is not newly claimed.

`uninstall.sh` delegates validation and selective restoration to `lib/ownership.py`. It checks the manifest before mutation, restores only unchanged recorded state, preserves user edits and changed parents, and retains incomplete records for retry. JSON snapshots remain local and private. It requires Python even when installation used the jq merge fallback. Neither uninstall nor doctor removes project data. Uninstall invokes `claude plugin uninstall` and `claude plugin marketplace remove` only for the mods and local marketplace the installer recorded (`mod` and `modmarket` ownership entries, which hold a plugin id or marketplace name instead of a snapshot); the marketplace is kept if any of its mods could not be removed. Plugins from `plugins.txt` are never removed.

`tack doctor --tools` runs the same script in tools mode: for each tool in `targets.txt` it detects the version, lists declared capabilities, compares the minimum version and runs the optional smoke check, discarding the tool's output. `.github/workflows/tools-compat.yml` runs it weekly against the latest Claude Code and Codex.

`tack doctor` delegates to `lib/doctor.sh` and uses `targets.txt`, installed configuration and ownership metadata to diagnose managed components. Deliberate foreign Git hooks and missing optional tools are warnings; broken managed components are errors. Project checks query the CLI's existing activation/trust predicates. Diagnostics read metadata structure, not private restoration snapshot contents for display.

## Project activation and sessions

```mermaid
flowchart LR
  project[Project git config or shared .tack marker] --> status[bin/tack status]
  status --> session[Claude session context]
  mode[Local or global tack.mode] --> session
  status --> gitpolicy[Conditional git checks]
  status --> formatter[Claude file formatter]
  preferences[Global instructions] --> workflow[Agent workflow and skills]
  session --> workflow
```

`bin/tack` is the source of truth for activation. An explicit `tack.enabled=false` wins; otherwise `true` enables the workflow, followed by a shared `.tack` file. Hooks call the CLI rather than reading these markers themselves. Formatter execution additionally requires `tack trusted --quiet`, which reads only local trust configuration. Claude receives activation, the effective mode and `tack context` excerpts at session start, and again after context compaction because the SessionStart hook has no matcher; other tools follow the instructions to run the same commands.

`tack mode` resolves the workflow mode: a local `tack.mode` wins over the global default, and a missing or invalid value means `auto`. The mode selects the `dev-workflow` level (lite, standard or strict) or, in `auto`, asks the assistant to pick one per task. Levels scale plans, handoffs, the AI log, reviews and delegation; hooks enforce the same checks at every level.

Human-readable `tack status` reports activation and local formatter trust together. Its exit code, including `--quiet`, depends only on activation. `tack trusted` and its quiet mode depend only on local trust; both commands share the same trust predicate.

`lib/project-context.sh` reads a bounded excerpt of project instructions and, depending on the mode, only the active handoff's status and next step (`lite`), an index of `docs/architecture.md` plus that handoff summary (`auto`, `standard`), or bounded excerpts of both (`strict`). A handoff check compares the handoff's modification or last commit time with later commits and its `Branch:` line with the current branch. The agent reads indexed documents in full only when the task needs them. It has a shared byte budget and per-file line limits and skips missing files and external symlinks. `tack.context=false` disables these extra excerpts.

In enabled projects, `skills/orchestrate/` routes complex independent strict-level tasks to available models and effort settings under an approved plan; at lite and standard it only suggests delegation. `tack.delegation=off` opts out of automatic delegation; missing/auto uses it. Capability detection and sequential fallbacks avoid promises that the current runtime cannot fulfil.

Instructions guide the model's workflow. Executable hooks enforce a narrower set of checks: secret scanning and attribution removal apply in every repository using the global git hooks; Conventional Commits and tag conventions depend on activation. Claude's command guard runs independently of activation, while file formatting requires an enabled and locally trusted project.

## Git hook flow

Global `core.hooksPath` points to this checkout's `git-hooks/`. A repository with its own configured `core.hooksPath` uses that path instead.

| Entry point | Current execution order |
| --- | --- |
| `pre-commit` | Run the local hook, then inspect exact staged paths and added lines in the final index for secrets; inspection errors block the commit |
| `commit-msg` | Remove attribution, validate the subject when enabled, then invoke the local commit-msg hook |
| `pre-push` | Buffer stdin, check protected refs and enabled tag conventions, then forward the original stdin to the local pre-push hook |
| Other hook names | Symlink to `_chain`, which delegates to the matching local hook |

`_chain` locates local hooks through git's common directory, including bare repositories and worktrees. It preserves arguments and stdin and prevents recursion through an environment flag and file-identity check. A failing local hook propagates its exit status.

## Verification and evaluations

CI runs ShellCheck and content validation on Linux, plus installer and hook tests on Linux and macOS. Tests use temporary homes and repositories so installation and git operations stay isolated.

Behaviour evaluations are a separate, manually invoked flow: `evals/run.sh` prepares a temporary scenario and captures an agent transcript; `grade.py` inspects the resulting repository and transcript and writes `metrics.json`; `report.py` aggregates those metrics. They use real model tokens and are not part of CI. Published measurements and their limits are in [results](results.md).

## Design choices

- Store shared configuration in one versioned checkout and expose it through symlinks, so edits apply locally without copying content into each tool.
- Add tool and plugin support through data files; use skills and agent files to extend procedures and roles.
- Keep project activation in one CLI and preserve always-on safety checks when the full workflow is disabled.
- Preserve independent user settings and local hook integration rather than replacing a repository's workflow wholesale.
- Keep executable scripts compatible with Bash 3.2, and provide Python and jq settings-merge implementations for portability.
