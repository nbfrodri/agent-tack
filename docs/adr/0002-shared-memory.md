# 0002: Shared user memory for Claude Code and Codex

- Status: accepted (2026-10-05, #44)

## Context
Handoffs in `docs/handoffs/` reach any assistant that reads the repository, and rules reach every tool through `global/AGENTS.md` and skills. User-level memory does not: Claude Code keeps its own project memory and Codex its own state, so switching tools loses lasting notes that are neither project content nor rules (the user's machine and accounts, an unconfirmed preference, ongoing personal context).

## Decision
- **Format:** one Markdown file, `# Memory`, a one-line header and one dated bullet per note (`- YYYY-MM-DD: text`), newest first. People can read and edit it with any editor. Only lines starting with `- ` are notes; other text is kept but not loaded.
- **Location:** `${XDG_CONFIG_HOME:-~/.config}/agent-tack/memory.md`, next to the user's modes and guard rules, outside every repository, mode 600. It is configuration the user owns, not state tack may prune.
- **Writing:** `tack memory add TEXT` (used by the `lessons` skill for notes that are not rules, after the user approves the exact text), or editing the file. Removing a note is editing the file. A lock directory serialises two tools adding at once, and a symlinked file (kept in a dotfiles repository) is written through.
- **Reading:** the SessionStart hook that Claude Code and Codex both run (`session-context.sh`, `--codex` for Codex) adds `tack memory context` in every project, enabled or not, labelled as the user's notes rather than rules.
- **Size cap:** `memory-max-chars` (default 2000) keeps whole notes from the top, so the newest survive, shortens a single overlong first note instead of dropping everything, and says where the rest is; under `context-max-chars` the memory comes after the mode rules and settings and before the project context.
- **Never stored:** credentials and personal data of other people. `tack memory add` refuses text that looks like a private key, a cloud or GitHub token, an API key or a `password=`-style assignment; the file is loaded into every session of every tool, so anything in it is visible to every model the user runs.
- **Off switch:** `tack config memory false --global`.

- **Prompt injection:** a note is loaded into every session of every project, so a note written on a repository's or a web page's behalf would persist everywhere. The block is framed as information about the user, never as instructions that override the user or the rules, and the `lessons` skill adds a note only after the user approves its exact text. The guard does not ask about `tack memory add`, because Codex would then refuse every add; the approval rule is an instruction, not enforcement.

## Consequences
- Both tools start with the same notes, and a note written in one is read by the other at its next session start.
- Each tool's own memory still exists; tack does not import or sync it. The shared file is for what should cross tools.
- Other tools (Copilot, Gemini, OpenCode, Crush, Cursor) have no session-start hook in tack and do not load it; they can read the file when asked.
