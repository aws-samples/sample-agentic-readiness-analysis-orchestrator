# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | greenshot--greenshot |
| **Date** | 2026-05-07 |
| **TD Version** | modernization-assessment |
| **Repo Type** | application |
| **Service Archetype** | stateless-utility (auto-detected) |
| **Priority** | P2 |
| **Tags** | csharp, desktop, windows |
| **Context** | Windows screenshot and annotation tool. |
| **Overall Score** | 1.54 / 4.0 |

**Archetype Justification**: This is a desktop Windows application with no persistent data store, no server-side API surface, no database connections, and no inter-service communication. All operations are local, synchronous, and user-initiated. Classified as stateless-utility — the closest fit for a standalone desktop tool with no backend services.

**Surface Flags**: has_persistent_data_store=false, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=false, has_multi_instance_deployment=false

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | 1.33 / 4.0 | ❌ Not Present | Critical |
| Application Architecture (APP) | 1.25 / 4.0 | ❌ Not Present | Critical |
| Data Platform Modernization (DATA) | 2.67 / 4.0 | 🟡 Partial | Needs Work |
| Security Baseline (SEC) | 1.33 / 4.0 | ❌ Not Present | Critical |
| Operations & Observability (OPS) | 1.13 / 4.0 | ❌ Not Present | Critical |
| **Overall** | **1.54 / 4.0** | **🟠 Needs Work** | |

**Classification:** Remediation Required

This repo has 6 High findings, 18 Medium findings, 2 Low findings. Rule matched: 2-11 High → Remediation Required. MOD classification treats "1 High" as Pilot-Ready (a single modernization gap), unlike ARA where "1 High" is an agent-deployment gate.

**Scoring Notes:**

- **INF**: INF-Q1=1, INF-Q2=Not Evaluated (no persistent data store), INF-Q3=Not Evaluated (stateless-utility), INF-Q4=Not Evaluated (stateless-utility), INF-Q5=1, INF-Q6=1, INF-Q7=1, INF-Q8=Not Evaluated (no persistent state), INF-Q9=Not Evaluated (no deployed workload), INF-Q10=1, INF-Q11=3. Evaluated: Q1, Q5, Q6, Q7, Q10, Q11 → (1+1+1+1+1+3)/6 = 8/6 = 1.33
- **APP**: APP-Q1=2, APP-Q2=1, APP-Q3=Not Evaluated (stateless-utility), APP-Q4=Not Evaluated (stateless-utility), APP-Q5=1, APP-Q6=1. Evaluated: Q1, Q2, Q5, Q6 → (2+1+1+1)/4 = 5/4 = 1.25
- **DATA**: DATA-Q1=2, DATA-Q2=2, DATA-Q3=Not Evaluated (no database), DATA-Q4=4. Evaluated: Q1, Q2, Q4 → (2+2+4)/3 = 8/3 = 2.67
- **SEC**: SEC-Q1=1, SEC-Q2=Not Evaluated (no at-rest data surface), SEC-Q3=1, SEC-Q4=1, SEC-Q5=3, SEC-Q6=1, SEC-Q7=1. Evaluated: Q1, Q3, Q4, Q5, Q6, Q7 → (1+1+1+3+1+1)/6 = 8/6 = 1.33
- **OPS**: OPS-Q1=1, OPS-Q2=Not Evaluated (no API surface), OPS-Q3=1, OPS-Q4=1, OPS-Q5=2, OPS-Q6=1, OPS-Q7=1, OPS-Q8=1, OPS-Q9=1. Evaluated: Q1, Q3, Q4, Q5, Q6, Q7, Q8, Q9 → (1+1+1+2+1+1+1+1)/8 = 9/8 = 1.13
- **Overall**: (1.33 + 1.25 + 2.67 + 1.33 + 1.13) / 5 = 7.71 / 5 = 1.54

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | No infrastructure as code exists — all infrastructure (if any) is manual | No reproducible infrastructure; no disaster recovery capability |
| 2 | APP-Q2: Monolith vs Microservices | 1 | Tightly coupled monolithic desktop application with no module boundaries for cloud decomposition | Cannot independently scale, deploy, or modernize components |
| 3 | OPS-Q6: Integration Testing | 1 | Zero automated tests of any kind (unit or integration) | No safety net for any migration or modernization effort; high regression risk |
| 4 | SEC-Q7: Application Security Pipeline | 1 | No SAST, DAST, or dependency vulnerability scanning in CI/CD pipeline | Vulnerabilities in dependencies may reach release artifacts undetected |
| 5 | INF-Q1: Managed Compute | 1 | No cloud compute — application is distributed as a desktop installer | No cloud elasticity, no managed patching, no operational visibility |

---

## Quick Agent Wins

No Quick Agent Wins identified. The system lacks the foundational capabilities (API documentation, CI/CD automation with testing, structured logging) needed to support agent integration. The CI/CD pipeline exists (INF-Q11 = 3), but without API surfaces, structured logging, or integration tests, no agent prerequisite conditions are met. Address the gaps identified in this assessment before pursuing agent opportunities.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=1 (<3), INF-Q1=1 (<3) |
| 2 | Move to Containers | Not Triggered | — | — | No container definitions found and INF-Q1<3, BUT contextual guard blocks: this is a desktop application with no server-side workload to containerize |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (≥3); no commercial DB engines detected |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2=Not Evaluated (no persistent data store); no databases to migrate |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads exist; contextual guard blocks |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1 (<3), OPS-Q5=2 (<3), OPS-Q6=1 (<3) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:** Greenshot is a tightly coupled monolithic Windows desktop application (APP-Q2 = 1). It is a single deployable unit (WinExe) with 12 projects compiled into one executable with plugins loaded at runtime. The plugin architecture provides some modularity, but all code shares the same process, same configuration system (custom INI), and same deployment lifecycle.

**Compute Model Gaps:** The application has no cloud compute presence (INF-Q1 = 1). It is distributed as a Windows installer and portable ZIP. There is no server-side component, no API, and no cloud infrastructure.

**Relevance for Desktop Application:** While Greenshot is a desktop application, the Move to Cloud Native pathway is triggered because the assessment evaluates cloud-readiness. If the team intends to add cloud-connected features (cloud storage integration, collaborative annotation, cross-device sync), the current monolithic architecture would need decomposition. Specifically:

- Cloud-connected features (image hosting, shared annotations, team collaboration) would benefit from a service-oriented backend
- The plugin architecture (Box, Dropbox, Imgur, Confluence, Jira) already demonstrates extension points that could become independent cloud services
- Image processing capabilities could be offered as cloud services

**Recommended Decomposition Approach:** If cloud modernization is a goal, consider the Strangler Fig approach — keep the desktop client functional while extracting backend services for cloud storage, image processing, and collaboration features.

**Representative AWS Services:** API Gateway, Lambda (for image processing), S3 (for image storage), ECS/EKS (for annotation service), EventBridge (for plugin integrations), DynamoDB (for metadata)

**Note on preferences:** Per technology preferences, EKS and DynamoDB are preferred; Lambda should be avoided. Backend services could run on EKS with DynamoDB for metadata storage and API Gateway for the entry point.

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 1):** No infrastructure as code exists. The build environment is defined only in GitHub Actions workflow files. There is no Terraform, CloudFormation, or CDK defining any infrastructure. All infrastructure (if any exists beyond GitHub-hosted runners) is manually configured.

**Current CI/CD State (INF-Q11 = 3):** GitHub Actions workflows exist with build (MSBuild on Windows), package (InnoSetup installer, portable ZIP), and deploy (GitHub Releases, Chocolatey) stages. The pipeline is automated but lacks testing stages — no unit tests, integration tests, or security scanning. Build secrets are properly managed via GitHub Secrets.

**Deployment Strategy Gaps (OPS-Q5 = 2):** Releases are published to GitHub Releases with auto-generated release notes. There is no canary or staged rollout — installers are published directly. The Chocolatey workflow triggers on full releases, providing a secondary distribution channel.

**Testing Gaps (OPS-Q6 = 1):** Zero automated tests exist in the repository. No unit tests, no integration tests, no UI tests. This is the single largest risk for any modernization effort.

**Recommended DevOps Improvements:**
1. **Add automated testing** — Start with unit tests for core image processing and editor logic using xUnit/NUnit. Add UI automation tests for critical workflows.
2. **Add security scanning** — Integrate Dependabot for NuGet dependency vulnerability alerts. Add a SAST tool (e.g., SonarQube, Semgrep) to the GitHub Actions pipeline.
3. **Improve deployment strategy** — Consider publishing to a beta channel before full release; use GitHub pre-releases for staged rollout.
4. **Add IaC for any cloud resources** — If cloud features are added, define infrastructure in Terraform or CDK from the start.

**Representative AWS Services:** CodeBuild (Windows build support), CodePipeline, CloudFormation/CDK (for any cloud infrastructure), X-Ray (for cloud service observability)

---

## Decomposition Strategy

*This section is included because APP-Q2 < 3 (APP-Q2 = 1).*

### Context

Greenshot is a tightly coupled monolithic desktop application. While it has a plugin architecture (7 plugins for external service integrations), the core application (capture, editor, configuration, forms) is a single, undifferentiated code mass with shared state through static instances and global configuration.

### Decomposition Approach Options

| Approach | When to Use | Level of Effort | Recommendation |
|----------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Extract cloud-connected features (image hosting, collaboration) as independent services while keeping the desktop client. | **Medium to High** | ✅ **Recommended.** Keep the desktop app as a client; build backend services incrementally. |
| **Conditional / Adaptive** | Containerize backend image processing first, then selectively extract high-value services. | **Low to Medium** | ✅ **Recommended when starting with a single cloud feature** (e.g., cloud image storage). |
| **Big-Bang Rewrite** | Rewrite as a web application or Electron app with microservices backend. | **Very High** | ⚠️ **Recommended against.** The desktop app serves its users well; focus on adding cloud capabilities, not replacing the client. |

### Pattern Recommendations

| Pattern | Purpose | When to Apply |
|---------|---------|---------------|
| **Anti-corruption Layer (ACL)** | Isolate new cloud services from the desktop client's data model | When extracting plugin integrations (Box, Dropbox, Imgur) into cloud-mediated services |
| **Hexagonal Architecture** | Structure new backend services with clear boundaries | Every new cloud service should follow ports-and-adapters from the start |

### Effort Estimation

| Factor | Signal | Assessment |
|--------|--------|-----------|
| Module boundaries | Plugin architecture provides some boundaries, but core is coupled | Medium effort to extract |
| Data coupling | Custom INI config shared across all modules | Low coupling (file-based, easily separated) |
| Communication patterns | All synchronous, in-process | New services would need API design from scratch |
| CI/CD maturity | CI/CD exists (INF-Q11=3) but no tests | Medium risk during extraction |
| Test coverage | Zero automated tests (OPS-Q6=1) | **High risk** — no safety net for any refactoring |

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Greenshot is distributed as a Windows desktop application (WinExe). There is no cloud compute infrastructure — no EC2, ECS, EKS, Lambda, or Fargate. The application runs entirely on end-user machines. Build compute uses GitHub-hosted runners (windows-latest, ubuntu-latest) in CI/CD but these are ephemeral and not production infrastructure. |
| **Gap** | No cloud compute exists. The application has no server-side component and no managed compute services. |
| **Recommendation** | If cloud features are planned (image hosting, collaboration, shared annotations), provision managed compute using EKS (preferred per technology preferences) or ECS with Fargate for backend services. |
| **Evidence** | `.github/workflows/release.yml` (runs-on: windows-latest), absence of any IaC files defining compute resources |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy a database. INF-Q2 does not apply. Greenshot stores all configuration in local INI files and does not connect to any database, managed or self-managed. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database driver imports in any .csproj; no connection strings in configuration files; custom INI-based settings system in source |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Workflow orchestration is not applicable by design — no multi-step workflows exist for a desktop screenshot tool. All operations are user-initiated, single-step captures and edits. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/Greenshot/GreenshotMain.cs` — single-threaded STAThread desktop entry point; no workflow patterns in source |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Synchronous operation is the correct design for a desktop screenshot application. No messaging or streaming infrastructure is needed — all operations are local, user-initiated, and complete within the user's session. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No SQS/SNS/Kafka/EventBridge references in any source or configuration file |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, security groups, NACLs, or network segmentation exist. The application is a desktop client with no cloud networking infrastructure. Network communication consists of outbound HTTPS calls to third-party APIs (Box, Dropbox, Imgur, Confluence, Jira) made directly from the user's machine. TLS 1.2/1.3 is enforced in `GreenshotMain.cs`. |
| **Gap** | No cloud network security infrastructure exists. If backend services are added, network security must be designed from scratch. |
| **Recommendation** | When cloud services are introduced, deploy them in a VPC with private subnets, least-privilege security groups, and VPC endpoints for AWS service access. |
| **Evidence** | `src/Greenshot/GreenshotMain.cs` (TLS enforcement), absence of any IaC defining networking |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or any managed entry point exists. The application is a desktop client that makes outbound HTTP calls to third-party services but exposes no API of its own. |
| **Gap** | No API entry point exists. No managed traffic control, throttling, or authentication layer. |
| **Recommendation** | If cloud backend services are developed, place API Gateway (preferred per technology preferences) in front of them with throttling, authentication, and request validation. |
| **Evidence** | Absence of any API Gateway, ALB, or CloudFront resources in repository |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling exists. The application runs on end-user desktops with no cloud compute that could be scaled. |
| **Gap** | No auto-scaling configuration for any resource. |
| **Recommendation** | When cloud services are introduced, configure auto-scaling from the start — EKS Horizontal Pod Autoscaler for compute, DynamoDB auto-scaling for data (per technology preferences). |
| **Evidence** | Absence of any auto-scaling configuration in repository |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no persistent state to back up. INF-Q8 does not apply. Greenshot stores only local user preferences in INI files on the user's machine — there is no server-side data requiring backup. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database, S3, or managed storage resources in repository |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload requiring HA evaluation. INF-Q9 does not apply. Greenshot runs on individual user desktops — there is no server-side deployment that could span availability zones. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No deployed compute workload; no IaC resources defining availability zones |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No infrastructure as code exists in the repository. There are no Terraform files, no CloudFormation templates, no CDK stacks, no Helm charts, and no Kustomize configurations. The only "infrastructure" definition is the GitHub Actions workflow configuration for CI/CD runners. |
| **Gap** | 0% IaC coverage. All infrastructure (if any exists beyond GitHub-hosted resources) is manually created. |
| **Recommendation** | If cloud infrastructure is introduced, adopt Infrastructure as Code from the start using CDK or Terraform. Even for the current state, consider defining the GitHub Pages and Cloudflare configurations as IaC. |
| **Evidence** | Absence of any `.tf`, `.cfn.yaml`, `cdk.json`, `Chart.yaml`, or `kustomization.yaml` files in repository |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GitHub Actions CI/CD is well-implemented with 4 workflows: (1) `release.yml` — full build pipeline with MSBuild, InnoSetup installer creation, portable ZIP, and GitHub Release deployment; (2) `choco-publish.yml` — Chocolatey package publishing on release; (3) `purge-cloudflare-cache.yml` — CDN cache invalidation; (4) `update-gh-pages.yml` — documentation rebuild. Build secrets are properly managed via GitHub Secrets (Box, Dropbox, Imgur OAuth credentials). The pipeline automates build and deploy stages with version extraction and artifact management. |
| **Gap** | No automated testing stage in the pipeline — the build proceeds directly from compile to package without any test execution. No IaC deployment automation (no infrastructure to deploy). |
| **Recommendation** | Add a test execution stage between build and package in the release workflow. Integrate Dependabot and a SAST tool as additional pipeline stages. |
| **Evidence** | `.github/workflows/release.yml`, `.github/workflows/choco-publish.yml`, `.github/workflows/purge-cloudflare-cache.yml`, `.github/workflows/update-gh-pages.yml` |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | C# targeting .NET Framework 4.8 (net480) with LangVersion=latest. Uses Windows Forms and WPF interop. The .NET SDK is 9.0.311 (for build tooling) but the runtime target is the legacy .NET Framework 4.8, not modern .NET. Key dependencies: Dapplo.Windows (P/Invoke wrappers), SixLabors.ImageSharp, log4net, HtmlAgilityPack. Heavy use of Windows-specific APIs: DirectX, COM Interop (Office 15.x), P/Invoke, WinRT. |
| **Gap** | .NET Framework 4.8 is legacy — it does not support cross-platform deployment, cannot run in Linux containers, and has a narrower cloud-native tooling ecosystem compared to modern .NET (6/7/8/9). The dependency on COM Interop and P/Invoke makes migration to modern .NET complex. |
| **Recommendation** | Evaluate migration to .NET 8/9 (LTS). The Windows-specific UI (WinForms/WPF) can still target `net8.0-windows` but gains access to modern .NET libraries, better performance, and improved cloud tooling. This is a prerequisite for containerization or any cloud deployment of backend components. |
| **Evidence** | `src/Directory.Build.props` (TargetFramework=net480), `src/Greenshot.Base/Greenshot.Base.csproj`, `src/Greenshot/Greenshot.csproj` |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Greenshot is a single deployable unit (WinExe) with 12 projects compiled into one application. While a plugin architecture exists (7 plugins for external integrations), all code runs in a single process with shared static state, shared configuration (custom INI system), and shared UI thread. The core modules (capture engine, editor, forms, configuration) have no defined interfaces or boundaries — they communicate through direct references and static instances. |
| **Gap** | Tightly-coupled monolith with no clear module boundaries for cloud decomposition. Pervasive shared state through static classes and direct cross-module references. The plugin architecture provides some extension points but the core is undifferentiated. |
| **Recommendation** | If cloud modernization is planned, identify service boundaries within the plugin architecture. The existing plugins (Box, Dropbox, Imgur, Confluence, Jira) are natural candidates for extraction into cloud-mediated integration services. The capture and image processing logic could become a cloud-accessible service. |
| **Evidence** | `src/Greenshot.sln` (12 projects, single output), `src/Greenshot/GreenshotMain.cs` (monolithic entry point), `src/Directory.Build.props` (shared build properties) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Sync request/response is the correct design for a desktop application — there is no inter-service communication to evaluate. All third-party API calls (Box, Dropbox, Imgur) are user-initiated upload operations that appropriately use async/await patterns within the desktop client. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | Desktop application with no inter-service communication; plugin HTTP calls use Dapplo.HttpExtensions |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. No operations exceed 30 seconds in normal usage — screenshot capture, annotation, and file saving are all sub-second operations. Image uploads to external services use async HTTP but are user-initiated and display progress feedback. Not applicable by design. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/Greenshot/GreenshotMain.cs` — synchronous desktop operations; HTTP uploads use async patterns with UI feedback |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning exists. Greenshot is a desktop application that does not expose any API. The application consumes third-party APIs (Box, Dropbox, Imgur, Confluence, Jira) but does not provide one. |
| **Gap** | No API exists to version. If cloud backend services are developed, versioning must be designed from the start. |
| **Recommendation** | When building cloud APIs for any backend services, implement URL-path versioning (e.g., /v1/) from the first release to ensure backward compatibility for the desktop client. |
| **Evidence** | No API routes, controllers, or API specification files in repository |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No service discovery mechanism exists. Third-party service endpoints (Box, Dropbox, Imgur, Confluence, Jira) are hardcoded as constants in plugin source code. The application does not participate in any service mesh or discovery system. |
| **Gap** | All external service endpoints are hardcoded constants. No dynamic discovery, no registry, no configuration-driven endpoint resolution. |
| **Recommendation** | When building cloud backend services, implement service discovery from the start. Use environment-variable-based endpoint configuration at minimum; consider AWS Cloud Map or App Mesh for production. |
| **Evidence** | Plugin source files with hardcoded API endpoint URLs |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Screenshots and annotations are stored on the local file system. The application saves images to user-specified directories in various formats (PNG, JPEG, BMP, GIF, TIFF). There is no cloud object storage, no managed storage service, and no parsing or indexing pipeline. |
| **Gap** | Data is on local file systems with no cloud accessibility. If cloud features are added (cross-device sync, shared screenshots), S3 would be needed. |
| **Recommendation** | For any cloud storage features, store images in S3 with appropriate lifecycle policies. Consider adding Textract for OCR on screenshots if text extraction features are desired. |
| **Evidence** | Source code file-save operations; no S3 or cloud storage references |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application uses a custom INI-based configuration system (`IniConfig`) that provides a centralized settings layer. File I/O for screenshots uses .NET System.IO APIs directly. The custom config system provides some structure but is not a formal data access layer — it's specific to this application with no standard interfaces. |
| **Gap** | Data access is through a custom, non-standard INI system and direct file I/O. No repository pattern, no abstraction layer for storage. |
| **Recommendation** | If the application expands to cloud storage, implement a storage abstraction layer (repository pattern) that can target both local file system and S3/cloud storage interchangeably. |
| **Evidence** | Custom `IniConfig` class references throughout source; direct `System.IO` usage for file operations |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy a database. DATA-Q3 does not apply. No database engine of any kind (SQL, NoSQL, embedded) is used by the application. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database references in any .csproj, no connection strings, no SQL files |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures or proprietary SQL exists. All business logic (screenshot capture, image processing, annotation, plugin integrations) is implemented in the C# application layer. No database coupling of any kind. |
| **Gap** | N/A — no database coupling exists. |
| **Recommendation** | N/A — this is the desired state. |
| **Evidence** | All 441 C# source files contain application logic; no SQL files in repository |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or cloud audit logging exists. The application uses log4net for local application logging (debug, error, info levels) with four configuration variants (debug/release/portable/zip). Logs are written to local files only. No cloud-based audit trail, no immutable log storage. |
| **Gap** | No cloud audit logging. Local log4net logs are not audit-grade — they can be deleted, modified, and have no tamper-proof storage. |
| **Recommendation** | If cloud services are introduced, enable CloudTrail from day one with log file validation and S3 Object Lock for immutable storage. For the current desktop app, the local log4net logging is appropriate for its context. |
| **Evidence** | `src/Greenshot/log4net*.xml` (4 config variants), `src/Greenshot.Base/Greenshot.Base.csproj` (log4net 3.3.0 dependency) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no database, S3 bucket, EBS volume, or similar. SEC-Q2 does not apply. Local user data (screenshots, configuration) is stored on the user's file system and protected by OS-level encryption (BitLocker, if enabled). |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No cloud storage, database, or managed data services in repository |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API exists to authenticate. The application is a desktop client that does not expose any API endpoints. When acting as an OAuth client (for Box, Dropbox, Imgur), it uses OAuth 2.0 flows to authenticate to third-party services — but this is outbound client auth, not inbound API protection. |
| **Gap** | No API authentication exists because no API exists. If backend services are developed, authentication must be designed. |
| **Recommendation** | When building backend APIs, implement OAuth2/JWT authentication on all endpoints from the start. Consider Amazon Cognito for user identity management (integrates well with API Gateway). |
| **Evidence** | `.Credentials.template` files showing OAuth client credential patterns; no inbound API or auth middleware |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity provider integration exists. The application authenticates to third-party services (Box, Dropbox, Imgur, Confluence, Jira) using per-service OAuth flows with application-specific credentials. There is no SSO, no central IdP, and no unified identity layer. |
| **Gap** | Each plugin manages its own authentication independently. No centralized identity provider. |
| **Recommendation** | If cloud services are added, integrate with Amazon Cognito as the centralized identity provider. Enable SSO for cloud-connected features and federate with corporate IdPs (Okta, Azure AD) if enterprise deployment is a goal. |
| **Evidence** | Per-plugin OAuth credential templates (Box, Dropbox, Imgur); Confluence/Jira plugins use separate authentication |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Build-time secrets (OAuth client IDs and secrets for Box, Dropbox, Imgur) are managed via GitHub Secrets and injected as environment variables during CI/CD. The `Directory.Build.props` uses MSBuild token replacement (`$(Box13_ClientSecret)`) to inject secrets at compile time. Template files (`.Credentials.template`) contain placeholder variables, not actual secrets. No plaintext credentials exist in the repository. |
| **Gap** | Secrets are properly managed in CI/CD via GitHub Secrets, but there is no rotation mechanism. OAuth client credentials are static — no automated rotation is configured. No dedicated secrets management service (AWS Secrets Manager, HashiCorp Vault) is in use. |
| **Recommendation** | For current desktop app context, GitHub Secrets is appropriate. If cloud services are introduced, migrate to AWS Secrets Manager with automated rotation for all service credentials. |
| **Evidence** | `src/Directory.Build.props` (token replacement for secrets), `.github/workflows/release.yml` (env vars from GitHub Secrets), `.Credentials.template` files (placeholder variables only) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute hardening or patching strategy exists. The application runs on end-user Windows machines — there is no server-side compute to harden. The CI/CD uses `windows-latest` GitHub-hosted runners which are maintained by GitHub, but there is no evidence of hardened build images or vulnerability scanning of the build environment. |
| **Gap** | No compute hardening. No vulnerability scanning (Inspector, Snyk, etc.). No hardened base images. |
| **Recommendation** | Add dependency vulnerability scanning (Dependabot for NuGet packages). If cloud compute is introduced, use hardened base images (Windows Server Core with CIS benchmarks) and enable AWS Inspector scanning. |
| **Evidence** | `.github/workflows/release.yml` (runs-on: windows-latest, no scanning steps) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No security scanning tools are integrated into the CI/CD pipeline. No SAST (SonarQube, Semgrep, CodeGuru), no dependency scanning (Dependabot, `dotnet list package --vulnerable`), no container scanning (N/A — no containers). The pipeline builds and packages without any security validation step. |
| **Gap** | No security scanning of any kind in the pipeline. Vulnerabilities in NuGet dependencies (SixLabors.ImageSharp, HtmlAgilityPack, log4net, Svg, etc.) could reach release artifacts undetected. |
| **Recommendation** | (1) Enable Dependabot for NuGet packages in the GitHub repository. (2) Add `dotnet list package --vulnerable` as a CI step. (3) Consider adding Semgrep or SonarQube for SAST scanning of C# code. |
| **Evidence** | `.github/workflows/release.yml` (no security scanning steps), absence of `.github/dependabot.yml` |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing is instrumented. The application uses log4net for local logging but has no OpenTelemetry, X-Ray, or any tracing SDK. As a desktop application, there are no distributed service boundaries to trace. |
| **Gap** | No distributed tracing. For a standalone desktop app this is expected, but if cloud services are added, tracing must be instrumented. |
| **Recommendation** | When cloud backend services are introduced, instrument OpenTelemetry from day one with X-Ray integration for distributed trace correlation. |
| **Evidence** | No OpenTelemetry or tracing SDK in any .csproj; only log4net for local logging |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no user-facing surface for which SLOs are meaningful. OPS-Q2 does not apply. Greenshot is a desktop application with no server-side API or persistent data store — SLOs (availability, latency) are not applicable to desktop software. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | Desktop application with no server-side component |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom metrics are published. No CloudWatch metrics, no telemetry, no analytics of any kind. The application has no instrumentation for business outcomes (screenshots taken, uploads completed, features used). |
| **Gap** | No metrics collection. No visibility into application usage patterns or feature adoption. |
| **Recommendation** | If usage analytics are desired, implement opt-in telemetry. For cloud features, publish business metrics to CloudWatch (uploads completed, errors by plugin, etc.). |
| **Evidence** | No metrics SDK in any .csproj; no CloudWatch or telemetry references |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting exists. There is no monitoring infrastructure — no CloudWatch alarms, no error rate tracking, no latency monitoring. The application has no server-side component to monitor. |
| **Gap** | No alerting or anomaly detection of any kind. |
| **Recommendation** | When cloud services are introduced, configure CloudWatch anomaly detection on error rates and latency for all API endpoints. Set up composite alarms with PagerDuty/OpsGenie integration. |
| **Evidence** | Absence of any monitoring, alerting, or anomaly detection configuration |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Deployments publish directly to GitHub Releases and Chocolatey. The release workflow creates a GitHub Release with installer and portable ZIP artifacts. Releases are marked as pre-releases with auto-generated release notes. Chocolatey publish triggers on full releases (not pre-releases). This provides a basic two-stage release (pre-release → full release) but no canary, blue/green, or gradual rollout to users. |
| **Gap** | No staged rollout strategy. All users who check for updates receive the same version simultaneously. No ability to roll back a bad release to a subset of users. |
| **Recommendation** | Implement a beta channel — publish to a separate GitHub pre-release track or Chocolatey pre-release feed before promoting to stable. Consider auto-update with staged rollout (5% → 25% → 100% over days). |
| **Evidence** | `.github/workflows/release.yml` (prerelease: true), `.github/workflows/choco-publish.yml` (triggers on published releases) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No automated tests exist in the repository — no unit tests, no integration tests, no UI tests, no test projects. The solution file contains 12 projects, none of which are test projects. There is no test framework dependency (xUnit, NUnit, MSTest) in any .csproj file. |
| **Gap** | Zero test coverage. This is the most critical gap for any modernization effort — without tests, refactoring or migration carries extreme regression risk. |
| **Recommendation** | (1) Add a test project targeting xUnit or NUnit. (2) Start with unit tests for core image processing logic (ImageSharp operations, format conversion). (3) Add integration tests for plugin API interactions (using mocked HTTP). (4) Add the test execution step to the GitHub Actions pipeline. |
| **Evidence** | `src/Greenshot.sln` (12 projects, 0 test projects), absence of any test framework references in .csproj files |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response automation exists. No runbooks, no SSM Automation documents, no self-healing patterns. For a desktop application, server-side incident response is not applicable — but there is also no documented process for handling release issues (bad builds, critical bugs). |
| **Gap** | No incident response process, automated or otherwise. |
| **Recommendation** | Document a release rollback process (how to yank a bad Chocolatey package, how to unpublish a GitHub Release). When cloud services are added, implement automated runbooks for common failure scenarios. |
| **Evidence** | Absence of any runbook, SSM document, or incident response configuration |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership model exists. No dashboards, no named alarm owners, no team attribution. The repository has no CODEOWNERS file, no monitoring configuration, and no SLO definitions. |
| **Gap** | No observability ownership of any kind. |
| **Recommendation** | Add a CODEOWNERS file for code review ownership. When cloud services are added, establish per-service dashboards with named owners and SLO definitions with team attribution. |
| **Evidence** | Absence of CODEOWNERS, dashboards, or observability configuration |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging exists because no AWS resources exist. The application is a desktop tool with no cloud infrastructure to tag. |
| **Gap** | No tagging governance. If cloud resources are introduced, tagging must be established from the start. |
| **Recommendation** | When cloud infrastructure is introduced, establish a tagging standard (Environment, Owner, Service, CostCenter) and enforce it via IaC required tags in Terraform/CDK modules. |
| **Evidence** | Absence of any AWS resources or IaC defining resources |

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
| `.github/workflows/release.yml` | INF-Q1, INF-Q11, SEC-Q6, SEC-Q7, OPS-Q5 | Main CI/CD pipeline — build, package, deploy stages |
| `.github/workflows/choco-publish.yml` | INF-Q11, OPS-Q5 | Chocolatey package publishing workflow |
| `.github/workflows/purge-cloudflare-cache.yml` | INF-Q11 | CDN cache purge automation |
| `.github/workflows/update-gh-pages.yml` | INF-Q11 | GitHub Pages rebuild trigger |
| `src/Directory.Build.props` | APP-Q1, APP-Q2, SEC-Q5 | Shared build properties — target framework, secrets injection |
| `src/Greenshot.Base/Greenshot.Base.csproj` | APP-Q1, SEC-Q1 | Base library project — dependencies, log4net |
| `src/Greenshot/Greenshot.csproj` | APP-Q1, APP-Q2 | Main application project — WinExe output |
| `src/Greenshot/GreenshotMain.cs` | INF-Q3, INF-Q5, APP-Q4 | Application entry point — TLS config, startup |
| `src/Greenshot.sln` | APP-Q2, OPS-Q6 | Solution file — 12 projects, no test projects |
| `src/Greenshot/App.config` | APP-Q1 | Runtime configuration — .NET Framework 4.7.2 target |
| `src/Greenshot/log4net*.xml` | SEC-Q1 | Logging configuration (4 variants) |
| `src/Greenshot.Plugin.Dropbox/Greenshot.Plugin.Dropbox.Credentials.template` | SEC-Q5 | OAuth credential template with placeholder tokens |
| `LICENSE` | — | GPLv3 license |
| `README.md` | — | Project documentation |
