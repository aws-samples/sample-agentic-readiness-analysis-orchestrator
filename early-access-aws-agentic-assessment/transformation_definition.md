
## Name
Agentic Readiness Assessment

## Objective
Evaluate a code repository's infrastructure, application architecture, data foundations, security posture, and operational maturity against agentic readiness criteria, then produce a structured Markdown gap analysis report with scored findings, prioritized recommendations, and a phased modernization roadmap.

## Summary
This transformation performs a comprehensive agentic readiness assessment on a codebase. It scans all files in the repository to discover infrastructure-as-code, application source code, CI/CD definitions, API specifications, dependency manifests, configuration files, and container definitions. It then evaluates what it finds against specific criteria across five categories:
- Infrastructure & Platform
- Application Architecture
- Data Foundations
- Identity, Security & Governance
- Operations & Observability

Each criterion is scored on a 1–4 scale. The output is a detailed Markdown report saved as `agentic-readiness-report.md` containing an executive summary, category scores, top 5 critical gaps, a three-phase modernization roadmap, recommended learning materials, detailed per-criterion findings with file references, and an evidence index.

## Entry Criteria
- The repository contains source code files (e.g., .java, .js, .ts, .py, .go, .cs)
- The repository is accessible and readable at the specified path
- Write permissions exist to create the output directory and report file

## Implementation Steps

### Step 1: Discovery — Static Scan

Scan the target repository to understand what exists:

- Get the full directory tree
- Identify all file types present
- Locate source code files (.py, .java, .js, .ts, .go, .cs, etc.)
- Locate IaC files (.tf, .yaml, .yml, template.yaml, CloudFormation templates, CDK stacks, Helm charts, Kustomize, ACK, KRO)
- Locate API spec files (openapi.yaml, swagger.json, any OpenAPI/Swagger files)
- Locate CI/CD definitions (.github/workflows/*.yml, buildspec.yml, Jenkinsfile, .gitlab-ci.yml, Dockerfile, docker-compose.yml)
- Locate dependency manifests (package.json, requirements.txt, pom.xml, *.gradle, go.mod, *.csproj)
- Locate configuration files (*.yaml, *.json, *.env, *.properties, *.toml)

Read all discovered files that are relevant to the assessment. Prioritize IaC, CI/CD, dependencies, API specs, application source code, config files, and Dockerfiles.

Ignore installed dependencies and built binaries, for example "node_modules" directory for Nodejs applications and "target" directory for Java applications.

### Step 2: Evaluate Infrastructure & Platform (10 criteria)

For each of the following criteria, examine the relevant files, determine a finding, assign a score from 1-4, identify the gap, and formulate a recommendation. Always cite specific file names and resource names.

**INF-Q1 — Compute**: Is the application using managed container orchestration (EKS, ECS) or serverless (Lambda) vs raw EC2?
- Look for: Terraform `aws_ecs_*`, `aws_eks_*`, `aws_lambda_*` vs `aws_instance` resources; CloudFormation resource types; Dockerfile presence; Kubernetes manifests.
- Agent-ready (score 4): 80% or more of compute is ECS/EKS/Lambda/Fargate. EC2 only for edge cases.

**INF-Q2 — Databases**: Are databases fully managed (RDS/Aurora/DynamoDB/DocumentDB) vs self-managed?
- Look for: Terraform `aws_rds_*`, `aws_dynamodb_*`, `aws_docdb_*` vs any compute resource (`aws_instance`, ECS task definitions, Kubernetes manifests, docker-compose) running database software (MySQL, PostgreSQL, MongoDB, Oracle, SQL Server, etc.); on-prem database references in connection strings or config files; database engine installation scripts in user-data, Dockerfiles, or Helm charts.
- WHY: Agent workflows require high availability and automatic failover. Self-managed databases — regardless of where they run (EC2, containers, on-premises, or other environments) — introduce maintenance windows, manual patching, and operational overhead that can cause agent failures. Identifying self-managed databases is a primary modernization target: migrating to managed services (RDS, Aurora, DynamoDB) via AWS DMS/SCT accelerates agentic readiness by eliminating ops burden and enabling the automatic backups, failover, and scaling that agent conversation history and state recovery depend on.
- Agent-ready (score 4): All databases are managed services with automated failover. No self-managed database software detected in any compute environment.

**INF-Q3 — Workflow Orchestration**: Is there a dedicated orchestration service (Step Functions, Temporal, Camunda) vs custom state machines?
- Look for: `aws_sfn_*` in Terraform; Temporal SDK imports; workflow YAML definitions; state machine patterns in code.
- Agent-ready (score 4): Dedicated workflow orchestration service in use.

**INF-Q4 — Async Messaging**: Is there managed messaging (SQS, SNS, EventBridge, MSK) vs self-managed Kafka/RabbitMQ?
- Look for: `aws_sqs_*`, `aws_sns_*`, `aws_mdb_*` in IaC; SDK imports for messaging; event-driven patterns in code.
- Agent-ready (score 4): Managed queue/bus service(s) present.

**INF-Q5 — Infrastructure as Code**: What percentage of infrastructure is defined in IaC vs created manually?
- Look for: Presence and coverage of .tf files, CDK stacks, CloudFormation templates, Helm charts. Check whether IaC covers compute, networking, databases, and messaging.
- Agent-ready (score 4): 90% or more of infrastructure defined in IaC.

**INF-Q6 — CI/CD**: Are there automated pipelines vs manual deployments?
- Look for: .github/workflows/, buildspec.yml, Jenkinsfile, CodePipeline definitions in IaC; pipeline stages with automated test, build, and deploy steps.
- Agent-ready (score 4): Full CI/CD automation with test, build, and deploy stages.

**INF-Q7 — API Entry Point**: Is there an API Gateway, ALB, or CloudFront vs direct service exposure?
- Look for: `aws_api_gateway_*`, `aws_apigatewayv2_*`, `aws_lb_*` in IaC; throttling and auth config on gateway.
- Agent-ready (score 4): API Gateway with throttling, auth, and request validation.

**INF-Q8 — Real-time Streaming**: Is there managed streaming (Kinesis, MSK) vs self-managed Kafka?
- Look for: `aws_kinesis_*`, `aws_msk_*`; Kafka/Kinesis SDK imports; stream consumer patterns.
- Agent-ready (score 4): Managed streaming service present for event-driven data.

**INF-Q9 — Network Security**: Are there VPC, private subnets, security groups, NACLs?
- Look for: `aws_vpc`, `aws_subnet`, `aws_security_group`; subnet tiers (public vs private); security group rules; check for overly permissive rules (0.0.0.0/0).
- Agent-ready (score 4): Services in private subnets, least-privilege security groups, network segmentation present.

**INF-Q10 — Auto-scaling**: Are ASGs, ECS Service auto-scaling, or Lambda concurrency limits configured?
- Look for: `aws_autoscaling_*`, `aws_appautoscaling_*`; scaling policies; min/max capacity settings.
- Agent-ready (score 4): All compute tiers have auto-scaling configured with appropriate min/max.

### Step 3: Evaluate Application Architecture (13 criteria)

**APP-Q1 — Programming Languages**: What languages are used and how mature is their agent ecosystem?
- Look for: File extensions; package.json (Node/TS), requirements.txt (Python), pom.xml/build.gradle (Java), go.mod (Go), *.csproj (.NET).
- Agent-ready (score 4): Python or TypeScript as primary languages (best agent framework ecosystem).

**APP-Q2 — API Documentation**: Are OpenAPI/Swagger specs present?
- Look for: openapi.yaml, swagger.json, api-docs, annotations like @OpenAPIDefinition or @ApiOperation in Java; FastAPI auto-generation; tsoa; Smithy models.
- Agent-ready (score 4): All APIs have current, maintained OpenAPI specs.

**APP-Q3 — Async vs Sync Communication**: What is the ratio of async to sync inter-service calls?
- Look for: HTTP client calls (axios, requests, RestTemplate, fetch) vs message publishing patterns; event-driven handlers; queue consumers.
- Agent-ready (score 4): More than 50% async, or async available for all long-running operations.

**APP-Q4 — Monolith vs Microservices**: Is it a single deployable unit or multiple services?
- Look for: Single deployable vs multiple service directories/repos; Helm charts for multiple services; Docker Compose with multiple services; IaC for multiple ECS tasks or Lambda functions.
- For monoliths, also assess: Package/module structure; dependency graphs (circular dependencies indicate tight coupling); clear module interfaces; shared mutable state patterns; database coupling (shared tables, foreign keys across domains).
- WHY: Agentic systems benefit from clear service boundaries for tool isolation, failure containment, and independent scaling. A tightly-coupled monolith blocks incremental modernization and makes it difficult to assign agent tools to specific domains. Understanding modularity helps determine decomposition strategy: modular monoliths can be containerized as-is and decomposed opportunistically, while tightly-coupled monoliths require refactoring before extraction. This assessment directly impacts Level of Effort (LoE) estimates and roadmap sequencing.
- Agent-ready (score 4): Microservices or modular monolith with clear service boundaries.
- Scoring guidance:
  - Score 4: Multiple independently deployable services OR modular monolith with well-defined module boundaries, no circular dependencies, clear interfaces
  - Score 3: Modular monolith with some coupling OR early-stage microservices with shared databases
  - Score 2: Monolith with identifiable modules but significant coupling (shared state, database coupling, circular dependencies)
  - Score 1: Tightly-coupled monolith with no clear module boundaries, pervasive shared state

**APP-Q5 — API Response Format**: Is the response format JSON, XML, binary, or other?
- Look for: Response serialization in code; content-type headers; protobuf/Thrift definitions; XML marshaling.
- Agent-ready (score 4): Structured JSON responses across all APIs.

**APP-Q6 — Workflow Logic**: Is there dedicated orchestration vs hardcoded business logic?
- Look for: Step Functions definitions; workflow engine usage vs large if/else state machines in code; workflow, process, or saga patterns.
- Agent-ready (score 4): Workflow orchestration service or framework in use.

**APP-Q7 — Idempotency**: Are idempotency keys and safe retry patterns implemented?
- Look for: Idempotency-Key headers; idempotency token parameters in API schemas; database upsert patterns; deduplication IDs in SQS calls.
- Agent-ready (score 4): Critical write APIs support idempotency keys.

**APP-Q8 — Rate Limiting & Throttling**: Is rate limiting applied at the API layer?
- Look for: API Gateway throttling config (burst/rate limits); WAF rules; rate limiting middleware (express-rate-limit, django-ratelimit, etc.); aws_api_gateway_usage_plan.
- Agent-ready (score 4): Rate limiting enforced at gateway and/or application layer.

**APP-Q9 — Resilience Patterns**: Are circuit breakers, retries, and timeouts implemented?
- Look for: Resilience4j, Hystrix, Polly, retry decorators; exponential backoff; timeout configurations; @Retry or @CircuitBreaker annotations; AWS SDK retry config.
- Agent-ready (score 4): All external dependency calls have retry + timeout + circuit breaker.

**APP-Q10 — Long-running Processes**: Are operations over 30 seconds handled asynchronously?
- Look for: Background job frameworks (Celery, Bull, SQS workers); async/polling patterns; job status APIs; Lambda async invocations; Step Functions for long processes.
- Agent-ready (score 4): All operations over 30 seconds implemented as async jobs with status polling or callbacks.

**APP-Q11 — API Versioning**: Is there URL path, header, or query parameter versioning?
- Look for: /v1/, /v2/ URL patterns; Accept-Version headers; versioning annotations; changelog files.
- Agent-ready (score 4): Consistent versioning strategy with backward compatibility guarantees.

**APP-Q12 — Service Discovery & Mesh**: Is there a service registry, API catalog, or service mesh?
- Look for: AWS Service Discovery, App Mesh, Istio, Consul; API Gateway as catalog; environment variables with hard-coded endpoints vs service discovery.
- Agent-ready (score 4): Service discovery mechanism present; no hard-coded service endpoints.

**APP-Q13 — AI/Agent Frameworks**: Is there existing use of agent SDKs or AI frameworks?
- Look for: boto3 with Bedrock; langchain, langgraph, crewai, strands-agents, openai, anthropic in requirements/package.json; Spring AI; MCP SDK imports.
- Agent-ready (score 4): AI/agent framework(s) already in use or clear integration points identified.

### Step 4: Evaluate Data Foundations (11 criteria)

**DATA-Q1 — Vector Database Presence**: Is a vector database present?
- Look for: OpenSearch with k-NN plugin; aws_opensearch_domain; Aurora pgvector extension; S3 Vectors; Bedrock Knowledge Bases; Pinecone/Weaviate/Chroma imports.
- Agent-ready (score 4): Managed vector store configured and integrated.

**DATA-Q2 — Vector DB Management**: Is the vector DB managed or self-hosted?
- Look for: Managed OpenSearch Service vs EC2-hosted OpenSearch; managed Pinecone vs Docker Compose Chroma; Bedrock Knowledge Bases.
- Agent-ready (score 4): Fully managed vector DB service.

**DATA-Q3 — RAG Implementation**: Is there document chunking, embeddings, and semantic search?
- Look for: Embedding model calls (Bedrock Titan, OpenAI ada); chunking/splitting code; similarity_search or knn_search patterns; Bedrock Knowledge Base integration.
- Agent-ready (score 4): Full RAG pipeline implemented and integrated.

**DATA-Q4 — Data Source Sprawl**: How many distinct data sources must be queried?
- Look for: Count distinct database/API connections in code; data access objects; repository classes; API client instantiations.
- Agent-ready (score 4): 3 or fewer data sources, or unified data access layer abstracting them.

**DATA-Q5 — Data Access Pattern**: Are data sources accessed via APIs vs direct DB connections from agent code?
- Look for: Database driver imports directly in API handlers vs data access layer; repository pattern vs direct query execution.
- Agent-ready (score 4): All data accessible via well-defined APIs; no direct DB connections from business logic layer.

**DATA-Q6 — Unstructured Data**: Is there S3 storage with parsing (Textract, Tika)?
- Look for: aws_s3_bucket; Textract calls; document parsing libraries; PDF/image processing.
- Agent-ready (score 4): Unstructured data stored in S3 with parsing pipeline available.

**DATA-Q7 — Schema Documentation**: Are data schemas versioned and documented?
- Look for: JSON Schema files; Avro/Protobuf schemas; database migration files (Flyway, Liquibase, Alembic); schema registry; OpenAPI schema definitions.
- Agent-ready (score 4): Schemas documented, versioned, and accessible.

**DATA-Q8 — Data Access Layer**: Is there a unified data access layer vs scattered connections?
- Look for: Centralized repository/DAO layer vs database imports spread across many modules; data access pattern consistency.
- Agent-ready (score 4): Unified data access layer; single point of data contract.

**DATA-Q9 — Embedding Freshness**: Are there incremental index updates vs one-time generation?
- Look for: Event-driven embedding refresh triggers; scheduled re-indexing pipelines; Bedrock Knowledge Base sync configuration; CDC (Change Data Capture) patterns.
- Agent-ready (score 4): Automated, event-driven or scheduled embedding refresh in place.

**DATA-Q10 — Database Engine Version & EOL**: Does IaC or deployment configuration specify the database engine version, and have any engines approaching or past end-of-life (EOL) been identified?
- Look for: Engine version parameters in `aws_rds_instance`, `aws_docdb_cluster`, `aws_elasticache_*`; engine version strings in docker-compose or Helm values; absence of explicit version pinning (implicit latest).
- WHY: Agentic systems require stable, supported data backends. EOL database engines introduce security vulnerabilities and lack modern API features needed for reliable tool-use. The assessment agent can cross-reference detected engine versions against public EOL schedules to flag migration urgency. Unversioned or implicitly-latest configurations are also a risk signal.
- Agent-ready (score 4): All database engine versions explicitly pinned in IaC; no engines at or past EOL.

**DATA-Q11 — Stored Procedures & Schema Complexity**: Does the application rely on stored procedures, triggers, or proprietary SQL constructs (e.g., T-SQL, PL/SQL)?
- Look for: `.sql` files containing `CREATE PROCEDURE`, `CREATE TRIGGER`, `CREATE FUNCTION`; ORM bypass patterns (raw SQL execution); references to proprietary SQL dialects in migration files or schema definitions.
- WHY: Stored procedures and proprietary SQL tightly couple business logic to the database engine, creating migration blockers. Identifying these early allows the roadmap to prioritize schema refactoring and logic extraction as a prerequisite to managed database migration. High stored procedure usage is a strong signal that database modernization will require significant effort beyond a lift-and-shift.
- Agent-ready (score 4): No stored procedures or proprietary SQL constructs detected; all business logic in application layer.

### Step 5: Evaluate Identity, Security & Governance (10 criteria)

**SEC-Q1 — Secret Management**: Are secrets in Secrets Manager/Vault vs hardcoded or in env vars?
- Look for: aws_secretsmanager_* in IaC; boto3.client('secretsmanager'); Vault client; hardcoded secrets patterns (password=, secret=, api_key= in code); .env files committed.
- Agent-ready (score 4): All secrets in Secrets Manager or equivalent; no hardcoded credentials.

**SEC-Q2 — IAM Least Privilege**: Are IAM policies using specific actions per resource vs wildcards?
- Look for: IAM policies in Terraform/CloudFormation; Action: "*" or Resource: "*" wildcards; role per service vs shared roles; condition keys.
- Agent-ready (score 4): Per-service IAM roles; no wildcard actions/resources.

**SEC-Q3 — Identity Propagation**: Is JWT/OAuth token exchange used across services?
- Look for: JWT parsing middleware; OAuth2 client credentials flow; token exchange patterns; Cognito/Okta integration; user context passed through service calls.
- Agent-ready (score 4): User identity propagated end-to-end via tokens; token exchange mechanism present.

**SEC-Q4 — Audit Logging**: Is CloudTrail enabled with immutable logs?
- Look for: aws_cloudtrail in IaC; CloudTrail log file validation enabled; S3 bucket with object lock for logs; CloudWatch log retention policies.
- Agent-ready (score 4): CloudTrail enabled with log file validation and immutable storage.

**SEC-Q5 — API Rate Limits**: Are rate limits enforced at the API level?
- Look for: API Gateway throttle settings; WAF rate rules; application-level rate limiting.
- Agent-ready (score 4): Rate limits enforced at gateway level with per-client quotas.

**SEC-Q6 — PII Redaction**: Is PII redacted from logs and error messages?
- Look for: Log scrubbing middleware; PII masking libraries; CloudWatch log filters; Macie enabled; regex patterns for PII in logging utilities.
- Agent-ready (score 4): Automated PII detection and redaction in logging pipeline.

**SEC-Q7 — Human Approval Workflows**: Are high-risk actions gated by human approval?
- Look for: Step Functions with human approval tasks (waitForTaskToken); approval Lambda patterns; approval API endpoints; manual approval stages in CI/CD for production.
- Agent-ready (score 4): Human-in-the-loop approval workflow for high-risk actions (deletions, refunds, bulk data modification).

**SEC-Q8 — Encryption at Rest**: Is KMS used for sensitive data?
- Look for: kms_key_id on S3/RDS/DynamoDB/EBS; aws_kms_key resources; customer-managed keys vs AWS-managed; encryption config on data stores.
- Agent-ready (score 4): Customer-managed KMS keys for all sensitive data stores.

**SEC-Q9 — API Authentication**: Is there per-request auth with OAuth2/JWT?
- Look for: Auth middleware; API Gateway authorizers; Cognito user pools; OAuth2 flows; Bearer token validation; API keys; @Authenticated annotations.
- Agent-ready (score 4): Every API endpoint authenticated; OAuth2/JWT standard in use.

**SEC-Q10 — Centralized Identity**: Is there a centralized identity provider (Cognito, Okta, Ping)?
- Look for: aws_cognito_*; OIDC/SAML configuration; identity provider federation; SSO configuration.
- Agent-ready (score 4): Single centralized identity provider; SSO enabled.

### Step 6: Evaluate Operations & Observability (12 criteria)

**OPS-Q1 — Distributed Tracing**: Is X-Ray, OpenTelemetry, or a partner solution in use with trace ID propagation?
- Look for: aws_xray_*; opentelemetry imports; trace context propagation in HTTP headers (traceparent, X-Amzn-Trace-Id); instrumentation wrappers; Datadog/Jaeger/Zipkin SDK; OpenTelemetry SDK in dependency manifests (requirements.txt, package.json, pom.xml); auto-instrumentation configs; presence of `gen_ai.*` semantic conventions for LLM spans; service mesh configs (Istio, App Mesh) or APM service map configurations that generate real-time dependency graphs.
- WHY: Agentic workflows span multiple components — LLMs, tools, databases, APIs, and sub-agents. Without end-to-end distributed tracing with propagated trace IDs, you cannot reconstruct what the agent did when it fails. Siloed observability — where metrics, logs, and traces are collected but not correlated across services — is insufficient for agentic workloads. You need to see the complete execution path: which tools were called, in what order, with what parameters and context, and where it broke down.
- Agent-ready (score 4): End-to-end distributed tracing with propagated trace IDs across all service boundaries; unified telemetry with no siloed observability by team or service.

**OPS-Q2 — Structured Logging**: Are logs in JSON format with correlation IDs?
- Look for: JSON log formatters (structlog, winston JSON, logback JSON); correlation ID middleware; traceId/correlationId fields in log output; CloudWatch Log Insights queries.
- Agent-ready (score 4): All services emit structured JSON logs with correlation IDs.

**OPS-Q3 — Automated Evals**: Is there an agent evaluation framework?
- Look for: Eval datasets; scoring scripts; LLM-as-judge patterns; pytest with LLM assertions; RAGAS; golden dataset files; A/B test infrastructure for prompts.
- Agent-ready (score 4): Automated eval pipeline with golden datasets and scoring.

**OPS-Q4 — SLOs**: Are SLOs defined for critical user journeys?
- Look for: SLO definitions in code or config; CloudWatch alarms on p99/p95 latency; error budget tracking; SLO dashboards; aws_cloudwatch_metric_alarm targeting latency/availability.
- Agent-ready (score 4): SLOs defined and monitored for all critical user-facing journeys.

**OPS-Q5 — Rollback Capability**: Is there automated rollback for code, config, and prompts?
- Look for: Blue/green or canary deployment config; CodeDeploy rollback triggers; Helm rollback; feature flags; prompt versioning; RollbackConfiguration in CloudFormation.
- Agent-ready (score 4): Automated rollback for code AND configuration (including prompts).

**OPS-Q6 — LLM Cost Tracking**: Is token usage tracked per request with attribution?
- Look for: LLM response token counting; cost attribution tags; per-user/feature metrics; CloudWatch custom metrics for token usage; usage object logging from LLM responses; tiered retention policies for observability data (logs, traces, LLM prompt/response pairs) to manage the significantly higher telemetry volume generated by agentic workloads.
- Agent-ready (score 4): Token usage tracked per request with user/feature/workflow attribution; observability data retention policies in place.

**OPS-Q7 — Business Metrics**: Are custom metrics published for business outcomes?
- Look for: cloudwatch.put_metric_data for business events; custom dashboards tracking resolution rates, conversion, satisfaction; business KPI alarms; not just infrastructure metrics.
- Agent-ready (score 4): Business outcome metrics published alongside infrastructure metrics.

**OPS-Q8 — Anomaly Detection**: Is there alerting on error rates and latency?
- Look for: CloudWatch anomaly detection; error rate alarms; latency p99 alarms; PagerDuty/OpsGenie integration; composite alarms.
- WHY: Agents can silently degrade — start hallucinating more, slow down responses, or drop below success thresholds. Static threshold-based alerting is poorly suited for agentic systems, which exhibit non-deterministic behavior. An agent suddenly calling 15 tools instead of 3 may indicate a reasoning loop — a fixed threshold won't catch this. Anomaly detection must understand behavioral baselines, not just infrastructure thresholds. Additionally, agentic systems can cause harm at machine speed: a misconfigured agent can execute hundreds of incorrect actions before a human notices, making slow mean-time-to-detect (MTTD) catastrophic when blast radius compounds with every autonomous step.
- Agent-ready (score 4): Anomaly detection enabled on error rates and latency for all critical paths; behavioral baseline monitoring in place.

**OPS-Q9 — Deployment Strategy**: Is the deployment blue/green, canary, or straight to production?
- Look for: CodeDeploy deployment config; Helm canary; Argo Rollouts; Lambda traffic shifting; ALB weighted target groups; feature flags for gradual rollout.
- Agent-ready (score 4): Canary or blue/green deployments; no direct-to-production releases.

**OPS-Q10 — Integration Testing**: Are there integration tests for critical workflows?
- Look for: Integration test directories; test containers; pytest-integration; API test suites (Postman/Newman); contract tests; end-to-end test pipelines in CI.
- Agent-ready (score 4): Integration test suites covering all critical workflows, run in CI pipeline.

**OPS-Q11 — Incident Response Automation**: Are incident response workflows automated, and do runbooks exist in machine-readable or structured form?
- Look for: Runbook files in the repository (markdown, YAML, or JSON runbooks); Systems Manager Automation documents (SSM documents); Lambda-based remediation functions; Step Functions for incident workflows; links to runbooks in alert configurations; evidence of self-healing patterns (auto-restart, auto-scaling on failure events).
- WHY: Agentic systems are themselves a form of operational automation — they take actions on behalf of users. If incident response is still largely manual, there is a fundamental mismatch: autonomous systems are being introduced while the ability to respond to their failures remains human-paced. Additionally, machine-readable runbooks are the raw material that agentic systems need to act autonomously in incident response use cases. Organizations with high automation ratios have already codified their operational knowledge into executable form, making it far easier to hand those workflows to an agent.
- Agent-ready (score 4): Self-healing automation resolves a defined class of incidents without human intervention; runbooks are versioned, machine-readable, and linked to alerts.

**OPS-Q12 — Observability Governance & Ownership**: Is there a defined ownership model for observability, with SLOs established and a shared responsibility model across platform and product teams?
- Look for: SLO definition files or dashboards with named owners; platform team tooling (centralized observability stack configs); evidence of developer-owned service-level instrumentation (per-service dashboards, per-service alarms); CODEOWNERS or team ownership files referencing observability assets.
- WHY: Agentic transformation requires organizational alignment around who owns agent quality, reliability, and safety in production. Without clear observability ownership, agentic systems will be deployed without adequate monitoring and accountability for failures will be unclear. Organizations with a shared responsibility model and SLO-driven culture can extend those practices to agentic workloads — defining agent-level SLOs (task success rate, hallucination rate, tool error rate) and assigning ownership across platform and product teams.
- Agent-ready (score 4): Observability-as-a-product mindset with dedicated platform engineering, SLO-driven culture, and clear ownership of service-level and agent-level SLOs.

### Step 7: Generate the Agentic Readiness Report

**Output Location:**
- Create a directory named `agentic-readiness-assessment` in the repository root if it doesn't already exist
- Create the report file with the naming pattern: `{project-name}-agentic-readiness-report.md`
  - `{project-name}` should be derived from the repository name or a user-provided project identifier
  - Example: For a project named "payment-service", create `payment-service-agentic-readiness-report.md`
- Full path example: `agentic-readiness-assessment/payment-service-agentic-readiness-report.md`

**Report Structure:**

Create the report file with exactly this structure:

```markdown
# Agentic Readiness Assessment Report
**Target**: <repository path>
**Date**: <date>
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment

---

## Table of Contents

1. Executive Summary
2. Top Priorities (Critical Gaps)
3. Readiness Roadmap
   - Phase 1 — Quick Wins (Days 1–30)
   - Phase 2 — Foundation (Months 1–3)
   - Phase 3 — Agent Enablement (Months 3–6)
4. Recommended Self-Paced Learning Materials
5. Detailed Findings
   - Infrastructure & Platform
   - Application Architecture
   - Data Foundations
   - Identity, Security & Governance
   - Operations & Observability
6. Appendix: Evidence Index

---

## Executive Summary

<3-5 sentence summary of overall readiness. Be direct. Note the strongest areas and most critical gaps. Emphasize this is an agentic readiness assessment, not a generic one.>

### Overall Score: X.X / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | X.X / 4.0 | <status emoji> |
| Application Architecture | X.X / 4.0 | <status emoji> |
| Data Foundations | X.X / 4.0 | <status emoji> |
| Identity, Security & Governance | X.X / 4.0 | <status emoji> |
| Operations & Observability | X.X / 4.0 | <status emoji> |

Status emojis: use ✅ for scores >= 3.5, 🟡 for scores >= 2.5, 🟠 for scores >= 1.5, ❌ for scores < 1.5.

---

## Top Priorities (Critical Gaps)

<List the 5 most impactful gaps that block agentic readiness. For each: what it is, why it matters for agentic workloads, and the first concrete step to address it.>

---

## Readiness Roadmap

<Account for cross-dependencies between phases. For example, containerizing an application is a prerequisite for moving it to EKS/ECS. When dependencies exist, state them explicitly.>

### Microservices Decomposition Strategy

<If APP-Q4 score indicates monolith (score < 4), include this section with approach recommendations based on modularity assessment. Present options, not prescriptions. Include Level of Effort (LoE) estimates.>

**Recommended Approach: Parallel Track (Option B)**
- **LoE**: Medium | **Risk**: Low-Medium | **Time to Value**: Fast
- **Strategy**: Modernize infrastructure while incrementally extracting services
- **Pattern**: [Strangler Fig](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) + [API Gateway Routing](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/api-routing.html)
- **Starting Point**: Extract one high-value, loosely-coupled service as proof of concept (look for services with: clear domain boundaries, minimal shared state, async communication patterns, independent data)
- **When to Use**: Most scenarios, especially when business value delivery cannot wait for complete decomposition

**Alternative: Conditional/Adaptive (Option C)**
- **LoE**: Varies by module | **Risk**: Low | **Time to Value**: Fastest
- **Strategy**: Assess each module independently, containerize modular components as-is, refactor tightly-coupled ones
- **Pattern**: [Hexagonal Architecture](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/hexagonal-architecture.html) + [Anti-corruption Layer](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/anti-corruption-layer.html)
- **Starting Point**: Containerize most modular components first (APP-Q4 score 3), defer tightly-coupled modules (APP-Q4 score 1-2)
- **When to Use**: Modular monolith with mixed coupling levels; want fastest path to containers

**Not Recommended: Big-Bang Decomposition (Option A)**
- **LoE**: Very High | **Risk**: High | **Time to Value**: Slow
- **Strategy**: Decompose entire monolith before any modernization
- **Only Consider If**: Complete rewrite is already planned, funded, and business-approved; existing system is being sunset

<Based on specific findings, recommend relevant patterns from the Cloud Design Patterns guide:>

**Pattern Recommendations Based on Your Architecture:**

<If APP-Q3 async score >= 3 AND INF-Q4 messaging present:>
- **Event-Driven Decomposition**: Use [Event Sourcing](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html) + [Saga Choreography](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-choreography.html) for services with async communication
- **Why**: Your existing async infrastructure (SQS/SNS/EventBridge) supports event-driven patterns with minimal additional investment

<If APP-Q4 monolith AND APP-Q7 no idempotency:>
- **Data Consistency**: Implement [Anti-corruption Layer](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/anti-corruption-layer.html) + [Transactional Outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html) before extraction
- **Why**: Without idempotency, service extraction risks data inconsistency; these patterns provide safety during transition

<If DATA-Q4 multiple data sources AND APP-Q3 mostly sync:>
- **Distributed Transactions**: Use [Saga Orchestration](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-orchestration.html) for cross-service transactions
- **Why**: Multiple data sources with sync communication require coordinated transaction handling across service boundaries

<If APP-Q4 monolith AND APP-Q12 no service discovery:>
- **Incremental Extraction**: Start with [Strangler Fig](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) + [API Gateway Routing Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/api-routing.html) (hostname, path, or header-based)
- **Why**: API Gateway provides routing, throttling, and auth without requiring service mesh infrastructure upfront

<If APP-Q9 resilience patterns missing:>
- **Resilience First**: Implement [Circuit Breaker](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/circuit-breaker.html) + [Retry with Backoff](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/retry-backoff.html) before decomposition
- **Why**: Microservices amplify failure modes; resilience patterns must be in place before increasing system distribution

### Phase 1 — Quick Wins (Days 1–30)
<3-5 items that are low-effort but high-impact. Things that can be done in a sprint.>

<If APP-Q4 indicates monolith, include decomposition preparation:>
- Conduct EventStorming or domain modeling workshop to identify bounded contexts and service candidates
- Map current module dependencies and data coupling (use dependency analysis tools)
- Identify first candidate service for extraction: look for high business value, low coupling, clear domain boundary
- Document current API contracts and data flows to establish baseline before changes

### Phase 2 — Foundation (Months 1–3)
<Structural improvements that require more planning but are essential before building agents.>

<If decomposition is recommended (Option B or C), include:>
- **If Option B (Parallel Track)**: Extract first service using Strangler Fig pattern; implement API Gateway routing; establish service-to-service authentication; containerize extracted service
- **If Option C (Conditional)**: Containerize modular components as separate deployments; implement service discovery; add anti-corruption layers at module boundaries; defer tightly-coupled modules for Phase 3 refactoring

### Phase 3 — Agent Enablement (Months 3–6)
<Capabilities that unlock the actual agent implementation once foundations are solid.>

<If decomposition is in progress:>
- Continue service extraction based on business priorities and agent use case requirements
- Implement domain-specific agent tools per service boundary
- Establish service-level SLOs and observability for agent-driven workflows

---

## Recommended Self-Paced Learning Materials

<Include relevant links only from the following categories with a short explanation of why each is helpful>

**Module 2: Move to Cloud Native (Containers and Serverless):**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for microservices decomposition: Strangler Fig, Anti-corruption Layer, Saga patterns, Event Sourcing, Circuit Breaker, API routing, Hexagonal Architecture, and more
- AWS Modernization Pathways: Move to Cloud Native Serverless — https://skillbuilder.aws/learning-plan/CMK2J48MVN/aws-modernization-pathways-move-to-cloud-native-serverless-includes-labs/EFUPP53B4Q
- Lambda Foundations — https://skillbuilder.aws/learn/XHRS91KKK6/aws-lambda-foundations/R85JRN3APC
- Architecting Serverless Applications — https://skillbuilder.aws/learn/MRWENY7FSX/architecting-serverless-applications/QVFY2JHVEH
- Amazon API Gateway for Serverless Applications — https://skillbuilder.aws/learn/GQA6FHWPJD/amazon-api-gateway-for-serverless-applications/JVRZ3PSW4H
- Deploying Serverless Applications — https://skillbuilder.aws/learn/M531VCW415/deploying-serverless-applications/SMY21G7FYZ
- Introduction to Amazon DynamoDB (Lab) — https://skillbuilder.aws/learn/6DYXN7K7ZQ/lab--introduction-to-amazon-dynamodb/GZ3EU55RYJ
- Amazon DynamoDB for Serverless Architecture — https://skillbuilder.aws/learn/SY1Y83VKTB/amazon-dynamodb-for-serverless-architectures/K9NM3PHH3S
- Modernize a Monolith to ECS and Fargate using Application Discovery — https://skillbuilder.aws/learn/1YXAWYH2WA/modernize-a-monolith-to-ecs-and-fargate-using-application-discovery/AQ37WHN3K1
- Meeting Simulator: Transform Monolithic App into Serverless Microservices — https://skillbuilder.aws/learn/HUKQHYU9TB/meeting-simulator-transforming-our-monolithic-app-into-serverless-microservices/NS6S2J7YR7

**Module 3: Move to Containers with Amazon ECS and EKS:**
- AWS Modernization Pathways: Move to Containers with Amazon EKS — https://skillbuilder.aws/learning-plan/GNYBZ9X9EM/aws-modernization-pathways-move-to-containers-with-amazon-eks-includes-labs/1HB9MKXD2N
- AWS Modernization Pathways: Move to Containers with Amazon ECS — https://skillbuilder.aws/learning-plan/CDA8Y4JRRR/aws-modernization-pathways-move-to-containers-with-amazon-ecs-includes-labs/1UB9AW4KYN
- Introduction to Containers — https://skillbuilder.aws/learn/CUCA1DK47V/introduction-to-containers/XJ58VC1FF5
- AWS Fargate Getting Started — https://skillbuilder.aws/learn/6QS9CM1V7K/aws-fargate-getting-started/EDX6V7B5YR
- Amazon ECR Getting Started — https://skillbuilder.aws/learn/M494WWS5EF/amazon-ecr-getting-started/N5CQ7DC6HT
- Amazon EKS Primer — https://skillbuilder.aws/learn/Z521GMBP1J/amazon-eks-primer/NGM5AF9K72
- Deploy Applications on Amazon EKS (Lab) — https://skillbuilder.aws/learn/2B5XUE2V9C/lab--deploy-applications-on-amazon-elastic-kubernetes-service-eks/SM5HZNTY9J
- Amazon ECS Getting Started — https://skillbuilder.aws/learn/CY2F57HH7V/amazon-ecs-getting-started/4QUDNRVSNC
- Working with Amazon Elastic Container Service (Lab) — https://skillbuilder.aws/learn/CV6ZEU3NHE/working-with-amazon-elastic-container-service/X989GB8H74
- EKS Workshop — https://www.eksworkshop.com/
- EKS Auto Mode Workshop — https://catalog.workshops.aws/workshops/aadbd25d-43fa-4ac3-ae88-32d729af8ed4

**Module 4: Move to Managed Databases:**
- AWS Modernization Pathways: Move to Managed Databases — https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC/aws-modernization-pathways-move-to-managed-databases-includes-labs/2S2QZKG9DV
- Introduction to Building with AWS Databases — https://skillbuilder.aws/learn/HYKKWEN9ZS/introduction-to-building-with-aws-databases/V7RVH2KY91
- Selecting your Data Migration Strategy with AWS — https://skillbuilder.aws/learn/RKGP54WJPP/selecting-your-data-migration-strategy-with-aws/D38U3CZEYR
- AWS Database Migration Service (DMS) Getting Started — https://skillbuilder.aws/learn/ND246G8Y3W/aws-database-migration-service-aws-dms-getting-started/QK5CCBP464
- Introduction to AWS Database Migration Service (Lab) — https://skillbuilder.aws/learn/CX63W1TFSH/introduction-to-aws-database-migration-service/3DJVXSU4SE
- Amazon RDS for Oracle Getting Started — https://skillbuilder.aws/learn/YMYMJUMAET/amazon-rds-for-oracle-getting-started/74GQB3CA9U
- Amazon RDS for SQL Server Getting Started — https://skillbuilder.aws/learn/WSV85JHZFF/amazon-rds-for-sql-server-getting-started/E446MXPEYH
- Migrating RDS MySQL to Aurora (Lab) — https://skillbuilder.aws/learn/RZF2GBUUWX/migrating-rds-mysql-to-aurora-with-read-replica/SMG825PXTK
- Amazon DocumentDB Getting Started — https://skillbuilder.aws/learn/5RTP1DW5WQ/amazon-documentdb-with-mongodb-compatibility-getting-started/JDFWRT5GPD
- Amazon Keyspaces Getting Started — https://skillbuilder.aws/learn/KHGZNGWXKV/amazon-keyspaces-getting-started/MXK17GET8G
- Amazon RDS for MariaDB Getting Started — https://skillbuilder.aws/learn/DAFQM637NV/amazon-rds-for-mariadb-getting-started/N2Z47FGXSE
- AWS PartnerCast: Vector Databases for Generative AI Applications — https://skillbuilder.aws/learn/UQ74USQJHU/aws-partnercast--vector-databases-for-generative-ai-applications--technical/7DKMBAPCST

**Module 5: Move to Managed Analytics:**
- AWS Modernization Pathways: Move to Managed Analytics — https://skillbuilder.aws/learning-plan/RWZA84NMVV/aws-modernization-pathways-move-to-managed-analytics--includes-labs/9BAKK2QQQU

**Module 6: Move to Modern DevOps:**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
- Working with AWS CodeCommit — https://skillbuilder.aws/learn/SH4UVGQX6S/working-with-aws-codecommit/Y9UGFPK95M
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
- AWS CloudFormation Getting Started — https://skillbuilder.aws/learn/RH22P2RXU4/aws-cloudformation-getting-started/KEK5BT6HSE
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
- Monitor Java Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/PMCTXKYK1Y/monitor-java-applications-using-amazon-cloudwatch-application-signals/15ZK4ETKE9
- Monitor .NET Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/255DDEDPV5/monitor-net-applications-using-amazon-cloudwatch-application-signals/1WZ1NT16HJ
- Monitor Python Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/JMPDZD64MV/monitor-python-applications-using-amazon-cloudwatch-application-signals/2JP3J2MPCK
- AWS Developer: CI/CD Automation — https://skillbuilder.aws/learn/C1KF8ZJ1D8/aws-developer--cicd-automation/KY1E1JS9FA
- AWS PartnerCast: Automate EKS Deployments With GitOps Using ArgoCD and GitHub Actions — https://skillbuilder.aws/learn/D9U7XMXP31/aws-partnercast--tech-talks--automate-eks-deployments-with-gitops-using-argocd-and-github-actions--technical/Z4M9Z8FY88
- AWS PartnerCast: Next-Gen Platform Engineering: Combining EKS, GitOps & Amazon Q for Intelligent DevOps — https://skillbuilder.aws/learn/FJBV2YWNSS/aws-partnercast--tech-talks--nextgen-platform-engineering-combining-eks-gitops--amazon-q-for-intelligent-devops--technical/NZ284HRTVG
- AWS PartnerCast: Unleash Innovation with a Cloud Operating Model and Platform Engineering — https://skillbuilder.aws/learn/EG2A78NXEC/aws-partnercast--tech-talks--unleash-innovation-with-a-cloud-operating-model-and-platform-engineering--technical/CC8ZTK88QK
- EKS Workshop: Automation — https://www.eksworkshop.com/docs/automation/
- EKS SaaS GitOps Workshop — https://catalog.workshops.aws/eks-saas-gitops/en-US/03-lab1

**Module 7: Move to AI:**
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
- Introduction to Generative AI: Art of the Possible — https://skillbuilder.aws/learn/ZEVZZ1D4AS/introduction-to-generative-ai--art-of-the-possible/Y7MTGJCW1U
- Planning a Generative AI Project — https://skillbuilder.aws/learn/HU1FQRGDDZ/planning-a-generative-ai-project/SYR3SCPSHC
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
- Essentials for Prompt Engineering — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
- AWS SimuLearn: Prompt Engineering with Amazon Bedrock — https://skillbuilder.aws/learn/FC13FQVQYG/aws-simulearn-prompt-engineering-with-amazon-bedrock/QDGW58VYHP
- Optimizing Foundation Models — https://skillbuilder.aws/learn/CDYTAJCKGY/optimizing-foundation-models/PVR1FRGN1T
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
- Amazon Q Developer Getting Started — https://skillbuilder.aws/learn/BQMRXE8AB4/amazon-q-developer-getting-started/JY4XXGZDJA
- Re-imagine Developer Experience using Amazon Q Developer (Lab) — https://skillbuilder.aws/learn/F7D8YHMVYK/lab--reimagine-developer-experience-using-amazon-q-developer/ZWRC749F68
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
- DevOps and AI on AWS: CloudWatch Anomaly Detection (Lab) — https://skillbuilder.aws/learn/RWYVJ73MXP/lab--devops-and-ai-on-aws-cloudwatch-anomaly-detection/BRPDNZUGU7
- Introduction to AWS DevOps Agent (Lab) — https://skillbuilder.aws/learn/2BMGKG58ZU/introduction-to-aws-devops-agent/S61EE8J7S9
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
- AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84

Only include links from categories that are relevant to the gaps found in this specific assessment.

---

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: <topic>
- **Score**: X/4 <status emoji>
- **Finding**: <what was observed, with specific file and resource references>
- **Gap**: <what is missing>
- **Recommendation**: <specific next step>

<Repeat for all INF questions in the same format>

### Application Architecture

#### APP-Q1: <topic>
- **Score**: X/4 <status emoji>
- **Finding**: <what was observed, with specific file and resource references>
- **Gap**: <what is missing>
- **Recommendation**: <specific next step>

<Repeat for all APP questions in the same format>

### Data Foundations

#### DATA-Q1: <topic>
- **Score**: X/4 <status emoji>
- **Finding**: <what was observed, with specific file and resource references>
- **Gap**: <what is missing>
- **Recommendation**: <specific next step>

<Repeat for all DATA questions in the same format>

### Identity, Security & Governance

#### SEC-Q1: <topic>
- **Score**: X/4 <status emoji>
- **Finding**: <what was observed, with specific file and resource references>
- **Gap**: <what is missing>
- **Recommendation**: <specific next step>

<Repeat for all SEC questions in the same format>

### Operations & Observability

#### OPS-Q1: <topic>
- **Score**: X/4 <status emoji>
- **Finding**: <what was observed, with specific file and resource references>
- **Gap**: <what is missing>
- **Recommendation**: <specific next step>

<Repeat for all OPS questions in the same format>

---

## Appendix: Evidence Index

<List key files examined during the assessment and what each revealed. Limit to 20 files.>
```

### Scoring Scale

Use this scoring scale consistently for all criteria:

| Score | Label | Meaning |
|-------|-------|---------|
| 4 | ✅ Agent-Ready | Fully meets the criterion. No gaps. |
| 3 | 🟡 Partial | Partially meets the criterion. Minor gaps. |
| 2 | 🟠 Needs Work | Exists but significant gaps. Moderate effort needed. |
| 1 | ❌ Not Present | Missing entirely or fundamentally inadequate. |

Calculate category scores as the average of all question scores in that category. Calculate the overall score as the average of all five category scores.

## Constraints and Guardrails

Strictly follow these rules at all times:

- **Be specific**: Always reference actual file names, resource names, and patterns found. Never write "there may be..." — state what was found or what was not found.
- **Absence is evidence**: If a search for OpenAPI specs finds none, that is a score of 1 (Not Present) for APP-Q2. State that clearly.
- **Read before judging**: Do not score a criterion without actually reading relevant files. If relevant files have not been found yet, keep searching.
- **Calibrate scores honestly**: A score of 4 means genuinely agent-ready, not just "has something." A score of 3 means meaningfully partial. Do not inflate scores.
- **IaC is ground truth**: Trust IaC definitions over README descriptions. What is deployed is what is defined in the IaC.
- **Do not modify any source code**: This is a read-only assessment. Only create the output report file.
- **Do not skip criteria**: All 42 criteria must be evaluated and scored in the report.
- **Microservices decomposition guidance**: If APP-Q4 score < 4 (monolith detected), include the "Microservices Decomposition Strategy" section in the roadmap with:
  - Recommended approach (Option B or C) based on modularity assessment
  - LoE estimates for each option
  - Pattern recommendations based on findings from APP-Q3, APP-Q7, APP-Q9, APP-Q12, DATA-Q4, INF-Q4
  - Specific starting points and first service extraction candidates
  - Integration of decomposition activities into Phase 1, 2, and 3 guidance
- **Customer choice**: Present options, not prescriptions. The customer decides between parallel track (Option B) or conditional/adaptive (Option C) based on their business priorities and risk tolerance.

## Validation / Exit Criteria

1. The directory `agentic-readiness-assessment` is created in the repository root (or already exists)
2. The report file `{project-name}-agentic-readiness-report.md` is created in the `agentic-readiness-assessment` directory
3. The report contains an Executive Summary with an overall numeric score
4. The report contains a score table with all five categories scored
5. The report contains a Top Priorities section with exactly 5 critical gaps
6. The report contains a Readiness Roadmap with three phases
7. The report contains a Recommended Self-Paced Learning Materials section with relevant links
8. The report contains Detailed Findings with all criteria scored 
9. Every finding references specific files or explicitly states what was not found
10. The report contains an Appendix: Evidence Index listing up to 20 key files examined
11. The report is formatted in valid Markdown with clear sections and readable structure
12. No source code files in the repository were modified
