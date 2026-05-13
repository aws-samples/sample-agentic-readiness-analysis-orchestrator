# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | zappa--Zappa |
| **Date** | 2025-01-08 |
| **Repo Type** | application |
| **Service Archetype** | stateless-utility (auto-detected) |
| **Priority** | P2 |
| **Tags** | python, serverless |
| **Context** | Python framework for deploying WSGI apps on AWS Lambda. |
| **Surface Flags** | has_persistent_data_store=false, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=false, has_multi_instance_deployment=false |
| **Overall Score** | 1.86 / 4.0 |

**Archetype Justification**: This is a CLI deployment tool (published to PyPI) with no runtime service component, no database connections, no persistent state, and no API surface of its own. All operations are stateless command-line invocations that package and deploy user applications to AWS Lambda. Classified as stateless-utility.

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | 1.17 / 4.0 | ❌ Not Ready | Critical |
| Application Architecture (APP) | 2.25 / 4.0 | 🟠 Needs Work | Needs Work |
| Data Platform Modernization (DATA) | 2.50 / 4.0 | 🟡 Partial | Needs Work |
| Security Baseline (SEC) | 1.60 / 4.0 | 🟠 Needs Work | Critical |
| Operations & Observability (OPS) | 1.80 / 4.0 | 🟠 Needs Work | Needs Work |

**Scoring Notes:**
- INF: (1+1+1+1+1+2) / 6 evaluated questions = 7/6 = 1.17 (INF-Q2, INF-Q3, INF-Q4, INF-Q8, INF-Q9 are Not Evaluated via surface gating or archetype-N/A)
- APP: (4+1+2+2) / 4 evaluated questions = 9/4 = 2.25 (APP-Q3, APP-Q4 are Not Evaluated archetype-N/A)
- DATA: (3+2) / 2 evaluated questions = 5/2 = 2.50 (DATA-Q3, DATA-Q4 are N/A — no persistent data store)
- SEC: (1+2+1+2+2) / 5 evaluated questions = 8/5 = 1.60 (SEC-Q2 is Not Evaluated via surface gating, SEC-Q3 is N/A — no API surface)
- OPS: (1+1+2+2+3) / 5 evaluated questions = 9/5 = 1.80 (OPS-Q2, OPS-Q3, OPS-Q4, OPS-Q8 are Not Evaluated via surface gating)
- Overall: (1.17 + 2.25 + 2.50 + 1.60 + 1.80) / 5 = 9.32/5 = 1.86

**Classification Tier: 🟠 Remediation Required**

This repo has 7 High findings, 12 Medium findings, 2 Low findings. The matched rule is: "2-11 High → Remediation Required." MOD classification differs from ARA: ARA's "1 High" is an agent-deployment gate; MOD's "1 High" maps to Pilot-Ready because a single modernization gap is typically non-blocking. MOD requires 2+ High findings to reach Remediation Required, reflecting cumulative maturity debt.

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q1: Managed Compute | 1 | No infrastructure definitions — tool generates CloudFormation for others but has no deployed compute of its own | Cannot demonstrate managed compute maturity; users must provision their own infrastructure |
| 2 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC files in the repository | No reproducible infrastructure; all deployment relies on the tool itself generating CF dynamically |
| 3 | INF-Q11: CI/CD Automation | 2 | CI exists but CD is manual (workflow_dispatch); no automated deployment pipeline | Release process requires manual intervention; no continuous delivery |
| 4 | SEC-Q1: Audit Logging | 1 | No CloudTrail or audit logging configuration | No audit trail for operations performed by the tool |
| 5 | SEC-Q5: Secrets Management | 1 | IAM policies use wildcard permissions; no secrets manager integration | Overly permissive default policies; environment variables used for configuration without encrypted secrets management |

## Quick Agent Wins

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists — comprehensive README.md (full API reference, advanced settings, 150+ configuration options), CONTRIBUTING.md, docs/ directory, and CHANGELOG.md
- **What it enables:** A knowledge agent that indexes Zappa's documentation corpus to answer developer questions about configuration options, deployment troubleshooting, and AWS service integration without requiring developers to read the full documentation
- **Additional steps:** Generate structured documentation index; consider converting README sections into smaller retrievable chunks
- **Effort:** Low

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 2) — GitHub Actions with CI workflow on push/PR and CD workflow for PyPI publishing
- **What it enables:** An agent that triggers builds, checks test results across the Python version matrix, and manages the release process (currently manual workflow_dispatch)
- **Additional steps:** Add webhook or API trigger capability to the CD workflow for programmatic release automation
- **Effort:** Medium

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 1 (monolith) but this is a CLI tool — decomposition is not architecturally warranted for a single-purpose deployment utility |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 1 but contextual guard prevents trigger: this is a CLI tool with no deployed compute workload — it generates Lambda deployments for others |
| 3 | Move to Open Source | Not Triggered | — | — | No commercial database engines detected; project is already fully open-source (MIT license) |
| 4 | Move to Managed Databases | Not Triggered | — | — | has_persistent_data_store=false; INF-Q2 is Not Evaluated — no database exists to migrate |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads exist; service_archetype is stateless-utility; no streaming/ETL artifacts found |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (no IaC), INF-Q11 = 2 (partial CI/CD), OPS-Q5 = 1 (no deployment strategy), OPS-Q6 = 2 (tests exist but limited integration coverage) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context |

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:**
- **IaC Coverage (INF-Q10 = 1):** No Terraform, CDK, CloudFormation, or Helm files in the repository. The tool itself generates CloudFormation dynamically via `troposphere`, but its own infrastructure/release process has no IaC definition.
- **CI/CD Automation (INF-Q11 = 2):** GitHub Actions CI workflow runs on push/PR with linting (flake8, black, isort) and testing (pytest with coverage across Python 3.9-3.14). CD workflow exists but requires manual `workflow_dispatch` trigger with version input — not continuous delivery.
- **Deployment Strategy (OPS-Q5 = 1):** PyPI publishing is direct-to-production with no canary or staged rollout. No version testing in staging before public release.
- **Integration Testing (OPS-Q6 = 2):** Unit tests with placebo (AWS API mocking) exist and run in CI. No integration tests against live AWS services.

**Recommendations:**
- Adopt automated semantic versioning and release-on-merge to eliminate manual CD triggers
- Add integration test stage using real AWS sandbox account (or LocalStack) in CI pipeline
- Consider adding a staging PyPI (TestPyPI) publish step before production release
- Define release quality gates: all Python versions pass, coverage threshold met, no security advisories

**Representative AWS Services:** CodeBuild, CodePipeline, CloudFormation (for release infrastructure IaC)

**Learning Materials:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute infrastructure is defined in the repository. The project is a CLI deployment tool that packages and deploys *other* applications to AWS Lambda. It does not itself run as a deployed service — it is installed via pip and executed locally or in CI/CD pipelines. No Terraform, CloudFormation, CDK, or other IaC files define compute resources. |
| **Gap** | No managed compute workloads. The tool has no deployed infrastructure of its own. |
| **Recommendation** | If operational hosting is desired (e.g., a Zappa-as-a-Service offering), consider deploying as a containerized service on EKS/ECS. For current CLI usage, this gap is inherent to the tool's nature. Preferences favor EKS for container orchestration. |
| **Evidence** | Absence of any IaC files in repository; `setup.py` defines console_scripts entry points for CLI usage only |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy a database. INF-Q2 does not apply. The tool interacts with DynamoDB in user deployments (for async task responses) but does not maintain its own persistent data store. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database connection strings, no ORM imports, no database resources in IaC. DynamoDB references in `zappa/core.py` are for deploying user resources, not the tool's own state. |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Workflow orchestration is not applicable by design — no multi-step workflows exist for a stateless CLI deployment tool. Each CLI command (deploy, update, rollback) is a single atomic operation. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `zappa/cli.py` — each CLI command is an atomic operation (deploy, update, undeploy, rollback); no multi-step coordination or state machines. |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Synchronous CLI execution is the correct design — no messaging or streaming infrastructure is needed. The tool manages SNS/SQS/Kinesis resources for user deployments but does not consume or produce messages itself. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `zappa/core.py` manages AWS messaging resources (SNS topics, SQS queues) on behalf of deployed applications; `zappa/asynchronous.py` implements async task invocation for deployed Lambda functions, not for the CLI tool itself. |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, security group, or network segmentation configuration exists for the tool itself. The tool generates VPC configuration for user deployments (`vpc_config` in settings) but has no network security posture of its own. The default `attach_policy.json` uses wildcard resource ARNs (`*`) for EC2 network interface operations. |
| **Gap** | Default IAM policies use overly permissive wildcard resources. No network security configuration for the tool's own operations. |
| **Recommendation** | Tighten default IAM policies in `zappa/policies/attach_policy.json` to use least-privilege resource patterns. Document network security best practices for users deploying with Zappa (VPC deployment, private subnets). |
| **Evidence** | `zappa/policies/attach_policy.json` — wildcard `"Resource": "*"` on EC2, Route53, Lambda, X-Ray; `test_settings.json` shows `vpc_config` as optional user configuration |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API entry point exists for the tool itself. It is a CLI application with no HTTP/REST surface. The tool creates API Gateway resources for user deployments but does not expose an API of its own. |
| **Gap** | No API entry point — the tool is CLI-only with no service endpoint. |
| **Recommendation** | If a service-based deployment API is desired, consider exposing Zappa operations behind API Gateway with authentication and throttling. For current CLI usage, this gap is inherent to the tool's design. |
| **Evidence** | `setup.py` entry_points define CLI commands only: `zappa=zappa.cli:handle`, `z=zappa.cli:handle` |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. The tool is a CLI application — it does not run as a persistent service requiring scaling. It configures Lambda concurrency for user deployments (`lambda_concurrency` setting) but has no scaling needs of its own. |
| **Gap** | No auto-scaling — not applicable for a CLI tool, but scores 1 as there is no deployed workload to scale. |
| **Recommendation** | Not applicable for current CLI architecture. If converted to a service, implement auto-scaling based on deployment request volume. |
| **Evidence** | `test_settings.json` shows `lambda_concurrency` as user-facing setting; no ASG or auto-scaling resources in repository |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no persistent state to back up. INF-Q8 does not apply. The tool is stateless — all state lives in the AWS account being deployed to (S3 deployment packages, CloudFormation stacks, Lambda functions). |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database, no S3 bucket ownership, no persistent state in the tool itself |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload requiring HA evaluation. INF-Q9 does not apply. The tool runs as a local CLI or in CI/CD — it is not a persistent service requiring multi-AZ deployment. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No deployed workload; CLI execution model; no IaC defining compute resources |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC files exist in the repository. No Terraform, CloudFormation templates, CDK stacks, Helm charts, or Kustomize configurations are present. The tool dynamically generates CloudFormation templates for user deployments via the `troposphere` library in `zappa/core.py`, but its own build/release infrastructure has no IaC definition. |
| **Gap** | 0% IaC coverage — all build and release infrastructure (GitHub Actions, PyPI publishing) is configured manually or via workflow YAML only. No reproducible infrastructure definition. |
| **Recommendation** | Define release infrastructure as IaC: GitHub repository settings, OIDC provider for PyPI, branch protection rules. Consider CDK or Terraform for managing the project's own AWS resources (if any). |
| **Evidence** | No `.tf`, `.cfn.yaml`, `cdk.json`, `Chart.yaml`, or `kustomization.yaml` files found. `zappa/core.py` uses troposphere for dynamic CF generation for user deployments only. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | CI is automated via GitHub Actions (`.github/workflows/ci.yml`) — runs on push/PR to master with multi-version Python testing (3.9-3.14), linting (flake8, black, isort), and coverage reporting (Coveralls). CD exists (`.github/workflows/cd.yml`) but requires manual `workflow_dispatch` trigger with explicit version input and dry-run option. Publishing to PyPI uses OIDC trusted publisher. |
| **Gap** | CD is semi-manual — requires human to trigger workflow_dispatch with version string. No automated release pipeline, no automated versioning, no continuous delivery. Build is automated but deployment is manual. |
| **Recommendation** | Implement automated semantic release (e.g., `semantic-release` or tag-based triggers). Add TestPyPI staging publish before production. Automate version bumping based on commit conventions. |
| **Evidence** | `.github/workflows/ci.yml` — full CI automation; `.github/workflows/cd.yml` — manual trigger with `workflow_dispatch` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Python 3.9-3.14 with modern tooling. The project supports the full range of current Python versions, uses modern dependency management (Pipenv), modern formatting (black 24.8.0), type checking (mypy 1.8.0), and modern packaging patterns. AWS SDK usage is via boto3 (latest), which is the current Python SDK for AWS. Framework ecosystem is mature: troposphere, werkzeug, click, requests. |
| **Gap** | None. Language and framework stack are current and well-maintained. |
| **Recommendation** | Continue maintaining support for latest Python versions. Consider migrating from setup.py to pyproject.toml for modern packaging standards. |
| **Evidence** | `setup.py` — python_requires=">=3.9", classifiers include 3.9-3.14; `Pipfile` — boto3>=1.17.28, troposphere>=3.0; `.pre-commit-config.yaml` — black 24.8.0, mypy v1.8.0 |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Single deployable unit — tightly-coupled monolithic CLI application. The `zappa/` package has 11 modules with significant cross-module coupling: `cli.py` (3,655 lines) imports from `core.py` (3,866 lines) which imports from `utilities.py`; `handler.py` imports from `wsgi.py`, `asgi.py`, `middleware.py`, and `utilities.py`. No clear module boundaries — cli.py contains 3,655 lines of mixed concerns (AWS interaction, user I/O, configuration parsing, deployment logic). |
| **Gap** | Tightly-coupled monolith with no clear service boundaries. `cli.py` handles everything from settings parsing to AWS API calls. No interface contracts between modules. |
| **Recommendation** | As a CLI tool, full microservice decomposition is not warranted. However, internal modularization would improve maintainability: separate configuration parsing, AWS orchestration, and deployment logic into distinct modules with clear interfaces. Consider a plugin architecture for event sources and deployment targets. |
| **Evidence** | `zappa/cli.py` — 3,655 lines; `zappa/core.py` — 3,866 lines; single `setup.py` packaging all modules together; `zappa/cli.py` directly imports from `zappa/core.py` and `zappa/utilities.py` |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Sync request/response (CLI command → AWS API calls → result) is the correct design; async inter-service communication is not needed. The tool makes synchronous boto3 API calls which is appropriate for a CLI tool awaiting operation completion. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `zappa/core.py` — all AWS interactions are synchronous boto3 calls; `zappa/cli.py` — sequential command execution |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. No operations exceed 30 seconds in the CLI tool's typical execution context — not applicable by design. Deployment operations (zip creation, S3 upload, CloudFormation stack updates) are inherently sequential CLI operations where the user expects to wait for completion. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `zappa/cli.py` — deployment commands use `tqdm` progress bars for long operations (S3 upload); CloudFormation stack operations poll until completion (expected CLI behavior) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The tool exposes a Python API (importable modules) and a CLI interface. CLI versioning exists via `zappa/__init__.py` version string and PyPI releases, but there is no formal API versioning strategy for the Python library interface. Breaking changes in the module API are not managed through versioning — imports from `zappa.core` or `zappa.handler` have no stability contract. |
| **Gap** | No formal API versioning for the Python library interface. Consumers importing from `zappa.core` or `zappa.handler` have no backward compatibility guarantee beyond SemVer at the package level. |
| **Recommendation** | Define a public API surface with `__all__` exports. Document which interfaces are stable vs internal. Use deprecation warnings before removing public APIs. |
| **Evidence** | `zappa/__init__.py` — version string; `setup.py` — SemVer versioning; no `__all__` in any module; no deprecation patterns observed |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | AWS service endpoints are resolved via boto3's built-in endpoint resolution (region-based). User deployment configuration uses environment variables and settings files (`zappa_settings.json`) for all service addresses. No dynamic service discovery — all endpoints are either AWS-managed (boto3 handles this) or user-configured (S3 bucket names, VPC IDs, etc.). |
| **Gap** | Environment variables and settings files for endpoints but no dynamic discovery mechanism. However, for a CLI deployment tool, environment-based configuration is architecturally appropriate. |
| **Recommendation** | Current approach is adequate for a CLI tool. If multi-environment deployment orchestration is added, consider AWS Systems Manager Parameter Store for dynamic configuration resolution. |
| **Evidence** | `test_settings.json` — S3 bucket names, VPC configs as static settings; `zappa/core.py` — boto3 sessions with region-based endpoint resolution |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The tool stores deployment packages (zip files) in S3. S3 is the primary storage mechanism for deployment artifacts. However, there is no parsing pipeline or content extraction — packages are binary artifacts stored for Lambda deployment, not documents requiring indexing or search. |
| **Gap** | S3 is used for artifact storage but with no parsing or extraction pipeline. For a deployment tool, this is appropriate — deployment packages don't need content parsing. |
| **Recommendation** | No action needed. S3 usage for deployment artifacts is appropriate. If build artifact analysis or dependency scanning is desired, consider adding S3 event-triggered analysis pipelines. |
| **Evidence** | `zappa/core.py` — S3 bucket operations for zip package upload/download; `test_settings.json` — `"s3_bucket": "lmbda"` configuration |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | AWS API access is partially centralized through the `Zappa` class in `zappa/core.py`, which wraps boto3 calls for Lambda, API Gateway, S3, IAM, CloudFormation, and other services. However, some boto3 operations are also performed directly in `zappa/cli.py` and `zappa/letsencrypt.py`, bypassing the core library's abstraction layer. |
| **Gap** | Data/API access layer is mostly centralized in `zappa/core.py` but not fully — `cli.py` and `letsencrypt.py` make direct boto3 calls outside the unified layer. |
| **Recommendation** | Consolidate all AWS API interactions into `zappa/core.py`. Extract Let's Encrypt ACME operations into a dedicated module that uses the core Zappa class for Route53 operations rather than direct boto3 calls. |
| **Evidence** | `zappa/core.py` — primary AWS interaction layer (Zappa class); `zappa/cli.py` — some direct boto3 usage; `zappa/letsencrypt.py` — direct Route53 boto3 calls |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `application` repository with no persistent data store (has_persistent_data_store=false). No database engine versions to evaluate. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `application` repository with no database. No stored procedures, triggers, or proprietary SQL constructs exist. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or audit logging configuration exists in the repository. The tool itself does not configure audit logging for its operations. While it creates CloudWatch Logs resources for user Lambda functions, it has no audit trail for deployment operations performed by the tool. Python `logging` module is used for CLI output but not for audit purposes. |
| **Gap** | No audit logging for deployment operations. A malicious or erroneous deployment has no audit trail beyond local CLI output and AWS CloudTrail (which the user must configure independently). |
| **Recommendation** | Add structured audit logging for all deployment operations (deploy, update, rollback, undeploy). Log operation metadata (who, what, when, which AWS account/region) to a structured format. Document that users should have CloudTrail enabled in their AWS accounts. |
| **Evidence** | No `aws_cloudtrail` resources; no audit log configuration; `zappa/core.py` uses `logging.basicConfig()` for operational logs only |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no database, no S3 bucket owned by the tool, no EBS volume, or similar. SEC-Q2 does not apply. The tool creates S3 buckets in user accounts but does not own data-at-rest infrastructure itself. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No IaC defining data stores; S3 buckets are created in user AWS accounts, not owned by the tool |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This system has no API surface (has_api_surface=false). It is a CLI tool — authentication is handled via AWS credentials (boto3 credential chain). SEC-Q3 does not apply to a CLI tool with no HTTP endpoints. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No HTTP endpoints; CLI uses boto3 credential resolution (environment variables, ~/.aws/credentials, IAM roles) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The tool relies on AWS IAM credentials via boto3's credential chain (environment variables, shared credentials file, IAM instance profiles, SSO). It supports IAM role assumption via `profile_name` setting. However, it does not integrate with a centralized identity provider for its own operations — it delegates entirely to AWS credential resolution. Supports configuring Cognito for user deployments but does not use centralized identity for the tool itself. |
| **Gap** | No centralized identity integration for the tool's own operations. Relies on AWS credential chain which can federate with external IdPs but the tool has no awareness of this. |
| **Recommendation** | Document best practices for using AWS SSO/IAM Identity Center with Zappa. Verify compatibility with SSO credential profiles. Consider adding explicit SSO profile support in settings. |
| **Evidence** | `zappa/core.py` — boto3 session creation with optional `profile_name`; `test_settings.json` — no identity provider configuration |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Default IAM policies in `zappa/policies/attach_policy.json` use wildcard permissions (`"Resource": "*"`) for multiple services (S3, DynamoDB, SNS, SQS, Kinesis, Route53, Lambda, EC2, X-Ray). The `remote_env` feature loads environment variables from S3 (`"remote_env": "s3://lmbda-env/prod/env.json"`) — secrets stored in plaintext JSON files on S3 without Secrets Manager integration. No secrets rotation or encrypted secrets management. |
| **Gap** | Wildcard IAM permissions in default policies. Secrets (environment variables) stored as plaintext JSON in S3 via `remote_env` feature. No Secrets Manager or Vault integration. |
| **Recommendation** | Replace wildcard IAM policies with least-privilege resource-scoped permissions. Add Secrets Manager integration for sensitive environment variables instead of plaintext S3 files. Add `aws_secrets_manager` as a supported source for runtime secrets. Preferences favor avoiding Lambda-based approaches — consider documenting EKS-based secrets management patterns for users migrating off Lambda. |
| **Evidence** | `zappa/policies/attach_policy.json` — wildcard `"Resource": "*"` on 8 service blocks; `test_settings.json` — `"remote_env": "s3://lmbda-env/prod/env.json"` (plaintext secrets in S3) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The tool targets AWS Lambda which is inherently patched by AWS (managed runtime). For Docker-based deployments (ECR), the tool supports custom base images but provides no guidance on image hardening or vulnerability scanning. Dependabot is not configured for the repository itself. Pre-commit hooks include static analysis (mypy, flake8) but no security-focused scanning. |
| **Gap** | No vulnerability scanning for the tool's own dependencies. No Dependabot or security advisory monitoring configured. No guidance for users on container image hardening for ECR-based deployments. |
| **Recommendation** | Enable Dependabot for Python dependency vulnerability scanning. Add `pip-audit` or `safety` to CI pipeline. For ECR-based deployments, document recommended base images (AWS-provided Lambda base images, Bottlerocket for EKS alternatives). |
| **Evidence** | `.github/workflows/ci.yml` — no security scanning step; `.pre-commit-config.yaml` — no security-focused hooks; no `.github/dependabot.yml` file |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The CI pipeline includes static analysis via flake8 (code quality) and mypy (type checking), but no SAST, DAST, or dependency vulnerability scanning tools are integrated. No Dependabot configuration, no `pip-audit`, no Snyk, no CodeQL. Pre-commit hooks run black, isort, flake8, and mypy — code quality tools but not security scanners. |
| **Gap** | No security-focused scanning in the CI/CD pipeline. Flake8 catches code quality issues but not security vulnerabilities. No dependency vulnerability scanning. |
| **Recommendation** | Add CodeQL or Semgrep to GitHub Actions for SAST. Add `pip-audit` step to CI pipeline for dependency vulnerability scanning. Configure Dependabot for automated dependency security updates. Add `.github/dependabot.yml` for Python ecosystem. |
| **Evidence** | `.github/workflows/ci.yml` — lint step uses flake8/black/isort only; `.pre-commit-config.yaml` — no security hooks; no `.github/dependabot.yml` |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing is instrumented in the tool itself. The tool supports X-Ray tracing for user deployments (`xray_tracing` setting, X-Ray permissions in attach_policy.json) but does not trace its own operations. CLI commands make multiple sequential AWS API calls with no trace context propagation. |
| **Gap** | No tracing for the tool's own multi-service AWS API operations. Deployment operations span Lambda, S3, API Gateway, CloudFormation, IAM — all without trace correlation. |
| **Recommendation** | Add OpenTelemetry instrumentation to boto3 calls within the tool for debugging deployment issues. This would enable users to trace why a deployment failed across multiple AWS service interactions. |
| **Evidence** | `zappa/policies/attach_policy.json` — X-Ray permissions for user deployments; no OpenTelemetry or X-Ray SDK imports in source code |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no user-facing surface for which SLOs are meaningful. OPS-Q2 does not apply. The tool is a CLI utility — it does not serve user traffic or maintain availability guarantees. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | CLI tool with no service-level guarantees; no deployed workload |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no user-facing surface for which business metrics are meaningful. As a CLI deployment tool, it does not generate business outcome metrics. OPS-Q3 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | CLI tool; no CloudWatch custom metrics; no business KPI tracking |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload for which anomaly detection is meaningful. As a CLI tool, it has no persistent runtime to monitor for anomalies. OPS-Q4 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No deployed workload; no CloudWatch alarms; no monitoring configuration |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Direct-to-production deployment with no staged rollout. The CD workflow (`.github/workflows/cd.yml`) publishes directly to PyPI production after manual trigger. The dry-run option exists but is a manual safeguard, not an automated staging strategy. No TestPyPI staging, no canary release, no phased rollout. |
| **Gap** | No deployment strategy — releases go directly to PyPI production. No staging, no canary, no phased rollout for the package itself. |
| **Recommendation** | Add TestPyPI as a staging target before production release. Implement automated smoke tests against TestPyPI install. Consider phased release via GitHub pre-release flags before marking as latest. |
| **Evidence** | `.github/workflows/cd.yml` — single `publish` job to PyPI with no staging step; `dry-run` is a manual input, not automated staging |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Tests exist and run in CI (`.github/workflows/ci.yml` — pytest across 6 Python versions). Tests use `placebo` for AWS API mocking — recording and replaying AWS API responses. This provides unit-level testing of AWS interactions but not true integration testing against live AWS services. No end-to-end deployment tests exist. |
| **Gap** | Tests use mocked AWS responses (placebo) but no integration tests against real AWS services. A deployment tool's critical path (actual Lambda deployment, API Gateway creation) is never tested end-to-end in CI. |
| **Recommendation** | Add integration test suite using a sandboxed AWS account or LocalStack. Test actual deploy/update/undeploy lifecycle against real AWS services in CI. Mark integration tests as a separate CI stage that runs on merge to master (not on every PR). |
| **Evidence** | `tests/placebo/` — large collection of recorded AWS API responses; `Makefile` — test targets use pytest; `.github/workflows/ci.yml` — runs all tests but all use mocked responses |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The tool provides rollback functionality (`zappa rollback`) which enables users to revert deployments. The `rollback` command restores a previous Lambda deployment package from S3. However, this is user-initiated recovery, not automated incident response. No runbooks, no automated remediation, no self-healing patterns exist for the tool's own operations. |
| **Gap** | Rollback exists as a manual CLI command. No automated incident detection or response for deployment failures. No structured runbooks for common failure scenarios. |
| **Recommendation** | Add automatic rollback on deployment failure (detect CloudFormation ROLLBACK_COMPLETE and restore previous state). Create structured runbooks for common deployment failures (permissions errors, package size limits, timeout issues). |
| **Evidence** | `zappa/cli.py` — `rollback` command implementation; no automated failure detection or response |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload for which observability ownership is meaningful. As a CLI tool published to PyPI, there are no service-level dashboards, alarms, or SLOs to own. OPS-Q8 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | CLI tool; no dashboards, no alarms, no team attribution for observability assets |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The tool supports resource tagging for user deployments. Users can configure tags via `tags` setting in `zappa_settings.json` which are applied to Lambda functions and other created resources. The tool applies tags to CloudFormation stacks and Lambda functions. However, there is no enforcement or validation of tagging standards — tags are optional and user-defined with no required keys. |
| **Gap** | Tagging is supported but not enforced. No required tag keys (environment, owner, cost-center). No validation that user-provided tags meet organizational standards. |
| **Recommendation** | Add optional `required_tags` configuration that validates user-provided tags against organizational standards before deployment. Document tagging best practices in README. |
| **Evidence** | `zappa/core.py` — tag application to CloudFormation stacks and Lambda functions; `test_settings.json` — no tags in test configurations (optional feature) |

## Decomposition Strategy

APP-Q2 scored 1 (tightly-coupled monolith). However, because this is a CLI deployment tool (not a web service), full microservice decomposition is not architecturally warranted. Instead, **internal modularization** is the appropriate decomposition strategy.

### Recommended Approach: Conditional / Adaptive (Internal Modularization)

For a CLI tool, the "decomposition" pathway is about improving internal code organization rather than splitting into independent services:

| Approach | Description | Applicability |
|----------|-------------|---------------|
| **Internal Module Extraction** | Extract `cli.py` (3,655 lines) and `core.py` (3,866 lines) into smaller focused modules with clear interfaces | ✅ Recommended — reduces cognitive load, improves testability |
| **Plugin Architecture** | Define plugin interfaces for event sources, deployment targets, and cloud providers | ✅ Recommended if multi-cloud support is desired |
| **Full Service Decomposition** | Split into microservices | ⚠️ Not recommended — a CLI tool does not benefit from service-level decomposition |

### Pattern Recommendations

| Pattern | Purpose | Application to Zappa |
|---------|---------|---------------------|
| **Hexagonal Architecture** | Separate core business logic from infrastructure concerns | Extract AWS-specific boto3 calls behind interfaces (ports); CLI is one adapter, a potential API service is another |
| **Command Pattern** | Encapsulate each CLI operation as a discrete command object | Replace 3,655-line cli.py with individual command classes (DeployCommand, UpdateCommand, RollbackCommand) |

### Effort Estimation

| Factor | Signal | Assessment |
|--------|--------|------------|
| Module boundaries | Identifiable (cli.py, core.py, handler.py, utilities.py) but with cross-cutting concerns | Medium effort |
| Data coupling | Low — no shared database; coupling is via function calls and shared config | Low effort |
| Test coverage | Comprehensive mocked tests exist; refactoring has safety net | Low risk |
| CI maturity | Full CI pipeline in place | Supports incremental refactoring |

**Estimated effort:** Medium — 2-4 weeks of focused refactoring to extract cli.py and core.py into well-bounded modules with clear interfaces.

## Learning Materials

- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `.github/workflows/ci.yml` | INF-Q11, SEC-Q6, SEC-Q7, OPS-Q6 | CI pipeline with lint and test stages |
| `.github/workflows/cd.yml` | INF-Q11, OPS-Q5 | Manual CD pipeline for PyPI publishing |
| `.github/workflows/maintenance.yml` | INF-Q11 | Stale issue management |
| `zappa/cli.py` | APP-Q2, APP-Q3, APP-Q4, OPS-Q7 | Main CLI module (3,655 lines) |
| `zappa/core.py` | INF-Q1, INF-Q2, INF-Q3, INF-Q4, INF-Q5, INF-Q10, APP-Q2, DATA-Q1, DATA-Q2, OPS-Q1, OPS-Q9 | Core AWS interaction library (3,866 lines) |
| `zappa/handler.py` | APP-Q2 | Lambda handler singleton |
| `zappa/asynchronous.py` | INF-Q4 | Async task execution for user deployments |
| `zappa/letsencrypt.py` | DATA-Q2 | Direct boto3 Route53 calls bypassing core |
| `zappa/policies/attach_policy.json` | INF-Q5, SEC-Q5, OPS-Q1 | Default IAM execution policy with wildcards |
| `zappa/policies/assume_policy.json` | INF-Q5 | IAM assume role policy |
| `setup.py` | APP-Q1, INF-Q6 | Package configuration and entry points |
| `Pipfile` | APP-Q1 | Dependency management |
| `.pre-commit-config.yaml` | SEC-Q6, SEC-Q7 | Code quality hooks (no security scanning) |
| `test_settings.json` | INF-Q5, INF-Q7, APP-Q6, SEC-Q5, DATA-Q1 | Test configuration with deployment settings |
| `tests/placebo/` | OPS-Q6 | Mocked AWS API responses for testing |
| `Makefile` | OPS-Q6 | Build and test automation targets |
| `README.md` | Quick Agent Wins | Comprehensive documentation |
