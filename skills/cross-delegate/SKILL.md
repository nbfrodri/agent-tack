---
name: cross-delegate
description: Hand a bounded task to the other installed assistant (Codex from Claude, Claude from Codex) through its non-interactive CLI and read back only a short report, so the long work stays out of your context. Use for wide code reading, mechanical multi-file edits or an independent review when `cross-delegation` allows it.
---

# Cross-delegate

The other assistant does the long work in its own context and returns a short, fixed-shape report; you read the report and the diff, not its transcript. `orchestrate` covers subagents inside one tool; this covers a second tool.

## 1. Gate

1. `tack config cross-delegation --get`: `off` means work directly; `one-way` means only the assistant the user opened delegates; `both` also lets the delegate hand work back. An explicit user request authorises one delegation even when it is `off`.
   In an enabled project, delegate on your own only at the strict and unleash workflow levels (`dev-workflow`); at lite and standard, suggest it in one line and wait. Outside enabled projects, suggest and wait. A message from tack that the 5-hour or weekly usage is high is such a suggestion: offer it in one line, and the user's yes authorises it. Run Codex with a sandbox (`-s`), never with `--dangerously-bypass-approvals-and-sandbox`.
2. The other CLI must be on PATH (`command -v codex` or `command -v claude`); otherwise work directly and say so.
3. A prompt that starts "You are a delegate" is a delegated session: do the task yourself and delegate nothing onward.
4. Delegate only work that pays back the handoff: wide reading, mechanical edits across files, a second-opinion review. Keep auth, payments, untrusted-input code and small or tightly coupled tasks with you.

## 2. Prepare

- Offer the user two or three tier options and recommend one by the `orchestrate` table; read the other tool's model with `tack models TIER`. The user's pick sets the tier and effort, unless they already stated a policy for this task.
- Effort follows that table: economical → low, balanced → medium, strongest → high. Bump the recommended tier and effort one level (up to strongest/high) for unclear requirements, missing tests or costly mistakes.
- Writing tasks run in their own worktree and branch, as in `orchestrate` section 2; read-only tasks (review, research) use `-s read-only`.
- The prompt is self-contained: goal, acceptance criteria, files it owns, the project's `AGENTS.md`, and the first line `You are a delegate: complete this task yourself and reply in the report shape.`
- When the task touches tack commands, name the `tack` skill in the prompt; the `core` set links it for Codex.

### Delegation record

For writing tasks in enabled projects, keep an entry in the active project handoff so another session can recover if the delegating assistant hits its own usage limit or is closed. Read-only tasks (review, research) need no entry.

- Before running Codex, find the active handoff under the directory printed by `tack config handoffs-path --get`; if none is active, create `YYYY-MM-DD-slug.md` with today's date, following the `project-docs` handoff format. Record the date, task in one line, branch, worktree path, announced model and effort, events and report file paths, and expected return.
- When the run ends, add the session id from the first events line (`thread_id`) and outcome: `done and verified`, `done and unverified`, `stopped (usage limit or failure)`, or `discarded`. Update it after verification; remove the entry once the work is integrated and verified.
- On startup with a delegation entry, read the report if it exists and run `git status --short` and `git diff --stat` in the recorded worktree. Recover the session id from the first events line if needed, then verify and integrate, resume from that worktree with the command in section 3, or discard per section 5; never merge unverified work.

## 3. Run Codex

Before running, tell the user: `Delegating to Codex: MODEL, effort LEVEL (tier TIER): REASON`.

```
codex exec --json -m MODEL -c model_reasoning_effort='"LEVEL"' -s workspace-write -C WORKTREE \
  --output-schema SKILL_DIR/references/report-schema.json -o REPORT.json "PROMPT" </dev/null > EVENTS.jsonl
```

- `-s read-only` for review and research. `</dev/null` stops Codex waiting for stdin.
- Read REPORT.json (verdict, summary, files, tests, blockers). Take the session id from the first line of EVENTS.jsonl (`thread_id`); inspect the last events if the run did not finish (section 5).
- Run `tack codex-used SESSION_ID`; report the recorded model and effort next to the summary, explicitly noting any difference from the request. If unavailable, say the actual settings could not be verified.
- Follow-ups continue the same session, with the same explicit selection and announce/report rule: `cd WORKTREE && codex exec resume SESSION_ID -m MODEL -c model_reasoning_effort='"LEVEL"' -o REPORT.json "FOLLOW-UP" </dev/null >/dev/null`.

`codex exec resume` has no `-C` option and runs in the calling shell's directory, not the original session's, so a resume launched from the main checkout works there.

## 4. Run Claude (from Codex)

Check `claude --help`: when it lists `--effort`, announce `Delegating to Claude: MODEL, effort LEVEL (tier TIER): REASON` and use `claude -p "PROMPT" --model MODEL --effort LEVEL --output-format json`. Otherwise omit effort from the announcement and command. The JSON result's `session_id` identifies the session; continue with `--resume SESSION_ID`, retaining the explicit settings. Ask for the same report fields in the prompt. Beside the summary, report the model recorded by the CLI result (for example its `modelUsage` keys), any fallback or difference, and the requested effort; if actual effort is not exposed, say it is unverified. Apply the same announce/report rule to follow-ups.

## 5. Verify

A report is a claim. Check the branch: diff, commits (Conventional Commits) and the tests the report names, then run the project's checks yourself before relying on the work. An off-shape report or one that contradicts the diff is unverified.

If Codex stops mid-task:

- A non-zero exit, an error or failed-turn event at the end of EVENTS.jsonl, or a missing or empty report means the run did not finish. Inspect the last events to distinguish a usage limit from another failure; never retry at once, since a usage limit is still there.
- Inspect the worktree with `git status --short` and `git diff --stat` to see what it did before stopping. Partial work is a claim; never merge it unverified.
- Tell the user in one line that Codex stopped and why, as far as the events show; say when the reason is unclear.
- Offer the user three choices: finish directly from the partial state; wait for the limit to reset and continue the same session with `cd WORKTREE && codex exec resume SESSION_ID -m MODEL -c model_reasoning_effort='"LEVEL"' -o REPORT.json "FOLLOW-UP" </dev/null >/dev/null`; or discard the worktree. Recommend finishing directly when little remains, or resuming from the worktree after the reset when a lot remains.
