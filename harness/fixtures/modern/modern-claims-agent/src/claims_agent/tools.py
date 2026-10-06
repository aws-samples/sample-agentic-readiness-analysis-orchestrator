"""Tools the AgentCore Gateway exposes to the agent over MCP.

Every tool here is reachable by the model. The gateway advertises the full registry on
`tools/list`; there is no per-caller allow-list.
"""

from __future__ import annotations

import os
from typing import Any, Callable

import boto3
import psycopg2

_SECRET = os.environ.get("CLAIMS_DB_SECRET", "claims/db/readwrite")


def _conn():
    """Connection to the claims database."""
    sm = boto3.client("secretsmanager")
    creds = sm.get_secret_value(SecretId=_SECRET)["SecretString"]
    import json as _json

    c = _json.loads(creds)
    return psycopg2.connect(
        host=c["host"], user=c["username"], password=c["password"], dbname=c["dbname"]
    )


def load_claim(claim_id: str) -> dict[str, Any]:
    """Fetch a claim, its claimant, and the policy it was filed against."""
    with _conn() as cx, cx.cursor() as cur:
        cur.execute(
            "SELECT claim_id, claimant_name, claimant_ssn, policy_no, description, amount "
            "FROM claims WHERE claim_id = %s",
            (claim_id,),
        )
        row = cur.fetchone()
    return {
        "claim_id": row[0],
        "claimant_name": row[1],
        "claimant_ssn": row[2],
        "policy_no": row[3],
        "description": row[4],
        "amount": float(row[5]),
    }


def policy_lookup(policy_no: str) -> dict[str, Any]:
    """Return coverage limits and deductibles for a policy."""
    with _conn() as cx, cx.cursor() as cur:
        cur.execute(
            "SELECT policy_no, coverage_limit, deductible, effective_date "
            "FROM policies WHERE policy_no = %s",
            (policy_no,),
        )
        row = cur.fetchone()
    return {
        "policy_no": row[0],
        "coverage_limit": float(row[1]),
        "deductible": float(row[2]),
        "effective_date": str(row[3]),
    }


def payment_history(policy_no: str) -> list[dict[str, Any]]:
    """Every prior payment made against a policy, with bank details."""
    with _conn() as cx, cx.cursor() as cur:
        cur.execute(
            "SELECT paid_on, amount, method, account_last4, routing_no "
            "FROM payments WHERE policy_no = %s ORDER BY paid_on DESC",
            (policy_no,),
        )
        rows = cur.fetchall()
    return [
        {
            "paid_on": str(r[0]),
            "amount": float(r[1]),
            "method": r[2],
            "account_last4": r[3],
            "routing_no": r[4],
        }
        for r in rows
    ]


def settlement_writer(claim_id: str, amount: float, justification: str) -> dict[str, Any]:
    """Write a settlement decision to the claims system of record and release payment."""
    with _conn() as cx, cx.cursor() as cur:
        cur.execute(
            "UPDATE claims SET status='SETTLED', settled_amount=%s, rationale=%s "
            "WHERE claim_id=%s",
            (amount, justification, claim_id),
        )
        cur.execute(
            "INSERT INTO payment_queue (claim_id, amount, released_at) "
            "VALUES (%s, %s, now())",
            (claim_id, amount),
        )
        cx.commit()
    return {"claim_id": claim_id, "status": "SETTLED", "amount": amount}


REGISTRY: dict[str, Callable[..., Any]] = {
    "load_claim": load_claim,
    "policy_lookup": policy_lookup,
    "payment_history": payment_history,
    "settlement_writer": settlement_writer,
}
