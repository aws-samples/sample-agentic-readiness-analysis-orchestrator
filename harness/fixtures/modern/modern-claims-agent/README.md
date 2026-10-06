# Claims Triage Agent

An **agentic** insurance-claims triage service. A **large language model** on **Amazon Bedrock**
reads a submitted claim, retrieves similar prior claims from a **vector store**, calls internal
tools to pull policy and payment data, and drafts a settlement recommendation for an adjuster.

Deployed on **Amazon Bedrock AgentCore** Runtime, fronted by an AgentCore Gateway that exposes the
internal tools over **MCP**. Long-term memory keeps per-claimant context across sessions.

## Architecture

```
adjuster UI ──► AgentCore Gateway (MCP) ──► AgentCore Runtime ──► Bedrock (Claude)
                      │                            │
                      │                            ├──► AgentCore Memory (per-claimant)
                      ├──► policy-lookup tool      └──► OpenSearch Serverless (vector store, RAG)
                      ├──► payment-history tool
                      └──► settlement-writer tool
```

## Components

| Path | What it is |
|---|---|
| `src/claims_agent/agent.py` | Agent loop — Bedrock `Converse` + tool dispatch |
| `src/claims_agent/tools.py` | The three MCP tools the gateway exposes |
| `src/claims_agent/memory.py` | AgentCore Memory read/write for claimant context |
| `src/claims_agent/retrieval.py` | RAG over the prior-claims knowledge base |
| `infra/agent-runtime.yaml` | AgentCore Runtime + Gateway + Memory (CloudFormation) |
| `infra/agent-iam.yaml` | Execution role for the agent |

## Running locally

```bash
pip install -r requirements.txt
export CLAIMS_MODEL_ID=anthropic.claude-sonnet-4-5-20250929-v1:0
python -m claims_agent.agent --claim-id CLM-10423
```

## Status

Live for the auto-claims book since March. Property claims are next.

The adjuster is expected to review every recommendation before it is sent, but the
`settlement-writer` tool can also post directly to the claims system of record when the agent is
run in unattended batch mode (see `docs/batch-mode.md`).

## Known gaps

Tracked in `docs/security-review-TODO.md`. Nothing there is currently blocking the auto-claims
rollout.
