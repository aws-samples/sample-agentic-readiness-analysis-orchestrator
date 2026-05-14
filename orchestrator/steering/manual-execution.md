# Manual Execution

How to run individual TDs directly via `atx custom def exec` without the Kiro orchestrator. Read this when the user wants to run a single repository's analysis, reproduce a failed run, or skip orchestration entirely.

> The Kiro orchestrator is the recommended path because it enforces the per-repo serialization rule, runs the reconciliation gate, and serializes portfolio TDs. Manual execution skips all of that — you own the safety contracts yourself.

---

## When to Use Manual Execution

- Single-repo analysis (orchestrator requires ≥2 repos)
- Reproducing a specific TD failure for debugging
- Re-running just the portfolio TD after fixing a per-repo report
- Running an analysis against a repo that isn't part of any portfolio config

---

## Per-Repo TDs

### ARA (per-repo)

```bash
cd ./services/my-service
atx custom def exec -n <your-ara-td-name> -p . -g file://atx-config-ara.yaml -x -t
```

`atx-config-ara.yaml` — ARA configs **never include `preferences`**:

```yaml
additionalPlanContext: |
  repo_type: "application"
  service_archetype: "stateful-crud"
  agent_scope: "write-enabled"
  context: "Legacy PHP e-commerce app running on EC2 with MySQL"
  priority: "P0"
  tags: ["monolith", "php"]
```

### MOD (per-repo)

```bash
cd ./services/my-service
atx custom def exec -n <your-mod-td-name> -p . -g file://atx-config-mod.yaml -x -t
```

`atx-config-mod.yaml` — MOD configs **never include `agent_scope`**:

```yaml
additionalPlanContext: |
  repo_type: "application"
  context: "Legacy PHP e-commerce app running on EC2 with MySQL"
  preferences:
    prefer: ["eks", "aurora", "bedrock", "dynamodb"]
    avoid: ["self-managed-kafka", "rds"]
  priority: "P0"
  tags: ["monolith", "php"]
```

### BAO (per-repo)

```bash
cd ./processes/loan-origination
# Step 1: Run the deterministic BPMN analyzer first
python3 <repo_root>/tools/bpmn-analyzer/run_analysis.py \
    --bpmn-dir . \
    --output ./bpmn-analysis.json

# Step 2: Run the BAO TD
atx custom def exec -n <your-bao-td-name> -p . -g file://atx-config-bao.yaml -x -t
```

`atx-config-bao.yaml`:

```yaml
additionalPlanContext: |
  analysis_report_path: "./bpmn-analysis.json"
  context: "Core loan origination BPMN workflows (Camunda C7)"
  daily_volume: 200
  priority: "P0"
  # Optional — cross-references downstream service ARA findings
  downstream_dependency_reports:
    - name: "credit-scoring-service"
      ara_report_path: "../credit-scoring/agentic-readiness-analysis/credit-scoring-ara-report.md"
```

---

## Portfolio TDs

### Portfolio ARA (after all individual ARA analyses)

```bash
atx custom def exec -n <your-portfolio-ara-td-name> -p . -g file://atx-portfolio-ara-config.yaml -x -t
```

`atx-portfolio-ara-config.yaml`:

```yaml
additionalPlanContext: |
  context: "Building customer-facing AI agents for support and order management"
  portfolio_name: "my-platform"
  service_inventory:
    - name: "service-a"
      path: "./services/service-a"
      priority: "P0"
      repo_type: "application"
      agent_scope: "write-enabled"
      tags: ["monolith", "php"]
    - name: "service-b"
      path: "./services/service-b"
      priority: "P1"
      repo_type: "application"
      agent_scope: "read-only"
      tags: ["backend", "inventory"]
  dependency_overrides:
    - source: "service-a"
      target: "service-b"
      type: "sync"
      description: "REST API calls for inventory checks"
```

### Portfolio MOD (after all individual MOD analyses)

```bash
atx custom def exec -n <your-portfolio-mod-td-name> -p . -g file://atx-portfolio-mod-config.yaml -x -t
```

`atx-portfolio-mod-config.yaml`:

```yaml
additionalPlanContext: |
  context: "Building customer-facing AI agents for support and order management"
  preferences:
    prefer: ["eks", "aurora", "bedrock"]
    avoid: ["self-managed-kafka"]
  portfolio_name: "my-platform"
  service_inventory:
    - name: "service-a"
      path: "./services/service-a"
      priority: "P0"
      repo_type: "application"
      service_archetype: "stateful-crud"
      tags: ["monolith", "php"]
    - name: "service-b"
      path: "./services/service-b"
      priority: "P1"
      repo_type: "application"
      service_archetype: "data-gateway"
      tags: ["backend", "inventory"]
  dependency_overrides:
    - source: "service-a"
      target: "service-b"
      type: "sync"
      description: "REST API calls for inventory checks"
```

> **Critical:** `service_inventory[]` and `dependency_overrides[]` MUST be structured YAML object arrays — never free-text bullet lists. Portfolio TDs parse these programmatically.

### Portfolio BAO (when applicable)

```bash
atx custom def exec -n <your-portfolio-bao-td-name> -p . -g file://atx-portfolio-bao-config.yaml -x -t
```

`atx-portfolio-bao-config.yaml`:

```yaml
additionalPlanContext: |
  context: "Identifying agentic opportunities in loan origination workflows"
  portfolio_name: "loan-platform"
  service_inventory:
    - name: "loan-origination-process"
      path: "./processes/loan-origination"
      priority: "P0"
      tags: ["camunda", "loan"]
    - name: "kyc-process"
      path: "./processes/kyc"
      priority: "P1"
      tags: ["camunda", "kyc"]
```

### Bridge TD (full analysis only)

Run after all relevant portfolio reports are generated:

```bash
atx custom def exec -n <your-bridge-td-name> -p . -g file://atx-config-bridge.yaml -x -t
```

`atx-config-bridge.yaml`:

```yaml
additionalPlanContext: |
  portfolio_ara_report_path: "agentic-readiness-analysis/my-platform-portfolio-ara-report.md"
  portfolio_mod_report_path: "modernization-readiness-analysis/my-platform-portfolio-mod-report.md"
  portfolio_name: "my-platform"
  # Optional: include if a portfolio BAO report exists
  # portfolio_bao_report_path: "bpmn-opportunity-analysis/my-platform-portfolio-bao-report.md"
```

The bridge report lands at the workspace root as `{portfolio_name}-bridge-report.md` and companion artifacts.

---

## Manual Execution Order (full analysis)

If you are running a full analysis manually from scratch, follow this order strictly:

```bash
# Per-repo phase — for EACH repo, run these in sequence on that repo:
#   1. ARA
#   2. MOD (only after ARA's .md exists)
#   3. BAO (only if .bpmn files present, only after MOD's .md exists)
# Across repos, the per-repo runs can be parallelized, BUT NEVER two TDs
# concurrently against the same repo path.

# Portfolio phase — strictly sequential, each gated by the prior's success:
atx custom def exec -n <portfolio_ara> -p . -g file://atx-portfolio-ara-config.yaml -x -t
# (verify portfolio ARA bundle complete before next step)
atx custom def exec -n <portfolio_mod> -p . -g file://atx-portfolio-mod-config.yaml -x -t
# (verify portfolio MOD bundle complete before next step)
atx custom def exec -n <portfolio_bao> -p . -g file://atx-portfolio-bao-config.yaml -x -t  # if applicable
# (verify portfolio BAO bundle complete before next step)
atx custom def exec -n <portfolio_bridge> -p . -g file://atx-config-bridge.yaml -x -t
```

> Always use `-x` (non-interactive) and `-t` (trust all tools). Each `atx custom def exec` is long-running (5–15 min per-repo, 15–30 min portfolio). Use the executeBash `timeout: 1200000` for per-repo and `timeout: 1800000` for portfolio.

---

## Branch Hygiene for Manual Runs

Before manual runs, create a portfolio-isolation branch in each affected repo:

```bash
git -C <repo_path> checkout -b portfolio-run-<date>
```

After manual runs complete, merge the ATX staging branches back:

```bash
git -C <repo_path> -P branch --list 'atx-result-staging-*'
# For each staging branch:
git -C <repo_path> merge --ff-only <staging_branch>
git -C <repo_path> branch -d <staging_branch>  # only after successful merge
```

This is the same Check A logic the orchestrator runs automatically. If you skip it, portfolio TDs will see only the working-branch view of the workspace and silently exclude staging-branch artifacts.

---

## Manual Reconciliation

If you are running portfolio TDs manually, also run the equivalent of Check B and Check C before each portfolio invocation:

**Check B (canonical paths):**
```bash
# Verify each per-repo report is at the canonical path
for repo in service-a service-b service-c; do
  ls services/$repo/agentic-readiness-analysis/$repo-ara-report.md
  ls services/$repo/modernization-readiness-analysis/$repo-mod-report.md
done
```

**Check C (four-artifact bundles):**
```bash
# For each canonical .md, verify .json, .html, .metadata.json companions
for f in $(find . -name '*-mod-report.md' -not -name '*portfolio*'); do
  base="${f%.md}"
  ls "$base.json" "$base.html" "$base.metadata.json" 2>/dev/null || echo "INCOMPLETE: $base"
done
```

If any per-repo report has `.md` but missing `.json`, re-run that per-repo TD before launching any portfolio TD.

See `steering/reconciliation-gate.md` for the full check contract.
