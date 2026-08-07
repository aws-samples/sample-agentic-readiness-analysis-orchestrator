# Portfolio MOD Report Template

> **Purpose:** Loaded by the Portfolio Modernization Readiness Analysis (portfolio-mod) TD when compiling the aggregated findings into the markdown report artifact. Defines the report header, executive dashboard, technology stack summary, service dependency map, cross-cutting concerns, phased roadmap, pathway aggregation, integration opportunities, risk analysis, resource allocation, AWS programs, learning materials, service-by-service summary, and analysis inventory.

---

## Report Template

The portfolio MOD TD emits a **four-artifact bundle** per the Four-Artifact Output Contract: `{portfolio_name}-portfolio-mod-report.md` (narrative), `.json` (canonical), `.html` (self-contained), `.metadata.json` (sidecar). This section specifies the MD structure; the JSON and HTML render subsets of the same data per the contract.

---

### Report Header

```markdown
# Portfolio Modernization Readiness Analysis Report

**Date**: <YYYY-MM-DD>
**Services Analyzed**: <count>
**Portfolio Context**: <context from additionalPlanContext, or "Not provided">
**Technology Preferences**: Prefer: <prefer list or "None">; Avoid: <avoid list or "None">
```

---

### Executive Dashboard

```markdown
## Executive Dashboard

### Portfolio Score Overview

| Metric | Value |
|--------|-------|
| Portfolio Overall Score | X.X / 4.0 |
| Score Range | X.X – X.X |
| Highest Scoring Service | <name> (X.X) |
| Lowest Scoring Service | <name> (X.X) |
| Pathways Triggered (portfolio-wide) | N of 7 |
| Cross-Cutting Foundational Blockers | N |
| Cross-Cutting Improvement Opportunities | N |

### Readiness Distribution

| Level | Services | Percentage | Description |
|-------|----------|------------|-------------|
| ✅ Mature (3.5–4.0) | N | X% | Fully meets criteria. Minor optimization only. |
| 🟡 Partial (2.5–3.4) | N | X% | Partially meets criteria. Targeted improvements needed. |
| 🟠 Needs Work (1.5–2.4) | N | X% | Significant gaps. Moderate modernization effort. |
| ❌ Not Ready (<1.5) | N | X% | Fundamental gaps. Major modernization required. |

### Category Score Averages

| Category | Portfolio Average | Min | Max | Services with N/A |
|----------|------------------|-----|-----|-------------------|
| Infrastructure & DevOps (INF) | X.X | X.X | X.X | N |
| Application Architecture (APP) | X.X | X.X | X.X | N |
| Data Platform (DATA) | X.X | X.X | X.X | N |
| Security Baseline (SEC) | X.X | X.X | X.X | N |
| Operations & Observability (OPS) | X.X | X.X | X.X | N |

### Repo Type Distribution

| Repo Type | Count | Percentage |
|-----------|-------|------------|
| application | N | X% |
| infrastructure-only | N | X% |
| deployment-config | N | X% |
| monorepo | N | X% |
| library | N | X% |

### Readiness Snapshot

| Metric | Value |
|--------|-------|
| analysis_date | <YYYY-MM-DD> |
| total_services | <N> |
| portfolio_score | <X.X> |
| score_range_min | <X.X> |
| score_range_max | <X.X> |
| mature_services | <N> |
| partial_services | <N> |
| needs_work_services | <N> |
| not_ready_services | <N> |
| pathways_triggered | <N> |
| foundational_blockers | <N> |
| improvement_opportunities | <N> |
| category_inf | <X.X> |
| category_app | <X.X> |
| category_data | <X.X> |
| category_sec | <X.X> |
| category_ops | <X.X> |
| portfolio_level_avg | <X.X> |
```

---

### Technology Stack Summary

```markdown
## Technology Stack Summary

### Programming Languages

| Language | Services | Percentage |
|----------|----------|------------|
| <language> | N | X% |

### Database Engines

| Engine | Type | Services | Managed? |
|--------|------|----------|----------|
| <engine> | Relational / NoSQL / Vector / Cache | N | Yes / No / Mixed |

**Database Distribution**: N managed, N self-managed, N commercial, N open source

### Compute Patterns

| Pattern | Services | Percentage |
|---------|----------|------------|
| <pattern> | N | X% |

### IaC and CI/CD Tools

| Tool | Category | Services |
|------|----------|----------|
| <tool> | IaC / CI/CD | N |

### Standardization Opportunities

<Identify consolidation and standardization opportunities based on technology diversity.
If preferences were provided, note alignment with preferred technologies.>

- <opportunity 1>
- <opportunity 2>

### 🏗️ Blueprint Candidates — Repos as Standardization Templates

> These repos demonstrate strong operational patterns that can be extracted and
> applied across the portfolio. Use them as reference implementations when
> modernizing other services.

| Blueprint Repo | Overall Score | Qualifying Scores | Extractable Patterns | Benefits For |
|---|---|---|---|---|
| <repo> | X.X | INF-Q10=4, INF-Q11=3, SEC-Q7=3 | Terraform modules, GitHub Actions workflows, Dependabot config | <N> repos scoring < 2 on these questions |

<For each blueprint candidate, include a brief narrative:>

**<repo-name>** — <1-2 sentence description of what makes this repo a good blueprint>
- **Extract**: <specific files/configs to copy>
- **Apply to**: <list of repos that would benefit>
- **Effort**: Low / Medium / High
```

---

### Service Dependency Map

```markdown
## Service Dependency Map

<If dependency_overrides were provided:>

### Dependency Overview

| Source Service | Target Service | Type | Coupling | Description |
|---------------|---------------|------|----------|-------------|
| <source> | <target> | sync / async / shared_db / shared_infra | High / Medium / Low | <description> |

### Service Dependency Metrics

| Service | Fan-In | Fan-Out | Blast Radius | Role | Overall Score |
|---------|--------|---------|--------------|------|---------------|
| <service> | N | N | X% | Foundation / Leaf / Internal | X.X |

### Foundation Services (High Fan-In)

<List services with fan-in >= 3. These must be modernized first.>

### Circular Dependencies

<If circular dependencies detected:>
⚠️ **Circular dependencies detected** — these must be broken in Phase 0:
- Cycle: <Service A> → <Service B> → <Service A>
- <additional cycles>

<If no circular dependencies:>
✅ No circular dependencies detected.

<If dependency_overrides were NOT provided:>

> No dependency information was provided in the portfolio configuration. To enable
> dependency-aware analysis — including coupling scores, blast radius calculation,
> circular dependency detection, and dependency-ordered roadmap phasing — add
> `dependency_overrides` to the portfolio config.
```

---

### Cross-Cutting Concerns

```markdown
## Cross-Cutting Concerns

> Cross-cutting concerns are gaps that appear across multiple services. They are
> classified into two tiers based on score severity.

### 🚨 Foundational Blockers

> Criteria scoring < 2 in 2+ repos. These block all modernization efforts.
> Address these first — nothing else matters until these are resolved.
> **Render this section only if at least one Foundational Blocker is classified. Omit entirely if empty.**

1. **<question_id>: <question topic>** — <N> of <M applicable> services score < 2
   - **Score Distribution**: <list scores per service>
   - **Impact**: <explain how this blocks modernization>
   - **Affected Services**: <list service names>
   - **Portfolio-Level Recommendation**: <coordinated solution>

<Repeat for each Foundational Blocker.>

### 💡 Improvement Opportunities

> Criteria scoring < 3 in at least **max(3, 33% of applicable repos)** (floor of 2 for portfolios with fewer than 4 applicable repos). Important but not blocking.
> Address as capacity allows or in parallel with other modernization work.
> **Render this section only if at least one Improvement Opportunity is classified. Omit entirely if empty.**

1. **<question_id>: <question topic>** — <N> of <M applicable> services score < 3
   - **Score Distribution**: <list scores per service>
   - **Impact**: <describe impact>
   - **Affected Services**: <list service names>
   - **Portfolio-Level Recommendation**: <coordinated solution>

<Repeat for each Improvement Opportunity.>

### 🔗 Infrastructure Cross-References

> **Render this section only if the portfolio contains `infrastructure-only` or `deployment-config` repos. Omit entirely if no such repos exist.**

> The following application repo findings may be mitigated by capabilities in
> infrastructure-only or deployment-config repos in this portfolio. Individual
> scores are unchanged — verify that the infra repo's configuration covers the
> application repo's deployment.

| App Repo | Question | App Score | Potentially Covered By | Infra Repo Score | Status |
|----------|----------|-----------|------------------------|------------------|--------|
| <app-repo> | <question_id> | 1 | <infra-repo> (infrastructure-only) | <3 or 4> | Verify |

**Summary**: <N> application repo findings across <M> questions may be mitigated by infrastructure capabilities in <K> infra/deployment repos. These represent potential false positives at the portfolio level — the capability exists but in a separate repository.

> ⚠️ **Action Required**: For each "Verify" row, confirm that the infrastructure repo's
> IaC/config actually covers the application repo's deployment environment. If confirmed,
> the application repo's finding is a false positive at the portfolio level (though the
> individual repo score remains unchanged for traceability).
```

If no cross-cutting concerns are identified in either tier:

```markdown
## Cross-Cutting Concerns

No cross-cutting concerns identified. All criteria meet the minimum thresholds across the portfolio.
```

---

### Per-Category Analysis

```markdown
### Per-Category Analysis

> Regardless of the tiered classification above, provide per-category analysis
> for a complete picture of portfolio health.

#### Infrastructure & DevOps

**Portfolio Score: X.X / 4.0**

**Common Patterns:**
- <pattern>: present in N services

**Critical Gaps:**
1. <gap>: affects N services — <recommendation>

#### Application Architecture

**Portfolio Score: X.X / 4.0**

<Analyze common application patterns and gaps>

#### Data Platform

**Portfolio Score: X.X / 4.0**

<Analyze common data patterns and gaps>

#### Security Baseline

**Portfolio Score: X.X / 4.0**

<Analyze common security patterns and gaps>

#### Operations & Observability

**Portfolio Score: X.X / 4.0**

<Analyze common operational patterns and gaps>
```

---

### Dependency-Aware Portfolio Modernization Roadmap

```markdown
## Portfolio Modernization Roadmap

> Dependency-aware phased roadmap with fixed phase names. Services are ordered
> by dependency graph position, then by priority (P0 → P1 → P2), then by score.

### Sequencing Principles

1. **Foundation First**: Shared infrastructure and platform capabilities before service-specific work
2. **Dependency Order**: Upstream services before downstream dependents
3. **Risk Mitigation**: High-risk changes sequenced to minimize blast radius
4. **Parallel Tracks**: Independent services can be modernized concurrently
5. **Quick Wins**: Early wins build momentum and demonstrate value

### Phase 0 — Cross-Cutting Foundation (Mo 0–1)

**Objective**: Establish shared capabilities, break circular dependencies, and address portfolio-wide blockers.

**Cross-Cutting Activities:**
- <Foundational Blocker remediation from Step 5>
- <Circular dependency breaking from Step 4.4>
- <Shared infrastructure improvements>

**Organizational Enablers:**
- Training: <topics based on skill gaps>
- Tooling: <tools to standardize>
- Standards: <standards to establish>

**Estimated Effort**: High / Medium / Low

### Phase 1 — Quick Wins (Mo 1–2)

**Objective**: Modernize foundation services and establish patterns.

**Services in Scope:**
1. **<Service Name>** (P0, Score: X.X / 4.0)
   - Current State: <summary>
   - Target State: <summary>
   - Key Activities:
     - <activity 1>
     - <activity 2>
   - Dependencies: None (foundation service)
   - Blocks: <services waiting on this one>
   - Estimated Effort: High / Medium / Low

<Repeat for each Phase 1 service, ordered by priority then fan-in.>

**Expected Outcomes:**
- <outcome 1>
- <outcome 2>

### Phase 2 — Foundation (Mo 2–4)

**Objective**: Modernize services that depend on Phase 1 services. Replicate proven patterns.

**Services in Scope:**
1. **<Service Name>** (P1, Score: X.X / 4.0)
   - Current State: <summary>
   - Target State: <summary>
   - Key Activities:
     - <activity 1>
     - <activity 2>
   - Dependencies: <Phase 1 services>
   - Blocks: <services waiting on this one, or "None">
   - Estimated Effort: High / Medium / Low

<Repeat for each Phase 2 service.>

**Parallel Tracks:**
- <Services that can be modernized concurrently>

### Phase 3 — Advanced (Mo 4–6+)

**Objective**: Optimize leaf services, implement advanced capabilities, continuous improvement.

**Services in Scope:**
1. **<Service Name>** (P2, Score: X.X / 4.0)
   - Current State: <summary>
   - Target State: <summary>
   - Key Activities:
     - <activity 1>
   - Dependencies: <Phase 2 services>
   - Estimated Effort: High / Medium / Low

<Repeat for each Phase 3 service.>

### Total Portfolio Effort

**Total Estimated Effort**: High / Medium / Low
**Expected Timeline**: X months (with Y parallel tracks)

### Target State Architecture

> After roadmap completion, the portfolio looks like this. Derived from triggered pathways, `preferences`, resolved cross-cutting blockers, and blueprint candidates per Step 6.7.

- **Compute:** <target compute platform — 1-2 sentences>
- **Data:** <target database/storage platform — 1-2 sentences>
- **Observability:** <target observability stack — 1-2 sentences>
- **CI/CD:** <target pipeline pattern — 1-2 sentences>
- **Security:** <target security posture — 1-2 sentences>
```


---

### AWS Modernization Pathways

```markdown
## AWS Modernization Pathways

> The AWS Modernization Pathways framework recognizes there is no "one-size-fits-all"
> approach. A customer portfolio may be divided into multiple pathways depending on
> workloads and priorities; these pathways can be executed in parallel.

### Portfolio Pathway Summary

| Pathway | Services Triggered | % of Portfolio | Priority | Est. Effort |
|---------|--------------------|----------------|----------|-------------|
| Move to Cloud Native | N | X% | High / Medium / Low | High / Medium / Low |
| Move to Containers | N | X% | High / Medium / Low | High / Medium / Low |
| Move to Open Source | N | X% | High / Medium / Low | High / Medium / Low |
| Move to Managed Databases | N | X% | High / Medium / Low | High / Medium / Low |
| Move to Managed Analytics | N | X% | High / Medium / Low | High / Medium / Low |
| Move to Modern DevOps | N | X% | High / Medium / Low | High / Medium / Low |
| Move to AI | N | X% | High / Medium / Low | High / Medium / Low |

### Portfolio Pathway Aggregation

This table shows exactly which repositories fall into each pathway status, providing
a single at-a-glance view of pathway coverage across the portfolio. Each repo appears
in exactly one column per pathway row.

| Pathway | Triggered | Not Triggered | Not Applicable |
|---------|-----------|---------------|----------------|
| Move to Cloud Native | <comma-separated repo names or "—"> | <comma-separated repo names or "—"> | <comma-separated repo names or "—"> |
| Move to Containers | ... | ... | ... |
| Move to Open Source | ... | ... | ... |
| Move to Managed Databases | ... | ... | ... |
| Move to Managed Analytics | ... | ... | ... |
| Move to Modern DevOps | ... | ... | ... |
| Move to AI | ... | ... | ... |

### Per-Service Pathway Assignment

| Service | Cloud Native | Containers | Open Source | Managed DB | Managed Analytics | Modern DevOps | Move to AI |
|---------|-------------|------------|-------------|------------|-------------------|---------------|------------|
| <service> | ✅ / — / N/A | ✅ / — / N/A | ✅ / — / N/A | ✅ / — / N/A | ✅ / — / N/A | ✅ / — / N/A | ✅ / — / N/A |

### Pathway Dependencies and Parallel Execution

**Sequential Dependencies:**
- Move to Containers should precede Move to Cloud Native (containerize before decomposing)
- Move to Open Source may precede Move to Managed Databases (migrate off proprietary first)
- Move to Modern DevOps enables faster execution of all other pathways (CI/CD accelerates delivery)
- Move to Managed Databases is often a prerequisite for Move to AI (data foundations needed)

**Parallel Execution Tracks:**
- **Track 1**: <pathways that can run concurrently>
- **Track 2**: <pathways that can run concurrently>

### Pathway Details

<For each triggered pathway, include a subsection:>

#### Move to <Pathway Name>

- **Services Affected**: <list> (N total)
- **Portfolio Priority**: High / Medium / Low
- **Common Trigger Criteria**:
  - <criterion ID> score < X: affects N services
  - <criterion ID> score < X: affects N services
- **Representative AWS Services**: <list, steered by preferences if provided>
- **Key Activities**:
  1. <portfolio-level activity>
  2. <per-service activity>
- **Cross-Service Synergies**: <shared patterns, reusable templates, common tooling>
- **Estimated Effort**: High / Medium / Low across N services
- **Roadmap Phase Alignment**: Phase 0 / 1 / 2 / 3
- **Relevant Learning Materials**: Module X — <module name>

<Repeat for each triggered pathway.>

<For the Move to AI pathway specifically, include the contextual guard suppression summary:>

#### Move to AI

- **Services Affected**: <list> (N total)
- **Portfolio Priority**: High / Medium / Low
- **Aggregation**: Move to AI: Triggered in X of Y services (Z services had no AI intent in context — pathway correctly suppressed)
- **Not Triggered Breakdown**:
  - Contextual guard suppression (no AI intent): <list of services or "—">
  - Already present (AI frameworks detected): <list of services or "—">
- **Common Trigger Criteria**:
  - <criterion ID> score < X: affects N services
- **Representative AWS Services**: <list, steered by preferences if provided>
- **Key Activities**:
  1. <portfolio-level activity>
  2. <per-service activity>
- **Cross-Service Synergies**: <shared patterns, reusable templates, common tooling>
- **Estimated Effort**: High / Medium / Low across N services
- **Roadmap Phase Alignment**: Phase 3
- **Relevant Learning Materials**: Module 7 — Move to AI

### Heavy Modernization Candidates

> Render this subsection only when at least one service has pathway_load ≥ 4 (per Step 7.5). Omit entirely otherwise.

> These services trigger 4+ modernization pathways and represent concentrated modernization debt. They require dedicated sprint capacity or a focused modernization initiative rather than incremental work alongside other services.

| Service | Pathways Triggered | Pathway Load | Cross-Reference |
|---------|---------------------|--------------|-----------------|
| <service name> | <comma-separated pathway names> | N | Risk register entry (if present) |
```

---

### Integration Opportunities

```markdown
## Integration Opportunities

### Shared Service Extraction

<Identify common functionality that could be extracted into shared services.>

**Opportunity: <service name>**
- **Current State**: Duplicated in <list services>
- **Proposed Solution**: <shared service proposal, steered by preferences>
- **Benefits**: <benefits>
- **Effort**: High / Medium / Low
- **Priority**: High / Medium / Low

### Event-Driven Architecture

<Identify opportunities to replace sync calls with async events.>

**Opportunity: <integration name>**
- **Current State**: <service A> calls <service B> synchronously
- **Proposed Solution**: Event-driven with <technology, steered by preferences>
- **Benefits**: <benefits>
- **Effort**: High / Medium / Low

### API Gateway Consolidation

<Identify opportunities for unified API management.>

### Observability Unification

<Identify opportunities for standardized observability.>
```

---

### Risk Analysis

```markdown
## Risk Analysis

### Risk Matrix

| Risk | Likelihood | Impact | Priority | Mitigation | Phase |
|------|------------|--------|----------|------------|-------|
| <risk description> | High / Medium / Low | High / Medium / Low | 🔴 Critical / 🟠 High / 🟡 Medium / 🟢 Low | <mitigation strategy> | Phase 0 / 1 / 2 / 3 |

### High-Risk Dependencies

<List services with score < 2.0 AND fan-in >= 3.>

### Single Points of Failure

<List services with blast radius >= 50% and no redundancy.>

### Circular Dependency Risks

<List all circular dependencies and their resolution plan.>

### Data Availability Risks

<List services with self-managed databases AND high fan-in.>

### Observability Blind Spots

<List services without tracing AND high fan-out.>
```

---

### Resource Allocation Recommendations

```markdown
## Resource Allocation Recommendations

### Team Structure

**Recommended Approach**: <centralized platform team + service teams / federated model>

**Platform Team**:
- Responsibilities: Shared infrastructure, platform capabilities, standards
- Skills Required: <skills>

**Service Teams**:
- Responsibilities: Service-specific modernization
- Skills Required: <skills>

### Skill Gaps

| Skill | Required For | Currently Available? | Priority |
|-------|-------------|---------------------|----------|
| <skill> | <activities> | Yes / No / Partial | High / Medium / Low |

### Training Recommendations

<Recommend training programs based on common gaps. Reference learning materials below.>

### External Support

<Recommend where AWS Professional Services or consulting partners could accelerate.>
```

---

### AWS Programs & Engagement Recommendations

```markdown
## AWS Programs & Engagement Recommendations

> **This section appears ONLY in portfolio reports, NEVER in individual reports.**
> Programs are engagement-level decisions scoped to the customer's overall estate.

### Recommended Programs

| Program | Acronym | Relevance | Trigger Findings | Next Step |
|---------|---------|-----------|-----------------|-----------|
| <program name> | <acronym> | <why recommended> | <specific findings> | <recommended action> |

> If no programs are triggered:
> "No specific AWS program recommendations based on current findings. As the
> portfolio evolves, re-assess to identify program eligibility."

### Program Details

<For each recommended program, provide a brief paragraph explaining:>
- Why this program was recommended (which specific findings triggered it)
- What the program provides
- Suggested timing relative to the modernization roadmap phases

> These are engagement-level recommendations. Discuss with your AWS Solutions Architect
> or Partner to determine eligibility and timing.
```

---

### Learning Materials

```markdown
## Recommended Self-Paced Learning Materials

> Include relevant links only from the following categories based on portfolio-wide
> skill gaps identified in the Resource Allocation section and triggered pathways.

<Include only modules relevant to the portfolio's triggered pathways and skill gaps.>
```

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

Only include links from categories that are relevant to the portfolio-wide gaps and triggered pathways found in this analysis.


---

### Portfolio-Level Findings

```markdown
## Portfolio-Level Findings

> These questions evaluate capabilities that can only be assessed by looking across
> multiple repos. They are distinct from cross-cutting analysis (which aggregates
> individual scores). Individual report scores are never overridden.

### <question_id>: <question topic>

- **Score**: <1-4>
- **Finding**: <what was observed across the portfolio>
- **Evidence**: <specific repos, files, or configurations>
- **Recommendation**: <portfolio-level action>
- **Contextual Annotations**: <any individual concerns this provides context for, with "verify" instructions>

<Repeat for each of the 5 portfolio-level questions (PORT-MOD-Q1 through PORT-MOD-Q5).>
```

---

### Service-by-Service Summary

```markdown
## Service-by-Service Summary

| Service | Repo Type | Priority | Overall Score | INF | APP | DATA | SEC | OPS | Pathways Triggered | Phase |
|---------|-----------|----------|---------------|-----|-----|------|-----|-----|--------------------|-------|
| <service> | <repo_type> | P0/P1/P2 | X.X | X.X | X.X | X.X | X.X | X.X | N of 7 | 0/1/2/3 |

### Individual Service Details

#### <Service Name>

- **Overall Score**: X.X / 4.0
- **Repository Type**: <repo_type>
- **Priority**: <P0/P1/P2 or "Not set">
- **Analysis Date**: <YYYY-MM-DD>
- **Category Scores**:
  - Infrastructure & DevOps: X.X
  - Application Architecture: X.X
  - Data Platform: X.X
  - Security Baseline: X.X
  - Operations & Observability: X.X
- **Top Gaps**:
  - <question_id>: score X — <brief finding summary>
  - <question_id>: score X — <brief finding summary>
  - <question_id>: score X — <brief finding summary>
- **Triggered Pathways**: <list of triggered pathway names>
- **Key Recommendations**:
  - <top 1–3 recommendations for this service>

<If dependency information is available:>
- **Depends On**: <list of services this service depends on>
- **Depended On By**: <list of services that depend on this service>
- **Blast Radius**: X%
- **Roadmap Phase**: Phase X — <phase name>

<Repeat for each service, ordered by: overall score (lowest first), then by priority (P0 first).>
```

---

### Analysis Inventory

```markdown
## Analysis Inventory

| # | Service | Report File | Analysis Date | Repo Type | Overall Score |
|---|---------|-------------|-----------------|-----------|---------------|
| 1 | <service name> | <file path> | <date> | <repo_type> | X.X |
```

---

### Table of Contents

The complete report structure, for reference:

```markdown
# Portfolio Modernization Readiness Analysis Report

1. Executive Dashboard
   - Portfolio Score Overview
   - Readiness Distribution
   - Category Score Averages
   - Repo Type Distribution
   - Readiness Snapshot
2. Technology Stack Summary
   - Programming Languages
   - Database Engines
   - Compute Patterns
   - IaC and CI/CD Tools
   - Standardization Opportunities
   - Blueprint Candidates
3. Service Dependency Map
4. Cross-Cutting Concerns
   - Foundational Blockers
   - Improvement Opportunities
   - Infrastructure Cross-References (when infra/deployment-config repos exist)
   - Per-Category Analysis
5. Portfolio Modernization Roadmap
   - Phase 0 — Cross-Cutting Foundation
   - Phase 1 — Quick Wins
   - Phase 2 — Foundation
   - Phase 3 — Advanced
   - Target State Architecture
6. AWS Modernization Pathways
   - Portfolio Pathway Summary
   - Portfolio Pathway Aggregation
   - Per-Service Pathway Assignment
   - Pathway Dependencies and Parallel Execution
   - Pathway Details
   - Heavy Modernization Candidates (when at least one service has pathway_load ≥ 4)
7. Integration Opportunities
8. Risk Analysis
9. Resource Allocation Recommendations
10. AWS Programs & Engagement Recommendations
11. Recommended Self-Paced Learning Materials
12. Portfolio-Level Findings
13. Service-by-Service Summary
14. Analysis Inventory
```
