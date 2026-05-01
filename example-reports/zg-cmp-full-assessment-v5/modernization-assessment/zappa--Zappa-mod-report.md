# Modernization Readiness Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | Zappa |
| **Date** | 2025-07-16 |
| **TD Version** | N/A (unable to resolve via CLI) |
| **Repo Type** | application |
| **Service Archetype** | stateless-utility (auto-detected) |
| **Priority** | P2 |
| **Tags** | python, serverless |
| **Context** | Python framework for deploying WSGI apps on AWS Lambda. |
| **Surface Flags** | has_persistent_data_store=false, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=false, has_multi_instance_deployment=false |
| **Overall Score** | 2.19 / 4.0 |

**Archetype Justification**: No database connections, no persistent state, no write operations at runtime. The Zappa handler acts as a stateless WSGI/ASGI adapter translating Lambda events to web framework requests. The CLI component (`zappa deploy`, `zappa update`) is a build/deploy-time tool, not a running service. Classified as stateless-utility.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.71 / 4.0 | 🟠 Needs Work |
| Application Architecture (APP) | 2.75 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 2.75 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 2.00 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.75 / 4.0 | 🟠 Needs Work |
| **Overall** | **2.19 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | SEC-Q7: Application Security Pipeline | 1 | No SAST, dependency scanning, or security gates in CI/CD pipeline | Vulnerabilities in dependencies (boto3, requests, werkzeug) could reach releases undetected |
| 2 | SEC-Q1: Audit Logging | 1 | No CloudTrail or audit logging configuration for the framework's own AWS operations | Deploy-time AWS API calls are not audited beyond CloudTrail account defaults |
| 3 | INF-Q1: Managed Compute | 1 | No IaC defining compute infrastructure for the framework itself | Framework generates Lambda/API Gateway for users but has no IaC for its own deployment infrastructure |
| 4 | OPS-Q3: Business Metrics | 1 | No custom metrics published for framework usage, deployment success rates, or error patterns | No data-driven insight into framework health or adoption |
| 5 | DATA-Q3: Database Engine Version | 1 | DynamoDB referenced for async response tables with no version management or lifecycle documentation | Async response table configuration has no documented lifecycle or cleanup strategy |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 3). GitHub Actions CI (`ci.yml`) runs lint, test, and coverage across Python 3.9–3.14. CD (`cd.yml`) handles versioned PyPI publishing.
- **What it enables:** An agent that triggers CI runs, checks build status across Python version matrix, monitors coverage trends, and manages release workflows.
- **Additional steps:** Expose CI/CD workflow dispatch via GitHub API tokens; create structured status reporting endpoint.
- **Effort:** Low

### RAG-Based Knowledge Agent

- **Prerequisite:** Extensive documentation exists. `README.md` (2,217 lines) covers installation, configuration, all CLI commands, advanced settings, and troubleshooting. `CONTRIBUTING.md`, `docs/` directory with SSL/domain guides, and `example/` directory with sample configurations.
- **What it enables:** A knowledge agent that indexes the README, docs, and example configurations to answer developer questions about Zappa configuration, deployment troubleshooting, and setting options.
- **Additional steps:** Index the README and docs into a vector store (e.g., Amazon Bedrock Knowledge Bases with S3 data source). The documentation is well-structured Markdown, suitable for chunking.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 — application has well-defined module boundaries; primary trigger not met. |
| 2 | Move to Containers | Not Triggered | — | — | Contextual guard: compute model is Lambda (serverless). Framework is designed for Lambda deployment. Containerization is not applicable. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 — no stored procedures or proprietary SQL. No commercial database engines detected. |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = Not Evaluated (no persistent data store). No databases to migrate. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | Contextual guard: no data processing workloads detected. stateless-utility archetype with no streaming/ETL artifacts. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (no IaC). Supporting: OPS-Q5 = 2 (no canary/blue-green), OPS-Q6 = 2 (no live integration tests). |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. Context: "Python framework for deploying WSGI apps on AWS Lambda" contains no AI-related signal terms. |

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:**

- **IaC Coverage (INF-Q10 = 1):** No infrastructure-as-code exists for the framework's own infrastructure. The framework *generates* CloudFormation templates for users via troposphere but does not define its own deployment infrastructure in IaC. As a PyPI-published library, the "infrastructure" is the CI/CD pipeline and GitHub repository configuration — but even these are not codified beyond workflow YAML files.

- **CI/CD Automation (INF-Q11 = 3):** GitHub Actions CI (`ci.yml`) provides automated lint (flake8, black, isort), test (pytest across Python 3.9–3.14), and coverage (Coveralls). CD (`cd.yml`) handles version tagging, GitHub Release creation, and PyPI publishing via trusted publisher (OIDC). However, the CI pipeline lacks security scanning (SAST, dependency vulnerability checks), and the CD pipeline has no automated rollback or canary release mechanism.

- **Deployment Strategy (OPS-Q5 = 2):** CD publishes directly to PyPI with manual `workflow_dispatch` trigger. Version tags and GitHub Releases provide rollback capability (by publishing a new version), but there is no staged rollout, canary release, or test-PyPI validation before production publish.

- **Integration Testing (OPS-Q6 = 2):** Tests use the `placebo` library to mock AWS API responses, providing deterministic unit-level testing. No live integration tests against actual AWS services exist in the CI pipeline.

**Recommendations (respecting preferences — prefer API Gateway, EventBridge, Bedrock):**

1. **Add Security Scanning to CI:** Integrate `pip-audit` or `safety` for dependency vulnerability scanning. Add CodeQL or Semgrep for SAST. Configure Dependabot for automated dependency updates. This is the highest-impact improvement.

2. **Implement Test-PyPI Staging:** Before publishing to production PyPI, publish to Test PyPI and run smoke tests. This provides a canary-like validation step for the library release process.

3. **Add Integration Test Suite:** Create a dedicated integration test workflow that deploys a minimal Flask/Django app to a test AWS account using Zappa, validates the deployment, and tears it down. Run on a schedule or before releases.

4. **Codify Repository Configuration:** Use Terraform or Pulumi to manage GitHub repository settings, branch protection rules, and secrets. This brings the "infrastructure" of the open-source project under version control.

**Representative AWS Services:** CodeBuild (for CI/CD if migrating from GitHub Actions), CodePipeline, CloudFormation (already used by the framework), X-Ray (already supported).

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
| **Finding** | No IaC files (Terraform, CloudFormation, CDK) exist in the repository to define compute resources for the framework itself. The framework is a pip-installable Python library published to PyPI — it has no deployed compute infrastructure of its own. The framework *generates* Lambda functions and API Gateway resources for user applications via `zappa/core.py` (using boto3 and troposphere), but these are created in the *user's* AWS account, not for the framework. The `zappa/handler.py` runs inside user-deployed Lambda functions as a WSGI/ASGI adapter. |
| **Gap** | As a library, Zappa has no compute infrastructure to manage. However, the framework's own build/test infrastructure (GitHub Actions runners) is the only "compute" — and it is fully managed by GitHub. The score of 1 reflects the literal absence of managed compute definitions in IaC, which is expected for a library repo type. |
| **Recommendation** | No action needed for compute modernization. The framework is correctly designed as a library distributed via PyPI. If the project ever needs dedicated infrastructure (e.g., a documentation site, integration test environment), define it in IaC using CloudFormation or CDK. |
| **Evidence** | No `.tf`, `.cfn.yaml`, `cdk.json`, or IaC files found in repository root or any subdirectory. `zappa/core.py` uses `boto3.client('lambda')` and `troposphere` to generate resources for users. |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy a database. The framework uses DynamoDB in `zappa/asynchronous.py` for optional async response capture (`ASYNC_RESPONSE_TABLE`), but this table is created in the user's AWS account as part of their deployment, not by the framework for its own persistence. Surface flag `has_persistent_data_store=false`. INF-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `zappa/asynchronous.py` lines referencing `DYNAMODB_CLIENT` — these operate on user-owned tables. No `aws_rds_*`, `aws_dynamodb_*` IaC resources in repository. |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Workflow orchestration is not applicable by design — no multi-step workflows exist for a stateless WSGI/ASGI adapter. The framework's CLI commands (`deploy`, `update`, `rollback`) are sequential imperative operations, not multi-service workflows requiring orchestration. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `zappa/cli.py` — CLI commands execute sequentially via boto3 API calls. No `aws_sfn_*`, Temporal, or workflow YAML definitions found. |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Synchronous HTTP/gRPC is the correct design for this stateless-utility and is in use. The Zappa handler (`zappa/handler.py`) processes Lambda invocations synchronously — each HTTP request is translated to a WSGI/ASGI environ, passed to the web framework, and the response is returned directly. The framework does support async task dispatch via Lambda invocation and SNS (`zappa/asynchronous.py`), which is an appropriate outbound signal mechanism using managed AWS services. |
| **Gap** | None. Synchronous request/response is the architecturally correct pattern for a WSGI/ASGI adapter running in Lambda. |
| **Recommendation** | Adopting async messaging infrastructure is NOT recommended for this archetype — it would add operational complexity without architectural benefit. The existing async task support via Lambda invocation and SNS is already well-implemented for the use case. |
| **Evidence** | `zappa/handler.py` — synchronous request processing. `zappa/asynchronous.py` — `LambdaAsyncResponse` uses `InvocationType='Event'` (managed Lambda async). `SnsAsyncResponse` uses SNS (managed). `zappa/policies/attach_policy.json` — includes SNS and SQS permissions. |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or network segmentation configuration exists for the framework itself. The framework *supports* VPC configuration for user-deployed Lambda functions (`vpc_config` parameter in `zappa/core.py` lines 1047, 1197, 1215-1238) including security group and subnet specification, but this is for user workloads. The framework's own operations (CLI commands calling AWS APIs) run on developer workstations or CI runners using standard HTTPS to AWS endpoints. |
| **Gap** | As a library/CLI tool, Zappa has no deployed services requiring network security configuration. The score of 1 reflects the literal absence, which is architecturally expected. |
| **Recommendation** | No action needed. If the project ever deploys its own infrastructure (integration test environment, documentation site), configure VPC with private subnets and least-privilege security groups. |
| **Evidence** | `zappa/core.py` — `vpc_config` parameter handling at lines 1047, 1197, 1215-1238. No `aws_vpc`, `aws_subnet`, `aws_security_group` IaC resources in repository. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The framework does not expose an API entry point of its own. It is a CLI tool and library. The framework *creates* API Gateway resources for user applications (REST APIs, HTTP APIs, WebSocket APIs) via `zappa/core.py` using troposphere and boto3, but these are in the user's account. The framework supports API Gateway, ALB, and CloudFront Lambda Function URLs as entry points for user deployments. |
| **Gap** | As a library, Zappa has no API surface requiring an entry point. The score of 1 reflects the literal absence, which is expected for a CLI/library tool. |
| **Recommendation** | No action needed. The framework correctly creates managed API entry points (API Gateway, ALB) for user deployments. |
| **Evidence** | `zappa/core.py` — `troposphere.apigateway` usage. `zappa/handler.py` — handles both REST API (v1) and HTTP API (v2) event formats. No API Gateway resources defined for the framework itself. |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists for the framework itself. The framework supports `lambda_concurrency` settings for user-deployed functions (referenced in `zappa/cli.py`), and Lambda inherently auto-scales. However, the framework has no deployed compute of its own requiring scaling. |
| **Gap** | As a library, Zappa has no deployed workloads requiring auto-scaling. The score of 1 reflects the literal absence, which is architecturally expected. |
| **Recommendation** | No action needed. The framework correctly leverages Lambda's inherent auto-scaling for user deployments. |
| **Evidence** | `zappa/cli.py` line 124 — `xray_tracing` and other Lambda configuration support. No `aws_autoscaling_*`, `aws_appautoscaling_*` resources in repository. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no persistent state to back up. The framework uses S3 at deploy-time to upload code packages, but these are ephemeral deployment artifacts in the user's account. Surface flags `has_persistent_data_store=false` and `has_at_rest_data_surface=false`. INF-Q8 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database resources, S3 bucket definitions, or backup configurations in repository. |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload requiring HA evaluation. The framework is a pip-installable library with no running infrastructure. Surface flag `has_deployed_workload=false`. INF-Q9 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No Dockerfile, no IaC defining compute resources, no deployment manifests for the framework itself. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No infrastructure-as-code exists for the framework's own infrastructure. The repository contains no `.tf`, `.cfn.yaml`, `cdk.json`, Helm charts, or Kustomize files defining infrastructure for the Zappa project itself. The framework *generates* CloudFormation templates for user deployments using `troposphere` (visible in `zappa/core.py`), but this is the framework's feature, not its own infrastructure. The project's "infrastructure" consists of GitHub repository settings, CI/CD workflows (`.github/workflows/`), and PyPI publishing configuration — none of which are managed via IaC. |
| **Gap** | GitHub repository configuration (branch protection, secrets, environments), CI/CD workflow management, and PyPI trusted publisher settings are not codified in IaC. Changes to these are manual. |
| **Recommendation** | Consider codifying repository infrastructure using Terraform GitHub provider or Pulumi to manage branch protection rules, required status checks, environment configurations, and secrets. This is a low-effort improvement that increases reproducibility and auditability. |
| **Evidence** | No IaC files in repository root or subdirectories. `zappa/core.py` imports `troposphere` — this generates IaC for users, not for the framework. `.github/workflows/` — CI/CD defined as YAML but not managed by IaC tooling. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GitHub Actions CI/CD pipelines exist with build, test, and deploy stages. **CI** (`.github/workflows/ci.yml`): Runs on push/PR to master. Matrix testing across Python 3.9–3.14. Stages: checkout → setup Python → install dependencies (pipenv) → lint (flake8, black, isort) → test (pytest) → coverage (Coveralls). **CD** (`.github/workflows/cd.yml`): Manual `workflow_dispatch` trigger with dry-run option. Stages: build package → tag version → create GitHub Release → publish to PyPI via trusted publisher (OIDC `id-token: write`). **Maintenance** (`.github/workflows/maintenance.yml`): Automated stale issue/PR cleanup on schedule. |
| **Gap** | CI pipeline lacks security scanning (no SAST, no dependency vulnerability scanning). CD pipeline has no automated testing gate before publish — it relies on CI having passed on the master branch, but there's no explicit gate. No automated rollback mechanism for bad PyPI releases. |
| **Recommendation** | Add `pip-audit` or `safety` to the CI pipeline for dependency scanning. Add a step in CD that explicitly requires the CI workflow to have passed on the tagged commit before publishing. Consider publishing to Test PyPI first as a validation step. |
| **Evidence** | `.github/workflows/ci.yml`, `.github/workflows/cd.yml`, `.github/workflows/maintenance.yml`, `Makefile` (test/lint targets). |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Python 3.9–3.14 supported (defined in `zappa/__init__.py` `SUPPORTED_VERSIONS` and `setup.py` classifiers). Modern Python at current versions with a mature cloud-native ecosystem. AWS SDK: `boto3 >= 1.17.28` (current Python AWS SDK v1, the standard for Python). Framework ecosystem: `troposphere >= 3.0` (CloudFormation template generation), `werkzeug` (WSGI utilities), `requests >= 2.32.0`, `PyYAML`, `argcomplete`, `click` (CLI framework). Dev tooling: `mypy 1.8.0` for static type checking, `black 24.8.0` for formatting, `flake8 7.0.0` for linting, `pytest` for testing. All dependencies are current and well-maintained. |
| **Gap** | None. Python is a first-class AWS SDK language with excellent cloud-native tooling. The framework supports the latest Python versions including 3.14 (pre-release). |
| **Recommendation** | No action needed. Continue tracking Python version releases and updating `SUPPORTED_VERSIONS` as AWS Lambda adds runtime support. |
| **Evidence** | `zappa/__init__.py` — `SUPPORTED_VERSIONS = [(3, 9), (3, 10), (3, 11), (3, 12), (3, 13), (3, 14)]`. `setup.py` — `python_requires=">=3.9"`. `Pipfile` — `boto3 = ">=1.17.28"`, `troposphere = ">=3.0"`. |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Single Python package (`zappa/`) with well-defined module boundaries and distinct responsibilities. Module structure: `core.py` (AWS API interactions, ~3,867 lines), `cli.py` (CLI interface, ~3,656 lines), `handler.py` (Lambda request handler), `wsgi.py` (WSGI request translation), `asgi.py` (ASGI request translation), `asynchronous.py` (async task dispatch), `middleware.py` (WSGI middleware), `utilities.py` (shared utilities), `websocket.py` (WebSocket support), `letsencrypt.py` (SSL cert management), `ext/django_zappa.py` (Django integration). No circular imports detected — modules have clear dependency direction (`cli → core → utilities`, `handler → wsgi/asgi/middleware/utilities`). |
| **Gap** | The two largest modules (`core.py` at 3,867 lines and `cli.py` at 3,656 lines) are large but have clear internal structure. `core.py` combines AWS resource management for Lambda, API Gateway, S3, CloudWatch Events, IAM, Route53, and more — these could be separate service-specific modules. As a library (not a deployed service), decomposition into microservices is not applicable, but modular decomposition would improve maintainability. |
| **Recommendation** | Consider splitting `core.py` into domain-specific modules (e.g., `core/lambda_ops.py`, `core/apigateway_ops.py`, `core/s3_ops.py`, `core/iam_ops.py`) for improved maintainability. This is internal refactoring, not service decomposition. |
| **Evidence** | `zappa/` directory structure — 13 Python modules. `zappa/core.py` — 3,867 lines. `zappa/cli.py` — 3,656 lines. Clear import structure: `cli.py` imports from `core.py` and `utilities.py`. |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Sync request/response is the correct design; async not needed. The Zappa handler processes each Lambda invocation synchronously — translating the API Gateway/ALB event into a WSGI/ASGI environ, calling the user's web application, and returning the response. The framework does provide async task dispatch (`zappa/asynchronous.py`) as a feature for user applications, using managed services (Lambda invocation, SNS). |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `zappa/handler.py` — synchronous request processing pipeline. `zappa/asynchronous.py` — async task feature for users, not for the framework's own communication. |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. No operations exceed 30 seconds — not applicable by design. The Zappa handler processes individual HTTP requests within Lambda's timeout. The CLI commands (`deploy`, `update`) may take longer, but these are developer-initiated build operations, not runtime service operations. The framework supports Lambda timeout configuration (`timeout_seconds` in settings) for user applications. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `zappa/handler.py` — per-request processing. `example/zappa_settings.json` — `"timeout_seconds": 300` is user-configurable. |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The framework uses SemVer versioning (`__version__ = "0.62.1"` in `zappa/__init__.py`). The CD pipeline supports versioned releases with SemVer input and git tags. However, there is no formal API versioning strategy for the framework's Python API (public functions and classes). No `CHANGELOG.md` with breaking change documentation following SemVer conventions (the `CHANGELOG.md` exists but is not structured around breaking/non-breaking changes). The framework does not use deprecation warnings for API changes. No `/v1/`, `/v2/` patterns (expected — this is a library, not an HTTP API). |
| **Gap** | No formal Python API stability guarantees or deprecation policy. Internal module functions are not clearly marked as public vs private (no `__all__` exports in most modules). SemVer is used for releases but the version is still 0.x (pre-1.0), indicating no stability guarantees. |
| **Recommendation** | Define `__all__` in public-facing modules to establish a clear public API surface. Add deprecation warnings (`warnings.warn`) before removing or changing public functions. Consider moving to 1.0 to signal API stability commitment. Structure `CHANGELOG.md` with "Breaking Changes", "Features", "Fixes" sections. |
| **Evidence** | `zappa/__init__.py` — `__version__ = "0.62.1"`. `.github/workflows/cd.yml` — SemVer version input. `CHANGELOG.md` — exists but unstructured. |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The framework uses environment variables for service endpoint configuration. User deployments configure AWS service endpoints implicitly through boto3 (region-based). The framework supports `aws_region` settings, S3 bucket names, and Lambda function names as configuration in `zappa_settings.json`. For deployed applications, service endpoints are configured through environment variables (`ENVIRONMENT_VARIABLES` in settings) and remote environment files (S3-based `REMOTE_ENV`). No dynamic service discovery mechanism (AWS Cloud Map, Consul, Istio). |
| **Gap** | Endpoint configuration is static (environment variables and settings files). No dynamic service discovery for the framework or for user-deployed applications. This is expected for a CLI/library tool — the framework creates infrastructure, it doesn't participate in runtime service discovery. |
| **Recommendation** | For user-facing functionality, consider adding support for AWS Cloud Map service discovery as a deployment option, allowing Zappa-deployed applications to register with and discover services dynamically. This would enhance the framework's value for microservice deployments. |
| **Evidence** | `zappa/handler.py` — `ENVIRONMENT_VARIABLES` setting, `REMOTE_ENV` S3-based config loading. `example/zappa_settings.json` — static configuration. `zappa/cli.py` — `aws_region` setting. |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The framework uses S3 extensively for deployment artifacts — uploading zip packages, storing slim handler archives, and hosting remote environment configuration files. `zappa/core.py` contains comprehensive S3 operations including bucket creation, object upload, versioning support, and tagging. The framework supports S3 bucket configuration (`s3_bucket` setting) and uses S3 as the primary storage for deployment packages. No parsing pipeline (Textract, Tika) is present, which is expected — deployment artifacts don't need document parsing. |
| **Gap** | S3 usage is well-implemented for deployment artifacts but limited to deployment operations. No automated parsing or extraction pipeline exists, though this is not needed for the framework's use case. |
| **Recommendation** | No action needed. The framework correctly uses S3 for its deployment artifact storage use case. |
| **Evidence** | `zappa/core.py` — S3 client operations, bucket creation, object upload. `zappa/handler.py` — `load_remote_project_archive` (S3 tarball download). `zappa/policies/attach_policy.json` — `s3:*` permissions. |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | AWS service interactions are mostly centralized in `zappa/core.py`, which serves as the primary data access layer for all AWS API calls (Lambda, API Gateway, S3, CloudWatch Events, IAM, Route53, CloudFormation, etc.). `zappa/cli.py` delegates to `core.py` for AWS operations. However, some direct boto3 access exists outside `core.py`: `zappa/asynchronous.py` creates its own boto3 clients (`LAMBDA_CLIENT`, `SNS_CLIENT`, `STS_CLIENT`, `DYNAMODB_CLIENT`) at module level. `zappa/handler.py` creates boto3 sessions for S3 access in `_get_boto_session()`. `zappa/websocket.py` creates its own `apigatewaymanagementapi` client. |
| **Gap** | While `core.py` centralizes most AWS operations, three modules create their own boto3 clients directly: `asynchronous.py`, `handler.py`, and `websocket.py`. This creates multiple integration points with different session management patterns. |
| **Recommendation** | Consider providing a shared session factory or client provider that `asynchronous.py`, `handler.py`, and `websocket.py` can use instead of creating clients directly. This would centralize AWS credential handling and enable easier testing/mocking. |
| **Evidence** | `zappa/core.py` — centralized Zappa class with boto3 clients. `zappa/asynchronous.py` — module-level `aws_session = boto3.Session()`. `zappa/handler.py` — `_get_boto_session()`. `zappa/websocket.py` — `_get_ws_client()`. |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The framework references DynamoDB in `zappa/asynchronous.py` for async response tables (`ASYNC_RESPONSE_TABLE`) but does not pin or manage database engine versions. The framework does not define database resources in IaC — it creates DynamoDB tables at runtime via the user's boto3 session. No database version management, engine version pinning, or EOL tracking exists. The framework supports deploying applications that use databases but has no lifecycle management for the database resources it creates. |
| **Gap** | The `ASYNC_RESPONSE_TABLE` DynamoDB table has no defined lifecycle, version management, or cleanup strategy. The table schema and configuration are hardcoded in `asynchronous.py` (`put_item`, `update_item`, `get_item` operations) without versioning or migration support. TTL is set to 600 seconds per item, but table-level TTL configuration is not managed. |
| **Recommendation** | Document the DynamoDB table schema and lifecycle for the async response feature. Add TTL configuration management via IaC or a setup command. For user-facing database features, provide version-aware configuration templates. |
| **Evidence** | `zappa/asynchronous.py` — `DYNAMODB_CLIENT.put_item(TableName=ASYNC_RESPONSE_TABLE, Item={"id": ..., "ttl": {"N": str(int(time.time() + 600))}})`. No database engine version pins found anywhere in the codebase. |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs exist in the codebase. All business logic resides in the Python application layer. The framework does not interact with relational databases — its data operations are limited to DynamoDB (simple key-value operations in `asynchronous.py`) and S3 (object storage in `core.py`). No `.sql` files, no ORM configurations, no raw SQL execution patterns found. |
| **Gap** | None. All logic is in the Python application layer. |
| **Recommendation** | No action needed. |
| **Evidence** | No `.sql` files in repository. No `CREATE PROCEDURE`, `CREATE TRIGGER`, `CREATE FUNCTION` patterns found. No SQL driver imports (no SQLAlchemy, no JDBC, no psycopg2, no pymysql). |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail configuration exists for the framework. The framework generates IAM policies (`zappa/policies/attach_policy.json`) that include `logs:*` permissions for CloudWatch Logs, enabling logging for user-deployed Lambda functions. However, no CloudTrail, audit logging, or log immutability configuration exists for the framework's own AWS operations (deployments, updates, rollbacks). The CLI operations in `zappa/cli.py` and `zappa/core.py` make extensive AWS API calls that are only logged if the user's AWS account has CloudTrail enabled independently. |
| **Gap** | Framework operations (deploy, update, rollback, certify) are not audited beyond whatever CloudTrail configuration exists in the user's AWS account. No log file validation or immutable storage configuration. |
| **Recommendation** | Document CloudTrail requirements for Zappa deployments in the README. Consider adding a `zappa audit` command that verifies CloudTrail is enabled in the deployment account. For the framework's CI/CD pipeline, GitHub Actions provides audit logs natively. |
| **Evidence** | `zappa/policies/attach_policy.json` — `"logs:*"` permission. No `aws_cloudtrail` resources. No CloudTrail configuration in any file. |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no database, S3 bucket, EBS volume, or similar defined for the framework itself. The framework creates S3 buckets and Lambda functions in user accounts but does not own data-at-rest resources. Surface flag `has_at_rest_data_surface=false`. SEC-Q2 does not apply. Note: The framework does support `aws_kms_key_arn` for encrypting Lambda environment variables (`zappa/core.py` lines 1202, 1225-1226, 1242), which is a positive security feature for user deployments. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `zappa/core.py` — `aws_kms_key_arn` parameter support. No IaC-defined data stores. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The framework provides comprehensive API authentication support for user-deployed applications. `zappa/handler.py` supports API Gateway authorizers (Lambda authorizers, processing `authorizer` context from `requestContext`), IAM authentication (`remote_user` extraction from IAM identity), and Cognito triggers (`get_function_for_cognito_trigger`). `example/zappa_settings.json` shows `authorizer` configuration with Lambda authorizer function. The framework's own CLI uses AWS credentials (IAM) for deployment operations via boto3 — this is standard AWS authentication. |
| **Gap** | Token-based auth (OAuth2/JWT) support depends on the user's web framework configuration, not the Zappa framework directly. The framework facilitates API Gateway authorizer integration but does not enforce authentication by default — new deployments can be created without any auth configuration. |
| **Recommendation** | Consider adding a warning during `zappa deploy` when no authorizer is configured, prompting users to add authentication. Document recommended authentication patterns (API Gateway authorizers, Cognito) in the README. |
| **Evidence** | `zappa/handler.py` — authorizer context extraction. `example/zappa_settings.json` — `"authorizer": {"function": "authmodule.lambda_handler"}`. `zappa/core.py` — API Gateway authorizer creation via troposphere. |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The framework supports Cognito integration for user-deployed applications. `zappa/handler.py` includes `get_function_for_cognito_trigger` handling Cognito trigger events (`triggerSource` in event). `zappa/policies/assume_policy.json` includes `apigateway.amazonaws.com`, `lambda.amazonaws.com`, and `events.amazonaws.com` as trusted principals. The framework supports API Gateway authorizers which can integrate with any OIDC/OAuth2 provider via Lambda authorizers. Some legacy auth patterns remain — direct IAM authentication and basic API key support coexist with Cognito integration. |
| **Gap** | Cognito integration is supported but not deeply integrated — the framework passes Cognito events through to user-defined handler functions rather than providing first-class Cognito User Pool configuration. No SAML/OIDC federation configuration support in `zappa_settings.json`. |
| **Recommendation** | Consider adding first-class `cognito_user_pool` configuration in `zappa_settings.json` to simplify Cognito-based authentication setup for API Gateway. |
| **Evidence** | `zappa/handler.py` — `get_function_for_cognito_trigger`, `COGNITO_TRIGGER_MAPPING`. `zappa/policies/assume_policy.json` — trust policy. |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No plaintext credentials found in source code or configuration files. The `.gitignore` excludes `zappa_settings.json` (which may contain AWS credentials), `.env` files, and other sensitive files. The framework supports: (1) `REMOTE_ENV` — loading environment variables from S3 JSON files (`zappa/handler.py` `load_remote_settings`), (2) `aws_kms_key_arn` — KMS encryption for Lambda environment variables (`zappa/core.py` line 1202), (3) AWS credential profiles via `profile_name` setting. However, no integration with AWS Secrets Manager or HashiCorp Vault exists. The `REMOTE_ENV` S3 file approach stores secrets as plaintext JSON in S3 (encrypted at rest if S3 bucket encryption is enabled, but no rotation). Environment variables set via `ENVIRONMENT_VARIABLES` in settings are stored in plaintext in the Lambda function configuration (unless KMS key is configured). |
| **Gap** | No Secrets Manager integration. `REMOTE_ENV` is S3-based without rotation. `ENVIRONMENT_VARIABLES` in `zappa_settings.json` could contain secrets stored as plaintext in the settings file (though `.gitignore` excludes this file). No automated secret rotation support. |
| **Recommendation** | Add AWS Secrets Manager integration as a configuration option — allow `zappa_settings.json` to reference Secrets Manager ARNs that are resolved at deploy time or runtime. Document best practices for secrets management in Zappa deployments (use KMS encryption, avoid plaintext in settings files). |
| **Evidence** | `.gitignore` — excludes `zappa_settings.json`. `zappa/handler.py` — `REMOTE_ENV` S3 loading. `zappa/core.py` — `aws_kms_key_arn` parameter. No `aws_secretsmanager_*` references in codebase. |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The framework deploys to AWS Lambda, which provides AWS-managed compute hardening and patching — Lambda runtime environments are maintained by AWS with security patches applied automatically. This is a strong baseline. However, the framework's own CI/CD pipeline has no vulnerability scanning. No SSM Patch Manager (N/A — no EC2 instances). No AWS Inspector or Snyk integration. The pre-commit hooks (`.pre-commit-config.yaml`) include code quality tools (black, isort, flake8, mypy) but no security-focused hooks (bandit, safety, pip-audit). |
| **Gap** | While Lambda provides managed patching for runtime, the framework's Python dependencies are not scanned for known vulnerabilities. No security-focused linting (bandit) or dependency auditing in the CI pipeline. |
| **Recommendation** | Add `bandit` to pre-commit hooks for Python security linting. Add `pip-audit` or `safety` to the CI pipeline to catch known vulnerabilities in dependencies. Consider adding `dependabot.yml` configuration for automated dependency update PRs. |
| **Evidence** | Lambda = AWS-managed patching. `.pre-commit-config.yaml` — flake8, black, isort, mypy (no bandit). `.github/workflows/ci.yml` — no security scanning steps. `Pipfile` — dependencies without vulnerability monitoring. |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SAST, DAST, or dependency vulnerability scanning tools are integrated into the CI/CD pipeline. The CI pipeline (`.github/workflows/ci.yml`) runs only: lint (flake8, black, isort), test (pytest), and coverage (Coveralls). No Dependabot configuration found (no `.github/dependabot.yml`). No Snyk, CodeQL, Semgrep, or other SAST tools. No `npm audit` equivalent (`pip-audit`, `safety`) in the pipeline. No container scanning (no containers to scan). The pre-commit configuration (`.pre-commit-config.yaml`) includes code quality tools but no security-focused hooks. |
| **Gap** | The CI/CD pipeline has no security validation step. Dependencies (`boto3`, `requests`, `werkzeug`, `troposphere`, `PyYAML`) are not scanned for known CVEs. No SAST tool analyzes the codebase for security vulnerabilities. |
| **Recommendation** | (1) Add `pip-audit` to CI: `pipenv run pip-audit` as a pipeline step. (2) Configure `.github/dependabot.yml` for automated dependency updates with security-only focus. (3) Add CodeQL or Semgrep GitHub Action for SAST. (4) Add `bandit` to pre-commit hooks for Python-specific security linting. This is the highest-priority security improvement. |
| **Evidence** | `.github/workflows/ci.yml` — no security scanning steps. No `.github/dependabot.yml`. No `.snyk` policy file. `.pre-commit-config.yaml` — no bandit or safety hooks. |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The framework provides built-in AWS X-Ray tracing support. `zappa/core.py` (line 206): `xray_tracing = False` (default). When enabled via `xray_tracing: true` in `zappa_settings.json`, the framework configures Lambda functions with `TracingConfig: {"Mode": "Active"}` (`zappa/core.py` line 1243). The IAM attach policy (`zappa/policies/attach_policy.json`) includes `xray:PutTraceSegments` and `xray:PutTelemetryRecords` permissions by default. The framework also provides Apache NCSA Common Log Format logging (`zappa/utilities.py` `ApacheNCSAFormatters`) with response time tracking in `zappa/handler.py`. No OpenTelemetry integration found in dependencies. |
| **Gap** | X-Ray tracing is optional (default: off) and requires manual configuration. No OpenTelemetry support. X-Ray trace context propagation depends on the user's web framework — Zappa doesn't add tracing middleware automatically. |
| **Recommendation** | Consider adding OpenTelemetry SDK as an optional dependency with auto-instrumentation middleware for WSGI/ASGI apps deployed via Zappa. This would provide vendor-neutral tracing support alongside the existing X-Ray integration. |
| **Evidence** | `zappa/core.py` lines 206, 226, 259, 1204, 1243, 1443 — `xray_tracing` support. `zappa/policies/attach_policy.json` — X-Ray permissions. `zappa/cli.py` line 124, 2717 — `xray_tracing` setting loading. |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no user-facing surface for which SLOs are meaningful. The framework is a CLI tool and library — it does not serve production traffic. Surface flags `has_api_surface=false` and `has_persistent_data_store=false`. OPS-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No SLO definitions, no CloudWatch alarms, no error budget tracking in repository. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom metrics are published for the framework. The framework supports CloudWatch logging for user-deployed applications (via `logs:*` IAM permissions) and provides detailed Apache NCSA log formatting (`zappa/utilities.py` `ApacheNCSAFormatters`) with response time tracking. However, no `cloudwatch.put_metric_data` calls exist in the framework for its own business metrics (deployment success rates, package sizes, deployment durations, version adoption). |
| **Gap** | No framework-level metrics tracking. Deployment operations in `zappa/core.py` and `zappa/cli.py` do not emit metrics that could inform maintainers about framework health or usage patterns. |
| **Recommendation** | Consider adding opt-in telemetry for deployment metrics (anonymized deployment counts, Python version distribution, error rates). This could use CloudWatch custom metrics or a lightweight analytics endpoint. Ensure any telemetry is opt-in with clear documentation. |
| **Evidence** | No `put_metric_data` calls in codebase. `zappa/utilities.py` — `ApacheNCSAFormatters` (access logging only). `zappa/policies/attach_policy.json` — no CloudWatch Metrics permissions beyond logs. |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configuration exists. The framework does not define CloudWatch alarms, anomaly detection rules, or PagerDuty/OpsGenie integrations. For user deployments, the framework supports CloudWatch logging but does not create alarms as part of the deployment process. No composite alarms, no error rate monitoring, no latency alerting. |
| **Gap** | No alerting for the framework's own operations or for user deployments. Users must configure monitoring independently after deploying with Zappa. |
| **Recommendation** | Consider adding optional alarm creation during `zappa deploy` — create CloudWatch alarms for Lambda error rate, throttling, and duration. Provide alarm templates in `zappa_settings.json` configuration. This would significantly improve the operational posture of Zappa-deployed applications. |
| **Evidence** | No `aws_cloudwatch_metric_alarm`, `put_metric_alarm`, or alerting configuration found in codebase. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The framework's own deployment (PyPI publishing) uses a manual `workflow_dispatch` trigger with a dry-run option in `.github/workflows/cd.yml`. The pipeline stages are: build → tag → release → publish. Version tags and GitHub Releases provide rollback capability (by publishing a new version). No canary or staged rollout to PyPI. For user deployments, the framework supports `zappa rollback <n>` which reverts to previous Lambda deployment packages stored in S3 — this is a basic rollback mechanism. No blue/green, canary, or traffic shifting for user deployments. |
| **Gap** | No staged rollout for library releases. No canary deployment support for user applications. The `zappa rollback` command is a manual emergency tool, not a deployment strategy. No Lambda alias-based traffic shifting. |
| **Recommendation** | For library releases: add a Test PyPI publish step before production PyPI. For user deployments: consider adding Lambda alias-based canary deployment support (e.g., `zappa deploy --canary 10%`) using Lambda weighted aliases. This aligns with API Gateway canary release support. |
| **Evidence** | `.github/workflows/cd.yml` — manual dispatch, no staging. `zappa/cli.py` — `rollback` command. No Lambda alias or traffic shifting configuration in codebase. |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Extensive test suite (~8,515 lines across 34 test files) covering core functionality. Tests use the `placebo` library to mock AWS API responses, providing deterministic, fast test execution. Test categories: `test_core.py` (4,447 lines — AWS operations), `test_handler.py` (691 lines — Lambda handler), `test_asgi.py` (499 lines — ASGI support), `test_placebo.py` (635 lines — AWS mocking), `test_utilities.py` (499 lines — utilities), `test_websocket.py` (621 lines — WebSocket), `test_middleware.py` (279 lines), `test_async.py` (102 lines). CI runs tests across Python 3.9–3.14 with coverage reporting via Coveralls. |
| **Gap** | All tests use mocked AWS responses (placebo). No live integration tests against actual AWS services (no real Lambda deployments, no real API Gateway creation, no real S3 operations in CI). While mocked tests are comprehensive, they cannot catch issues with actual AWS API behavior changes, IAM permission problems, or CloudFormation template validation errors. |
| **Recommendation** | Create a dedicated integration test workflow that deploys a minimal application to a test AWS account, validates the deployment (HTTP request to API Gateway), and tears it down. Run on a schedule (weekly) or before releases. Use a dedicated AWS account with minimal permissions. |
| **Evidence** | `tests/` — 34 test files, ~8,515 lines. `.github/workflows/ci.yml` — pytest with coverage. `Pipfile` — `placebo = "<0.10"` (AWS API mocking). `Makefile` — `tests` target. |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, incident response automation, or self-healing patterns exist. The `maintenance.yml` workflow handles stale issue/PR cleanup (automated repository maintenance) but not incident response. No Systems Manager Automation documents, no Lambda-based remediation, no incident workflow definitions. The framework provides `zappa tail` for log viewing and `zappa rollback` for emergency rollback, but these are manual tools, not automated response workflows. |
| **Gap** | No documented incident response procedures for framework issues or for user deployments. No automated remediation for common failure modes (deployment failures, Lambda timeout issues, API Gateway throttling). |
| **Recommendation** | Create runbooks (Markdown documents in `docs/runbooks/`) for common operational scenarios: failed deployments, Lambda cold start issues, API Gateway throttling, and rollback procedures. For user deployments, consider adding a `zappa doctor` command that diagnoses common issues (permissions, VPC configuration, timeout settings). |
| **Evidence** | `.github/workflows/maintenance.yml` — stale issue cleanup only. No runbook files in repository. No SSM Automation documents. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership artifacts exist. No CODEOWNERS file. No per-service dashboards or alarms with named owners. No SLO definitions with team attribution. The framework is an open-source project maintained by community contributors — traditional observability ownership patterns (named owners, team attribution) do not directly apply, but code ownership and monitoring of the CI/CD pipeline could be formalized. |
| **Gap** | No CODEOWNERS file to establish code review ownership. No CI/CD health dashboards. No monitoring of PyPI package health (download trends, compatibility issues). |
| **Recommendation** | Add a `CODEOWNERS` file mapping critical paths (`zappa/handler.py`, `zappa/core.py`, `.github/workflows/`) to core maintainers. Consider adding CI/CD health monitoring via GitHub status badges and scheduled health check workflows. |
| **Evidence** | No `CODEOWNERS` file found. No dashboard definitions. No alarm ownership documentation. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The framework supports resource tagging through `zappa_settings.json`. `zappa/cli.py` (line 2769-2770): `self.tags = self.stage_config.get("tags", {})`. Tags are applied to Lambda functions, S3 buckets, and other resources during deployment. `zappa/core.py` (lines 224, 299, 324, 959-960): Tags are propagated to CloudFormation parameters and S3 bucket tag sets. The framework allows users to define arbitrary key-value tags in their settings. |
| **Gap** | No default tags are enforced — tagging is entirely opt-in. No mandatory tags (e.g., `project`, `environment`, `managed-by`) are applied automatically. No tag validation or enforcement rules. Different resource types may have inconsistent tag application. |
| **Recommendation** | Add default tags automatically to all resources created by Zappa (e.g., `managed-by: zappa`, `zappa-version: 0.62.1`, `zappa-project: <project_name>`, `zappa-stage: <stage>`). Document recommended tagging practices in the README. Consider adding tag validation in `zappa_settings.json` schema. |
| **Evidence** | `zappa/cli.py` lines 2769-2770 — tag loading from settings. `zappa/core.py` lines 959-960 — S3 tag set application. `zappa/core.py` line 224 — `tags=()` default parameter. |

---

## Learning Materials

The following learning resources are mapped to the triggered pathway:

### Move to Modern DevOps

- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `zappa/__init__.py` | APP-Q1, APP-Q5 | Python version support (3.9–3.14), SemVer version `0.62.1` |
| `zappa/core.py` | INF-Q1, INF-Q4, INF-Q5, INF-Q6, INF-Q7, INF-Q10, SEC-Q2, SEC-Q3, SEC-Q5, OPS-Q1, OPS-Q9, DATA-Q1, DATA-Q2, APP-Q2 | Core AWS operations library (3,867 lines), troposphere IaC generation, VPC config, KMS support, X-Ray config, tagging, S3 operations |
| `zappa/cli.py` | INF-Q3, INF-Q11, APP-Q2, APP-Q6, OPS-Q1, OPS-Q5, OPS-Q9 | CLI interface (3,656 lines), xray_tracing setting, tags loading, rollback command |
| `zappa/handler.py` | INF-Q4, APP-Q2, APP-Q3, APP-Q4, SEC-Q3, SEC-Q4, SEC-Q5, APP-Q6, DATA-Q1 | Lambda request handler, WSGI/ASGI processing, authorizer support, REMOTE_ENV loading |
| `zappa/wsgi.py` | APP-Q2 | WSGI request translation module |
| `zappa/asgi.py` | APP-Q2 | ASGI request translation module |
| `zappa/asynchronous.py` | INF-Q2, INF-Q4, DATA-Q2, DATA-Q3 | Async task dispatch via Lambda/SNS, DynamoDB response table, boto3 client creation |
| `zappa/middleware.py` | APP-Q2 | WSGI middleware for cookie handling |
| `zappa/utilities.py` | APP-Q2, DATA-Q2, OPS-Q1, OPS-Q3 | Shared utilities, ApacheNCSAFormatters, event source implementations |
| `zappa/websocket.py` | DATA-Q2 | WebSocket support, boto3 apigatewaymanagementapi client |
| `zappa/letsencrypt.py` | APP-Q2 | Let's Encrypt SSL certificate management |
| `zappa/ext/django_zappa.py` | APP-Q2 | Django WSGI integration |
| `zappa/policies/attach_policy.json` | INF-Q4, SEC-Q1, SEC-Q5, OPS-Q1, DATA-Q1 | IAM attach policy with logs, X-Ray, S3, SNS, SQS, DynamoDB permissions |
| `zappa/policies/assume_policy.json` | SEC-Q4 | IAM trust policy for API Gateway, Lambda, Events |
| `.github/workflows/ci.yml` | INF-Q11, SEC-Q6, SEC-Q7, OPS-Q5, OPS-Q6 | CI pipeline: lint, test, coverage across Python 3.9–3.14 |
| `.github/workflows/cd.yml` | INF-Q11, APP-Q5, OPS-Q5 | CD pipeline: build, tag, release, PyPI publish |
| `.github/workflows/maintenance.yml` | OPS-Q7 | Automated stale issue/PR cleanup |
| `.pre-commit-config.yaml` | SEC-Q6, SEC-Q7 | Pre-commit hooks: black, isort, flake8, mypy (no security hooks) |
| `.gitignore` | SEC-Q5 | Excludes zappa_settings.json, .env files, sensitive configurations |
| `Pipfile` | APP-Q1, OPS-Q6 | Dependency manifest: boto3, troposphere, werkzeug, requests, placebo |
| `setup.py` | APP-Q1 | Package metadata, python_requires >= 3.9, entry_points |
| `example/zappa_settings.json` | SEC-Q3, APP-Q6 | Example settings with authorizer, region, S3 bucket configuration |
| `Makefile` | OPS-Q6 | Build/test targets: tests, flake, black, isort, mypy |
| `README.md` | Quick Agent Wins | Extensive documentation (2,217 lines) |
| `CONTRIBUTING.md` | Quick Agent Wins | Contribution guidelines |
| `CHANGELOG.md` | APP-Q5 | Version history (unstructured) |
| `tests/` | OPS-Q6 | Test suite: 34 files, ~8,515 lines, placebo-based AWS mocking |
