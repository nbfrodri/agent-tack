---
name: deployment
description: Configure Docker, CI/CD, environments and reversible deployments to Vercel, a VPS or AWS. Use for containers, pipelines, hosting or production deployment.
---

# Deployment

A good deployment is boring: every deploy goes through the same automated pipeline, the same artefact moves from staging to production, configuration comes from the environment, migrations are safe to run, and rolling back is one command.

Platform guidance (read the one you're deploying to):
- Vercel (Next.js and frontends): `references/vercel.md`
- VPS with Docker (any stack): `references/docker-vps.md`
- AWS: `references/aws.md`

## Choosing
| Situation | Good default |
| --- | --- |
| Next.js frontend or full stack | Vercel |
| Separate API (Python/Laravel/Node) + DB on a budget, full control | VPS with Docker Compose (+ a managed DB or backups) |
| Need for scale, compliance or company AWS infrastructure | AWS (ECS Fargate or App Runner + RDS) |
| Mixed | Vercel for the Next.js frontend + API on a VPS/AWS, with CORS and cookies planned for cross-domain |

Ask the user before creating paid cloud resources, changing DNS or touching production.

## Principles (12-factor)
- **Configuration in env vars**, validated at startup; `.env.example` documents every variable; real secrets live in the platform's secret store (Vercel env, GitHub Actions secrets, AWS Secrets Manager/SSM, `.env` on the server with `600` permissions) and never in git or images.
- **Build once, deploy many:** the same Docker image or build is promoted from staging to production, tagged with the git SHA (and a semver tag for releases).
- **Stateless app processes:** files go to object storage (S3, R2, Vercel Blob), sessions and cache to Redis or the DB, not to the container's disk.
- **Logs to stdout**; health endpoints for the platform (see `observability`).

## Docker essentials (any stack)
- Multi-stage builds: a builder stage with dev dependencies, and a slim runtime stage with only what runs.
- Pin base image versions (`node:22-alpine`, `python:3.13-slim`, `php:8.4-fpm-alpine`, not `latest`).
- Copy the dependency manifests and install before copying the source, so layers cache.
- Run as a non-root user, add a `HEALTHCHECK`, and use `.dockerignore` (`node_modules`, `.git`, `.env`, tests, local build output).
- One process per container (app, worker, scheduler are separate services built from the same image).
- Scan images (`docker scout`, Trivy) in CI.

## CI/CD with GitHub Actions
```
on PR:       lint → typecheck → unit/integration tests → build → E2E (optional) → preview deploy
on main:     same checks → build & push image (tag = SHA) → deploy to staging → smoke test
on release:  promote the same artefact to production (manual approval via GitHub Environments) → smoke test
```
- Use GitHub Environments (`staging`, `production`) with their own secrets and required reviewers for production.
- Use OIDC to authenticate to AWS (no long-lived access keys in secrets).
- Use `concurrency` groups so two deploys to the same environment don't overlap.

## Migrations on deploy
Run migrations as a separate step or one-off task before the new version receives traffic, never at the same time from every container's startup. Migrations must be backward-compatible with the running version (expand → migrate → contract; see the `database` skill) so rollbacks stay possible.

## Releases and rollbacks
- Zero downtime: rolling or blue/green deploys behind a health-checked load balancer or proxy, and graceful shutdown on `SIGTERM`.
- Rollback = redeploy the previous image tag or build (Vercel: Instant Rollback). Write the rollback command into the README or runbook.
- After each production deploy: a smoke test (health endpoint + one critical flow), then watch error rates in Sentry for a few minutes.

## Environments
`local` (docker-compose) → `preview` (per PR, where the platform supports it) → `staging` (mirror of production, separate DB) → `production`. Never point non-production environments at the production database.
