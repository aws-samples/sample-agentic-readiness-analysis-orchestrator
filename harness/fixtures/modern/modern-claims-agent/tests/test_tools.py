"""Tool-level unit tests. Happy path only — no adversarial input cases yet."""

from unittest.mock import MagicMock, patch

from claims_agent import tools


@patch("claims_agent.tools._conn")
def test_policy_lookup_shapes_result(conn):
    cur = MagicMock()
    cur.fetchone.return_value = ("POL-1", 50000.0, 500.0, "2025-01-01")
    conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = cur
    out = tools.policy_lookup("POL-1")
    assert out["coverage_limit"] == 50000.0
    assert out["deductible"] == 500.0


@patch("claims_agent.tools._conn")
def test_settlement_writer_marks_settled(conn):
    cur = MagicMock()
    conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = cur
    out = tools.settlement_writer("CLM-1", 1200.0, "routine")
    assert out["status"] == "SETTLED"
