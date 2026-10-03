# VPS with Docker

Cheap and full control, but you are the ops team: security updates, backups, monitoring and TLS are your job. Keep the setup simple and written down.

## Server baseline (do once, document it in the repo)
- A recent Ubuntu/Debian LTS release, a non-root sudo user, SSH key-only login (`PasswordAuthentication no`, `PermitRootLogin no`), a firewall (`ufw`) allowing only 22/80/443, `fail2ban`, and `unattended-upgrades` for security patches.
- Docker Engine + the Compose plugin from Docker's official repo; log rotation for containers (`json-file` with `max-size`, `max-file` in `daemon.json`).
- Databases are never exposed publicly: no `ports:` for DB services, only an internal Docker network.

## Reverse proxy + TLS
Use **Caddy** (automatic HTTPS, simplest) or Traefik (label-based) in front of the app containers. Nginx + certbot also works. Redirect HTTP→HTTPS, enable gzip/zstd, and set security headers.

Caddyfile example:
```
example.com {
  reverse_proxy app:3000
}
api.example.com {
  reverse_proxy api:8000
}
```

## Compose layout
- `compose.yaml` for the base services + `compose.override.yaml` for local dev (bind mounts, hot reload, exposed ports) + `compose.prod.yaml` for production (images from the registry, `restart: unless-stopped`, resource limits, healthchecks).
- Services: `proxy`, `app`/`web`, `api`, `worker` and `scheduler` (same image, different command), `db`, `redis`. Named volumes for data.
- `depends_on` with `condition: service_healthy` for start order; still make apps retry DB connections.

## Stack-specific images
- **Next.js:** `output: 'standalone'` in `next.config` and a multi-stage build copying `.next/standalone`, `.next/static` and `public`; run `node server.js` as a non-root user.
- **Python:** `python:3.x-slim` with `uv sync --frozen --no-dev` in the build stage. Run FastAPI with `uvicorn` (or `fastapi run`) using several workers, or `gunicorn -k uvicorn.workers.UvicornWorker`; run Django with `gunicorn` and serve static files via WhiteNoise or the proxy.
- **Laravel:** `php-fpm` + Nginx (or FrankenPHP/Octane in one container) with `composer install --no-dev --optimize-autoloader`. On deploy, run `php artisan config:cache route:cache view:cache` and the queue worker plus scheduler as separate services. Make `storage` and `bootstrap/cache` writable by the runtime user only.
- **Node API:** `node:22-alpine` or `-slim`, a production-only install (`npm ci --omit=dev` or equivalent), and `node dist/main.js` (not `npm start`, so signals reach the process).

## Deploy pipeline
1. GitHub Actions builds the images and pushes them to a registry (GHCR) tagged with the git SHA.
2. It deploys over SSH (a dedicated deploy user and key in GitHub Environment secrets): `docker compose pull && docker compose run --rm api <migrate command> && docker compose up -d --remove-orphans`.
3. Smoke test the health endpoint, and `docker image prune` old images (keep the previous one for rollback).
For zero downtime with several replicas, use the proxy's health checks or a tool like Kamal, which handles rolling deploys, TLS and rollbacks for Docker on VPSes.

Rollback: set the previous image tag and `docker compose up -d`.

## Backups and monitoring
- Nightly DB dumps (`pg_dump`, `mysqldump`, `mongodump`) from a cron job or container, encrypted and shipped off-server (S3, Backblaze B2, R2), with retention and a tested restore. Better still: use a managed DB and skip this.
- Uptime monitoring from outside, disk-space alerts, and container restart alerts. Lightweight options: Uptime Kuma, Netdata, Better Stack, or Beszel.
