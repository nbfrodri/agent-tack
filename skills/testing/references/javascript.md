# JavaScript / TypeScript testing (Vitest, Jest)

Use **Vitest** for new projects (fast, ESM and TypeScript native, Jest-compatible API); keep **Jest** where it's already set up. Don't mix both.

## Setup
- `vitest.config.ts`: `environment: 'node'` for backend code and `'jsdom'` (or `'happy-dom'`) for components, using per-file `// @vitest-environment jsdom` or `projects` when the repo has both; `setupFiles` for `@testing-library/jest-dom` and MSW; `coverage: { provider: 'v8', include: ['src/**'] }`.
- Next.js: Vitest + `@vitejs/plugin-react` + `vite-tsconfig-paths` (or Jest with `next/jest`). Async Server Components are covered by E2E tests or by testing their data functions directly.
- Scripts: `test` (watch locally), `test:run` (CI), `test:coverage`.
- Co-locate tests as `*.test.ts(x)` next to the code, or mirror `src/` in `tests/`, following the project.

## Unit tests
```ts
import { describe, it, expect } from 'vitest';

describe('calculateTotal', () => {
  it.each([
    { quantity: 1, expected: '10.00' },
    { quantity: 10, expected: '90.00' },
  ])('returns $expected for $quantity units', ({ quantity, expected }) => {
    expect(calculateTotal('10.00', quantity)).toBe(expected);
  });

  it('throws on negative quantities', () => {
    expect(() => calculateTotal('10.00', -1)).toThrow(/must be positive/);
  });
});
```
- Time: `vi.useFakeTimers()` + `vi.setSystemTime()`, restored in `afterEach`.
- Mocks: prefer injecting dependencies; use `vi.mock()` only for module boundaries (SDKs, `fs`), with `vi.mocked()` for types. Reset with `restoreMocks: true` in the config.
- Await every async assertion (`await expect(promise).rejects.toThrow()`); enable the `no-floating-promises` lint rule.

## React components (Testing Library)
```tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

it('shows an error when the email is already taken', async () => {
  const user = userEvent.setup();
  server.use(http.post('/api/users', () => HttpResponse.json(problem, { status: 409 })));
  render(<SignupForm />);

  await user.type(screen.getByLabelText(/email/i), 'taken@example.com');
  await user.click(screen.getByRole('button', { name: /sign up/i }));

  expect(await screen.findByRole('alert')).toHaveTextContent(/already registered/i);
});
```
- Query priority: `getByRole` > `getByLabelText` > `getByText` > `getByTestId`. Use `findBy*` for async UI and `queryBy*` for asserting absence.
- Mock the network with **MSW** handlers shared between tests (and Storybook, if used), not by mocking `fetch` or hooks.
- Wrap in the providers the component needs through a custom `render` helper (query client, theme, router).
- Test hooks through a component that uses them, or with `renderHook` for reusable hooks.
- Optionally add accessibility checks with `vitest-axe` / `jest-axe`.

## Node APIs
- Build the app without `listen()` and test it with `supertest(app)` (Express/Fastify, or `app.inject()` in Fastify) or Nest's `Test.createTestingModule` + `app.getHttpServer()`.
- DB: testcontainers (Postgres/MySQL), or `mongodb-memory-server`. Run the migrations once and isolate each test (transaction rollback or truncation). Prisma: a separate test database URL plus `prisma migrate reset --force` in global setup.
- Outgoing HTTP: MSW (Node) or `nock`, failing on unmatched requests.

## Coverage and quality
`vitest run --coverage` with thresholds once the baseline is known; Stryker for mutation testing of core logic.
