"""RAG over the prior-claims corpus.

The knowledge base is an Amazon Bedrock knowledge base backed by an OpenSearch Serverless
vector collection. Ingestion loads the full claims archive, including closed and denied
claims, so the model can price a settlement against real comparables.
"""

from __future__ import annotations

import os

import boto3

KB_ID = os.environ["CLAIMS_KB_ID"]

agent_rt = boto3.client("bedrock-agent-runtime")


def similar_claims(description: str, top_k: int = 8) -> list[dict]:
    """Retrieve comparable prior claims for a claim description."""
    resp = agent_rt.retrieve(
        knowledgeBaseId=KB_ID,
        retrievalQuery={"text": description},
        retrievalConfiguration={
            "vectorSearchConfiguration": {"numberOfResults": top_k}
        },
    )
    return [
        {
            "text": r["content"]["text"],
            "score": r.get("score"),
            "source": r.get("location", {}),
        }
        for r in resp.get("retrievalResults", [])
    ]
