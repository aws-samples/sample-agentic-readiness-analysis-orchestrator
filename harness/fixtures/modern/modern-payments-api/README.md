# Payments API

A serverless payments service (charge, refund, reconcile) built in 2024 on
Python 3.12 + AWS Lambda behind API Gateway, with DynamoDB for the ledger. It is
designed to be driven by machines: every mutating operation is idempotent,
authenticated with OAuth2 client-credentials, described by an OpenAPI 3.1 spec,
and emits structured JSON logs with a correlation id.

## Architecture
- **Runtime**: Python 3.12 on AWS Lambda (arm64), packaged with the AWS SAM CLI
- **API**: REST over API Gateway, contract-first from `openapi/payments.yaml` (OpenAPI 3.1)
- **Auth**: OAuth2 client-credentials (machine-to-machine) validated by a Lambda authorizer against Cognito; no human login path, no shared static keys
- **Data**: DynamoDB single-table ledger, point-in-time recovery on
- **IaC**: `infra/template.yaml` (SAM) — the entire stack is reproducible from source
- **Observability**: structured JSON logs (`aws_lambda_powertools`), X-Ray tracing, CloudWatch metrics; every request carries an `X-Correlation-Id`

## Safe for automated / agentic operation
- **Idempotency**: every write requires an `Idempotency-Key` header; keys are stored
  in DynamoDB with a TTL, so a retried charge or refund never double-executes.
- **Machine interface**: the OpenAPI spec is the source of truth and is validated in CI;
  a client (human or agent) can discover every operation, its schema, and its errors.
- **Least privilege**: each Lambda has its own IAM role scoped to the exact table/actions
  it uses. No wildcards.
- **Reversibility**: refunds are first-class and audited; nothing is hard-deleted — the
  ledger is append-only and reconciliation is a read.

## Tests & operations
- `tests/` — unit + contract tests; `pytest` runs offline with a DynamoDB Local stub.
- `RUNBOOK.md` — on-call procedures, dashboards, rollback via `sam deploy` to the prior version.
- CI: lint (`ruff`), type-check (`mypy`), test, and OpenAPI validation gate every merge.
