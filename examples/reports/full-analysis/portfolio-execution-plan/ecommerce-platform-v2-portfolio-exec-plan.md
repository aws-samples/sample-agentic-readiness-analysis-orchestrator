# Portfolio Modernization Execution Plan

| Field | Value |
|-------|-------|
| **Portfolio** | ecommerce-platform-v2 |
| **Services Assessed** | 5 |
| **Services In Scope** | 3 (local-monolith, unishop-monolith, aws-microservices) |
| **Pathways Planned** | 4 |
| **Assessment Date** | 2026-05-18 |
| **Plan Generated** | 2026-06-16 |
| **Team Size** | 8 engineers |
| **Timeline Constraint** | 12 months |
| **Budget Constraint** | $1.2M |
| **Risk Tolerance** | Moderate |

---

## Executive Summary

This execution plan covers the modernization of 3 services within the ecommerce-platform-v2 portfolio across 4 triggered MODA pathways. The plan is **feasible within the 12-month timeline** with an expected duration of 38 weeks (~9.5 months), leaving buffer for contingency.

**Key Numbers:**
- **Expected Duration:** 38 weeks (optimistic: 30, pessimistic: 52)
- **Expected Cost:** $1,020,000 (optimistic: $797K, pessimistic: $1.375M)
- **Critical Path:** WS-01 (DevOps) → WS-02 (Containers) → WS-04 (Cloud Native) = 34 weeks
- **Work Streams:** 4 deduplicated streams from 4 triggered pathways
- **Decision Points:** 5 requiring customer input

**Feasibility Assessment: GREEN**

The expected timeline (38 weeks) and cost ($1.02M) fit within constraints. The pessimistic estimate ($1.375M) exceeds the $1.2M budget, representing a risk that is mitigated through Graviton cost savings, scope management, and phased delivery.

**Top Risks:**
1. Cross-service dependency complexity during parallel modernization
2. No Kubernetes experience — EKS training required before containers work
3. Plaintext secrets in 2 repositories require immediate remediation

**Services with No Action Required:** eks-saas-gitops (score 2.93, Pilot-Ready) and books-api (score 3.0, Pilot-Ready) triggered no modernization pathways.

---

## Portfolio MODA Summary

| Service | Score | Classification | Pathways Triggered | Priority |
|---------|-------|---------------|-------------------|----------|
| local-monolith | 1.82 | Remediation Required | Cloud Native, Modern DevOps | P0 |
| unishop-monolith | 1.40 | Not Ready | Cloud Native, Containers, Managed DBs, Modern DevOps | P0 |
| aws-microservices | 2.40 | Remediation Required | Modern DevOps | P0 |
| eks-saas-gitops | 2.93 | Pilot-Ready | — | P1 |
| books-api | 3.00 | Pilot-Ready | — | P1 |

**Portfolio Average Score:** 2.31 / 4.0

**Category Weaknesses:**
- Operations & Observability: 1.53 (lowest)
- Security Baseline: 2.01
- Application Architecture: 2.17

---

## Work Stream Overview

| ID | Work Stream | Pathway | Services | Effort (Weeks) | Risk | Prerequisites |
|----|-------------|---------|----------|----------------|------|---------------|
| WS-01 | Move to Modern DevOps | move-to-modern-devops | local-monolith, unishop-monolith, aws-microservices | 8 / 12 / 18 | Medium | — |
| WS-02 | Move to Containers | move-to-containers | unishop-monolith | 4 / 6 / 10 | Medium | WS-01 |
| WS-03 | Move to Managed Databases | move-to-managed-databases | unishop-monolith | 3 / 5 / 8 | High | — |
| WS-04 | Move to Cloud Native | move-to-cloud-native | local-monolith, unishop-monolith | 12 / 16 / 24 | High | WS-01, WS-02 |

*Effort shown as optimistic / expected / pessimistic weeks.*

---

## Detailed Work Streams

### WS-01: Move to Modern DevOps

**Pathway:** move-to-modern-devops  
**Services:** local-monolith, unishop-monolith, aws-microservices  
**Risk Level:** Medium  
**Effort:** 8–18 weeks (expected: 12)

**Objective:** Establish CI/CD pipelines, Infrastructure as Code (CDK), automated testing, and progressive deployment strategies for all 3 affected services.

#### Phase 1: Shared Infrastructure Setup

| Task | Description | Effort | Service | Dependencies |
|------|-------------|--------|---------|--------------|
| WS01-T01 | Design shared CI/CD platform (CodePipeline, CodeBuild, ECR) via CDK | 8d | shared | — |
| WS01-T02 | Establish IaC patterns and CDK construct library | 5d | shared | — |
| WS01-T03 | Migrate plaintext secrets to AWS Secrets Manager | 3d | shared | — |

#### Phase 2: Per-Service CI/CD Implementation

| Task | Description | Effort | Service | Dependencies |
|------|-------------|--------|---------|--------------|
| WS01-T04 | CI/CD pipeline for local-monolith | 5d | local-monolith | WS01-T01 |
| WS01-T05 | CI/CD pipeline for unishop-monolith with IaC | 8d | unishop-monolith | WS01-T01, WS01-T02 |
| WS01-T06 | CI/CD pipeline for aws-microservices | 5d | aws-microservices | WS01-T01 |

#### Phase 3: Testing and Deployment Strategy

| Task | Description | Effort | Service | Dependencies |
|------|-------------|--------|---------|--------------|
| WS01-T07 | Integration test suites (70% critical path coverage) | 10d | shared | WS01-T04, WS01-T06 |
| WS01-T08 | Blue/green deployment for local-monolith | 5d | local-monolith | WS01-T04, WS01-T07 |
| WS01-T09 | Canary deployment for aws-microservices | 4d | aws-microservices | WS01-T06, WS01-T07 |

**Success Criteria:**
- All 3 services have operational CI/CD pipelines with automated quality gates
- IaC coverage > 80% for unishop-monolith infrastructure
- Integration test coverage on critical paths for all 3 services
- Progressive deployment (blue/green or canary) operational for at least 2 services
- Zero plaintext secrets in any repository

---

### WS-02: Move to Containers

**Pathway:** move-to-containers  
**Services:** unishop-monolith  
**Risk Level:** Medium  
**Effort:** 4–10 weeks (expected: 6)  
**Prerequisite:** WS-01

**Objective:** Containerize the unishop-monolith Java application and deploy on Amazon EKS with Graviton-based node groups.

#### Phase 1: Containerization

| Task | Description | Effort | Service | Dependencies |
|------|-------------|--------|---------|--------------|
| WS02-T01 | Multi-stage Dockerfile for ARM64/Graviton | 4d | unishop-monolith | — |
| WS02-T02 | Provision EKS cluster with Graviton nodes via CDK | 8d | unishop-monolith | WS02-T01 |
| WS02-T03 | Kubernetes manifests and Helm chart | 5d | unishop-monolith | WS02-T02 |

#### Phase 2: Production Readiness

| Task | Description | Effort | Service | Dependencies |
|------|-------------|--------|---------|--------------|
| WS02-T04 | Network policies and pod security standards | 5d | unishop-monolith | WS02-T03 |
| WS02-T05 | EKS deployment in CI/CD pipeline | 4d | unishop-monolith | WS02-T03 |
| WS02-T06 | Multi-AZ deployment with PDBs | 3d | unishop-monolith | WS02-T04 |

**Success Criteria:**
- unishop-monolith running on EKS with Graviton nodes
- Horizontal pod autoscaling operational
- Multi-AZ deployment with 99.95% availability target
- CI/CD pipeline deploys to EKS with image scanning

---

### WS-03: Move to Managed Databases

**Pathway:** move-to-managed-databases  
**Services:** unishop-monolith  
**Risk Level:** High  
**Effort:** 3–8 weeks (expected: 5)

**Objective:** Migrate unishop-monolith from self-managed MySQL to Amazon Aurora PostgreSQL with Multi-AZ, automated backups, and CMK encryption.

#### Phase 1: Assessment and Planning

| Task | Description | Effort | Service | Dependencies |
|------|-------------|--------|---------|--------------|
| WS03-T01 | Schema assessment and Aurora PostgreSQL compatibility report | 3d | unishop-monolith | — |
| WS03-T02 | Provision Aurora PostgreSQL cluster via CDK | 4d | unishop-monolith | WS03-T01 |

#### Phase 2: Migration Execution

| Task | Description | Effort | Service | Dependencies |
|------|-------------|--------|---------|--------------|
| WS03-T03 | Schema migration via AWS DMS | 5d | unishop-monolith | WS03-T02 |
| WS03-T04 | Application connection and query adaptation | 5d | unishop-monolith | WS03-T03 |
| WS03-T05 | Cutover and validation | 2d | unishop-monolith | WS03-T04 |

**Success Criteria:**
- unishop-monolith running on Aurora PostgreSQL (Multi-AZ)
- Customer-managed KMS encryption at rest enabled
- Point-in-time recovery with 35-day retention
- Zero data loss during migration

---

### WS-04: Move to Cloud Native

**Pathway:** move-to-cloud-native  
**Services:** local-monolith, unishop-monolith  
**Risk Level:** High  
**Effort:** 12–24 weeks (expected: 16)  
**Prerequisites:** WS-01, WS-02

**Objective:** Decompose both monoliths into microservices with event-driven communication patterns, deploying on EKS.

#### Phase 1: Domain Analysis and Shared Patterns

| Task | Description | Effort | Service | Dependencies |
|------|-------------|--------|---------|--------------|
| WS04-T01 | DDD workshop — bounded contexts and service boundaries | 5d | shared | — |
| WS04-T02 | Event-driven architecture design (EventBridge) | 4d | shared | WS04-T01 |
| WS04-T03 | Shared microservices CDK template | 5d | shared | WS04-T02 |

#### Phase 2: Strangler-Fig — unishop-monolith

| Task | Description | Effort | Service | Dependencies |
|------|-------------|--------|---------|--------------|
| WS04-T04 | Extract Order service | 10d | unishop-monolith | WS04-T03 |
| WS04-T05 | Extract Inventory/Catalog service | 8d | unishop-monolith | WS04-T04 |
| WS04-T06 | Implement async event patterns (EventBridge + SQS) | 5d | unishop-monolith | WS04-T04 |

#### Phase 3: Strangler-Fig — local-monolith

| Task | Description | Effort | Service | Dependencies |
|------|-------------|--------|---------|--------------|
| WS04-T07 | Extract Product/Catalog service (rewrite in Java/Spring) | 10d | local-monolith | WS04-T03 |
| WS04-T08 | Extract Order Management service with async processing | 8d | local-monolith | WS04-T07 |
| WS04-T09 | Extract User/Auth service (Cognito integration) | 6d | local-monolith | WS04-T07 |

#### Phase 4: Integration and Validation

| Task | Description | Effort | Service | Dependencies |
|------|-------------|--------|---------|--------------|
| WS04-T10 | End-to-end integration tests across all services | 5d | shared | WS04-T05, T06, T08, T09 |
| WS04-T11 | Decommission monolith remnants | 3d | shared | WS04-T10 |

**Success Criteria:**
- Both monoliths decomposed into independently deployable microservices
- Event-driven communication via EventBridge
- Database-per-service pattern implemented
- Async processing for long-running operations
- End-to-end integration tests passing

---

## Cross-Service Dependencies

```
WS-01 (Modern DevOps) ──────┬──► WS-02 (Containers) ──► WS-04 (Cloud Native)
                             │                                    ▲
                             └────────────────────────────────────┘
                             
WS-03 (Managed DBs) ────── runs in parallel with WS-01 ──────────
```

**Dependency Rules:**
1. WS-01 must complete before WS-02 (EKS deployment needs CI/CD pipeline)
2. WS-01 and WS-02 must complete before WS-04 (decomposition requires both CI/CD and container platform)
3. WS-03 has no prerequisites — can run in parallel with WS-01

**Inferred Service Dependencies (from MODA):**
- unishop-monolith → eks-saas-gitops (shared infrastructure)
- local-monolith → eks-saas-gitops (shared infrastructure)
- aws-microservices → eks-saas-gitops (shared infrastructure)

---

## Portfolio Timeline and Phasing

### Phase 1: Foundation & DevOps (Weeks 0–12)

| Week | WS-01 | WS-03 |
|------|-------|-------|
| 0–2 | Shared infra setup + EKS training (split team) | Schema assessment |
| 2–4 | CDK construct library + secrets migration | Aurora provisioning |
| 4–8 | Per-service CI/CD pipelines | DMS migration + cutover |
| 8–12 | Integration tests + progressive deployment | — (complete) |

### Phase 2: Core Migration (Weeks 12–30)

| Week | WS-02 | WS-04 |
|------|-------|-------|
| 12–14 | Containerization + Dockerfile | — |
| 14–18 | EKS provisioning + Helm charts | — |
| 18–20 | Production hardening | DDD workshop + event design |
| 20–24 | — (complete) | Shared patterns + unishop extraction |
| 24–30 | — | unishop completion + local-monolith start |

### Phase 3: Optimization & Validation (Weeks 30–38)

| Week | WS-04 |
|------|-------|
| 30–34 | local-monolith decomposition |
| 34–38 | Integration testing + monolith decommission |

---

## Critical Path Analysis

**Critical Path:** WS-01 → WS-02 → WS-04

| Segment | Expected Duration | Cumulative |
|---------|-------------------|-----------|
| WS-01 (Modern DevOps) | 12 weeks | 12 weeks |
| WS-02 (Containers) | 6 weeks | 18 weeks |
| WS-04 (Cloud Native) | 16 weeks | 34 weeks |

**Buffer:** 12 months (52 weeks) - 34 weeks = 18 weeks buffer on expected path.

**Parallel Savings:** WS-03 (5 weeks) runs concurrent with WS-01, saving 5 weeks vs serial execution.

**Timeline Risk:** Pessimistic critical path (18 + 10 + 24 = 52 weeks) would consume the entire 12-month constraint with no buffer.

---

## Risk Register

| ID | Category | Risk | Likelihood | Impact | Mitigation |
|----|----------|------|-----------|--------|------------|
| RISK-001 | Technical | Cross-service integration failures during parallel modernization | Medium | High | Shared CDK patterns established first; feature flags for incremental rollout |
| RISK-002 | Organizational | Team spread across 4 pathways reduces per-stream velocity | Medium | Medium | Dedicated sub-teams per stream; max 2 concurrent active streams |
| RISK-003 | Timeline | Pessimistic estimate consumes entire 12-month constraint | Low | High | Prioritize critical path; defer WS-04 local-monolith if behind |
| RISK-004 | Compliance | SOC2/PCI-DSS compliance during transition dual-running | Medium | High | Maintain controls in both systems; audit logging from day 1 |
| RISK-005 | Technical | No K8s experience — EKS upskilling blocks containers work | High | Medium | Formal training weeks 1-2; AWS SA pairing for cluster setup |
| RISK-006 | Cost | Budget ($1.2M) tight if pessimistic timeline materializes | Low | Medium | Graviton savings; Savings Plans; scope reduction as contingency |
| RISK-007 | Technical | MySQL→PostgreSQL incompatible SQL patterns | Medium | High | AWS SCT early assessment; Aurora MySQL as fallback |

---

## Engagement Cost Estimation

| Category | Optimistic | Expected | Pessimistic |
|----------|-----------|----------|-------------|
| People (8 engineers @ $250/hr) | $680,000 | $840,000 | $1,120,000 |
| Infrastructure Delta | $72,000 | $120,000 | $180,000 |
| Training (4 pathways) | $45,000 | $60,000 | $75,000 |
| **Total** | **$797,000** | **$1,020,000** | **$1,375,000** |

**Budget Assessment:** Expected cost ($1.02M) is within the $1.2M budget. Pessimistic ($1.375M) exceeds by 15% — mitigated through Graviton cost savings (20% compute reduction) and scope management.

**Cost Optimization Levers:**
- Graviton instances: 20% cost savings on EKS compute
- Savings Plans: Up to 30% reduction on committed compute
- Scope reduction: Defer local-monolith decomposition to follow-on engagement saves ~$250K

---

## Success Metrics and Phase Gates

### Phase Gates

| Gate | Week | Criteria | Go/No-Go Decision |
|------|------|----------|-------------------|
| DevOps Foundation | 12 | 3 CI/CD pipelines operational, IaC > 80%, zero plaintext secrets | Proceed to WS-02 |
| Database Migration | 14 | Aurora PostgreSQL operational, data validated, app connected | Confirm containers timeline |
| Pilot Containerized | 18 | EKS running, Multi-AZ verified, HPA operational | Proceed to WS-04 |
| First Decomposition | 26 | One bounded context extracted, events flowing | Confirm full decomposition scope |
| Migration Complete | 38 | All work streams complete, exit criteria met | Engagement closure |

### Leading Indicators (Weekly)
- Sprint velocity ≥ 80% of planned story points
- CI/CD pipeline success rate > 90%
- Test coverage on critical paths > 70%
- Zero infrastructure drift (unmanaged resources)

### Lagging Indicators (Monthly)
- Deployment frequency: daily per service
- MTTR: < 30 minutes
- Change failure rate: < 15%
- Lead time: < 1 day commit-to-production

### Exit Criteria
- All 4 triggered pathways fully addressed
- Portfolio MODA re-score: average ≥ 3.0 (from current 2.31)
- All in-scope services achieve Pilot-Ready or Cloud-Native Ready
- SOC2 and PCI-DSS compliance maintained — zero audit findings
- 99.95% availability maintained throughout

---

## Assumptions and Constraints

### Assumptions
1. Team of 8 engineers available at 70% capacity for modernization (30% BAU/support)
2. No major production incidents requiring sustained attention during migration
3. MODA reports reflect current state (assessed 2026-05-18, within 90-day currency window)
4. Infrastructure and tooling budget approved up to $1.2M
5. AWS account access and IAM permissions pre-provisioned
6. EKS training schedulable within first 4 weeks
7. Database migration window of 4 hours available for final cutover
8. SOC2 and PCI-DSS audit cycles known and planned around
9. Customer decision points resolved within 1 week of being raised

### Constraints
- **Compliance:** SOC2 and PCI-DSS must be maintained continuously — no compliance gaps during transition
- **Availability:** 99.95% uptime SLA — mandates incremental (strangler-fig) approach, no big-bang migrations
- **Technology:** Prefer EKS, Aurora PostgreSQL, Graviton, CDK; Avoid self-managed Kafka, Lambda for core services
- **Timeline:** Hard 12-month deadline
- **Budget:** $1.2M ceiling including all training and infrastructure

---

## Recommendations and Decision Points

### Immediate Actions (Week 0)
1. **Resolve DP-004** — Training approach decision (formal vs on-the-job)
2. **Remediate SEC-Q5** — Migrate plaintext secrets to Secrets Manager immediately (both repos)
3. **Resolve DP-001** — CI/CD platform selection

### Decision Points

| ID | Decision | Deadline | Recommendation |
|----|----------|----------|----------------|
| DP-001 | CI/CD platform: CodePipeline vs GitHub Actions | Week 2 | CodePipeline — native AWS integration, aligns with CDK |
| DP-002 | Database target: Aurora PostgreSQL vs Aurora MySQL | Week 4 | Aurora PostgreSQL — aligns with preference, better long-term |
| DP-003 | Decomposition approach: Strangler-fig vs Big-bang | Week 14 | Strangler-fig — required for 99.95% availability SLA |
| DP-004 | EKS training: Formal vs On-the-job | Week 1 | Formal training with parallel WS-01 execution |
| DP-005 | local-monolith language: Java rewrite vs PHP modernize | Week 14 | Java/Spring rewrite — leverages team strength |

### Recommended AWS Programs
- **Experience-Based Acceleration (EBA):** Triggered by 3 repos with scores < 3.0 and active pathways. Provides hands-on modernization guidance and accelerates team learning.
