---
name: ara-moda-orchestrator
description: Orchestrate Agentic Readiness Analysis (ARA) and Modernization Readiness Analysis (MODA) across a service portfolio using AWS Transform Continuous Modernization (atx ct), plus dependency-aware Execution Plan (EBA) generation via atx custom. Use when the user wants to assess agentic-AI readiness or cloud-modernization readiness across multiple repos/microservices, run portfolio analyses, manage findings/remediations, or build a modernization roadmap. Triggers: "agentic readiness", "ARA", "MODA", "modernization readiness", "portfolio analysis", "atx ct", "continuous modernization", "execution plan".
---

# ARA / MODA Portfolio Analysis Orchestrator

Turn Claude into an orchestrator for running comprehensive analyses across a service portfolio using **AWS Transform Continuous Modernization** (`atx ct`). `ct` handles repository discovery, parallel execution, portfolio-level aggregation, findings management, and remediation natively — this skill is the orchestration layer connecting `ct` with Execution Plan generation.

> Ported from the AWS "orchestrator" Kiro Power (`aws-samples/sample-agentic-readiness-analysis-orchestrator`). Where the original referenced Kiro's `readSteering` action, use the **Read** tool on the files in `references/`; where it referenced `executeBash`, use the **Bash** tool.

> **⚠️ Verified 2026-08-03 against atx 3.9.0 — read this before running anything.**
>
> **First: check your version correctly.** `atx --version` **lies inside Claude Code** — it prints `2.1.220.613`, which is Builder Toolbox's build number for *claude-code*, inherited via `$TOOLBOX_TOOL_VERSION`. atx resolves `TOOLBOX_TOOL_VERSION || SEG_VERSION || DEV_BUILD`, so the toolbox var wins over its own `SEG_VERSION`. Use one of these instead:
> ```bash
> env -u TOOLBOX_TOOL_VERSION atx --version      # → Version: 3.9.0
> ls -la "$(command -v atx)"                     # → .../share/atx/3.9.0/atx
> ```
> Any doc or bug report quoting a `2.1.x` "atx version" is quoting the wrong number.
>
> - **No server needed.** `atx ct server` still exists but is **hidden and deprecated** — analyses run in-process. It prints its own warning and starts a real daemon on `:8081` that will block your shell, so never invoke it. Use `atx ct status --health` (an in-process check, not a daemon ping). There is also a hidden top-level `--api <url>` defaulting to `http://localhost:8081`; leave it alone.
> - **`--wait` DOES exist** on `analysis run`, `remediation create`, and `remediation retry` — registered with `.hideHelp()`, so it appears in neither `--help` nor `atx ct schema`. Earlier revisions of this doc claimed it was removed; that was wrong. Prefer polling in agent workflows (see [Long-running analysis](#agent-behavior-long-running-analysis)) — but that is a *choice*, not a missing flag.
> - **`analysis list-artifacts` / `get-artifact` are GONE** — 0 occurrences in the shipped bundle; `error: unknown command`. Reports now come from `analysis get --json` → `report_paths`, but that map is **markdown-only**: `.json` and `.html` (and every portfolio artifact) live under `~/.atxct/sources/<src>/<type>/runs/<id>/`, which `report_paths` never mentions. See [Report artifacts](#report-artifacts).
> - **Region: only `us-east-1` resolves.** A stray `AWS_REGION=us-west-2` makes the definition/credential endpoint NXDOMAIN (`transform-custom.us-west-2.api.aws`). Always `export AWS_REGION=us-east-1 AWS_DEFAULT_REGION=us-east-1`.
> - **`atx ct schema` is NOT a complete manifest.** It reports 11 top-level commands and omits the hidden `schedule` and `server` groups plus every hidden flag. The shipped bundle is ground truth; treat `schema` (and `ATXControlTower/docs/cli-reference.md`) as incomplete.
> - **Zero-findings bug is fixed as of 3.9.0.** On 3.7.0 analyses completed with 0 findings. Verified fixed on 3.9.0: a single-repo ARA produced 43 findings and a MOD 31. If you are on 3.7.0, upgrade. See [Zero-findings bug](#zero-findings-bug-370).
> - **ARA/MOD findings are never auto-remediable.** Every finding they emit has `fix: null`, and `remediation create --ids` rejects those with `non_remediable=[...]`. Remediation of ARA/MOD output must go through `--transformation-name`. See [Remediation](#remediation).

## Supported analyses

| Analysis | `atx ct` type | What it evaluates |
|---|---|---|
| **Agentic Readiness (ARA)** | `agentic-readiness` | **43 questions across 8 categories** — API Surface & Interface Design (8), Authentication/Authorization/Identity (7), State Management & Transactional Integrity (7), Data Accessibility & Quality (7), Engineering & Deployment Maturity (5), Human-in-the-Loop & Approval Workflows (3), Discoverability & Semantic Readiness (3), Observability of Target Systems (3). Whether systems are ready to be safely called by AI agents. |
| **Modernization Readiness (MODA)** | `modernization-readiness` | **38 questions across 5 categories** — Infrastructure (11), Operations (9), Security (7), Application (6), Data (5). Cloud modernization opportunity assessment; identifies containerization, serverless, and platform-upgrade candidates. |
| **Execution Plan (EBA)** | N/A — generated by Claude via `atx custom def exec` | Dependency-aware roadmap. Claude builds `atx-config-exec-plan.yaml` (with `additionalPlanContext`) from discovered repos + `ct` findings, then runs the EBA TD. The ONE place `additionalPlanContext` is used. |

Counts and category names are derived from the TDs in this repo (`definitions/managed/{agentic,modernization}-readiness-analysis/SKILL.md`) — the authoritative source. An earlier revision of this doc claimed ARA was "56 criteria across 5 categories" and then listed MOD's categories; both were wrong.

| Requested scope | What runs |
|---|---|
| `agentic-readiness` | ARA across all discovered repos (per-repo + portfolio aggregation) |
| `modernization` | MODA across all discovered repos (per-repo + portfolio aggregation) |
| `full` | ARA + MODA + Execution Plan |

### Portfolio aggregation needs ≥ 2 repos

Both portfolio TDs are **managed and built into `ct`** — `AWS/portfolio-agentic-readiness-analysis` and `AWS/portfolio-modernization-readiness-analysis`. There is **no standalone portfolio command** (`ct portfolio`, `ct portfolio run`, `ct analysis portfolio`, `ct analysis aggregate` are all `unknown command`); the roll-up runs automatically as a second phase of `analysis run`, and lands in `portfolio_ara_summary` / `portfolio_mod_summary` on the analysis record.

⚠️ **Aggregation is per-run, and each portfolio TD requires at least 2 discovered reports** (`definitions/managed/portfolio-agentic-readiness-analysis/SKILL.md` step 1.1; MOD likewise). Consequences:

- **A single-repo run gets no portfolio report.** The CLI still invokes the portfolio TD and it still burns time (~13 min observed) before declining, then logs `runPortfolioAra: no portfolio ARA report found for <name>` and leaves `portfolio_ara_summary: null`. That is *expected behavior on 1 repo*, not a bug — don't debug it as one.
- **Separate single-repo runs do not accumulate.** Aggregation only ever covers the repos in one `analysis run` invocation, so to get a portfolio view, pass ≥2 repos (or omit `--repo` to take every repo under `--source`).
- **The bridge phase needs BOTH portfolio reports.** `runBridge` populates `bridge_summary`, and skips with `runBridge: missing portfolio report paths, skipping bridge` unless a portfolio ARA *and* a portfolio MOD report exist. Note this overlaps with the custom `definitions/custom/bridge-analysis/` TD in this repo — decide deliberately which one a given workflow uses.

**The per-repo phase runs concurrently.** An 11-repo ARA cloned and began analyzing 8 repos within ~2 minutes, so wall-clock ≈ slowest repo + portfolio phase (tens of minutes), not repos × ~20 min. `ATXCT_MAX_CONCURRENT_DEEP_SCANS` (default 1) gates only `tech-debt-comprehensive` and does **not** throttle ARA/MOD fan-out. Separately, an `ALREADY_RUNNING` guard rejects a run whose repos are mid-analysis for the same type, and `repos_done`/`repos_total` read `null` while a run is in flight — poll `status`, not those fields.

### When to use
- Planning agentic AI adoption across microservices
- Identifying shared infra gaps and modernization opportunities
- Prioritizing modernization by dependencies
- Tracking portfolio-wide readiness over time
- Generating execution roadmaps from findings
- Continuous monitoring of tech debt / readiness regressions

## Reference files (read on demand)

Do NOT load all of these proactively. Pick the one relevant to the current task and Read it.

| Reference | When to read |
|---|---|
| `references/getting-started.md` | First-time setup: AWS credentials, ATX CLI install, source configuration, pre-flight sequence |
| `references/ct-workflow.md` | Running analyses end-to-end: sources, discovery, analysis execution, findings management, report retrieval, remediation |
| `references/execution-plan.md` | Generating the Execution Plan (EBA) via `atx custom def exec` after ARA+MODA complete — includes the interactive config-generation flow |
| `references/troubleshooting.md` | Errors: analysis/discovery failures, missing reports, EBA/remediation errors, credentials |

> All four were rewritten against verified 3.9.0 behavior on 2026-08-03: the `atx ct server` start-up steps are gone (replaced by `atx ct status --health`), `list-artifacts`/`get-artifact` are gone (replaced by `analysis get --json` → `report_paths`, with the "`report_paths` is not the whole bundle" caveat), and `troubleshooting.md`'s claim that artifacts are "NOT on the local filesystem" is corrected — they are on local disk. This SKILL.md remains the source of truth for CLI behavior; the references carry the interactive flows and error taxonomies.

## Demo harness (tested end-to-end 2026-07-10; local-first)

A full reset-and-rebuild harness lives at the project root.
All scripts default to **LOCAL mode** (no GitHub, no Code Defender); pass `--remote` for GitHub mode.

```
<project>/demo-scripts/
├── 00-full-setup.sh           # Bake env: server (PYENV_VERSION=system) → source → discovery → trim → ARA → MODA → export (~45 min)
├── 00-push-repos.sh           # [remote only] Push 3 pre-baked repos to org (user runs — Code Defender)
├── 01-live-discovery-push.sh  # Live beat: pricing-cgi "appears" (3 repos → 4)
├── 02-reset-live-discovery.sh # Reset just the live-discovery beat
├── 99-full-reset.sh           # Nuke everything (ct + local state; + GitHub with --remote)
└── README.md
```

**Full local cycle:** `99-full-reset.sh` → `00-full-setup.sh` → demo-ready. No prerequisites beyond atx CLI + AWS creds.

Key fixes baked into the harness:
- **Portfolio repos are git-inited on the fly** — a fresh clone of the harness ships the portfolio dirs WITHOUT nested `.git` (they can't live inside the parent repo), and `ct` discovery scans for `.git` subdirs → finds 0. Setup self-heals: `git init -b main` + initial commit for any portfolio dir missing `.git`.
- `PYENV_VERSION=system` on server start (fixes pyenv 3.13.2 blake2b crash in git push)
- **Local remediation requires a CLEAN worktree** — prior analysis runs write `services/<repo>/{ara,mod}-report.{md,json,html}` artifacts INTO local repos (this is also where HTML reports live for local sources!). Remediation fails with "has uncommitted changes" until `services/` is removed. Reset cleans this.
- Local-source remediation completes with status `pr_open` and creates a local staging branch (`atx-result-staging-*`) — show the diff with `git diff main`.
- `findings update` (single) instead of `batch-update` — batch fails with `UnknownError` on some IDs.
- Retry-sweep in reset for teardown ordering (repos → findings → sources)
- Pipe-stdin-consumption fix in loops (capture first, or `< <(...)` process substitution)
- `ct` discovery does NOT follow symlinks — local sources need real repo dirs
- [remote only] `git-defender self-attest --reason 1` per repo; must run INSIDE a repo dir with matching `origin` remote set

## Core workflow (high-level)

```bash
# 0. Pre-flight — FAIL FAST (see references/getting-started.md)
aws sts get-caller-identity
env -u TOOLBOX_TOOL_VERSION atx --version                  # NOT plain `atx --version` — see version note
export AWS_REGION=us-east-1 AWS_DEFAULT_REGION=us-east-1   # see region note above
atx ct status --health     # in-process check; do NOT start `atx ct server`

# 1. Add a source. Local uses --path (absolute); remote uses --org + --token.
atx ct source add --name my-portfolio --provider local --path "$(pwd)/services"

# 2. Discover repositories (scans for .git subdirectories)
atx ct discovery scan --source my-portfolio
atx ct repository list

# 3. Run ARA (launch + poll — see "Long-running analysis" below)
atx ct analysis run --type agentic-readiness --source my-portfolio

# 4. Run MODA (after ARA; do not run both concurrently)
atx ct analysis run --type modernization-readiness --source my-portfolio

# 5. Inspect findings  (cheap aggregate first, then drill in)
atx ct findings count --by severity --json
atx ct findings list --json

# 6. Retrieve reports — report_paths, NOT the removed get-artifact
atx ct analysis get --id <analysis-id> --json | jq -r '.report_paths | to_entries[] | "\(.key)\t\(.value.ara // .value.mod)"'

# 7. (Optional) Generate execution plan (see references/execution-plan.md)
atx custom def exec -n eba-execution-plan-generator -p . -g file://atx-config-exec-plan.yaml -x -t
```

## Steering ARA / MODA without a custom TD

Four flags on `analysis run` shape the built-in ARA and MODA assessments — no custom TD required. Added in 3.5.0; **verified present on 3.9.0.** This is the answer whenever someone asks how to bias the analysis toward their environment.

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

Mixing them wrong is a **hard validation error, not a silent ignore** — e.g. `--agent-scope` with `--type modernization-readiness` fails with *"--agent-scope is only valid with --type agentic-readiness."* Note the asymmetry: `--context` is shared, the other three are type-exclusive.

Also available on `analysis run`: `--tags k=v,...` and `--telemetry k=v,...` (`client=zerodebt` is always appended). `--repos` is an alias for `--repo`; both are repeatable *and* comma-separated.

⚠️ **Not exposed via MCP.** `analysis_run`'s only properties are `assessment_type, inputs, repos, tags, telemetry` — steering would have to ride inside `inputs`, which is unverified. Use the CLI when you need steering.

## Source providers

`ct` supports four providers. **Local sources use `--path` (a parent directory containing repos as subdirectories) — always absolute. Remote providers use `--org` + `--token`.**

```bash
atx ct source add --name x --provider local     --path /absolute/path/to/parent-dir
atx ct source add --name x --provider github     --org my-org       --token ghp_xxx        # repo scope
atx ct source add --name x --provider gitlab     --org my-group     --token glpat-xxx [--url https://gitlab.example.com]   # api scope
atx ct source add --name x --provider bitbucket  --org my-workspace --token xxx [--username u] [--email e@x.com]
atx ct source list [--json]
atx ct source remove --name x
```

Do NOT point a local source at a single repo — point at the directory *containing* repos. Full detail in `references/ct-workflow.md` and `references/getting-started.md`.

## Analysis types

The exact `--type` values accepted on 3.9.0, in the order the CLI lists them:

| Type | Description |
|---|---|
| `rapid-techdebt-analysis` | Fast metadata-only scan of package manifests |
| `tech-debt-comprehensive` | Deep code-level tech debt analysis |
| `security` | Vulnerability / CVE detection (requires `atx ct setup security-agent`) |
| `agentic-readiness` | AI-agent integration readiness — 43 questions, 8 categories |
| `modernization-readiness` | Cloud modernization opportunity assessment — 38 questions, 5 categories |
| `custom` | Run any transformation definition: `--type custom --transformation-name <name>` |

**⚠️ `rapid-techdebt-analysis` is a display rename over an unchanged storage value.** The alias map is `{"rapid-techdebt-analysis":"tech-debt-quick","quick-scan":"tech-debt-quick"}`, so all three are accepted on input, but the **canonical persisted value is `tech-debt-quick`** — that is what `analysis list --type <x>` filters on and what stored records contain. This rename has no changelog entry. An earlier revision of this doc listed `tech-debt-quick` as the flag value to pass; it works, but `rapid-techdebt-analysis` is what `--help` advertises.

**Config limitation:** `-g`/`--configuration` on `atx ct analysis run` is **only valid with `--type custom`** — built-in types reject it. But this is *not* a blanket rule across the CLI: on `remediation create`, `remote analysis`, `remote remediation`, and `schedule create`, the gate is `--transformation-name` instead (*"--configuration is only valid with --transformation-name"*). To steer built-in ARA/MODA, use the steering flags above rather than `-g`.

## Report artifacts

**`analysis list-artifacts` and `analysis get-artifact` no longer exist** — verified 2026-08-03: `error: unknown command`, and **0 occurrences** across all three shipped bundles. They were never merely hidden here; they are not shipped. (Upstream they are registered `{hidden:true}` pending a read-path launch, with the ops throwing "not yet available".) Delete any code you find that calls them.

**Reports are on local disk, and `analysis get --json` tells you where.** `report_paths` maps each repo slug to its report file:

```bash
atx ct analysis get --id <id> --json | jq -r '.report_paths | to_entries[] | "\(.key)\t\(.value.ara // .value.mod)"'
# harness-portfolio::legacy-loan-calculator  /Users/me/.atxct/shared/analyses/<id>/artifacts/harness-portfolio__legacy-loan-calculator/legacy-loan-calculator-ara-report.md
```

⚠️ **`report_paths` is the markdown-only view.** It is the right way to enumerate *which* repos produced reports, but the wrong way to reach a `.json` or `.html` — those live in a different tree. See [Three on-disk locations](#three-on-disk-locations--know-which-one-has-what) before concluding an artifact wasn't generated.

Note `analysis list` returns a **thinner** object with no `report_paths` — you must call `get` per id. `analysis get --json` exposes 31 keys, the useful ones being `report_paths, ara_results, mod_results, portfolio_summary, portfolio_ara_summary, portfolio_mod_summary, repo_scores, repo_status, repo_errors, progress, repos_done, repos_total, status`.

### Three on-disk locations — know which one has what

`report_paths` points at the **thinnest** of the three. Measured on one 11-repo ARA run (`.md` / `.json` / `.html` / `.metadata.json` file counts):

| Location | md | json | html | meta | What it holds |
|---|---|---|---|---|---|
| `~/.atxct/shared/analyses/<id>/artifacts/<source>__<repo>/` (+ sibling `_portfolio_ara` / `_portfolio_mod`) | 12 | 1 | **0** | **0** | Per-analysis artifact store — **where `report_paths` points**. Effectively markdown-only. Plus `<id>/analysis.json`. |
| `~/.atxct/sources/<src>/<type>/runs/<id>/` | 12 | **13** | **1** | **1** | **Source-scoped run history — the only COMPLETE copy.** Where `portfolio_summary.report_path` points. Also holds the generated `.atx-config-*.yaml` per repo. |
| the repo working tree (local sources only) | ✓ | ✓ | ✓ | ✓ | Full per-repo bundle written into `services/<repo>/{agentic-readiness,modernization-readiness}-analysis/`. **Per-repo only — never portfolio.** |

Inside the `sources/` run tree:

```
~/.atxct/sources/<src>/<type>/runs/<id>/
├── <source>-<repo>-<16hex>/<type>-analysis/<repo>-{ara,mod}-report.{md,json}
└── portfolio-<name>/<type>-analysis/<name>-portfolio-{ara,mod}-report.{md,json,html,metadata.json}
```

Three traps in that layout:

- **`<type>` is the SOURCE's analysis root, not the run's type.** A `modernization-readiness` run's output sits under `sources/<src>/agentic-readiness/runs/<id>/` — verified: the MOD run `01KZ4DCZ…` wrote `.../agentic-readiness/runs/01KZ4DCZ…/<repo>/modernization-readiness-analysis/`. Do not build the path from the analysis type; glob `sources/*/*/runs/<id>/` or read `portfolio_summary.report_path`.
- **Per-repo dirs here are slug-mangled** (`<source>-<repo>-<16hex>`, a sha256 prefix), unlike the `<source>__<repo>` form in `shared/analyses/`. Glob, don't construct.
- **HTML and portfolio JSON exist ONLY here.** Not in `shared/analyses/`, and not in any working tree — no repo owns portfolio output. So "there is no HTML/JSON" is almost always a wrong-directory error, not a missing artifact. `find ~/.atxct -name '<name>-portfolio-*-report.html'` settles it.

Also: `~/.atxct/sources/<src>/{config.json,repos/index.json}`, `~/.atxct/shared/analyses/index.json`, and a `<type>/latest` symlink.

**Provider affects only the working-tree copy:**
- **Remote (GitHub) sources:** nothing is committed to the repos — no branch, no files. `ct` only touches repo git during a **remediation** (branch + PR). Both `~/.atxct` trees are still written.
- **Local sources:** analyses ALSO write the full per-repo bundle into each working tree (including HTML). ⚠️ Those files make the worktree dirty, which **blocks subsequent remediation** ("has uncommitted changes") — clean `services/` before remediating.

**So: do not hardcode formats, and do not treat `report_paths` as complete.** It is markdown-only in practice. To get a `.json` (what the EBA TD and every downstream tool consume) or an `.html` (what you open in a browser for a demo), go to the `sources/` run tree — for portfolio artifacts that is the *only* copy. Render with `pandoc` only after confirming the HTML genuinely isn't there.

```bash
# The reliable way to find every artifact of a run, regardless of type or slug mangling:
find ~/.atxct/sources -path "*runs/<analysis-id>/*" -type f \( -name '*.md' -o -name '*.json' -o -name '*.html' \)

# Portfolio bundle for one run (html + json live here and nowhere else):
ls ~/.atxct/sources/*/*/runs/<analysis-id>/portfolio-*/*-analysis/
```

⚠️ **`ct` auto-commits report bundles into local-source repos.** Each analysis lands its own commit (authored `ATX Bot <checkpoint@atx.bot>`) in the fixture/repo working tree. Two consequences: a tree can look clean right after an analysis because the output was *committed*, not because nothing was written; and a repo mid-analysis has those files modified, which trips the remediation dirty-worktree guard until the run finishes.

**Finding counts differ between the CLI and the report JSON — by design.** The report splits `findings[]` (severity-bearing gaps) from `evaluations[]` (passing questions, `status: pass`, no severity). The CLI's `findings count` includes both; the report's `counts.total` does not. Measured on one ARA: `counts.total: 36` vs CLI `43`, with disjoint `question_id` sets that union to exactly 43. Don't write an assertion that expects those two numbers to match.

### Zero-findings bug (3.7.0)

On 3.7.0 an analysis can report `complete` while contributing **zero findings** — this account currently shows 29 complete analyses and `findings: 0`. Symptoms:

```bash
atx ct status --json          # "analyses": {"complete": 29}, "findings": 0
atx ct findings list --json   # []
atx ct findings count --by severity --json   # {"groups": [], "total_count": 0}
```

The tell is in `analysis get --json`: `repo_errors` says `"No report generated"` for a repo while `repo_status` says `"done"` and `repo_scores` still reports a tier and `blocker_count: 0` — **a score fabricated from a missing report.** Root cause is a parser fallback: when a report's `categories` field is emitted as a JSON array (a shape the TD now produces), `parseModReport` fails to find a top-level `findings[]`, falls back to markdown, and yields nothing.

**Fix: upgrade to ≥ 3.9.0**, which recovers findings from all report shapes. **There is no `atx update` subcommand** (an earlier revision of this doc claimed there was — `atx update --help` just prints top-level help). Re-run the installer, which resolves `latest` from `index.json`:

```bash
curl -fsSL https://transform-cli.awsstatic.com/install.sh | bash
```

That is a write operation — get the user's go-ahead. Upgrading is non-destructive to `ct` state: sources, repos, and analyses all survive (verified across a 3.7.0 → 3.9.0 upgrade).

**Verified fixed on 3.9.0** (2026-08-03): a single-repo ARA on a fixture produced **43 findings** (10 high / 14 medium / 19 low — exactly the 43 ARA questions, split across all 8 categories), and MOD on the same repo produced **31**. Both analyses reached `complete` with `repo_errors: {}`.

**Partial self-heal:** an internal `repairMissingReports` runs automatically inside `getAnalysis()` and `listAnalyses()` — so simply running `atx ct analysis get --id <id>` may repair an analysis. It only handles `agentic-readiness`/`modernization-readiness`, only entries whose error is exactly `"No report generated"`, and only when it can *find* a report on disk to copy in. **It cannot help when the report was never written** — which is this account's case. There is no CLI command to trigger it directly.

## Hosted web Console

AWS Transform has a **hosted web Console — "Continuous modernization"** — with tabs **Dashboard / Findings / Remediations / Analyses / Sources / Settings**. It reads the same account-scoped data (`ct` CLI and Console show the same sources, analyses, findings, remediations live). Best "show the audience" surface — prefer it over exporting reports for demos. There is no local web UI: analyses run in-process, and the deprecated `:8081` daemon serves an API, not a page.

The console's **Run new analysis** wizard offers *Infrastructure* (**AWS managed — "Coming soon"**, or **Customer owned** → pick a deployed stack) and *Schedule* (**Run once** / **Recurring**). So today remote execution always runs on a stack you deployed yourself via `atx ct remote provision`.

**Console vs CLI — where they differ in capability:**

| Task | Console | CLI |
|---|---|---|
| Browse findings/analyses, demo | ✅ best | workable |
| Run analysis on an **SCM** source | ✅ | ✅ |
| Run analysis on a **`local`** source remotely | ❌ **fails** — no upload step (see below) | ✅ auto-bundles to S3 |
| ARA/MODA steering (`--context`, `--prefer`, …) | ❌ not exposed | ✅ |
| Recurring schedules | ✅ *Recurring* | ✅ `schedule create` (hidden) |

Neither surface is a superset. Reach for the CLI whenever a `local` source or steering is involved.

## Agent behavior: long-running analysis

Analyses take **5–15 minutes per repo** (large repos 20–30 min). Handle gracefully:

1. **Inform the user immediately** after launching: "Running ARA across N repos — ~5–15 min per repo. I'll monitor and report when done."
2. **Prefer polling over `--wait`** in agent workflows. `--wait` does exist (see below), but blocking a single tool call for 45 minutes gives the user no progress signal and risks a timeout. Launch without it, then poll.
3. **Poll autonomously** with `atx ct analysis get --id <id>` every 30–60s. Don't ask the user to wait.
4. **On completion**, report a summary (finding count, severity distribution, repos analyzed) — and **check `repo_errors`**, since `complete` does not mean every repo produced a report.
5. **On failure**, report the error and next steps (`references/troubleshooting.md`).

```bash
atx ct analysis run --type agentic-readiness --source my-portfolio   # returns immediately with an ID
atx ct analysis get --id <analysis-id>                               # running | complete | failed
atx ct findings count --by severity --json                           # cheap server-side aggregation
```

> **`--wait` exists but is hidden.** It is registered with `.hideHelp()` on **`analysis run`, `remediation create`, `remediation retry`**, so it shows up in neither `--help` nor `atx ct schema` — but it parses and works. Verified by differential test: `analysis run --type agentic-readiness --wait` advances to the *next* validation error (`At least one of --repo or --source is required`), whereas an unknown flag yields `error: unknown option`. Note that testing `--wait` *without* `--type` is inconclusive — the missing-required-option check fires first and produces the same message for any flag.
>
> Its own description: *"Block until the analysis completes, printing status as it runs. Without it, the command starts the analysis and returns immediately."* For `remediation create` the bundle adds: *"Opt-in for now; blocking will not become the default until a later release."* Use it in scripts/CI where a blocking call is fine; poll in interactive agent work. The harness `run-fixtures.sh` polls.
>
> Two further hidden subcommands exist for remote Batch — `analysis execute --id <id> [--wait] [--wait-timeout <min>]` and `remediation execute ...` (default timeout 240 min). These are **internal execute-only phases; do not invoke them directly.** By contrast `remote status --wait` is visible and normal (EC2 only).

**Polling in a background shell script:** the OS shell here is **zsh**, where `$status` is a **read-only reserved variable** — a loop that does `status=$(...)` fails with "read-only variable: status". Use a different name (`st=$(...)`). Verified 2026-07.

## Operational gotchas (verified 2026-07)

Confirmed behaviors that differ from naive expectation — save time by knowing these up front:

- **JSON field names are terse and not always obvious. Inspect before scripting:**
  - `source list --json` → each object uses `.source` (NOT `.name`) plus `.provider`, `.identifier`.
  - `repository list --json` → paginated envelope `{ items, nextToken, total }` — repos are under `.items[]` (NOT a top-level array), keyed by `.slug` and `.source`. **The key is `nextToken`, not `next_cursor`** (verified 2026-08-03). Item keys: `archived, assessed, created_at, created_by, default_branch, full_name, has_workflow, id, labels, language, private, schema_version, slug, source, updated_at`.
  - `findings list --json` → top-level array; auto-fix indicator is `.fix` (currently always `null` for ARA/MODA).
- **Pagination:** pass `--next-token <token>` (matching the response's `nextToken`) on `source list`, `repository list`, `analysis list`, `findings list`, `remediation list`. **There is no `--max-results`/`--limit` on the CLI** — only the MCP `repository_list` tool has a `limit`. Caveat: `repository list` pagination is *"only supported with a single --source."*
- **Prefer `findings count --by severity|repo|analysis-type`** over listing-then-counting — it aggregates server-side and is far cheaper on large portfolios.
- **Teardown ordering (reverse of creation):** you CANNOT remove a source that still has repos (HTTP 409 "has repositories that still reference it"). Order: **delete repositories → delete findings → remove source.** `analysis delete --cascade-findings` removes an analysis's findings, but repos discovered under a source persist until explicitly deleted.
- **Findings can only be deleted when `dismissed` or `obsolete`.** To purge `open` findings: `findings batch-update --ids <csv> --status dismissed --reason "..."` first, then `findings delete --id <id>` per finding (no batch delete).
- **`source remove` and per-item deletes exit 0 even when they no-op** (e.g. swallowed 409). Always re-list and verify counts afterward; don't trust exit codes alone.
- **Bulk deletes are slow** (sequential per-item API calls; ~1–2 s each). For dozens/hundreds of items, run the loop as a background Bash task and poll live counts, not the buffered output.
- **`custom def get` writes files into CWD** — run it from a scratch dir or clean up afterward.
- **Never invoke a bare `atx ct server`.** It is hidden and deprecated but still functional: it starts a real daemon on `:8081` and **blocks your shell** until killed (this caused a 2-minute tool timeout during verification). It prints its own warning: *"`atx ct server` is deprecated and no longer required for `atx ct` commands, which run directly in-process."*
- **Amazon Code Defender blocks `git push` to unapproved PUBLIC GitHub repos** — both from a local terminal AND from the `ct` remediation server-side push. The fix is `git-defender self-attest --reason 1 --url "https://github.com/<org>/<repo>.git"` for each repo. Do this BEFORE running remediation; the setup harness handles it automatically.
- **`PYENV_VERSION=system` for git pushes** on machines where pyenv's Python (3.13.2) has a broken `hashlib` (blake2b/blake2s `ValueError`). The system Python (3.9.6+) works. Without this, `git push` during remediation fails with a cryptic Python traceback — the root cause of "remediation failed to push branch". Historically applied when starting the server; now that execution is in-process, export it in the environment running `atx ct`. The harness scripts handle this.
- **Pipe-stdin consumption in loops:** when iterating over `atx ct repository list --json | jq ... | while read ...`, the `atx` CLI can consume the pipe's stdin and terminate the loop after one item. Fix: capture the output into a variable first, then `while read ... <<< "$variable"`. The harness scripts use this pattern.

## Guided workflow (UX)

After each major step, offer 2–3 concrete next actions, most valuable first — teach continuous modernization through progressive disclosure. Never leave the user at a dead end.

- **After discovery:** "Discovered N repos. Run Agentic Readiness (ARA), Modernization Readiness (MODA), or both?"
- **After ARA:** offer to run MODA, show high-severity findings, or generate a per-repo report.
- **After MODA:** offer execution plan, findings by severity/category, remediation of auto-fixable findings, or the portfolio report.
- **After both ARA+MODA:** recommend the execution plan (dependency-aware phased roadmap).
- **After EBA:** offer to summarize phases/timeline, show quick wins, or open the full plan.
- **After findings listed:** offer remediations, dismissals, or category/repo filters.

## Safety contract: Execution Plan (EBA)

Built-in ARA/MODA reject `-g`, but they are **not** uncontextualizable — use the [steering flags](#steering-ara--moda-without-a-custom-td) (`--context`, `--agent-scope`, `--prefer`, `--avoid`). The Execution Plan is the ONE analysis **Claude generates**: it builds `atx-config-exec-plan.yaml` with `additionalPlanContext` from `ct` data + user execution constraints, then runs it. See `references/execution-plan.md` for the full interactive flow.

1. **EBA runs ONLY AFTER both ARA and MODA show status `complete`** (verify via `atx ct analysis list`).
2. **Verify the reports actually exist** — `complete` is not sufficient (see [Zero-findings bug](#zero-findings-bug-370)). Check `analysis get --id <id> --json` for populated `report_paths` and an empty `repo_errors`, then confirm the files are on disk.
3. **Issue exactly one Bash call** for the EBA command with `timeout: 1800000` ms. Do not poll, background, or split it.
4. **Do NOT run EBA concurrently with any `atx ct analysis run`** — `ct` and custom exec conflict on git state.
5. **After it returns, verify the execution plan artifact exists** (`ls portfolio-execution-plan/*-portfolio-exec-plan.md`) before reporting success.

## MCP integration (alternative to CLI)

`atx ct mcp` exposes **25 tools** (verified 2026-08-03 via a live stdio `initialize` + `tools/list` handshake; `serverInfo.name = "atxct"`). An earlier revision claimed 41 tools and a "richer surface: tags, schedules, dashboards" — **that was backwards.** MCP is a strict *subset* of the CLI.

```
source_{add,list,get,remove,update}   discovery_scan
analysis_{run,get,list,cancel,delete} findings_{list,count,get,update,delete}
repository_{list,get,delete}          remediation_{create,status,list,cancel,retry,delete}
```

**Absent from MCP** — use the CLI for these: `findings batch-update`, `repository update`, `setup`, `status`, the entire `remote` group, the entire `schedule` group, and the ARA/MODA steering flags. EBA also requires the CLI (`atx custom def exec` is not an MCP tool). MCP is still the cleaner path for structured read/query work.

```bash
atx ct mcp                                # stdio (local agent integration)
atx ct mcp --transport http --port 3100   # HTTP
```

Add to `.claude/settings.json` (or `.mcp.json`):

```json
{
  "mcpServers": {
    "atxct": { "command": "atx", "args": ["ct", "mcp"], "env": { "AWS_PROFILE": "your-profile", "AWS_REGION": "us-east-1" } }
  }
}
```

MCP vs CLI differences (local source `provider_config.rootPath` vs `--path`; remote `identifier`/`token` vs `--org`/`--token`; `assessment_type` vs `--type`; agent polls `analysis/get` instead of `--wait`) are covered in `references/ct-workflow.md`.

## Authoring a custom remediation TD (Dockerfile/K8s, upgrades, etc.)

ARA/MODA findings are **assessment-only** — verified 2026-07 that every finding has `fix: null` and no `fix-transform`/metadata fix field, so the `remediation create --ids` path (which binds a finding to its own fix transform) has nothing to bind to. To auto-remediate, author your OWN transformation definition and run it against a repo with `remediation create --transformation-name`.

**TD source-directory schema** (from the `atx` binary's `SEGFileManager` / `DEFAULT_SCHEMA`):

```
my-td/
├── transformation_definition.md   # REQUIRED — the instructions the agent follows
├── summaries.md                    # optional — short summary
└── document_references/            # optional — supporting docs
```

`transformation_definition.md` is a natural-language spec: purpose, scope (exact files to generate/modify), how to analyze the repo, per-artifact requirements, PR body contents, and guardrails (e.g. "additive only, never overwrite, no real secrets"). Keep the change set small and reviewable.

**Save → publish → run:**

```bash
# Draft (temporary, ~30-day expiry) — good for iterating
AWS_REGION=us-east-1 atx custom def save-draft -n my-td --sd ./my-td --description "..."

# Publish (permanent registry entry) — required for remediation to reference it
AWS_REGION=us-east-1 atx custom def publish   -n my-td --sd ./my-td --description "..."

# Verify (registry has AWS-managed + user TDs; ours are user TDs)
AWS_REGION=us-east-1 atx custom def list          # pretty table, count summary
AWS_REGION=us-east-1 atx custom def get -n my-td  # NOTE: writes the TD files into CWD ('.')

# Run as a remediation → opens a PR on GitHub/GitLab/Bitbucket sources (local branch for local)
atx ct remediation create --repo <src>::<repo> --source <src> --transformation-name my-td --name "..."
atx ct remediation status --id <remediation-id>   # includes PR/MR link
```

> **`atx custom def *` needs `AWS_REGION` set explicitly** even when `atx ct` works fine — otherwise it errors "AWS Transform is not available in region 'us-west-2'". Prefix with `AWS_REGION=us-east-1` (or export it). `atx ct` reads region from AWS config; `atx custom def` does not.
> **`atx custom def get` writes the fetched TD files into the current directory** — run it from a scratch dir or clean up afterward.

> **⚠️ CRITICAL — `ct remediation` could NOT resolve a user-published custom TD. Re-confirmed on 3.9.0 (2026-08-03).** A `containerize-service` TD published and visible via `atx custom def list`/`get` (us-east-1) failed in `remediation create --transformation-name` with *"Transformation 'containerize-service' not found in the registry. Did you mean … containerize-to-eks?"* — even after restarting the `ct` server in the same region. The remediation runtime resolves TDs from a **different catalog than the CLI**: it surfaced `containerize-to-eks` (an AWS-**managed** transform that does NOT appear in `atx custom def list`) but not our user TD. The split is now demonstrated in both directions: `atx custom def exec -n containerize-service` runs the user TD fine, and `remediation create --transformation-name containerize-to-eks` succeeds while the reverse of each fails. Practical implications:
> - **Do NOT assume `ct remediation` can run an arbitrary user-published TD.** In this environment it only resolved **AWS-managed** transforms.
> - **For containerization remediation, prefer the managed `containerize-to-eks`** (generates container + EKS/K8s resources targeting EC2 managed node groups) — it's what the runtime actually resolves. Check `atx custom def list` for other `AWS/*` managed transforms (version-upgrades, SDK migrations, etc.).
> - **To run YOUR custom TD and still get a PR**, run it locally with `atx custom def exec -n <td> -p <repo> -x -t` to generate the changes, then open the PR yourself with `gh` (note: local `git push` to public GitHub may hit Amazon Code Defender — push from an approved terminal).
> - This may be an account/allowlist/propagation limitation rather than a hard product rule; re-test as the service evolves. But don't build a demo/workflow on custom-TD remediation without confirming resolution first with a throwaway run.

**Working end-to-end example (verified 3.9.0, 2026-08-03).** `containerize-to-eks` on a containerized Node fixture completed and committed its own change:

```bash
atx ct remediation create --transformation-name containerize-to-eks \
  --repo <src>::legacy-shipping-api --name test-containerize-eks
# → Remediating with 20 concurrent slot(s) (remote mode)...
# → status: completed   (~5 min)
```

It committed as `ATX Bot <checkpoint@atx.bot>`: *"Fix Dockerfile HEALTHCHECK to use reliable TCP connectivity check via Node.js net module instead of wget --spider which fails on HTTP 401…"* — a 2-line Dockerfile edit. Two lessons: the TD **adapts to an already-containerized repo** rather than no-opping or regenerating scaffolding, and its change set can be far smaller than the finding implies (the MOD `INF-Q1` gap was missing EKS IaC, which this did *not* address). Don't assume a remediation resolved the finding that motivated it — re-analyze and diff.

⚠️ **Remediation refuses to run against a repo with a dirty worktree**, and a repo being analyzed right now *is* dirty (`ct` rewrites its report bundle in place). Error: *"Local repository at … has uncommitted changes. Commit or stash them before running remediation."* Don't "fix" this by committing mid-analysis — you'd be racing the writer. Either wait for the analysis to finish, or test against an isolated copy of the fixture registered as its own source.

## Full CLI reference (condensed)

Enumerated live on 3.9.0 (2026-08-03). `atx ct --help` reports **11 groups**; `schedule` and `server` exist but are hidden.

**Status:** `atx ct status [--health] [--json]` — in-process; do not start `server`
**Schema:** `atx ct schema` — JSON manifest, but **incomplete** (omits hidden commands/flags)
**Sources:** `atx ct source add|list|get|remove|update` (`get`/`update` need `--name`)
**Discovery:** `atx ct discovery scan --source <name> [--path <override>] [--json]`
**Repositories:** `atx ct repository list|get|update|delete` (filters: `--source --language --labels --has-workflow --json --next-token`)
**Analysis:** `atx ct analysis run|get|list|cancel|delete` — **no `list-artifacts`, no `get-artifact`** (removed; use `get --json` → `report_paths`)
**Findings:** `atx ct findings list|count|get|update|batch-update|delete` — **no `dismiss`** (removed; use `update --status dismissed`)
 · `list` filters: `--repo --source --severity --min-severity --type --status --analysis-id --fix-transform --next-token --json`
 · `--severity` and `--min-severity` are **mutually exclusive**; both take `low|medium|high`
 · `count --by severity|repo|analysis-type` — server-side aggregation, prefer for large portfolios
**Remediation:** `atx ct remediation create|list|status|retry|cancel|delete` (`create`/`retry` accept hidden `--wait`)
**Setup:** `atx ct setup <component> [--status] [--delete]` (e.g. `security-agent`)
**MCP:** `atx ct mcp [--transport stdio|http] [--port 3100]` — 25 tools
**Remote:** `atx ct remote analysis|remediation|status|detect|provision|update|credentials|teardown|cancel|network` — see below
**Schedule** *(hidden)*: `atx ct schedule create|list|get|enable|disable|delete|teardown` — see below

### Removed commands — delete on sight

| Removed | Replacement |
|---|---|
| `analysis list-artifacts` | `analysis get --id <id> --json` → `.report_paths` |
| `analysis get-artifact` | read the file at the `report_paths` path directly |
| `findings dismiss` | `findings update --id <id> --status dismissed --reason "..."` |

Verified by direct invocation (`error: unknown command`) — not merely absent from `--help`. Everything else our docs referenced still exists.

### `atx ct remote` — Batch / EC2 execution

Run analyses on AWS-hosted compute instead of your laptop. Infra is one CloudFormation stack.

```bash
atx ct remote network discover [--vpc <id>] [--json]     # find usable VPCs/subnets/SGs
atx ct remote network create [--cidr 10.1.0.0/16] [--tags k=v] [--json]   # VPC + NAT + egress SG
atx ct remote provision --mode batch --vpc <id> --subnets <csv> --securityGroup <id> \
  --suffix <s> [--job-timeout <sec>] [--execute]         # omit --execute to preview the template
atx ct remote analysis --mode batch --types agentic-readiness --sources my-src --stack-name <name>
atx ct remote status --batch <id> --stack-name <name> [--json]
atx ct remote detect --mode batch|ec2                    # {"status":"not_deployed"|...}
atx ct remote teardown --mode batch [--execute]
```

**Stack names** (literals): `AtxInfrastructureStack[-suffix]` (Batch), `atx-runner[-suffix]` (EC2, `--stack-name` must start with `atx-runner`), `atx-scheduler`, `AtxDispatcherStack`, `AtxSecurityAgentStack-*`. Buckets: `atx-source-code-<acct>`, `atx-ct-output-<acct>`, `atx-custom-output-<acct>`.

**Mode-specific flags** — mixing them is a hard error:
- **Batch only:** `--securityGroup` (*required*), `--job-timeout <60..604800>` (default 43200 = 12h), `--resume`, `--batch <id>` on `status`. `remote status` needs `--stack-name` for Batch.
- **EC2 only:** `--workers 1-5`, `--instance-type`, `--volume-size`, `--existing-instance <id>`, `--group <id>` and `--wait` on `status`. `--securityGroup` optional (auto-creates a no-inbound SG, SSM access).

**Network prerequisites** (the console modal states these; all are load-bearing): private subnets only, no public IP, egress reaching the internet via **NAT gateway or VPC endpoints**, and `enableDnsSupport` + `enableDnsHostnames` on the VPC.

#### ⚠️ Local sources on remote compute — use the CLI, not the console

Remote jobs run in AWS, so a `--provider local` source pointing at a path on your laptop is **unreachable from the job**. The source directory must be zipped and uploaded to S3 first. Launching a local-provider analysis from the **web console** fails with:

```
Could not start analysis: local provider requires localBundleName and
sourceBucketName for repo <source>::<repo>
```

**The console has no upload step, so it cannot satisfy this — the CLI can.** `atx ct remote analysis` bundles the source directory (it embeds `archiver` and multipart-uploads to S3) and passes `localBundleName` + `sourceBucketName` through to the job for you:

```bash
atx ct remote analysis --mode batch \
  --types agentic-readiness \
  --sources harness-portfolio \
  --stack-name AtxInfrastructureStack-<suffix>
```

The job then reconstructs the tree inside the container:
```bash
aws s3 cp s3://<source-bucket>/repos/<bundle>.zip /tmp/ && unzip -q -o ... -d /home/atxuser/repos/
atx ct discovery scan --source <name> --path /home/atxuser/repos
```

Notes:
- The bundle is a **point-in-time snapshot**. Re-run `remote analysis` after editing fixtures, or the job analyzes stale code. Same caveat applies to `schedule create --provider local`, where the zip is uploaded once at create time and **every subsequent fire analyzes that same snapshot**.
- Default bucket is `atx-source-code-<accountId>-<stackSuffix>`, created by the stack (resolve the real name with `atx ct remote detect --mode batch`). `--source-bucket` overrides it and is *required* for local sources on the EC2 `--existing-instance` path.
- **For SCM providers (github/gitlab/bitbucket) none of this applies** — the job clones directly using staged credentials, and the console path works fine.
- Prefer an SCM source for anything recurring; local + remote is best for one-off runs over fixtures.

⚠️ **`network discover` does not validate egress.** It happily reports subnets whose `0.0.0.0/0` route points at a **deleted** NAT gateway (route state `blackhole`). The stack then deploys `CREATE_COMPLETE` and every job hangs with no egress. Verified 2026-08-03 on this account. Always check before provisioning:
```bash
aws ec2 describe-route-tables --filters "Name=association.subnet-id,Values=<subnet>" \
  --query 'RouteTables[].Routes[].[DestinationCidrBlock,NatGatewayId,State]' --output text
# the 0.0.0.0/0 row MUST say "active", not "blackhole"
```
When in doubt, `atx ct remote network create` builds a known-good VPC (~$32/mo for the NAT, billed idle). It also creates a **public** subnet to host the NAT — do **not** pass that one to `provision`; use `privateSubnetIds` only.

All mutating `remote` operations are gated behind `--execute`; `--ack` suppresses the admin-permissions prompt (prefer answering the prompt).

### `atx ct schedule` — recurring runs (hidden group)

EventBridge Scheduler, in a group named **`atx-ct`**.

```bash
atx ct schedule create --name nightly-ara --mode batch --job-type analysis \
  --types agentic-readiness --sources my-src \
  --recurrence daily --timezone America/Los_Angeles
atx ct schedule list|get|enable|disable|delete [--name <n>]
atx ct schedule teardown [--execute]
```

- ⚠️ **Breaking change in 3.8.0+ — verified on 3.9.0: `--expression` is GONE and `--recurrence` is now `(required)`.** It takes `daily | weekly:<MONDAY..SUNDAY> | monthly:<1..28>`; raw `cron(...)`/`at(...)` expressions are no longer accepted. Any 3.7.0-era script passing `--expression` will fail. Note the fire time is **not** configurable to the minute: per its own help, it "resolves to about 2 minutes from now (local wall clock, DST-stable)" — so a schedule named `nightly-*` won't necessarily run at night.
- `remote provision` also gained `--existing-scheduler-role-arn` and `--existing-instance-profile-name` for reusing pre-created IAM.
- **There is no `schedule setup`.** Scheduler infra is provisioned by `remote provision`, which ensures the `atx-scheduler` stack alongside the compute stack (`--skip-scheduler` opts out). Only `schedule teardown` remains.
- `--provider` defaults to `github`; with `local` it zips and uploads the source directory at create time, so **every fire analyzes that uploaded snapshot**, not your current working tree.
- Job flags mirror `remote analysis`/`remote remediation`. Note `-g` here is gated on `--transformation-name`, not `--type custom`.

Exact flags and examples for the core commands are in `references/ct-workflow.md` — but see the staleness warning above.
