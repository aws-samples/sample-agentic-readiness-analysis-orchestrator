# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | Zappa |
| **Date** | 2025-07-15 |
| **Repo Type** | application |
| **Service Archetype** | orchestrator (auto-detected) |
| **Priority** | P2 |
| **Tags** | python, serverless |
| **Context** | Python framework for deploying WSGI apps on AWS Lambda. |
| **Overall Score** | 2.57 / 4.0 |

**Archetype Justification**: Zappa's `core.py` initializes boto3 clients for 15+ AWS services (Lambda, API Gateway, S3, CloudFormation, IAM, Route53, SNS, DynamoDB, CloudWatch, ELBv2, EFS, ACM, STS, Cognito, Events) and the CLI orchestrates multi-step workflows across these services during deploy/update/undeploy operations. This high fan-out coordination pattern classifies it as an orchestrator.

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 2.18 / 4.0 | 🟠 Needs Work |
| Application Architecture (APP) | 2.83 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 3.75 / 4.0 | ✅ Mature |
| Security Baseline (SEC) | 2.29 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.78 / 4.0 | 🟠 Needs Work |
| **Overall** | **2.57 / 4.0** | **🟡 Partial** |

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q3: Workflow Orchestration | 1 | Multi-step deploy/update workflows across 15+ AWS services are entirely hardcoded in cli.py/core.py with no dedicated orchestration service — anti-pattern for orchestrator archetype | Hardcoded orchestration creates tight coupling, makes error recovery manual, and prevents visual workflow management for complex deployment pipelines |
| 2 | INF-Q10: IaC Coverage | 1 | No infrastructure-as-code for the tool's own infrastructure; CloudFormation templates are generated programmatically but the tool's deployment/release infra is not codified | Unable to reproduce infrastructure, no environment consistency, manual infrastructure changes are error-prone |
| 3 | SEC-Q7: App Security Pipeline | 1 | No SAST, dependency vulnerability scanning, or container scanning in CI/CD — only linting (flake8/black/isort) | Vulnerabilities in dependencies or code patterns can reach PyPI releases undetected |
| 4 | OPS-Q2: SLO Definitions | 1 | No SLO definitions for deployment success rates, Lambda cold-start latency, or API Gateway response times | Cannot measure whether Zappa-deployed applications meet user expectations or degrade over time |
| 5 | OPS-Q4: Anomaly Detection | 1 | No anomaly detection or alerting configuration for deployed workloads | Gradual degradation and novel failure modes in Zappa-deployed apps go undetected |

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 3). GitHub Actions workflows found at `.github/workflows/ci.yml` and `.github/workflows/cd.yml` with build, test, lint, and publish stages.
- **What it enables:** A DevOps agent that triggers CI runs, checks build status, monitors test results across the Python 3.9–3.14 matrix, and manages PyPI releases via the CD workflow dispatch.
- **Additional steps:** The CD workflow is currently manual-trigger only (`workflow_dispatch`). An agent could orchestrate the release process by triggering the workflow and monitoring its completion.
- **Effort:** Low

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository. `README.md` (2,217 lines, 100KB) provides comprehensive documentation covering installation, configuration, all CLI commands, advanced settings, and troubleshooting. `CHANGELOG.md`, `CONTRIBUTING.md`, and `docs/` directory provide additional content.
- **What it enables:** A RAG-based knowledge agent using Amazon Bedrock that indexes the README, changelog, and inline docstrings to answer developer questions about Zappa configuration, deployment patterns, and troubleshooting.
- **Additional steps:** Generate embeddings from README.md and source code docstrings. Consider indexing GitHub issues and discussions for broader coverage.
- **Effort:** Medium

### Observability Agent

- **Prerequisite:** Structured logging and tracing support in place (OPS-Q1 = 2). X-Ray tracing configurable via `xray_tracing` setting. CloudWatch logging configurable via `cloudwatch_log_level`. Common Log Format logging in `handler.py`.
- **What it enables:** An observability agent that queries CloudWatch logs from Zappa-deployed Lambda functions, traces request flows via X-Ray, and suggests root causes for deployment or runtime failures.
- **Additional steps:** X-Ray SDK should be added as an explicit dependency. Cross-service trace propagation needs to be verified for end-to-end correlation.
- **Effort:** Medium

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 (modular package with clear boundaries). Primary trigger not met. |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 3 (already on managed compute via Lambda). Contextual guard: compute is Lambda/serverless, not EC2/VM-based. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (no stored procedures). No commercial database engines detected. |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = 3 (databases already managed — DynamoDB, S3). |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 2 but no evidence of data processing workloads. Contextual guard prevents trigger. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (no IaC). Supporting: OPS-Q5 = 2 (no canary/blue-green). |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in context. Context is "Python framework for deploying WSGI apps on AWS Lambda." — no AI signal terms found. |

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 1):**
Zappa has no infrastructure-as-code for its own infrastructure. While the tool generates CloudFormation templates programmatically (via troposphere) for user applications, the tool's own release infrastructure, CI/CD environment, and operational resources are not defined in IaC. All infrastructure is configured manually through GitHub repository settings and PyPI project configuration.

**Current CI/CD State (INF-Q11 = 3):**
GitHub Actions CI pipeline (`.github/workflows/ci.yml`) runs a test matrix across Python 3.9–3.14 with linting (flake8, black, isort) and coverage reporting (Coveralls). The CD pipeline (`.github/workflows/cd.yml`) supports manual-trigger releases to PyPI with build verification. However, there is no automated rollback, no deployment staging, and no security scanning gates.

**Deployment Strategy Gaps (OPS-Q5 = 2):**
Lambda versioning and rollback are supported (`rollback_lambda_function_version`), and ALB alias (`ALB_LAMBDA_ALIAS`) enables zero-downtime updates. However, there is no canary or blue-green deployment pattern for Zappa-deployed applications. Deployments go directly to the Lambda function alias without traffic shifting.

**Recommended DevOps Improvements:**
1. **Add IaC for CI/CD infrastructure** — Define GitHub Actions runners, secrets, and environment configurations as code. Consider using AWS CodePipeline or EventBridge-triggered workflows for release automation.
2. **Add security scanning to CI** — Integrate `pip-audit` or `safety` for dependency vulnerability scanning. Add Dependabot configuration for automated dependency updates. Consider adding Semgrep or Bandit for SAST.
3. **Implement canary deployments** — Leverage Lambda weighted aliases and CodeDeploy for gradual traffic shifting. Zappa already creates Lambda aliases for ALB — extend this pattern to support canary/linear traffic shifting via API Gateway or CodeDeploy.
4. **Add automated rollback** — The `rollback_lambda_function_version` function exists but is manual. Integrate CloudWatch alarm-triggered automatic rollback via CodeDeploy.

**Representative AWS Services:** CodeBuild, CodePipeline, CodeDeploy (for Lambda canary), EventBridge (preferred per preferences), CloudFormation, CDK, CloudWatch

**Links:**
- [AWS DevOps Prescriptive Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/devops-pattern-list.html)
- [Lambda deployment with CodeDeploy](https://docs.aws.amazon.com/lambda/latest/dg/lambda-rolling-deployments.html)

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Zappa is fundamentally a serverless deployment framework. The `core.py` `create_lambda_function()` method creates Lambda functions (managed compute) with configurable runtime, memory, timeout, VPC, layers, and architecture (x86_64/arm64). API Gateway (v1 REST and v2 HTTP) is created via CloudFormation templates generated with troposphere. Docker image-based Lambda deployments are also supported (`docker_image_uri` parameter). The tool's own handler (`handler.py`) runs as a Lambda function. No EC2 instances are used. |
| **Gap** | The Zappa CLI tool itself runs locally (not on managed compute). It is distributed as a PyPI package and executed on developer machines. |
| **Recommendation** | No action needed. Zappa correctly targets Lambda as the compute platform for deployed applications. The CLI tool running locally is the expected pattern for deployment tools. |
| **Evidence** | `zappa/core.py` (create_lambda_function, update_lambda_function), `zappa/handler.py` (LambdaHandler), `setup.py` (console_scripts entry point) |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Zappa uses DynamoDB (fully managed) for async task response storage (`create_async_dynamodb_table` in `core.py`, `DYNAMODB_CLIENT` in `asynchronous.py`). S3 (fully managed) is used for deployment package storage and remote environment configuration. No self-managed databases are used. DynamoDB tables include TTL configuration for automatic cleanup. |
| **Gap** | Database resources (DynamoDB table for async responses) are created programmatically via boto3 rather than defined in IaC. No Multi-AZ configuration needed (DynamoDB is inherently multi-AZ). |
| **Recommendation** | Consider defining the async DynamoDB table as IaC (CloudFormation or CDK) rather than creating it imperatively via boto3. This would improve reproducibility and governance. |
| **Evidence** | `zappa/core.py` (create_async_dynamodb_table, _set_async_dynamodb_table_ttl), `zappa/asynchronous.py` (DYNAMODB_CLIENT, run_message, get_async_response) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | **Orchestrator archetype — anti-pattern detected.** Zappa's deployment workflow spans 15+ AWS services (IAM role creation → Lambda function creation → API Gateway setup via CloudFormation → Route53 DNS → SNS topic creation → CloudWatch Events scheduling → EFS provisioning) and is entirely hardcoded in `cli.py` and `core.py`. Each step calls boto3 synchronously with basic error handling. No Step Functions, Temporal, or other dedicated orchestration service is used. Rollback is manual (`rollback_lambda_function_version` handles only Lambda code, not the full deployment stack). |
| **Gap** | The entire multi-service deployment orchestration is hardcoded in Python with no managed workflow service. Error recovery is ad-hoc — if a step fails mid-deployment, partial state must be cleaned up manually. No retry policies, no compensation logic, no visual workflow management. This is a significant anti-pattern for the orchestrator archetype. |
| **Recommendation** | Consider introducing AWS Step Functions (or EventBridge-based orchestration per preferences) for the core deploy/update/undeploy workflows. Start with the most complex workflow (deploy) and model it as a state machine with explicit error handling, retries, and compensation steps. This would provide visual workflow management, automatic retries, and structured error recovery. |
| **Evidence** | `zappa/cli.py` (3,656 lines of hardcoded orchestration), `zappa/core.py` (sequential boto3 calls in deploy methods) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | **Orchestrator archetype calibration applied.** Zappa provides managed messaging integration: SNS for async task dispatch (`create_async_sns_topic`, `SnsAsyncResponse`), SQS event sources (`SqsEventSource`), DynamoDB Streams (`DynamoDBStreamEventSource`), Kinesis (`KinesisEventSource`), and CloudWatch Events/EventBridge (`schedule_events`). All managed services. However, the core deployment orchestration fan-out is entirely synchronous — the CLI invokes boto3 calls sequentially across 15+ services with no async decoupling. |
| **Gap** | For an orchestrator archetype, synchronous fan-out across many services is a risk — failures cascade, timeouts amplify, and there's no decoupling between orchestration steps. The async task system (SNS/Lambda) is available but is a feature for user applications, not used for Zappa's own orchestration. |
| **Recommendation** | Leverage EventBridge (preferred per preferences) or SNS for decoupling deployment orchestration steps. For example, emit events after each deployment stage completion to enable parallel execution of independent steps (e.g., Route53 DNS setup can happen in parallel with CloudWatch Events scheduling). |
| **Evidence** | `zappa/core.py` (create_async_sns_topic, schedule_events), `zappa/asynchronous.py` (LambdaAsyncResponse, SnsAsyncResponse), `zappa/utilities.py` (SqsEventSource, DynamoDBStreamEventSource, KinesisEventSource) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Zappa provides VPC configuration for Lambda functions (`vpc_config` parameter in `create_lambda_function`). The `attach_policy.json` includes EC2 network interface permissions (AttachNetworkInterface, CreateNetworkInterface, etc.) to support Lambda VPC deployment. However, VPC configuration is optional and not enforced by default. |
| **Gap** | VPC deployment is opt-in via `zappa_settings.json` configuration. By default, Lambda functions are deployed outside a VPC. No security group rules are defined in the codebase. The `attach_policy.json` grants `ec2:*NetworkInterface*` with `Resource: "*"` — overly permissive. |
| **Recommendation** | Document VPC deployment as a security best practice in README. Consider adding security group validation when VPC config is provided. Scope the EC2 network interface permissions to specific resources rather than `"*"`. |
| **Evidence** | `zappa/core.py` (create_lambda_function vpc_config parameter), `zappa/policies/attach_policy.json` (EC2 permissions) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Zappa creates API Gateway (v1 REST and v2 HTTP) as the entry point for deployed applications. `create_api_gateway_routes()` supports REST API with authorizers, CORS, and API key requirements. `create_api_gateway_v2_routes()` supports HTTP API with CORS and IAM authorization. CloudFront distribution is supported for Function URL custom domains. ALB integration is also available. |
| **Gap** | While API Gateway is fully supported for user applications, the tool provides limited configuration — no throttling configuration, no request validation templates, no WAF integration. These must be configured separately. |
| **Recommendation** | Add API Gateway throttling defaults and WAF integration options to `zappa_settings`. Consider adding API Gateway usage plans and request validation as configurable features. Leverage API Gateway (preferred per preferences) features more comprehensively. |
| **Evidence** | `zappa/core.py` (create_api_gateway_routes, create_api_gateway_v2_routes, deploy_api_gateway, create_websocket_api) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Lambda functions auto-scale by default. Zappa supports Lambda concurrency configuration via `put_function_concurrency` (`concurrency` parameter in `create_lambda_function` and `update_lambda_function`). DynamoDB tables created by Zappa use provisioned capacity with configurable read/write capacity units. |
| **Gap** | DynamoDB auto-scaling is not configured — tables use static provisioned capacity (`ReadCapacityUnits`, `WriteCapacityUnits`). No DynamoDB on-demand mode support. Lambda reserved concurrency is set but unreserved concurrency limits are not managed. |
| **Recommendation** | Add DynamoDB on-demand capacity mode or auto-scaling configuration for the async response table. Consider adding Lambda provisioned concurrency support for latency-sensitive workloads. |
| **Evidence** | `zappa/core.py` (create_lambda_function concurrency, create_async_dynamodb_table ProvisionedThroughput) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration found in the repository. DynamoDB tables created by Zappa do not have point-in-time recovery enabled. S3 buckets created by Zappa do not have versioning enabled. No AWS Backup plans or EBS snapshot policies are defined. |
| **Gap** | The async DynamoDB response table has TTL-based cleanup but no backup. S3 deployment packages are transient but not protected. No disaster recovery strategy exists. |
| **Recommendation** | Enable point-in-time recovery on DynamoDB tables created by Zappa. Enable S3 versioning on deployment buckets. Add configuration options for backup policies in `zappa_settings`. |
| **Evidence** | `zappa/core.py` (create_async_dynamodb_table — no PITR, upload_to_s3 — no versioning) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Lambda functions are inherently multi-AZ — AWS runs Lambda across multiple availability zones automatically. DynamoDB is also inherently multi-AZ with automatic replication. ALB deployments (`deploy_lambda_alb`) require subnets in different availability zones. API Gateway is a regional, multi-AZ service. |
| **Gap** | High availability is inherited from managed services rather than explicitly configured. No cross-region failover or disaster recovery configuration. ALB availability zone requirement is enforced by AWS but not validated by Zappa. |
| **Recommendation** | Document the inherent HA properties of Zappa-deployed applications. Consider adding cross-region deployment support for critical workloads. |
| **Evidence** | `zappa/core.py` (deploy_lambda_alb SubnetIds requirement), AWS Lambda inherent multi-AZ behavior |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No Terraform, CDK, or CloudFormation files exist in the repository for Zappa's own infrastructure. Zappa generates CloudFormation templates programmatically using troposphere (`cf_template` in `core.py`, `create_stack_template`, `update_stack`) for user applications, but this is runtime code generation, not IaC for the tool itself. The tool's CI/CD, PyPI publishing, and operational resources are configured manually. |
| **Gap** | 0% IaC coverage for the tool's own infrastructure. All infrastructure (GitHub Actions configuration, PyPI project settings, operational resources) is manually created. The programmatic CloudFormation generation is application code, not infrastructure definition. |
| **Recommendation** | Define CI/CD infrastructure as code using CloudFormation or CDK. Consider codifying GitHub Actions environment secrets and repository settings using Terraform GitHub provider or GitHub's REST API via IaC. |
| **Evidence** | No `.tf`, `.cfn.yaml`, `cdk.json`, or standalone CloudFormation template files found. `zappa/core.py` (troposphere template generation is application code). |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GitHub Actions CI pipeline (`.github/workflows/ci.yml`) runs on every push/PR to master with: Python test matrix (3.9–3.14), linting (flake8, black, isort), test execution (pytest), and coverage reporting (Coveralls). CD pipeline (`.github/workflows/cd.yml`) supports manual-trigger releases with build verification, git tagging, GitHub Release creation, and PyPI publishing (trusted publisher). Maintenance pipeline (`.github/workflows/maintenance.yml`) automates stale issue/PR cleanup. |
| **Gap** | CD is manual-trigger only (`workflow_dispatch`) — not automatic on merge. No automated security scanning gate. No automated rollback on failed deployments (PyPI is immutable anyway). No integration test stage that tests against real AWS services. |
| **Recommendation** | Add dependency vulnerability scanning to CI (pip-audit or safety). Consider automating the release process with semantic-release or similar. Add a pre-release integration test stage that deploys to a test AWS account. |
| **Evidence** | `.github/workflows/ci.yml`, `.github/workflows/cd.yml`, `.github/workflows/maintenance.yml`, `Makefile` (test targets) |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Zappa is written entirely in Python, which has first-class AWS SDK coverage (boto3), broad cloud-native tooling (Lambda, CDK, SAM), and mature framework ecosystems (Django, Flask, FastAPI support). Supports Python 3.9–3.14 (defined in `__init__.py` SUPPORTED_VERSIONS). |
| **Gap** | None. Python is the optimal language choice for an AWS serverless deployment framework. |
| **Recommendation** | No action needed. Continue supporting latest Python versions as AWS Lambda adds them. |
| **Evidence** | `zappa/__init__.py` (SUPPORTED_VERSIONS), `setup.py` (python_requires=">=3.9"), `Pipfile` (boto3 dependency), `.github/workflows/ci.yml` (test matrix 3.9–3.14) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Zappa is a single deployable package with well-defined module boundaries: `core.py` (AWS service orchestration), `cli.py` (CLI interface), `handler.py` (Lambda runtime handler), `wsgi.py`/`asgi.py` (request translation), `middleware.py` (WSGI middleware), `asynchronous.py` (async task dispatch), `utilities.py` (shared utilities), `websocket.py` (WebSocket support), `ext/django_zappa.py` (Django integration). Each module has a distinct responsibility. The `Zappa` class in `core.py` is the central coordinator but modules can be used independently. |
| **Gap** | Single package deployment — no independent deployability. The `Zappa` class accumulates responsibility for 15+ AWS service interactions. `cli.py` at 3,656 lines is a monolithic command handler. Some cross-module coupling exists through shared imports and the central `Zappa` class. |
| **Recommendation** | This is appropriate for a library/framework. No decomposition needed. Consider extracting `cli.py` into smaller command modules for maintainability. The modular monolith pattern with clear module boundaries is the correct architecture for a deployment tool. |
| **Evidence** | `zappa/` directory structure, `setup.py` (packages=["zappa"]), `zappa/core.py` (Zappa class), `zappa/cli.py` (3,656 lines) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | **Orchestrator archetype calibration applied.** Zappa's core deployment workflow is primarily synchronous — sequential boto3 calls across Lambda, API Gateway, IAM, S3, CloudFormation, Route53, etc. The async task system (SNS/Lambda dispatch via `asynchronous.py`) is a feature for user applications. Event source integrations (SQS, DynamoDB Streams, Kinesis, SNS, CloudWatch Events) provide async capabilities for deployed apps. However, the orchestration fan-out itself remains synchronous. |
| **Gap** | For an orchestrator archetype, primarily synchronous fan-out with limited async represents a gap. Deployment operations sequentially call 10+ services, creating timeout risk and cascading failure potential. |
| **Recommendation** | Introduce async patterns for independent deployment steps. For example, after Lambda function creation, Route53 DNS updates and CloudWatch Events scheduling can happen concurrently. Use Python `asyncio` with `aiobotocore` or EventBridge (preferred) for event-driven step coordination. |
| **Evidence** | `zappa/core.py` (synchronous boto3 calls throughout), `zappa/asynchronous.py` (LambdaAsyncResponse, SnsAsyncResponse — for user apps), `zappa/utilities.py` (event source classes) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | **Orchestrator archetype calibration applied.** CLI deployment operations can take several minutes (package creation, S3 upload, CloudFormation stack creation/update with wait). The Lambda client is configured with a 900-second read timeout (`long_config` in `core.py.__init__`). CloudFormation stack operations use waiters (`waiter.wait`) with progress bars (`tqdm`). Lambda function activation uses waiters (`wait_until_lambda_function_is_active`). |
| **Gap** | Long-running operations block the CLI process synchronously. CloudFormation stack updates can take minutes, and the CLI waits for completion with polling. No async job pattern with status callbacks — the user must keep the terminal open. Rollback downloads the Lambda function code synchronously via HTTP before re-uploading. |
| **Recommendation** | Consider adding a `--async` flag for long-running commands that returns immediately with a job ID and allows `zappa status <job-id>` to check completion. For CloudFormation operations, the stack status is already pollable — expose this as a detachable operation. |
| **Evidence** | `zappa/core.py` (long_config 900s timeout, update_stack waiter loop, wait_until_lambda_function_is_active, rollback_lambda_function_version) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Zappa uses semantic versioning for the PyPI package (`__version__ = "0.62.1"` in `__init__.py`). API Gateway versions are supported (v1 REST API and v2 HTTP API via `apigateway_version` parameter). The CD pipeline creates git tags for versions. Lambda function versioning is used for rollback capability. Settings file format has evolved across versions with backward compatibility. |
| **Gap** | No formal API versioning strategy for the Python library's public API (functions, classes, settings schema). Breaking changes in the settings format are not version-gated. No deprecation policy documented. |
| **Recommendation** | Document a deprecation policy for settings keys and public API methods. Consider adding settings schema versioning to detect and migrate old configuration formats automatically. |
| **Evidence** | `zappa/__init__.py` (__version__), `.github/workflows/cd.yml` (tag_version), `zappa/core.py` (apigateway_version parameter, rollback_lambda_function_version) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Zappa uses boto3's built-in endpoint resolution for all AWS service calls — no hard-coded endpoints. Custom endpoint URLs are supported via the `endpoint_urls` parameter in `Zappa.__init__()`, enabling testing against LocalStack or other non-AWS endpoints. The `configure_boto_session_method_kwargs` method dynamically applies endpoint overrides. AWS region-based service discovery is built into the boto3 session. |
| **Gap** | No formal service registry or catalog. Service endpoint configuration relies on boto3's internal resolution plus optional overrides. For deployed applications, service-to-service discovery must be configured externally. |
| **Recommendation** | Consider adding support for AWS Cloud Map or VPC Lattice integration for Zappa-deployed applications that need service discovery. Document patterns for service-to-service communication between Zappa-deployed Lambda functions. |
| **Evidence** | `zappa/core.py` (endpoint_urls parameter, configure_boto_session_method_kwargs, boto_client wrapper) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Zappa uses Amazon S3 (managed object storage) for deployment package storage. `upload_to_s3()` uploads Lambda zip packages to S3. `copy_on_s3()` supports copying within buckets. `remove_from_s3()` cleans up deployment artifacts. S3 is also used for remote environment configuration (`remote_env` setting loads JSON from S3). The `load_remote_project_archive` method downloads and extracts project archives from S3 for slim handler deployments. |
| **Gap** | No parsing pipeline for stored artifacts. Deployment packages are opaque zip/tarball files without indexing or search capability. No Textract or document processing integration. |
| **Recommendation** | No action needed for the deployment use case. S3 is the correct storage for deployment artifacts. If Zappa were to add a deployment audit/analysis feature, consider indexing deployment metadata. |
| **Evidence** | `zappa/core.py` (upload_to_s3, copy_on_s3, remove_from_s3), `zappa/handler.py` (load_remote_project_archive, load_remote_settings) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All AWS service clients are centralized in the `Zappa.__init__()` method with `boto_client()` and `boto_resource()` wrapper methods that apply consistent configuration (endpoint URLs, region). Clients initialized: `s3_client`, `lambda_client`, `elbv2_client`, `events_client`, `apigateway_client`, `acm_client`, `logs_client`, `iam_client`, `cloudwatch`, `route53`, `sns_client`, `cf_client`, `dynamodb_client`, `cognito_client`, `sts_client`, `efs_client`. The async module (`asynchronous.py`) initializes its own clients at module level for Lambda warm-start optimization but uses the same boto3 pattern. |
| **Gap** | None. The centralized client initialization in `Zappa.__init__()` provides a single point of control for all data access. |
| **Recommendation** | No action needed. The centralized boto3 client pattern is well-implemented. |
| **Evidence** | `zappa/core.py` (Zappa.__init__ client initialization, boto_client, boto_resource, configure_boto_session_method_kwargs) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Zappa uses DynamoDB (fully managed, serverless — no engine version to pin) for async response storage. S3 (fully managed, versionless) for deployment storage. No relational database engines are used. No database engine version pinning is needed because all data stores are fully managed serverless services with no customer-managed versions. |
| **Gap** | None. DynamoDB and S3 are versionless managed services with no EOL concerns. |
| **Recommendation** | No action needed. |
| **Evidence** | `zappa/core.py` (create_async_dynamodb_table — DynamoDB), `zappa/core.py` (upload_to_s3 — S3) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs. All business logic resides in Python application code. The DynamoDB async response table uses simple key-value operations (`put_item`, `update_item`, `get_item`) with no server-side logic. No SQL files, no ORM configurations, no database migration scripts. |
| **Gap** | None. |
| **Recommendation** | No action needed. |
| **Evidence** | `zappa/asynchronous.py` (DynamoDB operations — all application-layer logic), no `.sql` files in repository |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Zappa configures CloudWatch logging for API Gateway (`cloudwatch_log_level` setting with OFF/ERROR/INFO levels in `deploy_api_gateway`). Lambda functions automatically log to CloudWatch Logs. The `fetch_logs` method in `core.py` enables log retrieval. CloudWatch data trace logging is configurable (`cloudwatch_data_trace`). |
| **Gap** | No CloudTrail configuration in the codebase. No immutable log storage (S3 Object Lock). CloudWatch log retention periods are not configured — defaults to indefinite retention. API Gateway logging is opt-in and defaults to OFF. |
| **Recommendation** | Add CloudTrail configuration guidance in documentation. Add CloudWatch log retention period configuration to `zappa_settings`. Consider defaulting API Gateway logging to ERROR instead of OFF. |
| **Evidence** | `zappa/core.py` (deploy_api_gateway cloudwatch_log_level, cloudwatch_data_trace, fetch_logs, remove_log_group) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | KMS key ARN support exists (`aws_kms_key_arn` parameter in `create_lambda_function` and `update_lambda_configuration`). EFS file systems are created with `Encrypted=True`. Lambda environment variables can be encrypted with the specified KMS key. However, S3 bucket creation (`create_bucket` in `upload_to_s3`) does not specify server-side encryption — relies on S3 default encryption (if configured at the account level). |
| **Gap** | S3 buckets created by Zappa do not explicitly enable server-side encryption. While AWS now defaults S3 to SSE-S3, explicit configuration would be more robust. No documented key rotation policy. |
| **Recommendation** | Add explicit S3 server-side encryption (SSE-S3 or SSE-KMS) when creating deployment buckets. Add KMS key rotation documentation. Consider making `aws_kms_key_arn` apply to S3 buckets as well as Lambda functions. |
| **Evidence** | `zappa/core.py` (create_lambda_function aws_kms_key_arn, create_efs Encrypted=True, upload_to_s3 — no encryption config) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Zappa provides comprehensive API authentication options: TOKEN authorizers (custom Lambda authorizers), COGNITO_USER_POOLS authorizers, IAM authorization, API key requirements (`api_key_required`), and Function URL authorization (NONE or AWS_IAM). The `create_authorizer` method supports identity validation expressions and configurable token headers. API Gateway v2 supports AWS_IAM authorization. |
| **Gap** | OAuth2/JWT is not natively supported — requires a custom Lambda authorizer. Function URLs with `authorizer: NONE` add public access permissions (`FunctionURLAllowPublicAccess`). No built-in request validation. |
| **Recommendation** | Add native JWT authorizer support for API Gateway v2 (HTTP API supports JWT authorizers natively). Document security implications of Function URL public access. Consider adding request validation configuration. |
| **Evidence** | `zappa/core.py` (create_authorizer — TOKEN, COGNITO_USER_POOLS; create_api_gateway_v2_routes — AWS_IAM; deploy_lambda_function_url; FUNCTION_URL_PUBLIC_PERMISSION_RULES) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Zappa integrates with Amazon Cognito for user pool management (`update_cognito` method). Cognito triggers can be mapped to Lambda functions via `COGNITO_TRIGGER_MAPPING`. IAM-based authorization is supported across API Gateway v1, v2, and Function URLs. The assume policy allows `apigateway.amazonaws.com`, `lambda.amazonaws.com`, and `events.amazonaws.com` to assume roles. |
| **Gap** | No OIDC/SAML federation support. No SSO configuration. Cognito integration is basic — limited to user pool triggers and API Gateway authorizer. No centralized identity provider configuration in zappa_settings. |
| **Recommendation** | Add OIDC configuration support for API Gateway v2 JWT authorizers. Document Cognito user pool integration patterns for common use cases. |
| **Evidence** | `zappa/core.py` (update_cognito, create_authorizer COGNITO_USER_POOLS), `zappa/policies/assume_policy.json` |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Zappa provides `remote_env` setting that loads environment variables from a JSON file stored in S3 (`load_remote_settings` in `handler.py`). Lambda environment variables are configured via `aws_environment_variables`. No AWS Secrets Manager integration exists. No HashiCorp Vault integration. |
| **Gap** | `remote_env` stores secrets as plaintext JSON in S3 — no encryption enforcement, no rotation, no audit trail. Lambda environment variables are visible in the AWS Console. No Secrets Manager integration for automated rotation. Production credentials and API keys must be stored as environment variables or S3 files with no lifecycle management. |
| **Recommendation** | Add AWS Secrets Manager integration as a secrets source option in `zappa_settings`. This would enable automated rotation, encrypted storage, and audit trails. Consider deprecating `remote_env` in favor of Secrets Manager for sensitive configuration. |
| **Evidence** | `zappa/handler.py` (load_remote_settings — S3 JSON), `zappa/core.py` (aws_environment_variables in create_lambda_function) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Lambda runtime patching is managed by AWS — no customer action required. Zappa supports all current Python runtimes (3.9–3.14). Docker image-based Lambda deployments are supported (`docker_image_uri`), which allows customers to use hardened base images. The `ZAPPA_RUNNING_IN_DOCKER` flag enables Docker-based workflows. |
| **Gap** | No vulnerability scanning of the Zappa package itself or its dependencies. No guidance on using hardened Docker base images for container-based Lambda. No SSM Patch Manager integration (not applicable for Lambda). The `attach_policy.json` grants overly broad permissions (e.g., `s3:*`, `sns:*`, `sqs:*`, `dynamodb:*`, `kinesis:*`, `route53:*`). |
| **Recommendation** | Add pip-audit or safety to CI pipeline for dependency vulnerability scanning. Narrow the default `attach_policy.json` permissions to least-privilege. Document hardened Docker base image recommendations for container-based Lambda deployments. |
| **Evidence** | `zappa/__init__.py` (SUPPORTED_VERSIONS), `zappa/policies/attach_policy.json` (overly broad permissions), `zappa/core.py` (docker_image_uri support) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | CI pipeline includes linting only: flake8 (code quality), black (formatting), isort (import sorting), mypy (type checking via pre-commit). No SAST tools (no SonarQube, Semgrep, Bandit, CodeGuru). No dependency vulnerability scanning (no Dependabot, no pip-audit, no safety, no Snyk). No container scanning. Pre-commit hooks configured but focused on code style, not security. |
| **Gap** | No security scanning tools configured. Pipeline has no security validation step. Vulnerabilities in boto3, requests, troposphere, or other dependencies could reach PyPI releases undetected. No Dependabot configuration for automated dependency updates. |
| **Recommendation** | 1. Add Dependabot configuration (`.github/dependabot.yml`) for automated dependency updates. 2. Add `pip-audit` or `safety` to the CI pipeline for dependency vulnerability scanning. 3. Add Bandit or Semgrep for Python SAST scanning. 4. Add a security gate that blocks releases with critical findings. |
| **Evidence** | `.github/workflows/ci.yml` (flake8, black, isort — no security tools), `.pre-commit-config.yaml` (style hooks only), no `.github/dependabot.yml`, no `.snyk` |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | X-Ray tracing support exists: `xray_tracing` parameter in `Zappa.__init__()`, `TracingConfig: {"Mode": "Active"}` in `create_lambda_function` and `update_lambda_configuration`. The `attach_policy.json` includes X-Ray permissions (`xray:PutTraceSegments`, `xray:PutTelemetryRecords`). Common Log Format logging with response time is implemented in `handler.py` and `utilities.py`. |
| **Gap** | X-Ray SDK is not included as a dependency in `Pipfile` — users must add it themselves. No cross-service trace propagation configuration. No `traceparent` or `X-Amzn-Trace-Id` header forwarding between Zappa-deployed services. Basic tracing on individual functions but no end-to-end correlation. |
| **Recommendation** | Add X-Ray SDK as an optional dependency or document the installation requirement. Add trace header propagation for inter-service calls. Consider OpenTelemetry SDK support as an alternative to X-Ray. |
| **Evidence** | `zappa/core.py` (xray_tracing, TracingConfig), `zappa/policies/attach_policy.json` (X-Ray permissions), `Pipfile` (no X-Ray SDK) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found in the repository. No error budget tracking. No formal definition of acceptable service levels for Zappa-deployed applications or the tool itself. |
| **Gap** | No SLOs for deployment success rate, Lambda cold-start latency, API Gateway response time, or any other operational metric. No monitoring targets defined. |
| **Recommendation** | Define SLOs for Zappa-deployed applications as configurable settings (e.g., target p99 latency, error rate threshold). Add CloudWatch alarm templates that users can deploy alongside their applications. |
| **Evidence** | No SLO definition files, no CloudWatch alarm configurations, no error budget references in codebase |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | CloudWatch metrics are configurable for API Gateway (`cloudwatch_metrics_enabled` in `deploy_api_gateway` and `update_stage_config`). Lambda execution metrics are automatically collected by AWS. Common Log Format logging captures request method, path, status code, response size, and response time. |
| **Gap** | No custom business metrics published. Only infrastructure metrics (API Gateway latency, Lambda duration) are available. No `cloudwatch.put_metric_data` calls for business outcomes. No custom dashboards. |
| **Recommendation** | Add a `custom_metrics` configuration option that allows users to define CloudWatch custom metrics from within their application code. Provide helper functions for publishing business metrics from Lambda handlers. |
| **Evidence** | `zappa/core.py` (deploy_api_gateway cloudwatch_metrics_enabled, update_stage_config), `zappa/utilities.py` (ApacheNCSAFormatters) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configuration found. No CloudWatch alarms defined. No PagerDuty/OpsGenie integration. No composite alarms. |
| **Gap** | No alerting of any kind. Zappa-deployed applications have no built-in monitoring or alerting. Users must configure all alerting externally. |
| **Recommendation** | Add configurable CloudWatch alarms for common failure scenarios (Lambda errors, API Gateway 5xx rates, throttling). Consider CloudWatch anomaly detection for deployed Lambda functions. Add alarm configuration to `zappa_settings`. |
| **Evidence** | No CloudWatch alarm resources in codebase. No alerting configuration in any file. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Lambda versioning is supported — `create_lambda_function` and `update_lambda_function` use `Publish=True`. Rollback to previous versions is available via `rollback_lambda_function_version`. ALB Lambda alias (`ALB_LAMBDA_ALIAS = "current-alb-version"`) enables zero-downtime updates for ALB-backed deployments. Version cleanup is supported via `num_revisions` parameter. |
| **Gap** | No canary or blue/green deployment strategy. Lambda updates are atomic (direct-to-production). No traffic shifting between versions. No CodeDeploy integration. ALB alias updates are immediate (no gradual rollout). |
| **Recommendation** | Add Lambda weighted alias support for canary deployments. Integrate with AWS CodeDeploy for Lambda deployment with automatic rollback based on CloudWatch alarms. This aligns with the "Move to Modern DevOps" pathway recommendation. |
| **Evidence** | `zappa/core.py` (rollback_lambda_function_version, ALB_LAMBDA_ALIAS, update_lambda_function Publish=True) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive test suite: `tests/test_core.py`, `tests/test_handler.py`, `tests/test_async.py`, `tests/test_middleware.py`, `tests/test_utilities.py`, `tests/test_asgi.py`, `tests/test_websocket.py`, `tests/test_docs.py`. Tests use placebo for AWS API call mocking. CI pipeline runs full test suite across Python 3.9–3.14 with coverage reporting. |
| **Gap** | Tests use placebo (recorded AWS responses) rather than live AWS integration tests. No contract tests. No end-to-end deployment test that verifies a complete deploy/invoke/undeploy cycle. |
| **Recommendation** | Add an integration test stage that deploys a sample application to a test AWS account, verifies it responds correctly, and undeployments. This could run on a schedule or before releases. |
| **Evidence** | `tests/` directory (8+ test modules), `tests/placebo/` (recorded AWS responses), `.github/workflows/ci.yml` (pytest execution), `Makefile` (test targets) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks found. No incident response automation. No Systems Manager Automation documents. No self-healing patterns. The `maintenance.yml` workflow automates stale issue cleanup but this is repository maintenance, not incident response. |
| **Gap** | No incident response capability. Failed deployments must be investigated and resolved manually. No automated remediation for common failure modes (stuck CloudFormation stacks, orphaned Lambda functions, etc.). |
| **Recommendation** | Create runbooks for common failure scenarios: stuck CloudFormation stack (manual delete), orphaned resources after failed undeploy, Lambda function size limit exceeded. Consider adding a `zappa doctor` command that diagnoses and fixes common issues. |
| **Evidence** | No runbook files found. No SSM Automation documents. `.github/workflows/maintenance.yml` (repository maintenance only). |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CODEOWNERS file. No per-service dashboards. No named alarm owners. No SLO definitions with team attribution. No observability asset ownership structure. |
| **Gap** | No observability ownership of any kind. Monitoring responsibility for Zappa-deployed applications is undefined. |
| **Recommendation** | Add CODEOWNERS file for the repository. For Zappa-deployed applications, add configurable CloudWatch dashboard templates that include team/owner tags. |
| **Evidence** | No CODEOWNERS file. No dashboard definitions. No observability ownership references. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Zappa supports resource tagging via `self.tags` (set in `Zappa.__init__()`). Tags are applied to: Lambda functions (`tag_resource`), S3 buckets (`put_bucket_tagging`), CloudFormation stacks (`ZappaProject` tag), EFS file systems (`CreatedBy: Zappa`), and ALB resources. The `tags` configuration in `zappa_settings.json` allows users to define custom key-value tags. |
| **Gap** | No tag enforcement mechanism. No required tags defined. No AWS Config rules or Tag Policies integration. Tags are user-configurable but not validated or enforced. Some resources (API Gateway, CloudWatch logs) may not receive tags. |
| **Recommendation** | Add required tag validation (e.g., require `Environment`, `Owner`, `CostCenter` tags). Consider adding tag propagation to all resources created by Zappa, including API Gateway stages and CloudWatch log groups. |
| **Evidence** | `zappa/core.py` (self.tags, tag_resource, put_bucket_tagging, ZappaProject tag, EFS tags), `example/zappa_settings.json` |

## Learning Materials

### Move to Modern DevOps
- [Move to Modern DevOps — AWS SkillBuilder Learning Plan](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)
- [Lambda Deployment with CodeDeploy](https://docs.aws.amazon.com/lambda/latest/dg/lambda-rolling-deployments.html)

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `zappa/__init__.py` | APP-Q1, APP-Q5, SEC-Q6 | Python version support, semantic versioning |
| `zappa/core.py` | INF-Q1–Q11, APP-Q2–Q4, APP-Q6, DATA-Q1–Q3, SEC-Q1–Q6, OPS-Q1, OPS-Q3, OPS-Q5, OPS-Q9 | Central AWS service orchestration, Lambda/API Gateway/S3 management |
| `zappa/cli.py` | INF-Q3, APP-Q2 | CLI command handling, deployment orchestration (3,656 lines) |
| `zappa/handler.py` | INF-Q1, SEC-Q5, OPS-Q1, OPS-Q3 | Lambda runtime handler, WSGI/ASGI request processing |
| `zappa/asynchronous.py` | INF-Q2, INF-Q4, DATA-Q4 | SNS/Lambda async task dispatch, DynamoDB response storage |
| `zappa/utilities.py` | INF-Q4, OPS-Q3 | Event source classes (SQS, DynamoDB, Kinesis, S3, SNS), logging formatters |
| `zappa/wsgi.py` | APP-Q2 | WSGI request translation |
| `zappa/asgi.py` | APP-Q2 | ASGI request translation |
| `zappa/middleware.py` | APP-Q2 | WSGI middleware |
| `zappa/websocket.py` | APP-Q2 | WebSocket support |
| `zappa/ext/django_zappa.py` | APP-Q2 | Django integration |
| `zappa/policies/assume_policy.json` | SEC-Q4 | IAM assume role policy (API Gateway, Lambda, Events) |
| `zappa/policies/attach_policy.json` | INF-Q5, SEC-Q6, OPS-Q1 | IAM permissions (overly broad: s3:*, sns:*, etc.) |
| `.github/workflows/ci.yml` | INF-Q11, SEC-Q7, OPS-Q6 | CI pipeline: Python test matrix, linting, coverage |
| `.github/workflows/cd.yml` | INF-Q11, APP-Q5 | CD pipeline: manual PyPI release |
| `.github/workflows/maintenance.yml` | OPS-Q7 | Repository maintenance: stale issue cleanup |
| `.pre-commit-config.yaml` | SEC-Q7 | Pre-commit hooks: style enforcement only |
| `Pipfile` | APP-Q1, OPS-Q1 | Dependencies: boto3, troposphere, requests (no X-Ray SDK) |
| `setup.py` | APP-Q1, INF-Q1 | Package configuration, console_scripts entry point |
| `Makefile` | OPS-Q6 | Test targets, lint targets |
| `tests/` | OPS-Q6 | Comprehensive test suite (8+ modules) |
| `tests/placebo/` | OPS-Q6 | Recorded AWS API responses for testing |
| `example/zappa_settings.json` | OPS-Q9 | Example configuration with tags |
