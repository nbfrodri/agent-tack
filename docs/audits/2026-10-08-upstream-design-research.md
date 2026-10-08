# Upstream design research

Reviewed on 2026-10-08 after the owner requested useful ideas from public GitHub projects. This is architectural research, not an effectiveness comparison or imported implementation. No upstream code, prompts or dependencies were copied. License labels below are GitHub repository metadata at inspection time; inspect the actual file license and preserve applicable notices before any future code reuse.

| Project and inspected revision | Observed mechanism and primary source | Decision for tack |
| --- | --- | --- |
| Aider, `5dc9490bb35f9729ef2c95d00a19ccd30c26339c` (Apache-2.0) | Its [repository-map documentation](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/website/docs/repomap.md) describes symbol/dependency relevance ranking under a context budget. | Evaluate compact, relevant project context next. Do not add a parser/indexer dependency in the first verification increment; measure saved context and missed information before adopting one. |
| pre-commit, `c4292384c94590cd8e6c68f677d95e3675994602` (MIT) | The [check runner](https://github.com/pre-commit/pre-commit/blob/c4292384c94590cd8e6c68f677d95e3675994602/pre_commit/commands/run.py) filters by paths/types, distinguishes skipped checks, records failures and detects modifications made by hooks. | Adapt declared path routing and explicit result states. Reuse project check commands, including pre-commit when already present, without installing a second hook manager. A check that changes its inputs must not produce a stale success. |
| ECC, `ef648e01899ba3e8dc6371642deaaf64b4477775` (MIT) | The [README](https://github.com/affaan-m/ECC/blob/ef648e01899ba3e8dc6371642deaaf64b4477775/README.md) documents selective profiles/components and bounded startup context. The previous repository name redirects to ECC. | Keep capability selection explicit and context bounded. tack already has groups and context limits; improve their measured use rather than duplicate switches or import the whole catalog. |
| mini-SWE-agent, `04d809ceab9df28f9adaed044884180159172930` (MIT) | Its [agent loop](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/agents/default.py) has step/time/cost limits and serializes configuration, status and observations. | Keep the verifier small and observable: command, source, timeout, exit/result and output. Retain plain-assistant comparisons. Do not add a second model orchestration layer or assume its benchmark claims transfer to tack. |

OpenHands' SDK repository was also inspected but no SDK integration was selected: tack's first increment can run existing project commands without an agent SDK. A search surfaced Continue skills, but the referenced `continuedev/skills` repository and check skill returned 404 from GitHub/API; no design claim relies on that unavailable source.

## Adoption order and proof

1. **Now:** explicit check selection and outcomes through the shared CLI and existing adapters. Test a real failing project invariant, trust refusal, timeouts, changed files and unmapped paths locally. This implements a check runner, not an independent semantic judge.
2. **Next experiment:** compact task-relevant context and removal of redundant discovery. Compare current tack, the candidate and plain Codex on the same frozen tasks.
3. **Only with evidence:** richer dependency maps or specialist routing. Require a demonstrated defect reduction or human-effort saving that justifies additional latency and maintenance.

This research informs [ADR 0003](../adr/0003-project-verification-over-generic-process.md) and the [implementation plan](../archive/plans/2026-10-08-project-verification-implementation.md). Document the final adaptation and its tests; similarities to a popular project are not evidence of benefit.

## README presentation

The public READMEs of [uv](https://github.com/astral-sh/uv/blob/main/README.md) and [Aider](https://github.com/Aider-AI/aider/blob/main/README.md) were inspected for clear entrypoints, installation examples and visual navigation. The tack adaptation uses an original teal pin logo, status/license badges, an end-to-end team example, a Mermaid flow and links to measured results. No upstream artwork or copy was imported. The positioning remains specific to tack: shared conventions, organized context and project checks, with configuration gaps and adverse benchmark findings visible.
