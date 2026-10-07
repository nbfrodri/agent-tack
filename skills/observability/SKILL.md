---
name: observability
description: Add structured logs, error tracking, health checks, metrics, tracing and alerts. Use for monitoring, production diagnostics and Sentry integration.
---

# Observability

In production you can't attach a debugger. When something breaks you need to answer "what happened, to whom, and why" from what the app recorded, so design logs, errors and metrics for that moment.

## Structured logging
- Log JSON in production (human-readable in dev), with consistent fields: `timestamp`, `level`, `message`, `service`, `env`, `requestId`/`traceId`, `userId` (if known), and event-specific context.
  - Python: `structlog` or `logging` with a JSON formatter.
  - Laravel: Monolog channels with `JsonFormatter`, plus `Log::withContext()`.
  - Node: `pino` (`pino-http`).
  - Next.js: `pino` on the server, and the platform's log drains on Vercel.
- **Request ID:** accept or generate an `X-Request-ID` (or W3C `traceparent`) at the edge, attach it to every log line in the request, return it in responses and error bodies, and pass it to downstream calls.
- **Levels:** `error` needs someone to act; `warn` is unexpected but handled; `info` covers significant business events (order placed, user signed up); `debug` is off in production.
- Log events, not noise: one line per meaningful thing, no logging inside tight loops.
- **Never log** passwords, tokens, API keys, full card numbers or sensitive personal data. Redact at the logger level (`pino` redact paths, processors in structlog). Logs go to stdout; the platform or collector ships them.

## Error handling
- One global handler per app maps known errors to proper responses (see `api-design`) and reports unexpected ones. Don't swallow errors: handle them meaningfully or let them propagate to the global handler.
- Error tracking with **Sentry** (or similar) on both backend and frontend: source maps uploaded on deploy, `release` and `environment` set, users identified by ID only, and noise filtered (bots, expected 4xx).
- Frontend: React error boundaries (`error.tsx` in Next.js) with a friendly fallback, reporting to Sentry.
- Background jobs log start, finish and failure with the job ID, and failed jobs go to a dead-letter or failed-jobs table you actually watch.

## Health checks
- `GET /health` (liveness): the process is up; cheap, with no dependencies.
- `GET /ready` (readiness): the DB, cache and required services are reachable; used by load balancers, Docker healthchecks and orchestrators. Keep it fast and don't expose internals.
- External uptime monitoring (UptimeRobot, Better Stack, Checkly, CloudWatch Synthetics) on the public URL, alerting the user.

## Metrics and tracing
- Start with the **RED** metrics per endpoint: Rate, Errors, Duration (p50/p95/p99), plus queue depth and job failures, and DB pool usage.
- **OpenTelemetry** for vendor-neutral traces and metrics across frontend → API → DB → external calls, exported to whatever backend the project uses (Grafana, Honeycomb, Datadog, AWS X-Ray/CloudWatch, Sentry performance).
- Platform defaults are fine to start with: Vercel Analytics/Speed Insights, CloudWatch on AWS, and Prometheus + Grafana or Better Stack on a VPS.

## Alerts
Alert on symptoms users feel (error rate, latency, the site being down, a full queue or disk), not on every error log. Every alert should be actionable and say where to look; send them to a channel the user actually reads (email, Slack, Telegram).

## Checklist for "ready for production"
Structured logs with a request ID · secrets redacted · a global error handler · Sentry on the frontend and backend with source maps · `/health` and `/ready` · uptime monitor · basic RED metrics · alerts for downtime and error spikes · backups verified (see `database`).
