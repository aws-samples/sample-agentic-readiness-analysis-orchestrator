# Modernization Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | node-lambda |
| **Date** | 2026-04-30 |
| **TD Version** | 3g1iuew7esd4bia3 |
| **Repo Type** | application |
| **Service Archetype** | stateless-utility (auto-detected) |
| **Priority** | P2 |
| **Tags** | javascript, serverless, cli |
| **Context** | Node.js CLI for deploying AWS Lambda functions. |
| **Surface Flags** | has_persistent_data_store=false, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=false, has_multi_instance_deployment=false |
| **Overall Score** | **1.60 / 4.0** |

**Archetype Justification**: No database connections, no persistent state, no API surface, and no write endpoints detected. The tool is a CLI utility (`bin/node-lambda`) that executes commands (setup, run, package, deploy) against AWS APIs using the AWS SDK. All operations are stateless, command-driven, and run on developer machines or CI/CD environments. Classified as `stateless-utility`.

> **Note:** node-lambda is a CLI tool published as an npm package, not a deployed service. Many infrastructure and operations questions score low not because of poor engineering practices, but because the tool inherently has no infrastructure to manage, no API surface to secure, and no production workload to observe. The report frames this context throughout the findings.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.17 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.00 / 4.0 | 🟠 Needs Work |
| Data Platform Modernization (DATA) | 1.75 / 4.0 | 🟠 Needs Work |
| Security Baseline (SEC) | 1.83 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.25 / 4.0 | ❌ Not Present |
| **Overall** | **1.60 / 4.0** | **🟠 Needs Work** |

> **Scoring context:** 9 of 37 questions are recorded as "Not Evaluated (archetype-N/A)" because this stateless CLI tool does not expose the surfaces those questions assess (databases, HA, encryption at rest, SLOs, workflows, async messaging). These exclusions prevent false Score 1 findings and keep scores focused on genuinely applicable criteria.

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: IaC Coverage | 1 | No infrastructure-as-code exists. All infrastructure (if any) is created manually or doesn't exist. | Blocks reproducible environment setup and automated disaster recovery. Triggers Move to Modern DevOps pathway. |
| 2 | INF-Q11: CI/CD Automation | 2 | Build and test are automated via GitHub Actions, but no automated deployment pipeline (npm publish) exists. | Manual npm publish process is error-prone and creates release bottlenecks. Triggers Move to Modern DevOps pathway. |
| 3 | OPS-Q5: Deployment Strategy | 1 | No deployment strategy — npm package publishing is entirely manual with no staged rollout. | No ability to catch regressions before they affect all npm consumers. Supports Move to Modern DevOps pathway. |
| 4 | SEC-Q5: Secrets Management | 2 | Credentials passed via environment variables and CLI arguments with no secrets manager integration. | AWS credentials exposed in shell history and process listings; no rotation or audit trail. |
| 5 | OPS-Q6: Integration Testing | 2 | Unit tests with mocked AWS SDK calls exist, but no integration tests against live AWS services. | Mocked tests may miss real API contract changes, SDK behavior differences, or IAM permission issues. |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** INF-Q11 = 2 (CI/CD pipeline exists). GitHub Actions workflows (`.github/workflows/workflow.yml`) automate lint and test on push/PR.
- **What it enables:** An agent that triggers CI builds, checks test status across the Node.js 22.x/24.x matrix and OS variants (Ubuntu, macOS, Windows), and manages npm release workflows.
- **Additional steps:** Add an automated npm publish workflow to GitHub Actions (e.g., triggered by GitHub Releases or version tags). The agent can then orchestrate the full build → test → publish cycle.
- **Effort:** Medium (requires adding a publish workflow before the agent can manage releases).

### RAG-Based Knowledge Agent

- **Prerequisite:** Comprehensive README.md (270+ lines covering installation, usage, all 4 commands with full CLI option documentation, custom environment variables, S3 deployment, container image deployment, post-install scripts, contributing guide) and CHANGELOG.md (490+ lines of detailed release history from v0.8.0 through v1.3.0).
- **What it enables:** A knowledge agent powered by Amazon Bedrock that indexes the README, CHANGELOG, and example configuration files to answer developer questions about node-lambda usage, deployment options, troubleshooting, and version history.
- **Additional steps:** Index the documentation corpus (README.md, CHANGELOG.md, example files in `lib/`). Consider generating an OpenAPI-style specification of CLI commands to improve structured retrieval.
- **Effort:** Low (documentation already exists and is comprehensive; indexing is straightforward).

### Observability Agent

- **Prerequisite:** OPS-Q1 = 2 (aws-xray-sdk-core is a dependency and X-Ray segments are created during local Lambda execution in `lib/main.js`).
- **What it enables:** An agent that queries X-Ray traces from locally-run Lambda functions to help developers diagnose handler execution issues during local testing.
- **Additional steps:** The X-Ray integration is currently limited to local Lambda simulation. For broader value, the tool could emit structured logs (JSON format) during deploy operations to provide the agent with richer signal. Practical value is limited for a CLI tool.
- **Effort:** Medium (X-Ray SDK is present but the CLI context limits the observability surface available to an agent).

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 (modular structure with clear boundaries). Primary trigger requires APP-Q2 < 3. |
| 2 | Move to Containers | Not Triggered | — | — | Contextual guard: node-lambda is a CLI tool published to npm, not a deployed compute workload. There is no EC2/VM workload to containerize. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (no stored procedures). No commercial database engines detected. |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = Not Evaluated (no database exists). No databases to migrate. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = Not Evaluated (archetype-N/A). No data processing workloads exist in the repository. |
| 6 | Move to Modern DevOps | **Triggered** | **High** | **Medium** | INF-Q10 = 1 (no IaC), INF-Q11 = 2 (partial CI/CD). Supporting: OPS-Q5 = 1 (no deployment strategy), OPS-Q6 = 2 (limited testing). |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in context ("Node.js CLI for deploying AWS Lambda functions"). |

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

#### Current State

- **IaC Coverage (INF-Q10 = 1):** No infrastructure-as-code exists in the repository. There are no Terraform files, CloudFormation templates, CDK stacks, or any other IaC definitions. The tool itself has no infrastructure to define (it's a CLI), but the lack of IaC means there is no codified definition of any supporting infrastructure (e.g., CI/CD pipeline-as-code beyond GitHub Actions YAML).

- **CI/CD Automation (INF-Q11 = 2):** GitHub Actions provides automated build and test:
  - `workflow.yml` runs `npm ci` and `npm test` (lint + unit tests) on push and PR across Node.js 22.x and 24.x on Ubuntu, macOS, and Windows.
  - `codeql-analysis.yml` runs CodeQL SAST on push to master, PRs, and weekly schedule.
  - `dependabot.yml` monitors npm and GitHub Actions dependencies monthly.
  - **Missing:** No automated npm publish pipeline. Package releases to npm are manual.

- **Deployment Strategy (OPS-Q5 = 1):** No deployment strategy exists. The npm package is published manually with no staged rollout, no canary releases, and no automated rollback.

- **Integration Testing (OPS-Q6 = 2):** Comprehensive unit tests exist using Mocha + Chai + aws-sdk-mock. The `test/node-lambda.js` file spawns the CLI binary for integration-like testing. However, no tests run against live AWS services.

#### Recommendations

1. **Add automated npm publish workflow:** Create a GitHub Actions workflow triggered by GitHub Releases or version tags that automates `npm publish`. This is the highest-impact DevOps improvement for a CLI tool.

2. **Implement semantic release or conventional commits:** Adopt a tool like `semantic-release` or `release-please` to automate version bumps, changelog generation, and npm publishing based on commit conventions.

3. **Add staged rollout for npm:** Use npm's `--tag` feature to publish beta/next versions before promoting to `latest`. This provides a canary-like deployment strategy for npm packages.

4. **Expand test coverage with integration tests:** Add a CI stage that tests against real AWS services (using a dedicated test AWS account or LocalStack) to validate Lambda deployment, S3 upload, and event source configuration.

5. **Consider IaC for CI/CD infrastructure:** While the tool has no cloud infrastructure, the GitHub Actions workflows themselves could be managed more formally. Consider GitHub's reusable workflows for standardization.

#### Representative AWS Services

- **AWS CodeBuild** — For building and testing in AWS-native CI/CD (if migrating from GitHub Actions)
- **AWS CodePipeline** — For orchestrating build → test → publish pipelines
- **Amazon EventBridge** — For triggering automated workflows on release events

> **Preference note:** Per stated preferences, EKS and API Gateway recommendations are not applicable for this CLI tool context. The DevOps improvements focus on the npm package publishing lifecycle.

#### Learning Resources

- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute infrastructure is defined in this repository. node-lambda is a CLI tool published as an npm package — it runs on developer machines and CI/CD environments, not on managed compute. The tool *deploys* Lambda functions to AWS but does not define its own compute resources. No Terraform, CloudFormation, CDK, or any IaC files defining `aws_ecs_*`, `aws_eks_*`, `aws_lambda_*`, or `aws_instance` resources were found. |
| **Gap** | No managed compute — all compute is implicit (developer machines, GitHub Actions runners). This is architecturally expected for a CLI tool but means there is no cloud compute posture to evaluate. |
| **Recommendation** | For the CLI tool itself, no compute infrastructure change is needed — npm package distribution is the correct delivery model. If the tool were to evolve into a service (e.g., a deployment-as-a-service API), consider Lambda or ECS Fargate as the compute platform. |
| **Evidence** | `package.json` (npm package definition), `bin/node-lambda` (CLI entry point). No IaC files found in repository. |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy a database. node-lambda is a CLI tool with no persistent data store — no database connections, no ORM configurations, no database driver imports. The tool interacts with AWS Lambda, S3, CloudWatch Events, and CloudWatch Logs APIs for deployment operations but does not own or manage any database. INF-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `package.json` (no database driver dependencies), `lib/aws.js` (AWS SDK config for Lambda/S3/CloudWatch only). |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Workflow orchestration is not applicable by design — the CLI executes discrete commands (setup, run, package, deploy) sequentially. These are user-initiated CLI commands, not multi-step workflows requiring orchestration. No Step Functions, Temporal, or workflow engine is needed. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `bin/node-lambda` (CLI command definitions: setup, run, package, deploy), `lib/main.js` (command implementations). |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Synchronous CLI execution is the correct design — the user runs a command and waits for the result. No messaging or streaming infrastructure is needed. The tool does not consume or produce messages/events. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `bin/node-lambda` (synchronous CLI commands), `lib/main.js` (synchronous command execution with async/await for AWS API calls). |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or network infrastructure is defined in the repository. The CLI tool runs on developer machines and connects to AWS APIs over the internet. The tool *supports* VPC configuration for deployed Lambda functions via `--vpcSubnets` and `--vpcSecurityGroups` CLI options, but does not define its own network infrastructure. |
| **Gap** | No network security infrastructure defined. This is expected for a CLI tool — it has no deployed workload requiring network segmentation. |
| **Recommendation** | No network security changes needed for the CLI tool itself. The tool correctly passes VPC configuration through to Lambda functions it deploys. Consider documenting VPC best practices for Lambda deployments in the README. |
| **Evidence** | `bin/node-lambda` (VPC options: `--vpcSubnets`, `--vpcSecurityGroups`), `lib/main.js` (`_params` method constructs `VpcConfig`). No IaC files found. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, AppSync, ALB, CloudFront, or any API entry point is defined. node-lambda is a CLI tool with no API surface — it does not expose HTTP endpoints, gRPC services, or any network-accessible interface. |
| **Gap** | No API entry point exists. This is architecturally correct for a CLI tool — there is no API to protect with a gateway. |
| **Recommendation** | No API entry point needed for a CLI tool. If the tool were to evolve into a deployment service, implement API Gateway with throttling and authentication. |
| **Evidence** | `bin/node-lambda` (CLI interface only, no HTTP server), `package.json` (no express, fastify, or web framework dependencies). |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. The CLI tool has no deployed compute workload — it runs as a local process on developer machines or in CI/CD environments. There are no ASGs, ECS services, Lambda concurrency settings, or DynamoDB auto-scaling to configure. |
| **Gap** | No auto-scaling. This is expected for a CLI tool — there is no scalable workload to configure. |
| **Recommendation** | No auto-scaling needed for a CLI tool. No action required. |
| **Evidence** | No IaC files found. No compute resource definitions in the repository. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no persistent state to back up. node-lambda is a CLI tool that does not manage databases, S3 buckets, EBS volumes, or any data-at-rest resources as its own infrastructure. The tool creates S3 buckets for Lambda deployment artifacts (`lib/s3_deploy.js`), but these are created in the user's AWS account, not managed by the tool's infrastructure. INF-Q8 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `lib/s3_deploy.js` (S3 operations are deployment artifact uploads to user's account), `package.json` (no database dependencies). |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload requiring HA evaluation. node-lambda is a CLI tool that runs on developer machines — there is no production deployment requiring multi-AZ fault isolation. INF-Q9 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `package.json` (npm package, not a deployed service), `bin/node-lambda` (CLI entry point). No IaC or deployment manifests found. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No infrastructure-as-code files exist in the repository. No Terraform (`.tf`), CloudFormation (`.cfn.yaml`/`.cfn.json`), CDK (`cdk.json`), Helm (`Chart.yaml`), Kustomize (`kustomization.yaml`), or any other IaC files were found. The tool has no cloud infrastructure of its own to define — it is distributed as an npm package. |
| **Gap** | Zero IaC coverage. While the tool has no infrastructure to codify, the CI/CD pipeline configuration (GitHub Actions YAML) is the closest analog to "infrastructure" for this project, and it exists only as workflow files without reusable workflow patterns or environment-as-code definitions. |
| **Recommendation** | For a CLI tool, IaC coverage applies primarily to the CI/CD pipeline. Consider: (1) Define GitHub Actions workflows as reusable workflows for consistency. (2) If the tool needs any AWS resources for testing (e.g., a test Lambda function, test S3 bucket), define them in IaC (CloudFormation or CDK). |
| **Evidence** | Full directory scan: no `.tf`, `.cfn.*`, `cdk.json`, `Chart.yaml`, `kustomization.yaml`, or other IaC files found anywhere in the repository. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Build and test are automated via GitHub Actions. The `workflow.yml` runs `npm ci` and `npm test` (which executes lint via Standard.js + unit tests via Mocha) on every push and PR, across Node.js 22.x and 24.x on Ubuntu, macOS, and Windows. `codeql-analysis.yml` runs CodeQL SAST on push to master, PRs, and weekly schedule. `dependabot.yml` monitors npm and GitHub Actions dependency updates monthly. However, no automated deployment pipeline exists — `npm publish` is performed manually. |
| **Gap** | Deployment (npm publish) is manual. There is no automated release pipeline, no version bump automation, no changelog generation, and no staged rollout for npm package releases. Build automation exists but does not extend through the deploy stage. |
| **Recommendation** | Add an automated npm publish workflow to GitHub Actions triggered by version tags or GitHub Releases. Consider adopting `semantic-release` or `release-please` to automate version bumps, changelog updates, and npm publishing. Add `--provenance` flag to `npm publish` for supply chain security. |
| **Evidence** | `.github/workflows/workflow.yml` (build + test CI), `.github/workflows/codeql-analysis.yml` (SAST), `.github/dependabot.yml` (dependency updates). No publish/deploy workflow found. |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | JavaScript/Node.js with engine requirement `>= 22.0.0` (modern). CI tests against Node.js 22.x and 24.x. Key dependencies: `aws-sdk` v2.1377.0 (legacy — AWS SDK v3 is the current generation), `commander` v14.0.3 (modern CLI framework), `archiver` v7.0.1, `fs-extra` v11.3.4, `aws-xray-sdk-core` v3.12.0. Uses `@dotenvx/dotenvx` for environment variable management. Standard.js for linting. Dev dependencies include `mocha` v11.7.5, `chai` v6.2.2, `aws-sdk-mock` v6.2.2 (all modern). |
| **Gap** | AWS SDK v2 is the primary framework/SDK regression. AWS SDK v2 entered maintenance mode and SDK v3 (`@aws-sdk/*` modular packages) is the current generation with better tree-shaking, smaller bundle size, middleware stack, and first-class TypeScript support. The Node.js runtime version is modern (22+), but the SDK lag holds the score at 3. |
| **Recommendation** | Migrate from `aws-sdk` v2 to `@aws-sdk/*` v3 modular clients (`@aws-sdk/client-lambda`, `@aws-sdk/client-s3`, `@aws-sdk/client-cloudwatch-events`, `@aws-sdk/client-cloudwatch-logs`). This also requires migrating from `aws-sdk-mock` to `aws-sdk-client-mock` in tests. The migration is incremental — services can be migrated one at a time. |
| **Evidence** | `package.json` (`"aws-sdk": "^2.1377.0"`, `"engines": {"node": ">= 22.0.0"}`), `lib/aws.js` (`const aws = require('aws-sdk')`), `.github/workflows/workflow.yml` (tests Node.js 22.x, 24.x). |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Single deployable npm package with well-defined module boundaries. The `lib/` directory contains clearly separated modules: `main.js` (core Lambda class with CLI command implementations), `aws.js` (AWS SDK configuration), `s3_deploy.js` (S3 deployment logic), `s3_events.js` (S3 event source management), `schedule_events.js` (CloudWatch Events schedule management), `cloudwatch_logs.js` (CloudWatch Logs retention management). Each module has a single responsibility and clean interfaces. No circular dependencies observed — modules are imported in a clear hierarchy (`main.js` → `aws.js`, `s3_deploy.js`, `s3_events.js`, `schedule_events.js`, `cloudwatch_logs.js`). |
| **Gap** | Minor — while module boundaries are clear, the `main.js` file is large (~600 lines) and handles multiple concerns: CLI argument parsing, file operations, zip packaging, npm installation, and AWS Lambda deployment. The `_params` method alone is ~80 lines. This is a modular monolith that could benefit from further decomposition of `main.js` into smaller modules. |
| **Recommendation** | Consider extracting concerns from `main.js` into dedicated modules: (1) A `packager.js` for zip/archive operations, (2) A `installer.js` for npm/yarn install logic, (3) A `deployer.js` for AWS Lambda upload logic. This would improve testability and maintainability while keeping the single npm package distribution model. |
| **Evidence** | `lib/main.js` (core module, ~600 lines), `lib/aws.js` (AWS config, ~35 lines), `lib/s3_deploy.js` (S3 deploy, ~130 lines), `lib/s3_events.js` (~120 lines), `lib/schedule_events.js` (~100 lines), `lib/cloudwatch_logs.js` (~55 lines). |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Synchronous CLI command execution is the correct design — the user runs `node-lambda deploy` and waits for the result. There is no inter-service communication to evaluate for async vs sync patterns. AWS SDK calls use async/await internally but this is implementation detail, not architectural communication pattern. Async communication is not needed and would add complexity without benefit. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `bin/node-lambda` (synchronous CLI command dispatch), `lib/main.js` (async/await for AWS API calls within synchronous command execution). |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. No operations require async job infrastructure — the CLI operations (setup, run, package, deploy) complete in seconds to minutes and are inherently interactive. The zip operation may take "up to 30 seconds" (per `lib/main.js` console output) and deployments may take longer, but these are blocking CLI operations where the user expects to wait for completion. There is no need for status polling or callback infrastructure. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `lib/main.js` (`_zip` method: "Zipping repo. This might take up to 30 seconds"), `lib/main.js` (`deploy` method: sequential archive → upload → configure). |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning exists because the tool has no API surface. node-lambda is a CLI tool — it does not expose HTTP endpoints. The npm package has semantic versioning (`"version": "1.3.0"` in `package.json`) and a comprehensive `CHANGELOG.md` documenting changes from v0.8.0 through v1.3.0, but this is package versioning, not API versioning. |
| **Gap** | No API versioning strategy. This is architecturally expected — there are no API endpoints to version. The CLI interface itself does not have a formal versioning contract for command-line options (options can change between npm versions without a deprecation period). |
| **Recommendation** | For the CLI tool, consider documenting a CLI option stability policy (e.g., which options are stable vs experimental). If the tool exposes a programmatic Node.js API (`require('node-lambda')`), consider versioning the module's public API surface. The `index.js` file currently re-exports the Lambda class — this is an implicit public API. |
| **Evidence** | `package.json` (`"version": "1.3.0"`), `CHANGELOG.md` (release history), `bin/node-lambda` (CLI options), `index.js` (programmatic API). |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No service discovery mechanism exists. The CLI tool connects to AWS service endpoints implicitly through the AWS SDK, which resolves regional endpoints automatically (e.g., `lambda.us-east-1.amazonaws.com`). The tool accepts custom endpoints via `--endpoint` CLI option (e.g., for LocalStack testing), and AWS region via `--region`. Service endpoints are not hard-coded — they are resolved by the AWS SDK based on region configuration. |
| **Gap** | No service discovery. This is expected for a CLI tool — it communicates only with AWS APIs, which have their own endpoint resolution mechanism built into the SDK. |
| **Recommendation** | No service discovery needed. AWS SDK's built-in endpoint resolution is the correct pattern for AWS API access from a CLI tool. The `--endpoint` option provides flexibility for testing against local AWS emulators. |
| **Evidence** | `lib/aws.js` (AWS config with `region` and optional `endpoint`), `bin/node-lambda` (`--endpoint` option for custom endpoints, `--region` option). |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The tool uses S3 for deploying Lambda zip files (`lib/s3_deploy.js`), but this is deployment artifact storage — not unstructured data management. The S3 operations are limited to `createBucket` and `putObject` for uploading deployment packages. No document parsing, Textract integration, data lake patterns, or unstructured data management capabilities exist. |
| **Gap** | No unstructured data storage or parsing capability. This is expected for a CLI deployment tool — it has no data management responsibilities. |
| **Recommendation** | No unstructured data management needed for a CLI tool. The S3 usage for deployment artifacts is appropriate. |
| **Evidence** | `lib/s3_deploy.js` (`_createBucket`, `_putObject`, `putPackage` methods — deployment artifact upload only), `package.json` (no Textract, Tika, or document parsing dependencies). |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database access exists in this codebase. AWS SDK calls in `lib/aws.js` are for Lambda, S3, CloudWatch Events, and CloudWatch Logs APIs — not data access. There is no repository pattern, no DAO layer, no ORM, and no database queries. The tool does not read or write application data — it only interacts with AWS APIs for Lambda deployment operations. |
| **Gap** | No data access layer exists because the tool has no data storage needs. Not a gap for a CLI deployment tool. |
| **Recommendation** | No data access layer needed. No action required. |
| **Evidence** | `lib/aws.js` (AWS SDK config only), `lib/main.js` (Lambda API calls for deployment), `lib/s3_deploy.js` (S3 for artifacts), `package.json` (no database driver dependencies). |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database definitions exist in this repository. No IaC files define database resources, no database engine versions are specified, and no database connection strings are present. The default Lambda runtime in `bin/node-lambda` is set to `nodejs16.x` which is past EOL — but this is the Lambda runtime for functions being deployed, not a database engine. The `.env.example` sets `AWS_RUNTIME=nodejs24.x`. |
| **Gap** | No database engine version management because no databases exist. The stale default runtime (`nodejs16.x` in `bin/node-lambda`) is a separate concern addressed under APP-Q1. |
| **Recommendation** | No database engine version management needed. Consider updating the default `AWS_RUNTIME` in `bin/node-lambda` from `nodejs16.x` to `nodejs22.x` or `nodejs24.x` to match the `.env.example` template and current AWS Lambda supported runtimes. |
| **Evidence** | `bin/node-lambda` (`AWS_RUNTIME` default is `'nodejs16.x'`), `lib/.env.example` (`AWS_RUNTIME=nodejs24.x`). No database resources in the repository. |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, proprietary SQL, or any database interaction exists. All business logic resides in the application layer (JavaScript modules in `lib/`). The tool does not interact with any database — it communicates exclusively with AWS APIs (Lambda, S3, CloudWatch Events, CloudWatch Logs) using the AWS SDK. This is the ideal state: zero database coupling. |
| **Gap** | None. All business logic is in the application layer. |
| **Recommendation** | No action needed. Maintain the current pattern of keeping all logic in the application layer. |
| **Evidence** | `lib/main.js` (all business logic in JS), `lib/s3_deploy.js`, `lib/s3_events.js`, `lib/schedule_events.js`, `lib/cloudwatch_logs.js` (all AWS API-only interactions). No `.sql` files, no `CREATE PROCEDURE`/`CREATE TRIGGER`/`CREATE FUNCTION` patterns found. |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or audit logging configuration exists in the repository. No IaC defines `aws_cloudtrail` resources. The CLI tool itself produces console output during operations (e.g., "Uploading zip file to AWS Lambda...") but this is operational logging to stdout, not immutable audit logging. |
| **Gap** | No audit logging infrastructure. For a CLI tool, CloudTrail would typically be configured in the user's AWS account (outside this tool's scope), but the tool could emit structured log output to support audit trail construction. |
| **Recommendation** | Consider adding structured JSON logging to the CLI's deploy operations so that downstream log aggregation systems can capture deployment audit trails. For the tool's own npm publishing, GitHub Actions workflow logs serve as an audit trail. |
| **Evidence** | No IaC files found. `lib/main.js` uses `console.log` for operational output (unstructured text). |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no database, S3 bucket, EBS volume, or similar managed storage defined in IaC. The tool creates S3 buckets in the user's AWS account for deployment artifacts, but those are user-managed resources. The tool supports KMS key configuration for deployed Lambda functions via `--kmsKeyArn`, showing awareness of encryption. SEC-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `bin/node-lambda` (`--kmsKeyArn` option), `lib/main.js` (`KMSKeyArn: program.kmsKeyArn` in params). No IaC defining data-at-rest resources. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API endpoints exist to authenticate. The CLI tool accepts AWS credentials via environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`), CLI arguments (`--accessKey`, `--secretKey`), AWS profiles (`--profile`), and session tokens (`--sessionToken`) for authenticating to AWS APIs. However, the tool itself has no API surface requiring authentication. |
| **Gap** | No API authentication because no API exists. This is architecturally correct for a CLI tool. |
| **Recommendation** | No API authentication needed. The tool's support for multiple AWS credential methods (environment variables, CLI args, profiles, session tokens) is appropriate. Consider adding support for AWS SSO/Identity Center credentials via `aws sso login` integration for improved security posture. |
| **Evidence** | `bin/node-lambda` (`--accessKey`, `--secretKey`, `--profile`, `--sessionToken` options), `lib/aws.js` (`SharedIniFileCredentials` for profile-based auth). |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The tool uses AWS IAM credentials for authentication to AWS services. It supports multiple credential methods: (1) Direct access key and secret key via CLI args or environment variables, (2) AWS named profiles via `--profile` (uses `SharedIniFileCredentials`), (3) Session tokens for temporary credentials. Profile-based authentication can federate with external IdPs when configured in the AWS CLI (`~/.aws/config`). However, the tool does not directly integrate with Cognito, Okta, or any centralized IdP — it delegates to the AWS SDK's credential chain. |
| **Gap** | No direct centralized IdP integration. The tool relies on the AWS SDK's credential resolution, which can work with SSO/Identity Center when configured externally, but the tool doesn't have first-class SSO support. |
| **Recommendation** | Consider adding first-class AWS IAM Identity Center (SSO) support. The AWS SDK v3 migration (recommended in APP-Q1) would bring `@aws-sdk/credential-provider-sso` as a built-in credential resolver, automatically supporting `aws sso login` sessions. |
| **Evidence** | `lib/aws.js` (`SharedIniFileCredentials`, `accessKeyId`, `secretAccessKey`, `sessionToken`), `bin/node-lambda` (credential CLI options). |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No plaintext real credentials are committed to version control. The `.env.example` file contains placeholders (`AWS_ACCESS_KEY_ID=your_key`, `AWS_SECRET_ACCESS_KEY=your_secret`) and `deploy.env.example` contains `SECRET_VARIABLE=mysecretval` — both are template files with example values. The `.gitignore` correctly excludes `.env`, `deploy.env`, and `event.json`. However, the tool accepts credentials via environment variables and CLI arguments (`--accessKey`, `--secretKey`) without any secrets manager integration. There is no support for AWS Secrets Manager, HashiCorp Vault, or encrypted parameter store. Credentials passed via CLI arguments may appear in shell history and process listings. |
| **Gap** | Credentials are managed exclusively through environment variables and CLI arguments with no secrets manager integration, no rotation capability, and no encryption. CLI argument-based credential passing (`--accessKey`, `--secretKey`) exposes secrets in shell history and `ps` output. |
| **Recommendation** | (1) Deprecate `--accessKey` and `--secretKey` CLI arguments in favor of AWS profiles and environment variables (reduces shell history exposure). (2) Add documentation recommending AWS IAM Identity Center for credential management. (3) Consider integrating with AWS Secrets Manager for deploy.env secrets (the `CONFIG_FILE` feature could pull from Secrets Manager instead of local files). |
| **Evidence** | `lib/.env.example` (placeholder credentials), `lib/deploy.env.example` (`SECRET_VARIABLE=mysecretval`), `.gitignore` (excludes `.env`, `deploy.env`), `bin/node-lambda` (`--accessKey`, `--secretKey` CLI args), `lib/aws.js` (credential config). |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No compute resources to harden — the tool runs on developer machines and CI/CD runners. Dependabot is configured (`.github/dependabot.yml`) for monthly npm dependency updates and GitHub Actions updates, providing automated dependency patching. However, there is no SSM Patch Manager, no hardened AMI usage, no AWS Inspector configuration — because there are no compute resources to apply them to. The CI matrix tests on the latest Ubuntu, macOS, and Windows runners. |
| **Gap** | No compute hardening because no compute exists to harden. Dependabot provides dependency-level patching on a monthly cadence. The monthly interval means up to 30 days of exposure to newly disclosed vulnerabilities before Dependabot creates a PR. |
| **Recommendation** | (1) Enable Dependabot security updates (separate from version updates) for immediate PRs on security advisories. (2) Consider adding `npm audit` to the CI pipeline for real-time vulnerability detection on every build. (3) Add a `package-lock.json` integrity check to the CI pipeline. |
| **Evidence** | `.github/dependabot.yml` (monthly npm + GitHub Actions updates), `.github/workflows/workflow.yml` (CI on Ubuntu, macOS, Windows). No compute infrastructure to harden. |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | CodeQL SAST is configured in GitHub Actions (`codeql-analysis.yml`) and runs on push to master, PRs to master, and on a weekly schedule (Sunday 21:20 UTC). CodeQL analyzes JavaScript source code for security vulnerabilities. Dependabot (`.github/dependabot.yml`) monitors npm dependencies and GitHub Actions for updates on a monthly cadence. Standard.js linting runs as part of `npm test` in the CI pipeline. No container scanning (no containers exist). |
| **Gap** | No blocking security gate — CodeQL and Dependabot produce findings and PRs but there is no evidence of required status checks that block merges on critical security findings. No `npm audit` step in the CI pipeline for real-time dependency vulnerability detection. |
| **Recommendation** | (1) Configure CodeQL as a required status check on the `master` branch to block merges with critical security findings. (2) Add `npm audit --audit-level=critical` to the CI pipeline as a blocking step. (3) Enable Dependabot security advisories for immediate alerts (vs monthly version updates). |
| **Evidence** | `.github/workflows/codeql-analysis.yml` (CodeQL SAST on push/PR/schedule), `.github/dependabot.yml` (monthly npm + GitHub Actions updates), `.github/workflows/workflow.yml` (`npm test` includes Standard.js lint). |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | `aws-xray-sdk-core` v3.12.0 is a production dependency and is imported in `lib/main.js`. The SDK is used to create an X-Ray segment (`new AWSXRay.Segment('annotations')`) within a continuation-local-storage namespace when running Lambda handlers locally via the `run` command. This simulates the Lambda execution environment's tracing context for local testing. However, this is not distributed tracing of the CLI tool itself — it's tracing the Lambda handler that the tool executes locally. No trace propagation across service boundaries exists (the CLI is a single process). |
| **Gap** | X-Ray SDK is present but used only for local Lambda handler simulation, not for tracing the CLI's own operations (deploy, package). No cross-service trace propagation (not applicable for a single-process CLI). |
| **Recommendation** | For the CLI tool itself, distributed tracing has limited value since it's a single-process tool. However, consider adding X-Ray tracing to AWS SDK calls during deploy operations so that deployment traces appear in the user's X-Ray console, correlating CLI actions with AWS-side processing. |
| **Evidence** | `package.json` (`"aws-xray-sdk-core": "^3.12.0"`, `"continuation-local-storage": "^3.2.1"`), `lib/main.js` (`const AWSXRay = require('aws-xray-sdk-core')`, `nameSpace.set('segment', new AWSXRay.Segment('annotations'))`). |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no user-facing surface for which SLOs are meaningful. node-lambda is a CLI tool — it has no API surface and no persistent data store. SLOs (availability, latency, error rates) apply to services with user-facing endpoints, not to CLI tools that run on-demand on developer machines. OPS-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `bin/node-lambda` (CLI interface), `package.json` (npm package, not a service). |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom metrics are published. The CLI produces console output (`console.log`) for operational progress (e.g., "Moving files to temporary directory", "Zipping repo", "Uploading zip file to AWS Lambda") but does not emit structured metrics to CloudWatch or any metrics system. No `cloudwatch.put_metric_data` calls, no custom metric publishing, no business outcome tracking. |
| **Gap** | No metrics of any kind — no deployment success/failure rates, no deployment duration tracking, no package size metrics. For an open-source CLI tool, this limits the ability to understand usage patterns and identify performance regressions. |
| **Recommendation** | Consider adding optional telemetry (with user consent) to track deployment metrics: deployment duration, package size, target region, success/failure rate. Alternatively, emit deployment metrics to the user's CloudWatch (opt-in) so they can monitor their deployment pipeline health. |
| **Evidence** | `lib/main.js` (uses `console.log` throughout, no CloudWatch metrics SDK calls). |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting is configured. The CLI tool has no monitoring infrastructure — it runs on-demand and exits. No CloudWatch alarms, no error rate monitoring, no anomaly detection. |
| **Gap** | No alerting or anomaly detection. For a CLI tool, traditional alerting doesn't apply. However, the CI pipeline could benefit from alerting on test failures or dependency vulnerabilities. |
| **Recommendation** | Configure GitHub Actions notifications (Slack/email) for CI build failures. Consider adding GitHub Actions alerts for Dependabot security advisories. |
| **Evidence** | No CloudWatch alarms, no alerting configuration found in the repository. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy exists for the npm package. There is no automated npm publish pipeline, no staged rollout (beta/next tags), no canary releases, and no rollback mechanism. The `npm publish` process is entirely manual. The tool supports deploying Lambda functions with version aliases (`--lambdaVersion`) and multi-region deployment (`--region us-east-1,us-west-2`), but this is for the Lambda functions being deployed, not for the tool itself. |
| **Gap** | No deployment strategy for the npm package. Manual publishing with no staged rollout means a bad release reaches all users immediately. npm's `unpublish` has time limits (72 hours) and is not a reliable rollback mechanism. |
| **Recommendation** | (1) Implement automated npm publishing via GitHub Actions triggered by version tags. (2) Use npm's dist-tag system to publish pre-releases (`npm publish --tag next`) before promoting to latest. (3) Add post-publish smoke tests that install the published package and run basic commands. |
| **Evidence** | `package.json` (`"version": "1.3.0"`), `.github/workflows/` (no publish workflow). `bin/node-lambda` (`--lambdaVersion` for Lambda aliases — applies to deployed functions, not the tool). |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Comprehensive unit tests exist in `test/` using Mocha + Chai + aws-sdk-mock: `test/main.js` (1717 lines — extensive tests for the Lambda class), `test/node-lambda.js` (398 lines — spawns the CLI binary for integration-like testing), `test/s3_deploy.js` (198 lines), `test/s3_events.js`, `test/schedule_events.js`, `test/cloudwatch_logs.js`. Tests mock AWS SDK calls using `aws-sdk-mock` to test deploy, package, and event source management logic without calling real AWS APIs. `test/node-lambda.js` provides integration-like tests that spawn the CLI binary and verify stdout/stderr output and exit codes. However, no tests run against live AWS services. |
| **Gap** | Tests rely on mocked AWS SDK — they validate the tool's logic but not actual AWS API interactions. Mocks may drift from real API behavior. No integration tests against real AWS Lambda, S3, or CloudWatch APIs (even with LocalStack). |
| **Recommendation** | (1) Add a CI stage that runs integration tests against LocalStack for S3, Lambda, and CloudWatch operations. (2) Consider a scheduled integration test against a real AWS account (weekly) to catch API contract changes. (3) Add contract tests that verify mock behavior matches real API responses. |
| **Evidence** | `test/main.js` (1717 lines, mocked unit tests), `test/node-lambda.js` (CLI binary tests), `test/s3_deploy.js`, `.github/workflows/workflow.yml` (`npm test` runs in CI). |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks or incident response automation exist. No Systems Manager Automation documents, no Lambda-based remediation, no incident response workflows. For a CLI tool, "incidents" are typically user-facing issues (broken deployments, packaging failures) rather than production service incidents. |
| **Gap** | No incident response framework. For an open-source CLI tool, this manifests as no structured triage process for GitHub issues, no automated diagnostics, and no self-healing patterns. |
| **Recommendation** | (1) Create GitHub issue templates for common problems (deployment failures, packaging errors). (2) Add a `--debug` or `--verbose` flag that produces diagnostic output useful for bug reports. (3) Consider a `node-lambda doctor` command that validates environment setup (AWS credentials, Node.js version, required permissions). |
| **Evidence** | No runbook files, no incident response configuration found in the repository. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership exists. No CODEOWNERS file referencing observability configs, no per-service dashboards, no named alarm owners, no SLO definitions with team attribution. The repository has a single maintainer (`"author": "motdotla"` in `package.json`) but no formalized observability ownership structure. |
| **Gap** | No observability ownership framework. For an open-source CLI tool, this is less critical than for a production service, but contributor observability (CI health, dependency health, npm download trends) would improve maintainability. |
| **Recommendation** | (1) Add a CODEOWNERS file defining ownership of CI/CD workflows and security configurations. (2) Add GitHub Actions status badges to README for CI, CodeQL, and dependency status. The README already has a Node CI badge. |
| **Evidence** | `package.json` (`"author": "motdotla"`), `README.md` (has Node CI badge). No CODEOWNERS file, no observability dashboards. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The CLI supports a `--tags` option (`-A`) for tagging deployed Lambda functions with key-value pairs (e.g., `tagname1=tagvalue1,tagname2=tagvalue2`). The `_updateTags` method in `lib/main.js` applies tags to Lambda functions using `tagResource` and `untagResource` APIs. However, there is no tagging governance for the tool's own resources (it has no resources) and no enforcement of required tags on deployed Lambda functions. |
| **Gap** | No tagging governance. The tool supports tags as pass-through but does not enforce required tags, validate tag formats, or default to any standard tags (environment, owner, cost-center). |
| **Recommendation** | (1) Consider adding default tags to deployed Lambda functions (e.g., `deployed-by=node-lambda`, `deployed-at=<timestamp>`). (2) Add optional tag validation (e.g., `--requiredTags environment,owner` that fails deployment if specified tags are missing). (3) Document tagging best practices for Lambda deployments in the README. |
| **Evidence** | `bin/node-lambda` (`--tags` option), `lib/main.js` (`_params` method parses tags, `_updateTags` method applies them). |

---

## Learning Materials

### Move to Modern DevOps (Triggered)

- [Move to Modern DevOps — AWS Skill Builder Learning Plan](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

> No other pathways were triggered. Refer to [AWS Skill Builder](https://skillbuilder.aws/) for general cloud architecture training.

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `package.json` | INF-Q1, INF-Q2, INF-Q6, INF-Q7, INF-Q8, INF-Q9, APP-Q1, APP-Q2, APP-Q5, DATA-Q1, DATA-Q2, OPS-Q1, OPS-Q2, OPS-Q3, OPS-Q5, OPS-Q8 | npm package definition: name, version, dependencies, engines, scripts |
| `bin/node-lambda` | INF-Q1, INF-Q3, INF-Q4, INF-Q5, INF-Q6, INF-Q9, APP-Q3, APP-Q5, APP-Q6, DATA-Q3, SEC-Q3, SEC-Q4, SEC-Q5, OPS-Q2, OPS-Q5, OPS-Q9 | CLI entry point: commander options, environment variable defaults, command definitions |
| `lib/main.js` | INF-Q3, INF-Q4, INF-Q5, APP-Q2, APP-Q3, APP-Q4, DATA-Q4, OPS-Q1, OPS-Q3, OPS-Q9 | Core Lambda class: setup, run, package, deploy implementations (~600 lines) |
| `lib/aws.js` | INF-Q2, APP-Q6, SEC-Q3, SEC-Q4 | AWS SDK configuration: region, credentials, proxy, endpoint |
| `lib/s3_deploy.js` | INF-Q8, APP-Q2, DATA-Q1, DATA-Q4 | S3 deployment: bucket creation, zip upload for Lambda deployments |
| `lib/s3_events.js` | APP-Q2, DATA-Q4 | S3 event source management: notification configuration for Lambda triggers |
| `lib/schedule_events.js` | APP-Q2, DATA-Q4 | CloudWatch Events schedule management: rule creation, target configuration |
| `lib/cloudwatch_logs.js` | APP-Q2, DATA-Q4 | CloudWatch Logs retention: log group creation, retention policy |
| `.github/workflows/workflow.yml` | INF-Q11, SEC-Q6, SEC-Q7, OPS-Q5, OPS-Q6 | GitHub Actions CI: lint + test on Node.js 22.x/24.x across Ubuntu/macOS/Windows |
| `.github/workflows/codeql-analysis.yml` | INF-Q11, SEC-Q7 | CodeQL SAST: JavaScript analysis on push/PR/schedule |
| `.github/dependabot.yml` | INF-Q11, SEC-Q6, SEC-Q7 | Dependabot: monthly npm + GitHub Actions dependency updates |
| `lib/.env.example` | SEC-Q5 | Environment variable template with placeholder AWS credentials |
| `lib/deploy.env.example` | SEC-Q5 | Deploy environment template with example secret variable |
| `.gitignore` | SEC-Q5 | Excludes `.env`, `deploy.env`, `event.json` from version control |
| `index.js` | APP-Q5 | Programmatic API entry point (re-exports Lambda handler) |
| `README.md` | OPS-Q8, Quick Agent Wins | Comprehensive documentation: installation, usage, all CLI commands |
| `CHANGELOG.md` | APP-Q5, Quick Agent Wins | Release history from v0.8.0 through v1.3.0 |
| `test/main.js` | OPS-Q6 | Unit tests: 1717 lines, comprehensive mocked testing of Lambda class |
| `test/node-lambda.js` | OPS-Q6 | CLI binary tests: 398 lines, spawns CLI and verifies output/exit codes |
| `test/s3_deploy.js` | OPS-Q6 | S3Deploy unit tests: 198 lines with mocked S3 API |
