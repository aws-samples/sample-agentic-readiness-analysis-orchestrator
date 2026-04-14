# TASKS: Transformation Definition Restructuring

## Current State

```
Power: agentic-assessment-orchestrator
├── Reads portfolio-config.yaml (goal, repos, preferences, dependency_overrides)
├── TD: individual-aws-agentic-assessment (56 criteria, 5 categories, 1-4 scoring)
│   └── Mixes agentic readiness + modernization in one TD
│   └── Goal system re-weights everything (4 goals, conditional sections/phases/pathways)
│   └── Repo type classification + N/A mapping inside the TD
│   └── 7 pathways + decomposition + Quick Agent Wins (all conditional)
├── TD: portfolio-agentic-assessment (aggregates individual reports)
│   └── Tiered gap classification, pathway aggregation, 4-phase roadmap
│   └── AWS Programs (MAP, OLA, MMP, VMP, WAMP, EBA, ISV WMP, CE)
```

## Target State

```
Power: assessment-orchestrator
├── Reads portfolio-config.yaml
├── Classifies repos (application / infrastructure-only / deployment-config / monorepo / library)
├── Passes repo_type in additionalPlanContext to TDs
├── Routes by assessment_type:
│
├── assessment_type: "agentic-readiness"
│   ├── TD: agentic-readiness-assessment (49 questions, BLOCKER/RISK/INFO)
│   │   └── Reads repo_type → applies N/A mapping → skips N/A in counts
│   │   └── Reads agent_scope → evaluates conditional BLOCKERs
│   │   └── Output: readiness profile per repo
│   └── TD: portfolio-agentic-readiness
│       └── Cross-cutting blockers, readiness distribution, agentic programs
│
├── assessment_type: "modernization"
│   ├── TD: modernization-assessment (37 questions, scored 1-4)
│   │   └── Reads repo_type → applies N/A mapping → excludes N/A from averages
│   │   └── Reads repo_type → marks N/A pathways as Not Applicable
│   │   └── Output: category scores, triggered pathways
│   └── TD: portfolio-modernization
│       └── Cross-cutting concerns, pathway aggregation, roadmap, AWS Programs
│
├── assessment_type: "full" → runs both in parallel
```


## Source Documents

| Document | Location | Content |
|----------|----------|---------|
| ARA Questionnaire | `documents-study/agentic-readiness-assessment-v2.md` | 49 questions, 8 sections, BLOCKER/RISK/INFO, repo type N/A mapping, readiness profiles, remediation guidance, agentic programs |
| MOD Questionnaire | `documents-study/modernization-readiness-assessment-v2.md` | 37 questions, 5 sections, scored 1-4, repo type N/A mapping, 7 pathways, AWS Programs, learning materials |
| Architecture Diagrams | `documents-study/architecture-flow.md` | Current vs target state, repo classification flow, config generation, report structure |

---

## Tasks

### Phase 1: ARA Transformation Definition

- [ ] **T1.1** Write TD `agentic-readiness-assessment` as a Markdown transformation definition
  - Source: `agentic-readiness-assessment-v2.md`
  - Step 0: Read additionalPlanContext (repo_type, agent_scope, context, priority, tags)
  - Step 1: Discovery — scan repo for all files (IaC, source code, API specs, CI/CD, configs, containers, dependency manifests). Ignore node_modules, target, build dirs.
  - Step 2: Evaluate — 49 questions across 8 sections (API, AUTH, STATE, HITL, DATA, DISC, OBS, ENG)
  - Scoring: BLOCKER / RISK / INFO
  - Conditional BLOCKERs (⚡): API-Q4, STATE-Q1, AUTH-Q7, DATA-Q2 — evaluated based on `agent_scope` from additionalPlanContext
  - repo_type handling: read from additionalPlanContext → apply N/A mapping → skip N/A questions → exclude from counts
  - N/A display format: Severity=N/A, Finding="This is a {repo_type} repository. This question does not apply.", Gap=N/A, Recommendation=N/A
  - No pathways, no decomposition, no goals, no re-weighting, no preferences

- [ ] **T1.2** Define ARA report template in the TD
  - Metadata header: repo name, date, repo_type, agent_scope
  - Readiness Profile: Agent-Ready (0 blockers, 0-2 risks) / Pilot-Ready (0 blockers, 3-5 risks) / Remediation Required (1-2 blockers) / Not Agent-Integrable (3+ blockers)
  - Summary: BLOCKER count, RISK count, INFO count (excluding N/A)
  - BLOCKERs section: listed first with remediation guidance per blocker
  - RISKs section: listed with compensating control options
  - INFOs section: listed for planning reference
  - Detailed findings: all 49 questions with finding, gap, recommendation, evidence files
  - N/A questions: listed with N/A format (not omitted)
  - Evidence index: key files examined

- [ ] **T1.3** Define additionalPlanContext schema for ARA
  ```yaml
  additionalPlanContext: |
    repo_type: "application"           # from Power classification
    agent_scope: "write-enabled"       # read-only | write-enabled
    context: "Legacy PHP e-commerce"   # free-text
    priority: "P0"                     # P0/P1/P2
    tags: ["monolith", "php"]          # optional
  ```

- [ ] **T1.4** Define constraints and guardrails for ARA TD
  - Read-only assessment — do not modify source code
  - All 49 questions must appear in report (N/A questions use N/A format)
  - Evidence-based: cite specific file names and resource names
  - Absence is evidence: if a search finds nothing, that's a finding
  - Do not inflate severities: BLOCKER means deployment must not proceed

- [ ] **T1.5** Test ARA TD against example repos
  - Run against `monolith/` (application, write-enabled)
  - Run against `monolith/infrastructure/` (infrastructure-only)
  - Verify N/A mapping works correctly
  - Verify conditional BLOCKERs evaluate correctly for read-only vs write-enabled
  - Compare output against old TD output for same repos

### Phase 2: MOD Transformation Definition

- [ ] **T2.1** Write TD `modernization-assessment` as a Markdown transformation definition
  - Source: `modernization-readiness-assessment-v2.md`
  - Step 0: Read additionalPlanContext (repo_type, context, priority, tags, preferences)
  - Step 1: Discovery — scan repo for all files (IaC, source code, API specs, CI/CD, configs, containers, dependency manifests, K8s manifests, Helm charts). Ignore node_modules, target, build dirs.
  - Step 2: Evaluate — 37 questions across 5 sections (INF, APP, DATA, SEC, OPS)
  - Scoring: 1-4 scale (4=Mature, 3=Partial, 2=Needs Work, 1=Not Present)
  - repo_type handling: read from additionalPlanContext → apply N/A question mapping → exclude N/A from category averages → apply N/A pathway mapping
  - N/A scoring: excluded from numerator AND denominator. If all questions in category are N/A, category score = "N/A", excluded from overall average
  - 7 AWS Modernization Pathways with trigger conditions mapped to new question IDs (INF-Q, APP-Q, DATA-Q, SEC-Q, OPS-Q)
  - Decomposition strategy: included when APP-Q2 (Monolith vs Microservices) < 3
  - Preferences: read from additionalPlanContext, used to frame recommendations
  - No goals, no goal re-weighting, no conditional sections

- [ ] **T2.2** Define MOD report template in the TD
  - Metadata header: repo name, date, repo_type
  - Overall score + category score table (with caveat about reviewing categories individually)
  - Top 5 gaps: lowest-scoring questions
  - Quick Agent Wins: based on findings, suggest what agents could be built given the current architecture. Triggers: API docs exist → API-aware agent; structured JSON APIs → tool integration; clear DB schema → data query agent; CI/CD pipeline → DevOps agent; documentation exists → RAG knowledge agent. Only include wins where the system has enough foundation.
  - Pathway summary table: all 7 pathways with Status (Triggered/Not Triggered/Not Applicable), Priority, Key Trigger Criteria, Est. Effort
  - Pathway detail subsections: only for Triggered pathways
  - Decomposition strategy: conditional on APP-Q2
  - Detailed findings: all 37 questions per section
  - N/A questions: listed with N/A format, N/A categories shown as "N/A" with ➖ emoji
  - Learning materials: mapped to triggered pathways
  - Evidence index

- [ ] **T2.3** Define additionalPlanContext schema for MOD
  ```yaml
  additionalPlanContext: |
    repo_type: "application"           # from Power classification
    context: "Legacy PHP e-commerce"   # free-text
    priority: "P0"                     # P0/P1/P2
    tags: ["monolith", "php"]          # optional
    preferences:
      prefer: ["eks", "aurora"]
      avoid: ["serverless"]
  ```

- [ ] **T2.4** Define pathway trigger logic with new question IDs
  - Move to Cloud Native: APP-Q2 < 3 (guard), INF-Q1 < 3, APP-Q3 < 3, APP-Q4 < 3
  - Move to Containers: INF-Q1 < 3 (guard: must be EC2-based), no Dockerfile
  - Move to Open Source: DATA-Q4 < 3, INF-Q2 mentions commercial DB
  - Move to Managed Databases: INF-Q2 < 3, DATA-Q3 < 3
  - Move to Managed Analytics: INF-Q4 < 3 (guard: data processing must exist)
  - Move to Modern DevOps: INF-Q10 < 3, INF-Q11 < 3, OPS-Q5 < 3, OPS-Q6 < 3
  - Move to AI: no AI frameworks, no vector DB, no RAG, no eval framework

- [ ] **T2.5** Define constraints and guardrails for MOD TD
  - Read-only assessment
  - All 37 questions must appear in report
  - All 7 pathways must appear in pathway table (even if Not Triggered or N/A)
  - Evidence-based with file references
  - Calibrate scores honestly: 4 means genuinely mature, not just "has something"

- [ ] **T2.6** Test MOD TD against example repos
  - Run against `monolith/` (application)
  - Verify pathway triggers fire correctly
  - Verify N/A mapping for non-application repos
  - Compare output against old TD output

### Phase 3: Portfolio TDs

- [ ] **T3.1** Write TD `portfolio-agentic-readiness`
  - Input: ARA reports from all repos
  - Discovery: locate all `*-ara-report.md` files in repo directories
  - Parse: extract readiness profile, blocker/risk/info counts, per-question findings
  - Output:
    - Executive dashboard: portfolio readiness distribution (count per profile)
    - Cross-cutting BLOCKERs: same blocker in 2+ repos → portfolio-level blocker
    - Cross-cutting RISKs: same risk in 3+ repos → portfolio-level concern
    - Service dependency map: from dependency_overrides in config
    - Remediation guidance: which blockers to fix first across portfolio
    - Agentic programs: EBA-Agentic AI, Readiness Workshop, AgentCore Enablement
    - Service-by-service summary: repo name, profile, blocker count, risk count
  - NO pathways, NO roadmap phases, NO scores

- [ ] **T3.2** Write TD `portfolio-modernization`
  - Input: MOD reports from all repos
  - Discovery: locate all `*-mod-report.md` files in repo directories
  - Parse: extract scores, pathway triggers, findings per question, technology stack info
  - Output:
    - Executive dashboard: portfolio score overview, category averages, readiness distribution
    - Technology stack summary: languages, databases, compute patterns, IaC tools across portfolio
    - Service dependency map: from dependency_overrides — coupling scores, fan-in/fan-out, blast radius, circular dependency detection
    - Cross-cutting concerns: questions scoring < 3 in 3+ repos
    - Dependency-aware phased roadmap: 4 phases (Cross-Cutting Foundation → Quick Wins → Foundation → Advanced), services assigned based on dependencies and scores
    - Pathway aggregation: which pathways triggered across portfolio, repo counts per pathway
    - Integration opportunities: shared services, event-driven architecture, API gateway consolidation, observability unification
    - Risk assessment: high-risk dependencies (low score + high fan-in), single points of failure, circular dependencies, likelihood × impact matrix with mitigation strategies
    - Resource allocation: team structure recommendations, skill gap analysis (required vs current skills), training recommendations mapped to triggered pathways
    - AWS Programs: MAP, OLA, MMP, VMP, WAMP, EBA (per pathway), ISV WMP, CE
    - Learning materials: aggregated from triggered pathways
    - Service-by-service summary: repo name, overall score, phase assignment, triggered pathways

### Phase 4: Update the Power

- [ ] **T4.0** Implement repo type classification in the Power
  - Scan each repo before spawning subagents
  - Decision tree:
    1. Source code files exist?
       - Yes → multiple service dirs with separate build configs? → `monorepo`
       - Yes → package manifest but no deployable entry point? → `library`
       - Yes → otherwise → `application`
    2. No source code → only IaC provisioning files (Terraform/CDK/CloudFormation)? → `infrastructure-only`
    3. No source code → deployment configs (CI/CD, Helm, Kustomize, ArgoCD, Ansible, GitOps)? → `deployment-config`
    4. Otherwise → `application` (default)
  - User override via `repo_type` in portfolio config always takes precedence
  - Write `repo_type` into ATX config for each TD
  - Single classification per repo — both TDs get the same value

- [ ] **T4.1** Update portfolio-config.yaml schema
  - Replace `goal` with `assessment_type`: "agentic-readiness" | "modernization" | "full"
  - Add `agent_scope`: "read-only" | "write-enabled" (used by ARA TD)
  - Rename `goal_context` to `context` at portfolio level
  - Keep `preferences` (used by MOD TD only)
  - Keep `repositories` with existing fields (name, path, priority, context, preferences, repo_type, tags, repository_url, report_path)
  - Keep `dependency_overrides`
  - Update `transformation_definitions`:
    ```yaml
    transformation_definitions:
      agentic_readiness: "agentic-readiness-assessment"
      modernization: "modernization-assessment"
      portfolio_agentic_readiness: "portfolio-agentic-readiness"
      portfolio_modernization: "portfolio-modernization"
    ```

- [ ] **T4.2** Update Power orchestration logic
  - Parse `assessment_type` from config
  - Classify repos (T4.0)
  - Route by assessment_type:
    - `agentic-readiness`:
      1. Generate ARA ATX config per repo (repo_type, agent_scope, context, priority, tags)
      2. Spawn parallel subagents running ARA TD
      3. Wait for all to complete
      4. Generate portfolio ARA ATX config (service inventory, dependency_overrides, portfolio_name)
      5. Run portfolio-agentic-readiness TD
    - `modernization`:
      1. Generate MOD ATX config per repo (repo_type, context, priority, tags, preferences)
      2. Spawn parallel subagents running MOD TD
      3. Wait for all to complete
      4. Generate portfolio MOD ATX config (service inventory, dependency_overrides, portfolio_name, preferences)
      5. Run portfolio-modernization TD
    - `full`:
      1. Generate both ARA and MOD ATX configs per repo
      2. Spawn parallel subagents running both TDs per repo (2 subagents per repo)
      3. Wait for all to complete
      4. Generate portfolio ARA ATX config AND portfolio MOD ATX config (separate files)
      5. Run both portfolio TDs (can be parallel — they read different report files)

- [ ] **T4.3** Update report consolidation
  - `agentic-readiness` → `agentic-readiness-assessment/` folder
  - `modernization` → `modernization-assessment/` folder
  - `full` → both folders
  - Clean up temporary `.atx-config-*.yaml` files

- [ ] **T4.4** Update POWER.md documentation
  - New config schema with assessment_type
  - New orchestration flow
  - Repo classification logic
  - Example configs for each assessment_type
  - ATX CLI reference (unchanged)

### Phase 5: Testing and Validation

- [ ] **T5.1** Run ARA against all example repos (monolith, aws-microservices, books-api, eks-saas-gitops, MonoToMicroLegacy)
- [ ] **T5.2** Run MOD against all example repos
- [ ] **T5.3** Run `full` against all example repos — verify both reports generated
- [ ] **T5.4** Run portfolio ARA — verify cross-cutting blockers and readiness distribution
- [ ] **T5.5** Run portfolio MOD — verify pathway aggregation and roadmap
- [ ] **T5.6** Test with infrastructure-only and library repo types — verify N/A handling
- [ ] **T5.7** Compare ARA + MOD outputs against old mega-TD output — verify no important findings lost

### Phase 6: Cleanup and Migration

- [ ] **T6.1** Deprecate old `individual-aws-agentic-assessment` TD
- [ ] **T6.2** Deprecate old `portfolio-agentic-assessment` TD
- [ ] **T6.3** Generate new example reports for both formats
- [ ] **T6.4** Update dashboard HTML files for new report formats
- [ ] **T6.5** Update portfolio-config.schema.json
- [ ] **T6.6** Write migration guide for existing users (old config → new config)


---

## Decisions Made

1. **Split assessment into ARA (49 questions) + MOD (37 questions)** — zero overlap, different scoring models
2. **Goal system eliminated** — replaced by `assessment_type` (agentic-readiness / modernization / full)
3. **Repo classification moved to Power** — single source of truth, passed as additionalPlanContext
4. **5 repo types**: application, infrastructure-only, deployment-config, monorepo, library
5. **`deployment-config` broadened** — covers CI/CD pipelines, Helm, Kustomize, ArgoCD, Ansible, GitOps, service mesh configs
6. **ARA scoring: BLOCKER/RISK/INFO** with conditional BLOCKERs (⚡) based on agent_scope
7. **MOD scoring: 1-4 scale** with category scores as primary output, no readiness tiers
8. **7 pathways in MOD** (added Move to AI), 0 pathways in ARA
9. **AWS Programs in MOD portfolio** (MAP, OLA, MMP, VMP, WAMP, EBA, ISV WMP, CE)
10. **Agentic Programs in ARA portfolio** (EBA-Agentic AI, Readiness Workshop, AgentCore Enablement)
11. **ARA BLOCKERs (8)**: API-Q1, API-Q4⚡, AUTH-Q1, AUTH-Q7⚡, STATE-Q1⚡, DATA-Q1, DATA-Q2⚡, ENG-Q6
12. **Scoped Permissions (AUTH-Q2)** — RISK not BLOCKER (compensable at platform layer)
13. **Rollback (ENG-Q3)** — RISK not BLOCKER (canary + circuit breaker patterns suffice)
14. **OpenAPI spec (API-Q2)** — RISK not BLOCKER (GraphQL/Smithy serve same purpose)
15. **Remediation guidance** — principles-based, not fixed order
16. **COTS** — out of scope, noted as vendor evaluation use case
17. **Agent architecture** — out of scope (prompt injection, RAG, vector stores, multi-agent, MCP, evals, kill switches)
18. **N/A handling** — TD reads repo_type, applies mapping, lists N/A questions in report, excludes from counts/averages
19. **Quick Agent Wins** — Moved to MOD report (not ARA). The MOD report has the full architecture picture needed to suggest what agents could be built. ARA tells you if the system is safe for agents; MOD tells you what agents make sense given the architecture.
20. **Discovery/scan step** — Both TDs must scan the repo for files before evaluating. Explicit in T1.1 and T2.1. Scan IaC, source code, API specs, CI/CD, configs, containers, dependency manifests. Ignore node_modules, target, build, .git dirs.
21. **Portfolio risk assessment** — Kept in portfolio-modernization TD (likelihood × impact matrix, high-risk dependencies, single points of failure)
22. **Portfolio resource allocation** — Kept in portfolio-modernization TD (team structure, skill gaps, training mapped to pathways)

## Open Questions

1. **Dashboard updates** — Need new dashboards for ARA (blocker/risk/info) and MOD (scores + pathways). Current dashboards assume old format. Reports will be regenerated.
2. **`full` portfolio output** — Two separate portfolio reports (ARA + MOD), not combined. Can run portfolio TDs in parallel since they read different report files.
3. **Portfolio MOD roadmap phases** — Generic: Cross-Cutting Foundation → Quick Wins → Foundation → Advanced Capabilities.
4. **Example reports** — Need new examples for both formats against same repos.
