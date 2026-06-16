# Portfolio Configuration

How to build, validate, and edit `portfolio-config.yaml`. Read this when the user is setting up a new portfolio, modifying repository entries, adjusting preferences, or troubleshooting config validation errors.

---

## Minimum Configuration

```yaml
portfolio_name: "my-platform"
analysis_type: "agentic-readiness"

transformation_definitions:
  agentic_readiness: "agentic-readiness-analysis"
  modernization: "modernization-readiness-analysis"
  portfolio_agentic_readiness: "portfolio-agentic-readiness"
  portfolio_modernization: "portfolio-modernization"
  execution_plan: "portfolio-execution-plan-generation"

repositories:
  - name: "service-a"
    path: "./services/service-a"
  - name: "service-b"
    path: "./services/service-b"
```

---

## Configuration Schema

The full schema is in `portfolio-config.schema.json` at the repo root. Key fields:

| Field | Required | Type | Notes |
|---|---|---|---|
| `portfolio_name` | yes | string | Identifier for the portfolio |
| `analysis_type` | yes | enum | One of `agentic-readiness`, `modernization`, `full`, `execution-plan` |
| `context` | no | string | Free-text context that frames recommendations |
| `agent_scope` | no | enum | `read-only` or `write-enabled`. ARA-only — controls conditional BLOCKER severity. |
| `transformation_definitions` | yes | object | Names of the TDs in your AWS Transform registry |
| `preferences` | no | object | Global tech preferences (MOD-only) |
| `repositories` | yes | array | List of services to assess |
| `dependency_overrides` | no | array | Manual dependency declarations |

### `transformation_definitions` block

| Sub-field | Required | Notes |
|---|---|---|
| `agentic_readiness` | yes | Per-repo ARA TD name |
| `modernization` | yes | Per-repo MOD TD name |
| `portfolio_agentic_readiness` | yes | Portfolio ARA aggregator |
| `portfolio_modernization` | yes | Portfolio MOD aggregator |
| `execution_plan` | no | Portfolio execution plan generation (user-published TD, no `AWS/` prefix) |

### Per-repo fields

| Field | Required | Type | Notes |
|---|---|---|---|
| `name` | yes | string | Service identifier — used to derive the artifact slug |
| `path` | yes | string | Local path to the repo |
| `repository_url` | no | string | Git URL — Kiro clones if `path` doesn't exist |
| `priority` | no | enum | `P0`, `P1`, or `P2` |
| `context` | no | string | Free-text description of the service |
| `repo_type` | no | enum | `application`, `infrastructure-only`, `deployment-config`, `monorepo`, `library`. Overrides auto-detection. |
| `service_archetype` | no | enum | `stateless-utility`, `stateful-crud`, `orchestrator`, `data-gateway`, `event-processor`. ARA-only. Overrides auto-detection. |
| `agent_scope` | no | enum | Per-repo override of portfolio-level `agent_scope`. ARA-only. |
| `tags` | no | array | String array for categorization |
| `preferences` | no | object | Per-repo preference overrides (MOD-only) |
| `report_path` | no | string | Custom output path |

### `dependency_overrides` entry

| Field | Required | Notes |
|---|---|---|
| `source` | yes | Source service name |
| `target` | yes | Target service name |
| `type` | yes | `sync`, `async`, `shared_db`, or `shared_infra` |
| `description` | no | Free-text description |

---

## Analysis Type Choice

| `analysis_type` | When to use |
|---|---|
| `agentic-readiness` | Evaluating agent-deployment readiness. 43 questions, BLOCKER/RISK/INFO scoring. |
| `modernization` | Evaluating cloud architecture maturity. 37 questions, 1-4 scale. 7 modernization pathways. |
| `full` | Both analyses. Sequenced ARA → MOD within each repo, parallelized across repos. |

---

## Preferences (MOD-only)

The `preferences` object uses two flat arrays:

```yaml
preferences:
  prefer: ["eks", "aurora", "bedrock"]    # Technologies to recommend
  avoid: ["self-managed-kafka", "oracle"] # Technologies to avoid
```

Examples of how preferences influence recommendations:
- `avoid: ["serverless"]` → don't recommend Lambda, prefer containers
- `prefer: ["eks", "aurora"]` → recommend EKS for compute, Aurora for databases
- `avoid: ["microservices-decomposition"]` → keep as monolith, focus on containerization

### Per-repo Overrides and Merging

Per-repo `prefer` items are appended to global `prefer`. Per-repo `avoid` items are appended to global `avoid`.

**Conflict resolution:** If a value appears in both global `prefer` and per-repo `avoid`, the per-repo `avoid` wins (more specific overrides less specific). The conflicting value is removed from the merged `prefer` list.

```yaml
# Global
preferences:
  prefer: ["eks", "aurora", "rds"]
  avoid: ["oracle"]

# Per-repo
repositories:
  - name: "service-a"
    preferences:
      prefer: ["dynamodb"]
      avoid: ["rds"]  # Conflicts with global prefer — per-repo avoid wins

# Merged for service-a:
# prefer: ["eks", "aurora", "dynamodb"]   ← "rds" removed due to per-repo avoid
# avoid: ["oracle", "rds"]
```

**Preferences are MOD-only.** They appear in MOD individual ATX configs and in the Portfolio MOD ATX config — never in ARA configs.

### Common Preference Patterns

```yaml
# Keep as monolith, containerize only
preferences:
  prefer: ["ecs", "fargate"]
  avoid: ["microservices-decomposition"]

# Cost-focused: eliminate licenses
preferences:
  prefer: ["aurora-postgresql", "opensearch", "linux"]
  avoid: ["oracle", "sql-server", "windows"]

# Agent-focused: enable AI capabilities
preferences:
  prefer: ["bedrock", "opensearch-serverless", "api-gateway"]
  avoid: ["self-managed-ml-infrastructure"]
```

---

## Repo Type Classification

The Power classifies each repository before spawning subagents. The classified `repo_type` determines which questions are marked N/A in both ARA and MOD TDs. Classification happens once per repo — the same value goes into both ARA and MOD ATX configs.

If `repo_type` is set in the portfolio config for a repository, the Power uses that value and skips auto-detection.

### Auto-Detection Decision Tree

```
🔍 Scan Repo
    │
    ▼
┌─────────────────────────┐
│ repo_type in config?     │
│  YES → Use config value  │
│  NO  → Continue ▼        │
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│ Has source code?         │
│ (.java, .py, .ts, .js,  │
│  .go, .cs, .rb, .php,   │
│  .rs, etc.)              │
│  YES → ▼ (source path)  │
│  NO  → ▼ (no-source)    │
└──┬──────────────┬───────┘
   │              │
   ▼              ▼
SOURCE PATH    NO-SOURCE PATH
   │              │
   ▼              ▼
┌──────────┐  ┌──────────────────┐
│ Multiple │  │ IaC files only?  │
│ services │  │ (.tf, CFN, CDK,  │
│ w/ sep.  │  │  Helm, Kustomize)│
│ build    │  │  YES → infra-only│
│ configs? │  │  NO  → ▼         │
│  YES →   │  └────────┬─────────┘
│  monorepo│           │
│  NO → ▼  │           ▼
└──┬───────┘  ┌──────────────────┐
   │          │ Deploy configs?  │
   ▼          │ (Dockerfile,     │
┌──────────┐  │  docker-compose, │
│ Has      │  │  K8s manifests,  │
│ entry    │  │  CI/CD pipelines)│
│ point?   │  │  YES → deployment│
│ (main,   │  │        -config   │
│ index,   │  │  NO  → application│
│ app.*)   │  │        (default) │
│  YES →   │  └──────────────────┘
│  applic. │
│  NO →    │
│  library │
└──────────┘
```

| `repo_type` | Description | Triggered by |
|---|---|---|
| `application` | Deployable application with source code and entry point | Source code + entry point (also the default fallback) |
| `monorepo` | Multiple services with separate build configurations | Source code + multiple service dirs + separate build configs |
| `library` | Shared library/package without deployable entry point | Source code + package manifest but no entry point |
| `infrastructure-only` | Only IaC files | No source code, only IaC (.tf, CloudFormation, CDK, Helm, Kustomize) |
| `deployment-config` | Only deployment/CI/CD configuration | No source code, only deploy configs (Dockerfile, docker-compose, K8s manifests, CI/CD pipelines) |

---

## Validation Checklist

Before running the orchestrator, verify:

- [ ] `portfolio_name` is a non-empty string
- [ ] `analysis_type` is one of the four valid values
- [ ] `transformation_definitions` has all required TD names for the chosen `analysis_type`
- [ ] Each `repositories[]` entry has `name` and `path`
- [ ] All `path` values are relative to the portfolio root
- [ ] If `agent_scope` is set, value is `read-only` or `write-enabled`
- [ ] If `repo_type` is set on a repo, value is one of the five valid values
- [ ] If `priority` is set, value is `P0`, `P1`, or `P2`
- [ ] If `dependency_overrides[]` is present, each entry has `source`, `target`, and `type`

To validate against the JSON schema:

```bash
ajv validate -s portfolio-config.schema.json -d portfolio-config.yaml
```

---

## Example Configurations

### ARA-Only Portfolio

```yaml
portfolio_name: "payment-platform"
analysis_type: "agentic-readiness"
agent_scope: "write-enabled"
context: "Evaluating payment services for autonomous agent integration"

transformation_definitions:
  agentic_readiness: "agentic-readiness-analysis"
  modernization: "modernization-readiness-analysis"
  portfolio_agentic_readiness: "portfolio-agentic-readiness"
  portfolio_modernization: "portfolio-modernization"
  execution_plan: "portfolio-execution-plan-generation"

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

### MOD-Only Portfolio with Preferences

```yaml
portfolio_name: "ecommerce-platform"
analysis_type: "modernization"
context: "Modernizing legacy e-commerce platform for cloud-native architecture"

transformation_definitions:
  agentic_readiness: "agentic-readiness-analysis"
  modernization: "modernization-readiness-analysis"
  portfolio_agentic_readiness: "portfolio-agentic-readiness"
  portfolio_modernization: "portfolio-modernization"
  execution_plan: "portfolio-execution-plan-generation"

preferences:
  prefer: ["eks", "aurora", "bedrock"]
  avoid: ["self-managed-kafka", "oracle"]

repositories:
  - name: "storefront"
    path: "./services/storefront"
    priority: "P0"
    context: "Main customer-facing web application"
    preferences:
      avoid: ["microservices-decomposition"]  # Keep as monolith
  - name: "checkout"
    path: "./services/checkout"
    priority: "P0"
    context: "Handles payments and order processing"
    preferences:
      prefer: ["dynamodb"]
      avoid: ["rds"]
  - name: "inventory"
    path: "./services/inventory"
    priority: "P1"
    tags: ["backend", "data"]
  - name: "infra-repo"
    path: "./infrastructure"
    repo_type: "infrastructure-only"
    priority: "P2"

dependency_overrides:
  - source: "storefront"
    target: "checkout"
    type: "sync"
    description: "REST API calls for order placement"
  - source: "checkout"
    target: "inventory"
    type: "sync"
    description: "Validates inventory availability before order placement"
```

### Full Analysis

```yaml
portfolio_name: "fintech-platform"
analysis_type: "full"
context: "Building AI-powered financial advisory agents while modernizing infrastructure"
agent_scope: "read-only"

transformation_definitions:
  agentic_readiness: "agentic-readiness-analysis"
  modernization: "modernization-readiness-analysis"
  portfolio_agentic_readiness: "portfolio-agentic-readiness"
  portfolio_modernization: "portfolio-modernization"
  execution_plan: "portfolio-execution-plan-generation"

preferences:
  prefer: ["eks", "aurora", "bedrock"]
  avoid: ["self-managed-kafka"]

repositories:
  - name: "advisory-engine"
    path: "./services/advisory"
    priority: "P0"
    context: "Core financial advisory logic"
  - name: "portfolio-tracker"
    path: "./services/portfolio"
    priority: "P1"
    tags: ["backend", "data"]
  - name: "shared-infra"
    path: "./infrastructure"
    repo_type: "infrastructure-only"
    priority: "P2"
```

---

## Limitations

- Minimum 2 services required for portfolio analysis
- Individual analyses must complete successfully before portfolio aggregation
- Dependency detection is based on code analysis and may miss implicit dependencies — declare them via `dependency_overrides`
- Preferences guide MOD recommendations but do not guarantee specific solutions
- Preferences are MOD-only — not passed to ARA analyses
- Analysis quality depends on code completeness and documentation availability
