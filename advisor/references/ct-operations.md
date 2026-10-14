# Continuous Modernization Operations

The CLI mechanics of `atx ct`: sources, discovery, running analyses, findings, reports and their three on-disk locations, remediation, remote compute, schedules, and teardown. Read this when you are executing rather than advising.

Baseline: `atx` 3.18.0. A handful of features below carry a minimum-version note where the feature genuinely requires one; everything untagged works on any recent CLI.

---

## Pre-flight

```bash
aws sts get-caller-identity                                  # credentials resolve
export AWS_REGION=us-east-1 AWS_DEFAULT_REGION=us-east-1      # see below
atx ct status --health                                        # prints healthy | unhealthy
```

⚠️ **Only `us-east-1` resolves.** A stray `AWS_REGION=us-west-2` makes the definition and credential endpoint fail to resolve at all (NXDOMAIN on `transform-custom.us-west-2.api.aws`), so the failure can surface as a DNS error rather than a clean "not available" message. Set both variables explicitly rather than relying on a profile default.

**No server process is needed** — `atx ct` runs in-process, and `atx ct status --health` is an in-process check rather than a daemon ping. **Never run `atx ct server`**: it is deprecated, starts a real daemon, and blocks the shell until killed. "Server not running" is never a valid diagnosis for an `atx ct` failure.

---

## 1. Sources

Local sources use `--path` — a **parent directory** whose subdirectories are the repositories, always absolute. SCM providers use `--org` + `--token`.

```bash
atx ct source add --name x --provider local      --path /absolute/path/to/parent-dir
atx ct source add --name x --provider github     --org my-org       --token <pat>   # repo scope
atx ct source add --name x --provider gitlab     --org my-group     --token <pat> [--url https://gitlab.example.com]   # api scope
atx ct source add --name x --provider bitbucket  --org my-workspace --token <pat> [--username u] [--email e@example.com]

atx ct source list [--json]
atx ct source get    --name x
atx ct source update --name x --token <new-pat>   # rotate; stored locally and in AWS Secrets Manager
atx ct source remove --name x
```

**Do not point a local source at a single repository** — point at the directory *containing* repositories. The scanner looks for child directories with a `.git` folder.

```
✅ --path /home/user/services          (services/repo-a/.git, services/repo-b/.git)
❌ --path ./services                   (relative — may break if the CWD differs later)
❌ --path /home/user/services/repo-a   (this is a repository, not a parent of repositories)
```

The source name becomes the source half of every repository slug (`<source>::<repo>`), and it is account-scoped.

A source showing `SETUP_REQUIRED` means the source exists in the account but credentials are not configured on this machine — re-add it. `AUTH_REQUIRED` means the token is invalid or expired — re-add with a fresh token. Token scopes: GitHub needs `repo` (classic PAT), GitLab needs `api`, Bitbucket needs read for discovery and write for remediation.

### Commit and branch conventions *(requires atx >= 3.16)*

Some repositories reject pushes that do not match a required commit-message or branch-name shape. Record the convention on the source and remediation commits are written to match instead of being rejected at push.

```bash
atx ct source add    --name x --provider github --org o --token <pat> \
    --commit-message-template "<fmt>" --branch-name-template "<fmt>" \
    --git-committer-name "<name>" --git-committer-email "<email>"
atx ct source update --name x [--token <pat>] [--commit-message-template ...] [--branch-name-template ...]
```

`--git-committer-name` and `--git-committer-email` are required together; pass an empty string to clear any of them. `source update` does not require `--token`, so the conventions can be set from any machine.

---

## 2. Discovery and repositories

```bash
atx ct discovery scan --source my-portfolio [--path /different/path] [--json]
atx ct repository list [--source <n>] [--language <l>] [--has-workflow true|false] [--labels <csv>] [--next-token <t>] [--json]
atx ct repository get    --repo <slug> --source <n>
atx ct repository update --source <n> [--repo <csv>] --labels <csv>   # omit --repo for all repos under the source
atx ct repository delete --repo <slug> --source <n>
```

Labels are the grouping mechanism for targeted runs: set them with `repository update`, then select with `--labels` on `remote analysis` or `schedule create`. **`--labels` filters use AND semantics.** Pass an empty string to clear.

For a `local` source, a subdirectory without `.git` is still discovered, and a git repository is initialized in it on first remediation.

---

## 3. Running an analysis

```bash
# Launch without --wait (returns immediately with an analysis id)
atx ct analysis run --type agentic-readiness --source my-portfolio
atx ct analysis run --type modernization-readiness --source my-portfolio

# Target specific repos (--repos is an alias for --repo; both are repeatable AND comma-separated, unioned)
atx ct analysis run --type agentic-readiness --repo my-portfolio::my-app --source my-portfolio
```

Also available: `--display-name <name>` (the human-readable label in `analysis get`/`list`), `--tags k=v,...`, `--telemetry k=v,...`.

**`-g`/`--configuration` on `analysis run` requires `--type custom`** — built-in types reject it. This is not a blanket rule: on `remediation create`, `remote analysis`, `remote remediation` and `schedule create` the gate is `--transformation-name` instead. To steer the built-in analyses, use the steering flags.

Running a custom definition as an analysis:

```bash
atx ct analysis run --type custom --transformation-name my-td --source my-portfolio \
  -g "additionalPlanContext=Target Java 17,buildCommand=mvn clean test"
atx ct analysis run --type custom --transformation-name my-td --source my-portfolio -g file://my-config.yaml
```

**The definition must have been published with `--category analysis`**, or `ct` refuses the name here even though `atx custom def list` shows it: *"Transformation definition "my-td" has no category, so it can't be used for a custom analysis. Publish it with --category analysis to use it here."* The remediation path gates the same way on `--category remediation`. See [`td-catalog.md` §0](td-catalog.md#0-what-you-need-on-disk).

### Timing and concurrency

Analyses take **5–15 minutes per repository** (large repositories 20–30 min). **The per-repo phase runs concurrently** — wall clock is roughly the slowest repository plus the portfolio phase, not repositories × per-repo time; an 11-repo ARA had eight repositories in flight within about two minutes. `ATXCT_MAX_CONCURRENT_DEEP_SCANS` (default 1) gates only `tech-debt-comprehensive` and does **not** throttle the readiness analyses. An `ALREADY_RUNNING` guard rejects a run whose repositories are mid-analysis for the same type.

In agent workflows:

1. **Tell the user immediately** after launching: "Running across N repos — about 5–15 min per repo. I'll monitor and report when done."
2. **Poll rather than block.** `--wait` exists on `analysis run`, `remediation create` and `remediation retry` — it is hidden from `--help`, so an absent help entry is not evidence against it. Use it in scripts and CI; poll in interactive work, where blocking one tool call for 45 minutes gives no progress signal and risks a timeout.
3. **Poll autonomously** every 30–60s. Do not make the user ask.
4. **On completion**, report finding count, severity distribution, repositories analyzed — and **read `repo_errors`**, because `complete` does not mean every repository produced a report.
5. **If an analysis is genuinely stuck** past about 40 minutes with no progress, `atx ct analysis cancel --id <id>` and re-run. Check §4 first: "no reports" usually means the portfolio phase is still running.

> While a run is in flight, `repos_done` and `repos_total` read `null`. They are not a progress bar, and an agent watching them will conclude the run never started.

### ⚠️ `status: complete` is not a terminal signal on a multi-repo run

`status` flips to `complete` (and `completed_at` is stamped) when the **per-repo phase** finishes, while the **portfolio phase is still running** — for tens of minutes.

| Field | At premature `complete` | At true completion |
|---|---|---|
| `status` | `complete` | `complete` / `failed` |
| `report_paths` | `{}` (0 entries) | 12 entries |
| `portfolio_ara_summary` | `null` | populated |
| `progress` | `{"done": 0, "total": 11}` | — |

Measured: `status: complete` with `completed_at: 20:27:42Z`, yet at 20:37 the launching process was still alive and still logging `Still analyzing portfolio-<name>... (7m elapsed)`. An agent that stops at `status` reports **0 findings and no reports** on a run that had in fact produced 899 findings and a full portfolio bundle.

Wait on one of these instead:

- **If you launched the run, wait for the process to exit.** The only unambiguous signal.
- **Otherwise require `status` terminal *and* `report_paths` non-empty.** That map is written in the final record update, so it is empty for the whole premature window. **Cap it with a timeout** — a run that fails early leaves `report_paths` empty forever.

```bash
# Terminal check that does not fire early
atx ct analysis get --id <analysis-id> --json \
  | jq -e '.status as $s | (.report_paths // {} | length) as $n
           | if ($s == "running") then false
             elif $n > 0 then true
             else false end'   # exit 0 = genuinely done
```

Because `status` is already terminal, **a portfolio-phase error cannot transition it**, so `status: complete` does not imply `error: null`. Read `error` and `repo_errors` explicitly; never infer them from `status`. And never conclude "no reports were generated" from an empty `report_paths` alone — check disk first.

```bash
atx ct analysis get --id <id> --json | jq '{status, error, repo_errors}'
```

**Polling in a shell loop:** the shell here is zsh, where `$status` is a **read-only reserved variable**. `status=$(...)` fails with `read-only variable: status` — use another name (`st=$(...)`).

### Portfolio aggregation needs ≥ 2 repositories

Both portfolio definitions are managed and built into `ct`. There is **no standalone portfolio command** — the roll-up runs automatically as a second phase of `analysis run` and lands in `portfolio_ara_summary` / `portfolio_mod_summary` on the analysis record.

- **A single-repo run gets no portfolio report.** The CLI still invokes the portfolio definition, burns time before declining, logs `runPortfolioAra: no portfolio ARA report found`, and leaves the summary `null`. Expected on one repository — do not debug it.
- **Separate single-repo runs do not accumulate.** Aggregation covers only the repositories in one `analysis run`. Pass ≥ 2 repositories, or omit `--repo` to take every repository under `--source`.
- **The bridge phase needs BOTH portfolio reports.** `runBridge` populates `bridge_summary` and skips unless a portfolio ARA *and* a portfolio MOD report exist.

---

## 4. Reports on disk

```bash
atx ct analysis get --id <id> --json | jq -r '.report_paths | to_entries[] | "\(.key)\t\(.value.ara // .value.mod)"'
atx ct analysis list-artifacts --id <id> [--repo <repositoryId>] [--max-results 1-100] [--next-token <t>] [--json]
atx ct analysis get-artifact   --id <id> --artifact-id <aid> [--output <file>] [--force]
```

**`list-artifacts` and `get-artifact` are scoped to a managed-infrastructure analysis.** They list and download the artifacts *stored* for a run executed on AWS compute (`atx ct remote analysis`, §7); each artifact is one **per-repo bundle** (`<repo>/artifacts.zip`), and they materialize per-repo as each repository completes, so a mid-run listing can be partial. A **Local-mode run stores no artifacts**, so an empty listing there is expected, not a failure — glob the run tree, which works in every compute mode.

**Reports are on local disk, and `analysis get --json` tells you where.** `report_paths` maps each repository slug to its report file — but it is the **markdown-only view**. It is the right way to enumerate *which* repositories produced reports and the wrong way to reach a `.json` or `.html`.

`analysis list` returns a thinner object with no `report_paths`; call `get` per id. Useful `analysis get --json` keys: `report_paths`, `ara_results`, `mod_results`, `portfolio_summary`, `portfolio_ara_summary`, `portfolio_mod_summary`, `repo_scores`, `repo_status`, `repo_errors`, `progress`, `repos_done`, `repos_total`, `status`, `error`.

### Three on-disk locations — know which one has what

File counts from one 11-repo ARA run:

| Location | md | json | html | What it holds |
|---|---|---|---|---|
| `~/.atxct/shared/analyses/<id>/artifacts/<source>__<repo>/` | 12 | 1 | **0** | per-analysis artifact store — **where `report_paths` points.** Effectively markdown-only |
| `~/.atxct/sources/<src>/<type>/runs/<id>/` | 12 | **13** | **1** | **source-scoped run history — the only COMPLETE copy.** Where `portfolio_summary.report_path` points |
| the repository working tree (local sources only) | ✓ | ✓ | ✓ | full per-repo bundle. **Per-repo only — never portfolio** |

```
~/.atxct/sources/<src>/<type>/runs/<id>/
├── <source>-<repo>-<16hex>/<type>-analysis/<repo>-{ara,mod}-report.{md,json}
└── portfolio-<name>/<type>-analysis/<name>-portfolio-{ara,mod}-report.{md,json,html,metadata.json}
```

Three traps:

- **`<type>` is the SOURCE's analysis root, not the run's type.** A `modernization-readiness` run's output can sit under `sources/<src>/agentic-readiness/runs/<id>/`. Do not build the path from the analysis type — glob `sources/*/*/runs/<id>/`, or read `portfolio_summary.report_path`.
- **Per-repo directories here are slug-mangled** (`<source>-<repo>-<16hex>`, a sha256 prefix), unlike the `<source>__<repo>` form under `shared/analyses/`. Glob, do not construct.
- **HTML and portfolio JSON exist only here** — not in `shared/analyses/`, and not in any working tree, because no repository owns portfolio output.

```bash
# Every artifact of a run, regardless of type or slug mangling
find ~/.atxct/sources -path "*runs/<analysis-id>/*" -type f \( -name '*.md' -o -name '*.json' -o -name '*.html' \)

# Portfolio bundle for one run
ls ~/.atxct/sources/*/*/runs/<analysis-id>/portfolio-*/*-analysis/
```

### A missing portfolio bundle: check for absence before you assume misplacement

**Read the analysis record before you touch the filesystem.** The portfolio phase can terminate having written *no artifact at all*, with nothing in `repo_errors` — so a filesystem hunt looks for a file nothing ever wrote, and finding nothing proves nothing.

```bash
atx ct analysis get --id <id> --json \
  | jq '{status, portfolio_summary,
         pf: .repo_errors._portfolio_ara,
         pkeys: (.report_paths|keys|map(select(startswith("_"))))}'
```

Three steps, in this order:

1. **`_portfolio_ara` (or `_portfolio_mod`) populated** → the inner portfolio run **failed**, and its message is right there. That message is the bug; the path is not.
2. **`portfolio_summary: null`, no `_portfolio_*` key in `report_paths`, and nothing in `repo_errors`** → the portfolio phase **produced nothing**. This is not a path problem, and re-globbing will not find it. Re-run the portfolio phase (or confirm the run had ≥ 2 repositories — a single-repo run legitimately produces no portfolio report, §3).
3. **Only once those two are clean** is it a lookup problem — and then glob, because the type segment and the per-repo slugs are both unconstructible:

```bash
find ~/.atxct -name '*portfolio*-report.html'     # settles "does it exist anywhere" in one command
ls ~/.atxct/sources/*/*/runs/<analysis-id>/portfolio-*/*-analysis/
```

### Report kinds by analysis type

| Analysis type | Per-repo report key | Working-tree directory |
|---|---|---|
| `agentic-readiness` | `ara` | `services/<repo>/agentic-readiness-analysis/` |
| `modernization-readiness` | `mod` | `services/<repo>/modernization-readiness-analysis/` |
| `tech-debt-*` | `technical-debt-report/summary` | — |

**Provider affects only the working-tree copy.** For SCM sources nothing is committed to the repositories; `ct` touches repository git only during a remediation (branch + PR), and the reports still exist locally under `~/.atxct/`. For local sources, analyses **also** write the full per-repo bundle into each working tree, and `ct` **auto-commits** it, authored `ATX Bot <checkpoint@atx.bot>`. Two consequences: a tree can look clean right after an analysis because the output was *committed* rather than not written, and a repository mid-analysis has those files modified, which trips the remediation dirty-worktree guard until the run finishes.

```bash
git -C services/<repo> log --oneline --author=checkpoint@atx.bot -5
```

**Finding counts differ between the CLI and the report JSON, by design.** The report splits `findings[]` (severity-bearing gaps) from `evaluations[]` (passing questions, no severity). The CLI's `findings count` includes both; the report's `counts.total` does not. Measured on one ARA: `counts.total: 36` versus CLI `43`, with disjoint `question_id` sets that union to exactly 43. **Never assert those two numbers match.**

---

## 5. Findings

```bash
atx ct findings count --by severity|repo|analysis-type [--source <n>] [--repo <slug>] [--type <t>] [--status open|dismissed|obsolete] [--json]
atx ct findings list [--repo <n>] [--source <n>] [--severity low|medium|high] [--min-severity low|medium|high] \
                     [--type <t>] [--status open|dismissed|obsolete] [--analysis-id <id>] [--fix-transform <name>] [--next-token <t>] [--json]
atx ct findings get   --id <id>
atx ct findings update       --id  <id>  --status open|dismissed [--reason "..."] [--notes "..."]
atx ct findings batch-update --ids <csv> --status open|dismissed [--reason "..."]
atx ct findings delete --id <id>
```

Each finding carries a **severity** (high / medium / low), a **status** (open / dismissed / obsolete), the **type** that produced it, the **repository** as a slug, and `.fix` — the bound fix transform, always `null` for the readiness analyses.

- **`--severity` (exact) and `--min-severity` (threshold) are mutually exclusive.**
- **Prefer `findings count` over list-then-count** — it aggregates server-side and is far cheaper on large portfolios.
- **`--reason` is required when `--status dismissed`.**
- **Findings can only be deleted when `dismissed` or `obsolete`.** To purge open findings: `batch-update --status dismissed --reason "..."`, then `delete --id` per finding. **There is no batch delete.**
- **`findings dismiss` does not exist** — use `findings update --status dismissed --reason "..."`.

---

## 6. Remediation

```bash
atx ct remediation create --ids <csv> | --transformation-name <name> \
    [--repo <slug>] [--source <n>] [-g <config>] [--name <n>] [--slots <n>] [--local]
atx ct remediation list|status|retry|cancel|delete
```

Two modes, and which one applies depends on whether the findings carry a fix transform:

```bash
# (a) Finding-bound — ct maps each finding to its own fix transform
atx ct remediation create --ids finding-id-1,finding-id-2 --name "fix-batch-1"

# (b) Explicit-transform — run a chosen definition across a repository (findings just motivate it)
atx ct remediation create --repo my-portfolio::my-app --source my-portfolio \
  --transformation-name my-fix-td --name "containerize" [--local]
```

⚠️ **The readiness analyses' findings are never auto-remediable.** Every finding ARA and MOD emit has `fix: null`, and `remediation create --ids` rejects them with `non_remediable=[...]`. This is not a data problem with your particular findings — mode (a) only works for analysis types whose findings ship a bound fix transform. Remediation of readiness output must go through mode (b).

`--slots` caps concurrent repositories (default 20). `-g` is valid only with `--transformation-name`. `--local` runs the transform in-process against the checked-out working tree rather than delegating to the provider; useful for local sources.

Remediation creates branches and PRs/MRs by provider — GitHub PR, GitLab MR, Bitbucket PR, local branch (no PR, so review and merge it yourself). The PR-opening happens **server-side** and is independent of any local `git push`.

**Squashing a remediation result** *(requires atx >= 3.17)*: `--configuration squashCommits=true` collapses the per-step commits onto a new `atx-result-squashed-*` branch for review, while `atx-result-staging-*` keeps the step-by-step history. `--configuration commitHeader=...` sets that commit's subject and implies `squashCommits`; pass it as JSON (`--configuration '{"commitHeader":"..."}'`) if the subject contains a comma.

---

## 7. Remote compute

Run analyses on AWS compute instead of a laptop.

```bash
atx ct remote analysis --mode aws-managed --type agentic-readiness --sources my-portfolio
atx ct remote analysis --mode ec2|batch   --type agentic-readiness --sources my-portfolio --stack-name <stack>
```

| `--mode` | Infrastructure |
|---|---|
| `aws-managed` | **the AWS-managed fleet — no customer infrastructure required** *(requires atx >= 3.14)* |
| `ec2` | customer-deployed CloudFormation stack, one container per repository |
| `batch` | customer-deployed CloudFormation stack, AWS Batch on Fargate |

Fan-out is `--sources` (all repositories in a source) and/or `--repos` (specific repositories); supplying both runs their union. Filter with `--labels` (AND semantics, `--sources` only). Resume a partial Batch run with `--resume-incomplete --batch-name <id>`.

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

- **`provision`, `update` and `teardown` are dry-run by default** — they print a preview, and `provision` writes the CloudFormation template locally. They only act with `--execute`. These need administrative permissions; `--ack` skips the interactive prompt.
- **`provision` can reuse pre-created IAM** via `--existing-batch-job-role-arn`, `--existing-batch-execution-role-arn`, `--existing-lambda-{submit,terminate,metrics}-role-arn`, `--existing-instance-profile-name` and `--existing-scheduler-role-arn` — for accounts where agents may not create roles.
- **`remote credentials`** stores a source's token in AWS Secrets Manager so remote workers can clone.
- **A `local` source running remotely works from the CLI** (it bundles the source to S3) but **not from the console**, which has no upload step.

---

## 8. Schedules

```bash
atx ct schedule create --name nightly-ara --mode aws-managed --recurrence daily \
    --type agentic-readiness --sources my-portfolio --execution-role <arn>
atx ct schedule list|get|enable|disable|delete [--region <r>] [--json]
atx ct schedule teardown [--stack-name <n>] [--execute] [--yes]
```

- `--recurrence` is **required**: `daily` | `weekly:<MONDAY..SUNDAY>` | `monthly:<1..28>`. **Raw `cron(...)`/`at(...)` expressions are not accepted** — there is no `--expression` flag.
- **The fire time is not configurable to the minute.** Per its own help it "resolves to about 2 minutes from now (local wall clock, DST-stable)". A schedule named `nightly-*` will not necessarily run at night.
- `--execution-role <arn>` is **required for `--mode aws-managed`** (the role the scheduled runner assumes at fire time). `--mode ec2|batch` creates a local EventBridge schedule and needs `--stack-name`.
- List a schedule's fired child runs with `atx ct analysis list --schedule-id <sched-id>`.

---

## 9. Hosted console

AWS Transform has a hosted **Continuous modernization** console with Dashboard / Findings / Remediations / Analyses / Sources / Settings tabs, reading the same account-scoped data as the CLI. It is the best "show the audience" surface — prefer it over exporting reports for a demo. There is no local web UI.

| Task | Console | CLI |
|---|---|---|
| Browse findings and analyses, demo | ✅ best | workable |
| Run an analysis on an SCM source | ✅ | ✅ |
| Run an analysis on a `local` source remotely | ❌ no upload step | ✅ auto-bundles to S3 |
| Readiness steering (`--context`, `--agent-scope`, `--prefer`, `--avoid`) | ❌ not exposed | ✅ |
| Recurring schedules | ✅ | ✅ |

Neither surface is a superset. Reach for the CLI whenever a `local` source or steering is involved.

---

## 10. MCP integration

`atx ct mcp` exposes a **subset** of the CLI as MCP tools — read and query work is cleaner through it; anything in the absent list needs the CLI.

```bash
atx ct mcp                                # stdio (local agent integration)
atx ct mcp --transport http --port 3100   # HTTP
```

```json
{
  "mcpServers": {
    "atxct": { "command": "atx", "args": ["ct", "mcp"], "env": { "AWS_PROFILE": "your-profile", "AWS_REGION": "us-east-1" } }
  }
}
```

Enumerate the current tool set with an `initialize` + `tools/list` handshake rather than trusting a count written down here — it changes between releases. Broadly it covers `source_*`, `discovery_scan`, `repository_*`, `analysis_*`, `findings_*` and `remediation_*`.

**Absent from MCP — use the CLI:** `findings batch-update`, `repository update`, `setup`, `status`, the entire `remote` group, the entire `schedule` group, the readiness steering flags, and the execution plan (`atx custom def exec` is not an MCP tool).

MCP naming differs from the CLI: a local source's `provider_config.rootPath` versus `--path`; `identifier`/`token` versus `--org`/`--token`; `assessment_type` versus `--type`.

---

## 11. Operational notes

- **Failures carry a plain-language explanation and a suggested next step** on `analysis get`, `remediation status` and `remote status`, with the raw error kept as detail *(atx >= 3.17)*. Read the explanation rather than regex-matching the raw string.
- **`ATX_MAX_SOCKETS`** bounds simultaneous connections to the analysis service. A very wide submission may log `socket usage at capacity` — informational; tune that variable or raise the shell's open-file limit.
- **The terminal UI is the default.** For line-oriented output in scripts and agent runs, pass `--classic` or set `ATX_CLASSIC=1`.
- **JSON field names are terse. Inspect before scripting.**
  - `source list --json` → objects use `.source` (**not** `.name`), plus `.provider`, `.identifier`.
  - `repository list --json` → paginated envelope `{ items, nextToken, total }`; repositories are under `.items[]`, keyed by `.slug` and `.source`. The key is `nextToken`, **not** `next_cursor`.
  - `findings list --json` → top-level array; the auto-fix indicator is `.fix` (always `null` for the readiness analyses).
- **Pagination** is `--next-token <token>` on `source list`, `repository list`, `analysis list`, `findings list`, `remediation list`. Only `analysis list-artifacts` has `--max-results`. `repository list` pagination requires a single `--source`.
- **`custom def get` writes the fetched files into the CWD unless you pass `--td <dir>` — always pass it.** `--td, --target-directory` defaults to `"."`, so a bare `custom def get -n <name>` run inside a clone drops the fetched `SKILL.md` and `references/` on top of the working tree. `atx custom def get -n <name> --td "$(mktemp -d)"`.
- **`atx custom def` does not read the Region from AWS config** the way `atx ct` does. Set `AWS_REGION=us-east-1` explicitly on every `custom def` invocation.
- **`save-draft` entries are temporary** (roughly a 30-day expiry). Use `publish` for a permanent registry entry that `remediation create --transformation-name` can reference.
- **`publish --category <analysis|remediation>` is optional to `publish` and enforced by `ct`.** A definition published without it is accepted, listed, and then refused at the point of use: *"…has no category, so it can't be used for a custom analysis. Publish it with --category analysis to use it here."*
- **Pipe-stdin consumption in loops:** in `atx ct repository list --json | jq ... | while read ...`, the CLI can consume the pipe's stdin and end the loop after one item. Capture to a variable first, then `while read ... <<< "$var"`.
- **`PYENV_VERSION=system` for git pushes** on machines where pyenv's Python has a broken `hashlib` (blake2b/blake2s `ValueError`). Without it, `git push` during remediation fails with a Python traceback — the root cause of "remediation failed to push branch". Export it in the environment running `atx ct`.
- **Logs are the command's own stdout/stderr**, because analyses run in-process. Capture them on the invocation you care about: `atx ct analysis run --type agentic-readiness --source <name> > /tmp/atx-ct-run.log 2>&1`. Per-run state also persists under `~/.atxct/shared/analyses/<analysis-id>/`.

---

## 12. Teardown — reverse-order deletion

```bash
# 1. Delete analyses (optionally cascade their findings)
for id in $(atx ct analysis list --json | jq -r '.[].id'); do
  atx ct analysis delete --id "$id" --cascade-findings
done

# 2. Delete repositories UNDER each source (sources can't be removed while repos reference them → HTTP 409)
repos=$(atx ct repository list --json | jq -r '.items[] | "\(.slug)\t\(.source)"')
while IFS=$'\t' read -r slug src; do
  atx ct repository delete --repo "$slug" --source "$src"
done <<< "$repos"

# 3. Purge residual findings — must be dismissed/obsolete before delete (no batch delete)
open=$(atx ct findings list --status open --json | jq -r '.[].id' | paste -sd, -)
[ -n "$open" ] && atx ct findings batch-update --ids "$open" --status dismissed --reason "env reset"
for id in $(atx ct findings list --json | jq -r '.[].id'); do atx ct findings delete --id "$id"; done

# 4. NOW remove sources (the field is .source, not .name)
for name in $(atx ct source list --json | jq -r '.[].source'); do atx ct source remove --name "$name"; done

# 5. Verify — deletes exit 0 even on a no-op; trust the counts, not the exit code
echo "repos=$(atx ct repository list --json | jq .total) sources=$(atx ct source list --json | jq length) \
analyses=$(atx ct analysis list --json | jq length) findings=$(atx ct findings list --json | jq length)"
```

- **Teardown order is the reverse of creation.** You cannot remove a source that still has repositories (HTTP 409). `analysis delete --cascade-findings` removes that analysis's findings; repositories persist until explicitly deleted.
- **`source remove` and per-item deletes exit 0 even when they no-op** (for example on a swallowed 409). Re-list and verify counts; do not trust exit codes alone.
- **Bulk deletes are slow** (sequential API calls, roughly 1–2 s each). For dozens of items, run the loop as a background task and poll live counts rather than the buffered output.
- `atx ct status` gives a quick account-wide count of sources, repositories, analyses, findings and remediations.

---

## 13. Full command surface

`atx ct schema` prints a machine-readable JSON manifest of the command tree — the best starting point for automation. It covers 12 command groups but is **not exhaustive**: it omits the deprecated hidden `server` command and the `--wait` flag. Its `version` field is a schema constant, not the CLI version.

| Group | Commands |
|---|---|
| **Status** | `atx ct status [--health] [--json]` |
| **Schema** | `atx ct schema` |
| **Sources** | `source add\|list\|get\|remove\|update` |
| **Discovery** | `discovery scan --source <n> [--path <override>] [--json]` |
| **Repositories** | `repository list\|get\|update\|delete` |
| **Analysis** | `analysis run\|get\|list\|list-artifacts\|get-artifact\|cancel\|delete` |
| **Findings** | `findings list\|count\|get\|update\|batch-update\|delete` |
| **Remediation** | `remediation create\|list\|status\|retry\|cancel\|delete` |
| **Setup** | `setup <component> [--status] [--delete]` |
| **Remote** | `remote analysis\|remediation\|status\|detect\|provision\|update\|credentials\|teardown\|cancel\|network` |
| **Schedule** | `schedule create\|list\|get\|enable\|disable\|delete\|teardown` |
| **MCP** | `mcp [--transport stdio\|http] [--port <p>]` |

### Telemetry

```bash
atx ct analysis run --type agentic-readiness --source my-portfolio \
  --telemetry "agent=claude-code,executionMode=local"
```
