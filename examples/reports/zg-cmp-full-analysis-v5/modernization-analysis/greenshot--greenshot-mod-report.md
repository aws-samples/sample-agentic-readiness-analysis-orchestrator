# Modernization Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | greenshot |
| **Date** | 2026-04-30 |
| **TD Version** | Modernization Analysis v1.0 |
| **Repo Type** | monorepo |
| **Service Archetype** | stateless-utility (auto-detected) |
| **Priority** | P2 |
| **Tags** | csharp, desktop, windows |
| **Context** | Windows screenshot and annotation tool. |
| **Overall Score** | 1.68 / 4.0 |

**Archetype Justification**: This is a Windows desktop GUI application (WinForms/WPF) with OutputType `WinExe`. It has no HTTP server/API surface, no persistent database, no message queues, and no downstream service fan-out. All operations are local screen capture, image editing, and file I/O. Classified as `stateless-utility`.

**Surface Flags**: has_persistent_data_store=false, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=false, has_multi_instance_deployment=false

> **Note**: Greenshot is a Windows desktop application, not a cloud-native service. Many analysis questions evaluate cloud infrastructure maturity — VPCs, managed databases, auto-scaling, CloudTrail, distributed tracing — which are not applicable to the desktop application model. The low overall score reflects the absence of cloud infrastructure, not a failure to implement it where it would be appropriate. The analysis is most actionable in the areas of CI/CD maturity (INF-Q11), security pipeline (SEC-Q7), testing (OPS-Q6), and application language modernization (APP-Q1).

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.17 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.00 / 4.0 | 🟠 Needs Work |
| Data Platform Modernization (DATA) | 2.75 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.50 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.00 / 4.0 | ❌ Not Present |
| **Overall** | **1.68 / 4.0** | **🟠 Needs Work** |

**Scoring Notes:**
- **INF**: 5 of 11 questions excluded (INF-Q2, INF-Q3, INF-Q4, INF-Q8, INF-Q9 — Not Evaluated due to surface flags and archetype). Score based on 6 evaluated questions.
- **APP**: 2 of 6 questions excluded (APP-Q3, APP-Q4 — Not Evaluated for stateless-utility archetype). Score based on 4 evaluated questions.
- **DATA**: All 4 questions evaluated.
- **SEC**: 1 of 7 questions excluded (SEC-Q2 — Not Evaluated due to surface flag). Score based on 6 evaluated questions.
- **OPS**: 1 of 9 questions excluded (OPS-Q2 — Not Evaluated due to surface flags). Score based on 8 evaluated questions.

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | OPS-Q6: Integration Testing | 1 | No automated tests of any kind found in the repository — no unit tests, integration tests, or test projects. | Regressions go undetected; every code change carries risk of breaking existing functionality. Blocks safe modernization and refactoring. |
| 2 | SEC-Q7: Application Security Pipeline | 1 | No SAST, DAST, or dependency vulnerability scanning in CI/CD. No Dependabot configuration. | Vulnerable dependencies and code-level security issues reach production undetected. NuGet packages are not audited for known CVEs. |
| 3 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC files found. All infrastructure (GitHub Pages, CloudFlare, Chocolatey) is configured manually. | Infrastructure changes are non-reproducible and manual. No disaster recovery path for build/release infrastructure. |
| 4 | APP-Q1: Programming Languages | 2 | .NET Framework 4.8 (net480) — legacy runtime. Modern .NET (6/7/8/9/10) not adopted despite SDK 9.0 build tooling. | .NET Framework 4.8 is in maintenance mode. Blocks access to modern .NET performance improvements, cross-platform capability, and modern library ecosystem. |
| 5 | INF-Q11: CI/CD Automation | 2 | CI/CD automates build and release publishing but has no test stage, no IaC deployment, and no security scanning. | Pipeline provides no quality gates — builds and releases happen without automated verification. |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** INF-Q11 = 2 (CI/CD pipeline exists). GitHub Actions workflows (`release.yml`, `choco-publish.yml`) provide build and release automation.
- **What it enables:** An agent that can trigger builds, check release status, monitor GitHub Releases, and manage Chocolatey package publishing. Could also automate version bumping and changelog generation.
- **Additional steps:** GitHub Actions API access needs to be configured for agent invocation. Release workflow could expose a webhook or use `workflow_dispatch` (already configured in `release.yml`).
- **Effort:** Low — existing `workflow_dispatch` trigger in `release.yml` provides the invocation surface.

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists in repository. Found: `README.md` (developer getting started guide), `CONTRIBUTING.md` (coding standards), `docs/release-management.md` (versioning and release process), `TEXT_OBFUSCATION_FEATURE.md` (feature documentation), `SECURITY.md` (vulnerability reporting).
- **What it enables:** A RAG-based knowledge agent that indexes existing documentation to answer developer questions about build process, release management, coding standards, and feature implementation patterns.
- **Additional steps:** Documentation corpus is relatively small — consider supplementing with code comments and inline documentation from source files. An Amazon Bedrock knowledge base with S3-hosted documentation would provide the retrieval layer.
- **Effort:** Medium — documentation needs to be indexed and hosted; Bedrock knowledge base setup required.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 (modular monolith with clear plugin boundaries). Primary trigger requires APP-Q2 < 3. |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 1 and no container definitions found, BUT this is a Windows desktop application (WinExe) — containerization is not the appropriate modernization path for a desktop GUI application distributed as an installer. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (no stored procedures) and no commercial database engines detected. Primary trigger requires DATA-Q4 < 3. |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 is Not Evaluated (no database exists). Pathway trigger requires INF-Q2 < 3 on a scored question. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 is Not Evaluated and no data processing workloads exist. Contextual guard prevents trigger. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (no IaC). Primary trigger met. Supporting: OPS-Q5 = 1 (no staged deployment), OPS-Q6 = 1 (no integration tests). |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in context. Context is "Windows screenshot and annotation tool." — no AI-related signal terms found. |

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

#### Current State

- **IaC Coverage (INF-Q10 = 1):** No infrastructure-as-code files found in the repository. All infrastructure — GitHub Pages configuration, CloudFlare CDN settings, Chocolatey package repository — is configured manually outside the repository.
- **CI/CD State (INF-Q11 = 2):** GitHub Actions workflows exist and automate build (`release.yml`), Chocolatey publishing (`choco-publish.yml`), CloudFlare cache purge (`purge-cloudflare-cache.yml`), and GitHub Pages updates (`update-gh-pages.yml`). However, the pipeline lacks test stages, security scanning, and has no automated quality gates. A separate PowerShell script (`build-and-deploy.ps1`) handles signed release builds outside of CI/CD.
- **Deployment Strategy (OPS-Q5 = 1):** Releases are published directly to GitHub Releases and Chocolatey with no staged rollout, canary, or beta channel.
- **Integration Testing (OPS-Q6 = 1):** No automated tests of any kind found in the repository. No test projects in the solution.

#### Recommendations

1. **Add Automated Testing to CI/CD Pipeline**
   - Create test projects (e.g., `Greenshot.Tests`, `Greenshot.Editor.Tests`) using a .NET testing framework (xUnit, NUnit, or MSTest).
   - Add a test stage to `release.yml` that runs after build and before release artifact creation.
   - Start with unit tests for core logic (image processing, configuration parsing, plugin loading).

2. **Add Security Scanning to CI/CD Pipeline**
   - Add Dependabot configuration (`.github/dependabot.yml`) for NuGet package vulnerability monitoring.
   - Add `dotnet list package --vulnerable` check to the build pipeline.
   - Consider adding a SAST tool (e.g., Semgrep, SonarQube) as a pipeline step.

3. **Implement Staged Release Distribution**
   - Use GitHub Releases pre-release flag (already partially in place — `prerelease: true` in `release.yml`) as a beta channel.
   - Add a promotion workflow: pre-release → stable release after validation period.
   - Consider Chocolatey pre-release package support for staged distribution.

4. **Infrastructure as Code**
   - Define GitHub repository settings, branch protection rules, and Actions secrets via Terraform GitHub provider or GitHub CLI scripts.
   - Document CloudFlare configuration in IaC (Terraform CloudFlare provider).

#### Representative AWS Services
- **AWS CodeBuild / CodePipeline** — Alternative CI/CD if migrating from GitHub Actions.
- **Amazon S3 + CloudFront** — Managed download distribution for installer artifacts (alternative to GitHub Releases).
- **AWS CodeArtifact** — Package management for NuGet dependencies.

#### Relevant AWS Prescriptive Guidance
- [AWS DevOps Best Practices](https://docs.aws.amazon.com/prescriptive-guidance/latest/best-practices-devops/introduction.html)
- [CI/CD Pipeline on AWS](https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/create-a-ci-cd-pipeline.html)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS compute resources (ECS, EKS, Lambda, Fargate, EC2) are defined anywhere in the repository. Greenshot is a Windows desktop application (`OutputType: WinExe` in `src/Greenshot/Greenshot.csproj`) distributed as an installer executable and portable ZIP archive via GitHub Releases and Chocolatey. The application runs entirely on end-user Windows machines. |
| **Gap** | No cloud compute infrastructure exists. The application has no server-side component and no AWS compute footprint. |
| **Recommendation** | This gap is expected for a desktop application. If Greenshot were to add a cloud backend (e.g., for screenshot cloud storage, sync, or collaboration features), managed compute services like AWS Lambda (via API Gateway) or Amazon ECS on Fargate would be appropriate starting points. |
| **Evidence** | `src/Greenshot/Greenshot.csproj` (OutputType=WinExe), `.github/workflows/release.yml` (builds installer/ZIP, publishes to GitHub Releases), `build-and-deploy.ps1` (manual release script). No `.tf`, `.cfn.yaml`, `cdk.json`, or any IaC files found. |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy a database. Greenshot is a desktop application that stores data (screenshots, configuration) on the local file system. No database connections, drivers, ORM configurations, or database resources exist in the codebase or infrastructure. INF-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database driver imports in any `.csproj` file. No `ConnectionString` in `App.config`. No SQL files, migration files, or ORM configurations. Surface flag `has_persistent_data_store=false`. |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Workflow orchestration is not applicable by design — no multi-step workflows exist for a desktop screenshot and annotation tool. All operations are local, single-step actions (capture screen, edit image, export to destination). |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/Greenshot/Greenshot.csproj` (WinExe), `src/Greenshot/Destinations/` (single-step export destinations), `src/Greenshot/Helpers/CaptureHelper.cs` (capture operations). No Step Functions, Temporal, or workflow definitions found. |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Synchronous local operations are the correct design for a desktop application. The application captures screenshots, edits them locally, and exports to destinations (file, clipboard, cloud services) — all synchronous local operations. Async messaging infrastructure would add complexity without architectural benefit. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/Greenshot/Destinations/` (all destinations are synchronous local operations or HTTP uploads). No SQS, SNS, EventBridge, Kafka, or RabbitMQ references in any file. |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, security groups, NACLs, or any network infrastructure is defined. Greenshot is a desktop application with no server-side cloud infrastructure. The application makes outbound HTTPS calls to third-party APIs (Imgur, Box, Dropbox, Confluence, Jira) from the end-user's machine. |
| **Gap** | No cloud network security surface exists. This is expected for a desktop application. |
| **Recommendation** | If a cloud backend is added, deploy services in private subnets with least-privilege security groups. Use VPC endpoints for AWS service access and API Gateway as the entry point. |
| **Evidence** | No `.tf` files defining `aws_vpc`, `aws_subnet`, or `aws_security_group`. No CloudFormation or CDK network resources. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or any managed entry point exists. The application has no server-side API surface. Greenshot acts as an API client to third-party services, not an API server. |
| **Gap** | No cloud API entry point. Expected for a desktop application. |
| **Recommendation** | If a cloud API is introduced (e.g., screenshot cloud storage), use Amazon API Gateway with authentication, throttling, and request validation as the entry point. |
| **Evidence** | No `aws_api_gateway_*`, `aws_lb_*`, `aws_cloudfront_*` in any IaC. No server-side HTTP listener in source code. Surface flag `has_api_surface=false`. |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. No cloud compute workloads to scale. Desktop application scaling is determined by the number of user installations, not infrastructure scaling policies. |
| **Gap** | No auto-scaling. Expected for a desktop application with no cloud compute. |
| **Recommendation** | If cloud services are introduced, configure auto-scaling from the outset. Lambda provides implicit scaling; ECS/EKS require explicit auto-scaling policies with custom metrics. |
| **Evidence** | No `aws_autoscaling_*`, `aws_appautoscaling_*`, or scaling policies in any file. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no persistent state to back up. Greenshot stores screenshots and configuration on the local user's file system. No server-side data stores, S3 buckets, or managed databases exist. INF-Q8 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | Surface flags `has_persistent_data_store=false`, `has_at_rest_data_surface=false`. No backup configuration in any file. |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload requiring HA evaluation. Greenshot runs on individual user machines as a desktop application. There is no server-side deployment to distribute across Availability Zones. INF-Q9 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | Surface flag `has_deployed_workload=false`. No IaC defining compute resources. No multi-AZ configuration. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No Infrastructure as Code files found in the repository. No Terraform, CloudFormation, CDK, Helm, Kustomize, or Ansible files exist. All supporting infrastructure (GitHub repository settings, branch protection, GitHub Pages, CloudFlare CDN configuration, Chocolatey package repository) is configured manually. |
| **Gap** | 0% IaC coverage. All infrastructure is manually configured (ClickOps). Repository settings, CI/CD secrets, CloudFlare configuration, and Chocolatey publishing configuration are not codified. |
| **Recommendation** | Codify repository configuration using the Terraform GitHub provider or GitHub CLI scripts. Define CloudFlare configuration using the Terraform CloudFlare provider. Store all configuration as code in the repository for reproducibility and auditability. |
| **Evidence** | No files with extensions `.tf`, `.tfvars`, `.cfn.yaml`, `.cfn.json`. No `cdk.json`. No `Chart.yaml`. No `kustomization.yaml`. Full directory scan confirms absence. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GitHub Actions workflows automate the build and release process: `release.yml` builds the solution, creates installer and portable ZIP, publishes to GitHub Releases; `choco-publish.yml` publishes to Chocolatey on release; `purge-cloudflare-cache.yml` purges CDN cache on page builds; `update-gh-pages.yml` triggers GitHub Pages rebuild. However, **no test stage exists** in any workflow — builds proceed directly to packaging and release. No IaC deployment automation. A separate manual PowerShell script (`build-and-deploy.ps1`) handles signed release builds outside CI/CD. |
| **Gap** | Build is automated but no automated testing, no security scanning, and stable release builds require a manual process (`build-and-deploy.ps1`) for code signing. The CI/CD pipeline provides no quality gates. |
| **Recommendation** | Add a test stage to `release.yml` between build and artifact upload. Add dependency vulnerability scanning (`dotnet list package --vulnerable`). Add Dependabot configuration for NuGet packages. Investigate code signing integration into GitHub Actions to eliminate the manual `build-and-deploy.ps1` workflow. |
| **Evidence** | `.github/workflows/release.yml` (build + release, no test step), `.github/workflows/choco-publish.yml` (Chocolatey publishing), `.github/workflows/purge-cloudflare-cache.yml`, `.github/workflows/update-gh-pages.yml`, `build-and-deploy.ps1` (manual signed release), `docs/release-management.md` (documents dual-track release process). |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Greenshot is written in C# targeting **.NET Framework 4.8.0** (`net480` in `src/Directory.Build.props`). The build tooling uses .NET SDK 9.0.311 (`src/global.json`), and SDK-style project files are used (`Microsoft.NET.Sdk.WindowsDesktop`), but the actual runtime target is the legacy .NET Framework 4.x — not modern .NET (6/7/8/9/10). The application uses WinForms and WPF (`UseWindowsForms=true`, `UseWPF=true`). Key dependencies include: `log4net 3.3.0`, `SixLabors.ImageSharp 2.1.13`, `Dapplo.Windows 2.0.89`, `HtmlAgilityPack 1.12.4`, `System.Reactive.Linq 6.1.0`. |
| **Gap** | .NET Framework 4.8 is in maintenance mode — Microsoft is investing in modern .NET (currently .NET 10). The framework runtime blocks access to modern .NET performance improvements (Span<T>, hardware intrinsics, HTTP/3), cross-platform capability, and the modern NuGet library ecosystem. Compound legacy: legacy runtime (.NET Framework 4.8) + legacy UI framework (WinForms/WPF on .NET Framework). |
| **Recommendation** | Migrate from `net480` to `net8.0-windows` or `net10.0-windows` (modern .NET with Windows Desktop support). WinForms and WPF are supported on modern .NET. This enables: modern C# language features, improved performance, access to modern NuGet packages, and long-term support. Start with a porting analysis using `upgrade-assistant` tool. |
| **Evidence** | `src/Directory.Build.props` (`<TargetFramework>net480</TargetFramework>`, `<UseWPF>true</UseWPF>`, `<UseWindowsForms>true</UseWindowsForms>`), `src/global.json` (SDK 9.0.311), `src/Greenshot/Greenshot.csproj` (`Microsoft.NET.Sdk.WindowsDesktop`), `README.md` (".net Framework 4.8.0"). |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Greenshot is a single deployable unit (WinExe) with a well-defined plugin architecture. The codebase is organized into clear modules: `Greenshot.Base` (shared interfaces, core services, OAuth, configuration), `Greenshot.Editor` (image editor component), and 6 plugins (`Box`, `Confluence`, `Dropbox`, `ExternalCommand`, `Imgur`, `Jira`, `Office`). Plugins implement the `IGreenshotPlugin` interface and are loaded dynamically via `PluginHelper.LoadPlugins()` which scans for `Greenshot.Plugin.*.dll` files. A `SimpleServiceProvider` (service locator pattern) manages plugin registration and discovery. Plugin DLLs are copied to a `Plugins/` subdirectory during build. Each plugin can be independently configured and has its own configuration section. |
| **Gap** | While module boundaries are clear, all modules deploy as a single application — there is no independent deployment or scaling of individual components. The `SimpleServiceProvider` service locator pattern is functional but less robust than full dependency injection. Some cross-cutting concerns (configuration, OAuth) are tightly coupled through `Greenshot.Base`. |
| **Recommendation** | The current modular monolith architecture is appropriate for a desktop application. No decomposition is recommended. If cloud features are added in the future, the plugin architecture provides natural seams for extracting cloud-specific functionality into separate services. Consider migrating from service locator to constructor injection (e.g., `Microsoft.Extensions.DependencyInjection`) for improved testability. |
| **Evidence** | `src/Greenshot.Base/Interfaces/Plugin/IGreenshotPlugin.cs` (plugin interface), `src/Greenshot/Helpers/PluginHelper.cs` (dynamic plugin loading), `src/Greenshot.Base/Core/SimpleServiceProvider.cs` (service locator), `src/Directory.Build.props` (PostBuild target copies plugin DLLs). |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Synchronous request/response is the correct design for a desktop application — no inter-service communication exists. The application makes outbound HTTP calls to third-party APIs (Imgur, Box, Dropbox, Confluence, Jira) as a client, but these are user-initiated upload actions, not service-to-service communication patterns. Async communication patterns are not applicable. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/Greenshot/Destinations/` (export destinations make HTTP calls), `src/Greenshot.Base/Core/OAuth/` (OAuth2 client flows). No message queues, event buses, or service-to-service communication. |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. No operations exceed 30 seconds by design — screen capture is instantaneous, image editing is local, and exports to destinations are bounded by file size (typically < 5MB for screenshots). The OCR feature (Win10OcrDestination) uses the Windows 10 built-in OCR engine which processes single-image OCR in sub-second timeframes. No long-running process handling is needed. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/Greenshot/Helpers/CaptureHelper.cs` (capture operations), `src/Greenshot/Destinations/` (export operations), `src/Greenshot/Destinations/Win10OcrDestination.cs` (OCR). No background job frameworks, async polling patterns, or job status APIs. |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Greenshot has no API surface — it is a desktop application, not an API server. No OpenAPI specifications, versioned endpoints, or API contracts exist. The application consumes third-party APIs (Imgur, Box, Dropbox, Confluence, Jira) as a client using plugin-specific HTTP helpers and OAuth flows, but does not expose any APIs of its own. |
| **Gap** | No API versioning strategy because no API exists. This is expected for a desktop application. |
| **Recommendation** | If Greenshot adds a cloud backend API, establish a versioning strategy from the start (e.g., URL-path versioning `/v1/screenshots`). Use Amazon API Gateway with stage-based versioning. Define API contracts in OpenAPI format. |
| **Evidence** | No `openapi.yaml`, `swagger.yaml`, or `.graphql` files. No HTTP server/listener code. No `/v1/`, `/v2/` URL patterns. Surface flag `has_api_surface=false`. |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Greenshot uses file-system-based plugin discovery — `PluginHelper.LoadPlugins()` scans for `Greenshot.Plugin.*.dll` files in the application directory or portable application directory. For third-party API endpoints, configuration is managed through `IniConfig` (INI-file based configuration system) where users configure server URLs for Confluence and Jira instances. Cloud service endpoints (Imgur, Box, Dropbox) are likely hardcoded in plugin code as they are fixed SaaS endpoints. |
| **Gap** | Third-party API endpoints are a mix of hardcoded (SaaS services) and user-configured (Confluence, Jira) with no dynamic service discovery. This is acceptable for a desktop application but limits flexibility. |
| **Recommendation** | The current approach (hardcoded SaaS endpoints + user-configured enterprise endpoints) is appropriate for a desktop application. No changes recommended unless a cloud backend is introduced, in which case use environment-variable-based endpoint configuration or AWS Service Discovery. |
| **Evidence** | `src/Greenshot/Helpers/PluginHelper.cs` (`FindPluginsOnPath()`, `LoadPlugins()` scanning for DLLs), `src/Greenshot.Base/IniFile/` (INI configuration system), plugin `.csproj` files referencing Dapplo HTTP extension libraries for API communication. |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Screenshots and annotated images are stored on the local file system of the user's Windows machine. The application saves captured images to a user-configured directory (default: `%USERPROFILE%\Documents\Greenshot`). No managed object storage (S3) is used. No parsing pipeline (Textract, Tika) exists. Export destinations include clipboard, local file, printer, email, and cloud upload services (Imgur, Box, Dropbox) — but the cloud uploads are transient exports, not persistent managed storage. |
| **Gap** | Unstructured data (screenshots) is stored on local file systems with no managed storage, backup, or parsing capabilities. Users risk data loss if their machine fails. |
| **Recommendation** | If a cloud storage feature is desired, use Amazon S3 for screenshot storage with lifecycle policies. Pair with Amazon Textract for OCR text extraction from screenshots (complementing the existing Win10 OCR feature). Amazon S3 File Gateway could bridge the gap for users who want cloud backup with a file-system interface. |
| **Evidence** | `src/Greenshot/Destinations/FileDestination.cs` (saves to local filesystem), `src/Greenshot/Destinations/ClipboardDestination.cs` (copies to clipboard), plugin destinations (upload to Imgur/Box/Dropbox as transient exports). No `aws_s3_bucket` or S3 SDK references. |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Greenshot uses the Destinations pattern as a partially centralized output layer — all screenshot exports route through `IDestination` implementations (`FileDestination`, `ClipboardDestination`, `EmailDestination`, `PrinterDestination`, and plugin destinations). Configuration is managed through a centralized `IniConfig` system (`src/Greenshot.Base/IniFile/`). However, file I/O operations (reading/writing images) are scattered across multiple classes (`ImageIO`, `CaptureHelper`, individual destinations). There is no unified data access layer in the traditional sense because there is no database. |
| **Gap** | File I/O operations are distributed across multiple classes without a single point of control. The `IDestination` pattern provides output abstraction but does not cover input (image loading, configuration reading). |
| **Recommendation** | If data access becomes more complex (e.g., adding cloud storage), introduce a unified storage abstraction layer that encapsulates all I/O operations (local file, S3, cloud services) behind a single interface. The existing `IDestination` pattern is a good foundation for this. |
| **Evidence** | `src/Greenshot/Destinations/` (destination implementations), `src/Greenshot.Base/IniFile/` (centralized configuration), `src/Greenshot.Base/Core/SimpleServiceProvider.cs` (service locator for destinations). |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No database engine is used by Greenshot. The application has no database connections, SQL files, ORM configurations, or database driver dependencies. Configuration is stored in INI files on the local file system. Therefore, there are no database engine versions to manage and no EOL risk from database engines. |
| **Gap** | N/A — no database engines to evaluate. |
| **Recommendation** | N/A — no action needed. If a database is introduced in the future, ensure engine versions are explicitly pinned in IaC and establish a version update procedure. |
| **Evidence** | No database-related NuGet packages in any `.csproj` file. No `ConnectionString` in configuration files. No `.sql` files in the repository. No database resource definitions in IaC (no IaC exists). |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs exist. All business logic resides in the C# application layer. The application has no database and therefore no database-coupled logic. Image processing, annotation, and export logic are entirely in application code. |
| **Gap** | N/A — no database coupling. |
| **Recommendation** | N/A — the current architecture correctly places all logic in the application layer. |
| **Evidence** | No `.sql` files in repository. No `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION` statements. No ORM configurations. Full repository scan confirms absence. |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or cloud-based audit logging exists. The application uses `log4net 3.3.0` for local file-based logging (`src/Greenshot/log4net-release.xml`). Logs are written to `%LOCALAPPDATA%\Greenshot\Greenshot.log` with rolling file appender (3 backups, 1MB max per file). Log format includes ISO8601 timestamps, thread ID, log level, logger name, and message. This is application-level logging, not security audit logging. |
| **Gap** | No cloud audit trail. No immutable log storage. Local log files can be modified or deleted by the user. This is expected for a desktop application with no cloud infrastructure. |
| **Recommendation** | If a cloud backend is added, enable CloudTrail with log file validation and immutable S3 storage (Object Lock). For the desktop application, the current log4net configuration is adequate for troubleshooting. |
| **Evidence** | `src/Greenshot/log4net-release.xml` (rolling file appender to local filesystem), `src/Greenshot.Base/Greenshot.Base.csproj` (`log4net 3.3.0` dependency). No `aws_cloudtrail` or cloud logging configuration. |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no database, S3 bucket, EBS volume, or similar managed storage. Screenshots are stored on the local user's file system, which is outside the scope of cloud encryption-at-rest evaluation. SEC-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | Surface flag `has_at_rest_data_surface=false`. No S3 buckets, RDS instances, DynamoDB tables, or EBS volumes in IaC. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Greenshot does not expose an API — it is a desktop application. However, it acts as an OAuth2 client when connecting to third-party services. The `src/Greenshot.Base/Core/OAuth/` directory contains OAuth2 implementation (`OAuth2Helper.cs`, `OAuth2Settings.cs`, `OAuthSession.cs`) supporting authorization code flow with local server code receiver (`LocalServerCodeReceiver.cs`). Plugin credentials (client IDs and secrets for Imgur, Box, Dropbox) are managed through template files and injected at build time via environment variables. |
| **Gap** | OAuth2 client credentials (client IDs and secrets) are embedded in the distributed binary after build-time template injection. While not present as plaintext in source control (template placeholders used), the compiled binary contains these credentials. API key auth is used for some integrations rather than full OAuth2 token-based auth. |
| **Recommendation** | For third-party API integrations, continue using OAuth2 authorization code flow (already implemented). Consider moving client credentials to a configuration service rather than embedding in binaries. If a cloud API backend is introduced, implement per-request JWT authentication with Amazon Cognito. |
| **Evidence** | `src/Greenshot.Base/Core/OAuth/OAuth2Helper.cs`, `src/Greenshot.Base/Core/OAuth/OAuth2Settings.cs`, `src/Greenshot.Base/Core/OAuth/LocalServerCodeReceiver.cs`, `src/Greenshot.Plugin.Imgur/Greenshot.Plugin.Imgur.Credentials.template`, `src/Greenshot.Plugin.Box/Greenshot.Plugin.Box.Credentials.template`, `src/Greenshot.Plugin.Dropbox/Greenshot.Plugin.Dropbox.Credentials.template`. |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Greenshot uses OAuth2 to federate with external identity providers for third-party service access (Imgur, Box, Dropbox). Users authenticate directly with each cloud service through OAuth2 authorization code flow. For Confluence and Jira integrations, the application supports user-configured server connections. There is no single centralized identity provider — each plugin manages its own authentication independently. |
| **Gap** | No centralized IdP integration. Each plugin manages its own OAuth2 flows independently. This means users must authenticate separately with each service. |
| **Recommendation** | If a unified cloud experience is desired, introduce Amazon Cognito as a centralized identity provider with social identity federation (Google, Microsoft). This would provide SSO across all cloud integrations. For enterprise use (Confluence, Jira), support SAML/OIDC federation with corporate IdPs. |
| **Evidence** | `src/Greenshot.Base/Core/OAuth/` (per-plugin OAuth2 flows), plugin credential template files (per-plugin client credentials). No Cognito, Okta, or centralized OIDC configuration. |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | API credentials are managed through a build-time template system. Credential template files (e.g., `Greenshot.Plugin.Imgur.Credentials.template`) contain placeholders like `${Imgur13_ClientId}` that are replaced at build time with values from environment variables. The `Directory.Build.targets` file defines a custom MSBuild task (`ApplyTokenReplacements`) that performs this substitution, generating `.credentials.cs` files. Generated credential files are gitignored (`*.credentials.cs` in `.gitignore`). In CI/CD, values come from GitHub Secrets (`${{ secrets.Imgur13_ClientId }}`). No Secrets Manager or Vault integration. No rotation configured. |
| **Gap** | No dedicated secrets management service. Credentials are injected via environment variables at build time — they are not rotated, not audited, and end up embedded in compiled binaries. While no plaintext credentials exist in source control, the pattern lacks rotation and centralized management. |
| **Recommendation** | For build-time secrets, the current GitHub Secrets approach is acceptable. Add secret rotation procedures — rotate API credentials periodically and re-deploy. For runtime secrets in any future cloud backend, use AWS Secrets Manager with automated rotation. Consider using Azure Key Vault or similar for desktop application credential management if client credentials need runtime refresh. |
| **Evidence** | `src/Greenshot.Plugin.Imgur/Greenshot.Plugin.Imgur.Credentials.template` (placeholder pattern), `src/Greenshot.Plugin.Box/Greenshot.Plugin.Box.Credentials.template`, `src/Greenshot.Plugin.Dropbox/Greenshot.Plugin.Dropbox.Credentials.template`, `src/Directory.Build.targets` (ApplyTokenReplacements task), `src/Directory.Build.props` (Tokens ItemGroup), `.github/workflows/release.yml` (GitHub Secrets injection), `.gitignore` (`*.credentials.cs` excluded). |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No cloud compute resources exist to harden or patch. The application runs on end-user Windows machines. No SSM Patch Manager, no vulnerability scanning (Inspector/Snyk), no hardened base images. The CI/CD builds run on GitHub-hosted `windows-latest` runners which are managed by GitHub, but no additional hardening is applied to the build environment. |
| **Gap** | No compute hardening or patching strategy. The CI/CD build environment relies on GitHub's default `windows-latest` runner with no additional security controls. |
| **Recommendation** | Add dependency vulnerability scanning to the CI/CD pipeline (e.g., `dotnet list package --vulnerable`, NuGet audit). Consider using GitHub's built-in Dependabot for NuGet package monitoring. For the desktop application binary, consider code signing (partially addressed in `build-and-deploy.ps1` manual process) and implement Software Bill of Materials (SBOM) generation. |
| **Evidence** | `.github/workflows/release.yml` (`runs-on: windows-latest` — default GitHub runner), `build-and-deploy.ps1` (manual code-signing process). No SSM, Inspector, or Snyk configuration. |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No security scanning tools are integrated into the CI/CD pipeline. No SAST (SonarQube, Semgrep, CodeGuru), no DAST, no dependency vulnerability scanning (Dependabot, `dotnet list package --vulnerable`), and no container scanning (no containers exist). The `.github/` directory contains no `dependabot.yml` configuration. No `.snyk` policy file exists. The pipeline builds and releases without any security validation step. |
| **Gap** | No security scanning of any kind in the pipeline. Vulnerable NuGet dependencies and code-level security issues reach production undetected. |
| **Recommendation** | 1) Add `.github/dependabot.yml` for automated NuGet vulnerability monitoring. 2) Add `dotnet list package --vulnerable` to the build pipeline. 3) Add a SAST tool (Semgrep with C# support, or SonarQube Community Edition) as a pipeline step. 4) Consider GitHub Advanced Security code scanning if available. |
| **Evidence** | `.github/workflows/release.yml` (no security scanning steps), `.github/workflows/choco-publish.yml` (no scanning). No `.github/dependabot.yml`. No `.snyk` policy file. No SonarQube, Semgrep, or security scanning configuration anywhere in repository. |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing is implemented. The application uses `log4net` for local file-based logging only. No OpenTelemetry SDK, X-Ray instrumentation, or trace ID propagation exists. As a desktop application, distributed tracing across service boundaries is not a primary concern. However, basic structured logging and correlation IDs for HTTP requests to third-party APIs would improve debuggability. |
| **Gap** | No tracing of any kind. HTTP calls to third-party APIs (Imgur, Box, Dropbox, Confluence, Jira) have no correlation IDs for debugging failed uploads. |
| **Recommendation** | For the desktop application, add correlation IDs to outbound HTTP requests for debugging purposes. If a cloud backend is introduced, instrument with OpenTelemetry SDK and propagate trace IDs across all service boundaries. |
| **Evidence** | `src/Greenshot.Base/Greenshot.Base.csproj` (`log4net 3.3.0`), `src/Greenshot/log4net-release.xml` (file-based logging only). No OpenTelemetry, X-Ray, or tracing packages in any `.csproj`. |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no user-facing surface for which SLOs are meaningful. Greenshot is a desktop application — availability and latency are determined by the user's machine, not server-side infrastructure. OPS-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | Surface flags `has_api_surface=false`, `has_persistent_data_store=false`. No SLO definitions, CloudWatch alarms, or error budget tracking. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics are published. No CloudWatch, no telemetry, no analytics integration. The application has no cloud metrics infrastructure. Basic application events (captures, exports, errors) are logged to the local log4net file but not aggregated or analyzed. |
| **Gap** | No visibility into application usage patterns, feature adoption, or error rates across the user base. |
| **Recommendation** | Consider adding opt-in anonymous telemetry to understand feature usage patterns and crash rates. If telemetry is added, use Amazon EventBridge for event ingestion and Amazon CloudWatch for metrics aggregation. Respect user privacy and provide clear opt-out. |
| **Evidence** | No metrics publishing code. No CloudWatch, Application Insights, or telemetry SDK in any `.csproj`. Local `log4net` logging only. |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting is configured. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no error rate monitoring. Errors are logged to local log files only. |
| **Gap** | No proactive error detection. Issues are only discovered when users report them. |
| **Recommendation** | If telemetry is introduced (see OPS-Q3), add anomaly detection on crash rates and error patterns using CloudWatch anomaly detection. For the build/release infrastructure, add GitHub Actions workflow failure notifications. |
| **Evidence** | No alerting configuration in any file. No CloudWatch, PagerDuty, or OpsGenie references. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Releases are published directly to all users simultaneously via GitHub Releases (installer EXE + portable ZIP) and Chocolatey package. The `release.yml` workflow creates a GitHub Release with `prerelease: true` for continuous builds, but there is no staged rollout, beta channel, or canary mechanism. The Chocolatey publication (`choco-publish.yml`) triggers on the `published` release event — once published, the package is available to all Chocolatey users immediately. |
| **Gap** | Direct-to-production deployment with no staged rollout. All users receive the same version simultaneously. No beta channel or phased rollout. Regressions affect the entire user base. |
| **Recommendation** | Implement a staged release strategy: 1) Use GitHub Releases pre-release as a beta channel (partially in place). 2) Add a promotion workflow that moves a pre-release to stable after a validation period. 3) Use Chocolatey's `--pre` flag support to create a beta Chocolatey package. 4) Consider an in-app update mechanism that can target specific user segments (percentage rollout). |
| **Evidence** | `.github/workflows/release.yml` (`prerelease: true` for continuous builds, `softprops/action-gh-release@v2`), `.github/workflows/choco-publish.yml` (publishes on release `published` event), `docs/release-management.md` (describes stable vs unstable release tracks). |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No automated tests of any kind exist in the repository. No unit test projects, no integration test projects, no test files. A search for `*Test*`, `*Tests*`, `*.spec.*`, `*.test.*` across the entire repository found zero results (excluding `emoji-test.txt` which is a data file). The `Directory.Build.props` file references `Tests` and `Demo` project names in conditions but no such projects exist. The `TEXT_OBFUSCATION_FEATURE.md` describes manual testing steps but no automated test implementation. |
| **Gap** | Zero automated test coverage. All testing is manual. This means: 1) No regression protection during code changes. 2) No safety net for refactoring or modernization. 3) No quality gate in the CI/CD pipeline. |
| **Recommendation** | Create test projects (e.g., `Greenshot.Base.Tests`, `Greenshot.Editor.Tests`) using xUnit or NUnit. Start with: 1) Unit tests for core logic (image processing, configuration parsing, plugin loading). 2) Unit tests for the credential template replacement system. 3) Integration tests for OAuth2 flow (mock HTTP). 4) Add a test stage to `release.yml`. Target 50% code coverage for critical paths as an initial milestone. |
| **Evidence** | Full repository search for test files: zero results. `src/Directory.Build.props` (conditions for `Tests`/`Demo` projects but no such projects exist in solution). `TEXT_OBFUSCATION_FEATURE.md` (manual testing instructions only). No test frameworks in any `.csproj` dependency list. |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response runbooks or automation exist. `SECURITY.md` provides a vulnerability reporting path ("report it responsibly in our security section") but no operational runbooks, no automated remediation, and no structured incident response process. |
| **Gap** | No documented incident response process beyond security vulnerability reporting. No runbooks for common issues (failed builds, broken releases, user-reported crashes). |
| **Recommendation** | Create runbooks for: 1) Failed CI/CD builds (diagnosis and remediation steps). 2) Broken release rollback (how to unpublish a GitHub Release and Chocolatey package). 3) Security vulnerability response (expand SECURITY.md with triage and fix process). Store runbooks as Markdown in `docs/runbooks/`. |
| **Evidence** | `SECURITY.md` (vulnerability reporting only, 4 lines). No runbook files. No Systems Manager Automation documents. No incident response automation. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CODEOWNERS file exists. No per-service dashboards, named alarm owners, or team-attributed SLO definitions. The repository has no defined observability ownership structure. Build failures in GitHub Actions are visible to repository maintainers but there is no structured notification or ownership assignment. |
| **Gap** | No observability ownership. No CODEOWNERS. No structured monitoring or alerting with assigned owners. |
| **Recommendation** | Add a `CODEOWNERS` file to define ownership of critical paths (core, editor, plugins, CI/CD). Configure GitHub Actions workflow failure notifications to specific team members. If cloud infrastructure is added, establish per-component observability ownership with named alarm owners. |
| **Evidence** | No `.github/CODEOWNERS` file. No observability configuration files. No dashboards or alarm definitions. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resources exist and therefore no resource tagging. No IaC files where `default_tags` or resource tags would be defined. No tagging standard or governance policy. |
| **Gap** | No resource tagging. Expected for a repository with no AWS infrastructure. |
| **Recommendation** | If AWS resources are introduced, establish a tagging standard from the outset. Use `default_tags` in the Terraform AWS provider to apply consistent tags (Environment, Project, Owner, CostCenter) to all resources. Enforce with AWS Config `required-tags` rules. |
| **Evidence** | No IaC files. No `default_tags` configuration. No Tag Policies or AWS Config rules. |

---

## Learning Materials

### Move to Modern DevOps (Triggered)

- [Move to Modern DevOps — AWS SkillBuilder Learning Plan](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `src/Directory.Build.props` | INF-Q10, INF-Q11, APP-Q1, APP-Q2, SEC-Q5 | Central build configuration: TargetFramework=net480, WPF/WinForms enabled, credential token definitions, plugin PostBuild copy |
| `src/Directory.Build.targets` | SEC-Q5 | ApplyTokenReplacements MSBuild task for credential template processing |
| `src/global.json` | APP-Q1 | .NET SDK version pin: 9.0.311 |
| `src/version.json` | INF-Q11 | Nerdbank.GitVersioning configuration for SemVer version management |
| `src/Greenshot/Greenshot.csproj` | INF-Q1, INF-Q3, APP-Q1, APP-Q2 | Main application project: OutputType=WinExe, Microsoft.NET.Sdk.WindowsDesktop, package dependencies |
| `src/Greenshot.Base/Greenshot.Base.csproj` | APP-Q1, OPS-Q1, SEC-Q1 | Base library: log4net 3.3.0, Dapplo.HttpExtensions, SixLabors.ImageSharp, HtmlAgilityPack |
| `src/Greenshot.Editor/Greenshot.Editor.csproj` | APP-Q1 | Editor component: SixLabors.ImageSharp.Drawing, System.Reactive.Linq |
| `src/Greenshot.Base/Interfaces/Plugin/IGreenshotPlugin.cs` | APP-Q2 | Plugin interface definition: Initialize, Shutdown, Configure, Name, IsConfigurable |
| `src/Greenshot/Helpers/PluginHelper.cs` | APP-Q2, APP-Q6 | Plugin loading: FindPluginsOnPath, LoadPlugins, file-system-based discovery |
| `src/Greenshot.Base/Core/SimpleServiceProvider.cs` | APP-Q2 | Service locator pattern for plugin registration and dependency management |
| `src/Greenshot/Destinations/` | INF-Q3, INF-Q4, APP-Q3, APP-Q4, DATA-Q1, DATA-Q2 | Export destinations: File, Clipboard, Email, Printer, Win10OCR, Win10Share |
| `src/Greenshot/Helpers/CaptureHelper.cs` | INF-Q3, APP-Q4 | Screen capture operations |
| `src/Greenshot/log4net-release.xml` | SEC-Q1, OPS-Q1 | Release logging config: RollingFileAppender, %LOCALAPPDATA%\Greenshot\Greenshot.log |
| `src/Greenshot.Base/Core/OAuth/` | SEC-Q3, SEC-Q4, APP-Q3 | OAuth2 implementation: OAuth2Helper, OAuth2Settings, LocalServerCodeReceiver |
| `src/Greenshot.Plugin.Imgur/Greenshot.Plugin.Imgur.Credentials.template` | SEC-Q3, SEC-Q5 | Imgur credential template: ${Imgur13_ClientId}, ${Imgur13_ClientSecret} |
| `src/Greenshot.Plugin.Box/Greenshot.Plugin.Box.Credentials.template` | SEC-Q3, SEC-Q5 | Box credential template: ${Box13_ClientId}, ${Box13_ClientSecret} |
| `src/Greenshot.Plugin.Dropbox/Greenshot.Plugin.Dropbox.Credentials.template` | SEC-Q3, SEC-Q5 | Dropbox credential template: ${DropBox13_ClientId}, ${DropBox13_ClientSecret} |
| `.github/workflows/release.yml` | INF-Q1, INF-Q11, OPS-Q5, SEC-Q5, SEC-Q7 | CI/CD: build, package, GitHub Release publishing, GitHub Secrets for credentials |
| `.github/workflows/choco-publish.yml` | INF-Q11, OPS-Q5, SEC-Q7 | Chocolatey package publishing on release |
| `.github/workflows/purge-cloudflare-cache.yml` | INF-Q11 | CloudFlare cache purge on page build |
| `.github/workflows/update-gh-pages.yml` | INF-Q11 | GitHub Pages rebuild trigger |
| `build-and-deploy.ps1` | INF-Q1, INF-Q11, SEC-Q6 | Manual release script for signed builds |
| `docs/release-management.md` | INF-Q11, OPS-Q5 | Release process documentation: stable vs unstable, CI vs manual builds |
| `.gitignore` | SEC-Q5 | Excludes `*.credentials.cs` from version control |
| `SECURITY.md` | OPS-Q7 | Vulnerability reporting guidance (4 lines) |
| `README.md` | APP-Q1 | Developer documentation: .NET Framework 4.8.0, VS 2022+, build instructions |
| `CONTRIBUTING.md` | Quick Agent Wins (RAG) | Coding standards documentation |
| `TEXT_OBFUSCATION_FEATURE.md` | OPS-Q6, Quick Agent Wins (RAG) | Feature documentation with manual testing steps (no automated tests) |
| `src/Greenshot.Plugin.Confluence/Greenshot.Plugin.Confluence.csproj` | APP-Q6 | Confluence plugin: Dapplo.Confluence dependency |
| `src/Greenshot.Plugin.Jira/Greenshot.Plugin.Jira.csproj` | APP-Q6 | Jira plugin: Dapplo.Jira, Dapplo.HttpExtensions dependencies |
| `src/Greenshot.Base/IniFile/` | DATA-Q2, APP-Q6 | INI-file configuration system for application and plugin settings |
