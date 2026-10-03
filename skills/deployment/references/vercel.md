# Vercel

Best for Next.js (zero-config) and other frontends. Python and Node functions are supported too, but long-running APIs, WebSockets, heavy background jobs and Laravel are usually better on a VPS or AWS.

## Setup
- Connect the GitHub repo: every PR gets a preview deployment and `main` deploys to production. Or use `vercel link` / `vercel deploy` from the CLI.
- In monorepos, set the Root Directory per project. Pin the Node version via `engines` in `package.json` or the project settings.
- Environment variables are set per environment (Production / Preview / Development); `vercel env pull .env.local` brings them to local. Only `NEXT_PUBLIC_*` reach the browser.

## Things to plan for
- **Serverless/Fluid functions have time and memory limits** that depend on the plan; configure them per route if needed and move long work to a queue/cron (Vercel Cron Jobs, Inngest, QStash, Trigger.dev) or to a separate backend.
- **Database connections:** each function instance opens connections, so use a pooled or serverless-friendly connection (Neon or Supabase pooler, Prisma Accelerate, PlanetScale's driver, RDS Proxy) and place the DB in a region close to the functions' region.
- **Files:** the filesystem is read-only/ephemeral; use Vercel Blob, S3 or R2.
- **Caching:** check the Next.js caching behaviour for the version in use, and use `revalidatePath`/`revalidateTag` after mutations.
- **Middleware/proxy** runs on every matched request, so keep it light.

## Domains and security
Add domains in the project settings (HTTPS is automatic). Protect preview deployments if they show private data (Deployment Protection), and set security headers (CSP, HSTS…) in `next.config` `headers()` or middleware.

## CI
Vercel builds on push by itself; keep GitHub Actions for lint/test checks and require them in branch protection so a broken build isn't merged. Use `vercel build` + `vercel deploy --prebuilt` from Actions only if you need custom pipelines.

## Rollback
Instant Rollback from the dashboard or `vercel rollback`, then fix forward.

## Observability
Vercel logs (short retention; add a log drain for anything longer), Speed Insights and Web Analytics, plus Sentry for errors.
