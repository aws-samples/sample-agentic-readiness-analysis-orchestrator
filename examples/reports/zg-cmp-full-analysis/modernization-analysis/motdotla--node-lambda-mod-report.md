# Modernization Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | node-lambda |
| **Date** | 2025-07-14 |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | javascript, serverless, cli |
| **Context** | Node.js CLI for deploying AWS Lambda functions. |
| **Overall Score** | 1.84 / 4.0 |

**Archetype Justification**: This is a CLI tool that does not cleanly map to runtime service archetypes. It has no persistent state of its own, no message queue consumers, and no synchronous API surface. However, it performs write operations to external AWS services (Lambda, S3, CloudWatch Events). Per the auto-detection decision logic, ambiguous signals default to `stateful-crud` — the most conservative archetype that applies the strictest rubric without false downgrades.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.18 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.33 / 4.0 | 🟠 Needs Work |
| Data Platform Modernization (DATA) | 2.50 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.86 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.33 / 4.0 | ❌ Not Present |
| **Overall** | **1.84 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC files found — all infrastructure is manually managed or undefined | Blocks reproducible deployments, disaster recovery, and environment consistency. Triggers Move to Modern DevOps pathway. |
| 2 | INF-Q1: Managed Compute | 1 | No compute infrastructure defined — CLI tool has no managed compute or deployment target | No containerization or serverless infrastructure for the tool itself. Triggers Move to Containers pathway. |
| 3 | INF-Q5: Network Security | 1 | No VPC, subnet, or security group configuration defined for the tool's own infrastructure | No network segmentation or isolation for any infrastructure the tool provisions. |
| 4 | OPS-Q5: Deployment Strategy | 1 | No deployment strategy — npm publish is manual with no staged rollout | Direct-to-production releases with no canary, blue/green, or automated rollback. Supports Move to Modern DevOps pathway. |
| 5 | SEC-Q1: Audit Logging | 1 | No CloudTrail or audit logging configured | No audit trail for operations performed by the tool or its infrastructure. |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** INF-Q11 = 2 (≥ 2). CI/CD pipeline exists via GitHub Actions (`.github/workflows/workflow.yml`) with automated testing on push/PR.
- **What it enables:** An agent that triggers CI builds, checks test status across the Node.js 22.x/24.x matrix and Ubuntu/macOS/Windows platforms, manages npm release publishing, and automates version bumping in `package.json`.
- **Additional steps:** Add an npm publish workflow stage to GitHub Actions so the agent has a deployment surface to invoke. Configure GitHub Actions API access tokens.
- **Effort:** Medium

### RAG-Based Knowledge Agent

- **Prerequisite:** Extensive documentation exists — `README.md` (323 lines, comprehensive usage guide with all 4 commands and 40+ CLI options documented), `CHANGELOG.md` (491 lines covering all releases), and `lib/*.example` files providing configuration templates.
- **What it enables:** A RAG-based knowledge agent that indexes the README, CHANGELOG, and example configurations to answer developer questions about CLI usage, configuration options, deployment parameters, and version history without reading source code.
- **Additional steps:** Index `README.md`, `CHANGELOG.md`, and example files into a vector store. Consider generating an OpenAPI-style specification of CLI commands and options for structured tool discovery.
- **Effort:** Low

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 (≥ 3) — application has well-defined module boundaries; primary trigger not met. |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1 = 1 (< 3), no container definitions found. Note: CLI tool — containerization applies to packaging/distribution, not runtime compute. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (≥ 3) — no stored procedures or proprietary SQL. No commercial database engines detected. |
| 4 | Move to Managed Databases | Triggered | Low | Low | INF-Q2 = 1 (< 3), DATA-Q3 = 1 (< 3). Note: No databases exist in this CLI tool — score reflects absence, not self-managed databases. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | Contextual guard: no data processing workloads, streaming, ETL, or analytics artifacts found. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (< 3), INF-Q11 = 2 (< 3), OPS-Q5 = 1 (< 3). No IaC, partial CI/CD, no deployment strategy. |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in context ("Node.js CLI for deploying AWS Lambda functions."). |

---

<!-- PATHWAY_DETAILS -->

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model:**
This is a Node.js CLI tool distributed via npm (`npm install -g node-lambda`). There is no compute infrastructure defined — no EC2 instances, no ECS tasks, no Lambda functions for the tool itself. The tool runs on developer machines or CI environments. INF-Q1 scored 1 because no managed compute is defined.

**Container Readiness Indicators:**
- The tool has clear dependency management via `package.json` with pinned dependencies
- Node.js >= 22.0.0 runtime requirement is well-defined
- The tool already supports Docker for dependency installation (`--dockerImage` flag in deploy/package commands)
- No native binary dependencies that would complicate containerization
- Environment variables are externalized via `.env` and `deploy.env` files

**Recommendation:**
Since this is a CLI tool (not a running service), containerization is most relevant for:
1. **Reproducible build environments** — A Docker image with Node.js and the tool pre-installed ensures consistent Lambda packaging across developer machines and CI environments. The tool already has `--dockerImage` support for npm install, which could be extended to the full package/deploy workflow.
2. **CI/CD pipeline execution** — Container images provide hermetic build environments for GitHub Actions workflows. Consider using EKS-based CI runners or AWS CodeBuild with custom Docker images (per `prefer: ["eks"]`).
3. **Distribution** — Publishing a Docker image alongside the npm package provides an alternative distribution channel.

**Representative AWS Services:** ECR (container image registry), EKS (per preference for CI runner infrastructure), CodeBuild (container-based CI)

**Migration Approach:** Lift-and-containerize — create a Dockerfile with Node.js 22+ base, install node-lambda, and publish to ECR.

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** Low
**Estimated Effort:** Low

**Current Database Topology:**
No databases exist in this repository. The INF-Q2 score of 1 reflects the complete absence of database infrastructure, not the presence of self-managed databases. The tool interacts with AWS services (Lambda, S3, CloudWatch Events, CloudWatch Logs) but does not use or manage any database resources.

**Recommendation:**
This pathway is technically triggered by the scoring (INF-Q2 < 3) but is **not practically applicable** to this CLI tool. The tool has no data persistence requirements that would benefit from a managed database. If future features require state management (e.g., deployment history, rollback tracking, or multi-user coordination), consider:
- **DynamoDB** (per `prefer: ["dynamodb"]`) for deployment state tracking and audit logs
- **Aurora** (per `prefer: ["aurora"]`) if relational queries are needed

No immediate action is required for this pathway.

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 1):**
No Infrastructure as Code files found. No `.tf`, CloudFormation, CDK, Helm, or Kustomize files exist in the repository. Any infrastructure provisioned for testing, CI, or distribution is managed manually or externally.

**Current CI/CD State (INF-Q11 = 2):**
- ✅ GitHub Actions workflow (`.github/workflows/workflow.yml`) automates testing on push/PR
- ✅ Multi-platform testing: Ubuntu, macOS, Windows
- ✅ Multi-version testing: Node.js 22.x, 24.x
- ✅ CodeQL SAST scanning on push to master, PRs, and weekly schedule
- ✅ Dependabot configured for npm and GitHub Actions dependency updates
- ❌ No automated deployment/publish stage — npm publish is manual
- ❌ No automated version bumping or changelog generation
- ❌ No deployment pipeline for releasing to npm registry

**Deployment Strategy Gaps (OPS-Q5 = 1):**
No deployment strategy exists. npm packages are published manually with no staged rollout, canary testing, or automated rollback.

**Testing Gaps (OPS-Q6 = 3):**
Testing is relatively strong — mocha/chai test suite with aws-sdk-mock for unit tests and CLI spawn tests for integration testing. This is a solid foundation to build upon.

**Recommended DevOps Improvements:**

1. **Add automated npm publish pipeline** (High Priority)
   - Add a GitHub Actions workflow triggered on version tags (e.g., `v*`) that runs `npm publish`
   - Use GitHub Secrets for NPM_TOKEN management
   - Include pre-publish validation (lint, test, build)

2. **Add IaC for CI/CD infrastructure** (Medium Priority)
   - Define GitHub Actions self-hosted runner infrastructure in CDK or Terraform if needed
   - Consider AWS CodePipeline/CodeBuild for additional CI/CD capabilities (avoids self-managed infrastructure per preferences)

3. **Implement semantic versioning automation** (Medium Priority)
   - Use conventional commits and automated version bumping
   - Auto-generate CHANGELOG entries from commit history

4. **Add canary/staged npm publishing** (Lower Priority)
   - Publish to npm with `--tag next` for pre-release validation
   - Promote to `latest` tag after validation period

**Representative AWS Services:** CodeBuild (CI/CD), CodePipeline (orchestration), Systems Manager Parameter Store (secrets for npm tokens)

**Links to AWS DevOps Prescriptive Guidance:**
- [AWS DevOps Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/strategy-cicd-litmus/introduction.html)

---

<!-- DETAILED_FINDINGS -->

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute infrastructure is defined in the repository. There are no Terraform resources (`aws_ecs_*`, `aws_eks_*`, `aws_lambda_*`, `aws_instance`), no CloudFormation templates, no CDK stacks, and no Dockerfiles. This is a Node.js CLI tool distributed via npm that runs on developer machines — it does not define or manage its own compute workloads. |
| **Gap** | No managed compute infrastructure. The tool has no containerized or serverless deployment model for itself. |
| **Recommendation** | Consider creating a Docker image for reproducible build environments and CI/CD execution. Publish to ECR for use in EKS-based CI runners (per preference for EKS). This is lower priority for a CLI tool than for a running service. |
| **Evidence** | `package.json` (npm distribution), `bin/node-lambda` (CLI entry point). No IaC files found in repository root or any subdirectory. |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database resources found anywhere in the repository. No database connection strings, no database drivers in `package.json` dependencies, no IaC defining RDS, DynamoDB, DocumentDB, or any other database service. The tool does not use or manage databases. |
| **Gap** | Complete absence of database infrastructure. Score reflects absence rather than self-managed databases. |
| **Recommendation** | No action needed unless future features require state persistence. If deployment history tracking is needed, consider DynamoDB (per preference) for a lightweight, managed solution. |
| **Evidence** | `package.json` (no database drivers in dependencies), no `.tf`/`.yaml`/`.json` IaC files with database resources. |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The deployment workflow in `lib/main.js` follows a sequential pattern: `_archive()` → `_deployToRegion()` → `_uploadExisting()`/`_uploadNew()` → `_updateEventSources()` → `_updateScheduleEvents()` → `_updateS3Events()` → `_setLogsRetentionPolicy()`. These are implemented as Promise chains with basic error handling. The `_uploadExisting()` method includes a polling loop (up to 10 iterations with 3-second delays) waiting for `LastUpdateStatus === 'Successful'`. Multi-region deployment uses `Promise.all(regions.map(...))` for parallel execution. No dedicated workflow orchestration service (Step Functions, Temporal) is used. |
| **Gap** | Deployment workflows are hardcoded as Promise chains with basic structure but no dedicated orchestration service. Error handling and retry logic are minimal — the AWS SDK's built-in retry handles transient failures, but there's no workflow-level compensation or rollback. |
| **Recommendation** | For a CLI tool, the current approach is reasonable. If deployment complexity grows (e.g., multi-service orchestration, rollback procedures), consider AWS Step Functions for managing deployment workflows with built-in retry, error handling, and state tracking. Consider EventBridge (per preference) for event-driven deployment notifications. |
| **Evidence** | `lib/main.js` — `deploy()`, `_deployToRegion()`, `_uploadExisting()`, `_uploadNew()` methods; Promise chain patterns throughout. |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No messaging or streaming infrastructure is used by the tool itself. No SQS, SNS, EventBridge, MSK, or Kinesis resources are defined. The tool *manages* event source mappings for Lambda functions (SQS, Kinesis, DynamoDB Streams via `_updateEventSources()` in `lib/main.js`) and schedule events (CloudWatch Events via `lib/schedule_events.js`), but it does not consume or produce messages for its own operations. |
| **Gap** | No async messaging for the tool's own workflows. Multi-region deployments execute in parallel via `Promise.all` but have no event-driven coordination or notification mechanism. |
| **Recommendation** | Consider adding EventBridge (per preference) for deployment event notifications — publish events on deployment start, success, and failure. This would enable integration with monitoring systems and multi-tool workflows without tight coupling. |
| **Evidence** | `lib/main.js` — `_updateEventSources()` manages Lambda event sources; `lib/schedule_events.js` — manages CloudWatch Events rules; `lib/s3_events.js` — manages S3 event notifications. No messaging SDK usage for the tool's own operations. |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, or security group configuration is defined in the repository. The tool supports VPC configuration for deployed Lambda functions via `--vpcSubnets` and `--vpcSecurityGroups` CLI flags (see `bin/node-lambda` and `_params()` in `lib/main.js`), but it does not define network infrastructure for itself. |
| **Gap** | No network security configuration. The tool itself runs locally and connects to AWS APIs over the public internet. No VPC endpoints or PrivateLink configuration. |
| **Recommendation** | If the tool is used in CI/CD environments, consider deploying CI runners in a VPC with VPC endpoints for AWS services to avoid public internet exposure. Use API Gateway (per preference) with VPC integration for any future API surface. |
| **Evidence** | `bin/node-lambda` — `AWS_VPC_SUBNETS`, `AWS_VPC_SECURITY_GROUPS` env vars; `lib/main.js` — `_params()` VpcConfig section. No IaC defining VPC resources. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or any API entry point is defined. This is a CLI tool — it does not expose an HTTP API. Users interact with it via command-line commands (`setup`, `run`, `package`, `deploy`). |
| **Gap** | No API entry point. Not applicable for a CLI tool's current architecture. |
| **Recommendation** | If the tool evolves to include a web interface or API for programmatic access, use API Gateway (per preference) with authentication and throttling. For the current CLI architecture, no action needed. |
| **Evidence** | `bin/node-lambda` — CLI commands defined with `commander`; no HTTP server, Express, or similar framework in dependencies or source code. |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration. No compute resources, databases, or managed services are defined that would require scaling. The tool runs as a CLI process on the user's machine. |
| **Gap** | No auto-scaling — not applicable for a locally-run CLI tool. |
| **Recommendation** | No action needed for the current CLI architecture. If CI/CD infrastructure is formalized (e.g., CodeBuild projects, EKS runners), configure auto-scaling for those resources. |
| **Evidence** | No IaC files. No `aws_autoscaling_*`, `aws_appautoscaling_*`, or scaling policy resources. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration. The tool creates S3 buckets for deployment packages (`lib/s3_deploy.js`) but does not configure backups, versioning, or lifecycle policies on those buckets. No data stores owned by the tool require backup. |
| **Gap** | S3 deployment buckets lack versioning and lifecycle policies. No backup strategy for deployment artifacts. |
| **Recommendation** | Enable S3 versioning on deployment package buckets to allow rollback to previous Lambda deployment packages. Add lifecycle policies to expire old deployment artifacts and reduce storage costs. |
| **Evidence** | `lib/s3_deploy.js` — `_createBucket()` creates buckets without versioning configuration; `_putObject()` uploads deployment packages without lifecycle rules. |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ configuration. No deployed infrastructure exists for the tool itself. The tool supports multi-region Lambda deployment via comma-separated `--region` flag (e.g., `us-east-1,us-west-2,eu-west-1`) with `Promise.all` for parallel execution across regions, but this is for the user's Lambda functions, not for the tool's own infrastructure. |
| **Gap** | No high availability configuration for the tool itself. Not directly applicable for a CLI tool. |
| **Recommendation** | No action needed for the CLI tool itself. The multi-region deployment capability (`deploy()` in `lib/main.js`) already provides fault isolation for deployed Lambda functions across regions. |
| **Evidence** | `lib/main.js` — `deploy()` splits `program.region` by comma and deploys in parallel; `bin/node-lambda` — `AWS_REGION` default is `us-east-1,us-west-2,eu-west-1`. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC files found in the repository. No Terraform (`.tf`), CloudFormation (`.yaml`/`.json`), CDK (`cdk.json`), Helm (`Chart.yaml`), or Kustomize (`kustomization.yaml`) files exist. All infrastructure — including S3 buckets created during deployment, CloudWatch Events rules, and Lambda functions — is provisioned imperatively through the tool's JavaScript code via AWS SDK calls. |
| **Gap** | 0% IaC coverage. All infrastructure is created imperatively via AWS SDK calls in application code. Resources created by the tool (S3 buckets, CloudWatch Events rules, Lambda permissions) cannot be tracked, audited, or reproduced declaratively. |
| **Recommendation** | Consider providing CDK or CloudFormation templates as an alternative deployment mode alongside the imperative SDK-based approach. This would enable users to manage their Lambda infrastructure declaratively with drift detection, change sets, and rollback capabilities. For the tool's own CI/CD infrastructure, adopt Terraform or CDK. |
| **Evidence** | Repository root and all subdirectories scanned — no IaC files found. Infrastructure created imperatively in `lib/main.js`, `lib/s3_deploy.js`, `lib/schedule_events.js`, `lib/s3_events.js`, `lib/cloudwatch_logs.js`. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GitHub Actions workflow (`.github/workflows/workflow.yml`) automates linting and testing: runs `npm ci` and `npm test` (which executes `standard` linting and `mocha` unit tests) on push and pull request events. Tests run across Node.js 22.x and 24.x on Ubuntu, with Node.js 24.x on macOS and Windows. CodeQL SAST scanning (`.github/workflows/codeql-analysis.yml`) runs on push to master, PRs to master, and weekly on a cron schedule. Dependabot (`.github/dependabot.yml`) monitors npm and GitHub Actions dependencies monthly. **No automated deployment stage exists** — npm publish is manual. |
| **Gap** | Build and test are automated, but deployment (npm publish) is entirely manual. No automated version bumping, changelog generation, or release workflow. |
| **Recommendation** | Add a GitHub Actions release workflow triggered on version tags or GitHub Releases that runs `npm publish` with an NPM_TOKEN stored in GitHub Secrets. Include pre-publish validation (lint + full test suite). Consider using `semantic-release` or `changesets` for automated versioning. |
| **Evidence** | `.github/workflows/workflow.yml`, `.github/workflows/codeql-analysis.yml`, `.github/dependabot.yml`. No publish/deploy workflow found. |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | JavaScript (Node.js) is the sole language used. All source files are `.js` (CommonJS) with one `.mjs` (ES Module) file. The `package.json` specifies `"engines": { "node": ">= 22.0.0" }`, requiring a modern, actively maintained Node.js LTS version. JavaScript/Node.js has first-class AWS SDK coverage (`aws-sdk` v2 is a direct dependency), broad cloud-native tooling, and a mature framework ecosystem. |
| **Gap** | None. JavaScript/Node.js is a tier-1 language for AWS cloud-native development. |
| **Recommendation** | Consider migrating from `aws-sdk` v2 to `@aws-sdk/client-*` v3 (modular SDK) for reduced bundle sizes, improved tree-shaking, and continued AWS support. AWS SDK v2 entered maintenance mode. Also consider TypeScript adoption for improved type safety and developer experience. |
| **Evidence** | `package.json` — `"engines": { "node": ">= 22.0.0" }`, `"aws-sdk": "^2.1377.0"`; `.js` files throughout `lib/` and `bin/`. |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Single deployable unit — one npm package (`node-lambda`) with a well-organized modular structure. The application has clear module boundaries: `lib/main.js` (core Lambda class with deploy/package/run/setup commands), `lib/aws.js` (centralized AWS SDK configuration), `lib/s3_deploy.js` (S3 deployment package management), `lib/s3_events.js` (S3 event source configuration), `lib/schedule_events.js` (CloudWatch Events schedule management), `lib/cloudwatch_logs.js` (log retention management). Each module has a single responsibility and a clear interface. No circular dependencies detected — dependency flow is unidirectional: `main.js` → `{s3_deploy, s3_events, schedule_events, cloudwatch_logs}` → `aws.js`. |
| **Gap** | Minor: All modules share the `aws.sdk` singleton via `lib/aws.js`, creating coupling through the shared AWS SDK instance. This is acceptable for a CLI tool but would be a concern if decomposing into independent services. |
| **Recommendation** | The current modular monolith architecture is appropriate for a CLI tool. No decomposition needed. If the tool grows significantly, consider extracting the deployment engine into a library package separate from the CLI interface. |
| **Evidence** | `lib/main.js` — Lambda class imports `s3_deploy`, `s3_events`, `schedule_events`, `cloudwatch_logs`; `lib/aws.js` — shared SDK configuration; `bin/node-lambda` — CLI entry point using `commander`. |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Using `stateful-crud` archetype rubric. The tool communicates with AWS services via the AWS SDK using Promise-based async calls. All AWS API interactions are asynchronous (e.g., `lambda.createFunction()`, `s3.putObject()`, `cloudwatchevents.putRule()`). Multi-region deployment uses `Promise.all()` for parallel execution. However, the overall flow is sequential within a single region — each step must complete before the next begins (upload → configure → set event sources). There is no inter-service communication between components. The Promise chains in `_deployToRegion()` follow a sequential async pattern that is functionally synchronous in terms of workflow. |
| **Gap** | Primarily sequential execution within a region. No event-driven communication patterns between components. The Promise chains could be parallelized where dependencies allow (e.g., event source updates and tag updates could run concurrently — some parallelism already exists via `Promise.all` in `_deployToRegion()`). |
| **Recommendation** | The sequential pattern is largely correct for a deployment CLI. Consider parallelizing independent operations within `_deployToRegion()` more aggressively where there are no data dependencies. For future evolution, consider EventBridge (per preference) for decoupled deployment event notifications. |
| **Evidence** | `lib/main.js` — `deploy()` uses `Promise.all(regions.map(...))` for multi-region; `_deployToRegion()` uses sequential `await` calls; `_uploadExisting()` has polling loop with `setTimeout`. |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Using `stateful-crud` archetype rubric. The deployment process can be long-running: zipping large codebases (the tool warns "This might take up to 30 seconds"), uploading packages to S3 and Lambda, and waiting for Lambda configuration updates. `DEPLOY_TIMEOUT` defaults to 120000ms (2 minutes). The `_uploadExisting()` method includes a polling loop (up to 10 iterations × 3-second delay = 30 seconds max) waiting for `Configuration.LastUpdateStatus === 'Successful'`. However, there is no formal async job pattern — the CLI user must wait for the process to complete with no progress indication beyond console logs. |
| **Gap** | Long-running operations block the CLI process with no progress bars, no status API, and limited timeout handling. The `_uploadExisting()` polling loop has a fixed 10-iteration limit with no configurable backoff. |
| **Recommendation** | Add progress indicators (progress bars for zip/upload operations). Implement configurable backoff and timeout for the `LastUpdateStatus` polling loop. For very large deployments, consider an async deployment mode that submits the job and returns a deployment ID for status polling. |
| **Evidence** | `lib/main.js` — `_zip()` ("This might take up to 30 seconds"), `_uploadExisting()` polling loop, `DEPLOY_TIMEOUT` in `bin/node-lambda`; `lib/s3_deploy.js` — `putPackage()` sequential bucket creation and upload. |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API surface is exposed — this is a CLI tool. The npm package uses semantic versioning (`"version": "1.3.0"` in `package.json`) for release management. The CLI commands (`setup`, `run`, `package`, `deploy`) are versioned implicitly through the npm package version. No programmatic API is exposed that would require URL-path or header-based versioning. The `index.js` exports are minimal (a sample Lambda handler for testing, not an API). |
| **Gap** | No API versioning strategy. The programmatic interface exposed via `require('node-lambda')` (which returns the Lambda class singleton from `lib/main.js`) has no versioning contract. Breaking changes to the Lambda class API could affect programmatic consumers. |
| **Recommendation** | Document the programmatic API contract (the Lambda class methods exposed via `index.js`/`lib/main.js`). Follow semver strictly for the npm package. Consider exposing a versioned programmatic API if the library interface is intended for programmatic use (e.g., `const { deploy } = require('node-lambda/v2')`). |
| **Evidence** | `package.json` — `"version": "1.3.0"`, `"main": "lib/main.js"`; `index.js` — sample handler, not a versioned API; `bin/node-lambda` — CLI commands via `commander`. |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | AWS service endpoints are resolved automatically by the AWS SDK based on the configured region. The tool supports an `AWS_ENDPOINT` environment variable (used in `lib/aws.js` via `aws.config.endpoint = config.endpoint`) for pointing to alternative endpoints such as LocalStack for local testing. Service client instances are created per-module using the shared AWS SDK configuration from `lib/aws.js`. No hard-coded AWS service URLs exist in the source code — all endpoint resolution is delegated to the AWS SDK. |
| **Gap** | Endpoint configuration is via environment variables with no dynamic discovery mechanism. The `AWS_ENDPOINT` override is a static configuration, not a service registry. This is typical and appropriate for a CLI tool consuming AWS APIs. |
| **Recommendation** | The current approach is appropriate for a CLI tool. AWS SDK handles endpoint resolution correctly. No changes needed unless the tool needs to discover non-AWS services. |
| **Evidence** | `lib/aws.js` — `aws.config.endpoint = config.endpoint`; `bin/node-lambda` — `AWS_ENDPOINT` env var; `lib/s3_deploy.js`, `lib/s3_events.js`, `lib/schedule_events.js`, `lib/cloudwatch_logs.js` — service clients created with region parameter. |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The tool uses Amazon S3 for storing Lambda deployment packages. `lib/s3_deploy.js` creates S3 buckets (named `{FunctionName}-{region}-{md5hash}`) and uploads zip files via `putObject()`. S3 bucket names can also be configured via environment variables (`S3_{REGION}_BUCKET`). This is managed object storage usage, but strictly for deployment artifact storage — not for unstructured data with parsing or analytics capabilities. No Textract, Tika, or document parsing libraries are present. |
| **Gap** | S3 is used only for deployment artifact storage. No parsing pipeline, no document processing capabilities. No S3 lifecycle policies or versioning configured on deployment buckets. |
| **Recommendation** | Enable S3 versioning on deployment buckets to support deployment rollback. Add lifecycle policies to transition old deployment packages to S3 Glacier or expire them after a retention period. No parsing pipeline is needed for this use case. |
| **Evidence** | `lib/s3_deploy.js` — `_createBucket()`, `_putObject()`, `_bucketName()`, `_s3Key()`; `S3_LOCATION_POSSIBLE_VALUES` array for region-specific bucket configuration. |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | `lib/aws.js` serves as the centralized AWS SDK configuration module. It exports the `aws` SDK object and an `updateConfig()` function that handles credentials (profile-based via `SharedIniFileCredentials` or access key/secret key), session tokens, deploy timeouts, proxy configuration, and custom endpoints. Each service module (`s3_deploy.js`, `s3_events.js`, `schedule_events.js`, `cloudwatch_logs.js`) creates its own service client instances using the shared `aws.sdk` object, ensuring consistent configuration. The pattern is: `new aws.S3({ region, apiVersion: '...' })`. |
| **Gap** | Minor: Each module creates its own service client instances independently. There is no centralized service client factory or connection pool. This is appropriate for a CLI tool but could lead to inconsistencies if client configuration diverges. |
| **Recommendation** | The current pattern is clean and appropriate. For future enhancement, consider a centralized service client factory in `lib/aws.js` that returns pre-configured clients (e.g., `aws.getLambdaClient(region)`) to ensure consistent API version and configuration across modules. |
| **Evidence** | `lib/aws.js` — `module.exports = { sdk: aws, updateConfig() }`; `lib/s3_deploy.js` — `this.s3 = new aws.S3(...)`, `lib/s3_events.js` — `this.lambda = new aws.Lambda(...)`, `this.s3 = new aws.S3(...)`. |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database engines are defined in the repository. No RDS instances, DynamoDB tables, DocumentDB clusters, or any other database resources exist. No database connection strings or driver dependencies are present in `package.json`. The tool does not use databases. |
| **Gap** | No database version management — not applicable to this CLI tool. Score of 1 reflects the complete absence of database infrastructure rather than unpinned or EOL database versions. |
| **Recommendation** | No action needed. If databases are introduced in the future, pin engine versions explicitly in IaC and document an upgrade procedure. Prefer Aurora (per preference) or DynamoDB (per preference) for managed database services. |
| **Evidence** | `package.json` — no database driver dependencies; no IaC files defining database resources; no SQL migration files. |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, proprietary SQL, or any database-coupled business logic. All business logic resides in the application layer (JavaScript modules in `lib/`). The tool does not use databases at all — all data operations are AWS API calls via the AWS SDK. |
| **Gap** | None. No database-coupled logic exists. |
| **Recommendation** | Maintain the current approach of keeping all business logic in the application layer. |
| **Evidence** | All source files in `lib/` — business logic implemented in JavaScript with no SQL or database references. |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail configuration found. No IaC defines audit logging for AWS API calls made by the tool. The tool supports `AWS_TRACING_CONFIG` for enabling X-Ray tracing on deployed Lambda functions, but this is for the user's Lambda, not for auditing the tool's own operations. Console output (`console.log`) during deployment provides operational logging but is not a structured audit trail. |
| **Gap** | No audit logging for operations performed by the tool. Deployment actions (create/update Lambda functions, create S3 buckets, set event source mappings) are not audited. |
| **Recommendation** | Add structured logging with timestamps and operation details for all AWS API calls made during deployment. Consider publishing deployment audit events to CloudWatch Logs or EventBridge (per preference) for centralized audit trail. |
| **Evidence** | `bin/node-lambda` — `AWS_TRACING_CONFIG` env var; `lib/main.js` — `console.log` output throughout deployment flow; no CloudTrail or structured logging configuration. |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No KMS encryption configuration is defined for the tool's own resources. The tool supports `AWS_KMS_KEY_ARN` as a CLI parameter (passed to Lambda function configuration as `KMSKeyArn`), but this is for the user's Lambda function encryption, not for the tool's resources. S3 deployment buckets created by `lib/s3_deploy.js` do not have server-side encryption configured — `_createBucket()` and `_putObject()` do not include encryption parameters. |
| **Gap** | S3 deployment buckets are created without server-side encryption. Deployment packages (which may contain application source code and secrets from `deploy.env`) are stored unencrypted in S3. |
| **Recommendation** | Add server-side encryption (SSE-S3 or SSE-KMS) to S3 deployment buckets. Modify `_putObject()` in `lib/s3_deploy.js` to include `ServerSideEncryption: 'aws:kms'` or `ServerSideEncryption: 'AES256'`. Consider using customer-managed KMS keys for sensitive deployment packages. |
| **Evidence** | `lib/s3_deploy.js` — `_createBucket()` and `_putObject()` with no encryption parameters; `bin/node-lambda` — `AWS_KMS_KEY_ARN` parameter for Lambda function encryption only. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The tool authenticates to AWS using static credentials: `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` passed as environment variables or CLI flags (`--accessKey`, `--secretKey`). It also supports AWS profile-based authentication via `AWS_PROFILE` (using `SharedIniFileCredentials` in `lib/aws.js`) and session tokens via `AWS_SESSION_TOKEN`. There is no OAuth2/JWT-based authentication. No API surface is exposed that would require per-request auth. |
| **Gap** | Authentication relies on static AWS credentials passed via CLI flags or environment variables. No support for AWS SSO, identity center, or modern credential providers (e.g., `credential_process`, IAM Identity Center). |
| **Recommendation** | Add support for AWS credential provider chain via AWS SDK v3, which natively supports SSO, IAM Identity Center, and container credential providers. Deprecate direct `--accessKey`/`--secretKey` flags in favor of profile-based auth and environment credential chain. |
| **Evidence** | `lib/aws.js` — `aws.SharedIniFileCredentials({ profile: config.profile })`, `awsSecurity.accessKeyId = config.accessKey`; `bin/node-lambda` — `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_PROFILE`, `AWS_SESSION_TOKEN` env vars. |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The tool integrates with AWS IAM through the AWS SDK. It supports profile-based credentials (`SharedIniFileCredentials` in `lib/aws.js`) which can reference IAM roles and federated credentials configured in `~/.aws/config`. However, there is no direct integration with a centralized IdP (Cognito, Okta, Ping). The IAM integration is through the standard AWS credential chain, which can be configured externally to use SSO or federated identities. |
| **Gap** | No direct SSO or centralized IdP integration. The tool relies on AWS credential files and environment variables. Users must configure SSO externally via AWS CLI profiles. |
| **Recommendation** | Migrate to AWS SDK v3 which has built-in support for AWS IAM Identity Center (SSO) credential resolution. This would allow `node-lambda` to natively support `aws sso login` flows without requiring users to manually configure credential profiles. |
| **Evidence** | `lib/aws.js` — `aws.SharedIniFileCredentials`; `bin/node-lambda` — `AWS_PROFILE` env var. No Cognito, OIDC, or SAML configuration. |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Secrets are managed via environment files: `.env` (for CLI configuration including AWS credentials) and `deploy.env` (for Lambda function environment variables including secrets like `SECRET_VARIABLE=mysecretval`). The `.gitignore` correctly excludes `.env`, `deploy.env`, and `event_sources.json` from version control. The `.env.example` file contains placeholder credentials (`AWS_ACCESS_KEY_ID=your_key`, `AWS_SECRET_ACCESS_KEY=your_secret`). No integration with AWS Secrets Manager, HashiCorp Vault, or any dedicated secrets management service. No secret rotation mechanism. |
| **Gap** | Secrets stored in flat files on disk. While excluded from git, the `deploy.env` file containing Lambda environment secrets is read as plain text and passed directly to Lambda's `Environment.Variables`. No encryption, no rotation, no audit trail for secret access. |
| **Recommendation** | Add an option to resolve Lambda environment variables from AWS Secrets Manager instead of `deploy.env` files. Modify `_params()` in `lib/main.js` to support a `--secretsManagerArn` flag that fetches secrets at deploy time. For the tool's own AWS credentials, promote profile-based auth over direct access key/secret key patterns. |
| **Evidence** | `lib/.env.example` — `AWS_ACCESS_KEY_ID=your_key`, `AWS_SECRET_ACCESS_KEY=your_secret`; `lib/deploy.env.example` — `SECRET_VARIABLE=mysecretval`; `.gitignore` — excludes `.env`, `deploy.env`; `lib/main.js` — `_params()` reads `configFile` and passes to `params.Environment.Variables`. |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No compute resources to harden (CLI tool runs locally). Dependabot is configured (`.github/dependabot.yml`) to check npm and GitHub Actions dependencies monthly for known vulnerabilities. No SSM Patch Manager, AWS Inspector, or Snyk integration. No hardened base images (no containers). The `mocha` dependency has pinned overrides for `diff` (9.0.0) and `serialize-javascript` (7.0.5) in `package.json`, suggesting past vulnerability remediation. |
| **Gap** | Dependabot provides basic dependency vulnerability scanning, but checks only monthly. No SBOM generation, no vulnerability threshold blocking, and no automated patching for transitive dependencies beyond Dependabot PRs. |
| **Recommendation** | Increase Dependabot check frequency to weekly for npm dependencies. Add `npm audit` to the CI pipeline as a required step. Consider adding Snyk or Socket.dev for deeper supply chain security analysis. Generate SBOMs for each release. |
| **Evidence** | `.github/dependabot.yml` — monthly npm and github-actions checks; `package.json` — `"overrides"` section with pinned versions for `mocha` sub-dependencies. |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | CodeQL SAST scanning is configured in `.github/workflows/codeql-analysis.yml` — runs on push to `master`, PRs to `master`, and on a weekly cron schedule (Sundays at 21:20 UTC). Scans JavaScript source code. Dependabot (`.github/dependabot.yml`) monitors npm and GitHub Actions dependencies for known vulnerabilities monthly. The `standard` linter (`standard.js`) runs as part of `npm test` in CI. No container scanning (no containers to scan). No explicit blocking gate — CodeQL reports findings to GitHub Security tab but does not block merges. |
| **Gap** | No blocking security gate on critical findings. CodeQL results are advisory only. Dependabot check interval is monthly (could miss time-sensitive vulnerabilities). No `npm audit` step in CI pipeline. |
| **Recommendation** | Add `npm audit --audit-level=critical` as a required CI step that fails the build on critical vulnerabilities. Configure CodeQL to block PRs via branch protection rules when critical severity findings are detected. Increase Dependabot frequency to weekly. |
| **Evidence** | `.github/workflows/codeql-analysis.yml` — CodeQL JavaScript analysis; `.github/dependabot.yml` — monthly dependency checks; `package.json` — `"lint": "standard"` run in test script; `.github/workflows/workflow.yml` — `npm test` includes linting. |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | `aws-xray-sdk-core` (v3.12.0) is a production dependency in `package.json` and is imported in `lib/main.js`. X-Ray is used in the `_runHandler()` method to create a tracing segment named `'annotations'` via `AWSXRay.Segment('annotations')` within a `continuation-local-storage` namespace. This provides tracing context for locally-executed Lambda handler functions (the `run` command). However, this tracing is for the user's Lambda handler execution, not for the CLI tool's own operations across AWS service boundaries. The tool's deployment operations (Lambda API, S3 API, CloudWatch Events API) are not traced. |
| **Gap** | X-Ray tracing is limited to local Lambda handler execution. The tool's own deployment operations across multiple AWS services are not traced — there's no trace correlation across the `_deployToRegion()` workflow spanning Lambda, S3, CloudWatch Events, and CloudWatch Logs API calls. |
| **Recommendation** | Instrument the AWS SDK with X-Ray for the deployment workflow to get automatic tracing of all AWS API calls. This can be done by calling `AWSXRay.captureAWS(require('aws-sdk'))` in `lib/aws.js`. This would provide end-to-end visibility into deployment operations for debugging and performance analysis. |
| **Evidence** | `package.json` — `"aws-xray-sdk-core": "^3.12.0"`, `"continuation-local-storage": "^3.2.1"`; `lib/main.js` — `const AWSXRay = require('aws-xray-sdk-core')`, `new AWSXRay.Segment('annotations')` in `_runHandler()`. |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found. No CloudWatch alarms, no error budgets, no latency targets. The tool is a CLI — SLOs are less common for CLI tools than for running services, but deployment success rate and deployment latency targets could be defined. |
| **Gap** | No formal SLO definitions for deployment success rate, deployment duration, or multi-region deployment consistency. |
| **Recommendation** | Define basic SLOs for the deployment workflow: target deployment success rate, maximum deployment duration, and multi-region deployment consistency. These could be tracked as custom CloudWatch metrics published during deployment. |
| **Evidence** | No SLO definition files, no CloudWatch alarm configurations, no monitoring dashboard definitions found in the repository. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom metrics are published. The tool outputs operational information via `console.log` during deployment but does not publish structured metrics to CloudWatch or any other metrics service. No `cloudwatch.putMetricData` calls exist. No deployment success/failure counters, no package size metrics, no deployment duration tracking. |
| **Gap** | No business or operational metrics. Deployment outcomes are visible only in console output — not tracked, aggregated, or alertable. |
| **Recommendation** | Add optional CloudWatch metrics publishing for: deployment count (success/failure by region), deployment package size, deployment duration, and Lambda function update latency. These metrics would enable operational dashboards and trend analysis for teams using node-lambda at scale. |
| **Evidence** | All source files in `lib/` — `console.log` used throughout for operational output; no CloudWatch metrics SDK calls; no metrics configuration. |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configured. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no error rate monitoring. The tool exits with a non-zero exit code on deployment failure (`process.exitCode = 1` in `deploy()`) but there is no automated alerting on failure patterns. |
| **Gap** | No alerting mechanism for deployment failures or anomalous behavior. |
| **Recommendation** | For teams using node-lambda in CI/CD, integrate deployment failure notifications via GitHub Actions failure notifications, SNS topics, or EventBridge (per preference) rules triggering on deployment failure events. |
| **Evidence** | `lib/main.js` — `process.exitCode = 1` on deployment error in `deploy()`; no alerting, monitoring, or notification code. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy for the tool itself. The npm package is published manually with no staged rollout, canary testing, or automated rollback. The GitHub Actions workflow runs tests on push/PR but has no deployment stage. The tool does support Lambda function versioning (`--publish` and `--lambdaVersion` flags) and alias management (`_alias()` in `lib/main.js`), which enables blue/green deployment of the user's Lambda functions — but the tool itself has no deployment strategy. |
| **Gap** | Direct-to-production npm publish with no staged rollout. No pre-release channel (e.g., npm `--tag next`), no canary, no automated rollback if a broken version is published. |
| **Recommendation** | Implement a staged npm publishing strategy: publish with `--tag next` for pre-release validation, then promote to `latest` after a validation period. Add a GitHub Actions release workflow with automated npm publish on version tags. |
| **Evidence** | `.github/workflows/workflow.yml` — test-only workflow, no publish step; `lib/main.js` — `_alias()` supports Lambda alias management for users' Lambda functions; `package.json` — `"version": "1.3.0"`. |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive test suite using mocha, chai, and aws-sdk-mock. The test suite covers: `test/main.js` (1717 lines — tests for deploy, package, zip, event sources, aliases, S3 deploy, multi-region), `test/s3_deploy.js`, `test/s3_events.js`, `test/schedule_events.js`, `test/cloudwatch_logs.js`. Additionally, `test/node-lambda.js` (398 lines) contains genuine integration tests that spawn the actual CLI process via `child_process.spawn('node', [nodeLambdaPath, 'run', ...])` and verify stdout/stderr output and exit codes. Tests run in CI across Node.js 22.x/24.x and Ubuntu/macOS/Windows. The aws-sdk-mock tests mock AWS API responses for deterministic testing. |
| **Gap** | No end-to-end tests against actual AWS services (understandable for a CLI tool). The aws-sdk-mock tests verify behavior against mocked responses, which may diverge from actual AWS API behavior. No contract tests verifying AWS SDK compatibility. |
| **Recommendation** | Consider adding optional integration tests that run against LocalStack or an AWS test account for critical deployment paths. The tool already supports `--endpoint` for LocalStack. Add a CI workflow (triggered manually or on release) that runs deployment tests against a real-ish environment. |
| **Evidence** | `test/main.js` (1717 lines), `test/node-lambda.js` (398 lines — CLI spawn tests), `test/s3_deploy.js`, `test/s3_events.js`, `test/schedule_events.js`, `test/cloudwatch_logs.js`; `package.json` — `"mocha": "^11.7.5"`, `"aws-sdk-mock": "^6.2.2"`, `"chai": "^6.2.2"`; `.github/workflows/workflow.yml` — `npm test` in CI. |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, no automated incident response, no self-healing patterns. No Systems Manager Automation documents, no Lambda-based remediation, no Step Functions for incident workflows. The tool exits with error codes on failure but has no recovery or rollback mechanism. |
| **Gap** | No incident response automation. Deployment failures require manual intervention. No documented rollback procedures. |
| **Recommendation** | Document a deployment rollback procedure (e.g., re-deploy previous version via `node-lambda deploy --deployZipfile previous.zip`). Consider adding a `rollback` CLI command that retrieves and deploys the previous Lambda function version. Add machine-readable runbooks for common failure scenarios (e.g., "Function not found", "S3 bucket already exists", "timeout during update"). |
| **Evidence** | No runbook files, no automation documents, no recovery scripts found in the repository. `lib/main.js` — `_isFunctionDoesNotExist()` handles one specific error but no general recovery pattern. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No service-level dashboards, no alarms with named owners, no SLO definitions with team attribution. No CODEOWNERS file referencing observability configurations. No monitoring dashboards defined. The tool is a community open-source project (`author: "motdotla"`) without formal team observability ownership structures. |
| **Gap** | No observability ownership. No dashboards, alarms, or SLO definitions exist to own. |
| **Recommendation** | For organizations adopting node-lambda at scale, create a CloudWatch dashboard tracking deployment metrics per team. Define CODEOWNERS for the `.github/` directory to ensure CI/CD configuration has clear ownership. |
| **Evidence** | No CODEOWNERS file, no dashboard definitions, no alarm configurations, no SLO definitions found in the repository. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The tool supports user-defined tags for deployed Lambda functions via the `--tags` CLI flag (e.g., `--tags "tagname1=tagvalue1,tagname2=tagvalue2"`). Tag parsing is implemented in `_params()` in `lib/main.js`. The `_updateTags()` method replaces all tags on a Lambda function (clears existing, applies new). However, the tool does not enforce any tagging standard, does not apply default tags, and does not tag S3 deployment buckets or other resources it creates. |
| **Gap** | S3 deployment buckets, CloudWatch Events rules, and CloudWatch Log groups created by the tool are not tagged. No default tags (e.g., `deployed-by: node-lambda`, `version: 1.3.0`) are applied. No tagging governance or enforcement. |
| **Recommendation** | Add default tags to all resources created by the tool: `deployed-by: node-lambda`, `node-lambda-version: {version}`, `deployed-at: {timestamp}`. Tag S3 deployment buckets in `lib/s3_deploy.js`. Apply tags to CloudWatch Events rules in `lib/schedule_events.js`. |
| **Evidence** | `lib/main.js` — `_params()` Tags section, `_updateTags()` method; `bin/node-lambda` — `--tags` flag, `AWS_TAGS` env var; `lib/s3_deploy.js` — `_createBucket()` without tags. |

---

## Learning Materials

### Move to Containers
- [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM)
- [Move to Containers with Amazon ECS](https://skillbuilder.aws/learning-plan/CDA8Y4JRRR)
- [EKS Workshop](https://www.eksworkshop.com/)

### Move to Managed Databases
- [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)
- [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)

### Move to Modern DevOps
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `package.json` | INF-Q1, INF-Q2, INF-Q11, APP-Q1, APP-Q2, APP-Q5, OPS-Q1, OPS-Q6, SEC-Q6, DATA-Q3 | npm package manifest — dependencies, engines, scripts, version |
| `bin/node-lambda` | INF-Q4, INF-Q5, INF-Q6, APP-Q4, APP-Q5, APP-Q6, SEC-Q1, SEC-Q3, SEC-Q5, OPS-Q5, OPS-Q9 | CLI entry point — commander options, environment variable defaults |
| `lib/main.js` | INF-Q3, INF-Q4, INF-Q8, INF-Q9, INF-Q10, APP-Q2, APP-Q3, APP-Q4, OPS-Q1, OPS-Q4, OPS-Q5, OPS-Q7, OPS-Q9, SEC-Q5 | Core Lambda class — deploy, package, run, setup commands; Promise chains, polling, event source management |
| `lib/aws.js` | INF-Q2, APP-Q2, APP-Q6, SEC-Q3, SEC-Q4, DATA-Q2 | Centralized AWS SDK configuration — credentials, proxy, endpoint |
| `lib/s3_deploy.js` | INF-Q8, INF-Q10, DATA-Q1, SEC-Q2, OPS-Q9 | S3 deployment package management — bucket creation, object upload |
| `lib/s3_events.js` | INF-Q10, APP-Q2, DATA-Q2 | S3 event notification configuration for Lambda functions |
| `lib/schedule_events.js` | INF-Q10, APP-Q2, DATA-Q2, OPS-Q9 | CloudWatch Events schedule rule management |
| `lib/cloudwatch_logs.js` | INF-Q10, APP-Q2, DATA-Q2 | CloudWatch Logs retention policy management |
| `index.js` | APP-Q5 | Sample Lambda handler for development/testing |
| `.github/workflows/workflow.yml` | INF-Q11, OPS-Q5, OPS-Q6, SEC-Q7 | GitHub Actions CI workflow — test matrix (Node.js 22.x/24.x, Ubuntu/macOS/Windows) |
| `.github/workflows/codeql-analysis.yml` | INF-Q11, SEC-Q7 | CodeQL SAST scanning — JavaScript analysis on push, PR, and weekly cron |
| `.github/dependabot.yml` | INF-Q11, SEC-Q6, SEC-Q7 | Dependabot — monthly npm and GitHub Actions dependency checks |
| `lib/.env.example` | SEC-Q3, SEC-Q5 | Example environment file with AWS credential placeholders |
| `lib/deploy.env.example` | SEC-Q5 | Example deploy environment file with secret variable placeholder |
| `.gitignore` | SEC-Q5 | Excludes `.env`, `deploy.env`, `event_sources.json` from version control |
| `test/main.js` | OPS-Q6 | Comprehensive unit tests (1717 lines) with aws-sdk-mock |
| `test/node-lambda.js` | OPS-Q6 | CLI integration tests (398 lines) using child_process.spawn |
| `test/s3_deploy.js` | OPS-Q6 | S3 deploy module tests |
| `test/s3_events.js` | OPS-Q6 | S3 events module tests |
| `test/schedule_events.js` | OPS-Q6 | Schedule events module tests |
| `test/cloudwatch_logs.js` | OPS-Q6 | CloudWatch Logs module tests |
| `README.md` | Quick Agent Wins | Extensive usage documentation (323 lines) — 4 commands, 40+ CLI options |
| `CHANGELOG.md` | Quick Agent Wins | Release history (491 lines) — all versions documented |
