---
name: testing
description: Write or review behavioral tests with pytest, Pest/PHPUnit and Vitest/Jest. Use for test coverage, fixtures, boundary mocks, database tests or flaky suites.
---

# Testing

Tests exist so you can change code without fear. A good suite fails when behaviour breaks, passes when behaviour is preserved (even if the implementation changes), runs fast, and tells you exactly what broke. Tests that are coupled to implementation details, slow or flaky cost more than they protect.

For the TDD cycle itself see `dev-workflow` → `references/tdd.md`. For browser tests see the `e2e-testing` skill.

Framework-specific guidance (read the one the project uses):
- Python (pytest, FastAPI, Django): `references/python.md`
- PHP / Laravel (Pest, PHPUnit): `references/php.md`
- JavaScript / TypeScript (Vitest, Jest, Testing Library, Node APIs): `references/javascript.md`

## Before writing tests
Find out how the project runs its tests (README, `package.json` scripts, `pyproject.toml`, `composer.json`, CI workflow) and run the existing suite once, so you know the baseline (what already fails and how long it takes). Match the existing style: framework, folder layout, naming, factories and helpers. Don't introduce a second test framework.

## What to test at each layer
| Layer | Test type | Focus |
| --- | --- | --- |
| Domain (entities, value objects, pure functions) | Unit, no I/O | Business rules, invariants, edge cases. Most tests live here. |
| Use cases / services | Unit with fakes for ports, or integration | Orchestration, errors, side effects requested (events, emails) |
| Repositories / queries | Integration with a real DB | Queries return the right data, constraints, migrations |
| HTTP endpoints / Server Actions | Integration (API tests) | Status codes, validation (422), auth (401/403), response shape |
| UI components | Component tests | What the user sees and does, all four states (loading, error, empty, success) |
| Critical journeys | E2E (few) | Signup, login, checkout… end to end |

Don't test the framework or libraries (that Django saves a model, that React renders a div), trivial getters, or private methods directly (test them through the public API).

## Choosing cases
For each unit of behaviour, cover:
- the happy path;
- boundaries: empty, zero, one, many, max, off-by-one dates and time zones;
- invalid input and each error path;
- permissions (allowed, denied, someone else's resource);
- any bug that was fixed (a regression test named after the bug).

Use parametrised or table tests when the same behaviour is checked with many inputs.

## Writing them well
- **Name = behaviour:** `test_rejects_order_when_stock_is_insufficient`, `it('shows an error when the email is taken')`. The name should read like a spec.
- **Arrange / Act / Assert**, visibly separated, one behaviour per test. Several assertions are fine if they check the same behaviour.
- **Assert on outcomes**, not on implementation: returned values, state, HTTP responses, rendered output, messages sent. Avoid asserting that internal methods were called.
- **Test data via factories/builders** with sensible defaults, overriding only what matters to the test, so each test shows what's relevant. Avoid giant shared fixtures and fixture dumps.
- **Deterministic:** freeze time, seed randomness, no real network, no dependence on test order or on data left by other tests.
- **Self-contained:** a reader understands the test without jumping through many helpers. Some duplication in tests is fine if it keeps them clear.

## Mocks and fakes
Mock at the boundaries you don't own or that are slow or non-deterministic: HTTP to third parties, email/SMS, payment gateways, the clock, randomness, queues. Prefer **fakes** (in-memory repository, fake mailer) over mocks with call expectations. Don't mock the thing under test, value objects, or your own domain classes. For HTTP, intercept at the network layer (`respx`, `Http::fake()`, MSW/`nock`) rather than patching internal functions.

## Database tests
Use the same engine as production (testcontainers or a docker-compose service). Isolate each test with a transaction rollback or truncation, create data with factories, and assert query counts on important endpoints to catch N+1 regressions.

## Legacy code without tests (characterisation tests)
Before changing untested code, pin down what it does now: call it with representative inputs, record the actual outputs in assertions, and keep those tests while refactoring. If the current behaviour looks wrong, don't silently "fix" the expectation: note it, tell the user, and mark the test clearly (e.g. a `xfail`/`todo` with the reason). Break dependencies with seams (inject the clock, the HTTP client, the repository) to make code testable, in small, separate refactoring commits.

## Coverage
Coverage shows what is *not* tested; it doesn't prove the tests are good. Aim for high coverage on domain and use-case code; don't chase 100% on glue code. Look at uncovered branches in changed files, not just the global percentage. Mutation testing (mutmut, Infection, Stryker) on core domain logic is the real quality check, when it's worth the time.

## Flaky and slow tests
A flaky test is a bug, either in the test or in the code (race conditions). Reproduce it by running it many times or in random order, find the source of non-determinism (time, ordering, shared state, async waits, network), and fix it. Don't just add retries or sleeps. For slow suites, profile them (`pytest --durations`, `--profile`, Vitest reporters), move logic tests down to unit level, share expensive setup carefully, and run in parallel.

## Finishing
Run the full suite (and lint/type checks) before saying you're done. A test you wrote must have been seen failing for the right reason at least once, either before the implementation (TDD) or by temporarily breaking the code. Commit tests with the code they cover (`feat`/`fix`), or as `test(<scope>): …` when only adding tests.
