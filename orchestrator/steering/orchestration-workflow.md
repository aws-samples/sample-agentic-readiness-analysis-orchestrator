# Orchestration Workflow

The complete end-to-end workflow Kiro follows when running a portfolio assessment. Read this when actually executing an assessment, generating ATX configs, or spawning subagents.

> **Three safety contracts apply throughout** — they are stated in `POWER.md` and MUST be followed:
> 1. **No-Polling Contract** — Subagents call executeBash exactly once per ATX command and check the report file exactly once after it returns. No mid-run filesystem inspection.
> 2. **Per-Repo Serialization Rule** — In `full` mode, ARA → MOD → BAO run sequentially within a single repo. Cross-repo parallelism is fine; same-repo concurrency is forbidden.
> 3. **Portfolio TD Serialization** — All portfolio TDs share `-p .` and run strictly serially: Portfolio ARA → Portfolio MOD → Portfolio BAO → Bridge, with a Reconciliation Gate between each.

---

## High-Level Flow

```
portfolio-config.yaml
        │
        ▼
┌─────────────────────┐
│  0. Verify AWS       │  aws sts get-caller-identity
│     credentials      │  FAIL FAST if expired or missing
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  1. Parse YAML       │  Read assessment_type, context, preferences,
│     config file      │  repos, dependencies, TD names
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  2. Validate         │  assessment_type ∈ {agentic-readiness, modernization,
│     config           │   bpmn-opportunity, full}. Error if invalid.
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  3. Clone repos      │  For each repo with repository_url where path
│     (if needed)      │  doesn't exist yet
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  4. Classify repos   │  Run decision tree (or use config repo_type override)
│                      │  Same value used for ARA + MOD configs
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  5. Generate ATX     │  ARA configs: repo_type, agent_scope, context, priority, tags
│     config files     │  MOD configs: repo_type, context, priority, tags, merged preferences
└─────────┬───────────┘
          │
          ▼
┌─────────────────────────────────────────────────────┐
│  6. Per-repo execution                                │
│     PARALLEL ACROSS REPOS, SEQUENTIAL WITHIN A REPO  │
│                                                       │
│  full mode (one subagent per repo):                  │
│  ┌────────────────────────────┐                       │
│  │ repo-a: ARA → MOD → BAO    │ \                     │
│  ├────────────────────────────┤  \  parallel across   │
│  │ repo-b: ARA → MOD → BAO    │   >  repos            │
│  ├────────────────────────────┤  /                    │
│  │ repo-c: ARA → MOD → BAO    │ /                     │
│  └────────────────────────────┘                       │
│  (never two concurrent ATX runs on the same repo)     │
└─────────────────────┬───────────────────────────────┘
                      │  (wait for all to complete)
                      ▼
┌─────────────────────────────────────────────────────┐
│  6.5 RECONCILIATION GATE (mandatory)                  │
│  See steering/reconciliation-gate.md for full contract│
│                                                       │
│  A. Branch consolidation                              │
│  B. Filename / path standardization                   │
│  C. Four-artifact bundle completeness                 │
│  ABORT before any portfolio TD if any check fails.    │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────┐
│  7. Generate         │  Portfolio ARA / MOD / BAO configs
│     portfolio        │  Each receives structured service_inventory[]
│     configs          │  and dependency_overrides[]
└─────────┬───────────┘
          │
          ▼
┌─────────────────────────────────────────────────────┐
│  8. Portfolio TDs — STRICTLY SEQUENTIAL              │
│                                                       │
│  Portfolio ARA TD                                     │
│         ▼  (Reconciliation Gate)                      │
│  Portfolio MOD TD                                     │
│         ▼  (Reconciliation Gate)                      │
│  Portfolio BAO TD (when applicable)                   │
│         ▼  (Reconciliation Gate)                      │
│  Bridge TD (full + portfolio_bridge configured)       │
│                                                       │
│  Abort the chain if any gate fails.                   │
└─────────┬───────────────────────────────────────────┘
          │
          ▼
┌─────────────────────┐
│  9. Consolidate      │  ARA → agentic-readiness-assessment/
│     reports          │  MOD → modernization-assessment/
│                      │  BAO → bpmn-opportunity-assessment/
│                      │  Bridge → portfolio root
│                      │  Clean up temp .atx-config-*.yaml files
└─────────────────────┘
```

---

## Step 0: Pre-flight Checks

See `steering/getting-started.md` for the full pre-flight sequence (AWS credentials, ATX CLI, TD existence, repo cloning).

---

## Step 1: Run Individual Assessments

Kiro spawns **one subagent per repository**. The subagent count equals the repository count — never scales with TD count.

For each repository, Kiro:

1. Classifies `repo_type` (or uses config override) — see `steering/portfolio-config.md` for the decision tree
2. Generates the temporary ATX configuration files for each TD that will run on this repo
3. Spawns one subagent that runs all assigned TDs sequentially in this fixed order:

| `assessment_type` | TDs the subagent runs | Order |
|---|---|---|
| `agentic-readiness` | ARA only | (single TD) |
| `modernization` | MOD only | (single TD) |
| `bpmn-opportunity` | BAO only (skip if no `.bpmn` files) | (single TD) |
| `full` | ARA, MOD, and BAO (last only when `.bpmn` files present) | ARA → MOD → BAO |

> **Why sequential within a repo (Per-Repo Serialization Rule):** ATX creates a per-execution staging branch (`atx-result-staging-<timestamp>-<id>`) by stashing+committing local changes onto the staging branch and then restoring the original branch. Two ATX executions launched concurrently against the same repo path each create their own staging branch from the same starting HEAD. They diverge silently because neither sees the other's commits. The orchestrator then sees partial outputs at unexpected paths (e.g., `monolith/services/monolith/...`), missing JSON/HTML companions, and merge conflicts. Serializing eliminates the race entirely. Across different repos there is no shared HEAD, so cross-repo parallelism remains safe.

### Generated ATX Configuration Files

#### ARA config (`.atx-config-{slug}-ara.yaml`)

```yaml
additionalPlanContext: |
  repo_type: "application"
  service_archetype: "orchestrator"      # if set in config or auto-detected
  agent_scope: "write-enabled"           # from per-repo config, falling back to portfolio-level
  context: "Monolithic checkout handling payments and orders"
  priority: "P0"
  tags: ["backend", "payment", "critical-path"]
```

**ARA generation rules:**
1. `repo_type` from classification (auto-detected or config override)
2. `service_archetype` from per-repo config if present; otherwise omit (the ARA TD auto-detects)
3. `agent_scope` from per-repo config if present; otherwise from portfolio-level; default `read-only`
4. `context`, `priority`, `tags` from per-repo config (omit if absent)
5. **Never include `preferences`** — ARA configs do not contain preferences

#### MOD config (`.atx-config-{slug}-mod.yaml`)

```yaml
additionalPlanContext: |
  repo_type: "application"
  context: "Monolithic checkout handling payments and orders"
  preferences:
    prefer: ["eks", "aurora", "bedrock", "dynamodb"]
    avoid: ["self-managed-kafka", "serverless"]
  priority: "P0"
  tags: ["backend", "payment", "critical-path"]
```

**MOD generation rules:**
1. `repo_type` from classification (same value as ARA — classified once per repo)
2. `context`, `priority`, `tags` from per-repo config
3. Merge preferences: start with global `preferences`, append per-repo `preferences`. If a value appears in both global `prefer` and per-repo `avoid`, remove it from `prefer`. See `steering/portfolio-config.md` for full merge rules.
4. **Never include `agent_scope`** — MOD configs do not contain agent_scope

#### BAO config (`.atx-config-{slug}-bao.yaml`) — bpmn-opportunity only

```yaml
additionalPlanContext: |
  analysis_report_path: "<repo_path>/bpmn-analysis.json"
  context: "<from portfolio config>"
  daily_volume: 200
  priority: "<from repo config>"
  downstream_dependency_reports:
    - name: "credit-scoring-service"
      ara_report_path: "<dep_path>/agentic-readiness-assessment/<dep_name>-ara-report.md"
    - name: "customer-db"
      ara_report_path: "<dep_path>/agentic-readiness-assessment/<dep_name>-ara-report.md"
```

For BAO, the orchestrator first runs the deterministic BPMN analyzer to produce `bpmn-analysis.json`, then optionally runs ARA on each `downstream_dependencies[]` entry to produce dependency ARA reports the BAO TD cross-references.

### Per-Repo Subagent Contract

Each per-repo subagent runs the assessment transformations assigned to its repo. **Across different repos, subagents execute fully in parallel. Within a single repo, the subagent runs its TDs sequentially (never two ATX sessions on the same repo concurrently).**

**Single-TD repo (assessment_type ∈ {agentic-readiness, modernization, bpmn-opportunity}):**

```bash
atx custom def exec -n <td_name> -p <repo-path> -g file://.atx-config-<slug>-<suffix>.yaml -x -t
```

**Multi-TD repo (assessment_type == full):** The subagent runs each ATX command in sequence on its repo, waiting for each to fully complete (artifact present on disk) before launching the next:

```bash
# Step 1 — ARA on this repo (run, wait for *-ara-report.md to exist)
atx custom def exec -n <agentic_readiness> -p <repo-path> -g file://.atx-config-<slug>-ara.yaml -x -t

# Step 2 — MOD on the same repo (only after ARA artifact is on disk)
atx custom def exec -n <modernization> -p <repo-path> -g file://.atx-config-<slug>-mod.yaml -x -t

# Step 3 — BAO on the same repo (only if `.bpmn` files present, only after MOD artifact is on disk)
atx custom def exec -n <bpmn_opportunity> -p <repo-path> -g file://.atx-config-<slug>-bao.yaml -x -t
```

> **🌿 Per-Portfolio Branch Isolation (recommended).** For repos under your direct control, create a dedicated branch per portfolio run BEFORE invoking the orchestrator (e.g., `git checkout -b portfolio-assessment-<date>`). All ATX staging branches will fork from this branch. At the end you have a single isolated branch you can merge or delete as a unit. The orchestrator does not create this branch automatically — it is the operator's responsibility.

### Per-repo report locations

| TD | Output path (relative to repo root) |
|---|---|
| ARA | `{repo}/agentic-readiness-assessment/{slug}-ara-report.{md,json,html,metadata.json}` |
| MOD | `{repo}/modernization-assessment/{slug}-mod-report.{md,json,html,metadata.json}` |
| BAO | `{repo}/bpmn-opportunity-assessment/{slug}-bpmn-opportunity-report.{md,json,html,metadata.json}` |

`slug = lowercase(repo.name)` with any character not in `[a-z0-9_-]` replaced by `-`. Always derived from the portfolio config — never from the filesystem basename.

---

## Step 1.5: Reconciliation Gate

**Mandatory before any portfolio TD launches.** See `steering/reconciliation-gate.md` for the full Checks A / B / C contract.

The gate runs:
- Once after all per-repo subagents return (before Portfolio ARA)
- Once before each subsequent portfolio TD invocation

If any check fails, abort with an actionable error. **Do not invoke a portfolio TD on partial inputs** — partial portfolio reports look authoritative but exclude entire services silently.

---

## Step 2: Run Portfolio Assessments

After Step 1.5 reconciliation passes, generate portfolio-level ATX configs and run portfolio TDs.

### Portfolio ARA config (`.atx-config-portfolio-ara.yaml`)

```yaml
additionalPlanContext: |
  context: "Building customer-facing AI agents for support and order management"
  portfolio_name: "ecommerce-platform"
  service_inventory:
    - name: "storefront-web"
      path: "./services/storefront-web"
      priority: "P0"
      repo_type: "application"
      agent_scope: "write-enabled"
      tags: ["frontend", "customer-facing"]
    - name: "checkout-service"
      path: "./services/checkout-service"
      priority: "P0"
      repo_type: "application"
      agent_scope: "write-enabled"
      tags: ["backend", "payment"]
    - name: "infra-repo"
      path: "./infrastructure"
      priority: "P2"
      repo_type: "infrastructure-only"
      agent_scope: "read-only"
  dependency_overrides:
    - source: "storefront-web"
      target: "checkout-service"
      type: "sync"
      description: "Storefront calls Checkout REST API for order placement"
```

**Portfolio ARA generation rules:**
1. `context` from portfolio config (if present)
2. Build `service_inventory[]` from all repositories: `name`, `priority`, `path`, `tags`, `repo_type`, `agent_scope`
3. Include `dependency_overrides[]` verbatim from portfolio config
4. **Never include `preferences`**

### Portfolio MOD config (`.atx-config-portfolio-mod.yaml`)

```yaml
additionalPlanContext: |
  context: "Building customer-facing AI agents for support and order management"
  preferences:
    prefer: ["eks", "aurora", "bedrock"]
    avoid: ["self-managed-kafka"]
  portfolio_name: "ecommerce-platform"
  service_inventory:
    - name: "storefront-web"
      path: "./services/storefront-web"
      priority: "P0"
      repo_type: "application"
      service_archetype: "stateful-crud"
      tags: ["frontend", "customer-facing"]
    - name: "checkout-service"
      path: "./services/checkout-service"
      priority: "P0"
      repo_type: "application"
      service_archetype: "orchestrator"
      tags: ["backend", "payment"]
  dependency_overrides:
    - source: "storefront-web"
      target: "checkout-service"
      type: "sync"
      description: "Storefront calls Checkout REST API for order placement"
```

**Portfolio MOD generation rules:**
1. `context` from portfolio config (if present)
2. `preferences` from global portfolio-level only — NOT merged with per-repo preferences
3. Build `service_inventory[]` with `service_archetype` (when applicable for application repos)
4. Include `dependency_overrides[]` verbatim
5. **Never include `agent_scope`**

> **CRITICAL:** `service_inventory[]` and `dependency_overrides[]` MUST be emitted as structured YAML object arrays — NOT as free-text bullet lists. The Portfolio ARA/MOD TDs parse these fields programmatically. A bullet-list string silently degrades every feature keyed off structured inventory data.

### Portfolio BAO config (`.atx-config-portfolio-bao.yaml`)

When `assessment_type` is `bpmn-opportunity` or `full` AND at least one repo produced a BAO report:

```yaml
additionalPlanContext: |
  context: "Identifying agentic opportunities in loan origination workflows"
  portfolio_name: "loan-platform"
  service_inventory:
    - name: "loan-origination-process"
      path: "./processes/loan-origination"
      priority: "P0"
      tags: ["camunda", "loan"]
```

If `portfolio_bpmn_opportunity` is not configured in `transformation_definitions`, skip the portfolio BAO step and log a warning. The Bridge TD's BAO+ARA Readiness Matrix only generates when `portfolio_bao_report_path` is passed in.

### Portfolio TD Execution Order — STRICTLY SEQUENTIAL

> All portfolio TDs run with `-p .` on the workspace root. They share a single git HEAD. Running two concurrently triggers staging-branch divergence. **The orchestrator MUST run portfolio TDs strictly serially with a Reconciliation Gate between each invocation:**

```bash
# 1. Portfolio ARA
atx custom def exec -n <portfolio_agentic_readiness> -p . -g file://.atx-config-portfolio-ara.yaml -x -t

# (Reconciliation Gate: Checks A, B, C on the just-emitted portfolio ARA bundle)

# 2. Portfolio MOD
atx custom def exec -n <portfolio_modernization> -p . -g file://.atx-config-portfolio-mod.yaml -x -t

# (Reconciliation Gate)

# 3. Portfolio BAO (when applicable)
atx custom def exec -n <portfolio_bpmn_opportunity> -p . -g file://.atx-config-portfolio-bao.yaml -x -t

# (Reconciliation Gate)

# 4. Bridge TD (full + portfolio_bridge configured)
atx custom def exec -n <portfolio_bridge> -p . -g file://.atx-config-bridge.yaml -x -t
```

The Reconciliation Gate between portfolio TDs runs Checks A and B (branch consolidation, canonical-path verification) plus Check C (four-artifact bundle completeness). If any portfolio TD fails the gate, abort the chain — do not proceed to the next portfolio TD.

### Portfolio Report Locations

| TD | Output path |
|---|---|
| Portfolio ARA | `agentic-readiness-assessment/{portfolio-name}-portfolio-ara-report.{md,json,html,metadata.json}` |
| Portfolio MOD | `modernization-assessment/{portfolio-name}-portfolio-mod-report.{md,json,html,metadata.json}` |
| Portfolio BAO | `bpmn-opportunity-assessment/{portfolio-name}-portfolio-bao-report.{md,json,html,metadata.json}` |
| Bridge | `{portfolio-name}-bridge-report.{md,json,html,metadata.json}` (workspace root) |

---

## Step 2.5: Bridge TD (Full Assessment Only)

When `assessment_type: full` and `portfolio_bridge` is configured, the Bridge TD runs after all portfolio TDs complete and cross-references their reports.

### Bridge config (`.atx-config-bridge.yaml`)

```yaml
additionalPlanContext: |
  portfolio_ara_report_path: "agentic-readiness-assessment/ecommerce-platform-portfolio-ara-report.md"
  portfolio_mod_report_path: "modernization-assessment/ecommerce-platform-portfolio-mod-report.md"
  portfolio_name: "ecommerce-platform"
  portfolio_bao_report_path: "bpmn-opportunity-assessment/ecommerce-platform-portfolio-bao-report.md"
```

**Bridge generation rules:**
1. `portfolio_ara_report_path` → `agentic-readiness-assessment/{portfolio_name}-portfolio-ara-report.md`
2. `portfolio_mod_report_path` → `modernization-assessment/{portfolio_name}-portfolio-mod-report.md`
3. `portfolio_name` from portfolio config
4. If a portfolio BAO report exists at `bpmn-opportunity-assessment/{portfolio_name}-portfolio-bao-report.md`, set `portfolio_bao_report_path` to that path. Otherwise omit.
5. **Do NOT** use the deprecated `bpmn_opportunity_report_paths[]` field — Bridge consumes a single aggregated portfolio BAO report.

### When the Bridge Step Is Skipped

- `assessment_type` is not `full` → bridge not applicable
- `portfolio_bridge` not configured → skip with warning: `"portfolio_bridge not configured — bridge report will not be generated"`

### Failure Isolation

If the Bridge TD fails:
1. Log the failure with the error message
2. Report to the user: `"Bridge TD failed: {error}. The ARA and MOD portfolio reports are unaffected."`
3. The completed ARA and MOD portfolio reports are NOT affected
4. The overall assessment is considered successful — the bridge is supplementary

If one of the upstream portfolio TDs failed (so only one portfolio report exists), Bridge will detect the missing report and terminate with a clear error identifying which is missing. This is expected behavior.

---

## Step 3: Consolidate Reports

After all portfolio TDs (and bridge, if applicable) complete, consolidate reports into organized directories at the portfolio root.

For each `assessment_type`:

| `assessment_type` | Consolidation actions |
|---|---|
| `agentic-readiness` | Create/use `agentic-readiness-assessment/` at portfolio root. Copy each per-repo ARA report from `{repo}/agentic-readiness-assessment/` into the root folder. Portfolio ARA report already lives there. |
| `modernization` | Same pattern with `modernization-assessment/` |
| `bpmn-opportunity` | Same pattern with `bpmn-opportunity-assessment/` |
| `full` | All three folders + bridge report at portfolio root |

After all consolidation:
- Clean up temporary `.atx-config-*.yaml` files
- Clean up `bpmn-analysis.json` files (BAO mode only)

### Resulting Structure (full mode)

```
agentic-readiness-assessment/
├── service-a-ara-report.{md,json,html,metadata.json}
├── service-b-ara-report.{md,json,html,metadata.json}
├── service-c-ara-report.{md,json,html,metadata.json}
└── my-platform-portfolio-ara-report.{md,json,html,metadata.json}

modernization-assessment/
├── service-a-mod-report.{md,json,html,metadata.json}
├── service-b-mod-report.{md,json,html,metadata.json}
├── service-c-mod-report.{md,json,html,metadata.json}
└── my-platform-portfolio-mod-report.{md,json,html,metadata.json}

bpmn-opportunity-assessment/                                                  ← only when BAO ran
├── process-a-bpmn-opportunity-report.{md,json,html,metadata.json}
└── my-platform-portfolio-bao-report.{md,json,html,metadata.json}

my-platform-bridge-report.{md,json,html,metadata.json}                        ← full + portfolio_bridge
```

---

## Step 4: Review Reports

Reports are generated by the TDs — their content is defined by the TD specifications, not the orchestrator.

| Report | What it contains |
|---|---|
| ARA Portfolio | Readiness distribution, cross-cutting blockers/risks, service-by-service summary |
| MOD Portfolio | Score overview, cross-cutting concerns, dependency-aware roadmap, pathway aggregation, service-by-service summary |
| BAO Portfolio | Aggregated agentic opportunities, complexity distribution, cross-process patterns |
| Bridge | Shared remediation mapping, agentic readiness delta, MOD readiness gate, unified remediation sequence |

---

## Artifact Format

Every per-repo and portfolio assessment emits a four-file bundle:

| Artifact | Purpose |
|---|---|
| `{name}-report.md` | Richest-prose narrative artifact — rubric quotes, BLOCKER remediation blocks, score tables, top gaps, decomposition strategy, pathway details, execution roadmap, risk register |
| `{name}-report.json` | **Canonical machine-readable contract.** Consumed by the webapp and by portfolio TDs. JSON wins on any conflict. |
| `{name}-report.html` | Single self-contained HTML file. No external asset fetches at render time. Every data value originates from the JSON. |
| `{name}-report.metadata.json` | Tiny sidecar carrying `{assessment_type, assessment_date, td_version}`. Same fields are also at the root of the main JSON under `metadata`. |

The `.md` presence check is the authoritative success signal in the No-Polling Contract — all four artifacts are produced together or none are.
