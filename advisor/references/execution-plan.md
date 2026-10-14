# The Execution Plan

How to generate the portfolio execution plan after the readiness analyses have produced portfolio reports. Read this when the user wants a phased, dependency-aware roadmap under real constraints.

**This is the one artifact the advisor generates rather than reads.** It builds `atx-config-exec-plan.yaml` from analysis data plus the constraints only a human can supply, then runs `eba-execution-plan-generator` as a custom definition. Everything upstream of it — findings, portfolio roll-up, dependency graph, bridge — is read, not authored.

---

## When to run it

- After at least **one** portfolio report exists (ARA and/or MOD). Feed it **both** to get cross-dimension dependency detection; with one it degrades to a single-axis plan.
- After the dependency graph, if the estate is bigger than a handful of applications. The plan's sequencing is only as good as the dependency input behind it.
- When the user explicitly asks for a roadmap, a timeline, or a phased plan.

**Do not run it just because the analyses finished.** The plan needs team size and timeline, and it cannot infer either from code. If the customer has not supplied them, the honest next step is to ask — not to generate a plan on defaults and present it as advice.

---

## Prerequisites

1. **The prerequisite analyses show status `complete`** — `atx ct analysis list`.
2. **Report artifacts exist.** `atx ct analysis get --id <id> --json` returns a populated `report_paths` and an empty `repo_errors`. `complete` alone is not sufficient; see the terminal-signal section in [`ct-operations.md`](ct-operations.md).
3. **At least one portfolio report** — which requires ≥ 2 repositories in a single `analysis run`. Portfolio reports are produced automatically as the second phase of `analysis run`; there is no separate command, separate single-repo runs do **not** accumulate, and a single-repo run producing no portfolio report is expected rather than a bug.
4. **No concurrent `atx ct analysis run`.** `ct` analyses run in-process and conflict with a custom exec on git state.

---

## Locating the inputs

Reports are on local disk, and the analysis record tells you where.

```bash
ara_id=$(atx ct analysis list --type agentic-readiness      --status complete --json | jq -r '.[0].id')
mod_id=$(atx ct analysis list --type modernization-readiness --status complete --json | jq -r '.[0].id')

atx ct analysis get --id "$ara_id" --json | jq -r '.report_paths | to_entries[] | "\(.key)\t\(.value.ara // .value.mod)"'
```

`analysis list` returns a thinner object with no `report_paths` — call `get` per id.

> **`report_paths` will not get you the JSON this definition needs.** It is **markdown-only**, pointing into `~/.atxct/shared/analyses/<id>/artifacts/`, which on an 11-repo run held 12 `.md` files and exactly one `.json`. Use `report_paths` to see *which* repositories reported, then fetch the actual files from the tree that has them.

**The portfolio JSON exists in exactly one place** — the source-scoped run tree. No working tree contains it, because no single repository owns portfolio output.

```
~/.atxct/sources/<src>/<type>/runs/<id>/
├── <source>-<repo>-<16hex>/<type>-analysis/<repo>-{ara,mod}-report.{md,json}
└── portfolio-<name>/<type>-analysis/<name>-portfolio-{ara,mod}-report.{md,json,html,metadata.json}
```

Glob rather than construct, for two reasons: `<type>` is the **source's** analysis root rather than the run's type (a modernization run can write under `.../agentic-readiness/runs/<id>/`), and per-repo directories are slug-mangled.

```bash
# The portfolio JSON for a run — html and json live here and nowhere else
ls ~/.atxct/sources/*/*/runs/"$mod_id"/portfolio-*/*-analysis/

# Every artifact of a run, immune to type and slug surprises
find ~/.atxct/sources -path "*runs/$mod_id/*" -name '*.json'
```

`portfolio_summary.report_path` on the analysis record also points into this tree if you prefer reading it to globbing.

### ⚠️ The filename trap

This definition **documents** its inputs as `{portfolio-name}-mod-portfolio-report.json` / `-ara-portfolio-report.json`, while the portfolio definitions **emit** `{portfolio_name}-portfolio-mod-report.json` / `-portfolio-ara-report.json`. The two patterns do not match. **Resolve real paths from the analysis record and pass them explicitly. Never rely on either literal.**

---

## Building the configuration

The split is the whole design: the portfolio structure comes from the analyses automatically; the **execution constraints** come from a person. An agent cannot infer team capacity, budget or a compliance date from code.

### Step 1 — Auto-populate from analysis data

```bash
atx ct repository list --source <name> --json                 # → service_inventory[].name, .path, .tags
atx ct findings count --by repo --json                        # → per-repo severity distribution
atx ct findings list --source <name> --min-severity high --json
```

| Config field | Where it comes from |
|---|---|
| `portfolio_name` | the source name, or the portfolio report metadata |
| `service_inventory[].name` | repository slug (last segment) |
| `service_inventory[].path` | repository local path from `repository list` |
| `service_inventory[].priority` | repository labels, or the customer's own priority call |
| `service_inventory[].tags` | repository labels |
| `dependency_overrides[]` | **the dependency graph, or the customer's integration catalogue** |

> **On `dependency_overrides`:** do not synthesize these from findings and present them as declared. An edge with no evidence is a defect, not a low-confidence input. Either take them from the dependency-graph output (where each edge carries provenance and quoted evidence) or ask the customer for the declared set. Ten declared edges beat a hundred inferred ones.

> **On finding counts:** the CLI's count and the report JSON's own `counts.total` legitimately differ — the report splits `findings[]` from `evaluations[]` and the CLI counts both. Either is a valid basis for a summary; just do not treat the mismatch as a bug.

### Step 2 — Ask for the constraints

Conversationally, one or two at a time. These determine the phasing.

**Required in practice:**

> "How many engineers or teams are available for this modernization effort?" → `team_size`
>
> "What's your timeline?" → `timeline_constraint`

**Ask next:**

> "What's the budget envelope, including training and infrastructure?" → `budget_constraint`
>
> "What's the uptime requirement during migration?" → `availability_requirement` (this is what decides big-bang versus incremental)
>
> "How much risk can you take on parallelism and timeline compression — conservative, moderate, or aggressive?" → `risk_tolerance`

**Offer but do not require:**

> "Any compliance frameworks that must hold throughout?" → `compliance_requirements[]` (generates its own risks and validation gates)
>
> "What does the team already have — Kubernetes, Terraform, CI/CD?" → `existing_capabilities` (drives the training work stream and effort multipliers)
>
> "Any pathways to focus on or exclude?" → `priority_pathways` / `excluded_pathways`
>
> "Technology preferences?" → `preferences: {prefer, avoid}` — steers recommendations, never pathway logic

### Step 3 — Write the config

```yaml
additionalPlanContext: |
  portfolio_name: "my-platform"
  team_size: 8
  timeline_constraint: "12 months"
  budget_constraint: "$1.2M including training and infrastructure"
  compliance_requirements: ["SOC2", "PCI-DSS"]
  availability_requirement: "99.95%"
  risk_tolerance: "moderate"
  existing_capabilities: "Strong Java/Spring, basic Docker, CI/CD, no Kubernetes experience"
  preferences:
    prefer: ["eks", "aurora-postgresql", "graviton", "cdk"]
    avoid: ["self-managed-kafka"]
  service_inventory:
    - name: "payments-service"
      path: "/absolute/path/to/services/payments-service"
      priority: "P0"
      tags: ["java", "spring-boot"]
    - name: "user-service"
      path: "/absolute/path/to/services/user-service"
      priority: "P1"
      tags: ["python", "fastapi"]
  dependency_overrides:
    - source: "payments-service"
      target: "user-service"
      type: "sync"
      description: "REST calls for user validation"
```

> **`service_inventory[]` and `dependency_overrides[]` MUST be structured YAML object arrays** — never free-text bullet lists. The definition parses them programmatically.

Full field reference, including `ai_acceleration` and `ai_acceleration_overrides`, is in the definition's own `SKILL.md`. An annotated template ships in this repository at `examples/atx-config-exec-plan.yaml` (repository-root-relative) — copy it to the portfolio root, edit, and pass it with `-g file://`.

### Step 4 — Confirm before running

Present the config as prose, not YAML, and name what it does **not** know:

> "Here's the plan input:
>
> - **Portfolio:** my-platform — 11 services, 2 portfolio reports (both axes)
> - **Capacity:** 8 engineers, 12 months, moderate risk tolerance
> - **Budget:** $1.2M including training
> - **Hard constraints:** SOC2 and PCI-DSS throughout, 99.95% uptime during migration
> - **Dependencies:** 14 declared edges from the dependency graph; 3 services graded `Silent` (no integrations described — their placement is provisional, not evidence of independence)
> - **Not modelled:** cost per option, and the projected classification is band-only
>
> Generate it, or adjust anything first?"

Only run after the user confirms.

---

## Execution

```bash
workspace_abs=$(pwd)
config_abs="$workspace_abs/atx-config-exec-plan.yaml"

AWS_REGION=us-east-1 atx custom def exec \
  -n eba-execution-plan-generator \
  -p "$workspace_abs" \
  -g "file://$config_abs" \
  -x -t
```

| Flag | Purpose |
|---|---|
| `-n` | definition name |
| `-p` | workspace root — **absolute** in automated flows |
| `-g file://...` | configuration file, with the `file://` prefix |
| `-x` | non-interactive (mandatory for automated runs) |
| `-t` | trust all tools (mandatory for automated runs) |

`atx custom def` does **not** read the Region from AWS config the way `atx ct` does — set `AWS_REGION` explicitly.

The name only resolves if `eba-execution-plan-generator` has been **published into the account you are working in** (`atx custom def publish -n eba-execution-plan-generator --sd definitions/custom/eba-execution-plan-generator --category analysis`, verified with `atx custom def get -n eba-execution-plan-generator --td "$(mktemp -d)"`). The registry is per-account; see [`td-catalog.md` §0](td-catalog.md#0-what-you-need-on-disk).

Timeout: **1800000 ms (30 minutes)**, via the Bash tool's `timeout` parameter. For very large portfolios raise it to 2400000.

---

## Safety contract

1. **Run ONLY after the prerequisite analyses show status `complete`** — verify with `atx ct analysis list`.
2. **Verify report artifacts are available** via `atx ct analysis get --id <id> --json` (populated `report_paths`, empty `repo_errors`), then confirm the JSON files are on disk. `complete` alone is not sufficient.
3. **Issue exactly one Bash call** with `timeout: 1800000` ms. Do not poll, background, or split it.
4. **Do NOT run concurrently with `atx ct analysis run`** — git state conflicts.
5. **After completion, verify the artifact exists** before reporting success.

---

## Output

A four-artifact bundle in `portfolio-execution-plan/` at the workspace root:

```
portfolio-execution-plan/
├── {portfolio-name}-portfolio-exec-plan.md            # narrative roadmap
├── {portfolio-name}-portfolio-exec-plan.json          # machine-readable plan (canonical)
├── {portfolio-name}-portfolio-exec-plan.html          # self-contained HTML
└── {portfolio-name}-portfolio-exec-plan.metadata.json # sidecar metadata
```

The plan contains deduplicated work streams (one per triggered pathway; one per ARA category, where BLOCKERs become mandatory tasks and RISKs recommended), cross-dimension dependencies, shared-infrastructure tasks, a phased timeline with parallelization, a risk register, three-point effort and cost estimates with and without AI acceleration, and decision points for stakeholder review.

```bash
ls portfolio-execution-plan/*-portfolio-exec-plan.md   # exists ⇒ the run completed
```

---

## After it returns

**Read the plan before presenting it, and check two things.**

1. **Did the sequencing come from dependencies or from calendar buckets?** If the portfolio dependency map was empty, the phases degrade to generic time windows and the parallel tracks have no dependencies in them. That is a real result about your *input*, not about the customer's estate — say so, and go supply declared edges.
2. **Does any sentence claim platform work raised an agentic rung?** That is the drift to hunt for. Platform work lowers the price of every rung after it; it does not raise the rung.

Then present the plan as **one sequence**, not two backlogs: the modernization Phase 0 items annotated with the agentic findings each one resolves, then the agentic residue modernization does not buy. The bridge report produces exactly that pairing.

**If the run leaves you on a staging branch** (`git branch --show-current` shows `atx-result-staging-*`), that is normal — the transform creates one for its git operations. The output is on that branch; `git checkout <your-branch>` and merge or cherry-pick as needed.
