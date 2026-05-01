# Modernization Readiness Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | serverless/serverless |
| **Date** | 2026-04-29 |
| **Repo Type** | monorepo |
| **Service Archetype** | stateless-utility (auto-detected) |
| **Priority** | P2 |
| **Tags** | javascript, serverless, iac, cli |
| **Context** | Serverless Framework CLI for building and deploying serverless apps. |
| **Overall Score** | 2.37 / 4.0 |

**Archetype Justification**: This monorepo is a CLI tool distributed as an npm package. It has no persistent state of its own (deployment state is stored externally in S3/Dashboard), no database connections for its own operation, and all operations are synchronous command-line executions. The MCP package exposes a local SSE server for IDE integration but is not a deployed cloud service. Classified as `stateless-utility` because it performs stateless computation (CloudFormation template generation, AWS API calls) with no owned persistent state.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.73 / 4.0 | 🟠 Needs Work |
| Application Architecture (APP) | 3.00 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 3.00 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 2.14 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 2.00 / 4.0 | 🟠 Needs Work |
| **Overall** | **2.37 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q1: Managed Compute | 1 | No managed compute infrastructure — CLI tool distributed as npm package with no cloud compute for its own operation. | Limits ability to run the tool as a managed cloud service; distribution relies on S3/CloudFront via manual CLI commands in CI. |
| 2 | INF-Q2: Managed Databases | 1 | No database infrastructure defined — the CLI tool has no database needs of its own. | No direct modernization impact for a CLI tool, but limits state management capabilities. |
| 3 | INF-Q5: Network Security | 1 | No VPC, security groups, or network segmentation — no cloud infrastructure to secure. | No deployed infrastructure to protect; gap is structural given the CLI tool nature. |
| 4 | INF-Q10: IaC Coverage | 1 | Release infrastructure (S3 buckets, CloudFront distributions, IAM roles) managed via ClickOps — not defined in IaC. | Manual infrastructure changes are error-prone and non-reproducible; makes disaster recovery harder. |
| 5 | SEC-Q1: Audit Logging | 1 | No CloudTrail or audit logging configuration — the CLI tool has no infrastructure to audit. | No audit trail for infrastructure changes to the release pipeline resources. |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 3). Comprehensive GitHub Actions workflows for CI/CD are in place across `.github/workflows/`.
- **What it enables:** A DevOps agent that triggers deployments, checks build status, monitors release pipeline progress, and manages the multi-stage release process (test → canary → stable → npm publish).
- **Additional steps:** Expose GitHub Actions API access for the agent; create a structured interface for release status querying.
- **Effort:** Low

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists. Extensive documentation found in `docs/`, `README.md`, `TESTING.md`, `CONTRIBUTING.md`, `AGENTS.md`, `SECURITY.md`, `VERSIONING.md`, `RELEASE_PROCESS.md`, and the `packages/serverless/lib/plugins/aws/bedrock-agentcore/README.md`.
- **What it enables:** A RAG-based knowledge agent that indexes all project documentation and provides instant answers to developer questions about the Serverless Framework architecture, testing procedures, release process, and contribution guidelines.
- **Additional steps:** Index all markdown files and code comments into a vector store. The existing MCP package (`packages/mcp/`) already provides a `docs` tool that serves documentation for the Serverless Framework and Container Framework — this could be extended with RAG capabilities using Amazon Bedrock.
- **Effort:** Medium

### API-Aware Agent (MCP Extension)

- **Prerequisite:** API docs exist (APP-Q5 = 2). The MCP server exposes a well-documented set of tools with Zod schema validation in `packages/mcp/src/tools-definition.js`.
- **What it enables:** The existing MCP server already functions as an API-aware agent interface for AI IDEs. Extension opportunities include adding more tools for the Serverless Framework's own management (e.g., plugin management, configuration validation).
- **Additional steps:** Generate OpenAPI specification from the existing Zod schemas; add additional tools for framework-internal operations.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 — modular monolith with well-defined package boundaries; primary trigger not met. |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 1 but contextual guard prevents trigger: this is a CLI tool, not an EC2/VM-based workload. Dockerfiles found are for user examples and dev-mode containers, not for the CLI itself. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 — no stored procedures or commercial DB engines. No commercial database engines detected. |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = 1 but this is a CLI tool with no database needs. No databases to migrate. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads exist. Contextual guard prevents trigger: CLI tool has no streaming/ETL/analytics needs. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (primary): Release infrastructure (S3, CloudFront, IAM roles) not defined in IaC. |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. Context "Serverless Framework CLI for building and deploying serverless apps" does not contain AI-related signal terms. Note: The repo already has Bedrock AgentCore plugin support for user deployments. |

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 1):**
The release pipeline in `.github/workflows/release-framework.yml` and `.github/workflows/release-binary-installer.yml` uploads artifacts to S3 buckets and invalidates CloudFront distributions using AWS CLI commands directly in workflow steps. The underlying infrastructure — S3 buckets (`install.serverless.com`, canary/stable distribution buckets), CloudFront distributions (IDs `E1USPSJN28WQ8U`, `E3OEL4OJF1G5FG`), and IAM roles (`GithubActionsDeploymentRole` across 3 AWS accounts: `762003938904`, `377024778620`, `802587217904`) — is not defined in IaC. These resources were likely created manually (ClickOps).

**Current CI/CD State (INF-Q11 = 3):**
CI/CD automation is strong with comprehensive GitHub Actions workflows covering lint, unit tests, integration tests, cross-platform testing, canary release, stable release, and npm publish. However, there is no automated rollback mechanism in the release pipeline.

**Deployment Strategy Gaps (OPS-Q5 = 3):**
The release pipeline has a multi-stage structure (test → canary → stable → npm), which is a form of canary deployment. However, there is no automated rollback — if the canary release fails, manual intervention is required.

**Testing Gaps (OPS-Q6 = 3):**
Integration tests exist and run in CI for critical workflows, but some test suites (domains, SAM) appear to be run separately.

**Recommendations:**
1. **Define release infrastructure in IaC:** Use AWS CDK or CloudFormation (given the preference for AWS-native tooling) to define S3 buckets, CloudFront distributions, IAM roles, and OIDC providers. This enables reproducibility, audit trails, and disaster recovery.
2. **Add automated rollback:** Implement automated rollback in the release pipeline if canary validation fails, such as reverting the S3 upload and CloudFront cache.
3. **Consolidate CI/CD workflows:** Consider unifying the separate CI workflows (ci-framework, ci-engine, ci-binary-installer, ci-python) into a composite workflow that runs all relevant checks based on changed paths.

**Representative AWS Services:** CloudFormation, CDK, CodePipeline, CodeBuild, S3, CloudFront, IAM

**Links:**
- [Move to Modern DevOps Learning Plan](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | This is a CLI tool monorepo distributed as an npm package (`@serverlessinc/sf-core`, `@serverless/framework`). It has no compute infrastructure of its own — no EC2 instances, no ECS tasks, no Lambda functions, no Fargate services. The tool *generates* CloudFormation for users' Lambda/ECS/Fargate deployments but does not run on managed compute itself. The binary installer (Go) is distributed via S3, and the npm package is distributed via npm registry. |
| **Gap** | No managed compute infrastructure exists for the tool itself. This is expected for a CLI tool — it runs on the user's local machine or CI/CD runner, not on cloud compute. |
| **Recommendation** | For a CLI tool, managed compute is not directly applicable. If the team ever considers offering the Serverless Framework as a hosted service (e.g., deployment-as-a-service), consider Lambda or ECS Fargate for the compute layer. |
| **Evidence** | `package.json` (npm workspaces), `packages/sf-core/package.json` (bin: sf-core), `.github/workflows/release-framework.yml` (npm publish), `.github/workflows/release-binary-installer.yml` (S3 binary distribution) |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database infrastructure is defined in this repository. The CLI tool does not require a database for its own operation. State is managed through S3 (deployment artifacts) and the Serverless Dashboard platform. The `RELEASES_MONGO_URI` secret in the release workflow suggests a MongoDB connection for release metadata, but this is external and not defined in the repo. |
| **Gap** | No database infrastructure to assess. The `RELEASES_MONGO_URI` suggests an external MongoDB instance used during releases, but its management and configuration are outside this repository. |
| **Recommendation** | If the release metadata MongoDB instance is self-managed, consider migrating to Amazon DocumentDB or DynamoDB (preferred per preferences) for managed operation. Define the connection and any required infrastructure in IaC within this repository or a dedicated infrastructure repository. |
| **Evidence** | `.github/workflows/release-framework.yml` (RELEASES_MONGO_URI secret reference), `packages/engine/src/index.js` (state store pattern with load/save, no direct DB connections) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | **Archetype: stateless-utility.** No multi-step workflows exist that require dedicated orchestration. The CLI tool's execution flow is a synchronous command pipeline: parse CLI → route to runner → execute command → finalize. The `packages/engine/src/index.js` orchestrates deployment steps (deploy, dev, remove) as sequential operations within a single CLI execution. This is appropriate for a stateless utility — there is nothing to orchestrate with Step Functions or Temporal. |
| **Gap** | N/A — no orchestration gap exists for a stateless-utility archetype. |
| **Recommendation** | Dedicated workflow orchestration is not applicable for this archetype and does not represent a gap. The CLI's sequential execution model is the correct design. |
| **Evidence** | `packages/sf-core/src/index.js` (sequential run flow), `packages/sf-core/src/lib/router.js` (route → getRunner → run → finalize), `packages/engine/src/index.js` (deploy/dev/remove sequential methods) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | **Archetype: stateless-utility.** Synchronous HTTP/CLI execution is the correct design for this tool. The CLI processes commands synchronously: user invokes CLI → CLI makes AWS API calls → returns results. There is no need for messaging or streaming infrastructure. The MCP server uses Server-Sent Events (SSE) for real-time communication with AI IDEs, which is appropriate for its local development tool context. |
| **Gap** | N/A — synchronous communication is the correct design for a CLI tool. |
| **Recommendation** | Adopting async messaging is NOT recommended — it would add operational complexity without architectural benefit. The synchronous CLI execution model is appropriate for this archetype. |
| **Evidence** | `packages/sf-core/src/index.js` (synchronous run), `packages/mcp/src/server.js` (SSE for local IDE communication), `packages/engine/src/index.js` (synchronous deploy/remove) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, security groups, NACLs, or network segmentation is defined in this repository. This is expected — the CLI tool runs on user machines and CI/CD runners, not in a VPC. The release pipeline uses OIDC-based AWS credentials (not long-lived keys) to access S3/CloudFront, which is a positive security practice. |
| **Gap** | No network infrastructure to secure. The release pipeline interacts with AWS services (S3, CloudFront) but has no VPC-level network controls defined. |
| **Recommendation** | For the release infrastructure, consider defining VPC endpoints for S3 access if the release pipeline were to run on self-hosted runners. Currently, using GitHub-hosted runners with OIDC authentication is an appropriate pattern. |
| **Evidence** | `.github/workflows/release-framework.yml` (OIDC role-to-assume, no VPC references), `.github/workflows/release-binary-installer.yml` (same pattern) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, or CloudFront is configured as an entry point for the tool itself. The CLI tool is invoked directly from the command line. CloudFront distributions exist for the binary installer (`install.serverless.com`) and release artifacts, but these serve as CDN distribution points, not API entry points with auth/throttling. The MCP server runs on localhost with no API gateway. |
| **Gap** | No API entry point with throttling, auth, or request validation. CloudFront is used as a CDN for distribution, not as a protected API entry point. |
| **Recommendation** | For the MCP server component, if it were ever exposed as a hosted service, add API Gateway (preferred) with authentication and throttling. For the current local-only MCP server, adding API-level authentication would protect against unauthorized local access. |
| **Evidence** | `packages/mcp/src/server.js` (Express server on localhost, no auth middleware), `.github/workflows/release-framework.yml` (CloudFront for CDN distribution) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. The CLI tool runs on user machines and CI/CD runners — there are no scalable cloud resources to configure. |
| **Gap** | No auto-scaling infrastructure to assess. |
| **Recommendation** | Auto-scaling is not applicable for a CLI tool distributed as an npm package. If the tool's distribution infrastructure (S3/CloudFront) needed scaling, CloudFront already provides automatic scaling for CDN distribution. |
| **Evidence** | No IaC files defining scalable resources found in repository. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration exists in the repository. The release artifacts are stored in S3 buckets (referenced in CI/CD workflows) but no backup retention, PITR, or cross-region replication is defined. The source code is backed up through Git (GitHub repository). |
| **Gap** | Release infrastructure S3 buckets have no visible backup configuration. If release artifacts in S3 are lost, they would need to be rebuilt from source. |
| **Recommendation** | Enable S3 versioning and lifecycle policies on release artifact buckets. Define these configurations in IaC (see INF-Q10 recommendation). Consider cross-region replication for the `install.serverless.com` bucket since it serves the global install script. |
| **Evidence** | `.github/workflows/release-binary-installer.yml` (S3 uploads to install.serverless.com), `.github/workflows/release-framework.yml` (S3 tarball uploads) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ deployment configuration exists. The CLI tool itself does not require high availability — it's a local tool. The distribution infrastructure (CloudFront + S3) inherently provides multi-region availability, but this is CloudFront's default behavior, not an explicit configuration choice. |
| **Gap** | No explicit HA configuration. CloudFront provides inherent redundancy for distribution. |
| **Recommendation** | For the distribution infrastructure, CloudFront already provides multi-PoP availability. Ensure S3 buckets are in a region with good global latency. Consider S3 cross-region replication for the install script bucket as a belt-and-suspenders measure. |
| **Evidence** | `.github/workflows/release-framework.yml` (CloudFront distribution IDs), `.github/workflows/release-binary-installer.yml` (CloudFront + S3 distribution) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC files (Terraform, CloudFormation, CDK) exist for the project's own infrastructure. The release pipeline references specific AWS resources by ID — S3 buckets (`install.serverless.com`), CloudFront distributions (`E1USPSJN28WQ8U`, `E3OEL4OJF1G5FG`), and IAM roles (`GithubActionsDeploymentRole` in 3 AWS accounts) — but none of these are defined in code. This is 100% ClickOps for the tool's own infrastructure. Note: The `.tf` files found at `packages/sf-core/tests/integration/resolvers/terraform/` are test fixtures, not infrastructure definitions. |
| **Gap** | All release infrastructure is manually created: S3 buckets (at least 3), CloudFront distributions (at least 2), IAM roles (at least 3 across accounts 762003938904, 377024778620, 802587217904), and OIDC providers. None are defined in IaC. |
| **Recommendation** | Define all release infrastructure in IaC using CloudFormation or CDK (keeping the stack AWS-native). This should include: (1) S3 buckets for release artifacts and install script, (2) CloudFront distributions for canary and stable release channels, (3) IAM roles for GitHub Actions OIDC access across all 3 AWS accounts, (4) OIDC identity providers for GitHub Actions. Store the IaC in a dedicated `infrastructure/` directory within this repository. |
| **Evidence** | `.github/workflows/release-framework.yml` (hardcoded CloudFront IDs E1USPSJN28WQ8U, E3OEL4OJF1G5FG; role-to-assume ARNs), `.github/workflows/release-binary-installer.yml` (hardcoded S3 bucket install.serverless.com, CloudFront ID E3OEL4OJF1G5FG), No `.tf`, `template.yaml`, or CDK files for infrastructure found. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive CI/CD automation via GitHub Actions: (1) **CI workflows**: `ci-framework.yml` (lint + engine tests + framework unit/integration tests), `ci-engine.yml` (engine unit tests), `ci-binary-installer.yml` (Go tests + production build), `ci-python.yml` (Python requirements tests). (2) **Release workflows**: `release-framework.yml` (test matrix across Ubuntu/ARM Linux/Windows → canary release → stable release → npm publish), `release-binary-installer.yml` (Go build + S3/CloudFront release). The release pipeline has a structured multi-stage flow with cross-platform testing. |
| **Gap** | No automated rollback mechanism in the release pipeline. If a canary release causes issues, manual intervention is required to revert. No formal deployment gates (e.g., smoke tests against canary before promoting to stable). |
| **Recommendation** | Add automated rollback capability to the release pipeline — if canary validation fails, automatically revert the S3 upload and CloudFront invalidation. Consider adding smoke tests between canary and stable release stages to validate the canary before promotion. |
| **Evidence** | `.github/workflows/ci-framework.yml`, `.github/workflows/ci-engine.yml`, `.github/workflows/ci-binary-installer.yml`, `.github/workflows/ci-python.yml`, `.github/workflows/release-framework.yml`, `.github/workflows/release-binary-installer.yml` |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Primary language is **JavaScript (Node.js 24+, ES Modules)** — first-class AWS SDK coverage with `@aws-sdk/*` v3 extensively used across all packages. Secondary language is **Go** for the binary installer (`binary-installer/go.mod`, Go 1.26.1). **Java** is used for runtime wrappers (`packages/serverless/lib/plugins/aws/invoke-local/runtime-wrappers/java`). All three languages have excellent AWS SDK support and mature cloud-native tooling ecosystems. |
| **Gap** | No significant gap. The language choices are well-suited for cloud-native development. |
| **Recommendation** | Continue with the current language stack. The extensive use of AWS SDK v3 (`@aws-sdk/*` at version 3.1015.0) demonstrates mature integration with AWS services. |
| **Evidence** | `package.json` (type: module), `packages/serverless/package.json` (25+ @aws-sdk/* dependencies at 3.1015.0), `binary-installer/go.mod` (Go 1.26.1), `.github/dependabot.yml` (npm, gomod, maven ecosystems) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The monorepo has well-defined package boundaries using npm workspaces: `@serverlessinc/sf-core` (CLI entry point), `@serverless/framework` (core framework), `@serverless/engine` (container engine), `@serverless/mcp` (MCP server), `@serverless/util` (shared utilities), `@serverlessinc/standards` (lint configs). Each package has its own `package.json`, test suite, and clear responsibility. However, circular dependencies exist: `sf-core` depends on `serverless`, `engine`, `mcp`, `util`; `engine` depends on `util` and `sf-core`; `serverless` depends on `sf-core`. The `*` workspace references mean all packages are tightly coupled at the version level. |
| **Gap** | Circular dependencies between `sf-core` ↔ `engine` and `sf-core` ↔ `serverless` indicate coupling. The `*` workspace version references mean packages cannot be versioned independently. All packages are built and released together as a single unit. |
| **Recommendation** | Consider breaking circular dependencies by extracting shared interfaces into `@serverless/util` or a new `@serverless/types` package. The engine importing from `@serverlessinc/sf-core/src/utils/general/index.js` (direct path import rather than package export) indicates tight coupling that could be addressed by exposing shared utilities through proper package exports. |
| **Evidence** | `packages/sf-core/package.json` (depends on serverless, engine, mcp, util with `*`), `packages/engine/package.json` (depends on util, sf-core with `*`), `packages/engine/src/index.js` (imports from `@serverlessinc/sf-core/src/utils/general/index.js` — direct path import) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | **Archetype: stateless-utility.** Synchronous request/response is the correct design for a CLI tool. All inter-package communication is via synchronous JavaScript `import` and function calls. The CLI execution flow is sequential: parse command → route → run → finalize. The MCP server uses SSE for streaming responses to AI IDEs, which is an appropriate async pattern for its specific use case but does not affect the overall synchronous CLI architecture. |
| **Gap** | N/A — synchronous communication is the correct design for a CLI tool. |
| **Recommendation** | Async communication is NOT recommended for this architecture. The synchronous CLI execution model is appropriate for a stateless-utility. The existing async/await usage for AWS API calls and file I/O is correctly applied. |
| **Evidence** | `packages/sf-core/src/index.js` (sequential await chain), `packages/sf-core/src/lib/router.js` (await route → getRunner → run → finalize), `packages/mcp/src/server.js` (SSE for IDE communication) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | **Archetype: stateless-utility, with long-running operations.** The CLI handles inherently long-running operations: CloudFormation deployments can take minutes. The framework uses polling patterns with progress spinners (`@serverless/util` progress module) to provide user feedback during long operations. The `dev` mode uses WebSocket connections to proxy events from AWS to local code. However, these are CLI-level patterns (progress bars, polling loops) rather than async job submission with status APIs. |
| **Gap** | Long-running operations (deployments, removals) block the CLI process. There is no async job submission pattern — the user must keep the terminal open. This is acceptable for a CLI tool but limits programmatic integration scenarios. |
| **Recommendation** | For the current CLI use case, the synchronous polling approach with progress spinners is appropriate. If the Serverless Framework is ever consumed as a library (via `@serverless/engine`), consider adding an async deployment API that returns a job ID with status polling endpoint. |
| **Evidence** | `packages/sf-core/src/index.js` (progress.get('main')), `packages/engine/src/index.js` (await deploy(), await remove() — synchronous long-running), `packages/sf-core/src/lib/router.js` (progressive finalization) |

#### APP-Q5: API Versioning

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The MCP server exposes tools with no explicit API versioning — the server is `version: '1.0.0'` but individual tool endpoints have no version prefix. The npm packages use semantic versioning (`sf-core` at 4.33.2, `framework` at 4.0.0) which provides consumer-facing version contracts. The CLI commands have no versioning mechanism — breaking changes are handled through major version bumps. |
| **Gap** | No explicit API versioning strategy for the MCP server tools. The CLI command interface has no version prefixing. API changes are managed through npm semver rather than endpoint versioning. |
| **Recommendation** | For the MCP server, add tool versioning to allow AI IDEs to target specific tool versions and ensure backward compatibility. For the programmatic API surface (`@serverless/engine`), document version compatibility and consider adding API version headers. |
| **Evidence** | `packages/mcp/src/server.js` (McpServer version: '1.0.0', no tool versioning), `packages/mcp/src/tools-definition.js` (tools registered without version prefixes), `packages/sf-core/package.json` (version: 4.33.2) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Inter-package communication uses npm workspace resolution with `*` version references. The `sf-core/src/lib/router.js` implements a runner discovery pattern that dynamically selects the appropriate runner (ComposeRunner, CfnRunner, TraditionalRunner, ServerlessContainerFrameworkRunner, ServerlessAiFrameworkRunner) based on configuration files found in the working directory. This is a form of convention-based discovery but uses hardcoded runner class imports. Environment variables are used for API endpoints (Serverless Dashboard, platform events). |
| **Gap** | Service discovery is primarily through npm workspace resolution and hardcoded imports. Environment variables are used for external service endpoints (Dashboard API, platform event endpoints) but there is no dynamic discovery mechanism. |
| **Recommendation** | The current approach is appropriate for a CLI tool monorepo. The runner discovery pattern in `router.js` is well-designed. For external service endpoints (Dashboard, platform), consider centralizing endpoint configuration in a single module rather than using scattered environment variables. |
| **Evidence** | `packages/sf-core/src/lib/router.js` (runner discovery via configFileNames matching), `packages/sf-core/package.json` (workspace `*` references), `packages/util/src/telemetry/` (platform event client endpoints) |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The CLI tool uses S3 extensively for deployment artifacts — `@aws-sdk/client-s3` is a dependency of `sf-core`, `engine`, and `util`. Deployment packages (.zip files) are uploaded to S3 deployment buckets. Release artifacts (tarballs) are stored in S3 and served through CloudFront. The engine uses an S3-based state store pattern (`stateStore.load()` / `stateStore.save()`). However, there is no parsing pipeline for unstructured data — files are stored and retrieved without content analysis. |
| **Gap** | S3 is used for storage but no automated parsing or extraction pipeline exists. Deployment artifacts are stored as opaque blobs without content indexing. |
| **Recommendation** | For the current CLI tool use case, S3 storage without parsing is appropriate. If future features require analyzing deployment artifacts (e.g., scanning for security issues, analyzing code patterns), consider adding Textract or custom parsing pipelines. |
| **Evidence** | `packages/sf-core/package.json` (@aws-sdk/client-s3), `packages/engine/package.json` (@aws-sdk/client-s3), `packages/engine/src/index.js` (stateStore.load/save pattern), `.github/workflows/release-framework.yml` (S3 tarball uploads) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The engine uses a centralized state store pattern — `ServerlessEngine` constructor requires a `stateStore` with `load()` and `save()` methods. This provides a unified interface for state persistence regardless of the underlying storage (S3, local filesystem). The `@serverless/util` package provides shared utilities for S3 access and state management. However, some packages access AWS services directly (e.g., `@aws-sdk/client-cloudformation` in both `sf-core` and `serverless`) without going through a centralized access layer. |
| **Gap** | AWS SDK clients are instantiated in multiple packages independently. While the state store pattern centralizes state access, individual AWS service calls (CloudFormation, Lambda, S3) are scattered across the codebase without a single data access layer. |
| **Recommendation** | Consider centralizing AWS service client creation in `@serverless/util` or a new `@serverless/aws` package to ensure consistent configuration (retry policies, proxy settings, timeouts) across all packages. The `aws-sdk-v3-proxy` dependency in `@serverless/util` suggests some centralization exists for proxy configuration. |
| **Evidence** | `packages/engine/src/index.js` (stateStore.load/save interface), `packages/util/package.json` (aws-sdk-v3-proxy), `packages/serverless/package.json` (direct @aws-sdk/* dependencies), `packages/engine/package.json` (direct @aws-sdk/* dependencies) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No database engine is defined in this repository's own infrastructure. However, the AWS SDK dependencies are explicitly pinned at version `3.1015.0` across all packages — a form of "engine version" management for the tool's primary dependency. Node.js engine requirement is `>=18.0` in `packages/serverless/package.json`, and the CI runs on Node.js 24.x. Node.js 18 is approaching EOL. The Go binary installer uses Go 1.26.1. Dependabot is configured with version constraints that pin many dependencies to avoid Node.js 18-incompatible versions. |
| **Gap** | Node.js 18 minimum requirement is approaching EOL. Many Dependabot ignore rules exist specifically because packages drop Node.js 18 support (ora v9, open v11, p-limit v7, joi v18, etc.), which means the project is holding back dependency updates due to the Node.js 18 floor. |
| **Recommendation** | Plan a migration path to raise the minimum Node.js version to 20 or 22 (both LTS). This would unlock numerous blocked dependency updates and improve security posture. Document the version update procedure and migration timeline. |
| **Evidence** | `packages/serverless/package.json` (engines: node >=18.0), `.github/dependabot.yml` (14 ignore rules for Node.js 18 incompatibility), `.github/workflows/ci-framework.yml` (node-version: 24.x), `binary-installer/go.mod` (go 1.26.1) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs exist in this repository. The CLI tool has no database-backed data layer. All business logic is in the application layer (JavaScript/Node.js). The engine's state management uses a simple load/save pattern with JSON serialization and Zod schema validation. |
| **Gap** | N/A — no stored procedures or database coupling. |
| **Recommendation** | No action needed. The application-layer business logic approach is appropriate and eliminates database coupling concerns. |
| **Evidence** | No `.sql` files found in repository (searched for CREATE PROCEDURE, CREATE TRIGGER, CREATE FUNCTION). `packages/engine/src/index.js` (Zod schema validation for state, JSON serialization). |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or audit logging configuration exists in the repository. The release pipeline uses AWS IAM roles via OIDC federation, which would be logged by CloudTrail in the target AWS accounts — but CloudTrail configuration is not defined or referenced in this repo. |
| **Gap** | No audit logging configuration for the release infrastructure. CloudTrail may be configured in the target AWS accounts but is not defined or verified here. |
| **Recommendation** | Define CloudTrail configuration in IaC for the AWS accounts used by the release pipeline (762003938904, 377024778620, 802587217904). Enable log file validation and store logs in an S3 bucket with Object Lock for immutability. |
| **Evidence** | No `aws_cloudtrail`, CloudTrail, or audit logging resources found. `.github/workflows/release-framework.yml` (uses OIDC roles in 3 AWS accounts). |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No KMS or encryption-at-rest configuration exists in the repository. The S3 buckets used for release artifacts may have default encryption enabled, but this is not defined or verified in the codebase. |
| **Gap** | No encryption configuration for release artifact S3 buckets. No KMS key management visible. |
| **Recommendation** | Define S3 bucket encryption (using S3-managed keys at minimum, customer-managed KMS keys preferred) in IaC for all release artifact buckets. This should be part of the IaC initiative recommended in INF-Q10. |
| **Evidence** | No KMS, encryption, or `kms_key_id` references found in infrastructure definitions. `.github/workflows/release-framework.yml` (S3 uploads without explicit encryption flags). |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The CLI uses license keys (`SERVERLESS_LICENSE_KEY`) and access keys (`SERVERLESS_ACCESS_KEY`) for authentication with the Serverless Dashboard. GitHub Actions uses OIDC federation for AWS access (role-to-assume). The MCP server (`packages/mcp/src/server.js`) has **no authentication** — any local process can connect to the SSE endpoint. The MCP tools accept AWS profile/region parameters for downstream AWS calls but the MCP server itself has no auth. |
| **Gap** | The MCP server has no authentication. While it runs on localhost, any local process can invoke MCP tools that make AWS API calls using the user's configured credentials. This is a risk in shared development environments. API key/static credential pattern is used rather than OAuth2/JWT. |
| **Recommendation** | Add authentication to the MCP server — at minimum, a session token generated at startup. For the CLI authentication flow, consider migrating from license key/access key patterns to OAuth2/JWT-based authentication with the Serverless Dashboard. |
| **Evidence** | `packages/mcp/src/server.js` (no auth middleware on Express routes), `packages/mcp/src/tools-definition.js` (tools accept profile/region but no auth token), `.github/workflows/ci-framework.yml` (SERVERLESS_LICENSE_KEY_DEV, SERVERLESS_ACCESS_KEY_DEV secrets), `.github/workflows/release-framework.yml` (OIDC role-to-assume) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The CLI integrates with the Serverless Dashboard for authentication, which acts as a centralized identity provider. GitHub Actions uses OIDC federation with AWS IAM roles for CI/CD authentication. The `sf-core/src/lib/auth/` directory and `jwt-decode` dependency indicate JWT-based token handling with the Serverless Dashboard. The CLI supports AWS SSO credential resolution. |
| **Gap** | The Serverless Dashboard acts as the IdP, but some legacy auth paths remain (license keys, access keys). OIDC federation is used for CI but not for all CLI authentication flows. |
| **Recommendation** | Continue the migration toward centralized identity with the Serverless Dashboard as the primary IdP. Deprecate direct license key authentication in favor of Dashboard SSO flows. Ensure all CLI auth flows go through the same identity pipeline. |
| **Evidence** | `packages/sf-core/package.json` (jwt-decode dependency), `packages/sf-core/src/lib/auth/` (auth module directory), `.github/workflows/release-framework.yml` (OIDC role-to-assume), `README.md` (AWS SSO support documentation) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GitHub Actions uses encrypted secrets for sensitive values: `SERVERLESS_LICENSE_KEY_DEV`, `SERVERLESS_ACCESS_KEY_DEV`, `RELEASES_MONGO_URI`. Secrets are injected as environment variables only in the specific workflow steps that need them. No hardcoded credentials found in source code. The `.env` files in the test fixtures contain test values, not production secrets. However, there is no evidence of automated secret rotation. |
| **Gap** | No automated secret rotation is configured. The `RELEASES_MONGO_URI` connection string suggests database credentials are stored as a GitHub secret without rotation. |
| **Recommendation** | Implement automated rotation for the GitHub Actions secrets, particularly `RELEASES_MONGO_URI`. Consider using AWS Secrets Manager for secrets that need rotation, with GitHub Actions fetching secrets at runtime rather than using static GitHub secrets. |
| **Evidence** | `.github/workflows/ci-framework.yml` (secrets.SERVERLESS_LICENSE_KEY_DEV, secrets.SERVERLESS_ACCESS_KEY_DEV), `.github/workflows/release-framework.yml` (secrets.RELEASES_MONGO_URI), `.github/dependabot.yml` (no hardcoded credentials), test fixture `.env` files contain only test values |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Dependabot is comprehensively configured for all dependency ecosystems: npm (root workspace), npm (framework-dist), npm (sf-core-installer), gomod (binary-installer), maven (Java runtime wrappers), and github-actions. Dependency updates are grouped (aws-sdk, dev-dependencies, patch-updates) with cooldown periods. GitHub Actions are pinned to specific SHA hashes for supply chain security. However, no SAST or container scanning tools are configured. |
| **Gap** | No vulnerability scanning beyond Dependabot. No hardened base images for CI runners (using default GitHub-hosted runners). Dependabot catches known vulnerabilities in dependencies but does not scan application code. |
| **Recommendation** | Add `npm audit` to the CI pipeline to catch known vulnerabilities before merge. Consider adding GitHub's code scanning (CodeQL) for SAST coverage. The SHA-pinned GitHub Actions are an excellent supply chain security practice. |
| **Evidence** | `.github/dependabot.yml` (5 ecosystem configurations with grouping and cooldowns), `.github/workflows/ci-framework.yml` (SHA-pinned actions: actions/checkout@de0fac2e..., actions/setup-node@53b83947...), `.github/workflows/release-framework.yml` (SHA-pinned actions) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Dependabot is configured for dependency vulnerability scanning across all ecosystems (npm, gomod, maven, github-actions) with weekly update schedules. However, no SAST tools (SonarQube, Semgrep, CodeGuru) are integrated into the CI pipeline. No `npm audit` step exists in CI workflows. No container scanning for the Dockerfiles in the bedrock-agentcore examples or engine dev-mode containers. ESLint and Prettier are run for code quality but not for security analysis. |
| **Gap** | No SAST tool in the CI pipeline. No `npm audit` step. No container scanning. Dependabot provides dependency scanning but no application code security analysis. |
| **Recommendation** | Add `npm audit --audit-level=critical` as a CI step to block merges on critical dependency vulnerabilities. Integrate a SAST tool like CodeQL (free for public repos on GitHub) or Semgrep. Add container scanning for the Dockerfiles in `packages/serverless/lib/plugins/aws/bedrock-agentcore/examples/` and `packages/engine/src/lib/devMode/containers/`. |
| **Evidence** | `.github/dependabot.yml` (dependency scanning configured), `.github/workflows/ci-framework.yml` (no npm audit, no SAST steps), `.github/workflows/ci-engine.yml` (no security scanning steps), No `.snyk`, `sonar-project.properties`, or `.semgrepconfig` files found |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The CLI has a custom telemetry system in `packages/util/src/telemetry/` that sends usage and analysis events to the Serverless Dashboard platform. The `packages/sf-core/src/lib/router.js` creates detailed analysis events with machine ID, OS info, command details, and error information. However, this is custom telemetry/analytics — not distributed tracing with OpenTelemetry or X-Ray. There is no trace ID propagation across service boundaries. The logging system (`packages/util/src/logger/`) provides structured logging with namespaces (e.g., `log.get('core:router')`). |
| **Gap** | No OpenTelemetry or X-Ray instrumentation. Custom telemetry exists for analytics/usage tracking but does not provide request-level distributed tracing. No trace ID propagation between CLI and AWS services. |
| **Recommendation** | For a CLI tool, full distributed tracing is less critical than for a deployed service. However, adding OpenTelemetry instrumentation to the AWS SDK calls would provide valuable debugging information for users experiencing deployment issues. Consider adding trace context to the CLI's interaction with CloudFormation, S3, and other AWS services. |
| **Evidence** | `packages/util/src/telemetry/` (custom telemetry system), `packages/sf-core/src/lib/router.js` (createAnalysisEvent, createUsageEvent), `packages/util/src/logger/` (structured logging with namespaces) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found in the repository. As a CLI tool, traditional SLOs (latency p99, availability) are not directly applicable. However, the tool's distribution infrastructure (install script availability, npm package publish success rate) and deployment success rate could have SLO-like targets. |
| **Gap** | No formal SLO definitions for CLI tool performance, distribution availability, or deployment success rates. |
| **Recommendation** | Define SLOs for the distribution infrastructure: install script availability (e.g., 99.9% uptime for install.serverless.com), npm publish success rate, and binary download availability. Track CLI command success/failure rates using the existing telemetry system. |
| **Evidence** | No SLO definition files, error budget tracking, or availability targets found in the repository. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The CLI collects rich business metrics through its telemetry system: usage events (command execution, service unique ID), analysis events (OS, architecture, CI/CD detection, runner type, command, resolvers used, errors). The `instanceUsageTrackingClient` and `platformEventClient` in `packages/util/src/telemetry/` publish events to the Serverless Dashboard platform. Machine ID tracking enables unique installation counting. The `sf-core/src/lib/router.js` `createAnalysisEvent` includes project type, config file name, resolver usage, and error details. |
| **Gap** | Business metrics exist but are sent to the Serverless Dashboard platform — not to CloudWatch or a self-owned observability stack. There is no infrastructure-level metrics visibility within this repo. |
| **Recommendation** | The existing telemetry system is comprehensive for a CLI tool. Consider adding deployment duration tracking, CloudFormation operation timing, and SDK call latency as business metrics. Publish key metrics to CloudWatch for the release infrastructure to complement Dashboard analytics. |
| **Evidence** | `packages/sf-core/src/lib/router.js` (createUsageEvent, createAnalysisEvent with detailed attributes), `packages/util/src/telemetry/` (event publishing), `packages/util/src/instanceUsageTracking/` (usage tracking) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudWatch anomaly detection, alerting, or monitoring configuration found in the repository. The release infrastructure (S3/CloudFront) has no visible alarms for error rates, latency, or availability. |
| **Gap** | No alerting or anomaly detection for the release infrastructure. If the install script becomes unavailable or release artifacts are corrupted, there is no automated detection. |
| **Recommendation** | Add CloudWatch alarms for the release infrastructure: (1) CloudFront 5xx error rate alarm, (2) S3 4xx/5xx error rate alarms, (3) Install script download success rate. Define these in the IaC recommended in INF-Q10. Consider adding anomaly detection on CLI telemetry data to detect unusual error rate spikes after releases. |
| **Evidence** | No CloudWatch alarm definitions, anomaly detection configs, or alerting integration (PagerDuty, OpsGenie) found in repository. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The release pipeline implements a multi-stage deployment strategy: (1) **Test matrix** across Ubuntu, ARM Linux, and Windows, (2) **Canary release** — uploads tarballs to the canary distribution S3 bucket with CloudFront invalidation, (3) **Stable release** — uploads to the stable distribution S3 bucket (only if a new version is detected), (4) **NPM publish** — publishes the `@serverlessinc/sf-core` npm installer package. This is effectively a canary deployment pattern for a CLI tool. |
| **Gap** | No automated rollback if the canary release causes issues. The stable release is gated on a version bump but not on canary validation (e.g., no automated smoke tests against the canary). The canary → stable promotion is automatic (job dependency), not based on canary success metrics. |
| **Recommendation** | Add a canary validation step between the canary release and stable release jobs. This could be an automated smoke test that installs from the canary channel and runs basic CLI commands. Add automated rollback capability for the canary release (revert S3 objects if validation fails). |
| **Evidence** | `.github/workflows/release-framework.yml` (test-matrix → release-canary → release-stable → release-npm job chain), `.github/workflows/release-binary-installer.yml` (test → build → S3 upload → CloudFront invalidation) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Extensive integration test suites exist: `packages/sf-core/tests/integration/` covers simple-nodejs, simple-python, simple-dashboard, simple-compose, resolvers, sam, esbuild, domains, state, deployment-bucket, license-key, and local-plugin scenarios. These tests run in CI with AWS credentials and deploy actual CloudFormation stacks. The CI pipeline runs integration tests in both PR checks and release workflows. Engine has unit tests in `packages/engine/test/`. MCP has unit and e2e tests in `packages/mcp/tests/`. Python requirements tests run separately in `ci-python.yml`. |
| **Gap** | Some test suites appear to be run only on specific triggers (domains tests run separately with `--runInBand`, Python tests have a dedicated CI workflow). Not all integration test suites are run in every CI pipeline execution. |
| **Recommendation** | Ensure all critical integration test suites run in the release pipeline before canary deployment. Consider creating a test matrix that covers the full integration test surface (nodejs, python, sam, compose, resolvers) in both CI and release workflows. |
| **Evidence** | `packages/sf-core/tests/integration/` (12 integration test directories), `packages/sf-core/package.json` (13 test script variants), `.github/workflows/ci-framework.yml` (runs integration tests with AWS credentials), `.github/workflows/release-framework.yml` (cross-platform test matrix before release), `TESTING.md` (test setup documentation) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The `SECURITY.md` file documents the vulnerability reporting process (GitHub security advisories). The `sls support` CLI command generates incident reports with contextual information. However, there are no automated runbooks, Systems Manager documents, or Lambda-based remediation for the release infrastructure. Incident response is manual — report via GitHub security advisories, triage within 3 business days. |
| **Gap** | No automated incident response for release infrastructure failures. Runbook exists as documentation (SECURITY.md, RELEASE_PROCESS.md) but is not machine-readable or automated. |
| **Recommendation** | Create automated runbooks for common incidents: (1) Failed release rollback procedure, (2) S3/CloudFront outage response, (3) Compromised release artifact detection and response. Consider GitHub Actions workflows that can be manually triggered for incident response (e.g., rollback a release). |
| **Evidence** | `SECURITY.md` (vulnerability reporting process), `RELEASE_PROCESS.md` (release process documentation), `README.md` (sls support command for incident reports) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Each package has its own structured logging namespace (`log.get('core')`, `log.get('engine')`, `log.get('core:router')`), providing package-level log ownership. The observability module (`packages/sf-core/src/lib/observability/`) supports Axiom and Dashboard providers. However, there are no per-service dashboards, no named alarm owners, and no SLO definitions with team attribution. The telemetry system sends data to the Serverless Dashboard platform but there is no evidence of monitoring ownership within this repository. |
| **Gap** | No per-service dashboards or alarm ownership defined. Observability is ad hoc — structured logging exists but monitoring and alerting are not configured. |
| **Recommendation** | Define observability ownership for the release infrastructure: assign alarm owners for CloudFront/S3 metrics, create dashboards for release pipeline success rates, and establish on-call rotation for release-related incidents. |
| **Evidence** | `packages/sf-core/src/lib/observability/index.js` (ObservabilityProvider enum: DISABLED, AXIOM, DASHBOARD), `packages/util/src/logger/index.js` (structured logging), `packages/sf-core/src/lib/router.js` (namespace-based logging: log.get('core:router')) |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging configuration found in the repository. The release infrastructure (S3 buckets, CloudFront distributions, IAM roles) is not defined in IaC, so there are no tag definitions. No `default_tags`, `tags` blocks, or tagging standards visible. |
| **Gap** | No tagging governance for any AWS resources. Without IaC (INF-Q10), there is no mechanism to enforce tags. |
| **Recommendation** | When defining the release infrastructure in IaC (per INF-Q10 recommendation), include consistent tags: `Project: serverless-framework`, `Team: framework-team`, `Environment: production`, `CostCenter: <value>`. Use `default_tags` in Terraform or `Tags` in CloudFormation to enforce consistency. |
| **Evidence** | No IaC files with tag definitions found. No tagging standards documentation found. |

---

## Learning Materials

### Move to Modern DevOps (Triggered)

- [Move to Modern DevOps Learning Plan](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `package.json` | APP-Q1, APP-Q2 | Root workspace configuration, npm workspaces definition |
| `packages/serverless/package.json` | INF-Q1, APP-Q1, APP-Q2, DATA-Q3 | Framework package dependencies (25+ @aws-sdk/* at 3.1015.0), Node.js engine requirement |
| `packages/sf-core/package.json` | APP-Q1, APP-Q2, APP-Q5, OPS-Q6, SEC-Q4 | CLI entry point, workspace dependencies, test scripts, jwt-decode |
| `packages/engine/package.json` | APP-Q2, DATA-Q2 | Engine dependencies, workspace references |
| `packages/mcp/package.json` | APP-Q5, SEC-Q3 | MCP server dependencies, @modelcontextprotocol/sdk |
| `packages/util/package.json` | DATA-Q2 | Utility dependencies, aws-sdk-v3-proxy |
| `packages/standards/package.json` | APP-Q2 | ESLint standards package |
| `binary-installer/go.mod` | APP-Q1, DATA-Q3 | Go 1.26.1 binary installer |
| `.github/workflows/ci-framework.yml` | INF-Q11, SEC-Q5, SEC-Q6, SEC-Q7, OPS-Q6 | CI pipeline: lint, test, integration tests |
| `.github/workflows/ci-engine.yml` | INF-Q11, SEC-Q7 | Engine CI pipeline |
| `.github/workflows/ci-binary-installer.yml` | INF-Q11 | Go CI pipeline |
| `.github/workflows/ci-python.yml` | INF-Q11, OPS-Q6 | Python CI pipeline |
| `.github/workflows/release-framework.yml` | INF-Q1, INF-Q2, INF-Q8, INF-Q10, INF-Q11, SEC-Q1, SEC-Q2, SEC-Q3, SEC-Q5, OPS-Q5 | Release pipeline: test → canary → stable → npm, OIDC auth, S3/CloudFront |
| `.github/workflows/release-binary-installer.yml` | INF-Q1, INF-Q8, INF-Q10, OPS-Q5 | Binary release: Go build, S3 upload, CloudFront |
| `.github/dependabot.yml` | APP-Q1, DATA-Q3, SEC-Q6, SEC-Q7 | 5 ecosystem configs, version pinning, Node.js 18 ignore rules |
| `packages/sf-core/src/index.js` | INF-Q3, INF-Q4, APP-Q3, APP-Q4 | CLI entry point, sequential execution flow |
| `packages/sf-core/src/lib/router.js` | APP-Q2, APP-Q3, APP-Q6, OPS-Q1, OPS-Q3, OPS-Q8 | Command routing, runner discovery, telemetry events |
| `packages/engine/src/index.js` | INF-Q3, INF-Q4, APP-Q4, DATA-Q1, DATA-Q2, DATA-Q4 | Engine class, state store pattern, deployment types |
| `packages/mcp/src/server.js` | INF-Q4, INF-Q6, APP-Q3, APP-Q5, SEC-Q3 | Express SSE server, no auth middleware |
| `packages/mcp/src/tools-definition.js` | APP-Q5, SEC-Q3 | MCP tool definitions with Zod schemas |
| `packages/util/src/telemetry/` | OPS-Q1, OPS-Q3 | Custom telemetry system |
| `packages/util/src/logger/` | OPS-Q1, OPS-Q8 | Structured logging system |
| `packages/sf-core/src/lib/observability/index.js` | OPS-Q8 | Observability provider enum |
| `packages/sf-core/tests/integration/` | OPS-Q6 | 12 integration test directories |
| `packages/engine/test/` | OPS-Q6 | Engine unit tests |
| `packages/mcp/tests/` | OPS-Q6 | MCP unit and e2e tests |
| `packages/serverless/lib/plugins/aws/bedrock-agentcore/index.js` | Move to AI pathway | Bedrock AgentCore plugin for user deployments |
| `SECURITY.md` | OPS-Q7 | Vulnerability reporting process |
| `TESTING.md` | OPS-Q6 | Test environment setup documentation |
| `AGENTS.md` | Quick Agent Wins | AI agent integration documentation |
| `README.md` | Quick Agent Wins, SEC-Q4 | Project documentation, AWS SSO support |
| `docs/` | Quick Agent Wins | Framework documentation directory |
