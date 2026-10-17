---
name: cross-delegate
description: Hand a bounded task to the other installed assistant (Codex from Claude, Claude from Codex) through its non-interactive CLI and read back only a short report, so the long work stays out of your context. Use for wide code reading, mechanical multi-file edits or an independent review when `cross-delegation` allows it.
---

# Cross-delegate

The other assistant does the long work in its own context and returns a short, fixed-shape report; you read the report and the diff, not its transcript. `orchestrate` covers subagents inside one tool; this covers a second tool.

## 1. Gate

1. `tack config cross-delegation --get`: `off` means work directly; `one-way` means only the assistant the user opened delegates; `both` also lets the delegate hand work back. An explicit user request authorises one delegation even when it is `off`.
   In an enabled project, delegate on your own only at the strict and unleash workflow levels (`dev-workflow`); at lite and standard, suggest it in one line and wait. Outside enabled projects, suggest and wait. Run Codex with a sandbox (`-s`), never with `--dangerously-bypass-approvals-and-sandbox`.
2. The other CLI must be on PATH (`command -v codex` or `command -v claude`); otherwise work directly and say so.
3. A prompt that starts "You are a delegate" is a delegated session: do the task yourself and delegate nothing onward.
4. Delegate only work that pays back the handoff: wide reading, mechanical edits across files, a second-opinion review. Keep auth, payments, untrusted-input code and small or tightly coupled tasks with you.

## 2. Prepare

- Choose the tier by the `orchestrate` table and read the other tool's model with `tack models TIER`.
- Writing tasks run in their own worktree and branch, as in `orchestrate` section 2; read-only tasks (review, research) use `-s read-only`.
- The prompt is self-contained: goal, acceptance criteria, files it owns, the project's `AGENTS.md`, and the first line `You are a delegate: complete this task yourself and reply in the report shape.`

## 3. Run Codex

```
codex exec --json -m MODEL -s workspace-write -C WORKTREE \
  --output-schema SKILL_DIR/references/report-schema.json -o REPORT.json "PROMPT" </dev/null > EVENTS.jsonl
```

- `-s read-only` for review and research. `</dev/null` stops Codex waiting for stdin.
- Read REPORT.json (verdict, summary, files, tests, blockers). Take the session id from the first line of EVENTS.jsonl (`thread_id`) and ignore the rest of that file.
- Follow-ups continue the same session, so its context stays on its side: `codex exec resume SESSION_ID -o REPORT.json "FOLLOW-UP" </dev/null >/dev/null`.

## 4. Run Claude (from Codex)

`claude -p "PROMPT" --model MODEL --output-format json` prints a JSON result whose `session_id` identifies the session; continue with `claude -p "FOLLOW-UP" --resume SESSION_ID --output-format json`. Ask for the same report fields in the prompt.

## 5. Verify

A report is a claim. Check the branch: diff, commits (Conventional Commits) and the tests the report names, then run the project's checks yourself before relying on the work. If the report is empty, off-shape or contradicts the diff, retry once with a clearer prompt, then do the work directly.
