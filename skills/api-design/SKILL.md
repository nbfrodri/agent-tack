---
name: api-design
description: Backend and API design for FastAPI, Django, Laravel and Express/NestJS/Fastify: REST conventions, status codes, errors, validation, pagination, OpenAPI, layering and API tests. Use when creating or changing endpoints, routes, controllers, schemas or webhooks (API, endpoint, backend, ruta).
---

# API design and backend structure

An API is a contract with its clients (your frontend, mobile apps, other teams). It should be predictable: the same conventions on every endpoint, input validated at the edge, errors in one format, and documentation that matches the code because it's generated from it.

Framework-specific guidance (read the one that matches the project):
- Python (FastAPI, Django/DRF): `references/python.md`
- PHP (Laravel): `references/laravel.md`
- Node.js (NestJS, Express, Fastify): `references/node.md`

## Layering
Keep HTTP concerns out of business logic so the same logic can serve a CLI, a queue worker or another API version:
```
route/controller  →  validates & maps the request, calls a use case, maps the result to a response
use case/service  →  orchestrates: loads aggregates, applies domain rules, persists, emits events
domain            →  entities, value objects and business rules (no framework, no HTTP)
repository/adapter → persistence and external services, behind interfaces
```
Controllers should be thin; if one contains `if` statements about business rules, move them down a layer.

## REST conventions
- Resources are plural nouns: `/users`, `/users/{id}`, `/users/{id}/orders`. Actions that don't fit CRUD become sub-resources or explicit commands (`POST /orders/{id}/cancel`).
- Methods: `GET` reads (safe, cacheable), `POST` creates or runs commands, `PUT` replaces, `PATCH` partially updates, `DELETE` removes. `PUT`/`DELETE` must be idempotent; support an `Idempotency-Key` header for `POST`s that create payments or orders.
- Pick one JSON naming style (`camelCase` or `snake_case`) per API and keep it. Use ISO 8601 UTC for dates and strings for IDs and money amounts (or integer minor units), never floats.

## Status codes
| Code | When |
| --- | --- |
| 200 / 201 / 204 | OK / created (with a `Location` header) / no content |
| 400 | Malformed request |
| 401 | Not authenticated |
| 403 | Authenticated but not allowed |
| 404 | Not found (also for resources the user may not know exist) |
| 409 | Conflict (duplicates, version mismatch) |
| 422 | Validation failed |
| 429 | Rate limited (send `Retry-After`) |
| 500 | Unexpected error; never leak stack traces or SQL |

## One error format everywhere
Use RFC 9457 Problem Details (or the project's existing format), produced by a global exception handler:
```json
{
  "type": "https://example.com/errors/validation",
  "title": "Validation failed",
  "status": 422,
  "detail": "The request body is invalid.",
  "errors": { "email": ["Must be a valid email address."] },
  "traceId": "4bf92f35..."
}
```
Domain errors are mapped to status codes in one place, not with `try/except` in every controller.

## Validation
Validate every input at the boundary with a schema (Pydantic, Laravel Form Requests, zod or class-validator): types, formats, lengths, ranges and allowed values. Reject unknown fields on writes. Never trust client-provided IDs for ownership; check authorisation against the authenticated user.

## Collections
- Always paginate. Use cursor pagination for large or fast-changing sets, and offset/page pagination for small admin lists. Return metadata (`nextCursor` or `page/total`), set a max `limit`, and use a stable sort.
- Filtering and sorting through whitelisted query params: `?status=paid&sort=-createdAt`.
- Avoid N+1 queries when you embed related data (see the `database` skill).

## Versioning and evolution
Additive changes (new optional fields, new endpoints) are safe. Removing or renaming fields, changing types or making fields required is breaking: version it (`/v2` or a header), keep the old version during a deprecation period, and announce it (a `Deprecation` header, the changelog).

## Contract and docs
OpenAPI is the source of truth, generated from code (FastAPI, NestJS Swagger, Scribe or Scramble for Laravel) or written spec-first. Generate typed frontend clients from it when the frontend consumes this API (`openapi-typescript`, orval). Include examples and error responses.

## Cross-cutting
Authentication and authorisation (see the `auth` skill), rate limiting on public and auth endpoints, CORS restricted to known origins, request size limits, timeouts on outgoing calls, structured logs with a request ID (see `observability`), and a `/health` endpoint.

## Webhooks and background work
Verify webhook signatures, respond fast, process asynchronously in a queue, and make handlers idempotent (store processed event IDs). Anything slow (emails, reports, third-party calls) goes to a queue with retries and backoff.

## Testing
- Unit tests for the domain and use cases (no HTTP, no DB).
- API or integration tests per endpoint against a real test database: happy path, validation errors (422), auth (401/403), not found (404) and conflicts.
- Contract checks: the response matches the OpenAPI schema.
