# AWS

Powerful, but easy to over-build and to overspend. Start with the simplest managed service that fits, define everything as code, and set billing alerts on day one.

## Account basics
- Don't use the root user day to day: enable MFA on it, and use IAM Identity Center (SSO) users and roles. Least-privilege IAM policies.
- Set an AWS Budget with email alerts before creating resources. Tag everything (`project`, `env`).
- GitHub Actions authenticates through **OIDC** (`aws-actions/configure-aws-credentials` with a role), never long-lived access keys.
- One account or region setup per environment where possible, or at least separate VPCs and resources for `staging` and `prod`.

## Infrastructure as Code
Use Terraform/OpenTofu, AWS CDK (TypeScript or Python) or SST, versioned in the repo and applied from CI after a reviewed `plan`/`diff`. No click-ops for anything that matters. Remote state in S3 (with locking) for Terraform.

## Compute options (simplest first)
| Service | Use for |
| --- | --- |
| **AWS Amplify Hosting** | Next.js or static frontends when you want them on AWS instead of Vercel |
| **App Runner** | A containerised API with minimal setup (check it's available and still supported in the region; otherwise use ECS) |
| **ECS on Fargate** + ALB | The default for containerised APIs, workers and schedulers in production |
| **Lambda** + API Gateway | Event-driven or spiky workloads, small APIs (Mangum for FastAPI, Bref for Laravel, Lambda Web Adapter for containers) |
| **EC2** / **Lightsail** | A VPS-style setup (see `docker-vps.md`), when you need full control at a low price |

ECS Fargate essentials: images in ECR (scan on push); a task definition with secrets from Secrets Manager/SSM; the service behind an ALB with health checks on `/ready`; tasks in private subnets; autoscaling on CPU or requests; migrations as a one-off ECS task before updating the service; and deployment circuit breaker with rollback enabled.

## Data
- **RDS** (PostgreSQL or MySQL) or Aurora: in private subnets, Multi-AZ for production, automated backups + PITR, encryption at rest, and RDS Proxy for Lambda or many connections. Never publicly accessible.
- **DocumentDB** is only partially MongoDB-compatible; for real MongoDB, use **MongoDB Atlas** on AWS (with VPC peering or PrivateLink).
- **ElastiCache** (Redis/Valkey) for cache, sessions and queues; **SQS** for job queues; **S3** for files (block public access; serve through CloudFront or presigned URLs).

## Networking and security
A VPC with public subnets (only the ALB/NAT) and private subnets (apps, DBs); security groups that allow only the needed ports from the needed sources; HTTPS with ACM certificates on the ALB or CloudFront; Route 53 for DNS; WAF for public apps that need it.

## Observability
CloudWatch Logs (set retention, since the default is to keep logs forever and that costs money), CloudWatch alarms on 5xx, latency, CPU and DB connections, and X-Ray or OpenTelemetry (ADOT) for traces. Sentry for application errors.

## Cost traps
NAT Gateways (charged per hour and per GB; consider VPC endpoints for S3/ECR), idle RDS instances in non-production environments (stop them or size them down), CloudWatch log retention, data transfer out, and forgotten load balancers or Elastic IPs. Review Cost Explorer monthly.
