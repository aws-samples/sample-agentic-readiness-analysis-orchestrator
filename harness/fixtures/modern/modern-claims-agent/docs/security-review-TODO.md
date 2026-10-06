# Security review — open items

Raised by the platform team during the auto-claims launch review. None of these are blocking
the current rollout; revisit before the property-claims book goes live.

## Open

- **Guardrails.** No Bedrock guardrail is attached to the agent's invocation path. We rely on
  the system prompt to keep the model on-task. A prompt-injection test against the claim
  `description` field has not been run — a claimant controls that text.
- **Model access.** The execution role allows `bedrock:InvokeModel` on `Resource: '*'`. Any
  model enabled in the account is reachable, including ones that have not been through model
  review. We wanted per-environment model switching without a redeploy.
- **Gateway auth.** The tool gateway is `AuthorizerType: NONE`. It sits on a private subnet
  route from the adjuster UI, so we treated network reachability as sufficient. Anyone who can
  reach the endpoint can call any tool.
- **Tool exposure.** `tools/list` returns the full registry to every caller, including
  `settlement_writer`, which moves money. No per-caller tool allow-list.
- **Runtime is directly invocable.** The runtime ARN accepts SigV4 from any principal in the
  account, so the gateway is not the only path in. Gateway-side controls are therefore
  advisory.
- **Memory namespace.** All claimants share `/claims/shared`. Anything written for one
  claimant is retrievable in another claimant's session. No per-actor partition.
- **Memory content.** We write the raw exchange, which includes claimant SSN and bank routing
  numbers pulled by the tools. Nothing redacts before the write.
- **Retrieval scope.** The knowledge base holds the entire claims archive with no
  per-principal filter, so retrieval can surface another claimant's record into a prompt.
- **Prompts in logs.** `agent.py` logs the full prompt and completion to CloudWatch at INFO.
  Retention is 10 years and there is no data-protection policy on the log group.
- **Shell access.** The single execution role includes
  `bedrock-agentcore:InvokeAgentRuntimeCommandShell` alongside ordinary invoke, so anything
  that can invoke the agent can also open a shell in a live session.
- **Shared role.** Runtime and tool Lambda share `claims-agent-execution`. A tool compromise
  gets the agent's model and memory permissions too.
- **No eval gate.** Releases are promoted on unit tests only. No safety or tool-correctness
  evaluation runs before deploy.
- **No session tracing.** We cannot reconstruct an end-to-end agent session across gateway,
  runtime, and memory when an adjuster disputes a recommendation.
- **MFA.** The deploy role that can change the agent, its guardrails, or its model is
  reachable without MFA from CI.

## Closed

- Secrets moved out of environment variables into Secrets Manager (done March).
- Container image pinned to a digest in prod (done April).
