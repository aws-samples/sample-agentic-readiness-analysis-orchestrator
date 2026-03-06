---
name: "agentic-assessment-orchestrator"
displayName: "Agentic Assessment Orchestrator"
description: "Orchestrate comprehensive agentic readiness assessments across multiple repositories with portfolio-level analysis, dependency mapping, and coordinated modernization roadmaps."
keywords: ["agentic", "assessment", "portfolio", "modernization", "aws", "readiness", "transformation", "dependencies"]
author: "AWS"
---

# Agentic Assessment Orchestrator

## Overview

This Knowledge Base Power turns Kiro into an orchestrator for running comprehensive agentic readiness assessments across your entire service portfolio. Kiro reads your `portfolio-config.yaml`, handles repository cloning when needed, and coordinates two AWS Transform Custom transformations in sequence:

1. **Individual Repository Assessment** — Kiro spawns parallel subagents, one per repository, each running `atx custom def exec` concurrently to evaluate the codebase against 56 agentic readiness criteria across 5 categories
2. **Portfolio Assessment** — After all individual assessments complete, Kiro runs the portfolio transformation to aggregate results, identify cross-cutting concerns, map service dependencies, and produce a portfolio-wide modernization roadmap

The transformation definition names are configurable in `portfolio-config.yaml` via the `transformation_definitions` section — use whatever names you published to your AWS Transform registry.

**How Kiro Orchestrates:**
- Parses `portfolio-config.yaml` to discover all repositories, their configuration, and the transformation definition names
- Clones repositories automatically when `repository_url` is provided and the local `path` doesn't exist
- For each repository, Kiro generates a temporary ATX configuration file containing the service's `additionalPlanContext` — merging global and per-service transformation preferences, priority, tags, and any custom constraints from the portfolio config
- Spawns parallel subagents — one per repository — to run `atx custom def exec -n <individual_assessment> -g file://<generated-config> -x -t` concurrently
- Waits for all individual assessments to complete
- Generates a portfolio-level ATX configuration file with `additionalPlanContext` containing the full service inventory, dependency overrides, global preferences, and exclusions
- Runs `atx custom def exec -n <portfolio_assessment> -g file://<generated-portfolio-config> -x -t` to generate the aggregated report
- Consolidates all reports into a single `agentic-readiness-assessment/` folder at the portfolio root — copies individual reports from each repo, alongside the portfolio report — and cleans up temporary `.atx-config-*.yaml` files

> All `atx` commands MUST use `-x` (non-interactive) and `-t` (trust all tools) flags since assessments run at scale without human intervention.

> **⏱ Long-Running Commands — Timeout Handling:** `atx custom def exec` commands are long-running operations that typically take **5–15 minutes per repository** depending on codebase size. These commands **will likely exceed default shell timeouts**. Subagents MUST NOT hang waiting for output or assume the command failed just because it took a long time. Instead, subagents should:
> 1. Launch the `atx` command with an appropriate timeout (or no timeout)
> 2. **Do NOT poll, retry, or re-check repeatedly.** After launching the command, wait patiently. Do not check status in a loop or re-run the command. A single check after a reasonable wait (10–15 minutes) is sufficient.
> 3. If the command times out or appears to hang, check **once** whether the assessment report file was generated at the expected output path
> 4. Validate success by checking for the existence of the output report file: `{repo}/agentic-readiness-assessment/{project-name}-agentic-readiness-report.md`
> 5. If the report exists, treat the assessment as successful regardless of the command's exit behavior
> 6. Only report failure if the report file is missing AND the command returned a clear error
> 7. **Never retry a transformation that is still running.** Running duplicate `atx` processes against the same repo wastes resources and can cause conflicts.

**What You Get:**
- Dependency-aware modernization roadmaps that respect service relationships
- Cross-cutting concern identification (gaps affecting 3+ services)
- Integration opportunities (shared services, event-driven architecture)
- Resource allocation recommendations (team structure, skill gaps, training)
- Risk analysis with mitigation strategies
- Configurable transformation preferences to match your constraints

**When to Use:**
- Planning agentic AI adoption across microservices
- Identifying shared infrastructure gaps
- Prioritizing modernization based on dependencies
- Tracking portfolio-wide readiness progress
- Generating executive-level portfolio reports

---

## Prerequisites

Kiro orchestrates the assessment workflow, but relies on **AWS Transform CLI** to execute the actual transformations. You need:

1. **AWS Transform CLI** installed and configured
   ```bash
   # Check if installed
   atx --version
   
   # If not installed, follow: https://docs.aws.amazon.com/transform/
   ```

2. **Transformation definitions** published to your AWS Transform registry. The names are configured in `portfolio-config.yaml`:
   ```yaml
   transformation_definitions:
     individual_assessment: "your-individual-assessment-name"
     portfolio_assessment: "your-portfolio-assessment-name"
   ```
   Verify they exist:
   ```bash
   atx custom def list | grep your-assessment-name
   ```

3. **Repository access** — Repositories can be:
   - Already cloned locally (just set `path` in the config)
   - Auto-cloned by Kiro (set `repository_url` and `path` in the config — Kiro clones if `path` doesn't exist)

---

## Quick Start

### 1. Create Portfolio Configuration

Create `portfolio-config.yaml` defining which services to assess:

```yaml
portfolio_name: "my-platform"
transformation_definitions:
  individual_assessment: "early-access-aws-agentic-assessment"
  portfolio_assessment: "portfolio-agentic-assessment"
repositories:
  - name: "service-a"
    repository_url: "https://github.com/org/service-a.git"  # optional - Kiro clones if path doesn't exist
    path: "./services/service-a"
    priority: "P0"
  - name: "service-b"
    path: "./services/service-b"  # already cloned locally
    priority: "P1"
```

See `portfolio-config.example.yaml` for complete examples with transformation preferences.

### 2. Ask Kiro to Run the Portfolio Assessment

```
"Run the agentic assessment orchestrator on portfolio-config.yaml"
```

Kiro will:
1. Parse `portfolio-config.yaml` and read `transformation_definitions` for the assessment names
2. Clone any repositories where `repository_url` is provided and `path` doesn't exist yet
3. For each repository, generate a temporary ATX config file (e.g., `.atx-config-<service-name>.yaml`) with `additionalPlanContext` containing the service's transformation preferences, priority, tags, and constraints merged from global and per-service settings
4. Spawn parallel subagents — one per repository — each running `atx custom def exec -n <individual_assessment> -p <repo-path> -g file://.atx-config-<service-name>.yaml -x -t`
5. Wait for all subagents to complete
6. Generate a portfolio-level ATX config file (e.g., `.atx-config-portfolio.yaml`) with `additionalPlanContext` containing the full service inventory, dependency overrides, global preferences, and exclusions
7. Run `atx custom def exec -n <portfolio_assessment> -p . -g file://.atx-config-portfolio.yaml -x -t` to generate the aggregated portfolio report
8. Consolidate all reports — copy individual assessment reports from each repo's `agentic-readiness-assessment/` directory into a single `agentic-readiness-assessment/` folder at the portfolio root, alongside the portfolio report. Clean up temporary `.atx-config-*.yaml` files.

### 3. Or Run Manually Step by Step

**Individual assessments (repeat for each repo):**
```bash
cd ./services/my-service
atx custom def exec -n <your-individual-assessment-name> -p . -g file://atx-config.yaml -x -t
```

Where `atx-config.yaml` contains:
```yaml
additionalPlanContext: |
  Service: my-service
  Priority: P0
  Transformation Preferences:
  - Avoid technologies: kubernetes
  - Prefer technologies: ecs, fargate
  - Modernization approach: conservative
```

**Portfolio assessment (after all individual assessments):**
```bash
atx custom def exec -n <your-portfolio-assessment-name> -p . -g file://atx-portfolio-config.yaml -x -t
```

Where `atx-portfolio-config.yaml` contains:
```yaml
additionalPlanContext: |
  Portfolio: my-platform
  Services assessed: 2
  
  Service inventory:
  - service-a (P0, ./services/service-a)
  - service-b (P1, ./services/service-b)
  
  Dependency overrides:
  - service-a -> service-b (sync): REST API calls
  
  Global transformation preferences:
  - Avoid technologies: kubernetes
  - Prefer technologies: ecs, fargate
  - Modernization approach: moderate
```

> Always use `-x` (non-interactive) and `-t` (trust all tools) when running at scale. Note: these commands are long-running (5–15 min each). If a command times out, check for the output report file before assuming failure.

---

## Portfolio Configuration

### Basic Configuration

Create a `portfolio-config.yaml` file to define which repositories to assess. Kiro will parse this file to orchestrate the assessment workflow. See `portfolio-config.example.yaml` for a complete example.

**Minimum Configuration:**

```yaml
portfolio_name: "my-platform"
transformation_definitions:
  individual_assessment: "early-access-aws-agentic-assessment"
  portfolio_assessment: "portfolio-agentic-assessment"
repositories:
  - name: "service-a"
    path: "./services/service-a"
    priority: "P0"
  - name: "service-b"
    path: "./services/service-b"
    priority: "P1"
```

**With Repository Cloning:**

```yaml
portfolio_name: "my-platform"
repositories:
  - name: "service-a"
    repository_url: "https://github.com/org/service-a.git"  # Kiro clones if path doesn't exist
    path: "./services/service-a"
    priority: "P0"
  - name: "service-b"
    path: "./services/service-b"  # Already cloned locally
    priority: "P1"
```

**Advanced Configuration:**

```yaml
portfolio_name: "ecommerce-platform"
repositories:
  - name: "checkout-service"
    repository_url: "https://github.com/org/checkout.git"
    path: "./services/checkout"
    priority: "P0"
    transformation_preferences:
      avoid_technologies: ["kubernetes"]
      prefer_technologies: ["ecs", "fargate"]
      modernization_approach: "conservative"
      
global_transformation_preferences:
  avoid_technologies: ["kubernetes"]
  prefer_technologies: ["ecs", "lambda"]
  modernization_approach: "moderate"
```

### Configuration Schema

The full configuration schema is available in `portfolio-config.schema.json`. Key sections:

- **transformation_definitions** (required): Names of the AWS Transform definitions to use
  - `individual_assessment` (required): Name for per-repository assessments
  - `portfolio_assessment` (required): Name for portfolio aggregation
- **repositories** (required): List of services to assess (minimum 2)
  - `name` (required): Service identifier
  - `path` (required): Local path to repository
  - `repository_url` (optional): Git URL — Kiro clones if `path` doesn't exist
  - `priority` (required): P0 (critical), P1 (high), P2 (medium)
- **transformation_preferences** (optional): Service-specific constraints and preferences
- **global_transformation_preferences** (optional): Portfolio-wide defaults
- **dependency_overrides** (optional): Manual dependency declarations
- **exclusions** (optional): Services or paths to exclude

## Transformation Preferences

Control how recommendations are generated for each service:

### Technology Constraints

```yaml
transformation_preferences:
  # Avoid specific technologies
  avoid_technologies: ["kubernetes", "docker", "serverless"]
  
  # Prefer specific technologies
  prefer_technologies: ["ecs", "fargate", "lambda"]
```

### Architecture Constraints

```yaml
transformation_preferences:
  # Keep as monolith (don't decompose)
  avoid_microservices_decomposition: true
  keep_as_monolith: true
  
  # Avoid specific patterns
  avoid_patterns: ["event-sourcing", "cqrs"]
  
  # Prefer specific patterns
  prefer_patterns: ["rest-api", "openapi"]
```

### Database Constraints

```yaml
transformation_preferences:
  database_constraints:
    avoid_migration: true          # Don't recommend DB migration
    keep_current_database: true    # Keep current DB engine
    avoid_managed_services: false  # Can use RDS but keep same engine
```

### Deployment Constraints

```yaml
transformation_preferences:
  deployment_constraints:
    avoid_containers: true         # No containerization
    avoid_orchestration: true      # No K8s/ECS/EKS
    prefer_vm_based: true          # Prefer EC2
```

### Modernization Approach

```yaml
transformation_preferences:
  modernization_approach: "conservative"  # aggressive | moderate | conservative | minimal
  budget_constraints: "strict"            # strict | moderate | flexible
  timeline_constraints: "urgent"          # urgent | normal | flexible
```

---

## AWS Transform CLI Reference

### Execute Transformation

```bash
atx custom def exec \
  -n <transformation-name> \
  -p <code-repository-path> \
  -g file://<configuration-file> \
  -x \
  -t
```

**Key Options:**
- `-n, --transformation-name` - Name of the transformation definition
- `-p, --code-repository-path` - Path to repository (use `.` for current directory)
- `-g, --configuration` - Path to config file (with `file://` prefix) or inline `key=value` pairs. Supports `additionalPlanContext` to pass extra context to the transformation agent
- `-t, --trust-all-tools` - Trust all tools (no prompts)
- `-x, --non-interactive` - Run without user assistance (mandatory for parallel/batch execution)
- `--tv, --transformation-version` - Specific version to use

**Configuration File Format:**

The `-g` flag accepts an ATX execution configuration file (YAML or JSON), not arbitrary data. To pass portfolio or service context to the transformation, use the `additionalPlanContext` field:

```yaml
# atx-config.yaml
additionalPlanContext: |
  Service: checkout-service
  Priority: P0
  Transformation Preferences:
  - Avoid technologies: kubernetes, k8s, helm
  - Prefer technologies: ecs, fargate
  - Modernization approach: conservative
```

```bash
atx custom def exec -n my-assessment -p ./services/checkout -g file://atx-config.yaml -x -t
```

### List Available Transformations

```bash
atx custom def list
atx custom def list --json
```

### Get Transformation Details

```bash
atx custom def get -n <transformation-name>
atx custom def get -n <transformation-name> --tv <version>
```

### Interactive Mode

```bash
atx                           # Start new conversation
atx --resume                  # Resume most recent conversation
atx -t                        # Start with all tools trusted
```

**Full CLI Reference:** https://docs.aws.amazon.com/transform/latest/userguide/custom-command-reference.html

---

## Workflow

### How Kiro Orchestrates the Assessment

When you ask Kiro to run the portfolio assessment, it follows this sequence:

```
portfolio-config.yaml
        │
        ▼
┌─────────────────────┐
│  1. Parse YAML       │  Kiro reads portfolio-config.yaml
│     config file      │  and extracts repository list
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  2. Clone repos      │  For each repo with repository_url
│     (if needed)      │  where path doesn't exist yet
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  3. Generate ATX     │  For each repo, create .atx-config-<name>.yaml
│     config files     │  with additionalPlanContext from portfolio YAML
└─────────┬───────────┘
          │
          ▼
┌─────────────────────────────────────────────┐
│  4. Run individual assessments IN PARALLEL   │
│                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │ Subagent │ │ Subagent │ │ Subagent │ ... │
│  │ repo-a   │ │ repo-b   │ │ repo-c   │     │
│  │atx -g -xt│ │atx -g -xt│ │atx -g -xt│     │
│  └──────────┘ └──────────┘ └──────────┘     │
└─────────────────────┬───────────────────────┘
                      │  (wait for all to complete)
                      ▼
┌─────────────────────┐
│  5. Generate         │  Create .atx-config-portfolio.yaml with
│     portfolio config │  full service inventory & dependencies
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  6. Run portfolio    │  atx custom def exec
│     assessment       │  -n <portfolio_assessment>
│                      │  -p . -g file://.atx-config-portfolio.yaml -x -t
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  7. Consolidate      │  Copy all reports into single
│     reports          │  agentic-readiness-assessment/ folder
│                      │  at portfolio root. Clean up temp files.
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  8. Review reports   │  All reports in one place
└─────────────────────┘
```

### Step 0: Ensure Repositories Are Available

Kiro handles this automatically when `repository_url` is provided in the config. If a repository's `path` doesn't exist locally, Kiro clones it:

```bash
git clone <repository_url> <path>
```

If repositories are already present at their configured `path`, Kiro skips cloning.

For manual setup:
```bash
mkdir -p ./services
git clone https://github.com/org/service-a.git ./services/service-a
```

### Step 1: Run Individual Assessments (Parallel)

Kiro spawns one subagent per repository from `portfolio-config.yaml`. For each repository, Kiro first generates a temporary ATX configuration file that passes the service's context via `additionalPlanContext`. This merges global transformation preferences with any per-service overrides.

**Generated ATX config example** (`.atx-config-checkout-service.yaml`):
```yaml
additionalPlanContext: |
  Service: checkout-service
  Priority: P0
  Business Criticality: critical
  Tags: backend, payment, critical-path
  Owner Team: Checkout Team
  
  Transformation Preferences:
  - Avoid technologies: kubernetes, k8s, helm
  - Deployment constraints: avoid orchestration, prefer VM-based
  - Compliance requirements: PCI-DSS, SOC2
  - Timeline constraints: urgent
  - Custom constraints: Must complete migration within 6 months
```

Each subagent then runs the individual assessment transformation concurrently:

```bash
# Each subagent runs independently, using the name from transformation_definitions.individual_assessment:
atx custom def exec -n <individual_assessment> -p <repo-path> -g file://.atx-config-<service-name>.yaml -x -t
```

**How Kiro generates the `additionalPlanContext`:**
1. Start with `global_transformation_preferences` from the portfolio config
2. Overlay the service's `transformation_preferences` (service-level overrides global)
3. Include service metadata: `name`, `priority`, `tags`, `owner_team`, `business_criticality`
4. Include any `custom_constraints` verbatim
5. Format as human-readable text for the transformation agent

The `-x` (non-interactive) flag is mandatory — subagents run without human intervention. Kiro waits for all subagents to complete before proceeding.

> **Timeout Note:** Each `atx custom def exec` invocation is a long-running process (typically 5–15 minutes). Subagents MUST NOT poll, retry, or re-check repeatedly. After launching the command, wait patiently — do NOT check status in a loop or re-run the command. A single check after 10–15 minutes is sufficient. If the command appears to time out, check **once** whether the expected report file was written to `{repo}/agentic-readiness-assessment/` before reporting failure. The presence of the report file is the definitive success indicator, not the command's exit code or timing. Never retry a transformation that is still running.

Each assessment generates:
```
{repo}/agentic-readiness-assessment/{project-name}-agentic-readiness-report.md
```

### Step 2: Run Portfolio Assessment

After all subagents complete their individual assessments, Kiro generates a portfolio-level ATX configuration file and runs the portfolio transformation using the name from `transformation_definitions.portfolio_assessment`.

**Generated ATX config example** (`.atx-config-portfolio.yaml`):
```yaml
additionalPlanContext: |
  Portfolio: ecommerce-platform
  Description: Core e-commerce platform services
  Services Assessed: 8
  
  Service Inventory:
  - storefront-web (P0, critical, ./services/storefront-web) — Tags: frontend, customer-facing
  - checkout-service (P0, critical, ./services/checkout-service) — Tags: backend, payment
  - inventory-service (P1, high, ./services/inventory-service) — Tags: backend, data
  - notification-service (P2, medium, ./services/notification-service) — Tags: backend, messaging
  
  Dependency Overrides:
  - storefront-web -> product-catalog (sync): Storefront calls Product Catalog REST API for product listings
  - storefront-web -> user-service (sync): Storefront authenticates users via User Service
  - checkout-service -> inventory-service (sync): Checkout validates inventory availability before order placement
  - order-fulfillment -> notification-service (async): Fulfillment publishes order status events to notification queue
  
  Global Transformation Preferences:
  - Avoid technologies: kubernetes, k8s, helm
  - Prefer technologies: ecs, fargate, lambda
  - Modernization approach: moderate
  - Avoid patterns: event-sourcing, cqrs
  - Prefer patterns: rest-api, openapi
  - Deployment constraints: avoid orchestration
  - Compliance requirements: SOC2
  - Budget constraints: moderate
  - Timeline constraints: normal
  
  Exclusions:
  - Services: legacy-monolith, test-harness
  - Path patterns: **/archived/**, **/test/**, **/deprecated/**
```

```bash
atx custom def exec -n <portfolio_assessment> -p . -g file://.atx-config-portfolio.yaml -x -t
```

This generates:
```
agentic-readiness-assessment/{portfolio-name}-portfolio-agentic-readiness-report.md
```

### Step 3: Consolidate Reports

After the portfolio assessment completes, Kiro consolidates all reports into a single directory at the portfolio root for easy access and review.

**What Kiro does:**
1. Creates `agentic-readiness-assessment/` at the portfolio root (if it doesn't already exist from the portfolio assessment)
2. Copies each individual assessment report from `{repo}/agentic-readiness-assessment/{project-name}-agentic-readiness-report.md` into the root `agentic-readiness-assessment/` folder
3. The portfolio report is already at `agentic-readiness-assessment/{portfolio-name}-portfolio-agentic-readiness-report.md`
4. Cleans up temporary `.atx-config-*.yaml` files generated during the assessment

**Resulting structure:**
```
agentic-readiness-assessment/
├── service-a-agentic-readiness-report.md
├── service-b-agentic-readiness-report.md
├── service-c-agentic-readiness-report.md
└── my-platform-portfolio-agentic-readiness-report.md
```

### Step 4: Review Portfolio Report

The portfolio report provides:
- **Executive Dashboard** - Portfolio-wide readiness scores and trends
- **Service Dependency Map** - Visual representation of service relationships and coupling
- **Cross-Cutting Concerns** - Gaps affecting 3+ services that should be addressed portfolio-wide
- **4-Phase Modernization Roadmap** - Dependency-aware implementation plan
- **Integration Opportunities** - Shared services, event-driven architecture, API gateway patterns
- **Resource Allocation** - Team structure, skill gaps, training recommendations
- **Risk Analysis** - Portfolio-level risks with mitigation strategies

---

## Assessment Criteria Reference

1. **Infrastructure & Platform** (10 criteria)
   - Compute, databases, orchestration, messaging, IaC, CI/CD, API gateway, streaming, networking, auto-scaling

2. **Application Architecture** (13 criteria)
   - Languages, API docs, async/sync patterns, monolith vs microservices, response formats, workflows, idempotency, rate limiting, resilience, long-running processes, versioning, service discovery, AI frameworks

3. **Data Foundations** (11 criteria)
   - Vector databases, RAG, data sources, access patterns, unstructured data, schemas, data access layer, embedding freshness, DB versions, stored procedures

4. **Identity, Security & Governance** (10 criteria)
   - Secret management, IAM, identity propagation, audit logging, rate limits, PII redaction, human approval, encryption, API auth, centralized identity

5. **Operations & Observability** (12 criteria)
   - Distributed tracing, structured logging, automated evals, SLOs, rollback, LLM cost tracking, business metrics, anomaly detection, deployment strategy, integration testing, incident automation, observability governance

## Scoring Scale

| Score | Label | Meaning |
|-------|-------|---------|
| 4 | ✅ Agent-Ready | Fully meets criterion, no gaps |
| 3 | 🟡 Partial | Partially meets criterion, minor gaps |
| 2 | 🟠 Needs Work | Exists but significant gaps |
| 1 | ❌ Not Present | Missing entirely or inadequate |

## Output Structure

After consolidation, all reports are collected into a single folder at the portfolio root:

### Consolidated Output (Portfolio Root)

```
agentic-readiness-assessment/
├── {service-a}-agentic-readiness-report.md      ← copied from services/service-a/
├── {service-b}-agentic-readiness-report.md      ← copied from services/service-b/
├── {service-c}-agentic-readiness-report.md      ← copied from services/service-c/
└── {portfolio-name}-portfolio-agentic-readiness-report.md
    ├── Executive Dashboard
    ├── Portfolio Readiness Overview
    ├── Service Dependency Map
    ├── Cross-Cutting Concerns
    ├── 4-Phase Portfolio Roadmap
    ├── Integration Opportunities
    ├── Resource Allocation
    ├── Risk Analysis
    └── Service-by-Service Summary
```

### Individual Assessment Report (per repo, before consolidation)

```
{repo}/agentic-readiness-assessment/
└── {project-name}-agentic-readiness-report.md
    ├── Executive Summary
    ├── Top 5 Priorities
    ├── 3-Phase Roadmap
    ├── Learning Materials
    ├── Detailed Findings (56 criteria)
    └── Evidence Index
```

## Example Usage

### Basic Portfolio Assessment

```yaml
# portfolio-config.yaml
portfolio_name: "payment-platform"
transformation_definitions:
  individual_assessment: "early-access-aws-agentic-assessment"
  portfolio_assessment: "portfolio-agentic-assessment"
repositories:
  - name: "payment-gateway"
    path: "./services/payment-gateway"
    priority: "P0"
  - name: "fraud-detection"
    path: "./services/fraud-detection"
    priority: "P0"
  - name: "billing-service"
    path: "./services/billing"
    priority: "P1"
```

### Portfolio with Constraints

```yaml
# portfolio-config.yaml
portfolio_name: "ecommerce-platform"

transformation_definitions:
  individual_assessment: "my-team-agentic-assessment"
  portfolio_assessment: "my-team-portfolio-assessment"

# Global preferences apply to all services
global_transformation_preferences:
  avoid_technologies: ["kubernetes"]
  prefer_technologies: ["ecs", "fargate"]
  modernization_approach: "moderate"

repositories:
  - name: "storefront"
    path: "./services/storefront"
    priority: "P0"
    transformation_preferences:
      # Override: keep as monolith
      keep_as_monolith: true
      modernization_approach: "conservative"
      
  - name: "checkout"
    path: "./services/checkout"
    priority: "P0"
    transformation_preferences:
      # Override: avoid DB migration
      database_constraints:
        avoid_migration: true
        keep_current_database: true
      
  - name: "inventory"
    path: "./services/inventory"
    priority: "P1"
    # Uses global preferences
```

## Best Practices

1. **Run individual assessments first** - Portfolio assessment requires completed individual reports
2. **Always use `-x -t` flags** - Non-interactive (`-x`) is mandatory for parallel execution at scale; trust all tools (`-t`) avoids prompts blocking subagents
3. **Use transformation preferences** - Guide recommendations to match your constraints
4. **Document dependencies** - Use `dependency_overrides` for implicit dependencies
5. **Set realistic priorities** - P0 for critical services, P1 for high priority, P2 for medium
6. **Review cross-cutting concerns** - Address portfolio-wide gaps before service-specific work
7. **Follow dependency order** - Modernize upstream services before downstream dependents
8. **Validate configuration** - Use the JSON schema to validate your portfolio-config.yaml before running
9. **Leverage parallel subagents** - Kiro runs individual assessments concurrently, so larger portfolios don't linearly increase execution time

---

## Troubleshooting

### Individual Assessment Fails

**Problem:** Transformation fails on a specific repository

**Solutions:**
1. Check AWS Transform CLI is installed: `atx --version`
2. Verify transformation is available: `atx custom def list | grep <your-transformation-name>`
3. Ensure the names in `transformation_definitions` match exactly what you published
4. Ensure you're in the correct repository directory
5. Check repository has required files (source code, build configs)
6. Run in interactive mode without `-x -t` flags to see detailed errors

### Portfolio Assessment Can't Find Individual Reports

**Problem:** Portfolio assessment reports missing individual assessments

**Solutions:**
1. Verify individual assessments completed successfully
2. Check report paths match configuration:
   ```
   {repo}/agentic-readiness-assessment/{project-name}-agentic-readiness-report.md
   ```
3. Ensure `path` in portfolio-config.yaml points to correct repository directories
4. Verify repository names in config match actual directory names

### Configuration Validation Errors

**Problem:** Portfolio configuration is rejected

**Solutions:**
1. Validate against schema:
   ```bash
   # Using a JSON schema validator
   ajv validate -s portfolio-config.schema.json -d portfolio-config.yaml
   ```
2. Check minimum requirements:
   - At least 2 repositories defined
   - Each repository has `name`, `path`, and `priority`
   - Paths are relative to portfolio root
3. Review `portfolio-config.example.yaml` for correct format

### Transformation Preferences Not Applied

**Problem:** Recommendations ignore specified constraints

**Solutions:**
1. Check preference syntax matches schema exactly
2. Verify service-specific preferences override global preferences correctly
3. Remember preferences are guidance, not guarantees - some recommendations may still suggest avoided technologies if they're the best fit
4. Review generated report's "Transformation Preferences Applied" section

### AWS Transform CLI Not Found

**Problem:** `atx: command not found`

**Solutions:**
1. Install AWS Transform CLI: https://docs.aws.amazon.com/transform/
2. Verify installation: `atx --version`
3. Check PATH includes AWS Transform CLI binary location
4. Restart terminal after installation

### ATX Command Timeout

**Problem:** `atx custom def exec` command times out or appears to hang

**Context:** This is expected behavior. Individual assessments typically take 5–15 minutes per repository. Portfolio assessments can take even longer depending on the number of services.

**Solutions:**
1. **Check for the output report first** — the command may have completed successfully even if the shell timed out:
   ```bash
   # For individual assessments:
   ls {repo}/agentic-readiness-assessment/*-agentic-readiness-report.md
   
   # For portfolio assessments:
   ls agentic-readiness-assessment/*-portfolio-agentic-readiness-report.md
   ```
2. If the report file exists, the assessment succeeded — no need to re-run
3. If the report file is missing, re-run the command with a longer timeout or no timeout
4. For very large repositories, consider running assessments individually in interactive mode (without `-x`) to monitor progress

---

## Limitations

- Minimum 2 services required for portfolio assessment
- Individual assessments must complete successfully before portfolio assessment
- Dependency detection is based on code analysis and may miss implicit dependencies
- Transformation preferences guide recommendations but don't guarantee specific solutions
- Assessment quality depends on code completeness and documentation availability

---

## Related Resources

- [AWS Transform Documentation](https://docs.aws.amazon.com/transform/)
- [AWS Transform CLI Reference](https://docs.aws.amazon.com/transform/latest/userguide/custom-command-reference.html)
- [AWS Modernization Pathways](https://skillbuilder.aws/learning-plan)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
