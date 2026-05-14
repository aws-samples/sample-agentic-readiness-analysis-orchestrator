# Modernization Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | dvc |
| **Date** | 2025-07-16 |
| **TD Version** | Modernization Analysis v1.0 |
| **Repo Type** | application |
| **Service Archetype** | stateless-utility (auto-detected) |
| **Priority** | P2 |
| **Tags** | python, ml, data |
| **Context** | Data Version Control: git-for-ML-data, models, and experiments. |
| **Preferences** | Prefer: eks, aurora, dynamodb, api-gateway, eventbridge, bedrock · Avoid: self-managed-kafka, self-managed-kubernetes, oracle |
| **Surface Flags** | has_persistent_data_store=false, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=false, has_multi_instance_deployment=false |
| **Overall Score** | **2.15 / 4.0** |

**Archetype Justification**: DVC is a developer CLI tool distributed via PyPI with entry point `dvc.cli:main`. It has no HTTP/gRPC server endpoints, no deployed cloud workload, no databases that it provisions, and no persistent state it owns. All operations are command-driven synchronous request/response (CLI commands). Classified as `stateless-utility`.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.33 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.50 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 3.50 / 4.0 | ✅ Mature |
| Security Baseline (SEC) | 1.67 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.75 / 4.0 | 🟠 Needs Work |
| **Overall** | **2.15 / 4.0** | **🟠 Needs Work** |

> **Context Note**: DVC is a CLI tool and Python library — not a deployed cloud service. Many INF, SEC, and OPS questions evaluate deployed-infrastructure concerns (VPCs, auto-scaling, encryption at rest, API gateways) that are structurally not applicable to a CLI tool distributed via PyPI. The low INF and OPS scores reflect this architectural reality rather than engineering deficiency. The DATA and APP scores accurately reflect the codebase quality. Surface-gated and archetype-calibrated questions (8 total) were excluded to prevent false positives.

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC exists — all infrastructure (if any) would be manually created | Blocks reproducible environment provisioning and disaster recovery |
| 2 | SEC-Q1: Audit Logging | 1 | No CloudTrail or cloud audit logging for the tool's analytics/telemetry endpoints | No forensic capability for the analytics endpoint or Studio webhook integrations |
| 3 | SEC-Q3: API Authentication | 1 | Studio webhook endpoint uses bearer token but no OAuth2/JWT; CLI-to-remote auth varies by remote type | Inconsistent authentication patterns across remote integrations |
| 4 | OPS-Q1: Distributed Tracing | 1 | No OpenTelemetry or distributed tracing instrumentation | Cannot trace request flows across DVC → remote storage → Studio integrations |
| 5 | APP-Q6: Service Discovery | 1 | All remote endpoints are hardcoded in user config files with no dynamic discovery | Remote endpoints are static strings in DVC config — no service discovery mechanism |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 3). GitHub Actions workflows for tests, builds, benchmarks, plugin tests, and CodeQL are fully automated.
- **What it enables:** An agent that triggers test runs, monitors build status, manages PyPI releases, and auto-triages CI failures across the 5+ workflow files.
- **Additional steps:** Expose GitHub Actions status via API or webhook for agent consumption. Consider adding a release automation agent that validates test-pypi results before promoting to pypi.
- **Effort:** Low

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists. README.rst with comprehensive project description, external documentation at dvc.org/doc, CONTRIBUTING.md with link to contribution guide, extensive inline docstrings throughout the codebase.
- **What it enables:** A RAG-based knowledge agent using Amazon Bedrock that indexes DVC's documentation corpus (dvc.org/doc, README, code comments) to answer developer questions about DVC internals, CLI usage, and contribution workflows.
- **Additional steps:** Index the external dvc.org documentation site alongside the repository content. Use Amazon Bedrock with a knowledge base backed by Amazon OpenSearch for vector storage.
- **Effort:** Medium

### Data Query Agent

- **Prerequisite:** Database with clear schema (DATA-Q2 = 4). DVC has a well-structured data access layer via `dvc/data_cloud.py` (DataCloud/Remote pattern) and `dvc/database.py` (SQLAlchemy-based database client for `import-db`).
- **What it enables:** An agent that queries DVC's internal data structures (cache index, data index, experiment metadata) using natural language, helping developers understand data lineage and cache state.
- **Additional steps:** Expose the data index and experiment metadata through a structured query interface. The existing SQLite-based data index (`db.db`) provides a queryable foundation.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 (modular monolith with clear boundaries) — primary trigger not met |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 1 but contextual guard prevents: DVC has no deployed compute to containerize — it is a PyPI-distributed CLI tool |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (no stored procedures/proprietary SQL) — primary trigger not met; no commercial DB engines detected |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = Not Evaluated (no persistent data store deployed by this codebase) — primary trigger not evaluable |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = Not Evaluated; no data processing workloads deployed by this codebase — contextual guard prevents |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (no IaC) — primary trigger met |
| 7 | Move to AI | Triggered | Medium | Medium | Context contains "ML" (AI signal term detected); no AI/agent frameworks found in codebase |

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 finding):** No Infrastructure as Code exists in this repository. DVC is distributed as a PyPI package and does not define any cloud infrastructure. If DVC were to deploy supporting services (e.g., a managed experiment tracking API, a Studio backend, or a shared cache service), IaC would be essential.

**Current CI/CD State (INF-Q11 finding):** GitHub Actions provides comprehensive CI/CD automation with 5 workflow files covering testing (multi-OS, multi-Python-version matrix), building and publishing to PyPI (with test-pypi staging), CodeQL security scanning, benchmarks, and plugin compatibility testing. The pipeline includes build, test, and deploy stages with automated rollback via the alls-green check gate.

**Deployment Strategy Gaps (OPS-Q5 finding):** The build/publish pipeline uses a two-stage deployment strategy (test-pypi → pypi) which provides a staging gate before production release. This is appropriate for a PyPI package.

**Testing Gaps (OPS-Q6 finding):** Comprehensive test suite exists with unit, functional, and integration test directories. pytest-docker is used for integration tests with a git-server container. pytest-cov provides coverage reporting integrated with Codecov.

**Recommendations:**
- **IaC for Supporting Infrastructure:** If DVC's supporting services (analytics endpoint, Studio webhook, documentation hosting) are managed by the team, define them in Terraform or CDK. Use Amazon EventBridge for event-driven analytics processing and Amazon DynamoDB for telemetry storage (aligned with preferences).
- **IaC for Development Environments:** Consider using CDK or Terraform to define reproducible CI/CD runner configurations, especially for the complex multi-OS, multi-Python matrix.
- **Pipeline Enhancement:** Add automated changelog generation and release notes to the build pipeline. Consider GitHub Actions reusable workflows to reduce duplication across the 5 workflow files.

**Representative AWS Services:** CloudFormation, CDK, CodeBuild, CodePipeline, EventBridge, DynamoDB

**Learning Resources:**
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

### Pathway: Move to AI

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**AI Signal Detected:** The context field contains "ML" — DVC is described as "git-for-ML-data, models, and experiments." The project keywords in `pyproject.toml` include "ai", "machine-learning", and "data-science". DVC is deeply embedded in the ML ecosystem.

**Current AI/Agent Infrastructure State:**
- **AI/Agent Frameworks:** None detected. No imports of Bedrock SDK, LangChain, Strands, OpenAI, Spring AI, HuggingFace, or SageMaker SDK in the 298 Python source files.
- **Vector Database Infrastructure:** None detected. No OpenSearch with vector engine, Pinecone, pgvector, Weaviate, or Qdrant.
- **RAG Implementation:** None detected. No embedding generation, vector store queries, or retrieval chain patterns.
- **Agent Evaluation Frameworks:** None detected. No Ragas, DeepEval, or custom eval harnesses.

**Application Domain and Potential AI Use Cases:**
DVC manages ML data, models, and experiments — it is a foundational tool in the ML lifecycle. AI integration opportunities include:
1. **Natural Language Experiment Querying:** "Show me experiments where accuracy > 0.95 and learning rate < 0.01" → translates to DVC experiment filters
2. **Intelligent Pipeline Suggestions:** Agent analyzes `dvc.yaml` pipelines and suggests optimizations based on data dependencies
3. **Smart Data Versioning:** Agent recommends which data artifacts to version based on usage patterns and model impact analysis
4. **Automated Experiment Summarization:** Agent generates human-readable summaries of experiment results and parameter sweeps

**Foundation Requirements:**
- DVC's well-structured data access layer (`dvc/data_cloud.py`, `dvc/database.py`) provides a clean interface for agent tools
- The experiment tracking infrastructure (`dvc/repo/experiments/`) exposes structured metadata that agents can query
- The CI/CD pipeline (INF-Q11 = 3) can support agent-assisted release workflows

**Recommended AI Services (aligned with preferences):**
- **Amazon Bedrock** for foundation model access — natural language to DVC command translation
- **Amazon Bedrock AgentCore** for building agents that interact with DVC's experiment and data management features
- **Amazon OpenSearch Service** (vector engine) for semantic search across experiment metadata and documentation

**Learning Resources:**
- [Move to AI](https://skillbuilder.aws/learning-plan/VDFEE4ACCV)
- [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ)
- [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | DVC is a CLI tool distributed via PyPI (`pip install dvc`). No compute infrastructure is defined in this repository — no Terraform, CloudFormation, CDK, Helm charts, or Kubernetes manifests exist. The entry point is `dvc.cli:main` (defined in `pyproject.toml` under `[project.scripts]`). The only container definition is `tests/docker-compose.yml` which runs a test git-server (`ghcr.io/linuxserver/openssh-server`) — this is a test fixture, not a deployment artifact. |
| **Gap** | No managed compute workloads exist because DVC is not a deployed service. This score reflects the structural reality of a CLI tool, not an engineering deficiency. |
| **Recommendation** | If DVC's supporting services (analytics endpoint at `analytics.dvc.org`, Studio webhook integration) are owned by this team, consider defining their compute infrastructure in IaC using EKS or Fargate (aligned with preferences). For the CLI tool itself, no compute infrastructure is needed. |
| **Evidence** | `pyproject.toml` (entry point definition), `tests/docker-compose.yml` (test-only container), absence of `*.tf`, `Dockerfile`, `Chart.yaml`, `kustomization.yaml` files |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy a database. DVC's `dvc/database.py` provides a SQLAlchemy client for the `import-db` command that connects to *user-specified* databases — DVC does not own or provision any database. The `dvc/config_schema.py` `db` section defines connection parameters (`url`, `username`, `password`) for user-configured databases. INF-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `dvc/database.py`, `dvc/config_schema.py` (db section), absence of `aws_rds_*`, `aws_dynamodb_*` in any IaC |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Workflow orchestration is not applicable by design — DVC is a CLI tool where each command is a self-contained synchronous operation. DVC does include Celery/Kombu (`dvc/repo/experiments/queue/celery.py`) for local experiment queue management, but this is a local task queue running on the user's machine, not a deployed orchestration service. No multi-step workflows exist that would benefit from Step Functions or Temporal. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `dvc/repo/experiments/queue/celery.py`, `pyproject.toml` (celery, kombu dependencies) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Synchronous CLI command execution is the correct design for DVC — each CLI invocation runs a synchronous operation against local files or remote storage. The Celery/Kombu usage for experiment queuing is local task scheduling, not inter-service messaging. No messaging or streaming infrastructure is needed, and adopting async messaging would add operational complexity without architectural benefit. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `dvc/cli/__init__.py` (synchronous `main()` entry point), `dvc/repo/experiments/queue/` (local task queue) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or network configuration exists in this repository. DVC is a client-side CLI tool that makes outbound HTTPS requests to remote storage (S3, GCS, Azure, SSH) and to Studio (`studio.datachain.ai`). It does not define or manage any network infrastructure. |
| **Gap** | No network security controls are defined because DVC does not deploy services into a VPC. The tool relies on the user's network environment. |
| **Recommendation** | If DVC's supporting backend services (analytics endpoint, Studio API) are owned by this team, define their network infrastructure with private subnets, least-privilege security groups, and VPC endpoints for AWS service access. For the CLI tool itself, no network infrastructure is needed. |
| **Evidence** | Absence of `aws_vpc`, `aws_subnet`, `aws_security_group` in any file; `dvc/utils/studio.py` (outbound HTTPS to `studio.datachain.ai`) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | DVC has no API entry point — it is a CLI tool invoked directly by users. There is no API Gateway, ALB, CloudFront, or AppSync. The Studio integration (`dvc/utils/studio.py`) makes outbound requests to Studio's webhook endpoint but does not expose any inbound API surface. |
| **Gap** | No API entry point exists because DVC is not an API-serving application. This is architecturally correct for a CLI tool. |
| **Recommendation** | If the team plans to expose DVC functionality as an API service (e.g., a DVC-as-a-service offering), use Amazon API Gateway (aligned with preferences) with authentication, throttling, and request validation. |
| **Evidence** | `dvc/cli/__init__.py` (CLI entry point), `dvc/utils/studio.py` (outbound-only HTTP), absence of any HTTP server framework |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. DVC is a CLI tool with no deployed workload to scale. Resource utilization is bounded by the user's local machine capabilities and remote storage throughput. |
| **Gap** | No auto-scaling because no deployed workload exists. This is structurally expected for a CLI tool. |
| **Recommendation** | If DVC backend services are deployed, configure auto-scaling on EKS with Horizontal Pod Autoscaler or ECS service auto-scaling. Consider DynamoDB on-demand capacity for any data stores (aligned with preferences). |
| **Evidence** | Absence of `aws_autoscaling_*`, `aws_appautoscaling_*` in any file |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no persistent state to back up. DVC does not deploy any databases, S3 buckets, or data stores. The local DVC cache on user machines is managed by the user, and remote storage backups are the responsibility of the remote provider. INF-Q8 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | Surface flag `has_persistent_data_store=false`, `has_at_rest_data_surface=false` |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload requiring HA evaluation. DVC is a CLI tool that runs on the user's machine. High availability is not applicable — CLI tool availability is determined by package distribution (PyPI uptime) and user environment. INF-Q9 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | Surface flag `has_deployed_workload=false` |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No Infrastructure as Code exists in this repository. No Terraform files (`.tf`), CloudFormation templates, CDK stacks, Helm charts, or Kustomize configurations were found. The repository contains only application source code, tests, CI/CD workflows, and package configuration. |
| **Gap** | 0% IaC coverage. If any supporting infrastructure exists (analytics endpoint, monitoring, documentation hosting), it is not defined in this repository. |
| **Recommendation** | Define any supporting infrastructure (analytics ingestion, Studio webhook processing, documentation hosting) using CDK or Terraform. Start with the CI/CD runner infrastructure and shared development resources. Use EventBridge for event-driven telemetry processing and DynamoDB for analytics storage (aligned with preferences). |
| **Evidence** | Absence of `*.tf`, `*.tfvars`, `cdk.json`, `template.yaml`, `Chart.yaml`, `kustomization.yaml` files confirmed via recursive file search |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive CI/CD automation via GitHub Actions with 5 workflow files: (1) `tests.yaml` — lint + tests across 3 OS × 6 Python versions with pytest-cov, codecov upload, and Slack failure notification; (2) `build.yaml` — build, verify (twine check), publish to test-pypi and pypi with OIDC token auth; (3) `codeql.yml` — CodeQL security analysis on push/PR/schedule; (4) `benchmarks.yaml` — performance regression testing on PRs; (5) `plugin_tests.yaml` — cross-repo plugin compatibility tests. Build and deploy stages are fully automated with the test-pypi → pypi promotion path. |
| **Gap** | IaC changes are not covered because no IaC exists (INF-Q10 = 1). The pipeline covers application code comprehensively but cannot cover infrastructure changes. Automated rollback on pypi publish failure is not explicit — the build gate (`alls-green`) prevents bad builds from reaching publish, but there is no post-publish rollback mechanism (e.g., yanking a bad release automatically). |
| **Recommendation** | Add automated release rollback (PyPI yank) triggered by post-publish smoke test failures. When IaC is introduced (per INF-Q10 recommendation), extend the CI/CD pipeline to include `terraform plan` on PR and `terraform apply` on merge. |
| **Evidence** | `.github/workflows/tests.yaml`, `.github/workflows/build.yaml`, `.github/workflows/codeql.yml`, `.github/workflows/benchmarks.yaml`, `.github/workflows/plugin_tests.yaml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | DVC is written in Python with support for Python 3.9 through 3.14 (as specified in `pyproject.toml` classifiers). The project uses modern Python tooling: `setuptools>=77` with `setuptools_scm[toml]>=8` for builds, `ruff` for linting and formatting, `mypy==1.19.1` for static type checking, `uv` for fast dependency resolution in CI. Dependencies include modern cloud-native libraries: `fsspec>=2024.2.0` for filesystem abstraction, `rich>=12` for CLI output, `hydra-core>=1.1` for configuration management, `requests>=2.22` for HTTP, and the `dvc-s3`, `dvc-gs`, `dvc-azure` plugin ecosystem for cloud storage integration. AWS SDK access is through the `dvc-s3` plugin (which uses `boto3`/`s3fs`). |
| **Gap** | None. Python 3.9+ with a modern framework ecosystem and first-class AWS SDK coverage (via plugins) is a Score 4 language/framework combination. |
| **Recommendation** | Continue tracking Python version support. Consider dropping Python 3.9 when it reaches EOL (October 2025) to simplify the test matrix. The current 6-version support (3.9-3.14) is comprehensive. |
| **Evidence** | `pyproject.toml` (requires-python, classifiers, dependencies, build-system), `.pre-commit-config.yaml` (ruff, mypy, codespell) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | DVC is a single deployable unit (PyPI package) with well-organized modular architecture. The codebase is structured into clearly separated modules: `dvc/commands/` (CLI command handlers — 40+ command modules), `dvc/repo/` (repository operations — 30+ modules including experiments, metrics, params, plots), `dvc/fs/` (filesystem abstractions), `dvc/utils/` (shared utilities), `dvc/parsing/` (YAML/config parsing), `dvc/stage/` (pipeline stage management), `dvc/dependency/` (dependency tracking). The plugin architecture (`dvc-s3`, `dvc-gs`, `dvc-azure`, etc.) externalizes storage backends as independently versioned packages with defined interfaces. The `Repo` class (`dvc/repo/__init__.py`) is the central coordinator with clear method delegation to sub-modules. Module boundaries are well-defined with no circular dependency evidence. |
| **Gap** | This is a modular monolith with clear module boundaries and a plugin architecture, which is the appropriate design for a CLI tool. The `Repo` class is a large coordinator that imports ~30 methods from sub-modules — while well-organized, it serves as a central coupling point. The experiment queue subsystem (`dvc/repo/experiments/queue/`) is a self-contained module that could theoretically be a separate service but is correctly embedded for a CLI tool. |
| **Recommendation** | Maintain the current modular monolith architecture — it is appropriate for a CLI tool. Continue evolving the plugin architecture for storage backends. If experiment queue management becomes a shared service (e.g., for DVC Studio), consider extracting it as an independent microservice. |
| **Evidence** | `dvc/repo/__init__.py` (Repo class with method delegation), `dvc/commands/` (40+ command modules), `dvc/fs/` (filesystem abstraction), `pyproject.toml` (plugin dependencies: dvc-s3, dvc-gs, dvc-azure) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Sync request/response is the correct design — DVC is a CLI tool where each command executes synchronously. The user invokes `dvc push`, `dvc pull`, `dvc repro`, etc. and waits for completion. There is no inter-service communication to evaluate for async patterns. The outbound HTTPS calls to Studio (`dvc/utils/studio.py`) and remote storage are synchronous client calls, which is correct for a CLI tool. Async communication is not needed and would add operational complexity without benefit. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `dvc/cli/__init__.py` (synchronous `main()` entry point), `dvc/utils/studio.py` (synchronous HTTP client calls) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. No operations exceed 30 seconds in a server-context sense — DVC CLI commands like `dvc push` or `dvc repro` may take minutes for large datasets, but these are user-initiated CLI operations with progress bars (`tqdm`), not server-side request handlers. The user is at the terminal watching progress. The experiment queue (`dvc/repo/experiments/queue/`) handles long-running experiment execution by queuing tasks locally via Celery, which is an appropriate pattern for a CLI tool. Long-running process handling in the server sense is not applicable by design. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `dvc/progress.py` (Tqdm progress bars), `dvc/repo/experiments/queue/celery.py` (local task queue), `dvc/fs/callbacks.py` (TqdmCallback for transfer operations) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | DVC does not expose an HTTP API, so traditional URL-based API versioning does not apply. However, DVC has implicit versioning concerns: (1) The CLI command interface evolves across versions — commands are added, deprecated, and modified. (2) The DVC file format (`.dvc` files, `dvc.yaml`, `dvc.lock`) has versioning implications for backward compatibility. (3) The Python API (`dvc/api/`) provides programmatic access. (4) The Studio webhook integration (`dvc/utils/studio.py`) posts data with `"client": "dvc"` but no explicit version field. (5) The `dvc/config_schema.py` uses `DEPRECATED` markers for obsoleted config options (e.g., `no_traverse`, `protected`, `row_limit`), showing a deprecation-aware approach. Semantic versioning is used via `setuptools_scm` for package versions. |
| **Gap** | No explicit API versioning strategy for the programmatic API (`dvc/api/`), no version field in Studio webhook payloads, and no formal CLI compatibility policy documented in the repository. The DEPRECATED markers in config schema show awareness but ad hoc application. |
| **Recommendation** | Add a version field to Studio webhook payloads (`"client_version": dvc.__version__`) for backward-compatible API evolution. Document a CLI compatibility policy (e.g., deprecation warnings for one major version before removal). Consider versioning the Python API if it is intended as a stable interface. |
| **Evidence** | `dvc/config_schema.py` (DEPRECATED markers), `dvc/utils/studio.py` (`"client": "dvc"` without version), `dvc/version.py`, `pyproject.toml` (setuptools_scm) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All service endpoints are hardcoded or user-configured as static strings. Remote storage endpoints are configured in `.dvc/config` files with hardcoded URLs (e.g., `s3://bucket/path`, `gs://bucket/path`). The Studio URL defaults to `https://studio.datachain.ai` (hardcoded in `dvc/utils/studio.py` as `STUDIO_URL`). The analytics endpoint defaults to `https://analytics.dvc.org` (hardcoded in `dvc/analytics.py`). All endpoint configuration is via static config files, environment variables, or hardcoded defaults — no dynamic service discovery mechanism exists. |
| **Gap** | All endpoints are static — changes require user config updates or code changes. There is no service registry, DNS-based discovery, or API catalog. |
| **Recommendation** | For a CLI tool, static endpoint configuration via user config files is acceptable and standard practice. If DVC's backend services evolve into a service mesh, consider using DNS-based service discovery or AWS Cloud Map. For now, maintain the current approach but consider externalizing the hardcoded default URLs (`STUDIO_URL`, analytics endpoint) into a discoverable configuration service. |
| **Evidence** | `dvc/utils/studio.py` (`STUDIO_URL = "https://studio.datachain.ai"`), `dvc/analytics.py` (analytics endpoint URL), `dvc/config_schema.py` (remote URL configuration) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | DVC is fundamentally a tool for managing data stored in cloud object storage. It natively supports S3 (`dvc-s3` plugin), GCS (`dvc-gs`), Azure Blob (`dvc-azure`), and other storage backends via the `fsspec` filesystem abstraction. The `dvc/data_cloud.py` DataCloud class manages push/pull/status operations against remote object storage. Data is stored in S3 (or equivalent) with content-addressable hashing via the `dvc-data` library (hash-file operations). DVC enables users to version and access unstructured data (datasets, models, any file) in managed object storage. |
| **Gap** | DVC stores data in S3 but does not include an automated parsing or extraction pipeline for the stored data. There is no Textract integration, no document parsing pipeline, and no search/indexing capability over the stored artifacts. The tool manages storage lifecycle but not data understanding. |
| **Recommendation** | Consider integrating Amazon Textract or other parsing capabilities for document-type artifacts stored via DVC. This would enable ML teams to programmatically extract and index content from unstructured datasets managed by DVC. Use Amazon Bedrock (aligned with preferences) for intelligent data cataloging of DVC-managed artifacts. |
| **Evidence** | `dvc/data_cloud.py` (DataCloud class with push/pull/status), `dvc/cachemgr.py` (cache management with hash-file ODB), `pyproject.toml` (dvc-s3, dvc-gs, dvc-azure optional dependencies) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | DVC has a well-architected unified data access layer. The `dvc/data_cloud.py` DataCloud class provides a single point of access for all remote storage operations (push, pull, status). The `Remote` class encapsulates storage backend configuration with a consistent `odb` (Object Database) interface via `dvc_data.hashfile.db`. The `dvc/cachemgr.py` CacheManager provides unified local cache access. The `dvc/fs/` module provides filesystem abstractions (`FileSystem`, `DVCFileSystem`, `DataFileSystem`, `GitFileSystem`) that normalize access patterns across different storage backends. The `dvc/database.py` Client class provides a separate, cleanly isolated data access layer for the `import-db` feature using SQLAlchemy. All data access goes through well-defined abstractions — no scattered database connections or direct storage calls throughout the code. |
| **Gap** | None. The data access architecture is mature with clear abstractions and a single point of control. |
| **Recommendation** | Maintain the current unified data access layer. Consider documenting the ODB (Object Database) abstraction as a formal internal API for plugin developers. |
| **Evidence** | `dvc/data_cloud.py` (DataCloud/Remote classes), `dvc/cachemgr.py` (CacheManager), `dvc/fs/` (filesystem abstractions), `dvc/database.py` (SQLAlchemy client for import-db) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | DVC does not deploy any database engine — the `dvc/database.py` module provides a generic SQLAlchemy client for the `import-db` command that connects to user-specified databases via URL. The SQLAlchemy dependency is version-pinned in test dependencies: `sqlalchemy>=1,<3` (`pyproject.toml` `[project.optional-dependencies.tests]`). The `dvc/config_schema.py` `db` section accepts user-provided connection URLs without validating engine type or version. DVC itself uses SQLite internally (via `dvc_data.index.DataIndex.open("db.db")`) for the local data index, using Python's built-in `sqlite3` module — no separate engine deployment or version management needed. |
| **Gap** | The SQLAlchemy version range (`>=1,<3`) is very broad — it allows SQLAlchemy 1.x (approaching legacy status) and 2.x. No validation of the user-specified database engine version is performed by the `import-db` feature, which means users could connect to EOL database engines without warning. |
| **Recommendation** | Narrow the SQLAlchemy version range to `>=2.0,<3` to ensure modern SQLAlchemy features and avoid legacy 1.x patterns. Consider adding an optional warning when `import-db` connects to database engines known to be at or past EOL. |
| **Evidence** | `pyproject.toml` (sqlalchemy>=1,<3 in test dependencies), `dvc/database.py` (SQLAlchemy `create_engine` usage), `dvc/config_schema.py` (db config schema), `dvc/repo/__init__.py` (DataIndex using SQLite) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs exist in the DVC codebase. All business logic is in the Python application layer. The `dvc/database.py` module uses standard SQLAlchemy with generic SQL (`conn.exec_driver_sql("select 1")` for connection testing, `pd.read_sql(self.sql, self.con)` for data export). No `.sql` migration files, no `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION` statements were found. The data index uses SQLite through `dvc_data` library abstractions with no raw SQL in the DVC codebase. |
| **Gap** | None. All business logic is cleanly in the Python application layer with no database-level logic coupling. |
| **Recommendation** | Maintain the current approach of keeping all business logic in the application layer. This provides maximum database portability and simplifies any future database engine changes. |
| **Evidence** | `dvc/database.py` (standard SQLAlchemy usage, no stored procedures), absence of `.sql` files in repository, `dvc/repo/__init__.py` (DataIndex via dvc_data abstractions) |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or cloud audit logging is defined in this repository. DVC is a CLI tool that does not deploy cloud infrastructure. The tool has application-level logging via `dvc/logger.py` (Python `logging` module with custom `ColorFormatter`, `LoggerHandler`, and TRACE level), but this is client-side console logging, not audit logging. The analytics system (`dvc/analytics.py`) sends anonymized usage reports to `analytics.dvc.org` but this is telemetry, not audit logging — it does not record who performed what actions on which data. |
| **Gap** | No audit trail for DVC operations. When users `dvc push`, `dvc pull`, or modify data, there is no immutable log of these actions. For ML governance and compliance (model lineage, data access auditing), this is a gap. |
| **Recommendation** | Add structured audit logging for data-sensitive operations (push, pull, import, checkout) that can be forwarded to a centralized log system. Consider integrating with CloudTrail Data Events for S3 operations performed by DVC. For ML governance, log experiment operations with user identity, timestamp, and data hashes to enable lineage tracking. |
| **Evidence** | `dvc/logger.py` (client-side logging only), `dvc/analytics.py` (anonymized telemetry, not audit), absence of `aws_cloudtrail` in any file |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no database, S3 bucket, EBS volume, or similar managed storage is provisioned by this codebase. DVC is a client tool that writes to user-configured remote storage; encryption at rest is the responsibility of the remote storage provider (e.g., S3 server-side encryption configured by the user). DVC does support S3 SSE configuration in `dvc/config_schema.py` (`sse`, `sse_kms_key_id`, `sse_customer_algorithm`, `sse_customer_key`), allowing users to configure encryption for their S3 remotes. SEC-Q2 does not apply to the tool itself. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `dvc/config_schema.py` (S3 SSE config options), surface flag `has_at_rest_data_surface=false` |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | DVC does not expose any HTTP API endpoints, so per-request authentication does not apply in the traditional sense. However, DVC makes outbound authenticated calls: (1) Studio integration (`dvc/utils/studio.py`) uses bearer token auth (`Authorization: token {token}`) for webhook notifications — this is a simple token, not OAuth2/JWT. (2) Remote storage authentication varies by backend — S3 uses AWS credentials (`access_key_id`, `secret_access_key`, `session_token` in `dvc/config_schema.py`), GCS uses `credentialpath`, Azure uses `connection_string`/`sas_token`/`account_key`, SSH uses password/key auth. (3) The `dvc studio login` command (`dvc/commands/studio.py`) implements a device-code OAuth flow via `dvc_studio_client.auth.get_access_token`. |
| **Gap** | Outbound authentication is a mix of bearer tokens, API keys, and cloud-provider-specific credentials with no unified authentication pattern. The Studio token is a static bearer token stored in DVC config, not a short-lived JWT with scopes and expiration. |
| **Recommendation** | For Studio integration, consider migrating from static bearer tokens to short-lived JWT tokens with refresh capability. The `dvc studio login` already uses an OAuth device-code flow — extend this to produce short-lived tokens with automatic refresh. For AWS remote authentication, recommend IAM roles with temporary credentials over static access keys in DVC config. |
| **Evidence** | `dvc/utils/studio.py` (bearer token auth), `dvc/commands/studio.py` (OAuth device-code login flow), `dvc/config_schema.py` (remote auth config — access_key_id, password, sas_token) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | DVC has partial centralized identity integration. The `dvc studio login` command (`dvc/commands/studio.py`) uses `dvc_studio_client.auth.get_access_token` which implements a device-code OAuth flow to authenticate with Studio (an external identity provider). This provides SSO-like functionality for Studio integration. However, remote storage authentication (S3, GCS, Azure, SSH) uses per-remote static credentials configured in `.dvc/config` — there is no centralized identity federation across remote backends. The `db` config section (`dvc/config_schema.py`) also uses per-connection `username`/`password` without IdP integration. |
| **Gap** | Identity is fragmented across multiple credential stores: Studio has its own token, each remote has its own credentials, and `import-db` uses separate database credentials. No unified identity provider spans all DVC integrations. |
| **Recommendation** | Consider supporting AWS IAM Identity Center (SSO) for unified authentication across S3 remotes and DVC Studio. Support OIDC-based authentication for remote backends where possible, reducing the need for static credential configuration. |
| **Evidence** | `dvc/commands/studio.py` (OAuth device-code flow for Studio), `dvc/config_schema.py` (per-remote credentials: access_key_id, password, sas_token, client_secret), `dvc/config_schema.py` (db section with username/password) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No plaintext credentials are hardcoded in the DVC source code. Credentials are managed through two mechanisms: (1) DVC config files (`.dvc/config`, `.dvc/config.local`) where users store remote passwords, access keys, tokens — these are user-managed config files, not version-controlled by default (`.dvc/config.local` is gitignored). (2) Environment variables (`DVC_STUDIO_TOKEN`, AWS credential env vars, `DVC_SQLALCHEMY_ECHO`). The `dvc/config_schema.py` defines credential fields (`password`, `secret_access_key`, `session_token`, `client_secret`, `sas_token`, etc.) as plain string config values. No rotation is configured. No integration with AWS Secrets Manager or HashiCorp Vault. The Studio token is stored in the global DVC config file on the user's filesystem. |
| **Gap** | Production credentials (remote storage access keys, database passwords, Studio tokens) are stored in unencrypted config files or environment variables with no rotation capability. This is Score 2: no plaintext in source control, but credentials are in plain config files and env vars without encryption or rotation. |
| **Recommendation** | Add optional integration with AWS Secrets Manager for remote storage credentials — users could reference secrets by ARN instead of storing plaintext values in DVC config. Support credential helper plugins (similar to git credential helpers) for dynamic credential retrieval. Consider encrypting sensitive fields in `.dvc/config.local`. |
| **Evidence** | `dvc/config_schema.py` (credential fields: password, secret_access_key, session_token, client_secret), `dvc/env.py` (DVC_STUDIO_TOKEN env var), `dvc/commands/studio.py` (token saved to global config file) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployed compute resources exist to harden or patch. DVC is a CLI tool installed via `pip`/`conda` on user machines. There are no EC2 instances, containers, or serverless functions to apply SSM Patch Manager, vulnerability scanning, or hardened base images to. The `tests/docker-compose.yml` runs a test git-server container but this is not a production workload. |
| **Gap** | No compute hardening applicable — structural limitation of a CLI tool. Dependency vulnerability management exists (Dependabot, CodeQL) but is covered under SEC-Q7. |
| **Recommendation** | If DVC backend services are deployed on compute infrastructure, use Bottlerocket or AL2023 hardened AMIs on EKS nodes (aligned with preferences). Enable AWS Inspector for continuous vulnerability scanning. For the CLI tool itself, ensure the published PyPI package is built on clean, audited CI runners (currently using GitHub-hosted runners, which are reasonably hardened). |
| **Evidence** | `tests/docker-compose.yml` (test-only container), absence of any production compute definition |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | DVC has solid security tooling in the CI/CD pipeline: (1) **CodeQL** (`codeql.yml`) — SAST analysis with `security-extended` query suite running on push, PR, and weekly schedule. (2) **Dependabot** (`.github/dependabot.yml`) — daily dependency vulnerability scanning for both pip and GitHub Actions dependencies with automated PR creation. (3) **Pre-commit hooks** (`.pre-commit-config.yaml`) — `ruff` with security-related lint rules enabled (`S` = flake8-bandit security rules), `codespell` for typo detection. (4) **mypy** type checking with strict settings (`check_untyped_defs`, `strict_equality`, `warn_unreachable`). The ruff configuration enables security-focused rules: `S` (bandit), `BLE` (blind exceptions), `T10` (debugger), among others. |
| **Gap** | No container image scanning (no Dockerfile for production), no DAST (no deployed API to test against), and no explicit security gate that blocks merge on critical findings — CodeQL results are uploaded to GitHub Security tab but it's unclear if a SARIF-based PR check blocks merge on critical findings. |
| **Recommendation** | Add an explicit security gate to the CI pipeline that blocks merges on critical/high severity CodeQL findings. Consider adding `pip-audit` to the CI pipeline for Python-specific vulnerability scanning (complementing Dependabot). If containers are introduced, add ECR image scanning or Trivy container scanning. |
| **Evidence** | `.github/workflows/codeql.yml` (CodeQL with security-extended queries), `.github/dependabot.yml` (daily pip + github-actions scanning), `.pre-commit-config.yaml` (ruff with S rules, codespell), `pyproject.toml` (ruff lint select includes "S" for bandit) |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing is instrumented. DVC uses Python's built-in `logging` module via `dvc/logger.py` with custom formatters (ColorFormatter), log levels (including a custom TRACE level below DEBUG), and stream handlers. The logging setup (`dvc/logger.py:setup()`) configures handlers for stdout/stderr with color formatting and level filtering. There is no OpenTelemetry SDK, X-Ray instrumentation, or trace ID propagation in the codebase. The `iterative-telemetry` dependency provides anonymized usage telemetry but not distributed tracing. |
| **Gap** | No trace ID propagation across DVC → remote storage → Studio boundaries. When debugging issues like "why did `dvc push` to S3 fail?", there is no correlated trace that spans the CLI invocation, the storage API calls, and the Studio webhook notification. |
| **Recommendation** | Add OpenTelemetry instrumentation to DVC's core operations (push, pull, repro, experiments). Instrument the `dvc/data_cloud.py` DataCloud class, the `dvc/utils/studio.py` Studio client, and the `dvc/database.py` import-db client with trace spans. Propagate trace IDs in outbound HTTP headers (W3C Trace Context / `traceparent`). This would benefit both DVC developers and users diagnosing remote storage issues. |
| **Evidence** | `dvc/logger.py` (Python logging only, no tracing), `dvc/log.py` (logger setup), `pyproject.toml` (`iterative-telemetry` for usage analytics, not tracing) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no user-facing surface for which SLOs are meaningful. DVC is a CLI tool — its "availability" is determined by PyPI package availability and the user's local environment. Response time is bounded by local disk I/O and remote storage API latency, not by DVC's own infrastructure. OPS-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | Surface flags `has_api_surface=false`, `has_persistent_data_store=false` |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | DVC collects anonymized usage telemetry via `dvc/analytics.py` and the `iterative-telemetry` library. The analytics system captures: DVC version, OS information, command class name, return code, remote types in use, SCM class, and a hashed git remote path. Reports are sent to `analytics.dvc.org` as JSON via HTTP POST in a background daemon process. This is infrastructure/usage telemetry — it tracks which commands are run and on what platforms, not business outcomes like "datasets versioned per day" or "experiment success rate". Analytics can be disabled via `DVC_NO_ANALYTICS` env var or `core.analytics=false` config. |
| **Gap** | No business outcome metrics. Usage telemetry tracks command execution but not: data volume managed, push/pull success rates, experiment completion rates, cache hit ratios, or time-to-reproduce metrics that would inform product decisions and modernization priorities. |
| **Recommendation** | Add opt-in business metrics for key outcomes: cache hit rate (local vs remote), push/pull data volume, experiment queue throughput, and pipeline reproduction success rate. These metrics would inform product roadmap decisions and identify user pain points. Consider publishing metrics to CloudWatch Custom Metrics via Amazon EventBridge (aligned with preferences). |
| **Evidence** | `dvc/analytics.py` (usage telemetry system), `dvc/env.py` (DVC_NO_ANALYTICS, DVC_ANALYTICS_ENDPOINT env vars) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting is configured. DVC is a CLI tool with no deployed infrastructure to monitor. The GitHub Actions workflows have a Slack notification for CI failures on main (`tests.yaml`: `rtCamp/action-slack-notify` when tests fail on main), but this is CI failure notification, not runtime anomaly detection. There are no CloudWatch alarms, no error rate monitoring, no latency alerting. |
| **Gap** | No anomaly detection for DVC's supporting services. If the analytics endpoint (`analytics.dvc.org`) or Studio webhook integration experiences elevated error rates, there is no alerting mechanism in this repository. |
| **Recommendation** | If the analytics endpoint and Studio webhook are owned by this team, implement CloudWatch anomaly detection on error rates and latency. For the open-source CLI, consider publishing a status page for DVC's backend services. The Slack integration for CI failures is a good start — extend it to cover production service health. |
| **Evidence** | `.github/workflows/tests.yaml` (Slack notification on CI failure), absence of CloudWatch alarms or monitoring configuration |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | DVC uses a two-stage deployment strategy for PyPI publishing: (1) **test-pypi** — every push to main and every published release uploads to `test.pypi.org` first via `pypa/gh-action-pypi-publish` with `skip-existing: true`. (2) **pypi** — only published releases are uploaded to `pypi.org`. The build pipeline (`build.yaml`) includes: `uv build` for package creation, `twine check --strict` for package validation, artifact upload between jobs, and OIDC-based authentication (`id-token: write`) for trusted publishing. The `alls-green` check gate in `tests.yaml` ensures all test matrix entries pass before the "check" job succeeds. |
| **Gap** | The test-pypi → pypi promotion is a form of staged deployment, but there is no automated smoke test of the test-pypi package before promoting to pypi. The promotion is trigger-based (GitHub release event), not validation-based. No canary release mechanism for gradual user adoption of new versions. |
| **Recommendation** | Add an automated smoke test job that installs the test-pypi package and runs a subset of functional tests before the pypi publish step proceeds. Consider a beta/RC release channel for early adopters before promoting to stable release. |
| **Evidence** | `.github/workflows/build.yaml` (test-pypi and pypi publish stages, OIDC auth, twine check), `.github/workflows/tests.yaml` (alls-green check gate) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | DVC has a comprehensive test suite organized into three tiers: (1) **Unit tests** (`tests/unit/`) — 25+ test modules covering CLI, commands, data, dependencies, filesystem, output, remote, rendering, repository, SCM, and stage operations. (2) **Functional tests** (`tests/func/`) — 50+ test modules covering end-to-end command execution: add, checkout, commit, data cloud, diff, import, import-db, init, lock, ls, metrics, params, plots, remove, repro, run, status, and more. (3) **Integration tests** (`tests/integration/`) — focused tests for Studio live experiments and plots. The test infrastructure uses `pytest-docker` (`tests/docker-compose.yml` with git-server for SSH tests), `pytest-cov` for coverage, `pytest-xdist` for parallel execution, `pytest-mock`, and `pytest-timeout`. Coverage is reported to Codecov with a 2% threshold. Benchmarks (`dvc/testing/benchmarks/`) run on PRs with regression detection. |
| **Gap** | Integration tests are limited in scope — `tests/integration/` contains only Studio-related tests and plots tests. The bulk of testing is functional (single-process end-to-end) rather than true cross-service integration. No contract tests exist for the Studio webhook API. Plugin compatibility is tested separately in `plugin_tests.yaml` but only for `dvc-s3`. |
| **Recommendation** | Expand integration tests to cover more remote storage backends (beyond the SSH git-server in docker-compose). Add contract tests for the Studio webhook API to detect breaking changes. Extend plugin compatibility testing beyond `dvc-s3` to include `dvc-gs` and `dvc-azure`. |
| **Evidence** | `tests/unit/` (25+ modules), `tests/func/` (50+ modules), `tests/integration/` (Studio and plots tests), `tests/docker-compose.yml` (git-server for SSH tests), `pyproject.toml` (test dependencies: pytest-docker, pytest-cov, pytest-xdist), `.github/codecov.yml` (2% threshold) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response automation exists. There are no runbooks (markdown, YAML, or JSON), no Systems Manager Automation documents, no Lambda-based remediation, and no self-healing patterns. The only operational response mechanism is the Slack notification on CI main branch failures (`tests.yaml`). No structured incident management workflow is defined. |
| **Gap** | No automated incident response for any DVC-related operational issues. If the analytics endpoint goes down, if a PyPI release is broken, or if a critical security vulnerability is discovered, response is entirely manual and ad hoc. |
| **Recommendation** | Create operational runbooks for common scenarios: broken PyPI release (yank procedure), security vulnerability disclosure, analytics endpoint outage, and Studio webhook integration failure. Automate the most critical runbook — broken release detection and automated yank — using GitHub Actions. Consider using AWS Systems Manager Automation documents for backend service incidents. |
| **Evidence** | Absence of runbook files, SSM automation documents, or remediation Lambda functions; `.github/workflows/tests.yaml` (Slack notification — only automated response) |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | DVC has basic observability configuration: (1) **Codecov** (`.github/codecov.yml`) — coverage tracking with 2% threshold, GitHub checks disabled for annotations. (2) **Slack notifications** — CI failure alerts to a Slack channel. (3) **Benchmark tracking** — `benchmarks.yaml` runs performance regression tests with `pytest-benchmark` and fails on >5% regression. However, there is no service-level dashboard, no named alarm owners, no SLO definitions, and no CODEOWNERS file for observability assets. Team attribution of monitoring responsibilities is not formalized. |
| **Gap** | Ad hoc observability — coverage tracking and CI notifications exist, but no ownership model for monitoring, no service health dashboards, and no formalized on-call rotation for backend services. |
| **Recommendation** | Add a CODEOWNERS file with explicit ownership of CI/CD workflows and observability config. Create a service health dashboard for DVC's external dependencies (PyPI, test-pypi, analytics endpoint, Studio webhook). Define on-call rotation for release management and backend service health. |
| **Evidence** | `.github/codecov.yml` (coverage config), `.github/workflows/tests.yaml` (Slack notification), `.github/workflows/benchmarks.yaml` (benchmark regression detection), absence of CODEOWNERS file |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging exists because no AWS resources are defined in this repository. DVC is a CLI tool with no IaC. There are no `default_tags` in Terraform providers, no `tags` on resources, no tag enforcement rules, and no cost allocation configuration. |
| **Gap** | No resource tagging because no resources exist. This is structural for a CLI tool repository. |
| **Recommendation** | When IaC is introduced (per INF-Q10 recommendation), establish a tagging standard from day one. Apply consistent tags for `project: dvc`, `environment: {prod/staging}`, `owner: {team}`, `cost-center: {value}` across all resources. Use Terraform `default_tags` provider configuration and AWS Tag Policies for enforcement. |
| **Evidence** | Absence of any IaC files, absence of tag configuration |

---

## Learning Materials

The following learning resources are mapped to the triggered pathways:

### Move to Modern DevOps (Triggered)
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) — Comprehensive learning plan for modern DevOps practices on AWS
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) — Foundational DevOps concepts and AWS service integration

### Move to AI (Triggered)
- [Move to AI](https://skillbuilder.aws/learning-plan/VDFEE4ACCV) — Learning plan for AI adoption on AWS
- [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ) — Foundation model access and agent building with Bedrock
- [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD) — Building AI agents with AWS services

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `pyproject.toml` | INF-Q1, INF-Q3, INF-Q11, APP-Q1, APP-Q2, APP-Q5, DATA-Q1, DATA-Q3 | Package configuration, dependencies, entry points, Python version support, build system |
| `.github/workflows/tests.yaml` | INF-Q11, OPS-Q4, OPS-Q5, OPS-Q6, OPS-Q8 | CI test pipeline — multi-OS/multi-Python matrix, coverage, Slack notifications |
| `.github/workflows/build.yaml` | INF-Q11, OPS-Q5 | Build and publish pipeline — test-pypi → pypi staged deployment |
| `.github/workflows/codeql.yml` | INF-Q11, SEC-Q7 | CodeQL SAST analysis with security-extended queries |
| `.github/workflows/benchmarks.yaml` | INF-Q11, OPS-Q8 | Performance benchmark regression testing on PRs |
| `.github/workflows/plugin_tests.yaml` | INF-Q11, OPS-Q6 | Cross-repository plugin compatibility testing |
| `.github/dependabot.yml` | SEC-Q7 | Daily dependency vulnerability scanning for pip and GitHub Actions |
| `.github/codecov.yml` | OPS-Q8 | Coverage reporting configuration with 2% threshold |
| `.pre-commit-config.yaml` | SEC-Q7 | Pre-commit hooks: ruff (with bandit security rules), codespell, mypy, DVC hooks |
| `dvc/cli/__init__.py` | INF-Q1, INF-Q4, INF-Q6, APP-Q3 | CLI entry point — synchronous `main()` function |
| `dvc/repo/__init__.py` | APP-Q2, DATA-Q3 | Repo class — central coordinator with modular method delegation |
| `dvc/data_cloud.py` | INF-Q4, DATA-Q1, DATA-Q2, OPS-Q1 | DataCloud/Remote classes — unified data access for remote storage |
| `dvc/database.py` | INF-Q2, DATA-Q2, DATA-Q3, DATA-Q4 | SQLAlchemy-based database client for `import-db` command |
| `dvc/config_schema.py` | INF-Q2, SEC-Q2, SEC-Q3, SEC-Q4, SEC-Q5, APP-Q5, APP-Q6 | Configuration schema with remote credentials, db config, deprecation markers |
| `dvc/cachemgr.py` | DATA-Q1, DATA-Q2 | Cache management with hash-file ODB abstraction |
| `dvc/analytics.py` | SEC-Q1, OPS-Q3 | Anonymized usage telemetry system |
| `dvc/logger.py` | OPS-Q1 | Python logging setup — ColorFormatter, LoggerHandler, TRACE level |
| `dvc/log.py` | OPS-Q1 | Logger module for DVC — LoggerWithTrace class |
| `dvc/env.py` | SEC-Q5 | Environment variable definitions including DVC_STUDIO_TOKEN |
| `dvc/utils/studio.py` | INF-Q6, SEC-Q1, SEC-Q3, APP-Q3, APP-Q6 | Studio HTTP client — bearer token auth, webhook notifications |
| `dvc/commands/studio.py` | SEC-Q3, SEC-Q4 | Studio CLI commands — login (OAuth device-code flow), logout, token |
| `dvc/repo/experiments/queue/celery.py` | INF-Q3, INF-Q4 | Local Celery-based experiment queue management |
| `dvc/fs/` | APP-Q2, DATA-Q2 | Filesystem abstractions — FileSystem, DVCFileSystem, DataFileSystem, GitFileSystem |
| `dvc/commands/` | APP-Q2 | 40+ CLI command modules with clear separation of concerns |
| `dvc/progress.py` | APP-Q4 | Tqdm progress bar integration for CLI operations |
| `dvc/fs/callbacks.py` | APP-Q4 | TqdmCallback for transfer progress tracking |
| `dvc/version.py` | APP-Q5 | Version management via setuptools_scm |
| `tests/docker-compose.yml` | INF-Q1, SEC-Q6 | Test-only git-server container definition |
| `tests/unit/` | OPS-Q6 | 25+ unit test modules |
| `tests/func/` | OPS-Q6 | 50+ functional test modules |
| `tests/integration/` | OPS-Q6 | Integration tests for Studio and plots |
| `README.rst` | Quick Agent Wins | Project documentation with comprehensive description |
| `CONTRIBUTING.md` | Quick Agent Wins | Link to contribution guide at dvc.org |

