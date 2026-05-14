# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | motdotla--node-lambda |
| **Date** | 2026-05-07 |
| **TD Version** | modernization-readiness-analysis |
| **Repo Type** | application |
| **Service Archetype** | stateless-utility (auto-detected) |
| **Priority** | P2 |
| **Tags** | javascript, serverless, cli |
| **Context** | Node.js CLI for deploying AWS Lambda functions. |
| **Overall Score** | 1.56 / 4.0 |

**Archetype Justification**: This is a CLI tool (npm package) with no persistent data store, no deployed workload of its own (it deploys OTHER Lambda functions), no API surface, and no long-running processes. All operations are stateless command-line invocations that read config files and make AWS SDK calls. Classified as stateless-utility.

**Surface Flags**: has_persistent_data_store=false, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=false, has_multi_instance_deployment=false

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | N/A | N/A — all questions not applicable for this CLI tool | Ready |
| Application Architecture (APP) | 2.00 / 4.0 | 🟠 Needs Work | Critical |
| Data Platform Modernization (DATA) | N/A | N/A — all questions not applicable | Ready |
| Security Baseline (SEC) | 1.50 / 4.0 | ❌ Not Ready | Critical |
| Operations & Observability (OPS) | 1.17 / 4.0 | ❌ Not Ready | Critical |
| **Overall** | **1.56 / 4.0** | **🟠 Needs Work** | |

**Scoring Notes:**
- INF: All 11 questions are Not Evaluated (archetype-N/A) because this CLI tool has no deployed infrastructure of its own. Excluded from overall.
- APP: APP-Q1=3, APP-Q2=2, APP-Q3=NE, APP-Q4=NE, APP-Q5=1, APP-Q6=2 → (3+2+1+2)/4 = 8/4 = 2.00
- DATA: All 4 questions are Not Evaluated (archetype-N/A) because this CLI tool has no data store. Excluded from overall.
- SEC: SEC-Q1=1, SEC-Q2=NE, SEC-Q3=1, SEC-Q4=1, SEC-Q5=2, SEC-Q6=1, SEC-Q7=3 → (1+1+1+2+1+3)/6 = 9/6 = 1.50
- OPS: OPS-Q1=1, OPS-Q2=NE, OPS-Q3=1, OPS-Q4=1, OPS-Q5=NE, OPS-Q6=2, OPS-Q7=1, OPS-Q8=1, OPS-Q9=NE → (1+1+1+2+1+1)/6 = 7/6 = 1.17
- Overall: (2.00 + 1.50 + 1.17) / 3 = 4.67/3 = 1.56

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | SEC-Q1: Audit Logging | 1 | No CloudTrail or audit logging configuration exists | No visibility into CLI actions or deployment audit trail |
| 2 | SEC-Q3: API Authentication | 1 | No authentication layer; relies entirely on AWS credentials passed as CLI arguments or env vars | Credentials exposed in command history and process lists |
| 3 | SEC-Q4: Centralized Identity | 1 | No centralized IdP integration; credentials managed entirely by the user | No SSO or federated identity support |
| 4 | OPS-Q1: Distributed Tracing | 1 | X-Ray SDK is imported but only used for local Lambda simulation, not for tracing the CLI tool itself | No observability into CLI operations |
| 5 | APP-Q5: API Versioning | 1 | No API versioning strategy; CLI commands have no versioning contract | Breaking changes can be deployed without migration path |

---

## Quick Agent Wins

No Quick Agent Wins identified. The system lacks the foundational capabilities (API documentation, CI/CD deployment pipeline, structured logging, workflow orchestration) needed to support agent integration. This is a CLI tool with no deployed service surface. Address the gaps identified in this analysis before pursuing agent opportunities.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2=2 meets primary trigger but this is a CLI tool, not a deployable service. No supporting conditions met (INF questions all N/A). |
| 2 | Move to Containers | Not Applicable | — | — | This CLI tool has no deployed workload. Containerization does not apply. |
| 3 | Move to Open Source | Not Triggered | — | — | No commercial database engines detected. DATA-Q4 is N/A. |
| 4 | Move to Managed Databases | Not Triggered | — | — | No databases detected. INF-Q2 is N/A. has_persistent_data_store=false. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads. INF-Q4 is N/A. No streaming/ETL artifacts found. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=N/A, INF-Q11=N/A (surface-gated), but OPS-Q6<3 (integration test gaps). CI exists but lacks deployment automation for the package itself. |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. |

**Note on Move to Modern DevOps:** While INF-Q10 and INF-Q11 are N/A for this CLI tool (no infrastructure to provision, no deployment pipeline needed beyond npm publish), the CI/CD workflow exists for testing. The pathway is triggered based on OPS-Q6<3 (integration tests not comprehensive in CI pipeline).

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:**
- CI/CD pipeline exists via GitHub Actions (`.github/workflows/workflow.yml`) running tests on Node 22.x and 24.x across Ubuntu, macOS, and Windows.
- CodeQL security scanning is configured (`.github/workflows/codeql-analysis.yml`).
- Dependabot is configured for monthly dependency updates.
- No automated npm publish pipeline exists — releases appear to be manual.
- Integration tests exist in `test/` but coverage is limited to unit-level mocking of AWS SDK calls rather than true integration testing.

**Gaps:**
- No automated release/publish pipeline (npm publish is manual)
- Integration tests rely entirely on `aws-sdk-mock` — no contract tests or live integration tests
- No deployment strategy for the CLI package itself

**Recommended Improvements:**
- Add automated npm publish workflow triggered on version tags
- Add integration tests that validate CLI commands end-to-end (using localstack or similar)
- Add semantic versioning automation (e.g., semantic-release)

**Representative AWS Services:** CodeBuild, CodePipeline (if migrating CI), CloudWatch (for package telemetry)

**Learning Materials:**
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility` CLI tool. It does not deploy compute infrastructure of its own — it deploys OTHER applications to Lambda. Managed compute evaluation is not applicable by design. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy a database. has_persistent_data_store=false. INF-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. No multi-step workflows exist — not applicable by design. The CLI executes sequential steps (package → zip → upload → configure) but these are linear CLI operations, not orchestrated workflows requiring a dedicated service. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Synchronous CLI execution is the correct design; no messaging needed. The tool configures event sources (SQS, S3, CloudWatch Events) on the user's Lambda functions but does not itself consume or produce messages. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This CLI tool has no deployed workload (has_deployed_workload=false). It runs on the user's local machine and makes AWS API calls. Network security evaluation for the tool itself is not applicable. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This CLI tool has no API surface (has_api_surface=false). It is invoked from the command line, not through an API gateway. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This CLI tool has no deployed workload. Auto-scaling does not apply to command-line tools. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no persistent state to back up. has_persistent_data_store=false, has_at_rest_data_surface=false. INF-Q8 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload requiring HA evaluation. has_deployed_workload=false, has_api_surface=false. INF-Q9 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This CLI tool has no infrastructure to provision. It is distributed as an npm package. No Terraform, CloudFormation, CDK, or other IaC files exist because none are needed. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No .tf, .cfn.yaml, cdk.json, or other IaC files found in repository. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | While CI exists (GitHub Actions for testing), this CLI tool's "deployment" is npm publish — a package release, not an infrastructure deployment. The CI/CD question evaluates infrastructure and application deployment automation, which does not directly apply to a published npm CLI package. Evaluated under OPS-Q5/OPS-Q6 instead. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `.github/workflows/workflow.yml` — CI test pipeline exists. |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | JavaScript (CommonJS) on Node.js >= 22.0.0 with AWS SDK v2. The language runtime is modern (Node 22+) but the AWS SDK is outdated (v2 is in maintenance mode). The CLI framework (Commander.js v14) is current. |
| **Gap** | AWS SDK v2 (`aws-sdk ^2.1377.0`) is in maintenance mode. Should migrate to modular AWS SDK v3 (`@aws-sdk/client-*`). Additionally, `continuation-local-storage` is deprecated — should use Node.js native `AsyncLocalStorage`. |
| **Recommendation** | Migrate from `aws-sdk` v2 to `@aws-sdk/client-lambda`, `@aws-sdk/client-s3`, `@aws-sdk/client-cloudwatch-logs`, `@aws-sdk/client-cloudwatch-events`. Replace `continuation-local-storage` with native `AsyncLocalStorage` from `node:async_hooks`. |
| **Evidence** | `package.json` — `"aws-sdk": "^2.1377.0"`, `"continuation-local-storage": "^3.2.1"`, `"engines": {"node": ">= 22.0.0"}` |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Single deployable unit (npm package) with identifiable modules (`lib/main.js`, `lib/aws.js`, `lib/s3_deploy.js`, `lib/s3_events.js`, `lib/schedule_events.js`, `lib/cloudwatch_logs.js`). The modules share a common `aws.sdk` singleton from `lib/aws.js` and the main Lambda class in `lib/main.js` directly orchestrates all operations. Modules have clear responsibilities but direct coupling through the shared SDK instance. |
| **Gap** | Shared mutable state via `aws.sdk` singleton. The `lib/aws.js` module mutates global `aws.config` which affects all modules. No clear interfaces between modules — `main.js` directly instantiates all service classes. |
| **Recommendation** | For a CLI tool of this scope, a monolithic structure is acceptable. However, consider injecting the AWS client instances rather than sharing a mutable global singleton. This would improve testability and allow future modularization if needed. |
| **Evidence** | `lib/aws.js` — mutates global `aws.config`; `lib/main.js` — directly requires and instantiates all modules. |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Sync request/response (CLI command → AWS API calls → result) is the correct design; async inter-service communication is not needed. The tool makes sequential AWS SDK calls as part of single CLI invocations. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. No operations exceed 30 seconds in normal use — not applicable by design. The CLI packages code (zip), uploads to Lambda, and returns. While packaging large projects could take time, this is bounded local computation, not a long-running distributed operation. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy. The CLI exposes commands (`setup`, `run`, `package`, `deploy`) with numerous flags but no versioning contract. Breaking changes to CLI flags or behavior have no migration path beyond CHANGELOG.md notes. The npm package version (1.3.0) exists but there is no explicit compatibility guarantee or deprecation policy for individual CLI flags. |
| **Gap** | No versioning strategy for CLI commands or flag contracts. Users have no guaranteed migration path when flags change behavior or are removed. |
| **Recommendation** | Implement a deprecation policy for CLI flags with warnings before removal. Consider semver-strict adherence where major versions signal breaking CLI flag changes. Add a `--version` compatibility matrix in documentation. |
| **Evidence** | `bin/node-lambda` — CLI flags have no versioning annotations; `CHANGELOG.md` — documents changes but no formal deprecation policy. |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | AWS endpoints are configured via environment variables (`AWS_REGION`, `AWS_ENDPOINT`) and CLI flags. The tool uses the AWS SDK's built-in endpoint resolution for service endpoints but allows custom endpoint override for localstack/testing. No hard-coded service endpoints exist in source — all are parameterized through env vars and CLI args. |
| **Gap** | Endpoint configuration is entirely through environment variables — functional but not dynamic service discovery. For a CLI tool, this is an acceptable pattern. |
| **Recommendation** | The current environment-variable-based approach is appropriate for a CLI tool. No change needed. Consider documenting AWS endpoint override patterns more prominently for users testing with localstack. |
| **Evidence** | `bin/node-lambda` — `AWS_ENDPOINT`, `AWS_REGION` env vars; `lib/aws.js` — `config.endpoint` override. |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This CLI tool does not store or manage unstructured data. It creates zip archives transiently in the OS temp directory and optionally uploads them to S3 buckets for Lambda deployment. The S3 interaction is for deploying user code, not for storing the tool's own data. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `lib/main.js` — temp zip files; `lib/s3_deploy.js` — S3 upload for deployment only. |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This CLI tool has no persistent data store and no data access layer. It reads configuration from local files (`.env`, `deploy.env`, `event_sources.json`) and makes AWS API calls. No database connections exist. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database imports or connections in any source file. |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This CLI tool does not define or manage any database resources. has_persistent_data_store=false. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This CLI tool has no database and no stored procedures. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or audit logging configuration exists in this repository. The CLI tool makes AWS API calls (Lambda create/update, S3 operations) but provides no mechanism for auditing these actions beyond CloudTrail configured in the user's AWS account (which is outside this tool's scope). No local audit logging of deployment actions. |
| **Gap** | No audit logging of CLI deployment operations. Users have no local record of what was deployed, when, and with what parameters. |
| **Recommendation** | Add structured logging of deployment operations to a local log file (function name, region, timestamp, success/failure). This provides an audit trail independent of CloudTrail. Consider adding `--audit-log` option. |
| **Evidence** | No logging framework or audit log output found. `lib/main.js` uses only `console.log` for status output. |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no database, S3 bucket, EBS volume, or similar managed storage owned by this tool. The CLI creates transient zip files in the OS temp directory which are deleted after upload. SEC-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `lib/main.js` — `fs.unlinkSync(tmpZipFile)` after upload. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API authentication layer exists (the tool has no API). AWS credentials are accepted via CLI flags (`--accessKey`, `--secretKey`, `--sessionToken`) or environment variables. Passing credentials as CLI arguments exposes them in shell history and process lists. |
| **Gap** | Credentials can be passed as CLI arguments, exposing them in shell history and process lists (`ps aux`). While AWS profile-based auth is supported (`--profile`), the direct credential flags remain a security concern. |
| **Recommendation** | Deprecate `--accessKey` and `--secretKey` CLI flags in favor of AWS profile-based authentication, IAM roles, or SSO. Add documentation warning about credential exposure via CLI arguments. Consider supporting AWS SSO (`aws sso login`) workflow. |
| **Evidence** | `bin/node-lambda` — `-a, --accessKey [AWS_ACCESS_KEY_ID]`, `-s, --secretKey [AWS_SECRET_ACCESS_KEY]`; `lib/aws.js` — `awsSecurity.accessKeyId = config.accessKey`. |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized IdP integration. The tool accepts raw AWS credentials or an AWS profile name. No support for AWS SSO, OIDC federation, or SAML-based authentication. Users must manage their own credential lifecycle entirely. |
| **Gap** | No SSO or federated identity support. Users managing multiple AWS accounts have no streamlined auth flow through this tool. |
| **Recommendation** | Add support for AWS IAM Identity Center (SSO) credential resolution by leveraging the AWS SDK v3's built-in credential provider chain (which supports SSO natively). This would come naturally with the SDK v3 migration. |
| **Evidence** | `lib/aws.js` — Only supports `SharedIniFileCredentials` (profile) or explicit access key/secret. |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No plaintext credentials are stored in the repository source code. Credentials are read from environment variables or CLI arguments at runtime. The `.env` and `deploy.env` files are documented as gitignored. However, there is no integration with AWS Secrets Manager or any secrets rotation mechanism. The example files suggest storing credentials in `.env` files on disk. |
| **Gap** | No secrets management integration. Credentials are managed via env vars and `.env` files without rotation. The recommended workflow (storing credentials in `.env`) stores secrets in plaintext on the filesystem. |
| **Recommendation** | Add documentation recommending AWS IAM Identity Center (SSO) or credential helper tools over `.env` file storage. The SDK v3 migration would enable the full credential provider chain including SSO and container credential providers. |
| **Evidence** | `lib/.env.example` — template for credential storage; `.gitignore` does not include `.env` by default (only recommended in README); `bin/node-lambda` — reads from env vars. |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute hardening or patching strategy. The CLI runs on the user's local machine. Dependabot is configured for monthly dependency updates, which helps with vulnerability patching in npm packages, but there is no vulnerability scanning beyond CodeQL for the JavaScript source itself. |
| **Gap** | No runtime vulnerability scanning (e.g., `npm audit` in CI pipeline). Dependabot provides reactive updates but does not block vulnerable releases. |
| **Recommendation** | Add `npm audit` step to CI pipeline with failure on high/critical vulnerabilities. Consider adding Snyk or similar SCA tool for proactive vulnerability detection. |
| **Evidence** | `.github/dependabot.yml` — monthly updates only; `.github/workflows/workflow.yml` — no `npm audit` step. |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | CodeQL SAST scanning is integrated in CI/CD via `.github/workflows/codeql-analysis.yml`. It runs on push/PR to master and on a weekly schedule. Dependabot is configured for dependency updates. However, no `npm audit` or dependency vulnerability scanning step exists in the CI pipeline, and no blocking gate is configured. |
| **Gap** | No explicit dependency vulnerability scanning in CI (no `npm audit` step). CodeQL covers SAST but not dependency vulnerabilities. No blocking gate on findings. |
| **Recommendation** | Add `npm audit --audit-level=high` to the CI pipeline as a blocking step. This complements CodeQL's SAST coverage with dependency vulnerability detection. |
| **Evidence** | `.github/workflows/codeql-analysis.yml` — CodeQL scanning; `.github/dependabot.yml` — dependency updates; `.github/workflows/workflow.yml` — no `npm audit` step. |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | `aws-xray-sdk-core` is imported in `lib/main.js` but only used to create a mock X-Ray segment for local Lambda simulation (`nameSpace.set('segment', new AWSXRay.Segment('annotations'))`). This is for simulating the X-Ray context that Lambda functions expect during local `run` testing — it does not instrument the CLI tool itself with distributed tracing. |
| **Gap** | No distributed tracing of the CLI tool's own operations (deploy, package, etc.). The X-Ray SDK import is solely for Lambda local simulation support. |
| **Recommendation** | For a CLI tool, distributed tracing is of limited value. However, if deployment operations are to be monitored, consider adding OpenTelemetry instrumentation to track deploy durations and success rates. This is low priority for a CLI tool. |
| **Evidence** | `lib/main.js` — `const AWSXRay = require('aws-xray-sdk-core')`, used only in `_runHandler` for local simulation context. |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no user-facing service surface for which SLOs are meaningful. It is a CLI tool invoked locally — response time SLOs and availability SLOs do not apply to command-line tools. has_api_surface=false, has_persistent_data_store=false. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom metrics published. The CLI outputs to console.log only. No telemetry, no deployment success/failure tracking, no usage metrics. |
| **Gap** | No metrics on deployment success rates, package sizes, deployment durations, or error rates across users. |
| **Recommendation** | Consider adding opt-in anonymous telemetry for deployment success/failure rates and common error patterns. This would help prioritize development effort. Low priority for an open-source CLI tool. |
| **Evidence** | `lib/main.js` — only `console.log` output; no metrics SDK imports. |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configured. This is a CLI tool with no runtime service to monitor. |
| **Gap** | No alerting on npm package health (download drops, error report spikes). |
| **Recommendation** | For a CLI tool, this is very low priority. Consider GitHub Actions alerts on CI failures as a minimal signal. |
| **Evidence** | No monitoring or alerting configuration found. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This CLI tool is distributed as an npm package. Its "deployment" is `npm publish`. Canary/blue-green deployment strategies do not apply to npm package publishing in the same way they apply to service deployments. has_deployed_workload=false. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Test suite exists with 6 test files using Mocha + Chai + aws-sdk-mock. Tests mock AWS SDK calls and validate CLI behavior. However, all tests are unit-level with mocked AWS interactions — no integration tests against real or simulated AWS services (localstack). Tests run in CI on Node 22.x and 24.x across multiple OS. |
| **Gap** | All AWS interactions are mocked. No integration tests validate actual AWS API call sequences, error handling with real services, or end-to-end CLI workflows. |
| **Recommendation** | Add integration test suite using localstack to validate actual deploy/package workflows against simulated AWS services. This would catch SDK migration issues and real API contract changes. |
| **Evidence** | `test/main.js` — uses `aws-sdk-mock`; `test/s3_deploy.js`, `test/s3_events.js`, `test/schedule_events.js`, `test/cloudwatch_logs.js` — all mocked; `.github/workflows/workflow.yml` — runs `npm test` only. |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response runbooks or automation. No structured error handling documentation. When deployment fails, users receive raw AWS SDK error messages with no guided resolution. |
| **Gap** | No runbooks for common deployment failures. No structured troubleshooting guide beyond README examples. |
| **Recommendation** | Add a troubleshooting guide documenting common deployment errors (IAM permission issues, timeout errors, zip size limits) with resolution steps. |
| **Evidence** | No runbook files, no troubleshooting documentation beyond README. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership defined. No CODEOWNERS file, no monitoring dashboards, no team-attributed alarms. As an open-source project, ownership is implicit (single maintainer). |
| **Gap** | No structured ownership of observability or operational health. |
| **Recommendation** | Add CODEOWNERS file. For an open-source CLI tool, this is low priority but helps with contribution routing. |
| **Evidence** | No CODEOWNERS, no monitoring configuration. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This CLI tool does not own AWS resources. It helps users deploy Lambda functions and supports tagging via `--tags` flag, but the tagging governance of deployed resources is the user's responsibility, not this tool's. has_deployed_workload=false (for the tool itself). |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `bin/node-lambda` — `--tags` flag exists for user's Lambda function tagging. |

---

## Learning Materials

- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `package.json` | APP-Q1, SEC-Q5, SEC-Q6 | Dependency manifest showing AWS SDK v2, Node.js engine requirement, dependencies |
| `lib/main.js` | APP-Q2, OPS-Q1, OPS-Q3, SEC-Q1 | Core Lambda class with all deployment logic, X-Ray import for local sim |
| `lib/aws.js` | APP-Q1, APP-Q2, SEC-Q3, SEC-Q4 | AWS SDK v2 configuration wrapper with credential handling |
| `bin/node-lambda` | APP-Q5, APP-Q6, SEC-Q3, SEC-Q5 | CLI entry point with all command definitions and credential flags |
| `.github/workflows/workflow.yml` | OPS-Q6, SEC-Q6 | CI pipeline running tests on Node 22.x/24.x |
| `.github/workflows/codeql-analysis.yml` | SEC-Q7 | CodeQL SAST scanning configuration |
| `.github/dependabot.yml` | SEC-Q6, SEC-Q7 | Monthly dependency update configuration |
| `lib/s3_deploy.js` | DATA-Q1 | S3 deployment logic (transient uploads only) |
| `lib/schedule_events.js` | INF-Q3 | CloudWatch scheduled events configuration |
| `lib/s3_events.js` | INF-Q4 | S3 event notification configuration |
| `lib/cloudwatch_logs.js` | INF-Q3 | CloudWatch Logs retention policy setting |
| `test/main.js` | OPS-Q6 | Unit tests with aws-sdk-mock |
| `test/s3_deploy.js` | OPS-Q6 | Unit tests for S3 deployment |
| `test/s3_events.js` | OPS-Q6 | Unit tests for S3 events |
| `test/schedule_events.js` | OPS-Q6 | Unit tests for schedule events |
| `test/cloudwatch_logs.js` | OPS-Q6 | Unit tests for CloudWatch logs |
| `lib/.env.example` | SEC-Q5 | Template suggesting credential storage in .env files |
