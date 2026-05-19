# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | books-api |
| **Date** | 2026-05-18 |
| **TD Version** | modernization-readiness-analysis |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P1 |
| **Tags** | serverless, cdk, api, dynamodb |
| **Context** | Serverless REST API with CDK infrastructure for book catalog management. Clean API surface the agent can use as a tool for product lookups. |
| **Overall Score** | 3.00 / 4.0 |

**Archetype Justification**: DynamoDB table provides persistent state; POST /books creates records and GET /books reads them. The service owns its data and exposes CRUD operations on book entities. Classified as stateful-crud.

**Surface Flags**: has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=true, has_iac_provisioning_aws_resources=true

**Classification: 🟡 Pilot-Ready**

This repo has 0 High findings, 12 Medium findings, 7 Low findings. Rule matched: "0 High, ≥2 Medium → Pilot-Ready". MOD classification uses a softer model than ARA — in ARA, 1 High is an agent-deployment blocker; in MOD, 1 High represents a single modernization gap and maps to Pilot-Ready rather than Remediation Required.

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure & DevOps (INF) | 3.36 / 4.0 | 🟡 Partial | Needs Work |
| Application Architecture (APP) | 3.00 / 4.0 | 🟡 Partial | Needs Work |
| Data Platform (DATA) | 3.50 / 4.0 | ✅ Mature | Needs Work |
| Security Baseline (SEC) | 2.83 / 4.0 | 🟡 Partial | Needs Work |
| Operations & Observability (OPS) | 2.33 / 4.0 | 🟠 Needs Work | Needs Work |
| **Overall** | **3.00 / 4.0** | **🟡 Partial** | |

### Scoring Notes

- INF: (4+4+4+4+3+3+2+1+4+4+4) / 11 = 37/11 = 3.36
- APP: (3+4+4+4+1+2) / 6 = 18/6 = 3.00
- DATA: (4+2+4+4) / 4 = 14/4 = 3.50
- SEC: (3+3+3+4+3+1) / 6 = 17/6 = 2.83 (SEC-Q1 Not Evaluated — excluded)
- OPS: (4+2+1+2+4+4+1+1+2) / 9 = 21/9 = 2.33
- Overall: (3.36+3.00+3.50+2.83+2.33) / 5 = 15.02/5 = 3.00

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | SEC-Q7: Application Security Pipeline | 1 | No SAST, dependency scanning, or security gates in CI/CD pipeline | Vulnerabilities in dependencies or code reach production undetected |
| 2 | INF-Q8: Backup and Recovery | 1 | No PITR or backup configuration for DynamoDB table | Data loss event has no recovery path |
| 3 | APP-Q5: API Versioning Strategy | 1 | No API versioning on any endpoint | Breaking changes affect all consumers simultaneously |
| 4 | OPS-Q3: Business Metrics | 1 | No custom business metrics published | Cannot measure whether system delivers business value |
| 5 | OPS-Q7: Incident Response Automation | 1 | No runbooks or automated incident response | Incident resolution depends entirely on ad hoc human action |

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 4 — already microservices/serverless architecture |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 4 — compute already on Lambda (serverless); contextual guard prevents trigger |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 — no stored procedures or proprietary SQL; DynamoDB is not a commercial DB |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = 4 — DynamoDB is fully managed |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 4 — no data processing workloads exist; contextual guard prevents trigger |
| 6 | Move to Modern DevOps | Not Triggered | — | — | INF-Q10 = 4, INF-Q11 = 4 — full IaC coverage and CI/CD automation in place |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context |

No pathways triggered — this serverless application already uses managed services, has full IaC coverage, and automated CI/CD. Remaining gaps are operational maturity improvements rather than modernization pathway candidates.

---

## Detailed Findings

### Infrastructure & DevOps (INF)

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 4 ✅ Mature |
| **Finding** | All compute runs on AWS Lambda (serverless). Runtime is nodejs22.x. No EC2 instances. Functions use esbuild for bundling with SAM BuildMethod. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `template.yml` — `AWS::Serverless::Function` resources (GetAllBooks, CreateBook, CreateBookPreTraffic); Globals.Function.Runtime: nodejs22.x |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 4 ✅ Mature |
| **Finding** | DynamoDB (fully managed) via `AWS::Serverless::SimpleTable` with SSE enabled. No self-managed databases. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `template.yml` — BooksTable resource with SSESpecification.SSEEnabled: true |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 4 ✅ Mature |
| **Finding** | This stateful-crud service has no multi-step business workflows requiring orchestration. Operations are simple single-step CRUD (DynamoDB putItem, scan). The pre-traffic hook is a deployment concern handled by CodeDeploy, not a business workflow. |
| **Gap** | N/A |
| **Recommendation** | N/A — dedicated workflow orchestration is not needed for this service's current operations. |
| **Evidence** | `src/books/create/index.ts` — single DDB putItem; `src/books/get-all/index.ts` — single DDB scan |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 4 ✅ Mature |
| **Finding** | This stateful-crud service is self-contained with no cross-service state propagation. API Gateway → Lambda → DynamoDB is the complete data flow. State changes (book creation) do not need to propagate to downstream consumers. Synchronous request/response is appropriate for this standalone CRUD service. |
| **Gap** | N/A |
| **Recommendation** | N/A — adopting async messaging is not recommended for this self-contained service as it would add operational complexity without architectural benefit. If future requirements add downstream consumers (e.g., notifications on book creation), consider EventBridge for event-driven integration. |
| **Evidence** | `src/books/create/index.ts`, `src/books/get-all/index.ts` — no message publishing, no event emission, no downstream service calls |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 3 🟡 Partial |
| **Severity** | Low |
| **Finding** | Lambda functions run in AWS-managed network space (no customer VPC required for this architecture). API Gateway provides the entry point with Cognito authorization on write endpoints. DynamoDB access is controlled via IAM policy (DynamoDBReadPolicy, DynamoDBWritePolicy). No overly permissive rules detected. |
| **Gap** | No VPC endpoints for DynamoDB access (traffic traverses public AWS network rather than private link). No WAF configured on API Gateway. |
| **Recommendation** | Consider adding AWS WAF on API Gateway for rate limiting and IP-based controls. For sensitive data workloads, consider placing Lambda in a VPC with VPC endpoints for DynamoDB. For this public book catalog API, current posture is acceptable. |
| **Evidence** | `template.yml` — API Gateway with CognitoAuth; Lambda functions without VpcConfig; IAM policies with least-privilege (DynamoDBReadPolicy, DynamoDBWritePolicy) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 3 🟡 Partial |
| **Severity** | Low |
| **Finding** | API Gateway (AWS::Serverless::Api) serves as the entry point with Cognito authorization, CloudWatch logging (INFO level), and X-Ray tracing enabled. Default API Gateway throttling applies. |
| **Gap** | No explicit throttling configuration (uses API Gateway account-level defaults). No request validation models defined to reject malformed requests before reaching Lambda. |
| **Recommendation** | Add API Gateway request validators and models to reject invalid payloads at the gateway level. Configure per-method throttling appropriate to the expected load profile. |
| **Evidence** | `template.yml` — BooksApi resource with MethodSettings (LoggingLevel: INFO), TracingEnabled: true, Auth.Authorizers.CognitoAuth |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 2 🟠 Needs Work |
| **Severity** | Medium |
| **Finding** | Lambda functions auto-scale inherently (no concurrency limits configured). DynamoDB SimpleTable uses default provisioned capacity (5 RCU/5 WCU) with no auto-scaling configured and no on-demand billing mode specified. |
| **Gap** | DynamoDB table has static provisioned capacity with no auto-scaling. Under load, the table will throttle reads/writes at 5 capacity units. |
| **Recommendation** | Switch DynamoDB to on-demand billing mode (`BillingMode: PAY_PER_REQUEST`) for unpredictable workloads, or configure Application Auto Scaling on provisioned capacity. For a book catalog API, on-demand is simpler and more appropriate. |
| **Evidence** | `template.yml` — BooksTable (AWS::Serverless::SimpleTable) with no BillingMode or auto-scaling configuration; Lambda functions with no ReservedConcurrentExecutions |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 ❌ Not Ready |
| **Severity** | Medium |
| **Finding** | No backup or point-in-time recovery (PITR) configured for the DynamoDB table. No AWS Backup plan defined. |
| **Gap** | A data loss event (accidental deletion, application bug writing bad data) has no recovery path. DynamoDB PITR is not enabled. |
| **Recommendation** | Enable DynamoDB Point-in-Time Recovery (PITR) on the BooksTable. Add `PointInTimeRecoverySpecification: PointInTimeRecoveryEnabled: true` to the table definition. Consider AWS Backup for automated backup management with defined retention. |
| **Evidence** | `template.yml` — BooksTable has no PointInTimeRecoverySpecification; no aws_backup_plan or equivalent resource |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 4 ✅ Mature |
| **Finding** | All components are inherently multi-AZ: Lambda runs across multiple AZs automatically, DynamoDB replicates across 3 AZs within a region, and API Gateway is a regional service spanning multiple AZs. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `template.yml` — all resources are managed services with built-in multi-AZ (Lambda, DynamoDB, API Gateway, Cognito) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 4 ✅ Mature |
| **Finding** | All infrastructure is defined in IaC: SAM template covers compute (Lambda), database (DynamoDB), API (API Gateway), auth (Cognito), monitoring (CloudWatch Alarms), and deployment configuration. CDK covers the CI/CD pipeline (CodePipeline, CodeBuild, S3 artifact buckets). No evidence of manually-created resources. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `template.yml` — all application resources; `pipeline/lib/pipeline-stack.ts` — CI/CD pipeline resources |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 4 ✅ Mature |
| **Finding** | Full CI/CD pipeline via CDK-defined CodePipeline with 4 stages: Source (CodeStar Connections to GitHub) → Build (SAM build + unit tests) → Staging (deploy + end-to-end tests) → Production (manual approval + deploy). Automated rollback via CodeDeploy Linear10PercentEvery1Minute with CloudWatch Alarm triggers. Pre-traffic hooks validate new Lambda versions. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `pipeline/lib/pipeline-stack.ts` — full pipeline definition; `pipeline/buildspec.json` — build + unit tests; `pipeline/buildspec-test.json` — e2e tests; `pipeline/buildspec-deploy.json` — SAM deploy; `template.yml` — DeploymentPreference with Alarms |

### Application Architecture (APP)

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 3 🟡 Partial |
| **Severity** | Low |
| **Finding** | TypeScript 5.7 on Node.js 22.x — modern language and runtime. However, the application uses AWS SDK v2 (`aws-sdk` ^2.1692.0) instead of AWS SDK v3 (`@aws-sdk/*`). SDK v2 is in maintenance mode and does not receive new features. |
| **Gap** | AWS SDK v2 usage. SDK v2 is maintenance-mode; v3 provides modular imports (smaller bundles for Lambda cold starts), middleware stack, and first-class TypeScript support. |
| **Recommendation** | Migrate from `aws-sdk` v2 to `@aws-sdk/client-dynamodb` and `@aws-sdk/lib-dynamodb` (v3). This reduces bundle size, improves cold start times, and provides better TypeScript types. Also migrate `aws-xray-sdk-core` to the OpenTelemetry-based X-Ray instrumentation for SDK v3. |
| **Evidence** | `src/books/create/package.json` — `"aws-sdk": "^2.1692.0"`; `src/books/get-all/package.json` — same; `src/books/create/index.ts` — `import * as AWSCore from 'aws-sdk'` |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 4 ✅ Mature |
| **Finding** | Serverless microservice architecture. Each Lambda function (GetAllBooks, CreateBook) is independently deployable and scalable. Single bounded context (books) with a dedicated DynamoDB table. Clear API boundaries via API Gateway. No circular dependencies or shared mutable state beyond the DynamoDB table owned by this service. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `template.yml` — independent Lambda functions with separate CodeUri, policies, and deployment preferences; single DynamoDB table owned by this service |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 4 ✅ Mature |
| **Finding** | This stateful-crud service is self-contained with no inter-service communication. API Gateway → Lambda → DynamoDB is the complete flow. No downstream service calls, no synchronous coupling to other services. The absence of async is not a gap — there are no cross-service state changes that need propagation. |
| **Gap** | N/A |
| **Recommendation** | N/A — no inter-service communication exists to optimize. If future requirements introduce downstream consumers for book state changes, adopt EventBridge for event-driven integration. |
| **Evidence** | `src/books/create/index.ts`, `src/books/get-all/index.ts` — no HTTP client calls, no message publishing, no event emission to other services |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 4 ✅ Mature |
| **Finding** | All operations complete well within the 5-second Lambda timeout. DynamoDB putItem and scan operations complete in single-digit milliseconds. No operations approach 30 seconds. The architecture structurally prevents long-running operations. |
| **Gap** | N/A |
| **Recommendation** | N/A — async job infrastructure is not applicable for this service's current operations. |
| **Evidence** | `template.yml` — Globals.Function.Timeout: 5; `src/books/create/index.ts` — single DDB putItem; `src/books/get-all/index.ts` — single DDB scan |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 ❌ Not Ready |
| **Severity** | Medium |
| **Finding** | No API versioning strategy found. Endpoints are `/books` with no version prefix, no version headers, and no versioning annotations. |
| **Gap** | Breaking changes to the API (schema changes, removed fields) would affect all consumers simultaneously with no migration path. For a service intended as an agent tool for product lookups, this is a higher risk since agent integrations are brittle to schema changes. |
| **Recommendation** | Adopt URL-path versioning (`/v1/books`) as the simplest approach for REST APIs. Define the versioning strategy before adding new endpoints or modifying the book schema. For API Gateway, this can be implemented via stage variables or base path mappings. |
| **Evidence** | `template.yml` — ApiEvent.Path: /books (no version prefix); no version headers or annotations in source code |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 🟠 Needs Work |
| **Severity** | Medium |
| **Finding** | Environment variables configure service endpoints: TABLE environment variable for DynamoDB table name, FN_NEW_VERSION for Lambda function ARN. No dynamic service discovery mechanism. |
| **Gap** | No service registry or catalog. For a standalone serverless service communicating only with AWS managed services (DynamoDB), this is typical — AWS services are discovered via IAM + resource names rather than service registries. However, no API catalog exists to make this service discoverable by other services or agents. |
| **Recommendation** | For agent discoverability, publish an OpenAPI specification as a standalone file and register the API in a service catalog. Consider AWS Service Catalog or API Gateway's built-in export feature to generate the OpenAPI spec. |
| **Evidence** | `template.yml` — Environment.Variables.TABLE: !Ref BooksTable; `src/books/create-pre-traffic/index.ts` — process.env.TABLE, process.env.FN_NEW_VERSION |

### Data Platform (DATA)

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 4 ✅ Mature |
| **Finding** | This service handles only structured data (book records with defined schema: isbn, title, year, author, publisher, rating, pages). No unstructured data (documents, images, files) is stored or processed. There is no unstructured data modernization gap. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/books/create/index.ts` — structured DynamoDB PutItem with typed attributes; `src/books/get-all/index.ts` — structured DDB Scan result mapping |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 2 🟠 Needs Work |
| **Severity** | Medium |
| **Finding** | Each Lambda function directly instantiates a DynamoDB client and executes queries inline. No shared repository/DAO layer, no data access abstraction. The create handler and get-all handler both independently create `new AWS.DynamoDB()` clients with identical configuration. |
| **Gap** | DynamoDB client instantiation and query logic is duplicated across handlers with no shared data access module. Changes to the table schema or access patterns require updates in every handler. |
| **Recommendation** | Extract a shared `books-repository` module that encapsulates DynamoDB client creation, table configuration, and CRUD operations. This centralizes schema knowledge and simplifies SDK v3 migration. |
| **Evidence** | `src/books/create/index.ts` — `new AWS.DynamoDB(ddbOptions)` + putItem inline; `src/books/get-all/index.ts` — `new AWS.DynamoDB(ddbOptions)` + scan inline; identical client configuration duplicated |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 4 ✅ Mature |
| **Finding** | DynamoDB is a fully managed serverless database with no customer-managed engine version. AWS manages all versioning, patching, and lifecycle. No EOL risk. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `template.yml` — AWS::Serverless::SimpleTable (DynamoDB) — no engine version parameter exists |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 ✅ Mature |
| **Finding** | DynamoDB has no stored procedures, triggers, or proprietary SQL constructs. All business logic resides in the application layer (Lambda functions). No database-coupled logic. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/books/create/index.ts` — business logic in Lambda; `src/books/get-all/index.ts` — data transformation in Lambda; no SQL files in repository |

### Security Baseline (SEC)

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (surface-gated) |
| **Finding** | Audit logging (CloudTrail) is an AWS account-level service provisioned once per account or organization — not per-application. This repo contains application-level IaC only (Lambda, DynamoDB, API Gateway, Cognito for this service) which is the correct scope for an application repo. CloudTrail evaluation belongs in the foundation/account-level infrastructure repo. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `template.yml` — application-level resources only; no `AWS::CloudTrail::Trail`, `AWS::Config::*`, or organization-level resources |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 3 🟡 Partial |
| **Severity** | Low |
| **Finding** | DynamoDB table has server-side encryption enabled via `SSESpecification: SSEEnabled: true` (uses AWS-owned keys by default). S3 buckets in CDK pipeline use `BucketEncryption.S3_MANAGED`. All data stores have encryption at rest enabled. |
| **Gap** | Using AWS-managed/owned keys rather than customer-managed KMS keys. No explicit key rotation policy or centralized key management. |
| **Recommendation** | For a public book catalog, AWS-managed encryption is sufficient. If the data sensitivity increases (e.g., user data, purchase history), migrate to customer-managed KMS keys with defined rotation policies. |
| **Evidence** | `template.yml` — BooksTable.SSESpecification.SSEEnabled: true; `pipeline/lib/pipeline-stack.ts` — BucketEncryption.S3_MANAGED on both S3 buckets |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 🟡 Partial |
| **Severity** | Low |
| **Finding** | POST /books requires Cognito OAuth2 authorization with scopes (email + conditional aws.cognito.signin.user.admin). GET /books is intentionally public — reading book listings does not require authentication. API Gateway inherent throttling provides baseline protection for the public endpoint. |
| **Gap** | GET /books is unauthenticated. For a public book catalog this is a valid design choice, but the endpoint lacks explicit rate limiting or API key requirements that would protect against abuse. |
| **Recommendation** | Add API Gateway usage plans with API keys or throttling configuration on the public GET endpoint to prevent abuse. This is a low-priority enhancement for a book catalog but important if the API serves agent consumers at scale. |
| **Evidence** | `template.yml` — CreateBook.Events.ApiEvent.Auth with CognitoAuth and AuthorizationScopes; GetAllBooks.Events.ApiEvent has no Auth block |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 3 🟡 Partial |
| **Severity** | Low |
| **Finding** | AWS Cognito User Pool provides centralized identity management with OAuth2 flows (implicit grant). User Pool Client supports email-based registration with password policy enforcement. |
| **Gap** | Only COGNITO is configured as a supported identity provider — no federation with external IdPs (Okta, Azure AD, SAML). SSO is not enabled. |
| **Recommendation** | If organizational SSO integration is needed, add SAML or OIDC identity provider federation to the Cognito User Pool. For a standalone sample API, Cognito-only is acceptable. |
| **Evidence** | `template.yml` — CognitoUserPool, UserPoolClient with SupportedIdentityProviders: [COGNITO], AllowedOAuthFlows: [implicit] |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 4 ✅ Mature |
| **Finding** | No secrets to manage — the architecture is fully IAM-based. Lambda functions access DynamoDB via IAM roles (DynamoDBReadPolicy, DynamoDBWritePolicy). Cognito handles user authentication tokens. The pipeline stores the GitHub connection ARN in SSM Parameter Store. No hardcoded credentials, no database passwords, no API keys in source code. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `template.yml` — IAM policies via SAM policy templates; `pipeline/lib/pipeline-stack.ts` — StringParameter.fromStringParameterName for GitHub connection; no plaintext credentials in any file |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 3 🟡 Partial |
| **Severity** | Low |
| **Finding** | Lambda managed runtime (nodejs22.x) — AWS handles all OS-level patching and runtime updates. Current Node.js 22 is an active LTS version. No EC2 instances to harden. |
| **Gap** | No dependency vulnerability scanning (no Snyk, no npm audit in pipeline, no AWS Inspector). While the runtime is patched by AWS, application dependencies (aws-sdk, aws-xray-sdk-core, axios) are not scanned for known vulnerabilities. |
| **Recommendation** | Add `npm audit` to the build phase in `pipeline/buildspec.json` as a quick win. For comprehensive scanning, integrate Snyk or AWS Inspector for Lambda function scanning. |
| **Evidence** | `template.yml` — Runtime: nodejs22.x; `pipeline/buildspec.json` — no security scanning commands; `src/books/create/package.json` — dependencies without vulnerability scanning |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 ❌ Not Ready |
| **Severity** | Medium |
| **Finding** | No security scanning tools are configured in the CI/CD pipeline. The buildspec runs `npm test` (unit tests) but has no SAST, DAST, dependency scanning, or container scanning steps. No Dependabot configuration, no `.snyk` policy, no SonarQube or Semgrep integration. |
| **Gap** | Vulnerabilities in application dependencies or source code patterns reach production without any automated security validation. |
| **Recommendation** | Add dependency scanning: configure Dependabot or add `npm audit --audit-level=high` to `pipeline/buildspec.json` pre_build phase. Add SAST: integrate Semgrep or Amazon CodeGuru Reviewer. Both can be added incrementally without pipeline restructuring. |
| **Evidence** | `pipeline/buildspec.json` — only `npm test` in pre_build, no security commands; `pipeline/buildspec-test.json` — only mocha tests; no `.github/dependabot.yml`; no `.snyk` file |

### Operations & Observability (OPS)

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 4 ✅ Mature |
| **Finding** | X-Ray distributed tracing is fully instrumented: Lambda functions have `Tracing: Active` globally, API Gateway has `TracingEnabled: true`, and the application code wraps the AWS SDK with `AWSXRay.captureAWS(AWSCore)` to propagate traces through DynamoDB calls. End-to-end trace visibility from API Gateway → Lambda → DynamoDB. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `template.yml` — Globals.Function.Tracing: Active, BooksApi.TracingEnabled: true; `src/books/create/index.ts` — `AWSXRay.captureAWS(AWSCore)`; `src/books/get-all/index.ts` — same pattern |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 2 🟠 Needs Work |
| **Severity** | Medium |
| **Finding** | CloudWatch Alarms exist for Lambda error counts (Errors > 0 threshold on both functions). These provide basic availability alerting but are not formal SLO definitions. No latency percentile alarms (p99, p95), no error budget tracking. |
| **Gap** | No formal SLOs defined. No latency-based alarms. No error budget tracking or SLO dashboards. |
| **Recommendation** | Define SLOs for the book catalog API: availability target (e.g., 99.9%), latency p99 target (e.g., < 500ms). Add CloudWatch alarms on API Gateway latency metrics (p99). Consider CloudWatch ServiceLevelObjective resource for formal SLO tracking. |
| **Evidence** | `template.yml` — CreateBookAliasErrorMetricGreaterThanZeroAlarm, GetAllBooksAliasErrorMetricGreaterThanZeroAlarm (Errors > 0 threshold alarms only) |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 ❌ Not Ready |
| **Severity** | Medium |
| **Finding** | No custom business metrics published. No CloudWatch putMetricData calls in application code. Only default Lambda and API Gateway infrastructure metrics are available (invocations, errors, duration, 4xx/5xx). |
| **Gap** | Cannot measure business outcomes: books created per day, most-queried books, unique users, API adoption rate. Infrastructure metrics alone cannot answer whether the service delivers value. |
| **Recommendation** | Add custom CloudWatch metrics for key business events: `BooksCreated` count, `BooksQueried` count, `UniqueUsers` (if auth is extended to GET). Use CloudWatch Embedded Metric Format (EMF) in Lambda for zero-overhead metric publication. |
| **Evidence** | `src/books/create/index.ts` — no metric publication; `src/books/get-all/index.ts` — no metric publication; no CloudWatch dashboard resources in template |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 2 🟠 Needs Work |
| **Severity** | Medium |
| **Finding** | Static threshold alarms configured: Lambda Errors > 0 with 2 evaluation periods of 60 seconds. No anomaly detection, no composite alarms, no latency-based alerting. |
| **Gap** | Static error-count thresholds miss gradual degradation (e.g., increasing latency without errors) and novel failure patterns. No CloudWatch anomaly detection bands configured. |
| **Recommendation** | Add CloudWatch Anomaly Detection on API Gateway latency and Lambda duration metrics. Add composite alarms that combine error rate + latency signals. Consider integrating with SNS for alerting or PagerDuty/OpsGenie for on-call notification. |
| **Evidence** | `template.yml` — two CloudWatch::Alarm resources with static ComparisonOperator: GreaterThanThreshold, Threshold: 0 |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 4 ✅ Mature |
| **Finding** | Production deployments use `Linear10PercentEvery1Minute` (gradual traffic shifting). CloudWatch Alarms trigger automatic rollback if errors are detected during deployment. Pre-traffic hooks (CreateBookPreTraffic) run smoke tests on new Lambda versions before any traffic is shifted. Staging uses AllAtOnce (appropriate for non-production). |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `template.yml` — DeploymentPreference.Type: Linear10PercentEvery1Minute (production), Alarms list, Hooks.PreTraffic; `src/books/create-pre-traffic/index.ts` — smoke test implementation |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 4 ✅ Mature |
| **Finding** | End-to-end integration tests exist and run in the CI/CD pipeline. Tests cover: GET /books without auth, GET /books returns correct data, POST /books requires auth (401), POST /books validates payload (500), POST /books creates successfully (201). Tests run against the deployed staging environment with real Cognito users and DynamoDB data. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/books/tests/index.js` — comprehensive e2e test suite; `pipeline/buildspec-test.json` — runs tests in Staging stage; `pipeline/lib/pipeline-stack.ts` — testAction in Staging stage with deployed endpoint variables |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 ❌ Not Ready |
| **Severity** | Medium |
| **Finding** | No runbooks, no SSM Automation documents, no automated incident response workflows. No self-healing patterns beyond the deployment rollback (which is deployment-time, not runtime). |
| **Gap** | Incident response is entirely ad hoc. No documented procedures for common failure scenarios (DynamoDB throttling, Lambda cold start spikes, Cognito service issues). |
| **Recommendation** | Create runbooks for common incidents: DynamoDB throttle resolution (switch to on-demand or increase capacity), Lambda error spike investigation (check X-Ray traces), API Gateway 5xx troubleshooting. Start with markdown runbooks, then consider SSM Automation documents for automated remediation. |
| **Evidence** | No runbook files found; no SSM Automation documents; no Step Functions for incident workflows; no Lambda-based remediation functions |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 ❌ Not Ready |
| **Severity** | Medium |
| **Finding** | No CODEOWNERS file. CloudWatch Alarms exist but have no team attribution or named owners. No per-service dashboards defined in IaC. No SLO definitions with team attribution. |
| **Gap** | No clear ownership of observability assets. When alarms fire, there is no defined escalation path or responsible team. |
| **Recommendation** | Add a CODEOWNERS file. Add owner tags to CloudWatch Alarms. Define a CloudWatch dashboard in the SAM template for at-a-glance service health. Consider adding team/owner tags to all resources. |
| **Evidence** | No CODEOWNERS file; `template.yml` — alarms without owner/team tags; no CloudWatch::Dashboard resource |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 2 🟠 Needs Work |
| **Severity** | Medium |
| **Finding** | Basic tags applied via SAM Globals and individual resources: `project: my-project`, `environment: {Stage}`. DynamoDB table also tagged. S3 buckets in CDK pipeline do not have tags defined. |
| **Gap** | Only 2 tag keys (project, environment). Missing: owner, cost-center, team, service-name. No tag enforcement mechanism. Not all resource types are tagged (Cognito, IAM roles, CloudWatch Alarms lack tags). The `project: my-project` value is a placeholder. |
| **Recommendation** | Define a tagging standard with required keys: owner, team, cost-center, environment, service. Apply tags via SAM Globals (already partially done) and extend to all resource types. Add proper values replacing `my-project` placeholder. Consider AWS Config required-tags rule for enforcement. |
| **Evidence** | `template.yml` — Globals.Function.Tags: {project: my-project, environment: !Ref Stage}; BooksTable.Tags: same; no tags on CognitoUserPool, UserPoolClient, or CloudWatch Alarms |

---

## Learning Materials

No pathways triggered — no pathway-specific learning materials applicable. Refer to the [AWS SkillBuilder](https://skillbuilder.aws/) catalog for general cloud architecture training.

For the operational gaps identified:
- [AWS Well-Architected — Operational Excellence Pillar](https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/welcome.html)
- [AWS Observability Best Practices](https://aws-observability.github.io/observability-best-practices/)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `template.yml` | INF-Q1, INF-Q2, INF-Q3, INF-Q4, INF-Q5, INF-Q6, INF-Q7, INF-Q8, INF-Q9, INF-Q10, INF-Q11, APP-Q2, APP-Q3, APP-Q4, APP-Q5, APP-Q6, DATA-Q1, DATA-Q3, DATA-Q4, SEC-Q1, SEC-Q2, SEC-Q3, SEC-Q4, SEC-Q5, OPS-Q1, OPS-Q2, OPS-Q4, OPS-Q5, OPS-Q8, OPS-Q9 | SAM template defining all application infrastructure |
| `src/books/create/index.ts` | INF-Q3, INF-Q4, APP-Q1, APP-Q3, APP-Q4, DATA-Q1, DATA-Q2, DATA-Q4, OPS-Q1, OPS-Q3 | Lambda handler for book creation |
| `src/books/get-all/index.ts` | INF-Q3, INF-Q4, APP-Q3, APP-Q4, DATA-Q1, DATA-Q2, OPS-Q1, OPS-Q3 | Lambda handler for retrieving all books |
| `src/books/create/package.json` | APP-Q1, SEC-Q6 | Dependencies showing AWS SDK v2 usage |
| `src/books/get-all/package.json` | APP-Q1 | Dependencies showing AWS SDK v2 usage |
| `pipeline/lib/pipeline-stack.ts` | INF-Q10, INF-Q11, SEC-Q2, SEC-Q5, OPS-Q6 | CDK pipeline definition with full CI/CD stages |
| `pipeline/buildspec.json` | INF-Q11, SEC-Q6, SEC-Q7 | Build phase with unit tests, no security scanning |
| `pipeline/buildspec-test.json` | INF-Q11, OPS-Q6, SEC-Q7 | E2E test execution in staging |
| `pipeline/buildspec-deploy.json` | INF-Q11 | SAM deploy commands |
| `src/books/tests/index.js` | OPS-Q6 | End-to-end integration test suite |
| `src/books/create-pre-traffic/index.ts` | APP-Q6, OPS-Q5 | Pre-traffic hook for deployment validation |
