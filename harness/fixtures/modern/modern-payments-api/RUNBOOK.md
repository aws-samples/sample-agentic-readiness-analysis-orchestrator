# Payments API — Runbook

## Dashboards
- CloudWatch dashboard `payments-prod` — p50/p99 latency, 4xx/5xx, throttles.
- X-Ray service map `payments` — traces keyed by `X-Correlation-Id`.

## Alarms
| Alarm | Threshold | Action |
|---|---|---|
| `payments-5xx` | >1% over 5 min | Page on-call |
| `payments-idempotency-conflict` | >10/min | Investigate a misbehaving client retry loop |
| `payments-ddb-throttle` | any | Check on-demand capacity / hot partition |

## Deploy & rollback
- Deploy: `sam build && sam deploy --config-env prod`.
- Rollback: `sam deploy` pins each version; redeploy the previous artifact (immutable).
  No manual resource edits — the stack is the source of truth.

## Common operations
- **Reconcile a charge**: `GET /charges/{id}` — read-only, safe to run anytime.
- **Issue a refund**: `POST /charges/{id}/refunds` with an `Idempotency-Key`. Refunds are
  append-only and audited; there is no destructive path.
- **Replay a failed webhook**: safe — every write is idempotent.

## On-call escalation
1. Check `payments-prod` dashboard and recent deploys.
2. Filter logs by `correlation_id` to trace a single request end-to-end.
3. Escalate to Payments Platform if the ledger and gateway metrics disagree.
