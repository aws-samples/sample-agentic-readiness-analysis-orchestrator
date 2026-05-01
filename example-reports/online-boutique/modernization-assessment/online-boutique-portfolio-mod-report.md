# Portfolio Modernization Assessment Report

**Date**: 2026-04-15
**Services Assessed**: 11
**Portfolio Context**: Cloud-native e-commerce platform with 11 microservices. Evaluating for autonomous AI agent integration (customer support agent for order tracking, product recommendations, and cart management) and modernization maturity.
**Technology Preferences**: Prefer: EKS, DynamoDB, Bedrock, Terraform, GitOps; Avoid: Serverless, Manual Deployments

---

## Table of Contents

1. [Executive Dashboard](#executive-dashboard)
2. [Technology Stack Summary](#technology-stack-summary)
3. [Service Dependency Map](#service-dependency-map)
4. [Cross-Cutting Concerns](#cross-cutting-concerns)
5. [Portfolio Modernization Roadmap](#portfolio-modernization-roadmap)
6. [AWS Modernization Pathways](#aws-modernization-pathways)
7. [Integration Opportunities](#integration-opportunities)
8. [Risk Assessment](#risk-assessment)
9. [Resource Allocation Recommendations](#resource-allocation-recommendations)
10. [AWS Programs & Engagement Recommendations](#aws-programs--engagement-recommendations)
11. [Recommended Self-Paced Learning Materials](#recommended-self-paced-learning-materials)
12. [Portfolio-Level Findings](#portfolio-level-findings)
13. [Service-by-Service Summary](#service-by-service-summary)
14. [Assessment Inventory](#assessment-inventory)

---

## Executive Dashboard

### Portfolio Score Overview

| Metric | Value |
|--------|-------|
| Portfolio Overall Score | 2.03 / 4.0 |
| Score Range | 1.67 – 2.39 |
| Score Standard Deviation | 0.19 |
| Highest Scoring Service | shippingservice (2.39) |
| Lowest Scoring Service | currencyservice (1.67) |
| Pathways Triggered (portfolio-wide) | 3 of 7 |
| Cross-Cutting Foundational Blockers | 21 |
| Cross-Cutting Improvement Opportunities | 5 |

### Readiness Distribution

| Level | Services | Percentage | Description |
|-------|----------|------------|-------------|
| ✅ Mature (3.5–4.0) | 0 | 0% | Fully meets criteria. Minor optimization only. |
| 🟡 Partial (2.5–3.4) | 0 | 0% | Partially meets criteria. Targeted improvements needed. |
| 🟠 Needs Work (1.5–2.4) | 11 | 100% | Significant gaps. Moderate modernization effort. |
| ❌ Not Ready (<1.5) | 0 | 0% | Fundamental gaps. Major modernization required. |

### Category Score Averages

| Category | Portfolio Average | Min | Max | Services with N/A |
|----------|------------------|-----|-----|-------------------|
| Infrastructure & DevOps (INF) | 2.09 | 1.09 | 2.55 | 0 |
| Application Architecture (APP) | 2.45 | 2.17 | 2.83 | 1 |
| Data Platform (DATA) | 2.75 | 2.00 | 3.50 | 0 |
| Security Baseline (SEC) | 1.49 | 1.29 | 1.71 | 0 |
| Operations & Observability (OPS) | 1.44 | 1.22 | 1.67 | 0 |

### Repo Type Distribution

| Repo Type | Count | Percentage |
|-----------|-------|------------|
| application | 10 | 91% |
| infrastructure-only | 1 | 9% |
| deployment-config | 0 | 0% |
| monorepo | 0 | 0% |
| library | 0 | 0% |

### Readiness Snapshot

| Metric | Value |
|--------|-------|
| assessment_date | 2026-04-15 |
| total_services | 11 |
| portfolio_score | 2.03 |
| score_range_min | 1.67 |
| score_range_max | 2.39 |
| mature_services | 0 |
| partial_services | 0 |
| needs_work_services | 11 |
| not_ready_services | 0 |
| pathways_triggered | 3 |
| foundational_blockers | 21 |
| improvement_opportunities | 5 |
| category_inf | 2.09 |
| category_app | 2.45 |
| category_data | 2.75 |
| category_sec | 1.49 |
| category_ops | 1.44 |
| portfolio_level_avg | 1.60 |
## Technology Stack Summary

### Programming Languages

| Language | Services | Percentage |
|----------|----------|------------|
| Go | 4 (frontend, productcatalogservice, checkoutservice, shippingservice) | 36% |
| Python | 2 (emailservice, recommendationservice) | 18% |
| Node.js / JavaScript | 2 (paymentservice, currencyservice) | 18% |
| C# / .NET | 1 (cartservice) | 9% |
| Java | 1 (adservice) | 9% |
| N/A (infrastructure-only) | 1 (platform-infra) | 9% |

### Database Engines

| Engine | Type | Services | Managed? |
|--------|------|----------|----------|
| Redis | Cache / Key-Value | 11 (shared cart store) | Mixed — default is self-managed in-cluster; optional Memorystore managed |
| JSON file | File-based | 1 (productcatalogservice) | No — static file bundled in container image |

**Database Distribution**: 1 managed option (Memorystore, disabled by default), 1 self-managed (in-cluster Redis), 0 commercial, 2 open source (Redis, JSON)

### Compute Patterns

| Pattern | Services | Percentage |
|---------|----------|------------|
| Managed Kubernetes (GKE Autopilot) | 11 | 100% |
| EC2 / VM-based | 0 | 0% |
| Serverless (Lambda) | 0 | 0% |

### IaC and CI/CD Tools

| Tool | Category | Services |
|------|----------|----------|
| Terraform | IaC | 10 (all except currencyservice) |
| Kubernetes Manifests | IaC | 10 (all except currencyservice) |
| Helm Charts | IaC | 10 (all except currencyservice) |
| Kustomize | IaC | 10 (all except currencyservice) |
| GitHub Actions | CI/CD | 10 (all except currencyservice) |
| Google Cloud Build | CI/CD | 10 (all except currencyservice) |
| Skaffold | CI/CD | 10 (all except currencyservice) |
| None (no IaC/CI/CD) | IaC / CI/CD | 1 (currencyservice) |

### Standardization Opportunities

- **Language consolidation**: Go is the dominant language (4 services, 36%). C# (1 service) and Java (1 service) are single-service outliers — evaluate whether consolidating to Go would reduce operational complexity. However, each language is well-suited to its service's domain.
- **IaC gap**: currencyservice has **zero IaC and zero CI/CD** (INF-Q10=1, INF-Q11=1) — this is a critical outlier requiring immediate remediation via the Move to Modern DevOps pathway.
- **Messaging gap**: No messaging/streaming infrastructure exists across the entire portfolio. All 11 services use synchronous gRPC exclusively. This is the single largest architectural standardization opportunity.
- **Preference alignment**:
  - ✅ **Terraform** (preferred) — already the primary IaC tool for 10/11 services
  - ⚠️ **EKS** (preferred) — currently on GKE Autopilot; migration needed
  - ⚠️ **DynamoDB** (preferred) — not yet in use; Redis is the only data store
  - ⚠️ **GitOps** (preferred) — not yet adopted; deployments use Skaffold/kubectl
  - ⚠️ **Bedrock** (preferred) — no AI frameworks detected in any service
  - ✅ **Avoid Serverless** — no Lambda or serverless patterns in use
  - ✅ **Avoid Manual Deployments** — CI/CD exists for 10/11 services (currencyservice is the exception)
- **Technology diversity score**: 5 languages, 4 IaC tools, 3 CI/CD tools, 1 compute pattern, 1 DB engine across 11 services = 1.27 distinct technologies per service (moderate diversity)
## Service Dependency Map

> No dependency information was provided in the portfolio configuration. To enable
> dependency-aware analysis — including coupling scores, blast radius calculation,
> circular dependency detection, and dependency-ordered roadmap phasing — add
> `dependency_overrides` to the portfolio config.

### Inferred Dependencies (from MOD Report Findings)

Based on gRPC service connections documented in individual MOD reports, the following dependency patterns are observable:

| Source Service | Target Service(s) | Communication | Notes |
|---------------|-------------------|---------------|-------|
| frontend | productcatalogservice, cartservice, checkoutservice, currencyservice, shippingservice, recommendationservice, adservice | Synchronous gRPC | BFF pattern — calls all 7 backend services |
| checkoutservice | cartservice, productcatalogservice, shippingservice, currencyservice, paymentservice, emailservice | Synchronous gRPC | Orchestrator — calls 6 services sequentially during PlaceOrder |
| recommendationservice | productcatalogservice | Synchronous gRPC | Fetches product catalog for recommendation generation |

**Key observations:**
- **frontend** has the highest fan-out (7 downstream services) — it is the primary consumer
- **checkoutservice** is the critical-path orchestrator calling 6 services synchronously during checkout
- **productcatalogservice** has the highest inferred fan-in (called by frontend, checkoutservice, recommendationservice)
- **platform-infra** manages shared infrastructure (GKE cluster, Redis) for all services
- All communication is synchronous gRPC with no async patterns
## Cross-Cutting Concerns

> Cross-cutting concerns are gaps that appear across multiple services. They are
> classified into two tiers based purely on score severity — no goal-based logic.

### 🚨 Foundational Blockers

> Criteria scoring < 2 in 2+ repos. These block all modernization efforts.
> Address these first — nothing else matters until these are resolved.

1. **SEC-Q1: Audit Logging** — 11 of 11 services score < 2
   - **Score Distribution**: frontend=1, cartservice=1, productcatalogservice=1, checkoutservice=1, paymentservice=1, currencyservice=1, shippingservice=1, emailservice=1, recommendationservice=1, adservice=1, platform-infra=1
   - **Impact**: No forensic capability. Compliance blocker. Cannot trace security events or infrastructure changes across any service.
   - **Affected Services**: All 11 services
   - **Portfolio-Level Recommendation**: Deploy centralized AWS CloudTrail with log file validation and S3 Object Lock. Configure CloudWatch Logs for all EKS pods with defined retention. Define audit infrastructure in Terraform as a shared platform module.

2. **SEC-Q2: Encryption at Rest** — 11 of 11 services score < 2
   - **Score Distribution**: All services = 1
   - **Impact**: Cart data, session data, and configuration stored unencrypted. Blocks compliance for any regulated workload.
   - **Affected Services**: All 11 services
   - **Portfolio-Level Recommendation**: Establish AWS KMS customer-managed keys via Terraform. Enable encryption at rest on all data stores (ElastiCache, DynamoDB, S3, EBS). Enable EKS secrets encryption.

3. **INF-Q3: Workflow Orchestration** — 11 of 11 services score < 2
   - **Score Distribution**: All services = 1
   - **Impact**: Checkout flow is a hardcoded synchronous chain with no compensation, retry, or state management. Payment failures during shipping leave orders in inconsistent state.
   - **Affected Services**: All 11 services
   - **Portfolio-Level Recommendation**: Introduce AWS Step Functions for the checkout workflow. Model order placement as a state machine with compensation steps and retry policies.

4. **INF-Q4: Async Messaging and Streaming** — 11 of 11 services score < 2
   - **Score Distribution**: All services = 1
   - **Impact**: All communication is synchronous gRPC. Cascading failure risk across the entire service mesh. Email notifications block checkout responses.
   - **Affected Services**: All 11 services
   - **Portfolio-Level Recommendation**: Deploy Amazon SQS/SNS via Terraform for event-driven patterns. Start with checkout→email decoupling, then expand to catalog change events and ad impression tracking.

5. **INF-Q8: Backup and Recovery** — 11 of 11 services score < 2
   - **Score Distribution**: All services = 1
   - **Impact**: Redis uses emptyDir — all cart data lost on pod restart. No recovery capability for any data store. Zero disaster recovery posture.
   - **Affected Services**: All 11 services
   - **Portfolio-Level Recommendation**: Migrate to Amazon ElastiCache/DynamoDB with automated backups and PITR. Implement AWS Backup for centralized governance. Define backup policies in Terraform.

6. **OPS-Q2: SLO Definitions** — 11 of 11 services score < 2
   - **Score Distribution**: All services = 1
   - **Impact**: No measurable definition of "good enough" for any service. Cannot prioritize improvements or measure modernization impact.
   - **Affected Services**: All 11 services
   - **Portfolio-Level Recommendation**: Define SLOs for all services. Start with P0 services (checkout: 99.95% availability, p99 < 2s; frontend: 99.9% availability, p99 < 500ms). Implement SLO monitoring via CloudWatch on EKS.

7. **OPS-Q3: Business Metrics** — 11 of 11 services score < 2
   - **Score Distribution**: All services = 1
   - **Impact**: No visibility into business outcomes (orders, conversion, cart abandonment). Modernization decisions are not data-driven.
   - **Affected Services**: All 11 services
   - **Portfolio-Level Recommendation**: Instrument all services with OpenTelemetry metrics. Export to CloudWatch via ADOT collector on EKS. Build business dashboards for portfolio KPIs.

8. **OPS-Q4: Anomaly Detection and Alerting** — 11 of 11 services score < 2
   - **Score Distribution**: All services = 1
   - **Impact**: No proactive alerting. Service degradation discovered only when users report issues. Silent failures across the entire platform.
   - **Affected Services**: All 11 services
   - **Portfolio-Level Recommendation**: Deploy CloudWatch Alarms for error rate, latency, and pod restarts on all services. Enable anomaly detection. Integrate with PagerDuty/OpsGenie via SNS. Define alarms in Terraform.

9. **OPS-Q7: Incident Response Automation** — 11 of 11 services score < 2
   - **Score Distribution**: All services = 1
   - **Impact**: Incident response is entirely ad hoc. No runbooks, no automated remediation, no escalation paths. MTTR is unpredictable.
   - **Affected Services**: All 11 services
   - **Portfolio-Level Recommendation**: Create runbooks for common incidents per service. Implement SSM Automation documents for common remediation. Define incident response workflows with Step Functions.

10. **OPS-Q8: Observability Ownership** — 11 of 11 services score < 2
    - **Score Distribution**: All services = 1
    - **Impact**: No per-service observability ownership. CODEOWNERS covers code but not operational responsibility. Monitoring gaps inevitable.
    - **Affected Services**: All 11 services
    - **Portfolio-Level Recommendation**: Define per-service observability ownership. Create per-service CloudWatch dashboards with named owners. Tag alarms with team attribution.

11. **APP-Q3: Async vs Sync Communication** — 10 of 10 applicable services score < 2
    - **Score Distribution**: frontend=1, cartservice=1, productcatalogservice=1, checkoutservice=1, paymentservice=1, currencyservice=1, shippingservice=1, emailservice=1, recommendationservice=1, adservice=1 (platform-infra=N/A)
    - **Impact**: 100% synchronous coupling. Cascading failures. Latency compounds across the checkout chain (6+ sequential calls).
    - **Affected Services**: All 10 application services
    - **Portfolio-Level Recommendation**: Introduce event-driven patterns with SNS/SQS. Convert fire-and-forget operations (email, ad tracking) to async. Keep latency-sensitive calls (product lookup, currency conversion) synchronous.

12. **APP-Q5: API Versioning Strategy** — 9 of 10 applicable services score < 2
    - **Score Distribution**: frontend=1, cartservice=1, productcatalogservice=1, checkoutservice=2, paymentservice=1, currencyservice=1, shippingservice=1, emailservice=1, recommendationservice=1, adservice=1 (platform-infra=N/A)
    - **Impact**: Breaking proto changes affect all 11 services simultaneously. No backward compatibility guarantees. Blocks safe API evolution.
    - **Affected Services**: 9 application services (all except checkoutservice)
    - **Portfolio-Level Recommendation**: Adopt protobuf package versioning (`hipstershop.v1`). Split monolithic `demo.proto` into per-service proto files. Use Buf for breaking change detection.

13. **SEC-Q4: Centralized Identity Integration** — 9 of 11 services score < 2
    - **Score Distribution**: frontend=1, cartservice=1, productcatalogservice=1, checkoutservice=1, paymentservice=1, currencyservice=1, emailservice=1, recommendationservice=1, platform-infra=1 (shippingservice=2, adservice=2)
    - **Impact**: No centralized identity provider. All users are anonymous. No SSO, no federated identity. Blocks personalization and authenticated experiences.
    - **Affected Services**: 9 services
    - **Portfolio-Level Recommendation**: Integrate Amazon Cognito for user authentication. Use IRSA on EKS for service identity. Define Cognito resources in Terraform.

14. **SEC-Q7: Application Security Pipeline** — 7 of 11 services score < 2
    - **Score Distribution**: frontend=1, cartservice=1, productcatalogservice=1, paymentservice=1, currencyservice=1, shippingservice=1, adservice=1 (checkoutservice=2, emailservice=2, recommendationservice=2, platform-infra=2)
    - **Impact**: No security scanning in CI/CD for 7 services. Vulnerabilities in dependencies reach production undetected.
    - **Affected Services**: 7 services
    - **Portfolio-Level Recommendation**: Add language-specific vulnerability scanning to all CI pipelines (`govulncheck`, `npm audit`, `pip-audit`, `dotnet audit`, OWASP dependency-check). Add Trivy container scanning. Configure security gates.

15. **SEC-Q3: API Authentication** — 5 of 11 services score < 2
    - **Score Distribution**: frontend=1, checkoutservice=1, currencyservice=1, recommendationservice=1, platform-infra=1 (cartservice=2, productcatalogservice=2, paymentservice=2, shippingservice=2, emailservice=2, adservice=2)
    - **Impact**: 5 services have no authentication at all. Checkout and payment paths are unauthenticated, creating critical security vulnerability.
    - **Affected Services**: frontend, checkoutservice, currencyservice, recommendationservice, platform-infra
    - **Portfolio-Level Recommendation**: Enable Istio mTLS and AuthorizationPolicies by default. Implement JWT validation on external-facing endpoints. Use API Gateway with Cognito authorizers.

16. **OPS-Q9: Resource Tagging Governance** — 5 of 11 services score < 2
    - **Score Distribution**: productcatalogservice=1, paymentservice=1, currencyservice=1, shippingservice=1, platform-infra=1 (frontend=2, cartservice=2, checkoutservice=2, emailservice=2, recommendationservice=2, adservice=2)
    - **Impact**: Cannot track costs per service, identify resource ownership, or enforce budget controls for 5 services.
    - **Affected Services**: productcatalogservice, paymentservice, currencyservice, shippingservice, platform-infra
    - **Portfolio-Level Recommendation**: Implement `default_tags` in Terraform AWS provider. Enforce tagging via AWS Config required-tags rule.

17. **OPS-Q5: Deployment Strategy** — 4 of 11 services score < 2
    - **Score Distribution**: cartservice=1, checkoutservice=1, currencyservice=1, recommendationservice=1 (frontend=2, productcatalogservice=2, paymentservice=2, shippingservice=2, emailservice=2, adservice=2, platform-infra=2)
    - **Impact**: 4 services deploy directly to production with no staged rollout. Bad deployments affect 100% of users immediately for these services.
    - **Affected Services**: cartservice, checkoutservice, currencyservice, recommendationservice
    - **Portfolio-Level Recommendation**: Adopt ArgoCD with Argo Rollouts on EKS for canary deployments across all services. Define rollout strategies in Helm/Kustomize.

18. **APP-Q4: Long-Running Process Handling** — 3 of 10 applicable services score < 2
    - **Score Distribution**: frontend=1, checkoutservice=1, paymentservice=1 (cartservice=3, productcatalogservice=3, currencyservice=4, shippingservice=3, emailservice=2, recommendationservice=2, adservice=3; platform-infra=N/A)
    - **Impact**: Checkout and payment operations block synchronously with no async patterns. Large carts cause linear latency scaling.
    - **Affected Services**: frontend, checkoutservice, paymentservice
    - **Portfolio-Level Recommendation**: Implement async order processing via Step Functions/SQS. Return order IDs immediately with status polling endpoints.

19. **OPS-Q1: Distributed Tracing** — 3 of 11 services score < 2
    - **Score Distribution**: cartservice=1, shippingservice=1, adservice=1 (frontend=3, productcatalogservice=3, checkoutservice=3, paymentservice=3, currencyservice=3, emailservice=3, recommendationservice=3, platform-infra=2)
    - **Impact**: 3 services have no tracing. Cannot trace requests through cartservice (stateful) or shippingservice (critical path) — debugging production issues across these boundaries is guesswork.
    - **Affected Services**: cartservice, shippingservice, adservice
    - **Portfolio-Level Recommendation**: Implement OpenTelemetry SDK in cartservice (C#), shippingservice (Go), and adservice (Java). Deploy ADOT Collector on EKS for unified trace export to X-Ray.

20. **SEC-Q5: Secrets Management** — 3 of 11 services score < 2
    - **Score Distribution**: checkoutservice=1, paymentservice=1, platform-infra=1 (frontend=2, cartservice=2, productcatalogservice=2, currencyservice=2, shippingservice=2, emailservice=2, recommendationservice=2, adservice=2)
    - **Impact**: Critical-path services (checkout, payment) have no secrets management. Redis connection strings injected via sed. No rotation or audit.
    - **Affected Services**: checkoutservice, paymentservice, platform-infra
    - **Portfolio-Level Recommendation**: Deploy AWS Secrets Manager with External Secrets Operator on EKS. Enable automatic rotation. Store all credentials in Secrets Manager.

21. **INF-Q7: Auto-Scaling** — 2 of 11 services score < 2
    - **Score Distribution**: cartservice=1, currencyservice=1 (frontend=2, productcatalogservice=3, checkoutservice=2, paymentservice=2, shippingservice=3, emailservice=2, recommendationservice=3, adservice=2, platform-infra=3)
    - **Impact**: cartservice and currencyservice cannot scale at all — single replica with no HPA. Critical for a stateful cart service.
    - **Affected Services**: cartservice, currencyservice
    - **Portfolio-Level Recommendation**: Configure HPA for all services with minimum 2 replicas for P0 services. Use Karpenter on EKS for node scaling.

### 💡 Improvement Opportunities

> Criteria scoring < 3 in 3+ repos (not already classified as Foundational Blocker). Important but not blocking.

1. **INF-Q9: High Availability and Fault Isolation** — 10 of 11 applicable services score < 3
   - **Score Distribution**: frontend=2, cartservice=2, productcatalogservice=2, checkoutservice=2, paymentservice=2, currencyservice=1, emailservice=2, recommendationservice=2, adservice=2, platform-infra=2 (shippingservice=3)
   - **Impact**: Most services run single replicas with no pod anti-affinity or topology spread. AZ failures take down services.
   - **Affected Services**: 10 services (all except shippingservice)
   - **Portfolio-Level Recommendation**: Set minimum 2 replicas with topology spread constraints across AZs for all production services. Add PodDisruptionBudgets. Deploy EKS across 3+ AZs.

2. **INF-Q6: API Entry Point** — 6 of 11 services score < 3
   - **Score Distribution**: frontend=2, cartservice=2, productcatalogservice=2, currencyservice=1, recommendationservice=2, platform-infra=2 (checkoutservice=3, paymentservice=3, shippingservice=3, emailservice=3, adservice=3)
   - **Impact**: No API Gateway with throttling, authentication, or request validation for 6 services.
   - **Affected Services**: frontend, cartservice, productcatalogservice, currencyservice, recommendationservice, platform-infra
   - **Portfolio-Level Recommendation**: Deploy AWS ALB with WAF for frontend ingress. Use API Gateway or App Mesh for internal service traffic management.

3. **INF-Q5: Network Security** — 5 of 11 services score < 3
   - **Score Distribution**: frontend=2, cartservice=2, currencyservice=1, emailservice=2, platform-infra=2 (productcatalogservice=3, checkoutservice=3, paymentservice=3, shippingservice=3, recommendationservice=3, adservice=3)
   - **Impact**: Network policies exist but are disabled by default for 5 services. No VPC-level segmentation defined.
   - **Affected Services**: frontend, cartservice, currencyservice, emailservice, platform-infra
   - **Portfolio-Level Recommendation**: Enable NetworkPolicies by default. Define VPC with private subnets in Terraform for EKS migration.

4. **INF-Q2: Managed Databases** — 5 of 11 services score < 3
   - **Score Distribution**: cartservice=2, productcatalogservice=2, paymentservice=2, currencyservice=1, emailservice=2, platform-infra=2 (frontend=3, checkoutservice=3, shippingservice=3, recommendationservice=3, adservice=3)
   - **Impact**: Default Redis is self-managed with no persistence, failover, or backups. productcatalogservice uses a local JSON file.
   - **Affected Services**: cartservice, productcatalogservice, paymentservice, currencyservice, emailservice, platform-infra
   - **Portfolio-Level Recommendation**: Migrate to Amazon ElastiCache/DynamoDB (preferred) with Multi-AZ and automated backups.

5. **SEC-Q6: Compute Hardening and Patching** — 4 of 11 services score < 3
   - **Score Distribution**: paymentservice=2, currencyservice=2, recommendationservice=2, adservice=2 (frontend=3, cartservice=3, productcatalogservice=3, checkoutservice=3, shippingservice=3, emailservice=3, platform-infra=3)
   - **Impact**: 4 services lack vulnerability scanning. Alpine-based images without CVE monitoring may accumulate vulnerabilities.
   - **Affected Services**: paymentservice, currencyservice, recommendationservice, adservice
   - **Portfolio-Level Recommendation**: Add Trivy/ECR image scanning to all CI pipelines. Enable Amazon Inspector for runtime vulnerability detection on EKS.
### Per-Category Analysis

#### Infrastructure & DevOps

**Portfolio Score: 2.09 / 4.0**

**Common Patterns:**
- Managed Kubernetes (GKE Autopilot): present in 11 services — strong containerization baseline
- Terraform IaC: present in 10 services — good IaC foundation
- CI/CD via GitHub Actions: present in 10 services — solid automation baseline

**Critical Gaps:**
1. Async Messaging (INF-Q4): score 1 in all 11 services — no messaging infrastructure exists
2. Backup and Recovery (INF-Q8): score 1 in all 11 services — no data protection
3. Workflow Orchestration (INF-Q3): score 1 in all 11 services — hardcoded orchestration logic
4. currencyservice IaC/CI/CD (INF-Q10=1, INF-Q11=1): critical outlier with zero infrastructure-as-code

#### Application Architecture

**Portfolio Score: 2.45 / 4.0**

**Common Patterns:**
- Microservices architecture: all 10 application services are independently deployable with clear boundaries
- gRPC communication: consistent protocol across all services via shared protobuf definitions
- Clean data access patterns: DATA-Q2 scores of 3-4 across most services

**Critical Gaps:**
1. Async vs Sync (APP-Q3): score 1 in all 10 application services — 100% synchronous communication
2. API Versioning (APP-Q5): score 1 in 9 of 10 services — no versioning strategy
3. Long-Running Process Handling (APP-Q4): score 1 in 3 critical-path services (frontend, checkout, payment)

#### Data Platform

**Portfolio Score: 2.75 / 4.0**

**Common Patterns:**
- No stored procedures (DATA-Q4): score 4 in all services — all logic in application layer
- Redis as sole database engine: single data store technology across portfolio
- Clean data access abstractions: cartservice's ICartStore interface pattern is exemplary

**Critical Gaps:**
1. Self-managed Redis default: in-cluster Redis with emptyDir volume (no persistence)
2. Static data sources: productcatalogservice uses bundled JSON file, adservice uses hardcoded in-memory map
3. No managed database for new workloads (e.g., order history, user behavior data for AI)

#### Security Baseline

**Portfolio Score: 1.49 / 4.0** — Lowest category across the portfolio

**Common Patterns:**
- Container hardening is strong: distroless/Alpine images, non-root users, dropped capabilities across all services
- Istio AuthorizationPolicies defined but disabled by default

**Critical Gaps:**
1. Audit Logging (SEC-Q1): score 1 in all 11 services — no audit trail anywhere
2. Encryption at Rest (SEC-Q2): score 1 in all 11 services — no encryption on any data store
3. Centralized Identity (SEC-Q4): score 1 in 9 services — no identity provider
4. Application Security Pipeline (SEC-Q7): score 1 in 7 services — no security scanning in CI/CD
5. API Authentication (SEC-Q3): score 1 in 5 services including frontend and checkout — unauthenticated critical paths

#### Operations & Observability

**Portfolio Score: 1.44 / 4.0** — Second lowest category

**Common Patterns:**
- OpenTelemetry instrumentation exists in 8 of 11 services (but disabled by default)
- Kubernetes health probes configured across all services
- Structured JSON logging in most services

**Critical Gaps:**
1. SLO Definitions (OPS-Q2): score 1 in all 11 services — no service level objectives
2. Business Metrics (OPS-Q3): score 1 in all 11 services — no business outcome visibility
3. Anomaly Detection (OPS-Q4): score 1 in all 11 services — no alerting
4. Incident Response (OPS-Q7): score 1 in all 11 services — no runbooks or automation
5. Observability Ownership (OPS-Q8): score 1 in all 11 services — no per-service ownership

---

## Portfolio Modernization Roadmap

> Priority-based phased roadmap with fixed phase names. Since no dependency_overrides
> were provided, services are ordered by priority (P0 → P1 → P2) then by score.
> Dependency-based ordering is not available — provide `dependency_overrides` for a
> more accurate roadmap.

### Sequencing Principles

1. **Foundation First**: Shared infrastructure and platform capabilities before service-specific work
2. **Priority Order**: P0 services before P1, P1 before P2
3. **Risk Mitigation**: Lowest-scoring services addressed earlier within each priority tier
4. **Parallel Tracks**: Independent services can be modernized concurrently
5. **Quick Wins**: Early wins build momentum and demonstrate value

### Phase 0 — Cross-Cutting Foundation (Mo 0–1)

**Objective**: Establish shared capabilities, address portfolio-wide blockers, and bring currencyservice to baseline.

**Cross-Cutting Activities:**
- Deploy AWS CloudTrail with immutable S3 storage (SEC-Q1 blocker for all 11 services)
- Establish AWS KMS key management and enable encryption at rest on all data stores (SEC-Q2 blocker)
- Deploy Amazon SQS/SNS messaging infrastructure for event-driven patterns (INF-Q4 blocker)
- Implement centralized audit logging via CloudWatch Logs (SEC-Q1)
- Define SLOs for all P0 services (OPS-Q2)
- Deploy ADOT Collector on EKS for unified observability (OPS-Q1, OPS-Q3, OPS-Q4)
- Establish tagging governance with Terraform `default_tags` (OPS-Q9)
- Deploy AWS Secrets Manager with External Secrets Operator (SEC-Q5)
- Adopt protobuf versioning standard (`hipstershop.v1`) (APP-Q5)

**currencyservice Modernization (INF-Q10=1, INF-Q11=1):**
- Create Terraform modules for currencyservice infrastructure
- Build CI/CD pipeline with GitHub Actions
- Create Kubernetes manifests, Helm chart, and Kustomize overlays
- Add unit tests for conversion logic
- Estimated Effort: High

**Organizational Enablers:**
- Training: EKS migration, Terraform for AWS, GitOps with ArgoCD, Amazon Bedrock
- Tooling: ArgoCD/Flux on EKS, ADOT Collector, CloudWatch dashboards
- Standards: API versioning policy, tagging governance, security scanning requirements

**Estimated Effort**: High

### Phase 1 — Quick Wins (Mo 1–2)

**Objective**: Modernize P0 critical-path services. Establish patterns and reference implementations.

**Services in Scope:**

1. **platform-infra** (Score: 1.74 / 4.0)
   - Current State: GKE Autopilot IaC, self-managed Redis, no security baseline
   - Target State: EKS cluster with Terraform, ElastiCache/DynamoDB, CloudTrail, KMS
   - Key Activities:
     - Migrate Terraform from GCP to AWS (EKS, VPC, ElastiCache)
     - Deploy ArgoCD for GitOps (preferred)
     - Enable CloudTrail, KMS, Secrets Manager
   - Estimated Effort: High

2. **paymentservice** (P0, Score: 1.92 / 4.0)
   - Current State: No secrets management, no encryption, no SLOs
   - Target State: Secured payment pipeline with encryption, auth, and monitoring
   - Key Activities:
     - Implement secrets management for payment credentials
     - Add npm audit to CI pipeline
     - Define payment-specific SLOs (99.95% availability)
   - Estimated Effort: Medium

3. **frontend** (P0, Score: 2.05 / 4.0)
   - Current State: Unauthenticated, no API versioning, synchronous to all backends
   - Target State: Authenticated entry point with API Gateway, versioned APIs
   - Key Activities:
     - Deploy ALB with WAF for frontend ingress
     - Implement Cognito authentication
     - Add async patterns for non-critical calls (ads, recommendations)
   - Estimated Effort: Medium

4. **cartservice** (P0, Score: 2.11 / 4.0)
   - Current State: Self-managed Redis with emptyDir, no tracing, no auto-scaling
   - Target State: DynamoDB-backed cart with encryption, backups, and observability
   - Key Activities:
     - Implement DynamoDBCartStore via ICartStore interface
     - Add OpenTelemetry SDK for C#
     - Configure HPA with minimum 2 replicas
   - Estimated Effort: Medium

5. **productcatalogservice** (P0, Score: 2.11 / 4.0)
   - Current State: JSON file data source, no backups, no versioning
   - Target State: DynamoDB-backed catalog with versioned API
   - Key Activities:
     - Migrate product data to DynamoDB
     - Add API versioning to proto definitions
     - Implement catalog change events via SNS
   - Estimated Effort: Medium

6. **checkoutservice** (P0, Score: 2.16 / 4.0)
   - Current State: Hardcoded synchronous orchestration, no secrets management, no auth
   - Target State: Step Functions-orchestrated checkout with async email/notification
   - Key Activities:
     - Migrate PlaceOrder to Step Functions state machine
     - Decouple email confirmation to SQS
     - Implement secrets management for all credentials
   - Estimated Effort: High

**Expected Outcomes:**
- EKS cluster operational with GitOps deployment
- Managed database (DynamoDB/ElastiCache) replacing self-managed Redis
- Security baseline established (CloudTrail, KMS, Cognito)
- Reference patterns for other services to follow

### Phase 2 — Foundation (Mo 2–4)

**Objective**: Modernize P1 services. Replicate proven patterns from Phase 1.

**Services in Scope:**

1. **currencyservice** (P1, Score: 1.67 / 4.0)
   - Current State: No IaC, no CI/CD, no tests, lowest score in portfolio
   - Target State: Fully modernized with IaC, CI/CD, testing, and observability
   - Key Activities:
     - Complete IaC and CI/CD from Phase 0
     - Migrate exchange rates to DynamoDB
     - Add unit and integration tests
     - Enable mTLS and authentication
   - Estimated Effort: High

2. **recommendationservice** (P1, Score: 2.04 / 4.0)
   - Current State: Random product sampling, no tests, no auth
   - Target State: AI-powered recommendations with Bedrock, proper testing
   - Key Activities:
     - Add Python unit tests
     - Implement caching layer with DynamoDB
     - Implement Bedrock integration for AI recommendations
   - Estimated Effort: Medium

3. **shippingservice** (P1, Score: 2.39 / 4.0)
   - Current State: Highest application score, but tracing is TODO stub
   - Target State: Fully observable with tracing, SLOs, and canary deployments
   - Key Activities:
     - Implement OpenTelemetry tracing (complete TODO)
     - Define SLOs and CloudWatch alarms
     - Implement canary deployments
   - Estimated Effort: Low

**Parallel Tracks:**
- currencyservice (IaC/CI/CD) can proceed independently
- shippingservice (observability) can proceed independently
- recommendationservice (AI integration) depends on DynamoDB from Phase 1

### Phase 3 — Advanced (Mo 4–6+)

**Objective**: Optimize P2 services. Implement advanced capabilities. Continuous improvement.

**Services in Scope:**

1. **adservice** (P2, Score: 2.07 / 4.0)
   - Current State: Hardcoded in-memory ads, no tracing, no tests
   - Target State: DynamoDB-backed dynamic ads with AI-powered targeting
   - Key Activities:
     - Externalize ad data to DynamoDB
     - Implement OpenTelemetry Java agent
     - Add JUnit tests
     - Integrate Bedrock for dynamic ad generation
   - Estimated Effort: Medium

2. **emailservice** (P2, Score: 2.09 / 4.0)
   - Current State: Synchronous email delivery, no async patterns
   - Target State: SQS-based async email processing with monitoring
   - Key Activities:
     - Migrate to SQS-based email processing
     - Add Python unit tests
     - Define email delivery SLOs
   - Estimated Effort: Low

**Advanced Capabilities (All Services):**
- Full AI agent integration across the platform using Amazon Bedrock
- Comprehensive observability with X-Ray distributed tracing across all 11 services
- GitOps-based canary deployments with automated rollback for all services
- API Gateway consolidation with unified authentication

### Total Portfolio Effort

**Total Estimated Effort**: High
**Expected Timeline**: 6 months (with 3 parallel tracks)
- Track 1: Platform infrastructure and P0 services (Phases 0-1)
- Track 2: P1 services modernization (Phase 2)
- Track 3: P2 services and AI integration (Phase 3)
## AWS Modernization Pathways

> The AWS Modernization Pathways framework recognizes there is no "one-size-fits-all"
> approach. A customer portfolio may be divided into multiple pathways depending on
> workloads and priorities; these pathways can be executed in parallel.

### Portfolio Pathway Summary

| Pathway | Services Triggered | % of Portfolio | Priority | Est. Effort |
|---------|--------------------|----------------|----------|-------------|
| Move to Cloud Native | 0 | 0% | — | — |
| Move to Containers | 0 | 0% | — | — |
| Move to Open Source | 0 | 0% | — | — |
| Move to Managed Databases | 5 | 45% | Medium | Medium |
| Move to Managed Analytics | 0 | 0% | — | — |
| Move to Modern DevOps | 1 | 9% | Low | Medium |
| Move to AI | 10 | 91% | High | Medium |

### Portfolio Pathway Aggregation

| Pathway | Triggered | Not Triggered | Not Applicable |
|---------|-----------|---------------|----------------|
| Move to Cloud Native | — | frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice, adservice | platform-infra |
| Move to Containers | — | frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice, adservice | platform-infra |
| Move to Open Source | — | frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice, adservice, platform-infra | — |
| Move to Managed Databases | cartservice, productcatalogservice, paymentservice, emailservice, platform-infra | frontend, checkoutservice, currencyservice, shippingservice, recommendationservice, adservice | — |
| Move to Managed Analytics | — | — | frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice, adservice, platform-infra |
| Move to Modern DevOps | currencyservice | frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, shippingservice, emailservice, recommendationservice, adservice, platform-infra | — |
| Move to AI | frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice, adservice | — | platform-infra |

### Per-Service Pathway Assignment

| Service | Cloud Native | Containers | Open Source | Managed DB | Managed Analytics | Modern DevOps | Move to AI |
|---------|-------------|------------|-------------|------------|-------------------|---------------|------------|
| frontend | — | — | — | — | N/A | — | ✅ |
| cartservice | — | — | — | ✅ | N/A | — | ✅ |
| productcatalogservice | — | — | — | ✅ | N/A | — | ✅ |
| checkoutservice | — | — | — | — | N/A | — | ✅ |
| paymentservice | — | — | — | ✅ | N/A | — | ✅ |
| currencyservice | — | — | — | — | N/A | ✅ | ✅ |
| shippingservice | — | — | — | — | N/A | — | ✅ |
| emailservice | — | — | — | ✅ | N/A | — | ✅ |
| recommendationservice | — | — | — | — | N/A | — | ✅ |
| adservice | — | — | — | — | N/A | — | ✅ |
| platform-infra | N/A | N/A | — | ✅ | N/A | — | N/A |

### Pathway Dependencies and Parallel Execution

**Sequential Dependencies:**
- Move to Containers should precede Move to Cloud Native (containerize before decomposing) — not applicable, both untriggered
- Move to Open Source may precede Move to Managed Databases (migrate off proprietary first) — not applicable, no commercial databases
- Move to Modern DevOps enables faster execution of all other pathways (CI/CD accelerates delivery) — relevant for currencyservice
- Move to Managed Databases is often a prerequisite for Move to AI (data foundations needed) — relevant for 5 services

**Parallel Execution Tracks:**
- **Track 1**: Move to Managed Databases (5 services) — can start immediately
- **Track 2**: Move to AI (10 services) — can start in parallel, depends on data foundations for some services
- **Track 3**: Move to Modern DevOps (currencyservice only) — must complete before other pathways apply to currencyservice

### Pathway Details

#### Move to AI

- **Services Affected**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice, adservice (10 total)
- **Portfolio Priority**: High (91% of services triggered)
- **Common Trigger Criteria**:
  - No AI/agent framework imports detected: affects 10 services
  - No vector database infrastructure: affects 10 services
  - No RAG implementation patterns: affects 10 services
  - No agent evaluation frameworks: affects 10 services
- **Representative AWS Services**: Amazon Bedrock (preferred), Amazon Bedrock AgentCore, Amazon OpenSearch Service (vector engine), Amazon Bedrock Knowledge Bases, Amazon Q Developer
- **Key Activities**:
  1. Establish Bedrock access and API integration patterns across Go, Python, C#, Java, and Node.js services
  2. Build AI-powered shopping assistant using Bedrock with existing gRPC services as tools
  3. Implement semantic product search with OpenSearch vector engine
  4. Deploy AI-powered recommendation engine replacing random sampling
  5. Enable dynamic ad content generation with Bedrock foundation models
- **Cross-Service Synergies**: Shared Bedrock agent framework, shared vector store for product embeddings, unified agent evaluation harness
- **Estimated Effort**: Medium across 10 services
- **Roadmap Phase Alignment**: Phase 2 (foundation services) and Phase 3 (advanced capabilities)
- **Relevant Learning Materials**: Module 7 — Move to AI

#### Move to Managed Databases

- **Services Affected**: cartservice, productcatalogservice, paymentservice, emailservice, platform-infra (5 total)
- **Portfolio Priority**: Medium (45% of services triggered)
- **Common Trigger Criteria**:
  - INF-Q2 ≤ 2 — self-managed in-cluster Redis (default): affects 5 services
  - DATA-Q3 — mixed version pinning: affects 3 services
- **Representative AWS Services**: Amazon DynamoDB (preferred), Amazon ElastiCache for Redis, Amazon MemoryDB for Redis
- **Key Activities**:
  1. Migrate in-cluster Redis to Amazon ElastiCache for Redis or DynamoDB (preferred)
  2. Migrate productcatalogservice data from JSON file to DynamoDB
  3. Enable Multi-AZ, automated backups, encryption at rest on all managed databases
  4. Implement DynamoDBCartStore using cartservice's existing ICartStore interface pattern
- **Cross-Service Synergies**: Shared DynamoDB table design patterns, unified Terraform modules for database provisioning
- **Estimated Effort**: Medium across 5 services
- **Roadmap Phase Alignment**: Phase 1 (Quick Wins)
- **Relevant Learning Materials**: Module 4 — Move to Managed Databases

#### Move to Modern DevOps

- **Services Affected**: currencyservice (1 total)
- **Portfolio Priority**: Low (9% of services — only 1 service, but High priority for that service)
- **Common Trigger Criteria**:
  - INF-Q10 = 1 — zero IaC coverage
  - INF-Q11 = 1 — zero CI/CD automation
  - OPS-Q5 = 1 — no deployment strategy
  - OPS-Q6 = 1 — no integration tests
- **Representative AWS Services**: Amazon EKS (preferred), Amazon ECR, AWS CodeBuild, Terraform (preferred), ArgoCD on EKS (preferred for GitOps)
- **Key Activities**:
  1. Create Terraform modules for currencyservice EKS deployment
  2. Build GitHub Actions CI/CD pipeline with test → build → scan → deploy stages
  3. Create Kubernetes manifests, Helm chart, and HPA configuration
  4. Add Jest unit tests for conversion logic
  5. Adopt GitOps with ArgoCD for declarative deployment
- **Cross-Service Synergies**: Use existing platform-infra Terraform patterns and Helm chart templates as starting point
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 0 (Cross-Cutting Foundation)
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps
## Integration Opportunities

### Shared Service Extraction

**Opportunity: Centralized Authentication Service**
- **Current State**: No authentication exists in any service. SEC-Q3 scores 1-2 across all 11 services.
- **Proposed Solution**: Deploy Amazon Cognito as centralized IdP. Implement ALB with Cognito integration for frontend. Use Istio mTLS on EKS for service-to-service auth. Define all resources in Terraform (preferred).
- **Benefits**: Single authentication point, consistent identity across all services, enables personalization and AI agent authentication
- **Effort**: High
- **Priority**: High

**Opportunity: Centralized Audit Logging**
- **Current State**: SEC-Q1 = 1 across all 11 services. No audit trail anywhere.
- **Proposed Solution**: Deploy AWS CloudTrail with S3 Object Lock. Configure CloudWatch Logs with Fluent Bit on EKS. Centralize all service logs with consistent retention policies.
- **Benefits**: Single audit trail, compliance readiness, forensic capability, centralized log analysis
- **Effort**: Medium
- **Priority**: High

**Opportunity: Unified Observability Stack**
- **Current State**: OPS-Q1 ranges 1-3. 8 services have OpenTelemetry instrumented but disabled. 3 services have no tracing at all.
- **Proposed Solution**: Deploy ADOT Collector as DaemonSet on EKS. Enable tracing by default. Export to AWS X-Ray for traces and CloudWatch for metrics. Create per-service dashboards.
- **Benefits**: End-to-end distributed tracing, consistent metrics, unified dashboards, reduced debugging time
- **Effort**: Medium
- **Priority**: High

### Event-Driven Architecture

**Opportunity: Checkout-to-Email Decoupling**
- **Current State**: checkoutservice calls emailservice synchronously via gRPC. Email delivery blocks the checkout response.
- **Proposed Solution**: Publish "OrderPlaced" events to Amazon SNS. emailservice subscribes via SQS and processes asynchronously. Use EKS-hosted consumers (avoiding serverless per preferences).
- **Benefits**: Decoupled checkout from email latency, improved checkout response time, retry capability for failed emails
- **Effort**: Medium

**Opportunity: Product Catalog Change Events**
- **Current State**: Product catalog updates require container rebuild. No change notification to consumers.
- **Proposed Solution**: When product data moves to DynamoDB, enable DynamoDB Streams → SNS/EventBridge for catalog change events. recommendationservice and frontend can react to catalog updates asynchronously.
- **Benefits**: Real-time catalog propagation, pre-computed recommendations, reduced synchronous dependency
- **Effort**: Medium

### API Gateway Consolidation

- **Current State**: Frontend exposed via raw LoadBalancer with no throttling, auth, or WAF. Internal services have no API management.
- **Proposed Solution**: Deploy AWS ALB with WAF for frontend ingress on EKS. Use API Gateway for any external API endpoints. Implement rate limiting and request validation.
- **Benefits**: Consistent auth, DDoS protection, rate limiting, request validation, centralized API monitoring
- **Effort**: Medium

### Observability Unification

- **Current State**: 8 services have OpenTelemetry (disabled by default), 3 have none. No centralized dashboards, alarms, or SLOs.
- **Proposed Solution**: Deploy ADOT Collector on EKS with AWS X-Ray and CloudWatch integration. Enable tracing by default. Create CloudWatch dashboards per service. Define SLOs and alarms in Terraform.
- **Benefits**: End-to-end tracing across all 11 services, consistent metrics, centralized alerting, data-driven reliability decisions
- **Effort**: Medium

---

## Risk Assessment

### Risk Matrix

| Risk | Likelihood | Impact | Priority | Mitigation | Phase |
|------|------------|--------|----------|------------|-------|
| Cart data loss (Redis emptyDir) | High | High | 🔴 Critical | Migrate to DynamoDB/ElastiCache with persistence and backups | Phase 1 |
| Cascading checkout failure (sync chain) | High | High | 🔴 Critical | Implement Step Functions orchestration with compensation | Phase 1 |
| Security breach (no auth, no encryption) | High | High | 🔴 Critical | Deploy CloudTrail, KMS, Cognito, mTLS | Phase 0 |
| currencyservice outage (no IaC/CI/CD) | Medium | High | 🟠 High | Complete Modern DevOps pathway for currencyservice | Phase 0 |
| Silent service degradation (no alerting) | High | Medium | 🟠 High | Deploy CloudWatch Alarms and anomaly detection | Phase 0 |
| Undetected vulnerabilities (no scanning) | High | Medium | 🟠 High | Add security scanning to all CI pipelines | Phase 0 |
| Platform-infra failure (shared infrastructure) | Medium | High | 🟠 High | Implement HA for EKS cluster and data tier | Phase 1 |
| AZ failure with single replicas | Medium | Medium | 🟡 Medium | Configure multi-replica with topology spread | Phase 1 |
| Proto breaking change (no versioning) | Medium | Medium | 🟡 Medium | Adopt protobuf versioning and Buf breaking detection | Phase 0 |

### Single Points of Failure

- **platform-infra**: Manages shared GKE cluster and Redis for all 11 services. Any infrastructure issue affects 100% of portfolio.
- **Redis (in-cluster)**: Single-replica with emptyDir volume. Pod restart = complete cart data loss for all users.
- **currencyservice**: No IaC or CI/CD. Manual deployment. Any infrastructure loss requires manual reconstruction.

### Data Availability Risks

- **Redis cart data**: Self-managed with emptyDir (ephemeral). No backups, no persistence, no failover. Data loss on any pod disruption.
- **Product catalog**: Static JSON file bundled in container image. Updates require rebuild and redeployment.
- **Ad data**: Hardcoded in Java application memory. No external storage. Data changes require code changes.

### Observability Blind Spots

- **cartservice** (OPS-Q1=1): No distributed tracing on the stateful cart service. Cannot trace cart operations across service boundaries.
- **shippingservice** (OPS-Q1=1): Tracing is a TODO stub despite being on the critical checkout path.
- **adservice** (OPS-Q1=1): No tracing on the ad service. Cannot correlate ad serving performance with frontend latency.
- **All services** (OPS-Q4=1): No alerting anywhere. Degradation is invisible until user-reported.

---

## Resource Allocation Recommendations

### Team Structure

**Recommended Approach**: Centralized platform team + service teams (21 cross-cutting concerns warrant centralized approach)

**Platform Team** (4-6 engineers):
- Responsibilities: EKS cluster management, shared infrastructure (VPC, KMS, CloudTrail, ADOT), GitOps pipeline, security scanning, Terraform modules
- Skills Required: EKS, Terraform, ArgoCD, AWS security services (CloudTrail, KMS, Cognito), OpenTelemetry

**Service Teams** (2-3 engineers per team, 3-4 teams):
- Responsibilities: Service-specific modernization, database migration, AI integration, testing
- Skills Required: Service-specific language (Go, Python, C#, Java, Node.js), DynamoDB, Amazon Bedrock, gRPC

### Skill Gaps

| Skill | Required For | Currently Available? | Priority |
|-------|-------------|---------------------|----------|
| Amazon EKS | GKE → EKS migration | No (GKE experience exists) | High |
| Terraform for AWS | All AWS infrastructure | Partial (GCP Terraform exists) | High |
| ArgoCD / GitOps | Deployment modernization | No | High |
| AWS Security (CloudTrail, KMS, Cognito) | Security baseline | No | High |
| Amazon DynamoDB | Database migration | No | High |
| Amazon Bedrock | AI integration | No | Medium |
| OpenTelemetry / X-Ray | Observability | Partial (OTel instrumented in 8 services) | Medium |
| AWS Step Functions | Workflow orchestration | No | Medium |
| Amazon SQS/SNS | Event-driven architecture | No | Medium |

### Training Recommendations

1. **Immediate (Phase 0)**: EKS Workshop, Terraform for AWS, GitOps with ArgoCD, AWS Security Fundamentals
2. **Phase 1**: DynamoDB Developer Guide, CloudWatch observability, Step Functions
3. **Phase 2-3**: Amazon Bedrock Getting Started, Agentic AI on AWS, Move to AI Learning Plan

### External Support

- **AWS Professional Services**: Recommended for EKS migration and security baseline establishment (Phase 0-1). High-impact, time-sensitive activities.
- **AWS Solutions Architect**: Engage for architecture review of the DynamoDB migration pattern and Step Functions checkout workflow design.
- **Consulting Partner**: Consider for accelerating Phase 0 shared infrastructure work if internal team bandwidth is limited.

---

## AWS Programs & Engagement Recommendations

> **This section appears ONLY in portfolio reports, NEVER in individual reports.**
> Programs are engagement-level decisions scoped to the customer's overall estate.

### Recommended Programs

| Program | Acronym | Relevance | Trigger Findings | Next Step |
|---------|---------|-----------|-----------------|-----------|
| Migration Acceleration Program | MAP | Portfolio-wide modernization from GCP to AWS | All 11 services have overall score < 2.5 (highest: shippingservice at 2.39) | Request MAP engagement via AWS Solutions Architect |
| Microsoft Modernization Program | MMP | C#/.NET workload migration | cartservice uses C# on .NET 10.0 | Request MMP assessment for cartservice migration path |
| Experience-Based Acceleration | EBA | Multi-pathway modernization execution | All 11 services have triggered pathways AND score < 3.0. Focus: Move to AI (10 services), Move to Managed Databases (5 services) | Request EBA engagement focused on Move to AI and Move to Managed Databases pathways |

### Program Details

**Migration Acceleration Program (MAP)**
- Recommended because all 11 services have overall scores below 2.5, indicating significant modernization effort required across the entire portfolio. The portfolio is migrating from GCP to AWS with a comprehensive cloud-native modernization agenda.
- MAP provides migration credits, tooling, and expert guidance to accelerate large-scale migration and modernization programs.
- Suggested timing: Engage during Phase 0 to support the GKE → EKS migration and security baseline establishment.

**Microsoft Modernization Program (MMP)**
- Recommended because cartservice is built on C# / .NET 10.0. While .NET on Linux containers is well-supported on EKS, the MMP provides specialized guidance for .NET workload modernization on AWS.
- MMP provides .NET-specific migration tooling, guidance for .NET on EKS/Fargate, and access to .NET modernization specialists.
- Suggested timing: Engage during Phase 1 when cartservice is being migrated to DynamoDB and EKS.

**Experience-Based Acceleration (EBA)**
- Recommended because all 11 services have at least one triggered pathway and overall scores below 3.0. The portfolio has two major pathways: Move to AI (10 services, 91%) and Move to Managed Databases (5 services, 45%).
- EBA provides hands-on technical workshops and accelerated execution for specific modernization pathways.
- Suggested timing: Engage during Phase 1-2 for focused workshops on Amazon Bedrock integration and DynamoDB migration patterns.

> These are engagement-level recommendations. Discuss with your AWS Solutions Architect
> or Partner to determine eligibility and timing.
## Recommended Self-Paced Learning Materials

> Includes relevant links based on portfolio-wide skill gaps and triggered pathways.

**Module 2: Move to Cloud Native (Containers and Serverless):**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html

**Module 3: Move to Containers with Amazon ECS and EKS:**
- AWS Modernization Pathways: Move to Containers with Amazon EKS — https://skillbuilder.aws/learning-plan/GNYBZ9X9EM/aws-modernization-pathways-move-to-containers-with-amazon-eks-includes-labs/1HB9MKXD2N
- Introduction to Containers — https://skillbuilder.aws/learn/CUCA1DK47V/introduction-to-containers/XJ58VC1FF5
- Amazon EKS Primer — https://skillbuilder.aws/learn/Z521GMBP1J/amazon-eks-primer/NGM5AF9K72
- Deploy Applications on Amazon EKS (Lab) — https://skillbuilder.aws/learn/2B5XUE2V9C/lab--deploy-applications-on-amazon-elastic-kubernetes-service-eks/SM5HZNTY9J
- EKS Workshop — https://www.eksworkshop.com/
- EKS Auto Mode Workshop — https://catalog.workshops.aws/workshops/aadbd25d-43fa-4ac3-ae88-32d729af8ed4

**Module 4: Move to Managed Databases:**
- AWS Modernization Pathways: Move to Managed Databases — https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC/aws-modernization-pathways-move-to-managed-databases-includes-labs/2S2QZKG9DV
- Introduction to Building with AWS Databases — https://skillbuilder.aws/learn/HYKKWEN9ZS/introduction-to-building-with-aws-databases/V7RVH2KY91
- AWS Database Migration Service (DMS) Getting Started — https://skillbuilder.aws/learn/ND246G8Y3W/aws-database-migration-service-aws-dms-getting-started/QK5CCBP464
- Introduction to Amazon DynamoDB (Lab) — https://skillbuilder.aws/learn/6DYXN7K7ZQ/lab--introduction-to-amazon-dynamodb/GZ3EU55RYJ
- Amazon DynamoDB for Serverless Architecture — https://skillbuilder.aws/learn/SY1Y83VKTB/amazon-dynamodb-for-serverless-architectures/K9NM3PHH3S

**Module 6: Move to Modern DevOps:**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
- AWS CloudFormation Getting Started — https://skillbuilder.aws/learn/RH22P2RXU4/aws-cloudformation-getting-started/KEK5BT6HSE
- AWS PartnerCast: Automate EKS Deployments With GitOps Using ArgoCD and GitHub Actions — https://skillbuilder.aws/learn/D9U7XMXP31/aws-partnercast--tech-talks--automate-eks-deployments-with-gitops-using-argocd-and-github-actions--technical/Z4M9Z8FY88
- EKS Workshop: Automation — https://www.eksworkshop.com/docs/automation/
- EKS SaaS GitOps Workshop — https://catalog.workshops.aws/eks-saas-gitops/en-US/03-lab1

**Module 7: Move to AI:**
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
- Introduction to Generative AI: Art of the Possible — https://skillbuilder.aws/learn/ZEVZZ1D4AS/introduction-to-generative-ai--art-of-the-possible/Y7MTGJCW1U
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
- Essentials for Prompt Engineering — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
- Build and Evaluate RAG Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
- Amazon Q Developer Getting Started — https://skillbuilder.aws/learn/BQMRXE8AB4/amazon-q-developer-getting-started/JY4XXGZDJA
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY

---

## Portfolio-Level Findings

> These questions evaluate capabilities that can only be assessed by looking across
> multiple repos. They are distinct from cross-cutting analysis (which aggregates
> individual scores). Individual report scores are never overridden.

### PORT-MOD-Q1: IaC Standardization

- **Score**: 2
- **Finding**: Terraform is the primary IaC tool used by 10 of 11 services, providing a strong standardization foundation. Kubernetes manifests, Helm charts, and Kustomize overlays are consistently used across the same 10 services. However, currencyservice has **zero IaC coverage** (INF-Q10=1) — it has only a Dockerfile with no Terraform, no Kubernetes manifests, no Helm chart. The Terraform coverage for the remaining 10 services is GCP-focused and does not cover AWS resources. Multiple deployment tools are in use (Terraform + Skaffold + Helm + Kustomize) without clear separation of concerns.
- **Evidence**: `terraform/main.tf` (GKE cluster for 10 services), currencyservice repo (no .tf files, no Chart.yaml, no kustomization.yaml), `helm-chart/` (shared Helm chart for 10 services)
- **Recommendation**: Standardize on Terraform (preferred) for all infrastructure + Helm/Kustomize via GitOps for application deployment. Prioritize creating IaC for currencyservice. Migrate Terraform from GCP to AWS provider. Adopt a single deployment path (GitOps with ArgoCD, preferred).

### PORT-MOD-Q2: Shared Observability Platform

- **Score**: 1
- **Finding**: No centralized observability stack exists. OpenTelemetry instrumentation is present in 8 of 11 services but is **disabled by default** (`ENABLE_TRACING` not set, `opentelemetryCollector.create: false`). Three services (cartservice, shippingservice, adservice) have no tracing instrumentation at all — only TODO stubs. No shared CloudWatch dashboards, no centralized log aggregation, no cross-service trace correlation configured. Each service's observability is independent and mostly non-functional in the default deployment.
- **Evidence**: `helm-chart/values.yaml` (`opentelemetryCollector.create: false`, `googleCloudOperations.tracing: false`), cartservice/shippingservice/adservice OPS-Q1=1 (TODO stubs), absence of shared dashboard definitions
- **Recommendation**: Deploy ADOT Collector as a DaemonSet on EKS. Enable `ENABLE_TRACING=1` by default in all services. Complete OpenTelemetry instrumentation in cartservice (C#), shippingservice (Go), and adservice (Java). Export traces to X-Ray and metrics to CloudWatch. Create per-service and portfolio-level dashboards.
- **Contextual Annotations**: This finding provides context for the OPS-Q1 Foundational Blocker (3 services with score < 2) — **verify** that completing the TODO stubs in these 3 services AND enabling the OTel Collector by default would resolve the tracing gap portfolio-wide.

### PORT-MOD-Q3: Dependency Cycle Health

- **Score**: 2
- **Finding**: No explicit dependency graph was provided (`dependency_overrides` absent). Based on inferred dependencies from MOD reports: frontend calls 7 backend services synchronously, checkoutservice calls 6 services synchronously, and recommendationservice calls productcatalogservice. All dependencies are synchronous gRPC, which creates tight coupling. No circular dependencies are apparent from the inferred graph (frontend → backends, checkout → backends, recommendation → productcatalog are all unidirectional). However, the synchronous nature means any service on the checkout path becoming slow cascades to all upstream callers.
- **Evidence**: frontend `main.go` (7 gRPC connections), checkoutservice `main.go` (6 service env vars), recommendationservice `recommendation_server.py` (productcatalog gRPC call)
- **Recommendation**: Provide `dependency_overrides` in the portfolio config for formal dependency analysis. Break synchronous coupling on non-critical paths (email, ads, recommendations) with SQS/SNS. Implement circuit breakers for all synchronous gRPC calls.

### PORT-MOD-Q4: Technology Diversity

- **Score**: 2
- **Finding**: High language diversity with 5 languages across 10 application services: Go (4), Python (2), Node.js (2), C# (1), Java (1). IaC tooling is relatively standardized with Terraform as the primary tool (used by 10/11 services). A single database engine (Redis) and single compute pattern (managed Kubernetes) provide low diversity in those dimensions. The language diversity is intentional (polyglot microservices) but increases operational complexity — each language requires separate security scanning tools, dependency management, and build pipelines.
- **Evidence**: go.mod (4 services), requirements.txt (2 services), package.json (2 services), cartservice.csproj (1 service), build.gradle (1 service)
- **Recommendation**: Standardize CI/CD pipeline patterns per language family (Go pipeline template, Python pipeline template, etc.). Ensure each language has equivalent security scanning. Consider whether the Java adservice and C# cartservice could be migrated to Go for reduced operational overhead, though the current languages are well-suited to their domains.

### PORT-MOD-Q5: Shared Security Posture

- **Score**: 1
- **Finding**: No shared security posture exists across the portfolio. SEC category scores range from 1.29 to 1.71 — universally low. No shared WAF (the Istio Gateway accepts all hosts on HTTP with no WAF). No centralized security scanning pipeline (no SAST, DAST, or container scanning in any CI/CD workflow). No unified secrets management (some services use GCP Secret Manager conditionally, most have no secrets management). No consistent IAM patterns. Istio AuthorizationPolicies are defined in the Helm chart but disabled by default (`authorizationPolicies.create: false`).
- **Evidence**: SEC-Q1=1 (all 11), SEC-Q2=1 (all 11), SEC-Q3=1-2, SEC-Q7=1-2, `helm-chart/values.yaml` (`authorizationPolicies.create: false`, `networkPolicies.create: false`)
- **Recommendation**: Establish a centralized security baseline in Terraform: CloudTrail, KMS, Cognito, WAF, Secrets Manager. Enable Istio AuthorizationPolicies and NetworkPolicies by default. Add security scanning (Trivy, language-specific scanners) as a mandatory CI/CD stage across all pipelines. Implement a shared security scanning GitHub Actions reusable workflow.
- **Contextual Annotations**: This finding provides context for SEC-Q1 through SEC-Q7 Foundational Blockers — **verify** that a centralized platform team deploying shared security infrastructure would address the root cause (no security tooling/infrastructure) rather than requiring each service team to independently solve the same problems.

**Portfolio-Level Average**: (2 + 1 + 2 + 2 + 1) / 5 = **1.60**

---

## Service-by-Service Summary

| Service | Repo Type | Priority | Overall Score | INF | APP | DATA | SEC | OPS | Pathways Triggered | Phase |
|---------|-----------|----------|---------------|-----|-----|------|-----|-----|--------------------|-------|
| currencyservice | application | P1 | 1.67 | 1.09 | 2.50 | 2.25 | 1.29 | 1.22 | 2 of 7 | 0, 2 |
| platform-infra | infrastructure-only | — | 1.74 | 2.09 | N/A | 2.00 | 1.43 | 1.44 | 1 of 7 | 1 |
| paymentservice | application | P0 | 1.92 | 2.18 | 2.33 | 2.25 | 1.29 | 1.56 | 2 of 7 | 1 |
| recommendationservice | application | P1 | 2.04 | 2.27 | 2.33 | 2.75 | 1.43 | 1.44 | 1 of 7 | 2 |
| frontend | application | P0 | 2.05 | 2.09 | 2.17 | 3.00 | 1.43 | 1.56 | 1 of 7 | 1 |
| adservice | application | P2 | 2.07 | 2.27 | 2.67 | 2.50 | 1.57 | 1.33 | 1 of 7 | 3 |
| emailservice | application | P2 | 2.09 | 2.09 | 2.50 | 2.50 | 1.71 | 1.67 | 2 of 7 | 3 |
| cartservice | application | P0 | 2.11 | 1.91 | 2.50 | 3.25 | 1.57 | 1.33 | 2 of 7 | 1 |
| productcatalogservice | application | P0 | 2.11 | 2.18 | 2.50 | 2.75 | 1.57 | 1.56 | 2 of 7 | 1 |
| checkoutservice | application | P0 | 2.16 | 2.27 | 2.17 | 3.50 | 1.43 | 1.44 | 1 of 7 | 1 |
| shippingservice | application | P1 | 2.39 | 2.55 | 2.83 | 3.50 | 1.71 | 1.33 | 1 of 7 | 2 |

### Individual Service Details

#### currencyservice
- **Overall Score**: 1.67 / 4.0 — Lowest in portfolio
- **Repository Type**: application
- **Priority**: P1
- **Assessment Date**: 2026-04-15
- **Category Scores**: INF 1.09, APP 2.50, DATA 2.25, SEC 1.29, OPS 1.22
- **Top Gaps**: INF-Q10: score 1 (zero IaC), INF-Q11: score 1 (zero CI/CD), INF-Q5: score 1 (no network security)
- **Triggered Pathways**: Move to Modern DevOps, Move to AI
- **Key Recommendations**: Create Terraform IaC and CI/CD pipeline as highest priority. Build Kubernetes manifests and Helm chart. Add unit tests.
- **Roadmap Phase**: Phase 0 (IaC/CI/CD), Phase 2 (remaining modernization)

#### platform-infra
- **Overall Score**: 1.74 / 4.0
- **Repository Type**: infrastructure-only
- **Priority**: Not set
- **Assessment Date**: 2026-04-15
- **Category Scores**: INF 2.09, APP N/A, DATA 2.00, SEC 1.43, OPS 1.44
- **Top Gaps**: SEC-Q5: score 1 (no secrets management), INF-Q8: score 1 (no backups), SEC-Q3: score 1 (no API auth)
- **Triggered Pathways**: Move to Managed Databases
- **Key Recommendations**: Migrate Terraform from GCP to AWS. Deploy EKS with ArgoCD. Establish security baseline (CloudTrail, KMS, Secrets Manager).
- **Roadmap Phase**: Phase 1

#### paymentservice
- **Overall Score**: 1.92 / 4.0
- **Repository Type**: application
- **Priority**: P0
- **Assessment Date**: 2026-04-15
- **Category Scores**: INF 2.18, APP 2.33, DATA 2.25, SEC 1.29, OPS 1.56
- **Top Gaps**: SEC-Q1: score 1 (no audit logging), SEC-Q2: score 1 (no encryption), SEC-Q5: score 1 (no secrets management)
- **Triggered Pathways**: Move to Managed Databases, Move to AI
- **Key Recommendations**: Implement secrets management for payment credentials. Add security scanning to CI pipeline. Define payment-specific SLOs.
- **Roadmap Phase**: Phase 1

#### frontend
- **Overall Score**: 2.05 / 4.0
- **Repository Type**: application
- **Priority**: P0
- **Assessment Date**: 2026-04-15
- **Category Scores**: INF 2.09, APP 2.17, DATA 3.00, SEC 1.43, OPS 1.56
- **Top Gaps**: SEC-Q3: score 1 (no API auth), APP-Q3: score 1 (all sync), INF-Q4: score 1 (no messaging)
- **Triggered Pathways**: Move to AI
- **Key Recommendations**: Deploy ALB with WAF and Cognito auth. Implement async patterns for non-critical calls. Add API versioning.
- **Roadmap Phase**: Phase 1

#### cartservice
- **Overall Score**: 2.11 / 4.0
- **Repository Type**: application
- **Priority**: P0
- **Assessment Date**: 2026-04-15
- **Category Scores**: INF 1.91, APP 2.50, DATA 3.25, SEC 1.57, OPS 1.33
- **Top Gaps**: INF-Q8: score 1 (emptyDir data loss), OPS-Q1: score 1 (no tracing), OPS-Q5: score 1 (no deployment strategy)
- **Triggered Pathways**: Move to Managed Databases, Move to AI
- **Key Recommendations**: Migrate to DynamoDB via ICartStore interface. Add OpenTelemetry for C#. Configure HPA with 2+ replicas.
- **Roadmap Phase**: Phase 1

#### productcatalogservice
- **Overall Score**: 2.11 / 4.0
- **Repository Type**: application
- **Priority**: P0
- **Assessment Date**: 2026-04-15
- **Category Scores**: INF 2.18, APP 2.50, DATA 2.75, SEC 1.57, OPS 1.56
- **Top Gaps**: SEC-Q7: score 1 (no security scanning), APP-Q5: score 1 (no API versioning), INF-Q4: score 1 (no messaging)
- **Triggered Pathways**: Move to Managed Databases, Move to AI
- **Key Recommendations**: Migrate product data from JSON to DynamoDB. Add security scanning to CI. Implement catalog change events via SNS.
- **Roadmap Phase**: Phase 1

#### checkoutservice
- **Overall Score**: 2.16 / 4.0
- **Repository Type**: application
- **Priority**: P0
- **Assessment Date**: 2026-04-15
- **Category Scores**: INF 2.27, APP 2.17, DATA 3.50, SEC 1.43, OPS 1.44
- **Top Gaps**: SEC-Q3: score 1 (no API auth on payment path), INF-Q3: score 1 (hardcoded orchestration), INF-Q4: score 1 (no async)
- **Triggered Pathways**: Move to AI
- **Key Recommendations**: Migrate PlaceOrder to Step Functions. Implement mTLS/auth. Decouple email to SQS.
- **Roadmap Phase**: Phase 1

#### recommendationservice
- **Overall Score**: 2.04 / 4.0
- **Repository Type**: application
- **Priority**: P1
- **Assessment Date**: 2026-04-15
- **Category Scores**: INF 2.27, APP 2.33, DATA 2.75, SEC 1.43, OPS 1.44
- **Top Gaps**: SEC-Q3: score 1 (no auth), OPS-Q5: score 1 (direct deploy), APP-Q3: score 1 (all sync)
- **Triggered Pathways**: Move to AI
- **Key Recommendations**: Add Python tests. Implement Bedrock-powered recommendations. Add caching layer.
- **Roadmap Phase**: Phase 2

#### shippingservice
- **Overall Score**: 2.39 / 4.0 — Highest in portfolio
- **Repository Type**: application
- **Priority**: P1
- **Assessment Date**: 2026-04-15
- **Category Scores**: INF 2.55, APP 2.83, DATA 3.50, SEC 1.71, OPS 1.33
- **Top Gaps**: OPS-Q1: score 1 (tracing is TODO stub), SEC-Q1: score 1 (no audit logging), OPS-Q2: score 1 (no SLOs)
- **Triggered Pathways**: Move to AI
- **Key Recommendations**: Complete OpenTelemetry tracing (implement TODO). Define SLOs. Implement canary deployments.
- **Roadmap Phase**: Phase 2

#### emailservice
- **Overall Score**: 2.09 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: 2026-04-15
- **Category Scores**: INF 2.09, APP 2.50, DATA 2.50, SEC 1.71, OPS 1.67
- **Top Gaps**: INF-Q4: score 1 (no async), SEC-Q1: score 1 (no audit logging), OPS-Q2: score 1 (no SLOs)
- **Triggered Pathways**: Move to Managed Databases, Move to AI
- **Key Recommendations**: Migrate to SQS-based async processing. Add Python tests. Define email delivery SLOs.
- **Roadmap Phase**: Phase 3

#### adservice
- **Overall Score**: 2.07 / 4.0
- **Repository Type**: application
- **Priority**: P2
- **Assessment Date**: 2026-04-15
- **Category Scores**: INF 2.27, APP 2.67, DATA 2.50, SEC 1.57, OPS 1.33
- **Top Gaps**: OPS-Q1: score 1 (no tracing — TODO stub), SEC-Q7: score 1 (no security scanning), APP-Q3: score 1 (all sync)
- **Triggered Pathways**: Move to AI
- **Key Recommendations**: Externalize ad data to DynamoDB. Implement OpenTelemetry Java agent. Add JUnit tests.
- **Roadmap Phase**: Phase 3

---

## Assessment Inventory

| # | Service | Report File | Assessment Date | Repo Type | Overall Score |
|---|---------|-------------|-----------------|-----------|---------------|
| 1 | frontend | ./services/microservices-demo/src/frontend/frontend-mod-report.md | 2026-04-15 | application | 2.05 |
| 2 | cartservice | ./services/microservices-demo/src/cartservice/cartservice-mod-report.md | 2026-04-15 | application | 2.11 |
| 3 | productcatalogservice | ./services/microservices-demo/src/productcatalogservice/productcatalogservice-mod-report.md | 2026-04-15 | application | 2.11 |
| 4 | checkoutservice | ./services/microservices-demo/src/checkoutservice/checkoutservice-mod-report.md | 2026-04-15 | application | 2.16 |
| 5 | paymentservice | ./services/microservices-demo/src/paymentservice/paymentservice-mod-report.md | 2026-04-15 | application | 1.92 |
| 6 | currencyservice | ./services/microservices-demo/src/currencyservice/currencyservice-mod-report.md | 2026-04-15 | application | 1.67 |
| 7 | shippingservice | ./services/microservices-demo/src/shippingservice/shippingservice-mod-report.md | 2026-04-15 | application | 2.39 |
| 8 | emailservice | ./services/microservices-demo/src/emailservice/emailservice-mod-report.md | 2026-04-15 | application | 2.09 |
| 9 | recommendationservice | ./services/microservices-demo/src/recommendationservice/recommendationservice-mod-report.md | 2026-04-15 | application | 2.04 |
| 10 | adservice | ./services/microservices-demo/src/adservice/adservice-mod-report.md | 2026-04-15 | application | 2.07 |
| 11 | platform-infra | ./services/microservices-demo/microservices-demo-mod-report.md | 2026-04-15 | infrastructure-only | 1.74 |
