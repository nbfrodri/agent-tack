# Test-Driven Development

## The cycle
1. **Red:** write a small test describing the next behaviour. Run it and confirm it fails *for the expected reason* (not a broken import).
2. **Green:** write the minimal code that makes it pass. No speculative functionality.
3. **Refactor:** with the tests green, remove duplication and improve names and structure. Tests stay green after every step.

### Record the evidence
At standard and strict, a commit that changes behaviour carries two lines in its body, so a reviewer (or `code-reviewer`) can check the cycle without rerunning it:

```text
Red: uv run pytest -q tests/test_cart.py -> 1 failed (test_empty_cart_totals_zero)
Green: uv run pytest -q -> 14 passed
```

`Red:` is the run that failed for the expected reason before the change, naming the failing tests; `Green:` is the run that passed after it. Docs, config and refactors that keep behaviour need neither line; a refactor says `Green:` only.

Repeat in small steps: one behaviour per cycle, not the whole test suite at once. Start with the simplest case and add edge cases as you go. Short cycles mean every failure points at a single change.

In a new module, the first red is usually an `ImportError`, which proves nothing about behaviour. Create the minimal interface first (signatures that raise `NotImplementedError` or return an empty value) so the test fails on the assertion.

## Bugs
Before fixing a bug, write a test that reproduces it and fails. The fix is then demonstrated and protected against regressions.

## Good tests
- A name that describes the behaviour: `rejects_order_when_stock_is_insufficient`.
- Arrange / Act / Assert (or Given / When / Then).
- They test observable behaviour, not implementation details.
- Fast, deterministic and independent: no reliance on order, the real clock or the network.
- One reason to fail per test.

## Pyramid
- **Unit** (most): domain and pure logic, no I/O.
- **Integration:** repositories, adapters, a real or test database.
- **End-to-end** (few): the critical flows.

Use test doubles (fakes, stubs, mocks) only at the boundaries (network, DB, clock, external services), not to isolate every domain class.

## Pragmatism
- Business logic, calculations, validation, parsing: strict TDD.
- UI, glue code, configuration, one-off scripts, exploratory spikes: reasonable verification is enough (a smoke test, or a documented manual run). If a spike stays, add tests before calling it done.
- If the project has no tests, set up the ecosystem's standard test framework (pytest, vitest/jest, go test, cargo test…) as the first step, in its own commit.
