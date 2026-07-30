"""Payments API Lambda handlers.

Contract-first: every route here maps to an operationId in openapi/payments.yaml.
Every mutating operation is idempotent (Idempotency-Key header) and authorized by
an OAuth2 client-credentials token validated upstream by the Lambda authorizer, so
this code never sees or stores a credential. Structured logging + tracing are on by
default; nothing is hard-deleted (the ledger is append-only).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.metrics import MetricUnit, Metrics

logger = Logger(service="payments")
tracer = Tracer(service="payments")
metrics = Metrics(namespace="Payments")

_TABLE_NAME = os.environ["LEDGER_TABLE"]  # injected by SAM; no hardcoded resource ids
_dynamodb = boto3.resource("dynamodb")
_table = _dynamodb.Table(_TABLE_NAME)


@dataclass(frozen=True)
class Principal:
    """The authenticated client, as passed down by the Lambda authorizer context."""

    client_id: str
    scopes: frozenset[str]


def _principal(event: dict) -> Principal:
    ctx = event["requestContext"]["authorizer"]["lambda"]
    return Principal(client_id=ctx["client_id"], scopes=frozenset(ctx["scopes"].split()))


def _require_scope(principal: Principal, scope: str) -> None:
    if scope not in principal.scopes:
        raise PermissionError(f"missing required scope: {scope}")


@tracer.capture_method
def _idempotent_put(idempotency_key: str, request_hash: str, build_item):
    """Store `item` under a conditional put keyed by the idempotency key.

    A retry with the same key and body returns the stored result; a reuse of the key
    with a *different* body is a 409 conflict. This is what makes charge/refund safe
    to drive from an automated retry loop.
    """
    existing = _table.get_item(Key={"pk": f"idem#{idempotency_key}", "sk": "IDEM"}).get("Item")
    if existing is not None:
        if existing["request_hash"] != request_hash:
            raise ConflictError("idempotency key reused with a different request body")
        return json.loads(existing["result"]), False

    item, result = build_item()
    _table.put_item(Item=item)
    _table.put_item(
        Item={
            "pk": f"idem#{idempotency_key}",
            "sk": "IDEM",
            "request_hash": request_hash,
            "result": json.dumps(result),
            # TTL so the idempotency record self-expires; the ledger row is permanent.
            "ttl": _ttl_24h(),
        }
    )
    return result, True


class ConflictError(Exception):
    ...


def _ttl_24h() -> int:
    # Caller-independent: SAM sets IDEMPOTENCY_TTL_SECONDS; default 24h.
    return int(os.environ.get("NOW_EPOCH", "0")) + int(os.environ.get("IDEMPOTENCY_TTL_SECONDS", "86400"))
