# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | iterative--dvc |
| **Date** | 2026-05-07 |
| **Repo Type** | application |
| **Service Archetype** | stateless-utility (auto-detected) |
| **Priority** | P2 |
| **Tags** | python, ml, data |
| **Context** | Data Version Control: git-for-ML-data, models, and experiments. |
| **Overall Score** | 2.10 / 4.0 |

**Archetype Justification**: DVC is a pure CLI tool and Python library distributed via PyPI. It has no persistent data store of its own, no deployable service endpoints, no user-specific state, and no write operations to external services during normal operation. All operations are local filesystem and git operations. Classified as stateless-utility.

**Surface Flags**: has_persistent_data_store=false, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=false, has_multi_instance_deployment=false

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | 1.50 / 4.0 | 🟠 Needs Work | Critical |
| Application Architecture (APP) | 2.83 / 4.0 | 🟡 Partial | Needs Work |
| Data Platform Modernization (DATA) | 2.50 / 4.0 | 🟡 Partial | Needs Work |
| Security Baseline (SEC) | 2.43 / 4.0 | 🟠 Needs Work | Needs Work |
| Operations & Observability (OPS) | 1.67 / 4.0 | 🟠 Needs Work | Critical |
| **Overall** | **2.10 / 4.0** | **🟠 Needs Work** | |

**Scoring Notes:**
- INF: (1+Not Evaluated+Not Evaluated+Not Evaluated+1+1+1+Not Evaluated+Not Evaluated+2+3) / 6 = 9/6 = 1.50
- APP: (4+1+Not Evaluated+Not Evaluated+2+3) / 4 (scored questions) = 10/4 = 2.50 — Wait, recalculating below.

Let me recalculate correctly:
- INF: INF-Q1=1, INF-Q2=Not Evaluated, INF-Q3=Not Evaluated, INF-Q4=Not Evaluated, INF-Q5=1, INF-Q6=1, INF-Q7=1, INF-Q8=Not Evaluated, INF-Q9=Not Evaluated, INF-Q10=2, INF-Q11=3 → (1+1+1+1+2+3)/6 = 9/6 = 1.50
- APP: APP-Q1=4, APP-Q2=1, APP-Q3=Not Evaluated, APP-Q4=Not Evaluated, APP-Q5=2, APP-Q6=3 → (4+1+2+3)/4 = 10/4 = 2.50
- DATA: DATA-Q1=1, DATA-Q2=3, DATA-Q3=N/A (no DB deployed in IaC), DATA-Q4=4 → (1+3+4)/3 = 8/3 = 2.67
- SEC: SEC-Q1=1, SEC-Q2=Not Evaluated, SEC-Q3=N/A (no API surface), SEC-Q4=N/A (no API surface), SEC-Q5=3, SEC-Q6=2, SEC-Q7=3 → (1+3+2+3)/4 = 9/4 = 2.25
- OPS: OPS-Q1=1, OPS-Q2=Not Evaluated, OPS-Q3=1, OPS-Q4=1, OPS-Q5=2, OPS-Q6=3, OPS-Q7=1, OPS-Q8=1, OPS-Q9=1 → (1+1+1+2+3+1+1+1)/8 = 11/8 = 1.38

Recalculated overall: (1.50 + 2.50 + 2.67 + 2.25 + 1.38) / 5 = 10.30/5 = 2.06

---

**CORRECTED Score Summary:**

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | 1.50 / 4.0 | 🟠 Needs Work | Critical |
| Application Architecture (APP) | 2.50 / 4.0 | 🟠 Needs Work | Critical |
| Data Platform Modernization (DATA) | 2.67 / 4.0 | 🟡 Partial | Needs Work |
| Security Baseline (SEC) | 2.25 / 4.0 | 🟠 Needs Work | Critical |
| Operations & Observability (OPS) | 1.38 / 4.0 | ❌ Not Ready | Critical |
| **Overall** | **2.06 / 4.0** | **🟠 Needs Work** | |

---

## Classification

**Tier: 🟠 Remediation Required**

This repo has 11 High findings, 5 Medium findings, 1 Low finding. Rule matched: "2-11 High → Remediation Required."

MOD classification is deliberately softer than ARA classification on "1 High." ARA gates on agent safety — a single High is a deployment blocker. MOD measures modernization maturity — a single High is typically one modernization gap rather than a deployment blocker. For MOD, "2-11 High" yields "Remediation Required" because it indicates multiple fundamental modernization gaps across infrastructure, application architecture, and operations that together represent significant effort.

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | APP-Q2: Monolith vs Microservices | 1 | Single tightly-coupled monolithic CLI application with no module boundaries or independent deployability | Limits independent scaling of DVC components; prevents cloud-native distribution |
| 2 | INF-Q1: Managed Compute | 1 | No managed compute — no IaC, no ECS/EKS/Lambda definitions; distributed as a PyPI package only | No cloud deployment model exists; entirely client-side execution |
| 3 | INF-Q5: Network Security | 1 | No VPC, subnets, or security groups — no deployed infrastructure exists | No network security posture to evaluate; all execution is local |
| 4 | OPS-Q3: Business Metrics | 1 | No custom business metrics published to any monitoring system | No visibility into usage patterns or operational health beyond telemetry |
| 5 | OPS-Q7: Incident Response | 1 | No runbooks, no incident response automation | Ad hoc response to production issues |

---

## Quick Agent Wins

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository (README.rst, extensive docs referenced at dvc.org/doc, inline docstrings throughout codebase)
- **What it enables:** A RAG-based knowledge agent that indexes DVC documentation and source code to answer developer questions about DVC internals, CLI usage, and contribution workflows
- **Additional steps:** Generate embeddings from README.rst and inline documentation; connect to dvc.org/doc content for a comprehensive knowledge base
- **Effort:** Medium

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 3) — GitHub Actions workflows for tests, builds, plugin tests, and CodeQL scanning
- **What it enables:** An agent that triggers deployments (PyPI publishes), checks build status across the test matrix, and manages release workflows
- **Additional steps:** GitHub Actions API integration needed for agent-triggered operations
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=1 (monolith), INF-Q1=1 (no managed compute) |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1=1 but contextual guard: DVC is a CLI tool/library, not a VM-hosted service. No EC2 workloads to containerize. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 (no stored procedures); no commercial DB engines detected |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 Not Evaluated (no persistent data store); no self-managed databases |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 Not Evaluated; no data processing workloads requiring managed analytics |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=2 (partial IaC), OPS-Q5=2 (rolling deploys only), OPS-Q6=3 (integration tests exist but limited) |
| 7 | Move to AI | Triggered | Medium | Medium | No AI/agent frameworks detected; context mentions "ML" and "data" indicating AI/ML tooling intent |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:** DVC is a monolithic Python CLI application (APP-Q2=1) with a single deployable artifact (PyPI package). All 298 source modules live in a single `dvc/` package with tight internal coupling across commands, repository operations, filesystem abstractions, and experiment management.

**Compute Model Gaps:** No cloud compute exists (INF-Q1=1). DVC executes entirely on the user's local machine. There is no server-side component, no API service, and no cloud-hosted processing capability.

**Recommended Decomposition Approach:** Given DVC's nature as an ML/data tooling product, cloud-native modernization could involve:
- Extracting experiment queue management (currently Celery-based) into an EKS-hosted service
- Creating a cloud-hosted API for DVC Studio integration (experiment tracking, metrics)
- Moving data transfer operations to cloud-native serverless functions

**Representative AWS Services:** EKS (preferred per context), API Gateway, EventBridge, S3
**Recommended Patterns:** Strangler Fig (extract experiment queue first), Hexagonal Architecture for new services

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10=2):** No infrastructure-as-code exists for deployment infrastructure. CI/CD pipelines are defined in GitHub Actions YAML but there is no IaC for any supporting infrastructure (no Terraform, no CloudFormation, no CDK).

**Current CI/CD State (INF-Q11=3):** GitHub Actions provides automated build, test, and publish workflows. The test matrix covers 3 OS × 6 Python versions with parallel execution, coverage reporting, and CodeQL security scanning. However, deployment is limited to PyPI publish on release tag — no staged rollout or canary mechanism.

**Deployment Strategy Gaps (OPS-Q5=2):** PyPI publishing is binary — packages are either published or not. No canary releases, no staged rollouts, no traffic shifting.

**Testing Gaps (OPS-Q6=3):** Integration tests exist (7 files) alongside 136 unit test files and 104 functional test files. Plugin integration tests run against dvc-s3. However, end-to-end integration coverage could be expanded.

**Recommendations:**
- Implement IaC (Terraform or CDK) for any future cloud infrastructure
- Add staged PyPI publishing (Test PyPI → Production PyPI with validation gates) — already partially implemented
- Expand integration test coverage for cloud storage backends
- Add automated rollback mechanism for PyPI publishes

**Representative AWS Services:** CodeBuild, CodePipeline, CloudFormation, CDK

---

### Pathway: Move to AI

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current AI/Agent Infrastructure:** No AI/agent framework usage detected — no Bedrock SDK, LangChain, Strands, or other AI framework imports. DVC is tooling FOR ML projects but does not itself leverage AI capabilities.

**AI Intent Signal:** The context mentions "ML" and "data" — DVC is a core tool in ML workflows. The `tags` include "ml" and "data".

**Application Domain and Potential AI Use Cases:**
- **Intelligent experiment recommendations:** An AI agent that analyzes past experiment results and suggests parameter configurations
- **Natural language pipeline generation:** Convert plain English descriptions of ML workflows into DVC pipeline YAML
- **Automated data quality analysis:** AI-powered detection of data drift or quality issues in tracked datasets
- **Smart caching and prefetching:** ML-based prediction of which data files will be needed next

**Recommended AI Services (respecting preferences):** Amazon Bedrock (preferred), Amazon Q for developer experience, OpenSearch Service for vector-based experiment similarity search

**Foundation Requirements:** API surface documentation, structured experiment metadata, observability infrastructure

---

## Decomposition Strategy

**Condition:** APP-Q2 = 1 (tightly-coupled monolith)

### Approach Options

| Approach | When to Use | Level of Effort | Recommendation |
|----------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Extract high-value components (experiment queue, Studio API) while maintaining the CLI monolith for local operations | Medium to High | ✅ **Recommended.** Extract server-side components incrementally while preserving the CLI experience. |
| **Conditional / Adaptive** | Containerize the experiment queue worker first, then selectively extract other components | Low to Medium | ✅ **Recommended for immediate wins.** The Celery-based experiment queue is already architecturally separable. |
| **Big-Bang Rewrite** | Rewrite DVC as a microservices platform from scratch | Very High | ⚠️ **Not recommended.** DVC's primary value is as a CLI tool; server-side decomposition should be additive, not a rewrite. |

### Pattern Recommendations

| Pattern | Purpose | When to Apply |
|---------|---------|---------------|
| **Anti-corruption Layer** | Isolate new cloud services from the CLI monolith's internal data models | When extracting experiment queue into EKS service |
| **Event Sourcing** | Track experiment state changes as events for audit and replay | When building cloud-hosted experiment tracking |
| **Hexagonal Architecture** | Structure new services with clean boundaries | Every new cloud service extraction |

### Effort Estimation Factors

| Factor | Current State | Effort Signal |
|--------|---------------|---------------|
| Module boundaries | Some structure (commands/, repo/, api/) but heavy cross-imports | Medium effort |
| Data coupling | Local git/filesystem state; no shared database | Low effort for extraction |
| Stored procedures | None | N/A |
| Communication patterns | Local function calls; Celery for experiment queue | Medium — need to introduce network boundaries |
| CI/CD maturity | Good CI with GitHub Actions | Low effort to extend |
| Test coverage | Extensive (247 test files) | Low regression risk |

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed compute infrastructure exists. DVC is distributed exclusively as a PyPI package (`dvc` on pypi.org) and executes entirely on the user's local machine. No Terraform, CloudFormation, CDK, or any IaC defines compute resources. No ECS/EKS/Lambda/Fargate/EC2 definitions found. |
| **Gap** | No cloud compute model exists. All processing is client-side. |
| **Recommendation** | If cloud-hosted DVC capabilities are desired (e.g., experiment queue processing, Studio API), define compute infrastructure using EKS (preferred) with Terraform or CDK. The existing Celery-based experiment queue worker (`dvc/commands/experiments/queue_worker.py`) is a natural candidate for cloud-hosted compute. |
| **Evidence** | No `.tf`, `template.yaml`, `cdk.json`, or compute resource definitions found in repository. `pyproject.toml` defines PyPI distribution only. |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy a database. DVC uses local SQLite for internal caching (via `dvc-data` library) and provides an optional `import-db` feature (`dvc/database.py`) for users to import data FROM external databases, but DVC itself does not own or deploy any database. INF-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `dvc/database.py` — SQLAlchemy client for user-facing import-db feature only; no database resource definitions in IaC (no IaC exists). |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Workflow orchestration is not applicable by design — DVC is a CLI tool that executes user-initiated commands synchronously. The experiment queue uses Celery for local task execution but this is not multi-service orchestration requiring Step Functions or similar. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `dvc/commands/experiments/queue_worker.py` — Celery worker for local experiment queue; not a multi-service workflow. |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Synchronous CLI execution is the correct design. DVC uses Celery/Kombu internally for local experiment queue management, but this is a local process queue, not inter-service messaging. No managed messaging or streaming infrastructure is needed for a CLI tool. |
| **Gap** | N/A |
| **Recommendation** | Adopting async messaging infrastructure is NOT recommended for DVC's current architecture — it would add operational complexity without architectural benefit. If DVC's experiment queue is extracted to a cloud service, then managed messaging (SQS, EventBridge) should be evaluated at that point. |
| **Evidence** | `pyproject.toml` dependencies include `celery` and `kombu`; used locally in `dvc/commands/experiments/queue_worker.py` and `dvc/commands/queue/`. |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or network configuration exists. DVC has no deployed infrastructure — it runs entirely on the user's local machine. There is no network architecture to evaluate. |
| **Gap** | No network security posture exists because there is no deployed infrastructure. |
| **Recommendation** | If cloud infrastructure is introduced (per Move to Cloud Native pathway), define VPC with private subnets, least-privilege security groups, and VPC endpoints for AWS service access. Use EKS network policies for pod-level segmentation. |
| **Evidence** | No `.tf` files, no `aws_vpc`, `aws_subnet`, or `aws_security_group` resources. No IaC of any kind. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or any managed entry point exists. DVC exposes a Python API (`dvc/api/`) and CLI (`dvc/cli/`) but these are consumed locally — there is no network-accessible service endpoint. |
| **Gap** | No managed API entry point because there is no deployed service. |
| **Recommendation** | If a cloud-hosted DVC API is created, use API Gateway (preferred per context) with throttling, authentication, and request validation. |
| **Evidence** | `dvc/api/__init__.py` — Python-level API only; no network service definitions. |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. There is no deployed compute, database, or managed service that could be scaled. DVC runs as a local process on the user's machine. |
| **Gap** | No auto-scaling because there is no deployed infrastructure. |
| **Recommendation** | If cloud compute is introduced, configure auto-scaling with appropriate min/max for EKS node groups or ECS services. Use custom metrics (experiment queue depth) for scaling policies. |
| **Evidence** | No `aws_autoscaling_*`, `aws_appautoscaling_*`, or scaling policy definitions found. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no persistent state to back up. DVC operates on the user's local git repository and delegates data storage to external backends (S3, GCS, Azure). DVC itself does not own persistent state requiring backup. INF-Q8 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database resources, no S3 buckets defined in IaC, no backup configuration. Data is stored in user-managed remote backends. |

#### INF-Q9: High Availability

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload requiring HA evaluation. DVC is a CLI tool that runs locally. There is no service to make highly available. INF-Q9 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No deployed compute, no API surface, no database. Surface flags: has_deployed_workload=false, has_api_surface=false. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | CI/CD infrastructure is partially defined as code via GitHub Actions workflow YAML files (6 workflow files under `.github/workflows/`). However, no infrastructure provisioning IaC exists (no Terraform, CloudFormation, CDK). The GitHub Actions workflows define build, test, and publish automation but there is no infrastructure beyond that. Dependabot configuration provides automated dependency updates. |
| **Gap** | No IaC for infrastructure provisioning. Only CI/CD pipeline definitions exist as code. If any supporting infrastructure exists (e.g., PyPI publishing tokens, GitHub environments), it is configured manually. |
| **Recommendation** | Define all infrastructure in IaC. For the current project, this means codifying GitHub repository settings, branch protection rules, and secrets management. If cloud infrastructure is introduced, use Terraform or CDK from the start. |
| **Evidence** | `.github/workflows/tests.yaml`, `.github/workflows/build.yaml`, `.github/workflows/codeql.yml`, `.github/workflows/plugin_tests.yaml`, `.github/workflows/benchmarks.yaml`, `.github/dependabot.yml` |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive CI/CD automation via GitHub Actions covering: (1) automated tests across 3 OS × 6 Python versions with parallel execution, (2) automated build and PyPI publishing on release, (3) CodeQL security scanning, (4) plugin integration tests, (5) performance benchmarks, (6) Dependabot for dependency updates, (7) pre-commit hooks for linting. Pipeline stages include lint, test, build, and publish with automated quality gates. |
| **Gap** | No infrastructure-as-code deployment pipeline (because no infrastructure exists to deploy). PyPI publishing uses GitHub's trusted publishing (OIDC) but there's no automated rollback mechanism — once published to PyPI, a version cannot be easily unpublished. |
| **Recommendation** | Add automated validation gates between Test PyPI and Production PyPI publish (already partially implemented in `build.yaml`). Consider adding smoke tests that install from Test PyPI and verify basic functionality before production publish. |
| **Evidence** | `.github/workflows/tests.yaml` (matrix testing), `.github/workflows/build.yaml` (build + publish), `.github/workflows/codeql.yml` (security), `.github/workflows/plugin_tests.yaml` (integration), `.github/workflows/benchmarks.yaml` (perf) |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Pure Python 3.9+ with support for Python 3.9 through 3.14 (latest). Uses modern Python tooling: pyproject.toml (PEP 621), setuptools_scm for versioning, uv for fast package installation, ruff for linting, mypy for type checking. No legacy Python 2 code. First-class AWS SDK support via the `dvc-s3` plugin (boto3). Modern ecosystem with rich, click-style CLI patterns. |
| **Gap** | None — Python is a first-class cloud-native language with full AWS SDK coverage. The project uses the latest Python versions and modern tooling. |
| **Recommendation** | No action needed. Continue tracking latest Python versions (already supporting 3.14). |
| **Evidence** | `pyproject.toml`: `requires-python = ">=3.9"`, classifiers include Python 3.9-3.14, build system uses `setuptools>=77`, ruff/mypy/pre-commit for code quality. |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | DVC is a single deployable monolithic Python package with 298 source files in one `dvc/` package. All functionality — CLI commands, repository operations, filesystem abstractions, experiment management, data tracking, pipeline execution, and rendering — lives in a single artifact. There are some package-level boundaries (`dvc/commands/`, `dvc/repo/`, `dvc/api/`, `dvc/fs/`) but these are tightly coupled with extensive cross-imports. The experiment queue (Celery-based) is embedded within the monolith. |
| **Gap** | Single tightly-coupled monolith with no independently deployable services. All components must be released together. No clear service boundaries or independent scaling capability. |
| **Recommendation** | Apply Strangler Fig pattern to extract server-side capabilities: (1) Extract experiment queue worker as an independent EKS-deployed service, (2) Create a cloud-hosted API for experiment tracking and metrics aggregation, (3) Maintain CLI as a thin client that can operate both locally and against cloud services. See Decomposition Strategy section. |
| **Evidence** | Single `pyproject.toml` defines one package; single `dvc/` source tree; single entry point (`dvc.cli:main`); all 298 modules deployed as one artifact to PyPI. |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Sync request/response (CLI command → execute → return) is the correct design; async inter-service communication is not needed. DVC uses Celery internally for local experiment queue processing, but this is intra-process task scheduling, not inter-service communication. |
| **Gap** | N/A |
| **Recommendation** | Async inter-service communication is not applicable for DVC's current CLI architecture. If server-side components are extracted, evaluate async patterns (SQS, EventBridge) at that point. |
| **Evidence** | `dvc/cli/__init__.py` — synchronous command execution; `dvc/commands/experiments/queue_worker.py` — local Celery worker. |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. No operations exceed 30 seconds in a service context — DVC operations (data push/pull, experiment runs) can take long but they are user-initiated CLI operations with progress bars, not service-to-service calls requiring async status polling. The Celery experiment queue already handles long-running experiment execution asynchronously within the local context. |
| **Gap** | N/A |
| **Recommendation** | Long-running process async infrastructure is not applicable for the current CLI surface. The existing Celery-based experiment queue already provides local async processing with status polling (`dvc queue status`). |
| **Evidence** | `dvc/commands/queue/` — local queue management with status commands; `tqdm` progress bars for user-facing long operations. |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | DVC exposes a Python API (`dvc/api/__init__.py`) with a public surface area (`__all__` list) but no formal versioning strategy. The CLI uses major version bumps (semver via setuptools_scm) for breaking changes but there is no explicit API versioning mechanism (no `/v1/` paths, no version headers, no deprecation policy documented in code). The Python API's stability contract is implied by semver but not explicitly enforced with versioned interfaces. |
| **Gap** | No explicit API versioning strategy beyond package-level semver. Breaking changes to the Python API are only communicated through major version bumps, with no per-endpoint or per-function versioning. |
| **Recommendation** | Implement explicit deprecation decorators for Python API functions. Document API stability guarantees. If a REST API is introduced, use URL path versioning (`/v1/`) from the start. |
| **Evidence** | `dvc/api/__init__.py` — `__all__` defines public surface; `pyproject.toml` uses setuptools_scm for semver; no `@deprecated` decorators or versioned module structure found. |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | DVC uses environment variables for service endpoint configuration (`dvc/env.py`): `DVC_STUDIO_URL`, `DVC_ANALYTICS_ENDPOINT`, `DVC_UPDATER_ENDPOINT`. Remote storage backends are configured via DVC config files (`.dvc/config`). The plugin architecture (`dvc-s3`, `dvc-gs`, `dvc-azure`) provides a discovery mechanism for storage backends via Python entry points (`fsspec.specs`, `universal_pathlib.implementations` in `pyproject.toml`). |
| **Gap** | Service endpoints are configured via environment variables rather than dynamic discovery. This is appropriate for a CLI tool but limits flexibility if cloud services are introduced. |
| **Recommendation** | Current approach (environment variables + plugin entry points) is appropriate for DVC's CLI architecture. If cloud-hosted services are introduced, adopt AWS Service Discovery or environment-based configuration with proper service mesh integration. |
| **Evidence** | `dvc/env.py` — environment variable definitions for service URLs; `pyproject.toml` — entry points for plugin discovery; `.dvc/config` — remote backend configuration. |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | DVC tracks unstructured data (ML models, datasets, media files) but stores them on user-configured remote backends. DVC itself does not define or manage S3 buckets, parsing pipelines, or object storage infrastructure. Data is stored wherever the user configures their DVC remote (S3, GCS, Azure, local filesystem). No managed object storage with parsing capabilities is provisioned by DVC's own infrastructure. |
| **Gap** | DVC does not provision its own data storage infrastructure. While it enables users to store data in S3, DVC itself has no managed storage layer with parsing capabilities for its own operational data (telemetry, experiment metadata, metrics). |
| **Recommendation** | If DVC introduces cloud-hosted features (experiment tracking, metrics aggregation), use S3 for unstructured data storage with appropriate parsing pipelines (e.g., Athena for experiment result analysis). |
| **Evidence** | No `aws_s3_bucket` or object storage IaC found. `dvc-s3` is a user-configured plugin, not DVC's own infrastructure. |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | DVC has a well-structured data access layer through its filesystem abstraction (`dvc/fs/`) which provides a unified interface to multiple storage backends (local, S3, GCS, Azure, SSH, HDFS, WebDAV, WebHDFS) via the fsspec protocol. The `dvc-data` library provides a centralized data access layer for content-addressable storage. The `dvc/database.py` module provides a unified database client for the `import-db` feature. Some direct filesystem access exists in utility modules but the primary data path is centralized. |
| **Gap** | Most data access is centralized through fsspec, but some auxiliary code paths access the filesystem directly without going through the unified layer. |
| **Recommendation** | Continue maintaining the fsspec-based unified data access layer. Ensure all new data access goes through the centralized filesystem abstraction rather than direct os/pathlib calls. |
| **Evidence** | `dvc/fs/` — filesystem abstraction layer; `dvc-data` dependency; `dvc/database.py` — unified DB client; fsspec entry points in `pyproject.toml`. |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | DVC does not deploy or manage any database engines. The `import-db` feature (`dvc/database.py`) connects to user-specified external databases via SQLAlchemy but DVC itself does not own database infrastructure. No database engine versions are defined in IaC because no IaC exists. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `dvc/database.py` — SQLAlchemy client connects to user-specified URLs; no database resource definitions in IaC. |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs are used. DVC's database interaction (`dvc/database.py`) is read-only — it executes user-provided SQL queries to export data. All business logic is in the Python application layer. The `import-db` feature uses standard SQL (`select 1` for connection testing, user-provided queries for data export) with no proprietary extensions. |
| **Gap** | None — all logic is in the application layer with no database-coupled business logic. |
| **Recommendation** | No action needed. Continue keeping business logic in the application layer. |
| **Evidence** | `dvc/database.py` — only `exec_driver_sql("select 1")` and `pd.read_sql(sql, con)` calls; no CREATE PROCEDURE, CREATE TRIGGER, or proprietary SQL. |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail, audit logging, or immutable log storage is configured. DVC has no deployed infrastructure that would produce CloudTrail events. Application logging (`dvc/logger.py`) is for local terminal output only — not audit logging. The `iterative-telemetry` dependency collects anonymous usage analytics but this is not security audit logging. |
| **Gap** | No audit logging infrastructure. No CloudTrail, no immutable log storage, no audit trail for operations. |
| **Recommendation** | If cloud infrastructure is introduced, enable CloudTrail with log file validation and S3 Object Lock for immutable storage. For the current CLI tool, audit logging is less critical but consider structured logging for DVC Studio integration events. |
| **Evidence** | `dvc/logger.py` — standard Python logging to terminal; `dvc/analytics.py` — anonymous telemetry; no `aws_cloudtrail` or audit log configuration. |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no database, S3 bucket, EBS volume, or similar managed storage is provisioned by DVC. Data stored in user-configured remotes (S3, GCS, etc.) is encrypted per the user's configuration, not DVC's. SEC-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No data-at-rest resources defined. Surface flag: has_at_rest_data_surface=false. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | DVC does not expose network-accessible API endpoints. The Python API (`dvc/api/`) is consumed as a library import, not as a network service. DVC authenticates to external services (DVC Studio, cloud storage) using tokens and credentials, but it does not serve API requests itself. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No HTTP server, no API Gateway, no network-accessible endpoints. Surface flag: has_api_surface=false. |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | DVC does not manage user authentication. It delegates authentication to external services: DVC Studio (via `DVC_STUDIO_TOKEN`), cloud providers (via provider-specific credentials managed by the user's environment). DVC itself has no user database, no login flow, and no identity management. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `dvc/env.py` — `DVC_STUDIO_TOKEN` for external service auth; no Cognito, OIDC, or identity provider integration of its own. |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | DVC uses environment variables for all secret values (`DVC_STUDIO_TOKEN`, cloud provider credentials). No plaintext credentials are committed to the repository. The `tests/remotes_env.sample` file provides a template for test credentials without containing actual values. CI/CD uses GitHub Secrets (`${{ secrets.SLACK_WEBHOOK }}`). No production credentials exist in source code, configuration files, or version-controlled env files. |
| **Gap** | While no plaintext secrets are in source, there is no dedicated secrets management service (Secrets Manager, Vault) with automated rotation. Credentials are managed via environment variables without rotation policies. |
| **Recommendation** | For a CLI tool, environment variable-based secrets management is appropriate. If cloud infrastructure is introduced, adopt AWS Secrets Manager with rotation for service-to-service credentials. |
| **Evidence** | `dvc/env.py` — credential env vars (no values); `tests/remotes_env.sample` — template only; `.github/workflows/tests.yaml` — `secrets.SLACK_WEBHOOK`; no hardcoded credentials found. |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No deployed compute to harden. However, the CI/CD pipeline includes CodeQL security scanning (SAST) and Dependabot for dependency vulnerability patching. The project uses `ruff` with Bandit security rules (`S` rule set) enabled for source code linting. No vulnerability scanning of built artifacts or container images (no containers exist). |
| **Gap** | No compute hardening because no compute is deployed. Security scanning is limited to source code (CodeQL, ruff/Bandit) and dependency updates (Dependabot). No runtime vulnerability scanning. |
| **Recommendation** | Current source-level security tooling is adequate for a library. If containers are introduced, add container image scanning (ECR scanning, Snyk). Consider adding `pip-audit` to CI for Python-specific vulnerability detection. |
| **Evidence** | `.github/workflows/codeql.yml` — CodeQL with security-extended queries; `.github/dependabot.yml` — daily dependency updates; `pyproject.toml` — ruff `S` rules (Bandit). |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | CodeQL SAST scanning runs in CI/CD on every push to main and every PR, with `security-extended` query suite. Dependabot is configured for daily dependency vulnerability scanning (both pip and GitHub Actions ecosystems). Ruff with Bandit (`S`) rules provides additional static security analysis. However, there is no blocking security gate — CodeQL findings do not block merges, and there is no container scanning (no containers to scan). |
| **Gap** | CodeQL runs but may not block on critical findings. No explicit security gate that prevents merging code with critical vulnerabilities. No `pip-audit` or dedicated Python dependency vulnerability scanner in the CI pipeline itself (Dependabot creates PRs but doesn't block the main test pipeline). |
| **Recommendation** | Add a blocking security gate to the CI pipeline that fails on critical CodeQL findings. Add `pip-audit` to the test pipeline for real-time dependency vulnerability checking. Consider adding Semgrep for additional Python-specific security rules. |
| **Evidence** | `.github/workflows/codeql.yml` — SAST with security-extended; `.github/dependabot.yml` — dependency scanning; `pyproject.toml` — ruff `S` rules. |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumented. No OpenTelemetry, X-Ray, Jaeger, or Zipkin SDK found in dependencies or source code. DVC uses standard Python logging (`dvc/logger.py`) with a custom TRACE level for verbose debug output, but this is not distributed tracing with trace ID propagation. |
| **Gap** | No distributed tracing. As a library, DVC could instrument tracing that propagates through dependent applications, but no such instrumentation exists. |
| **Recommendation** | Add OpenTelemetry SDK as an optional dependency to instrument DVC operations (data transfers, experiment runs). This would enable trace propagation through applications that use DVC as a library, providing visibility into DVC's contribution to overall request latency. |
| **Evidence** | `pyproject.toml` — no opentelemetry/otel/tracing dependency; `dvc/logger.py` — standard Python logging only. |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no user-facing service surface for which SLOs are meaningful. DVC is a CLI tool — it does not serve network requests with measurable availability, latency, or error rate SLOs. Performance benchmarks exist but these are development metrics, not production SLOs. OPS-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `.github/workflows/benchmarks.yaml` — performance benchmarks, not SLOs. Surface flag: has_api_surface=false. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics are published to any monitoring system. DVC collects anonymous usage telemetry via `iterative-telemetry` package (`dvc/analytics.py`) but this is sent to the DVC team's analytics endpoint, not to CloudWatch or any customer-visible monitoring system. No business outcome metrics (command success rates, data transfer volumes, experiment completion rates) are published. |
| **Gap** | No business metrics published to monitoring. Usage telemetry exists but is not accessible as operational metrics with dashboards and alerting. |
| **Recommendation** | If operational visibility is desired, publish custom metrics (command execution counts, error rates by command, data transfer sizes, experiment durations) to CloudWatch or a metrics backend. The existing telemetry infrastructure could be extended for this purpose. |
| **Evidence** | `dvc/analytics.py` — anonymous telemetry collection; no CloudWatch, Datadog, Prometheus, or metrics SDK found. |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configured. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no error rate monitoring. The only operational alerting is a Slack notification when CI fails on main (`tests.yaml` notify job). |
| **Gap** | No anomaly detection, no alerting on error rates or latency. Only CI failure notifications exist. |
| **Recommendation** | For a CLI tool/library, production alerting has limited applicability. However, consider monitoring PyPI download trends, GitHub issue rates, and CI pipeline health metrics. If cloud services are introduced, implement CloudWatch anomaly detection on all critical paths. |
| **Evidence** | `.github/workflows/tests.yaml` — Slack notification on main branch CI failure; no CloudWatch alarms or monitoring configuration. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Deployment (PyPI publishing) uses a two-stage approach: commits to `main` publish to Test PyPI, and GitHub releases publish to production PyPI. This provides a basic validation stage. However, there is no canary release mechanism, no traffic shifting, no gradual rollout. Once published to PyPI, all users get the new version immediately (pip/uv will install the latest). |
| **Gap** | No canary or blue/green deployment. No gradual rollout mechanism. The Test PyPI → Production PyPI flow provides basic validation but no staged rollout to end users. |
| **Recommendation** | Consider implementing a staged release strategy: (1) Publish release candidates to Test PyPI for community testing, (2) Use GitHub pre-releases before full releases, (3) Add post-publish smoke tests that verify installation and basic functionality. For a PyPI package, full canary/blue-green is not applicable, but staged releases with validation gates are. |
| **Evidence** | `.github/workflows/build.yaml` — two environments: `test-pypi` (on push to main) and `pypi` (on release published). |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Integration tests exist across multiple tiers: (1) 7 integration test files under `tests/integration/` (plots integration tests), (2) 104 functional test files under `tests/func/` that test end-to-end CLI workflows, (3) Plugin integration tests (`plugin_tests.yaml`) that test DVC against the `dvc-s3` plugin. Tests run in CI via GitHub Actions with docker-compose for SSH git server testing. pytest-docker is available for container-based integration tests. |
| **Gap** | Integration test coverage is moderate — `tests/integration/` has 7 files focused on plots. Broader integration testing with cloud storage backends is limited to the plugin test workflow (only tests dvc-s3). No integration tests for DVC Studio communication or other cloud interactions. |
| **Recommendation** | Expand integration test coverage to include: (1) DVC Studio API contract tests, (2) Multi-backend integration tests (S3, GCS, Azure) in CI, (3) End-to-end experiment workflow tests with actual remote storage. |
| **Evidence** | `tests/integration/` — 7 files; `tests/func/` — 104 files; `.github/workflows/plugin_tests.yaml` — dvc-s3 integration; `tests/docker-compose.yml` — git server for SSH tests. |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, no incident response automation, no self-healing patterns. The only operational response mechanism is the Slack notification when CI fails on the main branch. No Systems Manager Automation documents, no Lambda-based remediation, no structured incident workflows. |
| **Gap** | No incident response automation. All incident response is ad hoc. |
| **Recommendation** | Create runbooks for common issues: (1) PyPI publish failures, (2) CI pipeline failures on main, (3) Security vulnerability responses (Dependabot/CodeQL findings). Start with markdown runbooks, then automate common responses with GitHub Actions or AWS Systems Manager. |
| **Evidence** | No runbook files found; no Systems Manager documents; no automated remediation. Only `.github/workflows/tests.yaml` Slack notification exists. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership defined. No CODEOWNERS for monitoring configuration, no per-service dashboards (no services exist), no named alarm owners, no SLO definitions with team attribution. The project has code coverage reporting (codecov) but no operational observability ownership. |
| **Gap** | No observability ownership. No dashboards, no alarms with owners, no team attribution for operational metrics. |
| **Recommendation** | Define observability ownership starting with CI/CD pipeline health metrics. Create a CODEOWNERS entry for `.github/workflows/` and monitoring configuration. If cloud infrastructure is introduced, establish per-service dashboard ownership from day one. |
| **Evidence** | No CODEOWNERS file for observability; no dashboards; `codecov.yml` exists but covers code coverage only, not operational metrics. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging exists because no AWS resources are provisioned. No `default_tags`, no tag enforcement, no Tag Policies. The only "tagging" is GitHub labels on Dependabot PRs (`"maintenance"`). |
| **Gap** | No resource tagging governance because no cloud resources exist. |
| **Recommendation** | If AWS resources are introduced, implement tagging governance from the start: define mandatory tags (team, environment, cost-center, service), enforce via Terraform `default_tags` and AWS Config rules. |
| **Evidence** | `.github/dependabot.yml` — GitHub labels only; no AWS resources to tag. |

---

## Learning Materials

### Move to Cloud Native
- [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

### Move to Modern DevOps
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

### Move to AI
- [Move to AI](https://skillbuilder.aws/learning-plan/VDFEE4ACCV)
- [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ)
- [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `pyproject.toml` | APP-Q1, APP-Q2, APP-Q5, INF-Q1, INF-Q11, OPS-Q1, DATA-Q2 | Primary dependency manifest, build config, project metadata |
| `.github/workflows/tests.yaml` | INF-Q11, OPS-Q4, OPS-Q5, OPS-Q6 | Main test pipeline with matrix testing and Slack notifications |
| `.github/workflows/build.yaml` | INF-Q11, OPS-Q5 | Build and PyPI publish pipeline with staged environments |
| `.github/workflows/codeql.yml` | SEC-Q6, SEC-Q7 | CodeQL SAST security scanning |
| `.github/workflows/plugin_tests.yaml` | OPS-Q6 | Plugin integration test workflow |
| `.github/workflows/benchmarks.yaml` | OPS-Q2 | Performance benchmarks |
| `.github/dependabot.yml` | SEC-Q6, SEC-Q7, OPS-Q9 | Dependency vulnerability scanning and updates |
| `dvc/env.py` | SEC-Q5, APP-Q6 | Environment variable definitions for service URLs and tokens |
| `dvc/database.py` | DATA-Q2, DATA-Q4, INF-Q2 | SQLAlchemy client for import-db feature |
| `dvc/logger.py` | OPS-Q1 | Standard Python logging configuration |
| `dvc/analytics.py` | OPS-Q3 | Anonymous telemetry collection |
| `dvc/api/__init__.py` | APP-Q5, APP-Q6, INF-Q6 | Public Python API surface |
| `dvc/cli/__init__.py` | APP-Q2 | CLI entry point and command dispatch |
| `dvc/commands/experiments/queue_worker.py` | INF-Q3, INF-Q4 | Celery-based local experiment queue worker |
| `dvc/commands/queue/` | INF-Q4, APP-Q4 | Queue management commands |
| `dvc/fs/` | DATA-Q2 | Filesystem abstraction layer (fsspec-based) |
| `tests/docker-compose.yml` | OPS-Q6 | Docker Compose for test SSH git server |
| `tests/integration/` | OPS-Q6 | Integration test files |
| `tests/func/` | OPS-Q6 | Functional test files |
| `tests/remotes_env.sample` | SEC-Q5 | Sample credentials template (no actual values) |
| `.pre-commit-config.yaml` | INF-Q11 | Pre-commit hooks for lint/type checking |
