# Portfolio Analysis Orchestrator

> Automated analysis of your service portfolio for agentic AI readiness and cloud-native modernization -- two dedicated analyses (ARA + MOD) with portfolio-level cross-cutting analysis, dependency-aware roadmaps, and consolidated reports.

This project provides a [Kiro](https://kiro.dev) Power that orchestrates [AWS Transform](https://docs.aws.amazon.com/transform/) managed transformation definitions across multiple repositories, plus example reports and interactive dashboards.

## Architecture

There are two layers:

1. **AWS Transform Managed Transformation Definitions** — published analysis logic available via `atx tp list` (early access)
2. **Kiro Power** — an orchestrator that reads `portfolio-config.yaml`, classifies repos, generates ATX configs, spawns parallel subagents, and consolidates reports

### Two-Analysis Architecture

| Analysis | Description |
|---|---|
| **Modernization Readiness Analysis (MOD)** | Scans portfolios for cloud-native maturity gaps and maps findings to AWS modernization pathways. |
| **Agentic Readiness Analysis (ARA)** | Evaluates whether systems are ready to be safely called by AI agents — covering APIs, identity, state management, human-in-the-loop, and observability. |

Zero question overlap between ARA and MOD. The `analysis_type` field routes which analyses run:
- `agentic-readiness` -> ARA only
- `modernization` -> MOD only
- `full` -> both analyses

### Analysis Flow

> **Per-repo execution model.** Subagents run **in parallel across repositories** but TDs are sequenced **within each repository** in `full` mode (ARA → MOD). Concurrent ATX runs against the same repo path fork divergent staging branches and lose artifacts. Portfolio TDs (Portfolio ARA → Portfolio MOD) run **strictly serially** with a Reconciliation Gate between each. See `orchestrator/POWER.md` for the full safety contracts.

```mermaid
flowchart TB
    CONFIG[portfolio-config.yaml] --> POWER[Power]
    
    POWER --> CLASSIFY[Classify Repos]
    CLASSIFY --> ROUTE{analysis_type?}
    
    ROUTE -->|agentic-readiness| A_GEN[Generate ARA configs]
    ROUTE -->|modernization| M_GEN[Generate MOD configs]
    ROUTE -->|full| ALL[All paths]
    ALL --> A_GEN
    ALL --> M_GEN

    A_GEN --> A_RUN[ARA TD per repo<br/>parallel across repos]
    M_GEN --> M_RUN[MOD TD per repo<br/>parallel across repos<br/>after ARA in full mode]

    A_RUN --> GATE1[Reconciliation Gate]
    M_RUN --> GATE1

    GATE1 --> A_PORT[Portfolio ARA TD]
    A_PORT --> GATE2[Reconciliation Gate]
    GATE2 --> M_PORT[Portfolio MOD TD]

    A_PORT --> A_OUT[ARA Portfolio Report]
    M_PORT --> M_OUT[MOD Portfolio Report]

    A_OUT --> DONE[Done]
    M_OUT --> DONE
```

### Repo Classification

The Power classifies each repo before spawning subagents. Classification determines N/A question mappings in both TDs. User override via `repo_type` in config always takes precedence.

```mermaid
flowchart TB
    SCAN[Scan Repo] --> CODE{Source code?}
    
    CODE -->|Yes| MULTI{Multiple services?}
    CODE -->|No| IAC{IaC only?}
    
    MULTI -->|Yes| T1[monorepo]
    MULTI -->|No| ENTRY{Has entry point?}
    
    ENTRY -->|Yes| T2[application]
    ENTRY -->|No| T3[library]
    
    IAC -->|Yes| T4[infrastructure-only]
    IAC -->|No| DEPLOY{Deploy configs?}
    
    DEPLOY -->|Yes| T5[deployment-config]
    DEPLOY -->|No| T6[application — default]
```

### Config -> ATX Config Generation

```mermaid
flowchart TB
    YAML[portfolio-config.yaml] --> POWER[Power]
    
    POWER -->|ARA config| ARA_CFG
    POWER -->|MOD config| MOD_CFG

    subgraph ARA_CFG [ARA additionalPlanContext]
        A1[repo_type]
        A2[service_archetype]
        A3[agent_scope]
        A4[context]
        A5[priority]
        A6[tags]
    end

    subgraph MOD_CFG [MOD additionalPlanContext]
        M1[repo_type]
        M2[context]
        M3[priority]
        M4[tags]
        M5[preferences — prefer/avoid]
    end
```

> `agent_scope` is ARA-only (drives conditional BLOCKERs). `service_archetype` is ARA-only (determines core/extended question tiers). `preferences` is MOD-only (frames recommendations). `repo_type`, `context`, `priority`, and `tags` are shared.

### Report Output

Every per-repo and portfolio analysis emits a **four-artifact bundle**: `.md` (richest narrative), `.json` (canonical machine-readable contract for the dashboard and downstream TDs), `.html` (single self-contained visualization), and `.metadata.json` (version compatibility sidecar). The `.json` artifact is authoritative if the four ever disagree.

```mermaid
flowchart LR
    subgraph ARA [agentic-readiness-analysis/]
        AR1[repo-a-ara-report<br/>md - json - html - metadata.json]
        AR2[repo-b-ara-report<br/>md - json - html - metadata.json]
        AR3[portfolio-ara-report<br/>md - json - html - metadata.json]
    end

    subgraph MOD [modernization-readiness-analysis/]
        MR1[repo-a-mod-report<br/>md - json - html - metadata.json]
        MR2[repo-b-mod-report<br/>md - json - html - metadata.json]
        MR3[portfolio-mod-report<br/>md - json - html - metadata.json]
    end

```

## Getting Started

### Prerequisites

- Valid AWS credentials (`aws sts get-caller-identity` -- the orchestrator checks this first and fails fast if expired)
- [AWS Transform CLI](https://docs.aws.amazon.com/transform/) installed (`atx --version`)
- [Kiro IDE](https://kiro.dev) with the Portfolio Analysis Orchestrator power installed

### Step 1: Verify Managed Transformation Definitions

The analyses use AWS-managed transformation definitions (early access). Verify they are available:

```bash
atx tp list
```

You should see:
- `AWS/agentic-readiness-analysis` — Evaluates whether systems are ready to be safely called by AI agents
- `AWS/modernization-readiness-analysis` — Scans portfolios for cloud-native maturity gaps and maps findings to AWS modernization pathways
- `AWS/portfolio-agentic-readiness-analysis` — Aggregates individual ARA reports into portfolio-level cross-cutting analysis
- `AWS/portfolio-modernization-readiness-analysis` — Aggregates individual MOD reports into portfolio-level roadmap and analysis

### Step 2: Install the Kiro Power

The Kiro Power lives at [`orchestrator/POWER.md`](orchestrator/POWER.md) and registers in Kiro as the `orchestrator` power (display name: **Portfolio Analysis Orchestrator**).

To install:

1. Open Kiro IDE
2. Open the Powers panel
3. Add a custom power from local directory and point Kiro at the `orchestrator/` directory of this repository

### Step 3: Create Your Portfolio Configuration

```yaml
portfolio_name: "my-platform"
analysis_type: "full"
context: "Building customer-facing AI agents while modernizing infrastructure"
agent_scope: "write-enabled"

transformation_definitions:
  agentic_readiness: "AWS/agentic-readiness-analysis"
  modernization: "AWS/modernization-readiness-analysis"
  portfolio_agentic_readiness: "AWS/portfolio-agentic-readiness-analysis"
  portfolio_modernization: "AWS/portfolio-modernization-readiness-analysis"

preferences:
  prefer: ["eks", "aurora", "bedrock"]
  avoid: ["self-managed-kafka", "oracle"]

repositories:
  - name: "service-a"
    repository_url: "https://github.com/org/service-a.git"
    path: "./services/service-a"
    priority: "P0"
  - name: "service-b"
    path: "./services/service-b"
    priority: "P1"

dependency_overrides:
  - source: "service-a"
    target: "service-b"
    type: "sync"
    description: "REST API calls"
```

See `portfolio-config.schema.json` for the full schema.

### Step 4: Run the Analysis

In Kiro chat:

```
Run the portfolio analysis orchestrator on portfolio-config.yaml
```

Kiro handles cloning, classification, config generation, parallel execution, and report consolidation.

**What Kiro does for you, beyond the obvious.** The orchestrator enforces three safety contracts that prevent silent data loss in long-running ATX runs: a no-polling contract for subagents, per-repo serialization within `full` mode, and strictly serial portfolio TDs gated by a reconciliation step. Read [`orchestrator/POWER.md`](orchestrator/POWER.md) for the full contracts and the seven steering files for runbook-level depth.

### Step 5 (Alternative): Run Manually Without Kiro

```bash
# Individual ARA (per repo)
atx custom def exec -n AWS/agentic-readiness-analysis -p ./services/my-service -g file://atx-config-ara.yaml -x -t

# Individual MOD (per repo)
atx custom def exec -n AWS/modernization-readiness-analysis -p ./services/my-service -g file://atx-config-mod.yaml -x -t

# Portfolio ARA (after all individual ARA analyses)
atx custom def exec -n AWS/portfolio-agentic-readiness-analysis -p . -g file://atx-portfolio-ara-config.yaml -x -t

# Portfolio MOD (after all individual MOD analyses)
atx custom def exec -n AWS/portfolio-modernization-readiness-analysis -p . -g file://atx-portfolio-mod-config.yaml -x -t
```

Always use `-x` (non-interactive) and `-t` (trust all tools) for batch execution.

## Project Structure

```
├── orchestrator/                       # Kiro Power (orchestration logic)
│   ├── POWER.md                        # Main power file with safety contracts
│   └── steering/                       # Runbook-level steering files
├── examples/
│   ├── fixtures/
│   │   └── monolith/                   # PHP test fixture (out-of-box testing)
│   └── reports/                        # Generated example reports
│       └── full-analysis/           # Full analysis across 6 repos
├── portfolio-config.schema.json        # Input contract (JSON schema)
└── README.md
```

## Example Reports

The `examples/reports/` directory contains a complete set of generated reports:

```
examples/reports/full-analysis/
├── portfolio-config.yaml
├── agentic-readiness-analysis/
│   ├── aws-microservices-ara-report.{md,json,html,metadata.json}
│   ├── books-api-ara-report.{md,json,html,metadata.json}
│   ├── eks-saas-gitops-ara-report.{md,json,html,metadata.json}
│   ├── local-monolith-ara-report.{md,json,html,metadata.json}
│   ├── unishop-monolith-ara-report.{md,json,html,metadata.json}
│   └── ecommerce-platform-v2-portfolio-ara-report.{md,json,html,metadata.json}
└── modernization-readiness-analysis/
    ├── aws-microservices-mod-report.{md,json,html,metadata.json}
    ├── books-api-mod-report.{md,json,html,metadata.json}
    ├── eks-saas-gitops-mod-report.{md,json,html,metadata.json}
    ├── local-monolith-mod-report.{md,json,html,metadata.json}
    ├── unishop-monolith-mod-report.{md,json,html,metadata.json}
    └── ecommerce-platform-v2-portfolio-mod-report.{md,json,html,metadata.json}
```

Each report is a four-file bundle: `.md` (narrative), `.json` (machine-readable), `.html` (self-contained visualization), `.metadata.json` (version sidecar).

## Live Dashboard

See the interactive portfolio dashboards (ARA + MOD) deployed at: **https://d2fplme21ym2t.cloudfront.net**

Each analysis also generates a self-contained `.html` report per repo and at portfolio level — see the examples in `examples/reports/full-analysis/`.

## Local Monolith (Test Fixture)

The `examples/fixtures/monolith/` directory contains a simple PHP application used as a test fixture so you can run analyses out of the box without cloning external repos.

## Contributing

We welcome contributions that improve the orchestration workflow or documentation. Use the GitHub issue templates to report bugs or suggest enhancements.

See [CONTRIBUTING.md](CONTRIBUTING.md) for general guidelines.

## Security

See [SECURITY.md](SECURITY.md) for security guidelines and [THREAT_MODEL.docx](THREAT_MODEL.docx) for the threat analysis. Treat analysis reports as confidential — they contain architecture details.

## Related Resources

- [AWS Transform Documentation](https://docs.aws.amazon.com/transform/)
- [AWS Transform CLI Reference](https://docs.aws.amazon.com/transform/latest/userguide/custom-command-reference.html)
- [AWS Modernization Pathways](https://skillbuilder.aws/learning-plan)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)

## License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.
