# Portfolio Agentic Readiness Assessment Report

**Date**: 2026-04-15
**Services Assessed**: 5
**Portfolio Context**: Evaluating the e-commerce platform portfolio for both autonomous AI agent integration and cloud-native modernization. The team is building a customer support agent that handles order inquiries, processes returns, and manages inventory restocking — while simultaneously modernizing legacy monoliths into containerized microservices on EKS.

---

## Executive Dashboard

### Readiness Distribution

| Profile | Services | Percentage | Description |
|---------|----------|------------|-------------|
| ✅ Agent-Ready | 0 | 0% | 0 blockers, 0–2 risks — broad agent deployment |
| 🟡 Pilot-Ready | 0 | 0% | 0 blockers, 3–5 risks — narrow pilot only |
| 🟠 Remediation Required | 1 | 20% | 1–2 blockers — remediate before any agent deployment |
| ❌ Not Agent-Integrable | 4 | 80% | 3+ blockers — deferred or descoped |

### Portfolio Summary

| Metric | Value |
|--------|-------|
| Total Services Assessed | 5 |
| Services Ready for Agents (Agent-Ready + Pilot-Ready) | 0 (0%) |
| Services Requiring Remediation | 5 (100%) |
| Total Unique BLOCKERs across Portfolio | 7 distinct question IDs |
| Total Unique RISKs across Portfolio | 33 distinct question IDs |
| Cross-Cutting BLOCKERs (same blocker in 2+ repos) | 7 |
| Cross-Cutting RISKs (same risk in 3+ repos) | 32 |
| Services with Write-Enabled Agent Scope | 5 (100%) |
| Services with Read-Only Agent Scope | 0 (0%) |

### Repo Type Distribution

| Repo Type | Count | Percentage |
|-----------|-------|------------|
| application | 4 | 80% |
| infrastructure-only | 1 | 20% |
| deployment-config | 0 | 0% |
| monorepo | 0 | 0% |
| library | 0 | 0% |

## Cross-Cutting BLOCKERs — Same Blocker in 2+ Repos

> These are BLOCKER-severity questions that appear in 2 or more repositories.
> They represent portfolio-wide agentic readiness gaps requiring coordinated remediation.
> Questions scored as N/A for a service do not count as gaps for that service.

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER in 4 of 4 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
- **N/A Services**: None (eks-saas-gitops scored INFO — IRSA-based machine identity is well-established)
- **Common Finding**: No machine identity authentication across any application service. Session-based auth (local-monolith), OAuth2 configured but disabled via `permitAll()` (unishop-monolith), completely open API Gateways (aws-microservices), and human-only Cognito User Pool with no client credentials flow (books-api). None of the 4 application services can authenticate an agent as a machine principal.
- **Root Cause Pattern**: Each service was designed for human users only — session cookies, browser-based OAuth implicit flow, or no auth at all. No service has implemented the OAuth2 client credentials grant required for machine-to-machine authentication.
- **Portfolio-Level Remediation**:
  - **Approach**: Platform-level fix — deploy a centralized Amazon Cognito User Pool with Resource Servers and client_credentials grant for all services
  - **Immediate Action**: Deploy a shared Cognito User Pool with custom scopes per service (e.g., `orders/read`, `catalog/write`, `inventory/read`). Issue unique client IDs per agent per service.
  - **Target State**: All 4 application services require a valid OAuth2 bearer token from the shared Cognito pool. Each agent identity is a registered app client with scoped permissions. Audit logs attribute every API call to a specific principal.
  - **Estimated Effort**: Medium
  - **Priority**: Critical — identity is the foundation for all other security controls
  - **Dependencies**: None — this must be resolved first

### AUTH-Q7: Immutable Audit Logging

- **Severity**: BLOCKER in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Conditional**: All 5 services have agent_scope "write-enabled" — evaluated as BLOCKER for all
- **Common Finding**: No immutable, tamper-evident audit trail in any service. unishop-monolith has CloudWatch Logs with only 7-day retention and unstructured `System.out.println()` output. aws-microservices uses `console.log` with full event payloads (including PII) and no log retention policies. local-monolith has PHP error logging with no structured audit records. books-api has API Gateway logging and X-Ray tracing but no CloudTrail and no application-level audit of authenticated principals. eks-saas-gitops has zero CloudTrail, CloudWatch Log Groups, or S3 object lock across all Terraform files.
- **Root Cause Pattern**: No service has implemented compliance-grade audit logging. Logs are either absent, unstructured, mutable, or lack principal attribution. No CloudTrail is configured in any service's IaC.
- **Portfolio-Level Remediation**:
  - **Approach**: Platform-level fix — deploy an organization-level CloudTrail trail with S3 object lock, plus per-service structured logging standards
  - **Immediate Action**: Deploy a centralized CloudTrail trail writing to an S3 bucket with object lock (WORM). Enable EKS control plane audit logging on eks-saas-gitops. Implement a structured JSON logging standard across all services.
  - **Target State**: Every write operation across the portfolio logs: authenticated principal, action performed, resource affected, timestamp, and request ID. Logs are stored immutably in S3 with object lock. CloudTrail captures all API Gateway, Lambda, and EKS API invocations.
  - **Estimated Effort**: Medium
  - **Priority**: Critical — compliance requirement for write-enabled agent scope
  - **Dependencies**: Resolve AUTH-Q1 first — you need machine identity before audit logs can attribute actions to specific agents

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER in 3 of 4 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith
- **Non-BLOCKER Services**: books-api (RISK — book catalog data is non-sensitive bibliographic metadata), eks-saas-gitops (N/A — infrastructure-only)
- **Common Finding**: PII stored without classification or field-level protection. unishop-monolith stores email, first_name, last_name in plaintext MySQL. aws-microservices stores firstName, lastName, email, address, cardInfo (potential PCI violation) in DynamoDB with no classification tags. local-monolith stores customer_name, customer_email, shipping_address in plaintext MySQL. No Macie integration, no field-level encryption, no data classification tags on any resource across any service.
- **Root Cause Pattern**: Services store customer PII as part of normal business operations but have never undergone data classification. PII fields are exposed directly in API responses with no redaction or filtering.
- **Portfolio-Level Remediation**:
  - **Approach**: Hybrid — portfolio-level data classification policy + per-service field-level tagging and redaction
  - **Immediate Action**: Define a portfolio data classification policy identifying PII field categories (email, name, address, payment). Tag all database tables and DynamoDB tables with `data-classification` resource tags. Implement field-level redaction in API responses.
  - **Target State**: All data stores tagged with classification. PII fields identified, tagged, and subject to field-level access controls. API responses support scope-based field filtering — agents receive only the PII necessary for their task. Amazon Macie scanning for PII detection.
  - **Estimated Effort**: High
  - **Priority**: High
  - **Dependencies**: AUTH-Q1 (need identity to enforce per-agent PII access controls)

### DATA-Q2: Data Residency and Sovereignty

- **Severity**: BLOCKER in 4 of 4 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
- **Conditional**: All 4 have agent_scope "write-enabled" — evaluated as BLOCKER. eks-saas-gitops is N/A (infrastructure-only).
- **Common Finding**: No data residency documentation or controls in any application service. unishop-monolith has no region restrictions in CloudFormation. aws-microservices has the CDK `env` property commented out (region-agnostic). local-monolith deploys via Docker with no region awareness. books-api has a single-region DynamoDB deployment but no formal residency documentation. Write-enabled agents transmitting PII to LLM providers in different jurisdictions create legal exposure across all services.
- **Root Cause Pattern**: No service has documented which data residency regulations apply or which regions are approved for data processing. Region pinning is absent or undocumented.
- **Portfolio-Level Remediation**:
  - **Approach**: Platform-level fix — document portfolio data residency policy, pin all stacks to specific regions, specify approved LLM endpoints
  - **Immediate Action**: Create a portfolio-level `DATA_RESIDENCY.md` documenting applicable regulations (GDPR for EU customers, LGPD for Brazilian customers), approved AWS regions, and approved LLM endpoint locations. Pin all CDK/CloudFormation stacks to explicit regions. For books-api (non-PII bibliographic data), document the residency exemption.
  - **Target State**: Data residency requirements documented and enforced at the infrastructure level. All stacks deployed to specific approved regions. Agent configurations specify Amazon Bedrock endpoints in the same region as data storage. PII redacted or anonymized before cross-region LLM transmission.
  - **Estimated Effort**: Medium
  - **Priority**: High
  - **Dependencies**: DATA-Q1 (classify data before applying residency controls per field)

### STATE-Q1: Compensation and Rollback

- **Severity**: BLOCKER in 4 of 4 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
- **Conditional**: All 4 have agent_scope "write-enabled" — evaluated as BLOCKER. eks-saas-gitops is N/A (infrastructure-only).
- **Common Finding**: No saga pattern or compensation logic in any application service. unishop-monolith has `@Transactional` on individual operations but no cross-operation coordination. aws-microservices has a 4-step checkout flow (basket → EventBridge → SQS → order) with no error compensation — partial failures leave inconsistent state. local-monolith has a multi-step fulfillment workflow (validate → assign-warehouse → pick → pack → ship) with each step committing independently. books-api has only a single `PutItem` with no delete endpoint for rollback.
- **Root Cause Pattern**: All services implement single-operation transactions but have no mechanism for multi-step workflow compensation. An agent executing a sequence of API calls has no way to undo previously successful steps if a subsequent step fails.
- **Portfolio-Level Remediation**:
  - **Approach**: Per-service fix — each service needs individual compensation endpoints and workflow orchestration
  - **Immediate Action**: Implement explicit undo/compensation endpoints for each service's write operations. Add DLQ to aws-microservices SQS OrderQueue. Add DELETE /books/{isbn} to books-api. Implement compensation endpoints for local-monolith's fulfillment workflow steps.
  - **Target State**: All multi-step write workflows have compensating actions defined. AWS Step Functions used for complex agent workflows with error handling and compensation states. DLQ monitoring with alerts for failed compensations.
  - **Estimated Effort**: High
  - **Priority**: High
  - **Dependencies**: API-Q4 (idempotency is a prerequisite for safe compensation — you must be able to retry compensation actions)

### API-Q4: Idempotent Write Operations

- **Severity**: BLOCKER in 4 of 4 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
- **Conditional**: All 4 have agent_scope "write-enabled" — evaluated as BLOCKER. eks-saas-gitops is N/A (infrastructure-only).
- **Common Finding**: No idempotency key support on write endpoints in any application service. unishop-monolith uses `INSERT IGNORE` (database-level, not application-level idempotency). aws-microservices generates UUIDs server-side with `uuidv4()` and has no idempotency on checkout. local-monolith generates order IDs with `uniqid('order-')` with no deduplication. books-api uses `PutItem` with no `ConditionExpression` — silently overwrites existing records.
- **Root Cause Pattern**: No service implements the `Idempotency-Key` header pattern. Agent retries or LLM non-deterministic duplicate tool calls will create duplicate orders, duplicate products, or silently overwrite records.
- **Portfolio-Level Remediation**:
  - **Approach**: Hybrid — adopt AWS Lambda Powertools idempotency utility as portfolio standard + per-service implementation
  - **Immediate Action**: Add `Idempotency-Key` header support to all write endpoints. For serverless services (aws-microservices, books-api), use Lambda Powertools idempotency utility with DynamoDB backing table. For container/EC2 services (local-monolith, unishop-monolith), implement idempotency middleware with a deduplication table.
  - **Target State**: All write endpoints across the portfolio accept and enforce idempotency keys. Duplicate requests return the original response without re-executing side effects.
  - **Estimated Effort**: Medium
  - **Priority**: High
  - **Dependencies**: None

### ENG-Q6: Cross-Origin and Network Policies

- **Severity**: BLOCKER in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: Permissive or absent network security across all services. unishop-monolith has wildcard CORS allowing all methods from all origins with security groups open to 0.0.0.0/0. aws-microservices has no CORS on any API Gateway, no VPC attachment, no WAF, and publicly accessible APIs. local-monolith has no CORS headers, no security groups, and port 8080 exposed directly. books-api has no CORS on the SAM API Gateway, no WAF, no resource policies. eks-saas-gitops has EKS API server publicly accessible, Argo Workflows and Kubecost exposed via internet-facing LoadBalancers without authentication, and Kubecost network policies disabled.
- **Root Cause Pattern**: Network security was not designed for machine-speed agent access. Services are either completely open, behind permissive CORS, or exposed directly to the internet without WAF or API Gateway protection.
- **Portfolio-Level Remediation**:
  - **Approach**: Hybrid — deploy portfolio-wide WAF rules + per-service CORS and network policy configuration
  - **Immediate Action**: Deploy AWS WAF with rate limiting rules for all public-facing API Gateways. Add CORS configuration to each service. Set `cluster_endpoint_public_access = false` on eks-saas-gitops EKS cluster. Change Argo Workflows and Kubecost LoadBalancers to internal.
  - **Target State**: All services behind API Gateways with WAF protection. CORS restricted to specific allowed origins. EKS API endpoint private-only. Network policies enabled for all EKS namespaces. Security groups restrict inbound to API Gateways only.
  - **Estimated Effort**: Medium
  - **Priority**: High
  - **Dependencies**: None — can be resolved in parallel with identity and data remediation

## Cross-Cutting RISKs — Same Risk in 3+ Repos

> These are RISK-severity questions that appear in 3 or more repositories.
> They represent portfolio-wide patterns warranting coordinated attention.
> Questions scored as N/A for a service do not count as gaps for that service.

### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: Overly broad permissions across the portfolio. Application services lack fine-grained RBAC (permitAll, coarse roles, ReadWrite grants). eks-saas-gitops has AdministratorAccess on IRSA roles.
- **Compensating Controls**: Deploy API Gateway resource policies or reverse proxy rules per service to restrict agent access to specific endpoints. For eks-saas-gitops, scope Argo Workflows and TF Controller IRSA roles to specific namespaces and API groups. Define per-agent permission boundaries in the agent orchestration layer to enforce least privilege until application-level RBAC is implemented.
- **Portfolio-Level Recommendation**: Define a portfolio-wide RBAC model with agent-specific roles scoped to minimum required operations per service.
- **Estimated Effort**: Medium

### AUTH-Q3: Action-Level Authorization — RISK in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: No action-level authorization differentiation. Application services cannot restrict an agent to read-only operations. eks-saas-gitops has wildcard ClusterRoles.
- **Compensating Controls**: Implement action-level enforcement at the API Gateway or reverse proxy layer by mapping HTTP methods (GET vs POST/PUT/DELETE) to allow/deny rules per agent identity. For eks-saas-gitops, replace wildcard ClusterRoles with namespace-scoped Roles granting only required verbs. Restrict agents to read-only endpoints during initial pilot phases.
- **Portfolio-Level Recommendation**: Implement per-endpoint permission checks in all services. Replace wildcard K8s ClusterRoles with scoped Roles.
- **Estimated Effort**: Medium

### AUTH-Q6: Credential Management — RISK in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: Hardcoded credentials (unishop-monolith application.properties, CloudFormation), hardcoded PHP fallback (local-monolith), plaintext K8s secrets (eks-saas-gitops), no Secrets Manager integration (books-api, aws-microservices).
- **Compensating Controls**: Immediately remove all hardcoded credential fallbacks from application code. Use Docker secrets or environment-specific `.env` files with restricted file permissions for containerized services. For eks-saas-gitops, enable Kubernetes Secrets encryption at rest via EKS envelope encryption. Implement manual credential rotation procedures until automated rotation is deployed.
- **Portfolio-Level Recommendation**: Standardize on AWS Secrets Manager for all credentials. Implement automatic rotation. Migrate all hardcoded credentials immediately.
- **Estimated Effort**: Medium

### AUTH-Q8: Agent Identity Suspension — RISK in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: No mechanism to suspend individual agent identities. Suspension requires destroying accounts, disabling entire services, or Terraform changes.
- **Compensating Controls**: Implement IP-based blocking at the API Gateway or WAF layer as an emergency kill switch for misbehaving agents. For Cognito-backed services, configure app client disable as a suspension mechanism. For eks-saas-gitops, annotate IRSA roles with a suspension runbook that documents the Terraform changes needed for immediate revocation. Deploy a centralized agent identity registry that can instantly revoke access tokens.
- **Portfolio-Level Recommendation**: Design all agent identities as individually revocable Cognito app clients or API keys with instant suspension capability.
- **Estimated Effort**: Low

### AUTH-Q4: Identity Propagation — RISK in 4 of 4 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api (eks-saas-gitops N/A)
- **Common Finding**: No JWT extraction, no user context propagation, self-asserted identity in request bodies. OAuth2 libraries present but unused in unishop-monolith.
- **Compensating Controls**: For the initial pilot, leverage each service's single-process architecture where user context is inherently available within the request scope. Log the originating user/agent identity in all operations to maintain traceability. Use API Gateway request context to inject verified identity claims into backend requests.
- **Portfolio-Level Recommendation**: Derive user identity from JWT claims via Cognito. Propagate identity context through SecurityContext or Lambda event requestContext.
- **Estimated Effort**: Medium

### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User — RISK in 4 of 4 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api (eks-saas-gitops N/A)
- **Common Finding**: No distinction between agent acting autonomously and agent acting on behalf of a user. No separate auth flows or audit fields.
- **Compensating Controls**: For the initial pilot, restrict all agents to agent-as-self mode with dedicated service accounts. Log all agent actions as agent-initiated in audit records to maintain a clear attribution trail. Include both agent identity and delegating user identity (if applicable) in custom log fields until formal OAuth2 token exchange flows are implemented.
- **Portfolio-Level Recommendation**: Implement two OAuth2 flows: client_credentials for agent-as-self, token exchange for agent-on-behalf-of-user.
- **Estimated Effort**: Medium

### API-Q2: Machine-Readable API Specification — RISK in 4 of 4 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api (eks-saas-gitops N/A)
- **Common Finding**: No OpenAPI, Swagger, or any machine-readable spec in any application service. APIs defined only in source code.
- **Compensating Controls**: Manually author agent tool definitions from code analysis for the initial pilot. Use API recording/proxy tools to capture request/response pairs and generate initial OpenAPI specs. For serverless services (aws-microservices, books-api), export API definitions from API Gateway console as a starting point.
- **Portfolio-Level Recommendation**: Generate OpenAPI 3.0 specs for all services. Use springdoc-openapi for Java, API Gateway export for serverless.
- **Estimated Effort**: Low

### API-Q3: Structured Error Responses — RISK in 4 of 4 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api (eks-saas-gitops N/A)
- **Common Finding**: No structured error codes, no retryable indicators. unishop-monolith returns bare 400 status. aws-microservices leaks stack traces. local-monolith has inconsistent formats. books-api returns empty 500 bodies.
- **Compensating Controls**: Map known HTTP status codes to retry behavior in agent tool definitions (e.g., 5xx → retry with backoff, 4xx → do not retry). Implement a thin error-mapping middleware or API Gateway response transformation to normalize error formats before they reach agents. Configure agent retry policies based on status codes rather than error message parsing.
- **Portfolio-Level Recommendation**: Standardize on `{"error": {"code": "...", "message": "...", "retryable": boolean}}` format across all services.
- **Estimated Effort**: Low

### API-Q5: API Versioning and Deprecation — RISK in 4 of 4 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api (eks-saas-gitops N/A)
- **Common Finding**: No API versioning on any service. Unversioned paths (e.g., `/unicorns`, `/product`, `/books`). No changelogs or deprecation policies.
- **Compensating Controls**: Freeze the current API surface during initial agent integration — no breaking changes without coordinated agent tool definition updates. Add API contract tests (ENG-Q2) to detect breaking changes before deployment. Document current endpoint behavior in agent tool definitions as the de facto v1 contract.
- **Portfolio-Level Recommendation**: Add `/v1/` URL prefix to all API endpoints. Establish portfolio-wide 90-day deprecation notice policy.
- **Estimated Effort**: Low

### API-Q7: Asynchronous Operation Support — RISK in 4 of 4 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api (eks-saas-gitops N/A)
- **Common Finding**: All operations synchronous (except aws-microservices checkout which is fire-and-forget with no status tracking). No job status polling or webhook patterns.
- **Compensating Controls**: Set generous HTTP timeouts on agent clients for the initial pilot (30s+ for write operations). Monitor actual response times across all services and implement async patterns only for operations exceeding 5 seconds. For aws-microservices checkout, add a status query endpoint so agents can verify order completion after the fire-and-forget submission.
- **Portfolio-Level Recommendation**: Implement async patterns (job submission + polling) for operations exceeding 5 seconds. Add status tracking to aws-microservices checkout.
- **Estimated Effort**: Medium

### STATE-Q2: Queryable Current State — RISK in 4 of 4 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api (eks-saas-gitops N/A)
- **Common Finding**: Incomplete state queryability. Missing individual resource GET endpoints. aws-microservices requires exact orderDate for queries.
- **Compensating Controls**: Add individual resource GET endpoints (GET by ID) for the most critical agent-consumed entities as a targeted fix. Use existing list endpoints with client-side filtering in agent tool definitions for the initial pilot. For aws-microservices, document the orderDate query requirement in agent tool definitions to ensure correct parameter usage.
- **Portfolio-Level Recommendation**: Add individual resource GET endpoints (GET by ID) to all services for agent read-before-write patterns.
- **Estimated Effort**: Low

### STATE-Q3: Concurrency Controls — RISK in 4 of 4 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api (eks-saas-gitops N/A)
- **Common Finding**: No optimistic locking. No version fields or ETags. Last-writer-wins on concurrent writes across all services.
- **Compensating Controls**: Add `SELECT ... FOR UPDATE` to critical MySQL queries (unishop-monolith, local-monolith) to serialize concurrent access on high-contention resources like inventory. For DynamoDB services (aws-microservices, books-api), add `ConditionExpression` with version attributes on write operations. Limit agent concurrency in the orchestration layer to reduce the likelihood of write conflicts during the initial pilot.
- **Portfolio-Level Recommendation**: Add version attributes and conditional writes/ETags to all data stores.
- **Estimated Effort**: Medium

### STATE-Q4: Circuit Breakers and Resilience — RISK in 4 of 4 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api (eks-saas-gitops N/A)
- **Common Finding**: No circuit breakers, no retry logic, no timeout configurations. Database/SDK failures cascade directly.
- **Compensating Controls**: Configure HTTP connection and read timeouts on all database and SDK clients across services. Add health check endpoints that agents can query before initiating multi-step workflows. Implement retry logic with exponential backoff in the agent orchestration layer rather than within each service. Monitor service health via container/Lambda health checks as a basic liveness signal.
- **Portfolio-Level Recommendation**: Add Resilience4j (Java) or SDK retry configuration (Node.js) across all services. Configure connection timeouts.
- **Estimated Effort**: Medium

### STATE-Q5: Rate Limiting and Throttling — RISK in 4 of 4 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api (eks-saas-gitops N/A)
- **Common Finding**: No explicit rate limiting on any application service. Default API Gateway limits only where applicable.
- **Compensating Controls**: Deploy nginx or API Gateway with rate limiting rules in front of services that currently lack them (local-monolith, unishop-monolith). For services already behind API Gateway (aws-microservices, books-api), configure usage plans with per-agent API key throttling. Implement per-agent rate limits in the agent orchestration layer as an additional guardrail.
- **Portfolio-Level Recommendation**: Deploy API Gateway with usage plans and per-agent throttling for all services.
- **Estimated Effort**: Medium

### STATE-Q6: Blast Radius and Transaction Limits — RISK in 4 of 4 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api (eks-saas-gitops N/A)
- **Common Finding**: No per-agent transaction limits. Unbounded scans (SELECT * / DynamoDB Scan with no Limit). No spend caps or operation quotas.
- **Compensating Controls**: Implement transaction limits in the agent orchestration layer (e.g., max orders per hour, max refund amount per session) as the first line of defense. Add approval gates for operations exceeding configurable thresholds. Add `LIMIT` clauses to all SQL queries and `Limit` parameters to all DynamoDB Scan operations to cap result sizes at the application level.
- **Portfolio-Level Recommendation**: Add Limit parameters to all list operations. Implement per-agent operation quotas via API Gateway usage plans.
- **Estimated Effort**: Medium

### STATE-Q7: Infrastructure Capacity for Agent Traffic — RISK in 4 of 4 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api (eks-saas-gitops N/A)
- **Common Finding**: No load testing. unishop-monolith on single t3.small EC2. local-monolith on single Docker container. aws-microservices uses deprecated NODEJS_14_X runtime. No provisioned concurrency.
- **Compensating Controls**: Tune Apache/Nginx worker configurations for concurrent connections on container-based services. Upgrade aws-microservices Lambda runtime from deprecated NODEJS_14_X to NODEJS_20_X immediately (also a security concern). Monitor container CPU/memory usage and Lambda concurrent executions with CloudWatch alerts to detect capacity issues early. Limit agent request concurrency in the orchestration layer during initial pilot.
- **Portfolio-Level Recommendation**: Conduct load testing for all services simulating agent traffic patterns. Upgrade runtimes. Add auto-scaling.
- **Estimated Effort**: Medium

### HITL-Q1: Draft/Pending State — RISK in 4 of 4 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api (eks-saas-gitops N/A)
- **Common Finding**: All writes immediately committed. No draft/pending state for agent proposals requiring human review.
- **Compensating Controls**: For the initial pilot, restrict agents to proposing actions (recording recommendations in a separate tracking system) rather than executing writes directly. Use the existing return approval pattern in local-monolith as a template for adding draft states to other services. Implement a portfolio-wide agent action queue where proposed writes are logged for human review before execution.
- **Portfolio-Level Recommendation**: Add status fields (draft/pending/confirmed) to records. Agent-created records default to draft.
- **Estimated Effort**: Medium

### HITL-Q2: Configurable Approval Gates — RISK in 4 of 4 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api (eks-saas-gitops N/A)
- **Common Finding**: No runtime approval gates. Only local-monolith has a return approval pattern. No Step Functions with human approval tasks.
- **Compensating Controls**: Implement approval logic in the agent orchestration layer (e.g., require human approval for orders exceeding $500, refunds exceeding $100, or bulk operations). Use the existing local-monolith return approval workflow (`POST /api/admin/approve-return`) as the design pattern for other services. Deploy a centralized approval queue using Amazon SQS + Step Functions `waitForTaskToken` for high-risk operations across the portfolio.
- **Portfolio-Level Recommendation**: Implement Step Functions with `waitForTaskToken` for high-risk operations across services.
- **Estimated Effort**: High

### HITL-Q3: Sandbox/Staging Environment — RISK in 4 of 4 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api (eks-saas-gitops N/A)
- **Common Finding**: No production-equivalent staging environments. books-api has the best staging (CI/CD pipeline with staging deploy + E2E tests). Others have minimal or no staging.
- **Compensating Controls**: Use local-monolith's docker-compose environment and books-api's CI/CD staging pipeline as baseline models for other services. Create enhanced seed data scripts for realistic agent testing scenarios. Deploy separate AWS accounts or resource prefixes for staging environments using existing IaC templates. Run agent integration tests against books-api's staging environment first as a proof-of-concept.
- **Portfolio-Level Recommendation**: Create staging environments for all services with production-equivalent data shapes and seed data generators.
- **Estimated Effort**: Medium

### DATA-Q3: Selective Query Support — RISK in 4 of 4 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api (eks-saas-gitops N/A)
- **Common Finding**: No pagination, filtering, or result size limits. All list endpoints return unbounded result sets.
- **Compensating Controls**: Limit the number of records processed by the agent at the orchestration layer (e.g., truncate responses exceeding 50 items). Pre-filter data in agent tool definitions by specifying query parameters or status filters where available. Add `LIMIT 50` to MySQL queries and `Limit: 50` to DynamoDB Scan operations as a quick application-level fix across all services.
- **Portfolio-Level Recommendation**: Add limit/offset/cursor pagination to all list endpoints with a default limit of 50.
- **Estimated Effort**: Low

### DATA-Q4: System of Record Designations — RISK in 3 of 4 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith (books-api INFO, eks-saas-gitops N/A)
- **Common Finding**: No documented system-of-record designations. DMS replication creates ambiguous copies. Denormalized data in checkout flows.
- **Compensating Controls**: Document the current authoritative data sources per entity (e.g., unishop-monolith MySQL for unicorn products, aws-microservices DynamoDB for orders, local-monolith MySQL for legacy products) in agent tool documentation. Establish a naming convention for data stores that indicates ownership. Restrict agents to writing only to the authoritative source for each entity type.
- **Portfolio-Level Recommendation**: Document SoR per entity. Establish clear data ownership before service decomposition.
- **Estimated Effort**: Low

### DATA-Q5: Reliable Timestamps — RISK in 4 of 4 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api (eks-saas-gitops N/A)
- **Common Finding**: Incomplete timestamps. unishop-monolith has @JsonIgnore on timestamps. aws-microservices has timestamps only on orders. local-monolith has no explicit UTC. books-api has no timestamps at all.
- **Compensating Controls**: Set server/container timezones to UTC via Dockerfile or environment configuration across all services. Document the timezone assumption in agent tool definitions. For books-api, add `createdAt`/`updatedAt` DynamoDB attributes using ISO 8601 UTC format as a quick fix. Remove `@JsonIgnore` from timestamp fields in unishop-monolith to expose them in API responses.
- **Portfolio-Level Recommendation**: Add created_at/updated_at ISO 8601 UTC fields to all records across all services.
- **Estimated Effort**: Low

### DATA-Q6: Data Freshness Signaling — RISK in 4 of 4 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api (eks-saas-gitops N/A)
- **Common Finding**: No Cache-Control, X-Data-Age, or consistency-level headers in any API response.
- **Compensating Controls**: Document in agent tool definitions that all data is served directly from primary data stores with strong consistency (no caching layers). Add `Cache-Control: no-cache` headers to all GET endpoints to explicitly signal data is always fresh. For DynamoDB services, document whether queries use eventually consistent or strongly consistent reads so agents understand consistency guarantees.
- **Portfolio-Level Recommendation**: Add Cache-Control and consistency headers to all GET endpoints. Document consistency model per service.
- **Estimated Effort**: Low

### DATA-Q7: PII Redaction in Logs — RISK in 4 of 4 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api (eks-saas-gitops N/A)
- **Common Finding**: PII leaks into logs across all services. aws-microservices logs full checkout payloads including cardInfo. unishop-monolith uses e.printStackTrace(). No scrubbing or masking anywhere.
- **Compensating Controls**: Add custom error handlers that sanitize exception messages before logging across all services. Configure CloudWatch Logs data protection policies to automatically detect and mask PII patterns (email, credit card, name) in log streams. Set aggressive log retention policies (7–30 days) to limit PII exposure windows. Remove full event payload logging from aws-microservices Lambda functions immediately (cardInfo logging is a potential PCI violation).
- **Portfolio-Level Recommendation**: Implement structured logging with PII field redaction. Add CloudWatch Logs data protection policies.
- **Estimated Effort**: Medium

### DISC-Q1: Schema Documentation and Versioning — RISK in 4 of 4 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api (eks-saas-gitops N/A)
- **Common Finding**: No versioned schemas, no migration frameworks, no schema registry. Schemas defined only in application code.
- **Compensating Controls**: Extract current database schemas into standalone documentation files (SQL DDL exports for MySQL services, DynamoDB table definitions for serverless services) as a quick first step. Freeze schema changes during initial agent integration — treat the current schema as the stable contract. Add agent tool definition versioning that references specific schema versions to detect drift.
- **Portfolio-Level Recommendation**: Adopt database migration frameworks (Flyway for Java/PHP, CDK for DynamoDB). Create JSON Schema files per entity.
- **Estimated Effort**: Medium

### OBS-Q1: Distributed Tracing and Structured Logging — RISK in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: No distributed tracing in 4 of 5 services (books-api has X-Ray enabled). No structured logging anywhere — all use unstructured console.log/println/error_log. No correlation IDs.
- **Compensating Controls**: Enable X-Ray tracing on books-api (already partially configured) as the portfolio tracing baseline. Add request ID middleware to all services that generates and returns a UUID in response headers for agent-side correlation. Adopt AWS Lambda Powertools Logger for serverless services (aws-microservices, books-api) as a quick win for structured JSON logging. For container services, add JSON log formatting via SLF4J/Logback (unishop-monolith) or Monolog (local-monolith).
- **Portfolio-Level Recommendation**: Enable X-Ray/OpenTelemetry across all services. Adopt AWS Lambda Powertools Logger (Node.js) and SLF4J/Logback (Java) for structured JSON logging.
- **Estimated Effort**: Medium

### OBS-Q2: Alerting on Error Rates and Latency — RISK in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: No operational alerting. books-api has deployment-focused Lambda error alarms but no latency or operational alerts. All others have zero alerting.
- **Compensating Controls**: Deploy CloudWatch alarms for Lambda error rates and concurrent execution limits on serverless services (aws-microservices, books-api) as a quick first step. Monitor container health checks for Docker-based services. Implement agent-side alerting on HTTP error rates (>5% errors over 5 minutes) and response time degradation (P95 > 2 seconds) as a compensating detection layer. Use books-api's existing CodeDeploy alarm pattern as a template for other services.
- **Portfolio-Level Recommendation**: Deploy CloudWatch alarms for API error rates (>5% over 5min), P95 latency (>2s), and DLQ depth across all services.
- **Estimated Effort**: Medium

### ENG-Q1: Infrastructure Governance — RISK in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: IaC exists in all services but drift detection and peer review enforcement are missing across the portfolio.
- **Compensating Controls**: Add CODEOWNERS files to all repositories to require team review for infrastructure file changes. Enable branch protection rules on all repositories to enforce PR review before merge. Enable AWS Config with managed rules for drift detection on deployed resources. For eks-saas-gitops, run `terraform plan` manually before each apply and review output as a lightweight governance check.
- **Portfolio-Level Recommendation**: Enable AWS Config drift detection. Add CODEOWNERS files. Enforce branch protection with mandatory reviews.
- **Estimated Effort**: Low

### ENG-Q2: CI/CD with API Contract Testing — RISK in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: No API contract testing in any service. books-api has the most mature CI/CD (Source→Build→Staging→Prod). Others have minimal or no pipelines.
- **Compensating Controls**: Use books-api's existing CI/CD pipeline (Source→Build→Staging→Prod with E2E tests) as the portfolio template for other services. Implement manual API smoke tests before each deployment using curl scripts or Postman collections. Run agent integration tests after each deployment to detect breaking changes. Add OpenAPI spec validation as a pre-commit hook where specs are available.
- **Portfolio-Level Recommendation**: Implement CI/CD pipelines for all services. Add OpenAPI validation and consumer-driven contract tests.
- **Estimated Effort**: High

### ENG-Q3: Rollback Capability — RISK in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: books-api has CodeDeploy with gradual traffic shifting and automatic rollback. Others lack automated rollback — manual redeployment or Docker restart required.
- **Compensating Controls**: Tag Docker images with version numbers before each deployment for container-based services (local-monolith, unishop-monolith) to enable manual rollback to the previous image. For eks-saas-gitops, use Git revert to trigger Flux reconciliation as a de facto rollback mechanism. Adopt books-api's CodeDeploy with gradual traffic shifting pattern as the portfolio standard. Document rollback procedures per service as runbooks.
- **Portfolio-Level Recommendation**: Implement automated deployment with rollback triggers for all services. Use CodeDeploy or blue/green patterns.
- **Estimated Effort**: High

### ENG-Q4: API Test Coverage — RISK in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: Zero test coverage in 3 services (unishop-monolith, aws-microservices, local-monolith). books-api has unit + E2E tests. eks-saas-gitops has only a Helm connectivity test.
- **Compensating Controls**: Implement Postman/Newman API smoke test collections for each service's agent-facing endpoints as a quick coverage baseline. Use books-api's existing test suite (unit + E2E) as the portfolio model. Run agent integration tests from the agent orchestration layer after each deployment as a compensating validation mechanism. Focus initial test coverage on high-risk write endpoints used by the customer support agent (order creation, return processing, inventory updates).
- **Portfolio-Level Recommendation**: Target minimum API test coverage for all agent-facing endpoints. Add contract tests for all services.
- **Estimated Effort**: High

### ENG-Q5: Encryption at Rest — RISK in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: Inconsistent encryption. No customer-managed KMS keys anywhere. unishop-monolith has no encryption at all. aws-microservices has SQS unencrypted. eks-saas-gitops skips Checkov encryption checks.
- **Compensating Controls**: Enable AWS-managed encryption at rest on all RDS, DynamoDB, SQS, and S3 resources as an immediate baseline (default encryption covers most cases). For container-based services (local-monolith), enable EBS encryption on EC2/ECS hosts. Remove Checkov skip annotations in eks-saas-gitops and address the flagged encryption gaps. For local Docker deployments, enable filesystem-level encryption on the Docker host. Plan migration to customer-managed KMS keys as a follow-up for PII-containing data stores.
- **Portfolio-Level Recommendation**: Enable KMS encryption on all data stores. Create a shared customer-managed KMS key for PII-containing services.
- **Estimated Effort**: Medium

## Service Dependency Map

### Dependency Overview

| Source Service | Target Service | Type | Description |
|---------------|---------------|------|-------------|
| aws-microservices | books-api | async | Microservices ordering flow triggers book catalog updates via EventBridge events |
| books-api | aws-microservices | sync | Books API queries product microservice for catalog data via REST |
| unishop-monolith | eks-saas-gitops | shared_infra | Unishop will be deployed onto the EKS cluster managed by eks-saas-gitops |
| local-monolith | eks-saas-gitops | shared_infra | Local monolith will be containerized and deployed onto the EKS cluster |
| aws-microservices | local-monolith | sync | Microservices query monolith for legacy product data during migration |

### Service Dependency Metrics

| Service | Fan-In | Fan-Out | Role | Readiness Profile |
|---------|--------|---------|------|-------------------|
| eks-saas-gitops | 2 | 0 | Internal | 🟠 Remediation Required |
| aws-microservices | 1 | 2 | Internal | ❌ Not Agent-Integrable |
| books-api | 1 | 1 | Internal | ❌ Not Agent-Integrable |
| local-monolith | 1 | 1 | Internal | ❌ Not Agent-Integrable |
| unishop-monolith | 0 | 1 | Leaf | ❌ Not Agent-Integrable |

### High-Risk Dependency Patterns

1. **High-Risk Shared Infrastructure Service: eks-saas-gitops**
   - **Affected Services**: unishop-monolith, local-monolith (shared_infra dependency)
   - **Risk**: eks-saas-gitops is the shared EKS infrastructure service with Fan-In=2 (below the Foundation threshold of Fan-In≥3, but still a critical shared dependency) and readiness profile "Remediation Required" with 2 BLOCKERs (AUTH-Q7: no immutable audit logging, ENG-Q6: publicly exposed EKS API and internet-facing LoadBalancers). Both unishop-monolith and local-monolith will be deployed onto this EKS cluster. The ENG-Q6 BLOCKER (publicly accessible Kubernetes API server, Argo Workflows exposed without authentication, Kubecost with disabled network policies) affects all services deployed to this cluster — even if individual services resolve their own network security gaps, the underlying infrastructure remains exposed.
   - **Recommendation**: Prioritize eks-saas-gitops ENG-Q6 remediation (set `cluster_endpoint_public_access = false`, move LoadBalancers to internal, enable network policies) before deploying containerized versions of unishop-monolith and local-monolith to the cluster.

2. **Transitive Blocker Propagation: aws-microservices → local-monolith**
   - **Affected Services**: aws-microservices, local-monolith
   - **Risk**: aws-microservices (Not Agent-Integrable, 7 BLOCKERs) depends synchronously on local-monolith (Not Agent-Integrable, 7 BLOCKERs) for legacy product data queries during migration. Both services are independently blocked, but the synchronous dependency means that even if aws-microservices resolves all its own BLOCKERs, agent operations that trigger calls to local-monolith will still be affected by local-monolith's unresolved BLOCKERs (no machine identity, no audit logging, no idempotency, etc.).
   - **Recommendation**: Remediate both services in parallel. Consider implementing a data cache or read replica in aws-microservices to reduce synchronous dependency on local-monolith during migration.

3. **Circular Dependency: aws-microservices ↔ books-api**
   - **Affected Services**: aws-microservices, books-api
   - **Risk**: aws-microservices sends async events to books-api via EventBridge, while books-api makes sync REST calls back to aws-microservices. This circular dependency means both services must be simultaneously agent-ready for the full data flow to work. Since both are "Not Agent-Integrable", neither can serve as a stepping stone for incremental agent enablement of the other.
   - **Recommendation**: Break the circular dependency by implementing an independent data store or API for catalog data that both services can query without depending on each other.

4. **Shared Infrastructure Cascading: EKS Network Security Gap**
   - **Affected Services**: unishop-monolith, local-monolith, eks-saas-gitops
   - **Risk**: The AUTH-Q7 BLOCKER (no CloudTrail, no immutable audit logging) on eks-saas-gitops means that when unishop-monolith and local-monolith are deployed to the EKS cluster, agent-initiated write operations via IRSA roles will not be recorded in an immutable audit trail — even if the individual services implement their own application-level audit logging.
   - **Recommendation**: Deploy centralized CloudTrail with EKS control plane audit logging before deploying any agent-enabled services to the cluster.

## Portfolio Remediation Guidance

> Portfolio context: Evaluating the e-commerce platform portfolio for both autonomous AI agent integration and cloud-native modernization. The team is building a customer support agent that handles order inquiries, processes returns, and manages inventory restocking.

### Remediation Priority Order

Remediation of cross-cutting BLOCKERs should follow this general priority:

1. **Identity and Access** — Resolve AUTH-section BLOCKERs first. You cannot enforce any other security control without machine identity and scoped permissions.
2. **Data Integrity** — Resolve STATE and DATA-section BLOCKERs second. Protect data before enabling agent write operations.
3. **API Surface** — Resolve API-section BLOCKERs third. Ensure a stable, documented integration surface for agent tools.
4. **Remaining BLOCKERs** — Address in order of affected service count (most affected first).

### Coordinated Remediation Plan

#### Identity Foundation

**BLOCKERs addressed**: AUTH-Q1, AUTH-Q7
**Services affected**: All 5 services

- **What to do**: Deploy a centralized Amazon Cognito User Pool with Resource Servers and client_credentials grant. This single platform-level action unblocks machine identity authentication (AUTH-Q1) for all 4 application services simultaneously. In parallel, deploy an organization-level CloudTrail trail writing to S3 with object lock and enable EKS control plane audit logging on eks-saas-gitops — this addresses AUTH-Q7 across all 5 services. Implement a portfolio-wide structured JSON logging standard. For the customer support agent use case, register the agent as a Cognito app client with scopes for `orders/read`, `returns/write`, and `inventory/read` across relevant services.
- **Expected outcome**: All services have machine identity authentication. All write operations are logged in an immutable audit trail with principal attribution. The customer support agent can authenticate and its actions are fully auditable.
- **Effort**: Medium — 4–8 weeks for both AUTH-Q1 and AUTH-Q7

#### Data Protection

**BLOCKERs addressed**: DATA-Q1, DATA-Q2
**Services affected**: unishop-monolith, aws-microservices, local-monolith, books-api

- **What to do**: Define a portfolio data classification policy identifying PII categories. Apply classification tags to all data stores. Document data residency requirements and pin all stacks to specific approved AWS regions. For the customer support agent handling order inquiries and returns, classify customer PII fields (name, email, address, payment info) and define which fields the agent can access. Implement field-level redaction so the agent receives only necessary PII. Document that Amazon Bedrock in the same region is the approved LLM endpoint for PII processing.
- **Expected outcome**: All PII is classified and tagged. Data residency policy documented and enforced. The customer support agent accesses only the PII necessary for its scoped tasks. LLM calls stay within the approved jurisdiction.
- **Effort**: High — 4–6 weeks for DATA-Q1, Medium — 2–3 weeks for DATA-Q2

#### Write Safety

**BLOCKERs addressed**: API-Q4, STATE-Q1
**Services affected**: unishop-monolith, aws-microservices, local-monolith, books-api

- **What to do**: Adopt a portfolio-wide idempotency standard using `Idempotency-Key` headers. For serverless services (aws-microservices, books-api), use Lambda Powertools idempotency utility. For container/EC2 services (local-monolith, unishop-monolith), implement idempotency middleware. In parallel, implement compensation endpoints for each service's multi-step workflows. For the customer support agent processing returns and managing restocking, idempotency ensures that retry on a "process return" or "restock inventory" API call does not duplicate the operation. Compensation logic ensures that a failed multi-step return workflow can be cleanly reversed.
- **Expected outcome**: All write endpoints are idempotent. Multi-step agent workflows have defined compensation paths. The customer support agent can safely retry failed operations and recover from partial workflow failures.
- **Effort**: Medium — 3–4 weeks for API-Q4, High — 6–8 weeks for STATE-Q1

#### Network Hardening

**BLOCKERs addressed**: ENG-Q6
**Services affected**: All 5 services

- **What to do**: Deploy AWS WAF with rate limiting rules on all public-facing API Gateways. Add explicit CORS configuration to each service restricting allowed origins. For eks-saas-gitops: set `cluster_endpoint_public_access = false`, change Argo Workflows and Kubecost LoadBalancers from internet-facing to internal, enable Kubecost network policies. For application services: deploy API Gateway in front of each service with WAF, restrict security groups to API Gateway only. For the customer support agent, configure WAF rules that allow the agent's known IP ranges while rate-limiting all clients.
- **Expected outcome**: All services accessible only through controlled network paths. CORS restricted to authorized origins. EKS cluster not publicly accessible. WAF provides rate limiting and IP reputation filtering. The customer support agent operates through a well-defined, secured network path.
- **Effort**: Medium — 3–4 weeks

## Agentic Program Recommendations

> These are engagement-level recommendations based on the portfolio's agentic readiness
> profile. Discuss with your AWS Solutions Architect to determine eligibility and timing.

| Program | Relevance | Trigger Findings | Next Step |
|---------|-----------|-----------------|-----------|
| EBA-Agentic AI | NOT triggered — 0 services are Agent-Ready or Pilot-Ready | Re-evaluate after completing the Identity Foundation and Network Hardening remediation groups | Request EBA engagement via AWS Solutions Architect once services reach Pilot-Ready |

### Program Details

> No agentic programs currently triggered. As the portfolio's agentic readiness improves through remediation of cross-cutting BLOCKERs, re-assess to identify EBA-Agentic AI eligibility.

## Service-by-Service Summary

| Service | Repo Type | Agent Scope | Readiness Profile | BLOCKERs | RISKs | INFOs | N/A |
|---------|-----------|-------------|-------------------|----------|-------|-------|-----|
| unishop-monolith | application | write-enabled | ❌ Not Agent-Integrable | 7 | 32 | 10 | 0 |
| aws-microservices | application | write-enabled | ❌ Not Agent-Integrable | 7 | 32 | 10 | 0 |
| local-monolith | application | write-enabled | ❌ Not Agent-Integrable | 7 | 33 | 9 | 0 |
| books-api | application | write-enabled | ❌ Not Agent-Integrable | 6 | 32 | 11 | 0 |
| eks-saas-gitops | infrastructure-only | write-enabled | 🟠 Remediation Required | 2 | 11 | 2 | 34 |

### Individual Service Details

#### unishop-monolith

- **Readiness Profile**: ❌ Not Agent-Integrable
- **Repo Type**: application
- **Agent Scope**: write-enabled
- **Priority**: P0
- **BLOCKERs** (7):
  - AUTH-Q1: OAuth2 configured but `permitAll()` disables all authentication — no machine identity
  - API-Q4: No idempotency keys on write endpoints; `INSERT IGNORE` provides only DB-level protection
  - STATE-Q1: No compensation/rollback for multi-step basket and user creation workflows
  - AUTH-Q7: No immutable audit logging; CloudWatch Logs with only 7-day retention and unstructured output
  - DATA-Q1: PII (email, first_name, last_name) in plaintext MySQL with no classification or field-level controls
  - DATA-Q2: No data residency documentation or controls; PII could be sent to any jurisdiction
  - ENG-Q6: Wildcard CORS, security groups open to 0.0.0.0/0, no WAF
- **Key Recommendations**:
  - Enable OAuth2 validation in ResourceServerConfig.java and configure Cognito client credentials
  - Migrate hardcoded credentials from application.properties and CloudFormation to Secrets Manager
  - Add encryption at rest to RDS cluster (StorageEncrypted: true)
- **Depends On**: eks-saas-gitops (shared_infra — EKS deployment target)
- **Depended On By**: None

#### aws-microservices

- **Readiness Profile**: ❌ Not Agent-Integrable
- **Repo Type**: application
- **Agent Scope**: write-enabled
- **Priority**: P0
- **BLOCKERs** (7):
  - AUTH-Q1: All three API Gateways completely open — no authorizer, no API keys, no auth
  - API-Q4: No idempotency on POST /product and POST /basket/checkout — retries create duplicates
  - STATE-Q1: 4-step checkout flow with no compensation; EventBridge events not reversible
  - AUTH-Q7: No CloudTrail in CDK; Lambda logs full event payloads including PII without retention policies
  - DATA-Q1: Order table stores PII + cardInfo with no classification tags or field-level encryption
  - DATA-Q2: CDK stack env property commented out — no region pinning, no residency documentation
  - ENG-Q6: No CORS on any API Gateway, no VPC attachment, no WAF, APIs publicly accessible
- **Key Recommendations**:
  - Add API Gateway API keys immediately, then migrate to Cognito OAuth 2.0 client credentials
  - Upgrade Lambda runtime from deprecated NODEJS_14_X to NODEJS_20_X
  - Tokenize or remove cardInfo field from order table (potential PCI DSS violation)
- **Depends On**: books-api (async — EventBridge events), local-monolith (sync — legacy product data)
- **Depended On By**: books-api (sync — REST catalog queries)

#### local-monolith

- **Readiness Profile**: ❌ Not Agent-Integrable
- **Repo Type**: application
- **Agent Scope**: write-enabled
- **Priority**: P0
- **BLOCKERs** (7):
  - AUTH-Q1: Session-based PHP auth only — no OAuth2, no API keys, no machine identity
  - API-Q4: No idempotency keys on any write endpoint; order IDs use uniqid() with no deduplication
  - STATE-Q1: Multi-step fulfillment workflow (7 steps) with each step committing independently — no saga
  - AUTH-Q7: Application-level order_status_history is mutable MySQL — not an immutable audit log
  - DATA-Q1: Customer PII (name, email, shipping address) in plaintext MySQL without classification
  - DATA-Q2: Docker deployment with no region awareness; no residency documentation
  - ENG-Q6: No CORS headers, no security groups, port 8080 exposed directly, no WAF
- **Key Recommendations**:
  - Implement API key authentication as alternative auth path alongside session-based auth
  - Remove hardcoded credential fallback `getenv('DB_PASS') ?: 'ecommerce_pass'` from index.php
  - Deploy API Gateway with WAF in front of the application
- **Depends On**: eks-saas-gitops (shared_infra — EKS deployment target)
- **Depended On By**: aws-microservices (sync — legacy product data queries)

#### books-api

- **Readiness Profile**: ❌ Not Agent-Integrable
- **Repo Type**: application
- **Agent Scope**: write-enabled
- **Priority**: P1
- **BLOCKERs** (6):
  - AUTH-Q1: Cognito User Pool with human-only implicit grant — no client credentials for machine identity
  - API-Q4: POST /books uses PutItem with no ConditionExpression — silent overwrites on retries
  - STATE-Q1: No delete endpoint, no saga pattern, no compensation for multi-step agent workflows
  - AUTH-Q7: API Gateway logging and X-Ray enabled but no CloudTrail, no immutable storage, no principal logging
  - DATA-Q2: No formal data residency documentation (book catalog data is non-PII but write-enabled scope requires documented assessment)
  - ENG-Q6: No CORS on SAM API Gateway, no WAF, no network policy documentation
- **Key Recommendations**:
  - Add Cognito App Client with client_credentials grant and custom scopes (books/read, books/write)
  - Add ConditionExpression to PutItem to prevent silent overwrites
  - Add CORS configuration to BooksApi SAM resource — fastest blocker to resolve
- **Depends On**: aws-microservices (sync — REST catalog queries)
- **Depended On By**: aws-microservices (async — EventBridge events)

#### eks-saas-gitops

- **Readiness Profile**: 🟠 Remediation Required
- **Repo Type**: infrastructure-only
- **Agent Scope**: write-enabled
- **Priority**: P1
- **BLOCKERs** (2):
  - AUTH-Q7: No CloudTrail, no CloudWatch Log Groups, no S3 object lock in any Terraform file
  - ENG-Q6: EKS API publicly accessible, Argo Workflows and Kubecost exposed via internet-facing LoadBalancers without authentication, Kubecost network policies disabled
- **Key Recommendations**:
  - Add aws_cloudtrail resource with log file validation and S3 bucket with object lock
  - Set cluster_endpoint_public_access = false and move LoadBalancers to internal
  - Replace AdministratorAccess on argo-workflows and tf-controller IRSA roles with scoped policies
- **Depends On**: None
- **Depended On By**: unishop-monolith (shared_infra), local-monolith (shared_infra)

## Assessment Inventory

| # | Service | Report File | Assessment Date | Repo Type | Agent Scope |
|---|---------|-------------|-----------------|-----------|-------------|
| 1 | unishop-monolith | ./services/unishop-monolith-to-microservices/MonoToMicroLegacy/MonoToMicroLegacy-ara-report.md | 2026-04-15 | application | write-enabled |
| 2 | aws-microservices | ./services/aws-microservices/aws-microservices-ara-report.md | 2026-04-15 | application | write-enabled |
| 3 | local-monolith | ./monolith/monolith-ara-report.md | 2026-04-15 | application | write-enabled |
| 4 | books-api | ./services/books-api/books-api-ara-report.md | 2026-04-15 | application | write-enabled |
| 5 | eks-saas-gitops | ./services/eks-saas-gitops/eks-saas-gitops-ara-report.md | 2025-07-15 | infrastructure-only | write-enabled |

---

*End of Portfolio Agentic Readiness Assessment Report*
