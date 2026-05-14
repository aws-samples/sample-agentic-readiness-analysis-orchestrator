# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | zappa--Zappa |
| **Date** | 2025-05-08 |
| **Repo Type** | application |
| **Service Archetype** | stateless-utility (auto-detected) |
| **Priority** | P2 |
| **Tags** | python, serverless |
| **Context** | Python framework for deploying WSGI apps on AWS Lambda. |
| **Overall Score** | 1.98 / 4.0 |

**Archetype Justification**: Zappa is a CLI tool and library with no persistent database connections, no user-specific state, no write-back endpoints, and no deployed API surface of its own. All operations are stateless command executions (package, deploy, update, rollback) that orchestrate AWS resources on behalf of users. Classified as stateless-utility.

**Surface Flags**: has_persistent_data_store=false, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=false, has_multi_instance_deployment=false, has_iac_provisioning_aws_resources=false

---

## Classification

**Tier: Remediation Required**

This repo has 4 High findings, 15 Medium findings, 1 Low finding. The matched rule is: "2-11 High → Remediation Required."

MOD classification treats "1 High" as Pilot-Ready (a single modernization gap) rather than a deployment blocker. This contrasts with the ARA classification, where "1 High" is an agent-deployment gate due to safety concerns. With 7 High findings, this repo falls into the "2-11 High → Remediation Required" tier, indicating significant modernization gaps across infrastructure, security, and operations that need attention before cloud-native readiness can be achieved.

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | 1.50 / 4.0 | 🟠 Needs Work | Critical |
| Application Architecture (APP) | 2.00 / 4.0 | 🟠 Needs Work | Critical |
| Data Platform Modernization (DATA) | 3.75 / 4.0 | ✅ Mature | Needs Work |
| Security Baseline (SEC) | 1.20 / 4.0 | ❌ Not Ready | Critical |
| Operations & Observability (OPS) | 1.43 / 4.0 | ❌ Not Ready | Critical |
| **Overall** | **1.98 / 4.0** | **🟠 Needs Work** | |

**Scoring Notes**:
- INF: (1+1+1+1+1+4) / 6 = 9/6 = 1.50 (INF-Q2, Q3, Q4, Q8, Q9 excluded — surface-gated or archetype-N/A)
- APP: (4+1+1+2) / 4 = 8/4 = 2.00 (APP-Q3, Q4 excluded — archetype-N/A)
- DATA: (3+4+4+4) / 4 = 15/4 = 3.75
- SEC: (1+1+2+1+1) / 5 = 6/5 = 1.20 (SEC-Q1, Q2 excluded — surface-gated)
- OPS: (1+1+1+4+1+1+1) / 7 = 10/7 = 1.43 (OPS-Q2, Q5 excluded — surface-gated)

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q1: Managed Compute | 1 | No managed compute infrastructure defined — this is a CLI tool with no deployed workload | Cannot evaluate cloud-native compute readiness; no workload to modernize in-place |
| 2 | SEC-Q3: API Authentication | 1 | No API authentication — CLI tool exposes no HTTP endpoints | No API surface to protect; limits ability to expose Zappa as a service |
| 3 | SEC-Q4: Centralized Identity | 1 | No centralized identity integration — uses AWS IAM credential chain only | No unified access control; relies entirely on environment-level AWS credentials |
| 4 | SEC-Q7: Application Security Pipeline | 1 | No SAST, dependency scanning, or container scanning in CI/CD | Vulnerabilities in dependencies may reach production undetected |
| 5 | APP-Q2: Monolith vs Microservices | 1 | Tightly-coupled monolith — single package with cli.py (3,655 LOC) and core.py (3,866 LOC) heavily intertwined | Limits independent testability, scaling of individual components, and team autonomy |

---

## Quick Agent Wins

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists (OPS-Q6 >= 2 implied by extensive README, CHANGELOG, docs/ directory, CONTRIBUTING.md, and example/ with detailed usage guides)
- **What it enables:** A RAG-based knowledge agent could index Zappa's extensive README (full settings reference, advanced features, troubleshooting), docs directory, and CHANGELOG to answer developer questions about configuration, deployment patterns, and version migration.
- **Additional steps:** Convert README sections into structured chunks; generate embeddings for the settings reference and event source documentation. Consider generating an OpenAPI-like settings schema from the JSON settings format.
- **Effort:** Low

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 4)
- **What it enables:** A DevOps agent that triggers CI runs, checks build status across the Python 3.9-3.14 matrix, monitors Coveralls coverage reports, and manages the CD workflow (versioned releases to PyPI).
- **Additional steps:** Expose GitHub Actions API access to the agent; define trigger conditions for the manual CD workflow dispatch.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=1 (monolith), INF-Q1=1 (no managed compute) |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1=1 but contextual guard: no deployed workload exists (CLI tool published to PyPI, not a running service) |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (no stored procedures); no commercial DB engines detected |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 Not Evaluated (no database); DATA-Q3=4 (no database to version) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 Not Evaluated (archetype-N/A); no data processing workloads exist |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1 (no IaC for own infrastructure), OPS-Q6=4 (tests exist) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:** Zappa is a single monolithic Python package (APP-Q2=1) with two dominant modules — `cli.py` (3,655 LOC) and `core.py` (3,866 LOC) — that are tightly coupled. The CLI module directly instantiates and calls methods on the Zappa core class. No module boundaries, no clear interfaces between deployment orchestration, Lambda management, API Gateway management, and CloudFormation stack operations.

**Compute Model Gaps (INF-Q1=1):** Zappa itself has no deployed compute. It runs on developer machines and in CI/CD pipelines. There is no managed compute infrastructure to modernize.

**Recommended Decomposition Approach:** Given that Zappa is a CLI tool rather than a deployed service, "Move to Cloud Native" in this context means refactoring the monolithic package into well-bounded modules with clear interfaces — enabling independent evolution of the CLI layer, the AWS orchestration layer, and the Lambda handler layer. This could enable:
- Publishing the handler as a separate lightweight package (reducing Lambda cold start)
- Offering the orchestration layer as a standalone library for programmatic use
- Enabling plugin architectures for different cloud providers or deployment targets

**Representative AWS Services:** Lambda (for async operations), Step Functions (for complex deployment workflows), EventBridge (for deployment event notifications), API Gateway (if Zappa-as-a-Service is considered).

**Recommended Patterns:** Hexagonal Architecture (separate CLI/orchestration/handler concerns), Anti-corruption Layer (between boto3 and domain logic).

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10=1):** No infrastructure-as-code defines Zappa's own operational infrastructure. The project has no IaC for:
- Its own CI/CD infrastructure (GitHub Actions is configured but not provisioned via IaC)
- No Terraform or CDK managing the PyPI publishing, GitHub environments, or secrets
- No operational infrastructure (monitoring, alerting) defined in code

**Current CI/CD State (INF-Q11=4):** Excellent CI/CD pipeline with:
- Multi-version Python test matrix (3.9-3.14)
- Lint checks (flake8, black, isort)
- Coverage reporting (Coveralls)
- Manual CD pipeline with dry-run support, tagging, GitHub Release, and PyPI publish

**Gaps to Address:**
- Add dependency vulnerability scanning (pip-audit, Safety, or Dependabot)
- Add SAST tooling (Semgrep, Bandit) to the CI pipeline
- Define IaC for GitHub repository settings, branch protections, and secrets rotation
- Add security gates that block merges on critical vulnerability findings

**Recommended DevOps Toolchain:** GitHub Dependabot for dependency scanning, Bandit or Semgrep for Python SAST, GitHub branch protection rules codified via Terraform GitHub provider.

---

## Decomposition Strategy

> This section is included because APP-Q2 < 3.

### Current State

Zappa is a single deployable package with tightly coupled modules. The primary coupling is between:
- `cli.py` — CLI command handling, user interaction, settings loading, and orchestration
- `core.py` — AWS service interactions (Lambda, API Gateway, S3, CloudFormation, IAM)
- `handler.py` — Lambda runtime handler (WSGI/ASGI translation)

`cli.py` directly imports and instantiates `Zappa` from `core.py`, calling dozens of methods with complex parameter passing. `core.py` handles everything from ZIP creation to CloudFormation template generation to IAM role creation — a "god class" pattern.

### Recommended Approach: Strangler Fig (Parallel Track)

| Approach | Description | Level of Effort | Recommendation |
|----------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Extract `handler.py` + `wsgi.py` + `asgi.py` as a standalone lightweight package first (Lambda runtime only). Then progressively extract AWS service modules from `core.py` into focused modules (lambda_manager, api_gateway_manager, cloudformation_manager, s3_manager). | Medium | ✅ **Recommended.** Lowest risk. Handler extraction provides immediate value (smaller Lambda packages). |
| **Conditional / Adaptive** | Keep the monolithic package but refactor `core.py` into internal modules with clear interfaces. Don't split into separate packages unless specific business need arises. | Low to Medium | ✅ **Recommended when team capacity is limited.** Internal modularization without package splits. |
| **Big-Bang Rewrite** | Rewrite Zappa as a multi-package monorepo with separate packages for CLI, core, handler, and extensions. | High | ⚠️ **Not recommended.** High risk of breaking the existing user base. |

### Pattern Recommendations

| Pattern | Purpose | Application to Zappa |
|---------|---------|---------------------|
| **Hexagonal Architecture** | Separate domain logic from infrastructure adapters | Separate AWS SDK calls (adapters) from deployment logic (domain). Enable testing without placebo mocks. |
| **Anti-corruption Layer** | Isolate internal refactoring from public API | Maintain backward-compatible CLI interface and settings format while restructuring internals. |

### Effort Estimation Factors

| Factor | Current State | Effort Signal |
|--------|--------------|---------------|
| Module boundaries | Minimal — cli.py and core.py are 7,500+ LOC combined | High effort |
| Data coupling | No database coupling (stateless tool) | Low effort |
| Test coverage | Good — 36 test files with mocking | Low effort (regression safety net exists) |
| CI/CD maturity | Excellent — full pipeline exists | Low effort (can support multi-package builds) |

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zappa is a CLI tool and Python library published to PyPI. It has no deployed compute infrastructure of its own — no Lambda functions, no ECS tasks, no EC2 instances running this tool as a service. It runs on developer machines and in CI runners. |
| **Gap** | No managed compute — all execution happens locally or in ephemeral CI environments. |
| **Recommendation** | If Zappa were to offer a hosted deployment service (Zappa-as-a-Service), consider ECS/Fargate or Lambda for hosting the orchestration engine. For the current CLI tool use case, this gap is structural rather than a deficiency. |
| **Evidence** | No `aws_ecs_*`, `aws_eks_*`, `aws_lambda_*`, or `aws_instance` resources found. No Dockerfile. setup.py defines a console_scripts entry point only. |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy a database. INF-Q2 does not apply. Zappa is a stateless CLI tool that reads settings files and makes API calls to AWS — it has no persistent data store of its own. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database drivers, no connection strings, no `aws_rds_*` or `aws_dynamodb_*` resources. No ORM imports. |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Workflow orchestration is not applicable by design — no multi-step workflows exist for a stateless CLI tool. Each Zappa command (deploy, update, rollback) is a single imperative sequence, not an orchestrated workflow requiring retry/resume semantics. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No `aws_sfn_*` resources, no Temporal SDK, no workflow YAML. Commands are sequential imperative operations in cli.py. |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Synchronous HTTP/CLI execution is the correct design; async messaging is not needed. Zappa's own execution model is a synchronous CLI invocation that orchestrates AWS APIs sequentially. (Note: Zappa *configures* async messaging for user apps — SNS, SQS, Kinesis event sources — but does not consume messaging itself.) |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `zappa/asynchronous.py` provides async task dispatch for user-deployed apps, not for Zappa's own execution. CLI operations are synchronous. |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or network segmentation configuration exists. Zappa is a CLI tool that runs on developer machines — it has no deployed network infrastructure. |
| **Gap** | No network security configuration — the tool itself is not deployed in a VPC. |
| **Recommendation** | Not applicable for a CLI tool. If Zappa were deployed as a hosted service, private subnets with least-privilege security groups would be required. |
| **Evidence** | No `aws_vpc`, `aws_subnet`, `aws_security_group` resources. No network configuration files. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zappa exposes no HTTP API of its own. It is a CLI tool invoked via `zappa deploy/update/rollback` commands. No API Gateway, ALB, or CloudFront serves as an entry point for this tool. (Note: Zappa *creates* API Gateways for user apps.) |
| **Gap** | No API entry point — the tool is CLI-only. |
| **Recommendation** | If a programmatic API or SaaS offering is desired, expose deployment operations via API Gateway with authentication, throttling, and request validation. |
| **Evidence** | `setup.py` entry_points define only CLI: `zappa=zappa.cli:handle`. No HTTP server code in the package. |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration — Zappa has no deployed compute to scale. It runs as a local CLI process. |
| **Gap** | No auto-scaling — no workload to scale. |
| **Recommendation** | Not applicable for a CLI tool. No action needed. |
| **Evidence** | No `aws_autoscaling_*`, no `aws_appautoscaling_*` resources. No Lambda concurrency configuration for the tool itself. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no persistent state to back up. INF-Q8 does not apply. Zappa stores no data — deployment artifacts are uploaded to user-owned S3 buckets managed by the user's AWS account. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No `backup_retention_period`, no `aws_backup_plan`, no data stores requiring backup. |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload requiring HA evaluation. INF-Q9 does not apply. Zappa runs as a local CLI tool — there is no production service that needs multi-AZ resilience. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No `multi_az` configuration, no ASG, no ECS service, no deployed workload. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC defines Zappa's own operational infrastructure. The GitHub Actions workflows exist as YAML but no Terraform, CDK, or CloudFormation manages the project's CI/CD infrastructure, PyPI publishing credentials, or GitHub repository settings. Note: Zappa *generates* CloudFormation for user apps via troposphere, but has no IaC for itself. |
| **Gap** | 0% IaC coverage for the project's own infrastructure (GitHub environments, secrets, branch protections). |
| **Recommendation** | Consider Terraform GitHub provider to codify repository settings, branch protection rules, and environment/secret management. This provides auditability and reproducibility for the project's operational infrastructure. |
| **Evidence** | No `.tf` files, no `cdk.json`, no CloudFormation templates for own infrastructure. `.github/workflows/*.yml` define pipelines but are not IaC for infrastructure provisioning. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Full CI/CD automation via GitHub Actions covering both application code testing and release publishing. CI pipeline (`.github/workflows/ci.yml`) runs on every push/PR to master with: Python 3.9-3.14 test matrix, lint checks (flake8, black, isort), pytest with coverage, Coveralls reporting. CD pipeline (`.github/workflows/cd.yml`) provides manual-trigger release with: build verification, semantic versioning, GitHub Release creation, and automated PyPI publish via trusted publisher (OIDC). |
| **Gap** | No gap — CI/CD is comprehensive for a library/CLI tool. |
| **Recommendation** | No action needed. Consider adding automated dependency update checks (Dependabot) and security scanning gates (see SEC-Q7). |
| **Evidence** | `.github/workflows/ci.yml`, `.github/workflows/cd.yml`, `.github/workflows/maintenance.yml`, `Makefile` with test/lint targets. |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Python 3.9-3.14 with modern ecosystem. Uses current boto3 (>=1.17.28), troposphere (>=3.0), modern tooling (black, mypy, isort, pytest). The framework supports the latest Python versions including 3.14 (unreleased). Dependencies are well-maintained and current. |
| **Gap** | No gap — modern Python with current AWS SDK. |
| **Recommendation** | No action needed. Continue tracking Python version support as new versions are released. |
| **Evidence** | `setup.py` python_requires=">=3.9", classifiers include 3.9-3.14. `Pipfile` specifies modern dependency versions. `zappa/__init__.py` validates SUPPORTED_VERSIONS = [(3,9)...(3,14)]. |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Tightly-coupled monolith. Single Python package (`zappa/`) with no module boundaries. `core.py` (3,866 LOC) is a god class handling Lambda management, API Gateway setup, S3 uploads, IAM roles, CloudFormation stacks, VPC configuration, and certificate management. `cli.py` (3,655 LOC) directly instantiates and orchestrates `core.py`. No clear interfaces between concerns. Cross-module coupling is pervasive — `cli.py` accesses internal attributes of the `Zappa` class extensively. |
| **Gap** | No module boundaries, no clear interfaces, god class pattern in `core.py`. Single deployable unit with no separation of concerns. |
| **Recommendation** | Refactor into bounded modules: separate Lambda handler runtime (handler.py + wsgi.py + asgi.py) as an independent package, extract AWS service adapters from core.py into focused modules (lambda_ops, apigateway_ops, cloudformation_ops, s3_ops), define clean interfaces between CLI and orchestration layers. See Decomposition Strategy section. |
| **Evidence** | `zappa/core.py` (3,866 lines, single class), `zappa/cli.py` (3,655 lines, single class), tight coupling between them. No internal package structure beyond flat module layout. |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Sync request/response (CLI invocation → AWS API calls → result) is the correct design; async inter-service communication is not needed. Zappa's CLI operations are inherently synchronous — a user runs a command and waits for completion. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | CLI entry point (`zappa.cli:handle`) processes commands synchronously. No inter-service communication exists — all calls are to AWS APIs via boto3. |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. No operations exceed 30 seconds in the critical path — not applicable by design. While deployment operations can take time (waiting for CloudFormation), these are inherent to the AWS API and are handled by polling/waiting patterns in core.py that are appropriate for a CLI tool (users expect to wait for deployment). |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | CloudFormation wait operations in `core.py` use boto3 waiters (appropriate for CLI). No user-facing API that would timeout. |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy — Zappa exposes no HTTP API. The CLI interface uses semantic versioning for releases (v0.62.1) but has no URL-path, header, or query-parameter versioning for an API surface. The `zappa_settings.json` format has no explicit versioning mechanism for configuration schema. |
| **Gap** | No API versioning — CLI tool with no REST API surface. Settings format changes are handled implicitly via deprecation warnings in code. |
| **Recommendation** | If Zappa adds a programmatic API or the settings schema evolves significantly, implement explicit versioning. For now, consider adding a settings schema version field to `zappa_settings.json` to enable forward-compatible configuration parsing. |
| **Evidence** | No `/v1/`, `/v2/` patterns. No Accept-Version headers. `zappa_settings.json` has no version field. CLI is versioned only by PyPI package version. |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Environment variables for AWS endpoint configuration via boto3 (AWS_DEFAULT_REGION, AWS_PROFILE, AWS_ACCESS_KEY_ID). boto3 handles AWS service endpoint resolution internally. No hard-coded service endpoints in the codebase — all AWS endpoints are resolved by the SDK based on region configuration. |
| **Gap** | No dynamic service discovery mechanism, but for a CLI tool calling AWS APIs, boto3's built-in endpoint resolution is adequate. |
| **Recommendation** | No action needed. boto3's endpoint resolution is the correct pattern for AWS SDK-based tools. |
| **Evidence** | `os.environ["AWS_DEFAULT_REGION"]` in tests. boto3 session handling in `core.py`. No hard-coded AWS endpoint URLs. |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Zappa uses S3 for storing deployment packages (ZIP files). It uploads, downloads, and manages S3 objects as part of the deployment workflow. However, there is no parsing pipeline — deployment packages are opaque ZIP archives, not parsed or indexed for content discovery. |
| **Gap** | Data in S3 but no automated parsing or extraction pipeline. Deployment artifacts are stored but not searchable or analyzable. |
| **Recommendation** | For the deployment tool use case, no parsing pipeline is needed — ZIPs are consumed by Lambda directly. If deployment analytics are desired (package size trends, dependency analysis), consider adding S3 event-driven processing. |
| **Evidence** | `core.py` contains extensive S3 operations: `upload_to_s3()`, `remove_from_s3()`, `copy_on_s3()`. S3 bucket references throughout `cli.py` and test settings. |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All AWS service interactions are centralized through the `Zappa` class in `core.py`. This single class serves as the unified data access layer — all boto3 calls (S3, Lambda, API Gateway, CloudFormation, IAM, CloudWatch) go through this one module. The CLI layer (`cli.py`) never makes direct boto3 calls; it always goes through the `Zappa` core class. |
| **Gap** | No gap — centralized access layer. |
| **Recommendation** | No action needed. While `core.py` is too large (god class), it does provide a single point of control for all AWS interactions. Future refactoring should maintain this centralization principle even when splitting into sub-modules. |
| **Evidence** | `zappa/core.py` - single `Zappa` class handles all boto3 interactions. `zappa/cli.py` imports and uses only the `Zappa` class for AWS operations. |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No database engines are used by this tool. Zappa has no database — it is a stateless CLI tool. There are no engine versions to pin, no EOL risk, and no version management needed. |
| **Gap** | No gap — no database to manage. |
| **Recommendation** | No action needed. |
| **Evidence** | No database resources in IaC. No database connection strings. No migration files. |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs. All business logic resides in the Python application layer. Zappa has no database interaction — there is no SQL of any kind in the codebase. |
| **Gap** | No gap — no database coupling. |
| **Recommendation** | No action needed. |
| **Evidence** | No `.sql` files. No `CREATE PROCEDURE`, `CREATE TRIGGER`, `CREATE FUNCTION`. No ORM imports. No raw SQL execution patterns. |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | Audit logging (CloudTrail) is an AWS account-level service provisioned once per account or organization — not per-application. This repo contains no IaC provisioning AWS resources (has_iac_provisioning_aws_resources=false). It is a CLI tool published to PyPI; CloudTrail evaluation belongs in the foundation/account-level infrastructure repo. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No `aws_cloudtrail` resources. No IaC provisioning AWS infrastructure. |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no database, S3 bucket, EBS volume, or similar managed by this repo. SEC-Q2 does not apply. Zappa uploads to user-owned S3 buckets; encryption configuration is the user's responsibility. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | has_at_rest_data_surface=false. No `aws_s3_bucket`, `aws_rds_*`, or `aws_kms_key` resources defined by this repo. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API authentication — Zappa is a CLI tool with no HTTP endpoints. It does not expose an API that requires per-request authentication. Authentication to AWS is handled by the boto3 credential chain (environment variables, AWS profiles, IAM roles) which is standard for CLI tools. |
| **Gap** | No API authentication — no API surface exists to protect. |
| **Recommendation** | If Zappa were to expose a programmatic API (e.g., deployment-as-a-service), implement OAuth2/JWT authentication. For the current CLI tool use case, boto3 credential chain is appropriate. |
| **Evidence** | No auth middleware, no API Gateway authorizers, no Cognito user pools for the tool itself. Entry point is CLI only (`zappa.cli:handle`). |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity integration. Zappa relies on AWS IAM credential chain (environment variables, ~/.aws/credentials, instance profiles) for authentication to AWS services. No integration with Cognito, Okta, or other centralized IdP for the tool's own access control. |
| **Gap** | No centralized identity — relies entirely on local AWS credential configuration. |
| **Recommendation** | For a CLI tool, AWS IAM credential chain with SSO support (aws sso login) is the standard pattern. Consider documenting AWS SSO/IAM Identity Center integration in Zappa's README for users who want federated access. |
| **Evidence** | boto3 session creation in `core.py` uses default credential chain. No OIDC/SAML configuration. No IdP federation code. |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No plaintext credentials in source code or version control. AWS credentials are handled via boto3 credential chain (environment variables, AWS profiles, IAM roles). The CI/CD pipeline uses GitHub Secrets (`${{ secrets.GITHUB_TOKEN }}`) and OIDC for PyPI publishing (trusted publisher). However, no Secrets Manager or Vault integration exists — credentials are in environment variables without rotation. |
| **Gap** | Production credentials (AWS access keys) kept in environment variables without rotation. No Secrets Manager integration for credential lifecycle management. |
| **Recommendation** | Document best practices for credential rotation. Consider supporting AWS Secrets Manager for `remote_env` secret retrieval (currently supports only S3-stored env files). Encourage users to use IAM roles and SSO rather than long-lived access keys. |
| **Evidence** | No hardcoded credentials. `.github/workflows/cd.yml` uses `id-token: write` for OIDC PyPI publish. `test_settings.json` contains `"remote_env": "s3://lmbda-env/prod/env.json"` — secrets loaded from S3, not hardcoded. No `aws_secretsmanager_*` resources. |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute hardening or patching strategy — Zappa has no deployed compute to harden. The tool runs on developer machines and CI runners (GitHub-hosted Ubuntu). No SSM Patch Manager, no vulnerability scanning of the execution environment. |
| **Gap** | No compute hardening — no deployed workload to harden. |
| **Recommendation** | For the CI environment, GitHub-hosted runners are auto-patched. For the Python package itself, add dependency vulnerability scanning (see SEC-Q7). No further action needed for a CLI tool. |
| **Evidence** | No SSM Agent, no `aws_ssm_patch_baseline`, no Inspector/Snyk configuration. CI runs on `ubuntu-latest` (auto-updated). |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SAST, DAST, or dependency vulnerability scanning tools are integrated into the CI/CD pipeline. The pipeline has lint checks (flake8, black, isort) and type checking (mypy via pre-commit) but no security-focused scanning. No Dependabot configuration, no `pip-audit`, no `safety`, no Bandit, no Semgrep. |
| **Gap** | No security scanning — no Dependabot, no SAST, no dependency audit. Pipeline has zero security validation steps. |
| **Recommendation** | Add Dependabot for automated dependency update PRs. Integrate `pip-audit` or `safety` into the CI pipeline for dependency vulnerability detection. Add Bandit or Semgrep for Python SAST. Configure security gates that block merges on critical findings. |
| **Evidence** | `.github/workflows/ci.yml` — lint and test stages only, no security steps. No `.github/dependabot.yml`. No `.snyk` policy. No `bandit.yml` or `semgrep.yml` configuration. `.pre-commit-config.yaml` has mypy but no security hooks. |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumented in the Zappa tool itself. While Zappa *configures* X-Ray for user-deployed Lambda functions (attach_policy.json grants `xray:PutTraceSegments`), the CLI tool has no tracing for its own operations (deploy workflows, API calls to AWS). |
| **Gap** | No tracing of Zappa's own deployment operations. Complex multi-step deployments (CloudFormation + Lambda + API Gateway) have no end-to-end trace visibility. |
| **Recommendation** | Consider adding OpenTelemetry instrumentation to core.py to trace deployment operations. This would help debug slow deployments and identify which AWS API calls are bottlenecks. |
| **Evidence** | No OpenTelemetry SDK in Pipfile. No X-Ray SDK for the tool itself. `attach_policy.json` enables X-Ray for deployed apps only. |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no user-facing surface for which SLOs are meaningful. OPS-Q2 does not apply. Zappa is a CLI tool — there is no production service with availability or latency requirements. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | has_api_surface=false, has_persistent_data_store=false. No SLO definitions in code or config. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom metrics published. Zappa does not track deployment success rates, package sizes, deployment durations, or other business-relevant metrics for the tool itself. |
| **Gap** | No business metrics — deployment operations are not measured or tracked. |
| **Recommendation** | Consider publishing deployment metrics (success/failure rate, deployment duration, package size) to CloudWatch or a telemetry service. This would inform tool improvement priorities. |
| **Evidence** | No `cloudwatch.put_metric_data` calls for the tool's own operations. No telemetry collection. |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configured. Zappa has no deployed service to monitor — no alarms, no anomaly detection on error rates or latency. |
| **Gap** | No alerting — no production service to alert on. |
| **Recommendation** | Not applicable for a CLI tool. If deployment success metrics were added (see OPS-Q3), alerting on failure rate spikes would be valuable. |
| **Evidence** | No CloudWatch alarms. No PagerDuty/OpsGenie integration. No composite alarms. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | No deployed workload found in this repo — deployment strategy cannot be assessed from source code alone. Zappa is published to PyPI; its "deployment" is a package release, not a service deployment. The CD pipeline handles versioned PyPI releases with dry-run support. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | has_deployed_workload=false. `.github/workflows/cd.yml` handles PyPI publishing, not service deployment. |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Comprehensive test suite with 36 test files covering critical workflows. Uses placebo library to mock AWS API responses, enabling integration-level testing without real AWS credentials. Tests cover: Lambda function creation/update/rollback, API Gateway deployment, CLI command workflows, handler event processing, WSGI/ASGI translation, async task dispatch, WebSocket handling, and more. All tests run in CI on every push/PR across Python 3.9-3.14. |
| **Gap** | No gap — thorough integration test coverage running in CI. |
| **Recommendation** | No action needed. Consider adding end-to-end tests against a real AWS account (canary deployments) for additional confidence. |
| **Evidence** | `tests/test_core.py`, `tests/test_handler.py`, `tests/test_placebo.py`, 36 test files total. `tests/placebo/` directory with extensive pre-recorded AWS API responses. CI runs pytest with coverage on every push. |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response automation or runbooks. No machine-readable runbooks, no automated remediation, no incident workflow definitions. |
| **Gap** | No runbooks or incident response automation. |
| **Recommendation** | For a CLI tool, traditional incident response is less relevant. However, consider adding troubleshooting guides (structured Markdown runbooks) for common deployment failures (CloudFormation rollback, Lambda size limits, IAM permission errors). |
| **Evidence** | No runbook files. No SSM Automation documents. No Step Functions for incident workflows. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership defined. No CODEOWNERS for monitoring configs, no per-service dashboards, no team-attributed alarms. |
| **Gap** | No observability ownership — no production service with monitoring needs. |
| **Recommendation** | Not applicable for a CLI tool. If Zappa were a hosted service, define CODEOWNERS for observability assets and create per-component dashboards. |
| **Evidence** | No CODEOWNERS file referencing observability. No dashboard definitions. No alarm ownership. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging governance for Zappa's own infrastructure (it has none). Zappa does support user-configurable tags for deployed Lambda functions and API Gateways (via `zappa_settings.json` "tags" field), but the tool itself has no tagged AWS resources. |
| **Gap** | No tagging governance — no AWS resources owned by this repo. |
| **Recommendation** | No action needed for the tool itself. Consider documenting tagging best practices in the README for users configuring `zappa_settings.json` tags. |
| **Evidence** | No `default_tags` in Terraform. No `tags` on owned resources. test_settings.json shows user-configurable event sources but no tag configuration examples. |

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
| `.github/workflows/ci.yml` | INF-Q11, OPS-Q6, SEC-Q7 | CI pipeline with Python 3.9-3.14 matrix, lint, test, coverage |
| `.github/workflows/cd.yml` | INF-Q11, SEC-Q5, OPS-Q5 | CD pipeline with PyPI publish via OIDC |
| `.github/workflows/maintenance.yml` | INF-Q11 | Stale issue/PR management |
| `setup.py` | APP-Q1, APP-Q5, INF-Q6 | Package definition, entry points, Python version requirements |
| `Pipfile` | APP-Q1, SEC-Q5 | Runtime and dev dependencies |
| `zappa/__init__.py` | APP-Q1 | Python version validation, version declaration |
| `zappa/core.py` | APP-Q2, DATA-Q2, OPS-Q1, INF-Q1 | Core AWS orchestration (3,866 LOC god class) |
| `zappa/cli.py` | APP-Q2, APP-Q5 | CLI entry point (3,655 LOC) |
| `zappa/handler.py` | APP-Q2 | Lambda runtime handler (Singleton pattern) |
| `zappa/asynchronous.py` | INF-Q4 | Async task dispatch for user apps |
| `zappa/wsgi.py` | APP-Q2 | WSGI request creation from API Gateway events |
| `zappa/asgi.py` | APP-Q2 | ASGI scope creation from API Gateway events |
| `zappa/policies/attach_policy.json` | OPS-Q1, SEC-Q3 | IAM policy (xray, logs, lambda, s3, kinesis, sns, sqs, dynamodb, route53) |
| `zappa/policies/assume_policy.json` | SEC-Q4 | IAM assume role policy |
| `tests/test_core.py` | OPS-Q6 | Core library tests with placebo mocking |
| `tests/placebo/` | OPS-Q6 | Pre-recorded AWS API responses for testing |
| `test_settings.json` | APP-Q6, DATA-Q1 | Multi-stage test configuration |
| `.pre-commit-config.yaml` | SEC-Q7 | Pre-commit hooks (flake8, black, isort, mypy, doctoc) |
| `README.md` | Quick Agent Wins | Comprehensive usage documentation |
| `CHANGELOG.md` | Quick Agent Wins | Version history |
| `docs/` | Quick Agent Wins | SSL/DNS setup guides, community resources |
| `example/` | DATA-Q1 | Example Flask app with zappa_settings.json |
