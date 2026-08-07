# MOD Modernization Pathways — Steps 7–9

> **Purpose:** Loaded by the Modernization Readiness Analysis (MOD) TD after scoring the 37 questions. Defines the 7 AWS Modernization Pathways with their full trigger logic and contextual guards (Step 7), the pathway summary table, the conditional Decomposition Strategy (Step 8, when APP-Q2 < 3), and the AI/Agent infrastructure evaluation logic (Step 9). Step 7 is authoritative over the Summary quick-reference table.

---

### Step 7: Evaluate AWS Modernization Pathways

After scoring all 37 questions in Steps 2–6, evaluate each of the 7 AWS Modernization Pathways. Each pathway has defined trigger conditions mapped to specific MOD question IDs and contextual guards that prevent false positives. Multiple pathways can be triggered simultaneously.

For each pathway, determine its status:

- **Triggered** — All trigger conditions are met AND the contextual guard does not prevent it.
- **Not Triggered** — One or more trigger conditions are not met, or the contextual guard prevents it.
- **Not Applicable** — The pathway is in the N/A pathway set for the detected `repo_type` (see N/A Pathway Mappings in the N/A Mapping section above).

#### 7.0 Check N/A Pathway Mappings

Before evaluating any pathway, check the `repo_type` against the N/A Pathway Mappings table. If a pathway is N/A for the detected repo_type, record it directly in the pathway summary table as:

| Field | Value |
|-------|-------|
| **Status** | Not Applicable |
| **Reason** | This is a `{repo_type}` repository. This pathway does not apply. |
| **Priority** | — |
| **Est. Effort** | — |

Do not evaluate trigger conditions for N/A pathways. Proceed to evaluate only the applicable pathways below.

#### 7.1 Move to Cloud Native

**Pathway:** Decompose monolith applications into loosely coupled distributed architectures using microservices, serverless, and event-driven patterns.

**Trigger Conditions:**

| Condition | Question ID | Threshold | Description |
|-----------|-------------|-----------|-------------|
| Primary | APP-Q2 | < 3 | Application is a monolith or tightly coupled — not yet decomposed into independently deployable services. |
| Supporting | INF-Q1 | < 3 | Compute is primarily EC2-based with limited managed container orchestration or serverless adoption. |
| Supporting | APP-Q3 | < 3 | Inter-service communication is primarily synchronous HTTP with limited async patterns. |
| Supporting | APP-Q4 | < 3 | Long-running operations are handled synchronously with no async job processing. |

**Trigger Logic:** Triggered when APP-Q2 < 3 (primary trigger) AND at least one supporting condition is also met (INF-Q1 < 3, APP-Q3 < 3, or APP-Q4 < 3).

**Contextual Guard:** None — if the application is a monolith with supporting infrastructure gaps, this pathway is relevant regardless of other factors. Note that with archetype calibration applied in Steps 3–4, APP-Q3 and APP-Q4 will not score below 3 purely because a service is synchronous-by-design (e.g., `stateless-utility`, `data-gateway`), so those supporting triggers naturally reflect genuine async-readiness gaps rather than archetype mismatches.

**Priority:** High — monolith decomposition is typically the highest-impact modernization initiative.
**Est. Effort:** High — decomposition requires architectural redesign, service boundary identification, data separation, and incremental migration.

**When Triggered, Include in Pathway Detail Section:**
- Current architecture state (monolith type, coupling level from APP-Q2 finding)
- Compute model gaps (from INF-Q1 finding)
- Communication pattern gaps (from APP-Q3, APP-Q4 findings)
- Recommended decomposition approach (link to Decomposition Strategy section if APP-Q2 < 3)
- Representative AWS services: Lambda, API Gateway, Step Functions, EventBridge, ECS/EKS
- Recommended patterns: Strangler Fig, Anti-corruption Layer, Event Sourcing, Saga
- Links to AWS prescriptive guidance for monolith decomposition

#### 7.2 Move to Containers

**Pathway:** Containerize existing workloads running on EC2/VMs and adopt fully managed container orchestration.

**Trigger Conditions:**

| Condition | Question ID | Threshold | Description |
|-----------|-------------|-----------|-------------|
| Primary | INF-Q1 | < 3 | Compute is primarily EC2/VM-based with no managed container orchestration or serverless. |
| Supporting | Discovery | No container definitions | No Dockerfile, docker-compose.yml, or Kubernetes manifests found during Step 1 discovery scan. |

**Trigger Logic:** Triggered when INF-Q1 < 3 AND no container definitions were found in the discovery scan.

**Contextual Guard:** This pathway SHALL NOT trigger if compute is already Lambda, Fargate, or ECS. Specifically:
- If INF-Q1 finding indicates compute is already running on ECS, EKS, Fargate, or Lambda, this pathway is **Not Triggered** even if INF-Q1 scores < 3 (e.g., a mix of managed and EC2 scoring a 2 would not trigger if the managed portion is already containerized).
- The guard prevents recommending containerization to workloads that have already moved beyond EC2/VM-based compute.

**Priority:** Medium — containerization is a foundational step that enables further modernization but is not as architecturally impactful as decomposition.
**Est. Effort:** Medium — requires creating Dockerfiles, container orchestration configs, and updating CI/CD pipelines, but does not require architectural redesign.

**When Triggered, Include in Pathway Detail Section:**
- Current compute model (from INF-Q1 finding — EC2 instance types, AMIs, auto-scaling groups)
- Container readiness indicators (application dependencies, port bindings, config externalization)
- Recommended container orchestration platform (respect `preferences` — e.g., if `prefer: ["eks"]`, recommend EKS; if `avoid: ["serverless"]`, do not recommend Fargate)
- Representative AWS services: ECS, EKS, Fargate, ECR, App Runner
- Migration approach: lift-and-containerize vs refactor-then-containerize
- Links to AWS container migration guidance

#### 7.3 Move to Open Source

**Pathway:** Migrate from commercial database engines and licensed software to open-source alternatives to reduce licensing costs and increase flexibility.

**Trigger Conditions:**

| Condition | Question ID | Threshold | Description |
|-----------|-------------|-----------|-------------|
| Primary | DATA-Q4 | < 3 | Application relies on stored procedures, triggers, or proprietary SQL constructs (T-SQL, PL/SQL) that couple business logic to a commercial database engine. |
| Supporting | INF-Q2 | Finding | INF-Q2 finding mentions commercial database engines — Oracle, SQL Server, or other licensed database products detected in IaC or connection strings. |

**Trigger Logic:** Triggered when DATA-Q4 < 3 AND commercial database engines are detected in the INF-Q2 finding or discovery scan.

**Contextual Guard:** None — if proprietary SQL and commercial engines are detected, migration to open source is relevant regardless of other factors.

**Priority:** Medium — licensing cost reduction is significant but migration complexity depends on stored procedure density and proprietary SQL usage.
**Est. Effort:** High — requires schema conversion (AWS SCT), stored procedure extraction to application layer, query rewriting, and thorough regression testing.

**When Triggered, Include in Pathway Detail Section:**
- Commercial engines detected (from INF-Q2 finding — Oracle, SQL Server, etc.)
- Stored procedure and proprietary SQL density (from DATA-Q4 finding)
- Database engine versions and EOL status (from DATA-Q3 finding)
- Recommended migration targets (respect `preferences` — e.g., if `prefer: ["aurora"]`, recommend Aurora PostgreSQL/MySQL)
- Representative AWS services: RDS PostgreSQL, RDS MySQL, RDS MariaDB, Aurora, Amazon Linux, EKS
- Migration tools: AWS Schema Conversion Tool (SCT), AWS Database Migration Service (DMS)
- Links to AWS database migration prescriptive guidance

#### 7.4 Move to Managed Databases

**Pathway:** Migrate from self-managed databases (on EC2, containers, or on-premises) to fully managed, purpose-built cloud-native database services.

**Trigger Conditions:**

| Condition | Question ID | Threshold | Description |
|-----------|-------------|-----------|-------------|
| Primary | INF-Q2 | < 3 | Databases are self-managed — running on EC2, in containers, or on-premises with manual patching, backup, and scaling. |
| Supporting | DATA-Q3 | < 3 | Database engine versions are unpinned, approaching EOL, or at EOL — indicating lack of lifecycle management. |

**Trigger Logic:** Triggered when INF-Q2 < 3 (self-managed databases detected). DATA-Q3 < 3 strengthens the case but is not required.

**Contextual Guard:** None — if databases are self-managed, migration to managed services is relevant regardless of other factors.

**Priority:** High — self-managed databases are a significant operational burden and a common source of incidents.
**Est. Effort:** Medium — managed database migration is well-tooled (DMS/SCT) but requires downtime planning, connection string updates, and validation.

**When Triggered, Include in Pathway Detail Section:**
- Current database topology (from INF-Q2 finding — self-managed engines, hosting model)
- Engine versions and EOL status (from DATA-Q3 finding)
- Data access patterns (from DATA-Q2 finding — centralized vs scattered)
- Recommended managed database targets (respect `preferences` — e.g., if `prefer: ["aurora"]`, recommend Aurora; if `avoid: ["dynamodb"]`, do not recommend DynamoDB)
- Representative AWS services: Aurora, RDS, DynamoDB, DocumentDB, ElastiCache, MemoryDB, OpenSearch Service
- Migration tools: AWS DMS, AWS SCT
- Links to AWS managed database migration guidance

#### 7.5 Move to Managed Analytics

**Pathway:** Migrate from self-managed streaming, ETL, and analytics infrastructure to fully managed, cost-optimized data lake and real-time analytics services.

**Trigger Conditions:**

| Condition | Question ID | Threshold | Description |
|-----------|-------------|-----------|-------------|
| Primary | INF-Q4 | < 3 | Messaging and streaming infrastructure is self-managed (Kafka on EC2, RabbitMQ in containers) or absent entirely. |
| Supporting | Discovery | Data source sprawl | Multiple data sources detected with no unified access layer (DATA-Q2 finding indicates scattered data access). |

**Trigger Logic:** Triggered when INF-Q4 < 3 AND evidence of data processing workloads exists in the discovery scan.

**Contextual Guard:** Evidence of data processing workloads MUST exist. This pathway SHALL NOT trigger if:
- No streaming, ETL, data pipeline, or analytics artifacts were found during discovery (Step 1).
- The application has no data processing responsibilities (e.g., a simple CRUD API with no analytics or streaming needs).
- The detected `service_archetype` is `stateless-utility` or `data-gateway` AND no streaming/ETL artifacts were found — these archetypes correctly score 4 on INF-Q4 when sync-only, and the low score does not indicate a modernization gap for them.

The guard prevents recommending managed analytics infrastructure to applications that do not process, transform, or analyze data at scale.

**Priority:** Medium — managed analytics reduces operational overhead for data-intensive workloads but is not relevant for all applications.
**Est. Effort:** Medium to High — depends on the complexity of existing streaming/ETL infrastructure and the volume of data pipelines to migrate.

**When Triggered, Include in Pathway Detail Section:**
- Current streaming/messaging infrastructure (from INF-Q4 finding — self-managed Kafka, RabbitMQ, etc.)
- Data access patterns and sprawl (from DATA-Q2 finding)
- Data processing workloads identified during discovery (ETL scripts, pipeline definitions, Glue jobs, Airflow DAGs)
- Recommended managed analytics targets (respect `preferences`)
- Representative AWS services: Redshift, Kinesis Data Streams, MSK Serverless, Athena, Lake Formation, Glue, QuickSight
- Links to AWS analytics modernization guidance

#### 7.6 Move to Modern DevOps

**Pathway:** Adopt modern development philosophies, practices, and tools for high-velocity, safe, and automated application delivery.

**Trigger Conditions:**

| Condition | Question ID | Threshold | Description |
|-----------|-------------|-----------|-------------|
| Primary | INF-Q10 | < 3 | Low IaC coverage — significant infrastructure is manually created (ClickOps). |
| Primary | INF-Q11 | < 3 | No CI/CD automation — deployments are manual or semi-manual. |
| Supporting | OPS-Q5 | < 3 | No canary or blue/green deployment strategy — direct-to-production releases. |
| Supporting | OPS-Q6 | < 3 | No integration tests in the CI pipeline. |

**Trigger Logic:** Triggered when at least one primary condition is met (INF-Q10 < 3 OR INF-Q11 < 3). Supporting conditions (OPS-Q5 < 3, OPS-Q6 < 3) strengthen the case and expand the scope of recommendations.

**Contextual Guard:** None — if IaC coverage or CI/CD automation is lacking, modern DevOps practices are universally relevant.

**Priority:** High — DevOps maturity is foundational to all other modernization pathways. Without automated pipelines and IaC, other modernization efforts are harder to execute safely.
**Est. Effort:** Medium — IaC adoption and CI/CD pipeline creation are well-understood practices with extensive tooling and guidance.

**When Triggered, Include in Pathway Detail Section:**
- Current IaC coverage (from INF-Q10 finding — percentage of infrastructure in code vs manual)
- Current CI/CD state (from INF-Q11 finding — pipeline stages, automation level)
- Deployment strategy gaps (from OPS-Q5 finding)
- Testing gaps (from OPS-Q6 finding)
- Recommended DevOps toolchain (respect `preferences`)
- Representative AWS services: CodeCommit, CodeBuild, CodePipeline, CodeDeploy, CloudFormation, CDK, Proton, X-Ray, CloudWatch
- Links to AWS DevOps prescriptive guidance

#### 7.7 Move to AI

**Pathway:** Leverage AWS AI services to transform applications with AI capabilities, bridging traditional modernization and AI-driven computing. This pathway evaluates whether the application has adopted AI/agent frameworks, vector databases, RAG patterns, or agent evaluation infrastructure.

**Trigger Conditions:**

| Condition | Source | Description |
|-----------|--------|-------------|
| Primary | Discovery (Step 1) | No AI/agent framework usage detected — no imports of Bedrock SDK, LangChain, Strands, OpenAI, Spring AI, HuggingFace, or SageMaker SDK in source code. |
| Supporting | Discovery (Step 1) | No vector database or embeddings infrastructure detected — no OpenSearch with vector engine, Pinecone, pgvector, Weaviate, or Qdrant. |
| Supporting | Discovery (Step 1) | No RAG implementation detected — no embedding generation, vector store queries, or retrieval chain patterns. |
| Supporting | Discovery (Step 1) | No agent evaluation framework detected — no Ragas, DeepEval, or custom eval harness. |

**Trigger Logic:** Triggered when the primary condition is met (no AI/agent frameworks detected). Supporting conditions strengthen the case and expand the scope of recommendations.

**Contextual Guard:** Requires explicit AI/agent/LLM intent in the portfolio or service context. Before evaluating primary trigger conditions, scan both the portfolio-level `context` and the service-level `context` (from `additionalPlanContext`) for AI-related signal terms.

**AI-Related Signal Terms (case-insensitive, whole-word match):**
"agentic", "LLM", "machine learning", "Bedrock", "generative AI", "GenAI", "RAG", "vector database", "vector store", "embedding", "copilot", "chatbot", "AI agent", "AI-powered", "large language model"

> **Note:** Generic terms like "AI", "agent", "ML", "assistant", and "autonomous" are excluded because they produce false matches in non-AI contexts (e.g., "autonomous scaling", "ML pipeline for fraud detection", "agent identity", "virtual assistant" for IVR). The retained terms are specific enough to indicate LLM/GenAI intent.

**Guard Logic:**

```
ai_signals = ["agentic", "LLM", "machine learning", "Bedrock", "generative AI", 
              "GenAI", "RAG", "vector database", "vector store", "embedding",
              "copilot", "chatbot", "AI agent", "AI-powered", "large language model"]

portfolio_context = additionalPlanContext.context  # portfolio-level
service_context = additionalPlanContext.context     # service-level (from repo config)

has_ai_intent = false
for signal in ai_signals:
    if signal in portfolio_context (case-insensitive) OR signal in service_context (case-insensitive):
        has_ai_intent = true
        break

if not has_ai_intent:
    pathway_status = "Not Triggered"
    reason = "No AI/agent intent detected in portfolio or service context."
else:
    # Proceed with primary trigger evaluation (no AI frameworks detected)
    evaluate_primary_triggers()
```

If neither the portfolio-level context nor the service-level context contains any of the AI-related signal terms, the pathway status is set to **Not Triggered** with reason: "No AI/agent intent detected in portfolio or service context." The primary trigger conditions are not evaluated. When at least one context string contains an AI-related signal and the primary trigger conditions are met, the pathway status is set to **Triggered**.

**Priority:** Medium — AI adoption is increasingly important but depends on the application's domain and use cases.
**Est. Effort:** Medium — initial AI integration (e.g., adding Bedrock for a single use case) is moderate effort, but building comprehensive AI infrastructure (vector DBs, RAG, eval frameworks) requires more investment.

**When Triggered, Include in Pathway Detail Section:**
- Current AI/agent infrastructure state (from discovery — what was and was not found)
- Application domain and potential AI use cases based on analysis findings
- Recommended AI services (respect `preferences`)
- Representative AWS services: Amazon Bedrock, Amazon Bedrock AgentCore, Amazon Q, SageMaker, OpenSearch Service (vector engine), Amazon Kendra
- Foundation requirements: what needs to be in place before AI integration (API surface, data access, observability)
- Links to AWS AI/ML prescriptive guidance

---

### Pathway Summary Table

After evaluating all 7 pathways, compile the results into a summary table. All 7 pathways MUST appear in this table regardless of status. This table appears in the report output before the pathway detail subsections.

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | {Triggered / Not Triggered / Not Applicable} | {High / Medium / Low / —} | {High / Medium / Low / —} | {Question IDs and scores that triggered it, or reason for Not Triggered / Not Applicable} |
| 2 | Move to Containers | {Triggered / Not Triggered / Not Applicable} | {High / Medium / Low / —} | {High / Medium / Low / —} | {Question IDs and scores that triggered it, or reason for Not Triggered / Not Applicable} |
| 3 | Move to Open Source | {Triggered / Not Triggered / Not Applicable} | {High / Medium / Low / —} | {High / Medium / Low / —} | {Question IDs and scores that triggered it, or reason for Not Triggered / Not Applicable} |
| 4 | Move to Managed Databases | {Triggered / Not Triggered / Not Applicable} | {High / Medium / Low / —} | {High / Medium / Low / —} | {Question IDs and scores that triggered it, or reason for Not Triggered / Not Applicable} |
| 5 | Move to Managed Analytics | {Triggered / Not Triggered / Not Applicable} | {High / Medium / Low / —} | {High / Medium / Low / —} | {Question IDs and scores that triggered it, or reason for Not Triggered / Not Applicable} |
| 6 | Move to Modern DevOps | {Triggered / Not Triggered / Not Applicable} | {High / Medium / Low / —} | {High / Medium / Low / —} | {Question IDs and scores that triggered it, or reason for Not Triggered / Not Applicable} |
| 7 | Move to AI | {Triggered / Not Triggered / Not Applicable} | {High / Medium / Low / —} | {High / Medium / Low / —} | {Question IDs and scores that triggered it, or reason for Not Triggered / Not Applicable} |

**Status values:**
- **Triggered** — All trigger conditions met and contextual guard does not prevent it. Include priority, effort, and key trigger criteria.
- **Not Triggered** — One or more trigger conditions not met, or contextual guard prevents it. Set priority and effort to "—". Key trigger criteria should explain why it was not triggered (e.g., "INF-Q1 = 4 — compute already on managed services").
- **Not Applicable** — Pathway is N/A for the detected `repo_type`. Set priority and effort to "—". Key trigger criteria should state: "This is a `{repo_type}` repository. This pathway does not apply."

**Pathway Detail Subsections:**
After the summary table, include a detailed subsection for each **Triggered** pathway only. Each detail subsection should contain the content specified in the "When Triggered, Include in Pathway Detail Section" guidance for that pathway above. Do not include detail subsections for Not Triggered or Not Applicable pathways.


### Step 8: Decomposition Strategy (Conditional — APP-Q2 < 3)

This section is **conditional**. Include it in the report ONLY when APP-Q2 (Monolith vs Microservices) scores less than 3. If APP-Q2 >= 3, skip this section entirely — the application is already decomposed or has well-defined module boundaries, and decomposition guidance is not needed.

When APP-Q2 < 3, the application is a monolith or tightly coupled system that would benefit from decomposition. This section provides concrete approach options, pattern recommendations, and effort estimates to guide the modernization strategy.

#### 8.1 Decomposition Approach Options

Evaluate the monolith's characteristics (from APP-Q2 finding, DATA-Q2 finding, and discovery evidence) and recommend one of the following approaches:

| Approach | Description | When to Use | Level of Effort | Recommendation |
|----------|-------------|-------------|-----------------|----------------|
| **Strengthen as Modular Monolith** | Keep the application as a single deployable unit but enforce strict module boundaries: separate schemas per module, explicit inter-module APIs (no direct cross-module database access), clear ownership per module. | APP-Q2 = 2 and the team is < 3-4 squads, deployment cadence is acceptable, and the primary driver is code quality rather than independent scaling or team autonomy. | **Low** — 2-6 months of internal refactoring. No new infrastructure or deployment topology changes. | ✅ **Recommended when decomposition drivers are weak.** Not every monolith needs microservices. If the team is small, deployment frequency is adequate, and the primary issue is code coupling rather than operational independence, strengthening module boundaries is the correct outcome — not a stepping stone. |
| **Strangler Fig (Parallel Track)** | Incrementally extract services from the monolith while keeping the monolith running. New features are built as services; existing features are migrated over time. The monolith shrinks as services grow. | APP-Q2 = 2 (identifiable modules with coupling). The monolith has recognizable boundaries that can be extracted one at a time. Team can sustain parallel development. Strong drivers for decomposition exist (independent scaling, team autonomy, deployment independence). | **Medium to High** — 6-18 months depending on monolith size. Each extraction is a bounded effort. | ✅ **Recommended for most monoliths where decomposition is warranted.** Lowest risk, incremental value delivery, no big-bang cutover. |
| **Conditional / Adaptive** | Start with containerizing the monolith as-is (lift-and-containerize), then selectively extract high-value services based on business priority. Not all modules need to become services — some may remain in the monolith permanently. | APP-Q2 = 2 and the team has limited capacity for full decomposition. Business pressure requires quick wins before full architectural change. | **Low to Medium** — containerization in 2-4 weeks, selective extraction over 3-12 months. | ✅ **Recommended when capacity is constrained** or when only specific modules need independent scaling/deployment. |
| **Big-Bang Rewrite** | Rewrite the entire application as microservices from scratch, replacing the monolith in a single cutover. | Almost never. Only when the monolith is so degraded (APP-Q2 = 1, no identifiable modules, pervasive shared state) that incremental extraction is impossible. | **Very High** — 12-24+ months. High risk of scope creep, feature parity gaps, and failed cutover. | ⚠️ **Recommended against.** High risk of failure. If the monolith is functional, Strangler Fig or Conditional approaches are safer. Only consider if the monolith is truly unmaintainable. |

#### 8.2 Pattern Recommendations

When decomposing a monolith, apply these architectural patterns to manage the transition safely. Each pattern is linked to AWS prescriptive guidance:

| Pattern | Purpose | When to Apply | AWS Prescriptive Guidance |
|---------|---------|---------------|---------------------------|
| **Anti-corruption Layer (ACL)** | Isolate the new service from the monolith's data model and API contracts. Prevents the monolith's design decisions from leaking into new services. | Every extraction — place an ACL between the new service and the monolith to translate between their models. | [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) |
| **Saga Pattern** | Manage distributed transactions across services that were previously handled by a single database transaction in the monolith. | When extracting modules that participate in multi-step business transactions (e.g., order → payment → inventory). | [Saga pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html) |
| **Event Sourcing** | Capture all changes as a sequence of events rather than storing only current state. Enables audit trails, temporal queries, and event-driven integration between services. | When the extracted service needs to maintain a history of state changes, or when multiple services need to react to the same business events. | [Event sourcing pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html) |
| **Hexagonal Architecture (Ports and Adapters)** | Structure each new service with clear boundaries between business logic (core), external interfaces (ports), and infrastructure adapters. | Every new service — ensures the service is testable, portable, and decoupled from specific infrastructure choices. | [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |

#### 8.3 Effort Estimation Factors

The actual decomposition effort depends on these factors discovered during the analysis:

| Factor | Low Effort Signal | High Effort Signal | Source |
|--------|-------------------|-------------------|--------|
| Module boundaries | Clear package/module structure with minimal cross-dependencies | No clear boundaries, circular dependencies, pervasive shared state | APP-Q2 finding |
| Data coupling | Each module owns its data; minimal shared database tables | Single shared database with cross-module joins and shared mutable state | DATA-Q2 finding |
| Stored procedures | No stored procedures; all logic in application layer | Heavy stored procedure usage coupling logic to the database | DATA-Q4 finding |
| Communication patterns | Some async patterns already in place | All communication is synchronous HTTP | APP-Q3 finding |
| CI/CD maturity | Automated pipeline exists; can support multi-service deployment | Manual deployments; no pipeline to extend | INF-Q11 finding |
| Test coverage | Integration tests exist for critical workflows | No automated tests — regression risk during extraction | OPS-Q6 finding |

Use these factors to calibrate the effort estimate for the recommended approach. Include the calibrated estimate in the report.


### Step 9: AI/Agent Infrastructure Evaluation Logic

This section documents the evaluation logic that connects AI/agent discovery findings (from Step 1) to the Move to AI pathway (Step 7.7). The actual discovery scanning is performed in Step 1, and the Move to AI pathway evaluation is in Step 7.7. This section serves as a cross-reference explaining how AI/agent infrastructure signals flow through the analysis.

#### 9.1 AI/Agent Discovery Signals

During the discovery scan (Step 1), the following AI/agent infrastructure signals are identified and recorded in the file inventory:

| Signal Category | What to Look For | Discovery Evidence |
|-----------------|------------------|-------------------|
| **AI/Agent Frameworks** | Bedrock SDK imports, LangChain imports, Strands SDK imports, OpenAI SDK imports, Spring AI imports, HuggingFace imports, SageMaker SDK imports | Import statements in source code; framework dependencies in package manifests (e.g., `boto3` with `bedrock-runtime`, `langchain` in requirements.txt, `@aws-sdk/client-bedrock-runtime` in package.json, `spring-ai` in pom.xml) |
| **Vector Database Infrastructure** | OpenSearch with vector engine (`knn` plugin), Pinecone client imports, pgvector extension in PostgreSQL config, Weaviate client imports, Qdrant client imports | IaC resources for vector-capable databases; client library imports in source code; database configuration enabling vector extensions |
| **RAG Implementation** | Embedding generation calls, vector store query patterns, retrieval chain implementations, document chunking logic | Source code patterns: embedding API calls, similarity search queries, retrieval-augmented generation chains, document loaders and splitters |
| **Agent Evaluation Frameworks** | Ragas imports, DeepEval imports, custom evaluation harness patterns, LLM-as-judge implementations | Test files with evaluation framework imports; evaluation configuration files; benchmark datasets |

#### 9.2 How Discovery Signals Feed the Move to AI Pathway

The AI/agent discovery signals recorded in Step 1 are consumed by Step 7.7:

- The Move to AI pathway's primary trigger condition checks whether AI/agent frameworks were found during discovery.
- If **no** AI/agent framework imports are detected, the primary trigger is met.
- Supporting conditions check for absence of vector DB infrastructure, RAG implementation, and agent evaluation frameworks.
- The pathway is triggered when the primary condition is met (no AI/agent frameworks), regardless of supporting conditions.
- See Step 7.7 for the complete trigger logic and contextual guard.

The discovery scan (Step 1) is the single source of truth for what AI/agent artifacts exist. The Move to AI pathway (Step 7.7) consumes those findings through its trigger evaluation logic.

**Scope note:** The modernization analysis does NOT recommend specific agent use cases for the target system. That concern — where agents can add value to this system, given its foundations — belongs to the Agentic Readiness Analysis (ARA) and its downstream agentic-program recommendations. MOD's role is to identify modernization gaps; ARA's role is to identify agent integration opportunities.



