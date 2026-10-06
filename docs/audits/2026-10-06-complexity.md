# Audit: complexity and what to trim

- Date: 2026-10-06, on `main` at `d38b2e8`. Scope: what can be deleted, merged or made optional without losing a guarantee. Report only; nothing here is applied.
- Complements [what each workflow step caught](../benchmarks/2026-10-05-step-value.md), which covers the process steps; this one covers code and configuration.

## Size today

About 11,200 lines of shell and Python (half of them tests), 19 skills (103 KB of `SKILL.md`), 10 agents, 5 modes plus `auto`, and 23 feature toggles, written in 3 days (339 commits). Per area:

| Area | Lines | Commits touching it | Evidence of value |
| --- | --- | --- | --- |
| Command guard (`guard-bash.sh`, `lib/guard-*`, `shell-parse.*`) | 1,023 | 23 | Review found real bypasses in #76; core guarantee |
| Ownership and safe uninstall (`lib/ownership.*`, `uninstall.sh`) | 702 | 18 | Restores users' files; core guarantee |
| Mods (`lib/mods.sh`, `plugins/`) | 652 | 12 | Claude Code only; none measured |
| Evals (`evals/`) | 883 | 21 | Produced every number in `results.md` |
| Activity log and turn report | 482 | — | Off by default; not yet used for a measurement |
| Shots and visual review (`lib/shots*`, mode rules) | 184 | 2 | New in #82; none measured |
| Memory, lessons, trace, model tiers | 333 | 9 | None measured |

## Findings, ranked by payoff

| # | Finding | Recommendation | Payoff |
| --- | --- | --- | --- |
| 1 | **Former-name compatibility after two days.** The `agent-harness` and `harness` names are still handled in 90 lines across 19 runtime files: `bin/harness`, `HARNESS_ALLOW_*`, `harness.*` git keys, `#harness` hook tags, the state and config directory migration. The rename happened on 2026-10-04 and the project has one maintainer. | Run `./install.sh` once on every machine you use (it migrates), then delete the former names in one change, with a test that the migration ran. | Fewer branches in the guard, hooks and installer; one name in docs |
| 2 | **`lean` and `lite` overlap.** The lean benchmark measured the same cost as lite on a bug fix and about 10% less on a new project, with the same branch, commit and test. Two modes with the same outcome add a choice users must understand. | Merge them: keep `lite` with lean's self-contained rules and terse replies, or keep `lean` as `reply-style terse` + `skill-loading minimal` on top of `lite`, which those toggles already express. | One mode fewer in README, `auto` and docs |
| 3 | **Toggle sprawl.** 23 toggles, several of which tune another (`memory` + `memory-max-chars`, `context` + `context-max-chars`, `unleash-max-tool-calls` + `unleash-max-cost`, `reply-style` + `skill-loading` + `subagent-model`). Each one needs docs, `tack config` tests and help text. | Before adding another, require a measured reason. Candidates to fold: the `*-max-chars` caps into one `context-budget`; `reply-style`, `skill-loading` and `subagent-model` into a single `economy` toggle, which is what `lean` already is (see 2). | Smaller `features.txt` and `usage.md` |
| 4 | **Features without evidence.** Mods, visual review, memory, lessons and trace together are about 1,170 lines with no measurement showing they change outcomes. | Turn on `tack config activity-log true` for two weeks (as the step-value note already proposes), then keep what was used. Move what was not into opt-in skill groups or a separate repository. | Smaller install and core |
| 5 | **Guard latency on native Windows.** The guard took 0.8 to 1.5 s per command in Git Bash, against a 500 ms budget in CI. Every process start costs about 50 ms there, and about 200 ms for the `python3` App Execution Alias. Reading the hook input in one process cut 10 to 15%; the rest is the subshells of the rule files. | If native Windows becomes a target, measure the guard there in CI (a `windows-latest` job running `tests/guard.test.sh`) and cut subshells in `guard-*.sh` (parameter expansion instead of `$(…)`). Until then, WSL2. | Usable guard on native Windows |
| 6 | **Duplicated mode rules.** The `Visual review` and `CI` bullets of `modes/standard.md` and `modes/strict.md` are identical, about 900 characters each. Only one mode loads per session, so this costs maintenance, not context, and the explicit text at session start is what the assistant follows. | Keep the text; add a `tests/validate.sh` check that the shared bullets match across modes so they cannot drift. | Low: prevents drift |

## What not to trim

- **Ownership and safe uninstall:** 700 lines, but it is what makes installing over a user's own configuration safe.
- **The shell parser in the guard:** the bypasses in #76 show that pattern matching alone is not enough.
- **Evals:** the only way to tell whether any of the above earns its cost.

Limits: one maintainer and three days of history; line counts include comments; "evidence of value" lists what is recorded in this repository, not what a user may have noticed.
