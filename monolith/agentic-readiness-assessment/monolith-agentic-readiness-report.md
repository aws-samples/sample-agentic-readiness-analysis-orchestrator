# Agentic Readiness Assessment Report
**Target**: ./monolith
**Date**: 2026-03-06
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment

---

## Table of Contents

1. Executive Summary
2. Top Priorities (Critical Gaps)
3. Readiness Roadmap
   - Phase 1 — Quick Wins (Days 1–30)
   - Phase 2 — Foundation (Months 1–3)
   - Phase 3 — Agent Enablement (Months 3–6)
4. Recommended Modernization Pathways
5. Recommended Self-Paced Learning Materials
6. Detailed Findings
   - Infrastructure & Platform
   - Application Architecture
   - Data Foundations
   - Identity, Security & Governance
   - Operations & Observability
7. Appendix: Evidence Index

---

## Executive Summary

This is a PHP monolithic e-commerce application with **all business logic contained in a single `index.php` file (~2,000+ lines)**, serving orders, inventory, payments, returns, user management, warehouse operations, shipping, and quality control domains. The application is far from agentic readiness. Its strongest area is **Data Foundations** (1.7/4.0), benefiting from a single MySQL data source with no stored procedures — providing a clean migration path. Its weakest areas are **Operations & Observability** (1.0/4.0) with zero monitoring, testing, or deployment automation, and **Application Architecture** (1.2/4.0) with a tightly-coupled monolith, no API documentation, no async patterns, and no resilience mechanisms. Significant foundational work — containerization to EKS, CI/CD pipelines, service decomposition, and observability — must be completed before any agentic capabilities can be safely introduced.

### Overall Score: 1.5 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 2.1 / 4.0 | 🟠 |
| Application Architecture | 1.2 / 4.0 | ❌ |
| Data Foundations | 1.7 / 4.0 | 🟠 |
| Identity, Security & Governance | 1.4 / 4.0 | ❌ |
| Operations & Observability | 1.0 / 4.0 | ❌ |

---

## Top Priorities (Critical Gaps)

### 1. 🔴 Tightly-Coupled Monolith with No Service Boundaries (APP-Q4: 1/4)
**What**: The entire application — orders, inventory, payments, returns, users, warehouses, shipping, and quality control — exists in a single `index.php` file with shared database tables, foreign keys across domains, and inline HTML/CSS/JS. There are no module boundaries, no separation of concerns, and no independent deployability.
**Why it matters for agentic workloads**: Agents need well-defined API boundaries to act as tools. A monolith provides no clear tool boundaries, no failure isolation, and no ability to assign agent capabilities to specific domains. An agent acting on the order domain could inadvertently corrupt inventory or payment data due to tight coupling.
**First step**: Conduct a domain-modeling workshop (EventStorming) to identify bounded contexts. Map the 9 database tables to candidate services: Inventory, Orders, Payments, Returns, Users, and Warehouse/Fulfillment. Begin containerizing the monolith as-is for EKS deployment while planning Strangler Fig extraction.

### 2. 🔴 No CI/CD Pipeline or Deployment Automation (INF-Q6: 1/4, OPS-Q9: 1/4)
**What**: Deployment is a manual `deploy.sh` script that runs `docker-compose build` and `docker-compose up -d` locally. There are no GitHub Actions, no CodePipeline, no CodeBuild, no buildspec.yml, no Jenkinsfile, and no automated test/build/deploy stages.
**Why it matters for agentic workloads**: Agents will require frequent prompt tuning, model updates, and configuration changes. Without CI/CD, every change requires manual intervention, creating a bottleneck that prevents the rapid iteration agentic systems demand. Automated rollback — critical when an agent starts misbehaving — is impossible without deployment automation.
**First step**: Create a CodePipeline with CodeBuild for automated Docker image builds, push to ECR (already provisioned in CloudFormation), and deploy to EKS. Add at minimum a lint and smoke test stage.

### 3. 🔴 Zero Observability — No Tracing, Structured Logging, or Monitoring (OPS-Q1: 1/4, OPS-Q2: 1/4, OPS-Q8: 1/4)
**What**: The application has no distributed tracing (no X-Ray, no OpenTelemetry), no structured logging (PHP uses basic `error_reporting`/`ini_set`), no CloudWatch alarms, no anomaly detection, no correlation IDs, and no custom metrics. The only monitoring is an App Runner health check.
**Why it matters for agentic workloads**: Agents can silently degrade — hallucinating, looping, or failing without visible symptoms. Without observability, you cannot detect when an agent is misbehaving, reconstruct what it did, or measure its effectiveness. Agentic systems generate significantly more telemetry than traditional applications, and the infrastructure to handle this must be in place before agents are deployed.
**First step**: Add structured JSON logging with correlation IDs to the PHP application using a library like Monolog. Deploy OpenTelemetry Collector as a sidecar in EKS and instrument the application for distributed tracing.

### 4. 🔴 No Async Messaging or Event-Driven Patterns (INF-Q4: 1/4, APP-Q3: 1/4)
**What**: All inter-process communication is synchronous HTTP with direct database queries. There is no SQS, SNS, EventBridge, or any messaging infrastructure. The order fulfillment workflow (confirmed → validated → warehouse_assigned → picking → packed → quality_checked → shipped → delivered) is executed through sequential synchronous API calls.
**Why it matters for agentic workloads**: Agents orchestrate multi-step workflows that must be resilient to failures and support long-running operations. Without async messaging, agent workflows will be fragile — a single failure in the fulfillment chain breaks the entire flow with no retry mechanism. Event-driven architecture enables agents to react to state changes, enabling autonomous decision-making.
**First step**: Introduce Amazon SQS for the order fulfillment workflow. Start with the order-confirmed event triggering validation asynchronously, then extend to warehouse assignment and shipping.

### 5. 🔴 No API Documentation or OpenAPI Specs (APP-Q2: 1/4)
**What**: API routes are defined inline in `index.php` using regex pattern matching (e.g., `preg_match('#^/api/orders/([^/]+)/validate$#', ...)`). There is no OpenAPI specification, no Swagger documentation, no API catalog, and no machine-readable API description.
**Why it matters for agentic workloads**: Agents discover and invoke tools through API specifications. Without OpenAPI specs, agents cannot understand what endpoints exist, what parameters they accept, or what responses they return. This is the most fundamental prerequisite for agent tool integration — agents literally cannot work without machine-readable API descriptions.
**First step**: Generate an OpenAPI 3.0 specification documenting all existing `/api/*` endpoints, their request/response schemas, and authentication requirements. Use this as the foundation for agent tool definitions.

## Readiness Roadmap

> **Note**: This roadmap follows an **aggressive modernization** approach per project requirements, with EKS as the target container orchestration platform. Cross-dependencies between phases are explicitly stated.

### Microservices Decomposition Strategy

The application scores **1/4 on APP-Q4** — a tightly-coupled monolith with all business logic in a single file (`index.php`), a shared MySQL database with foreign keys across domains, and no module boundaries. Decomposition is essential for agentic readiness.

**Domain Analysis — Candidate Services:**

| Domain | Tables | Coupling Level | Extraction Priority |
|--------|--------|---------------|-------------------|
| Inventory | `inventory` | Low — read-heavy, minimal writes | ⭐ First candidate |
| Orders | `orders`, `order_items`, `order_status_history` | High — FK to inventory, payments, returns | Second candidate |
| Payments | `payments` | Medium — FK to orders | Third candidate |
| Returns | `returns` | Medium — FK to orders, touches inventory | Fourth candidate |
| Users | `users` | Low — auth only, no FK to business tables | Can extract early |
| Warehouses/Fulfillment | `warehouses`, `interactions` | Medium — references orders, inventory | Later extraction |

**Recommended Approach: Parallel Track (Option B)**
- **LoE**: Medium | **Risk**: Low-Medium | **Time to Value**: Fast
- **Strategy**: Modernize infrastructure (EKS deployment, CI/CD, observability) while incrementally extracting services
- **Pattern**: [Strangler Fig](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) + [API Gateway Routing](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/api-routing.html)
- **Starting Point**: Extract the **Inventory Service** first — it has the clearest domain boundary, is primarily read-heavy (`GET /api/products`), has a single table with no outbound foreign keys, and can be independently scaled. Deploy behind an ALB with path-based routing (`/api/products` → Inventory Service, all other routes → Monolith).
- **When to Use**: Most scenarios, especially when business value delivery cannot wait for complete decomposition

**Alternative: Conditional/Adaptive (Option C)**
- **LoE**: Varies by module | **Risk**: Low | **Time to Value**: Fastest
- **Strategy**: Assess each module independently; containerize the monolith as-is on EKS first, then extract loosely-coupled domains while deferring tightly-coupled ones
- **Pattern**: [Hexagonal Architecture](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/hexagonal-architecture.html) + [Anti-corruption Layer](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/anti-corruption-layer.html)
- **Starting Point**: Deploy monolith on EKS as a single pod, extract Inventory and Users (low coupling) first, defer Orders/Payments/Returns (high coupling) for Phase 3
- **When to Use**: If team bandwidth is limited or risk tolerance is low

**Not Recommended: Big-Bang Decomposition (Option A)**
- **LoE**: Very High | **Risk**: High | **Time to Value**: Slow
- **Strategy**: Decompose entire monolith before any modernization
- **Only Consider If**: Complete rewrite is already planned, funded, and business-approved; existing system is being sunset

**Pattern Recommendations Based on Your Architecture:**

- **Incremental Extraction**: Start with [Strangler Fig](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) + [API Gateway Routing Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/api-routing.html) (path-based routing via ALB). The ALB provides routing, throttling context, and auth without requiring service mesh infrastructure upfront. This is the recommended starting pattern given no existing service discovery (APP-Q12 score 1).

- **Data Consistency**: Implement [Anti-corruption Layer](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/anti-corruption-layer.html) + [Transactional Outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html) before extracting Orders or Payments. Without idempotency (APP-Q7 score 1), service extraction risks data inconsistency — these patterns provide safety during transition.

- **Resilience First**: Implement [Circuit Breaker](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/circuit-breaker.html) + [Retry with Backoff](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/retry-backoff.html) before decomposition. Currently no resilience patterns exist (APP-Q9 score 1). Microservices amplify failure modes — resilience patterns must be in place before increasing system distribution.

- **Distributed Transactions**: Use [Saga Orchestration](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-orchestration.html) via AWS Step Functions for the order fulfillment workflow once extracted. The current synchronous 8-step fulfillment flow (confirmed → delivered) is a natural candidate for saga orchestration.

### Phase 1 — Quick Wins (Days 1–30)

1. **Create OpenAPI 3.0 specification** for all existing `/api/*` endpoints — document request/response schemas, authentication requirements, and status codes. This is the foundation for agent tool definitions.
2. **Set up CI/CD pipeline** using AWS CodePipeline + CodeBuild: automate Docker build → push to ECR → deploy to EKS. Replace the manual `deploy.sh` script.
3. **Migrate secrets to AWS Secrets Manager** — remove hardcoded credentials from `docker-compose.yml` (MYSQL_ROOT_PASSWORD, MYSQL_USER, MYSQL_PASSWORD) and `index.php` fallback defaults. Update CloudFormation to reference Secrets Manager instead of parameter defaults.
4. **Add structured JSON logging** with correlation IDs using Monolog or similar PHP logging library. Configure CloudWatch Logs agent for log aggregation.
5. **Conduct domain-modeling workshop** (EventStorming) to identify bounded contexts and map service extraction candidates. Document current module dependencies and data coupling.
6. **Prepare EKS cluster IaC** — create Terraform or CloudFormation templates for EKS cluster, node groups, ALB Ingress Controller, and ECR integration.

### Phase 2 — Foundation (Months 1–3)

**Prerequisite**: Phase 1 CI/CD pipeline and EKS cluster IaC must be complete.

1. **Deploy monolith to EKS** — containerize as-is using existing Dockerfile, deploy behind ALB with health checks. Migrate from App Runner to EKS per user preference. This establishes the container orchestration foundation.
2. **Extract first service (Inventory)** using Strangler Fig pattern — create a dedicated Inventory Service (Python or TypeScript for better agent ecosystem), deploy as separate EKS pod, route `/api/products` via ALB path-based routing to the new service.
3. **Introduce Amazon SQS** for async order fulfillment events — start with order-confirmed → validation trigger. Add dead-letter queues for resilience.
4. **Implement distributed tracing** with AWS X-Ray or OpenTelemetry — instrument both the monolith and extracted services. Deploy OpenTelemetry Collector as EKS DaemonSet.
5. **Add integration tests** for critical workflows (order creation, fulfillment, returns) — integrate into CI/CD pipeline. Use PHPUnit for the monolith, appropriate frameworks for extracted services.
6. **Implement rate limiting** at the ALB/API layer — configure request throttling, per-client quotas.
7. **Set up CloudWatch alarms** for error rates, latency p99, and availability SLOs on critical endpoints.

### Phase 3 — Agent Enablement (Months 3–6)

**Prerequisite**: EKS deployment, first service extraction, CI/CD, and observability from Phase 2 must be operational.

1. **Continue service extraction** — extract Orders and Payments services using Strangler Fig + Saga Orchestration patterns. Implement Transactional Outbox for data consistency.
2. **Deploy Amazon OpenSearch Service** with k-NN plugin as managed vector database for product catalog semantic search and customer interaction history.
3. **Implement RAG pipeline** — set up Amazon Bedrock Knowledge Bases for document chunking, embedding generation, and semantic search across order history and product catalog.
4. **Integrate Amazon Bedrock agents** — create fulfillment automation agent using extracted service APIs as tools (via OpenAPI specs from Phase 1). Start with order validation and warehouse assignment automation.
5. **Add agent evaluation framework** — create golden datasets for fulfillment decisions, implement automated scoring, set up LLM-as-judge for agent response quality.
6. **Implement LLM cost tracking** — add per-request token usage tracking with CloudWatch custom metrics, user/workflow attribution, and tiered retention policies for agent telemetry.
7. **Deploy human-in-the-loop workflows** — implement Step Functions with approval tasks for high-risk agent actions (refund processing, bulk inventory changes).

## Recommended Modernization Pathways

Based on the assessment findings, the following AWS Modernization Pathways are recommended for this application. Multiple pathways can execute in parallel because modern applications comprise multiple interconnected components — each requiring its own modernization approach.

### Pathway Summary

| Pathway | Triggered | Priority | Key Trigger Criteria | Est. Effort |
|---------|-----------|----------|---------------------|-------------|
| Move to Cloud Native | Yes | High | APP-Q4: 1/4, APP-Q3: 1/4, APP-Q10: 1/4 | High |
| Move to Containers | Yes | High | INF-Q1 < 3 (local dev), APP-Q4: 1/4 | Medium |
| Move to Open Source | No | N/A | Already using MySQL open source | N/A |
| Move to Managed Databases | Yes | Medium | DATA-Q2: 1/4 (no vector DB) | Medium |
| Move to Managed Analytics | Yes | Low | INF-Q8: 1/4 (no streaming) | Low |
| Move to Modern DevOps | Yes | High | INF-Q6: 1/4, OPS-Q9: 1/4, OPS-Q10: 1/4, OPS-Q1: 1/4 | High |
| Move to AI | Yes | High | APP-Q13: 1/4, DATA-Q1: 1/4, DATA-Q3: 1/4, OPS-Q3: 1/4 | High |

### Parallel Execution Plan

**Parallel Track 1**: Move to Containers + Move to Modern DevOps (no dependencies — containerize the app while building CI/CD pipelines simultaneously)
**Parallel Track 2**: Move to Managed Databases (can begin vector DB planning while containers and DevOps tracks progress)
**Sequential Dependencies**:
- Move to Cloud Native depends on Move to Containers (must containerize before decomposing to microservices on EKS)
- Move to AI depends on Move to Cloud Native (need service boundaries/APIs before building agent tools) and Move to Managed Databases (need vector DB for RAG)
- Move to Managed Analytics depends on Move to Cloud Native (need event-driven architecture before streaming analytics)

### Move to Containers

- **Priority**: High
- **Trigger Criteria Met**:
  - INF-Q1: Score 3/4 — App Runner in CloudFormation but local dev uses raw Docker Compose. User preference is EKS.
  - APP-Q4: Score 1/4 — Monolith needing containerization as the first step toward decomposition.
- **Current State**: Dockerfile exists for PHP 8.2 Apache. Docker Compose used for local development. CloudFormation deploys to App Runner (not the preferred EKS target). ECR repository already provisioned.
- **Target State**: Application deployed on Amazon EKS with Fargate or managed node groups, behind an ALB, with ECR for image storage. Container orchestration enables independent scaling and zero-downtime deployments.
- **Key Activities**:
  1. Create EKS cluster IaC (Terraform/CloudFormation) with ALB Ingress Controller
  2. Adapt existing Dockerfile for EKS deployment (add health check endpoints, graceful shutdown)
  3. Create Kubernetes manifests (Deployment, Service, Ingress) for the monolith
  4. Deploy behind ALB with path-based routing to support future service extraction
- **Dependencies**: None — can start immediately
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 1 (EKS IaC prep), Phase 2 (deployment)
- **Relevant Learning Materials**: Module 3 — Move to Containers with Amazon ECS and EKS

### Move to Cloud Native

- **Priority**: High
- **Trigger Criteria Met**:
  - APP-Q4: Score 1/4 — Tightly-coupled monolith with no service boundaries
  - APP-Q3: Score 1/4 — 100% synchronous communication, no async patterns
  - APP-Q10: Score 1/4 — No async handling for long-running operations
- **Current State**: Single PHP monolith with all domains in one file. All communication is synchronous HTTP. The 8-step fulfillment workflow is hardcoded as sequential API calls.
- **Target State**: Microservices architecture on EKS with event-driven communication via SQS/EventBridge. Per user preference, EKS-based containerized microservices (not Lambda/serverless). Step Functions for workflow orchestration.
- **Key Activities**:
  1. Extract Inventory Service as first microservice (Strangler Fig pattern)
  2. Introduce SQS for async order fulfillment events
  3. Implement Step Functions for the fulfillment workflow orchestration
  4. Extract Orders, Payments, and Returns services incrementally
  5. Implement EventBridge for cross-service event communication
- **Dependencies**: Move to Containers must complete first (EKS cluster required)
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 2 (first extraction), Phase 3 (continued decomposition)
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native (Containers and Serverless)

### Move to Managed Databases

- **Priority**: Medium
- **Trigger Criteria Met**:
  - DATA-Q2: Score 1/4 — No vector database for AI/semantic search capabilities
  - DATA-Q10: Score 3/4 — Dev/prod version mismatch (MySQL 8.0 in Docker vs 8.4.8 in RDS)
- **Current State**: RDS MySQL 8.4.8 in production (managed). No vector database. Docker Compose uses self-managed MySQL 8.0 for local development.
- **Target State**: RDS MySQL retained for transactional data. Amazon OpenSearch Service with k-NN plugin added for vector search. Dev environment aligned with production versions.
- **Key Activities**:
  1. Align Docker Compose MySQL version with RDS production version
  2. Deploy Amazon OpenSearch Service with k-NN plugin for vector search
  3. Configure Aurora PostgreSQL with pgvector as an alternative vector store (evaluate vs OpenSearch)
  4. Migrate per-service databases as microservices are extracted (database-per-service pattern)
- **Dependencies**: None for vector DB deployment; database-per-service depends on Move to Cloud Native
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 2 (version alignment), Phase 3 (vector DB deployment)
- **Relevant Learning Materials**: Module 4 — Move to Managed Databases

### Move to Managed Analytics

- **Priority**: Low
- **Trigger Criteria Met**:
  - INF-Q8: Score 1/4 — No managed streaming service (no Kinesis, no MSK)
- **Current State**: No streaming infrastructure. No real-time analytics. All data access is synchronous database queries.
- **Target State**: Amazon Kinesis Data Streams for real-time order and fulfillment event streaming. Athena for ad-hoc analytics on order history stored in S3.
- **Key Activities**:
  1. Implement Kinesis Data Streams for order events after SQS is in place
  2. Set up S3 data lake for historical order and fulfillment analytics
  3. Configure Athena for ad-hoc querying of fulfillment performance data
- **Dependencies**: Move to Cloud Native (need event-driven architecture first)
- **Estimated Effort**: Low
- **Roadmap Phase Alignment**: Phase 3
- **Relevant Learning Materials**: Module 5 — Move to Managed Analytics

### Move to Modern DevOps

- **Priority**: High
- **Trigger Criteria Met**:
  - INF-Q6: Score 1/4 — No CI/CD pipeline; manual deploy.sh only
  - OPS-Q9: Score 1/4 — Manual deployment, no canary/blue-green
  - OPS-Q10: Score 1/4 — Zero integration tests
  - OPS-Q1: Score 1/4 — No distributed tracing
- **Current State**: Manual deployment via `deploy.sh` shell script. No CI/CD pipeline. No tests of any kind. No tracing, no structured logging, no monitoring beyond App Runner health checks.
- **Target State**: Full CI/CD with CodePipeline/CodeBuild, automated testing in pipeline, canary deployments on EKS, distributed tracing with X-Ray/OpenTelemetry, structured logging with CloudWatch, SLOs with CloudWatch alarms.
- **Key Activities**:
  1. Create CodePipeline + CodeBuild for automated build/test/deploy
  2. Implement structured JSON logging with correlation IDs
  3. Deploy OpenTelemetry Collector on EKS for distributed tracing
  4. Add integration tests to CI/CD pipeline
  5. Implement canary deployment strategy on EKS (Argo Rollouts or Flagger)
  6. Set up CloudWatch dashboards, alarms, and SLOs
- **Dependencies**: None — can start immediately in parallel with Move to Containers
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 1 (CI/CD, logging), Phase 2 (tracing, testing, deployment strategy)
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

### Move to AI

- **Priority**: High
- **Trigger Criteria Met**:
  - APP-Q13: Score 1/4 — No AI/agent frameworks present
  - DATA-Q1: Score 1/4 — No vector database
  - DATA-Q3: Score 1/4 — No RAG implementation
  - OPS-Q3: Score 1/4 — No evaluation framework
  - OPS-Q6: Score 1/4 — No LLM cost tracking
- **Current State**: No AI capabilities whatsoever. No agent frameworks, no vector database, no embeddings, no RAG, no LLM integration. The application has rich decision-making endpoints (fraud detection, warehouse assignment, shipping carrier selection, quality control) that are currently manual — these are prime automation candidates.
- **Target State**: Amazon Bedrock agents automating order fulfillment decisions. RAG pipeline over order history and product catalog via Bedrock Knowledge Bases. OpenSearch vector database for semantic search. Automated evaluation framework for agent quality. LLM cost tracking with attribution.
- **Key Activities**:
  1. Deploy OpenSearch Service with k-NN for vector store
  2. Implement RAG pipeline with Bedrock Knowledge Bases
  3. Build fulfillment agent using Bedrock Agents with extracted service APIs as tools
  4. Create evaluation datasets for fulfillment decisions (order validation, warehouse assignment, carrier selection)
  5. Implement LLM cost tracking with CloudWatch custom metrics
  6. Deploy human-in-the-loop approval workflows for high-risk actions
- **Dependencies**: Move to Cloud Native (need API boundaries for tools), Move to Managed Databases (need vector DB)
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 3 (Agent Enablement)
- **Relevant Learning Materials**: Module 7 — Move to AI

## Recommended Self-Paced Learning Materials

**Module 2: Move to Cloud Native (Containers and Serverless):**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for microservices decomposition: Strangler Fig, Anti-corruption Layer, Saga patterns, Event Sourcing, Circuit Breaker, API routing, Hexagonal Architecture, and more. Critical for your monolith decomposition strategy.
- AWS Modernization Pathways: Move to Cloud Native Serverless — https://skillbuilder.aws/learning-plan/CMK2J48MVN/aws-modernization-pathways-move-to-cloud-native-serverless-includes-labs/EFUPP53B4Q
- Architecting Serverless Applications — https://skillbuilder.aws/learn/MRWENY7FSX/architecting-serverless-applications/QVFY2JHVEH
- Amazon DynamoDB for Serverless Architecture — https://skillbuilder.aws/learn/SY1Y83VKTB/amazon-dynamodb-for-serverless-architectures/K9NM3PHH3S
- Modernize a Monolith to ECS and Fargate using Application Discovery — https://skillbuilder.aws/learn/1YXAWYH2WA/modernize-a-monolith-to-ecs-and-fargate-using-application-discovery/AQ37WHN3K1
  - Directly applicable: walks through the monolith-to-containers migration pattern you need for Phase 2.
- Meeting Simulator: Transform Monolithic App into Serverless Microservices — https://skillbuilder.aws/learn/HUKQHYU9TB/meeting-simulator-transforming-our-monolithic-app-into-serverless-microservices/NS6S2J7YR7

**Module 3: Move to Containers with Amazon ECS and EKS:**
- AWS Modernization Pathways: Move to Containers with Amazon EKS — https://skillbuilder.aws/learning-plan/GNYBZ9X9EM/aws-modernization-pathways-move-to-containers-with-amazon-eks-includes-labs/1HB9MKXD2N
  - Your primary learning path given EKS is the preferred container orchestration platform.
- Introduction to Containers — https://skillbuilder.aws/learn/CUCA1DK47V/introduction-to-containers/XJ58VC1FF5
- Amazon EKS Primer — https://skillbuilder.aws/learn/Z521GMBP1J/amazon-eks-primer/NGM5AF9K72
- Deploy Applications on Amazon EKS (Lab) — https://skillbuilder.aws/learn/2B5XUE2V9C/lab--deploy-applications-on-amazon-elastic-kubernetes-service-eks/SM5HZNTY9J
  - Hands-on lab directly applicable to your Phase 2 EKS deployment.
- Amazon ECR Getting Started — https://skillbuilder.aws/learn/M494WWS5EF/amazon-ecr-getting-started/N5CQ7DC6HT
- EKS Workshop — https://www.eksworkshop.com/
  - Comprehensive EKS workshop covering ALB Ingress, service mesh, observability on EKS.
- EKS Auto Mode Workshop — https://catalog.workshops.aws/workshops/aadbd25d-43fa-4ac3-ae88-32d729af8ed4

**Module 4: Move to Managed Databases:**
- AWS Modernization Pathways: Move to Managed Databases — https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC/aws-modernization-pathways-move-to-managed-databases-includes-labs/2S2QZKG9DV
- Introduction to Building with AWS Databases — https://skillbuilder.aws/learn/HYKKWEN9ZS/introduction-to-building-with-aws-databases/V7RVH2KY91
- AWS PartnerCast: Vector Databases for Generative AI Applications — https://skillbuilder.aws/learn/UQ74USQJHU/aws-partnercast--vector-databases-for-generative-ai-applications--technical/7DKMBAPCST
  - Critical for understanding vector database options (OpenSearch k-NN, pgvector) for your RAG pipeline in Phase 3.

**Module 5: Move to Managed Analytics:**
- AWS Modernization Pathways: Move to Managed Analytics — https://skillbuilder.aws/learning-plan/RWZA84NMVV/aws-modernization-pathways-move-to-managed-analytics--includes-labs/9BAKK2QQQU

**Module 6: Move to Modern DevOps:**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
  - Comprehensive learning plan covering CI/CD, IaC, monitoring — all critical gaps for this application.
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
  - Essential for establishing the integration testing practices missing from this application (OPS-Q10: 1/4).
- AWS PartnerCast: Automate EKS Deployments With GitOps Using ArgoCD and GitHub Actions — https://skillbuilder.aws/learn/D9U7XMXP31/aws-partnercast--tech-talks--automate-eks-deployments-with-gitops-using-argocd-and-github-actions--technical/Z4M9Z8FY88
  - Directly applicable to your EKS deployment strategy with GitOps-based CI/CD.
- EKS Workshop: Automation — https://www.eksworkshop.com/docs/automation/

**Module 7: Move to AI:**
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
  - Foundation for integrating Bedrock agents in Phase 3.
- Essentials for Prompt Engineering — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
  - Hands-on lab for the RAG pipeline planned in Phase 3.
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
  - Core learning for understanding agentic patterns before building fulfillment automation agents.
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
- AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84
  - Advanced: covers observable agent patterns critical for production agent deployments.

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 3/4 🟡
- **Finding**: The CloudFormation template (`infrastructure/monolith-apprunner.yaml`) deploys an `AWS::AppRunner::Service` resource — a fully managed compute platform similar to ECS Fargate. The `Dockerfile` defines a PHP 8.2 Apache container image. Locally, `docker-compose.yml` runs the application via raw Docker. An ECR repository (`AWS::ECR::Repository`) is provisioned for image storage with scan-on-push enabled. App Runner provides managed scaling, HTTPS, and health checks.
- **Gap**: App Runner is managed compute but not the preferred EKS platform. Local development uses raw Docker Compose with no orchestration. No EKS cluster, no Kubernetes manifests, no ALB Ingress Controller.
- **Recommendation**: Create EKS cluster IaC with ALB Ingress Controller. Migrate from App Runner to EKS for container orchestration per user preference. Keep ECR for image storage.

#### INF-Q2: Databases
- **Score**: 3/4 🟡
- **Finding**: CloudFormation defines `AWS::RDS::DBInstance` (MySQL 8.4.8, `db.t3.micro`, gp3 storage, encrypted, private subnets, 7-day backup retention, auto minor version upgrade). RDS is a fully managed database service with automated backups and failover. However, `docker-compose.yml` runs a self-managed `mysql:8.0` container for local development with hardcoded credentials.
- **Gap**: Dev/prod environment mismatch (MySQL 8.0 vs 8.4.8). Local development uses self-managed MySQL. No Multi-AZ deployment configured for high availability in production.
- **Recommendation**: Align Docker Compose MySQL version with production. Consider enabling Multi-AZ for RDS in production. Evaluate Aurora MySQL for auto-scaling and better failover capabilities.

#### INF-Q3: Workflow Orchestration
- **Score**: 1/4 ❌
- **Finding**: No Step Functions, Temporal, Camunda, or any workflow orchestration service found in IaC or code. The order fulfillment workflow (confirmed → validated → warehouse_assigned → picking → packed → quality_checked → shipped → delivered) is implemented as sequential manual API calls in `index.php` with hardcoded status transitions via the `update_order_status()` function.
- **Gap**: No dedicated workflow orchestration. The 8-step fulfillment workflow is entirely manual and has no retry, compensation, or state management capabilities.
- **Recommendation**: Implement AWS Step Functions to orchestrate the order fulfillment workflow. Define the state machine with retry logic, error handling, and human approval tasks. This is a natural candidate for agent-driven automation.

#### INF-Q4: Async Messaging
- **Score**: 1/4 ❌
- **Finding**: No SQS, SNS, EventBridge, MSK, or any messaging resources found in the CloudFormation template or application code. All inter-process communication is synchronous HTTP. The `index.php` file processes all requests synchronously — order creation, payment processing, inventory updates, and status changes all happen in a single blocking request/response cycle.
- **Gap**: Zero async messaging capability. All operations are synchronous, creating tight coupling and fragility.
- **Recommendation**: Introduce Amazon SQS for the order fulfillment workflow. Start by publishing order events (order-confirmed, order-validated) to SQS queues, then add consumers that process each fulfillment step asynchronously. Add dead-letter queues for error handling.

#### INF-Q5: Infrastructure as Code
- **Score**: 3/4 🟡
- **Finding**: `infrastructure/monolith-apprunner.yaml` is a comprehensive CloudFormation template covering: VPC (`AWS::EC2::VPC`), 2 private subnets, DB subnet group, security groups (DB and App Runner), RDS MySQL instance, VPC Connector, ECR Repository, 2 IAM roles, App Runner Service, Auto Scaling Configuration, WAF Web ACL, IP Set, and WAF Association. This covers compute, networking, database, security, and container registry.
- **Gap**: No IaC for monitoring (CloudWatch alarms, dashboards), CI/CD pipeline (CodePipeline/CodeBuild), or DNS/Route53. The CloudFormation is for App Runner — EKS IaC does not exist yet. No Terraform or CDK usage.
- **Recommendation**: Create EKS cluster IaC (Terraform or CloudFormation). Add CloudWatch alarms and dashboards to IaC. Add CodePipeline/CodeBuild definitions. Target 90%+ IaC coverage.

#### INF-Q6: CI/CD
- **Score**: 1/4 ❌
- **Finding**: The only deployment mechanism is `deploy.sh` — a 30-line shell script that runs `docker-compose build` and `docker-compose up -d` locally. It includes a basic health check (`curl -f http://localhost:8080/api/products`). No GitHub Actions workflows, no `buildspec.yml`, no Jenkinsfile, no CodePipeline definitions, no `.gitlab-ci.yml`. The CloudFormation Outputs include manual deployment instructions (build → tag → push to ECR → update stack).
- **Gap**: No automated CI/CD pipeline. No automated testing, building, or deployment stages. Every deployment requires manual intervention.
- **Recommendation**: Create AWS CodePipeline with CodeBuild stages: source → lint → test → build Docker image → push to ECR → deploy to EKS. Add automated rollback on failed health checks.

#### INF-Q7: API Entry Point
- **Score**: 2/4 🟠
- **Finding**: App Runner provides a managed HTTPS endpoint (`AppRunnerServiceUrl` output). A WAF Web ACL (`AWS::WAFv2::WebACL`) with an IP Set is configured for IP whitelisting — default action is Block, with an Allow rule for specific IPs. WAF has CloudWatch metrics enabled (`CloudWatchMetricsEnabled: true`). However, there is no API Gateway, no ALB with throttling, no request validation, and no per-route auth configuration.
- **Gap**: No API Gateway with throttling, auth, and request validation. WAF provides IP whitelisting only — no rate limiting, no request/response transformation, no API key management.
- **Recommendation**: Deploy an ALB with the EKS migration. Configure ALB with health checks, path-based routing (for future microservices), and integrate with WAF rate-based rules. Consider adding API Gateway for agent-facing endpoints with throttling and request validation.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No Kinesis Data Streams, no MSK, no Kafka SDK imports, no stream consumer patterns found in IaC or application code. All data access is synchronous database queries.
- **Gap**: No real-time streaming capability. Cannot support event-driven data pipelines or real-time analytics for agent decision-making.
- **Recommendation**: Introduce Amazon Kinesis Data Streams or MSK Serverless for order and fulfillment event streaming after async messaging (SQS) is established. Use for real-time analytics on fulfillment performance.

#### INF-Q9: Network Security
- **Score**: 3/4 🟡
- **Finding**: CloudFormation defines a VPC (`10.0.0.0/16`), 2 private subnets (`10.0.1.0/24`, `10.0.2.0/24`), a DB security group allowing MySQL (3306) only from the App Runner security group, and the RDS instance is set to `PubliclyAccessible: false`. The App Runner VPC Connector routes egress through the VPC. WAF provides IP whitelisting.
- **Gap**: No public subnets defined (NAT Gateway pattern incomplete). No NACLs configured beyond VPC defaults. Security groups are appropriately restrictive but only cover two tiers (App Runner and DB). No VPC Flow Logs for network monitoring.
- **Recommendation**: Add VPC Flow Logs for network monitoring. Configure NACLs for defense-in-depth. When migrating to EKS, ensure pod security policies and network policies are configured. Add a public subnet tier with NAT Gateway for outbound internet access.

#### INF-Q10: Auto-scaling
- **Score**: 3/4 🟡
- **Finding**: CloudFormation defines `AWS::AppRunner::AutoScalingConfiguration` with configurable `MinSize` (default 1), `MaxSize` (default 3), and `MaxConcurrency` (100). Parameters allow adjustment of min/max via CloudFormation parameters.
- **Gap**: Auto-scaling is limited to the single App Runner service. No auto-scaling for the database tier (RDS `db.t3.micro` is fixed). When migrating to EKS, Horizontal Pod Autoscaler (HPA) and Cluster Autoscaler will need to be configured.
- **Recommendation**: When migrating to EKS, configure HPA based on CPU/memory and custom metrics. Set up Cluster Autoscaler or Karpenter for node scaling. Consider Aurora Auto-scaling for the database tier.

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 2/4 🟠
- **Finding**: The application is written entirely in PHP 8.2 (specified in `Dockerfile`: `FROM php:8.2-apache`). PHP extensions include `pdo` and `pdo_mysql`. The frontend is inline HTML/CSS/JavaScript within `index.php`. No `composer.json` dependency manifest exists — the application relies solely on PHP built-in extensions.
- **Gap**: PHP has a limited agent framework ecosystem compared to Python or TypeScript. No Bedrock SDK, no LangChain, no Strands Agents SDK for PHP. The inline JavaScript frontend lacks a modern framework.
- **Recommendation**: When extracting microservices, consider using Python or TypeScript for new services to leverage the richer agent SDK ecosystem (boto3 with Bedrock, LangChain, Strands Agents). Keep the PHP monolith running during the transition.

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: No `openapi.yaml`, `swagger.json`, or any API specification file exists in the repository. API routes are defined inline in `index.php` using PHP regex pattern matching (e.g., `preg_match('#^/api/orders/([^/]+)/validate$#', $request_uri, $matches)`). There are approximately 20+ API endpoints covering products, orders, fulfillment workflow, returns, user management, and admin operations. No API documentation annotations, no auto-generation, no Swagger UI.
- **Gap**: No machine-readable API specification. Agents cannot discover or invoke tools without OpenAPI specs. The current API surface is undocumented and only discoverable by reading source code.
- **Recommendation**: Create an OpenAPI 3.0 specification documenting all `/api/*` endpoints. Include request/response schemas, authentication requirements, and error codes. This is the single most important prerequisite for agent tool integration.

#### APP-Q3: Async vs Sync Communication
- **Score**: 1/4 ❌
- **Finding**: 100% of communication is synchronous. All API endpoints in `index.php` process requests in a single blocking request/response cycle. Order creation (`POST /api/orders`) performs inventory check, order insert, item inserts, inventory update, payment insert, and status update all within a single database transaction (`$db->beginTransaction()` / `$db->commit()`). No message publishing, no event-driven patterns, no queue consumers, no async job processing.
- **Gap**: All operations are synchronous, creating fragility and preventing resilient workflow execution. Long-running operations (return processing, order fulfillment) block the caller.
- **Recommendation**: Introduce Amazon SQS for decoupling the order fulfillment workflow. Publish events on order state changes, consume them asynchronously. Use EventBridge for cross-domain event distribution as services are extracted.

#### APP-Q4: Monolith vs Microservices
- **Score**: 1/4 ❌
- **Finding**: The entire application is a single `index.php` file containing all business domains: orders, inventory, payments, returns, user management, warehouse management, shipping, and quality control. It includes the full HTML/CSS/JS frontend (embedded inline). The shared MySQL database has 9 tables with foreign keys across domains (`order_items` → `orders`, `payments` → `orders`, `returns` → `orders`). There is one deployable unit (Dockerfile copies only `index.php` and `.htaccess`). There are no module boundaries, no namespace separation, no interfaces between domains. Functions like `get_db()`, `init_db()`, `seed_data()`, and `update_order_status()` are shared globally. All domains share mutable state through the same PDO connection.
- **Gap**: Tightly-coupled monolith with no clear module boundaries, pervasive shared state via the database, cross-domain foreign keys, and inline frontend. This is the most severe architectural blocker for agentic readiness.
- **Recommendation**: See Microservices Decomposition Strategy in the Readiness Roadmap section. Start with the Parallel Track (Option B) approach: containerize on EKS first, then extract Inventory Service using Strangler Fig pattern.

#### APP-Q5: API Response Format
- **Score**: 3/4 🟡
- **Finding**: All `/api/*` endpoints return structured JSON responses using `json_encode()`. The content type is set via `header('Content-Type: application/json')`. API responses include consistent structures like `{'products': [...]}`, `{'success': true, 'order_id': '...'}`, `{'error': '...'}` with appropriate HTTP status codes (200, 400, 401, 403, 404, 500). The non-API routes (login page, main application) return HTML.
- **Gap**: API responses are JSON but there is no standardized error response format across all endpoints. HTML rendering is mixed into the same file. No JSON Schema validation on responses.
- **Recommendation**: Standardize the error response format across all APIs (e.g., `{error: string, code: string, details: object}`). When extracting services, separate the frontend from the API layer entirely.

#### APP-Q6: Workflow Logic
- **Score**: 1/4 ❌
- **Finding**: The order fulfillment workflow is hardcoded across multiple API endpoints in `index.php`. The status flow is: `confirmed` → `validated` → `warehouse_assigned` → `picking` → `packed` → `quality_checked` → `shipped` → `delivered`. Each transition is a separate POST endpoint (e.g., `/api/orders/{id}/validate`, `/api/orders/{id}/assign-warehouse`, `/api/orders/{id}/pick`). The `update_order_status()` helper function records history but has no state machine validation — any status can be set at any time. No Step Functions, no Temporal, no workflow engine.
- **Gap**: No workflow orchestration. Status transitions are not validated (no guard conditions). No retry logic, no compensation on failure, no timeouts. A failed step leaves the order in an inconsistent state.
- **Recommendation**: Implement AWS Step Functions for the fulfillment workflow. Define valid state transitions, retry policies, timeouts, and compensation actions. Add human approval tasks for quality check and return processing.

#### APP-Q7: Idempotency
- **Score**: 1/4 ❌
- **Finding**: No idempotency keys, no deduplication tokens, no upsert patterns found. Order IDs are generated with `uniqid('order-')`, payment IDs with `uniqid('pay-')`, return IDs with `uniqid('return-')` — all non-idempotent. A duplicate `POST /api/orders` request would create a duplicate order. No `Idempotency-Key` header handling. No deduplication on SQS (since SQS is not used).
- **Gap**: No idempotency support on any write endpoint. Duplicate requests will create duplicate records. This is dangerous for agent workflows where retries are common.
- **Recommendation**: Add idempotency key support to critical write endpoints (order creation, payment processing, return approval). Use a database-backed idempotency table or DynamoDB for idempotency token storage. Generate deterministic IDs instead of `uniqid()`.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: The WAF Web ACL in CloudFormation provides IP whitelisting only — no rate-based rules. No rate limiting middleware in the PHP application code (no `express-rate-limit` equivalent). No API Gateway usage plan or throttling configuration. No per-client or per-endpoint rate limiting.
- **Gap**: No rate limiting at any layer. An agent (or any client) could overwhelm the application with requests. No protection against abuse or runaway agent loops.
- **Recommendation**: Add WAF rate-based rules as an immediate fix. When migrating to EKS with ALB, configure rate limiting. For agent-facing endpoints, implement per-client throttling with API Gateway usage plans.

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: No circuit breakers, no retry logic, no timeout configurations, no exponential backoff found in the application code. Database calls use basic `try/catch` blocks with `PDOException` handling but no retry on transient failures. The `get_db()` function terminates the process on connection failure (`die("Database connection failed: ...")`). No Resilience4j, Hystrix, or any resilience library.
- **Gap**: No resilience patterns. Database connection failure crashes the application. No graceful degradation, no fallback responses, no timeout on external calls.
- **Recommendation**: Implement connection pooling and retry with exponential backoff for database connections. Add timeouts on all database queries. When extracting services, implement circuit breaker pattern for inter-service communication. Use Guzzle HTTP client with retry middleware for external API calls.

#### APP-Q10: Long-running Processes
- **Score**: 1/4 ❌
- **Finding**: All operations are synchronous and blocking. Return processing (`POST /api/returns`), order creation with inventory checks and payment processing (`POST /api/orders`), and the multi-step fulfillment workflow all execute within a single HTTP request/response. The return submission response states: "A customer service representative will review your request within 24-48 hours" — indicating manual async processing that is not automated. No background job framework (no Celery, no Bull, no PHP workers).
- **Gap**: No async processing for any operation. Long-running operations like return review, order fulfillment, and quality inspection are handled manually outside the application.
- **Recommendation**: Implement SQS-based async job processing for return reviews, fulfillment automation, and quality checks. Use Step Functions for orchestrating multi-step async workflows. Return status polling APIs are already partially present.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No URL path versioning (no `/v1/`, `/v2/` prefixes). No `Accept-Version` headers. No versioning annotations. All API routes use unversioned paths (e.g., `/api/products`, `/api/orders`, `/api/admin/users`). No changelog or API versioning documentation.
- **Gap**: No API versioning strategy. Breaking changes to agent tool APIs would break all agents simultaneously with no backward compatibility.
- **Recommendation**: Introduce URL path versioning (`/api/v1/products`) when creating the OpenAPI specification. Implement a versioning strategy that supports backward compatibility for agent tool definitions.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 1/4 ❌
- **Finding**: Single monolith — no service-to-service communication exists. The database host is configured via environment variable (`$host = getenv('DB_HOST') ?: 'mysql'`) with a hardcoded fallback default. No AWS Service Discovery, no App Mesh, no Consul, no service registry. No API catalog.
- **Gap**: No service discovery mechanism. When services are extracted, they will need a way to discover each other. The hardcoded database host fallback is a risk.
- **Recommendation**: When migrating to EKS, use Kubernetes native service discovery (DNS-based). For cross-service communication, use ALB path-based routing initially. Evaluate AWS Cloud Map or App Mesh as the number of services grows.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No AI or agent framework imports, SDKs, or integrations found anywhere in the codebase. No `boto3` with Bedrock, no LangChain, no Strands Agents SDK, no OpenAI SDK, no MCP SDK. No `composer.json` with any AI-related dependencies. The application has rich decision-making endpoints (fraud detection in `/api/orders/{id}/validation-data`, warehouse assignment in `/api/warehouses/assignment-options`, shipping carrier selection in `/api/carriers/shipping-options`, quality checklist in `/api/orders/{id}/quality-checklist`) that are currently manual processes — prime candidates for agent automation.
- **Gap**: No AI capabilities. However, the application has well-structured decision-making data endpoints that provide context for human decisions — these map directly to agent tool inputs.
- **Recommendation**: The existing decision-data endpoints provide an excellent foundation for agent tools. When building the fulfillment agent in Phase 3, use these endpoints as tool inputs (via OpenAPI specs) for Amazon Bedrock agents. Consider Python or TypeScript for the agent orchestration layer.

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No vector database found. No OpenSearch with k-NN plugin, no Aurora pgvector extension, no S3 Vectors, no Bedrock Knowledge Bases, no Pinecone, no Weaviate, no Chroma imports in the codebase or IaC. The only database is MySQL (RDS in production, Docker Compose locally).
- **Gap**: No vector storage or semantic search capability. Agents cannot perform similarity-based product searches, find related orders, or leverage semantic understanding of customer interactions.
- **Recommendation**: Deploy Amazon OpenSearch Service with k-NN plugin for vector search. Alternatively, evaluate Aurora PostgreSQL with pgvector if consolidating on a single database engine is preferred. Use for product catalog semantic search and customer interaction similarity.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database exists (see DATA-Q1), so there is no vector DB management to evaluate.
- **Gap**: When a vector database is introduced, it must be a managed service to avoid operational overhead.
- **Recommendation**: Use a fully managed vector database: Amazon OpenSearch Service (managed), Bedrock Knowledge Bases (serverless), or Aurora PostgreSQL with pgvector (managed). Avoid self-hosted solutions.

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No RAG pipeline components found. No embedding model calls, no document chunking/splitting code, no similarity search patterns, no Bedrock Knowledge Base integration. No references to embedding models (Titan, ada) or vector search APIs.
- **Gap**: No RAG capability. The application has rich data (order history, customer interactions, product catalog) that could benefit from semantic retrieval for agent-assisted customer service and fulfillment optimization.
- **Recommendation**: Implement RAG using Amazon Bedrock Knowledge Bases. Ingest product catalog, order history, and fulfillment data. Use Amazon Titan Embeddings for vector generation. Connect to OpenSearch as the vector store.

#### DATA-Q4: Data Source Sprawl
- **Score**: 4/4 ✅
- **Finding**: Single MySQL database with 9 tables: `orders`, `order_items`, `inventory`, `payments`, `returns`, `interactions`, `order_status_history`, `warehouses`, `users`. All data is accessed through a single PDO connection via the `get_db()` function. No external API calls, no additional data sources, no file storage, no cache layer.
- **Gap**: None — single data source is optimal for agent simplicity. However, as services are extracted, data source sprawl will need to be managed with a unified data access layer.
- **Recommendation**: Maintain data source discipline during microservices extraction. Implement a unified API layer (each service owns its data and exposes it via APIs) to prevent sprawl as the architecture evolves.

#### DATA-Q5: Data Access Pattern
- **Score**: 1/4 ❌
- **Finding**: All data access is via direct PDO database connections inline in API route handlers. Raw SQL queries are scattered throughout `index.php` — for example: `$stmt = $db->prepare('SELECT * FROM orders WHERE id = ?')`, `$stmt = $db->prepare('UPDATE inventory SET stock_quantity = stock_quantity - ? WHERE product_id = ?')`. No repository pattern, no Data Access Objects (DAOs), no ORM (no Eloquent, no Doctrine). The `get_db()` function returns a raw PDO connection used directly in every handler.
- **Gap**: No data access layer. SQL is tightly coupled to route handlers, making it impossible for agents to access data through well-defined interfaces. Database schema changes would require modifying every handler.
- **Recommendation**: As services are extracted, implement a repository pattern for each service's data access. Each microservice should own its data and expose it only through APIs — direct database access from other services must be prohibited.

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: No S3 storage, no document parsing libraries (Textract, Tika), no file upload handling. Product image URLs reference `/images/` paths (e.g., `/images/tshirt.jpg`, `/images/jeans.jpg`) but these are static relative URLs with no actual file storage or processing infrastructure.
- **Gap**: No unstructured data handling. Cannot process customer-uploaded documents (return photos, damage claims) or product images for AI analysis.
- **Recommendation**: Implement S3 for product image and document storage. Add Amazon Textract or Rekognition for document/image processing in the returns workflow (e.g., customer uploads damage photos for agent-assisted return processing).

#### DATA-Q7: Schema Documentation
- **Score**: 1/4 ❌
- **Finding**: No JSON Schema files, no Avro/Protobuf schemas, no database migration framework (Flyway, Liquibase, Alembic, Phinx). The database schema is defined via `CREATE TABLE IF NOT EXISTS` statements in the `init_db()` function in `index.php`. Schema changes are handled with inline `ALTER TABLE` statements wrapped in try/catch blocks (e.g., adding `warehouse_location`, `weight_lbs`, `dimensions` columns to the inventory table). No schema versioning, no migration history.
- **Gap**: No schema documentation or versioning. Schema changes are fragile (ALTER TABLE in try/catch). No way to track schema evolution or roll back schema changes.
- **Recommendation**: Implement a database migration framework (Flyway for MySQL or Phinx for PHP). Extract schema definitions into versioned migration files. Document the schema with OpenAPI schema definitions in the API specification.

#### DATA-Q8: Data Access Layer
- **Score**: 1/4 ❌
- **Finding**: No unified data access layer. The `get_db()` function provides a raw PDO connection. All SQL queries are scattered across ~20+ route handlers in `index.php`. For example, the order creation handler contains 5 different SQL operations (SELECT inventory, INSERT orders, INSERT order_items, UPDATE inventory, INSERT payments). There is no abstraction, no query builder, no centralized data contract.
- **Gap**: No data access abstraction. Every route handler contains its own SQL, creating duplication and making schema changes risky. No single point of data contract for agents to interact with.
- **Recommendation**: When extracting services, implement a repository pattern per service. Each service should have a dedicated data access layer that encapsulates all database operations behind a clean interface. Use an ORM (Eloquent for PHP, SQLAlchemy for Python, Prisma for TypeScript) to reduce raw SQL.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embeddings exist (see DATA-Q1, DATA-Q3). No event-driven embedding refresh triggers, no scheduled re-indexing pipelines, no CDC (Change Data Capture) patterns.
- **Gap**: When embeddings are implemented, they must be kept fresh as the underlying data changes.
- **Recommendation**: When implementing the RAG pipeline, set up event-driven embedding refresh. Use DynamoDB Streams or SQS events triggered on data changes (product catalog updates, new orders) to incrementally update embeddings in the vector store.

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 3/4 🟡
- **Finding**: CloudFormation explicitly pins MySQL version: `EngineVersion: '8.4.8'` in `infrastructure/monolith-apprunner.yaml`. Docker Compose uses `mysql:8.0` in `docker-compose.yml`. MySQL 8.0 reached end-of-life in April 2026, but 8.4 is a current Innovation Release. Both versions are explicitly specified (not implicit latest). RDS has `AutoMinorVersionUpgrade: true` enabled.
- **Gap**: Dev/prod version mismatch: Docker Compose uses MySQL 8.0 while RDS uses 8.4.8. This can cause behavioral differences in SQL execution. MySQL 8.0 is approaching EOL.
- **Recommendation**: Update `docker-compose.yml` to use `mysql:8.4` to match production. Consider standardizing on MySQL 8.4 LTS or evaluating Aurora MySQL for enhanced managed capabilities.

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 4/4 ✅
- **Finding**: No stored procedures, triggers, or functions found in any SQL statements in `index.php`. All `CREATE TABLE` statements use standard MySQL DDL without proprietary constructs. All business logic resides in the PHP application layer. No `.sql` files with `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION`. No ORM bypass patterns or raw proprietary SQL.
- **Gap**: None — all business logic is in the application layer, which is the desired state for agentic readiness. This significantly simplifies database migration and service extraction.
- **Recommendation**: Maintain this practice as services are extracted. Keep all business logic in the application/service layer. Avoid introducing stored procedures or database-level triggers.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 1/4 ❌
- **Finding**: Database credentials are hardcoded in multiple locations: `docker-compose.yml` contains `MYSQL_ROOT_PASSWORD: rootpassword`, `MYSQL_USER: ecommerce_user`, `MYSQL_PASSWORD: ecommerce_pass`. The `index.php` `get_db()` function has hardcoded fallback credentials: `$user = getenv('DB_USER') ?: 'ecommerce_user'` and `$pass = getenv('DB_PASS') ?: 'ecommerce_pass'`. CloudFormation uses Parameters with `NoEcho: true` for DB credentials but includes `Default` values (`DBUsername: ecommerce_user`, `DBPassword: ChangeMe123!`). No AWS Secrets Manager, no HashiCorp Vault, no parameter store references.
- **Gap**: Credentials are hardcoded in source code and configuration files. Default passwords in CloudFormation parameters. No secret rotation capability.
- **Recommendation**: Migrate all secrets to AWS Secrets Manager. Remove hardcoded fallbacks from `index.php`. Remove default values from CloudFormation DB credential parameters. Implement automatic secret rotation for database credentials.

#### SEC-Q2: IAM Least Privilege
- **Score**: 2/4 🟠
- **Finding**: CloudFormation defines two IAM roles. `AppRunnerInstanceRole` uses the managed policy `arn:aws:iam::aws:policy/CloudWatchLogsFullAccess` — this grants wildcard access to all CloudWatch Logs actions and resources (`logs:*`), which is overly broad. `AppRunnerAccessRole` uses `AWSAppRunnerServicePolicyForECRAccess` — this is appropriately scoped for ECR image pulling. Both roles have specific `AssumeRolePolicyDocument` limiting the trust to App Runner service principals.
- **Gap**: `CloudWatchLogsFullAccess` is a wildcard policy granting permissions far beyond what the application needs. No per-service IAM roles (monolith has one role for everything). No condition keys or resource restrictions on the instance role.
- **Recommendation**: Replace `CloudWatchLogsFullAccess` with a custom policy granting only `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` on specific log group ARNs. When migrating to EKS, use IAM Roles for Service Accounts (IRSA) with per-pod least-privilege policies.

#### SEC-Q3: Identity Propagation
- **Score**: 1/4 ❌
- **Finding**: Authentication is PHP session-based. `session_start()` initializes the session; `$_SESSION['user']` stores the authenticated user object after login. API endpoints check `isset($_SESSION['user'])` and return 401 if not set. Admin endpoints additionally check `$_SESSION['user']['role'] !== 'admin'` for 403. Password is removed from the session (`unset($user['password'])`). No JWT tokens, no OAuth2 flows, no token exchange, no Cognito integration.
- **Gap**: Session-based auth does not propagate across services. When services are extracted, there is no user identity token to pass between them. Sessions are server-local and not portable across EKS pods without sticky sessions or session stores.
- **Recommendation**: Implement JWT-based authentication. Use Amazon Cognito as the identity provider. Issue JWT tokens on login, validate them in each service. Implement token exchange for service-to-service authentication. Store sessions in ElastiCache Redis for the transition period.

#### SEC-Q4: Audit Logging
- **Score**: 1/4 ❌
- **Finding**: No CloudTrail configuration in the CloudFormation template. No application-level audit logging beyond the `order_status_history` table, which records order status changes with `changed_by`, `notes`, and `created_at` fields. No immutable log storage, no CloudWatch log retention policies defined in IaC. No logging of authentication events, API access, or data modifications outside of order status changes.
- **Gap**: No comprehensive audit trail. No CloudTrail for AWS API activity. No application audit log for security-relevant events (login attempts, permission changes, data access).
- **Recommendation**: Enable CloudTrail with log file validation and S3 object lock for immutable storage. Implement application-level audit logging for authentication events, admin actions, and data modifications. Set CloudWatch log retention policies.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: The WAF Web ACL in CloudFormation is configured for IP whitelisting only (`IPSetReferenceStatement` with Allow action). The default action is `Block`. No rate-based rules are defined in the WAF configuration. No API Gateway throttle settings. No application-level rate limiting middleware.
- **Gap**: No rate limiting enforcement. Agent requests are not throttled. No per-client quotas. A runaway agent could overwhelm the application.
- **Recommendation**: Add WAF rate-based rules (e.g., 1000 requests per 5 minutes per IP). When adding API Gateway for agent endpoints, configure per-client usage plans with burst and rate limits. Implement application-level rate limiting for critical endpoints.

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: No PII redaction in logs or error messages. Customer emails (`customer_email`), names (`customer_name`), and addresses (`shipping_address`) are returned in API responses without masking. The password is removed from the session object (`unset($user['password'])`), but no other PII scrubbing exists. No log filtering, no Macie integration, no PII regex patterns in logging utilities. Error messages include raw database error details (`$e->getMessage()`) which could leak schema information.
- **Gap**: PII is exposed in API responses and could appear in logs. Error messages leak database internals. No automated PII detection or redaction.
- **Recommendation**: Implement PII masking in API responses (e.g., mask email to `j***@example.com`). Add log scrubbing middleware to redact PII before logging. Sanitize error messages to hide database internals. Consider Amazon Macie for S3 data classification when unstructured data is added.

#### SEC-Q7: Human Approval Workflows
- **Score**: 2/4 🟠
- **Finding**: Manual admin approval exists for returns via the `POST /api/admin/approve-return` endpoint — an admin must review pending returns and manually approve them, triggering refund processing and inventory restoration. The order fulfillment workflow also requires manual admin action at each step (validate, assign warehouse, pick, pack, quality check, ship). However, these are not formal human-in-the-loop workflows — they are simple API endpoints that any admin can call without structured approval processes, audit trails, or escalation paths.
- **Gap**: Manual approval exists but is not a structured workflow. No Step Functions with `waitForTaskToken` patterns. No approval queues, no SLA tracking on approvals, no escalation for delayed reviews.
- **Recommendation**: Implement Step Functions with human approval tasks (`waitForTaskToken`) for high-risk actions: return approvals over a threshold amount, bulk inventory changes, and user role changes. Add SLA tracking and escalation for delayed approvals.

#### SEC-Q8: Encryption at Rest
- **Score**: 2/4 🟠
- **Finding**: RDS has `StorageEncrypted: true` in CloudFormation, using the default AWS-managed encryption key. ECR repository uses `EncryptionType: AES256` (AWS-managed). No customer-managed KMS keys (`aws_kms_key` resources) are defined. No encryption configuration on other data stores (there are no S3 buckets, DynamoDB tables, or EBS volumes in the current architecture).
- **Gap**: Encryption uses AWS-managed keys only, not customer-managed KMS keys. No key rotation policy. No encryption policy for data in transit within the VPC.
- **Recommendation**: Create customer-managed KMS keys for RDS and ECR encryption. Enable KMS key rotation. When adding S3 and other data stores, enforce encryption with customer-managed keys via AWS Config rules.

#### SEC-Q9: API Authentication
- **Score**: 2/4 🟠
- **Finding**: All `/api/*` endpoints check for session authentication: `if (!isset($_SESSION['user'])) { http_response_code(401); ... }`. Admin endpoints additionally check role: `if ($_SESSION['user']['role'] !== 'admin') { http_response_code(403); ... }`. Login uses username/password with `password_verify()` against bcrypt-hashed passwords. However, there is no OAuth2, no JWT, no API Gateway authorizers, no API key authentication, no CORS configuration.
- **Gap**: Session-based auth only. No token-based authentication suitable for agent-to-API communication. No API keys for programmatic access. No CORS headers for cross-origin requests.
- **Recommendation**: Implement JWT-based authentication via Amazon Cognito. Add API key authentication for agent/programmatic access. Configure CORS headers. When adding API Gateway, use Cognito authorizers for all endpoints.

#### SEC-Q10: Centralized Identity
- **Score**: 1/4 ❌
- **Finding**: No centralized identity provider. Authentication is handled by a custom `users` table in MySQL with bcrypt-hashed passwords. Login is via `POST /login` with form-based username/password submission. No Amazon Cognito, no OIDC/SAML configuration, no Okta/Ping integration, no SSO, no MFA. User management is via admin CRUD endpoints (`/api/admin/users`).
- **Gap**: No centralized identity provider. Custom auth implementation is a security risk and does not support federation, SSO, or MFA. Cannot integrate with enterprise identity systems.
- **Recommendation**: Implement Amazon Cognito as the centralized identity provider. Migrate existing users to Cognito User Pool. Enable MFA. Configure OIDC federation for enterprise SSO. Use Cognito tokens for API authentication across all services.

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 1/4 ❌
- **Finding**: No X-Ray SDK, no OpenTelemetry SDK, no trace context propagation headers (`traceparent`, `X-Amzn-Trace-Id`). No tracing instrumentation in the PHP code. No tracing-related dependencies in the application (no `composer.json` with tracing packages). No Datadog, Jaeger, or Zipkin SDK. No service map or dependency graph generation.
- **Gap**: Zero distributed tracing capability. Cannot trace requests across the monolith or future services. Cannot reconstruct agent execution paths.
- **Recommendation**: Deploy OpenTelemetry Collector as a sidecar/DaemonSet in EKS. Instrument the PHP application with the OpenTelemetry PHP SDK. Configure trace context propagation for all HTTP calls. Enable AWS X-Ray as the tracing backend.

#### OPS-Q2: Structured Logging
- **Score**: 1/4 ❌
- **Finding**: PHP error logging is configured with `error_reporting(E_ALL)`, `ini_set('display_errors', '0')`, and `ini_set('log_errors', '1')` in `index.php`. This outputs unstructured plain-text error logs. No JSON log formatter (no Monolog, no structlog equivalent). No correlation IDs in log output. No request ID tracking. No CloudWatch Logs Insights queries.
- **Gap**: Unstructured plain-text logs with no correlation IDs. Cannot correlate logs across requests or trace agent actions. Cannot query logs effectively.
- **Recommendation**: Implement Monolog with JSON formatter for structured logging. Add request correlation ID middleware that generates a UUID per request and includes it in all log entries. Configure CloudWatch Logs agent for log aggregation from EKS pods.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No evaluation framework, no golden datasets, no scoring scripts, no LLM-as-judge patterns, no test assertions for LLM outputs. No AI/ML testing infrastructure of any kind.
- **Gap**: No agent evaluation capability. When agents are deployed, there is no way to measure their quality, detect regressions, or compare prompt versions.
- **Recommendation**: Create golden datasets for fulfillment decisions: manually curated examples of correct order validation, warehouse assignment, and shipping carrier selection. Build automated eval pipeline using Python with RAGAS or custom scoring. Integrate into CI/CD pipeline.

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: No SLO definitions in code or configuration. No CloudWatch alarms in the CloudFormation template (no `AWS::CloudWatch::Alarm` resources). No error budget tracking. The only health monitoring is the App Runner `HealthCheckConfiguration` (HTTP check on `/`, interval 10s, timeout 5s). No p99/p95 latency monitoring.
- **Gap**: No SLOs for any user journey. No alerting on degraded performance. Cannot define or monitor agent-level SLOs (task success rate, latency).
- **Recommendation**: Define SLOs for critical user journeys: order creation (<500ms p99), product listing (<200ms p99), fulfillment step completion (<2s p99). Create CloudWatch alarms for these SLOs. Track error budgets. Extend to agent SLOs in Phase 3.

#### OPS-Q5: Rollback Capability
- **Score**: 1/4 ❌
- **Finding**: No blue/green deployment, no canary deployment, no feature flags, no rollback configuration. `deploy.sh` is a forward-only deployment script (`docker-compose build && docker-compose up -d`). No CodeDeploy rollback triggers. No Helm rollback. No `RollbackConfiguration` in CloudFormation. No prompt versioning (no prompts exist yet).
- **Gap**: No automated rollback. A bad deployment requires manual intervention. No ability to quickly revert agent behavior changes.
- **Recommendation**: When migrating to EKS, implement canary deployments using Argo Rollouts or Flagger. Configure automated rollback on health check failure. Add feature flags (AWS AppConfig) for gradual rollout of agent capabilities and prompt changes.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage in the application. No token counting, no cost attribution, no usage metrics. No CloudWatch custom metrics for any AI/ML usage.
- **Gap**: When LLMs are integrated, there is no infrastructure for tracking token usage, costs, or attribution.
- **Recommendation**: When integrating Bedrock agents in Phase 3, implement per-request token usage tracking. Log the `usage` object from LLM responses. Publish CloudWatch custom metrics for token counts with dimensions for user, workflow, and model. Set up cost alerting thresholds. Implement tiered retention policies for agent telemetry data.

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: No custom CloudWatch metrics, no business outcome tracking. No `cloudwatch.put_metric_data` calls. No dashboards tracking business KPIs (order volume, fulfillment time, return rate, revenue). The application only tracks order status history in the `order_status_history` database table — not as operational metrics.
- **Gap**: No business metrics published. Cannot measure fulfillment efficiency, customer satisfaction, or agent impact on business outcomes.
- **Recommendation**: Publish CloudWatch custom metrics for: orders per hour, average fulfillment time, return rate, revenue per day. Create operational dashboards. When agents are deployed, track agent-driven vs manual fulfillment rates and decision accuracy.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: No CloudWatch anomaly detection. No error rate alarms. No latency monitoring. No PagerDuty/OpsGenie integration. No composite alarms. WAF has `CloudWatchMetricsEnabled: true` but no alarms configured on WAF metrics.
- **Gap**: No anomaly detection. Cannot detect when error rates spike, latency degrades, or agent behavior deviates from baselines. Agentic systems can cause harm at machine speed without detection.
- **Recommendation**: Enable CloudWatch anomaly detection on key metrics (error rate, latency, request count). Create composite alarms. Set up PagerDuty/OpsGenie integration for on-call alerting. When agents are deployed, add behavioral anomaly detection (tool call frequency, response time variance).

#### OPS-Q9: Deployment Strategy
- **Score**: 1/4 ❌
- **Finding**: Deployment is manual via `deploy.sh` which runs `docker-compose build` and `docker-compose up -d`. This is a direct-to-production deployment with no staged rollout. No CodeDeploy, no Helm canary, no Argo Rollouts, no Lambda traffic shifting, no ALB weighted target groups, no feature flags.
- **Gap**: Direct-to-production deployments with no safety net. Any deployment failure affects all users immediately.
- **Recommendation**: Implement canary deployment strategy on EKS using Argo Rollouts or Flagger. Route 5% of traffic to the new version, monitor error rates and latency, automatically roll back if metrics degrade. Use feature flags (AWS AppConfig) for gradual feature enablement.

#### OPS-Q10: Integration Testing
- **Score**: 1/4 ❌
- **Finding**: No test files, no test directories, no PHPUnit configuration, no `composer.json` with test dependencies, no `phpunit.xml`. No integration test suites, no API tests (Postman/Newman), no contract tests, no end-to-end test pipelines. The only validation is the health check in `deploy.sh` (`curl -f http://localhost:8080/api/products`).
- **Gap**: Zero test coverage. No way to validate that changes don't break existing functionality. No regression testing for agent tool APIs.
- **Recommendation**: Add PHPUnit for unit and integration tests covering critical workflows (order creation, fulfillment steps, return processing). Add API integration tests using Postman/Newman. Integrate tests into the CI/CD pipeline. When services are extracted, add contract tests between services.

#### OPS-Q11: Incident Response Automation
- **Score**: 1/4 ❌
- **Finding**: No runbook files in the repository (no markdown, YAML, or JSON runbooks). No Systems Manager Automation documents. No Lambda-based remediation functions. No Step Functions for incident workflows. No self-healing patterns (no auto-restart beyond Docker Compose's depends_on). No links to runbooks in any alert configuration (no alerts exist).
- **Gap**: No incident response automation. No machine-readable runbooks for agents to execute. Manual incident response only.
- **Recommendation**: Create operational runbooks in markdown format for common incidents (database connection failure, high error rate, capacity exhaustion). Implement SSM Automation documents for automated remediation (restart pods, scale up, failover). Add self-healing patterns in EKS (liveness/readiness probes, pod disruption budgets).

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No CODEOWNERS file, no team ownership files, no SLO definition files, no observability configuration files. No platform team tooling evidence. No per-service dashboards or per-service alarms. The only observability-related resource is the `CloudWatchLogsFullAccess` managed policy on the App Runner instance role — which provides access but no structure.
- **Gap**: No observability ownership model. No SLO-driven culture. No shared responsibility model for monitoring. When agents are deployed, there will be no accountability for agent quality, reliability, or safety.
- **Recommendation**: Establish an observability ownership model. Create a CODEOWNERS file. Define service-level SLOs with named owners. Set up centralized dashboards. When agents are deployed, assign ownership for agent-level SLOs (task success rate, hallucination rate, tool error rate).

## Appendix: Evidence Index

| # | File | What It Revealed |
|---|------|-----------------|
| 1 | `index.php` | Single monolithic PHP file (~2,000+ lines) containing all business domains: orders, inventory, payments, returns, users, warehouses, shipping, QC. Inline HTML/CSS/JS frontend. Direct PDO database access. Session-based auth. Hardcoded credential fallbacks. 20+ API endpoints with JSON responses. No resilience patterns, no idempotency, no structured logging. |
| 2 | `infrastructure/monolith-apprunner.yaml` | CloudFormation template deploying: VPC with private subnets, RDS MySQL 8.4.8 (encrypted, private), App Runner Service, ECR Repository, 2 IAM roles (one with overly broad CloudWatchLogsFullAccess), Auto Scaling Configuration (min 1, max 3), WAF Web ACL with IP whitelisting. No CloudWatch alarms, no Step Functions, no SQS, no API Gateway. |
| 3 | `Dockerfile` | PHP 8.2 Apache container with `pdo` and `pdo_mysql` extensions. Copies only `index.php` and `.htaccess`. No health check endpoint, no graceful shutdown, no multi-stage build, no non-root user. |
| 4 | `docker-compose.yml` | Defines two services: `mysql` (mysql:8.0 with hardcoded credentials) and `monolith` (PHP app). Health checks configured. Dev/prod MySQL version mismatch (8.0 vs 8.4.8). Hardcoded database passwords in environment variables. |
| 5 | `deploy.sh` | Manual deployment script: `docker-compose build` + `docker-compose up -d` + health check curl. No CI/CD integration, no rollback, no staged deployment, no test execution. |
| 6 | `.htaccess` | Apache URL rewrite rules routing all requests to `index.php`. Enables clean URL patterns for the PHP router. |
| 7 | `.gitignore` | Excludes database files, logs, OS files, and IDE configs. No evidence of test directories, documentation, or additional configuration files being ignored. |
