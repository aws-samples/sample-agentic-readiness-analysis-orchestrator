# Unattended batch mode

Overnight, the agent drains the triage queue without an adjuster in the loop.

```bash
python -m claims_agent.batch --queue nightly --max-claims 500
```

In this mode the `settlement_writer` tool posts directly to the claims system of record and
releases payment. There is no approval step and no dollar ceiling — the model's recommended
amount is written as-is. Claims over the auto-approve threshold were supposed to be routed to a
human queue, but that check lives in the UI, not in the tool, so batch mode bypasses it.

Rollback is manual: pull the `payment_queue` rows for the run and reverse them.
