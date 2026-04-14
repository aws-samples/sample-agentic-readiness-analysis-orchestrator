# Assessment Architecture Flow

## Current State (Today)

```mermaid
flowchart TB
    CONFIG[portfolio-config.yaml] --> POWER[Power: Orchestrator]
    POWER --> GOAL{Parse goal}
    GOAL -->|All 4 goals use same TD| MEGA_TD

    subgraph PER_REPO [Per Repository - parallel]
        MEGA_TD[TD: individual-aws-agentic-assessment<br/>56 criteria mixed agentic + modernization<br/>Goal re-weighting + conditional sections<br/>Pathway mapping + decomposition<br/>Repo classification inside TD]
    end

    MEGA_TD --> REPORT1[Hybrid Report<br/>Goal-specific phases<br/>Conditional Quick Agent Wins<br/>Conditional Decomposition]
    REPORT1 --> PORTFOLIO_TD[TD: portfolio-agentic-assessment<br/>Tiered gap classification<br/>Goal-driven cross-cutting concerns]
    PORTFOLIO_TD --> PORTFOLIO_REPORT[Portfolio Report]

    style MEGA_TD fill:#ff6b6b,color:#fff
    style PORTFOLIO_TD fill:#ff6b6b,color:#fff
```

---

## Target State (New Architecture)

```mermaid
flowchart TB
    CONFIG[portfolio-config.yaml] --> POWER[Power: Assessment Orchestrator]
    
    POWER --> CLASSIFY[Classify Repos<br/>Scan each repo<br/>Detect: application / infrastructure-only<br/>/ deployment-cicd / monorepo / library<br/>User override via repo_type in config]
    
    CLASSIFY --> TYPE{assessment_type?}

    TYPE -->|agentic-readiness| ARA_FLOW
    TYPE -->|modernization| MOD_FLOW
    TYPE -->|full| BOTH

    BOTH[Run both in parallel] --> ARA_FLOW
    BOTH --> MOD_FLOW

    subgraph ARA_FLOW [Agentic Readiness Flow]
        ARA_CFG[Generate ATX config per repo<br/>agent_scope + repo_type + context]
        ARA_TD[TD: agentic-readiness-assessment<br/>49 questions - BLOCKER/RISK/INFO<br/>Reads repo_type from context<br/>Applies N/A mapping per repo type<br/>Skips N/A questions in scoring]
        ARA_REPORT[ARA Report per repo<br/>Readiness Profile<br/>N/A questions listed but excluded from counts]
        ARA_PORTFOLIO[TD: portfolio-agentic-readiness<br/>Cross-cutting blockers<br/>Portfolio readiness distribution<br/>Agentic programs]
        ARA_PORT_REPORT[Portfolio ARA Report]

        ARA_CFG --> ARA_TD --> ARA_REPORT --> ARA_PORTFOLIO --> ARA_PORT_REPORT
    end

    subgraph MOD_FLOW [Modernization Flow]
        MOD_CFG[Generate ATX config per repo<br/>repo_type + context + preferences]
        MOD_TD[TD: modernization-assessment<br/>37 questions - Scored 1-4<br/>Reads repo_type from context<br/>Applies N/A mapping per repo type<br/>N/A pathways marked Not Applicable]
        MOD_REPORT[MOD Report per repo<br/>Category scores + Pathways<br/>N/A categories excluded from averages]
        MOD_PORTFOLIO[TD: portfolio-modernization<br/>Cross-cutting concerns<br/>Dependency-aware roadmap<br/>AWS Programs]
        MOD_PORT_REPORT[Portfolio MOD Report]

        MOD_CFG --> MOD_TD --> MOD_REPORT --> MOD_PORTFOLIO --> MOD_PORT_REPORT
    end

    style CLASSIFY fill:#f9c74f,color:#000
    style ARA_TD fill:#4ecdc4,color:#fff
    style MOD_TD fill:#45b7d1,color:#fff
    style ARA_PORTFOLIO fill:#4ecdc4,color:#fff
    style MOD_PORTFOLIO fill:#45b7d1,color:#fff
```

---

## Repo Classification (Power Responsibility)

```mermaid
flowchart TB
    REPO[Scan Repository] --> HAS_CODE{Source code files?}
    
    HAS_CODE -->|Yes| MULTI{Multiple service dirs<br/>with separate build configs?}
    HAS_CODE -->|No| HAS_IAC{Only IaC provisioning?<br/>Terraform / CDK / CloudFormation}
    
    MULTI -->|Yes| MONOREPO[monorepo]
    MULTI -->|No| HAS_ENTRY{Deployable entry point?<br/>Dockerfile / IaC / main}
    
    HAS_ENTRY -->|Yes| APP[application]
    HAS_ENTRY -->|No| LIB[library]
    
    HAS_IAC -->|Yes| INFRA[infrastructure-only]
    HAS_IAC -->|No| HAS_DEPLOY{Deployment configs?<br/>CI/CD pipelines / Helm / Kustomize<br/>ArgoCD / Ansible / GitOps<br/>Service mesh / Env configs}
    
    HAS_DEPLOY -->|Yes| DEPLOY[deployment-config]
    HAS_DEPLOY -->|No| APP_DEFAULT[application - default]

    style MONOREPO fill:#4ecdc4,color:#fff
    style APP fill:#4ecdc4,color:#fff
    style LIB fill:#f9c74f,color:#000
    style INFRA fill:#f9c74f,color:#000
    style DEPLOY fill:#f9c74f,color:#000
    style APP_DEFAULT fill:#4ecdc4,color:#fff
```

---

## Per-Repo ATX Config Generation

```mermaid
flowchart TB
    POWER[Power + repo_type] --> TYPE{assessment_type?}

    TYPE -->|agentic-readiness| ARA_CFG
    TYPE -->|modernization| MOD_CFG
    TYPE -->|full| BOTH_CFG[Generate both]
    BOTH_CFG --> ARA_CFG
    BOTH_CFG --> MOD_CFG

    subgraph ARA_CFG [ARA Config]
        A1[repo_type: application]
        A2[agent_scope: write-enabled]
        A3[context: Legacy PHP e-commerce]
        A4[priority: P0]
        A5[tags: monolith, php]
    end

    subgraph MOD_CFG [MOD Config]
        M1[repo_type: application]
        M2[context: Legacy PHP e-commerce]
        M3[priority: P0]
        M4[tags: monolith, php]
        M5[preferences: prefer eks, aurora]
    end
```

---

## Report Output Structure

```mermaid
flowchart LR
    subgraph AR [agentic-readiness-assessment/]
        AR1[service-a-ara-report.md]
        AR2[service-b-ara-report.md]
        AR3[portfolio-ara-report.md]
    end

    subgraph MR [modernization-assessment/]
        MR1[service-a-mod-report.md]
        MR2[service-b-mod-report.md]
        MR3[portfolio-mod-report.md]
    end
```

---

## Old vs New Comparison

```mermaid
flowchart LR
    subgraph OLD [Current: 1 Mega-TD]
        direction TB
        O1[56 mixed criteria]
        O2[4 goals with re-weighting]
        O3[Repo classification inside TD]
        O4[Conditional sections]
        O5[Tiered gap classification]
        O6[7 pathways + goal alignment]
    end

    OLD -->|Split and Simplify| NEW

    subgraph NEW [New: 2 Focused TDs]
        direction TB
        N1[ARA: 49 questions<br/>BLOCKER/RISK/INFO<br/>Agentic programs]
        N2[MOD: 37 questions<br/>Scored 1-4<br/>7 pathways + AWS programs]
        N3[Power: repo classification<br/>+ orchestration]
    end
```
