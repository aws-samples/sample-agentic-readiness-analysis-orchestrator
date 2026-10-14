# The AWS Transform Paths

Routing reference. Read this before you tell a customer which path their estate belongs on, and **always** before you promise that two paths chain.

Baseline: `atx` 3.18.0. Top-level commands are `custom`, `json`, `mcp`, `ct`. There is no `atx update` — re-run the installer at `https://transform-cli.awsstatic.com/install.sh`.

---

## Six paths plus Custom

The docs' own navigation gives seven capability chapters plus one input collector. The cleanest framing for routing is **six agent-driven paths plus Custom as the escape hatch**, where Full-stack Windows counts as one path with two sub-agents and Discovery is an input rather than a destination. Splitting .NET from SQL Server gives you seven agents; both framings are defensible.

| Path | Ingests | Produces |
|---|---|---|
| **Migrations (including VMware)** | three discovery routes — Application Discovery Service collectors, the open-source vCenter export tool, or imported discovery data from any source; plus free text to enrich planning | discovery inventory; application groupings → move groups → migration waves; **7Rs strategy recommendations** per server and per application with target service, confidence and reasoning; landing zone; VPC network architecture translated and deployed; rehost to EC2 with test and cutover. Interactive HTML dashboard by default; PDF and PPTX on request |
| **Mainframe modernization** | mainframe source via an **S3 connector**. z/OS: COBOL + copybooks, PL/I, JCL + PROC, CICS CSD, BMS, Db2, VSAM, IMS TM. Fujitsu GS21: PSAM, ADL, NDB | codebase analysis, generated technical documentation, business rules traced to source, domain decomposition, wave planning, refactored **Java/Spring**, IaC for the target, test scenarios and functional-equivalence validation |
| **Full-stack Windows — .NET** | source from Azure Repos, Bitbucket, GitHub, GitLab. From .NET Framework 3.5, .NET Core 3.1, .NET 5.x–10 | assessment report + customizable modernization plan, transformed code targeting .NET 8 / 10 / Standard, transformation report, local build validation, ported unit tests |
| **Full-stack Windows — SQL Server** | live SQL Server connection (online) or uploaded DDL (offline), **plus** the associated .NET app source. SQL Server 2008 R2–2022, any edition, on RDS, EC2 or off-AWS | converted Aurora PostgreSQL schema, T-SQL → PL/pgSQL stored procedures, data migration via **AWS DMS** with integrity validation, rewritten EF / EF Core / ADO.NET data access and connection strings, wave-based plan, CloudFormation or CDK, ECS/EC2 deployment with rollback |
| **Source code containerization** | source from GitHub, Bitbucket, GitLab via AWS CodeConnections, or **.zip upload** (1 GB per file, 8 GB total). Optional private dependency sources: CodeArtifact (Maven, PyPI, npm) and private ECR base images | Dockerfiles and config, images built, tested and published to **ECR with vulnerability scanning**, then **Helm charts for EKS** or **Terraform modules for ECS**, with validation and security scanning. Nine-step workflow ending in test-infra deploy, teardown, cutover |
| **Migration assessments** | **the broadest ingestion surface in the product** — nine formats, auto-detected, partial data accepted, incremental uploads supported: Transform Discovery Tool export, RVTools (ZIP/CSV or Excel, full or vInfo-only), CMDB exports, Migration Evaluator Quick Insights, MPA import file, NetApp Data Infrastructure Insights, partner tools (ModelizeIT, Cloudamize, Matilda Cloud, Device42), and the Assessment Data template (Excel). **Or no file at all** — rough estimation from chat | TCO business case; best-fit and lowest-cost EC2 recommendations including Graviton, Dedicated Hosts and pricing models; SQL Server on RDS/EC2 with licensing and edition analysis; storage across EBS, S3 and FSx for NetApp ONTAP; self-managed Kafka → MSK Express; business value across the AWS Cloud Value Framework pillars; sustainability impact; scenario comparison and what-if; executive presentations. Also indicates **MAP** qualification |
| **Continuous modernization** (`atx ct`) | source repositories via **sources**: `github` (org, classic PAT), `gitlab` (group or user, including self-hosted), `bitbucket` (Cloud workspace or DC project), `local` (a **parent folder** whose subdirectories are each one repo) | findings (severity high/medium/low, status open/dismissed/obsolete, each optionally carrying a fix transform), HTML reports by severity / repo / analysis type, remediation PRs and MRs, scheduled recurring analyses |
| **Custom** (`atx custom`) | a code repository path, plus a transformation definition: `SKILL.md` (required, YAML frontmatter with `name` + `description`) + optional `references/` + optional `scripts/`. Steering via `additionalPlanContext` and `buildCommand` | transformed code, plus knowledge items and lessons harvested automatically from each run (`list-ki`, `get-ki`, `export-ki-markdown`, `learnings`) |

### Discovery tool — an input, not a destination

Deployable on VMware, Hyper-V or Linux. Three routes: VMware vCenter auto-discovery, Hyper-V auto-discovery, and CSV server import. Collects servers, databases and **network connections**; needs OS-level credentials (SSH / WinRM) for deep collection, with optional database credentials for direct SQL collection and OS-level fallback detection. **Output is an MPA export** — a `.zip` containing `mpa_exports/` — which is the documented handoff into Migration assessments.

---

## The hard limits, by path

These are the sentences that stop an engagement. Check them before routing, not after.

**Migrations.** The 7Rs report **requires** the discovery step *and* application grouping to be complete first. Workspace Region pins the job Region, though for VMware the workspace Region is used for discovery while the migration target Region may differ. Despite the name, the path covers VMware, Hyper-V **and bare metal** — "the VMware path" is a misnomer the product has moved past, even though the console still creates the job as "VMware migration".

**Mainframe.** Legacy job schedulers are **not** modernized — they are only read during assessment to spot missing artifacts. São Paulo supports **mainframe agents only**, so any multi-path engagement in that Region fragments across workspaces. And the refactor execution engine is a **separate tool on a separate portal**, reached by single sign-on from the AWS Mainframe Modernization console with its own doc set; build-and-deploy of the refactored application uses the mainframe Runtime, documented under the `m2` doc set, which does have an API reference. Mainframe refactor is genuinely a second surface, not a view of the first.

**.NET.** Scope is strictly **.NET-to-.NET**. It will not transform Blazor UI components, Win32 DLLs without core-compatible libraries, repositories with no .NET solution, or website projects lacking a project file. C# is GA; **VB.NET is preview**; desktop (WinForms/WPF), Xamarin and ASMX are **preview**. Cross-stack work — WebForms to React, or any non-.NET target — is explicitly out of scope; route it to Custom and do not promise it from the .NET agent.

**SQL Server.** The sharpest limits in the product. It **requires .NET 6, 7, 8 or 10 — .NET Framework 4.x and earlier is NOT supported**, so the .NET path must run first. Target is **Aurora PostgreSQL 15+ only**. Available in **us-east-1 only** (a clone-to-region workaround is documented). An AWS-hosted source database must be in the same Region as AWS Transform. The source VPC needs subnets in at least two Availability Zones, a DMS requirement. The database user needs `VIEW DEFINITION` and `VIEW DATABASE STATE`. Database passwords must be printable ASCII excluding `/`, `@`, `"` and space. The application must already build and run.

**Containerization.** **Not standalone-addressable** — you reach it only by creating a VMware migration job, then choosing standalone containerization or end-to-end migration with a wave whose strategy is `containerize`. It is **for applications that are not yet containerized** and explicitly **does not support migrating existing containerized workloads**; use normal ECS/EKS deployment for those. EKS needs an existing cluster or create permissions.

  ‼ **This is the managed path, and it is console-only.** It is not the only way to containerize:
  the `containerize-service` custom definition does a per-repository Dockerfile and manifests from
  the CLI via `atx ct remediation create --transformation-name`, with no migration job involved.
  Different scope and different output — the comparison is in `SKILL.md` stage 1. Do not tell an
  SA the console is mandatory for containerization; tell them which route fits.

**Migration assessments.** **Rough estimation is standalone and cannot be combined** with uploaded inventory or chat data-enrichment — pick one mode. Tunable assumptions are a fixed set: pricing model, target Region, utilization and right-sizing, processor architecture, tenancy, instance-type exclusions, EBS configuration, and SQL Server licensing (BYOM / LI / BYOL).

**Continuous modernization.** Architecturally the odd one out: *all analysis and remediation run in the customer's AWS account using their credentials, and their source code stays under their control.* Four compute options — **Local** (default), **AWS Transform-managed** (no infra), **AWS Batch on Fargate** (recommended), **EC2**. Its modernization-readiness analysis treats on-prem and VMware as **out of scope**. A `local` source running remotely works from the CLI, which bundles the source to S3, but **not** from the console, which has no upload step.

**Custom.** Documented routing-away rules — these are the official "don't use Custom" boundaries: COBOL and mainframe go to the mainframe path; .NET Framework to .NET Core goes to the Windows path; VMware goes to the Migrations path.

---

## Continuous modernization — the analysis types

Six, verified against the binary (`--type`):

| Type | What it does |
|---|---|
| `rapid-techdebt-analysis` | metadata-only manifest scan (`pom.xml`, `package.json`, `requirements.txt`) — **does not read source** |
| `tech-debt-comprehensive` | deep code-level tech-debt analysis |
| `security` | SAST via the AWS Security Agent; **one-time infrastructure setup required** (`atx ct setup security-agent`) |
| `agentic-readiness` | agent-integration readiness |
| `modernization-readiness` | cloud modernization opportunity assessment |
| `custom` | any published transformation definition: `--type custom --transformation-name <name>` |

⚠️ **`rapid-techdebt-analysis` is a display name over a different stored value.** `rapid-techdebt-analysis`, `quick-scan` and `tech-debt-quick` are all accepted on input, but the **canonical persisted value is `tech-debt-quick`** — that is what `analysis list --type <x>` filters on and what stored records contain. Pass what `--help` advertises; filter and assert on `tech-debt-quick`.

**Steering flags, verbatim from the binary:** `--context` is valid with `agentic-readiness` *or* `modernization-readiness`; `--agent-scope` is **agentic-readiness only**; `--prefer` and `--avoid` are **modernization-readiness only**; `--transformation-name` and `-g`/`--configuration` **require `--type custom`**. There is no `--agent-type`.

**Three remediation modes:** findings-based (each finding uses its own fix transform), transformation-definition override, and direct (run a definition against a repository with no findings at all).

`atx ct schema` prints the entire command surface as a machine-readable JSON manifest — use it rather than scraping `--help`.

---

## Driver matrix

| Path | `atx` CLI | Web app | MCP | IDE | Public API |
|---|---|---|---|---|---|
| Migrations (incl. VMware) | no | yes | **yes, full lifecycle** | no | no |
| Mainframe | no | yes | yes | **VS Code / Open VSX** | no (the Runtime has one, under `m2`) |
| .NET | no | yes | yes | **Visual Studio** | no |
| SQL Server | no | yes | yes | no | no |
| Containerization | no (but see `containerize-service`) | yes (inside a migration job) | not documented | no | no |
| Migration assessments | no | yes | not documented | no | no |
| Continuous modernization | **yes (`atx ct`)** | yes | **yes (`atx ct mcp`)** | agent plugin | no |
| Custom | **yes (`atx custom`)** | yes (monitoring) | yes | **VS Code / Open VSX** | no |

Shared developer-tool surfaces: the **agent plugin** at `awslabs/agent-plugins` (`plugins/aws-transform`), the VS Code / Open VSX IDE plugin, and the MCP server `awslabs.aws-transform-mcp-server` on PyPI with 19 tools covering workspace, job, human-in-the-loop, artifact, connector, chat and resource browsing. There is also an agent builder toolkit letting partners and ISVs build and register their own agents into AWS Transform.

### The API question

**There is no publicly documented AWS Transform control-plane API.** The service has no API Reference doc set, the docs navigation has no API chapter, and the MCP server documentation states plainly that most of its tools use *web API authentication (browser login)* — a browser-login web API is not a public API. Absence of documentation is strong evidence but not formal proof, so phrase the claim as *"no publicly documented API; automation goes through the CLI (continuous modernization and Custom only) or the MCP server."*

**Practical consequence:** the only two paths you can script non-interactively today are **Continuous modernization** and **Custom**. Everything else is chat-and-human-in-the-loop, reachable programmatically only through the MCP server's browser-authenticated tools. `atx ct schema` exists precisely so agents can discover the CM surface machine-readably, and `atx ct analysis run --json` returns `{ analysisId, status, total, findingCount }`.

---

## Composability — what chains

Verified, documented, in-product:

1. **Discovery tool → Migration assessments.** Upload the `.zip`, or unzip and upload the MPA files from `mpa_exports/`.
2. **Discovery → Migrations discovery → planning → app grouping → move groups → waves → rehost.** The spine of the Migrations path, and re-uploadable: new discovery data is auto-processed, de-duplicated and merged, and changed dependencies **flag impacted dependency groups** with wave-plan adjustment recommendations.
3. **Migrations wave → Containerization.** Set a wave's strategy to `containerize`. This is the only path-to-path *execution* handoff in the product.
4. **.NET modernization → SQL Server modernization.** A **hard prerequisite**, not a preference.
5. **Containerization → ECR → ECS/EKS**, with IaC generated for the chosen target.
6. **Mainframe analysis and decomposition → refactor (separate portal) → mainframe Runtime build and deploy.** Three surfaces, one journey.
7. **Within CM: analysis → findings → remediation**, where a finding can carry its own fix transform. And **custom definitions are first-class inside CM** — `--type custom --transformation-name <name>` for analysis, `--transformation-name` for remediation. This is the one genuine two-way composition: CM consumes the Custom registry.

## Composability — what does not

1. **Containerization cannot ingest already-containerized workloads.** A documented refusal.
2. **Rough estimation in Migration assessments is standalone.** It cannot be mixed with uploaded inventory or chat enrichment.
3. **The .NET path will not do cross-stack work.** Route it to Custom.
4. **Custom must not be used for COBOL/mainframe, or for .NET Framework → .NET Core.** Documented routing-away.
5. **SQL Server modernization is us-east-1 only** and Aurora PostgreSQL 15+ only. If the estate is elsewhere the chain breaks and needs a clone-to-region detour.
6. **São Paulo workspaces support mainframe agents only.**
7. **Workspace Region pins the job Region**, and the workspace is also the permissions boundary — so a multi-Region program needs multiple workspaces and cross-path artifact sharing is bounded by workspace, not by account.
8. **No documented data handoff from Continuous modernization into any service-side path.** CM runs in the customer account on customer credentials while every other path runs service-side in a workspace. CM *recommends* the other paths as programs instead of handing off data. **The join is a recommendation, not a data flow** — do not design an engagement around a handoff that does not exist.
9. **Migration assessments → Migrations job**: both are job types in the same workspace and both can consume the same discovery export, but there is **no documented programmatic promotion** of an assessment into a wave plan. Treat them as "same inputs, separate jobs."

---

## Sequences an SA would actually use

- **Estate-wide, no clear target yet:** Discovery tool → Migration assessments (business case + MAP qualification) → Migrations planning → 7Rs report. **The 7Rs report is the fork** — it names rehost vs replatform vs refactor per application, and that output routes each application to its path.
- **Rehost-heavy estate:** Migrations end to end, with `containerize` strategy on the waves worth replatforming.
- **Windows / SQL estate:** .NET first (mandatory if on Framework 4.x), then SQL Server. Never the reverse.
- **Mainframe:** its own track, start to finish.
- **Code-level, already on AWS:** Continuous modernization, scheduled recurring, with custom definitions for anything the six built-in analysis types do not cover.
- **In parallel, not in sequence:** Migration assessments (business case, finance audience) and Continuous modernization (code health, engineering audience).
