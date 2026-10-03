# Next.js (App Router)

Check the Next.js version first: caching defaults and some APIs (async `params`/`cookies()`/`headers()`, caching directives) changed between majors. Follow the conventions already used in the repo, and confirm uncertain APIs against the current docs.

## Server vs Client Components
- Components are Server Components by default: fetch data there, keep secrets there, and ship no JS for them.
- Add `'use client'` only to the leaves that need state, effects, event handlers or browser APIs. Push the boundary as far down the tree as possible.
- Pass serialisable props from server to client. You can pass Server Components as `children` into Client Components.
- Code that must never reach the browser (DB access, secrets) goes in modules marked with `import 'server-only'`.

## Data fetching and mutations
- Read data in Server Components (or route handlers) through a data-access layer (`lib/data/*`) that also checks authorisation, rather than calling the DB from scattered components.
- Fetch in parallel (`Promise.all`) and stream slow parts with `<Suspense>` boundaries.
- Mutations: Server Actions (`'use server'`) for forms and app-internal mutations; Route Handlers (`app/api/**/route.ts`) for public or third-party APIs and webhooks.
- Treat every Server Action as a public endpoint: validate input with a schema, check authentication and authorisation inside it, and return typed results or errors instead of throwing raw errors at the client.
- After mutating, revalidate explicitly (`revalidatePath` / `revalidateTag`, or the version's equivalent), and `redirect` where appropriate.
- Be explicit about caching for each fetch or route (static, revalidated at an interval, or dynamic) instead of relying on defaults you haven't checked for this version.

## Routing and files
- `layout.tsx` for shared UI, `page.tsx` for routes, `loading.tsx` and `error.tsx` (a Client Component) for each meaningful segment, `not-found.tsx` for 404s.
- Route groups `(group)` to organise without changing URLs; private folders `_components` for co-located non-route files.
- `generateMetadata` / `metadata` for SEO on every public page; `sitemap.ts` and `robots.ts` for public sites.
- Middleware only for cheap, cross-cutting concerns (redirects, locale). Never rely on it as the only authorisation check.

## Environment variables
Only `NEXT_PUBLIC_*` variables reach the browser, so never put secrets behind that prefix. Validate env vars at startup with a schema (e.g. zod in `env.ts`).

## Testing
- Unit and component tests with Vitest or Jest plus Testing Library. Async Server Components are best covered by E2E tests or by testing their data functions directly.
- Server Actions and data-access functions can be tested as plain async functions.
- E2E with Playwright against `next build && next start` in CI, not the dev server.
