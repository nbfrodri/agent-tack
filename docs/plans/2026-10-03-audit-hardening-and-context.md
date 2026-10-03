# Audit hardening and automatic project context

- Status: approved
- Goal: fix the ten verified audit findings and provide bounded, current project context at session start.
- Approval: the owner requested implementation of automatic context and execution of the audit fixes, with commits as work progresses.

## Steps and commits

1. Secret scanning: regression tests for local hooks staging secrets and filenames containing Unicode, quotes, tabs or newlines; scan the final index using exact paths.
2. Formatter trust: tests proving shared activation does not authorise executable formatters; introduce an explicit local trust setting and CLI command.
3. Command guard: fixtures for executable heredocs, compact git options and wrapper options; preserve benign quoted text, handle unsupported executable syntax conservatively and bound analysis cost.
4. Configuration and activation: regression tests for mixed hook groups, validator crashes and failed CLI mutations; preserve user commands and return useful non-zero errors.
5. Evaluations: offline stub-CLI and transcript tests; propagate runner failures, improve file-order metrics and provider handling, and avoid reporting unavailable evidence as success.
6. Startup context: add `harness context`, cap the included project instructions, architecture and active handoff, integrate Claude SessionStart and instruct other tools to load it; test disabled projects, missing docs, nested directories and JSON escaping.
7. Verification and docs: run all tests and ShellCheck; update architecture, usage, audit status and AI log with verified results.

Each block ends in a focused Conventional Commit with regression tests and relevant documentation. Keep the current handoff updated after each milestone.

## Acceptance criteria

- Every verified audit reproduction is covered by an automated regression check and corrected.
- Automatic context is useful without loading an entire documentation tree or repeating unrelated instructions.
- Shared workflow activation and local code-execution trust are distinct.
- Scripts remain compatible with Bash 3.2; tests use isolated HOME, XDG and git configuration and make no real agent requests.
- Existing checks remain green; new eval tests run in CI; no hooks are bypassed.
- No push, PR, merge or release is performed without the owner's approval.

## Scope and risks

`harness doctor`, installer dry-run and uninstall remain separate proposals. Parsing changes must not silently skip long or unsupported commands; trust migration must not run untrusted project code. Revised eval metrics need a new benchmark before historical results are compared.
