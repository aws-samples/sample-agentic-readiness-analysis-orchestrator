---
name: ara-moda-orchestrator
description: Orchestrate Agentic Readiness Analysis (ARA) and Modernization Readiness Analysis (MODA) across a service portfolio using AWS Transform Continuous Modernization (atx ct), plus dependency-aware Execution Plan (EBA) generation via atx custom. Use when the user wants to assess agentic-AI readiness or cloud-modernization readiness across multiple repos/microservices, run portfolio analyses, manage findings/remediations, schedule recurring analyses, or build a modernization roadmap. Triggers: "agentic readiness", "ARA", "MODA", "modernization readiness", "portfolio analysis", "atx ct", "continuous modernization", "execution plan".
---

# ARA / MODA Portfolio Analysis Orchestrator

Run comprehensive readiness analyses across a service portfolio with **AWS Transform Continuous Modernization** (`atx ct`). `ct` handles repository discovery, parallel execution, portfolio-level aggregation, findings management, remediation, and scheduling. This skill is the orchestration layer that drives it and connects it to Execution Plan generation.

**Written against `atx` 3.14.1.** Check your version with `readlink -f "$(command -v atx)"` — the path ends in the real version. `atx --version` is unreliable: it can report the version of whatever tool manager installed `atx` rather than `atx` itself. Upgrade with `atx update` (also `--check`, `--target-version <v>`, `--force`); upgrades preserve sources, repos, analyses, and findings. A handful of features below are tagged with a minimum version; everything untagged works on any recent CLI.

## Pre-flight

```bash
aws sts get-caller-identity                                 # credentials resolve
export AWS_REGION=us-east-1 AWS_DEFAULT_REGION=us-east-1     # see below
atx ct status --health                                       # prints healthy | unhealthy
```

⚠️ **Only `us-east-1` resolves.** A stray `AWS_REGION=us-west-2` makes the definition/credential endpoint NXDOMAIN (`transform-custom.us-west-2.api.aws`). Set both variables explicitly rather than relying on a profile default.

**No server process is needed** — `atx ct` runs in-process. `atx ct status --health` is an in-process check, not a daemon ping.

## Supported analyses

| Analysis | `atx ct` type | What it evaluates |
|---|---|---|
| **Agentic Readiness (ARA)** | `agentic-readiness` | **43 questions across 8 categories** — API Surface & Interface Design (8), Authentication/Authorization/Identity (7), State Management & Transactional Integrity (7), Data Accessibility & Quality (7), Engineering & Deployment Maturity (5), Human-in-the-Loop & Approval Workflows (3), Discoverability & Semantic Readiness (3), Observability of Target Systems (3). Whether systems are ready to be safely called by AI agents. |
| **Modernization Readiness (MODA)** | `modernization-readiness` | **38 questions across 5 categories** — Infrastructure (11), Operations (9), Security (7), Application (6), Data (5). Cloud modernization opportunity assessment; identifies containerization, serverless, and platform-upgrade candidates. |
| **Execution Plan (EBA)** | `atx custom def exec` | Dependency-aware roadmap. Built by this skill from discovered repos + `ct` findings, then run as a custom TD. The one place `additionalPlanContext` is used. |

Question counts and category names come from the TDs in this repo (`definitions/managed/{agentic,modernization}-readiness-analysis/SKILL.md`), which are authoritative.

| Requested scope | What runs |
|---|---|
| `agentic-readiness` | ARA across all discovered repos (per-repo + portfolio aggregation) |
| `modernization` | MODA across all discovered repos (per-repo + portfolio aggregation) |
| `full` | ARA + MODA + Execution Plan |

## Core workflow

```bash
# 1. Add a source. Local uses --path (absolute); SCM providers use --org + --token.
atx ct source add --name my-portfolio --provider local --path "$(pwd)/services"

# 2. Discover repositories (each subdirectory containing .git is one repo)
atx ct discovery scan --source my-portfolio
atx ct repository list

# 3. Run ARA (returns immediately with an id; poll — see Long-running analyses)
atx ct analysis run --type agentic-readiness --source my-portfolio

# 4. Run MODA (do not run concurrently with ARA — they conflict on git state)
atx ct analysis run --type modernization-readiness --source my-portfolio

# 5. Inspect findings (cheap server-side aggregate first, then drill in)
atx ct findings count --by severity --json
atx ct findings list --min-severity high --json

# 6. Retrieve reports
atx ct analysis get --id <analysis-id> --json | jq -r '.report_paths | to_entries[] | "\(.key)\t\(.value.ara // .value.mod)"'

# 7. (Optional) Generate the execution plan — see references/execution-plan.md
atx custom def exec -n eba-execution-plan-generator -p . -g file://atx-config-exec-plan.yaml -x -t
```

## Steering ARA and MODA

Four flags on `analysis run` shape the built-in assessments. No custom TD required — this is the normal way to bias an analysis toward a customer's environment.

| Flag | Valid with | Values | Default |
|---|---|---|---|
| `--context <text>` | **both** ARA and MODA | free-form prose | none |
| `--agent-scope <scope>` | **ARA only** | `read-only` \| `write-enabled` | `read-only` |
| `--prefer <list>` | **MODA only** | comma-separated, e.g. `eks,aurora,bedrock` | none |
| `--avoid <list>` | **MODA only** | comma-separated, e.g. `self-managed-kafka` | none |

```bash
atx ct analysis run --type agentic-readiness --source my-src \
  --agent-scope write-enabled --context "Customer-facing AI agents with tool-use"

atx ct analysis run --type modernization-readiness --source my-src \
  --prefer eks,aurora,bedrock --avoid self-managed-kafka
```

Mixing them wrong is a **hard validation error, not a silent ignore** — `--agent-scope` with `--type modernization-readiness` fails with *"--agent-scope is only valid with --type agentic-readiness."* Note the asymmetry: `--context` is shared; the other three are type-exclusive.

Also on `analysis run`: `--display-name <name>` (human-readable label shown in `analysis get`/`list`), `--tags k=v,...`, `--telemetry k=v,...`. `--repos` is an alias for `--repo`; both are repeatable *and* comma-separated, and the values are unioned.

⚠️ **Steering is not exposed via MCP.** Use the CLI when you need it.

## Source providers

Local sources use `--path` (a parent directory whose subdirectories are the repos) — always absolute. SCM providers use `--org` + `--token`.

```bash
atx ct source add --name x --provider local      --path /absolute/path/to/parent-dir
atx ct source add --name x --provider github     --org my-org       --token <pat>    # repo scope
atx ct source add --name x --provider gitlab     --org my-group     --token <pat> [--url https://gitlab.example.com]   # api scope
atx ct source add --name x --provider bitbucket  --org my-workspace --token <pat> [--username u] [--email e@example.com]

atx ct source list [--json]
atx ct source get    --name x
atx ct source update --name x --token <new-pat>    # rotate; stored locally and in AWS Secrets Manager
atx ct source remove --name x
```

**Do not point a local source at a single repo** — point at the directory *containing* repos. The source name becomes the source-half of every repo slug (`<source>::<repo>`), and it is account-scoped.

## Analysis types

| Type | Description |
|---|---|
| `rapid-techdebt-analysis` | Fast metadata-only scan of package manifests |
| `tech-debt-comprehensive` | Deep code-level tech debt analysis |
| `security` | Vulnerability / CVE detection (requires `atx ct setup security-agent`) |
| `agentic-readiness` | AI-agent integration readiness — 43 questions, 8 categories |
| `modernization-readiness` | Cloud modernization opportunity assessment — 38 questions, 5 categories |
| `custom` | Any transformation definition: `--type custom --transformation-name <name>` |

⚠️ **`rapid-techdebt-analysis` is a display name over a different stored value.** `rapid-techdebt-analysis`, `quick-scan`, and `tech-debt-quick` are all accepted on input, but the **canonical persisted value is `tech-debt-quick`** — that is what `analysis list --type <x>` filters on and what stored records contain. Pass what `--help` advertises; filter and assert on `tech-debt-quick`.

**`-g`/`--configuration` on `analysis run` requires `--type custom`** — built-in types reject it. This is not a blanket rule: on `remediation create`, `remote analysis`, `remote remediation`, and `schedule create` the gate is `--transformation-name` instead. To steer built-in ARA/MODA use the steering flags, not `-g`.

## Portfolio aggregation needs ≥ 2 repos

Both portfolio TDs are managed and built into `ct` (`AWS/portfolio-agentic-readiness-analysis`, `AWS/portfolio-modernization-readiness-analysis`). There is **no standalone portfolio command** — the roll-up runs automatically as a second phase of `analysis run` and lands in `portfolio_ara_summary` / `portfolio_mod_summary` on the analysis record.

- **A single-repo run gets no portfolio report.** The CLI still invokes the portfolio TD, burns time before declining, logs `runPortfolioAra: no portfolio ARA report found`, and leaves the summary `null`. Expected on 1 repo — don't debug it.
- **Separate single-repo runs do not accumulate.** Aggregation covers only the repos in one `analysis run`. Pass ≥2 repos, or omit `--repo` to take every repo under `--source`.
- **The bridge phase needs BOTH portfolio reports.** `runBridge` populates `bridge_summary` and skips unless a portfolio ARA *and* a portfolio MOD report exist.

**The per-repo phase runs concurrently** — wall-clock ≈ slowest repo + portfolio phase, not repos × per-repo time. An 11-repo ARA began analyzing 8 repos within ~2 minutes. `ATXCT_MAX_CONCURRENT_DEEP_SCANS` (default 1) gates only `tech-debt-comprehensive` and does **not** throttle ARA/MODA fan-out. An `ALREADY_RUNNING` guard rejects a run whose repos are mid-analysis for the same type.

## Long-running analyses

Analyses take **5–15 minutes per repo** (large repos 20–30 min).

1. **Tell the user immediately** after launching: "Running ARA across N repos — ~5–15 min per repo. I'll monitor and report when done."
2. **Poll rather than block.** `--wait` exists on `analysis run`, `remediation create`, and `remediation retry`, but blocking one tool call for 45 minutes gives no progress signal and risks a timeout. Use it in scripts and CI; poll in interactive work.
3. **Poll autonomously** with `analysis get --id <id>` every 30–60s. Don't make the user ask.
4. **On completion**, report finding count, severity distribution, repos analyzed — and **read `repo_errors`**, because `complete` does not mean every repo produced a report.
5. **On failure**, report the error and next steps (`references/troubleshooting.md`).

### ⚠️ `status: complete` is not a terminal signal on a multi-repo run

`status` flips to `complete` (and `completed_at` is stamped) when the **per-repo phase** finishes, while the **portfolio phase is still running** — for tens of minutes.

| field | at premature `complete` | at true completion |
|---|---|---|
| `status` | `complete` | `complete` / `failed` |
| `report_paths` | `{}` (0 entries) | 12 entries |
| `portfolio_ara_summary` | `null` | populated |
| `progress` | `{"done": 0, "total": 11}` | — |

An agent that stops at `status` reports **0 findings and no reports** on a run that produced 899 findings and a full portfolio bundle. Wait on one of these instead:

- **If you launched the run, wait for the process to exit.** The only unambiguous signal.
- **Otherwise require `status` terminal *and* `report_paths` non-empty.** That map is written in the final record update, so it is empty for the whole premature window. Cap it with a timeout — a run that fails early leaves `report_paths` empty forever.

Because `status` is already terminal, **a portfolio-phase error cannot transition it**, so `status: complete` does not imply `error: null`. Read `error` and `repo_errors` explicitly; never infer them from `status`. Never conclude "no reports were generated" from an empty `report_paths` alone — check disk first.

**Polling in a shell loop:** the shell here is zsh, where `$status` is a **read-only reserved variable**. `status=$(...)` fails with "read-only variable: status" — use another name (`st=$(...)`).

## Report artifacts

```bash
atx ct analysis list-artifacts --id <id> [--repo <repositoryId>] [--max-results 1-100] [--next-token <t>] [--json]
atx ct analysis get-artifact  --id <id> --artifact-id <aid> [--output <file>] [--force]
```

Each artifact is one **per-repo bundle** (`<repo>/artifacts.zip`). **Artifacts materialize per-repo as each repo completes, so a mid-run listing can be partial.** This is how to get the full bundle, which `report_paths` does not expose.

**Reports are on local disk, and `analysis get --json` tells you where.** `report_paths` maps each repo slug to its report file — but it is the **markdown-only view**. It is the right way to enumerate *which* repos produced reports and the wrong way to reach a `.json` or `.html`.

`analysis list` returns a thinner object with no `report_paths`; call `get` per id. Useful `analysis get --json` keys: `report_paths, ara_results, mod_results, portfolio_summary, portfolio_ara_summary, portfolio_mod_summary, repo_scores, repo_status, repo_errors, progress, repos_done, repos_total, status, error`.

### Three on-disk locations — know which one has what

| Location | md | json | html | What it holds |
|---|---|---|---|---|
| `~/.atxct/shared/analyses/<id>/artifacts/<source>__<repo>/` | 12 | 1 | **0** | Per-analysis artifact store — **where `report_paths` points.** Effectively markdown-only. |
| `~/.atxct/sources/<src>/<type>/runs/<id>/` | 12 | **13** | **1** | **Source-scoped run history — the only COMPLETE copy.** Where `portfolio_summary.report_path` points. |
| the repo working tree (local sources only) | ✓ | ✓ | ✓ | Full per-repo bundle. **Per-repo only — never portfolio.** |

```
~/.atxct/sources/<src>/<type>/runs/<id>/
├── <source>-<repo>-<16hex>/<type>-analysis/<repo>-{ara,mod}-report.{md,json}
└── portfolio-<name>/<type>-analysis/<name>-portfolio-{ara,mod}-report.{md,json,html,metadata.json}
```

Three traps:

- **`<type>` is the SOURCE's analysis root, not the run's type.** A `modernization-readiness` run's output can sit under `sources/<src>/agentic-readiness/runs/<id>/`. Don't build the path from the analysis type — glob `sources/*/*/runs/<id>/`, or read `portfolio_summary.report_path`.
- **Per-repo dirs here are slug-mangled** (`<source>-<repo>-<16hex>`, a sha256 prefix), unlike the `<source>__<repo>` form under `shared/analyses/`. Glob, don't construct.
- **HTML and portfolio JSON exist only here** — not in `shared/analyses/`, and not in any working tree, because no repo owns portfolio output.

```bash
# Every artifact of a run, regardless of type or slug mangling:
find ~/.atxct/sources -path "*runs/<analysis-id>/*" -type f \( -name '*.md' -o -name '*.json' -o -name '*.html' \)

# Portfolio bundle for one run:
ls ~/.atxct/sources/*/*/runs/<analysis-id>/portfolio-*/*-analysis/
```

**Provider affects only the working-tree copy.** SCM sources: nothing is committed to the repos; `ct` touches repo git only during a remediation (branch + PR). Local sources: analyses **also** write the full per-repo bundle into each working tree, and `ct` auto-commits it (authored `ATX Bot <checkpoint@atx.bot>`). Two consequences — a tree can look clean right after an analysis because the output was *committed* rather than not written; and a repo mid-analysis has those files modified, which trips the remediation dirty-worktree guard until the run finishes.

**Finding counts differ between the CLI and the report JSON, by design.** The report splits `findings[]` (severity-bearing gaps) from `evaluations[]` (passing questions, no severity). The CLI's `findings count` includes both; the report's `counts.total` does not. Measured on one ARA: `counts.total: 36` vs CLI `43`, with disjoint `question_id` sets that union to exactly 43. Never assert those two numbers match.

## Findings

```bash
atx ct findings count --by severity|repo|analysis-type [--source <n>] [--repo <slug>] [--type <t>] [--status open|dismissed|obsolete] [--json]
atx ct findings list [--repo <n>] [--source <n>] [--severity low|medium|high] [--min-severity low|medium|high] \
                     [--type <t>] [--status open|dismissed|obsolete] [--analysis-id <id>] [--fix-transform <name>] [--next-token <t>] [--json]
atx ct findings get   --id <id>
atx ct findings update       --id  <id>  --status open|dismissed [--reason "..."] [--notes "..."]
atx ct findings batch-update --ids <csv> --status open|dismissed [--reason "..."]
atx ct findings delete --id <id>
```

- **`--severity` (exact) and `--min-severity` (threshold) are mutually exclusive.**
- **Prefer `findings count` over list-then-count** — it aggregates server-side and is far cheaper on large portfolios.
- **`--reason` is required when `--status dismissed`.**
- **Findings can only be deleted when `dismissed` or `obsolete`.** To purge open findings: `batch-update --status dismissed --reason "..."`, then `delete --id` per finding (there is no batch delete).

## Remediation

```bash
atx ct remediation create --ids <csv> | --transformation-name <name> \
    [--repo <slug>] [--source <n>] [-g <config>] [--name <n>] [--slots <n>] [--local]
atx ct remediation list|status|retry|cancel|delete
```

⚠️ **ARA/MODA findings are never auto-remediable.** Every finding they emit has `fix: null`, and `remediation create --ids` rejects them with `non_remediable=[...]`. Remediation of ARA/MODA output must go through `--transformation-name`.

`--slots` caps concurrent repos (default 20). `-g` is valid only with `--transformation-name`.

## Remote execution

Run analyses on AWS compute instead of a laptop.

```bash
atx ct remote analysis --mode aws-managed --type agentic-readiness --sources my-portfolio
atx ct remote analysis --mode ec2|batch   --type agentic-readiness --sources my-portfolio --stack-name <stack>
```

| `--mode` | Infrastructure |
|---|---|
| `aws-managed` | **The AWS-managed fleet — no customer infra required.** *(requires atx ≥ 3.14; verified on 3.14.1)* |
| `ec2` | Customer-deployed CloudFormation stack, one container per repo |
| `batch` | Customer-deployed CloudFormation stack, AWS Batch |

Fan-out is `--sources` (all repos in a source) and/or `--repos` (specific repos) — supplying both runs their union. Filter with `--labels` (AND semantics, `--sources` only). Resume a partial Batch run with `--resume-incomplete --batch-name <id>`.

```bash
atx ct remote detect   --mode ec2|batch [--stack-name <n>] [--tags k=v]
atx ct remote status   [--batch <id>] [--group <id>] [--stack-name <n>] [--wait] [--wait-timeout <min>]
atx ct remote cancel   [--mode ec2|batch] [--batch <id>] [--job <id>] [--group <id>]
atx ct remote network  discover [--vpc <id>] | create [--cidr 10.1.0.0/16] [--no-security-group]
atx ct remote provision --mode ec2|batch --vpc <id> --subnets <ids> [--securityGroup <id>] [--workers 1-5] [--execute]
atx ct remote update    --mode ec2|batch [--execute]
atx ct remote teardown  --mode ec2|batch --stack-name <n> [--execute]
atx ct remote credentials --source <n> --token <pat> | --remove
```

- **`provision`, `update`, and `teardown` are dry-run by default** — they print a preview (and `provision` writes the CloudFormation template locally). They only act with `--execute`. These need admin permissions; `--ack` skips the interactive prompt.
- **`provision` can reuse pre-created IAM** via `--existing-batch-job-role-arn`, `--existing-batch-execution-role-arn`, `--existing-lambda-{submit,terminate,metrics}-role-arn`, `--existing-instance-profile-name`, and `--existing-scheduler-role-arn` — for accounts where agents may not create roles.
- **`remote credentials`** stores a source's token in AWS Secrets Manager so remote workers can clone.
- **A `local` source running remotely works from the CLI** (it bundles the source to S3) but **not from the Console**, which has no upload step.

## Schedules

Recurring analyses. Fully surfaced in `--help` and in `atx ct schema`.

```bash
atx ct schedule create --name nightly-ara --mode aws-managed --recurrence daily \
    --type agentic-readiness --sources my-portfolio --execution-role <arn>
atx ct schedule list|get|enable|disable|delete [--region <r>] [--json]
atx ct schedule teardown [--stack-name <n>] [--execute] [--yes]
```

- `--recurrence` is **required**: `daily` | `weekly:<MONDAY..SUNDAY>` | `monthly:<1..28>`. Raw `cron(...)`/`at(...)` expressions are not accepted.
- **The fire time is not configurable to the minute** — per its own help it "resolves to about 2 minutes from now (local wall clock, DST-stable)". A schedule named `nightly-*` will not necessarily run at night.
- `--execution-role <arn>` is **required for `--mode aws-managed`** (the role the Scheduled Analysis Runner assumes at fire time). `--mode ec2|batch` creates a local EventBridge schedule and needs `--stack-name`.
- List a schedule's fired child runs with `atx ct analysis list --schedule-id <sched-id>`.

## Repositories and labels

```bash
atx ct repository list [--source <n>] [--language <l>] [--has-workflow true|false] [--labels <csv>] [--next-token <t>] [--json]
atx ct repository get    --repo <slug> --source <n>
atx ct repository update --source <n> [--repo <csv>] --labels <csv>    # omit --repo for all repos under the source
atx ct repository delete --repo <slug> --source <n>
```

Labels are the grouping mechanism for targeted runs — set them with `repository update`, then select with `--labels` on `remote analysis` / `schedule create`. `--labels` filters use AND semantics. Pass an empty string to clear.

## Hosted web Console

AWS Transform has a hosted **Continuous modernization** Console with Dashboard / Findings / Remediations / Analyses / Sources / Settings tabs, reading the same account-scoped data as the CLI. It is the best "show the audience" surface — prefer it over exporting reports for demos. There is no local web UI.

**Where the Console and CLI differ:**

| Task | Console | CLI |
|---|---|---|
| Browse findings/analyses, demo | ✅ best | workable |
| Run analysis on an SCM source | ✅ | ✅ |
| Run analysis on a `local` source remotely | ❌ no upload step | ✅ auto-bundles to S3 |
| ARA/MODA steering (`--context`, `--prefer`, …) | ❌ not exposed | ✅ |
| Recurring schedules | ✅ | ✅ `schedule create` |

Neither surface is a superset. Reach for the CLI whenever a `local` source or steering is involved.

## Safety contract: Execution Plan (EBA)

The Execution Plan is the one analysis **this skill generates**: it builds `atx-config-exec-plan.yaml` with `additionalPlanContext` from `ct` data plus the user's execution constraints, then runs it. See `references/execution-plan.md` for the interactive flow.

1. **EBA runs ONLY AFTER both ARA and MODA show status `complete`** (verify via `analysis list`).
2. **Verify the reports actually exist** — `complete` is not sufficient. Check `analysis get --id <id> --json` for populated `report_paths` and empty `repo_errors`, then confirm the files are on disk.
3. **Issue exactly one Bash call** for the EBA command with `timeout: 1800000` ms. Do not poll, background, or split it.
4. **Do NOT run EBA concurrently with any `analysis run`** — `ct` and custom exec conflict on git state.
5. **After it returns, verify the artifact exists** (`ls portfolio-execution-plan/*-portfolio-exec-plan.md`) before reporting success.

## MCP integration

`atx ct mcp` exposes a **subset** of the CLI as MCP tools — read/query work is cleaner through it; anything in the "absent" list below needs the CLI.

```bash
atx ct mcp                                # stdio (local agent integration)
atx ct mcp --transport http --port 3100   # HTTP
```

Enumerate the current tool set with an `initialize` + `tools/list` handshake rather than trusting a count written down here — it changes between releases. Broadly it covers `source_*`, `discovery_scan`, `repository_*`, `analysis_*`, `findings_*`, and `remediation_*`.

**Absent from MCP — use the CLI:** `findings batch-update`, `repository update`, `setup`, `status`, the entire `remote` group, the entire `schedule` group, the ARA/MODA steering flags, and EBA (`atx custom def exec` is not an MCP tool).

```json
{
  "mcpServers": {
    "atxct": { "command": "atx", "args": ["ct", "mcp"], "env": { "AWS_PROFILE": "your-profile", "AWS_REGION": "us-east-1" } }
  }
}
```

MCP naming differs from the CLI (local source `provider_config.rootPath` vs `--path`; `identifier`/`token` vs `--org`/`--token`; `assessment_type` vs `--type`) — see `references/ct-workflow.md`.

## Operational notes

- **JSON field names are terse. Inspect before scripting.**
  - `source list --json` → objects use `.source` (**not** `.name`), plus `.provider`, `.identifier`.
  - `repository list --json` → paginated envelope `{ items, nextToken, total }`; repos are under `.items[]`, keyed by `.slug` and `.source`. The key is `nextToken`, **not** `next_cursor`.
  - `findings list --json` → top-level array; the auto-fix indicator is `.fix` (always `null` for ARA/MODA).
- **Pagination** is `--next-token <token>` on `source list`, `repository list`, `analysis list`, `findings list`, `remediation list`. Only `analysis list-artifacts` has `--max-results`. `repository list` pagination requires a single `--source`.
- **Teardown order is the reverse of creation.** You cannot remove a source that still has repos (HTTP 409). Order: **delete repositories → delete findings → remove source.** `analysis delete --cascade-findings` removes that analysis's findings; repos persist until explicitly deleted.
- **`source remove` and per-item deletes exit 0 even when they no-op** (e.g. a swallowed 409). Re-list and verify counts; don't trust exit codes alone.
- **Bulk deletes are slow** (sequential API calls, ~1–2 s each). For dozens of items, run the loop as a background task and poll live counts rather than the buffered output.
- **`custom def get` writes files into CWD** — run it from a scratch dir.
- **Pipe-stdin consumption in loops:** in `atx ct repository list --json | jq ... | while read ...`, the CLI can consume the pipe's stdin and end the loop after one item. Capture to a variable first, then `while read ... <<< "$var"`.
- **`findings dismiss` does not exist** — use `findings update --status dismissed --reason "..."`.
- **`PYENV_VERSION=system` for git pushes** on machines where pyenv's Python has a broken `hashlib` (blake2b/blake2s `ValueError`). Without it, `git push` during remediation fails with a Python traceback — the root cause of "remediation failed to push branch". Export it in the environment running `atx ct`.

## Guided workflow (UX)

After each major step, offer 2–3 concrete next actions, most valuable first. Never leave the user at a dead end.

- **After discovery:** "Discovered N repos. Run Agentic Readiness (ARA), Modernization Readiness (MODA), or both?"
- **After ARA:** offer MODA, high-severity findings, or a per-repo report.
- **After MODA:** offer the execution plan, findings by severity/category, remediation, or the portfolio report.
- **After both:** recommend the execution plan (dependency-aware phased roadmap).
- **After EBA:** offer to summarize phases/timeline, show quick wins, or open the full plan.
- **After findings listed:** offer remediations, dismissals, or category/repo filters.

## Reference files (read on demand)

Do NOT load these proactively. Pick the one relevant to the task and Read it.

| Reference | When to read |
|---|---|
| `references/getting-started.md` | First-time setup: credentials, CLI install, source configuration, pre-flight |
| `references/ct-workflow.md` | Running analyses end-to-end: sources, discovery, execution, findings, reports, remediation |
| `references/execution-plan.md` | Generating the Execution Plan via `atx custom def exec`, including the interactive config flow |
| `references/troubleshooting.md` | Errors: analysis/discovery failures, missing reports, EBA/remediation errors, credentials |

## Full command surface

`atx ct schema` prints a machine-readable JSON manifest of the command tree — the best starting point for automation. It covers 12 command groups (`source`, `discovery`, `repository`, `analysis`, `findings`, `remediation`, `setup`, `status`, `remote`, `schedule`, `mcp`, `schema`) but is **not exhaustive**: it omits the deprecated hidden `server` command and the `--wait` flag. Its `version` field is a schema constant, not the CLI version.

**Status** `atx ct status [--health] [--json]`
**Schema** `atx ct schema`
**Sources** `atx ct source add|list|get|remove|update`
**Discovery** `atx ct discovery scan --source <n> [--path <override>] [--json]`
**Repositories** `atx ct repository list|get|update|delete`
**Analysis** `atx ct analysis run|get|list|list-artifacts|get-artifact|cancel|delete`
**Findings** `atx ct findings list|count|get|update|batch-update|delete`
**Remediation** `atx ct remediation create|list|status|retry|cancel|delete`
**Setup** `atx ct setup <component> [--status] [--delete]`
**Remote** `atx ct remote analysis|remediation|status|detect|provision|update|credentials|teardown|cancel|network`
**Schedule** `atx ct schedule create|list|get|enable|disable|delete|teardown`
**MCP** `atx ct mcp [--transport stdio|http] [--port <p>]`
