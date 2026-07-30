# Orders Service — Safety Notes

This service is production-grade for **human-operated** use. Before it can be driven
by an **autonomous agent**, the following irreversible operations need guardrails.
None of these is a code-quality bug — the code is clean — they are missing *controls*.

| Operation | Why it's risky unattended | Remediation |
|---|---|---|
| `DELETE /orders/{id}` | Hard-deletes the order row and customer PII. No soft-delete, no audit, no confirmation. A retried timeout destroys data permanently. | Soft-delete + audit log; require an explicit `confirm=true` and an approval token. |
| `POST /orders/{id}/refund` | Real money movement with no `Idempotency-Key`. A duplicate call double-refunds. | Add idempotency keys; cap auto-refund amount; require human approval above a threshold. |
| `POST /orders/{id}/cancel` | Cancels a physical warehouse dispatch — an irreversible downstream side effect — with no dry-run. | Dry-run mode; human-in-the-loop confirmation before the dispatch recall fires. |
| mutating endpoints | No rate limiting; an automated caller can fan out unchecked. | Per-client rate limits + circuit breaker. |

## Not blockers
- Auth is present and correct (JWT RS256, role claims enforced).
- Secrets come from Secrets Manager; nothing hardcoded.
- The API is documented and the app is containerized + IaC-deployed.

The intent of this fixture: a modern app that is **Pilot-Ready** for agents but carries
**safety concerns** until the irreversible operations get human-in-the-loop controls.
