# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | greenshot--greenshot |
| **Date** | 2026-05-08 |
| **TD Version** | modernization-assessment |
| **Repo Type** | application |
| **Service Archetype** | stateless-utility (auto-detected) |
| **Priority** | P2 |
| **Tags** | csharp, desktop, windows |
| **Context** | Windows screenshot and annotation tool. |
| **Overall Score** | 1.72 / 4.0 |

**Archetype Justification**: This is a Windows desktop application with no persistent data store, no API surface, no database connections, and no downstream service calls. All operations are local computation (screenshot capture, image processing, annotation). User settings are stored in local INI files on the user's machine. Classified as stateless-utility.

**Surface Flags**: has_persistent_data_store=false, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=false, has_multi_instance_deployment=false, has_iac_provisioning_aws_resources=false

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | 1.17 / 4.0 | ❌ Not Ready | Critical |
| Application Architecture (APP) | 1.75 / 4.0 | 🟠 Needs Work | Critical |
| Data Platform Modernization (DATA) | 3.00 / 4.0 | 🟡 Partial | Ready |
| Security Baseline (SEC) | 1.67 / 4.0 | 🟠 Needs Work | Critical |
| Operations & Observability (OPS) | 1.00 / 4.0 | ❌ Not Ready | Critical |
| **Overall** | **1.72 / 4.0** | **🟠 Needs Work** | |

**Scoring Notes:**
- INF: (1+1+1+1+1+2) / 6 scored = 7/6 = 1.17 [INF-Q2, INF-Q3, INF-Q4, INF-Q8, INF-Q9 Not Evaluated]
- APP: (2+2+1+2) / 4 scored = 7/4 = 1.75 [APP-Q3, APP-Q4 Not Evaluated]
- DATA: (2+3+4) / 3 scored = 9/3 = 3.00 [DATA-Q3 Not Evaluated due to no DB in IaC]
- SEC: (3+1+1) / 3 scored = 5/3 = 1.67 [SEC-Q1, SEC-Q2, SEC-Q3, SEC-Q4 Not Evaluated]
- OPS: (1+1+1+1+1+1+1) / 7 scored = 7/7 = 1.00 [OPS-Q2, OPS-Q5 Not Evaluated]
- Overall: (1.17 + 1.75 + 3.00 + 1.67 + 1.00) / 5 = 8.59 / 5 = 1.72

---

## Classification

**Tier: 🟠 Remediation Required**

This repo has 4 High findings, 16 Medium findings, 1 Low finding. Rule matched: "2-11 High → Remediation Required."

MOD classification is deliberately softer than ARA classification on "1 High." ARA gates on agent safety — a single High is a deployment blocker. MOD measures modernization maturity — a single High is typically one modernization gap rather than a deployment blocker. For MOD, "1 High" maps to Pilot-Ready rather than Remediation Required.

**Classification Consistency Check**: consistent — V5 band "Needs Work" (score 1.72, range 1.5–2.4) ≡ V6 "Remediation Required."

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q1: Managed Compute | 1 | No cloud compute — application is a Windows desktop binary with no managed services | Cannot scale, patch, or manage compute through cloud services |
| 2 | INF-Q10: Infrastructure as Code | 1 | No IaC of any kind — all infrastructure (GitHub Pages, CloudFlare) managed manually | No reproducibility, no environment consistency, no DR capability |
| 3 | OPS-Q6: Integration Testing | 1 | No automated tests of any kind exist in the repository | No regression safety net for any code changes |
| 4 | SEC-Q6: Compute Hardening | 1 | No vulnerability scanning or patching strategy for dependencies | Known vulnerabilities in dependencies may reach production undetected |
| 5 | SEC-Q7: Security Pipeline | 1 | No SAST, DAST, or dependency scanning in CI/CD pipeline | Security vulnerabilities in code and dependencies are never automatically detected |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 2). GitHub Actions workflows are configured with build and deploy stages.
- **What it enables:** An agent that triggers deployments, checks build status, manages release notes, and coordinates the release process.
- **Additional steps:** GitHub Actions API access is already available via GITHUB_TOKEN. Agent would orchestrate existing workflow dispatch and monitor release status.
- **Effort:** Low

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository. README.md, CONTRIBUTING.md, copilot-instructions.md, docs/ directory with release management and changelog documentation, translation guides.
- **What it enables:** A knowledge agent that answers developer questions about the Greenshot build process, architecture, contribution guidelines, and release procedures using existing documentation as a corpus.
- **Additional steps:** Index the existing documentation files. The `.github/copilot-instructions.md` file is particularly comprehensive and would serve as a primary knowledge source.
- **Effort:** Low

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2, INF-Q1=1, APP-Q5=1 |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1=1 but contextual guard blocks: this is a desktop application, not an EC2/VM server workload. No server-side compute exists to containerize. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (no stored procedures). No commercial database engines detected. |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 Not Evaluated (no persistent data store). No database exists. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 Not Evaluated. No data processing workloads exist. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1, INF-Q11=2, OPS-Q6=1 |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:** Greenshot is a monolithic Windows desktop application built as a single deployable binary (WinExe) with plugin DLLs. The entire application runs locally on the user's machine with no cloud-native decomposition. While it has a plugin architecture (Box, Dropbox, Imgur, Jira, Confluence, Office), these plugins are compiled as DLLs loaded at runtime — not independently deployable services.

**Compute Model Gaps:** No managed cloud compute exists. The application is a desktop binary distributed via installer and portable ZIP. There is no server-side component to migrate.

**Communication Pattern Gaps:** The application communicates with external cloud services (Box, Dropbox, Imgur, etc.) via synchronous HTTP/OAuth for screenshot upload. There are no inter-service communication patterns since there is only one executable.

**Recommended Decomposition Approach:** Given that this is a desktop application, a full cloud-native decomposition would be a fundamental architectural transformation. The realistic modernization path would be:
1. Extract cloud upload functionality into a backend API service (API Gateway + Lambda or ECS)
2. Add a cloud-based annotation/storage service for cross-device screenshot access
3. Consider a web-based companion app using serverless architecture

**Representative AWS Services:** Lambda, API Gateway, S3, CloudFront, Cognito (for user auth), DynamoDB (for metadata)

**Recommended Patterns:** Strangler Fig (extract cloud features first), Event-Driven Architecture (for async upload processing)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10=1):** No infrastructure is defined as code. The GitHub Actions workflows handle CI/CD but no infrastructure provisioning exists. GitHub Pages and CloudFlare configurations are managed manually.

**Current CI/CD State (INF-Q11=2):** GitHub Actions provides automated build and release creation. The pipeline covers:
- NuGet restore
- MSBuild compilation
- Artifact upload
- GitHub Release creation with auto-tagging
- Chocolatey publishing (on release)

However, there is no automated testing stage, no security scanning, and deployment is limited to artifact publishing (not infrastructure deployment).

**Testing Gaps (OPS-Q6=1):** No automated tests exist. The copilot-instructions.md explicitly states "There are NO automated test projects in this repository."

**Recommended DevOps Improvements:**
1. **Add automated testing** — Unit tests for core screenshot logic, image processing, and plugin interfaces
2. **Add security scanning** — Integrate Dependabot for NuGet dependency scanning, add a SAST tool (e.g., SonarQube, Semgrep) to the GitHub Actions pipeline
3. **Add integration testing** — Test plugin OAuth flows and upload functionality
4. **Formalize release process** — Add environment-based deployment stages (dev → staging → production release)

**Representative AWS Services:** CodeBuild (if migrating CI), CodePipeline, CloudFormation/CDK (for any future cloud infrastructure)

---

## Decomposition Strategy

**Condition:** APP-Q2 = 2 (monolith with identifiable modules)

### Approach Options

| Approach | Description | When to Use | Level of Effort | Recommendation |
|----------|-------------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Extract cloud upload plugins into independent backend services while keeping the desktop app as the primary interface. New cloud features built as services. | Greenshot has clear plugin boundaries (Box, Dropbox, Imgur, etc.) that can be extracted as independent services. | Medium to High | ✅ **Recommended.** Plugin boundaries provide natural service extraction points. |
| **Conditional / Adaptive** | Keep the desktop app as-is but add a cloud backend for new features (cross-device sync, web-based annotation). Selectively migrate functionality. | Team capacity is focused on the desktop app. Cloud features are additive, not replacements. | Low to Medium | ✅ **Recommended for initial phase.** Adds cloud value without disrupting the desktop app. |
| **Big-Bang Rewrite** | Rewrite Greenshot as a cloud-native web application replacing the desktop client entirely. | Not recommended for a mature desktop application with an established user base. | Very High | ⚠️ **Recommended against.** The desktop app serves its purpose well; cloud services should complement it, not replace it. |

### Pattern Recommendations

| Pattern | Purpose | When to Apply |
|---------|---------|---------------|
| **Anti-corruption Layer** | Isolate cloud services from the desktop app's internal data model | When extracting upload plugins into backend services |
| **Event Sourcing** | Track screenshot history and annotations as events for cross-device sync | When building a cloud-based screenshot storage/sync feature |

### Effort Estimation Factors

| Factor | Signal | Assessment |
|--------|--------|------------|
| Module boundaries | Clear plugin architecture with separate projects per plugin | Low effort for extraction |
| Data coupling | Minimal — each plugin is independent; shared config via INI files | Low coupling |
| Stored procedures | None — no database | Not applicable |
| Communication patterns | Synchronous HTTP/OAuth to cloud services | Low complexity |
| CI/CD maturity | GitHub Actions exists but no testing | Medium effort to add quality gates |
| Test coverage | No automated tests | High risk during extraction |

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Greenshot is a Windows desktop application compiled as a WinExe binary targeting .NET Framework 4.8.0. There is no cloud compute of any kind — no EC2, no ECS/EKS, no Lambda, no Fargate. The application runs entirely on end-user Windows machines. |
| **Gap** | No managed compute — the application has no server-side component. All processing occurs on the user's local machine. |
| **Recommendation** | If cloud features are desired (e.g., cross-device screenshot sync, cloud-based annotation), consider building backend services using Lambda or ECS with EKS as preferred by organizational preferences. |
| **Evidence** | `src/Greenshot/Greenshot.csproj` (OutputType=WinExe), `src/Directory.Build.props` (TargetFramework=net480, RuntimeIdentifiers=win10-x64;win10-x86) |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy a database. INF-Q2 does not apply. Greenshot stores user preferences in local INI files on the user's machine. There is no persistent data store — no RDS, DynamoDB, or self-managed database of any kind. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database references in any .csproj file. No connection strings. No database drivers in NuGet packages. Settings stored via custom IniConfig system in local files. |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Workflow orchestration is not applicable by design — no multi-step workflows exist. Greenshot captures screenshots, processes images locally, and uploads to cloud services in a single synchronous operation. There are no multi-service coordination needs. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | Application architecture review: single-step capture → annotate → export flow with no multi-service orchestration. |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Synchronous HTTP/OAuth is the correct design for a desktop screenshot tool uploading to cloud services. No messaging or streaming infrastructure is needed. The application uploads screenshots directly to destination services (Box, Dropbox, Imgur) via synchronous HTTP calls — this is architecturally correct for a desktop utility. |
| **Gap** | N/A |
| **Recommendation** | Adopting async messaging is NOT recommended — it would add operational complexity without architectural benefit for a desktop application. |
| **Evidence** | Plugin source code uses `Dapplo.HttpExtensions` for synchronous HTTP uploads. No message queue producers or consumers exist. |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, security groups, subnets, or network segmentation exists. This is a desktop application with no cloud infrastructure — there is no network architecture to evaluate. |
| **Gap** | No cloud network security infrastructure exists. The application communicates directly from user machines to external cloud services over the public internet. |
| **Recommendation** | If backend services are built in the future, deploy them in a VPC with private subnets, least-privilege security groups, and VPC endpoints for AWS service access. |
| **Evidence** | No IaC files exist. No Terraform, CloudFormation, or CDK resources of any kind. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or any managed entry point exists. The application does not expose APIs — it is a desktop tool that consumes external APIs. |
| **Gap** | No API entry point exists because no APIs are exposed. |
| **Recommendation** | If cloud backend services are built, use API Gateway with throttling and authentication as the entry point. Organizational preferences favor API Gateway. |
| **Evidence** | No IaC defining API Gateway, ALB, or CloudFront. No server-side API endpoints in source code. |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling exists. There are no scalable cloud resources — no ASGs, no ECS services, no Lambda functions. |
| **Gap** | No cloud resources exist that could benefit from auto-scaling. |
| **Recommendation** | If cloud services are built in the future, configure auto-scaling on all compute and data resources from day one. |
| **Evidence** | No IaC files. No AWS resources of any kind defined in the repository. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no persistent state to back up. INF-Q8 does not apply. Greenshot stores user preferences locally on end-user machines — there is no server-side data store that requires backup configuration. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database, S3 bucket, EBS volume, or any cloud data store exists in this repository. |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload requiring HA evaluation. INF-Q9 does not apply. Greenshot is a desktop application running on individual user machines — multi-AZ deployment is not a meaningful concept for this architecture. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No server-side deployment. No IaC defining compute, networking, or data store resources. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No infrastructure as code of any kind exists in this repository. No Terraform, CloudFormation, CDK, Helm, or other IaC tools are present. The only "infrastructure" is GitHub Pages (configured via GitHub UI) and CloudFlare (managed externally). |
| **Gap** | 0% IaC coverage — all infrastructure (GitHub Pages, CloudFlare cache, Chocolatey publishing) is configured manually outside the repository. |
| **Recommendation** | Define any cloud infrastructure as code. If migrating to AWS, use CDK or Terraform to define all resources. Even for the current setup, GitHub Pages configuration could be version-controlled. |
| **Evidence** | No `.tf`, `.tfvars`, `template.yaml`, `cdk.json`, `Chart.yaml`, or `kustomization.yaml` files found anywhere in the repository. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GitHub Actions provides automated build and release artifact creation. The `release.yml` workflow automates NuGet restore, MSBuild compilation, artifact packaging (installer + portable ZIP), Git tagging, and GitHub Release creation. Additional workflows handle Chocolatey publishing and CloudFlare cache purging. However, there are no automated test stages, no security scanning, and no staged deployment (canary/blue-green). |
| **Gap** | Build is automated but there is no test stage (no tests exist), no security scanning stage, and no staged deployment. The pipeline goes directly from build to release artifact publication. |
| **Recommendation** | Add test stages to the pipeline (requires creating tests first). Integrate Dependabot for NuGet vulnerability scanning. Add a SAST tool (SonarQube or Semgrep) as a required pipeline step before artifact creation. |
| **Evidence** | `.github/workflows/release.yml` (build + deploy), `.github/workflows/choco-publish.yml`, `.github/workflows/purge-cloudflare-cache.yml`, `.github/workflows/update-gh-pages.yml` |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application is written in C# targeting .NET Framework 4.8.0. This is the legacy .NET Framework — NOT modern .NET (6/7/8/9/10). The project uses `Microsoft.NET.Sdk.WindowsDesktop` SDK-style project files but targets `net480`. The codebase uses `LangVersion=latest` for C# language features but is constrained by the .NET Framework 4.8 runtime and BCL. |
| **Gap** | .NET Framework 4.8 is in maintenance mode (security fixes only). It lacks modern .NET features: cross-platform support, performance improvements (Span<T> ecosystem, native AOT), modern hosting model, and the latest ASP.NET Core capabilities. The AWS SDK for .NET v3 supports .NET Framework 4.8 but the broader cloud-native .NET ecosystem (minimal APIs, native AOT, container-optimized builds) targets modern .NET only. |
| **Recommendation** | Migrate from .NET Framework 4.8 to modern .NET (8 or 9 LTS). This is a prerequisite for containerization and access to the full modern .NET ecosystem. WinForms and WPF are supported on modern .NET for Windows-only applications. |
| **Evidence** | `src/Directory.Build.props` (TargetFramework=net480), `src/Greenshot/Greenshot.csproj` (Sdk=Microsoft.NET.Sdk.WindowsDesktop), `README.md` (.NET Framework 4.8.0) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Greenshot is a monolithic desktop application with identifiable module boundaries. The solution contains 12 projects: main application (Greenshot), core library (Greenshot.Base), editor (Greenshot.Editor), build tasks (Greenshot.BuildTasks), installer, and 7 plugins (Box, Confluence, Dropbox, ExternalCommand, Imgur, Jira, Office). Plugins are compiled as separate DLLs but are loaded at runtime into the same process — they are not independently deployable services. |
| **Gap** | Single deployable unit (WinExe + plugin DLLs). While the plugin architecture provides good modularity within the monolith, all components share the same process, memory space, and lifecycle. Cloud upload functionality (Box, Dropbox, Imgur) is tightly coupled to the desktop app's runtime. |
| **Recommendation** | The plugin architecture provides natural decomposition boundaries if cloud backend services are desired. Each cloud upload plugin (Box, Dropbox, Imgur) could be extracted into an independent backend service. However, for a desktop application, this monolithic architecture is not inherently problematic — decomposition is only valuable if cloud-native features are planned. |
| **Evidence** | `src/Greenshot.sln` (12 projects), `src/Greenshot.Plugin.Box/`, `src/Greenshot.Plugin.Dropbox/`, `src/Greenshot.Plugin.Imgur/`, `src/Directory.Build.props` (PostBuild target copies plugins to main app output) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Sync request/response is the correct design; async is not needed. Greenshot communicates with external cloud services (Box, Dropbox, Imgur, Jira, Confluence) via synchronous HTTP/OAuth calls for screenshot upload. This is the correct pattern for a desktop utility making individual upload requests. There are no inter-service communication patterns because there is only one application. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | Plugin source code uses Dapplo.HttpExtensions for HTTP communication. No message queues, event buses, or async communication infrastructure. |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. No operations exceed 30 seconds — not applicable by design. Screenshot capture is instantaneous. Image processing (annotation, effects) operates on in-memory bitmaps with sub-second latency. Cloud uploads may take longer depending on file size and network, but these are handled by the HTTP client library with appropriate timeouts — this is standard for a desktop application and does not represent a long-running process architecture concern. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | Application flow: capture (instant) → annotate (interactive, user-paced) → export (seconds for upload). No background job frameworks, no async job queues. |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning exists because no APIs are exposed. Greenshot is a consumer of external APIs (Box, Dropbox, Imgur) but does not expose any API surface of its own. The desktop application has no endpoints, no REST API, no RPC surface. |
| **Gap** | No API versioning strategy. If cloud backend services are built in the future, a versioning strategy would need to be established from the start. |
| **Recommendation** | If backend services are introduced, adopt URL-path versioning (e.g., /v1/) from day one with backward-compatibility guarantees. Use API Gateway's stage/version features. |
| **Evidence** | No API endpoint definitions in source code. No OpenAPI specs, no Swagger files, no REST controllers. |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Service endpoints for cloud integrations (Box, Dropbox, Imgur, Jira, Confluence) are configured via environment variables injected at build time (OAuth client IDs/secrets) and hardcoded base URLs in the plugin source code. There is no dynamic service discovery — but for a desktop application connecting to well-known external SaaS APIs with stable URLs, this is a reasonable pattern. |
| **Gap** | All external service endpoints are hardcoded in application code. While this is acceptable for connecting to stable SaaS APIs (Box, Dropbox, Imgur have well-known endpoints), it means endpoint changes require code changes and recompilation. |
| **Recommendation** | Externalize service endpoint URLs into configuration (rather than hardcoded in source). If cloud backend services are added, adopt a service registry or environment-variable-based discovery for internal service-to-service communication. |
| **Evidence** | `src/Directory.Build.props` (OAuth tokens via environment variables), Plugin source code (hardcoded API base URLs for Box, Dropbox, Imgur, Jira, Confluence) |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Screenshots and images are stored on the local file system of the user's machine. The application saves captured images to user-specified directories in various formats (PNG, JPEG, BMP, GIF, TIFF). There is no cloud object storage — no S3 integration for persistent screenshot storage. Upload plugins send images to third-party services (Box, Dropbox, Imgur) but these are external to the application's data model. |
| **Gap** | Unstructured data (screenshots) stored on local file systems with no cloud-based managed storage. No S3 integration for centralized, accessible storage. No parsing or indexing of screenshot content. |
| **Recommendation** | If cross-device access or centralized screenshot management is desired, integrate S3 for screenshot storage with optional Textract/Rekognition for content extraction and search. Organizational preferences favor DynamoDB for metadata storage alongside S3. |
| **Evidence** | `src/Greenshot/Destinations/FileDestination.cs` (saves to local filesystem), no `aws_s3_bucket` or S3 SDK references in any file. |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Greenshot has a centralized configuration system via `IniConfig` in `Greenshot.Base`. All application settings are managed through a single INI configuration abstraction. Image capture and processing is centralized through `CaptureHelper` and the `Surface` editor component. Plugin data access (OAuth tokens, upload settings) follows a consistent pattern through plugin-specific configuration classes. |
| **Gap** | While configuration access is centralized, the image export/destination pattern has some inconsistency — each plugin handles its own upload logic independently with different error handling approaches. |
| **Recommendation** | If building cloud services, maintain the existing centralized pattern and extend it with a unified data access layer for any cloud storage integration. |
| **Evidence** | `src/Greenshot.Base/` (IniConfig system), `src/Greenshot/Helpers/CaptureHelper.cs`, consistent plugin structure across all Greenshot.Plugin.* projects |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy a database. DATA-Q3 does not apply. Greenshot uses local INI files for configuration — there is no database engine to version or evaluate for EOL status. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database references in any .csproj, no connection strings, no database drivers in NuGet packages. |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs exist. All business logic resides in the C# application layer. There is no database of any kind — all logic for screenshot capture, image processing, annotation, and cloud upload is implemented in application code. |
| **Gap** | None — this is the ideal state. All business logic is in the application layer with no database coupling. |
| **Recommendation** | Maintain this approach if databases are introduced in the future — keep business logic in the application layer. |
| **Evidence** | No .sql files in the repository. No ORM configurations. No database-related NuGet packages. All logic in C# source files. |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | Audit logging (CloudTrail) is an AWS account-level service provisioned once per account or organization — not per-application. This repo contains no AWS IaC of any kind (no application-level or account-level infrastructure). CloudTrail evaluation belongs in the foundation/account-level infrastructure repo. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No IaC files exist. `has_iac_provisioning_aws_resources=false`. |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no database, S3 bucket, EBS volume, or similar. SEC-Q2 does not apply. Screenshots are stored on the user's local filesystem; encryption at rest is a responsibility of the user's OS-level disk encryption (BitLocker). |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `has_at_rest_data_surface=false`. No cloud data stores in repository. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no API surface. SEC-Q3 does not apply. Greenshot does not expose any API endpoints — it is a desktop application that consumes external APIs. The application authenticates to external services (Box, Dropbox, Imgur) via OAuth2, which demonstrates good security practice for API consumption but is not relevant to SEC-Q3 (which evaluates authentication on exposed APIs). |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `has_api_surface=false`. No HTTP server, no REST controllers, no API Gateway. |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no API surface and no user authentication system. SEC-Q4 does not apply. Greenshot is a desktop utility — it authenticates to external services via OAuth2 (per-service), but there is no centralized identity provider integration because the application does not manage user identities. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `has_api_surface=false`. OAuth2 tokens stored locally per plugin. No Cognito, Okta, or SAML integration. |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | OAuth client IDs and secrets for cloud service integrations (Box, Dropbox, Flickr, Imgur, Photobucket, Picasa) are managed through GitHub Secrets and injected as environment variables at build time. The `Directory.Build.props` defines token replacement that embeds these values during compilation. No plaintext credentials exist in the source code — the source contains placeholder tokens that are replaced during the build process. |
| **Gap** | Secrets are managed via GitHub Secrets (good) and injected at build time via environment variables (acceptable), but there is no rotation mechanism. OAuth client secrets are static and embedded into the compiled binary at build time — they cannot be rotated without rebuilding and redistributing the application. |
| **Recommendation** | For a desktop application distributed as a binary, build-time secret injection via GitHub Secrets is a reasonable approach. Consider: (1) using short-lived OAuth tokens with refresh flows rather than embedding long-lived client secrets, (2) evaluating whether OAuth public client (PKCE) flows could eliminate the need for client secrets in the distributed binary. |
| **Evidence** | `.github/workflows/release.yml` (12 secrets: Box13_ClientId/Secret, DropBox13_ClientId/Secret, Flickr_ClientId/Secret, Imgur13_ClientId/Secret, Photobucket_ClientId/Secret, Picasa_ClientId/Secret), `src/Directory.Build.props` (Tokens ItemGroup with ReplacementValue from environment variables) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No vulnerability scanning or patching strategy exists. The CI/CD pipeline has no dependency vulnerability scanning (no Dependabot, no `dotnet audit`, no Snyk). NuGet package versions are pinned but there is no automated process to detect or alert on known vulnerabilities in those dependencies. The application uses `SixLabors.ImageSharp 2.1.13` (released 2023, with newer versions available), `Dapplo.Windows 2.0.89`, and other dependencies that are not automatically checked for CVEs. |
| **Gap** | No vulnerability scanning for NuGet dependencies. No Dependabot configuration. No automated patching strategy. Dependency versions are static with no mechanism to detect known vulnerabilities. |
| **Recommendation** | Enable GitHub Dependabot for NuGet package vulnerability scanning. Add `dotnet list package --vulnerable` to the CI pipeline as a required check. Consider Snyk or GitHub Advanced Security for deeper vulnerability analysis. |
| **Evidence** | No `.github/dependabot.yml` file. No vulnerability scanning step in `.github/workflows/release.yml`. No `dotnet audit` or equivalent in any workflow. |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SAST, DAST, or dependency vulnerability scanning is integrated into the CI/CD pipeline. The GitHub Actions workflows perform build and release only — no security validation of any kind occurs before artifacts are published. |
| **Gap** | Complete absence of security scanning in the pipeline. No Dependabot, no SAST tool, no container scanning (no containers exist), no code quality gates. |
| **Recommendation** | Add the following security scanning to the CI pipeline: (1) GitHub Dependabot for NuGet vulnerability alerts, (2) a SAST tool (SonarQube, Semgrep, or GitHub CodeQL — CodeQL supports C#) as a required check, (3) consider CodeGuru Reviewer if migrating to AWS CI/CD. |
| **Evidence** | `.github/workflows/release.yml` — no security scanning steps. No `.github/dependabot.yml`. No SonarQube, Semgrep, or CodeQL configuration files. |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing is instrumented. The application uses log4net for local logging (debug and release configurations) but has no tracing infrastructure — no OpenTelemetry, no X-Ray, no trace ID propagation. This is a desktop application with no distributed services to trace across, but even for HTTP calls to external services, no correlation IDs or trace context are propagated. |
| **Gap** | No tracing of any kind. log4net provides local file-based logging only with no structured trace correlation. |
| **Recommendation** | For a desktop application, distributed tracing is of limited value since there is only one service. If cloud backend services are added, instrument with OpenTelemetry from day one. For the current app, consider adding correlation IDs to cloud upload requests for debugging. |
| **Evidence** | `src/Greenshot.Base/Greenshot.Base.csproj` (log4net 3.3.0 dependency), `src/Greenshot/log4net-release.xml`, `src/Greenshot/log4net-debug.xml`. No OpenTelemetry or X-Ray SDK in any .csproj. |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no user-facing surface for which SLOs are meaningful. OPS-Q2 does not apply. Greenshot is a desktop application — it has no API surface and no persistent data store against which SLOs (latency, availability, error rate) could be measured. Application quality is measured by crash rate and user satisfaction, not SLO-style metrics. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `has_api_surface=false`, `has_persistent_data_store=false`. No CloudWatch alarms, no SLO definitions. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics are published. The application has no telemetry, no analytics, no metric collection of any kind. There is no CloudWatch integration, no custom metric publication, and no usage analytics. |
| **Gap** | No business or usage metrics. No understanding of feature usage patterns, upload success rates, or user engagement. |
| **Recommendation** | Consider adding opt-in telemetry for desktop usage patterns (screenshot frequency, plugin usage, export destination preferences). If cloud services are added, publish business metrics (upload success rate, annotation features used) to CloudWatch. |
| **Evidence** | No `cloudwatch` or telemetry SDK in any .csproj. No metrics collection code in source. No analytics configuration. |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting is configured. There are no CloudWatch alarms, no error rate monitoring, no latency tracking. For a desktop application with no cloud backend, there is no server-side system to monitor. |
| **Gap** | No alerting of any kind. If cloud upload services experience issues (API rate limits, authentication failures), there is no automated detection or notification. |
| **Recommendation** | If cloud backend services are added, configure CloudWatch anomaly detection on error rates and latency from day one. For the current setup, consider monitoring GitHub release download metrics and Chocolatey install counts as business health indicators. |
| **Evidence** | No CloudWatch, Datadog, or monitoring SDK in any .csproj. No alarm definitions. No monitoring configuration. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | No deployed workload found in this repo — deployment strategy cannot be assessed from source code alone. Greenshot is distributed as a desktop installer and portable ZIP via GitHub Releases. There is no server-side deployment to evaluate for canary/blue-green strategies. Desktop application "deployment" is user-initiated download and install — fundamentally different from server-side deployment. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `has_deployed_workload=false`. Distribution via GitHub Releases (`.exe` installer, `.zip` portable). No server-side compute to deploy to. |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No automated tests of any kind exist in this repository. The `.github/copilot-instructions.md` explicitly states: "There are NO automated test projects in this repository." No unit tests, no integration tests, no end-to-end tests. |
| **Gap** | Complete absence of automated testing. No regression safety net for code changes. Every change relies entirely on manual testing. |
| **Recommendation** | Introduce automated testing incrementally: (1) Unit tests for core image processing logic (Greenshot.Base, Greenshot.Editor), (2) Integration tests for plugin OAuth flows and upload functionality, (3) UI automation tests for critical user workflows (capture, annotate, export). Use xUnit or NUnit with MSTest runner. |
| **Evidence** | `.github/copilot-instructions.md` ("There are NO automated test projects in this repository"), `src/Greenshot.sln` (no test projects), no `*Test*` or `*Tests*` directories or projects. |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response automation or runbooks exist. There is no server-side system to have incidents on — the application runs on user machines. However, there are no documented procedures for handling security vulnerabilities, broken releases, or cloud service integration failures. |
| **Gap** | No incident response procedures documented. The SECURITY.md simply directs vulnerability reports to GitHub's security tab with no documented response process, timeline commitments, or escalation procedures. |
| **Recommendation** | Document incident response procedures for: (1) security vulnerability response (timeline, patching process, disclosure), (2) broken release rollback (how to pull a bad release from GitHub/Chocolatey), (3) OAuth credential rotation (if a client secret is compromised). |
| **Evidence** | `SECURITY.md` (minimal — just directs to GitHub security tab), no runbooks, no incident response documentation. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership exists. There are no dashboards, no alarms with owners, no SLO definitions with team attribution. The application has no monitoring infrastructure of any kind. |
| **Gap** | No observability assets exist to have ownership over. No monitoring, no dashboards, no alarms. |
| **Recommendation** | If cloud services are added, establish observability ownership from day one with per-service dashboards and named alarm owners. For the current setup, at minimum track GitHub release metrics and Chocolatey download counts. |
| **Evidence** | No monitoring configuration files. No CloudWatch, Datadog, or Grafana references. No CODEOWNERS for observability assets. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resources exist to tag. There is no cloud infrastructure of any kind in this repository. No tagging standard, no tag enforcement, no cost allocation tags. |
| **Gap** | No resources to tag and no tagging governance. If cloud infrastructure is introduced, a tagging strategy needs to be established. |
| **Recommendation** | When cloud resources are introduced, establish a mandatory tagging standard (Environment, Service, Owner, CostCenter) enforced via IaC (required tags in modules) and AWS Config rules. |
| **Evidence** | No IaC files. No AWS resources. No `default_tags` or tag-related configuration. |

---

## Learning Materials

### Move to Cloud Native
- [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

### Move to Modern DevOps
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `src/Greenshot/Greenshot.csproj` | INF-Q1, APP-Q1, APP-Q2 | Main application project file — OutputType=WinExe, SDK, package references |
| `src/Directory.Build.props` | INF-Q1, APP-Q1, APP-Q2, SEC-Q5 | Shared build properties — TargetFramework=net480, OAuth token replacement, RuntimeIdentifiers |
| `src/Greenshot.sln` | APP-Q2, OPS-Q6 | Solution file — 12 projects, no test projects |
| `src/Greenshot.Base/Greenshot.Base.csproj` | OPS-Q1, DATA-Q2 | Core library — log4net, Dapplo.HttpExtensions, SixLabors.ImageSharp |
| `src/Greenshot.Editor/Greenshot.Editor.csproj` | APP-Q2 | Editor component — SixLabors.ImageSharp, System.Reactive |
| `.github/workflows/release.yml` | INF-Q11, SEC-Q5, SEC-Q6, SEC-Q7 | CI/CD pipeline — build, package, release |
| `.github/workflows/choco-publish.yml` | INF-Q11 | Chocolatey publishing workflow |
| `.github/workflows/purge-cloudflare-cache.yml` | INF-Q11 | CloudFlare cache management |
| `.github/copilot-instructions.md` | OPS-Q6 | Developer documentation — confirms no tests exist |
| `SECURITY.md` | OPS-Q7 | Minimal security policy — directs to GitHub security tab |
| `README.md` | APP-Q1 | Project overview — .NET Framework 4.8.0, Windows desktop |
| `src/Greenshot/App.config` | APP-Q1 | Runtime configuration — .NET Framework 4.7.2 supportedRuntime |
| `src/nuget.config` | SEC-Q6 | NuGet package source — nuget.org only |
| `src/Greenshot/log4net-release.xml` | OPS-Q1 | Logging configuration — file-based logging only |
| `src/Greenshot/log4net-debug.xml` | OPS-Q1 | Debug logging configuration |
