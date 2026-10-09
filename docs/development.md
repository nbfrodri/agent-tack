# Development

How to change this repo safely: commands, adding skills or agents, and measuring behaviour.

The [engineering practices](engineering-practices.md) connect conventions to concrete failure cases, compatibility, recovery and measured outcomes. Keep one responsibility per component, reuse project commands across local checks and CI, and include tests that would fail for the defect being fixed. A new configuration format needs explicit version/validation behavior; a persistent-state change needs a recovery strategy and relevant tests.

## Commands

This repository uses its own `checks-map.json`. Run `bin/tack verify --plan` to see
the selection, review the commands and grant `bin/tack trust` locally before
`bin/tack verify --budget-seconds 600`. Use `--all` for a clean-clone baseline.
No global installation or workflow activation is required for these manual checks.

Documentation-only changes select content validation. Runtime, installer, hook and
test changes conservatively select the full parallel suite; shell/Python changes
also select lint. The full suite includes content validation, so mixed changes can
repeat that short check. We accept this small duplication instead of maintaining
a second test runner. Keep Node, cached/downloadable esbuild and the pinned linters
available as described below. The 600-second budget is explicit because the
default 120 seconds may not fit the full suite. CI still checks platform behavior;
a mapped path does not mean every semantic risk is covered. Review docs manually.

```bash
tests/lint.sh            # ShellCheck on every script and ruff on the Python (ruff through uvx at the pinned version when uv is installed)
tests/run-all.sh         # every suite below, in parallel (-j N), with a one-line summary each
tests/validate.sh        # skills, agents, references, budgets, former names, closed docs and local human-doc links/anchors
tests/validate.test.sh   # the validator catches each kind of error
tests/install.test.sh    # installer, in throwaway HOME directories
tests/lifecycle.test.sh  # ownership, previews and safe uninstall
tests/doctor.test.sh     # read-only installation diagnostics
tests/tools.test.sh      # targets.txt columns, `doctor --tools` and the weekly workflow
tests/mods.test.sh       # mods step: install, opt-outs, dry run, uninstall and doctor (fake claude CLI)
tests/vscode.test.sh     # VS Code step: chat.useAgentsMdFile install, opt-out, dry run, uninstall and doctor
claude plugin validate plugins && claude plugin test plugins/usage-band && claude plugin test plugins/agent-activity   # the mods themselves (needs the claude CLI)
tests/mods-unit.sh                    # the mods' unit tests with Node only (esbuild via npx), as CI runs them
tests/hooks.test.sh      # git and Claude Code hooks, in throwaway repos
tests/cli.test.sh        # activation, modes, config, startup context and the help-vs-docs drift check
tests/settings.test.sh   # mixed user and tack hook groups in Python and jq
tests/safety.test.sh     # final index scanning, exact paths and formatter trust
tests/guard.test.sh      # executable shell syntax, boundaries and long inputs
tests/evals.test.sh      # offline runner, transcript metrics and report fixtures
tests/evidence.test.sh   # bounded batches, comparison identity and fresh-session evidence
tests/project-capabilities.test.sh # project definitions, references and discovery index
tests/project-setup.test.sh # read-only discovery, minimal scaffold, readiness and remembered review state
tests/project-config.test.sh # shared preferences, clone propagation, local trust, paths and hook consumers
tests/bootstrap.test.sh  # optional pinned installation, consent, existing installs and cache failures
tests/team.test.sh       # branch overlap, isolated merge conflicts and parallel handoff context
tests/pr-policy.test.sh  # offline PR metadata, drafts, project conventions and inert event input
tests/verification.test.sh # path-selected checks, real failure detection, trust, timeouts and Stop integration
tests/native-agents.test.sh # native formats, installation preservation and Gemini/Copilot hook protocols
tests/smoke.test.sh      # portable installation and hook smoke checks
```
CI runs ShellCheck 0.11.0 (pinned by checksum in `.github/workflows/ci.yml`; use the same version locally, as the runner's default one reports different warnings) and content validation on Linux, the installer and hook regression suites on Linux and macOS, and `claude plugin validate`/`test` for each mod on Linux when the claude CLI is available (it skips otherwise). Rules for contributors (bash 3.2, isolated tests…) are in [`AGENTS.md`](../AGENTS.md).

Native Windows CI also checks ownership/restoration, the verifier, shared project configuration and the portable smoke flow. Symlink tests that need unavailable local privileges report an explicit skip. Keep command examples in their owning guide; the CLI drift check searches the current setup, usage, configuration, verification, installation and advanced guides.

The [onboarding conversation protocol](../evals/project-onboarding.md) prepares interactive model evaluations for proposal relevance, user selection and remembered choices. It has not been run. Deterministic setup/protocol tests do not prove model compliance; real-model runs require an agreed budget.

## Adding a skill, agent or tool
1. Create `skills/<name>/SKILL.md` or `agents/<name>.md` with `name` and `description` (what it does and when to use it, within the budget `validate.sh` enforces), or add a line to `targets.txt` for a new AI tool.
2. List it in [components](components.md) (the validator requires it); mention it in the README only if it changes what a newcomer needs to know.
3. Run `tests/validate.sh` and `./install.sh`, then commit and push.

## Tools compatibility (weekly)
`.github/workflows/tools-compat.yml` runs every Monday (and on demand from the Actions tab). It installs the latest Claude Code and Codex with npm, runs `./install.sh --skip-plugins` in a temporary HOME and then `tack doctor --tools`. It uses no credentials. A failure means a new tool release changed something the installer relies on: read the log, then adjust `targets.txt` or the installer.

## Behaviour evals

### Backend/frontend integration

The [teamwork pilot](benchmarks/2026-10-08-teamwork.md) uses `evals/teamwork.py` and its frozen manifest to run two producer/consumer pairs. Preview with `python3 evals/teamwork.py evals/batches/teamwork-pilot.json --dry-run`. Live execution requires a new output directory and private authentication; four sessions maximum, no retries. The worker reuses isolated Codex invocation/capture helpers; the separate `docs/benchmarks/support/probe-teamwork.py` grades delivered components offline. Do not mix these outcomes with the larger historical quality batch.

### Minimal requests and independent code review

The [quality/efficiency protocol](benchmarks/2026-10-08-quality-efficiency-protocol.md) compares plain projects, current tack and a candidate using the same minimal requests. `evals/quality.py` runs bounded implementation/setup stages in separate disposable containers; `quality_worker.py` handles one session. `quality_review.py` prepares anonymous production-only bundles and validates agent grades. `quality_grade.py` supplies hidden checks only after delivery. Offline coverage lives in `tests/quality.test.py` and runs through `tests/evidence.test.sh`.

```bash
python3 evals/quality.py evals/batches/quality-efficiency.json --stage coding --dry-run
docker build -t tack-quality:20261008 -f evals/quality.Dockerfile evals
```

For live runs, freeze the resolved image ID in the manifest, retain exact product commits, and supply `--auth /private/codex-auth.json --output /private/new-results` with `--stage pilot`, `setup` or `coding`. Each output directory must be new. Review calls use `quality_review.py MANIFEST --source RESULTS --output NEW-REVIEWS --auth PRIVATE-AUTH`. The review controller keeps condition mappings outside reviewer containers. Do not expose them to the orchestrator until its independent code assessment is saved. Run hidden grading in another disposable container after model execution. The public recipe pins the base and Codex version; rebuilt system packages may differ, so record tool versions and image identity.

The completed [quality report](benchmarks/2026-10-08-quality-efficiency.md) publishes adverse outcomes as well as benefits. `docs/benchmarks/support/summarize-quality.py RESULTS --output FACTS.json` joins coding, setup and review evidence only after a complete `reviews/orchestrator-blind.json` matches the anonymous bundle and raw-review hashes. Save that assessment before opening mappings or grading outcomes. `probe-quality.py` runs separately in an isolated environment against captured deliveries; its post-hoc findings supplement frozen acceptance without changing it. These reporting helpers are not installed by tack.

### Reproducible batches and local capabilities

Optional manifest fields `variant` (`primary` or `held-out`) and `skill_groups` fix the fixture family and installed skill groups. They override ambient evaluation settings and are included in resume identity. Endpoint changes also invalidate a batch's identity without storing the endpoint itself.

`evals/batch.py` runs finite manifests through the existing runner. Templates in `evals/batches/` need explicit model selections before execution. Previewing them is offline and creates no output:

```bash
python3 evals/batch.py evals/batches/core-comparison.json --dry-run
python3 evals/batch.py evals/batches/project-capabilities.json --dry-run
```

Select an experiment budget and suitable installed CLIs before running a real batch. Both conditions get ephemeral HOME, XDG, Git and provider directories; only authentication is carried across. File-backed authentication or API environment credentials work; keyring-only authentication may require a compatible login method. No real credentials or raw transcripts belong in commits.

The manifest declares scenarios, conditions, explicit provider/model pairs, repetition count, ordering seed, maximum runs, timeout and concurrency (at most eight). Optional `estimated_cost_per_run_usd` and `max_cost_usd` in `limits` reject an over-budget estimate and stop new waves when observed spend leaves insufficient budget. Estimates cannot cap the provider's actual charge; unknown observed cost stops further budgeted waves. Use small pilots first. Effort selection is rejected until an adapter actually applies it.

Run `python3 evals/batch.py <manifest.json> --output <private-results-directory>` on Linux/macOS or WSL. Repeating the same command resumes completed matching runs. A different manifest/source or interrupted run requires a new batch ID; no previous output is erased. Concurrent controllers are excluded by a `.running` marker; inspect interrupted work before removing a stale marker. Grade failures and incomplete runs remain visible.

Individual runs keep the existing arguments; `EVALS_PROVIDER=codex` or `claude` selects the tool for any scenario, and `codex-new-project` remains an alias. `EVALS_MODEL` selects the requested model, `EVALS_SKILL_GROUPS` fixes a non-baseline group's selection, and `EVALS_VARIANT=held-out` selects alternative event types in extended scenarios. The setup time is separate from agent execution time.

Metric version 3 groups only compatible observed configurations. Models, CLI versions, prompts, fixtures, hidden checks, permissions and time limits define cohorts; source and effective configuration define separate columns. Missing observations and legacy metric versions remain explicit. Acceptance rates include sample counts and 95% Wilson intervals; failed-attempt costs contribute to total spend and cost per accepted outcome. A tiny sample is not a universal effectiveness claim.

`event-routing` exercises a multi-file JavaScript service. The capability scenarios cover creation, an existing skill, a trivial edit, read-only review, a specialist role and disabled/unavailable delegation. Positive reuse cases invoke a fresh CLI session after the first task. Hidden checks assess artifacts and functional outcomes; completed transcript reads are reported separately and do not prove causal benefit. Run held-out confirmation only after freezing the candidate; do not tune against those checks and label them independent evidence.

Offline regression suites are `tests/evidence.test.sh` and `tests/project-capabilities.test.sh`. They use fixtures and fake CLIs, not paid sessions. The complete runner now includes `tests/mods-unit.sh`; Node and npx are required and esbuild 0.25.10 must be cached or downloadable. Native CLI plugin validation remains an explicit optional CI check when the CLI is available.

### Individual runs and historical metrics

The [adoption comparison](benchmarks/2026-10-08-adoption-protocol.md) uses `evals/adoption.py`, a separate runner for setup and second-clone work. Its manifest is `evals/batches/project-adoption.json`; it is not a `batch.py` manifest. Supply a frozen product checkout, the pinned subscription launcher, a private authentication file and a new private output directory. `--dry-run` lists the matrix without model calls. Keep `adoption_grade.py` outside the model environment until all sessions finish, then run it against the output. `tests/evidence.test.sh` includes its offline isolation, timeout and grading regressions.

Real sessions on throwaway repos, comparing tack with a plain assistant. They use tokens, so run them by hand after choosing the experiment budget.
```bash
evals/run.sh <new-project|bug-fix|release|vague-requirement|conventions|attachments|search> <baseline|auto|lean|lite|standard|strict> [repetition]   # harness = auto
evals/grade.py $EVALS_OUT/<scenario>/<condition>-<rep>    # writes metrics.json
evals/report.py                                          # Markdown tables
evals/outcomes.py <repo> [--ref main] [--days N] [--json]  # escaped defects and rework from a repo's history
```
Latest results: [results](results.md).

Outcomes come before process. `bug-fix` and `new-project` have hidden acceptance tests in `evals/hidden/<scenario>/test_hidden.py`, which the agent never sees: the grader runs them against the finished repo through the project's own environment (`uv run python evals/hidden/run.py`, plain `test_*` functions, no pytest needed) and records `hidden_passed`, `hidden_total` and `hidden_pass`; the report lists them first. The new-project prompt names the package and function (`cart.cart_total(items)`) so the tests can call it. `evals/outcomes.py` reads a repository's history: a `feat:` commit is an escaped defect when a `fix:` that reached the main line in a later step changes or deletes its lines within N days (SZZ-style, through `git blame`; docs, Markdown and tests excluded, and a fix that only adds lines is not linked); a fix on the same branch before the merge counts as caught before merge. The split assumes branches merged with merge commits; with squash, rebase or fast-forward merges every fix counts as escaped, and on a feature branch pass `--ref main`. It also counts fixes, reverts, bookkeeping commits (`docs(handoffs|plans|ai)`) and the median lead time from a merged branch's first commit to its merge.

Historical metrics version 2 separates Claude and Codex transcript formats, preserves unknown evidence as `null` and distinguishes test-file order from a verified red/green test run. Reports group runs by provider and metrics version rather than combining incompatible measurements.

Codex baseline runs use temporary HOME, XDG and CODEX_HOME directories. Only `auth.json` is copied with private permissions and removed afterward; API authentication through environment variables also works. Keyring-only authentication or credentials defined only in `config.toml` need a compatible authentication method before running the baseline. No global instructions, skills or Codex configuration are copied.


Each eval writes `metadata.json` with the scenario, condition, workflow mode, repetition, prompt SHA-256, harness revision, provider/CLI version, metric version and permission allowlist. Set `EVALS_MODEL` to request an explicit model; the resolved model is recorded only when observed in the transcript. A missing observation remains unknown. Do not publish raw transcripts or authentication files. Freeze tack checkout before comparing runs so instruction edits cannot alter one condition mid-experiment.

The runner sets private HOME, XDG_CONFIG_HOME, XDG_STATE_HOME, XDG_DATA_HOME, XDG_CACHE_HOME, provider config/auth directories and Git configuration **before** installing either condition. Merely changing HOME does not override inherited XDG paths. It copies only required authentication files with private permissions and removes those temporary copies after each attempt. Keep failed or interrupted attempts separate from completed samples; runner exit status and provider errors take precedence over an artifact-only score.
