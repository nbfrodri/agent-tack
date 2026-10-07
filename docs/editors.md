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
| GitHub Copilot (`copilot`; CLI, VS Code Copilot Chat) | ✔ | ✔ | CLI | CLI | — | ✔ |
| Gemini CLI (`gemini`) | ✔ | ✔ | ✔ | ✔ | — | ✔ |
| OpenCode (`opencode`) | ✔ | ✔ | ✔ | — | — | ✔ |
| Crush (`crush`) | ✔ | ✔ | — | — | — | ✔ |
| Cursor (`cursor`; editor and CLI) | manual, once | ✔ | ✔ | command guard only | — | ✔ |

- **Global instructions** carry your preferences and the workflow for enabled projects, including the mode rules.
- **Git hooks** enforce Conventional Commits, no AI attribution, no secrets and protected `main` and tags for every tool, because git runs them whoever commits.
- **Agent hooks** run in Claude Code, Codex, Gemini CLI and Copilot CLI: command guard, startup context, fast check, Stop check and tool-call limit. Gemini/Copilot use a shared protocol adapter and do not get per-file formatting or transcript cost accounting. Cursor receives only the command guard. OpenCode and Crush follow remaining checks as instructions. **Mods** exist only in Claude Code.
- **Shared memory:** the startup adapters for Claude Code, Codex, Gemini CLI and Copilot CLI load your notes from `~/.config/agent-tack/memory.md`, including outside enabled projects, subject to the memory toggle ([usage](usage.md#shared-memory), [ADR 0002](adr/0002-shared-memory.md)). Native tool memory remains separate. Other tools read the file only when asked.
- **Startup context:** registered hooks deliver it in Claude Code, Codex, Gemini CLI and Copilot CLI, including pending project setup. Other tools follow global instructions to run `tack status` and `tack context`; if needed ask them to run those commands. Context and hook toggles still apply.

## Claude Code

- **Terminal:** `claude` in the project. Everything applies: instructions, skills, agents, hooks, mods and the startup context with the mode.
- **VS Code and JetBrains extensions:** they use the same configuration as the CLI (`~/.claude`), so nothing else is needed. Open the project folder, start a Claude Code session and check the startup message names the mode.
- **Mods:** `/usage-band` hides or shows the usage band; `/activity` opens or closes the activity pane. They need a restart after installing.
- **Check:** `tack doctor` (links, settings, hooks, mods) and `tack mode show`.

## Codex

- **Terminal:** `codex` in the project. Reads `~/.codex/AGENTS.md` and the skills in `~/.codex/skills` and `~/.agents/skills`.
- **VS Code extension:** shares the CLI configuration (`~/.codex`), so it receives the same instructions and skills.
- **Models:** delegation uses `gpt-6-luna` for `economical`, `gpt-6.1-sol` for `balanced` and `gpt-6-astra` for `strongest`, following the [current model guidance](https://learn.chatgpt.com/docs/models) checked on 2026-10-07. `tack models` shows the mapping; override it for your account in `~/.config/agent-tack/model-tiers.txt` (`codex strongest <model>`). These choices do not change your main session's model or grant model access.
- **Agents:** the installer generates one Codex agent per tack agent in `~/.codex/agents/<name>.toml`; review-only agents run in a read-only sandbox. A file you already had with the same name is left alone, and a generated file you edit is kept on reinstall and uninstall.
- **Hooks:** the installer registers the command guard, startup context, fast check, check before stopping and tool-call limit in `~/.codex/hooks.json`, next to your own hooks. **Codex runs a hook only after you approve it:** open Codex, run `/hooks` and trust tack hooks once (again after an update changes them). Because Codex cannot ask for confirmation from a hook, everything the guard would ask about is refused with a reason, so the assistant leaves those commands to you; that includes `gh pr merge` when the guard cannot read the pull request's checks. Tack's Codex hooks pass `--codex`, so the opt-in activity log (`tack log`) labels Codex entries.
- Codex's own `/import` can bring chats from Claude Code; skip its configuration import ([usage](usage.md#moving-between-tools-and-machines)).
- **Check:** `tack doctor --tools` (runs `codex doctor --summary`).

## GitHub Copilot

- **Copilot CLI:** `copilot` in the project. Reads `~/.copilot/copilot-instructions.md` and the skills.
- **CLI agents and hooks:** generated `~/.copilot/agents/*.agent.md` and merged `~/.copilot/hooks/tack.json`, following [agent configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration) and [hook protocols](https://docs.github.com/en/copilot/reference/hooks-reference). CLI integration does not establish equivalent native support in VS Code Chat. Custom definitions and hook entries are preserved.
- **Copilot Chat in VS Code:** configured whenever VS Code is installed (`code`, `code-insiders` or `codium`), even without the Copilot CLI. It reads the user instructions in `~/.copilot/copilot-instructions.md` and the skills in `~/.agents/skills`, `~/.claude/skills` and `~/.copilot/skills`.
  - The installer turns on the VS Code setting `chat.useAgentsMdFile` in your user settings, so each project's `AGENTS.md` loads too. It only adds the key when it is absent: an existing value (even `false`) is kept, and a `settings.json` with comments or trailing commas is left untouched with a warning (add `"chat.useAgentsMdFile": true` yourself). Opt out with `tack config vscode-agents-md false --global`; `./uninstall.sh` removes the key only if it still holds the installed value.
  - Use agent mode for tasks that edit files and run commands; the instructions tell it to follow `dev-workflow` in enabled projects.
- **Check:** in Copilot Chat, ask "which instructions are you following?"; the answer should mention tack workflow.

## Cursor

- **One manual step:** Cursor keeps global rules in its settings, not in a file. Copy the contents of `global/AGENTS.md` from your checkout into *Cursor Settings → Rules* (User Rules) once; the installer reminds you. Paste again after updates that change that file.
- **Command guard:** the installer registers `hooks/cursor/guard.sh` for `beforeShellExecution` in `~/.cursor/hooks.json`, next to your own hooks. It translates Cursor's hook format to the shared guard and back, so Cursor refuses or asks about the same commands as Claude Code. The adapter needs `python3`; without it Cursor runs commands unchecked. The other agent hooks (startup context, checks after edits and before stopping) do not run in Cursor yet.
- **Skills and agents:** tool-specific links in `~/.cursor/skills` and generated `~/.cursor/agents/*.md`, following [skills](https://cursor.com/docs/skills) and [subagents](https://cursor.com/docs/subagents). Read-only roles set `readonly: true`; role text preserves more specific restrictions. Tack does not enable cloud sync.
- **`cursor-agent`** (terminal) uses the same rules and skills.
- **Check:** `tack doctor` shows "cursor: detected but not configured by this installation" until you paste the rules; the warning stays because tack cannot see Cursor's settings.

## Gemini CLI, OpenCode and Crush

- **Gemini CLI:** `~/.gemini/GEMINI.md`, `~/.gemini/skills`, native roles in `~/.gemini/agents/*.md`, and hooks in `~/.gemini/settings.json`. [Subagents](https://geminicli.com/docs/core/subagents/) and [hooks](https://geminicli.com/docs/hooks/reference/) have native schemas; tack translates them instead of copying Claude configuration. Guard asks become denials requiring user confirmation.
- **OpenCode:** `~/.config/opencode/AGENTS.md`, `~/.config/opencode/skills` and [native Markdown subagents](https://opencode.ai/docs/agents/) in `~/.config/opencode/agents/`. Tack manages no OpenCode runtime plugin/hooks; global git hooks still apply.
- **Crush:** `~/.config/AGENTS.md` and `~/.config/crush/skills`, as documented in its [official configuration guide](https://github.com/charmbracelet/crush). No verified native agent/hook adapter is installed; use portable role instructions when needed.

They are configured only when installed; rerun `./install.sh` after installing one of them later.

Native adapters and paths were checked against the linked documentation on 2026-10-07. Local tests exercise rendered formats, hook payloads and install/reinstall/uninstall with temporary homes; no paid model sessions were run. Account, version and runtime support still determine which features a tool can use. `-` in targets.txt denotes an unmanaged integration, not a claim that the vendor lacks it.

Project capabilities do not require a native agent adapter. The project's AGENTS.md indexes local skills and portable role definitions; read matching definitions explicitly when native discovery is unavailable. `.agents/agents/` is a tack convention, not a universal editor configuration directory. Existing delegation permissions still govern invocation, and unsupported roles can be followed sequentially. See [project capabilities](customization.md#project-capabilities).

## Windows


- **WSL2 is the supported path** (below). Native Windows is not supported yet: tack is bash scripts, symlinks and bash git hooks.
- **Native Windows with Git Bash (experimental):** the checkout keeps LF endings and holds no symlinks. CI runs the validator, native ownership/ACL regressions and the install/reinstall/doctor/hooks/guard/uninstall flow on `windows-latest` (`tests/ownership-platform.test.sh`, `tests/smoke.test.sh`). The AI tools themselves are not exercised. `./install.sh` needs native Python 3, Windows PowerShell and symlinks: turn on Developer Mode (*Settings > System > For developers*), or the installer stops before changing anything. Most suites need Linux or macOS; on Windows run those in a container, for example from PowerShell: `docker run --rm -v "${PWD}:/src:ro" ubuntu:24.04 bash -c 'apt-get update -qq && apt-get install -yqq git jq python3 >/dev/null && git clone -q /src /w && cd /w && tests/run-all.sh'`.
- **Windows restoration privacy:** new ownership metadata uses a private DACL; doctor and uninstall reject exposed metadata or junction redirection. Older private records retain MSYS identity checks. An older displaced symlink without its original Windows file/directory type is preserved for manual recovery, as is any edited file or replaced parent. Uninstall does not relax an unsafe legacy ACL or delete its records. See [ownership and diagnostics](architecture.md#installation-ownership-and-diagnostics).
- **WSL2 is supported:** clone into the Linux file system (for example `~/Projects`, not `/mnt/c`), install the AI CLIs inside WSL and run `./install.sh` there.
- **VS Code on Windows:** open the project with the **WSL** extension (*Remote: Open Folder in WSL*), so the Claude Code, Codex and Copilot extensions run inside WSL and read the configuration tack installed there. Not verified on a Windows machine yet; check with `tack doctor --tools` inside WSL and the per-tool checks above.
- **Cursor on Windows** also supports opening WSL folders; paste the rules once as above.

## Other editors and tools

Any tool that reads a project's `AGENTS.md` gets the project's instructions. To give a new tool your global instructions and skills, add one line to `targets.txt` with its paths and rerun `./install.sh` ([customization](customization.md)).
