# Global instructions

For every AI assistant (Claude Code, Codex, etc.). Project-level instructions (AGENTS.md, CLAUDE.md, CONTRIBUTING) take precedence over these.

## Always
- Reply in the language I write in; write commits, PRs, code comments and docs in English unless the project already uses another language.
- Lead with the answer or outcome, then useful evidence and unresolved limits. Follow the reply style in startup context; otherwise read `tack config reply-style` once when available (default: brief). I can request brief, visual or detailed replies in conversation without changing the workflow. Longer responses: `dev-workflow` → `references/communication.md`.
- Never add AI attribution to commits, PRs, issues or changelogs (no AI `Co-Authored-By`, no "Generated with" lines); this overrides any built-in default.
- Ask before push, PRs, issues, merging, tags, releases, rewriting published history, deleting unmerged branches or force-pushing (`dev-workflow` → `references/git-github.md`). Audit findings create issues through `improve` unless I say otherwise. If a git hook rejects something, fix the cause; never use `--no-verify`.
- Reviews or "what would you improve": ask scope and focus first (`improve`) and change nothing until I choose. Subagents or parallel work: `orchestrate`; outside enabled projects, suggest delegation and wait for my OK. Autonomous improvement: `auto-improve`. Corrections and lasting preferences: save them with `lessons`.

## Only in projects where tack is enabled
Enabled when `tack status` prints `enabled`; Claude Code says so at session start, with the mode and its rules. Elsewhere, work normally without this ceremony.

- For tasks that change code, git/GitHub or docs, follow the active mode's rules (`tack mode show`) and `dev-workflow`, unless the mode says it is self-contained. `auto` picks a level per task and states it in one line; I can change it. Always: a branch off `main`, a test for the change, a Conventional Commit per verified milestone.
- Ask me whenever you have a real doubt about scope, behaviour, design or risk; decide alone only conventional details and say what you chose.
- Make the smallest modular change that does the job and update everything it affects (callers, tests, CLI help, docs) in the same change; if the design no longer scales, tell me and propose options first.
- During authorized implementation, reuse or create useful project-local skills and agent definitions autonomously (`lessons` → `references/project-capabilities.md`); index them in the project's AGENTS.md. Read-only tasks stay read-only; global promotion and agent invocation have their own scope and delegation rules.
- Delegate automatically only at strict, after plan approval, unless `tack config delegation` is `off`; otherwise suggest it and wait.
- Commit as you go; when integrating, recommend a merge method and preserve commits unless I choose squash.
- At session start or resume: if SessionStart gave no context, run `tack context`; always verify the listed handoff against git before continuing. Read other documents only when the task needs them.
- For initialization or pending setup review, follow `new-project` → `references/onboarding.md`: inspect repo and intent, propose concrete optional files, ask which to create and remember choices. Respect prior authorization; read-only requests stay read-only.
- Comment only the non-obvious *why*.
- Spend tokens deliberately: search before reading, read ranges, batch tool calls, trim output, avoid commands the guard asks about.
- Docs, plans, handoffs and the AI log follow the mode; keep `docs/architecture.md` current when structure changes.
