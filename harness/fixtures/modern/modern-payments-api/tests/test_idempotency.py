"""Contract + behavior tests. Run offline against DynamoDB Local.

These prove the two properties an automated caller depends on:
  1. A retried write with the same Idempotency-Key does not double-execute.
  2. Reusing a key with a different body is rejected (409), not silently applied.
"""

from __future__ import annotations

import json

import pytest


@pytest.fixture()
def charge_event():
    return {
        "headers": {"Idempotency-Key": "k-0123456789abcdef", "X-Correlation-Id": "trace-1"},
        "requestContext": {"authorizer": {"lambda": {"client_id": "svc-orders", "scopes": "payments:write payments:read"}}},
        "body": json.dumps({"amount": 4200, "currency": "USD", "source": "tok_visa"}),
    }


def test_charge_is_idempotent_on_retry(charge_event, ledger_stub):
    from payments.handlers import create_charge

    first = create_charge(charge_event, None)
    second = create_charge(charge_event, None)  # same key + body => no double charge

    assert first["statusCode"] == 201
    assert second["statusCode"] == 201
    assert json.loads(first["body"])["id"] == json.loads(second["body"])["id"]
    assert ledger_stub.charge_count() == 1


def test_key_reuse_with_different_body_conflicts(charge_event, ledger_stub):
    from payments.handlers import create_charge

    create_charge(charge_event, None)
    charge_event["body"] = json.dumps({"amount": 9999, "currency": "USD", "source": "tok_visa"})
    conflict = create_charge(charge_event, None)

    assert conflict["statusCode"] == 409
    assert json.loads(conflict["body"])["code"] == "idempotency_conflict"


def test_missing_scope_is_denied(charge_event, ledger_stub):
    from payments.handlers import create_charge

    charge_event["requestContext"]["authorizer"]["lambda"]["scopes"] = "payments:read"
    with pytest.raises(PermissionError):
        create_charge(charge_event, None)
