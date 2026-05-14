# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | zappa--Zappa |
| **Date** | 2026-01-15 |
| **TD Version** | modernization-readiness-analysis-v6.2-simulated |
| **Repo Type** | application |
| **Service Archetype** | stateless-utility (auto-detected) |
| **Priority** | P2 |
| **Tags** | python, serverless |
| **Context** | Python framework for deploying WSGI apps on AWS Lambda. |
| **Overall Score** | 1.98 / 4.0 |

**Archetype Justification**: Zappa is a CLI tool and library with no persistent database connections, no user-specific state, no write-back endpoints, and no deployed API surface of its own. All operations are stateless command executions (package, deploy, update, rollback) that orchestrate AWS resources on behalf of users. Classified as stateless-utility.

**Surface Flags**: has_persistent_data_store=false, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=false, has_multi_instance_deployment=false, has_iac_provisioning_aws_resources=false

**Preferences**: prefer = [eks, aurora, dynamodb, api-gateway, eventbridge, bedrock]; avoid = [self-managed-kafka, self-managed-kubernetes, oracle]. Preferences steer recommendation framing only — they do not change scores or pathway triggers (Constraint C6).

---

## Classification

**Tier: Remediation Required**

This repo has 4 High findings, 15 Medium findings, 1 Low finding. The matched rule is: **"2-11 High → Remediation Required"**.

MOD classification treats "1 High" as Pilot-Ready (a single modernization gap) rather than a deployment blocker. This contrasts with the ARA classification, where "1 High" is an agent-deployment gate due to safety concerns. With 4 High findings here, this repo falls into the "2-11 High → Remediation Required" tier, indicating significant modernization gaps across infrastructure, security, and operations — though the majority reflect the structural fact that Zappa is a CLI tool rather than a deployed service.

**Classification consistency check**: `consistent`. V5 overall score 1.98 maps to V5 band "Needs Work" (1.5–2.4), which is the V5/V6 equivalence partner of V6 tier "Remediation Required" per Req 29 AC 1.

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | 1.50 / 4.0 | 🟠 Needs Work | Critical |
| Application Architecture (APP) | 2.00 / 4.0 | 🟠 Needs Work | Critical |
| Data Platform Modernization (DATA) | 3.75 / 4.0 | ✅ Mature | Needs Work |
| Security Baseline (SEC) | 1.20 / 4.0 | ❌ Not Ready | Needs Work |
| Operations & Observability (OPS) | 1.43 / 4.0 | ❌ Not Ready | Needs Work |
| **Overall** | **1.98 / 4.0** | **🟠 Needs Work** | |

**Scoring Notes** (N/A and Not Evaluated questions excluded from both numerator and denominator):

- **INF**: (1+1+1+1+1+4) / 6 = 9/6 = 1.50. Q2 excluded (surface-gated: no persistent data store). Q3, Q4 excluded (archetype-N/A: stateless-utility). Q8 excluded (surface-gated: no data to back up). Q9 excluded (surface-gated: no deployed workload).
- **APP**: (4+1+1+2) / 4 = 8/4 = 2.00. Q3, Q4 excluded (archetype-N/A: stateless-utility).
- **DATA**: (3+4+4+4) / 4 = 15/4 = 3.75.
- **SEC**: (1+1+2+1+1) / 5 = 6/5 = 1.20. Q1 excluded (surface-gated: no account-level IaC). Q2 excluded (surface-gated: no data-at-rest surface).
- **OPS**: (1+1+1+4+1+1+1) / 7 = 10/7 = 1.43. Q2 excluded (surface-gated: no user-facing surface). Q5 excluded (surface-gated: no deployed workload).

**Category-level divergence** between `score_rating` (V5 band) and `severity_status` (V6 severity count) is permitted and expected: DATA scores Mature on the V5 band because DATA-Q1 scored 3 and the other three DATA questions scored 4, but V6 severity_status shows Needs Work because the single DATA-Q1 Low-severity finding is counted.

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q1: Managed Compute | 1 | No managed compute infrastructure — CLI tool with no deployed workload | Cannot evaluate cloud-native compute readiness |
| 2 | INF-Q10: IaC Coverage | 1 | 0% IaC for the project's own operational infrastructure | No auditable, reproducible definition of repo-level infra |
| 3 | INF-Q5: Network Security | 1 | No VPC, subnet, or security group — no deployed network | Structural; if hosted as a service, VPC-based design required |
| 4 | APP-Q2: Monolith vs Microservices | 1 | Tightly-coupled monolith: core.py (3,866 LOC) god class | Limits testability, maintainability, and handler extraction |
| 5 | SEC-Q7: Application Security Pipeline | 1 | No SAST, dependency scanning, or container scanning in CI/CD | Vulnerabilities may reach PyPI releases undetected |

---

## Quick Agent Wins

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists — extensive README, CHANGELOG, docs/ directory, CONTRIBUTING.md, and example/ with detailed usage guides.
- **What it enables:** Index Zappa's documentation to answer developer questions about zappa_settings.json configuration, deployment patterns, and version migration between releases.
- **Additional steps:** Convert README sections into structured chunks; generate embeddings for the settings reference and event source documentation. preferences.prefer includes `bedrock`, so Amazon Bedrock Knowledge Bases is the recommended target.
- **Effort:** Low

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 4) — mature GitHub Actions CI across Python 3.9-3.14 and manual CD workflow with OIDC PyPI publishing.
- **What it enables:** Trigger CI runs, check build status across the Python matrix, monitor Coveralls coverage reports, and manage the manual CD workflow (tagged releases to PyPI).
- **Additional steps:** Expose GitHub Actions API access to the agent; define trigger conditions for the manual CD workflow dispatch.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=1 (monolith), INF-Q1=1 (no managed compute) |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1=1 meets threshold, but contextual guard blocks: no deployed workload (CLI tool, not a running service) |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (no stored procedures); no commercial DB engines detected |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 Not Evaluated (no database); DATA-Q3=4 |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 Not Evaluated (archetype-N/A); no data processing workloads |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1 (no IaC for own infrastructure); SEC-Q7=1 supporting |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State (APP-Q2=1):** Zappa is a single monolithic Python package with two dominant modules — `cli.py` (3,655 LOC) and `core.py` (3,866 LOC) — that are tightly coupled. The CLI module directly instantiates and calls methods on the Zappa core class. No module boundaries, no clear interfaces between deployment orchestration, Lambda management, API Gateway management, and CloudFormation stack operations.

**Compute Model Gaps (INF-Q1=1):** Zappa itself has no deployed compute. It runs on developer machines and in GitHub-hosted CI runners. There is no managed compute infrastructure to modernize in-place.

**Recommended Decomposition Approach:** Given that Zappa is a CLI tool rather than a deployed service, "Move to Cloud Native" in this context means refactoring the monolithic package into well-bounded modules with clear interfaces. This enables:

- Publishing the handler runtime as a separate lightweight package (reducing Lambda cold start)
- Offering the orchestration layer as a standalone library for programmatic use
- Supporting plugin architectures for different cloud providers or deployment targets

**Representative AWS Services:** Lambda, API Gateway, Step Functions, EventBridge. ECS/EKS apply if a hosted orchestration service is ever added. preferences.prefer includes `eks`, `api-gateway`, and `eventbridge`, which aligns with these services.

**Recommended Patterns:** Hexagonal Architecture (separate CLI, orchestration, handler concerns), Anti-corruption Layer (between boto3 and domain logic).

**Learning Materials:**
- [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN)
- [AWS Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10=1):** No infrastructure-as-code defines Zappa's own operational infrastructure:

- No Terraform or CDK managing PyPI publishing configuration, GitHub environments, or secrets
- No IaC for GitHub branch protections, CODEOWNERS policies, or repository settings
- No operational infrastructure (monitoring, alerting) defined in code

**Current CI/CD State (INF-Q11=4):** Excellent CI/CD pipeline covering:

- Multi-version Python test matrix (3.9-3.14)
- Lint checks (flake8, black, isort)
- Coverage reporting via Coveralls
- Manual CD pipeline with dry-run support, tagging, GitHub Release, and PyPI publish via OIDC trusted publisher

**Gaps to Address:**

- Add dependency vulnerability scanning (pip-audit, Safety, or GitHub Dependabot) — addresses SEC-Q7=1
- Add SAST tooling (Semgrep, Bandit) to the CI pipeline — addresses SEC-Q7=1
- Define IaC for GitHub repository settings, branch protections, and secrets rotation — addresses INF-Q10=1
- Add security gates that block merges on critical vulnerability findings

**Recommended DevOps Toolchain:** GitHub Dependabot for dependency scanning, Bandit or Semgrep for Python SAST, GitHub branch protection rules codified via the Terraform GitHub provider.

**Learning Materials:**
- [AWS Modernization Pathways: Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Decomposition Strategy

> This section is included because APP-Q2 < 3.

### Current State

Zappa is a single deployable package with tightly coupled modules. The primary coupling is between:

- `cli.py` (3,655 LOC) — CLI command handling, user interaction, settings loading, and orchestration
- `core.py` (3,866 LOC) — AWS service interactions (Lambda, API Gateway, S3, CloudFormation, IAM)
- `handler.py` (1,003 LOC) — Lambda runtime handler (WSGI/ASGI translation)
- `utilities.py` (1,049 LOC) — shared helpers

`cli.py` directly imports and instantiates `Zappa` from `core.py`, calling dozens of methods with complex parameter passing. `core.py` handles everything from ZIP creation to CloudFormation template generation to IAM role creation — a god class pattern.

### Recommended Approach: Strangler Fig (Parallel Track)

| Approach | Description | Level of Effort | Recommendation |
|----------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Extract `handler.py` + `wsgi.py` + `asgi.py` as a standalone lightweight package first (Lambda runtime only). Then progressively extract AWS service modules from `core.py` into focused modules (lambda_ops, apigateway_ops, cloudformation_ops, s3_ops). | Medium to High | ✅ **Recommended.** Lowest risk. Handler extraction provides immediate value (smaller Lambda packages). |
| **Conditional / Adaptive** | Keep the monolithic package but refactor `core.py` into internal modules with clear interfaces. Don't split into separate packages unless specific business need arises. | Low to Medium | ✅ **Recommended when team capacity is limited.** Internal modularization without package splits. |
| **Big-Bang Rewrite** | Rewrite Zappa as a multi-package monorepo with separate packages for CLI, core, handler, and extensions. | Very High | ⚠️ **Not recommended.** High risk of breaking the existing user base. |

### Pattern Recommendations

| Pattern | Purpose | Application to Zappa |
|---------|---------|---------------------|
| **Hexagonal Architecture** | Separate domain logic from infrastructure adapters | Separate AWS SDK calls (adapters) from deployment logic (domain). Enable testing without placebo mocks. |
| **Anti-corruption Layer** | Isolate internal refactoring from public API | Maintain backward-compatible CLI interface and settings format while restructuring internals. |

Links to AWS prescriptive guidance: [Strangler Fig](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html), [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html).

### Effort Estimation Factors

| Factor | Current State | Effort Signal |
|--------|--------------|---------------|
| Module boundaries | Minimal — cli.py and core.py are 7,500+ LOC combined | High effort |
| Data coupling | No database coupling (stateless tool) | Low effort |
| Test coverage | Good — 36 test files with comprehensive mocking | Low effort (regression safety net exists) |
| CI/CD maturity | Excellent — full pipeline exists (INF-Q11=4) | Low effort (can support multi-package builds) |
| Stored procedures | None (DATA-Q4=4) | Low effort |
| Async patterns | Not applicable (stateless-utility archetype) | — |

---

## Detailed Findings

### Infrastructure, Platform, and DevOps (INF)

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zappa is a CLI tool and Python library published to PyPI. It has no deployed compute infrastructure of its own — no Lambda functions, no ECS tasks, no EC2 instances run this tool as a service. It runs on developer machines and in GitHub-hosted CI runners. |
| **Gap** | No managed compute — all execution happens locally or in ephemeral CI environments. |
| **Recommendation** | If a hosted deployment service is desired in the future, ECS/Fargate or Lambda are appropriate targets. For the current CLI tool use case, this gap is structural rather than a deficiency. |
| **Evidence** | No `aws_ecs_*`, `aws_eks_*`, `aws_lambda_*`, or `aws_instance` resources found. No Dockerfile. setup.py defines a console_scripts entry point only. |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy a database (surface-gated: has_persistent_data_store=false). INF-Q2 does not apply. Zappa is a stateless CLI tool that reads settings files and makes API calls to AWS — it has no persistent data store of its own. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database drivers, no connection strings, no `aws_rds_*` or `aws_dynamodb_*` resources. No ORM imports. |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Workflow orchestration is not applicable by design — no multi-step workflows exist that require retry/resume semantics. Each Zappa command (deploy, update, rollback) is a single imperative sequence appropriate for a CLI tool. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No `aws_sfn_*` resources, no Temporal SDK, no workflow YAML. Commands are sequential imperative operations in cli.py. |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Synchronous CLI execution is the correct design; async messaging is not needed for Zappa's own execution model. (Note: Zappa *configures* SNS/SQS/Kinesis event sources for user apps via zappa_settings.json, but does not consume messaging itself.) |
| **Gap** | N/A |
| **Recommendation** | N/A — adopting async messaging would add operational complexity without architectural benefit for a CLI tool. |
| **Evidence** | `zappa/asynchronous.py` provides async task dispatch for user-deployed apps, not for Zappa's own execution. CLI operations are synchronous. |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or network segmentation configuration exists. Zappa is a CLI tool executed on developer machines — it has no deployed network infrastructure. |
| **Gap** | No network security configuration — the tool itself is not deployed in a VPC. |
| **Recommendation** | Not applicable for a CLI tool. If Zappa were hosted as a service, private subnets with least-privilege security groups and VPC endpoints would be required. |
| **Evidence** | No `aws_vpc`, `aws_subnet`, `aws_security_group` resources. No network configuration files. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zappa exposes no HTTP API of its own. It is invoked via `zappa deploy/update/rollback` commands. No API Gateway, ALB, or CloudFront serves as an entry point for this tool. (Zappa *creates* API Gateways for user apps.) |
| **Gap** | No API entry point — the tool is CLI-only. |
| **Recommendation** | If a programmatic API is desired, expose deployment operations via API Gateway with authentication and throttling. preferences.prefer includes `api-gateway`. |
| **Evidence** | setup.py entry_points define only `zappa=zappa.cli:handle`. No HTTP server code in the package. |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling — Zappa has no deployed compute to scale. It runs as a local CLI process. |
| **Gap** | No auto-scaling — no workload to scale. |
| **Recommendation** | Not applicable for a CLI tool. No action needed. |
| **Evidence** | No `aws_autoscaling_*`, no `aws_appautoscaling_*` resources. No Lambda concurrency configuration for the tool itself. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no persistent state to back up (surface-gated: has_persistent_data_store=false AND has_at_rest_data_surface=false). INF-Q8 does not apply. Deployment artifacts are uploaded to user-owned S3 buckets managed by the user's AWS account. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No `backup_retention_period`, no `aws_backup_plan`, no data stores requiring backup. |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload requiring HA evaluation (surface-gated: has_deployed_workload=false). INF-Q9 does not apply. Zappa runs as a local CLI tool — there is no production service that needs multi-AZ resilience. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No `multi_az` configuration, no ASG, no ECS service, no deployed workload. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC defines Zappa's own operational infrastructure. GitHub Actions workflows exist as YAML but no Terraform, CDK, or CloudFormation manages the project's CI/CD infrastructure, PyPI publishing credentials, or GitHub repository settings. Note: Zappa *generates* CloudFormation for user apps via troposphere, but has no IaC for itself. |
| **Gap** | 0% IaC coverage for the project's own infrastructure (GitHub environments, secrets, branch protections). |
| **Recommendation** | Consider the Terraform GitHub provider to codify repository settings, branch protection rules, and environment/secret management. This provides auditability and reproducibility for the project's operational infrastructure. |
| **Evidence** | No `.tf` files, no `cdk.json`, no CloudFormation templates for own infrastructure. `.github/workflows/*.yml` define pipelines but are not IaC for infrastructure provisioning. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Full CI/CD automation via GitHub Actions covering both application code testing and release publishing. CI (`.github/workflows/ci.yml`) runs on every push/PR with: Python 3.9-3.14 test matrix, lint checks (flake8, black, isort), pytest with coverage, Coveralls reporting. CD (`.github/workflows/cd.yml`) provides manual-trigger release with build verification, semantic versioning, GitHub Release creation, and automated PyPI publish via trusted publisher (OIDC). |
| **Gap** | No gap — CI/CD is comprehensive for a library/CLI tool. |
| **Recommendation** | No action needed. Consider adding automated dependency update checks (Dependabot) and security scanning gates (see SEC-Q7). |
| **Evidence** | `.github/workflows/ci.yml`, `.github/workflows/cd.yml`, `.github/workflows/maintenance.yml`, `Makefile` with test/lint targets. |

---

### Application Architecture (APP)

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Python 3.9-3.14 with a modern ecosystem. Uses current boto3 (>=1.17.28), troposphere (>=3.0), modern tooling (black, mypy, isort, pytest). The framework tracks the latest Python versions including 3.14. Dependencies are well-maintained and current. |
| **Gap** | No gap — modern Python with current AWS SDK. |
| **Recommendation** | No action needed. Continue tracking Python version support as new versions are released. |
| **Evidence** | `setup.py` python_requires=">=3.9", classifiers include 3.9-3.14. `Pipfile` specifies modern dependency versions. `zappa/__init__.py` validates SUPPORTED_VERSIONS = [(3,9)...(3,14)]. |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Tightly-coupled monolith. Single Python package (`zappa/`) with no module boundaries. `core.py` (3,866 LOC) is a god class handling Lambda management, API Gateway setup, S3 uploads, IAM roles, CloudFormation stacks, VPC configuration, and certificate management. `cli.py` (3,655 LOC) directly instantiates and orchestrates `core.py`. Cross-module coupling is pervasive — `cli.py` accesses internal attributes of the `Zappa` class extensively. |
| **Gap** | No module boundaries, no clear interfaces, god class pattern in `core.py`. Single deployable unit with no separation of concerns. |
| **Recommendation** | Refactor into bounded modules: extract the Lambda handler runtime (handler.py + wsgi.py + asgi.py) as an independent package; extract AWS service adapters from core.py into focused modules (lambda_ops, apigateway_ops, cloudformation_ops, s3_ops); define clean interfaces between CLI and orchestration layers. See Decomposition Strategy section. |
| **Evidence** | `zappa/core.py` (3,866 lines, single class), `zappa/cli.py` (3,655 lines, single class), tight coupling between them. No internal package structure beyond flat module layout. |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Sync request/response (CLI invocation → AWS API calls → result) is the correct design; async inter-service communication is not needed. Zappa's CLI operations are inherently synchronous — a user runs a command and waits for completion. Archetype calibration: for stateless-utility, Score 4 under the default rubric is recorded instead as Not Evaluated to avoid inflating the archetype-correct score. |
| **Gap** | N/A |
| **Recommendation** | N/A — adopting async is NOT recommended; it would add operational complexity without architectural benefit. |
| **Evidence** | CLI entry point (`zappa.cli:handle`) processes commands synchronously. No inter-service communication — all calls are to AWS APIs via boto3. |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. No user-facing operations exceed 30 seconds in the critical path — not applicable by design. Deployment operations can take time (waiting for CloudFormation), but these are handled by boto3 waiter polling patterns in core.py that are appropriate for a CLI tool (users expect to wait for deployment). |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | CloudFormation wait operations in `core.py` use boto3 waiters (appropriate for CLI). No user-facing API that would timeout. |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy — Zappa exposes no HTTP API. The CLI uses semantic versioning for PyPI releases (v0.62.x) but has no URL-path, header, or query-parameter versioning for an API surface. `zappa_settings.json` has no explicit schema version field; changes are handled implicitly via deprecation warnings. |
| **Gap** | No API versioning — CLI tool with no REST API surface. Settings format changes are handled implicitly. |
| **Recommendation** | If Zappa adds a programmatic API or the settings schema evolves significantly, implement explicit versioning. For now, consider adding a settings schema version field to `zappa_settings.json` to enable forward-compatible configuration parsing. |
| **Evidence** | No `/v1/`, `/v2/` patterns. No Accept-Version headers. `zappa_settings.json` has no version field. CLI is versioned only by PyPI package version. |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Environment variables for AWS endpoint configuration via boto3 (AWS_DEFAULT_REGION, AWS_PROFILE, AWS_ACCESS_KEY_ID). boto3 handles AWS service endpoint resolution internally. No hard-coded AWS endpoints in the codebase — all AWS endpoints are resolved by the SDK based on region configuration. No dynamic service discovery beyond SDK endpoint resolution. |
| **Gap** | No dynamic service discovery mechanism, but for a CLI tool calling AWS APIs, boto3's built-in endpoint resolution is adequate. |
| **Recommendation** | No action needed. boto3's endpoint resolution is the correct pattern for AWS SDK-based tools. |
| **Evidence** | `os.environ["AWS_DEFAULT_REGION"]` in tests. boto3 session handling in `core.py`. No hard-coded AWS endpoint URLs. |

---

### Data Platform Modernization (DATA)

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Zappa uses S3 for storing deployment packages (ZIP files). It uploads, downloads, and manages S3 objects as part of the deployment workflow. However, there is no parsing pipeline — deployment packages are opaque ZIP archives, not parsed or indexed for content discovery. |
| **Gap** | Data in S3 but no automated parsing or extraction pipeline. |
| **Recommendation** | For the deployment tool use case, no parsing pipeline is needed — ZIPs are consumed by Lambda directly. If deployment analytics are desired (package size trends, dependency analysis), consider S3 event-driven processing via EventBridge (preferences.prefer includes `eventbridge`). |
| **Evidence** | `core.py` contains extensive S3 operations: `upload_to_s3()`, `remove_from_s3()`, `copy_on_s3()`. S3 bucket references throughout `cli.py` and test settings. |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All AWS service interactions are centralized through the `Zappa` class in `core.py`. This single class serves as the unified data access layer — all boto3 calls (S3, Lambda, API Gateway, CloudFormation, IAM, CloudWatch) go through this one module. The CLI layer (`cli.py`) never makes direct boto3 calls; it always goes through the `Zappa` core class. |
| **Gap** | No gap — centralized access layer. |
| **Recommendation** | No action needed. While core.py is too large (god class, see APP-Q2), it does provide a single point of control for AWS interactions. Future refactoring should maintain this centralization principle when splitting into sub-modules. |
| **Evidence** | `zappa/core.py` — single `Zappa` class handles all boto3 interactions. `zappa/cli.py` imports and uses only the `Zappa` class for AWS operations. |

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

### Security Baseline (SEC)

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | Audit logging (CloudTrail) is an AWS account-level service provisioned once per account or organization — not per-application. This repo contains no IaC provisioning AWS resources (has_iac_provisioning_aws_resources=false). Zappa is a CLI tool published to PyPI; CloudTrail evaluation belongs in the foundation/account-level infrastructure repo. Future: provide audit logging status via `additionalPlanContext`. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No `aws_cloudtrail` resources. No IaC provisioning AWS infrastructure. |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface (surface-gated: has_at_rest_data_surface=false) — no database, S3 bucket, EBS volume, EFS file system, or similar managed by this repo. SEC-Q2 does not apply. Zappa uploads to user-owned S3 buckets; encryption configuration is the user's responsibility. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | has_at_rest_data_surface=false. No `aws_s3_bucket`, `aws_rds_*`, or `aws_kms_key` resources defined by this repo. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API authentication — Zappa is a CLI tool with no HTTP endpoints. It does not expose an API that requires per-request authentication. Authentication to AWS is handled by the boto3 credential chain (environment variables, AWS profiles, IAM roles) which is standard for CLI tools. |
| **Gap** | No API authentication — no API surface exists to protect. |
| **Recommendation** | If Zappa were to expose a programmatic API (deployment-as-a-service), implement OAuth2/JWT authentication. For the current CLI use case, the boto3 credential chain is appropriate. |
| **Evidence** | No auth middleware, no API Gateway authorizers, no Cognito user pools for the tool itself. Entry point is CLI only (`zappa.cli:handle`). |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity integration. Zappa relies on the AWS IAM credential chain (environment variables, ~/.aws/credentials, instance profiles) for authentication to AWS services. No integration with Cognito, Okta, or other centralized IdP for the tool's own access control. |
| **Gap** | No centralized identity — relies entirely on local AWS credential configuration. |
| **Recommendation** | For a CLI tool, the AWS IAM credential chain with SSO support (`aws sso login`, IAM Identity Center) is the standard pattern. Document AWS SSO/IAM Identity Center integration in the README. |
| **Evidence** | boto3 session handling in `zappa/core.py`. No Cognito, OIDC/SAML, or SSO configuration for the tool itself. |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No plaintext credentials in source. AWS credentials are handled via the boto3 credential chain; PyPI publishing uses GitHub OIDC trusted publisher (no long-lived tokens in CD). However, no AWS Secrets Manager integration and no documented rotation policy. |
| **Gap** | Production credentials in environment variables without a documented rotation policy. No Secrets Manager integration. |
| **Recommendation** | Document credential rotation best practices in the README. Encourage IAM roles and SSO over long-lived access keys. If programmatic deployment use cases arise, add AWS Secrets Manager support for credential retrieval. |
| **Evidence** | `.github/workflows/cd.yml` uses OIDC trusted publishing. No `aws_secretsmanager_*` usage. No Vault client imports. No hardcoded credentials in source or committed `.env` files. |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute hardening configuration — Zappa has no deployed compute to harden. The tool runs on developer machines and on GitHub-hosted CI runners (auto-patched by GitHub). |
| **Gap** | No compute hardening — no deployed workload to harden. |
| **Recommendation** | For CI, GitHub-hosted runners are auto-patched. For the package itself, add dependency vulnerability scanning (see SEC-Q7). |
| **Evidence** | `.github/workflows/ci.yml` uses GitHub-hosted runners (`ubuntu-latest`). No SSM Patch Manager, no AWS Inspector configuration. |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SAST, DAST, or dependency vulnerability scanning in CI/CD. The pipeline has lint checks (flake8, black, isort) but no security-focused scanning. No Dependabot, pip-audit, Safety, Bandit, or Semgrep. |
| **Gap** | No security scanning — zero security validation steps in the pipeline. |
| **Recommendation** | Add Dependabot for dependency updates. Integrate pip-audit or Safety for vulnerability detection. Add Bandit or Semgrep for Python SAST. Configure blocking gates on critical findings. This is a quick, high-value improvement given the already-mature CI/CD (INF-Q11=4). |
| **Evidence** | `.github/workflows/ci.yml` — pytest, flake8, black, isort, coveralls steps only. No security tooling configured. No `dependabot.yml` in `.github/`. |

---

### Operations & Observability (OPS)

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No tracing instrumented in the Zappa CLI tool itself. While Zappa can configure X-Ray for user-deployed Lambda apps, the tool has no tracing for its own deployment operations — CloudFormation polling, S3 uploads, IAM updates are not traced. |
| **Gap** | No tracing of deployment operations. Complex multi-step deployments have no end-to-end trace visibility. |
| **Recommendation** | Consider OpenTelemetry instrumentation for core.py to trace deployment operations and identify AWS API bottlenecks. Low value unless deployment troubleshooting becomes a pain point. |
| **Evidence** | No OpenTelemetry, X-Ray, or tracing libraries in `Pipfile` or `setup.py` install_requires. |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no user-facing surface for which SLOs are meaningful (surface-gated: has_api_surface=false AND has_persistent_data_store=false). OPS-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No deployed API, no latency/error-rate alarms. CLI operation duration is inherent to the underlying AWS APIs. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom metrics published. Deployment success rates, package sizes, and deployment durations are not tracked. |
| **Gap** | No business metrics — deployment operations are not measured or tracked. |
| **Recommendation** | Consider publishing anonymized deployment telemetry (success/failure rate, duration, package size) to inform tool improvement priorities. Opt-in with clear disclosure. |
| **Evidence** | No `cloudwatch.put_metric_data` calls in the codebase. No telemetry collection. |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting configured — no deployed service to monitor. |
| **Gap** | No alerting — no production service to alert on. |
| **Recommendation** | Not applicable for a CLI tool. If deployment telemetry is added (see OPS-Q3), alerting on failure-rate spikes would become valuable. |
| **Evidence** | No CloudWatch alarms, no PagerDuty/OpsGenie integration. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | No deployed workload found in this repo (surface-gated: has_deployed_workload=false). Deployment strategy cannot be assessed from CLI source alone. Zappa is distributed as a PyPI package; GitHub Actions CD publishes to PyPI via OIDC trusted publisher, but this is package publishing, not service deployment. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `.github/workflows/cd.yml` publishes to PyPI. No ECS, EKS, Lambda, or deployment orchestration for a running service. |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Comprehensive test suite. 36+ test files in `tests/` directory with extensive mocking. pytest runs across Python 3.9-3.14 matrix in CI. Coverage reported via Coveralls. Integration-style tests with placebo AWS mocks cover deployment operations, CloudFormation template generation, IAM role creation, and Lambda lifecycle. |
| **Gap** | No gap — strong test coverage with CI integration. |
| **Recommendation** | No action needed. Consider adding contract tests for the zappa_settings.json schema if it evolves. |
| **Evidence** | `tests/` directory with 36+ test files. `.github/workflows/ci.yml` runs pytest on every push/PR. `Makefile` test target. |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, automated remediation, or structured incident workflows. Troubleshooting is ad hoc through GitHub Issues. |
| **Gap** | No runbooks or incident response automation. |
| **Recommendation** | Add structured troubleshooting guides for common deployment failures (CloudFormation rollback, Lambda size limits, IAM permission errors) to docs/. Convert to machine-readable form for future agent consumption. |
| **Evidence** | No runbook files, no SSM Automation documents, no self-healing patterns in the repo. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership defined. No CODEOWNERS for monitoring assets, no dashboards, no team-attributed alarms. |
| **Gap** | No observability ownership — no production service with monitoring needs. |
| **Recommendation** | Not applicable for a CLI tool. If Zappa were deployed as a hosted service, define CODEOWNERS for observability assets and named alarm owners. |
| **Evidence** | No `.github/CODEOWNERS` file. No dashboards or observability configuration in the repo. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging governance for own infrastructure (none exists). Zappa supports user-configurable tags for user-deployed resources via `zappa_settings.json` but has no tagged AWS resources of its own. |
| **Gap** | No tagging governance — no AWS resources owned by this repo. |
| **Recommendation** | No action needed for the tool itself. Document tagging best practices for users configuring `zappa_settings.json` tags (cost allocation, ownership, environment). |
| **Evidence** | No `default_tags` in any IaC. No tagged AWS resources owned by this repo. zappa_settings schema supports user-provided `tags` dict. |

---

## Learning Materials

Learning resources for the two triggered pathways:

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to Cloud Native** | [Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |
| **Move to Modern DevOps** | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `setup.py` | INF-Q1, INF-Q6, SEC-Q3, APP-Q1 | Package metadata; console_scripts entry point defines CLI, not HTTP API |
| `zappa/core.py` | APP-Q2, APP-Q6, DATA-Q1, DATA-Q2, SEC-Q4 | 3,866 LOC god class containing all AWS service interactions |
| `zappa/cli.py` | APP-Q2, APP-Q5 | 3,655 LOC CLI command handler; directly instantiates Zappa core class |
| `zappa/handler.py` | APP-Q2 | 1,003 LOC Lambda runtime handler for user apps — extraction candidate |
| `zappa/utilities.py` | APP-Q2 | 1,049 LOC shared helper module |
| `zappa/asynchronous.py` | INF-Q4 | Async task dispatch for user-deployed apps, not Zappa's own execution |
| `zappa/__init__.py` | APP-Q1 | Defines SUPPORTED_VERSIONS Python 3.9–3.14 |
| `Pipfile` | APP-Q1, OPS-Q1 | Python dependency manifest; modern boto3, black, pytest |
| `.github/workflows/ci.yml` | INF-Q11, SEC-Q6, SEC-Q7, OPS-Q6 | Full CI pipeline: pytest across Python 3.9-3.14, flake8, black, isort, coveralls |
| `.github/workflows/cd.yml` | INF-Q11, SEC-Q5, OPS-Q5 | Manual CD pipeline; PyPI publish via OIDC trusted publisher |
| `.github/workflows/maintenance.yml` | INF-Q11 | Maintenance workflow |
| `test_settings.json` | APP-Q5, DATA-Q1 | Sample zappa_settings.json — no schema version field |
| `tests/` | OPS-Q6 | 36+ test files with placebo AWS mocks |
| `Makefile` | INF-Q11, OPS-Q6 | test and lint targets |
| `docs/` | Quick Agent Wins (RAG) | Documentation corpus for knowledge agent |
| `CHANGELOG.md` | Quick Agent Wins (RAG) | Release history for knowledge agent corpus |
| `README.md` | Quick Agent Wins (RAG), SEC-Q4 | Extensive settings reference and usage guide |
