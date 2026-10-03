# Handoff: rename to agent-harness, support more AI tools, measure results

- **Status:** in progress
- **Last updated:** 2026-10-03 21:40
- **Tool:** Claude Code (Opus 5.5)
- **Branch:** `main`

## Goal
1. Rename the project to `agent-harness` (repo, local dir, docs) and the CLI to `harness` (marker `.harness`, git key `harness.enabled`, hook tag `#harness`, env `HARNESS_ALLOW_*`, canonical link `~/.agents/harness`), migrating old installs cleanly.
2. Install for Claude Code, Codex, Cursor (editor + cursor-agent), GitHub Copilot CLI, Gemini CLI, OpenCode and Crush, using each tool's documented paths (verify, don't guess).
3. Everything in English (except intentional Spanish trigger phrases and user prompts).
4. Benchmark with vs without the harness: 3 scenarios × 2 conditions × 2 repetitions with Claude; baseline = `--setting-sources project,local --disable-slash-commands` and git hooks disabled via an isolated GIT_CONFIG_GLOBAL. Document metrics in docs/results.md and README.
5. GitHub: rename repo, description, topics. Ask before pushing.

## Done
- Baseline method verified: normal session sees the harness (YES), baseline doesn't (NO).
- Rename in code, tests and docs: CLI `harness`, `.harness`, `harness.enabled`, `#harness`, `HARNESS_ALLOW_*`, `~/.agents/harness`; installer migrates old agent-config installs (tested). Agent headings in English.

## Next
1. Commit; later: move local dir to ~/Projects/agent-harness, rename GitHub repo, re-run install.
2. Multi-tool adapters (verify each tool's paths in its docs).
3. Benchmark tooling (condition harness|baseline, metrics JSON, report) and 12 runs.
4. Concise README; move detail to docs/ (why, installer, hooks, sharing, results).
