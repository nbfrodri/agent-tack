# Editors and AI tools

How to use tack with each AI tool, in the terminal and in editors. Install once with `./install.sh` from your checkout ([README](../README.md#install)); the installer configures every supported tool it finds and skips the rest. Then, in each project where you want the workflow:

```bash
tack enable            # this clone (or --shared to commit a .tack marker)
tack mode              # auto by default; see usage.md for lite, standard, strict, unleash
tack doctor --tools    # which tools are installed and what each one received
```

Restart the tool or editor after installing or updating so it reloads instructions and skills.

## What each tool receives

| Tool | Global instructions | Skills | Agents | Agent hooks | Mods | Git hooks |
| --- | --- | --- | --- | --- | --- | --- |
| Claude Code (`claude`; CLI, VS Code, JetBrains) | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Codex (`codex`; CLI, VS Code) | ✔ | ✔ | ✔ | ✔ (approve once with `/hooks`) | — | ✔ |
| GitHub Copilot (`copilot`; CLI, VS Code Copilot Chat) | ✔ | ✔ | — | — | — | ✔ |
| Gemini CLI (`gemini`) | ✔ | ✔ | — | — | — | ✔ |
| OpenCode (`opencode`) | ✔ | ✔ | — | — | — | ✔ |
| Crush (`crush`) | ✔ | ✔ | — | — | — | ✔ |
| Cursor (`cursor`; editor and `cursor-agent`) | manual, once | ✔ | — | command guard only | — | ✔ |

- **Global instructions** carry your preferences and the workflow for enabled projects, including the mode rules.
- **Git hooks** enforce Conventional Commits, no AI attribution, no secrets and protected `main` and tags for every tool, because git runs them whoever commits.
- **Agent hooks** (command guard with green-only merges, startup context, fast check, check before stopping, tool-call limit, opt-in activity log) run in Claude Code and Codex; Cursor gets the command guard through a thin adapter (`hooks/cursor/guard.sh`) registered in `~/.cursor/hooks.json`. **Mods** (usage band, activity pane) exist only in Claude Code. Other tools follow the same rules as instructions, without enforcement.
- **Shared memory:** Claude Code and Codex both load your notes from `~/.config/agent-tack/memory.md` at session start, in every project, so switching between them keeps what you told one ([usage](usage.md#shared-memory), [ADR 0002](adr/0002-shared-memory.md)). Each keeps its own memory as well; other tools read the file only when asked.
- **Startup context:** Claude Code receives it automatically. Other tools are told by the global instructions to run `tack status` and `tack context` at the start of a session; if a tool skips it, ask it to ("run tack context").

## Claude Code

- **Terminal:** `claude` in the project. Everything applies: instructions, skills, agents, hooks, mods and the startup context with the mode.
- **VS Code and JetBrains extensions:** they use the same configuration as the CLI (`~/.claude`), so nothing else is needed. Open the project folder, start a Claude Code session and check the startup message names the mode.
- **Mods:** `/usage-band` hides or shows the usage band; `/activity` opens or closes the activity pane. They need a restart after installing.
- **Check:** `tack doctor` (links, settings, hooks, mods) and `tack mode show`.

## Codex

- **Terminal:** `codex` in the project. Reads `~/.codex/AGENTS.md` and the skills in `~/.codex/skills` and `~/.agents/skills`.
- **VS Code extension:** shares the CLI configuration (`~/.codex`), so it receives the same instructions and skills.
- **Models:** delegation picks a tier (`economical`, `balanced`, `strongest`); Codex's tiers say `inherit` in `model-tiers.txt` until you name your account's models in `~/.config/agent-tack/model-tiers.txt` (`codex strongest <model>`); `tack models` shows the result.
- **Agents:** the installer generates one Codex agent per tack agent in `~/.codex/agents/<name>.toml`; review-only agents run in a read-only sandbox. A file you already had with the same name is left alone, and a generated file you edit is kept on reinstall and uninstall.
- **Hooks:** the installer registers the command guard, startup context, fast check, check before stopping and tool-call limit in `~/.codex/hooks.json`, next to your own hooks. **Codex runs a hook only after you approve it:** open Codex, run `/hooks` and trust tack hooks once (again after an update changes them). Because Codex cannot ask for confirmation from a hook, everything the guard would ask about is refused with a reason, so the assistant leaves those commands to you; that includes `gh pr merge` when the guard cannot read the pull request's checks. Tack's Codex hooks pass `--codex`, so the opt-in activity log (`tack log`) labels Codex entries.
- Codex's own `/import` can bring chats from Claude Code; skip its configuration import ([usage](usage.md#moving-between-tools-and-machines)).
- **Check:** `tack doctor --tools` (runs `codex doctor --summary`).

## GitHub Copilot

- **Copilot CLI:** `copilot` in the project. Reads `~/.copilot/copilot-instructions.md` and the skills.
- **Copilot Chat in VS Code:** configured whenever VS Code is installed (`code`, `code-insiders` or `codium`), even without the Copilot CLI. It reads the user instructions in `~/.copilot/copilot-instructions.md` and the skills in `~/.agents/skills`, `~/.claude/skills` and `~/.copilot/skills`.
  - The installer turns on the VS Code setting `chat.useAgentsMdFile` in your user settings, so each project's `AGENTS.md` loads too. It only adds the key when it is absent: an existing value (even `false`) is kept, and a `settings.json` with comments or trailing commas is left untouched with a warning (add `"chat.useAgentsMdFile": true` yourself). Opt out with `tack config vscode-agents-md false --global`; `./uninstall.sh` removes the key only if it still holds the installed value.
  - Use agent mode for tasks that edit files and run commands; the instructions tell it to follow `dev-workflow` in enabled projects.
- **Check:** in Copilot Chat, ask "which instructions are you following?"; the answer should mention tack workflow.

## Cursor

- **One manual step:** Cursor keeps global rules in its settings, not in a file. Copy the contents of `global/AGENTS.md` from your checkout into *Cursor Settings → Rules* (User Rules) once; the installer reminds you. Paste again after updates that change that file.
- **Command guard:** the installer registers `hooks/cursor/guard.sh` for `beforeShellExecution` in `~/.cursor/hooks.json`, next to your own hooks. It translates Cursor's hook format to the shared guard and back, so Cursor refuses or asks about the same commands as Claude Code. The adapter needs `python3`; without it Cursor runs commands unchecked. The other agent hooks (startup context, checks after edits and before stopping) do not run in Cursor yet.
- **Skills:** from `~/.agents/skills`.
- **`cursor-agent`** (terminal) uses the same rules and skills.
- **Check:** `tack doctor` shows "cursor: detected but not configured by this installation" until you paste the rules; the warning stays because tack cannot see Cursor's settings.

## Gemini CLI, OpenCode and Crush

- **Gemini CLI:** `~/.gemini/GEMINI.md` and `~/.agents/skills`.
- **OpenCode:** `~/.config/opencode/AGENTS.md` and `~/.agents/skills`.
- **Crush:** `~/.config/AGENTS.md` and `~/.agents/skills`.

They are configured only when installed; rerun `./install.sh` after installing one of them later.

## Windows

- **WSL2 is the supported path** (below). Native Windows is not supported yet: tack is bash scripts, symlinks and bash git hooks.
- **Native Windows with Git Bash (experimental, not verified end to end):** the checkout keeps LF endings and holds no symlinks, so git hooks run and `tests/validate.sh` passes there. `./install.sh` needs symlinks: turn on Developer Mode (*Settings > System > For developers*), or the installer stops before changing anything. The test suites need Linux or macOS; on Windows run them in a container, for example from PowerShell: `docker run --rm -v "${PWD}:/src:ro" ubuntu:24.04 bash -c 'apt-get update -qq && apt-get install -yqq git jq python3 >/dev/null && git clone -q /src /w && cd /w && tests/run-all.sh'`.
- **WSL2 is supported:** clone into the Linux file system (for example `~/Projects`, not `/mnt/c`), install the AI CLIs inside WSL and run `./install.sh` there.
- **VS Code on Windows:** open the project with the **WSL** extension (*Remote: Open Folder in WSL*), so the Claude Code, Codex and Copilot extensions run inside WSL and read the configuration tack installed there. Not verified on a Windows machine yet; check with `tack doctor --tools` inside WSL and the per-tool checks above.
- **Cursor on Windows** also supports opening WSL folders; paste the rules once as above.

## Other editors and tools

Any tool that reads a project's `AGENTS.md` gets the project's instructions. To give a new tool your global instructions and skills, add one line to `targets.txt` with its paths and rerun `./install.sh` ([customization](customization.md)).
