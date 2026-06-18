# CT Workflow

The end-to-end workflow for running analyses using AWS Transform Continuous Modernization. Read this when actually executing analyses, managing findings, or generating reports.

---

## High-Level Flow

```
┌─────────────────────┐
│  0. Pre-flight      │  aws sts get-caller-identity + atx ct status --health
│                     │  FAIL FAST if anything missing
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  1. Add source      │  atx ct source add --provider <provider> ...
│                     │  Local: --path    Remote: --org + --token
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  2. Discover repos  │  atx ct discovery scan --source <name>
│                     │  Verify: atx ct repository list
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  3. Run ARA         │  atx ct analysis run --type agentic-readiness
│                     │  --source <name>  (poll until complete)
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  4. Run MODA        │  atx ct analysis run --type modernization-readiness
│                     │  --source <name>  (poll until complete)
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  5. Inspect         │  atx ct findings list --json
│     findings        │  Filter by severity, type, repo, source
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  6. Retrieve        │  atx ct analysis list-artifacts --id <id>
│     artifacts       │  atx ct analysis get-artifact --id <id> --repo <slug> --name ara
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  7. (Optional)      │  atx custom def exec -n portfolio-execution-plan-generation
│     Execution Plan  │  Requires report artifacts from steps 3-4
└─────────────────────┘
```

---

## Step 1: Add Source

Choose the appropriate provider.

**Local repos (always use absolute paths — relative paths may not resolve correctly):**
```bash
atx ct source add --name my-portfolio --provider local --path /absolute/path/to/services
```

**GitHub org:**
```bash
atx ct source add --name my-portfolio --provider github --org my-org --token ghp_xxx
```

**GitLab group:**
```bash
atx ct source add --name my-portfolio --provider gitlab --org my-group --token glpat-xxx [--url https://gitlab.example.com]
```

**Bitbucket workspace:**
```bash
atx ct source add --name my-portfolio --provider bitbucket --org my-workspace --token xxx [--username user] [--email e@x.com]
```

Verify:
```bash
atx ct source list
```

---

## Step 2: Discover Repositories

```bash
atx ct discovery scan --source my-portfolio
```

For local sources, you can override the path at scan time:
```bash
atx ct discovery scan --source my-portfolio --path /different/path
```

Verify discovered repos:
```bash
atx ct repository list
atx ct repository list --source my-portfolio --json
```

### Repository Management

After discovery, you can:
- **Filter by language:** `atx ct repository list --language java`
- **Filter by labels:** `atx ct repository list --labels team:platform,priority:P0`
- **Label repos** for filtering: `atx ct repository update --id <id> --labels team:platform,priority:P0`
- **Delete irrelevant repos**: `atx ct repository delete --repo <slug> --source <name>`

### Repo Slugs

Each discovered repo gets a slug in the format `<source>::<repo-name>`. This slug is used in:
- `--repo` filters on analysis commands
- `findings list --repo` filters
- `analysis get-artifact --repo` to retrieve per-repo artifacts

---

## Step 3: Run ARA Analysis

### Recommended: Launch + Poll (agent workflows)

```bash
# Launch without --wait (returns immediately with analysis ID)
atx ct analysis run --type agentic-readiness --source my-portfolio
# → "Analysis 01KV... (agentic-readiness) started on N repo(s)"

# Tell the user: "Running ARA — this takes 5-15 minutes per repo. I'll check back."

# Poll every 30-60 seconds
atx ct analysis get --id <analysis-id>
# → Status: running | complete | failed

# On complete — summarize for the user
atx ct findings list --analysis-id <id> --json
```

### Alternative: Blocking wait (scripts/CI)

```bash
atx ct analysis run --type agentic-readiness --source my-portfolio --wait
```

The `--wait` flag blocks until the analysis completes (or fails). Suitable for scripts but NOT recommended for agent workflows — it holds the execution slot for 5–30 minutes with no intermediate feedback.

### Targeting specific repos

```bash
atx ct analysis run --type agentic-readiness --repo my-portfolio::my-app --source my-portfolio
```

### What happens internally

1. ct queues analysis jobs for each discovered repo
2. Per-repo analyses run in parallel (ct manages concurrency)
3. Portfolio-level aggregation runs after all per-repo analyses complete
4. Report artifacts are stored in the ct artifact store
5. Findings are generated and stored in the ct findings database

### Verify success

```bash
atx ct analysis list --json  # Status should show 'complete'
```

---

## Step 4: Run MODA Analysis

### Recommended: Launch + Poll (agent workflows)

```bash
# Launch without --wait
atx ct analysis run --type modernization-readiness --source my-portfolio
# → "Analysis 01KW... (modernization-readiness) started on N repo(s)"

# Tell the user: "Running MODA — this takes 5-15 minutes per repo. I'll check back."

# Poll every 30-60 seconds
atx ct analysis get --id <analysis-id>

# On complete — summarize for the user
atx ct findings list --analysis-id <id> --json
```

### Alternative: Blocking wait (scripts/CI)

```bash
atx ct analysis run --type modernization-readiness --source my-portfolio --wait
```

### Running both (full analysis)

Launch both sequentially, polling each:
```bash
atx ct analysis run --type agentic-readiness --source my-portfolio
# Poll until complete...
atx ct analysis run --type modernization-readiness --source my-portfolio
# Poll until complete...
```

Do NOT run both simultaneously — ct handles internal parallelism, but launching two analysis types concurrently on the same source can cause resource contention.

---

## Step 5: Inspect Findings

### List all findings (JSON)

```bash
atx ct findings list --json
```

### Filter findings

```bash
# By severity (exact match)
atx ct findings list --severity high

# By minimum severity threshold
atx ct findings list --min-severity medium

# By analysis type
atx ct findings list --type agentic-readiness

# By source
atx ct findings list --source my-portfolio

# By repo
atx ct findings list --repo my-portfolio::my-app

# By status
atx ct findings list --status open

# By analysis run
atx ct findings list --analysis-id <id>

# By fix-transform (auto-fixable findings)
atx ct findings list --fix-transform <td-name>

# Combined
atx ct findings list --source my-portfolio --type agentic-readiness --min-severity medium --json
```

### Finding Structure

Each finding includes:
- **severity**: high, medium, or low
- **status**: open, dismissed, or obsolete
- **type**: the analysis type that produced it
- **repository**: which repo it applies to (as slug)
- **fix-transform**: the TD that can remediate it (if auto-fixable)

### Manage findings

```bash
# Dismiss a false positive
atx ct findings update --id <id> --status dismissed --reason "Not applicable to our use case"

# Add notes
atx ct findings update --id <id> --notes "Tracked in JIRA-1234"

# Batch dismiss
atx ct findings batch-update --ids id1,id2,id3 --status dismissed --reason "..."

# Delete dismissed/obsolete
atx ct findings delete --id <id>
```

---

## Step 6: Retrieve Report Artifacts

Report artifacts are stored in the ct server's artifact store, NOT on the local filesystem.

### List artifacts for an analysis

```bash
atx ct analysis list-artifacts --id <analysis-id> --json
```

### Get specific artifact content

```bash
# Per-repo ARA report
atx ct analysis get-artifact --id <analysis-id> --repo <source>::<repo-name> --name ara

# Per-repo MODA report
atx ct analysis get-artifact --id <analysis-id> --repo <source>::<repo-name> --name mod

# Portfolio-level ARA report
atx ct analysis get-artifact --id <analysis-id> --repo _portfolio_ara --name report

# Portfolio-level MODA report
atx ct analysis get-artifact --id <analysis-id> --repo _portfolio_mod --name report

# Save to file
atx ct analysis get-artifact --id <analysis-id> --repo <slug> --name ara > ./report.md
```

### Artifact names by analysis type

| Analysis type | Per-repo artifact name | Portfolio artifact repo key | Portfolio artifact name |
|---|---|---|---|
| `agentic-readiness` | `ara` | `_portfolio_ara` | `report` |
| `modernization-readiness` | `mod` | `_portfolio_mod` | `report` |
| `tech-debt-*` | `technical-debt-report/summary` | — | — |

Use `list-artifacts --json` to discover available names for any given analysis.

---

## Custom Analysis Type

For running custom TDs as analyses (not ARA/MODA built-ins):

```bash
atx ct analysis run --type custom --transformation-name my-custom-td --source my-portfolio --wait
```

Custom analyses support the `-g`/`--configuration` flag:

```bash
atx ct analysis run --type custom --transformation-name my-custom-td \
  --source my-portfolio \
  -g "additionalPlanContext=Target Java 17,buildCommand=mvn clean test" \
  --wait
```

Or with a config file:
```bash
atx ct analysis run --type custom --transformation-name my-custom-td \
  --source my-portfolio \
  -g file://my-config.yaml \
  --wait
```

---

## Remediation (Optional)

After identifying findings, you can auto-remediate:

```bash
# Create remediation from specific findings
atx ct remediation create --ids finding-id-1,finding-id-2 --name "fix-tech-debt-batch-1"

# Create remediation with a specific TD
atx ct remediation create --repo my-portfolio::my-app --source my-portfolio \
  --transformation-name my-fix-td --name "upgrade-java" --local

# Check status (includes PR/MR links)
atx ct remediation status --id <remediation-id>

# Retry failures
atx ct remediation retry --id <remediation-id>
```

Remediation creates branches and PRs/MRs depending on source provider:
- GitHub → Pull Request
- GitLab → Merge Request
- Bitbucket → Pull Request
- Local → local branch (no PR)

---

## Telemetry

Pass telemetry metadata to track analysis runs:

```bash
atx ct analysis run --type agentic-readiness --source my-portfolio \
  --telemetry "agent=kiro,executionMode=local" --wait
```

`client=zerodebt` is always included automatically.
