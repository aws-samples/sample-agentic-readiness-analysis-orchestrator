# Catalog GraphQL API

A modern product-catalog GraphQL service built in 2024 on Node.js 20 + TypeScript
and Apollo Server 4, backed by DynamoDB. It is authenticated, schema-first,
containerized, and IaC-deployed. It is close to agent-ready — the catalog is
read-mostly and its writes are naturally idempotent (upsert by SKU) — with only a
couple of minor hardening gaps left.

## Architecture
- **Runtime**: Node.js 20 + TypeScript, Apollo Server 4 (GraphQL)
- **API**: GraphQL, schema-first from `schema/catalog.graphql`
- **Auth**: API Gateway + Cognito JWT authorizer; resolvers check scopes
- **Data**: DynamoDB (products keyed by SKU); writes are upserts (idempotent by nature)
- **IaC**: `infra/template.yaml` (SAM), Fargate-free — Lambda resolver
- **Observability**: structured logs with a request id; CloudWatch metrics

## What's good
- Schema-first GraphQL with typed resolvers; introspection is a machine-discoverable contract.
- Real JWT auth with scope checks on mutations.
- Upsert-by-SKU means a retried `upsertProduct` mutation is safe (no duplicate rows).
- Reproducible infra; least-privilege resolver role.

## Minor gaps (hardening, not blockers)
- **No query depth / complexity limit** — a deeply nested query could be expensive.
  Add a depth limit and cost analysis. (Availability concern, not a safety one.)
- **`deleteProduct` mutation soft-deletes but does not emit an audit event** — the
  data is recoverable, but the who/when is not recorded. Add an audit trail.

Neither gap involves an irreversible destructive operation or missing auth, so this
lands **Pilot-Ready** with only routine hardening advised.
