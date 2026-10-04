# Workflow modes pilot (invalid comparison)

- Date: 2026-10-04. Frozen revision `754e91c`; Claude Code 2.1.288; requested model `claude-sonnet-5-5`; private HOME and XDG paths per session; core install with `--skip-plugins`.
- Sessions: `bug-fix` ×2 and `new-project` ×1 for baseline, lite, standard, strict and auto. All 15 exited 0.
- Status: **not a valid comparison**. Kept as evidence for the fixes below; the next benchmark reruns everything.

## Defects found

1. **Eval permissions:** the allowlist lacked `python -m pytest` (agents ran it with a `PYTHONPATH=src` prefix). In `bug-fix` no condition could run tests, and the harness modes correctly refused to commit unverified work, so commit and branch metrics are not comparable. Fixed in `3cb889e`.
2. **Harness regression:** after the global instructions were shortened, no mode created a branch in `bug-fix` and none loaded `dev-workflow`; the always-on text no longer named branch, test and commit. Fixed in `a572920` by stating those core rules at every level in the global instructions and the SessionStart message.

## Observations worth re-checking

| Cost per session (USD) | Baseline | Lite | Auto | Standard | Strict |
| --- | --- | --- | --- | --- | --- |
| bug-fix (mean of 2) | 0.047 | 0.094 | 0.098 | 0.108 | 0.105 |
| new-project | 0.094 | 0.179 | 0.196 | 0.305 | 0.791 |

- `auto` chose lite for `bug-fix` and standard for `new-project`, announcing the level as instructed.
- `strict` in `new-project` produced 5 commits, 20 tests, a plan, `AGENTS.md`, `docs/`, an AI log row and a handoff, and ran `code-reviewer` (most of its cost). Baseline made no commit and used no branch.
- Most of the harness overhead in `bug-fix` is input tokens (about 60k baseline vs 94k–172k with the harness).
- In `strict`, the command guard asked for review of opaque agent commands (an interpreter heredoc, chained `head; harness status; …`); the next phase's token-efficiency rules address this.
