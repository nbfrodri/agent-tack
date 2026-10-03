# Six-run benchmark checkpoint

- Status: paused at the user's request; resume when Claude's session limit resets.
- Branch: `test/benchmark-reproducibility`; implementation commits `19bac43`, `81f23c3` integrated by parent.
- Frozen checkout: `/tmp/harness-frozen-benchmark-20261004`, detached `a8fd642a2aa0197e152b12e42f1755a9fa89e6e9`.
- Raw private output root: `/tmp/harness-six-run-20261004.yv_c1sj2/raw`. Never commit raw transcripts or credential files.
- Sanitized aggregates: `/tmp/harness-six-run-20261004.yv_c1sj2/aggregate` (metadata, metrics v2, runner exits, report, attempts, independent functional checks).

## Attempt status

Exactly two sessions attempted (H1, B1), both runner exit 1 and provider `is_error=true` due to Claude's session limit. No completed samples. Four approved attempts remain: H2, B2, H3, B3. Do not replace H1/B1 or exceed six attempts without new authorization. The provider declared reset at 01:50 Europe/Madrid on 2026-10-04; verify restored availability before resuming. Do not make additional model calls while paused.

- CLI: Claude Code `2.1.288`.
- Requested and observed resolved model in both attempts: `claude-sonnet-4-6`.
- Scenario: `bug-fix`; same seeded fixture and prompt for both conditions.
- Prompt SHA256: `fa75512f4bbe9da0b63b01a746832c93cd91da53afb94c159907405c7a155c6d` (prompt.txt bytes including newline).
- Permissions: `acceptEdits`; exact allowlist retained in metadata.json.
- Treatment: core harness installed from frozen checkout using `--skip-plugins`; baseline disables user setting sources and slash commands.
- H1 reached a functional empty-cart fix and regression test (3 tests pass; test-before-code observed), then hit the limit before committing. B1 made no fix (2 seeded tests pass). Independent `average_price([])` check succeeds only in H1.
- Costs observed: H1 `$0.1035732`, B1 `$0`. Interrupted samples do not support a benchmark comparison.

## Safe resume

Prepared script `/tmp/resume-harness-benchmark-20261004.py` runs only H2/B2/H3/B3 against the same frozen checkout/revision. It sets private HOME, CLAUDE_CONFIG_DIR, XDG_CONFIG_HOME, XDG_STATE_HOME, XDG_DATA_HOME, XDG_CACHE_HOME, CODEX_HOME, Git config and uv cache. It excludes inherited Claude/Anthropic/Codex variables, copies only required credentials privately and removes session HOME after each attempt. No account identifiers are recorded. These /tmp artifacts are session checkpoints; preserve or reconstruct them before reboot.

```bash
python3 /tmp/resume-harness-benchmark-20261004.py /tmp/harness-frozen-benchmark-20261004 a8fd642a2aa0197e152b12e42f1755a9fa89e6e9
python3 /tmp/grade-harness-benchmark-20261004.py /tmp/harness-frozen-benchmark-20261004 /tmp/harness-six-run-20261004.yv_c1sj2
```

The user chose to save the checkpoint and resume with Claude after the limit resets. This authorises the four remaining attempts once availability is restored; do not ask again for those attempts. Replacing failed attempts or exceeding six calls needs new authorisation. Grade against metrics v2 and update attempts.json rather than claiming incomplete runs succeeded. The current attempts.json describes only H1/B1 and must be refreshed after resumption.

## Accidental installer state and reversible recovery

H1 inherited the host XDG_STATE_HOME by mistake and created `/home/phobos/.local/state/agent-harness/ownership`. H2 installation stopped before any model call because that record refers to H1's temporary HOME. Read-only verification found ownership/home exactly `/tmp/harness-six-run-20261004.yv_c1sj2/home-harness-1` and all 96 recorded paths beneath that temporary HOME. Real user configuration paths were not targeted. Temporary credential HOMEs have now been removed.

Automatic approval review rejected deletion of this record, citing irreversible removal under the real HOME without explicit authorization and possible reversal/uninstall damage. The parent then prepared a safer reversible recovery that was approved: an atomic rename in the same filesystem to `/home/phobos/.local/state/agent-harness/benchmark-ownership-20261004`. All 96 records and private snapshots remain intact, and the active ownership path is clear. Nothing was deleted. Do not remove this backup without explicit permission. XDG isolation is corrected for the pending four runs.

## Verification

RED: reproducibility test failed because metadata.json was absent; allowlist assertion failed before it was recorded. GREEN: all 17 eval tests and ShellCheck on evals/run.sh pass. Actual model identifier comes only from observed init events; unknown stays null.
