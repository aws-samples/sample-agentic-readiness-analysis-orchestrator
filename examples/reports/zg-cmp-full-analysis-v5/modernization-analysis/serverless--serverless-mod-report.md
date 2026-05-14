# Modernization Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | frameworks-core |
| **Date** | 2025-07-16 |
| **TD Version** | (not available — run `atx custom def get -n modernization-analysis` to resolve) |
| **Repo Type** | monorepo |
| **Service Archetype** | stateless-utility (auto-detected, per-service) |
| **Priority** | P2 |
| **Tags** | javascript, serverless, iac, cli |
| **Context** | Serverless Framework CLI for building and deploying serverless apps. |
| **Surface Flags** | has_persistent_data_store=false, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=false, has_multi_instance_deployment=false |
| **Overall Score** | **2.78 / 4.0** |

**Archetype Justification**: All packages in this monorepo are libraries or CLI tools — no package deploys a persistent service, owns a database, or exposes an API surface. No database connections, no write endpoints, no message queue consumers detected. Classified as `stateless-utility` per-service.

> **Scoring Transparency Note:** Repo type is `monorepo`. Per the TD's N/A mapping, all 37 questions apply for monorepo. The TD's surface-gate mechanism (Step 1.6) explicitly authorizes "Not Evaluated" treatment for 5 questions (INF-Q2, INF-Q8, INF-Q9, SEC-Q2, OPS-Q2). Three additional questions (INF-Q3, APP-Q3, APP-Q4) qualify for "Not Evaluated (archetype-N/A)" via the TD's archetype calibration tables for `stateless-utility`. The remaining 7 questions without surface-gate or archetype-gate authorization (INF-Q1, INF-Q5, INF-Q6, INF-Q7, DATA-Q3, OPS-Q4, OPS-Q9) are scored per the TD rubric even though the scored surface does not exist in this repository (e.g., no deployed compute to evaluate for INF-Q1, no VPC to evaluate for INF-Q5). INF-Q4 is archetype-calibrated and scores 4 for `stateless-utility` (synchronous design is correct). These scores result in a lower overall score (2.78 vs the original 3.22) that reflects the literal absence of infrastructure in a CLI tool monorepo. Readers should weight the APP, DATA, and SEC category scores more heavily when evaluating this repository's actual modernization readiness.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 2.00 / 4.0 | 🟠 Needs Work |
| Application Architecture (APP) | 3.75 / 4.0 | ✅ Mature |
| Data Platform Modernization (DATA) | 3.00 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 2.67 / 4.0 | 🟡 Partial |
| Operations & Observability (OPS) | 2.50 / 4.0 | 🟡 Partial |
| **Overall** | **2.78 / 4.0** | **🟡 Partial** |

**Scoring notes:**
- INF category: 4 of 11 questions are Not Evaluated (INF-Q2 surface-gated, INF-Q3 archetype-N/A, INF-Q8 surface-gated, INF-Q9 surface-gated). Score based on INF-Q1 (1), INF-Q4 (4), INF-Q5 (1), INF-Q6 (1), INF-Q7 (1), INF-Q10 (2), INF-Q11 (4). Mean = 14/7 = 2.00.
- APP category: 2 of 6 questions are Not Evaluated (APP-Q3 archetype-N/A, APP-Q4 archetype-N/A). Score based on APP-Q1 (4), APP-Q2 (4), APP-Q5 (3), APP-Q6 (4). Mean = 15/4 = 3.75.
- DATA category: 0 Not Evaluated. Score based on DATA-Q1 (3), DATA-Q2 (4), DATA-Q3 (1), DATA-Q4 (4). Mean = 12/4 = 3.00.
- SEC category: 1 of 7 questions is Not Evaluated (SEC-Q2 surface-gated). Score based on SEC-Q1 (2), SEC-Q3 (3), SEC-Q4 (3), SEC-Q5 (3), SEC-Q6 (3), SEC-Q7 (2). Mean = 16/6 = 2.67.
- OPS category: 1 of 9 questions is Not Evaluated (OPS-Q2 surface-gated). Score based on OPS-Q1 (2), OPS-Q3 (3), OPS-Q4 (1), OPS-Q5 (4), OPS-Q6 (4), OPS-Q7 (3), OPS-Q8 (2), OPS-Q9 (1). Mean = 20/8 = 2.50.
- Overall = (2.00 + 3.75 + 3.00 + 2.67 + 2.50) / 5 = 2.78.

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q1: Managed Compute | 1 | No deployed compute workloads. The CLI tool is distributed as an npm package and binary — it does not run on EC2, ECS, EKS, Lambda, or Fargate. | No immediate modernization impact (CLI tools are not deployed services), but the score reflects the absence of any managed compute surface. |
| 2 | INF-Q5: Network Security | 1 | No VPC, subnets, security groups, or network segmentation. The tool runs on users' machines with no cloud-deployed network infrastructure. | No immediate impact — CLI tools do not have network infrastructure. Release pipeline AWS operations use OIDC-authenticated roles but no dedicated VPC. |
| 3 | INF-Q6: API Entry Point | 1 | No API Gateway, ALB, or CloudFront as an application entry point. The tool has no cloud-deployed API. The MCP server runs locally. | No immediate impact for a CLI tool. If the MCP server is ever cloud-deployed, an API Gateway entry point would be needed. |
| 4 | INF-Q7: Auto-Scaling | 1 | No auto-scaling configuration. No deployed workload exists to scale. | No immediate impact — CLI tools run on user machines. Release distribution via S3+CloudFront inherently scales. |
| 5 | DATA-Q3: DB Engine Version | 1 | No database engine versions defined in IaC. The tool does not own databases. The RELEASES_MONGO_URI in CI suggests a MongoDB instance exists externally but its engine version is not managed in this repository. | The external MongoDB instance's version lifecycle is not tracked here. If it approaches EOL, this repository provides no visibility. |

---

## Quick Agent Wins

### 1. API-Aware Agent (Already Implemented)

- **Prerequisite:** API docs exist (APP-Q5 ≥ 2, score = 3) and structured JSON responses are present.
- **Evidence:** The `@serverless/mcp` package **already implements** a comprehensive MCP (Model Context Protocol) server with 16+ agent tools defined in `packages/mcp/src/tools-definition.js`. Tools include `list-resources`, `aws-lambda-info`, `aws-iam-info`, `aws-sqs-info`, `aws-s3-info`, `aws-dynamodb-info`, `aws-logs-search`, `aws-logs-tail`, `aws-errors-info`, `aws-cloudwatch-alarms`, `deployment-history`, `service-summary`, `list-projects`, and `docs`. Each tool has Zod-validated parameters and structured JSON responses.
- **What it enables:** AI agents can already discover and invoke Serverless Framework capabilities as tools via MCP protocol (stdio or HTTP).
- **Additional steps:** None — this is production-ready. Consider publishing the MCP server as a standalone package for broader agent ecosystem adoption.
- **Effort:** Already complete.

### 2. DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 ≥ 2, score = 4).
- **Evidence:** GitHub Actions workflows provide comprehensive CI/CD automation with test, build, canary release, stable release, and npm publish stages. The release pipeline uses AWS credentials via `role-to-assume` for S3/CloudFront operations.
- **What it enables:** A DevOps agent could trigger deployments, check build status, manage release canary/stable promotion, and monitor CI pipeline health via GitHub Actions API.
- **Additional steps:** Expose GitHub Actions API integration as MCP tools or add GitHub-specific tools to the existing MCP server.
- **Effort:** Medium

### 3. RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists in repository (detected during discovery).
- **Evidence:** Extensive documentation exists: `docs/sf/` (Serverless Framework docs including getting-started, guides, providers, tutorial), `docs/scf/` (Serverless Container Framework), `docs/engine-types.md`, `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `TESTING.md`, `VERSIONING.md`, `RELEASE_PROCESS.md`, `AGENTS.md`. The MCP server already has a `docs` tool that provides access to documentation.
- **What it enables:** A RAG-based knowledge agent could index all documentation and provide natural language answers to developer questions about Serverless Framework configuration, deployment patterns, and troubleshooting.
- **Additional steps:** The existing MCP `docs` tool provides direct document access. For RAG, consider adding vector embeddings of the documentation corpus and a retrieval-augmented search tool.
- **Effort:** Medium

### 4. Observability Agent

- **Prerequisite:** Structured logging and tracing in place (OPS-Q1 ≥ 2, score = 2 — borderline).
- **Evidence:** Telemetry client (`packages/util/src/telemetry/`) publishes structured events to the Serverless Platform API. Analysis events include OS, architecture, CI/CD detection, command, runner type, errors, and machine ID. The MCP server already has `aws-errors-info`, `aws-logs-search`, `aws-logs-tail`, and `aws-cloudwatch-alarms` tools.
- **What it enables:** An observability agent could query CloudWatch logs, trace incidents across Lambda functions, analyze error patterns, and suggest root causes — all using the existing MCP tools.
- **Additional steps:** This is largely already implemented via the MCP error analysis tools. Enhance with automated correlation between deployment history and error patterns.
- **Effort:** Low (existing tools cover most use cases)

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 4 — monorepo already has well-defined module boundaries via npm workspaces. |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 1 but container definitions exist in the repository (dev-mode Dockerfiles). Contextual guard: tool is distributed as npm package + binary, not as a container. Dockerfiles in repo are for users' dev-mode containers, not the tool itself. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (no stored procedures), no commercial DB engines detected. |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 is Not Evaluated (no persistent data store). No databases to migrate. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 4 (synchronous design correct for stateless-utility archetype). No data processing workloads exist. Contextual guard: no streaming, ETL, or analytics artifacts found. |
| 6 | Move to Modern DevOps | Triggered | Medium | Low | INF-Q10 = 2 — Release infrastructure (S3, CloudFront) lacks IaC. CI/CD (INF-Q11 = 4) is already mature. |
| 7 | Move to AI | Not Triggered | — | — | Primary trigger NOT met — AI/agent frameworks ARE present (@aws-sdk/client-bedrock-agentcore, MCP server, bedrock-agentcore plugin). The codebase already has significant AI infrastructure. |

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Low

**Current IaC Coverage (INF-Q10 = 2):**
The release pipeline uses AWS CLI commands directly in GitHub Actions workflows to upload tarballs to S3 and invalidate CloudFront caches. Three separate AWS accounts are referenced (762003938904 for CI, 377024778620 for canary, 802587217904 for stable releases), each with IAM roles, S3 buckets, and CloudFront distributions — but none of this infrastructure is defined in code. If a bucket is accidentally deleted or a CloudFront distribution misconfigured, there is no IaC to recreate it.

**Current CI/CD State (INF-Q11 = 4):**
CI/CD automation is comprehensive and mature. The release pipeline already follows modern DevOps practices: cross-platform test matrix, canary releases, staged promotion, automated npm publishing. This is a strong foundation.

**Deployment Strategy (OPS-Q5 = 4):**
The canary → stable release pattern is already in place and working well.

**Recommendations:**
1. **Define release infrastructure in IaC** — Use CDK or CloudFormation (preferred for a Serverless Framework project) to codify the S3 buckets, CloudFront distributions, IAM roles, and CloudFront invalidation configurations used by the release pipeline. This covers three AWS accounts.
2. **Add IaC for GitHub Actions IAM roles** — The `role-to-assume` IAM roles (GithubActionsDeploymentRole) should be defined in IaC with OIDC trust policies.
3. **Consider AWS CDK** — Given the team's deep AWS expertise and JavaScript ecosystem, CDK in TypeScript would be a natural fit for defining release infrastructure.

**Representative AWS services:** CloudFormation, CDK, S3, CloudFront, IAM
**Learning resources:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

<!-- Decomposition Strategy section omitted — APP-Q2 = 4, not applicable -->

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | This monorepo contains CLI tools and libraries. No packages deploy their own compute workloads — the tool deploys compute for users via CloudFormation generation, but does not itself run on EC2, ECS, EKS, Lambda, or Fargate. All compute on raw EC2 or on-premises with no managed services — in this case, no compute at all. The tool is distributed as an npm package and standalone binary via S3+CloudFront. |
| **Gap** | No managed compute. The CLI tool has no deployed compute surface. This is inherent to the repository's nature as a CLI tool monorepo, not a deployment gap. |
| **Recommendation** | No action required. CLI tools are not deployed services and do not need managed compute. If any package evolves into a deployed service (e.g., a cloud-hosted MCP server), adopt ECS/Fargate or Lambda at that point. |
| **Evidence** | `package.json` (npm package distribution), `binary-installer/` (Go binary for CLI installation), `.github/workflows/release-framework.yml` (distributes via S3+CloudFront+npm, not deployed compute) |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy a database. No database resources, connection strings, or database drivers exist for the tool's own use. INF-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No `aws_rds_*`, `aws_dynamodb_*`, or database connection configuration found in the repository. The tool generates database CloudFormation for users but does not own databases. |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | All packages in this monorepo are libraries/CLI tools. No multi-step workflows exist that would benefit from dedicated orchestration services. The CLI's internal operation flow (parse config → resolve → deploy) is a straightforward sequential pipeline, not a distributed workflow. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `packages/sf-core/src/lib/router.js` (sequential routing logic), `packages/sf-core/src/lib/runners/` (runner pattern is synchronous command dispatch) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Per archetype calibration for `stateless-utility`: Synchronous communication is the correct design and is in use; no messaging needed. This CLI tool ecosystem communicates via synchronous JavaScript imports within a single Node.js process. No SQS, SNS, EventBridge, Kafka, or streaming infrastructure exists or is needed. The tool's outbound telemetry signals use the Serverless Platform API (managed service). `@aws-sdk/client-sqs` and `@aws-sdk/client-eventbridge` in `packages/engine/package.json` are for managing users' resources, not the tool's own messaging. |
| **Gap** | None. Synchronous communication is the correct design for a CLI tool. Adopting async messaging is NOT recommended — it would add operational complexity without architectural benefit. |
| **Recommendation** | None required. The synchronous design is appropriate for this archetype. |
| **Evidence** | No messaging SDK imports for the tool's own operations. `@aws-sdk/client-sqs` and `@aws-sdk/client-eventbridge` in `packages/engine/package.json` are for managing users' resources. `packages/util/src/telemetry/index.js` publishes events to managed Platform API. |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnets, security groups, NACLs, or network segmentation defined in this repository. The CLI tool runs on users' machines and authenticates to AWS using standard credential chains. There is no cloud-deployed infrastructure for the tool itself that would require network isolation. The release pipeline operates via GitHub Actions runners connecting to AWS APIs over the public internet using OIDC-authenticated IAM roles. |
| **Gap** | Services deployed in the default VPC or to public subnets without isolation — in this case, no cloud-deployed services at all. No network security controls exist because no network infrastructure exists for this CLI tool. |
| **Recommendation** | No action required for the CLI tool itself. If release infrastructure is ever codified in IaC (per INF-Q10 recommendation), consider deploying any supporting resources in a VPC with proper network segmentation. |
| **Evidence** | No VPC, subnet, or security group definitions in the repository. `packages/engine/src/lib/aws/vpc.js` exists but is for managing users' VPC resources. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, AppSync, ALB, or CloudFront configured as an application entry point. The tool does not expose a cloud-deployed API. The MCP server (`packages/mcp/src/server.js`) runs locally via stdio or HTTP but is not a cloud-deployed API with managed entry point. CloudFront distributions exist for release artifact distribution (CDN), not as API entry points. |
| **Gap** | Services exposed directly with no gateway or load balancer — in this case, no deployed API services exist. The MCP server, when running in HTTP mode, has no API Gateway, ALB, or CloudFront fronting it. |
| **Recommendation** | No action required for the CLI tool itself. If the MCP server is ever deployed as a cloud service, front it with API Gateway (preferred per preferences: api-gateway) with throttling, authentication, and request validation. |
| **Evidence** | `packages/mcp/src/server.js` (local Express server, not cloud-deployed), no API Gateway or ALB resources in the repo for the tool itself. |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. No deployed workload exists to auto-scale. The CLI tool runs on users' machines. The release infrastructure (S3+CloudFront) is inherently auto-scaling as managed AWS services, but this is not application compute auto-scaling. No `aws_autoscaling_*` or `aws_appautoscaling_*` resources found. |
| **Gap** | No auto-scaling — all capacity is statically provisioned. In this case, no capacity exists to provision because no compute workloads are deployed. |
| **Recommendation** | No action required for the CLI tool itself. The release distribution infrastructure (S3+CloudFront) inherently scales. If any package evolves into a deployed service, configure auto-scaling at that point. |
| **Evidence** | No `aws_autoscaling_*` or `aws_appautoscaling_*` resources. `packages/engine/src/lib/aws/autoscaling.js` exists for managing users' auto-scaling, not the tool's own. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no persistent state to back up. The CLI tool is stateless; state is stored in users' AWS accounts (CloudFormation stacks, S3 deployment buckets). Release artifacts in S3 are the closest to "owned data" but are reproducible from source. INF-Q8 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No databases, no persistent storage owned by the tool. Release S3 buckets contain reproducible build artifacts. |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload requiring HA evaluation. The CLI tool runs on users' local machines. CloudFront for distribution provides inherent HA but is not an application workload. INF-Q9 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No compute instances, ECS services, or EKS deployments for the tool itself. Distribution via CloudFront is inherently multi-AZ. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The repository has **no IaC** (Terraform, CDK, CloudFormation) defining the tool's own release infrastructure. The release pipeline operates across three AWS accounts (762003938904, 377024778620, 802587217904), each with S3 buckets, CloudFront distributions (E1USPSJN28WQ8U for canary, E3OEL4OJF1G5FG for stable), and IAM roles (GithubActionsDeploymentRole). All of this infrastructure was created manually or via other means — no IaC tracks or reproduces it. The `release-framework.yml` and `release-binary-installer.yml` workflows use `aws s3 cp` and `aws cloudfront create-invalidation` commands directly. |
| **Gap** | Release infrastructure across 3 AWS accounts is not defined in code. S3 buckets, CloudFront distributions, IAM roles with OIDC trust policies, and CloudFront invalidation configurations are all manually managed. |
| **Recommendation** | Define release infrastructure in CDK or CloudFormation. Start with the IAM roles (GithubActionsDeploymentRole with GitHub OIDC trust), then S3 buckets, then CloudFront distributions. Use separate CDK stacks per AWS account. This is a bounded, low-risk effort since the infrastructure already exists — the IaC codifies what's in place. |
| **Evidence** | `.github/workflows/release-framework.yml` (lines referencing `aws s3 cp`, `aws cloudfront create-invalidation`, `role-to-assume`), `.github/workflows/release-binary-installer.yml` (same pattern), no `.tf`, `cdk.json`, or `template.yaml` files in repository |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Comprehensive CI/CD automation covering all packages with multi-stage pipelines. **CI pipelines:** `ci-framework.yml` (lint, unit tests for sf-core and serverless, build, integration tests with AWS credentials via OIDC), `ci-engine.yml` (engine unit tests), `ci-python.yml` (Python requirements integration tests with actual AWS deployments), `ci-binary-installer.yml` (Go unit tests + production build). **Release pipeline:** `release-framework.yml` implements a sophisticated 4-stage release: (1) test-engine (engine unit tests), (2) test-matrix (cross-platform: ubuntu, arm-linux, windows — with unit tests, build, integration tests on each), (3) release-canary (upload tarballs to canary S3/CloudFront, tag version), (4) release-stable (upload to stable S3/CloudFront, write to MongoDB release registry), (5) release-npm (publish sf-core-installer to npm). Canary releases deploy on every main push; stable releases only on version bumps. All workflows use pinned GitHub Actions (SHA-based) and OIDC for AWS authentication. |
| **Gap** | Minor: no automated rollback mechanism if canary release fails in production. The canary → stable gate is version-tag based, not metric-based. |
| **Recommendation** | Consider adding automated canary validation (e.g., smoke tests against canary tarballs before promoting to stable). This is a minor enhancement to an already mature pipeline. |
| **Evidence** | `.github/workflows/ci-framework.yml`, `.github/workflows/ci-engine.yml`, `.github/workflows/ci-python.yml`, `.github/workflows/ci-binary-installer.yml`, `.github/workflows/release-framework.yml`, `.github/workflows/release-binary-installer.yml` |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Modern cloud-native stack: **JavaScript (ESM)** with Node.js 18+ (CI runs on 24.x), AWS SDK v3 (3.1015.0 — current as of analysis), Jest 30, esbuild 0.27.4, Express 5, zod v4, Zod-validated schemas throughout. **Go 1.26.1** for the binary installer. All packages use `"type": "module"` (ESM). Dependencies are current and well-maintained. The MCP server uses `@modelcontextprotocol/sdk ^1.27.1`. |
| **Gap** | Legacy AWS SDK v2 (`aws-sdk ^2.1693.0`) still present as a dependency in `@serverless/framework` alongside v3. This is a migration-in-progress signal — the v3 client factory exists and is actively used, but v2 hasn't been fully removed. |
| **Recommendation** | Complete migration from AWS SDK v2 to v3 and remove the `aws-sdk` v2 dependency. The `client-factory.js` infrastructure is already in place for v3. |
| **Evidence** | `packages/serverless/package.json` (AWS SDK v3 3.1015.0 + legacy v2), `packages/sf-core/package.json` (AWS SDK v3), `packages/engine/package.json` (AWS SDK v3), `binary-installer/go.mod` (Go 1.26.1), `package.json` (root: ESM type, Node.js) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Well-structured **modular monolith** via npm workspaces with clear package boundaries: `@serverless/util` (shared utilities) → `@serverlessinc/standards` (linting config) → `@serverless/framework` (core framework logic, plugins, CloudFormation generation) → `@serverless/engine` (reusable deployment engine) → `@serverlessinc/sf-core` (CLI entry point, router, runners) → `@serverless/mcp` (MCP server consuming engine and framework). Each package has its own `package.json` with explicit dependencies, separate test suites (`tests/unit/`, `tests/integration/`), and clear interfaces. The router pattern in `sf-core/src/lib/router.js` cleanly dispatches to runners (ComposeRunner, CfnRunner, ServerlessContainerFrameworkRunner, ServerlessAiFrameworkRunner, TraditionalRunner) based on config file detection. |
| **Gap** | No significant gaps. The workspace structure is well-defined with `"*"` aliases for internal dependencies, enabling independent development while maintaining a unified build. |
| **Recommendation** | None required. The modular workspace architecture is appropriate for this monorepo. |
| **Evidence** | `package.json` (workspaces config), `packages/sf-core/src/lib/router.js` (runner dispatch), `packages/*/package.json` (dependency declarations), `packages/sf-core/tests/integration/` (12 integration test directories) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | All packages are libraries/CLI tools. Inter-package communication is via synchronous JavaScript `import` statements, which is the correct design for a CLI tool ecosystem. There are no inter-service network calls between packages — they share a single Node.js process. Async/await is used appropriately for I/O operations (AWS SDK calls, file operations) but this is intra-process concurrency, not inter-service communication. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `packages/sf-core/src/lib/router.js` (synchronous import of runners), `packages/serverless/lib/aws/v3/client-factory.js` (async AWS calls within single process) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | The CLI tool handles long-running operations (CloudFormation deployments, Docker image builds) using async/await patterns with progress indicators (ora via `@serverless/util`). The progress system (`progress.get('main').notice(...)`) provides user feedback during extended operations. Step Functions-style orchestration is not applicable — the CLI runs in a single user session. This is the correct design for a CLI tool. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `packages/sf-core/src/lib/router.js` (progressMain.notice patterns), `packages/util/package.json` (ora dependency for spinners), `packages/serverless/lib/plugins/aws/bedrock-agentcore/docker/coordinator.js` (Docker build as async operation) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Versioning strategy exists at multiple levels: (1) **Package versioning** — All packages use semver (`@serverlessinc/sf-core@4.33.2`, `@serverless/framework@4.0.0`, etc.) with documented versioning policy (`VERSIONING.md`). (2) **CLI command versioning** — The CLI supports `--version` and version commands. The router pattern supports multiple runner types (Compose, CFN, SCF, SAI, Traditional) providing a form of API versioning for different config file formats. (3) **MCP tool definitions** — The MCP server defines tools with Zod-validated schemas providing implicit interface contracts. (4) **Plugin interface** — The Serverless Framework plugin interface (hooks system) is established but not formally versioned beyond major version bumps. |
| **Gap** | No formal API versioning for the plugin interface or MCP tool schemas. Breaking changes to the plugin hook system or MCP tool parameters are managed via major version bumps rather than versioned interfaces (e.g., no `/v1/` or `Accept-Version` equivalent for plugin hooks). |
| **Recommendation** | Consider adding version metadata to MCP tool definitions and documenting plugin interface stability guarantees per semver. This is minor — the current approach of major-version breaking changes is standard for CLI tools. |
| **Evidence** | `VERSIONING.md`, `packages/sf-core/package.json` (version 4.33.2), `packages/mcp/src/tools-definition.js` (Zod schemas for tool params), `packages/sf-core/src/lib/router.js` (multi-runner dispatch) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | **npm workspace resolution** provides dynamic package discovery. All internal dependencies use `"*"` workspace aliases (e.g., `"@serverless/engine": "*"` in sf-core's package.json), which npm resolves to the local workspace package at install time. No hardcoded paths or endpoints between packages. The router in `sf-core/src/lib/router.js` dynamically discovers runners based on config file detection using `RunnerClass.configFileNames` and `RunnerClass.shouldRun()` — a plugin-style discovery pattern. |
| **Gap** | None. Workspace aliases and plugin discovery patterns are the correct approach for a monorepo CLI tool. |
| **Recommendation** | None required. |
| **Evidence** | `packages/sf-core/package.json` (`"@serverless/engine": "*"`, `"@serverless/framework": "*"`, `"@serverless/mcp": "*"`), `packages/sf-core/src/lib/router.js` (dynamic runner discovery) |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The tool uses S3 extensively for deployment artifacts: Lambda function zips, CloudFormation templates, and release tarballs are uploaded to S3 using AWS SDK v3. The `@aws-sdk/lib-storage` package is used for multipart uploads. The engine package has a dedicated `s3.js` module (`packages/engine/src/lib/aws/s3.js`). Release artifacts are stored in S3 and served via CloudFront. |
| **Gap** | No automated parsing or extraction pipeline for stored data. S3 is used as a distribution mechanism, not a data lake. This is appropriate for the use case — deployment artifacts don't need parsing pipelines. |
| **Recommendation** | No action needed for the tool's own use case. S3 usage is well-structured and appropriate. The gap between Score 3 and Score 4 (parsing pipeline) is not relevant for CLI distribution artifacts. |
| **Evidence** | `packages/serverless/package.json` (`@aws-sdk/client-s3`, `@aws-sdk/lib-storage`), `packages/engine/src/lib/aws/s3.js`, `.github/workflows/release-framework.yml` (`aws s3 cp` commands) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Well-organized, centralized AWS SDK access layer. The `@serverless/framework` package provides a centralized **client factory** (`packages/serverless/lib/aws/v3/client-factory.js`) that creates memoized AWS SDK v3 clients with consistent configuration (region, credentials, proxy support). The `@serverless/engine` package has a structured `aws/` directory with dedicated service modules (`s3.js`, `dynamodb.js`, `ecs.js`, `cloudformation.js`, `lambda.js`, `iam.js`, `sqs.js`, `ssm.js`, `vpc.js`, `route53.js`, `ecr.js`, `cloudwatch.js`, `eventbridge.js`, `alb.js`, `acm.js`, `autoscaling.js`, `cloudfront.js`). The `@serverless/util` package provides shared proxy configuration (`addProxyToAwsClient`). This is a textbook centralized data access layer. |
| **Gap** | None. The multi-layered client factory → service module pattern provides excellent separation of concerns. |
| **Recommendation** | None required. |
| **Evidence** | `packages/serverless/lib/aws/v3/client-factory.js` (centralized factory), `packages/engine/src/lib/aws/` (22 service-specific modules), `packages/util/src/proxy/` (proxy support for all clients) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database engine versions are defined in IaC or deployment configuration. The tool does not own or manage database infrastructure. The `RELEASES_MONGO_URI` secret in `.github/workflows/release-framework.yml` references an external MongoDB instance used for release metadata, but its engine version, EOL status, and lifecycle management are not tracked in this repository. No version pinning exists because no database resources are defined. |
| **Gap** | No version pinning; engine version and EOL status unknown for the external MongoDB instance referenced via `RELEASES_MONGO_URI`. The repository provides no visibility into the database engine lifecycle for its only known database dependency. |
| **Recommendation** | Document the MongoDB engine version and EOL timeline for the release metadata database. If the MongoDB instance is managed externally (e.g., MongoDB Atlas), ensure its engine version is tracked and upgraded before EOL. Consider codifying the MongoDB connection as part of the IaC effort (INF-Q10). |
| **Evidence** | No database engine definitions in the repository. `RELEASES_MONGO_URI` in `.github/workflows/release-framework.yml` references an external MongoDB instance with no version tracking. |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL anywhere in the codebase. All business logic resides in the JavaScript/Go application layer. The tool generates CloudFormation resources for users but does not itself use database-tier business logic. The closest to database interaction is the `RELEASES_MONGO_URI` secret used in the release pipeline to write release metadata to MongoDB — this is a simple write, not stored procedure usage. |
| **Gap** | None. |
| **Recommendation** | None required. |
| **Evidence** | No `.sql` files with `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION` in the repository. `RELEASES_MONGO_URI` in `.github/workflows/release-framework.yml` is a simple API call, not database-tier logic. |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No explicit CloudTrail configuration for the tool's own AWS operations. The release pipeline makes AWS API calls (S3 uploads, CloudFront invalidations) across three AWS accounts using OIDC-authenticated IAM roles, but there is no evidence of CloudTrail being explicitly configured or monitored for these accounts. GitHub Actions provides audit logs for workflow executions. The tool generates CloudTrail configurations for users but doesn't configure its own. |
| **Gap** | No explicit audit logging for the tool's own AWS operations. The three AWS accounts used for releases (CI, canary, stable) may or may not have CloudTrail enabled — this is not visible from the repository. |
| **Recommendation** | Ensure CloudTrail is enabled with log file validation in all three AWS accounts used by the release pipeline. Define CloudTrail configuration in IaC (tied to INF-Q10 recommendation). At minimum, verify that the accounts have organization-level CloudTrail trails. |
| **Evidence** | `.github/workflows/release-framework.yml` (3 AWS accounts with `role-to-assume`), no `aws_cloudtrail` resources in repository |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no database, EBS volume, or EFS file system. The release S3 buckets store distribution tarballs (reproducible build artifacts), but these are not sensitive data. The S3 buckets and their encryption configuration are not visible from the repository (no IaC). SEC-Q2 does not apply for the tool's own data surface. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database, EBS, or EFS resources. S3 buckets referenced in `.github/workflows/release-framework.yml` but encryption config not visible without IaC. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Robust authentication implementation in `packages/sf-core/src/lib/auth/index.js`: (1) **Token-based auth** — OAuth2/JWT via Serverless Dashboard with ID token refresh, Access Key V1 (personal), and Access Key V2 (License Key). (2) **AWS credentials** — `@aws-sdk/credential-providers` with `fromNodeProviderChain` for flexible credential resolution, including AWS SSO support (`packages/sf-core/src/lib/auth/aws-sso-login.js`). (3) **CI/CD auth** — GitHub Actions uses OIDC-based `role-to-assume` (no static credentials). (4) **SSM License Key** — Automatically fetches license key from `/serverless-framework/license-key` SSM parameter with decryption. The MCP server inherits AWS credentials from the environment. |
| **Gap** | The MCP server (`packages/mcp/src/server.js`) runs locally and inherits ambient credentials without explicit per-request authentication. While appropriate for a local dev tool, the MCP server when running in HTTP mode (Express) does not enforce authentication on incoming requests. |
| **Recommendation** | Add authentication middleware to the MCP HTTP server for scenarios where it's exposed beyond localhost. This is low priority for current local-only usage but important if the MCP server is ever exposed on a network. |
| **Evidence** | `packages/sf-core/src/lib/auth/index.js` (comprehensive auth class), `packages/sf-core/src/lib/auth/aws-sso-login.js`, `.github/workflows/release-framework.yml` (`role-to-assume` OIDC), `packages/mcp/src/server.js` (no auth middleware) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The tool integrates with **Serverless Dashboard** as a centralized identity provider: (1) Browser-based login flow via WebSocket broker (`loginViaBrowser()` in auth/index.js), (2) JWT token management with automatic refresh, (3) Organization-scoped access keys, (4) SSO integration via AWS SSO (`aws-sso-login.js`). The `@serverless-inc/sdk` CoreSDK is used for all platform API interactions. Multiple authentication paths coexist: Dashboard user sessions, Access Keys V1, License Keys (Access Keys V2), and SSM-sourced license keys. |
| **Gap** | Some legacy auth paths remain — the `.serverlessrc` file-based credential storage predates modern centralized identity patterns. The coexistence of three authentication flows (user session, access key, license key) adds complexity. |
| **Recommendation** | Consider consolidating authentication flows over time. The current multi-path approach serves different use cases (interactive dev, CI/CD, license-only) and is functional, but documentation of when to use which flow could be improved. |
| **Evidence** | `packages/sf-core/src/lib/auth/index.js` (Authentication class with 3 flows), `packages/sf-core/src/lib/auth/aws-sso-login.js`, `packages/sf-core/package.json` (`@serverless-inc/sdk`, `@aws-sdk/client-sso-oidc`) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | **GitHub Secrets** properly used for all CI/CD credentials: `SERVERLESS_LICENSE_KEY_DEV`, `SERVERLESS_ACCESS_KEY_DEV`, `RELEASES_MONGO_URI`. No plaintext credentials in source code or version-controlled config files. The tool supports fetching license keys from **AWS SSM Parameter Store** with decryption (`WithDecryption: true`). The `.serverlessrc` file stores credentials locally on users' machines (not committed to git — listed in `.gitignore`). OIDC-based `role-to-assume` eliminates static AWS credentials in CI/CD. |
| **Gap** | No evidence of automated rotation for the GitHub Secrets. The `RELEASES_MONGO_URI` secret suggests a MongoDB connection string — rotation policy is not visible. SSM parameter for license keys uses `WithDecryption: true` but the underlying KMS key rotation is not configured in this repository. |
| **Recommendation** | Document rotation policy for GitHub Secrets. Consider migrating the MongoDB connection (used for release metadata) to a solution with automated rotation (e.g., Secrets Manager with rotation Lambda). This is low priority given the limited scope of secrets used. |
| **Evidence** | `.github/workflows/release-framework.yml` (`${{ secrets.* }}`), `packages/sf-core/src/lib/auth/index.js` (SSM license key fetch with decryption), `.gitignore` (excludes rc files), no hardcoded credentials found in source scan |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | **Dependabot** is comprehensively configured across 5 ecosystems: npm (root workspace), npm (framework-dist), npm (sf-core-installer), gomod (binary-installer), maven (Java runtime wrapper), and github-actions. Version groups intelligently bundle AWS SDK updates. Cooldown periods prevent update fatigue. GitHub Actions use **pinned SHAs** (e.g., `actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd`) — an excellent security practice preventing supply chain attacks via tag manipulation. CI runs on GitHub-hosted runners (ubuntu-latest, arm-linux, windows) — GitHub manages patching. `husky` + `lint-staged` enforce code quality on commit. |
| **Gap** | No vulnerability scanning tool (AWS Inspector, Snyk, Trivy) is configured. Dependabot handles version updates but does not perform deep vulnerability analysis. No container image scanning for the dev-mode Dockerfiles. |
| **Recommendation** | Add `npm audit` or Snyk to the CI pipeline for vulnerability scanning beyond Dependabot's version updates. Consider Trivy for scanning the dev-mode container images in `packages/engine/src/lib/devMode/containers/`. |
| **Evidence** | `.github/dependabot.yml` (5 ecosystem configs with groups, cooldown, ignores), `.github/workflows/ci-framework.yml` (pinned SHA actions), `package.json` (husky, lint-staged) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | **Dependency scanning** is in place via Dependabot (version updates across npm, gomod, maven, github-actions). **ESLint** runs in CI as part of the lint step. However, **no SAST tool** (CodeQL, Semgrep, SonarQube, CodeGuru) is integrated into the CI pipeline. No container scanning for the Dockerfiles in `packages/engine/src/lib/devMode/containers/`. No `npm audit` step in CI workflows. For a CLI tool that handles AWS credentials, authentication tokens, and deploys infrastructure, the lack of SAST is a notable gap. |
| **Gap** | Missing SAST tool in CI/CD pipeline. No security gate blocking on critical findings. No container image scanning. `npm audit` not explicitly run in CI (though `npm ci` may surface some issues). |
| **Recommendation** | Add CodeQL (free for open-source repos) or Semgrep to the GitHub Actions CI pipeline. CodeQL has excellent JavaScript/TypeScript support and would catch common vulnerability patterns in credential handling, injection, and prototype pollution. Add an `npm audit --production` step to CI. Consider Trivy for container scanning. |
| **Evidence** | `.github/workflows/ci-framework.yml` (lint step exists, no SAST step), `.github/dependabot.yml` (dependency scanning only), no `.github/codeql/` or `.semgrep.yml` configuration |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The tool provides **observability integration for users' deployments** via Axiom and Serverless Dashboard (`packages/serverless/lib/plugins/observability/`, `packages/sf-core/src/lib/observability/index.js` defining DISABLED/AXIOM/DASHBOARD providers). **Telemetry** is collected for the CLI tool itself via `packages/util/src/telemetry/` (publishes structured events to Serverless Platform API) and `instanceUsageTrackingClient`. Analysis events include detailed context (OS, architecture, CI/CD detection, command, runner type, errors). However, there is **no distributed tracing with trace ID propagation** for the CLI tool's own operations — no OpenTelemetry SDK, no X-Ray instrumentation, no `traceparent` headers in outbound AWS SDK calls. |
| **Gap** | No trace ID propagation across the CLI tool's AWS SDK calls. When a deployment involves multiple AWS service calls (S3 upload → CloudFormation create → Lambda configuration), there is no trace connecting these operations for debugging. |
| **Recommendation** | Instrument the AWS SDK v3 client factory with OpenTelemetry or X-Ray tracing. The centralized `client-factory.js` is the ideal injection point — all AWS clients flow through it. This would enable end-to-end tracing of deployment operations. |
| **Evidence** | `packages/util/src/telemetry/index.js` (event-based telemetry, not tracing), `packages/sf-core/src/lib/observability/index.js` (provider enum), `packages/serverless/lib/aws/v3/client-factory.js` (no tracing middleware) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no user-facing API surface for which SLOs are meaningful. The CLI tool runs on users' machines — its "availability" is determined by npm package availability and S3/CloudFront distribution uptime, both of which are managed AWS services. SLOs would apply to the Serverless Platform API (external to this repo), not the CLI tool itself. OPS-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No SLO definitions found. Tool is a CLI, not a service with uptime requirements. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The tool publishes **business-relevant telemetry** beyond basic infrastructure metrics: (1) `platformEventClient` in `packages/util/src/telemetry/index.js` publishes structured events in batches to `core.serverless.com/api/events/publish/bulk`. (2) `instanceUsageTrackingClient` tracks per-service usage events with `serviceUniqueId`, command, and framework version. (3) Analysis events (`createAnalysisEvent` in `packages/sf-core/src/lib/router.js`) capture OS, architecture, CI/CD detection, machine ID, project type, CLI options, resolvers used, runner-specific details, and error context. (4) Deployment events are saved via `saveDeployment()`. This provides rich business metrics on CLI usage patterns. |
| **Gap** | Metrics are published to the Serverless Platform API but there's no evidence of dashboards or systematic analysis within this repository. The telemetry is collected but the consumption/analysis layer is external. |
| **Recommendation** | This is appropriate — the CLI tool publishes metrics to the platform for analysis. No change needed for the CLI repo itself. |
| **Evidence** | `packages/util/src/telemetry/index.js` (PlatformEventClient), `packages/sf-core/src/lib/router.js` (createAnalysisEvent, createUsageEvent, sendDeploymentEvent) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting is configured for the CLI tool's operations. No CloudWatch alarms, anomaly detection, error rate monitoring, or latency alerting exists in this repository. The release pipeline relies on GitHub Actions success/failure notifications. The tool publishes telemetry events to the Serverless Platform API, but consumption and alerting on that telemetry is external to this repository. |
| **Gap** | No alerting configured. The release pipeline has no automated alerting on failure rates or anomalies beyond GitHub Actions workflow failure notifications. Telemetry data is published but no anomaly detection monitors it from this repository. |
| **Recommendation** | Add CloudWatch alarms or GitHub Actions alerting for release pipeline health metrics (e.g., consecutive failures, S3 upload failures, CloudFront invalidation failures). Consider monitoring download metrics from the release S3/CloudFront distributions to detect distribution issues. |
| **Evidence** | No CloudWatch alarms, anomaly detection, or alerting configuration in the repository. `.github/workflows/release-framework.yml` has no alerting step beyond workflow status. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Sophisticated **canary + stable** release strategy in `release-framework.yml`: (1) **test-matrix** — Cross-platform testing on ubuntu, arm-linux, windows with unit tests, build, and integration tests. (2) **release-canary** — Upload tarballs to canary S3 bucket (account 377024778620) with CloudFront distribution (E1USPSJN28WQ8U), invalidate cache. Tag version if new. (3) **release-stable** — Triggered only on version tag. Upload to stable S3 bucket (account 802587217904) with CloudFront distribution (E3OEL4OJF1G5FG), write to releases.json/versions.json, invalidate cache. (4) **release-npm** — Publish sf-core-installer to npm registry. This is a textbook canary → stable promotion pattern with automated gates. Binary installer has a separate release pipeline with similar quality. |
| **Gap** | No automated metric-based validation between canary and stable (the gate is version-tag presence, not canary health metrics). This is acceptable for a CLI distribution pattern. |
| **Recommendation** | The current strategy is already mature. Consider adding automated smoke tests that run against the canary distribution before manual version tagging triggers stable promotion. |
| **Evidence** | `.github/workflows/release-framework.yml` (4-stage pipeline: test-matrix → release-canary → release-stable → release-npm), `.github/workflows/release-binary-installer.yml` (separate binary release pipeline) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | **Extensive integration test suites** covering critical workflows across all major packages: (1) `packages/sf-core/tests/integration/` — 12 integration test directories: deployment-bucket, domains, esbuild, license-key, local-plugin, resolvers, sam, simple-compose, simple-dashboard, simple-nodejs, simple-python, state. (2) `packages/engine/integration/e2e/` — Engine end-to-end tests. (3) `packages/mcp/tests/e2e/` — MCP server end-to-end tests (aws-errors-info). (4) `packages/sf-core/tests/python/` — Python requirements integration tests. All integration tests run in CI pipeline with actual AWS credentials (OIDC-authenticated) against real AWS services. Cross-platform execution (ubuntu, arm-linux, windows) in the release pipeline. |
| **Gap** | None significant. The integration test coverage is comprehensive and runs against live AWS infrastructure. |
| **Recommendation** | None required. The test coverage is excellent. |
| **Evidence** | `packages/sf-core/tests/integration/` (12 directories), `packages/mcp/tests/e2e/`, `.github/workflows/ci-framework.yml` (integration tests in CI with AWS credentials), `.github/workflows/release-framework.yml` (cross-platform integration tests in release) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The `serverless support` command (`packages/sf-core/src/lib/runners/core/support.js`, 715 lines) generates comprehensive diagnostic reports including: service configuration, deployment state, error details, environment info (OS, Node.js version, framework version), and relevant logs. This is effectively a **machine-readable runbook** for diagnosing deployment failures. Support modes include summary, comprehensive (all), AI-friendly, and GitHub issue format. The `saveMeta()` function in the router saves metadata for every command execution, creating an audit trail for debugging. |
| **Gap** | No self-healing automation. The support command generates reports for human analysis, not automated remediation. No automated incident response for release pipeline failures. |
| **Recommendation** | Consider adding automated retry logic for common release pipeline failures (e.g., CloudFront invalidation timeouts, S3 upload failures). The support command is already valuable for user-facing incident response. |
| **Evidence** | `packages/sf-core/src/lib/runners/core/support.js` (715-line diagnostic report generator), `packages/sf-core/src/lib/router.js` (saveMeta function), `packages/sf-core/src/lib/meta/` (metadata persistence) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Telemetry exists (analysis events, usage events, deployment events) but there is no structured observability ownership within the repository. No CODEOWNERS file referencing observability configs. No per-package dashboards or alarms. No team attribution on monitoring assets. The `ObservabilityProvider` enum (DISABLED, AXIOM, DASHBOARD) in `sf-core/src/lib/observability/` defines providers for users' observability, not the tool's own monitoring. |
| **Gap** | No per-package observability ownership. Telemetry events are published but there's no evidence of who owns monitoring for which package, or what thresholds/alarms exist for the telemetry data. |
| **Recommendation** | Add a CODEOWNERS entry for observability-related files. Define ownership for telemetry data analysis — who monitors CLI error rates, adoption metrics, and release health? This is an organizational practice more than a code change. |
| **Evidence** | `packages/sf-core/src/lib/observability/index.js` (user-facing observability only), no CODEOWNERS file, no per-package alarm definitions |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging governance exists in this repository. The release infrastructure (S3 buckets, CloudFront distributions, IAM roles across 3 AWS accounts) is not defined in IaC, so no tags are applied or enforced from this repository. The tool generates tagged CloudFormation resources for users (Lambda functions, API Gateways, etc. with framework-applied tags), but the tool's own AWS resources have no visible tagging. No `default_tags`, `required-tags` Config rules, or Tag Policies are defined. |
| **Gap** | No tags found on resources; or only Name tags with no cost/ownership attribution. The 3 AWS accounts used by the release pipeline have S3 buckets, CloudFront distributions, and IAM roles with no tagging governance visible from this repository. Cost allocation and ownership attribution for release infrastructure is not trackable. |
| **Recommendation** | When release infrastructure is codified in IaC (per INF-Q10 recommendation), include consistent tagging: `Environment` (ci/canary/stable), `Project` (frameworks-core), `Owner` (team name), `CostCenter`. Apply `default_tags` in the Terraform/CDK provider block or CloudFormation stack-level tags. |
| **Evidence** | No AWS resource definitions with tags for the tool's own infrastructure. Release S3 buckets referenced by name only in CI scripts (`.github/workflows/release-framework.yml`). No `default_tags` or tag enforcement configuration. |

---

## Learning Materials

### Move to Modern DevOps (Triggered)

- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `package.json` | APP-Q1, APP-Q2, APP-Q6 | Root workspace config, ESM type, npm workspaces |
| `packages/serverless/package.json` | APP-Q1, DATA-Q1, DATA-Q2, INF-Q4 | AWS SDK v3 + v2 deps, framework version |
| `packages/sf-core/package.json` | APP-Q1, APP-Q2, APP-Q6, SEC-Q4 | CLI entry point deps, workspace aliases |
| `packages/engine/package.json` | APP-Q1, INF-Q4 | Engine deps with 22 AWS SDK clients |
| `packages/mcp/package.json` | APP-Q5, SEC-Q3 | MCP server deps, Express 5, MCP SDK |
| `packages/util/package.json` | APP-Q1, OPS-Q1 | Utility deps (ora, dockerode, chalk) |
| `packages/standards/package.json` | APP-Q1 | ESLint/Prettier standards |
| `binary-installer/go.mod` | APP-Q1 | Go 1.26.1, binary installer deps |
| `.github/workflows/ci-framework.yml` | INF-Q11, SEC-Q7, OPS-Q6 | CI pipeline: lint, unit tests, integration tests |
| `.github/workflows/ci-engine.yml` | INF-Q11 | Engine CI pipeline |
| `.github/workflows/ci-python.yml` | INF-Q11, OPS-Q6 | Python integration tests |
| `.github/workflows/ci-binary-installer.yml` | INF-Q11 | Go binary CI pipeline |
| `.github/workflows/release-framework.yml` | INF-Q10, INF-Q11, OPS-Q5, SEC-Q1, SEC-Q5 | Release pipeline: canary → stable → npm |
| `.github/workflows/release-binary-installer.yml` | INF-Q10, INF-Q11, OPS-Q5 | Binary release pipeline |
| `.github/dependabot.yml` | SEC-Q6, SEC-Q7 | 5-ecosystem dependency scanning config |
| `packages/serverless/lib/aws/v3/client-factory.js` | DATA-Q2, OPS-Q1, SEC-Q3 | Centralized AWS SDK v3 client factory |
| `packages/engine/src/lib/aws/` | DATA-Q2 | 22 service-specific AWS modules |
| `packages/sf-core/src/lib/router.js` | APP-Q2, APP-Q3, APP-Q6, OPS-Q3 | CLI router, runner dispatch, telemetry |
| `packages/sf-core/src/lib/auth/index.js` | SEC-Q3, SEC-Q4, SEC-Q5 | Authentication class (JWT, SSO, License Keys) |
| `packages/sf-core/src/lib/auth/aws-sso-login.js` | SEC-Q4 | AWS SSO integration |
| `packages/sf-core/src/lib/runners/core/support.js` | OPS-Q7 | Diagnostic report generator (715 lines) |
| `packages/sf-core/src/lib/observability/index.js` | OPS-Q1, OPS-Q8 | Observability provider enum |
| `packages/serverless/lib/plugins/observability/index.js` | OPS-Q1, OPS-Q8 | User-facing observability config |
| `packages/util/src/telemetry/index.js` | OPS-Q1, OPS-Q3 | Telemetry event publisher |
| `packages/mcp/src/tools-definition.js` | APP-Q5, Quick Agent Wins | 16+ MCP tool definitions |
| `packages/serverless/lib/plugins/aws/bedrock-agentcore/index.js` | Move to AI | Bedrock AgentCore plugin |
| `packages/sf-core/tests/integration/` | OPS-Q6 | 12 integration test directories |
| `packages/mcp/tests/e2e/` | OPS-Q6 | MCP end-to-end tests |
| `SECURITY.md` | SEC-Q1 | Security vulnerability reporting policy |
| `VERSIONING.md` | APP-Q5 | Versioning policy documentation |
| `packages/engine/src/lib/devMode/containers/` | SEC-Q6, SEC-Q7 | Dev-mode Dockerfiles (nodejs, python, proxy) |
| `docs/sf/` | Quick Agent Wins | Serverless Framework documentation |
