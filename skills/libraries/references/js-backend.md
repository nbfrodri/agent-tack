# TypeScript and JavaScript on the server, and tooling

Follow the runtime the project targets (Node, Bun, Deno, edge workers): several rows depend on it. Names are npm packages.

| Need | Default | Alternatives | Notes |
| --- | --- | --- | --- |
| HTTP framework | `hono` | `fastify`, `@nestjs/core`, `express`, `elysia` | Hono runs on every runtime; Fastify for Node-only services; NestJS for large teams wanting structure; Elysia targets Bun |
| Typed API between own client and server | `@trpc/server` | `@orpc/server`, `@ts-rest/core` | oRPC and ts-rest also produce OpenAPI for outside consumers |
| Validation | `zod` | `valibot` | |
| Environment variables | `@t3-oss/env-core` | plain `zod` schema | |
| SQL | `drizzle-orm` | `prisma`, `kysely` | Prisma for its migrations and tooling; Kysely is a query builder only |
| Authentication | `better-auth` | `next-auth` | Follow the `auth` skill |
| Background jobs | `bullmq` | `pg-boss`, `inngest` | BullMQ needs Redis; pg-boss uses the Postgres already there; Inngest is a hosted service with a free tier |
| Logging | `pino` | | |
| Tracing and errors | `@opentelemetry/api` | `@sentry/node` | |
| Email | `resend` with `@react-email/components` | `nodemailer` | Resend is a paid service with a free tier; Nodemailer speaks SMTP to any provider |
| Payments | `stripe` | | |
| WebSockets | `ws` | `socket.io` | Socket.IO adds rooms, reconnection and fallbacks |
| HTTP client | built-in `fetch` | `ky`, `ofetch` | For retries, timeouts and hooks |
| Utilities | `es-toolkit` | | Replaces lodash; most needs are in the language now |
| IDs | `nanoid` | `crypto.randomUUID()` | |
| Images | `sharp` | | Native binary; not available on edge runtimes |
| LLM calls | `ai` | the provider's own SDK | |
| Tests | `vitest` | `node:test` | See the `testing` skill |
| HTTP tests and mocks | `supertest`, `msw` | | |
| Browser tests | `@playwright/test` | | See `e2e-testing` |
| Running TypeScript | `tsx` | Node's built-in type stripping | |
| Bundling a library | `tsdown` | `tsup` | |
| Lint and format | `@biomejs/biome` | ESLint with Prettier | Keep what the project has |
| CLI arguments | `commander` | `citty` | |
| CLI prompts and UI | `@clack/prompts` | `ink` | Ink renders React in the terminal |
