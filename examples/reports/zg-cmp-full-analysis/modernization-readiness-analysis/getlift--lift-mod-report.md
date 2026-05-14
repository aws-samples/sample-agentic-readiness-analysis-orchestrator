# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | serverless-lift |
| **Date** | 2025-07-18 |
| **Repo Type** | application |
| **Service Archetype** | stateless-utility (auto-detected) |
| **Priority** | P2 |
| **Tags** | typescript, serverless, iac |
| **Context** | Serverless Framework plugin providing higher-level AWS constructs. |
| **Overall Score** | 2.83 / 4.0 |

**Archetype Justification**: No database connections, no persistent state, no message queue consumption, and no write endpoints detected. The plugin reads Serverless Framework configuration and produces CloudFormation templates via AWS CDK synthesis. All operations are deploy-time computations without runtime state. Classified as stateless-utility.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 3.64 / 4.0 | ✅ Mature |
| Application Architecture (APP) | 3.67 / 4.0 | ✅ Mature |
| Data Platform Modernization (DATA) | 3.75 / 4.0 | ✅ Mature |
| Security Baseline (SEC) | 1.86 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.22 / 4.0 | ❌ Not Present |
| **Overall** | **2.83 / 4.0** | **🟡 Partial** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | SEC-Q1: Audit Logging | 1 | No CloudTrail or audit logging configuration in any construct | No audit trail for compliance or forensic analysis; users deploying with Lift have no visibility into infrastructure changes |
| 2 | SEC-Q4: Centralized Identity | 1 | No Cognito, Okta, or IdP integration in any construct | Users must implement identity management separately; no reusable identity patterns provided |
| 3 | SEC-Q7: Application Security Pipeline | 1 | No SAST, dependency scanning, or security gates in CI/CD pipeline | Vulnerable dependencies or code patterns could reach npm releases undetected |
| 4 | OPS-Q1: Distributed Tracing | 1 | No X-Ray or OpenTelemetry instrumentation in plugin or generated constructs | Constructs deployed by users lack tracing by default; debugging production issues requires manual instrumentation |
| 5 | OPS-Q9: Resource Tagging | 1 | No default tags or tagging governance applied to generated resources | Resources created by Lift constructs have no cost allocation, ownership, or environment tags |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** INF-Q11 = 3 (CI/CD pipeline exists with build, test, lint, and npm publish stages in `.github/workflows/ci.yml` and `.github/workflows/release.yml`)
- **What it enables:** An agent that triggers CI builds on demand, monitors build status, manages npm release workflows, and reports test results or lint failures to developers.
- **Additional steps:** Expose GitHub Actions API access for agent invocation; consider adding a webhook endpoint for CI status callbacks.
- **Effort:** Low — existing CI/CD pipeline provides the automation surface; agent orchestrates via GitHub API.

### RAG-Based Knowledge Agent

- **Prerequisite:** Extensive documentation exists in the repository — `README.md` (194 lines), `docs/` directory with 11 Markdown files covering all constructs (queue.md, storage.md, webhook.md, server-side-website.md, single-page-app.md, static-website.md, database-dynamodb-single-table.md, configuration.md, permissions.md, comparison.md, serverless-types.md), and `CONTRIBUTING.md`.
- **What it enables:** A RAG-based knowledge agent (powered by Amazon Bedrock) that indexes all Lift documentation and source code to answer developer questions about construct configuration, debugging, and best practices. Could serve as an intelligent assistant for Lift users.
- **Additional steps:** Generate embeddings from documentation files; set up a vector store (e.g., Amazon OpenSearch with vector engine); implement a retrieval chain using Bedrock.
- **Effort:** Medium — documentation corpus exists but requires embedding generation and vector store setup.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 4 — application is already well-modularized with clear construct/provider interfaces |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 4 — compute targets are already Lambda/CloudFront (managed services); no EC2/VM-based compute |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 — no stored procedures or proprietary SQL; no commercial database engines detected |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = 4 — all database constructs use DynamoDB (fully managed) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 4 (stateless-utility calibration); no data processing workloads detected |
| 6 | Move to Modern DevOps | Not Triggered | — | — | INF-Q10 = 4, INF-Q11 = 3 — IaC coverage is 100% and CI/CD pipeline exists with automated testing |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. Context "Serverless Framework plugin providing higher-level AWS constructs." contains no AI-related signal terms. |

No pathways triggered — no pathway detail subsections included.

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The plugin generates CloudFormation resources exclusively for managed AWS services: Lambda functions (via Serverless Framework integration in `src/providers/AwsProvider.ts`), CloudFront distributions (`src/constructs/aws/ServerSideWebsite.ts`, `src/constructs/aws/abstracts/StaticWebsiteAbstract.ts`), API Gateway HttpApi (`src/constructs/aws/Webhook.ts`), SQS queues (`src/constructs/aws/Queue.ts`), DynamoDB tables (`src/constructs/aws/DatabaseDynamoDBSingleTable.ts`), S3 buckets (`src/constructs/aws/Storage.ts`), and EventBridge event buses (`src/constructs/aws/Webhook.ts`). No EC2 instances, no raw compute resources. The only compute model is serverless Lambda. |
| **Gap** | None. All compute targets are fully managed services. |
| **Recommendation** | No action needed. The plugin already targets the most modern managed compute services. |
| **Evidence** | `src/providers/AwsProvider.ts` (registerConstructs), `src/constructs/aws/Queue.ts` (Lambda worker), `src/constructs/aws/Webhook.ts` (HttpApi + Lambda authorizer), `src/constructs/aws/ServerSideWebsite.ts` (CloudFront + Lambda backend) |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The `DatabaseDynamoDBSingleTable` construct (`src/constructs/aws/DatabaseDynamoDBSingleTable.ts`) creates a fully managed DynamoDB table with `BillingMode.PAY_PER_REQUEST`, `pointInTimeRecovery: true`, and DynamoDB Streams enabled. No self-managed database resources (no RDS on EC2, no MongoDB in containers, no database installation scripts). |
| **Gap** | None. The only database construct uses a fully managed service with automated failover. |
| **Recommendation** | No action needed. Consider expanding the construct library to include Aurora Serverless v2 or DynamoDB global tables for multi-region use cases, aligned with the preference for `aurora` and `dynamodb`. |
| **Evidence** | `src/constructs/aws/DatabaseDynamoDBSingleTable.ts` (Table construct with PAY_PER_REQUEST, pointInTimeRecovery) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | **Archetype: stateless-utility.** No multi-step workflows exist — the plugin performs single-pass CDK synthesis and deploy-time operations (S3 sync, CloudFront invalidation). These are sequential deploy-time utility operations, not business workflows requiring orchestration. The absence of workflow orchestration is the correct design for this archetype. |
| **Gap** | N/A — no workflows to orchestrate. Correct outcome for stateless-utility. |
| **Recommendation** | Dedicated workflow orchestration is not applicable for this archetype and does not represent a gap. If future constructs need multi-step provisioning workflows, consider AWS Step Functions integration, aligned with the preference for `eventbridge`. |
| **Evidence** | `src/plugin.ts` (sequential hook execution: initialize → compileEvents → deploy → postDeploy), `src/constructs/aws/ServerSideWebsite.ts` (postDeploy: sequential S3 sync → CloudFront invalidation) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | **Archetype: stateless-utility.** Synchronous HTTP/gRPC is the correct design for this plugin. The Queue construct (`src/constructs/aws/Queue.ts`) does generate managed SQS queues with dead letter queues and EventBridge event buses (`src/constructs/aws/Webhook.ts`), demonstrating that the plugin helps users adopt managed async messaging. The plugin itself operates synchronously during `sls deploy` — this is correct and does not need async messaging. |
| **Gap** | None. Synchronous design is appropriate for this archetype. The constructs provided to users already leverage managed messaging services (SQS, EventBridge). |
| **Recommendation** | Adopting async messaging for the plugin's own operations is NOT recommended — it would add operational complexity without architectural benefit. The constructs already promote best-practice managed messaging for end users. |
| **Evidence** | `src/constructs/aws/Queue.ts` (SQS + DLQ), `src/constructs/aws/Webhook.ts` (EventBridge), `src/plugin.ts` (synchronous hook lifecycle) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The `Vpc` construct (`src/constructs/aws/Vpc.ts`) creates a VPC with `maxAzs: 2`, private subnets, and a dedicated security group (`AppSecurityGroup`). Lambda functions are placed in private subnets via `provider.setVpcConfig()`. However, the security group allows egress to `Peer.anyIpv4()` on all ports (`Port.allTraffic()`), and no VPC endpoints, PrivateLink, or VPC Lattice are configured. |
| **Gap** | Egress rule is overly permissive (0.0.0.0/0 on all ports). No VPC endpoints for AWS service access (S3, DynamoDB, SQS), which means traffic exits the VPC to reach AWS services. No managed networking services (VPC Lattice, PrivateLink). |
| **Recommendation** | Add VPC endpoint constructs for commonly used services (S3, DynamoDB, SQS) to keep traffic within the AWS network. Consider restricting the egress security group rule to specific CIDR ranges or ports. Consider adding VPC Lattice support for service-to-service communication patterns. |
| **Evidence** | `src/constructs/aws/Vpc.ts` (maxAzs: 2, AppSecurityGroup with Peer.anyIpv4() egress, privateSubnets for Lambda) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The `Webhook` construct (`src/constructs/aws/Webhook.ts`) uses API Gateway HttpApi as the entry point, with optional Lambda authorizer for authentication. The `ServerSideWebsite` construct (`src/constructs/aws/ServerSideWebsite.ts`) uses CloudFront as the CDN entry point with API Gateway as the backend origin. Static websites (`SinglePageApp`, `StaticWebsite`) use CloudFront distributions with S3 origins. No direct service exposure. |
| **Gap** | None. All constructs use managed entry points (API Gateway, CloudFront). |
| **Recommendation** | No action needed. Consider adding throttling configuration options to the Webhook construct's API Gateway, aligned with the preference for `api-gateway`. |
| **Evidence** | `src/constructs/aws/Webhook.ts` (HttpApi, CfnAuthorizer), `src/constructs/aws/ServerSideWebsite.ts` (CloudFront Distribution with API Gateway origin), `src/constructs/aws/abstracts/StaticWebsiteAbstract.ts` (CloudFront with S3Origin) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | DynamoDB table uses `BillingMode.PAY_PER_REQUEST` (`src/constructs/aws/DatabaseDynamoDBSingleTable.ts`), which provides on-demand auto-scaling. Lambda functions scale inherently with managed concurrency. SQS queues scale automatically. However, there is no explicit auto-scaling configuration for any resources, no Lambda concurrency limits, and no DynamoDB provisioned capacity option with auto-scaling for cost optimization on predictable workloads. |
| **Gap** | No Lambda concurrency limits configured (relevant for protecting downstream dependencies). No option for DynamoDB provisioned capacity with auto-scaling for cost optimization. |
| **Recommendation** | Add optional `maxConcurrency` configuration to Lambda-backed constructs for downstream protection. Consider offering a DynamoDB provisioned-capacity mode with auto-scaling as an alternative to PAY_PER_REQUEST for cost-sensitive workloads. |
| **Evidence** | `src/constructs/aws/DatabaseDynamoDBSingleTable.ts` (BillingMode.PAY_PER_REQUEST), `src/constructs/aws/Queue.ts` (maxConcurrency option for SQS event source mapping) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | DynamoDB has `pointInTimeRecovery: true` enabled in `src/constructs/aws/DatabaseDynamoDBSingleTable.ts`. The Storage construct (`src/constructs/aws/Storage.ts`) creates S3 buckets with `versioned: true` and lifecycle rules that expire non-current versions after 30 days. However, there is no cross-region backup replication, no documented restore procedure, and no AWS Backup plan integration. |
| **Gap** | No cross-region backup replication for DynamoDB or S3. No documented or automated restore procedures. No AWS Backup plan integration for centralized backup management. |
| **Recommendation** | Add optional cross-region replication for DynamoDB (global tables) and S3 (cross-region replication). Consider adding an AWS Backup plan construct for centralized backup orchestration. |
| **Evidence** | `src/constructs/aws/DatabaseDynamoDBSingleTable.ts` (pointInTimeRecovery: true), `src/constructs/aws/Storage.ts` (versioned: true, NoncurrentVersionExpiration: 30 days) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Lambda functions are inherently multi-AZ. DynamoDB is a multi-AZ managed service with automatic replication. The `Vpc` construct (`src/constructs/aws/Vpc.ts`) creates resources across `maxAzs: 2` availability zones. CloudFront distributions are globally distributed by design. SQS queues are regionally redundant. All constructs target services that provide built-in multi-AZ resilience. |
| **Gap** | None. All services are inherently multi-AZ or globally distributed. |
| **Recommendation** | No action needed. For additional resilience, consider adding an optional multi-region configuration for DynamoDB (global tables) and S3 (cross-region replication). |
| **Evidence** | `src/constructs/aws/Vpc.ts` (maxAzs: 2), `src/constructs/aws/DatabaseDynamoDBSingleTable.ts` (DynamoDB — inherently multi-AZ), `src/constructs/aws/ServerSideWebsite.ts` (CloudFront — global CDN) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | This plugin IS infrastructure as code. 100% of the infrastructure it manages is defined as AWS CDK constructs that synthesize to CloudFormation templates. The entire construct library — Queue, Storage, Webhook, Vpc, DatabaseDynamoDBSingleTable, ServerSideWebsite, SinglePageApp, StaticWebsite — produces CloudFormation resources via CDK synthesis in `src/providers/AwsProvider.ts` (`appendCloudformationResources` method). Compute (Lambda), networking (VPC, security groups), databases (DynamoDB), messaging (SQS, EventBridge), storage (S3), and CDN (CloudFront) are all defined in code. The `eject` command in `src/plugin.ts` even allows users to export the raw CloudFormation template. |
| **Gap** | None. IaC coverage is complete by design. |
| **Recommendation** | No action needed. Consider adding CloudWatch alarms, Route 53 health checks, or AWS Backup plans as constructs to extend IaC coverage to operational/DR resources for end users. |
| **Evidence** | `src/providers/AwsProvider.ts` (CDK App, Stack, synth), `src/plugin.ts` (eject command), all `src/constructs/aws/*.ts` files |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GitHub Actions CI pipeline (`.github/workflows/ci.yml`) runs on push to master and PRs with three parallel jobs: (1) unit tests across Node 20/22/24 with Serverless Framework v3, (2) lint (eslint + prettier), (3) TypeScript type checks. Release pipeline (`.github/workflows/release.yml`) publishes to npm using OIDC trusted publishing on GitHub Release events. However, there are no automated rollback mechanisms, no deployment pipeline (appropriate for a library), and no security scanning in the pipeline. |
| **Gap** | No security scanning (SAST, dependency audit) in the CI pipeline. No automated rollback — an npm publish failure requires manual intervention. Build matrix does not test with Serverless v4 (commented out). |
| **Recommendation** | Add `npm audit` or Snyk dependency scanning as a CI step. Add a post-publish verification step. Uncomment and resolve Serverless v4 testing. Consider adding automated npm unpublish on critical failures. |
| **Evidence** | `.github/workflows/ci.yml` (unit-tests, lint, type jobs), `.github/workflows/release.yml` (npm publish with OIDC) |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The entire codebase is written in TypeScript (50 `.ts` files across `src/` and `test/`). TypeScript has first-class AWS SDK coverage (`aws-cdk-lib` ^2.215.0 and `aws-sdk` ^2.1322.0 in dependencies), broad cloud-native tooling, and a mature framework ecosystem. TypeScript compiles to ES2019 (`tsconfig.json`) with strict mode enabled, providing type safety and modern language features. |
| **Gap** | None. TypeScript is a Tier 1 language for AWS cloud-native development. |
| **Recommendation** | No action needed. The language choice is optimal for this use case. Consider migrating from `aws-sdk` v2 (in devDependencies) to `@aws-sdk` v3 (modular) for tree-shaking benefits and reduced bundle size. |
| **Evidence** | `package.json` (TypeScript ^4.3.4, aws-cdk-lib ^2.215.0), `tsconfig.json` (target: es2019, strict: true), all `.ts` files in `src/` |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The codebase is a single npm package with well-defined module boundaries and clear interfaces. The architecture follows a plugin pattern with: (1) **Constructs** — each implementing `ConstructInterface` (`src/constructs/ConstructInterface.ts`) with `outputs()`, `variables()`, `permissions()`, `postDeploy()`, `preRemove()` contracts. (2) **Providers** — each implementing `ProviderInterface` (`src/providers/ProviderInterface.ts`) with `createConstruct()`. (3) **Static interfaces** (`StaticConstructInterface`, `StaticProviderInterface`) defining registration contracts with `type`, `schema`, `create()`, and `commands`. Each construct (Queue, Storage, Webhook, Vpc, etc.) is self-contained with its own CDK resources, configuration schema, and lifecycle methods. No circular dependencies detected between constructs. The provider system (`AwsProvider`, `StripeProvider`) uses a registry pattern for extensibility. TypeScript path aliases (`@lift/providers`, `@lift/constructs`) enforce module boundaries. |
| **Gap** | None. The modular architecture with clear interfaces and no circular dependencies represents best-practice modularity for a plugin library. |
| **Recommendation** | No action needed. The current architecture is well-structured for its purpose. |
| **Evidence** | `src/constructs/ConstructInterface.ts`, `src/constructs/StaticConstructInterface.ts`, `src/providers/ProviderInterface.ts`, `src/providers/AwsProvider.ts` (registerConstructs pattern), `tsconfig.json` (path aliases) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | **Archetype: stateless-utility.** Synchronous request/response is the correct design for this plugin. The plugin operates as a CLI-time tool that reads configuration, synthesizes CloudFormation templates, and performs deploy-time operations. All communication is synchronous: CDK synthesis is in-memory, AWS API calls (CloudFormation describeStacks, S3 operations, CloudFront invalidation) are sequential deploy-time operations in `src/classes/aws.ts` and `src/CloudFormation.ts`. Async messaging is not needed and would add unnecessary complexity. |
| **Gap** | None. Synchronous is the correct design for this archetype. |
| **Recommendation** | Adopting async communication for the plugin's own operations is NOT recommended — it would add operational complexity without architectural benefit. |
| **Evidence** | `src/plugin.ts` (synchronous hook lifecycle), `src/classes/aws.ts` (sequential AWS API calls), `src/CloudFormation.ts` (synchronous stack output retrieval) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | **Archetype: stateless-utility.** No operations exceed 30 seconds by design. CDK synthesis is in-memory computation that completes in seconds. Deploy-time S3 sync and CloudFront invalidation are bounded operations managed by the AWS SDK with built-in timeouts. The `sleep(500)` in `src/constructs/aws/Queue.ts` (purgeDlq) is a 500ms wait for SQS eventual consistency, not a long-running operation. The `pollMessages` function in `src/constructs/aws/queue/sqs.ts` uses `WaitTimeSeconds: 3` for SQS long-polling — a bounded, non-blocking operation. |
| **Gap** | None. No long-running operations exist. Correct outcome for stateless-utility. |
| **Recommendation** | Async job infrastructure is not applicable for the current surface. No action needed. |
| **Evidence** | `src/plugin.ts` (synchronous synthesis), `src/constructs/aws/Queue.ts` (sleep(500) — bounded), `src/constructs/aws/queue/sqs.ts` (WaitTimeSeconds: 3), `src/utils/sleep.ts` |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The package uses npm semantic versioning via `npm version $RELEASE_VERSION` in the release pipeline (`.github/workflows/release.yml`). The `peerDependencies` in `package.json` specify `serverless: "^3 \|\| ^4"` demonstrating major version compatibility awareness. The construct schemas (`QUEUE_DEFINITION`, `STORAGE_DEFINITION`, etc.) use `additionalProperties: false` to enforce strict configuration contracts. However, there is no formal API versioning strategy for the construct configuration schema (e.g., no `/v1/` or version field in the schema), and breaking changes to construct configuration would require a semver major bump without a migration path. |
| **Gap** | No formal configuration schema versioning strategy. Breaking changes to construct configs rely solely on semver — no migration tooling or deprecation annotations exist. |
| **Recommendation** | Consider adding a schema version field to construct configurations to enable forward-compatible evolution. Add deprecation annotations and migration guides for breaking changes. The `eject` command is a good pattern — consider extending it to support configuration migration. |
| **Evidence** | `package.json` (peerDependencies: serverless ^3 \|\| ^4), `.github/workflows/release.yml` (npm version), `src/constructs/aws/Queue.ts` (QUEUE_DEFINITION with additionalProperties: false) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The plugin uses the Serverless Framework's plugin discovery mechanism — it is loaded by name from `serverless.yml` (`plugins: [serverless-lift]`). Internally, constructs are discovered through a registry pattern: `AwsProvider.registerConstructs()` registers all construct classes, and `LiftPlugin.registerProviders()` registers provider classes. There are no hard-coded service endpoints — AWS endpoints are handled by the AWS SDK. The provider pattern (`ProviderInterface.createConstruct()`) enables extensible discovery of construct implementations. |
| **Gap** | The construct registry is static (compile-time registration). Third-party construct discovery requires manual plugin registration (`AwsProvider.registerConstructs(...)` call in consumer code). No dynamic discovery mechanism for community-contributed constructs. |
| **Recommendation** | Consider implementing a dynamic construct discovery mechanism (e.g., npm package convention or plugin manifest) for community-contributed constructs. The current static registry pattern works for the core library but limits extensibility. |
| **Evidence** | `src/providers/AwsProvider.ts` (registerConstructs, getConstructClass, getAllConstructClasses), `src/plugin.ts` (LiftPlugin.registerProviders), `package.json` (main: dist/src/plugin.js) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The `Storage` construct (`src/constructs/aws/Storage.ts`) creates S3 buckets with intelligent tiering (transition to `INTELLIGENT_TIERING` at day 0), versioning, block public access, enforce SSL, and configurable lifecycle rules. The `ServerSideWebsite` and `StaticWebsite` constructs also create S3 buckets for web asset storage. S3 is the correct choice for unstructured data. However, no parsing pipeline is provided — no Textract, Tika, or document processing constructs exist. |
| **Gap** | No document parsing or extraction pipeline. Users storing documents in the Storage construct have no built-in way to make content searchable or processable. |
| **Recommendation** | Consider adding an optional document processing pipeline construct using Amazon Textract or Amazon Comprehend for users who need to parse and index unstructured data stored in S3. This could integrate with Amazon OpenSearch for full-text search capabilities and Amazon Bedrock for AI-powered document understanding. |
| **Evidence** | `src/constructs/aws/Storage.ts` (S3 with INTELLIGENT_TIERING, versioned, blockPublicAccess, enforceSSL), `src/constructs/aws/ServerSideWebsite.ts` (S3 for assets), `src/constructs/aws/abstracts/StaticWebsiteAbstract.ts` (S3 for static sites) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The codebase has a centralized pattern for all AWS API interactions. The `awsRequest` function in `src/classes/aws.ts` provides a single entry point for AWS SDK calls, wrapping the Serverless Framework's legacy provider. The `AwsProvider.request()` method in `src/providers/AwsProvider.ts` delegates to `awsRequest()`. CloudFormation stack output retrieval is centralized in `src/CloudFormation.ts` via `getStackOutput()`. All constructs access AWS services exclusively through these centralized methods — no scattered direct SDK calls. The `StripeProvider` also centralizes Stripe API access through its `sdk` property. |
| **Gap** | None. Data access is fully centralized through the provider pattern. |
| **Recommendation** | No action needed. The centralized request pattern is well-implemented. |
| **Evidence** | `src/classes/aws.ts` (awsRequest, emptyBucket, invalidateCloudFrontCache), `src/CloudFormation.ts` (getStackOutput), `src/providers/AwsProvider.ts` (request method) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The only database construct is `DatabaseDynamoDBSingleTable` (`src/constructs/aws/DatabaseDynamoDBSingleTable.ts`), which creates a DynamoDB table. DynamoDB is a fully managed NoSQL service — AWS manages all engine versions, patches, and upgrades transparently. There is no engine version to pin, no EOL risk, and no manual update procedure needed. No RDS, DocumentDB, ElastiCache, or other versioned database engines are present in the codebase. |
| **Gap** | None. DynamoDB has no engine version management concerns. |
| **Recommendation** | No action needed. If RDS or Aurora constructs are added in the future, ensure engine version pinning is a required configuration parameter with validation against EOL databases. Prefer Aurora PostgreSQL or Aurora MySQL, aligned with the preference for `aurora`. |
| **Evidence** | `src/constructs/aws/DatabaseDynamoDBSingleTable.ts` (DynamoDB — no engine version parameter) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs exist in the codebase. The `DatabaseDynamoDBSingleTable` construct uses standard DynamoDB operations — it defines partition keys (`PK`), sort keys (`SK`), GSIs, LSIs, and streams, all through the CDK DynamoDB API. All business logic resides in the TypeScript application layer. No `.sql` files, no `CREATE PROCEDURE`, no `CREATE TRIGGER`, and no proprietary SQL dialects detected. |
| **Gap** | None. All logic is in the application layer. |
| **Recommendation** | No action needed. Continue keeping business logic in the application layer as the construct library expands. |
| **Evidence** | `src/constructs/aws/DatabaseDynamoDBSingleTable.ts` (DynamoDB API only — PK, SK, GSI, LSI, Streams) |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail configuration exists in any construct. The plugin does not generate CloudTrail resources, S3 buckets with log file validation, or CloudWatch log retention policies for audit purposes. No `aws_cloudtrail` equivalent CDK constructs are present. While CloudTrail may be configured separately by users at the account level, the plugin provides no audit logging constructs or guidance. |
| **Gap** | No audit logging construct provided. Users deploying with Lift have no built-in CloudTrail or audit logging setup. This is a significant gap for compliance-sensitive workloads. |
| **Recommendation** | Add an optional CloudTrail construct or account-level security baseline construct that configures CloudTrail with log file validation and immutable S3 storage (Object Lock). At minimum, document the expectation that users configure CloudTrail at the account level outside of Lift. |
| **Evidence** | Searched all `src/constructs/aws/*.ts` files — no CloudTrail, no audit logging resources found |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The `Storage` construct (`src/constructs/aws/Storage.ts`) defaults to `BucketEncryption.S3_MANAGED` with an option for `BucketEncryption.KMS_MANAGED`. The `Queue` construct (`src/constructs/aws/Queue.ts`) supports SQS encryption with `kmsManaged` and `kms` options (including customer-managed KMS keys). DynamoDB has encryption at rest enabled by default in AWS. However, the default encryption for Storage is S3-managed (not customer-managed KMS), and there is no centralized key management or documented rotation policy. The `ServerSideWebsite` and `StaticWebsite` bucket constructs do not configure any explicit encryption. |
| **Gap** | Default encryption is AWS-managed, not customer-managed KMS. No centralized key management. No documented key rotation policy. Website asset buckets (`ServerSideWebsite`, `StaticWebsite`) have no explicit encryption configuration — they rely on S3 default encryption which may or may not be enabled at the account level. |
| **Recommendation** | Consider defaulting to customer-managed KMS keys for the Storage and Queue constructs. Add explicit encryption configuration to the website asset buckets. Add a key rotation policy option. Consider providing a centralized KMS key construct that other constructs can reference. |
| **Evidence** | `src/constructs/aws/Storage.ts` (BucketEncryption.S3_MANAGED default, KMS_MANAGED option), `src/constructs/aws/Queue.ts` (encryption options: kmsManaged, kms), `src/constructs/aws/ServerSideWebsite.ts` (no encryption on Assets bucket) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The `Webhook` construct (`src/constructs/aws/Webhook.ts`) enforces authentication by default — it requires either an `authorizer` (Lambda authorizer) or explicit `insecure: true` flag. The construct throws an error if neither is provided, and throws an error if both are specified (mutually exclusive). The authorizer is a custom Lambda function with `REQUEST` type and `enableSimpleResponses: true`. However, this is a custom Lambda authorizer, not OAuth2/JWT or a centralized IdP integration. The `ServerSideWebsite` construct has no authentication mechanism on the CloudFront distribution. |
| **Gap** | Authentication is custom Lambda-based, not OAuth2/JWT or centralized IdP. No Cognito integration or JWT authorizer option. The `ServerSideWebsite` construct has no authentication for its CloudFront distribution. |
| **Recommendation** | Add a JWT authorizer option to the Webhook construct using API Gateway's built-in JWT authorizer with Cognito or external IdPs. Consider adding CloudFront Functions or Lambda@Edge authentication for the `ServerSideWebsite` construct. Align with the preference for `api-gateway` by leveraging API Gateway's native auth capabilities. |
| **Evidence** | `src/constructs/aws/Webhook.ts` (CfnAuthorizer with authorizerType: "REQUEST", insecure flag validation), `src/constructs/aws/ServerSideWebsite.ts` (no auth on CloudFront) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No Cognito user pool, Okta, SAML, or OIDC integration exists in any construct. The `Webhook` construct's authorizer is a custom Lambda function — not a centralized IdP. The `StripeProvider` authenticates via local API keys (environment variable or config file), not through a centralized identity system. No `aws_cognito_*` equivalent CDK constructs found. |
| **Gap** | No centralized identity provider integration. Applications built with Lift must implement their own authentication entirely, with no reusable identity patterns provided by the plugin. |
| **Recommendation** | Add a Cognito user pool construct or authentication construct that integrates with API Gateway's JWT authorizer. This would provide users with a turnkey authentication solution. Consider supporting OIDC federation for enterprise use cases. |
| **Evidence** | Searched all `src/constructs/aws/*.ts` and `src/providers/*.ts` — no Cognito, no OIDC, no SAML, no IdP resources found. `src/providers/StripeProvider.ts` (API key from env/file) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The `StripeProvider` (`src/providers/StripeProvider.ts`) reads API keys from the `STRIPE_API_KEY` environment variable or from a local TOML config file (`~/.config/stripe/config.toml`). This is environment-variable-based secrets management with no encryption, rotation, or centralized secrets store. No `aws_secretsmanager_*` or HashiCorp Vault integration exists in any construct or provider. The Queue, Storage, and other constructs do not handle secrets directly, but users building on top of Lift have no built-in secrets management pattern. |
| **Gap** | API keys sourced from environment variables or local config files with no encryption or rotation. No Secrets Manager or Vault integration. |
| **Recommendation** | Integrate Secrets Manager for the StripeProvider — read the Stripe API key from Secrets Manager with automated rotation instead of environment variables. Add a Secrets Manager integration pattern that other constructs can reference for database credentials and API keys. |
| **Evidence** | `src/providers/StripeProvider.ts` (process.env.STRIPE_API_KEY, ~/.config/stripe/config.toml) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The plugin targets Lambda functions exclusively for compute — Lambda runtime patching is managed by AWS. No EC2 instances, no custom AMIs, and no SSM Patch Manager needed. However, there is no AWS Inspector, Snyk, or vulnerability scanning configuration for the Lambda functions generated by the constructs. No hardened base images (since Lambda uses AWS-managed runtimes). The `package.json` specifies `engines: { node: ">=14.15.0" }` — Node.js 14 reached EOL in April 2023. |
| **Gap** | No vulnerability scanning for Lambda functions. The `engines` field specifies Node.js 14+ which is past EOL. No Lambda runtime version enforcement in generated CloudFormation. |
| **Recommendation** | Update the `engines` field to require Node.js 18+ (current LTS minimum). Add Lambda runtime version validation to constructs that generate Lambda functions. Consider adding an optional AWS Inspector integration construct. |
| **Evidence** | `package.json` (engines: node >= 14.15.0), Lambda compute generated by Queue and Webhook constructs (no runtime version enforcement) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The CI pipeline (`.github/workflows/ci.yml`) runs unit tests, eslint, prettier, and TypeScript type checks. However, there is no SAST tool (no SonarQube, Semgrep, or CodeGuru), no dependency vulnerability scanning (no Dependabot, no `npm audit`, no Snyk), no container scanning (not applicable — no containers), and no security gates in the pipeline. The eslint configuration (`.eslintrc`) includes code quality rules but no security-focused rules (no eslint-plugin-security). |
| **Gap** | No security scanning tools configured. No Dependabot, no `npm audit`, no SAST tool, no container scanning. The pipeline has no security validation step whatsoever. Given that this is a library published to npm and used by many downstream projects, vulnerable dependencies could propagate widely. |
| **Recommendation** | Add `npm audit --audit-level=high` as a CI step. Enable Dependabot or Renovate for automated dependency updates. Add a SAST tool (Semgrep or SonarQube) to the CI pipeline. Add `eslint-plugin-security` to the eslint configuration. Consider adding a security gate that blocks releases on critical findings. |
| **Evidence** | `.github/workflows/ci.yml` (no security scanning steps), `.eslintrc` (no security plugins), no `.snyk` file, no `dependabot.yml` in `.github/` |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No X-Ray, OpenTelemetry, or any tracing instrumentation found in the plugin code, constructs, or dependency manifests. The constructs that generate Lambda functions (Queue, Webhook, ServerSideWebsite) do not enable X-Ray tracing on those functions. No `aws-xray-sdk` or `@opentelemetry/*` packages in `package.json`. No tracing configuration in API Gateway or CloudFront constructs. |
| **Gap** | No tracing instrumentation whatsoever. Lambda functions generated by constructs have no X-Ray tracing enabled. API Gateway has no tracing configured. Users must manually add tracing to all resources created by Lift. |
| **Recommendation** | Add optional X-Ray tracing configuration to Lambda-backed constructs (Queue worker, Webhook authorizer). Enable API Gateway tracing in the Webhook construct. Consider adding an OpenTelemetry layer option for Lambda functions. |
| **Evidence** | `package.json` (no tracing dependencies), `src/constructs/aws/Queue.ts` (no tracing on worker Lambda), `src/constructs/aws/Webhook.ts` (no tracing on HttpApi or authorizer Lambda) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions, error budgets, or SLO-focused CloudWatch alarms found in any construct. The Queue construct supports an optional DLQ alarm (email notification when messages appear in the dead letter queue), but this is a failure notification, not an SLO definition. No p99/p95 latency alarms, no availability SLOs, no error budget tracking. |
| **Gap** | No SLO definitions for any construct. Users deploying with Lift have no built-in SLO monitoring for their queues, websites, or APIs. |
| **Recommendation** | Add optional SLO configuration to constructs — e.g., Queue construct could expose `sloProcessingTime` and `sloErrorRate` options that create CloudWatch alarms with appropriate thresholds. Website constructs could expose `sloAvailability` and `sloLatencyP99` options backed by CloudFront metrics. |
| **Evidence** | `src/constructs/aws/Queue.ts` (alarm for DLQ messages only — not an SLO), no SLO configuration in any construct |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom CloudWatch metric publishing in any construct. The Queue construct's DLQ alarm uses the built-in `AWS/SQS` namespace metric `ApproximateNumberOfMessagesVisible` — this is an infrastructure metric, not a business metric. No `cloudwatch.put_metric_data` equivalent calls for business outcomes. No custom metric namespaces defined. |
| **Gap** | No custom business metrics. Constructs rely entirely on default AWS service metrics with no business-outcome instrumentation. |
| **Recommendation** | Consider adding optional custom metric publishing to constructs — e.g., Queue construct could publish `MessagesProcessedSuccessfully` and `MessageProcessingDuration` custom metrics. Website constructs could publish `PageLoadTime` and `ErrorsByPath` custom metrics via CloudFront real-time logs. |
| **Evidence** | `src/constructs/aws/Queue.ts` (Metric namespace: "AWS/SQS" — infrastructure metric only) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The Queue construct (`src/constructs/aws/Queue.ts`) creates a static threshold alarm for DLQ messages: `ApproximateNumberOfMessagesVisible > 0` with `evaluationPeriods: 1` and `treatMissingData: TreatMissingData.NOT_BREACHING`. This is a basic alerting mechanism but uses only static thresholds. No CloudWatch anomaly detection, no composite alarms, no PagerDuty/OpsGenie integration. No other constructs have any alerting. |
| **Gap** | Only one static threshold alarm exists (Queue DLQ). No anomaly detection. No alerting on other constructs (websites, storage, database). No composite alarms. |
| **Recommendation** | Add anomaly detection-based alarms for key metrics across constructs. Add optional alerting configuration to all constructs (e.g., website constructs could alert on 5xx error rate anomalies, database construct could alert on throttling). Consider adding composite alarm support. |
| **Evidence** | `src/constructs/aws/Queue.ts` (Alarm with ComparisonOperator.GREATER_THAN_THRESHOLD, threshold: 0, TreatMissingData.NOT_BREACHING) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The release pipeline (`.github/workflows/release.yml`) publishes the npm package directly on GitHub Release events with `npm publish --access public`. This is a publish pipeline for a library, not a service deployment strategy. There is no blue/green, canary, or staged rollout mechanism. The npm publish is a single-shot operation with no rollback capability. For constructs that generate Lambda functions, no deployment strategy is configured — Lambda functions deploy directly via CloudFormation with no traffic shifting. |
| **Gap** | No staged deployment strategy for npm publishes. No Lambda deployment preferences (canary, linear, all-at-once) configured in generated Lambda functions. Direct-to-production npm publish with no staged rollout. |
| **Recommendation** | For the library itself: consider publishing to a `next` npm tag first, validating, then promoting to `latest`. For generated Lambda functions: add optional deployment preference configuration (canary, linear) using CodeDeploy integration, aligned with AWS best practices for Lambda deployments. |
| **Evidence** | `.github/workflows/release.yml` (direct npm publish, no staging), `src/constructs/aws/Queue.ts` (Lambda worker with no deployment preference) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The repository has 14 test files in `test/unit/` covering all constructs: queues, storage, webhooks, VPC, databases, static websites, single page apps, server-side websites, Stripe, permissions, variables, extensions, and common functionality. Tests use Jest with `ts-jest`, sinon for mocking, and the `@serverless/test` utilities for running Serverless Framework in test mode (`runServerless` in `test/utils/`). Tests verify CloudFormation template generation by checking resource properties. However, these are unit tests — they mock AWS calls and do not test against live AWS services. No integration test directory, no Localstack, no test containers, no end-to-end deployment tests. |
| **Gap** | All tests are unit tests that mock AWS interactions. No integration tests against live services. No end-to-end tests that deploy constructs and verify the deployed infrastructure. |
| **Recommendation** | Add integration tests that deploy constructs to a test AWS account and verify the created resources. Use Localstack or AWS CDK assertions for construct-level integration testing. Add end-to-end tests for critical construct paths (e.g., Queue: deploy → send message → verify worker invocation). |
| **Evidence** | `test/unit/` (14 test files), `jest.config.js` (ts-jest preset), `test/utils/` (runServerless, mockAws utilities) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, no automated remediation, no incident response automation found in the repository. No Systems Manager Automation documents, no Lambda-based remediation, no Step Functions incident workflows. The Queue construct's DLQ alarm sends an email notification but provides no automated remediation. The `failed:retry` CLI command (`src/constructs/aws/Queue.ts`) is a manual remediation tool, not an automated response. |
| **Gap** | No incident response automation. No runbooks (markdown, YAML, or machine-readable). No self-healing patterns. |
| **Recommendation** | Add runbook documentation for common operational scenarios (e.g., DLQ message accumulation, CloudFront cache issues, S3 sync failures). Consider adding an automated remediation construct that creates Step Functions workflows for common incident responses, such as automatic DLQ retry. |
| **Evidence** | No runbook files found in repository. `src/constructs/aws/Queue.ts` (manual `failed:retry` command, email alarm notification) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CODEOWNERS file found in the repository. No per-service dashboards defined in any construct. No team attribution on the Queue DLQ alarm. No SLO definitions with team ownership. The `.github/` directory contains `CONTRIBUTING.md` and `pull_request_template.md` but no CODEOWNERS. |
| **Gap** | No observability ownership patterns. No CODEOWNERS for observability configs. No team-attributed dashboards or alarms. |
| **Recommendation** | Add a CODEOWNERS file with ownership attribution for observability configurations. Consider adding optional `owner` and `team` tags to construct alarm and dashboard resources. Add per-construct CloudWatch dashboard generation. |
| **Evidence** | No CODEOWNERS file in `.github/`. `src/constructs/aws/Queue.ts` (alarm with no owner attribution) |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No default tags or tagging governance found in any construct. Resources created by the plugin (DynamoDB tables, S3 buckets, SQS queues, CloudFront distributions, API Gateway, VPCs, security groups) have no tags applied. No `tags` property in any construct configuration schema. No `default_tags` equivalent in the CDK stack configuration. No AWS Config required-tags rules or Tag Policies. |
| **Gap** | All resources created by Lift constructs have zero tags. No cost allocation, no ownership attribution, no environment identification. This is a critical gap for organizations that rely on tagging for cost management and governance. |
| **Recommendation** | Add a global `tags` configuration option in the Lift plugin configuration (`lift.tags` in serverless.yml) that applies default tags to all resources created by all constructs. Support per-construct tag overrides. Include `Environment`, `Service`, `Owner`, and `ManagedBy: serverless-lift` as recommended default tags. Leverage CDK's `Tags.of(scope).add()` for propagation. |
| **Evidence** | All `src/constructs/aws/*.ts` files — no `Tags` or `tags` property usage. `src/plugin.ts` — no tag configuration in LIFT_CONFIG_SCHEMA |

---

## Learning Materials

No pathways triggered — no pathway-specific learning materials applicable. Refer to the [AWS SkillBuilder](https://skillbuilder.aws/) catalog for general cloud architecture training.

**General recommendations based on analysis findings:**
- [AWS Security Best Practices](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html) — Address SEC gaps
- [AWS Observability Best Practices](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Observability-Best-Practices.html) — Address OPS gaps
- [Operational Excellence Pillar - AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/welcome.html) — General operational maturity

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `package.json` | APP-Q1, APP-Q5, SEC-Q6, SEC-Q7, OPS-Q1 | Dependency manifests, engines field, TypeScript version, peer dependencies |
| `tsconfig.json` | APP-Q1, APP-Q2 | TypeScript configuration, path aliases for module boundaries |
| `src/plugin.ts` | INF-Q3, INF-Q4, INF-Q10, APP-Q2, APP-Q3, APP-Q4, OPS-Q9 | Plugin entry point, hook lifecycle, eject command, schema registration |
| `src/providers/AwsProvider.ts` | INF-Q1, INF-Q2, INF-Q10, APP-Q2, APP-Q6, DATA-Q2 | CDK synthesis, construct registration, AWS request delegation |
| `src/providers/StripeProvider.ts` | SEC-Q4, SEC-Q5 | Stripe API key management via env vars and config file |
| `src/constructs/ConstructInterface.ts` | APP-Q2 | Construct contract interface definition |
| `src/constructs/StaticConstructInterface.ts` | APP-Q2 | Static construct contract with type, schema, create, commands |
| `src/providers/ProviderInterface.ts` | APP-Q2 | Provider contract interface definition |
| `src/constructs/aws/Queue.ts` | INF-Q1, INF-Q4, INF-Q7, OPS-Q1, OPS-Q2, OPS-Q3, OPS-Q4, OPS-Q5, OPS-Q7, OPS-Q8, SEC-Q2 | SQS queue, DLQ, alarm, Lambda worker, encryption options |
| `src/constructs/aws/Storage.ts` | INF-Q1, INF-Q8, DATA-Q1, SEC-Q2 | S3 bucket with intelligent tiering, versioning, encryption |
| `src/constructs/aws/Webhook.ts` | INF-Q1, INF-Q4, INF-Q6, SEC-Q3, OPS-Q1 | API Gateway HttpApi, EventBridge, Lambda authorizer |
| `src/constructs/aws/Vpc.ts` | INF-Q5, INF-Q9 | VPC with maxAzs: 2, private subnets, security groups |
| `src/constructs/aws/DatabaseDynamoDBSingleTable.ts` | INF-Q2, INF-Q7, INF-Q8, INF-Q9, DATA-Q3, DATA-Q4 | DynamoDB table with PAY_PER_REQUEST, PITR, streams |
| `src/constructs/aws/ServerSideWebsite.ts` | INF-Q1, INF-Q6, INF-Q9, DATA-Q1, SEC-Q2, SEC-Q3 | CloudFront distribution, S3 assets, API Gateway backend |
| `src/constructs/aws/SinglePageApp.ts` | INF-Q6, DATA-Q1 | CloudFront + S3 static site |
| `src/constructs/aws/StaticWebsite.ts` | INF-Q6, DATA-Q1, SEC-Q2 | CloudFront + S3 static website with public access |
| `src/constructs/aws/abstracts/StaticWebsiteAbstract.ts` | INF-Q6, DATA-Q1, SEC-Q2 | Base class for static websites with CloudFront, S3Origin |
| `src/classes/aws.ts` | INF-Q4, APP-Q3, DATA-Q2 | Centralized AWS request function, S3 operations, CloudFront invalidation |
| `src/CloudFormation.ts` | APP-Q3, DATA-Q2 | Centralized CloudFormation stack output retrieval |
| `src/constructs/aws/queue/sqs.ts` | APP-Q4 | SQS polling and retry message functions |
| `src/utils/sleep.ts` | APP-Q4 | Bounded sleep utility |
| `.github/workflows/ci.yml` | INF-Q11, SEC-Q7, OPS-Q5, OPS-Q6 | CI pipeline with unit tests, lint, type checks |
| `.github/workflows/release.yml` | INF-Q11, APP-Q5, OPS-Q5 | npm publish pipeline with OIDC |
| `.eslintrc` | SEC-Q7 | ESLint configuration with no security plugins |
| `test/unit/` | OPS-Q6 | 14 unit test files covering all constructs |
| `jest.config.js` | OPS-Q6 | Jest configuration with ts-jest |
| `README.md` | Quick Agent Wins | Plugin documentation and usage guide |
| `docs/` | Quick Agent Wins | 11 Markdown documentation files for all constructs |
| `.github/CONTRIBUTING.md` | OPS-Q8 | Contributing guide (no CODEOWNERS) |
