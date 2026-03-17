
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

### Step 0: Read Goal & Classify Repo

Before beginning the discovery scan, read the assessment context from `additionalPlanContext` to determine the goal, preferences, and repo classification that will shape the entire assessment.

#### 0.1 Read Assessment Context

Extract the following fields from `additionalPlanContext`:

- **`goal`** — The customer's modernization objective. Must be one of the 4 predefined values below.
- **`goal_context`** — Optional free-text field providing additional context for scoping recommendations (e.g., "Building a customer support agent for order and inventory data").
- **`repo_type`** — Optional user-provided repo classification override. If present, use it directly instead of auto-detecting.
- **`context`** — Optional free-text description of the repository (e.g., "Legacy PHP e-commerce app running on EC2 with MySQL").
- **`preferences`** — Optional object with `prefer` and `avoid` string arrays that guide recommendations:
  - `prefer`: technologies/patterns to favor (e.g., `["eks", "aurora", "bedrock"]`)
  - `avoid`: technologies/patterns to avoid (e.g., `["serverless", "microservices-decomposition"]`)

#### 0.2 Validate and Default the Goal

Apply these rules to determine the effective goal:

1. If `goal` is present and is one of the 4 predefined values → use it as-is.
2. If `goal` is absent → default to `agentic-readiness`.
3. If `goal` is present but not one of the 4 predefined values → default to `agentic-readiness` and log a warning: **"Unrecognized goal '{value}', defaulting to agentic-readiness"**.

The `goal_context` field is always passed through regardless of goal validation — it provides additional framing even when the goal defaults.

#### 0.3 Goal Definition Reference Card

Use this reference throughout the assessment to determine phase names, priority criteria, pathway alignment, and conditional report sections.

```
GOAL DEFINITIONS:

enable-agentic-use-case:
  description: "Enable a specific agentic AI use case — scoped to the identified use case being built"
  primary_pathways: [Move to AI, Move to Managed Databases, Move to Modern DevOps]
  phases: [Agent Quick Wins, Agent Foundations, Agent Scale & Optimization]
  priority_criteria: [APP-Q2, APP-Q13, DATA-Q1, DATA-Q2, DATA-Q3, SEC-Q7, OPS-Q3, OPS-Q6]

cloud-native-modernization:
  description: "Decompose and modernize into cloud-native architectures"
  primary_pathways: [Move to Cloud Native, Move to Containers, Move to Modern DevOps]
  phases: [Containerize & Automate, Decompose & Decouple, Optimize & Scale]
  priority_criteria: [APP-Q4, INF-Q1, INF-Q5, INF-Q6, APP-Q3, OPS-Q9]

cost-optimization:
  description: "Reduce costs through license elimination, managed services, right-sizing"
  primary_pathways: [Move to Open Source, Move to Managed Databases, Move to Managed Analytics]
  phases: [License & Quick Savings, Managed Service Migration, Optimization & Governance]
  priority_criteria: [INF-Q2, DATA-Q2, DATA-Q10, DATA-Q11, INF-Q8]

agentic-readiness:
  description: "Evaluate overall agentic readiness across all dimensions with equal weighting"
  primary_pathways: [all equal]
  phases: [Quick Wins, Foundation, Advanced Capabilities]
  priority_criteria: [all equal]
```

#### 0.4 Goal Alignment Mapping

Use this table in Step 7 (Pathway Mapping) to populate the "Goal Alignment" column for each pathway.

| Goal | High Alignment | Medium Alignment | Low Alignment |
|------|---------------|-----------------|--------------|
| `enable-agentic-use-case` | Move to AI, Move to Managed Databases, Move to Modern DevOps | Move to Cloud Native, Move to Containers | Move to Open Source, Move to Managed Analytics |
| `cloud-native-modernization` | Move to Cloud Native, Move to Containers, Move to Modern DevOps | Move to Managed Databases, Move to Open Source | Move to AI, Move to Managed Analytics |
| `cost-optimization` | Move to Open Source, Move to Managed Databases, Move to Managed Analytics | Move to Containers, Move to Modern DevOps | Move to Cloud Native, Move to AI |
| `agentic-readiness` | All Medium | — | — |

#### 0.5 Goal-Specific Phase Names

Use these phase names in Step 8 (Report Generation) for the Readiness Roadmap section.

| Goal | Phase 1 | Phase 2 | Phase 3 |
|------|---------|---------|---------|
| `agentic-readiness` | Quick Wins (Days 1–30) | Foundation (Months 1–3) | Advanced Capabilities (Months 3–6) |
| `enable-agentic-use-case` | Agent Quick Wins (Days 1–30) | Agent Foundations (Months 1–3) | Agent Scale & Optimization (Months 3–6) |
| `cloud-native-modernization` | Containerize & Automate (Days 1–30) | Decompose & Decouple (Months 1–3) | Optimize & Scale (Months 3–6) |
| `cost-optimization` | License & Quick Savings (Days 1–30) | Managed Service Migration (Months 1–3) | Optimization & Governance (Months 3–6) |

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

#### 1.1 Repo Type Classification

After completing the file discovery scan above, classify the repository type. The detected repo type determines which assessment criteria apply (some criteria are scored as N/A for non-application repos) and influences pathway applicability in Step 7.

**If `repo_type` was provided in Step 0** (from `additionalPlanContext`), use it directly and skip auto-detection. User-provided overrides always take precedence.

**If `repo_type` was NOT provided**, apply the following detection decision tree using the files discovered above:

```
1. Check for source code files (.py, .java, .js, .ts, .go, .cs):

   IF source code files exist:
     a. Check for multiple independent service directories with separate build configs
        (e.g., services/api/ with its own package.json, services/worker/ with its own pom.xml,
        or packages/ dirs each with their own dependency manifest).
        → If yes: repo_type = "monorepo"

     b. Check if a package manifest exists (package.json, pom.xml, requirements.txt, go.mod,
        *.csproj, *.gradle) but NO deployable entry point is found:
        - No Dockerfile
        - No IaC files (Terraform, CDK, CloudFormation, Helm, Kustomize)
        - No main application entry point (no main(), no if __name__ == "__main__",
          no server.listen(), no @SpringBootApplication, no func main())
        → If yes: repo_type = "library"

     c. Otherwise:
        → repo_type = "application"

   IF NO source code files exist:
     a. Check if only IaC files exist (Terraform .tf files, CDK stacks, CloudFormation
        templates, Helm charts, Kustomize configs, ACK/KRO manifests):
        → If yes: repo_type = "infrastructure-only"

     b. Check if only CI/CD definition files exist (GitHub Actions workflows, Jenkinsfile,
        buildspec.yml, .gitlab-ci.yml, deployment scripts, Helm charts for deployment only):
        → If yes: repo_type = "deployment-cicd"

     c. Otherwise:
        → repo_type = "application" (default — most comprehensive assessment)
```

**Repo Type Definitions:**

| Repo Type | Description | Example |
|-----------|-------------|---------|
| `application` | Contains application source code. This is the default when source code files exist alongside other files. | Java service, Python API, Node.js app |
| `infrastructure-only` | Only IaC files exist with NO source code files. | Terraform modules, CDK stacks, CloudFormation templates |
| `deployment-cicd` | Only CI/CD definition files exist with NO source code and NO IaC. | GitHub Actions workflows, Jenkinsfiles, Helm deployment charts |
| `monorepo` | Multiple independent service directories with separate build configs. | Monorepo with `services/`, `packages/` dirs each with their own package manifest |
| `library` | Package manifest exists but NO deployable entry point (no Dockerfile, no IaC, no main application entry point). | Internal SDK, shared utilities package |

**Record the detected `repo_type`** in the assessment context. It will be used in:
- **Steps 2–6** (Scoring): To determine which criteria are scored as N/A for the detected repo type
- **Step 7** (Pathway Mapping): To determine which pathways are "Not Applicable" for the repo type
- **Step 8** (Report Generation): To include the repo type in the report metadata header

### N/A Criteria Mapping by Repo Type

Before scoring criteria in Steps 2–6, consult this mapping to determine which criteria are N/A for the detected repo type (from Step 1.1). Criteria scored as N/A are excluded from category averages and the overall score.

**N/A Criteria by Repo Type:**

| Repo Type | Criteria Scored as N/A |
|-----------|----------------------|
| `application` | None — all 56 criteria apply |
| `infrastructure-only` | APP-Q1 through APP-Q13, DATA-Q1 through DATA-Q9, DATA-Q11 |
| `deployment-cicd` | APP-Q1 through APP-Q13, DATA-Q1 through DATA-Q11, INF-Q1 through INF-Q4, INF-Q7 through INF-Q10 |
| `library` | INF-Q1 through INF-Q10, OPS-Q4 through OPS-Q12 |
| `monorepo` | None — all 56 criteria apply (assessed per-service within the repo) |

**N/A Display Format:**

When a criterion is N/A for the detected repo type, display it as:

```markdown
#### <Criterion ID>: <Criterion Name>
- **Score**: N/A
- **Finding**: This is a <repo_type> repository. <Category> criteria do not apply.
- **Gap**: N/A
- **Recommendation**: N/A
```

For example, for an `infrastructure-only` repo:

```markdown
#### APP-Q1: Programming Languages
- **Score**: N/A
- **Finding**: This is an infrastructure-only repository. Application architecture criteria do not apply.
- **Gap**: N/A
- **Recommendation**: N/A
```

### Step 2: Evaluate Infrastructure & Platform (10 criteria)

> **N/A Check**: Before scoring each criterion below, check the N/A Criteria Mapping above. If the criterion is N/A for the detected repo type, use the N/A display format instead of scoring it. For `deployment-cicd` repos, INF-Q1 through INF-Q4 and INF-Q7 through INF-Q10 are N/A. For `library` repos, all INF criteria (INF-Q1 through INF-Q10) are N/A.

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

> **N/A Check**: Before scoring each criterion below, check the N/A Criteria Mapping from the preamble above Step 2. If the criterion is N/A for the detected repo type, use the N/A display format instead of scoring it. For `infrastructure-only` and `deployment-cicd` repos, all APP criteria (APP-Q1 through APP-Q13) are N/A.

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

> **N/A Check**: Before scoring each criterion below, check the N/A Criteria Mapping from the preamble above Step 2. If the criterion is N/A for the detected repo type, use the N/A display format instead of scoring it. For `infrastructure-only` repos, DATA-Q1 through DATA-Q9 and DATA-Q11 are N/A (DATA-Q10 still applies). For `deployment-cicd` repos, all DATA criteria (DATA-Q1 through DATA-Q11) are N/A.

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

> **N/A Check**: Before scoring each criterion below, check the N/A Criteria Mapping from the preamble above Step 2. If the criterion is N/A for the detected repo type, use the N/A display format instead of scoring it. No SEC criteria are N/A for any repo type — all 10 security criteria apply to all repo types (`application`, `infrastructure-only`, `deployment-cicd`, `library`, `monorepo`).

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

> **N/A Check**: Before scoring each criterion below, check the N/A Criteria Mapping from the preamble above Step 2. If the criterion is N/A for the detected repo type, use the N/A display format instead of scoring it. For `library` repos, OPS-Q4 through OPS-Q12 are N/A (OPS-Q1 through OPS-Q3 still apply).

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

### Scoring Calculation Rules (N/A-Adjusted)

After completing Steps 2–6, calculate category and overall scores using these rules to properly handle N/A criteria:

**Category Averages:**
- Calculate each category average using only scored (non-N/A) criteria. Exclude N/A criteria from both the numerator and the denominator.
- Example: If Infrastructure & Platform has 10 criteria but 3 are N/A for the detected repo type, the category average = sum of the 7 scored criteria ÷ 7.

**Edge Case — All Criteria N/A in a Category:**
- If ALL criteria in a category are N/A for the detected repo type, the category score is **"N/A"**. Skip that category entirely when calculating the overall average.
- This can happen for `deployment-cicd` repos where Application Architecture (all 13 criteria N/A) and Data Foundations (all 11 criteria N/A) are entirely inapplicable.

**Overall Score:**
- Overall score = average of the 5 category scores, where each category score is already adjusted for N/A exclusion.
- If a category is entirely N/A, exclude it from the overall average denominator.
- Example: If a `deployment-cicd` repo has only 3 scoreable categories (Infrastructure, Security, Operations), the overall score = (INF avg + SEC avg + OPS avg) ÷ 3.

**Score Table Display for N/A Categories:**

When a category is entirely N/A, display it in the score table as:

```markdown
| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 2.8 / 4.0 | 🟡 |
| Application Architecture | N/A | ➖ |
| Data Foundations | N/A | ➖ |
| Identity, Security & Governance | 3.2 / 4.0 | 🟡 |
| Operations & Observability | 2.5 / 4.0 | 🟡 |
```

Use ➖ as the status emoji for N/A categories.

### Step 7: Map to AWS Modernization Pathways

Based on the scores and findings from Steps 2-6, determine which AWS Modernization Pathways apply to this application. Multiple pathways can apply simultaneously because modern applications comprise multiple interconnected components — each requiring its own modernization approach.

#### 7.1 Pathway Status Determination

Evaluate each pathway independently and assign exactly one of three statuses:

- **Triggered** — The pathway's trigger conditions are met. Show the priority level and key trigger criteria.
- **Not Triggered** — The pathway's trigger conditions are NOT met, but the pathway is still listed. Priority shown as "—".
- **Not Applicable** — The pathway does not apply to the detected repo type (from Step 1.1). Show a reason explaining why (e.g., "Infrastructure-only repo — no application compute to containerize"). Priority shown as "—".

**Status determination order (V2.5 four-step evaluation):** For each pathway, follow this evaluation order strictly. Stop at the first step that produces a result:

```
For each pathway:
  Step 1: Is pathway N/A for repo type? → "Not Applicable" (stop — see section 7.3)
  Step 2: Does contextual guard pass? → If no: "Not Triggered" (stop)
  Step 3: Are trigger conditions met at goal-weighted threshold? → If yes: "Triggered" (stop)
  Step 4: Otherwise: "Not Triggered"
```

Earlier steps always take precedence. A pathway that is N/A by repo type is never evaluated for contextual guards. A pathway whose contextual guard fails is never evaluated for trigger thresholds.

#### 7.2 Pathway Trigger Rules

Evaluate each pathway using the four-step evaluation order above. Each pathway has three components: (A) a contextual relevance guard, (B) trigger conditions, and (C) goal-weighted threshold behavior. The contextual guard must pass before trigger conditions are evaluated. The goal-weighted threshold (see section 7.2.1) determines how many trigger conditions must be met based on the pathway's Goal Alignment level for the current goal.

**Move to Cloud Native (Containers and Serverless):**

**(A) Contextual Guard:** APP-Q4 must be < 3. If APP-Q4 ≥ 3 (already modular or microservices), the pathway is **Not Triggered** — stop evaluation. Async and long-running process gaps (APP-Q3, APP-Q10) in an already-decomposed service are maturity improvements within the existing architecture, not Cloud Native migration needs.

**(B) Trigger Conditions** (evaluated only if guard passes):
- APP-Q4 < 3 (monolith or tightly coupled)
- INF-Q1 < 3 (EC2-heavy compute)
- APP-Q3 < 3 (sync-heavy communication)
- APP-Q10 < 3 (no async for long-running operations)

**(C) Goal-Weighted Thresholds** (see section 7.2.1 for tier definitions):
- High alignment: ANY 1 condition met → Triggered
- Medium alignment: At least 2 conditions met → Triggered
- Low alignment: APP-Q4 ≤ 2 (primary criterion, severe gap) → Triggered

- Focus: Decompose monolith applications into loosely coupled distributed architectures using microservices
- Representative AWS Services: Lambda, API Gateway, Step Functions, EventBridge
- Aligns with: Phase 2 (Foundation) and Phase 3 (Agent Enablement) roadmap activities

**Move to Containers:**

**(A) Contextual Guard:** Compute must be EC2/VM-based or bare-metal. If INF-Q1 ≥ 3 (already Lambda/Fargate/ECS), the pathway is **Not Triggered** — stop evaluation. Absence of Dockerfile is expected for serverless workloads, not a gap.

**(B) Trigger Conditions** (evaluated only if guard passes):
- INF-Q1 < 3 (no managed container orchestration or serverless)
- No Dockerfile or container definitions found in discovery

**Removed from V2:** `APP-Q4 < 4` is no longer a trigger condition. Monolith detection is a Cloud Native concern, not a Containers concern. A monolith on ECS is already containerized.

**(C) Goal-Weighted Thresholds** (see section 7.2.1 for tier definitions):
- High alignment: ANY 1 condition met → Triggered
- Medium alignment: Both conditions met → Triggered
- Low alignment: INF-Q1 ≤ 2 AND no Dockerfile → Triggered

- Focus: Containerize existing workloads and adopt fully managed container orchestration services
- Representative AWS Services: ECS, EKS, Fargate, ECR
- Aligns with: Phase 1 (Quick Wins) for Dockerfile creation, Phase 2 (Foundation) for orchestration

**Move to Open Source:**

**(A) Contextual Guard:** None required — the current trigger rules are already precise and evidence-based. Commercial database/license detection does not suffer from the "absence = gap" problem.

**(B) Trigger Conditions** (unchanged from V2):
- DATA-Q11 < 3 (proprietary SQL/stored procedures detected)
- INF-Q2 findings mention commercial database engines (Oracle, SQL Server, or other commercial licenses)

**(C) Goal-Weighted Thresholds** (see section 7.2.1 for tier definitions):
- High alignment: ANY 1 condition met → Triggered
- Medium alignment: At least 2 conditions met → Triggered
- Low alignment: Primary criterion (DATA-Q11 or INF-Q2) ≤ 2 → Triggered

- Focus: Move away from commercial workloads/licenses to open source for flexibility and reduced cost
- Representative AWS Services: RDS open source engines (PostgreSQL, MySQL, MariaDB), EKS, Amazon Linux
- Aligns with: Phase 2 (Foundation) for database migration planning

**Move to Managed Databases:**

**(A) Contextual Guard:** INF-Q2 findings must show self-managed or significantly under-managed databases (self-hosted MySQL/PostgreSQL on EC2, unmanaged Redis, MongoDB on containers, etc.). If all databases are already fully managed (DynamoDB, Aurora, RDS, ElastiCache, DocumentDB), the pathway is **Not Triggered** — stop evaluation.

**(B) Trigger Conditions** (evaluated only if guard passes):
- INF-Q2 < 3 (self-managed databases detected) — threshold raised from `< 4`
- DATA-Q10 < 3 (EOL or unpinned database engine versions) — threshold raised from `< 4`

**Removed from V2:** `DATA-Q2 < 4` (absence of vector DB) is no longer a trigger for this pathway. Vector DB gaps are an AI pathway concern. A service using DynamoDB (fully managed, score 4 on INF-Q2) should not be told to "Move to Managed Databases" because it lacks a vector store.

**(C) Goal-Weighted Thresholds** (see section 7.2.1 for tier definitions):
- High alignment: ANY 1 condition met → Triggered
- Medium alignment: At least 2 conditions met → Triggered
- Low alignment: INF-Q2 ≤ 2 (severe self-managed DB gap) → Triggered

- Focus: Adopt fully managed purpose-built cloud native databases for scalability and reduced operational burden
- Representative AWS Services: Aurora, RDS, DynamoDB, DocumentDB, ElastiCache, OpenSearch Service
- Aligns with: Phase 2 (Foundation) for migration, Phase 1 (Quick Wins) for version pinning

**Move to Managed Analytics:**

**(A) Contextual Guard:** Evidence of data processing, ETL, analytics workloads, or self-managed streaming infrastructure (self-hosted Kafka, RabbitMQ, Redis Streams, Spark, Hadoop, Flink) must be found during the Step 1 discovery scan. If none found, the pathway is **Not Triggered** — stop evaluation.

**(B) Trigger Conditions** (evaluated only if guard passes):
- INF-Q8 < 3 (self-managed streaming detected) — note: this now only fires when the repo actually HAS self-managed streaming, not when streaming is simply absent
- DATA-Q4 < 3 (data source sprawl with no unified access layer)

**Removed from V2:** The vague "no managed analytics services detected in discovery" catch-all clause is eliminated entirely. This was the primary source of false positives — it triggered for any repo that didn't use Kinesis/Redshift/Athena, even if the repo had zero analytics needs.

**(C) Goal-Weighted Thresholds** (see section 7.2.1 for tier definitions):
- High alignment: ANY 1 condition met → Triggered
- Medium alignment: Both conditions met → Triggered
- Low alignment: INF-Q8 ≤ 2 (severe self-managed streaming gap) → Triggered

- Focus: Adopt fully managed, cost-optimized data lake and real-time analytics
- Representative AWS Services: Redshift, Kinesis, MSK Serverless, Athena, Lake Formation
- Aligns with: Phase 2 (Foundation) for streaming migration, Phase 3 for analytics optimization

**Move to Modern DevOps:**

**(A) Contextual Guard:** None required — DevOps criteria (IaC, CI/CD, deployment strategies, testing, observability) are universally relevant to all application and infrastructure repos.

**(B) Trigger Conditions** (unchanged from V2):
- INF-Q5 < 3 (low IaC coverage)
- INF-Q6 < 3 (no CI/CD automation)
- OPS-Q9 < 3 (no canary/blue-green deployments)
- OPS-Q10 < 3 (no integration tests)
- OPS-Q1 < 3 (no distributed tracing)

**(C) Goal-Weighted Thresholds** (see section 7.2.1 for tier definitions):
- High alignment: ANY 1 condition met → Triggered
- Medium alignment: At least 2 conditions met → Triggered
- Low alignment: At least 2 conditions met AND one scores ≤ 2 → Triggered

- Focus: Adopt modern philosophies, practices, and tools for high-velocity application delivery
- Representative AWS Services: CodeCommit, CodeBuild, CodePipeline, CodeDeploy, CloudFormation, CDK, X-Ray, CloudWatch
- Aligns with: Phase 1 (Quick Wins) for IaC and CI/CD, Phase 2 for advanced deployment strategies

**Move to AI:**

**(A) Contextual Guard:** None required — in the context of an agentic readiness assessment, AI criteria are universally relevant. The entire assessment exists to evaluate AI readiness.

**(B) Trigger Conditions** (unchanged from V2):
- APP-Q13 < 3 (no agent frameworks)
- DATA-Q1 < 3 (no vector database)
- DATA-Q3 < 3 (no RAG implementation)
- OPS-Q3 < 3 (no eval framework)
- OPS-Q6 < 3 (no LLM cost tracking)

**(C) Goal-Weighted Thresholds** (see section 7.2.1 for tier definitions):
- High alignment: ANY 1 condition met → Triggered
- Medium alignment: At least 2 conditions met → Triggered
- Low alignment: At least 2 conditions met AND one scores ≤ 2 → Triggered

- Focus: Leverage AWS AI services to transform applications with AI capabilities, bridging traditional modernization and AI-driven computing
- Representative AWS Services: Amazon Bedrock, Amazon Bedrock AgentCore, Amazon Q, SageMaker
- Aligns with: Phase 3 (Agent Enablement) primarily, Phase 2 for data foundations (vector DB, RAG)

#### 7.2.1 Goal-Weighted Threshold Reference

The goal-weighted threshold determines how many trigger conditions must be met for a pathway to trigger, based on the pathway's Goal Alignment level (High, Medium, or Low) for the current goal.

| Alignment Tier | Threshold Rule | Rationale |
|---------------|---------------|-----------|
| **High** | ANY 1 trigger condition met → Triggered | Primary pathways for the goal. Even minor gaps are valuable to surface because the customer is actively pursuing this direction. |
| **Medium** | At least 2 trigger conditions met → Triggered | Relevant but not the customer's focus. A single marginal gap shouldn't generate a recommendation that distracts from the primary goal. |
| **Low** | Primary criterion ≤ 2 AND contextually relevant → Triggered | Tangential to the customer's goal. Only severe, undeniable gaps should surface these pathways. For pathways with 3+ conditions (Modern DevOps, Move to AI), Low requires at least 2 conditions met AND one scoring ≤ 2. |

**Special case — `agentic-readiness`:** When the goal is `agentic-readiness`, all 7 pathways have Medium alignment. This means every pathway requires at least 2 trigger conditions to fire. This is intentionally stricter than V2 (where everything triggered on a single OR) because agentic-readiness should surface only meaningful gaps, not every minor imperfection.

**Interaction with contextual guards:** The goal-weighted threshold is only evaluated AFTER the contextual guard passes (see the four-step evaluation order at the top of section 7.2). A pathway whose guard fails is "Not Triggered" regardless of goal alignment.

#### 7.3 Not Applicable Rules by Repo Type

Before evaluating trigger conditions, check if the pathway is Not Applicable for the detected repo type. Pathways marked N/A are listed in the summary table with status "Not Applicable", a reason, and "—" for Priority and Est. Effort.

| Repo Type | Not Applicable Pathways | Reason |
|-----------|------------------------|--------|
| `infrastructure-only` | Move to Cloud Native | N/A — no application code to decompose into cloud-native services |
| `infrastructure-only` | Move to Containers | N/A — no application to containerize |
| `infrastructure-only` | Move to AI | N/A — no application code for agent integration |
| `infrastructure-only` | Move to Managed Analytics | N/A — no data processing code |
| `deployment-cicd` | Move to Cloud Native | N/A — deployment repo, no application to decompose |
| `deployment-cicd` | Move to Containers | N/A — deployment repo, no application to containerize |
| `deployment-cicd` | Move to Open Source | N/A — deployment repo, no application or database workloads |
| `deployment-cicd` | Move to Managed Databases | N/A — deployment repo, no database workloads |
| `deployment-cicd` | Move to Managed Analytics | N/A — deployment repo, no data processing workloads |
| `deployment-cicd` | Move to AI | N/A — deployment repo, no application code for agent integration |
| `library` | Move to Containers | N/A — library is not independently deployable |
| `library` | Move to Modern DevOps | N/A — library has no deployment pipeline |
| `library` | Move to Managed Databases | N/A — library does not manage infrastructure |
| `library` | Move to Managed Analytics | N/A — library does not manage infrastructure |
| `library` | Move to Cloud Native | N/A — library is not a deployable service |
| `application` | _(none)_ | All 7 pathways are applicable |
| `monorepo` | _(none)_ | All 7 pathways are applicable |

**Note:** For `deployment-cicd` repos, only Move to Modern DevOps is applicable (the one pathway directly relevant to CI/CD and deployment practices). For `library` repos, Move to Open Source and Move to AI remain applicable (libraries can have licensing and AI integration concerns).

#### 7.4 Goal Alignment Column

Add a "Goal Alignment" column to the pathway summary table. The alignment value (High, Medium, or Low) is determined by looking up the current goal against the Goal Alignment Mapping table defined in **Step 0, section 0.4**.

For each pathway:
1. Look up the effective goal from Step 0.
2. Find the pathway in the Goal Alignment Mapping table (section 0.4).
3. Record the alignment as High, Medium, or Low.

The Goal Alignment column is shown for all pathways regardless of status (Triggered, Not Triggered, or Not Applicable).

#### 7.5 Priority and Recording Rules

**Priority is only shown for "Triggered" pathways.** Pathways with status "Not Triggered" or "Not Applicable" show "—" for Priority and Est. Effort.

**For each Triggered pathway, record:**
- Pathway name
- Status: Triggered
- Goal Alignment: High, Medium, or Low (from section 7.4)
- Trigger criteria met (which specific scores/findings triggered it)
- Priority: High (score < 2 on trigger criteria), Medium (score 2-2.9), Low (score 3-3.4)
- Key activities required (derived from the gap recommendations in the triggered criteria)
- Estimated effort level: High, Medium, or Low (based on number and severity of related gaps)
- Dependencies on other pathways (e.g., Move to Containers may be prerequisite for Move to Cloud Native)
- Relevant learning materials module (maps directly to the learning materials catalog)

**For each Not Triggered pathway, record:**
- Pathway name
- Status: Not Triggered
- Goal Alignment: High, Medium, or Low (from section 7.4)
- Priority: —
- Key Trigger Criteria: —
- Est. Effort: —

**For each Not Applicable pathway, record:**
- Pathway name
- Status: Not Applicable
- Goal Alignment: High, Medium, or Low (from section 7.4)
- Reason: Brief explanation of why the pathway does not apply (from the N/A rules table in section 7.3)
- Priority: —
- Key Trigger Criteria: The reason from the N/A rules table (e.g., "Infra-only repo — no app code")
- Est. Effort: —

#### 7.6 Pathway Summary Table Format

Present all 7 pathways in a single summary table using this format. Every pathway appears in the table regardless of status.

```markdown
| Pathway | Status | Goal Alignment | Priority | Key Trigger Criteria | Est. Effort |
|---------|--------|---------------|----------|---------------------|-------------|
| Move to Cloud Native | Triggered | High | High | APP-Q4: 1/4, INF-Q1: 1/4 | High |
| Move to Containers | Triggered | High | High | INF-Q1: 1/4 | Medium |
| Move to Open Source | Not Triggered | Low | — | — | — |
| Move to Managed Databases | Triggered | Medium | Medium | INF-Q2: 2/4 | Medium |
| Move to Managed Analytics | Not Applicable | Low | — | Infra-only repo — no data processing code | — |
| Move to Modern DevOps | Triggered | High | High | INF-Q5: 1/4, INF-Q6: 1/4 | High |
| Move to AI | Triggered | High | High | APP-Q13: 1/4, DATA-Q1: 1/4 | High |
```

**Table column definitions:**
- **Pathway**: The AWS Modernization Pathway name
- **Status**: Triggered, Not Triggered, or Not Applicable
- **Goal Alignment**: High, Medium, or Low (from the Goal Alignment Mapping in Step 0, section 0.4)
- **Priority**: High/Medium/Low for Triggered pathways; "—" for Not Triggered and Not Applicable
- **Key Trigger Criteria**: The specific criteria scores that triggered the pathway; "—" for Not Triggered; the N/A reason for Not Applicable
- **Est. Effort**: Estimated effort for Triggered pathways; "—" for Not Triggered and Not Applicable

#### 7.7 Parallel Execution Assessment

For Triggered pathways only:
- Identify which pathways can execute in parallel (no dependencies between them)
- Identify which pathways have sequential dependencies (e.g., containerize before decomposing to microservices)
- Note that a single application commonly pursues 3-5 pathways simultaneously

### Step 8: Generate the Agentic Readiness Report

**Output Location:**
- Create a directory named `agentic-readiness-assessment` in the repository root if it doesn't already exist
- Create the report file with the naming pattern: `{project-name}-agentic-readiness-report.md`
  - `{project-name}` should be derived from the repository name or a user-provided project identifier
  - Example: For a project named "payment-service", create `payment-service-agentic-readiness-report.md`
- Full path example: `agentic-readiness-assessment/payment-service-agentic-readiness-report.md`

#### 8.1 Goal-Driven Top 5 Critical Gaps Selection

When selecting the Top 5 Critical Gaps, apply goal-based weighting to prioritize criteria that matter most for the customer's objective:

1. Identify all criteria with scores below 3 (these are the candidate gaps).
2. Look up the effective goal's priority criteria from the Goal Definition Reference Card in Step 0 (section 0.3).
3. When two criteria have equal gap severity (same score), rank the goal-priority criterion higher.
4. For `agentic-readiness`, all criteria are weighted equally — select purely by gap severity (lowest scores first).
5. The Top 5 should still be based on actual gaps (low scores). The goal just breaks ties and boosts priority criteria when gaps are equally severe.

**Example**: If the goal is `enable-agentic-use-case` and both INF-Q1 (score 2) and APP-Q2 (score 2) are gaps, APP-Q2 ranks higher because it is a priority criterion for enable-agentic-use-case.

#### 8.2 Goal-Scoped Decomposition Section

The Microservices Decomposition Strategy section is conditionally included based on two factors: (1) whether a monolith exists (APP-Q4 < 4), and (2) the effective goal.

**If APP-Q4 >= 4** (no monolith detected): Omit the decomposition section entirely, regardless of goal.

**If APP-Q4 < 4** (monolith detected), apply goal-based scoping:

| Goal | Decomposition Section Behavior |
|------|-------------------------------|
| `cloud-native-modernization` | **Full section** — include all decomposition options (Option A/B/C), pattern recommendations, LoE estimates, and integration into all three roadmap phases. This is the current V1 behavior. |
| `agentic-readiness` | **Full section** — same as cloud-native-modernization. |
| `enable-agentic-use-case` | **Condensed paragraph** — replace the full decomposition section with: "This monolith would benefit from service extraction to create clear agent tool boundaries. See the Move to Cloud Native pathway for detailed decomposition guidance. For now, agents can interact with the monolith via its existing API surface." |
| `cost-optimization` | **Skip entirely** — omit the decomposition section unless decomposition directly reduces cost (e.g., extracting a service to move from a commercial database to open source). If cost-relevant, include a brief note only: "Decomposing [specific module] would enable migration from [commercial DB] to [open-source alternative], reducing licensing costs." |

#### 8.3 Quick Agent Wins Section

Include the Quick Agent Wins section in the report ONLY when the goal is `enable-agentic-use-case` or `agentic-readiness`. Omit this section entirely for `cloud-native-modernization` and `cost-optimization`.

**Score-threshold triggers for identifying wins:**

Scan the assessment scores and include a win for each threshold that is met:

| Condition | Win |
|-----------|-----|
| APP-Q2 >= 2 (API docs exist) | "Build an API-aware agent that can discover and invoke your existing endpoints" |
| APP-Q5 >= 3 (structured JSON responses) | "Agent tool integration is straightforward with your JSON APIs" |
| Documentation/README/wiki content exists | "Build a RAG-based knowledge agent using your existing documentation" |
| DATA-Q7 >= 2 (database with clear schema) | "Build a data query agent with natural language to SQL" |
| INF-Q6 >= 2 (CI/CD pipeline exists) | "Build a DevOps agent that can trigger deployments and check status" |

When `goal_context` is provided, tailor the wins to that context. For example, if `goal_context` mentions "customer support agent", frame wins around customer support use cases (e.g., "Build a customer support agent that queries your order database via natural language" instead of the generic "Build a data query agent").

**Placement in report**: The Quick Agent Wins section appears AFTER the pathway details and decomposition section, BEFORE the Readiness Roadmap.

#### 8.4 Goal-Specific Roadmap Phase Names

Use the goal-specific phase names from the Goal-Specific Phase Names table in Step 0 (section 0.5) for the Readiness Roadmap section. Do NOT use the generic V1 phase names.

| Goal | Phase 1 | Phase 2 | Phase 3 |
|------|---------|---------|---------|
| `agentic-readiness` | Quick Wins (Days 1–30) | Foundation (Months 1–3) | Advanced Capabilities (Months 3–6) |
| `enable-agentic-use-case` | Agent Quick Wins (Days 1–30) | Agent Foundations (Months 1–3) | Agent Scale & Optimization (Months 3–6) |
| `cloud-native-modernization` | Containerize & Automate (Days 1–30) | Decompose & Decouple (Months 1–3) | Optimize & Scale (Months 3–6) |
| `cost-optimization` | License & Quick Savings (Days 1–30) | Managed Service Migration (Months 1–3) | Optimization & Governance (Months 3–6) |

#### 8.5 Report Metadata Header

Include the detected repo type and effective goal in the report metadata header:

```markdown
- **Assessment Goal**: <effective goal value, e.g., enable-agentic-use-case>
- **Goal Context**: <goal_context value if provided, otherwise omit this line>
- **Repository Type**: <detected repo_type, e.g., application (auto-detected)>
```

#### 8.6 Report Template

Create the report file with exactly this structure. Sections marked with conditional logic should be included or omitted based on the rules in sections 8.1–8.5 above.

```markdown
# Agentic Readiness Assessment Report
**Target**: <repository path>
**Date**: <date>
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Assessment Goal**: <effective goal>
**Goal Context**: <goal_context if provided, otherwise omit>
**Repository Type**: <detected repo_type>

---

## Table of Contents

1. Executive Summary
2. Score Table
3. Top Priorities (Critical Gaps)
4. Detailed Findings
   - Infrastructure & Platform
   - Application Architecture
   - Data Foundations
   - Identity, Security & Governance
   - Operations & Observability
5. Recommended Modernization Pathways
   - Pathway Summary Table
   - Pathway Details (for Triggered pathways)
6. Microservices Decomposition Strategy (conditional — see section 8.2)
7. Quick Agent Wins (conditional — see section 8.3)
8. Readiness Roadmap
   - Phase 1 — <goal-specific name> (Days 1–30)
   - Phase 2 — <goal-specific name> (Months 1–3)
   - Phase 3 — <goal-specific name> (Months 3–6)
9. Recommended Self-Paced Learning Materials
10. Appendix: Evidence Index

---

## Executive Summary

<3-5 sentence summary of overall readiness. Be direct. Note the strongest areas and most critical gaps. Frame the summary around the effective goal — e.g., for enable-agentic-use-case, emphasize agent readiness; for cost-optimization, emphasize cost reduction opportunities. If goal_context is provided, reference it in the framing.>

### Overall Score: X.X / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | X.X / 4.0 | <status emoji> |
| Application Architecture | X.X / 4.0 | <status emoji> |
| Data Foundations | X.X / 4.0 | <status emoji> |
| Identity, Security & Governance | X.X / 4.0 | <status emoji> |
| Operations & Observability | X.X / 4.0 | <status emoji> |

Status emojis: use ✅ for scores >= 3.5, 🟡 for scores >= 2.5, 🟠 for scores >= 1.5, ❌ for scores < 1.5.

For categories where all criteria are N/A (due to repo type), display the score as "N/A" and use "—" for the status emoji.

---

## Top Priorities (Critical Gaps)

<List the 5 most impactful gaps using the goal-weighted selection logic from section 8.1. For each: what it is, why it matters for the customer's goal, and the first concrete step to address it. Frame "why it matters" around the effective goal — e.g., for enable-agentic-use-case, explain why the gap blocks agent workflows; for cost-optimization, explain the cost impact.>

---

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: <topic>
- **Score**: X/4 <status emoji>
- **Finding**: <what was observed, with specific file and resource references>
- **Gap**: <what is missing>
- **Recommendation**: <specific next step>

<Repeat for all INF questions. For N/A criteria, use the N/A display format from the N/A Criteria Mapping section.>

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

## Recommended Modernization Pathways

Based on the assessment findings, the following AWS Modernization Pathways are evaluated for this application. Multiple pathways can execute in parallel because modern applications comprise multiple interconnected components — each requiring its own modernization approach.

### Pathway Summary

<Use the V2 pathway table format from Step 7 (section 7.6). All 7 pathways appear in the table regardless of status.>

| Pathway | Status | Goal Alignment | Priority | Key Trigger Criteria | Est. Effort |
|---------|--------|---------------|----------|---------------------|-------------|
| Move to Cloud Native | <Triggered/Not Triggered/Not Applicable> | <High/Medium/Low> | <High/Medium/Low or —> | <criteria or — or N/A reason> | <High/Medium/Low or —> |
| Move to Containers | ... | ... | ... | ... | ... |
| Move to Open Source | ... | ... | ... | ... | ... |
| Move to Managed Databases | ... | ... | ... | ... | ... |
| Move to Managed Analytics | ... | ... | ... | ... | ... |
| Move to Modern DevOps | ... | ... | ... | ... | ... |
| Move to AI | ... | ... | ... | ... | ... |

### Parallel Execution Plan

<Describe which pathways can execute in parallel and which have sequential dependencies. For example, Move to Containers may be a prerequisite for Move to Cloud Native.>

**Parallel Track 1**: <pathways that can run concurrently>
**Parallel Track 2**: <pathways that can run concurrently>
**Sequential Dependencies**: <pathway A must complete before pathway B>

<For each Triggered pathway, include a subsection:>

### Move to <Pathway Name>

- **Priority**: High/Medium/Low
- **Goal Alignment**: High/Medium/Low
- **Trigger Criteria Met**:
  - <criterion ID>: Score X/4 — <brief finding>
  - <criterion ID>: Score X/4 — <brief finding>
- **Current State**: <summary of current state based on findings>
- **Target State**: <what agent-ready looks like for this pathway>
- **Key Activities**:
  1. <activity from roadmap>
  2. <activity from roadmap>
- **Dependencies**: <other pathways that must complete first, or "None">
- **Estimated Effort**: High/Medium/Low
- **Roadmap Phase Alignment**: Phase 1/2/3
- **Relevant Learning Materials**: Module X — <module name>

<Repeat for each Triggered pathway. Do NOT include subsections for Not Triggered or Not Applicable pathways.>

---

## Microservices Decomposition Strategy

<CONDITIONAL — apply the rules from section 8.2:>
<If APP-Q4 >= 4 (no monolith): OMIT this entire section.>
<If APP-Q4 < 4 AND goal is cloud-native-modernization or agentic-readiness: Include FULL section below.>
<If APP-Q4 < 4 AND goal is enable-agentic-use-case: Include CONDENSED paragraph only.>
<If APP-Q4 < 4 AND goal is cost-optimization: OMIT unless decomposition directly reduces cost.>

<FULL SECTION (for cloud-native-modernization and agentic-readiness):>

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

<CONDENSED PARAGRAPH (for enable-agentic-use-case):>

> This monolith would benefit from service extraction to create clear agent tool boundaries. See the Move to Cloud Native pathway for detailed decomposition guidance. For now, agents can interact with the monolith via its existing API surface.

---

## Quick Agent Wins

<CONDITIONAL — include ONLY when goal is enable-agentic-use-case or agentic-readiness. OMIT for cloud-native-modernization and cost-optimization.>

Even before completing the full modernization roadmap, these agent opportunities are available based on your current architecture:

<For each score-threshold trigger that is met (from section 8.3), include a numbered win:>

1. **<Win Title>** — <1-2 sentence description of what agent could be built now>
   - **Leverages**: <existing capability found in assessment, e.g., "OpenAPI spec at /api/swagger.json">
   - **Effort**: Low/Medium
   - **Value**: <what it enables>

2. **<Win Title>** — ...

<If goal_context is provided, tailor the wins to that context.>

> These opportunities can be pursued in parallel with the modernization roadmap.
> They demonstrate agent value early while foundations are being built.

---

## Readiness Roadmap

<Account for cross-dependencies between phases. For example, containerizing an application is a prerequisite for moving it to EKS/ECS. When dependencies exist, state them explicitly.>

### Phase 1 — <goal-specific phase 1 name from section 8.4>
<3-5 items that are low-effort but high-impact. Things that can be done in a sprint.>

<If APP-Q4 indicates monolith AND goal is cloud-native-modernization or agentic-readiness, include decomposition preparation:>
- Conduct EventStorming or domain modeling workshop to identify bounded contexts and service candidates
- Map current module dependencies and data coupling (use dependency analysis tools)
- Identify first candidate service for extraction: look for high business value, low coupling, clear domain boundary
- Document current API contracts and data flows to establish baseline before changes

### Phase 2 — <goal-specific phase 2 name from section 8.4>
<Structural improvements that require more planning but are essential.>

<If decomposition is recommended (Option B or C) AND goal is cloud-native-modernization or agentic-readiness, include:>
- **If Option B (Parallel Track)**: Extract first service using Strangler Fig pattern; implement API Gateway routing; establish service-to-service authentication; containerize extracted service
- **If Option C (Conditional)**: Containerize modular components as separate deployments; implement service discovery; add anti-corruption layers at module boundaries; defer tightly-coupled modules for Phase 3 refactoring

### Phase 3 — <goal-specific phase 3 name from section 8.4>
<Capabilities that unlock the target state once foundations are solid.>

<If decomposition is in progress AND goal is cloud-native-modernization or agentic-readiness:>
- Continue service extraction based on business priorities
- Implement domain-specific agent tools per service boundary
- Establish service-level SLOs and observability

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
- **Assessment foundations are invariant**: The 56 assessment criteria (INF-Q1 through OPS-Q12), 5 category structure (Infrastructure, Application, Data, Security, Operations), 1–4 scoring scale, 7 AWS Modernization Pathways, and pathway trigger rules remain unchanged from V1. V2 adds a priority lens on top — it does not alter the underlying assessment framework.
- **Do not skip criteria**: All 56 criteria must be evaluated and scored in the report. Criteria that are N/A for the detected repo type must still appear in the report using the N/A display format.
- **Repo type classification**: The agent must classify the repo type during Step 1 (Discovery) using the detection decision tree. A user-provided `repo_type` override in `additionalPlanContext` always takes precedence over auto-detection.
- **N/A scoring rules**: Criteria scored as N/A are excluded from category averages. If all criteria in a category are N/A, the category score is "N/A" and is skipped in the overall average calculation.
- **Goal is a priority lens, not a filter**: All 7 pathways are always evaluated for every repo regardless of goal. The goal only changes weighting, framing, phase names, and conditional section inclusion — it never removes pathways from evaluation.
- **Goal-scoped decomposition**: The decomposition section is conditionally included based on goal (see Step 8, section 8.2). Only include the full decomposition section for `cloud-native-modernization` and `agentic-readiness`. Use the condensed paragraph for `enable-agentic-use-case`. Skip for `cost-optimization` unless cost-relevant.
- **Quick Agent Wins conditional inclusion**: Include the Quick Agent Wins section only when goal is `enable-agentic-use-case` or `agentic-readiness`. Omit for `cloud-native-modernization` and `cost-optimization`.
- **Goal-specific phase names**: Always use the goal-specific phase names from Step 0 (section 0.5) in the Readiness Roadmap. Do not use generic phase names.
- **Goal-weighted Top 5**: Apply goal-priority criteria weighting when selecting the Top 5 Critical Gaps (see Step 8, section 8.1). For `agentic-readiness`, all criteria are weighted equally.
- **Report metadata**: Always include the detected repo type and effective goal in the report metadata header.
- **Customer choice**: Present options, not prescriptions. The customer decides between parallel track (Option B) or conditional/adaptive (Option C) based on their business priorities and risk tolerance.
- **Modernization Pathways**: All 7 AWS Modernization Pathways must be evaluated against the trigger criteria. Only include triggered pathways in the detailed subsections. A pathway is triggered when ANY of its trigger conditions are met. Multiple pathways executing in parallel is the norm, not the exception.
- **Pathway table format**: Use the V2 pathway table format with Status (Triggered/Not Triggered/Not Applicable), Goal Alignment, Priority, Key Trigger Criteria, and Est. Effort columns.

## Validation / Exit Criteria

1. The directory `agentic-readiness-assessment` is created in the repository root (or already exists)
2. The report file `{project-name}-agentic-readiness-report.md` is created in the `agentic-readiness-assessment` directory
3. The report contains a metadata header with Assessment Goal, Goal Context (if provided), and Repository Type
4. The report contains an Executive Summary with an overall numeric score framed around the effective goal
5. The report contains a score table with all five categories scored (N/A for categories where all criteria are N/A)
6. The report contains a Top Priorities section with exactly 5 critical gaps, weighted by goal-priority criteria
7. The report contains Detailed Findings with all 56 criteria evaluated and scored (including N/A criteria with proper display format where applicable based on repo type)
8. The report contains a Recommended Modernization Pathways section with the V2 pathway table (Status, Goal Alignment, Priority, Key Trigger Criteria, Est. Effort) for all 7 pathways
9. The report contains pathway detail subsections for each Triggered pathway (not for Not Triggered or Not Applicable)
10. The report contains a Microservices Decomposition Strategy section scoped by goal (full, condensed, or omitted per section 8.2 rules)
11. The report contains a Quick Agent Wins section when goal is `enable-agentic-use-case` or `agentic-readiness` (omitted for other goals)
12. The report contains a Readiness Roadmap with three phases using goal-specific phase names from Step 0 (section 0.5)
13. The report contains a Recommended Self-Paced Learning Materials section with relevant links
14. Every finding references specific files or explicitly states what was not found
15. The report contains an Appendix: Evidence Index listing up to 20 key files examined
16. The report is formatted in valid Markdown with clear sections and readable structure
17. No source code files in the repository were modified
