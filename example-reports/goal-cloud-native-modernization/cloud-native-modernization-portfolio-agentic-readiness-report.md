# Portfolio Agentic Readiness Assessment Report
**Portfolio**: cloud-native-modernization
**Assessment Goal**: cloud-native-modernization
**Goal Context**: Decomposing monoliths into containerized microservices on EKS with GitOps deployment
**Services Assessed**: 3
**Assessment Date**: 2026-03-17
**Assessed by**: AWS Transform Custom — Portfolio Agentic Readiness Assessment

---

## Table of Contents

1. Executive Dashboard
2. Portfolio Readiness Overview
3. Service Dependency Map
4. Cross-Cutting Concerns
5. Portfolio Modernization Roadmap
   - Phase 0 — Cross-Cutting Foundation (Mo 0–1)
   - Phase 1 — Containerize & Automate (Mo 1–2)
   - Phase 2 — Decompose & Decouple (Mo 2–4)
   - Phase 3 — Optimize & Scale (Mo 4–6+)
6. AWS Modernization Pathways
7. AWS Programs & Engagement Recommendations
8. Integration Opportunities
9. Resource Allocation Recommendations
10. Recommended Self-Paced Learning Materials
11. Risk Analysis
12. Service-by-Service Summary
13. Appendix: Assessment Inventory

---

## Executive Dashboard

This portfolio of 3 services — an EKS SaaS GitOps platform, a legacy Java Spring Boot monolith, and a PHP e-commerce monolith — is assessed against the goal of **decomposing monoliths into containerized microservices on EKS with GitOps deployment**. The portfolio readiness score of **1.5 / 4.0** reflects significant gaps across all categories, with Operations & Observability (1.0/4.0) and Security (1.3/4.0) as the weakest areas. No service is agent-ready, and 67% of the portfolio scores below 1.5 ("Not Ready"). The two monoliths (unishop-monolith at 1.2/4.0 and local-monolith at 1.4/4.0) require foundational work — containerization, IaC, CI/CD, and observability — before any microservices decomposition can begin.

The **eks-saas-gitops** platform (1.9/4.0) is the strongest service and serves as the foundation that both monoliths will deploy onto. Its EKS cluster, Terraform IaC, Flux CD GitOps pipeline, and microservices architecture provide reusable patterns for the rest of the portfolio. However, it has critical security gaps (AdminAccess IAM policies) and zero testing or observability that must be resolved first. The dependency structure is clear: eks-saas-gitops must be hardened in Phase 1 before either monolith migrates to it in Phase 2.

The modernization effort is **High** across the board. Key blockers include: absence of CI/CD pipelines in 2 of 3 services, zero observability across the entire portfolio, and tightly-coupled monolith architectures in both application services. The estimated timeline is **6+ months** across 4 phases, with the first month dedicated to cross-cutting foundations (shared CI/CD patterns, observability stack, ECR registry, Helm chart templates) before service-level work begins.

### Portfolio Readiness Score: 1.5 / 4.0

| Category | Portfolio Score | Distribution | Status |
|----------|----------------|--------------|--------|
| Infrastructure & Platform | 2.0 / 4.0 | ✅ 0 services, 🟡 2 services, 🟠 0 services, ❌ 1 service | 🟠 |
| Application Architecture | 1.5 / 4.0 | ✅ 0 services, 🟡 1 service, 🟠 0 services, ❌ 2 services | ❌ |
| Data Foundations | 1.8 / 4.0 | ✅ 0 services, 🟡 0 services, 🟠 3 services, ❌ 0 services | 🟠 |
| Identity, Security & Governance | 1.3 / 4.0 | ✅ 0 services, 🟡 0 services, 🟠 2 services, ❌ 1 service | ❌ |
| Operations & Observability | 1.0 / 4.0 | ✅ 0 services, 🟡 0 services, 🟠 0 services, ❌ 3 services | ❌ |

**Readiness Distribution:**
- ✅ Agent-Ready (3.5-4.0): 0 services (0%)
- 🟡 Partial (2.5-3.4): 0 services (0%)
- 🟠 Needs Work (1.5-2.4): 1 service (33%) — eks-saas-gitops
- ❌ Not Ready (< 1.5): 2 services (67%) — unishop-monolith, local-monolith

### Key Metrics

| Metric | Value | Insight |
|--------|-------|---------|
| Total Services | 3 | 1 EKS platform (monorepo) + 2 monolith applications |
| Average Readiness Score | 1.5 / 4.0 | All services below "Partial" threshold; significant modernization required |
| Services Ready for Cloud-Native | 0 (0%) | No service meets the 3.5+ threshold for production-grade cloud-native readiness |
| Critical Dependencies | 1 | eks-saas-gitops is the single foundation service; blast radius = 100% |
| Shared Infrastructure Gaps | 5+ | CI/CD, observability, API auth, rate limiting, secrets management affect 2-3 services |
| Estimated Modernization Effort | High | All services below 2.0; structural changes needed across infra, app, and ops |
| Expected Timeline | 6+ months | 4 phases with 2 parallel tracks after Phase 1 foundation work |

---

## Portfolio Readiness Overview

### Technology Stack Summary

**Programming Languages:**
- Python 3.9 (Flask): 1 service (33%) — eks-saas-gitops
- Java 8 (Spring Boot 2.1.x): 1 service (33%) — unishop-monolith
- PHP 8.2: 1 service (33%) — local-monolith

**Database Engines:**
- DynamoDB (managed, NoSQL): 1 service (33%) — eks-saas-gitops
- MySQL (self-managed or unknown): 1 service (33%) — unishop-monolith
- MySQL 8.4 (RDS managed): 1 service (33%) — local-monolith

**Compute Patterns:**
- EKS with Karpenter: 1 service (33%) — eks-saas-gitops
- EC2 (bare): 1 service (33%) — unishop-monolith
- App Runner (managed containers): 1 service (33%) — local-monolith

**IaC Maturity:**
- Terraform (comprehensive): 1 service (33%) — eks-saas-gitops
- CloudFormation (basic): 1 service (33%) — local-monolith
- None: 1 service (33%) — unishop-monolith

**Deployment Maturity:**
- Flux CD GitOps (CD only, no CI): 1 service (33%) — eks-saas-gitops
- Manual deployment: 2 services (67%) — unishop-monolith, local-monolith

### Common Strengths

1. **Cloud-native target architecture exists (eks-saas-gitops)**: The EKS platform with Terraform, Flux CD, Helm charts, Karpenter, and SQS messaging provides a proven reference architecture and reusable patterns for the monolith migrations.
2. **Managed databases partially adopted**: 2 of 3 services use managed data stores (DynamoDB, RDS MySQL), reducing operational overhead for data layer management.
3. **No stored procedures or proprietary SQL**: All 3 services keep business logic in the application layer, making database migration straightforward. No PL/SQL, T-SQL, or triggers to refactor.
4. **Container foundation exists**: eks-saas-gitops runs fully on EKS, local-monolith has a Dockerfile and App Runner deployment. Only unishop-monolith is fully un-containerized.
5. **Well-decomposed microservices pattern available**: eks-saas-gitops demonstrates producer-consumer-payments microservices with per-service IRSA, Helm releases, and independent deployments — a template for decomposing the monoliths.

### Common Gaps

1. **No CI/CD pipelines in 2 of 3 services**: Only eks-saas-gitops has CD (Flux CD), but even it lacks CI (build/test). Unishop and local-monolith have zero automation.
2. **Zero observability across entire portfolio**: All 3 services score 1/4 on distributed tracing (OPS-Q1), structured logging (OPS-Q2), and anomaly detection (OPS-Q8). No X-Ray, OpenTelemetry, or structured logging anywhere.
3. **Zero testing across entire portfolio**: No test files exist in any repository. All 3 services score 1/4 on integration testing (OPS-Q10).
4. **Monolith architecture in application services**: Both unishop-monolith and local-monolith score 1/4 on monolith decomposition (APP-Q4). Single-file/single-JAR architectures with shared databases.
5. **No API documentation anywhere**: All 3 services score 1/4 on API documentation (APP-Q2). No OpenAPI specs, no Swagger annotations, no API discovery.
6. **Critical security gaps**: All 3 services lack API authentication, rate limiting, and PII redaction. eks-saas-gitops has AdminAccess IAM policies. Unishop has hardcoded credentials.
7. **No deployment strategies**: All 3 services score 1/4 on deployment strategy (OPS-Q9). No canary, blue-green, or progressive delivery anywhere.

---

## Service Dependency Map

### High-Level Architecture

The portfolio follows a hub-and-spoke topology centered on **eks-saas-gitops** as the shared EKS platform. Both monolith applications (unishop-monolith and local-monolith) will be containerized and deployed onto this EKS cluster. There are no direct dependencies between the two monoliths — they operate as independent workloads sharing the same container orchestration infrastructure.

```
  unishop-monolith ──────┐
  (Java Spring Boot)     │ shared_infra (EKS cluster)
                         ▼
                   eks-saas-gitops
                   (EKS + Terraform + Flux CD)
                         ▲
  local-monolith ────────┘
  (PHP e-commerce)       shared_infra (EKS cluster)
```

### Service Dependency Matrix

| Service | Depends On | Depended On By | Coupling Score | Fan-In | Fan-Out | Blast Radius | Priority |
|---------|------------|----------------|----------------|--------|---------|--------------|----------|
| eks-saas-gitops | None | unishop-monolith, local-monolith | — | 2 | 0 | 100% | P0 |
| unishop-monolith | eks-saas-gitops | None | Low | 0 | 1 | 0% | P0 |
| local-monolith | eks-saas-gitops | None | Low | 0 | 1 | 0% | P1 |

**Coupling Score Definitions:**
- **Low**: Shared infrastructure only (EKS cluster, ECR, Flux CD) — no shared databases, no synchronous API calls between services

**Priority Definitions:**
- **P0**: eks-saas-gitops (foundation service, highest fan-in), unishop-monolith (critical application per config)
- **P1**: local-monolith (secondary priority per config)

### Critical Path Analysis

1. **Foundation Services** (must be modernized first):
   - **eks-saas-gitops**: Both monoliths will deploy onto this EKS cluster. It must be hardened (security fixes, observability, testing) before accepting production workloads from the monolith migrations.

2. **Dependent Services** (can be modernized after foundation):
   - **unishop-monolith** (P0): Depends on eks-saas-gitops for EKS deployment target. Containerization and EKS migration require the platform to be ready.
   - **local-monolith** (P1): Depends on eks-saas-gitops for EKS deployment target. Migration from App Runner to EKS requires the platform to be ready.

3. **Parallel Tracks** (no mutual dependency):
   - unishop-monolith and local-monolith can be modernized concurrently in Phase 2 since they have no dependencies on each other.

### Circular Dependency Detection

No circular dependencies detected (Tarjan's SCC analysis). The dependency graph is a directed acyclic graph (DAG) with eks-saas-gitops as the root node.

### Integration Points

**Shared Infrastructure:**
- EKS Cluster: All 3 services will run on the eks-saas-gitops EKS cluster (v1.32, Karpenter autoscaling)
- ECR: Shared container image registry for all service Docker images
- Flux CD: Shared GitOps deployment pipeline for continuous delivery to EKS
- Helm Charts: eks-saas-gitops provides reusable Helm chart templates for tenant workloads

**Potential Future Integrations:**
- SQS messaging (eks-saas-gitops already uses SQS for producer-consumer patterns; both monoliths will need async messaging during decomposition)
- Shared observability stack (ADOT Collector, CloudWatch, X-Ray) deployed once on EKS, consumed by all services
- Unified API Gateway / ALB Ingress Controller for routing to all microservices

---

## Cross-Cutting Concerns

> Cross-cutting concerns are gaps that appear across multiple services. They are classified into four tiers based on severity and relationship to the portfolio's assessment goal (`cloud-native-modernization`).

### 🚨 Foundational Blockers

> These gaps block all modernization efforts, not just `cloud-native-modernization`.
> Address these first — nothing else matters until these are resolved.

1. **INF-Q6: CI/CD Pipeline** — 2 of 3 services score < 2
   - **Impact**: Without CI/CD, no automated build, test, or deployment is possible. Manual deployments cannot support the velocity needed for microservices on EKS. GitOps (a stated preference) requires CI pipelines to build images and push to ECR.
   - **Affected services**: unishop-monolith (1/4), local-monolith (1/4)
   - **Recommendation**: Establish a portfolio-standard CI pipeline template (GitHub Actions → build → test → Docker → ECR push). eks-saas-gitops's Flux CD provides the CD side; replicate this pattern across all services.

2. **OPS-Q1: Distributed Tracing** — 3 of 3 services score < 2
   - **Impact**: Zero observability across the entire portfolio. As services are decomposed and deployed on EKS, cross-service request tracing is essential for debugging. Without tracing, the portfolio becomes an opaque, unmaintainable distributed system.
   - **Affected services**: eks-saas-gitops (1/4), unishop-monolith (1/4), local-monolith (1/4)
   - **Recommendation**: Deploy a shared ADOT Collector as an EKS DaemonSet managed by Flux CD. Add OpenTelemetry auto-instrumentation to all services (Python, Java, PHP). Export traces to AWS X-Ray.

3. **APP-Q8 + SEC-Q5: Rate Limiting** — 3 of 3 services score < 2 on both APP-Q8 and SEC-Q5
   - **Impact**: No rate limiting at any layer across the portfolio. Services are vulnerable to abuse, DDoS, and resource exhaustion. This is a prerequisite for safe production deployment on EKS.
   - **Affected services**: eks-saas-gitops (1/4), unishop-monolith (1/4), local-monolith (1/4)
   - **Recommendation**: Deploy AWS WAF with rate-based rules on the shared ALB Ingress Controller. Add per-service rate limiting middleware. Configure per-tenant/client quotas at the API Gateway level.

### ⚠️ Prerequisites for `cloud-native-modernization`

> These gaps specifically block your path to `cloud-native-modernization`.
> They aren't the goal itself, but you can't get there without them.

1. **INF-Q5: Infrastructure as Code** — 1 of 3 services score = 2 (exists but weak: N/A — only 1 service at score 1, 1 at score 3, 1 at score 4)
   - *Note*: INF-Q5 scores are: eks-saas-gitops (4/4), unishop-monolith (1/4), local-monolith (3/4). Only 1 service scores < 2, which does not meet the 2+ service threshold for Tier 1. However, unishop-monolith's score of 1 (zero IaC) is a critical individual blocker. The local-monolith scores 3 (CloudFormation exists but needs Terraform migration per preferences).
   - **Impact on goal**: GitOps deployment requires all infrastructure defined as code. Without IaC for unishop-monolith, EKS deployment is impossible.
   - **Affected services**: unishop-monolith (1/4 — zero IaC)
   - **Recommendation**: Create Terraform modules for unishop-monolith's infrastructure (VPC, EKS namespace, Aurora MySQL, ECR). Migrate local-monolith from CloudFormation to Terraform per portfolio preferences.

### 🎯 Goal Deliverables — What You're Here to Build

> These are the capabilities your `cloud-native-modernization` initiative will deliver.
> Low scores here confirm the need for the initiative, not additional blockers.
> Your individual assessment reports detail the current state and roadmap for each.

1. **APP-Q4: Monolith Decomposition** — 2 of 3 services score < 3
   - **Current state**: Both application services are tightly-coupled monoliths. unishop-monolith is a single Spring Boot JAR with 3 MySQL tables in a shared schema. local-monolith is a single `index.php` file (~2000+ lines) with 9 shared MySQL tables. eks-saas-gitops is already decomposed (4/4).
   - **Affected services**: unishop-monolith (1/4), local-monolith (1/4)
   - **Roadmap reference**: Phase 2 (Decompose & Decouple) — Strangler Fig pattern with domain modeling, service extraction, and database decomposition.

2. **APP-Q3: Async Communication** — 2 of 3 services score < 3
   - **Current state**: Both monoliths use 100% synchronous communication. Unishop has synchronous ResponseEntity controllers. Local-monolith has synchronous PHP request handlers. eks-saas-gitops has mature async patterns with SQS (3/4).
   - **Affected services**: unishop-monolith (1/4), local-monolith (1/4)
   - **Roadmap reference**: Phase 2 — Introduce SQS/EventBridge for inter-service communication as services are extracted.

3. **INF-Q1: Managed Compute / Container Orchestration** — 1 of 3 services scores < 3 (unishop-monolith on raw EC2)
   - **Current state**: eks-saas-gitops (3/4, EKS), local-monolith (3/4, App Runner), unishop-monolith (1/4, raw EC2). All will converge to EKS.
   - **Affected services**: unishop-monolith (1/4)
   - **Roadmap reference**: Phase 1 (Containerize) for unishop-monolith; Phase 2 for local-monolith's App Runner → EKS migration.

4. **OPS-Q9: Deployment Strategy (Canary/Blue-Green)** — 3 of 3 services score < 3
   - **Current state**: All services deploy straight-to-production. eks-saas-gitops uses Flux CD reconciliation with no canary. Both monoliths use manual deployment.
   - **Affected services**: eks-saas-gitops (1/4), unishop-monolith (1/4), local-monolith (1/4)
   - **Roadmap reference**: Phase 3 (Optimize & Scale) — Flagger + Flux for canary deployments, Argo Rollouts for progressive delivery.

### 💡 General Improvement Opportunities

> These gaps are important but do not directly block `cloud-native-modernization`.
> Address them as capacity allows or in parallel with goal work.

1. **APP-Q2: API Documentation** — 3 of 3 services score < 3
   - **Impact**: No OpenAPI specifications exist anywhere. API discovery is impossible without reading source code. This hinders service contract definition during decomposition.
   - **Affected services**: eks-saas-gitops (1/4), unishop-monolith (1/4), local-monolith (1/4)
   - **Recommendation**: Generate OpenAPI specs for each service. Use flask-smorest (Python), SpringDoc (Java), and swagger-php (PHP). Publish via Swagger UI.

2. **OPS-Q10: Integration Testing** — 3 of 3 services score < 3
   - **Impact**: Zero test files exist in any repository. Every code change and service extraction is untested. Decomposition without tests is high risk.
   - **Affected services**: eks-saas-gitops (1/4), unishop-monolith (1/4), local-monolith (1/4)
   - **Recommendation**: Establish testing before decomposition begins. Add pytest (Python), Spring Boot Test (Java), PHPUnit/Pest (PHP) with CI pipeline integration.

3. **SEC-Q9: API Authentication** — 3 of 3 services score < 3
   - **Impact**: All APIs are unauthenticated or use session-based auth not suitable for microservices. Machine-to-machine auth is absent.
   - **Affected services**: eks-saas-gitops (1/4), unishop-monolith (1/4), local-monolith (2/4)
   - **Recommendation**: Deploy Amazon Cognito as the portfolio-wide identity provider. Implement JWT validation in each service. Use IRSA for service-to-AWS auth on EKS.

4. **SEC-Q1: Secret Management** — 3 of 3 services score < 3
   - **Impact**: Hardcoded credentials in unishop-monolith and local-monolith. Git tokens exposed in eks-saas-gitops. Critical security vulnerability.
   - **Affected services**: eks-saas-gitops (2/4), unishop-monolith (1/4), local-monolith (1/4)
   - **Recommendation**: Migrate all secrets to AWS Secrets Manager. Deploy External Secrets Operator on EKS for Kubernetes secret injection.

5. **APP-Q7: Idempotency** — 3 of 3 services score < 3
   - **Impact**: No idempotency patterns. Duplicate requests create duplicate records. Critical for microservices with network retries.
   - **Affected services**: eks-saas-gitops (1/4), unishop-monolith (1/4), local-monolith (1/4)
   - **Recommendation**: Implement idempotency keys for write operations in all services before decomposition.

6. **APP-Q9: Resilience Patterns** — 3 of 3 services score < 3
   - **Impact**: No circuit breakers, retries, or timeouts. Exception handling swallows errors (`e.printStackTrace()`, `die()`). Microservices amplify failure modes.
   - **Affected services**: eks-saas-gitops (1/4), unishop-monolith (1/4), local-monolith (1/4)
   - **Recommendation**: Add resilience libraries (tenacity for Python, Resilience4j for Java) before decomposition. Implement circuit breaker + retry + timeout for all external calls.

7. **SEC-Q4: Audit Logging** — 3 of 3 services score < 3
   - **Impact**: No CloudTrail configuration. No application-level audit logging. No immutable log storage.
   - **Affected services**: eks-saas-gitops (1/4), unishop-monolith (1/4), local-monolith (1/4)
   - **Recommendation**: Enable CloudTrail with log file validation. Enable EKS control plane logging. Implement structured audit logging in application code.

8. **SEC-Q10: Centralized Identity** — 3 of 3 services score < 3
   - **Impact**: No centralized identity provider. Each service manages authentication separately (sessions, custom login, no auth).
   - **Affected services**: eks-saas-gitops (1/4), unishop-monolith (1/4), local-monolith (1/4)
   - **Recommendation**: Deploy Amazon Cognito as the portfolio-wide identity provider. Implement OIDC federation for SSO.

### Per-Category Analysis

### Infrastructure & Platform

**Portfolio Score: 2.0 / 4.0**

The infrastructure category shows the widest variance across services. eks-saas-gitops (3.1/4.0) has comprehensive Terraform, EKS, and managed services, while unishop-monolith (1.0/4.0) has zero IaC, zero containerization, and no managed infrastructure. local-monolith (1.9/4.0) sits in between with App Runner, RDS, and CloudFormation IaC.

**Common Patterns:**
- EKS as the target compute platform: present in 1 service (eks-saas-gitops), target for all 3
- Managed databases: 2 of 3 services (DynamoDB, RDS MySQL)
- SQS messaging: 1 service (eks-saas-gitops) — template for the others

**Critical Gaps:**
1. **INF-Q6 (CI/CD)**: 2 services score 1/4. Foundational blocker addressed in Phase 0.
2. **INF-Q8 (Real-time Streaming)**: All 3 services score 1/4. No Kinesis/MSK — lower priority for cloud-native goal.

### Application Architecture

**Portfolio Score: 1.5 / 4.0**

This is the category most directly impacted by the cloud-native modernization goal. eks-saas-gitops (2.2/4.0) has microservices but lacks API docs, resilience, and testing. Both monoliths (1.2/4.0 each) are tightly coupled with no async patterns.

**Critical Gaps:**
1. **APP-Q4 (Monolith Decomposition)**: 2 services at 1/4 — the core deliverable of this initiative
2. **APP-Q3 (Async Communication)**: 2 services at 1/4 — required for decoupled microservices

### Data Foundations

**Portfolio Score: 1.8 / 4.0**

Data patterns are relatively uniform across services with most gaps in AI/agent capabilities (not priority for cloud-native goal). The strongest area is schema simplicity — no stored procedures or triggers.

**Common Patterns:**
- Clean schema with no stored procedures: 3 services (DATA-Q11 scores: 4, 3, 4)
- Minimal data source sprawl: 3 services (DATA-Q4 scores: 3, 4, 3)

**Critical Gaps:**
1. **DATA-Q5 (Data Access Pattern)**: All services at 1-2/4. Direct DB calls without abstraction layers make service extraction difficult.

### Identity, Security & Governance

**Portfolio Score: 1.3 / 4.0**

Security is consistently weak across the portfolio with no service scoring above 1.4/4.0 overall. The most critical issues are API authentication, secret management, and IAM policies.

**Critical Gaps:**
1. **SEC-Q9 (API Authentication)**: All 3 services at 1-2/4. Unauthenticated APIs across the portfolio.
2. **SEC-Q1 (Secret Management)**: All 3 services at 1-2/4. Hardcoded credentials in multiple services.

### Operations & Observability

**Portfolio Score: 1.0 / 4.0**

This is the weakest category across the entire portfolio. All 3 services score 1.0-1.1/4.0. Nearly every operations criterion scores 1/4 across all services — representing a complete absence of operational maturity.

**Critical Gaps:**
1. **OPS-Q1 through OPS-Q12**: Nearly all criteria score 1/4 across all 3 services. The portfolio has zero observability, zero testing, zero deployment strategies, and zero incident response.
2. **This must be addressed in Phase 0 before any decomposition work begins.**

---

## Portfolio Modernization Roadmap

### Sequencing Principles

1. **Foundation First**: Shared infrastructure and platform capabilities before service-specific work
2. **Dependency Order**: eks-saas-gitops (foundation) before unishop-monolith and local-monolith (dependents)
3. **Risk Mitigation**: Harden the EKS platform before deploying monolith workloads onto it
4. **Parallel Tracks**: unishop-monolith and local-monolith can be modernized concurrently (no mutual dependency)
5. **Quick Wins**: CI/CD pipeline templates and observability stack deliver immediate value to all services
6. **Goal Alignment**: Within each phase, cloud-native priority activities (APP-Q4, INF-Q1, INF-Q5, INF-Q6, APP-Q3, OPS-Q9) are listed first

### Phase 0 — Cross-Cutting Foundation (Mo 0–1)

**Objective**: Establish shared capabilities and organizational readiness across the portfolio

**Shared Infrastructure:**
- Deploy shared ADOT Collector as EKS DaemonSet (benefits all 3 services)
- Set up shared ECR repositories for all service Docker images
- Establish CI pipeline template (GitHub Actions → build → test → Docker → ECR push)
- Deploy External Secrets Operator on EKS for centralized secret management
- Deploy AWS WAF with rate-based rules on the shared ALB Ingress Controller
- Enable EKS control plane logging (`api`, `audit`, `authenticator`)

**Platform Capabilities:**
- Establish Helm chart template library derived from eks-saas-gitops patterns
- Set up Flux CD namespaces and GitOps repository structure for all services
- Deploy Prometheus/Grafana stack (Kubecost already present) for metrics across all services
- Establish CloudWatch Log Groups with retention policies for all services

**Organizational Enablers:**
- Training: Terraform/IaC, Docker/EKS containers, GitOps (Flux CD/ArgoCD), Helm charts
- Tooling: Standardize on Terraform for all IaC, GitHub Actions for CI, Flux CD for CD
- Standards: Define API response envelope standard, structured logging format (JSON with correlation IDs), Helm chart conventions

**Expected Outcomes:**
- All services can push Docker images to ECR via CI pipeline
- Observability stack ready to receive traces and logs from all services
- Secrets migrated from hardcoded values to Secrets Manager
- Team upskilled on EKS, Terraform, and GitOps

**Estimated Effort**: High

### Phase 1 — Containerize & Automate (Mo 1–2)

**Objective**: Harden the foundation EKS platform and containerize the monoliths. Goal-priority activities listed first.

**Services in Scope:**

1. **eks-saas-gitops** (P0, Score: 1.9/4.0)
   - Current State: EKS cluster with Terraform, Flux CD, microservices architecture. Critical security gaps (AdminAccess IAM) and zero observability/testing.
   - Target State: Production-hardened EKS platform with scoped IAM, observability, and CI/testing pipeline.
   - Key Activities (goal-priority activities first):
     - Add CI pipeline for building/testing container images (INF-Q6 improvement)
     - Add OpenTelemetry SDK to Flask microservices + ADOT Collector (OPS-Q9/OPS-Q1 foundation)
     - Scope IAM policies — replace AdminAccess on argo-workflows-irsa and tf-controller-irsa
     - Add pytest integration tests for producer→SQS→consumer→DynamoDB flow (OPS-Q10)
     - Implement structured JSON logging with correlation IDs (OPS-Q2)
     - Enable HPA for tenant microservices (INF-Q10)
   - Dependencies: None (foundation service)
   - Blocks: unishop-monolith, local-monolith
   - Estimated Effort: High

**Cross-Service Activities:**
- Create Dockerfile for unishop-monolith (multi-stage Gradle → JRE 17 build)
- Create Helm charts for both monoliths (liveness/readiness probes, IRSA, Flux CD integration)
- Establish Terraform modules for Aurora MySQL (target for unishop-monolith migration)
- Migrate unishop-monolith secrets from hardcoded application.properties to Secrets Manager

**Expected Outcomes:**
- eks-saas-gitops platform hardened with scoped IAM and observability
- Both monoliths containerized and ready for EKS deployment
- CI pipelines operational for all 3 services
- Aurora MySQL cluster provisioned for unishop-monolith

**Estimated Effort**: High

### Phase 2 — Decompose & Decouple (Mo 2–4)

**Objective**: Migrate monoliths to EKS and begin service extraction. Goal-priority activities listed first.

**Services in Scope:**

1. **unishop-monolith** (P0, Score: 1.2/4.0)
   - Current State: Java 8 Spring Boot monolith on EC2, no IaC, no CI/CD, self-managed MySQL.
   - Target State: Containerized on EKS with Terraform IaC, GitOps deployment, Aurora MySQL, and initial service extraction begun.
   - Key Activities (goal-priority activities first):
     - Deploy containerized monolith to EKS via Helm + Flux CD (APP-Q4/INF-Q1)
     - Begin Strangler Fig decomposition — extract User service first (APP-Q4)
     - Introduce SQS/EventBridge for basket-catalog async communication (APP-Q3)
     - Create Terraform modules for service infrastructure (INF-Q5)
     - Migrate MySQL to Aurora MySQL using DMS (INF-Q2)
     - Add OpenTelemetry Java auto-instrumentation (OPS-Q1)
     - Add integration tests for critical API endpoints (OPS-Q10)
     - Implement JWT authentication with Cognito (SEC-Q9)
   - Dependencies: eks-saas-gitops (Phase 1)
   - Blocks: None
   - Estimated Effort: High

2. **local-monolith** (P1, Score: 1.4/4.0)
   - Current State: PHP monolith on App Runner, CloudFormation IaC, RDS MySQL, single index.php.
   - Target State: Containerized on EKS with Terraform IaC, GitOps deployment, and domain modeling completed for future decomposition.
   - Key Activities (goal-priority activities first):
     - Migrate from App Runner to EKS via Helm + Flux CD (INF-Q1)
     - Conduct domain modeling workshop — identify bounded contexts (APP-Q4 preparation)
     - Introduce EventBridge for fulfillment workflow async events (APP-Q3)
     - Migrate IaC from CloudFormation to Terraform (INF-Q5)
     - Upgrade RDS MySQL to Aurora MySQL (INF-Q2)
     - Add OpenTelemetry PHP auto-instrumentation (OPS-Q1)
     - Add API integration tests with PHPUnit/Newman (OPS-Q10)
     - Replace PHP sessions with JWT authentication via Cognito (SEC-Q3)
   - Dependencies: eks-saas-gitops (Phase 1)
   - Blocks: None
   - Estimated Effort: High

**Parallel Tracks:**
- unishop-monolith and local-monolith can be modernized concurrently by separate teams (no mutual dependency)

**Expected Outcomes:**
- Both monoliths running on EKS with GitOps deployment
- Aurora MySQL operational for both applications
- User service extracted from unishop-monolith (first microservice)
- Domain modeling complete for local-monolith decomposition
- Observability operational across all services

**Estimated Effort**: High

### Phase 3 — Optimize & Scale (Mo 4–6+)

**Objective**: Complete microservices decomposition, implement advanced deployment strategies, and optimize cross-service workflows. Goal-priority activities listed first.

**Activities:**
- Complete Strangler Fig decomposition for both monoliths (APP-Q4):
  - unishop-monolith: Extract Catalog and Basket services
  - local-monolith: Extract Fulfillment, Users, and Inventory services
- Implement canary/blue-green deployments with Flagger + Flux CD (OPS-Q9)
- Implement database-per-service pattern for all extracted microservices
- Deploy unified API Gateway with per-service routing, versioning, and throttling (APP-Q11, INF-Q7)
- Implement distributed tracing correlation across all services (OPS-Q1 maturity)
- Add resilience patterns (circuit breaker, retry, timeout) to all inter-service calls (APP-Q9)
- Generate OpenAPI specs for all microservices (APP-Q2)
- Define and monitor SLOs for critical paths across all services (OPS-Q4)
- Implement anomaly detection with CloudWatch alarms (OPS-Q8)
- Continuous optimization and advanced EKS features (auto-scaling, multi-AZ, service mesh)

**Expected Outcomes:**
- All monoliths fully decomposed into independently deployable microservices on EKS
- Progressive delivery (canary) operational for all services
- End-to-end observability with tracing, structured logging, and SLO monitoring
- Production-grade security with Cognito JWT, WAF, and scoped IAM
- Each microservice has its own CI/CD pipeline, Helm chart, database, and API docs

**Estimated Effort**: High

### Total Portfolio Effort

**Total Estimated Effort**: High
**Expected Timeline**: 6+ months (with 2 parallel tracks in Phase 2)

---

## AWS Modernization Pathways

Based on the portfolio-wide assessment findings, the following AWS Modernization Pathways have been identified for each service. The AWS Modernization Pathways framework recognizes there is no "one-size-fits-all" approach — a customer portfolio may be divided into multiple pathways depending on workloads and priorities, and these pathways can be executed in parallel.

### Portfolio Pathway Summary

| Pathway | Services Triggered | % of Portfolio | Priority | Est. Effort |
|---------|--------------------|----------------|----------|-------------|
| Move to Cloud Native | 2 services (unishop-monolith, local-monolith) | 67% | High | High |
| Move to Containers | 1 service (unishop-monolith) | 33% | Medium | Medium |
| Move to Open Source | 0 services | 0% | Low | — |
| Move to Managed Databases | 1 service (unishop-monolith) | 33% | Medium | Medium |
| Move to Managed Analytics | 0 services | 0% | Low | — |
| Move to Modern DevOps | 3 services | 100% | High | High |
| Move to AI | 3 services | 100% | Low | High |

### Per-Service Pathway Assignment

| Service | Cloud Native | Containers | Open Source | Managed DB | Managed Analytics | Modern DevOps | Move to AI |
|---------|-------------|------------|-------------|------------|-------------------|---------------|------------|
| eks-saas-gitops | — | — | — | — | — | ✅ | ✅ |
| unishop-monolith | ✅ | ✅ | — | ✅ | — | ✅ | ✅ |
| local-monolith | ✅ | — | — | — | — | ✅ | ✅ |

### Portfolio Pathway Aggregation

This table shows exactly which repositories fall into each pathway status, providing a single at-a-glance view of pathway coverage across the portfolio. Each repo appears in exactly one column per pathway row. Goal Alignment is based on the portfolio-level goal (`cloud-native-modernization`) using the goal-pathway alignment mapping.

| Pathway | Triggered | Not Triggered | Not Applicable | Goal Alignment |
|---------|-----------|---------------|----------------|---------------|
| Move to Cloud Native | unishop-monolith, local-monolith | eks-saas-gitops | — | High |
| Move to Containers | unishop-monolith | eks-saas-gitops, local-monolith | — | High |
| Move to Open Source | — | eks-saas-gitops, unishop-monolith, local-monolith | — | Medium |
| Move to Managed Databases | unishop-monolith | eks-saas-gitops, local-monolith | — | Medium |
| Move to Managed Analytics | — | eks-saas-gitops, unishop-monolith, local-monolith | — | Low |
| Move to Modern DevOps | eks-saas-gitops, unishop-monolith, local-monolith | — | — | High |
| Move to AI | eks-saas-gitops, unishop-monolith, local-monolith | — | — | Low |

### Pathway Dependencies and Parallel Execution

**Sequential Dependencies:**
- **Move to Containers** should precede **Move to Cloud Native** because containerization is a prerequisite for Kubernetes-based microservices decomposition
- **Move to Modern DevOps** should precede all other pathways because CI/CD pipelines, testing, and observability are needed to safely execute any modernization
- **Move to Managed Databases** should complete before service extraction in **Move to Cloud Native** to avoid managing self-managed databases during decomposition

**Parallel Execution Tracks:**
- **Track 1 (Foundation)**: Move to Modern DevOps — starts immediately across all services (Phase 0-1)
- **Track 2 (Infrastructure)**: Move to Containers + Move to Managed Databases — runs in parallel with Track 1 for unishop-monolith (Phase 1-2)
- **Track 3 (Decomposition)**: Move to Cloud Native — begins after Tracks 1 and 2 establish foundations (Phase 2-3)
- **Track 4 (Future)**: Move to AI — lowest priority for cloud-native goal, deferred to Phase 3+

### Pathway Details

#### Move to Cloud Native

- **Services Affected**: unishop-monolith, local-monolith (2 total)
- **Portfolio Priority**: High
- **Common Trigger Criteria**:
  - APP-Q4 < 4: 2 services (both monoliths score 1/4 — tightly-coupled single-deployment architectures)
  - APP-Q3 < 3: 2 services (both monoliths score 1/4 — 100% synchronous communication)
  - INF-Q1 < 3: 1 service (unishop-monolith at 1/4 — raw EC2)
  - APP-Q10 < 3: 2 services (both monoliths score 1/4 — no async processing)
- **Representative AWS Services**: EKS, Fargate, API Gateway, EventBridge, Step Functions, SQS
- **Key Activities**:
  1. Conduct domain modeling workshops for both monoliths to identify bounded contexts
  2. Use Strangler Fig pattern to incrementally extract services, starting with least-coupled domains
  3. Introduce EventBridge/SQS for async inter-service communication
  4. Implement API Gateway routing between monolith and extracted services
- **Cross-Service Synergies**: eks-saas-gitops's microservices architecture (producer-consumer-payments) provides proven patterns for decomposition. Its Helm charts, IRSA roles, and SQS patterns can be templated for newly extracted services.
- **Estimated Effort**: High across 2 services
- **Roadmap Phase Alignment**: Phase 2 (Decompose & Decouple) and Phase 3 (Optimize & Scale)
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native (Containers and Serverless)

#### Move to Containers

- **Services Affected**: unishop-monolith (1 total)
- **Portfolio Priority**: Medium
- **Common Trigger Criteria**:
  - INF-Q1 < 3: 1 service (unishop-monolith at 1/4 — running on raw EC2 with no containerization)
  - No Dockerfile found in unishop-monolith (commented-out Docker config in build.gradle)
- **Representative AWS Services**: EKS, Fargate, ECR, Docker
- **Key Activities**:
  1. Create multi-stage Dockerfile for Spring Boot application (Gradle build → JRE 17 runtime)
  2. Set up ECR repository and push initial container image
  3. Create Helm chart with liveness/readiness probes and IRSA
  4. Deploy to EKS with Fargate profiles
- **Cross-Service Synergies**: eks-saas-gitops and local-monolith already have container foundations. Helm chart patterns from eks-saas-gitops apply directly.
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 1 (Containerize & Automate)
- **Relevant Learning Materials**: Module 3 — Move to Containers with Amazon ECS and EKS

#### Move to Managed Databases

- **Services Affected**: unishop-monolith (1 total)
- **Portfolio Priority**: Medium
- **Common Trigger Criteria**:
  - INF-Q2 < 4: 1 service (unishop-monolith at 1/4 — self-managed/unknown MySQL)
  - DATA-Q10 < 4: 1 service (unishop-monolith at 1/4 — MySQL engine version unknown and unpinned)
- **Representative AWS Services**: Aurora MySQL, DMS, Secrets Manager
- **Key Activities**:
  1. Create Aurora MySQL cluster in Terraform with engine version pinning and multi-AZ
  2. Migrate data from existing MySQL using AWS DMS
  3. Move credentials to AWS Secrets Manager
  4. Configure automated backups and point-in-time recovery
- **Cross-Service Synergies**: local-monolith already uses RDS MySQL (3/4) — upgrade to Aurora for consistency. eks-saas-gitops uses DynamoDB (fully managed, no action needed).
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 1 (Aurora setup) → Phase 2 (data migration)
- **Relevant Learning Materials**: Module 4 — Move to Managed Databases

#### Move to Modern DevOps

- **Services Affected**: eks-saas-gitops, unishop-monolith, local-monolith (3 total)
- **Portfolio Priority**: High
- **Common Trigger Criteria**:
  - INF-Q6 < 3: 2 services (unishop-monolith 1/4, local-monolith 1/4 — no CI/CD)
  - OPS-Q9 < 3: 3 services (all at 1/4 — no progressive delivery)
  - OPS-Q10 < 3: 3 services (all at 1/4 — zero tests)
  - OPS-Q1 < 3: 3 services (all at 1/4 — no distributed tracing)
  - INF-Q5 < 3: 1 service (unishop-monolith at 1/4 — no IaC)
- **Representative AWS Services**: CodeBuild, CodePipeline, CloudFormation/Terraform, X-Ray, CloudWatch, Flux CD
- **Key Activities**:
  1. Establish portfolio-standard CI pipeline template (GitHub Actions → build → test → Docker → ECR)
  2. Deploy Flux CD GitOps for all services
  3. Add OpenTelemetry instrumentation across all services
  4. Implement structured JSON logging with correlation IDs
  5. Write integration tests for critical paths
  6. Deploy Flagger for canary deployments (Phase 3)
- **Cross-Service Synergies**: eks-saas-gitops's Flux CD configuration is the template for all services. Shared ADOT Collector serves the entire EKS cluster.
- **Estimated Effort**: High across 3 services
- **Roadmap Phase Alignment**: Phase 0 (foundations) → Phase 1 (implementation) → Phase 3 (advanced)
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

#### Move to AI

- **Services Affected**: eks-saas-gitops, unishop-monolith, local-monolith (3 total)
- **Portfolio Priority**: Low (not aligned with cloud-native-modernization goal)
- **Common Trigger Criteria**:
  - APP-Q13 < 3: 3 services (all at 1/4 — no AI/agent frameworks)
  - DATA-Q1 < 3: 3 services (all at 1/4 — no vector database)
  - DATA-Q3 < 3: 3 services (all at 1/4 — no RAG implementation)
- **Representative AWS Services**: Amazon Bedrock, OpenSearch Service, Aurora pgvector, Strands Agents SDK
- **Key Activities**:
  1. Defer to Phase 3+ after cloud-native foundations are established
  2. Add vector database (Aurora pgvector or OpenSearch) when AI use cases are prioritized
  3. Integrate Amazon Bedrock for AI capabilities in extracted microservices
- **Cross-Service Synergies**: Once services are decomposed, each microservice boundary becomes a natural agent tool boundary.
- **Estimated Effort**: High across 3 services
- **Roadmap Phase Alignment**: Phase 3+ (deferred)
- **Relevant Learning Materials**: Module 7 — Move to AI

### Example: Parallel Pathway Execution for a Single Service

**unishop-monolith** simultaneously pursues 4 pathways:
- **Move to Containers** (Phase 1): Containerize the Spring Boot JAR into a Docker image on EKS
- **Move to Managed Databases** (Phase 1-2): Migrate self-managed MySQL to Aurora MySQL
- **Move to Modern DevOps** (Phase 0-2): Establish IaC, CI/CD, testing, and observability
- **Move to Cloud Native** (Phase 2-3): Decompose monolith into microservices using Strangler Fig pattern

---

## AWS Programs & Engagement Recommendations

> **This section appears ONLY in portfolio reports, NEVER in individual reports.** Programs are engagement-level decisions scoped to the customer's overall estate, not per-repo.

Based on the portfolio assessment findings, the following AWS programs may accelerate your modernization journey:

### Recommended Programs

| Program | Relevance | Trigger Findings | Next Step |
|---------|-----------|-----------------|-----------|
| Migration Acceleration Program (MAP) | High | All 3 repos score below 2.5 overall: eks-saas-gitops (1.9), unishop-monolith (1.2), local-monolith (1.4). Significant modernization investment needed across the portfolio. | Evaluate MAP eligibility with AWS Account SA. MAP provides migration credits, tooling, and methodology for large-scale modernization. |
| EBA — Move to Modern DevOps | High | 3/3 services triggered. OPS-Q9, OPS-Q10, OPS-Q1 all score 1/4 across the portfolio. Zero CI/CD in 2 services. This is the highest-priority pathway. | Request EBA engagement via SA for Modern DevOps pathway. Focus on CI/CD, GitOps, and observability foundations. |
| EBA — Move to Cloud Native | High | 2/3 services triggered. APP-Q4 score 1/4 in both monoliths. Core deliverable of the modernization initiative. | Request EBA engagement via SA for Cloud Native pathway. Focus on Strangler Fig decomposition and EKS migration. |
| EBA — Move to Containers | Medium | 1/3 services triggered (unishop-monolith). INF-Q1 score 1/4 — raw EC2 deployment with no containerization. | Request EBA engagement via SA for Containers pathway. Focus on Dockerfile creation and EKS deployment. |
| EBA — Move to Managed Databases | Medium | 1/3 services triggered (unishop-monolith). INF-Q2 score 1/4, DATA-Q10 score 1/4 — self-managed MySQL with unknown engine version. | Request EBA engagement via SA for Managed Databases pathway. Focus on Aurora MySQL migration with DMS. |
| EBA — Move to AI | Low | 3/3 services triggered but low goal alignment for cloud-native-modernization. APP-Q13, DATA-Q1, DATA-Q3 all score 1/4. | Defer EBA for AI pathway. Re-evaluate after cloud-native foundations are established in Phase 3+. |
| ISV Workload Migration Program (ISV WMP) | Medium | eks-saas-gitops is a SaaS platform (multi-tenant architecture with tiered isolation). Goal context mentions "EKS with GitOps deployment" for a SaaS workload. | Evaluate ISV WMP eligibility if the portfolio represents an ISV SaaS offering being modernized. Discuss with AWS Partner team. |

### Program Details

**Migration Acceleration Program (MAP)**: Recommended because all 3 services score below 2.5, indicating a portfolio-wide modernization effort requiring significant investment. MAP provides migration credits to offset modernization costs, access to prescriptive guidance, and a proven methodology for phased migrations. This should be evaluated in Phase 0 alongside organizational readiness.

**EBA — Move to Modern DevOps**: The highest-priority EBA engagement. All 3 services need CI/CD, observability, and deployment strategy improvements. This pathway affects 100% of the portfolio and is a prerequisite for all other modernization work. An EBA engagement would accelerate the establishment of shared DevOps patterns in Phase 0-1.

**EBA — Move to Cloud Native**: The core engagement for the cloud-native-modernization goal. Both monoliths need decomposition into containerized microservices. An EBA engagement would provide expert guidance on domain modeling, Strangler Fig implementation, and EKS microservices architecture. Recommended for Phase 2 timing.

**ISV Workload Migration Program (ISV WMP)**: The eks-saas-gitops service has multi-tenant SaaS architecture with tiered isolation (basic/advanced/premium). If this portfolio represents an ISV modernizing their SaaS platform, the ISV WMP provides specialized support for SaaS modernization on AWS.

> These are engagement-level recommendations. Discuss with your AWS Solutions Architect
> or Partner to determine eligibility and timing.

---

## Integration Opportunities

### Shared Service Extraction

**Opportunity 1: Unified Observability Stack**
- Current State: Zero observability across all 3 services. Each would need to independently set up tracing, logging, and metrics.
- Proposed Solution: Deploy a shared observability stack on EKS — ADOT Collector (DaemonSet), Fluent Bit (DaemonSet), Prometheus + Grafana, CloudWatch dashboards — managed as shared Flux CD HelmReleases.
- Benefits: Single deployment serves all services. Consistent trace/log/metric formats. Portfolio-wide visibility. Reduced per-service operational overhead.
- Effort: Medium
- Priority: High (foundational for all modernization work)

**Opportunity 2: Centralized Authentication Service**
- Current State: eks-saas-gitops has no auth, unishop-monolith has disabled OAuth2, local-monolith uses PHP sessions. All 3 need authentication.
- Proposed Solution: Deploy Amazon Cognito as the portfolio-wide identity provider. Implement a shared authentication middleware/library for JWT validation. Configure OIDC federation for admin access.
- Benefits: Single identity provider for all services. Consistent JWT-based auth. SSO across the portfolio. No per-service auth implementation.
- Effort: Medium
- Priority: High (security prerequisite)

**Opportunity 3: Shared API Gateway / Ingress Controller**
- Current State: eks-saas-gitops has ALB Ingress, local-monolith has App Runner endpoint, unishop-monolith has direct EC2 exposure. No unified API management.
- Proposed Solution: Deploy a unified ALB Ingress Controller or Amazon API Gateway on EKS. All services route through a single entry point with throttling, authentication, and request validation.
- Benefits: Consistent API management. Unified rate limiting and WAF. Single endpoint for monitoring. Enables Strangler Fig routing during decomposition.
- Effort: Medium
- Priority: High (enables decomposition)

### Event-Driven Architecture

**Opportunity 1: Shared Event Bus for Domain Events**
- Current State: eks-saas-gitops uses SQS for producer-consumer messaging. Both monoliths use 100% synchronous communication. No event bus exists.
- Proposed Solution: Deploy Amazon EventBridge as the portfolio-wide event bus. As services are extracted from monoliths, they publish domain events (OrderCreated, InventoryUpdated, PaymentProcessed) to EventBridge. Consumers subscribe to relevant events asynchronously.
- Benefits: Decoupled inter-service communication. Event replay and audit. Enables independent service scaling. Reduces cascading failure risk.
- Effort: Medium
- Priority: High (enables decomposition)

**Opportunity 2: SQS Pattern Replication**
- Current State: eks-saas-gitops has mature SQS patterns (per-tenant queues, Argo Events triggers). Both monoliths have no async messaging.
- Proposed Solution: Replicate eks-saas-gitops's SQS patterns to the monolith decomposition. Use SQS for point-to-point async communication between extracted services (e.g., Basket → Catalog in unishop, Fulfillment → Warehouse in local-monolith).
- Benefits: Proven patterns from eks-saas-gitops. Managed service with no operational overhead. Dead letter queues for reliability.
- Effort: Low
- Priority: Medium

### API Gateway Consolidation

- Current State: No unified API management. Three different entry points (ALB, App Runner, EC2 direct).
- Proposed Solution: Consolidate all service endpoints behind the EKS ALB Ingress Controller with path-based routing. Add Amazon API Gateway for external-facing APIs with throttling, API keys, and usage plans.
- Benefits: Single entry point for all APIs. Consistent rate limiting and auth. Simplified DNS and TLS management. Enables version-based routing during decomposition.
- Effort: Medium
- Priority: High

### Observability Unification

- Current State: 3 different (or absent) observability stacks. eks-saas-gitops has Kubecost and Metrics Server. Both monoliths have zero observability.
- Proposed Solution: Deploy a unified observability platform on EKS: OpenTelemetry (ADOT Collector) for traces, Fluent Bit for logs, Prometheus for metrics, Grafana for dashboards, CloudWatch for alarms. All managed as Flux CD HelmReleases.
- Benefits: End-to-end tracing across all services. Consistent log format. Unified dashboards. Portfolio-wide SLO monitoring. Reduced tool sprawl.
- Effort: Medium
- Priority: High

---

## Resource Allocation Recommendations

### Team Structure

**Recommended Approach**: Dedicated platform team + embedded service teams

The portfolio has 5+ cross-cutting concerns affecting all services (CI/CD, observability, auth, API gateway, secrets management), which warrants a dedicated platform team to build shared capabilities while service teams focus on application-specific modernization.

**Platform Team** (2-3 people):
- Responsibilities: EKS cluster management, Terraform module library, Flux CD GitOps infrastructure, shared observability stack (ADOT, Fluent Bit, Prometheus), shared authentication (Cognito), CI pipeline templates, Helm chart templates, WAF configuration
- Skills Required: Kubernetes/EKS, Terraform, Flux CD/GitOps, Helm, observability (OpenTelemetry, Prometheus, Grafana), AWS networking, IAM/security
- Timeline: Active from Phase 0 onward; transitions to maintenance in Phase 2

**Service Team A — unishop-monolith** (2-3 people):
- Responsibilities: Containerize Java monolith, Aurora MySQL migration, Strangler Fig decomposition, service-specific CI/CD, domain modeling and service extraction
- Skills Required: Java/Spring Boot, Docker, Helm, Terraform, MySQL/Aurora, DMS, microservices patterns
- Timeline: Active from Phase 1 onward

**Service Team B — local-monolith** (1-2 people):
- Responsibilities: App Runner → EKS migration, CloudFormation → Terraform migration, domain modeling, service-specific CI/CD, future decomposition
- Skills Required: PHP, Docker, Helm, Terraform, RDS/Aurora, CloudFormation
- Timeline: Active from Phase 2 onward (lower priority than unishop)

### Skill Gaps

1. **Terraform/IaC**: Required for all infrastructure provisioning. Currently only eks-saas-gitops uses Terraform. unishop-monolith team has zero IaC experience. Critical gap.
2. **Kubernetes/EKS**: Required for all service deployments. Only eks-saas-gitops team has EKS experience. Both monolith teams need upskilling. Critical gap.
3. **GitOps (Flux CD)**: Required for the preferred deployment model. Only eks-saas-gitops has Flux CD. Both monolith teams need training. Medium gap.
4. **Helm Charts**: Required for Kubernetes deployment manifests. Only eks-saas-gitops has Helm charts. Both monolith teams need training. Medium gap.
5. **Observability (OpenTelemetry, X-Ray)**: Required for distributed tracing across all services. No team has observability experience. Critical gap.
6. **Docker/Containers**: Required for containerizing the monoliths. local-monolith has a basic Dockerfile. unishop-monolith has zero containerization. Medium gap.
7. **Microservices Decomposition Patterns**: Required for Strangler Fig, Saga, anti-corruption layer. No team has decomposition experience. High gap.

### Training Recommendations

Prioritize training for Phase 0 and Phase 1 skills (needed first):

1. **EKS and Containers** (Phase 0 — all teams): Amazon EKS Primer, Deploy Applications on EKS (Lab), Introduction to Containers, EKS Workshop
2. **Modern DevOps / CI/CD** (Phase 0 — all teams): Getting Started with DevOps on AWS, CI/CD Automation, Automate EKS Deployments with GitOps
3. **Cloud Design Patterns** (Phase 1 — service teams): Cloud Design Patterns (Strangler Fig, Anti-corruption Layer, Saga, Circuit Breaker)
4. **Managed Databases** (Phase 1 — unishop team): Migrating RDS MySQL to Aurora, DMS Getting Started
5. **Observability** (Phase 0 — platform team): Monitor Python/Java Applications Using CloudWatch Application Signals

### External Support

- **AWS Professional Services or Consulting Partners** recommended for:
  - Phase 0: Platform team establishment and EKS cluster hardening (2-4 weeks)
  - Phase 2: Strangler Fig decomposition guidance for unishop-monolith (4-8 weeks)
  - Aurora MySQL migration for unishop-monolith using DMS (2-4 weeks)
- **Knowledge transfer**: External consultants should pair with internal teams to build capability, not just deliver artifacts
- **Estimated external support duration**: 2-3 months for platform work, 1-2 months per service for decomposition guidance

---

## Recommended Self-Paced Learning Materials

Based on portfolio-wide skill gaps in containers/EKS, cloud-native decomposition, managed databases, and modern DevOps:

**Module 2: Move to Cloud Native (Containers and Serverless):**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for microservices decomposition: Strangler Fig, Anti-corruption Layer, Saga patterns, Event Sourcing, Circuit Breaker, API routing, Hexagonal Architecture, and more
- AWS Modernization Pathways: Move to Cloud Native Serverless — https://skillbuilder.aws/learning-plan/CMK2J48MVN/aws-modernization-pathways-move-to-cloud-native-serverless-includes-labs/EFUPP53B4Q
- Modernize a Monolith to ECS and Fargate using Application Discovery — https://skillbuilder.aws/learn/1YXAWYH2WA/modernize-a-monolith-to-ecs-and-fargate-using-application-discovery/AQ37WHN3K1
- Meeting Simulator: Transform Monolithic App into Serverless Microservices — https://skillbuilder.aws/learn/HUKQHYU9TB/meeting-simulator-transforming-our-monolithic-app-into-serverless-microservices/NS6S2J7YR7

**Module 3: Move to Containers with Amazon ECS and EKS:**
- AWS Modernization Pathways: Move to Containers with Amazon EKS — https://skillbuilder.aws/learning-plan/GNYBZ9X9EM/aws-modernization-pathways-move-to-containers-with-amazon-eks-includes-labs/1HB9MKXD2N
- Introduction to Containers — https://skillbuilder.aws/learn/CUCA1DK47V/introduction-to-containers/XJ58VC1FF5
- AWS Fargate Getting Started — https://skillbuilder.aws/learn/6QS9CM1V7K/aws-fargate-getting-started/EDX6V7B5YR
- Amazon ECR Getting Started — https://skillbuilder.aws/learn/M494WWS5EF/amazon-ecr-getting-started/N5CQ7DC6HT
- Amazon EKS Primer — https://skillbuilder.aws/learn/Z521GMBP1J/amazon-eks-primer/NGM5AF9K72
- Deploy Applications on Amazon EKS (Lab) — https://skillbuilder.aws/learn/2B5XUE2V9C/lab--deploy-applications-on-amazon-elastic-kubernetes-service-eks/SM5HZNTY9J
- EKS Workshop — https://www.eksworkshop.com/
- EKS Auto Mode Workshop — https://catalog.workshops.aws/workshops/aadbd25d-43fa-4ac3-ae88-32d729af8ed4

**Module 4: Move to Managed Databases:**
- AWS Modernization Pathways: Move to Managed Databases — https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC/aws-modernization-pathways-move-to-managed-databases-includes-labs/2S2QZKG9DV
- Introduction to Building with AWS Databases — https://skillbuilder.aws/learn/HYKKWEN9ZS/introduction-to-building-with-aws-databases/V7RVH2KY91
- Selecting your Data Migration Strategy with AWS — https://skillbuilder.aws/learn/RKGP54WJPP/selecting-your-data-migration-strategy-with-aws/D38U3CZEYR
- AWS Database Migration Service (DMS) Getting Started — https://skillbuilder.aws/learn/ND246G8Y3W/aws-database-migration-service-aws-dms-getting-started/QK5CCBP464
- Migrating RDS MySQL to Aurora (Lab) — https://skillbuilder.aws/learn/RZF2GBUUWX/migrating-rds-mysql-to-aurora-with-read-replica/SMG825PXTK

**Module 6: Move to Modern DevOps:**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
- Monitor Python Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/JMPDZD64MV/monitor-python-applications-using-amazon-cloudwatch-application-signals/2JP3J2MPCK
- Monitor Java Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/PMCTXKYK1Y/monitor-java-applications-using-amazon-cloudwatch-application-signals/15ZK4ETKE9
- AWS Developer: CI/CD Automation — https://skillbuilder.aws/learn/C1KF8ZJ1D8/aws-developer--cicd-automation/KY1E1JS9FA
- AWS PartnerCast: Automate EKS Deployments With GitOps Using ArgoCD and GitHub Actions — https://skillbuilder.aws/learn/D9U7XMXP31/aws-partnercast--tech-talks--automate-eks-deployments-with-gitops-using-argocd-and-github-actions--technical/Z4M9Z8FY88
- AWS PartnerCast: Next-Gen Platform Engineering: Combining EKS, GitOps & Amazon Q for Intelligent DevOps — https://skillbuilder.aws/learn/FJBV2YWNSS/aws-partnercast--tech-talks--nextgen-platform-engineering-combining-eks-gitops--amazon-q-for-intelligent-devops--technical/NZ284HRTVG
- AWS PartnerCast: Unleash Innovation with a Cloud Operating Model and Platform Engineering — https://skillbuilder.aws/learn/EG2A78NXEC/aws-partnercast--tech-talks--unleash-innovation-with-a-cloud-operating-model-and-platform-engineering--technical/CC8ZTK88QK
- EKS Workshop: Automation — https://www.eksworkshop.com/docs/automation/
- EKS SaaS GitOps Workshop — https://catalog.workshops.aws/eks-saas-gitops/en-US/03-lab1

---

## Risk Analysis

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **eks-saas-gitops platform instability during monolith migration** — AdminAccess IAM policies and lack of testing could cause issues when deploying new workloads | High | High | Scope IAM policies and add integration tests in Phase 1 before accepting monolith workloads in Phase 2. Run load tests on the EKS cluster. |
| **Data loss during unishop-monolith MySQL → Aurora migration** — Self-managed MySQL with unknown engine version and no backup visibility | Medium | High | Use AWS DMS with validation for data migration. Perform dry-run migration first. Maintain parallel databases during cutover window. |
| **Monolith decomposition introduces distributed system failures** — Both monoliths have zero resilience patterns (APP-Q9: 1/4), no retries, no circuit breakers | High | High | Implement resilience patterns (Resilience4j, tenacity) BEFORE service extraction. Start with the Strangler Fig pattern for incremental risk. |
| **Technology diversity increases operational complexity** — 3 languages (Python, Java, PHP) require different toolchains, expertise, and operational patterns | Medium | Medium | Standardize on common patterns (Helm, IRSA, OTel, JSON logging) across all languages. Platform team provides language-agnostic infrastructure. |
| **Flux CD Gitops reconciliation disruption** — Incorrectly configured Helm charts or namespace conflicts could affect existing eks-saas-gitops tenants | Medium | High | Use separate Flux CD kustomizations and namespaces for monolith workloads. Test Helm chart rendering in CI before merging. |

### Organizational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Skill gap delays** — Teams lack EKS, Terraform, and GitOps experience needed for Phase 0-1 | High | Medium | Begin training immediately (Phase 0). Pair with external consultants for knowledge transfer. Use EKS SaaS GitOps Workshop for hands-on learning. |
| **Parallel track coordination overhead** — Two monolith teams working concurrently in Phase 2 may compete for platform team attention | Medium | Medium | Assign dedicated platform team liaison per service team. Prioritize unishop-monolith (P0) for platform support conflicts. |
| **Scope creep during decomposition** — Monolith decomposition can expand indefinitely without clear phase gates | Medium | High | Define clear phase boundaries with specific deliverables. Phase 2 goal: containerize and deploy on EKS + first service extraction only. Defer full decomposition to Phase 3. |

### Dependency Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **eks-saas-gitops as single point of failure** — Blast radius 100%. If the EKS cluster fails, all services are affected | Medium | High | Implement multi-AZ NAT gateways. Configure multi-AZ node groups. Add cluster health monitoring. Consider multi-cluster strategy for production isolation. |
| **Shared EKS cluster resource contention** — New monolith workloads may starve existing eks-saas-gitops tenant services | Medium | Medium | Use Kubernetes ResourceQuotas and LimitRanges per namespace. Configure Karpenter NodePools with application taints (already partially configured). Monitor with Kubecost. |

### Single Points of Failure

1. **eks-saas-gitops EKS cluster**: All 3 services depend on this single cluster. EKS cluster endpoint is publicly accessible (INF-Q9 finding). Single NAT gateway is a network SPOF.
   - Mitigation: Set cluster endpoint to private access. Deploy multi-AZ NAT gateways. Consider a separate EKS cluster for the monolith workloads if isolation is critical.

2. **unishop-monolith self-managed MySQL**: Unknown management status, unknown engine version, no automated backups visible in IaC. If this database fails, the monolith is completely down.
   - Mitigation: Priority action — migrate to Aurora MySQL with multi-AZ failover and automated backups in Phase 1.

3. **Flux CD GitOps pipeline**: All deployments flow through Flux CD reconciliation from a single Gitea instance running on EC2 (not highly available).
   - Mitigation: Consider migrating Gitea to a managed Git service (GitHub, CodeCommit) or deploying Gitea on EKS with persistent storage for high availability.

---

## Service-by-Service Summary

### eks-saas-gitops

- **Overall Score**: 1.9 / 4.0 🟠
- **Repository**: ./services/eks-saas-gitops
- **Repository Type**: monorepo (auto-detected)
- **Assessment Date**: 2026-03-17
- **Category Scores**:
  - Infrastructure: 3.1 / 4.0 🟡
  - Application: 2.2 / 4.0 🟡
  - Data: 1.8 / 4.0 🟠
  - Security: 1.3 / 4.0 🟠
  - Operations: 1.1 / 4.0 🟠
- **Top Priorities**:
  1. OPS-Q9: No canary/blue-green deployment strategy (1/4)
  2. OPS-Q10: Zero test files in the entire repository (1/4)
  3. OPS-Q1: No distributed tracing (1/4)
  4. SEC-Q9: All APIs completely unauthenticated (1/4)
  5. SEC-Q2: AdminAccess IAM policies on Argo Workflows and TF Controller (2/4)
- **Dependencies**: None (foundation service)
- **Depended On By**: unishop-monolith, local-monolith
- **Modernization Pathways**: Move to Modern DevOps (Triggered, High), Move to AI (Triggered, Low)
- **Goal Alignment**: Move to Modern DevOps (High), Move to AI (Low)
- **Modernization Phase**: Phase 1 — Containerize & Automate
- **Estimated Effort**: High

### unishop-monolith

- **Overall Score**: 1.2 / 4.0 ❌
- **Repository**: ./services/unishop-monolith-to-microservices/MonoToMicroLegacy
- **Repository Type**: application (auto-detected)
- **Assessment Date**: 2026-03-17
- **Category Scores**:
  - Infrastructure: 1.0 / 4.0 ❌
  - Application: 1.2 / 4.0 ❌
  - Data: 1.8 / 4.0 🟠
  - Security: 1.1 / 4.0 ❌
  - Operations: 1.0 / 4.0 ❌
- **Top Priorities**:
  1. APP-Q4: Tightly-coupled monolith with shared MySQL schema (1/4)
  2. INF-Q1: EC2-only compute with no containers (1/4)
  3. INF-Q5: Zero infrastructure as code (1/4)
  4. INF-Q6: No CI/CD pipeline (1/4)
  5. APP-Q3: 100% synchronous communication (1/4)
- **Dependencies**: eks-saas-gitops (shared_infra — will deploy onto EKS cluster)
- **Depended On By**: None
- **Modernization Pathways**: Move to Cloud Native (Triggered, High), Move to Containers (Triggered, High), Move to Managed Databases (Triggered, High), Move to Modern DevOps (Triggered, High), Move to AI (Triggered, Medium)
- **Goal Alignment**: Move to Cloud Native (High), Move to Containers (High), Move to Modern DevOps (High), Move to Managed Databases (Medium), Move to AI (Low)
- **Modernization Phase**: Phase 2 — Decompose & Decouple
- **Estimated Effort**: High

### local-monolith

- **Overall Score**: 1.4 / 4.0 ❌
- **Repository**: ./monolith
- **Repository Type**: application (auto-detected)
- **Assessment Date**: 2026-03-17
- **Category Scores**:
  - Infrastructure: 1.9 / 4.0 🟡
  - Application: 1.2 / 4.0 🟠
  - Data: 1.7 / 4.0 🟠
  - Security: 1.4 / 4.0 🟠
  - Operations: 1.0 / 4.0 🟠
- **Top Priorities**:
  1. APP-Q4: Monolith — single index.php file with all domains (1/4)
  2. INF-Q6: No CI/CD pipeline — manual deploy.sh only (1/4)
  3. APP-Q3: 100% synchronous communication (1/4)
  4. OPS-Q9: Manual deployment with no progressive delivery (1/4)
  5. OPS-Q1: No distributed tracing (1/4)
- **Dependencies**: eks-saas-gitops (shared_infra — will containerize and deploy onto EKS cluster)
- **Depended On By**: None
- **Modernization Pathways**: Move to Cloud Native (Triggered, High), Move to Modern DevOps (Triggered, High), Move to AI (Triggered, Low)
- **Goal Alignment**: Move to Cloud Native (High), Move to Modern DevOps (High), Move to AI (Low)
- **Modernization Phase**: Phase 2 — Decompose & Decouple
- **Estimated Effort**: High

---

## Appendix: Assessment Inventory

### Reports Analyzed

| Service | Repository Path | Repo Type | Assessment Date | Overall Score | Report Path |
|---------|----------------|-----------|-----------------|---------------|-------------|
| eks-saas-gitops | ./services/eks-saas-gitops | monorepo (auto-detected) | 2026-03-17 | 1.9 / 4.0 | ./services/eks-saas-gitops/agentic-readiness-assessment/eks-saas-gitops-agentic-readiness-report.md |
| unishop-monolith | ./services/unishop-monolith-to-microservices/MonoToMicroLegacy | application (auto-detected) | 2026-03-17 | 1.2 / 4.0 | ./services/unishop-monolith-to-microservices/MonoToMicroLegacy/agentic-readiness-assessment/MonoToMicroLegacy-agentic-readiness-report.md |
| local-monolith | ./monolith | application (auto-detected) | 2026-03-17 | 1.4 / 4.0 | ./monolith/agentic-readiness-assessment/monolith-agentic-readiness-report.md |

### Assessment Methodology

- Individual assessments performed using: AWS Transform Custom — Agentic Readiness Assessment
- Portfolio assessment performed using: AWS Transform Custom — Portfolio Agentic Readiness Assessment
- Assessment criteria: 56 total criteria across 5 categories
- Scoring scale: 1-4 (Not Present, Needs Work, Partial, Agent-Ready)
- Portfolio goal: cloud-native-modernization
- Goal context: Decomposing monoliths into containerized microservices on EKS with GitOps deployment
- Preferences: prefer [eks, fargate, terraform, gitops, helm, containers, api-gateway], avoid [self-managed-kubernetes, manual-deployments]

---

## Recommended Next Steps

1. **Immediate (Week 1)**:
   - Review this portfolio assessment with all stakeholders and validate priorities
   - Kick off MAP eligibility evaluation with your AWS Solutions Architect
   - Begin EKS and Terraform training for all team members (EKS Workshop, EKS Primer)
   - Scope IAM policies on eks-saas-gitops — replace AdminAccess immediately (highest security risk)

2. **Short-term (Month 1 — Phase 0)**:
   - Establish the platform team (2-3 people) for shared infrastructure work
   - Deploy shared ADOT Collector and Fluent Bit on EKS cluster
   - Create CI pipeline template (GitHub Actions → Docker → ECR) and implement for all services
   - Migrate hardcoded secrets to AWS Secrets Manager (unishop-monolith, local-monolith, eks-saas-gitops)
   - Deploy External Secrets Operator and AWS WAF on EKS
   - Create Dockerfile for unishop-monolith (multi-stage Gradle build)

3. **Medium-term (Months 1-3 — Phases 1-2)**:
   - Harden eks-saas-gitops: scoped IAM, integration tests, OpenTelemetry, structured logging
   - Deploy unishop-monolith and local-monolith containers to EKS via Helm + Flux CD
   - Migrate unishop-monolith MySQL to Aurora MySQL using DMS
   - Begin Strangler Fig decomposition of unishop-monolith (extract User service first)
   - Conduct domain modeling workshop for local-monolith
   - Deploy Amazon Cognito as portfolio-wide identity provider

4. **Long-term (Months 3-6+ — Phase 3)**:
   - Complete microservices decomposition for both monoliths
   - Implement canary deployments with Flagger + Flux CD
   - Deploy unified API Gateway with versioning and throttling
   - Define and monitor SLOs for all services
   - Implement end-to-end distributed tracing and anomaly detection
   - Evaluate AI capabilities (Bedrock, vector databases) after cloud-native foundations are solid
