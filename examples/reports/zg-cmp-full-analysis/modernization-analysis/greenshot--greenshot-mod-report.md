# Modernization Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | greenshot |
| **Date** | 2025-07-17 |
| **Repo Type** | monorepo |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | csharp, desktop, windows |
| **Context** | Windows screenshot and annotation tool. |
| **Overall Score** | 1.33 / 4.0 |

**Archetype Justification**: Desktop WinForms/WPF application with local INI file configuration state and user-initiated upload operations to third-party cloud services. Cloud service archetype model does not directly apply; classified as stateful-crud (conservative default) per TD decision logic for ambiguous cases.

> **Important Context**: Greenshot is a **Windows desktop application**, not a cloud-hosted service. Many analysis questions evaluate cloud infrastructure maturity, managed services, and operational practices that are inherently absent in a desktop application. The low scores across INF, SEC, and OPS categories reflect the fundamental nature of the application — they are not necessarily gaps that need closing within the current desktop deployment model. However, if the application were to be modernized for cloud deployment (e.g., a SaaS screenshot service), these scores identify the full scope of work required.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.09 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 1.50 / 4.0 | ❌ Not Present |
| Data Platform Modernization (DATA) | 1.75 / 4.0 | 🟠 Needs Work |
| Security Baseline (SEC) | 1.29 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.00 / 4.0 | ❌ Not Present |
| **Overall** | **1.33 / 4.0** | **❌ Not Present** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | OPS-Q1 through OPS-Q9 (all) | 1 | No cloud observability, testing, deployment strategy, or operational practices in place. | Zero operational visibility; no automated testing means regression risk on every release; direct-to-production releases with no staged rollout. |
| 2 | INF-Q10: IaC Coverage | 1 | No infrastructure-as-code — all infrastructure is manually configured or workflow-only. | Infrastructure changes are non-reproducible; no disaster recovery or environment consistency. |
| 3 | INF-Q1: Managed Compute | 1 | No cloud compute — application runs entirely on end-user Windows machines as a desktop executable. | Application cannot scale elastically; no managed compute benefits (patching, scaling, monitoring). |
| 4 | SEC-Q7: Application Security Pipeline | 1 | No SAST, DAST, or dependency vulnerability scanning in CI/CD pipeline. | Vulnerabilities in NuGet dependencies or application code reach production undetected. |
| 5 | APP-Q3: Async vs Sync Communication | 1 | All third-party API communication (Imgur, Box, Dropbox, Confluence, Jira) is synchronous HTTP. | Upload operations block the UI thread; timeout risks on large images or slow networks. |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 2). GitHub Actions `release.yml` provides build and deploy automation to GitHub Releases; `choco-publish.yml` automates Chocolatey package publishing.
- **What it enables:** An agent that triggers builds, checks build status, manages release creation, and automates version tagging. Could orchestrate the release workflow end-to-end including the manual `build-and-deploy.ps1` script for signed releases.
- **Additional steps:** Expose GitHub Actions API endpoints for agent invocation. Consider adding webhook notifications for build status changes.
- **Effort:** Low — existing GitHub Actions API provides the automation surface.

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists in repository. `README.md` (project overview, build instructions), `CONTRIBUTING.md` (coding conventions), `.github/copilot-instructions.md` (comprehensive developer guide with build commands, architecture, troubleshooting), `docs/release-management.md` (versioning and release process), `SECURITY.md` (vulnerability reporting).
- **What it enables:** A knowledge agent that indexes existing documentation to answer developer questions about build processes, coding conventions, plugin architecture, and release management. Particularly valuable given the project's non-standard build requirements (MSBuild-only, no `dotnet build`).
- **Additional steps:** Index the `.github/copilot-instructions.md` file as the primary knowledge source — it contains the most comprehensive developer documentation. Consider generating API documentation from XML doc comments in source code.
- **Effort:** Low — existing documentation provides a rich corpus for RAG indexing.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2, INF-Q1=1, APP-Q3=1, APP-Q4=1. Desktop monolith with no cloud infrastructure. Note: only relevant if cloud migration is a goal. |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1=1 and no containers found, but contextual guard prevents trigger: application is a desktop executable, not EC2/VM-based compute. Containerization pathway does not apply to desktop applications. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (≥3). No stored procedures or proprietary SQL. No commercial database engines detected. |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2=1 but no databases exist. Desktop app uses local INI file configuration. No database to migrate. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4=1 but no data processing workloads exist. Contextual guard: no streaming, ETL, or analytics artifacts found. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1, INF-Q11=2 (<3). Supporting: OPS-Q5=1, OPS-Q6=1. No IaC, limited CI/CD, no testing, no deployment strategy. |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in context. Context is "Windows screenshot and annotation tool." with no AI-related signal terms. |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

> **Important Caveat**: This pathway is triggered because the technical criteria are met (monolithic desktop application with no cloud infrastructure). However, Greenshot is a Windows desktop screenshot tool — it is designed to run on end-user machines, not as a cloud service. This pathway is only relevant if the product strategy includes creating a cloud-hosted version (e.g., a SaaS screenshot/annotation service, a browser extension with cloud backend, or an API-based image processing service).

**Current Architecture State:**
- Single deployable WinExe (Greenshot.exe) targeting .NET Framework 4.8 with WinForms/WPF UI
- Plugin architecture with 7 plugins (Box, Confluence, Dropbox, ExternalCommand, Imgur, Jira, Office) loaded dynamically at runtime
- Clear module boundaries: Greenshot.Base → Greenshot.Editor → Greenshot → Plugins
- All modules compile into a single output directory and are distributed as one installer package
- Plugins share the same process and communicate through interfaces (IGreenshotPlugin)

**Compute Model Gaps:**
- No cloud compute whatsoever — application runs on end-user Windows desktops
- No containerization, no serverless functions, no managed orchestration

**Communication Pattern Gaps:**
- All third-party API communication (Imgur, Box, Dropbox, etc.) is synchronous HTTP using `HttpWebRequest`
- No async messaging patterns; upload operations block during execution
- OAuth2 token management is synchronous with blocking browser-based authorization flows

**If Cloud Migration Were Pursued:**
- **Recommended Architecture**: Decompose into API-based image capture/annotation service with serverless backend
- **Representative AWS Services**: Amazon API Gateway for API entry point, AWS Lambda or Amazon ECS on Fargate for image processing, Amazon S3 for image storage, Amazon EventBridge for event-driven plugin integrations, Amazon Bedrock for AI-powered annotation features
- **Recommended Patterns**: Strangler Fig for incremental migration, Hexagonal Architecture for new services
- **See**: Decomposition Strategy section below for detailed approach options

**Links to AWS Prescriptive Guidance:**
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)
- [Strangler Fig Pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 1):**
- No infrastructure-as-code files found in the repository (no Terraform, CloudFormation, CDK, Helm, or Kustomize)
- GitHub Actions workflows define CI/CD pipeline configuration but no infrastructure provisioning
- Build environment is configured entirely through GitHub Actions YAML workflow steps
- The `build-and-deploy.ps1` script is a manual release process — not automated IaC

**Current CI/CD State (INF-Q11 = 2):**
- GitHub Actions `release.yml` automates: NuGet restore → MSBuild → package installer → create portable ZIP → create GitHub Release
- `choco-publish.yml` automates Chocolatey package publishing on release events
- `purge-cloudflare-cache.yml` and `update-gh-pages.yml` automate post-release tasks
- **Critical Gap**: No automated testing step in any pipeline. The copilot-instructions.md explicitly states "There are NO automated test projects in this repository."
- **Gap**: No automated rollback mechanism; releases are published directly to GitHub Releases as pre-releases

**Deployment Strategy Gaps (OPS-Q5 = 1):**
- Direct-to-production release via GitHub Releases (installer .exe and portable .zip)
- No staged rollout, no canary, no blue/green for desktop releases
- Chocolatey publishing happens automatically on release events with no staged distribution

**Testing Gaps (OPS-Q6 = 1):**
- Zero automated test projects in the entire solution (confirmed by examining all .csproj files)
- No unit tests, integration tests, or end-to-end tests
- Manual testing is the only verification method (per copilot-instructions.md validation checklist)

**Recommended DevOps Improvements (ordered by impact):**

1. **Add Automated Testing** (Highest Priority)
   - Create `Greenshot.Tests` project with unit tests for core logic (image processing, plugin loading, configuration management)
   - Add test step to `release.yml` before build step
   - Use xUnit or NUnit for .NET Framework 4.8 compatibility
   - Start with tests for `Greenshot.Base` (most reusable, least UI-dependent code)

2. **Add Dependency Vulnerability Scanning**
   - Enable GitHub Dependabot for NuGet package vulnerability alerts
   - Add `dotnet list package --vulnerable` step to CI pipeline
   - Consider adding Snyk or GitHub Advanced Security for deeper scanning

3. **Implement Staged Release Strategy**
   - Use GitHub Releases draft → pre-release → full release workflow
   - Add a "release candidate" stage where community can test before full release
   - Consider Chocolatey pre-release packages for staged distribution

4. **Add IaC for CI/CD Infrastructure** (if moving to cloud)
   - If cloud deployment is pursued, define all infrastructure in Terraform or CDK
   - Prefer EKS for container orchestration per technology preferences
   - Use Aurora or DynamoDB for any persistent state per preferences

**Representative AWS Services:** AWS CodeBuild, AWS CodePipeline, AWS CodeDeploy, AWS CDK, Amazon CloudWatch
**Links:** [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Decomposition Strategy

> **Context**: APP-Q2 scored 2 — the application is a monolith with identifiable modules (plugin architecture) but a single deployable unit. This section provides decomposition guidance **if** a cloud migration is pursued.

### Decomposition Approach Options

| Approach | Description | When to Use | Level of Effort | Recommendation |
|----------|-------------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Incrementally extract services from the desktop application while keeping the desktop client running. New cloud features are built as services; existing features migrate over time. Desktop app becomes a thin client. | APP-Q2 = 2 (identifiable modules with coupling). Greenshot has clear plugin boundaries that can be extracted one at a time. | **Medium to High** — 6-18 months depending on scope. Each plugin can be extracted as an independent service. | ✅ **Recommended for Greenshot.** Plugin boundaries provide natural extraction points. Start with image upload plugins (Imgur, Box, Dropbox) as cloud services. |
| **Conditional / Adaptive** | Build a cloud API layer alongside the desktop app. Cloud services handle storage, processing, and integrations. Desktop app calls cloud APIs instead of third-party APIs directly. Only high-value features move to cloud. | When the team wants to add cloud capabilities without fully rewriting the desktop app. | **Low to Medium** — cloud API in 2-4 weeks, selective feature migration over 3-12 months. | ✅ **Recommended as starting point.** Add cloud backend for storage (S3) and plugin integrations without disrupting the desktop experience. |
| **Big-Bang Rewrite** | Rewrite as a web-based SaaS application or Progressive Web App from scratch. | Almost never — and especially not recommended for a mature desktop application with 20+ years of development history. | **Very High** — 12-24+ months. High risk of feature parity gaps. | ⚠️ **Recommended against.** Greenshot has extensive UI logic, OS-level screen capture capabilities, and Windows-specific integrations that cannot be replicated in a web context without significant compromise. |

### Pattern Recommendations

| Pattern | Purpose | When to Apply | AWS Prescriptive Guidance |
|---------|---------|---------------|---------------------------|
| **Anti-corruption Layer (ACL)** | Isolate cloud services from the desktop app's internal data models. Prevents desktop design decisions from leaking into cloud services. | Every extraction — place an ACL between desktop app and new cloud APIs. | [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) |
| **Event Sourcing** | Capture all user actions (capture, annotate, export) as events. Enable cross-device sync and audit trails. | When building cloud-backed storage or collaboration features. | [Event sourcing pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html) |
| **Hexagonal Architecture** | Structure each cloud service with clear boundaries between business logic, external interfaces, and infrastructure adapters. | Every new cloud service — ensures testability and portability. | [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |

### Effort Estimation Factors

| Factor | Signal in Greenshot | Effort Impact |
|--------|---------------------|---------------|
| Module boundaries | Clear plugin architecture with `IGreenshotPlugin` interface; plugins are separate assemblies | Low — natural extraction points exist |
| Data coupling | No shared database; INI file configuration is per-component | Low — no database decomposition needed |
| Stored procedures | None (DATA-Q4 = 4) | Low — no database logic extraction |
| Communication patterns | All synchronous HTTP (APP-Q3 = 1) | Medium — async patterns need to be introduced for cloud services |
| CI/CD maturity | Basic CI/CD exists (INF-Q11 = 2) but no testing | Medium — pipeline needs testing and multi-service deployment capability |
| Test coverage | No automated tests (OPS-Q6 = 1) | High — regression risk during extraction; tests must be added first |

**Calibrated Effort Estimate**: Medium to High. The clean plugin boundaries and absence of database coupling reduce architectural complexity, but the complete lack of automated tests makes any extraction risky. **Recommendation: Add automated tests for core functionality before beginning any decomposition.**

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No cloud compute infrastructure exists. Greenshot is a Windows desktop application (WinExe) distributed as an installer (.exe via InnoSetup) and portable ZIP archive. It runs entirely on end-user Windows machines. No Terraform, CloudFormation, CDK, or any IaC defining EC2, ECS, EKS, Lambda, or Fargate resources was found. The build output targets `net480` (`.NET Framework 4.8`) and produces a Windows executable. |
| **Gap** | No managed compute — the application has no cloud compute footprint. This is by design for a desktop application. |
| **Recommendation** | If cloud migration is pursued, containerize the image processing and plugin integration logic as ECS/EKS services on Fargate (per technology preferences favoring EKS). Desktop client would become a thin frontend calling cloud APIs. |
| **Evidence** | `src/Greenshot/Greenshot.csproj` (OutputType=WinExe, TargetFramework=net480), `src/Directory.Build.props` (TargetFramework=net480), absence of any `.tf`, CloudFormation, or CDK files in repository |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database infrastructure exists — no RDS, DynamoDB, DocumentDB, or self-managed database. The application stores configuration in local INI files via `IniConfig` class. User data (screenshots) is saved to the local filesystem or uploaded to third-party services. No database connection strings, ORM configurations, or SQL migration files found anywhere in the codebase. |
| **Gap** | No databases to manage. This is inherent to the desktop application architecture. |
| **Recommendation** | If cloud migration is pursued, use DynamoDB for user metadata and configuration storage, Aurora for structured data (per technology preferences). Amazon S3 for screenshot storage with lifecycle policies. |
| **Evidence** | `src/Greenshot.Base/IniFile/IniConfig.cs` (local INI configuration), absence of any database-related NuGet packages in all `.csproj` files, no connection strings in `App.config` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No workflow orchestration services found. The desktop application uses a simple event-driven UI flow — user captures screen → editor opens → user annotates → user exports to destination. Plugin loading follows a sequential scan pattern in `PluginHelper.LoadPlugins()`. No Step Functions, Temporal, Camunda, or any orchestration framework detected. With archetype `stateful-crud`, this scores 1 as the application has no dedicated orchestration for its multi-step capture-edit-export workflow. |
| **Gap** | Multi-step capture-edit-export workflow is implemented as direct procedural code with no orchestration framework. |
| **Recommendation** | If cloud migration is pursued, use AWS Step Functions to orchestrate the capture → process → annotate → export workflow. Step Functions provides visual workflow management, error handling, and retry logic. Use EventBridge for event-driven plugin integrations. |
| **Evidence** | `src/Greenshot/Helpers/PluginHelper.cs` (sequential plugin loading), `src/Greenshot/Destinations/FileDestination.cs` (direct procedural export flow), absence of any orchestration framework references |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No messaging or streaming infrastructure. All communication with third-party APIs (Imgur, Box, Dropbox, Confluence, Jira) uses synchronous `HttpWebRequest` calls. No SQS, SNS, EventBridge, Kafka, or any message queue detected. With archetype `stateful-crud`, synchronous-only cross-service state changes score 1 — the upload operations to third-party services are state-changing actions that would benefit from async decoupling. |
| **Gap** | All third-party API communication is synchronous HTTP. Upload operations block the calling thread with no retry or timeout resilience beyond basic `HttpWebRequest` timeout configuration. |
| **Recommendation** | If cloud migration is pursued, use Amazon EventBridge for event-driven plugin integrations and Amazon SQS for reliable async upload processing. This decouples the capture/edit experience from the export latency. Avoid self-managed Kafka per technology preferences. |
| **Evidence** | `src/Greenshot.Plugin.Imgur/ImgurUtils.cs` (synchronous `HttpWebRequest`), `src/Greenshot.Plugin.Box/BoxUtils.cs` (synchronous upload), `src/Greenshot.Base/Core/NetworkHelper.cs` (all synchronous HTTP), `src/Greenshot.Base/Core/OAuth/OAuth2Helper.cs` (synchronous OAuth flow) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, security groups, NACLs, or network segmentation. The application is a desktop executable running on end-user machines. It communicates over the public internet to third-party APIs. TLS 1.2/1.3 is enforced in `GreenshotMain.cs` (`ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12 | SecurityProtocolType.Tls13`). However, a concerning finding in `NetworkHelper.cs`: SSL certificate validation is disabled globally (`ServicePointManager.ServerCertificateValidationCallback += delegate { return true; }`), which bypasses certificate checking for all HTTPS connections. |
| **Gap** | No cloud network security. SSL certificate validation is globally disabled in `NetworkHelper.cs`, which is a security concern — any MITM attack with an invalid certificate would succeed. |
| **Recommendation** | **Immediate**: Remove the blanket SSL certificate validation bypass in `NetworkHelper.cs` — this is a security vulnerability. If specific services require custom certificate handling, implement targeted validation. **Cloud migration**: Deploy services in private subnets with least-privilege security groups and VPC endpoints. |
| **Evidence** | `src/Greenshot/GreenshotMain.cs` (TLS 1.2/1.3 enforcement), `src/Greenshot.Base/Core/NetworkHelper.cs` (SSL validation bypass at static constructor), absence of any VPC/security group IaC |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or any managed entry point. The application is a desktop executable — it does not expose any API endpoints. It acts as a client calling third-party APIs, not as a server. |
| **Gap** | No API entry point — inherent to desktop application architecture. |
| **Recommendation** | If cloud migration is pursued, use Amazon API Gateway as the entry point for cloud-based image processing APIs. API Gateway provides throttling, authentication, and request validation. Per technology preferences, prefer API Gateway. |
| **Evidence** | `src/Greenshot/Greenshot.csproj` (OutputType=WinExe — not a server), absence of any listener/server code in the application |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration. Desktop application runs as a single process on end-user machines. No ASG, ECS service scaling, Lambda concurrency, or DynamoDB auto-scaling. |
| **Gap** | No auto-scaling — inherent to desktop application architecture. |
| **Recommendation** | If cloud migration is pursued, configure auto-scaling for all scalable resources: EKS/ECS service scaling for image processing, DynamoDB auto-scaling for metadata storage, and Lambda concurrency limits for event-driven functions. |
| **Evidence** | Absence of any scaling-related configuration in the repository |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No automated backup configuration. Desktop application stores data locally on user machines — backup is the user's responsibility. No `aws_backup_plan`, no RDS backup retention, no S3 versioning. |
| **Gap** | No backup infrastructure — inherent to desktop application architecture. |
| **Recommendation** | If cloud migration is pursued, enable automated backups on all data stores: RDS/Aurora automated backups with PITR, DynamoDB PITR, S3 versioning for screenshot storage, and AWS Backup plans for cross-service backup management. |
| **Evidence** | Absence of any backup-related configuration in the repository |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ deployment. Desktop application runs as a single process on a single user machine. No redundancy, no failover. |
| **Gap** | No high availability — inherent to desktop application architecture. |
| **Recommendation** | If cloud migration is pursued, deploy all production services across 2+ Availability Zones. Use Multi-AZ for Aurora/RDS, cross-AZ EKS/ECS task placement, and ALB with cross-zone load balancing. |
| **Evidence** | Absence of any AZ-related configuration in the repository |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No infrastructure-as-code files found. No Terraform (`.tf`), CloudFormation (`.cfn.yaml`), CDK, Helm, or Kustomize files. The only "infrastructure" is the GitHub Actions CI/CD pipeline configuration (`.github/workflows/`), the Chocolatey package template (`chocolatey/`), and the InnoSetup installer script. These define build/release processes but do not provision cloud infrastructure. |
| **Gap** | 0% IaC coverage — all infrastructure (CI/CD environment, GitHub Pages, CloudFlare CDN) is configured manually or through platform-specific UI. |
| **Recommendation** | Define CI/CD infrastructure and any supporting cloud resources in IaC. If cloud migration is pursued, use AWS CDK (with C# support for team alignment) or Terraform to define all infrastructure. Start with defining the build environment, then add application infrastructure as cloud services are created. |
| **Evidence** | Repository-wide search for `.tf`, `.cfn.yaml`, `.cfn.json`, `cdk.json`, `Chart.yaml`, `kustomization.yaml` returned no results. Only infrastructure-like files: `.github/workflows/*.yml`, `chocolatey/greenshot.nuspec.template` |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | CI/CD pipeline exists via GitHub Actions with partial automation. `release.yml` automates: checkout → MSBuild restore → MSBuild build → package installer artifact → package portable ZIP → create GitHub Release with version tagging. `choco-publish.yml` automates Chocolatey publishing on release events. `purge-cloudflare-cache.yml` purges CDN cache on page builds. `update-gh-pages.yml` triggers GitHub Pages rebuild on releases. However, there is **no automated testing step** in any pipeline — builds go directly from compile to package/deploy. The manual `build-and-deploy.ps1` script exists for signed (stable) releases. |
| **Gap** | Build is automated but deployment lacks testing gates. No automated tests exist in the project at all. No automated rollback mechanism. Two release paths exist (automated CI for unstable, manual script for stable) creating process inconsistency. |
| **Recommendation** | Add a test step to `release.yml` before the build step. Create a `Greenshot.Tests` project with unit tests for `Greenshot.Base` core logic. Add dependency vulnerability scanning (Dependabot, `dotnet list package --vulnerable`). Unify the release process so stable releases also go through CI with code signing as an additional step. |
| **Evidence** | `.github/workflows/release.yml` (build + deploy, no test step), `.github/workflows/choco-publish.yml` (Chocolatey automation), `build-and-deploy.ps1` (manual release script), `.github/copilot-instructions.md` (explicitly states "There are NO automated test projects in this repository") |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Primary language is C# targeting .NET Framework 4.8 (`net480`). The application uses WinForms and WPF for UI. The .NET SDK version is 9.0.311 (for build tooling). Key NuGet packages include: `log4net` 3.3.0 (logging), `SixLabors.ImageSharp` 2.1.13 (image processing), `Dapplo.Windows.*` 2.0.89 (Windows interop), `HtmlAgilityPack` 1.12.4 (HTML parsing), `Svg` 3.4.7 (SVG rendering), `System.Reactive.Linq` 6.1.0 (reactive extensions), `Nerdbank.GitVersioning` 3.9.50 (versioning). |
| **Gap** | .NET Framework 4.8 is legacy — .NET 8/9 provides better cloud-native tooling, cross-platform support, and performance. The application is locked to Windows due to WinForms/WPF UI framework choice. |
| **Recommendation** | Consider migrating from .NET Framework 4.8 to .NET 8+ for improved performance, better cloud-native tooling ecosystem, and access to modern C# language features. However, this is a significant effort given the WinForms/WPF dependency. AWS SDK for .NET has first-class support for modern .NET. |
| **Evidence** | `src/Directory.Build.props` (TargetFramework=net480, UseWPF=true, UseWindowsForms=true), `src/global.json` (SDK 9.0.311), `src/Greenshot.Base/Greenshot.Base.csproj` (NuGet packages), all `.csproj` files use `Microsoft.NET.Sdk.WindowsDesktop` |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Single deployable WinExe (Greenshot.exe) with dynamically loaded plugins. The solution contains 12 projects with clear module boundaries: `Greenshot.Base` (core library) → `Greenshot.Editor` (editor component) → `Greenshot` (main app) → 7 Plugins (Box, Confluence, Dropbox, ExternalCommand, Imgur, Jira, Office). Plugins implement `IGreenshotPlugin` interface and are loaded by `PluginHelper.LoadPlugins()` via assembly scanning. Post-build events copy plugin DLLs into the main app's `Plugins/` directory. Despite clear module structure, all components share the same process, memory space, and configuration system (`IniConfig`). Plugins depend on `Greenshot.Base` and communicate through shared interfaces — there are no separate deployable units. |
| **Gap** | Monolith with identifiable modules but single deployable unit. Plugins share `Greenshot.Base` as a common dependency and all run in the same process. Plugin architecture provides modularity but not independent deployability, scaling, or fault isolation. |
| **Recommendation** | The plugin architecture provides natural module boundaries for decomposition if cloud migration is pursued. Each plugin (Imgur, Box, Dropbox, etc.) could become an independent microservice. Start by extracting shared base library interfaces into API contracts. See Decomposition Strategy section. |
| **Evidence** | `src/Greenshot.sln` (12 projects), `src/Greenshot/Helpers/PluginHelper.cs` (dynamic plugin loading via `Assembly.LoadFrom`), `src/Greenshot.Base/Interfaces/Plugin/IGreenshotPlugin.cs` (shared plugin interface), `src/Directory.Build.props` (PostBuild target copying plugin DLLs to main output) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All inter-service communication is synchronous HTTP. Plugins communicate with third-party APIs (Imgur, Box, Dropbox, Confluence, Jira) using synchronous `HttpWebRequest` via `NetworkHelper.CreateWebRequest()`. OAuth2 authorization flows are also synchronous — `OAuth2Helper.CheckAndAuthenticateOrRefresh()` blocks until authorization completes, including opening a browser window and waiting for callback. No async messaging patterns, no event-driven handlers, no message queue consumers. With archetype `stateful-crud`, all-synchronous communication for cross-service state changes (uploads) scores 1. |
| **Gap** | 100% synchronous communication. Upload operations block the calling thread. OAuth2 token refresh blocks until complete. No fire-and-forget upload capability. |
| **Recommendation** | Introduce async patterns for upload operations. In the current desktop context, use `Task.Run()` with `async/await` for non-blocking uploads. If cloud migration is pursued, use Amazon SQS for reliable async upload queuing and EventBridge for event-driven plugin notifications. |
| **Evidence** | `src/Greenshot.Base/Core/NetworkHelper.cs` (`HttpWebRequest` — all synchronous), `src/Greenshot.Plugin.Imgur/ImgurUtils.cs` (synchronous `GetResponse()`), `src/Greenshot.Plugin.Box/BoxUtils.cs` (synchronous upload flow), `src/Greenshot.Base/Core/OAuth/OAuth2Helper.cs` (synchronous OAuth2 flow) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No async job processing or status polling for long-running operations. Image uploads to Imgur, Box, Dropbox, Confluence, and Jira are synchronous operations that could take significant time depending on image size and network conditions. The `NetworkHelper` class configures `WebRequestTimeout` and `WebRequestReadWriteTimeout` from configuration but all operations block until completion. No background worker patterns, no progress reporting from the network layer, no upload queue. With archetype `stateful-crud`, all-synchronous long-running operations score 1. |
| **Gap** | Upload operations are unbounded in duration and block the calling thread. Large screenshots on slow networks could create timeout issues. No retry logic for failed uploads. |
| **Recommendation** | Implement async upload with progress tracking. Use `BackgroundWorker` or `async/await` with `Task` for non-blocking uploads in the desktop app. Add retry logic with exponential backoff for transient failures. If cloud migration is pursued, use AWS Step Functions for orchestrating upload workflows with timeout handling and retries. |
| **Evidence** | `src/Greenshot.Plugin.Box/BoxUtils.cs` (synchronous `UploadToBox` method), `src/Greenshot.Plugin.Imgur/ImgurUtils.cs` (synchronous `RetrieveImgurInfo`), `src/Greenshot.Base/Core/NetworkHelper.cs` (`webRequest.Timeout` and `webRequest.ReadWriteTimeout` configuration) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy. The application does not expose any API endpoints — it is a desktop application that consumes third-party APIs. There are no URL versioning patterns (`/v1/`, `/v2/`), no version headers, no API contracts. The third-party API URLs called by plugins are hard-coded (e.g., `https://upload.box.com/api/2.0/files/content` in BoxUtils.cs, `Config.ImgurApi3Url` in ImgurUtils.cs). |
| **Gap** | No API surface to version. Hard-coded third-party API URLs mean that API changes by third-party services could break plugins without graceful degradation. |
| **Recommendation** | If cloud migration creates an API surface, implement consistent API versioning from day one (URL path-based `/v1/` recommended for simplicity). For the current desktop app, externalize third-party API URLs to configuration to allow updates without code changes. |
| **Evidence** | `src/Greenshot.Plugin.Box/BoxUtils.cs` (hard-coded `UploadFileUri` and `FilesUri`), `src/Greenshot.Plugin.Imgur/ImgurUtils.cs` (`Config.ImgurApi3Url`), absence of any OpenAPI, Swagger, or API spec files |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No service discovery mechanism. Third-party API endpoints are hard-coded as constants in plugin source code (e.g., `https://upload.box.com/api/2.0/files/content`, `https://api.box.com/oauth2/token`). Plugin configuration (including API base URLs) is stored in local INI files via `IniConfig`. There is no service registry, no dynamic routing, and no API catalog. |
| **Gap** | All service endpoints are hard-coded in source code or static configuration. No dynamic discovery for third-party API endpoints. |
| **Recommendation** | Externalize all API endpoint URLs to configuration. If cloud migration is pursued, use AWS Service Discovery or API Gateway as a service catalog. For EKS deployments, leverage Kubernetes Service DNS for internal service discovery. |
| **Evidence** | `src/Greenshot.Plugin.Box/BoxUtils.cs` (hard-coded `UploadFileUri`, `FilesUri`), `src/Greenshot.Plugin.Imgur/ImgurUtils.cs` (hard-coded URL patterns), `src/Greenshot.Base/Core/OAuth/OAuth2Helper.cs` (token URLs from settings) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Screenshots and unstructured data are stored on the local filesystem. `FileDestination.cs` saves captured images to user-configured local paths using `ImageIO.Save()`. Additional destinations include: clipboard (`ClipboardDestination.cs`), email attachment (`EmailDestination.cs`), printer (`PrinterDestination.cs`), and third-party cloud services (Imgur, Box, Dropbox) via plugin uploads. No Amazon S3, no managed object storage, no parsing pipeline (Textract, Tika). Data resides entirely on end-user machines or is sent to non-AWS third-party services. |
| **Gap** | Data on local file systems with no managed cloud storage. No centralized storage, no search capability, no parsing pipeline for captured images. |
| **Recommendation** | If cloud migration is pursued, use Amazon S3 as the primary storage for screenshots with lifecycle policies for tiering. Add Amazon Textract for OCR on captured screenshots (text extraction from screen captures). Use S3 event notifications via EventBridge to trigger processing pipelines. |
| **Evidence** | `src/Greenshot/Destinations/FileDestination.cs` (local filesystem save via `ImageIO.Save`), `src/Greenshot/Destinations/ClipboardDestination.cs`, `src/Greenshot.Plugin.Imgur/ImgurUtils.cs` (upload to third-party), `src/Greenshot.Plugin.Box/BoxUtils.cs` (upload to third-party) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No unified data access layer — there is no database to access. Configuration is managed through `IniConfig` which provides a centralized INI file read/write mechanism. However, file I/O for screenshots is handled directly in each destination class (`FileDestination`, plugins) via `ImageIO` static methods. Image export operations are scattered across multiple destination implementations with no common data access abstraction for storage operations. Each plugin independently manages its own upload logic using `NetworkHelper` and `OAuth2Helper`. |
| **Gap** | No unified storage abstraction. Each destination (file, clipboard, Imgur, Box, Dropbox, etc.) implements its own storage/upload logic independently. No common interface for "persist a screenshot" that could be swapped between storage backends. |
| **Recommendation** | Create a unified storage abstraction (`IScreenshotStorage`) that each destination implements. This abstraction would enable easy addition of cloud storage backends (S3, Azure Blob) without modifying the core capture/edit workflow. Pattern: Repository pattern with storage adapters. |
| **Evidence** | `src/Greenshot/Destinations/FileDestination.cs` (direct `ImageIO.Save` calls), `src/Greenshot.Plugin.Box/BoxUtils.cs` (independent upload logic), `src/Greenshot.Plugin.Imgur/ImgurUtils.cs` (independent upload logic), `src/Greenshot.Base/IniFile/IniConfig.cs` (centralized config but not a data access layer) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database engines are used by this application. There are no database connection strings, no ORM configurations, no SQL migration files, and no database engine definitions in any IaC (because no IaC exists). The application stores all persistent data in local INI files and the filesystem. |
| **Gap** | No database engine versioning because no databases exist. This is not a gap for the current desktop architecture but would need to be addressed if cloud migration introduces database services. |
| **Recommendation** | If cloud migration introduces databases, explicitly pin engine versions in IaC from day one. Prefer Aurora PostgreSQL or DynamoDB per technology preferences. Establish a documented version-update procedure. |
| **Evidence** | Absence of any database-related NuGet packages (no Entity Framework, no Dapper, no ADO.NET providers) in all `.csproj` files; no `.sql` files in repository; no connection strings in `App.config` |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs. All business logic is in the C# application layer. The application does not use any database — configuration is in INI files, and all data processing (image capture, annotation, format conversion, upload) is implemented in C# code. This is the ideal state: zero database-coupled business logic. |
| **Gap** | None — no stored procedures or proprietary SQL. This is a strength. |
| **Recommendation** | Maintain this pattern if cloud migration introduces databases. Keep all business logic in the application layer; use databases only for data persistence. Avoid stored procedures to maintain database engine portability. |
| **Evidence** | Repository-wide search for `.sql` files, `CREATE PROCEDURE`, `CREATE TRIGGER`, `CREATE FUNCTION` returned no results. All business logic is in `.cs` source files. |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent cloud audit logging. The application uses log4net for local file-based logging. `log4net-release.xml` configures a `RollingFileAppender` writing to `%LocalAppData%\Greenshot\Greenshot.log` with 1MB max file size and 3 rollback files. Log format includes ISO8601 timestamps, thread ID, log level, logger name, and message. Logging is configured at INFO level for release builds. This provides local diagnostic logging but not immutable audit trails. |
| **Gap** | No cloud audit logging. Local log files are mutable and can be deleted by the user. No centralized log aggregation. |
| **Recommendation** | If cloud migration is pursued, enable CloudTrail with log file validation and S3 Object Lock for immutable storage. For the current desktop app, consider adding structured JSON logging for better parseability and optional telemetry opt-in for crash reporting. |
| **Evidence** | `src/Greenshot/log4net-release.xml` (RollingFileAppender to local filesystem), `src/Greenshot/log4net-debug.xml`, `src/Greenshot/GreenshotMain.cs` (`LogHelper.InitializeLog4Net()`), `src/Greenshot.Base/Greenshot.Base.csproj` (log4net 3.3.0 NuGet package) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No KMS or encryption at rest. Screenshots are saved to the local filesystem as unencrypted image files. Configuration (including OAuth2 tokens) is stored in plaintext INI files on disk. No encryption of data at rest in any form — no DPAPI, no file-level encryption, no encrypted configuration store. OAuth2 access tokens and refresh tokens for Box, Dropbox, and Imgur are stored in plaintext in the user's INI configuration file. |
| **Gap** | Sensitive data (OAuth2 tokens, refresh tokens) stored in plaintext on disk. No encryption at rest for any data. |
| **Recommendation** | **Immediate**: Encrypt OAuth2 tokens at rest using Windows DPAPI (`System.Security.Cryptography.ProtectedData`) before writing to INI files. **Cloud migration**: Use AWS KMS customer-managed keys for all sensitive data stores. Enable SSE-S3 or SSE-KMS for S3 screenshot storage. |
| **Evidence** | `src/Greenshot.Plugin.Box/BoxUtils.cs` (stores `RefreshToken`, `AccessToken` back to INI config), `src/Greenshot.Base/IniFile/IniConfig.cs` (plaintext INI file storage), absence of any encryption references in codebase |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application does not expose API endpoints — it is a desktop client. However, it implements OAuth2 authentication for third-party API access. `OAuth2Helper.cs` supports multiple authorization modes: `LocalServer` (localhost callback), `EmbeddedBrowser` (WebBrowser control), and `JsonReceiver` (via Greenshot website redirect). Plugins use OAuth2 with per-plugin client credentials (client ID and client secret) injected at build time via `.Credentials.template` files and `Directory.Build.targets` token replacement. Bearer token authorization is added to requests via `AddOAuth2Credentials()`. Imgur additionally uses `Client-ID` header authorization. |
| **Gap** | OAuth2 is implemented for third-party API access but the application has no authentication for its own operations. API keys are compiled into the binary — if the binary is decompiled, client secrets are exposed. |
| **Recommendation** | **Immediate**: Do not embed client secrets in the binary. Use PKCE (Proof Key for Code Exchange) flow instead of client_secret for desktop applications — this is the OAuth2 best practice for public clients. **Cloud migration**: Use Amazon Cognito for user authentication and API Gateway authorizers for service authentication. |
| **Evidence** | `src/Greenshot.Base/Core/OAuth/OAuth2Helper.cs` (OAuth2 implementation with 3 authorization modes), `src/Greenshot.Plugin.Box/Greenshot.Plugin.Box.Credentials.template` (build-time secret injection), `src/Greenshot.Plugin.Imgur/Greenshot.Plugin.Imgur.Credentials.template`, `src/Greenshot.Plugin.Imgur/ImgurUtils.cs` (Client-ID header), `src/Directory.Build.targets` (token replacement at build time) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity provider integration. The application does not have a user authentication system — it runs as a desktop process under the Windows user's context. OAuth2 is used per-plugin for authorizing uploads to third-party services (Box, Dropbox, Imgur, Confluence, Jira), but each plugin manages its own OAuth2 session independently. There is no SSO, no Cognito, no OIDC federation. |
| **Gap** | No centralized identity. Each plugin manages its own OAuth2 tokens independently. No unified identity for the user across plugins. |
| **Recommendation** | If cloud migration is pursued, use Amazon Cognito as the centralized identity provider with SSO support. Federate third-party service authorization through Cognito's identity federation capabilities instead of per-plugin OAuth2 flows. |
| **Evidence** | `src/Greenshot.Plugin.Box/BoxUtils.cs` (plugin-specific OAuth2 settings), `src/Greenshot.Plugin.Imgur/ImgurUtils.cs` (Imgur-specific Client-ID auth), absence of any centralized identity configuration |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Secrets are managed through a build-time template replacement system. `.Credentials.template` files contain placeholders (`${Box13_ClientId}`, `${Imgur13_ClientId}`, etc.) that are replaced with actual values from environment variables during MSBuild via `Directory.Build.targets` `ProcessTemplates` target. In CI, these values come from GitHub Secrets (visible in `release.yml` env block). The generated `.Credentials.cs` files are not committed to version control (generated at build time). At runtime, OAuth2 tokens are stored in plaintext INI files. No AWS Secrets Manager, no HashiCorp Vault, no encrypted runtime secret storage. |
| **Gap** | Build-time secrets injection is reasonable for CI but client secrets are compiled into the binary. Runtime OAuth2 tokens are stored in plaintext INI files with no rotation. No secrets manager for runtime credentials. |
| **Recommendation** | **Immediate**: (1) Encrypt runtime OAuth2 tokens using DPAPI before storing in INI files. (2) Move to PKCE OAuth2 flow to eliminate client_secret from the binary. **Cloud migration**: Use AWS Secrets Manager for all API credentials with automated rotation. Never compile secrets into application binaries. |
| **Evidence** | `src/Greenshot.Plugin.Imgur/Greenshot.Plugin.Imgur.Credentials.template` (template with `${Imgur13_ClientId}` placeholder), `src/Directory.Build.props` (Tokens ItemGroup with ReplacementValue from env vars), `src/Directory.Build.targets` (ProcessTemplates target), `.github/workflows/release.yml` (GitHub Secrets env block with 12 secret references) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No cloud compute hardening. The application is a desktop executable. Code signing is implemented for stable releases — `Greenshot-Installer.csproj` contains a `signtool.exe` command that signs `Greenshot.exe` with a Certum EV certificate (using `$(CertumThumbprint)`). SHA-256 file hashes are generated for all DLLs during the installer build (`GetFileHash` task writing `checksum.SHA256`). However, no vulnerability scanning, no SSM patching, no hardened base images — these concepts don't apply to a desktop application. |
| **Gap** | No vulnerability scanning for dependencies or application code. Code signing exists for stable releases only (not for CI/unstable builds). No automated patching strategy for NuGet dependencies. |
| **Recommendation** | **Immediate**: Enable GitHub Dependabot for NuGet vulnerability alerts. Add `dotnet list package --vulnerable` to CI pipeline. Sign all builds (including unstable) for binary integrity. **Cloud migration**: Use SSM Patch Manager, AWS Inspector, and hardened container images (Bottlerocket for EKS). |
| **Evidence** | `src/Greenshot-Installer/Greenshot-Installer.csproj` (signtool.exe code signing, SHA256 hash generation), `docs/release-management.md` ("Continuous builds are not code-signed due to restrictions of the EV code signing process"), absence of any vulnerability scanning configuration |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SAST, DAST, or dependency vulnerability scanning tools in the CI/CD pipeline. `release.yml` contains only build and deploy steps — no security scanning. No Dependabot configuration (`dependabot.yml` not found). No `.snyk` policy file. No SonarQube, Semgrep, CodeGuru, or Roslyn analyzers configured. No `dotnet list package --vulnerable` step. No container scanning (no containers). The `.github/` directory has no security-related workflow files beyond the basic `SECURITY.md` vulnerability reporting policy. |
| **Gap** | Zero security scanning in pipeline. NuGet package vulnerabilities, code vulnerabilities, and secret leaks can reach production undetected. |
| **Recommendation** | **Immediate (Low Effort)**: (1) Add `.github/dependabot.yml` for NuGet vulnerability monitoring. (2) Add `dotnet list package --vulnerable` step to `release.yml`. (3) Consider adding Roslyn security analyzers (e.g., `SecurityCodeScan.VS2019` NuGet package) for SAST. **Medium Effort**: Add GitHub Advanced Security or SonarCloud for comprehensive SAST scanning. |
| **Evidence** | `.github/workflows/release.yml` (no security scanning steps), absence of `dependabot.yml`, absence of `.snyk`, absence of any security scanning NuGet packages in `.csproj` files, `SECURITY.md` (vulnerability reporting policy only) |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing. The application uses log4net for local file logging with no trace ID propagation. Log entries include timestamp, thread ID, log level, and logger name but no correlation IDs, trace IDs, or span IDs. HTTP calls to third-party APIs do not propagate trace headers (`traceparent`, `X-Amzn-Trace-Id`). No OpenTelemetry, X-Ray, or any tracing SDK in dependencies. |
| **Gap** | No tracing capability. When an upload to Imgur or Box fails, there is no way to correlate the client-side error with the API response beyond local log inspection. |
| **Recommendation** | Add correlation IDs to log entries for each capture-edit-export workflow execution. If cloud migration is pursued, instrument with OpenTelemetry SDK and AWS X-Ray for end-to-end distributed tracing across cloud services. |
| **Evidence** | `src/Greenshot/log4net-release.xml` (log format without trace IDs), `src/Greenshot.Base/Greenshot.Base.csproj` (log4net only, no tracing SDK), `src/Greenshot.Base/Core/NetworkHelper.cs` (no trace header propagation) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions. The application is a desktop tool with no formal service level objectives. No error budget tracking, no p99/p95 latency targets, no availability targets. No CloudWatch alarms or monitoring dashboards. |
| **Gap** | No SLOs — inherent to desktop application architecture. |
| **Recommendation** | If cloud migration creates backend services, define SLOs for upload success rate, image processing latency, and API availability from day one. Use CloudWatch ServiceLevelObjective resources. |
| **Evidence** | Absence of any SLO definition files, CloudWatch alarm configurations, or monitoring dashboard definitions in the repository |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics published. No telemetry infrastructure. The application does not track capture counts, upload success/failure rates, export destination usage, or any business outcome metrics. No `cloudwatch.put_metric_data` calls, no custom dashboards. |
| **Gap** | No business metrics — no visibility into how the application is used or how features perform. |
| **Recommendation** | Consider adding opt-in anonymous usage telemetry to track feature adoption and error rates (with user consent). If cloud migration is pursued, publish business metrics to CloudWatch (uploads per destination, image processing times, feature usage). |
| **Evidence** | Absence of any metrics or telemetry SDK in NuGet dependencies, absence of any metrics publishing code in source files |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no error rate monitoring. The application has a bug reporting form (`BugReportForm`) that displays exception details to the user, but this is user-initiated error reporting, not automated alerting. |
| **Gap** | No automated alerting. Application errors are only visible when users encounter them and choose to report. |
| **Recommendation** | If cloud migration is pursued, configure CloudWatch anomaly detection on error rates and latency for all API endpoints. Set up composite alarms with PagerDuty/OpsGenie integration for on-call notification. |
| **Evidence** | `src/Greenshot/GreenshotMain.cs` (BugReportForm for unhandled exceptions — user-facing only), absence of any alerting configuration |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Direct-to-production deployment. `release.yml` builds and publishes releases directly to GitHub Releases as pre-releases. `choco-publish.yml` publishes to Chocolatey automatically on release events. No staged rollout, no canary, no blue/green. Users download the latest release and install it — there is no mechanism for gradual rollout or rollback. The `build-and-deploy.ps1` manual script creates releases as drafts, providing a manual review step, but this is only for stable releases. |
| **Gap** | All releases go directly to all users simultaneously. No staged rollout means a bad release affects 100% of users immediately. No automated rollback — users must manually install a previous version. |
| **Recommendation** | Implement a staged release strategy: (1) CI builds → pre-release on GitHub → community testing → promote to stable release. (2) Use Chocolatey pre-release packages for staged distribution. (3) Consider in-app update channel selection (stable/beta). If cloud migration is pursued, use CodeDeploy with canary or blue/green deployment for backend services. |
| **Evidence** | `.github/workflows/release.yml` (direct GitHub Release creation with `prerelease: true`), `.github/workflows/choco-publish.yml` (automatic Chocolatey publish on release), `build-and-deploy.ps1` (manual script creates draft releases), `docs/release-management.md` (describes two release paths) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No automated tests of any kind. No unit tests, no integration tests, no end-to-end tests. The solution contains 12 projects and none are test projects (confirmed by examining all `.csproj` files — no xUnit, NUnit, or MSTest references). The `.github/copilot-instructions.md` explicitly states: "There are NO automated test projects in this repository. Do not attempt to run tests." The CI pipeline (`release.yml`) has no test step. The validation checklist in copilot-instructions.md includes "Manual testing of affected features (no automated tests available)." |
| **Gap** | Zero test coverage. Every release relies entirely on manual testing. Regression risk is very high — any code change could introduce bugs that are not caught before release. |
| **Recommendation** | **Highest Priority DevOps Improvement**: Create `Greenshot.Base.Tests` and `Greenshot.Editor.Tests` projects. Start with unit tests for: (1) Image format handling in `ImageIO`, (2) INI configuration parsing in `IniConfig`, (3) OAuth2 token management in `OAuth2Helper`, (4) Network helper URL encoding in `NetworkHelper`. Add a test step to `release.yml` before the build step. Target 40% code coverage on `Greenshot.Base` as an initial goal. |
| **Evidence** | `src/Greenshot.sln` (no test projects), all `.csproj` files (no test framework references), `.github/workflows/release.yml` (no test step), `.github/copilot-instructions.md` ("There are NO automated test projects") |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response automation. No runbooks (markdown, YAML, or JSON), no Systems Manager Automation documents, no Lambda-based remediation. The application has a `SECURITY.md` file that directs users to report vulnerabilities via GitHub's security section, but this is a vulnerability disclosure policy, not an incident response procedure. |
| **Gap** | No incident response procedures or automation. Security vulnerability handling is manual and reactive. |
| **Recommendation** | Create incident response runbooks for common issues: (1) Security vulnerability in a NuGet dependency, (2) OAuth2 credential compromise, (3) Broken release (installer doesn't work). If cloud migration is pursued, use Systems Manager Automation for self-healing patterns and Step Functions for incident workflows. |
| **Evidence** | `SECURITY.md` (vulnerability disclosure policy only), absence of any runbook files, absence of any automation documents |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership. No per-service dashboards, no alarms with named owners, no SLO definitions with team attribution. No CODEOWNERS file for observability assets. The application has no monitoring infrastructure to own. |
| **Gap** | No observability infrastructure or ownership — inherent to desktop application architecture. |
| **Recommendation** | If cloud migration is pursued, establish observability ownership from day one: per-service dashboards, named alarm owners, and CODEOWNERS entries for monitoring configuration. Define SLOs with team attribution. |
| **Evidence** | Absence of any dashboard, alarm, or monitoring configuration in the repository; absence of CODEOWNERS file |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resources to tag. The application is a desktop executable with no cloud infrastructure. No `default_tags` in Terraform provider, no `tags` on any resources, no tagging standards documented. |
| **Gap** | No resource tagging — inherent to desktop application architecture with no cloud resources. |
| **Recommendation** | If cloud migration is pursued, establish a tagging standard from day one: `Environment`, `Service`, `Owner`, `CostCenter` as required tags. Enforce via CDK constructs or Terraform modules with required tags. Use AWS Organizations Tag Policies for governance. |
| **Evidence** | Absence of any AWS resource definitions or tagging configuration in the repository |

---

## Learning Materials

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to Cloud Native** | [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |
| **Move to Modern DevOps** | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `src/Greenshot/Greenshot.csproj` | INF-Q1, INF-Q6, APP-Q1, APP-Q2 | Main application project — OutputType=WinExe, TargetFramework=net480, NuGet dependencies |
| `src/Directory.Build.props` | INF-Q1, INF-Q11, APP-Q1, APP-Q2, SEC-Q3, SEC-Q5 | Shared build properties — TargetFramework, Tokens for credential injection, PostBuild plugin copy |
| `src/Directory.Build.targets` | SEC-Q5 | Token replacement system for credential templates at build time |
| `src/global.json` | APP-Q1 | .NET SDK version 9.0.311 |
| `src/version.json` | INF-Q11 | Nerdbank.GitVersioning configuration |
| `src/Greenshot.sln` | APP-Q2, OPS-Q6 | Solution file — 12 projects, no test projects |
| `src/Greenshot/GreenshotMain.cs` | INF-Q5, OPS-Q4 | Entry point — TLS 1.2/1.3 enforcement, unhandled exception handling with BugReportForm |
| `src/Greenshot/Helpers/PluginHelper.cs` | INF-Q3, APP-Q2 | Dynamic plugin loading via assembly scanning, IGreenshotPlugin interface |
| `src/Greenshot/Destinations/FileDestination.cs` | INF-Q3, DATA-Q1, DATA-Q2 | Local filesystem screenshot save via ImageIO.Save |
| `src/Greenshot/log4net-release.xml` | SEC-Q1, OPS-Q1 | Release logging config — RollingFileAppender, INFO level, ISO8601 timestamps |
| `src/Greenshot/App.config` | INF-Q2 | Application configuration — .NET Framework runtime, DPI awareness |
| `src/Greenshot.Base/Greenshot.Base.csproj` | APP-Q1, SEC-Q1, OPS-Q1 | Core library NuGet packages — log4net, ImageSharp, Dapplo.Windows, HtmlAgilityPack |
| `src/Greenshot.Editor/Greenshot.Editor.csproj` | APP-Q1 | Editor component — ImageSharp.Drawing, System.Reactive.Linq |
| `src/Greenshot.Base/Core/NetworkHelper.cs` | INF-Q4, INF-Q5, APP-Q3, OPS-Q1 | HTTP communication — all synchronous HttpWebRequest, SSL validation bypass |
| `src/Greenshot.Base/Core/OAuth/OAuth2Helper.cs` | INF-Q4, APP-Q3, SEC-Q3 | OAuth2 implementation — 3 authorization modes, synchronous token management |
| `src/Greenshot.Base/IniFile/IniConfig.cs` | INF-Q2, DATA-Q2 | Local INI file configuration management |
| `src/Greenshot.Plugin.Imgur/ImgurUtils.cs` | INF-Q4, APP-Q3, APP-Q4, DATA-Q1 | Imgur upload — synchronous HttpWebRequest, Client-ID authorization |
| `src/Greenshot.Plugin.Imgur/Greenshot.Plugin.Imgur.Credentials.template` | SEC-Q3, SEC-Q5 | Credential template — `${Imgur13_ClientId}` and `${Imgur13_ClientSecret}` placeholders |
| `src/Greenshot.Plugin.Box/BoxUtils.cs` | INF-Q4, APP-Q3, APP-Q4, APP-Q6, DATA-Q1, DATA-Q2, SEC-Q2 | Box upload — synchronous OAuth2 upload, hard-coded API URLs, token storage in INI |
| `src/Greenshot.Plugin.Box/Greenshot.Plugin.Box.Credentials.template` | SEC-Q3, SEC-Q5 | Credential template — `${Box13_ClientId}` and `${Box13_ClientSecret}` placeholders |
| `src/Greenshot-Installer/Greenshot-Installer.csproj` | SEC-Q6 | Installer build — InnoSetup, signtool.exe code signing, SHA256 hash generation |
| `.github/workflows/release.yml` | INF-Q11, OPS-Q5, OPS-Q6, SEC-Q5, SEC-Q7 | Main CI/CD pipeline — build + deploy, no tests, GitHub Secrets for credentials |
| `.github/workflows/choco-publish.yml` | INF-Q11, OPS-Q5 | Chocolatey package publishing automation |
| `.github/workflows/purge-cloudflare-cache.yml` | INF-Q11 | CloudFlare CDN cache purge on page build |
| `.github/workflows/update-gh-pages.yml` | INF-Q11 | GitHub Pages rebuild trigger |
| `.github/copilot-instructions.md` | INF-Q11, OPS-Q6 | Comprehensive developer guide — confirms no test projects, documents build process |
| `build-and-deploy.ps1` | INF-Q11, OPS-Q5 | Manual release script for signed stable releases |
| `docs/release-management.md` | OPS-Q5 | Release process documentation — versioning, stable vs unstable builds |
| `README.md` | Quick Agent Wins | Project overview, build instructions, contribution guidelines |
| `CONTRIBUTING.md` | Quick Agent Wins | Coding conventions and style guide |
| `SECURITY.md` | OPS-Q7, SEC-Q7 | Vulnerability disclosure policy |
| `src/Greenshot.Base/Interfaces/Plugin/IGreenshotPlugin.cs` | APP-Q2 | Plugin interface definition |
