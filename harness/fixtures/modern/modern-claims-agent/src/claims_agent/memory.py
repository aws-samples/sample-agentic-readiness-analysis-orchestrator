"""AgentCore Memory access for per-claimant context.

Long-term memory keeps what we have learned about a claimant across sessions so the agent
does not re-ask for the same details.
"""

from __future__ import annotations

import json
import os

import boto3

MEMORY_ID = os.environ["CLAIMS_MEMORY_ID"]

agentcore = boto3.client("bedrock-agentcore")


def recall(actor_id: str) -> list[dict]:
    """Everything remembered for this actor."""
    resp = agentcore.retrieve_memory_records(
        memoryId=MEMORY_ID,
        namespace="/claims/shared",
        searchCriteria={"searchQuery": actor_id, "topK": 25},
    )
    return resp.get("memoryRecordSummaries", [])


def remember(actor_id: str, claim_id: str, messages: list, completion: dict) -> None:
    """Persist a triage exchange.

    Writes the raw exchange, including whatever the retrieval step pulled in and whatever
    the tools returned, so later sessions have the full context.
    """
    agentcore.create_event(
        memoryId=MEMORY_ID,
        actorId=actor_id,
        sessionId=claim_id,
        eventTimestamp=None,
        payload=[
            {
                "conversational": {
                    "role": "USER",
                    "content": {"text": json.dumps(messages)},
                }
            },
            {
                "conversational": {
                    "role": "ASSISTANT",
                    "content": {"text": json.dumps(completion)},
                }
            },
        ],
    )
