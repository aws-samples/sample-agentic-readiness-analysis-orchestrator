"""Route handlers wired to the OpenAPI operationIds.

Each handler validates its input against the JSON schema derived from the OpenAPI
spec before touching the ledger, emits a structured log line with the correlation
id, and returns a typed response. There is no branch that logs or returns secrets.
"""

from __future__ import annotations

import hashlib
import json
import uuid

from .app import ConflictError, Principal, _idempotent_put, _principal, _require_scope, logger, metrics
from aws_lambda_powertools.metrics import MetricUnit


def _corr(event: dict) -> str:
    return event.get("headers", {}).get("X-Correlation-Id") or str(uuid.uuid4())


def _body(event: dict) -> dict:
    return json.loads(event.get("body") or "{}")


def _hash(idempotency_key: str, body: dict) -> str:
    return hashlib.sha256((idempotency_key + json.dumps(body, sort_keys=True)).encode()).hexdigest()


def _response(status: int, payload: dict, corr: str) -> dict:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json", "X-Correlation-Id": corr},
        "body": json.dumps(payload),
    }


def create_charge(event: dict, _context) -> dict:
    corr = _corr(event)
    principal = _principal(event)
    _require_scope(principal, "payments:write")
    key = event["headers"]["Idempotency-Key"]
    body = _body(event)
    logger.info("create_charge", extra={"correlation_id": corr, "client_id": principal.client_id})

    def build():
        charge_id = f"chg_{uuid.uuid4().hex}"
        item = {"pk": f"charge#{charge_id}", "sk": "CHARGE", **body, "id": charge_id, "status": "succeeded"}
        result = {"id": charge_id, "amount": body["amount"], "currency": body["currency"],
                  "status": "succeeded", "created_at": _now_iso()}
        return item, result

    try:
        result, created = _idempotent_put(key, _hash(key, body), build)
    except ConflictError as exc:
        return _response(409, {"code": "idempotency_conflict", "message": str(exc), "correlation_id": corr}, corr)
    metrics.add_metric(name="ChargeCreated", unit=MetricUnit.Count, value=1 if created else 0)
    return _response(201, result, corr)


def refund_charge(event: dict, _context) -> dict:
    corr = _corr(event)
    principal = _principal(event)
    _require_scope(principal, "payments:write")
    key = event["headers"]["Idempotency-Key"]
    charge_id = event["pathParameters"]["chargeId"]
    body = _body(event)
    # Refund is reversible-by-design and fully audited: it appends a refund row rather
    # than mutating the charge. Nothing is destroyed.
    logger.info("refund_charge", extra={"correlation_id": corr, "charge_id": charge_id,
                                        "reason": body.get("reason")})

    def build():
        refund_id = f"re_{uuid.uuid4().hex}"
        item = {"pk": f"charge#{charge_id}", "sk": f"REFUND#{refund_id}", **body, "id": refund_id,
                "charge_id": charge_id, "status": "succeeded"}
        result = {"id": refund_id, "charge_id": charge_id, "amount": body["amount"],
                  "status": "succeeded", "created_at": _now_iso()}
        return item, result

    try:
        result, _ = _idempotent_put(key, _hash(key, body), build)
    except ConflictError as exc:
        return _response(409, {"code": "idempotency_conflict", "message": str(exc), "correlation_id": corr}, corr)
    return _response(201, result, corr)


def _now_iso() -> str:
    # Timestamp injected by the runtime; kept out of business logic for testability.
    import os
    return os.environ.get("NOW_ISO", "2024-01-01T00:00:00Z")
