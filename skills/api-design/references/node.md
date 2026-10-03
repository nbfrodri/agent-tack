# Node.js backends (NestJS, Express, Fastify)

## Tooling
TypeScript in `strict` mode, ESLint + Prettier (or Biome), Vitest or Jest, `supertest` for HTTP tests, and `tsx` for running in dev. Pin the Node version (`.nvmrc` or `engines`) and use the lockfile of the project's package manager (npm, pnpm, yarn or bun), never a mix.

## Choosing
- **NestJS**: modules, dependency injection and decorators out of the box. A good fit for larger APIs and DDD-style layering.
- **Fastify**: fast, schema-first (JSON Schema/TypeBox or zod) with built-in validation and serialisation.
- **Express**: minimal; you assemble the structure yourself. Fine for small services, or when the project already uses it.

## NestJS
- One module per bounded context (`orders/`, `users/`), with controller → service → repository inside; keep pure domain classes free of Nest decorators when using DDD.
- DTOs with `class-validator` + a global `ValidationPipe({ whitelist: true, forbidNonWhitelisted: true, transform: true })`, or zod via a pipe.
- Global exception filters map domain errors to the standard error format; Guards for authentication and authorisation; Interceptors for logging and response mapping.
- `@nestjs/config` with schema validation for env vars; `@nestjs/swagger` for OpenAPI.
- Tests: `Test.createTestingModule` with overridden providers for unit tests; e2e tests with `supertest` against `app.getHttpServer()`.

## Express / Fastify
```
src/
  app.ts            # builds the app (no listen) so tests can import it
  server.ts         # listen + graceful shutdown
  config/env.ts     # zod-validated env
  modules/<feature>/{routes,controller,service,repository,schemas}.ts
  middleware/       # auth, error handler, request id, rate limit
```
- Validate `body`, `params` and `query` with zod (Express) or route schemas (Fastify).
- Express: one central error-handling middleware (4 arguments) as the last `app.use`. In Express 4, async errors must reach `next()` (wrap handlers or use Express 5, which forwards rejected promises).
- Security middleware: `helmet`, `cors` with an explicit origin list, body size limits and rate limiting.
- Graceful shutdown on `SIGTERM`: stop accepting connections, finish in-flight requests, then close DB pools.

## Data access
Prisma (schema-first, migrations with `prisma migrate`) or Drizzle (SQL-like, typed) for Postgres/MySQL; Mongoose or the official driver for MongoDB. Keep ORM calls inside repositories, and use transactions for multi-step writes.

## General
- Never block the event loop: no sync file or crypto calls in request paths; move CPU-heavy work to worker threads or a queue (BullMQ).
- Always `await` or handle promises; enable `@typescript-eslint/no-floating-promises`.
- Structured logging with `pino`, including a request ID.
