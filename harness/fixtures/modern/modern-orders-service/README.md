# Orders Service

A modern order-management service built in 2023 on Node.js 20 + TypeScript,
Fastify, and PostgreSQL (RDS). Containerized, IaC-deployed, JWT-authenticated, with
an OpenAPI spec and a healthy test suite. It is a well-engineered app — but several
of its operations are **irreversible and run without a human in the loop**, which is
what makes it risky to hand to an autonomous agent as-is.

## Architecture
- **Runtime**: Node.js 20 + TypeScript, Fastify 4
- **API**: REST, described in `openapi/orders.yaml` (OpenAPI 3.0)
- **Auth**: JWT bearer tokens (RS256), verified per request; role claims enforced
- **Data**: PostgreSQL 15 on RDS, migrations via `node-pg-migrate`
- **IaC**: `infra/ecs.yaml` (CloudFormation) — ECS Fargate service + ALB
- **Observability**: structured JSON logs (pino) with a request id; CloudWatch metrics

## What's good
- Clean layering (routes → services → repositories), typed end to end.
- Real authN/authZ; no static keys; secrets from Secrets Manager.
- Reproducible infra; blue/green deploy on ECS.
- Unit + integration tests.

## Safety gaps that block *autonomous* operation
These are deliberate: the service is safe for humans but not yet safe to drive unattended.
- **`DELETE /orders/{id}` hard-deletes the row and all customer PII** with no soft-delete,
  no confirmation, and no audit trail. An agent retrying a timeout could destroy data.
- **`POST /orders/{id}/refund` issues a real money movement with no idempotency key and
  no approval step** — a duplicate call double-refunds.
- **`POST /orders/{id}/cancel` triggers warehouse dispatch cancellation**, an irreversible
  downstream side effect, with no dry-run or human confirmation.
- No rate limiting on the mutating endpoints, so an automated caller can fan out unchecked.

See `SAFETY.md` for the full list and the intended remediation (add idempotency keys,
soft-delete + audit, and a human-approval gate on irreversible operations).
