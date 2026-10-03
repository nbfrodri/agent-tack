# AI work log

Newest first. One row per significant AI-assisted task.

| Date | Tool | Task | Outcome | Human review |
| --- | --- | --- | --- | --- |
| 2026-10-03 | Codex | Publish audit fixes and mark resolved issues | Published `fix/audit-hardening-and-session-context`; issues #13–#24 verified closed as completed, with fix commit links and test evidence; [audit](../audits/2026-10-03-improvement-agent-harness.md) updated | Owner explicitly requested push and issue completion; integration into main remains pending |
| 2026-10-03 | Codex with three subagents | Execute audit hardening plan; automatic startup context and audit issues | [Completed plan](../plans/2026-10-03-audit-hardening-and-context.md); ten findings corrected; issues #13–#24 created; ShellCheck, validation and 426 automated checks passed; local commits, no push or PR | Owner authorised implementation, subagents, issues and incremental commits; final publication remains pending |
| 2026-10-03 | Codex | Whole-project audit; English content, installation paths, architecture and customization docs | [Audit](../audits/2026-10-03-improvement-agent-harness.md); architecture and customization documented; harness requires architecture docs; 275 tests and ShellCheck passed | Owner chose audit scope and priorities and requested the documentation changes |
| 2026-10-03 | Claude Code | Renamed to agent-harness, support for 7 AI tools, auto-improve, benchmark with vs without the harness, docs split into `docs/` | `54db771`…; [results](../results.md) | Owner chose names, tools, defaults and benchmark size |
| 2026-10-03 | Claude Code, with 4 read-only reviewer subagents | Improvement audit of the whole repo and fixes for all findings | [Audit](../audits/2026-10-03-improvement-agent-config.md); issues #2–#12 closed by `f2221d7`…`6092f75` | User chose scope, focus areas and what to fix |
| 2026-10-03 | Claude Code | Per-project switch (`agent-config enable`), release and tag convention, repo moved to ~/Projects | `3722357`, `8f1c1de`, `bd5185a` | Decisions taken by the user through questions |
