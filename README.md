# Agentic Readiness Assessment

Evaluate your service portfolio's readiness for agentic AI adoption. This project provides two AWS Transform (ATX) custom transformation definitions and a Kiro Power that orchestrates them across multiple repositories to produce individual and portfolio-level readiness reports.

## What's in This Repo

```
.
├── agentic-assessment-orchestrator/     # Kiro Power — orchestrates assessments
│   ├── POWER.md                         # Power definition and documentation
│   ├── portfolio-config.example.yaml    # Example portfolio configuration
│   └── portfolio-config.schema.json     # JSON Schema for validation
├── early-access-aws-agentic-assessment/ # ATX transformation: individual repo assessment
│   └── transformation_definition.md     # 56 criteria across 5 categories
├── portfolio-agentic-assessment/        # ATX transformation: portfolio aggregation
│   └── transformation_definition.md     # Cross-service analysis and roadmap
├── monolith/                            # Local PHP monolith for testing
│   ├── index.php, Dockerfile, docker-compose.yml
│   └── infrastructure/monolith-apprunner.yaml
├── example-reports/                     # Example output from a full run
│   ├── agentic-readiness-assessment/    # Individual + portfolio reports
│   └── example-transform-custom-additional-context/  # Generated ATX configs
├── test-portfolio-config.yaml           # Portfolio config used for the example run
├── static/
│   └── end-kiro-conversation-after-using-power.png
└── sprint-plan.svg
```

## How It Works

There are two layers:

1. **ATX Custom Transformation Definitions** — the actual assessment logic published to your AWS Transform registry
2. **Kiro Power** — an orchestrator that reads a `portfolio-config.yaml`, generates ATX config files with `additionalPlanContext`, spawns parallel subagents for individual assessments, then runs the portfolio aggregation

### Assessment Flow

```
portfolio-config.yaml
        │
        ▼
  Kiro Power parses config, clones repos if needed
        │
        ▼
  ┌──────────┐ ┌──────────┐ ┌──────────┐
  │ Subagent │ │ Subagent │ │ Subagent │  ← parallel individual assessments
  │ repo-a   │ │ repo-b   │ │ repo-c   │     via atx custom def exec
  └──────────┘ └──────────┘ └──────────┘
        │           │           │
        └───────────┼───────────┘
                    ▼
        Portfolio assessment (aggregation)
                    │
                    ▼
        Consolidated reports in one folder
```

Each individual assessment evaluates 56 criteria across 5 categories:
- Infrastructure & Platform (10 criteria)
- Application Architecture (13 criteria)
- Data Foundations (11 criteria)
- Identity, Security & Governance (10 criteria)
- Operations & Observability (12 criteria)

The portfolio assessment then aggregates results, maps service dependencies, identifies cross-cutting concerns, and produces a phased modernization roadmap.

## Getting Started

### Prerequisites

- [AWS Transform CLI](https://docs.aws.amazon.com/transform/) installed (`atx --version`)
- [Kiro IDE](https://kiro.dev) with the Agentic Assessment Orchestrator power installed

### Step 1: Publish the ATX Transformation Definitions

The two transformation definitions need to be published to your AWS Transform registry:

```bash
# Publish the individual repository assessment
atx custom def publish \
  -n agentic-readiness-assessment \
  --sd early-access-aws-agentic-assessment \
  --description "Evaluate a code repository against 56 agentic readiness criteria"

# Publish the portfolio aggregation assessment
atx custom def publish \
  -n portfolio-agentic-readiness-assessment \
  --sd portfolio-agentic-assessment \
  --description "Aggregate individual assessments into portfolio-level analysis"
```

Verify they're available:

```bash
atx custom def list
```

You should see both under "User Transformations". The names you choose here must match what you put in `transformation_definitions` in your portfolio config.

### Step 2: Install the Kiro Power


The `agentic-assessment-orchestrator/` directory is a Kiro Power. To install it:

1. Open Kiro IDE
2. Open the Powers panel (click the Powers icon in the sidebar or use the command palette)
3. Click "Configure" to open the powers management panel
4. Add the `agentic-assessment-orchestrator` power from this repository — point it to the `agentic-assessment-orchestrator/` directory

Once installed, Kiro will have access to the orchestration logic defined in `POWER.md`, including how to parse your portfolio config, generate ATX configs, and coordinate parallel assessments.

### Step 3: Create Your Portfolio Configuration

Create a `portfolio-config.yaml` at the root of your working directory. At minimum:

```yaml
portfolio_name: "my-platform"
transformation_definitions:
  individual_assessment: "agentic-readiness-assessment"
  portfolio_assessment: "portfolio-agentic-readiness-assessment"
repositories:
  - name: "service-a"
    path: "./services/service-a"
    priority: "P0"
  - name: "service-b"
    path: "./services/service-b"
    priority: "P1"
```

Repositories can be already cloned locally (just set `path`) or auto-cloned by Kiro (set `repository_url` and `path`).

See `agentic-assessment-orchestrator/portfolio-config.example.yaml` for a full example with transformation preferences, dependency overrides, and exclusions.

### Step 4: Run the Assessment via Kiro

In Kiro chat, ask:

```
Run the agentic assessment orchestrator on portfolio-config.yaml
```

Kiro will:
1. Parse the config and read `transformation_definitions` for the ATX names
2. Clone repos where `repository_url` is provided and `path` doesn't exist
3. Generate a temporary `.atx-config-<service>.yaml` per repo with `additionalPlanContext` (merging global + per-service preferences)
4. Spawn parallel subagents running `atx custom def exec -n <individual_assessment> -p <repo> -g file://<config> -x -t`
5. Wait for all to complete (5–15 min per repo)
6. Generate `.atx-config-portfolio.yaml` with the full service inventory
7. Run `atx custom def exec -n <portfolio_assessment> -p . -g file://<portfolio-config> -x -t`
8. Consolidate all reports into `agentic-readiness-assessment/` at the root and clean up temp files

![Kiro Power conversation end](static/end-kiro-conversation-after-using-power.png)

### Step 5 (Alternative): Run Manually Without Kiro

You can also run the ATX transformations directly:

```bash
# Individual assessment (repeat per repo)
atx custom def exec -n agentic-readiness-assessment -p ./services/my-service -x -t

# With additional context via config file
atx custom def exec -n agentic-readiness-assessment -p ./services/my-service -g file://atx-config.yaml -x -t

# Portfolio assessment (after all individual assessments complete)
atx custom def exec -n portfolio-agentic-readiness-assessment -p . -g file://atx-portfolio-config.yaml -x -t
```

Always use `-x` (non-interactive) and `-t` (trust all tools) for batch execution.

## Example Run

This repo includes a complete example run using `test-portfolio-config.yaml` at the root. That config assesses 4 repositories:

| Service | Type | Priority | Source |
|---------|------|----------|--------|
| unishop-monolith | Java/Spring monolith | P0 | [aws-samples/unishop-monolith-to-microservices](https://github.com/aws-samples/unishop-monolith-to-microservices) |
| aws-microservices | Lambda/DDB/EventBridge | P0 | [awsrun/aws-microservices](https://github.com/awsrun/aws-microservices) |
| local-monolith | PHP monolith | P0 | `./monolith` (included in this repo) |
| books-api | Serverless SAM API | P1 | [aws-samples/aws-serverless-books-api-sample](https://github.com/aws-samples/aws-serverless-books-api-sample) |

### Example Output

The `example-reports/` directory contains the full output:

- `example-reports/agentic-readiness-assessment/` — all individual reports + the portfolio report:
  - `unishop-monolith-agentic-readiness-report.md`
  - `aws-microservices-agentic-readiness-report.md`
  - `monolith-agentic-readiness-report.md`
  - `books-api-agentic-readiness-report.md`
  - `ecommerce-platform-test-portfolio-agentic-readiness-report.md`

- `example-reports/example-transform-custom-additional-context/` — the generated ATX config files that Kiro (or you) pass to each transformation via `-g file://`. These show exactly how `additionalPlanContext` is constructed from the portfolio config:

```yaml
# example: .atx-config-local-monolith.yaml
additionalPlanContext: |
  Service: local-monolith
  Priority: P0
  Description: Local PHP monolith application targeting EKS-based containerized deployment
  Tags: monolith, php, containers, eks
  
  Transformation Preferences:
  - Prefer technologies: eks, ecr, alb, rds
  - Prefer patterns: container-orchestration, microservices
  - Avoid technologies: lambda, serverless
  - Modernization approach: aggressive
```

```yaml
# example: .atx-config-portfolio.yaml
additionalPlanContext: |
  Portfolio: ecommerce-platform-test (4 services)

  SERVICE SCORES:
  1. unishop-monolith (P0): 1.4/4.0
  2. aws-microservices (P0): 1.8/4.0
  3. local-monolith (P0): 1.5/4.0
  4. books-api (P1): 2.2/4.0

  DEPENDENCIES:
  aws-microservices→books-api: ASYNC (EventBridge)
  books-api→aws-microservices: SYNC (REST)
  ...
```

This makes it easy to see how the Kiro Power translates your `portfolio-config.yaml` into the parameters that drive each transformation.

## Local Monolith (Test Fixture)

The `monolith/` directory contains a simple PHP application used for testing. It includes:
- `index.php` — single-file PHP app
- `Dockerfile` and `docker-compose.yml` — container definitions
- `infrastructure/monolith-apprunner.yaml` — AWS App Runner config
- `agentic-readiness-assessment/monolith-agentic-readiness-report.md` — its generated assessment report

This is included so you can run the full portfolio assessment out of the box with `test-portfolio-config.yaml` without needing to clone all external repos first (the other 3 repos get auto-cloned via `repository_url`).

## Managing Transformation Definitions

### Update Definitions

If you modify the transformation definition markdown files, re-publish them:

```bash
# Delete old versions
atx custom def delete -n agentic-readiness-assessment
atx custom def delete -n portfolio-agentic-readiness-assessment

# Publish updated versions
atx custom def publish \
  -n agentic-readiness-assessment \
  --sd early-access-aws-agentic-assessment \
  --description "Evaluate a code repository against 56 agentic readiness criteria"

atx custom def publish \
  -n portfolio-agentic-readiness-assessment \
  --sd portfolio-agentic-assessment \
  --description "Aggregate individual assessments into portfolio-level analysis"
```

### List Definitions

```bash
atx custom def list
```

### Get Definition Details

```bash
atx custom def get -n agentic-readiness-assessment
```

## Scoring Scale

| Score | Label | Meaning |
|-------|-------|---------|
| 4 | ✅ Agent-Ready | Fully meets criterion |
| 3 | 🟡 Partial | Minor gaps |
| 2 | 🟠 Needs Work | Significant gaps |
| 1 | ❌ Not Present | Missing or inadequate |

## Roadmap

1. **Custom output formats** — Allow transformation definitions to produce reports in configurable formats (JSON, CSV, SARIF) beyond Markdown, so teams can feed results into their existing dashboards and tooling
2. **Interactive HTML dashboard** — Auto-generate a visual portfolio dashboard from the assessment reports. A hand-built prototype lives at `example-reports/agentic-readiness-assessment/dashboard.html` — open it in a browser to see what this could look like

## Related Resources

- [AWS Transform Documentation](https://docs.aws.amazon.com/transform/)
- [AWS Transform CLI Reference](https://docs.aws.amazon.com/transform/latest/userguide/custom-command-reference.html)
- [AWS Modernization Pathways](https://skillbuilder.aws/learning-plan)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
