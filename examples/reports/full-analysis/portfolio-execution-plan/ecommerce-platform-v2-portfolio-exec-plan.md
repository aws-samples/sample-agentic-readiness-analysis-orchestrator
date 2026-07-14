# Portfolio Execution Plan

## ecommerce-platform-v2

| Field | Value |
|-------|-------|
| **Portfolio** | ecommerce-platform-v2 |
| **Services Assessed** | 5 |
| **Dimensions** | MODA + ARA |
| **MODA Pathways Planned** | 4 (Modern DevOps, Cloud Native, Containers, Managed Databases) |
| **ARA BLOCKERs Addressed** | 4 (AUTH-Q1 across 4 services) |
| **Total Effort (Traditional)** | 56-92 weeks |
| **Total Effort (AI-Accelerated)** | 30-52 weeks |
| **AI Acceleration Benefit** | 44% effort reduction, 32 weeks saved |
| **Feasibility** | Yellow — achievable within 12 months with AI tooling but tight |
| **Team Size** | 8 engineers |
| **Risk Tolerance** | Moderate |

---

## Executive Summary

This execution plan addresses the **ecommerce-platform-v2** portfolio comprising 5 services requiring both modernization (MODA) and agent-readiness (ARA) work. The portfolio has:

- **4 triggered MODA pathways** requiring infrastructure and application modernization
- **4 AUTH-Q1 BLOCKERs** preventing safe agent deployment
- **22 RISK-SAFETY findings** requiring remediation for production agent use
- **2 services classified as "Not Ready"/"Remediation Required"** for modernization
- **4 services classified as "Remediation Required"** for agent readiness

**Key constraint:** The team has strong Java/Spring skills but **no Kubernetes experience**, which is the primary risk for EKS adoption. The plan includes training and phased adoption to mitigate this gap.

**AI Acceleration Impact:** With AI-assisted tooling, the engagement reduces from an expected 72 weeks of effort to 40 weeks — a **44% reduction** saving an estimated **$318,000** and **20 calendar weeks**. The primary beneficiaries are IaC generation (60% acceleration), CI/CD pipeline creation (60%), test suite generation (50%), and code migration tasks (50%).

**Budget Assessment:** Expected AI-accelerated cost of $591K is well within the $1.2M budget constraint, leaving margin for contingency and scope expansion.

---

## Portfolio Analysis Summary

### Modernization Readiness (MODA)

| Service | Score | Tier | Pathways Triggered |
|---------|-------|------|-------------------|
| local-monolith | 1.82 | Remediation Required | Cloud Native, Modern DevOps |
| unishop-monolith | 1.40 | Not Ready | Cloud Native, Containers, Managed DBs, Modern DevOps |
| aws-microservices | 2.40 | Remediation Required | Modern DevOps |
| books-api | 3.00 | Pilot-Ready | None |
| eks-saas-gitops | 2.93 | Pilot-Ready | None |

**Portfolio average score:** 2.31 (Needs Work)

### Agent Readiness (ARA)

| Service | Tier | BLOCKERs | RISK-Safety | RISK-Quality |
|---------|------|----------|-------------|--------------|
| local-monolith | Remediation Required | 1 | 9 | 13 |
| unishop-monolith | Remediation Required | 1 | 11 | 15 |
| aws-microservices | Remediation Required | 1 | 9 | 13 |
| books-api | Remediation Required | 1 | 5 | 11 |
| eks-saas-gitops | Pilot-Ready (Safety Concerns) | 0 | 3 | 5 |

**Critical cross-cutting BLOCKER:** AUTH-Q1 (No Machine Identity Authentication) affects 4 of 5 services. No agent can safely call any application service until this is resolved.

---

## Modernization Work Streams

| ID | Work Stream | Services | Traditional (wks) | AI-Accelerated (wks) | Savings | Risk |
|----|-------------|----------|-------------------|---------------------|---------|------|
| WS-01 | Move to Modern DevOps | 3 | 10-18 | 5-10 | 50% | Medium |
| WS-02 | Move to Cloud Native | 2 | 22-36 | 12-20 | 43% | High |
| WS-03 | Move to Containers | 1 | 8-14 | 4-8 | 40% | Medium |
| WS-04 | Move to Managed Databases | 1 | 6-10 | 3-7 | 38% | Medium |

### WS-01: Move to Modern DevOps

**Services:** local-monolith, unishop-monolith, aws-microservices
**Effort:** 7 weeks AI-accelerated (14 traditional) | **Prerequisites:** None

Establishes CI/CD pipelines with CDK Pipelines, IaC coverage, integration testing, and progressive delivery. This is the foundational work stream — most other work streams depend on having reliable deployment infrastructure.

**Key tasks:**
- Shared CI/CD pipeline template library (CDK)
- Per-service pipeline implementation
- IaC definition for unishop-monolith (currently zero coverage)
- Integration test suites for all 3 services
- Progressive delivery (canary deployments with auto-rollback)

### WS-02: Move to Cloud Native

**Services:** local-monolith, unishop-monolith
**Effort:** 16 weeks AI-accelerated (28 traditional) | **Prerequisites:** WS-01, WS-03

The highest-effort work stream. Decomposes two tightly-coupled monoliths into independently deployable microservices on EKS with event-driven communication via EventBridge.

**Key tasks:**
- Architecture design for both monoliths (domain boundaries, data ownership)
- Sequential service extraction (user → product → order/basket)
- EKS deployment with Graviton instances
- EventBridge integration for async communication
- Zero-downtime cutover

### WS-03: Move to Containers

**Services:** unishop-monolith
**Effort:** 6 weeks AI-accelerated (10 traditional) | **Prerequisites:** WS-01

Containerizes unishop-monolith and establishes the EKS platform that WS-02 will use for decomposed services.

**Key tasks:**
- EKS cluster provisioning (CDK, Graviton node groups)
- Multi-arch Dockerfile for Java/Spring Boot
- Helm charts and Kubernetes manifests
- Blue-green traffic cutover from EC2 to EKS

### WS-04: Move to Managed Databases

**Services:** unishop-monolith
**Effort:** 5 weeks AI-accelerated (8 traditional) | **Prerequisites:** None

Migrates self-managed MySQL to Aurora PostgreSQL with Multi-AZ, encryption, and automated backups.

**Key tasks:**
- Aurora PostgreSQL cluster provisioning (CDK)
- Schema and query conversion (MySQL → PostgreSQL)
- DMS migration with validation
- Production cutover

---

## Agent-Readiness Work Streams

| ID | Work Stream | Services | BLOCKERs | Traditional (wks) | AI-Accelerated (wks) | Savings | Risk |
|----|-------------|----------|----------|-------------------|---------------------|---------|------|
| WS-05 | Agent Identity & Authorization | 5 | 4 | 10-18 | 5-10 | 50% | High |
| WS-06 | Transactional Integrity | 4 | 0 | 6-12 | 3-7 | 38% | Medium |
| WS-07 | Data Accessibility | 4 | 0 | 6-10 | 3-6 | 50% | Medium |
| WS-08 | Agent Observability | 5 | 0 | 4-8 | 2-5 | 50% | Low |

### WS-05: Implement Agent Identity & Authorization (BLOCKER Resolution)

**Services:** All 5 | **BLOCKERs:** 4 AUTH-Q1 findings
**Effort:** 7 weeks AI-accelerated (14 traditional) | **Prerequisites:** None

**This is the highest-priority work stream.** Until AUTH-Q1 BLOCKERs are resolved, no agent can safely call any application service. The approach is a shared Cognito resource server with client_credentials grant type providing machine identity across all services.

**Phase 1 (Mandatory — BLOCKER resolution):**
- Design shared machine identity pattern
- Implement auth for each of the 4 affected services
- Validate agent authentication works end-to-end

**Phase 2 (Safety hardening):**
- Scoped permissions (read-only by default)
- CloudTrail with immutable storage
- Emergency identity suspension mechanism

### WS-06: Ensure Transactional Integrity

**Services:** 4 application services
**Effort:** 5 weeks AI-accelerated (8 traditional) | **Prerequisites:** None

Implements rate limiting to prevent runaway agent loops and compensation patterns for multi-step operations.

### WS-07: Improve Data Accessibility

**Services:** 4 application services
**Effort:** 4 weeks AI-accelerated (8 traditional) | **Prerequisites:** WS-05

Implements PII filtering in agent responses, pagination, structured input validation, and PII redaction in logs. Depends on WS-05 because PII scoping requires caller identity.

### WS-08: Add Agent Observability

**Services:** All 5
**Effort:** 3 weeks AI-accelerated (6 traditional) | **Prerequisites:** WS-01

Implements distributed tracing (X-Ray + OpenTelemetry on EKS), structured logging with correlation IDs, and alerting on error rates and latency.

---

## AI Acceleration Analysis

### Overall Portfolio Acceleration

| Metric | Traditional | AI-Accelerated | Savings |
|--------|-------------|----------------|---------|
| Total Effort | 72 weeks | 40 weeks | 32 weeks (44%) |
| Calendar Duration | 62 weeks | 42 weeks | 20 weeks |
| Total Cost | $909K | $591K | $318K (35%) |

### Per-Work-Stream Breakdown

| Work Stream | Traditional | AI-Accelerated | Acceleration |
|-------------|-------------|----------------|--------------|
| WS-01 Modern DevOps | 14 wks | 7 wks | 50% |
| WS-02 Cloud Native | 28 wks | 16 wks | 43% |
| WS-03 Containers | 10 wks | 6 wks | 40% |
| WS-04 Managed Databases | 8 wks | 5 wks | 38% |
| WS-05 Agent Identity | 14 wks | 7 wks | 50% |
| WS-06 Transactional Integrity | 8 wks | 5 wks | 38% |
| WS-07 Data Accessibility | 8 wks | 4 wks | 50% |
| WS-08 Observability | 6 wks | 3 wks | 50% |

### Task Category Distribution

- **High acceleration (40-60%):** 65% of total effort — IaC generation, CI/CD pipelines, code migration, test generation, API specification writing, boilerplate/scaffolding
- **Medium acceleration (15-30%):** 15% of total effort — data migration validation, security pattern implementation
- **Minimal acceleration (0-10%):** 20% of total effort — architecture design, production cutover, compliance review, training

---

## Cross-Dimension Dependencies

| Source | Target | Type | Rationale |
|--------|--------|------|-----------|
| WS-01 (Modern DevOps) | WS-08 (Observability) | enables | CI/CD required for deploying observability instrumentation |
| WS-03 (Containers) | WS-02 (Cloud Native) | enables | EKS platform must exist before services can be decomposed onto it |
| WS-05 (Agent Identity) | WS-07 (Data Accessibility) | enables | Caller identity needed to scope data access and PII filtering |

---

## Cross-Service Dependencies

Based on the portfolio dependency map:
- **eks-saas-gitops** is a foundation service (fan-in: 2) — both unishop-monolith and aws-microservices depend on it
- **unishop-monolith** and **aws-microservices** are leaf services targeting EKS deployment
- **local-monolith** and **books-api** are independent (no cross-service dependencies detected)

---

## Unified Timeline and Phasing

### Phase 1: Foundation & Safety (Weeks 0-8)

**Parallel work streams:** WS-01, WS-04, WS-05, WS-06

| Week | WS-01 | WS-04 | WS-05 | WS-06 |
|------|-------|-------|-------|-------|
| 0-2 | Pipeline templates | Aurora provisioning | Auth pattern design | Rate limiting |
| 2-4 | Per-service pipelines | Schema conversion | Auth implementation (4 services) | DLQ/timeouts |
| 4-6 | IaC + testing | DMS migration | Auth validation | Compensation (start) |
| 6-8 | Progressive delivery | Cutover | Scoped permissions + audit | Compensation (complete) |

**Milestone:** DevOps Foundation + BLOCKERs Resolved (Week 8)

### Phase 2: Core Execution (Weeks 8-34)

**Parallel work streams:** WS-03, WS-07, WS-08 (starting week 8); WS-02 (starting week 14)

| Week | WS-03 | WS-02 | WS-07 | WS-08 |
|------|-------|-------|-------|-------|
| 8-14 | EKS + containerize | — | PII filtering + pagination | Tracing + logging |
| 14-20 | Complete | Architecture design | Input validation + residency | Alerting |
| 20-28 | — | Service extraction | — | — |
| 28-34 | — | Final extraction + cutover | — | — |

**Milestones:**
- EKS Platform Ready (Week 14)
- Agent Pilot Ready (Week 24)
- Cloud Native Decomposition Complete (Week 34)

### Phase 3: Optimization & Validation (Weeks 34-42)

- Final compliance validation (SOC2, PCI-DSS)
- MODA and ARA re-evaluation
- Agent pilot testing with production traffic
- Documentation and handover
- Knowledge transfer to operations team

**Milestone:** Portfolio Execution Complete (Week 42)

---

## Critical Path Analysis

**Critical path:** WS-01 → WS-03 → WS-02

The longest dependency chain runs through:
1. **WS-01** (7 weeks): DevOps foundation must be established first
2. **WS-03** (6 weeks): EKS platform must be operational before decomposition
3. **WS-02** (16 weeks): Cloud-native decomposition is the longest single work stream

**Critical path duration:** ~42 weeks (AI-accelerated expected)

**Non-critical paths (can absorb delays):**
- WS-04 (Managed DBs): 5 weeks, no downstream dependencies affecting critical path
- WS-05 (Agent Identity): 7 weeks, parallel with WS-01
- WS-06 (Transactional Integrity): 5 weeks, parallel with WS-01
- WS-07 (Data Accessibility): 4 weeks, starts after WS-05
- WS-08 (Observability): 3 weeks, starts after WS-01

---

## Risk Register

| ID | Category | Risk | Likelihood | Impact | Mitigation |
|----|----------|------|------------|--------|------------|
| RISK-001 | Technical | No K8s experience — steep EKS learning curve | High | High | 3-day training + embedded AWS SA for first 4 weeks |
| RISK-002 | Agent Safety | AUTH-Q1 BLOCKERs prevent agent deployment until resolved | High | High | Prioritize WS-05 Phase 1 in Foundation phase |
| RISK-003 | Timeline | 12-month constraint tight with 42-week expected timeline | Medium | Medium | Monitor velocity weekly, identify scope reduction candidates |
| RISK-004 | Compliance | SOC2/PCI-DSS gates add overhead during migrations | High | Medium | Engage compliance early, maintain dual-running |
| RISK-005 | Organizational | 8-person team spread across 8 streams | Medium | Medium | Assign dedicated pairs, max 3 concurrent streams |
| RISK-006 | Cost | $1.2M may be tight with dual-running and EKS costs | Medium | Medium | Graviton (20% savings), minimize dual-running periods |
| RISK-007 | Technical | Cross-dimension dependencies extend critical path | Medium | Medium | Weekly cross-dimension sync, identify parallel paths |

---

## Engagement Cost Estimation

### Dual-Perspective Cost Summary

| Category | Traditional | AI-Accelerated | Savings |
|----------|-------------|----------------|---------|
| People | $720,000 | $400,000 | $320,000 |
| AI Tooling | — | $42,000 | — |
| Infrastructure | $124,000 | $84,000 | $40,000 |
| Training | $65,000 | $65,000 | $0 |
| **Total (Expected)** | **$909,000** | **$591,000** | **$318,000 (35%)** |

**Budget assessment:** AI-accelerated expected cost of $591K is well within the $1.2M budget, providing $609K contingency margin.

### Cost Assumptions
- People rate: $250/hr × 40 hrs/week
- Infrastructure delta: $2,000/month per active service
- AI tooling: $500/month per engineer (8 engineers)
- Training: $65K total (EKS, CDK, DevOps, agent patterns, compliance)

---

## Success Metrics and Phase Gates

### Leading Indicators
- Sprint velocity (story points/week per engineer)
- Test coverage increase per sprint
- Integration test pass rate
- CI/CD pipeline success rate

### Lagging Indicators (MODA)
- Deployment frequency (target: daily per service)
- Mean time to recovery (target: < 30 minutes)
- MODA re-score improvement (target: all services > 3.0)
- Change failure rate (target: < 15%)

### Lagging Indicators (ARA)
- BLOCKER count (target: 0)
- ARA re-score (target: all services Pilot-Ready or better)
- Agent authentication success rate (target: > 99.9%)
- Agent error rate (target: < 1% of requests)
- Time to agent identity suspension (target: < 60 seconds)

### Exit Criteria
1. All 4 triggered MODA pathways addressed
2. All 4 AUTH-Q1 BLOCKERs resolved
3. No High-severity gaps remaining
4. All services have CI/CD with integration tests
5. Portfolio MODA average > 3.0
6. All services Pilot-Ready or better on ARA

---

## Assumptions and Constraints

1. Team availability at 70% capacity (30% for BAU, on-call, meetings)
2. No major production incidents requiring sustained attention during migration
3. MODA and ARA reports are current (assessed 2026-05-18, within 90-day freshness window)
4. Infrastructure and tooling budget of $1.2M approved and available
5. Agent deployment does not proceed until BLOCKER remediation completes (WS-05 Phase 1)
6. AI tooling available to engineers (coding assistants, agent-based code generation, automated test generation)
7. AI acceleration estimates based on 2025-2026 tooling capabilities; actual acceleration varies by team proficiency
8. AWS account permissions and sandbox environments available
9. Compliance team available for SOC2/PCI-DSS review within 2-week SLA
10. EKS cluster costs included in $1.2M budget
11. Existing Jenkins CI/CD will be replaced (not maintained in parallel long-term)

---

## Recommendations and Decision Points

### Critical Decisions Required (Weeks 1-2)

| ID | Decision | Recommendation | Deadline |
|----|----------|---------------|----------|
| DP-001 | Container orchestrator | EKS with Graviton | Week 2 |
| DP-002 | Database engine | Aurora PostgreSQL | Week 2 |
| DP-003 | Machine identity approach | Cognito client_credentials | Week 1 |
| DP-005 | IaC tool | AWS CDK (TypeScript) | Week 1 |

### Near-Term Decisions (Weeks 3-10)

| ID | Decision | Recommendation | Deadline |
|----|----------|---------------|----------|
| DP-004 | Decomposition strategy | Phased: containerize then extract | Week 6 |
| DP-006 | Agent deployment timing | After WS-05 Phase 1 + rate limiting (week 10) | Week 8 |
| DP-007 | Training approach | 3-day instructor-led + embedded SA | Week 3 |
| DP-008 | local-monolith language | Keep PHP on containers initially | Week 10 |

### Strategic Recommendations

1. **Start with WS-05 (Agent Identity) and WS-01 (DevOps) in parallel** — these are the two foundational streams that unblock everything else
2. **Invest in EKS training early** — the team's K8s gap is the #1 technical risk
3. **Use CDK for all new infrastructure** — team already has TypeScript experience from aws-microservices
4. **Plan for compliance gates** — SOC2/PCI-DSS reviews should be scheduled 2 weeks before each milestone
5. **Consider ECS Fargate as fallback** — if EKS adoption proves too slow, ECS provides a simpler container path

---

*Generated: 2026-06-16 | TD Version: eba-execution-plan-generator | Mode: Unified (MODA + ARA)*
