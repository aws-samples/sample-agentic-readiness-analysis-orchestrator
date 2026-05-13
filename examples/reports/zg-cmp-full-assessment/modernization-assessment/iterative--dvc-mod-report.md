# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | dvc |
| **Date** | 2026-04-29 |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | python, ml, data |
| **Context** | Data Version Control: git-for-ML-data, models, and experiments. |
| **Overall Score** | 2.08 / 4.0 |

**Archetype Justification**: DVC is a CLI tool with local persistent state (SQLite for state/index via dvc-data, file-based cache) and write operations (add, push, import, commit). No HTTP API surface or message queue consumers detected. Classified as stateful-crud (conservative default for ambiguous signals — CLI tool does not map cleanly to service archetypes).

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.27 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.33 / 4.0 | 🟠 Needs Work |
| Data Platform Modernization (DATA) | 3.25 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 2.00 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.56 / 4.0 | 🟠 Needs Work |
| **Overall** | **2.08 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q1: Managed Compute | 1 | No cloud compute infrastructure defined; DVC is distributed as a pip package with no IaC for compute resources. | Cannot leverage managed scaling, patching, or elastic capacity for any hosted DVC service deployment. |
| 2 | INF-Q5: Network Security | 1 | No VPC, security groups, or network segmentation defined. No IaC for network infrastructure. | If DVC were deployed as a service, there would be no network isolation or blast-radius containment. |
| 3 | INF-Q10: IaC Coverage | 1 | No Infrastructure as Code files found (no Terraform, CloudFormation, CDK, Helm, or Kustomize). | Infrastructure changes would be entirely manual (ClickOps), non-reproducible, and error-prone. |
| 4 | SEC-Q1: Audit Logging | 1 | No CloudTrail or equivalent audit logging configured. DVC's own telemetry (iterative-telemetry) is usage analytics, not security audit logging. | No forensic capability for security incident investigation; compliance gaps for production deployments. |
| 5 | OPS-Q1: Distributed Tracing | 1 | No distributed tracing instrumented. DVC uses Python logging with configurable levels but no OpenTelemetry or X-Ray integration. | Debugging failures across remote storage interactions is guesswork; no end-to-end visibility. |

---

<!-- SECTION: Quick Agent Wins -->
## Quick Agent Wins

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists in repo — `README.rst` provides comprehensive user documentation with CLI workflow examples, installation instructions, and architecture overview. External documentation at `https://dvc.org/doc` is referenced. `CONTRIBUTING.md` links to contribution guides.
- **What it enables:** A RAG-based knowledge agent that indexes DVC documentation (README.rst, external docs at dvc.org/doc, CLI help text) to answer developer and user questions about DVC usage, configuration, and troubleshooting.
- **Additional steps:** Index the external documentation corpus at dvc.org/doc alongside the in-repo README.rst. Consider generating structured FAQ content from GitHub Issues and Discussions.
- **Effort:** Medium — documentation exists but is split between in-repo and external sources; indexing the external corpus requires a crawl/ingest pipeline.

### CI/CD DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 4). GitHub Actions workflows provide comprehensive build, test, and publish automation across `.github/workflows/tests.yaml`, `.github/workflows/build.yaml`, `.github/workflows/codeql.yml`, `.github/workflows/plugin_tests.yaml`, and `.github/workflows/benchmarks.yaml`.
- **What it enables:** A DevOps agent that triggers test runs, checks build status, monitors PyPI publishing, and manages release workflows via GitHub Actions API.
- **Additional steps:** Expose GitHub Actions workflow dispatch API for agent invocation. Define agent-callable actions for common operations (re-run failed tests, trigger benchmark comparison, initiate release).
- **Effort:** Low — existing pipeline provides the automation surface; agent orchestrates via GitHub API.

### Data Query Agent

- **Prerequisite:** Database with clear schema (DATA-Q2 = 4). DVC has a well-structured unified data access layer via `dvc/data_cloud.py` (DataCloud class) and `dvc/fs/` filesystem abstractions providing a clean query interface for remote data stores.
- **What it enables:** A data query agent that uses natural language to interact with DVC-managed data — listing tracked files, checking remote status, querying experiment metrics via the Python API (`dvc.api`).
- **Additional steps:** Generate OpenAPI spec from the `dvc.api` Python module to enable tool discovery. Wrap key DVC Python API functions as agent-callable tools.
- **Effort:** Medium — the Python API exists (`dvc/api/__init__.py` exports `metrics_show`, `params_show`, `exp_show`, etc.) but needs wrapper/spec generation for agent consumption.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 (modular monolith with clear boundaries). Primary trigger (APP-Q2 < 3) not met. |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1 = 1 (no managed compute); no Dockerfiles found in repository. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (no stored procedures or proprietary SQL). No commercial DB engines detected. |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = 1 (no IaC-defined databases), but DVC uses only local SQLite for state — no production database to migrate. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads detected. DVC is a data versioning CLI, not a data pipeline. Contextual guard prevents trigger. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (no IaC). OPS-Q5 = 2 (rolling PyPI publish, no canary/blue-green). |
| 7 | Move to AI | Triggered | Medium | Medium | No AI/agent frameworks detected. Context contains "ML" — AI intent signal present in "git-for-ML-data". |

---

<!-- SECTION: Pathway Details -->
### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model:** DVC is distributed as a Python package via pip/conda with no cloud compute infrastructure defined. No Dockerfiles, no Kubernetes manifests, no Helm charts found. The only container artifact is `tests/docker-compose.yml` which runs a test git-server, not DVC itself.

**Container Readiness Indicators:**
- Python application with well-defined `pyproject.toml` entry point (`dvc = "dvc.cli:main"`)
- Dependencies are pip-installable with optional extras for cloud storage backends
- Configuration externalized via `.dvc/config` files and environment variables (`dvc/env.py` defines 20+ environment variables)
- No hardcoded filesystem paths that would prevent containerization

**Recommended Container Orchestration Platform:** EKS (per user preference for `eks`) for any hosted DVC service deployment (e.g., DVC Studio backend, CI/CD pipeline workers that run DVC commands).

**Representative AWS Services:** Amazon EKS, Amazon ECR, AWS Fargate (for serverless container execution)

**Migration Approach:** Lift-and-containerize — create a Dockerfile based on the existing `pyproject.toml` build system, then deploy as an EKS workload. Consider multi-stage builds to minimize image size.

**AWS Guidance:** [Containerize applications](https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/containerize-applications.html)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 1):** No Infrastructure as Code files found. If DVC or related services are deployed to AWS, all infrastructure would need to be defined manually. The repository has zero Terraform, CloudFormation, CDK, or Helm files.

**Current CI/CD State (INF-Q11 = 4):** Excellent CI/CD automation already exists via GitHub Actions — comprehensive test matrix (tests.yaml), automated build and PyPI publishing (build.yaml), SAST scanning (codeql.yml), plugin compatibility testing (plugin_tests.yaml), and performance benchmarking (benchmarks.yaml). This is a strong foundation.

**Deployment Strategy Gaps (OPS-Q5 = 2):** PyPI publishing uses a simple push-to-main → Test PyPI, release → PyPI workflow. No canary or staged rollout for the package distribution itself.

**Recommended DevOps Toolchain:**
- **IaC:** AWS CDK (Python) or Terraform for any AWS infrastructure provisioning
- **Container Registry:** Amazon ECR for container images
- **Deployment:** EKS with ArgoCD or Flux for GitOps-based deployment
- **Monitoring:** Amazon CloudWatch with EventBridge (per user preference for `eventbridge`) for operational event routing

**Representative AWS Services:** AWS CDK, Amazon ECR, AWS CodeBuild, AWS CodePipeline, Amazon CloudWatch, Amazon EventBridge

**AWS Guidance:** [DevOps on AWS](https://docs.aws.amazon.com/prescriptive-guidance/latest/strategy-devops/introduction.html)

---

### Pathway: Move to AI

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current AI/Agent Infrastructure State:** No AI/agent framework usage detected in the repository. No imports of Bedrock SDK, LangChain, Strands, OpenAI, Spring AI, HuggingFace, or SageMaker SDK. No vector database infrastructure. No RAG implementation. No agent evaluation framework.

**AI Intent Signal:** The context "Data Version Control: git-for-ML-data, models, and experiments" contains "ML", which is an AI-related signal term. DVC is inherently an ML tooling project — it manages ML data, models, and experiments.

**Application Domain and Potential AI Use Cases:**
1. **Intelligent experiment analysis** — Use Amazon Bedrock (per user preference) to analyze experiment results, suggest hyperparameter tuning strategies, and generate experiment summaries
2. **Natural language DVC operations** — An AI-powered CLI assistant that translates natural language into DVC commands
3. **Data quality assessment** — AI-powered analysis of tracked datasets for anomalies, drift detection, and quality scoring
4. **Smart pipeline optimization** — AI analysis of DVC pipeline DAGs to suggest parallelization and caching strategies

**Quick Wins:** See Quick Agent Wins section above for immediate opportunities (RAG knowledge agent, CI/CD DevOps agent, Data Query agent).

**Recommended AI Services:** Amazon Bedrock (per user preference for `bedrock`), Amazon Bedrock AgentCore for agent orchestration, Amazon Q for developer productivity

**Foundation Requirements:**
- API surface documentation (generate OpenAPI spec from `dvc.api`)
- Structured logging for agent observability (currently basic Python logging only)
- Authentication/authorization for agent-to-DVC interactions

**AWS Guidance:** [AI/ML on AWS](https://docs.aws.amazon.com/prescriptive-guidance/latest/ml-best-practices/introduction.html)

---

<!-- SECTION: Detailed Findings -->
## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No cloud compute infrastructure is defined in the repository. DVC is a CLI tool distributed via pip, conda, snap, brew, and platform-specific packages. There are no Terraform, CloudFormation, CDK, or other IaC files defining compute resources (no `aws_ecs_*`, `aws_eks_*`, `aws_lambda_*`, or `aws_instance` resources). The repository contains only Python source code, CI/CD pipelines, and configuration. |
| **Gap** | No compute infrastructure defined at all — neither managed nor self-managed. If DVC were to be deployed as a service (e.g., DVC Studio backend, pipeline worker), there is no compute foundation. |
| **Recommendation** | If deploying DVC as a service workload, define compute infrastructure using EKS (per preference) with Fargate for serverless container execution. Use AWS CDK (Python) to define compute resources alongside the existing Python codebase. |
| **Evidence** | No `.tf`, `.cfn.yaml`, `cdk.json`, `Chart.yaml`, or `Dockerfile` files found in repository root or subdirectories. `pyproject.toml` defines `dvc = "dvc.cli:main"` as the entry point (CLI distribution, not service deployment). |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC-defined database resources found. DVC uses local SQLite for state management (via `dvc-data` library — `DataIndex.open()` in `dvc/repo/__init__.py` opens `db.db`). The `dvc/database.py` module provides a generic SQLAlchemy-based database import capability (`import-db` command) for connecting to user-specified external databases, but does not define or manage database infrastructure itself. |
| **Gap** | No managed database infrastructure. Local SQLite is used for state, which is appropriate for a CLI tool but would not scale for a service deployment. |
| **Recommendation** | If evolving DVC into a service with shared state, adopt Aurora (per preference) or DynamoDB (per preference) for persistent state management instead of local SQLite. Use AWS CDK to define managed database resources with Multi-AZ failover. |
| **Evidence** | `dvc/database.py` — SQLAlchemy `create_engine()` for generic DB connections. `dvc/repo/__init__.py` — `DataIndex.open(os.path.join(index_dir, "db.db"))` for local SQLite state. No `aws_rds_*`, `aws_dynamodb_*` in repo. |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | DVC implements its own pipeline/workflow orchestration internally (`dvc repro`, `dvc.yaml` stages, DAG-based execution in `dvc/repo/reproduce.py`, `dvc/dagascii.py`). However, this is application-layer orchestration — DVC IS the orchestrator, not a consumer of orchestration services. There is no use of Step Functions, MWAA, Temporal, or Camunda. Celery/kombu (`dvc-task` dependency) is used locally for background task queueing (e.g., analytics daemon), not for workflow orchestration. Applying stateful-crud archetype calibration: DVC has multi-step business operations (reproduce pipelines, push/pull across stages) that are entirely hardcoded in application code with no dedicated orchestration service. |
| **Gap** | Multi-step workflows (pipeline reproduction, multi-stage data operations) are hardcoded in Python application logic with no dedicated orchestration service for visibility, retry handling, or state management. |
| **Recommendation** | For hosted/service deployments, consider AWS Step Functions to orchestrate long-running DVC pipelines (reproduce, push, pull) with built-in retry logic, error handling, and visual workflow management. EventBridge (per preference) can trigger pipeline executions based on data events. |
| **Evidence** | `dvc/repo/reproduce.py` — pipeline reproduction logic. `dvc/dagascii.py` — DAG visualization. `pyproject.toml` — celery, kombu, dvc-task dependencies. No `aws_sfn_*` or Temporal SDK imports found. |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | DVC uses Celery and Kombu for local task queueing (via `dvc-task` dependency), primarily for background analytics reporting (`dvc/daemon.py` spawns detached processes for analytics). This is local process-level async, not cloud messaging infrastructure. No SQS, SNS, EventBridge, MSK, or Kinesis resources or SDK imports found. Applying stateful-crud archetype calibration: DVC performs cross-service state changes (push/pull to remote storage) synchronously with no managed messaging for decoupling. |
| **Gap** | All remote storage interactions (push, pull, fetch, status) are synchronous blocking operations. No managed messaging for cross-service state propagation or event-driven patterns. Background analytics use a subprocess daemon pattern rather than managed messaging. |
| **Recommendation** | For service deployments, adopt EventBridge (per preference) for event-driven notifications on data operations (push completed, pull completed, pipeline finished). Use SQS for decoupling long-running data transfer operations. Avoid self-managed Kafka (per preference). |
| **Evidence** | `pyproject.toml` — celery, kombu dependencies. `dvc/daemon.py` — subprocess-based background task execution. `dvc/analytics.py` — daemon-based analytics sending. No `aws_sqs_*`, `aws_sns_*`, `aws_eventbridge_*` in repo. |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, security group, NACL, or network infrastructure defined. DVC is a CLI tool that runs on user machines and connects to cloud storage remotes (S3, GCS, Azure, SSH) via their respective client libraries. Network security is delegated to the user's environment and cloud provider configurations. |
| **Gap** | No network security infrastructure. If DVC were deployed as a service, there would be no network isolation, segmentation, or controlled ingress/egress. |
| **Recommendation** | For service deployments, define VPC with private subnets using AWS CDK. Deploy DVC workloads in private subnets with VPC endpoints for S3 access (PrivateLink). Use security groups with least-privilege rules. |
| **Evidence** | No `aws_vpc`, `aws_subnet`, `aws_security_group` resources found. No IaC files of any kind in repository. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or any managed entry point configured. DVC is a CLI tool (`dvc = "dvc.cli:main"` entry point in `pyproject.toml`) and Python library (`dvc.api` module), not a web service. The Python API (`dvc/api/__init__.py`) exposes functions like `metrics_show`, `params_show`, `exp_show`, `open`, `read` for programmatic access, but these are library functions, not HTTP endpoints. |
| **Gap** | No managed API entry point. The Python API is not exposed as a web service with throttling, authentication, or request validation. |
| **Recommendation** | If exposing DVC functionality as a web service, use API Gateway (per preference for `api-gateway`) with Lambda or EKS backends. Define OpenAPI specification from the existing `dvc.api` module to formalize the API contract. |
| **Evidence** | `pyproject.toml` — `dvc = "dvc.cli:main"` (CLI entry point). `dvc/api/__init__.py` — Python library API exports. No `aws_api_gateway_*`, `aws_lb_*`, `aws_appsync_*` resources. |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration found. No IaC resources for auto-scaling groups, application auto-scaling policies, Lambda concurrency limits, or DynamoDB capacity auto-scaling. DVC runs as a local CLI tool with no cloud compute to scale. |
| **Gap** | No auto-scaling infrastructure. Workloads cannot respond to demand changes. |
| **Recommendation** | For service deployments on EKS (per preference), configure Horizontal Pod Autoscaler (HPA) with custom metrics. For DynamoDB (per preference) state stores, enable auto-scaling on read/write capacity. |
| **Evidence** | No `aws_autoscaling_*`, `aws_appautoscaling_*` resources. No IaC files in repository. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup or recovery configuration found. DVC's local state (SQLite databases, file cache) has no automated backup. The design relies on Git for metadata versioning and cloud remotes for data durability, but there is no explicit backup configuration for the local state/index databases. |
| **Gap** | No automated backups for local state. No point-in-time recovery. No restore procedures documented. |
| **Recommendation** | For service deployments, configure automated backups on Aurora (per preference) with PITR. For DynamoDB (per preference), enable point-in-time recovery. Use AWS Backup for cross-service backup orchestration. |
| **Evidence** | No `backup_retention_period`, `point_in_time_recovery`, or `aws_backup_plan` resources. `dvc/repo/__init__.py` — local SQLite state with no backup mechanism. |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No high availability or fault isolation configuration found. DVC runs as a local CLI tool on a single machine. No multi-AZ deployment, no load balancers, no cross-zone configuration. |
| **Gap** | No HA configuration. Single point of failure for any service-based deployment. |
| **Recommendation** | For service deployments, deploy across 2+ AZs on EKS (per preference). Configure Aurora (per preference) with Multi-AZ failover. Use ALB with cross-zone load balancing enabled. |
| **Evidence** | No `multi_az`, `availability_zones` configurations. No IaC files in repository. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero IaC files found in the repository. No Terraform (`.tf`, `.tfvars`), CloudFormation, CDK (`cdk.json`), Helm (`Chart.yaml`), Kustomize (`kustomization.yaml`), or Ansible playbooks. The repository contains only Python source code, test files, CI/CD workflow definitions, and configuration files. |
| **Gap** | 0% IaC coverage. All infrastructure (if any exists) is manually created. Non-reproducible, error-prone, and not version-controlled. |
| **Recommendation** | Adopt AWS CDK (Python) to define infrastructure as code alongside the existing Python codebase. Start with compute (EKS per preference), networking (VPC, subnets), and data stores (Aurora/DynamoDB per preference). CDK's Python SDK aligns with DVC's existing Python ecosystem. |
| **Evidence** | `find . -name "*.tf" -o -name "*.tfvars" -o -name "cdk.json" -o -name "Chart.yaml" -o -name "kustomization.yaml"` returned no results. Repository root contains only: `dvc/`, `tests/`, `.github/`, `pyproject.toml`, `README.rst`, and documentation files. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Comprehensive CI/CD automation via GitHub Actions with 5 workflow files: (1) `tests.yaml` — full test matrix across 3 OS platforms (ubuntu, macOS, Windows) and 6 Python versions (3.9–3.14) with parallel execution, coverage reporting, and Slack notifications on failure; (2) `build.yaml` — automated build, verification (twine check), and publishing to Test PyPI (on main push) and PyPI (on release); (3) `codeql.yml` — CodeQL SAST with security-extended queries on push, PR, and scheduled runs; (4) `plugin_tests.yaml` — cross-repo plugin compatibility testing (dvc-s3); (5) `benchmarks.yaml` — performance regression benchmarks on PRs with failure thresholds. Additionally: Dependabot configured for daily pip and GitHub Actions dependency updates; pre-commit hooks for ruff linting, codespell, mypy type checking; codecov integration with 2% threshold. |
| **Gap** | No gap — this is mature CI/CD automation for a library/tool project. The pipeline covers build, test, security scanning, performance benchmarking, and automated publishing with quality gates. |
| **Recommendation** | No immediate action needed. The CI/CD pipeline is comprehensive. If deploying as a service, extend the existing pipeline with deployment stages (EKS deployment, canary rollout). |
| **Evidence** | `.github/workflows/tests.yaml`, `.github/workflows/build.yaml`, `.github/workflows/codeql.yml`, `.github/workflows/plugin_tests.yaml`, `.github/workflows/benchmarks.yaml`, `.github/dependabot.yml`, `.pre-commit-config.yaml`, `.github/codecov.yml` |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Python is the sole programming language. The repository contains ~298 Python source files in `dvc/` with comprehensive type annotations (mypy configured in `pyproject.toml`). Python has first-class AWS SDK coverage (boto3), broad cloud-native tooling, and a mature ecosystem for ML/data engineering. DVC leverages the Python ecosystem extensively: fsspec for filesystem abstraction, SQLAlchemy for database connectivity, requests for HTTP, celery/kombu for task management. |
| **Gap** | No gap — Python is an ideal language for cloud-native ML tooling with first-class AWS SDK support. |
| **Recommendation** | No action needed. Python is well-suited for the DVC use case and has excellent AWS integration via boto3 and the `dvc-s3`, `dvc-gs`, etc. plugin ecosystem. |
| **Evidence** | `pyproject.toml` — `requires-python = ">=3.9"`, classifiers for Python 3.9–3.14. All source files in `dvc/` are `.py`. |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | DVC is a single deployable CLI application (monolith), but it has a well-structured modular internal architecture with clear module boundaries: `dvc/commands/` (CLI command handlers, ~45 files), `dvc/repo/` (repository operations, ~45 files), `dvc/fs/` (filesystem abstractions), `dvc/api/` (Python API), `dvc/dependency/` (dependency types), `dvc/stage/` (pipeline stage management), `dvc/parsing/` (configuration parsing), `dvc/render/` (output rendering), `dvc/utils/` (utilities). Each module has a clear single responsibility. The plugin architecture (dvc-s3, dvc-gs, dvc-azure as separate packages) demonstrates good boundary design. No circular dependencies detected between top-level modules. Data access is centralized through `dvc/data_cloud.py` and `dvc/cachemgr.py`. |
| **Gap** | Single deployable unit — cannot independently scale or deploy individual modules. However, the plugin-based remote storage architecture provides some service boundary separation. |
| **Recommendation** | The modular monolith structure is appropriate for a CLI tool. If DVC evolves into a service, the existing module boundaries (commands, repo operations, data cloud, filesystem) provide natural service extraction points via the Strangler Fig pattern. |
| **Evidence** | `dvc/commands/` — 45 command modules. `dvc/repo/` — 45 operation modules. `dvc/api/__init__.py` — clean public API. `pyproject.toml` — single package distribution. Plugin architecture: `dvc-s3`, `dvc-gs`, `dvc-azure` as optional dependencies. |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Applying stateful-crud archetype calibration. DVC is primarily synchronous — all CLI operations (add, push, pull, fetch, reproduce) block until completion. The `dvc/daemon.py` module provides a subprocess-based async mechanism for non-critical operations (analytics reporting), using `os.fork()` on POSIX and `subprocess.Popen` on Windows. Celery/kombu (`dvc-task` dependency) provides local task queue capabilities. However, cross-service state changes (push to S3, pull from remote) are entirely synchronous with tqdm progress bars for user feedback. No managed messaging for async decoupling. |
| **Gap** | For the stateful-crud archetype, DVC is primarily synchronous with some async for background jobs — scoring 2. Cross-service data operations (push/pull to cloud remotes) that could benefit from async are handled synchronously. |
| **Recommendation** | For service deployments, introduce async patterns for data transfer operations using SQS for job queuing and EventBridge (per preference) for event notification on completion. Keep synchronous reads where appropriate. |
| **Evidence** | `dvc/daemon.py` — subprocess-based async for analytics. `dvc/data_cloud.py` — synchronous push/pull/status operations. `dvc/fs/callbacks.py` — TqdmCallback for synchronous progress tracking. `pyproject.toml` — celery, kombu dependencies for local task queuing. |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Applying stateful-crud archetype calibration. DVC handles several long-running operations (data push/pull/fetch for large datasets, pipeline reproduction, garbage collection) synchronously with progress bars (tqdm/rich). The `TqdmCallback` in `dvc/fs/callbacks.py` provides progress tracking. The daemon subprocess pattern (`dvc/daemon.py`) is used for analytics — a background job mechanism. However, there is no job status API, no polling pattern, and no callback mechanism for long-running data operations. Users must wait for CLI commands to complete. |
| **Gap** | For the stateful-crud archetype, some background job processing exists (daemon) but inconsistent patterns — scoring 2. Long-running data transfers (push/pull of large datasets) are purely synchronous with no async job processing or status polling. |
| **Recommendation** | For service deployments, implement async job processing for data operations exceeding 30 seconds. Use Step Functions for orchestrating multi-stage data transfers with status tracking. Provide job status API endpoints for polling. |
| **Evidence** | `dvc/data_cloud.py` — synchronous `push()`, `pull()`, `status()` methods. `dvc/fs/callbacks.py` — `TqdmCallback` for progress. `dvc/daemon.py` — subprocess background jobs (analytics only). `dvc/progress.py` — Tqdm progress bar wrapper. |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | DVC uses semantic versioning for the package (`setuptools_scm` in `pyproject.toml`). The Python API (`dvc/api/__init__.py`) exports a stable set of functions (`metrics_show`, `params_show`, `exp_show`, `open`, `read`, etc.) but has no explicit versioning strategy for the API surface itself. The CLI commands have no versioned paths. The `__all__` export list in `dvc/api/__init__.py` provides some API surface control. No HTTP API versioning (no `/v1/` paths). No `CHANGELOG` or API deprecation policy found in-repo (though the README links to external docs). |
| **Gap** | Package-level semantic versioning exists but the Python API itself has no explicit version contract, deprecation policy, or backward compatibility guarantees beyond the package version. |
| **Recommendation** | Document the Python API versioning strategy. Consider adding `@deprecated` decorators for API functions being phased out. If exposing as a web service, adopt URL path versioning (`/v1/`, `/v2/`) via API Gateway (per preference). |
| **Evidence** | `pyproject.toml` — `setuptools_scm` for version management. `dvc/api/__init__.py` — `__all__` export list. `.github/release.yml` — changelog categories for releases. No explicit API versioning docs in-repo. |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No service registry, API catalog, or service mesh. DVC uses user-configured remote URLs (`dvc remote add <name> <url>`) stored in `.dvc/config` files. Remote endpoints are static configuration — users manually specify S3 bucket URLs, SSH hostnames, GCS paths, etc. The `dvc/config_schema.py` defines the remote URL schema but there is no dynamic discovery mechanism. |
| **Gap** | All remote endpoints are hard-coded in user configuration files. No dynamic service discovery, no service mesh, no API catalog. |
| **Recommendation** | For service deployments, adopt AWS Cloud Map or EKS service discovery for internal services. For remote storage endpoints, consider a centralized configuration service backed by DynamoDB (per preference) or AWS AppConfig for dynamic endpoint management. |
| **Evidence** | `dvc/config_schema.py` — `REMOTE_SCHEMAS` with static URL-based remote definitions. `dvc/data_cloud.py` — `get_remote()` reads configuration for remote endpoints. `.dvc/config` — empty (remotes configured by user). |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | DVC's core purpose is managing unstructured data (ML datasets, models, large binary files). It supports S3 as a primary remote storage backend via the `dvc-s3` plugin (`pyproject.toml` optional dependency). Additional cloud storage support includes GCS (`dvc-gs`), Azure Blob (`dvc-azure`), SSH, HDFS, WebDAV, and OSS. Data is stored in S3 (or other backends) with content-addressable hashing via `dvc-data` library. However, DVC itself does not provide automated parsing/extraction capabilities (no Textract, Tika integration). It is a storage management layer, not a data processing pipeline. |
| **Gap** | Data is stored in S3 (good) but there is no automated parsing or extraction pipeline for the managed unstructured data. DVC manages the files but does not process their content. |
| **Recommendation** | Integrate Amazon Textract or Amazon Comprehend for automated document parsing on DVC-managed datasets stored in S3. Consider Amazon Bedrock (per preference) for intelligent content analysis of managed data assets. |
| **Evidence** | `pyproject.toml` — `dvc-s3>=3.2.1,<4` optional dependency. `dvc/config_schema.py` — S3 remote schema with `sse`, `sse_kms_key_id` fields. `dvc/data_cloud.py` — `DataCloud` class for cloud storage operations. |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | DVC has an exemplary unified data access layer. The `dvc/data_cloud.py` `DataCloud` class provides a single interface for push/pull/status across all remote storage backends. The `dvc/fs/` module provides filesystem abstractions (`dvc/fs/__init__.py`, `dvc/fs/dvc.py`, `dvc/fs/data.py`) using the fsspec framework for uniform filesystem operations. The `dvc/cachemgr.py` `CacheManager` centralizes cache management. All data access flows through these centralized components — individual commands in `dvc/commands/` and operations in `dvc/repo/` use the DataCloud and filesystem abstractions rather than making direct storage calls. |
| **Gap** | No gap — the data access layer is well-centralized with a single point of data contract through DataCloud, filesystem abstractions, and cache management. |
| **Recommendation** | No action needed. The unified data access pattern is a strength. Maintain this pattern as new storage backends are added. |
| **Evidence** | `dvc/data_cloud.py` — `DataCloud` class with unified push/pull/status. `dvc/fs/` — filesystem abstractions using fsspec. `dvc/cachemgr.py` — centralized `CacheManager`. `dvc/repo/push.py`, `dvc/repo/pull.py`, `dvc/repo/fetch.py` — all use `DataCloud` interface. |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | DVC's `dvc/database.py` uses SQLAlchemy generically — it connects to user-specified databases via `create_engine(url)` for the `import-db` command. No database engine version is pinned in the repository. Local SQLite state databases (opened via `dvc-data` library in `dvc/repo/__init__.py`) use whatever SQLite version is bundled with the Python runtime. The `pyproject.toml` specifies `sqlalchemy>=1,<3` for testing, a very wide range with no engine version requirements. `dvc/config_schema.py` `db` section allows user-specified database URLs with username/password but no engine version constraints. |
| **Gap** | No database engine version pinning. SQLite version depends on Python runtime. SQLAlchemy version range is very wide (>=1,<3). No version-update procedure or EOL tracking. |
| **Recommendation** | Pin SQLAlchemy to a more specific range in production dependencies. Document the supported database engines and their version requirements for `import-db`. Consider adding engine version validation in `dvc/database.py` to warn users about EOL database engines. |
| **Evidence** | `dvc/database.py` — `create_engine(url)` with no version constraints. `pyproject.toml` — `sqlalchemy>=1,<3` (test dependency only). `dvc/config_schema.py` — `db` section with no version fields. `dvc/repo/__init__.py` — `DataIndex.open()` for local SQLite. |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs. The `dvc/database.py` module executes user-provided SQL queries via SQLAlchemy for the `import-db` feature but does not define any stored procedures, triggers, or functions. All business logic is in the Python application layer. The `Serializer` class in `dvc/database.py` uses `pd.read_sql()` for generic query execution and data export (CSV/JSON). The `Client` class uses `conn.exec_driver_sql("select 1")` for connection testing only. No `.sql` migration files found in the repository. |
| **Gap** | No gap — all business logic resides in the application layer with no database coupling via stored procedures. |
| **Recommendation** | No action needed. The clean separation of business logic from the database layer is a strength that enables future database engine flexibility. |
| **Evidence** | `dvc/database.py` — `Serializer.to_csv()`, `Serializer.to_json()` using `pd.read_sql()`. No `CREATE PROCEDURE`, `CREATE TRIGGER`, `CREATE FUNCTION` found in repository. No `.sql` files found. |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging configured. DVC has its own usage telemetry system (`dvc/analytics.py` with `iterative-telemetry` dependency) that sends anonymous usage reports to `analytics.dvc.org`, but this is product analytics, not security audit logging. The telemetry collects command class, return code, DVC version, system info, and remote types — no security-relevant audit events. Python logging (`dvc/logger.py`) provides DEBUG/TRACE levels for diagnostic purposes but no structured audit log output. |
| **Gap** | No security audit logging. No CloudTrail integration. No immutable audit log storage. Product telemetry is not a substitute for security audit logging. |
| **Recommendation** | For service deployments, enable CloudTrail with log file validation and S3 Object Lock for immutable storage. For the CLI tool, consider adding structured audit logging for security-relevant operations (remote credential access, data push/pull to external systems) using Python's `logging` module with structured JSON output. |
| **Evidence** | `dvc/analytics.py` — product telemetry, not audit logging. `dvc/logger.py` — diagnostic logging only. No `aws_cloudtrail` resources. |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | DVC supports S3 server-side encryption configuration in `dvc/config_schema.py`: `sse` (encryption algorithm), `sse_kms_key_id` (KMS key ID), `sse_customer_algorithm`, and `sse_customer_key` fields for S3 remotes. This enables users to configure customer-managed KMS keys for S3 remote storage. However, encryption is not enabled by default — it requires explicit user configuration. Local cache and state databases (SQLite) have no encryption. Other remote types (GCS, Azure, SSH) do not have equivalent encryption configuration fields in the DVC schema (though the cloud providers may apply default encryption). |
| **Gap** | Encryption support exists for S3 remotes but is not enabled by default. Local data (cache, SQLite state) is unencrypted. No encryption configuration for non-S3 remotes in DVC schema. |
| **Recommendation** | Make S3 SSE configuration a recommended default in DVC documentation. Consider defaulting to `sse: "aws:kms"` for new S3 remotes. For service deployments, enforce customer-managed KMS keys for all data stores. |
| **Evidence** | `dvc/config_schema.py` — S3 remote schema: `"sse": str`, `"sse_kms_key_id": str`, `"sse_customer_algorithm": str`, `"sse_customer_key": str`. No default encryption configuration. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | DVC supports authentication for cloud remotes via static credentials stored in DVC config: S3 (`access_key_id`, `secret_access_key`, `session_token`, `profile`), Azure (`connection_string`, `sas_token`, `account_key`, `tenant_id`, `client_id`, `client_secret`), GDrive (OAuth via `gdrive_client_id`, `gdrive_client_secret`), SSH (`password`, `keyfile`). DVC Studio integration uses token-based auth (`studio.token` in config, `DVC_STUDIO_TOKEN` env var). These are static credential authentication patterns — no OAuth2/JWT token-based auth with per-request validation. No HTTP API endpoints exist to authenticate against. |
| **Gap** | Authentication is static credential-based (API keys, passwords, connection strings) rather than token-based (OAuth2/JWT). Credentials are stored in config files without per-request token rotation. No HTTP API surface exists for per-request authentication. |
| **Recommendation** | For service deployments, implement OAuth2/JWT authentication via API Gateway (per preference for `api-gateway`) with Cognito integration. Migrate from static credentials to IAM role-based authentication for AWS service access. |
| **Evidence** | `dvc/config_schema.py` — `access_key_id`, `secret_access_key`, `password`, `sas_token`, `client_secret` fields in remote schemas. `dvc/env.py` — `DVC_STUDIO_TOKEN`. No OAuth2/JWT middleware or token validation code. |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity provider integration. DVC uses per-remote authentication with separate credential sets for each cloud provider. DVC Studio uses a simple token (`studio.token` in config or `DVC_STUDIO_TOKEN` env var). GDrive uses OAuth but with DVC's own client ID — not a centralized organizational IdP. No Cognito, Okta, Ping, or SAML integration. No SSO capability. |
| **Gap** | Application manages its own authentication entirely per-remote with no external IdP integration. No centralized identity management, no SSO, no federated authentication. |
| **Recommendation** | For service deployments, integrate with Amazon Cognito for centralized identity management. Implement SSO via SAML/OIDC federation with organizational identity providers. Use IAM roles with Cognito identity pools for AWS service access instead of per-remote static credentials. |
| **Evidence** | `dvc/config_schema.py` — per-remote credential schemas (S3, Azure, GDrive, SSH each with separate auth). `studio.token` field. No `aws_cognito_*`, OIDC, or SAML configuration. |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Secrets (remote credentials) are stored in DVC config files (`.dvc/config` and `.dvc/config.local`). The `config_schema.py` defines fields for sensitive data: `password`, `secret_access_key`, `session_token`, `client_secret`, `sas_token`, `account_key`, `passphrase`. DVC recommends using `.dvc/config.local` (which is .gitignored by default) for sensitive credentials, and environment variables are supported for key secrets (`DVC_STUDIO_TOKEN`). However, there is no integration with AWS Secrets Manager, HashiCorp Vault, or any dedicated secrets management system. No automated rotation. Secrets can be stored in the `.dvc/config` file which may be committed to Git if `.dvc/config.local` is not used. |
| **Gap** | Some secrets in environment variables and .gitignored config files, but production credentials (database passwords, API keys) still in config files without encryption or rotation. No dedicated secrets management system. |
| **Recommendation** | Integrate with AWS Secrets Manager for remote credential management. Support dynamic secret retrieval in `dvc/config.py` via Secrets Manager SDK. Implement secret rotation for long-lived credentials. Warn users if sensitive fields are found in `.dvc/config` (non-local). |
| **Evidence** | `dvc/config_schema.py` — `password`, `secret_access_key`, `client_secret`, `sas_token` fields. `dvc/env.py` — `DVC_STUDIO_TOKEN` env var. `dvc/config.py` — file-based config loading with no secrets manager integration. |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No dedicated compute hardening or patching strategy for DVC itself (it's a CLI tool). For CI/CD, GitHub Actions uses managed runners (ubuntu-latest, macos-latest, windows-latest) which are automatically patched by GitHub. Dependabot is configured (`.github/dependabot.yml`) for daily dependency vulnerability scanning of both pip packages and GitHub Actions versions. CodeQL SAST provides vulnerability scanning of the codebase. No SSM Patch Manager, AWS Inspector, or hardened base images (no containers to harden). |
| **Gap** | Some patching automation (Dependabot) and vulnerability scanning (CodeQL) present but not comprehensive for a deployed service. No hardened container images (no containers). No SSM Patch Manager. |
| **Recommendation** | When containerizing (see Move to Containers pathway), use hardened base images (AWS Bottlerocket for EKS nodes, distroless Python images for containers). Enable Amazon Inspector for container vulnerability scanning in ECR. |
| **Evidence** | `.github/dependabot.yml` — daily dependency update checks for pip and github-actions. `.github/workflows/codeql.yml` — CodeQL SAST. `.github/workflows/tests.yaml` — managed GitHub runners. |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Comprehensive application security pipeline: (1) CodeQL SAST configured in `.github/workflows/codeql.yml` with `security-extended` query suite, running on push to main, PRs, and weekly scheduled scans; (2) Dependabot configured in `.github/dependabot.yml` for daily pip and github-actions dependency scanning; (3) Ruff linter configured in `pyproject.toml` with `"S"` (security) rules enabled in the rule selection; (4) Pre-commit hooks (`.pre-commit-config.yaml`) with ruff-check for security linting; (5) mypy type checking configured with strict settings for additional code quality assurance. No container scanning (not applicable — no containers in production). |
| **Gap** | No gap for current architecture. SAST + dependency scanning with security gates in CI/CD. Container scanning not applicable (no containers). |
| **Recommendation** | No immediate action needed. When containerizing, add ECR image scanning and Snyk container scanning to the pipeline. |
| **Evidence** | `.github/workflows/codeql.yml` — CodeQL with `security-extended`. `.github/dependabot.yml` — daily dependency scanning. `pyproject.toml` — ruff `"S"` rules enabled. `.pre-commit-config.yaml` — ruff-check pre-commit hook. |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumented. DVC uses Python's logging module (`dvc/log.py`, `dvc/logger.py`) with custom levels (DEBUG, TRACE — a custom level below DEBUG). The `ColorFormatter` in `dvc/logger.py` provides colored console output. No OpenTelemetry SDK, X-Ray instrumentation, or trace ID propagation. No `traceparent` or `X-Amzn-Trace-Id` headers. The logging setup covers `dvc`, `dvc_objects`, and `dvc_data` loggers but uses standard Python logging without structured trace context. |
| **Gap** | No distributed tracing. Debugging failures across remote storage interactions (S3, GCS, Azure) is limited to log-level diagnostics without trace correlation. |
| **Recommendation** | Instrument OpenTelemetry SDK for distributed tracing. Add trace context propagation to remote storage operations (push/pull/fetch). For service deployments, enable AWS X-Ray integration. OpenTelemetry Python SDK integrates well with the existing Python logging setup. |
| **Evidence** | `dvc/log.py` — basic `logging.Logger` with trace level. `dvc/logger.py` — `ColorFormatter`, `LoggerHandler` using Python standard logging. No opentelemetry, aws-xray-sdk in `pyproject.toml` dependencies. |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found. No availability targets, latency budgets, or error rate thresholds defined anywhere in the repository. No CloudWatch alarms or monitoring configuration. DVC is a CLI tool — SLOs are not traditionally defined for CLI tools, but if deployed as a service, they would be critical. |
| **Gap** | No SLOs defined. No formal definition of acceptable service levels for any DVC operation. |
| **Recommendation** | For service deployments, define SLOs for critical operations: data push/pull latency p99, API availability target, experiment tracking response time. Use Amazon CloudWatch with EventBridge (per preference) for SLO monitoring and alerting. |
| **Evidence** | No SLO files, CloudWatch alarm configurations, or error budget tracking found in repository. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | DVC collects usage telemetry via `dvc/analytics.py` and the `iterative-telemetry` dependency. The telemetry includes: DVC version, command executed (`cmd_class`), return code (`cmd_return_code`), system info (OS, Python version), remote types, and a git remote hash. This is sent to `analytics.dvc.org`. These are product usage metrics, not business outcome metrics. No CloudWatch custom metrics, no business KPI dashboards, no conversion or performance tracking. |
| **Gap** | Infrastructure/usage metrics exist (product telemetry) but no business outcome metrics (operation success rates, data transfer volumes, pipeline execution durations). Metrics are sent to an external endpoint, not to CloudWatch. |
| **Recommendation** | For service deployments, publish business metrics to CloudWatch: data transfer volumes, pipeline execution success rates, experiment completion rates, cache hit ratios. Use CloudWatch dashboards for operational visibility. |
| **Evidence** | `dvc/analytics.py` — `_runtime_info()` collects telemetry. `pyproject.toml` — `iterative-telemetry>=0.0.7` dependency. No `cloudwatch.put_metric_data` calls. |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configured. No CloudWatch alarms, no error rate monitoring, no latency tracking. The only notification mechanism is the Slack webhook in `tests.yaml` for CI failures on main branch — a CI notification, not production alerting. |
| **Gap** | No anomaly detection, no alerting, no production monitoring. |
| **Recommendation** | For service deployments, configure CloudWatch anomaly detection on error rates and p99 latency. Set up composite alarms with EventBridge (per preference) for routing to PagerDuty or OpsGenie. |
| **Evidence** | `.github/workflows/tests.yaml` — Slack notification for CI failures only. No CloudWatch, PagerDuty, or OpsGenie configuration. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | DVC uses a rolling publish strategy via GitHub Actions (`build.yaml`): pushes to main automatically publish to Test PyPI (with `local_scheme="no-local-version"`), and GitHub releases trigger publication to production PyPI. This provides a staged rollout (Test PyPI → PyPI) but without traffic shifting, canary testing, or rollback automation. The `twine check --strict` step validates package integrity before publishing. |
| **Gap** | Rolling deployment to PyPI with basic health checks (twine check) but no traffic shifting or canary testing. No automated rollback mechanism. Users consume the latest published version without gradual exposure. |
| **Recommendation** | For the library distribution: consider a staged rollout with release candidates on Test PyPI before production PyPI publish. For service deployments: implement canary deployments on EKS (per preference) with progressive traffic shifting and automated rollback on error rate increases. |
| **Evidence** | `.github/workflows/build.yaml` — Test PyPI publish on main push, PyPI publish on release. `twine check --strict` validation step. No CodeDeploy, Argo Rollouts, or traffic shifting configuration. |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Comprehensive test suite with clear separation: (1) `tests/unit/` — 136 unit test files covering individual modules; (2) `tests/func/` — 104 functional test files covering end-to-end CLI operations (add, checkout, commit, data cloud, diff, experiments, gc, import, ls, metrics, params, plots, repro, etc.); (3) `tests/integration/` — 7 integration test files including Studio live experiments integration; (4) `tests/docker-compose.yml` — Docker-based test infrastructure (git-server for SSH tests). Tests run in CI via `tests.yaml` with multi-platform (ubuntu, macOS, Windows) and multi-Python-version (3.9–3.14) matrix. Plugin compatibility tests in `plugin_tests.yaml`. Performance benchmarks in `benchmarks.yaml` with regression detection (`--benchmark-compare-fail=min:5%`). Coverage tracked via codecov with 2% threshold. |
| **Gap** | No gap — integration test suites cover critical workflows and run in CI with comprehensive platform/version matrix. |
| **Recommendation** | No immediate action needed. The test suite is comprehensive. Consider adding contract tests for the Python API (`dvc.api`) to ensure backward compatibility across versions. |
| **Evidence** | `tests/func/` — 104 functional test files. `tests/unit/` — 136 unit test files. `tests/integration/` — 7 integration test files. `.github/workflows/tests.yaml` — 36+ matrix combinations. `.github/workflows/benchmarks.yaml` — performance regression testing. `.github/codecov.yml` — coverage tracking. |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response automation or runbooks found. `.github/release.yml` provides changelog categorization (breaking changes, features, bug fixes, maintenance) but is not an incident response mechanism. No Systems Manager Automation documents, no Lambda-based remediation, no Step Functions for incident workflows. No self-healing patterns. The Slack notification in `tests.yaml` notifies on CI failure but is not an incident response system. |
| **Gap** | No runbooks, no automated incident response, no self-healing patterns. Incident response is entirely ad hoc. |
| **Recommendation** | For service deployments, create runbooks in Systems Manager Automation for common incidents (storage connectivity failure, cache corruption, high error rates). Implement self-healing with Lambda-based remediation triggered by CloudWatch alarms via EventBridge (per preference). |
| **Evidence** | `.github/release.yml` — changelog categories only. `.github/workflows/tests.yaml` — CI failure Slack notification. No runbook files, SSM Automation documents, or remediation scripts. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership defined. No CODEOWNERS file found in the repository. `.github/codecov.yml` provides coverage tracking with a 2% regression threshold but this is code coverage, not production observability. No per-service dashboards, no named alarm owners, no SLO definitions with team attribution. |
| **Gap** | No observability ownership. No CODEOWNERS for monitoring assets. No dashboards with team attribution. |
| **Recommendation** | Add a CODEOWNERS file mapping observability configuration to responsible teams. For service deployments, create per-module CloudWatch dashboards with named owners. Define SLOs with team attribution. |
| **Evidence** | No CODEOWNERS file. `.github/codecov.yml` — code coverage tracking only. No dashboard definitions or alarm ownership configuration. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging found. No IaC files exist to tag resources. No `default_tags` in any Terraform provider configuration. No `required-tags` AWS Config rules. No Tag Policies. DVC as a CLI tool does not manage AWS resources directly — it delegates to cloud provider libraries for remote storage access. |
| **Gap** | No resource tagging governance. If AWS resources are provisioned for DVC service deployment, there are no tagging standards or enforcement mechanisms. |
| **Recommendation** | When defining IaC (per Move to Modern DevOps pathway), establish a tagging standard from day one. Use `default_tags` in Terraform or CDK `Tags.of()` for consistent tagging. Implement AWS Config `required-tags` rules and Tag Policies in AWS Organizations for enforcement. |
| **Evidence** | No IaC files. No `tags` blocks. No `default_tags` configuration. No AWS Config or Organizations configuration. |

---

## Learning Materials

### Move to Containers
- [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM)
- [Move to Containers with Amazon ECS](https://skillbuilder.aws/learning-plan/CDA8Y4JRRR)
- [EKS Workshop](https://www.eksworkshop.com/)

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
| `pyproject.toml` | INF-Q1, INF-Q2, INF-Q3, INF-Q4, INF-Q11, APP-Q1, APP-Q2, APP-Q3, APP-Q4, APP-Q5, DATA-Q1, DATA-Q3, OPS-Q1, OPS-Q3, SEC-Q7 | Primary dependency manifest; defines entry points, dependencies (celery, kombu, sqlalchemy, fsspec), optional cloud remotes (dvc-s3, dvc-gs, dvc-azure), ruff security rules, Python version requirements |
| `.github/workflows/tests.yaml` | INF-Q11, OPS-Q4, OPS-Q5, OPS-Q6 | Comprehensive test CI — multi-platform/multi-Python matrix, coverage, Slack notifications |
| `.github/workflows/build.yaml` | INF-Q11, OPS-Q5 | Build and publish pipeline — Test PyPI and PyPI publication |
| `.github/workflows/codeql.yml` | INF-Q11, SEC-Q6, SEC-Q7 | CodeQL SAST with security-extended queries |
| `.github/workflows/plugin_tests.yaml` | INF-Q11, OPS-Q6 | Cross-repo plugin compatibility testing (dvc-s3) |
| `.github/workflows/benchmarks.yaml` | INF-Q11, OPS-Q6 | Performance benchmarking with regression detection |
| `.github/dependabot.yml` | SEC-Q6, SEC-Q7 | Daily dependency vulnerability scanning for pip and github-actions |
| `.github/codecov.yml` | OPS-Q6, OPS-Q8 | Code coverage tracking with 2% threshold |
| `.github/release.yml` | OPS-Q7 | Changelog categorization for releases |
| `.pre-commit-config.yaml` | INF-Q11, SEC-Q7 | Pre-commit hooks: ruff-check, codespell, mypy, JSON/YAML validation |
| `dvc/data_cloud.py` | INF-Q4, APP-Q3, APP-Q4, DATA-Q2 | Unified data access layer — DataCloud class for push/pull/status |
| `dvc/database.py` | INF-Q2, DATA-Q3, DATA-Q4 | SQLAlchemy-based generic database import — Serializer, Client classes |
| `dvc/config_schema.py` | INF-Q2, SEC-Q2, SEC-Q3, SEC-Q4, SEC-Q5, APP-Q6, DATA-Q1 | Remote configuration schemas — S3 SSE, credentials, remote URLs |
| `dvc/daemon.py` | INF-Q3, INF-Q4, APP-Q3, APP-Q4 | Subprocess-based background task execution for analytics |
| `dvc/analytics.py` | SEC-Q1, OPS-Q3 | Product telemetry — usage analytics to analytics.dvc.org |
| `dvc/env.py` | SEC-Q3, SEC-Q5 | Environment variable definitions — DVC_STUDIO_TOKEN and 20+ config vars |
| `dvc/log.py` | OPS-Q1 | Basic Python logger with TRACE level |
| `dvc/logger.py` | OPS-Q1, SEC-Q1 | Logging configuration — ColorFormatter, LoggerHandler, multi-level setup |
| `dvc/repo/__init__.py` | INF-Q2, INF-Q3, APP-Q2 | Repo class — modular architecture, local SQLite state, DataCloud integration |
| `dvc/api/__init__.py` | APP-Q5, APP-Q6 | Python API surface — metrics_show, params_show, exp_show, open, read exports |
| `dvc/cli/__init__.py` | APP-Q2 | CLI entry point — main() function, argument parsing, analytics integration |
| `dvc/fs/callbacks.py` | APP-Q4 | TqdmCallback for synchronous progress tracking |
| `dvc/cachemgr.py` | DATA-Q2 | Centralized CacheManager for cache operations |
| `dvc/config.py` | SEC-Q5 | File-based config loading — no secrets manager integration |
| `dvc/commands/` | APP-Q2 | 45 command handler modules — modular CLI command structure |
| `dvc/fs/` | DATA-Q2 | Filesystem abstractions using fsspec framework |
| `tests/func/` | OPS-Q6 | 104 functional test files covering end-to-end CLI operations |
| `tests/unit/` | OPS-Q6 | 136 unit test files covering individual modules |
| `tests/integration/` | OPS-Q6 | 7 integration test files including Studio live experiments |
| `tests/docker-compose.yml` | INF-Q1 | Test infrastructure only — git-server container for SSH testing |
| `README.rst` | Quick Agent Wins | Comprehensive documentation — CLI workflows, architecture, installation |
| `.dvc/config` | SEC-Q5, APP-Q6 | Empty DVC config — remotes configured by user |
