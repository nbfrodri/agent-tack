# Deployment

| Environment | Where | Trigger | Secrets in |
| --- | --- | --- | --- |
| Staging | | push to `main` | |
| Production | | tag `v*` + approval | |

## Deploy
Steps or the pipeline that does them.

## Roll back
```bash
# exact command to go back to the previous version
```

## Database migrations
When and how they run on deploy.

## After deploying
Smoke test and what to watch (errors, latency) for the first minutes.
