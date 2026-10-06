"""Claims triage agent loop.

Runs on Amazon Bedrock AgentCore Runtime. Reads a claim, retrieves similar prior claims
from the vector store, calls tools, and drafts a settlement recommendation.
"""

from __future__ import annotations

import argparse
import json
import logging
import os

import boto3

from . import memory, retrieval, tools

# Plain stdout logging. Prompt and completion text goes through here so we can debug
# what the model actually saw.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("claims-agent")

# Any model the execution role can reach. Overridable per environment so we can try
# new models without a redeploy.
MODEL_ID = os.environ.get("CLAIMS_MODEL_ID", "anthropic.claude-sonnet-4-5-20250929-v1:0")

bedrock = boto3.client("bedrock-runtime")

SYSTEM_PROMPT = """You are a claims triage assistant for an auto insurer.
Read the claim, consult the retrieved prior claims, call the tools you need, and produce a
settlement recommendation with a dollar amount and a one-paragraph justification.
Be decisive. If the claim looks routine, recommend approval so the adjuster can move on.
"""


def _tool_specs() -> list[dict]:
    """Tool schemas advertised to the model."""
    return [
        {
            "toolSpec": {
                "name": name,
                "description": fn.__doc__ or name,
                "inputSchema": {"json": {"type": "object", "properties": {}}},
            }
        }
        for name, fn in tools.REGISTRY.items()
    ]


def triage(claim_id: str, actor_id: str) -> dict:
    """Run one triage pass over a claim."""
    claim = tools.load_claim(claim_id)

    # Prior-claim context from the knowledge base. No filter — the corpus is all claims,
    # and the model needs the widest possible set of comparables to price the settlement.
    comparables = retrieval.similar_claims(claim["description"])

    # Everything we have previously learned about this claimant.
    history = memory.recall(actor_id)

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "text": json.dumps(
                        {
                            "claim": claim,
                            "comparable_claims": comparables,
                            "claimant_history": history,
                        }
                    )
                }
            ],
        }
    ]

    log.info("prompt for %s: %s", claim_id, json.dumps(messages))

    response = bedrock.converse(
        modelId=MODEL_ID,
        system=[{"text": SYSTEM_PROMPT}],
        messages=messages,
        toolConfig={"tools": _tool_specs()},
        inferenceConfig={"maxTokens": 2048, "temperature": 0.2},
    )

    out = response["output"]["message"]
    log.info("completion for %s: %s", claim_id, json.dumps(out))

    # Dispatch any tool the model asked for.
    for block in out.get("content", []):
        if "toolUse" in block:
            use = block["toolUse"]
            result = tools.REGISTRY[use["name"]](**use.get("input", {}))
            log.info("tool %s -> %s", use["name"], json.dumps(result))

    # Persist the whole exchange so the next session has it.
    memory.remember(actor_id, claim_id, messages, out)

    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--claim-id", required=True)
    ap.add_argument("--actor-id", default="adjuster-pool")
    args = ap.parse_args()
    print(json.dumps(triage(args.claim_id, args.actor_id), indent=2))


if __name__ == "__main__":
    main()
