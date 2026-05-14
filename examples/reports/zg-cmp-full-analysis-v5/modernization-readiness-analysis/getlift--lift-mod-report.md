# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | serverless-lift |
| **Date** | 2025-07-16 |
| **TD Version** | modernization-readiness-analysis |
| **Repo Type** | application |
| **Service Archetype** | stateless-utility (auto-detected) |
| **Priority** | P2 |
| **Tags** | typescript, serverless, iac |
| **Context** | Serverless Framework plugin providing higher-level AWS constructs. |
| **Surface Flags** | has_persistent_data_store=false, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=false, has_multi_instance_deployment=false |
| **Overall Score** | **1.6 / 4.0** |

**Archetype Justification**: This is a Serverless Framework plugin (NPM package) that generates CloudFormation resources via AWS CDK constructs at build time. It has no database connections, no API endpoints, no message queue consumers, and no persistent state of its own. It does not run as a deployed service — it is published to NPM and executed as part of the `serverless deploy` command. Classified as `stateless-utility` as the closest match.

> **Note:** While `repo_type` is specified as `application`, this repository is functionally an NPM library/plugin. Many INF, SEC, and OPS questions evaluate surfaces this repository does not expose (compute, databases, networking, deployed workloads). The low overall score reflects that reality — the questions are designed for deployed applications, and many produce Score 1 when there is no deployed infrastructure to evaluate. The surface-flag gates (Step 1.6) prevent false Score 1 on the most clearly inapplicable questions, but the remaining infrastructure and operations questions still score against the absence of deployment infrastructure.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.3 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.5 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 1.8 / 4.0 | 🟠 Needs Work |
| Security Baseline (SEC) | 1.2 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.1 / 4.0 | ❌ Not Present |
| **Overall** | **1.6 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | SEC-Q7: Application Security Pipeline | 1 | No SAST, DAST, or dependency vulnerability scanning in CI/CD pipeline | Vulnerabilities in dependencies (lodash, aws-cdk-lib, stripe) could reach consumers undetected. Critical for a widely-used OSS library. |
| 2 | INF-Q11: CI/CD Automation | 3 | CI pipeline covers tests, lint, and type checking, but the release pipeline is a direct publish with no staged rollout or automated rollback | A broken release goes directly to all NPM consumers with no canary or staged validation. |
| 3 | SEC-Q5: Secrets Management | 2 | StripeProvider uses environment variables (STRIPE_API_KEY) without rotation or managed secrets store | While no plaintext secrets exist in source, the env var pattern lacks rotation and audit trails. |
| 4 | OPS-Q6: Integration Testing | 2 | Unit tests exist (13+ files) but no integration tests against live AWS infrastructure | CDK construct correctness depends on CloudFormation synthesis behavior — snapshot tests catch regressions but miss AWS-side compatibility issues. |
| 5 | APP-Q6: Service Discovery | 1 | No service discovery mechanism | As a library/plugin, service discovery is architecturally unnecessary. Low practical impact but scores against the rubric. |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** INF-Q11 = 3 (CI/CD pipeline exists with GitHub Actions — `ci.yml` runs unit tests, lint, type checking; `release.yml` handles npm publish).
- **What it enables:** A DevOps agent that triggers CI builds, checks test status, and manages release workflows. Could automate version bumps, changelog generation, and release coordination.
- **Additional steps:** Add a GitHub Actions API token for agent access. Consider adding a `workflow_dispatch` trigger on `release.yml` for agent-initiated releases.
- **Effort:** Low — existing GitHub Actions pipeline provides the automation surface.

### RAG-Based Knowledge Agent

- **Prerequisite:** Extensive documentation exists in the repository — `README.md` (194 lines), `docs/` directory with 11 files covering all constructs (queue.md, storage.md, webhook.md, vpc.md, database-dynamodb-single-table.md, single-page-app.md, static-website.md, server-side-website.md, comparison.md, configuration.md, permissions.md), and `CONTRIBUTING.md`.
- **What it enables:** A RAG-based knowledge agent that indexes all Lift documentation and answers developer questions about construct configuration, migration from raw CloudFormation, and troubleshooting. Useful for onboarding contributors and supporting end users.
- **Additional steps:** Index documentation into a vector store (Amazon Bedrock Knowledge Base or OpenSearch with vector engine). Consider adding inline code comments to the corpus for deeper technical answers.
- **Effort:** Medium — documentation corpus exists but needs indexing and retrieval chain setup.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 (modular architecture with well-defined boundaries). Primary trigger not met. |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 1 but no EC2/VM-based compute exists to containerize. This is a library published to NPM, not a deployed service. Contextual guard prevents trigger. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (no stored procedures or proprietary SQL). No commercial DB engines detected. |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 is Not Evaluated (no persistent data store). No databases to migrate. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 is Not Evaluated. No data processing workloads exist. Contextual guard prevents trigger. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (no IaC for repo infrastructure), OPS-Q5 = 1 (direct-to-production publish), OPS-Q6 = 2 (no integration tests). |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in context ("Serverless Framework plugin providing higher-level AWS constructs."). |

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

#### Current State

- **IaC Coverage (INF-Q10 = 1):** The repository has no infrastructure-as-code for its own infrastructure. As a library published to NPM, it does not provision AWS resources for itself. However, the CI/CD pipeline configuration itself is the "infrastructure" for this repo type, and it lacks several modern DevOps practices.
- **CI/CD Automation (INF-Q11 = 3):** GitHub Actions CI pipeline (`.github/workflows/ci.yml`) runs unit tests across Node.js 20/22/24, lint checks, and TypeScript type checking. The release pipeline (`.github/workflows/release.yml`) publishes to NPM on GitHub release events using OIDC for trusted publishing. However, the release is a direct publish with no staged validation.
- **Deployment Strategy (OPS-Q5 = 1):** The library publishes directly to NPM on every GitHub release. No canary, staged, or gradual rollout mechanism exists. A broken release immediately affects all consumers who install or update.
- **Integration Testing (OPS-Q6 = 2):** 13+ unit test files exist covering all constructs, but no integration tests validate CDK synthesis against actual CloudFormation behavior or AWS service compatibility.

#### Recommendations

1. **Add dependency vulnerability scanning to CI/CD:**
   - Add `npm audit --audit-level=high` step to `ci.yml`.
   - Enable GitHub Dependabot (`dependabot.yml`) for automated dependency update PRs.
   - Consider adding Snyk or CodeGuru for SAST analysis.

2. **Implement staged release strategy:**
   - Publish to a `@next` or `@beta` NPM dist-tag first for pre-release validation.
   - Add a manual approval gate before promoting to `@latest`.
   - Consider `npm pack` + dry-run validation in CI before publish.

3. **Add integration testing:**
   - Implement CDK synthesis integration tests that validate generated CloudFormation templates against AWS CloudFormation Linter (`cfn-lint`).
   - Consider adding contract tests that deploy constructs to a sandbox AWS account and validate resource creation.

4. **Modernize Node.js version pinning:**
   - Update `.nvmrc` from v16.6.2 (EOL) to Node.js 20 LTS or 22 LTS to align with CI matrix.

**Representative AWS Services:** CodeBuild, CodePipeline, CloudFormation Linter, AWS CDK Assertions Library.

**Learning Resources:**
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute infrastructure is defined in this repository. The repo is a Serverless Framework plugin (NPM library) that generates CloudFormation resources for end users via AWS CDK constructs. It does not provision or deploy compute resources (EC2, ECS, EKS, Lambda, Fargate) for itself. The `package.json` `main` field points to `dist/src/plugin.js` — a Node.js module consumed by the Serverless Framework at build time, not a deployed workload. |
| **Gap** | No compute infrastructure exists to evaluate. |
| **Recommendation** | As a library/plugin, this repository does not require its own compute infrastructure. No action needed for managed compute. The Score 1 reflects absence rather than a genuine gap for this repo type. |
| **Evidence** | `package.json` (main: "dist/src/plugin.js"), absence of Terraform/CloudFormation/CDK app files, absence of Dockerfile |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy a database. INF-Q2 does not apply. The repository generates DynamoDB constructs (`src/constructs/aws/DatabaseDynamoDBSingleTable.ts`) for end users but does not itself deploy or connect to any database. `has_persistent_data_store=false`. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `package.json` (no database driver dependencies), `src/constructs/aws/DatabaseDynamoDBSingleTable.ts` (generates constructs for users) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Workflow orchestration is not applicable by design — no multi-step workflows exist for a build-time library plugin. The plugin generates CloudFormation resources synchronously during `serverless deploy` with no long-running orchestration needs. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/plugin.ts` (synchronous construct loading and CloudFormation generation), absence of Step Functions, Temporal, or workflow definitions |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. This is a build-time library with no runtime communication pattern. The plugin generates SQS Queue and EventBridge constructs (`src/constructs/aws/Queue.ts`, `src/constructs/aws/Webhook.ts`) for end users but does not itself consume or produce messages at runtime. Synchronous execution is the correct design for a build-time plugin. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/constructs/aws/Queue.ts` (generates SQS for users), `src/constructs/aws/Webhook.ts` (generates EventBridge for users), absence of runtime message consumers |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnets, security groups, or network segmentation is defined for this repository's own deployment. The repo generates VPC constructs (`src/constructs/aws/Vpc.ts`) for end users — the generated VPC creates private subnets with a security group allowing egress — but this is for consumers' infrastructure, not the plugin's own. |
| **Gap** | No network infrastructure exists. |
| **Recommendation** | As a library/plugin published to NPM, this repository does not require its own network infrastructure. No action needed. The Score 1 reflects absence rather than a genuine gap. |
| **Evidence** | `src/constructs/aws/Vpc.ts` (generates VPC for users), absence of IaC for repo's own networking |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, AppSync, ALB, or CloudFront is defined as an entry point for this repository's own API surface. The repo generates API Gateway constructs for users (Webhook construct uses `HttpApi` from `aws-cdk-lib/aws-apigatewayv2`, ServerSideWebsite uses CloudFront Distribution), but these are for consumer infrastructure. |
| **Gap** | No API entry point exists. |
| **Recommendation** | As a library/plugin, this repository does not expose its own API surface. No action needed. |
| **Evidence** | `src/constructs/aws/Webhook.ts` (HttpApi for users), `src/constructs/aws/ServerSideWebsite.ts` (CloudFront for users) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling mechanisms are configured. The repository does not deploy scalable resources. It is a build-time library. |
| **Gap** | No auto-scaling infrastructure exists. |
| **Recommendation** | Not applicable for a library/plugin. No action needed. |
| **Evidence** | Absence of `aws_autoscaling_*`, `aws_appautoscaling_*`, or scaling configuration in any file |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no persistent state to back up. INF-Q8 does not apply. `has_persistent_data_store=false` and `has_at_rest_data_surface=false`. The library generates DynamoDB tables with `pointInTimeRecovery: true` for users (`src/constructs/aws/DatabaseDynamoDBSingleTable.ts`), demonstrating awareness of backup best practices in generated constructs. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/constructs/aws/DatabaseDynamoDBSingleTable.ts` (PITR enabled for user constructs) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload requiring HA evaluation. INF-Q9 does not apply. `has_deployed_workload=false`. The VPC construct generates multi-AZ infrastructure (`maxAzs: 2`) for users (`src/constructs/aws/Vpc.ts`), demonstrating HA awareness. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/constructs/aws/Vpc.ts` (maxAzs: 2 for users) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No infrastructure is defined in IaC for this repository's own deployment or operational needs. The repository is itself an IaC tool — it generates CloudFormation via CDK — but does not define its own infrastructure (no Terraform, CloudFormation templates, or CDK app for the repo's CI/CD infrastructure, monitoring, or deployment). CI/CD is defined via GitHub Actions YAML but not provisioned through IaC. |
| **Gap** | Repository has no IaC-managed infrastructure. CI/CD pipeline is defined declaratively in GitHub Actions YAML files, but there is no broader IaC governance. |
| **Recommendation** | For a library/plugin, the GitHub Actions workflow files effectively serve as the "infrastructure" definition. Consider this a low-priority gap. If the project grows to require AWS resources (e.g., integration test sandbox accounts, artifact storage), adopt IaC at that point. |
| **Evidence** | `.github/workflows/ci.yml`, `.github/workflows/release.yml` (declarative CI/CD), absence of .tf, .cfn.yaml, cdk.json files |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GitHub Actions CI pipeline (`.github/workflows/ci.yml`) runs on push to master, PRs, and manual dispatch. It includes three jobs: (1) unit tests across Node.js 20/22/24 with Serverless v3 matrix, (2) lint (eslint + prettier), (3) TypeScript type checking. The release pipeline (`.github/workflows/release.yml`) triggers on GitHub release events and publishes to NPM using OIDC for trusted publishing (`id-token: write`). Pre-commit hooks via Husky run `lint-staged` for formatting and linting. |
| **Gap** | No IaC deployment pipeline (no IaC exists). No security scanning in CI (no npm audit, Dependabot, Snyk, or SAST). Release pipeline is a direct publish with no staged rollout, dry-run validation, or automated rollback. No integration tests in the pipeline. |
| **Recommendation** | Add `npm audit --audit-level=high` to CI. Enable Dependabot for automated dependency updates. Add a pre-publish validation step (e.g., `npm pack` + install test). Consider a `@beta` dist-tag publish step before promoting to `@latest`. |
| **Evidence** | `.github/workflows/ci.yml`, `.github/workflows/release.yml`, `.husky/pre-commit`, `package.json` (scripts.test, scripts.lint) |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | TypeScript ^4.3.4 targeting ES2019, compiled to CommonJS. Runtime dependencies include `aws-cdk-lib` ^2.215.0 (current) and `constructs` 10.2.20. Dev dependencies include `aws-sdk` ^2.1322.0 (AWS SDK for JavaScript **v2**, which is in maintenance mode — v3 is the current SDK). `.nvmrc` pins Node.js v16.6.2 (EOL since September 2023), but CI tests on Node.js 20, 22, and 24 (all current). TypeScript is a modern cloud-native language with first-class AWS CDK support. |
| **Gap** | AWS SDK v2 in devDependencies (maintenance mode, v3 is current). `.nvmrc` pins an EOL Node.js version (v16.6.2). TypeScript 4.x is functional but TypeScript 5.x is the current major version with improved performance and decorators. |
| **Recommendation** | Update `.nvmrc` to Node.js 20 or 22 LTS. Migrate from `aws-sdk` v2 to `@aws-sdk/*` v3 modular packages (the v2 usage is in devDependencies only, so impact is limited to test utilities and runtime AWS calls in Queue/ServerSideWebsite). Consider upgrading to TypeScript 5.x for improved performance and modern decorator support. |
| **Evidence** | `package.json` (typescript: ^4.3.4, aws-sdk: ^2.1322.0, aws-cdk-lib: ^2.215.0), `tsconfig.json` (target: es2019), `.nvmrc` (v16.6.2), `.github/workflows/ci.yml` (node: 20, 22, 24) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Single deployable unit (one NPM package) with well-defined internal module boundaries. The architecture follows a modular plugin design: `src/constructs/` (8 construct implementations behind `ConstructInterface`), `src/providers/` (2 providers behind `ProviderInterface`), `src/classes/` (utility classes), `src/utils/` (shared utilities), `src/types/` (type definitions). Constructs are independently registerable (`AwsProvider.registerConstructs(...)`) with clear static interfaces (`StaticConstructInterface`). No circular dependencies observed. Each construct is self-contained with its own schema definition, CDK resource creation, permissions, variables, and outputs. Path aliases (`@lift/providers`, `@lift/constructs`) enforce clean import boundaries. |
| **Gap** | Single deployable unit — all constructs are bundled into one NPM package. No ability to install individual constructs independently. However, this is the standard and correct packaging model for Serverless Framework plugins. |
| **Recommendation** | The current modular monolith architecture is appropriate for a Serverless Framework plugin. The well-defined construct/provider interfaces would support future decomposition into separate packages if needed (e.g., `@lift/queue`, `@lift/storage`), but there is no current need. |
| **Evidence** | `src/plugin.ts` (plugin class with provider/construct registration), `src/constructs/ConstructInterface.ts`, `src/providers/ProviderInterface.ts`, `src/constructs/aws/` (8 independent constructs), `tsconfig.json` (path aliases) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Async vs sync communication is not applicable by design — the library has no inter-service communication of its own. It is a build-time tool that generates CloudFormation resources synchronously. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/plugin.ts` (synchronous construct loading), absence of HTTP clients, gRPC stubs, or message publishing patterns for the library's own communication |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Long-running process handling is not applicable by design — no operations in this build-time plugin exceed 30 seconds. CDK synthesis and CloudFormation template generation are fast in-memory operations. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/plugin.ts` (in-memory CDK synthesis), `src/providers/AwsProvider.ts` (synchronous stack synthesis via `this.app.synth()`) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The library uses NPM semantic versioning (semver) for its public API. `peerDependencies` declares compatibility with `serverless: ^3 || ^4`. The `package.json` version is managed via the release pipeline (`npm version $RELEASE_VERSION --no-git-tag-version`). GitHub releases map to NPM versions. Each construct exposes a JSON schema (`static schema = WEBHOOK_DEFINITION`) that defines the construct's configuration contract. The `eject` command enables users to export generated CloudFormation for migration away from Lift without breaking changes. |
| **Gap** | No explicit API changelog or migration guide for breaking changes between versions. No deprecation annotations in code. Construct schemas are versioned implicitly through NPM semver but have no independent versioning. |
| **Recommendation** | Add a CHANGELOG.md with conventional changelog format. Consider adding `@deprecated` annotations in TypeScript for constructs or properties being phased out. Document breaking changes in GitHub releases. |
| **Evidence** | `package.json` (peerDependencies: serverless ^3 || ^4), `.github/workflows/release.yml` (npm version management), construct schema definitions (e.g., `WEBHOOK_DEFINITION` in `src/constructs/aws/Webhook.ts`) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No service discovery mechanism. This is a library/plugin — it does not communicate with other services at runtime. The Serverless Framework itself provides the plugin discovery mechanism (plugins array in serverless.yml), but there is no AWS Service Discovery, Consul, Istio, or similar. |
| **Gap** | No service discovery. |
| **Recommendation** | Service discovery is not architecturally relevant for a library/plugin. No action needed. This Score 1 reflects the rubric's focus on deployed services rather than a genuine gap. |
| **Evidence** | `package.json` (NPM package, not a service), absence of service discovery configuration |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The library does not store unstructured data. It generates S3 bucket constructs for users (`src/constructs/aws/Storage.ts`) with intelligent tiering, versioning, block public access, and SSL enforcement, but does not manage its own data storage. No Textract or parsing pipelines are present. |
| **Gap** | No unstructured data storage. |
| **Recommendation** | Not applicable for a library/plugin. No action needed. |
| **Evidence** | `src/constructs/aws/Storage.ts` (S3 bucket construct for users) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database access layer exists in this library. The `DatabaseDynamoDBSingleTable` construct generates DynamoDB table resources for end users but does not access data itself. The `aws-sdk` v2 is in devDependencies only and is used for operational commands (Queue `sendMessage`, `purgeQueue`, `pollMessages`) — these are CLI utility functions, not a data access layer. |
| **Gap** | No data access layer. |
| **Recommendation** | Not applicable for a library/plugin. No action needed. |
| **Evidence** | `src/constructs/aws/DatabaseDynamoDBSingleTable.ts` (generates DynamoDB for users), `package.json` (aws-sdk in devDependencies only) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database engine definitions exist in this repository. The `DatabaseDynamoDBSingleTable` construct creates DynamoDB tables (serverless, fully managed, no engine version concept) for end users. No RDS, DocumentDB, ElastiCache, or other versioned database engines are defined. No engine version pinning or EOL concerns exist. |
| **Gap** | No database engines to version. |
| **Recommendation** | Not applicable for this repository. DynamoDB is serverless and fully managed with no engine version lifecycle. No action needed. |
| **Evidence** | `src/constructs/aws/DatabaseDynamoDBSingleTable.ts` (DynamoDB PAY_PER_REQUEST, no engine version) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs. All business logic is in the TypeScript application layer. The library generates NoSQL (DynamoDB) constructs with a single-table design pattern (PK/SK, LSI, GSI) — no SQL coupling. No `.sql` files, no `CREATE PROCEDURE`, no `CREATE TRIGGER`, no ORM bypass patterns. |
| **Gap** | N/A — fully meets criterion. |
| **Recommendation** | No action needed. The NoSQL approach and application-layer business logic avoid database coupling. |
| **Evidence** | `src/constructs/aws/DatabaseDynamoDBSingleTable.ts` (DynamoDB single-table design), absence of .sql files or stored procedure definitions |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail configuration in this repository. No IaC defines audit logging for the repo's own infrastructure (because no infrastructure exists). The library does not generate CloudTrail resources for end users either. |
| **Gap** | No audit logging. |
| **Recommendation** | Not applicable for a library/plugin with no deployed infrastructure. If the project adds AWS resources (e.g., integration test accounts), add CloudTrail at that time. |
| **Evidence** | Absence of `aws_cloudtrail` in any file, absence of IaC files |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no database, S3 bucket, EBS volume, or similar. SEC-Q2 does not apply. `has_at_rest_data_surface=false`. Notably, the generated constructs demonstrate encryption awareness: `Storage` construct uses `BucketEncryption.S3_MANAGED` by default with optional KMS (`src/constructs/aws/Storage.ts`), and `Queue` construct supports `kmsManaged` and `kms` encryption options (`src/constructs/aws/Queue.ts`). |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/constructs/aws/Storage.ts` (S3_MANAGED encryption default), `src/constructs/aws/Queue.ts` (KMS encryption options) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API endpoints are defined for this repository itself. However, the Webhook construct (`src/constructs/aws/Webhook.ts`) demonstrates strong security-by-default design: it **requires** either an authorizer or explicit `insecure: true` flag. The construct creates a Lambda authorizer with `REQUEST` type and `enableSimpleResponses: true` when secure mode is used. This shows security awareness in generated constructs. |
| **Gap** | No API authentication for the repo's own surface (because no API surface exists). |
| **Recommendation** | Not applicable for a library/plugin. The Webhook construct's authorizer enforcement is a good security practice for generated infrastructure. |
| **Evidence** | `src/constructs/aws/Webhook.ts` (CfnAuthorizer, mandatory authorizer or insecure flag) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity provider integration. The library does not integrate with Cognito, Okta, or any IdP for its own authentication. The Stripe provider (`src/providers/StripeProvider.ts`) uses Stripe's own API key authentication but does not integrate with a centralized identity system. |
| **Gap** | No identity provider integration. |
| **Recommendation** | Not applicable for a library/plugin. The Stripe provider's authentication model (env var or TOML config file) is appropriate for a CLI tool context. |
| **Evidence** | `src/providers/StripeProvider.ts` (STRIPE_API_KEY from env or TOML), absence of Cognito, OIDC, or SAML configuration |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No plaintext credentials in source code or version control. The `StripeProvider` (`src/providers/StripeProvider.ts`) reads the Stripe API key from either the `STRIPE_API_KEY` environment variable or a TOML config file at `~/.config/stripe/config.toml` (user home directory, not committed to git). No `.env` files are committed. No hardcoded passwords, API keys, or tokens found in any source file. However, there is no Secrets Manager, Vault, or rotation mechanism — the env var / config file approach is standard for CLI tools but lacks audit trails and rotation. |
| **Gap** | Production credentials (Stripe API key) managed via environment variables or unencrypted local config files without rotation or managed secrets store. |
| **Recommendation** | For a CLI tool context, environment variables are the standard approach. If this plugin is used in CI/CD pipelines, recommend users store the Stripe API key in AWS Secrets Manager or GitHub Actions secrets with rotation. Document this as a best practice in the plugin's security guidance. |
| **Evidence** | `src/providers/StripeProvider.ts` (process.env.STRIPE_API_KEY, TOML config file), `.gitignore` (no .env files committed), absence of Secrets Manager or Vault integration |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute resources to harden. The library does not deploy EC2 instances, containers, or any compute that requires patching or vulnerability scanning. Node.js runtime patching is managed by end users who run the Serverless Framework. |
| **Gap** | No compute hardening. |
| **Recommendation** | Not applicable for a library/plugin. No action needed. |
| **Evidence** | Absence of Dockerfile, EC2 instances, AMI references, SSM configuration |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SAST, DAST, or dependency vulnerability scanning tools are integrated into the CI/CD pipeline. The CI pipeline (`.github/workflows/ci.yml`) runs unit tests, lint, and type checking — but no security scanning. No `npm audit` step. No Dependabot configuration (`.github/dependabot.yml` is absent). No Snyk, SonarQube, CodeGuru Reviewer, or similar tools. No `.snyk` policy file. The library has 14 runtime dependencies including `lodash`, `stripe`, and `aws-cdk-lib` — all of which have had security advisories in the past. |
| **Gap** | Complete absence of security scanning in the CI/CD pipeline. For a widely-used open-source library, this is a significant gap — vulnerabilities in dependencies could be distributed to all consumers. |
| **Recommendation** | **High priority:** Add `npm audit --audit-level=high` as a CI step. Enable GitHub Dependabot for automated dependency update PRs. Consider adding Snyk or Socket.dev for deeper dependency analysis. For SAST, add ESLint security plugins (`eslint-plugin-security`) or Semgrep with Node.js/TypeScript rules. |
| **Evidence** | `.github/workflows/ci.yml` (no security scanning steps), absence of `.github/dependabot.yml`, absence of `.snyk`, `package.json` (14 runtime dependencies) |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumentation. No OpenTelemetry SDK, X-Ray SDK, or tracing library in dependencies. The library runs as a build-time tool, not a runtime service, so distributed tracing is not architecturally relevant for its own execution. |
| **Gap** | No distributed tracing. |
| **Recommendation** | Not applicable for a build-time library. However, the generated constructs (Queue, Webhook, ServerSideWebsite) could benefit from optional X-Ray tracing configuration as a feature for end users. Consider adding optional `tracing: true` configuration to constructs that generate Lambda functions. |
| **Evidence** | `package.json` (no tracing dependencies), absence of OpenTelemetry or X-Ray imports |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no user-facing surface for which SLOs are meaningful. OPS-Q2 does not apply. `has_api_surface=false` and `has_persistent_data_store=false`. The library is consumed as an NPM dependency at build time. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `package.json` (NPM library), absence of API surface or persistent data |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom metrics published. No CloudWatch `put_metric_data` calls. No business outcome tracking. The library generates CloudWatch alarms for the Queue construct (DLQ alarm in `src/constructs/aws/Queue.ts`), but this is for end user infrastructure, not the library's own metrics. |
| **Gap** | No business metrics. |
| **Recommendation** | For a library/plugin, consider tracking NPM download metrics and GitHub issue resolution times as external business metrics. No CloudWatch metrics are applicable. |
| **Evidence** | `src/constructs/aws/Queue.ts` (CloudWatch alarm for users), absence of metric publishing in library code |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configured for this repository. The Queue construct generates CloudWatch alarms for end users (`src/constructs/aws/Queue.ts` creates DLQ alarms with SNS notification), but no alerting exists for the library itself. |
| **Gap** | No alerting. |
| **Recommendation** | Not applicable for a library/plugin. Consider adding GitHub Actions status badges and notification webhooks for CI failures. |
| **Evidence** | `src/constructs/aws/Queue.ts` (user-facing alarms), absence of repo-level alerting |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The release pipeline (`.github/workflows/release.yml`) publishes directly to NPM on GitHub release events. The process: checkout → setup Node.js 20 → npm install → `npm version $RELEASE_VERSION` → `npm publish --access public`. No staged rollout, no `@beta` or `@next` dist-tag pre-release, no canary validation, no automated rollback mechanism. A broken release immediately affects all consumers who install or update. |
| **Gap** | Direct-to-production NPM publish with no staged rollout or pre-release validation. |
| **Recommendation** | Implement a two-phase release: (1) publish to `@beta` dist-tag first, (2) after validation period or manual approval, promote to `@latest`. Add a `npm pack` + dry-run install step to validate package integrity before publish. Consider adding `npm deprecate` automation for rollback of broken releases. |
| **Evidence** | `.github/workflows/release.yml` (direct npm publish) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The `test/unit/` directory contains 13 test files covering all constructs: `common.test.ts`, `databasesDynamoDBSingleTable.test.ts`, `extensions.test.ts`, `permissions.test.ts`, `queues.test.ts`, `serverSideWebsite.test.ts`, `singlePageApp.test.ts`, `staticWebsite.test.ts`, `storage.test.ts`, `stripe.test.ts`, `variables.test.ts`, `vpc.test.ts`, `webhooks.test.ts`. Tests use Jest with `ts-jest` and appear to be snapshot/mock-based (testing CDK synthesis output). CI runs tests across Node.js 20/22/24 with Serverless v3 matrix. No integration tests against live AWS services or CloudFormation deployment validation. |
| **Gap** | No integration tests. Unit tests validate CDK synthesis output but do not verify that generated CloudFormation templates deploy successfully or that constructs behave correctly when deployed to AWS. |
| **Recommendation** | Add CloudFormation template validation using `cfn-lint` in CI. Consider adding integration tests that deploy a minimal Lift configuration to a sandbox AWS account and validate resource creation. The AWS CDK provides `assertions` module for template validation — ensure it is being used for deep template structure checks beyond snapshots. |
| **Evidence** | `test/unit/` (13 test files), `jest.config.js`, `.github/workflows/ci.yml` (test matrix), absence of integration test directory or live AWS test configuration |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, no automated incident response, no Systems Manager Automation documents. No incident response workflows defined. The `.github/CONTRIBUTING.md` and `.github/ISSUE_TEMPLATE/` exist for contributor workflows but not for operational incident response. |
| **Gap** | No incident response automation. |
| **Recommendation** | For a library/plugin, incident response primarily means responding to reported bugs and security vulnerabilities. Consider adding a `SECURITY.md` file with vulnerability reporting instructions and response SLAs. Add issue templates for bug reports with reproduction steps. |
| **Evidence** | `.github/CONTRIBUTING.md`, `.github/ISSUE_TEMPLATE/`, absence of runbooks or incident automation |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No service-level dashboards, alarms with named owners, or SLO definitions tied to specific teams. No CODEOWNERS file for observability assets. No team attribution on any monitoring configuration. |
| **Gap** | No observability ownership. |
| **Recommendation** | Add a `CODEOWNERS` file to the repository defining ownership of key areas (constructs, providers, CI/CD). For an OSS project, this helps maintain accountability for code review and issue triage. |
| **Evidence** | Absence of CODEOWNERS, absence of dashboards or alarm ownership |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resources are defined for this repository to tag. The generated constructs do not enforce tagging by default — CDK resources in Storage, Queue, Webhook, etc. do not include `default_tags` or required tag configurations. Users can add tags via the `extensions` mechanism but it is not enforced. |
| **Gap** | Generated constructs do not enforce or suggest resource tagging. |
| **Recommendation** | Consider adding optional `tags` configuration to constructs that would propagate tags to all generated CloudFormation resources. This would help end users comply with tagging governance. Low priority for the library itself but high value for users' operational maturity. |
| **Evidence** | `src/constructs/aws/Storage.ts`, `src/constructs/aws/Queue.ts`, `src/constructs/aws/Webhook.ts` (no tag configuration), `src/plugin.ts` (extensions mechanism available but tags not enforced) |

---

## Learning Materials

### Triggered Pathway: Move to Modern DevOps

- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `package.json` | INF-Q1, INF-Q2, INF-Q11, APP-Q1, APP-Q2, APP-Q5, APP-Q6, DATA-Q1, DATA-Q2, SEC-Q5, SEC-Q7, OPS-Q1, OPS-Q2, OPS-Q6 | NPM package manifest — dependencies, devDependencies, peerDependencies, scripts, main entry point |
| `tsconfig.json` | APP-Q1, APP-Q2 | TypeScript configuration — target ES2019, path aliases for module boundaries |
| `.nvmrc` | APP-Q1 | Node.js version pin — v16.6.2 (EOL) |
| `.github/workflows/ci.yml` | INF-Q10, INF-Q11, SEC-Q7, OPS-Q6 | CI pipeline — unit tests (Node 20/22/24), lint, type checking |
| `.github/workflows/release.yml` | INF-Q11, OPS-Q5 | Release pipeline — npm publish on GitHub release event |
| `.husky/pre-commit` | INF-Q11 | Pre-commit hooks — lint-staged |
| `src/plugin.ts` | INF-Q3, APP-Q2, APP-Q3, APP-Q4 | Main plugin class — construct/provider registration, lifecycle hooks, variable resolution |
| `src/providers/AwsProvider.ts` | INF-Q2, INF-Q3, APP-Q2 | AWS provider — CDK stack synthesis, construct registration, CloudFormation generation |
| `src/providers/StripeProvider.ts` | SEC-Q4, SEC-Q5 | Stripe provider — API key from env var or TOML config file |
| `src/constructs/aws/Queue.ts` | INF-Q4, OPS-Q3, OPS-Q4, SEC-Q2 | Queue construct — SQS, DLQ, CloudWatch alarms, KMS encryption options |
| `src/constructs/aws/Storage.ts` | DATA-Q1, SEC-Q2, OPS-Q9 | Storage construct — S3 bucket with encryption, versioning, lifecycle rules |
| `src/constructs/aws/Webhook.ts` | INF-Q4, INF-Q6, SEC-Q3 | Webhook construct — HttpApi, EventBridge, Lambda authorizer enforcement |
| `src/constructs/aws/DatabaseDynamoDBSingleTable.ts` | INF-Q2, INF-Q8, DATA-Q1, DATA-Q2, DATA-Q3, DATA-Q4 | DynamoDB construct — single-table design, PITR, PAY_PER_REQUEST |
| `src/constructs/aws/Vpc.ts` | INF-Q5, INF-Q9 | VPC construct — multi-AZ, private subnets, security groups |
| `src/constructs/aws/ServerSideWebsite.ts` | INF-Q6 | Server-side website construct — CloudFront Distribution, S3 assets |
| `src/constructs/aws/SinglePageApp.ts` | INF-Q6 | Single page app construct — CloudFront with SPA routing |
| `src/constructs/aws/StaticWebsite.ts` | INF-Q6 | Static website construct — S3 static hosting with CloudFront |
| `src/constructs/ConstructInterface.ts` | APP-Q2 | Construct interface — defines contract for all constructs |
| `src/providers/ProviderInterface.ts` | APP-Q2 | Provider interface — defines contract for all providers |
| `test/unit/` | OPS-Q6 | Unit test directory — 13 test files covering all constructs |
| `jest.config.js` | OPS-Q6 | Jest configuration — ts-jest preset, module name mapping |
| `.eslintrc` | INF-Q11 | ESLint configuration — TypeScript rules, import ordering |
| `README.md` | Quick Agent Wins | Documentation — 194 lines, plugin overview, installation, quick start |
| `docs/` | Quick Agent Wins | Documentation directory — 11 files covering all constructs |
| `.github/CONTRIBUTING.md` | OPS-Q7 | Contributing guidelines |
| `.github/ISSUE_TEMPLATE/` | OPS-Q7 | Issue templates |
