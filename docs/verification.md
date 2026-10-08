# Project verification

`tack verify` selects project checks for files changed on the branch and in the working tree, including untracked and deleted paths. It executes existing commands, not model calls. `tack verify --plan` inspects selection without running project code; add `--json` for structured results. Execution requires local `tack trust`, including manual use when workflow activation is off. Trust is not inherited from a global setting or another teammate's clone.

By default the base is the branch's merge base with local `main`, `master` or `develop`; on those branches it is HEAD. With no local trunk it compares against HEAD and reports that base. Use `--base REF` to choose a known comparison reference, or `--base HEAD` for uncommitted changes only. A shallow clone or custom branch layout needs an appropriate explicit base. New repositories without commits include all nonignored files.

Optional `checks-map.json` is versioned project data. Activation and scaffolding do not create it. During setup, select commands that exist and verify meaningful project behavior. For example, in a project that already has these tests and scripts:

```json
{
  "version": 1,
  "checks": [
    {
      "id": "api-contract",
      "paths": ["src/api/*", "tests/api/*", "openapi.json"],
      "command": "uv run pytest tests/api && uv run python scripts/check_api_compatibility.py",
      "timeout_seconds": 90
    },
    {
      "id": "storage-regressions",
      "paths": ["src/storage/*", "migrations/*", "tests/storage/*"],
      "command": "uv run pytest tests/storage",
      "timeout_seconds": 60
    }
  ]
}
```

Patterns use case-sensitive forward-slash project paths. `*` spans directories; `**/` also matches zero directories. Each selected command runs from the repository root, once even when multiple rules select it; duplicate commands use the shortest declared timeout. File names are never interpolated into commands. Changes to the map select every check. Commands run in Bash with pipeline failure propagation. Reuse a project's existing pre-commit/lint/type/test commands when appropriate; tack installs no extra checker.

Keep maps proportionate. If `npm test` already runs the focused suites, selecting all three repeats work; use the full command alone or map focused suites where appropriate. Tack cannot infer command containment. Retain project-required checks and keep prose needing manual review visible rather than mapping it to unrelated tests.

Without a map, verification reuses `check-fast` when set, or the canonical test command already detected by tack for source/test/recognized build-config changes. Other paths remain unmapped. This fallback is not dependency analysis or proof that every relevant test ran.

Results identify commands, their source, matched paths, statuses and bounded failure output. Exit codes: **0** selected checks passed with unchanged inputs and no unmapped paths, or explicitly **no_changes**; **1** a check failed/timed out; **2** configuration/execution/trust error; **3** verification is incomplete or unavailable. `--plan` returns 0 for a valid plan even when it reports unmapped paths; it never claims checks passed. No checks for changed files is **unverified**, not success.

The default total command budget is 120 seconds; `--budget-seconds N` accepts 1-600. Individual timeouts default to 60 seconds in maps and are capped by the remaining total budget. Budget-exhausted checks are not run. If a check changes tracked or nonignored untracked inputs, results are marked incomplete: review the edits and verify again. Ignored build outputs are outside that fingerprint; checks are trusted project code, not sandboxed. No cached success is reused.

## Read a result

Suppose a map associates `src/api/*` with `npm run test:api`. You change `src/api/orders.js` and `guide/orders.md`. `tack verify --plan` shows the selected command without executing it. After local trust, `tack verify` might print this illustrative result:

```text
Verification: incomplete (2 changed paths)
- api: passed: npm run test:api (from checks-map.json)
No check selected for: 'guide/orders.md'
Selected checks are declared verification, not proof of complete semantic coverage.
```

The API tests passed, while the guide still needs review. This returns exit code 3; do not add a meaningless command just to make every file green. If a test fails, the result names the failed command and includes its recent output. `tack verify --json` provides the same report as data, including changed paths, selected checks, statuses and unmapped paths.

The verifier does not write tests, ask a model to grade the code, prove TDD/SOLID, or decide that the feature meets every requirement. It connects existing project checks to the current changes and makes the evidence and gaps visible.

With a map, the shared Stop hook uses this verification instead of its older single-test-command path, and reports failures, untrusted execution and mapping gaps before the assistant stops. The existing one-retry limit still applies. `fast-check` after edits retains its existing explicit command. Other tools can use the same CLI even without a native completion hook. A path having a selected check is only declared routing coverage, not a guarantee of semantic correctness.

## Documentation reminders

`docs-map.txt` lives in the project root. It tells the Stop hook which docs may need review after a code change:

```text
# source glob | one or more relevant documents
src/api/* | docs/api.md, README.md
bin/mycli | docs/usage.md
```

If a matching source file changed but none of the listed docs changed, the hook asks for a review. Editing any listed doc satisfies the rule. This is a filename reminder: it does not check the wording, require meaningless doc edits or prove that the docs are current. Explain when no update is needed.

`checks-map.json` selects commands; `docs-map.txt` points to documentation. Neither is a dependency manifest.

## Optional requirement links

For a project that uses requirement IDs such as `R1`, run:

```bash
tack trace path/to/plan.md
tack trace # newest filename in the configured plans-path
```

Trace reports `linked` when a tracked test file mentions an ID and `MISSING` otherwise. It also warns about IDs absent from the plan. Exit codes are 0 for all links found, 1 for missing links and 2 for usage/configuration errors. It does not run tests or inspect their assertions. An empty test can mention an ID, so these links are not proof of coverage. Ordinary tasks do not need numbered IDs.

## Automatic checks

Set `check-fast` to an existing short command when feedback after edits is useful. It runs only in a trusted project, with a 60-second timeout. The unmapped Stop fallback has a 120-second timeout. Both use Bash pipeline failure detection and bounded failure output, including on systems without the `timeout` utility. Supported hook integrations are listed in [tool support](editors.md).

The Stop hook also reports uncommitted work, stale handoffs, documentation reminders and source changes without test-file changes. Existing tests may already cover a change: review their behavior rather than adding a test just to change a filename. The hook asks once; a second stop is permitted. Separate invocations can repeat checks; tack does not cache a passing result.

## Optional external checks

Reuse installed project tools before adding a checker. [Aislop](https://github.com/scanaislop/aislop) can be selected for supported languages when it finds useful issues your existing checks miss. Review and pin the chosen version in the project's normal dependency file; do not download latest during verification. A small local trial of 0.18.1 found a swallowed exception, but also warned about a deliberately retained public wrapper. Its score is not a code-quality verdict.

Start with the installed command `aislop scan --json`, inspect diagnostics and skipped engines, and keep rules advisory while assessing noise. For blocking CI, use the tool's documented CI command and project-calibrated rules through an existing script. Route that script with checks-map.json when useful. A missing dependency or skipped analysis is not evidence of complete verification. No extra model, repair loop, per-edit hook or network service is required.

Tack adds no new mandatory Git hook for this integration. Preserve the project's hook manager and local-hook chaining. Fast staged checks belong at commit time; expensive integration suites usually belong in CI. Select a hook for a demonstrated failure, test partially staged files and false positives, and measure latency. Repository protections, not local hooks alone, enforce shared merge policy.
