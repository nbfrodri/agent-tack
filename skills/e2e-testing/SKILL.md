---
name: e2e-testing
description: End-to-end browser tests with Playwright: critical flows, resilient locators, auth state, test data, flaky tests, CI. Use when writing or fixing E2E or browser tests (Playwright, Cypress, e2e, probar el flujo completo).
---

# End-to-end testing (Playwright)

E2E tests are the slowest and most fragile layer of the test pyramid, so keep them few and valuable: cover the critical user journeys (sign up, log in, checkout, the core feature) end to end, and leave edge cases to unit and integration tests. If the project already uses Cypress, follow it; for new setups, use Playwright.

## Setup
- `npm init playwright@latest` (TypeScript), in the frontend repo or an `e2e/` folder of a monorepo. Playwright also has a Python flavour (`pytest-playwright`) for Python-only projects.
- `playwright.config.ts`: `baseURL` from an env var; `webServer` to start the app (a production build, e.g. `next build && next start`, not the dev server); `retries: 2` in CI only; `trace: 'on-first-retry'`; `screenshot: 'only-on-failure'`; Chromium in PRs, plus Firefox/WebKit/mobile viewports nightly if needed.
- The backend and database run in CI through docker-compose or a service container, with seeded test data.

## Writing resilient tests
- **Locators** the way users find things: `getByRole('button', { name: 'Save' })`, `getByLabel('Email')`, `getByText`. Fall back to `getByTestId` (`data-testid`) only when there's no accessible name. Never use CSS/XPath tied to layout or generated class names.
- **Web-first assertions** that auto-wait: `await expect(page.getByRole('alert')).toHaveText(...)`. Never use `waitForTimeout`; wait for a visible state or a network response (`page.waitForResponse`).
- One user journey per test, independent and runnable in any order or in parallel. Name tests after the behaviour: `test('user can reset password via email link')`.
- Page Objects or custom fixtures for repeated interactions, kept thin (they expose actions, the assertions stay in the tests).

## Authentication
Log in once in a setup project and reuse `storageState` across tests, with one stored state per role (admin, regular user). Test the login UI itself in a dedicated test, and seed users through the API or DB rather than the UI.

## Test data
- Create the data each test needs through API calls or DB seeding in fixtures, with unique values (e.g. emails with a random suffix) so parallel tests don't collide. Clean up after, or reset the DB per run.
- Never run E2E against production data. Smoke tests against production use dedicated test accounts and only read-only or reversible actions.

## External services
Mock third-party services (payments, email, maps) with `page.route()` or at the backend with sandbox or test modes (Stripe test mode, Mailpit/Mailhog to catch emails). Don't mock your own backend in E2E; that's what component tests are for.

## Extra checks
- Accessibility: `@axe-core/playwright` on key pages, failing on serious violations.
- Visual regression: `toHaveScreenshot()` for stable, important screens only, with masks for dynamic content and snapshots generated in the same OS/browser as CI (e.g. the Playwright Docker image).

## Flaky tests
Reproduce with `--repeat-each=20` and inspect the trace (`npx playwright show-trace`). Usual causes: race conditions with network or animations (wait for the state, not a time), shared data between tests, time-dependent logic (`page.clock`), and non-deterministic ordering. Fix the cause; don't just add retries.

## CI
Run on every PR in GitHub Actions (cache browsers, or use the official Playwright container), shard across machines when the suite grows (`--shard=1/4`), and upload the HTML report and traces as artifacts on failure.
