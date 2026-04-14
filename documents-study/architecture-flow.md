# Assessment Architecture Flow

## Current State

```mermaid
flowchart TB
    CONFIG[📄 portfolio-config.yaml] --> POWER[⚙️ Power]
    POWER --> MEGA[🔴 1 Mega-TD<br/>56 criteria · 4 goals<br/>Conditional everything]
    MEGA --> REPORT[📊 Hybrid Report]
    REPORT --> PORT[🔴 1 Portfolio TD]
    PORT --> FINAL[📋 Portfolio Report]
```

## Target State

```mermaid
flowchart TB
    CONFIG[📄 portfolio-config.yaml] --> POWER[⚙️ Power]
    
    POWER --> CLASSIFY[🔍 Classify Repos]
    CLASSIFY --> ROUTE{assessment_type?}
    
    ROUTE -->|agentic-readiness| A_GEN
    ROUTE -->|modernization| M_GEN
    ROUTE -->|full| BOTH[Both paths]
    BOTH --> A_GEN
    BOTH --> M_GEN

    A_GEN[📝 Generate ARA configs] --> A_RUN
    M_GEN[📝 Generate MOD configs] --> M_RUN

    subgraph A_RUN [🟢 ARA per repo - parallel]
        direction TB
        A_EVAL[Evaluate 49 questions]
        A_SECTIONS[API Surface · Auth & Identity<br/>State & Transactions · Human-in-the-Loop<br/>Data Quality · Discoverability<br/>Observability · Engineering Maturity]
        A_OUT[Readiness Profile<br/>BLOCKERs · RISKs · INFOs<br/>Remediation Guidance<br/>Evidence Index]
        A_EVAL --> A_SECTIONS --> A_OUT
    end
    subgraph M_RUN [🔵 MOD per repo - parallel]
        direction TB
        M_EVAL[Evaluate 37 questions]
        M_SECTIONS[Infrastructure & DevOps<br/>App Architecture · Data Platform<br/>Security Baseline<br/>Operations & Observability]
        M_OUT[Category Scores · Top 5 Gaps<br/>7 Modernization Pathway Triggers<br/>Quick Agent Wins<br/>Decomposition Strategy<br/>Learning Materials]
        M_EVAL --> M_SECTIONS --> M_OUT
    end

    A_RUN --> A_PORT[🟢 Portfolio ARA TD<br/>Cross-cutting blockers<br/>Readiness distribution<br/>Agentic programs]
    M_RUN --> M_PORT[🔵 Portfolio MOD TD<br/>Cross-cutting concerns<br/>Dependency-aware roadmap<br/>Modernization Pathway aggregation<br/>Risk & resource analysis<br/>AWS Programs]

    A_PORT --> A_OUT[📋 ARA Portfolio Report]
    M_PORT --> M_OUT[📋 MOD Portfolio Report]

    style A_TD fill:#4ecdc4,color:#fff
    style M_TD fill:#45b7d1,color:#fff
    style A_PORT fill:#4ecdc4,color:#fff
    style M_PORT fill:#45b7d1,color:#fff
```

## Repo Classification

```mermaid
flowchart TB
    SCAN[🔍 Scan Repo] --> CODE{Source code?}
    
    CODE -->|Yes| MULTI{Multiple services?}
    CODE -->|No| IAC{IaC only?}
    
    MULTI -->|Yes| T1[📦 monorepo]
    MULTI -->|No| ENTRY{Has entry point?}
    
    ENTRY -->|Yes| T2[📦 application]
    ENTRY -->|No| T3[📦 library]
    
    IAC -->|Yes| T4[📦 infrastructure-only]
    IAC -->|No| DEPLOY{Deploy configs?}
    
    DEPLOY -->|Yes| T5[📦 deployment-config]
    DEPLOY -->|No| T6[📦 application ∗default]

    style T1 fill:#4ecdc4,color:#fff
    style T2 fill:#4ecdc4,color:#fff
    style T3 fill:#f9c74f,color:#000
    style T4 fill:#f9c74f,color:#000
    style T5 fill:#f9c74f,color:#000
    style T6 fill:#4ecdc4,color:#fff
```

## Config Flow: Portfolio YAML → Per-Repo ATX Configs

```mermaid
flowchart TB
    YAML[📄 portfolio-config.yaml] --> POWER[⚙️ Power]
    
    POWER --> |ARA config| ARA_CFG
    POWER --> |MOD config| MOD_CFG

    subgraph ARA_CFG [ARA: .atx-config-ara-repoA.yaml]
        A1[repo_type: application]
        A2[agent_scope: write-enabled]
        A3[context: Order service]
        A4[priority: P0]
        A5[tags: backend, critical]
    end

    subgraph MOD_CFG [MOD: .atx-config-mod-repoA.yaml]
        M1[repo_type: application]
        M2[context: Order service]
        M3[priority: P0]
        M4[tags: backend, critical]
        M5[preferences:]
        M6[  prefer: eks, aurora]
        M7[  avoid: serverless]
    end
```

> **Note:** `agent_scope` is ARA-only (drives conditional BLOCKERs). `preferences` is MOD-only (frames recommendations). `repo_type`, `context`, `priority`, and `tags` are shared by both.

## N/A Mapping: What Gets Skipped

```mermaid
flowchart TB
    subgraph APP [application]
        A[All questions apply<br/>All pathways apply]
    end
    
    subgraph INFRA [infrastructure-only]
        I_SKIP[❌ Skip: APP, most DATA]
        I_KEEP[✅ Keep: INF, SEC, OPS]
        I_PATH[❌ Pathways: Cloud Native,<br/>Containers, AI, Analytics]
    end
    
    subgraph DEPLOY [deployment-config]
        D_SKIP[❌ Skip: APP, DATA,<br/>most INF]
        D_KEEP[✅ Keep: IaC, CI/CD,<br/>SEC, OPS]
        D_PATH[✅ Only: Modern DevOps]
    end
    
    subgraph LIB [library]
        L_SKIP[❌ Skip: all INF,<br/>most OPS]
        L_KEEP[✅ Keep: APP, DATA,<br/>SEC, Tracing]
        L_PATH[✅ Only: Open Source, AI]
    end

    subgraph MONO [monorepo]
        M[All questions apply<br/>All pathways apply<br/>Assessed per-service]
    end
```

## Report Output

```mermaid
flowchart LR
    subgraph ARA [📁 agentic-readiness-assessment/]
        AR1[repo-a-ara-report.md]
        AR2[repo-b-ara-report.md]
        AR3[portfolio-ara-report.md]
    end

    subgraph MOD [📁 modernization-assessment/]
        MR1[repo-a-mod-report.md]
        MR2[repo-b-mod-report.md]
        MR3[portfolio-mod-report.md]
    end
```
