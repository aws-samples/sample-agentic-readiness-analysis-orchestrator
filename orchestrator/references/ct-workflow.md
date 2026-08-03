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
│  6. Retrieve        │  atx ct analysis get --id <id> --json  → .report_paths
│     artifacts       │  AND ls services/<repo>/*-analysis/  (working tree)
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  7. (Optional)      │  atx custom def exec -n eba-execution-plan-generator
│     Execution Plan  │  Requires report artifacts from steps 3-4
└─────────────────────┘
```

There is no step for starting a server: `atx ct` analyses run **in-process**. `atx ct server` is hidden and deprecated, and starts a daemon on `:8081` that blocks the shell — never invoke it. Pre-flight with `atx ct status --health`.

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
- the keys of `report_paths` in `analysis get --json` (see Step 6)

---

## Step 3: Run ARA Analysis

### Recommended: Launch + Poll (agent workflows)

```bash
# Launch without --wait (returns immediately with analysis ID)
atx ct analysis run --type agentic-readiness --source my-portfolio
# → "Analysis 01KV... (agentic-readiness) started on N repo(s)"

# Tell the user: "Running ARA — this takes 5-15 minutes per repo. I'll check back."

# Poll every 30-60 seconds
atx ct analysis get --id <analysis-id> --json | jq -r .status
# → running | complete | failed

# On complete — summarize for the user
atx ct findings list --analysis-id <id> --json
```

> Poll `status` and nothing else. While a run is in flight, `repos_done` and `repos_total` read `null` — they are not a progress bar and an agent that watches them will conclude the run never started.

### Alternative: Blocking wait (scripts/CI)

```bash
atx ct analysis run --type agentic-readiness --source my-portfolio --wait
```

`--wait` does exist on `analysis run` (and on `remediation create` / `remediation retry`), though it is hidden from `--help`. It blocks until the analysis completes (or fails). Suitable for scripts but NOT recommended for agent workflows — it holds the execution slot for 5–30 minutes with no intermediate feedback.

### Targeting specific repos

```bash
atx ct analysis run --type agentic-readiness --repo my-portfolio::my-app --source my-portfolio
```

### What happens internally

1. ct queues analysis jobs for each discovered repo
2. Per-repo analyses run **concurrently** — verified on 3.9.0, an 11-repo ARA had 8 repos in flight within ~2 minutes. Wall-clock is therefore roughly the slowest repo plus the portfolio phase, not the sum of the repos.
3. Portfolio-level aggregation runs automatically as a **second phase of the same `analysis run`** once the per-repo reports land — you do not launch it separately. Each portfolio TD needs **≥ 2 discovered reports**: a single-repo run produces no portfolio report and logs `runPortfolioAra: no portfolio ARA report found for <name>`. Aggregation is per-run, so separate single-repo runs do **not** accumulate into a portfolio — scan the whole portfolio in one run.
4. Report artifacts are recorded in `report_paths` and written into the repo working trees (see Step 6)
5. Findings are generated and stored in the ct findings database
6. For local sources, ct **auto-commits** the report bundle into the repo's working tree as `ATX Bot <checkpoint@atx.bot>`. Expect unexpected commits on the branch you had checked out.

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

# Poll every 30-60 seconds (status only — repos_done/repos_total are null mid-run)
atx ct analysis get --id <analysis-id> --json | jq -r .status

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

Reports land as **files on the local filesystem**. There is no artifact-fetch subcommand — `analysis list-artifacts` and `analysis get-artifact` were removed (they now fail with `error: unknown command`). Discover report locations from the analysis record instead.

### List report paths for an analysis

```bash
atx ct analysis get --id <id> --json | jq -r '.report_paths | to_entries[] | "\(.key)\t\(.value.ara // .value.mod)"'
```

Keys are repo slugs (plus the portfolio entries); values are paths you read directly with `cat`/`Read`.

### `report_paths` is markdown-only — three trees, different contents

**Verified on 3.9.0.** File counts from one 11-repo ARA run:

| Location | md | json | html | meta |
|---|---|---|---|---|
| `~/.atxct/shared/analyses/<id>/artifacts/` — **where `report_paths` points** | 12 | 1 | 0 | 0 |
| `~/.atxct/sources/<src>/<type>/runs/<id>/` — **the complete copy** | 12 | 13 | 1 | 1 |
| `services/<repo>/*-analysis/` in the working tree (local sources) | ✓ | ✓ | ✓ | ✓ |

Use `report_paths` to enumerate which repos reported. To read a `.json` or open an `.html`, go to the `sources/` run tree:

```bash
# every artifact of a run
find ~/.atxct/sources -path "*runs/<id>/*" -type f
# portfolio bundle — html and portfolio json exist HERE AND NOWHERE ELSE
ls ~/.atxct/sources/*/*/runs/<id>/portfolio-*/*-analysis/
```

Two path traps: `<type>` is the **source's** analysis root, not the run's type (a MOD run lands under `sources/<src>/agentic-readiness/runs/<id>/`), and per-repo dirs there are slug-mangled `<source>-<repo>-<16hex>` rather than `<source>__<repo>`. Glob; don't construct. `portfolio_summary.report_path` also points into this tree.

Working trees carry only **per-repo** bundles — never portfolio output, since no repo owns it. So a missing portfolio `.html`/`.json` is nearly always a wrong-directory error, not a failed render.

Note that ct **auto-commits** the per-repo bundles into local-source repo working trees, authored as `ATX Bot <checkpoint@atx.bot>`.

### Report kinds by analysis type

| Analysis type | Per-repo report key | Working-tree directory |
|---|---|---|
| `agentic-readiness` | `ara` | `services/<repo>/agentic-readiness-analysis/` |
| `modernization-readiness` | `mod` | `services/<repo>/modernization-readiness-analysis/` |
| `tech-debt-*` | `technical-debt-report/summary` | — |

Portfolio reports appear as their own `report_paths` entries once the portfolio phase runs (which requires ≥ 2 repos in the run — see Step 3). That entry is the `.md`; the portfolio `.json`, `.html`, and `.metadata.json` are only in `~/.atxct/sources/<src>/<type>/runs/<id>/portfolio-<name>/`.

---

## Custom Analysis Type

For running custom TDs as analyses (not ARA/MODA built-ins):

```bash
atx ct analysis run --type custom --transformation-name my-custom-td --source my-portfolio
# then poll: atx ct analysis get --id <analysis-id> --json | jq -r .status
```

The `--wait` in the snippets below is the scripted/CI form; from an agent, launch without it and poll `status` as in Step 3.

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

There are two remediation modes. **Which one applies depends on whether findings carry a fix transform — and ARA/MODA findings currently do NOT.**

```bash
# (a) Finding-bound — ct maps each finding to its own fix-transform
atx ct remediation create --ids finding-id-1,finding-id-2 --name "fix-batch-1"

# (b) Explicit-transform — run a chosen TD across a repo (findings just motivate it)
atx ct remediation create --repo my-portfolio::my-app --source my-portfolio \
  --transformation-name my-fix-td --name "containerize" [--local]

# Check status (includes PR/MR links)
atx ct remediation status --id <remediation-id>

# Retry failures
atx ct remediation retry --id <remediation-id>
```

> **Verified 2026-08 on 3.9.0: ARA and MODA findings are assessment-only.** Every finding has `fix: null` and no `fix-transform` field — so mode (a) has nothing to bind to, and `remediation create --ids` rejects the whole batch, reporting them as `non_remediable`. To auto-remediate an assessment finding (e.g. "not containerized"), author your own TD and use mode (b) `--transformation-name`. See **"Authoring a custom remediation TD"** in `SKILL.md`. Mode (a) is for analysis types whose findings ship a bound fix transform (e.g. certain tech-debt/upgrade transforms).

`--local` runs the ATX transform in-process against the checked-out working tree rather than delegating to the provider; useful for local sources. `-g/--configuration` is valid only alongside `--transformation-name`. `remediation create` and `remediation retry` also accept the hidden `--wait`; prefer polling `remediation status --id <id>` in agent workflows.

Remediation creates branches and PRs/MRs depending on source provider:
- GitHub → Pull Request
- GitLab → Merge Request
- Bitbucket → Pull Request
- Local → local branch (no PR)

This PR-opening happens **server-side** and is independent of any local `git push` (relevant on Amazon-managed machines where Code Defender blocks pushes to unapproved public repos).

## Teardown / fresh environment (reverse-order deletion)

Resetting the account for a clean demo requires deleting in **reverse dependency order** — verified 2026-07:

```bash
# 1. Delete analyses (optionally cascade their findings)
for id in $(atx ct analysis list --json | jq -r '.[].id'); do
  atx ct analysis delete --id "$id" --cascade-findings
done

# 2. Delete repositories UNDER each source (sources can't be removed while repos reference them → HTTP 409)
atx ct repository list --json | jq -r '.items[] | "\(.slug)\t\(.source)"' | while IFS=$'\t' read slug src; do
  atx ct repository delete --repo "$slug" --source "$src"
done

# 3. Purge residual findings — must be dismissed/obsolete before delete (no batch delete)
open=$(atx ct findings list --status open --json | jq -r '.[].id' | paste -sd, -)
[ -n "$open" ] && atx ct findings batch-update --ids "$open" --status dismissed --reason "env reset"
for id in $(atx ct findings list --json | jq -r '.[].id'); do atx ct findings delete --id "$id"; done

# 4. NOW remove sources (field is .source, not .name)
for name in $(atx ct source list --json | jq -r '.[].source'); do atx ct source remove --name "$name"; done

# 5. Verify — deletes exit 0 even on no-op; trust the counts, not the exit code
echo "repos=$(atx ct repository list --json | jq .total) sources=$(atx ct source list --json | jq length) analyses=$(atx ct analysis list --json | jq length) findings=$(atx ct findings list --json | jq length)"
```

Run large teardowns as a background task (per-item API calls are slow). `atx ct status` gives a quick account-wide count of sources/repos/analyses/findings/remediations.

---

## Telemetry

Pass telemetry metadata to track analysis runs:

```bash
atx ct analysis run --type agentic-readiness --source my-portfolio \
  --telemetry "agent=claude-code,executionMode=local"
```

(`--telemetry` composes with `--wait` too, but agent runs should launch and poll.)

`client=zerodebt` is always included automatically.
