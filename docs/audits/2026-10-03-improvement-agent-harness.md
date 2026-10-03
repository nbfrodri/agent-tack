# Whole-project improvement audit

Assessment for personal use, prioritising incremental fixes. Executable code reviewed at `f93cb50`; the requested documentation and English-content changes were added during this review. The ten verified findings have been fixed and published on [`fix/audit-hardening-and-session-context`](https://github.com/nbfrodri/agent-harness/tree/fix/audit-hardening-and-session-context). Issues #13–#24 are closed as completed at the owner's request, with fix commits and verification recorded in their comments. Integration into `main` and remote CI are tracked in [PR #25](https://github.com/nbfrodri/agent-harness/pull/25).

## Resolution tracking

| Finding | GitHub issue | Fix commit |
| --- | --- | --- |
| Local hook stages secrets after scanning | [#13](https://github.com/nbfrodri/agent-harness/issues/13) | `cc47d63` |
| Quoted filenames bypass scanning | [#14](https://github.com/nbfrodri/agent-harness/issues/14) | `cc47d63` |
| Shared activation implies formatter trust | [#15](https://github.com/nbfrodri/agent-harness/issues/15) | `3ca51fa`, `538563c` |
| Executable shell syntax bypasses checks | [#16](https://github.com/nbfrodri/agent-harness/issues/16) | `69b6ec6` |
| Validator errors reported as success | [#17](https://github.com/nbfrodri/agent-harness/issues/17) | `cd65e89` |
| Mixed groups lose user hooks | [#18](https://github.com/nbfrodri/agent-harness/issues/18) | `cd65e89` |
| Activation failures reported as success | [#19](https://github.com/nbfrodri/agent-harness/issues/19) | `3ca51fa`, `bf098e0` |
| Eval runner hides failures | [#20](https://github.com/nbfrodri/agent-harness/issues/20) | `699423d` |
| Eval ordering metrics give false positives | [#21](https://github.com/nbfrodri/agent-harness/issues/21) | `699423d`, `7f3f4a2` |
| Guard exceeds its analysis time budget | [#22](https://github.com/nbfrodri/agent-harness/issues/22) | `69b6ec6` |

Requested additions: [#23](https://github.com/nbfrodri/agent-harness/issues/23) startup context (`3ca51fa`); [#24](https://github.com/nbfrodri/agent-harness/issues/24) automatic audit issues (`31d6226`).

The scorecard below records the initial assessment, rather than a new post-fix score. The implementation plan is [complete](../plans/2026-10-03-audit-hardening-and-context.md). On integration, 10,014-character guard input took 0.127 s and 50,014 took 0.196 s; 70,014 characters returned `ask` in 0.057 s. Times are local observations, not guaranteed cross-platform thresholds.

Final local checks passed: ShellCheck, content validation and 426 automated checks (12 validator, 87 installer, 177 existing hooks, 34 CLI/context, 2 settings, 42 security, 56 guard and 16 offline eval checks). Integration review also verified that failed shared activation preserves a local opt-out and unsuccessful tool writes cannot prove test-first ordering. Remote CI and macOS results are recorded in [PR #25](https://github.com/nbfrodri/agent-harness/pull/25); no live model benchmark was run.

## Scorecard

Scores use the evaluator rubric: 6–7 means solid with clear gaps; 8–9 means consistent good practice. Overall: **7.4/10**, the unweighted mean of seven applicable dimensions. No application UI was assessed.

| Dimension | Score | Evidence |
| --- | --- | --- |
| Architecture | 8.5 | Installer orchestration, settings merge and shell parsing have separate owners; activation is centralised in `bin/harness`; architecture is now documented |
| Code quality | 7.0 | Small dependencies and readable shell, but several commands discard failures and the guard implements only part of shell syntax |
| Tests | 7.5 | All 275 checks passed; meaningful integration tests, but reproduced failures below have no regression coverage |
| Security | 5.5 | Secret scanning, hook chaining and command checks exist, but paths, execution order and formatter trust leave significant gaps |
| Performance | 6.5 | Guard analysis took 0.079 s for 1,014 characters and 2.955 s for 10,014; a 50,014-character input exceeded 12 s, longer than the configured 10 s hook timeout |
| Documentation | 8.5 | README and focused docs, plus requested architecture, customization and English content; published eval claims still need stronger measurement |
| Tooling | 8.0 | ShellCheck, content validation, isolated tests and Linux/macOS CI; eval infrastructure lacks automated fixture tests |

## Verification and limits

- ShellCheck passed with the command in `AGENTS.md`.
- `tests/validate.sh` passed; all 11 validator, 87 installer and 177 hook tests passed.
- Additional reproductions ran in temporary repositories with isolated HOME, XDG configuration and git configuration. Synthetic credential patterns were used; no real secrets or destructive shell commands were executed.
- English prompts for all four eval scenarios were checked with stub CLIs, without spending model tokens. Metric ordering was tested with a fixture transcript and mocked external subprocess results.
- Performance timings are local observations on Linux, not portable thresholds. No macOS run, remote CI status, live agent benchmark, full historical secret scan or external service audit was performed.

## Findings and proposed work

Effort: S = a small focused change; M = several related paths and regression cases. Fixes should begin with failing regression tests. Priorities reflect impact and implementation cost; the first four affect safety controls.

### 1. Local pre-commit hooks can add secrets after scanning

- **Priority:** high. **Effort:** S. **Location:** `git-hooks/pre-commit:70`.
- The harness scans first and runs the local hook afterward. A local formatter or generator can stage additional files that the scanner never sees.
- **Reproduction:** a local hook created and staged `.env`; the global hook exited 0 and `.env` remained in the index.
- **Change:** run the local hook and propagate its failure before scanning the final index, or scan again after it succeeds.
- **Risk:** preserve local-hook exit status and document the revised order. Add an integration test that proves a staged secret blocks an actual commit.

### 2. Quoted Git paths bypass secret and environment-file checks

- **Priority:** high. **Effort:** M. **Location:** `git-hooks/pre-commit:31` and `git-hooks/pre-commit:45`.
- Git quotes special filenames. The `.env` check treats quoted names as literal paths, and the added-line parser recognises only unquoted `+++ b/` headers.
- **Reproduction:** the same synthetic AWS pattern was blocked in `normal.txt` and accepted in `café.txt` and a filename containing a quote. `café/.env` was also accepted.
- **Change:** consume staged filenames as NUL-delimited data, preserve their exact bytes and inspect staged content without depending on human-readable diff headers. Retain the intended added-content policy or explicitly document a move to scanning complete staged blobs.
- **Risk:** whole-blob scanning can flag existing fixtures or historical credentials; define that behaviour and test Unicode, quotes, tabs, newlines and custom diff prefixes.

### 3. A shared activation marker is treated as formatter trust

- **Priority:** high. **Effort:** M. **Location:** `hooks/claude/format-file.sh:26`, `hooks/claude/format-file.sh:56`, `bin/harness:27`.
- A cloned repository can contain `.harness`, formatter configuration and an executable under `node_modules/.bin`. Editing a file then runs that executable without an explicit local trust decision.
- **Reproduction:** a temporary repository with only a shared marker, a Prettier config and a harmless stub binary executed the stub; no local `harness.enabled` setting existed.
- **Change:** distinguish workflow activation from permission to execute project code. Require locally stored trust for automatic formatters and executable formatter configs; a shared marker should only enable the workflow.
- **Risk:** shared projects will need a one-time local trust action. Keep existing activation semantics for instructions and git conventions.

### 4. Shell guard coverage is narrower than its documented behaviour

- **Priority:** high. **Effort:** M. **Location:** `hooks/claude/lib/shell-parse.sh:82`, `hooks/claude/guard-bash.sh:82`, `hooks/claude/guard-bash.sh:286`.
- Heredocs are always skipped, including substitutions in unquoted heredocs and scripts read by a shell. Compact `git -c…` options and options on wrappers such as `sudo -n` are also missed.
- **Reproduction:** the hook returned no decision for an executable shell heredoc, a command substitution inside an unquoted heredoc, an attached hooksPath override and `sudo -n` followed by a prohibited command. Only their JSON inputs were analysed; none of these commands ran.
- **Change:** add regression cases for executable heredocs and wrapper options, recognise compact git configuration options and state the supported parsing boundary accurately. Ask for review when an executable construct cannot be analysed safely.
- **Risk:** conservative handling can add confirmation prompts; test benign quoted data as well as executable inputs to avoid false positives.

### 5. The validator reports success after its Python checker crashes

- **Priority:** medium. **Effort:** S. **Location:** `tests/validate.sh:75`.
- The Python checker runs inside command substitution feeding a heredoc. Its exit status is discarded, so exceptions need not increment `ERRORS`.
- **Reproduction:** deleting the README from a temporary copy produced a traceback, `All valid` and exit 0.
- **Change:** capture and check the Python exit status before processing its findings. Add a test for a missing file or checker failure, rather than only well-formed validation errors.
- **Risk:** failures previously ignored will begin failing CI, which is the intended behaviour.

### 6. Mixed hook groups lose independent user commands

- **Priority:** medium. **Effort:** S. **Location:** `lib/settings-merge.py:22`, `lib/settings-merge.py:39`, `lib/settings-merge.jq:3`.
- If any command in a group contains a harness tag, the whole group is removed. A user's command in the same group disappears on installation.
- **Reproduction:** a group containing `echo user-hook` and a harness-tagged command lost the user command after merging.
- **Change:** filter owned commands within each group, retaining group metadata and remaining user commands. Exercise the same fixture against Python and jq.
- **Risk:** preserve matcher and other group attributes, and avoid duplicate harness commands on reinstall.

### 7. The activation CLI reports success when writes fail

- **Priority:** medium. **Effort:** S. **Location:** `bin/harness:36` through `bin/harness:52`.
- Config writes, marker writes and removals are followed by success messages without checking their status.
- **Reproduction:** an existing `.git/config.lock` made `harness enable` exit 0 and print “Enabled”, while `harness status` still printed `disabled`.
- **Change:** handle each mutation's failure, return non-zero and only announce successful state changes. Distinguish an absent config entry from a failed unset.
- **Risk:** test shared markers and partial failures so a failed command does not silently change the other activation mechanism.

### 8. Eval runner failures look successful to callers

- **Priority:** medium. **Effort:** S. **Location:** `evals/run.sh:168`.
- The CLI status is recorded, but the final successful `echo` becomes the script's exit status. Scenario setup failures are also not consistently checked.
- **Reproduction:** a stub agent exited 42; `run.txt` recorded that status, but the runner exited 0.
- **Change:** store the agent status, write the report and exit with the stored status; check scenario setup steps. Add offline tests with stub CLIs.
- **Risk:** partial transcripts should remain available for diagnosis instead of being deleted on failure.

### 9. Test-first metrics can reward implementation-first changes

- **Priority:** medium. **Effort:** M. **Location:** `evals/grade.py:43`, `evals/grade.py:92`; related adapter gap in `evals/run.sh:154`.
- Changes of two lines or fewer are discarded as placeholders. If the implementation is a one-line fix and a longer test is written afterward, the metric reports test-first. File order also does not prove a failing test ran before the fix.
- **Reproduction:** a fixture transcript edited the implementation first, then wrote a test; grading reported `test_written_before_code=true`.
- **Change:** distinguish scaffolding from edits, track first behavioural implementation changes and record a separate red/green metric when transcript evidence supports it. Keep unknown metrics unknown. Add provider-specific transcript fixtures; the Codex runner currently lacks separate baseline flags and grading only recognises Claude tool events.
- **Risk:** revised metrics will not be directly comparable to published tables. Rerun both conditions and record prompt, model and configuration versions before making stronger claims.

### 10. Long command strings exceed the command guard's time budget

- **Priority:** medium. **Effort:** M. **Location:** `hooks/claude/lib/shell-parse.sh:47`, `claude/settings.json:16`.
- The shell loop repeatedly slices and appends strings one character at a time. Long quoted arguments become slow even when the command itself is harmless.
- **Measurement:** one invocation per size took 0.079 s at 1,014 characters, 2.955 s at 10,014, and exceeded 12 s at 50,014. The hook timeout is configured at 10 s.
- **Change:** measure representative command payloads, reduce repeated full-string work and introduce explicit handling for inputs that cannot be analysed within the time budget.
- **Risk:** do not improve speed by silently truncating inputs or skipping substitutions. Verification must preserve decisions for commands near the size boundary.

## What to keep

- Separate installation, JSON merging, parsing and policy; no application framework is needed here.
- Data-driven tool and plugin support, concise global instructions and detailed skill references.
- Temporary HOME and git environments, local hook integration, migration tests and platform CI.
- Measured behaviour evaluations with explicit sample-size limits; improve the measurement rather than discarding the approach.

## Additional proposals and implemented additions

1. **`harness doctor` (M), proposed:** report tool availability, installed link targets, settings validity, effective hooksPath, activation source and formatter trust. Installer warnings are not available as a later health check.
2. **`install.sh --dry-run` (M):** preview link replacements, settings changes and plugin operations before installation. The current installer immediately mutates the user's configuration.
3. **Offline eval regression suite (M), implemented:** setup failures, transcript adapters, metric ordering and reporting are covered by 16 checks using stub CLIs and fixtures, now included in CI.
4. **Optional startup context summary (M), implemented:** `harness context` supplies bounded excerpts from `AGENTS.md`, `docs/architecture.md` and an active handoff. Claude SessionStart loads them automatically; other tools are instructed to run the command. `git config harness.context false` disables the additional context.

A safe uninstall or rollback command is a later option: it needs ownership metadata so it removes only harness-managed files and preserves user changes. Prefer these operational features over adding more generic skills until the verified safety gaps are closed.
