# Modernization Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | arrow |
| **Date** | 2026-04-30 |
| **TD Version** | 3g1iuew7esd4bia3qcdwvael |
| **Repo Type** | application |
| **Service Archetype** | stateless-utility (auto-detected) |
| **Priority** | P2 |
| **Tags** | python, library |
| **Context** | Python library for human-friendly date and time handling. |
| **Surface Flags** | has_persistent_data_store=false, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=false, has_multi_instance_deployment=false |
| **Overall Score** | **1.93 / 4.0** |

**Archetype Justification**: No database connections, no writes, no HTTP/gRPC API endpoints, no message queues, and no downstream service calls detected. All operations are pure stateless computation on datetime objects (parsing, formatting, shifting, humanizing). Classified as stateless-utility.

> **Note:** While `repo_type` is set to `application`, the repository context and tags describe a Python library published to PyPI with no deployment infrastructure. Surface flags are all `false`, which gates several infrastructure and operations questions as Not Evaluated. This accurately reflects the library nature of this codebase within the `application` analysis framework.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.71 / 4.0 | 🟠 Needs Work |
| Application Architecture (APP) | 3.75 / 4.0 | ✅ Mature |
| Data Platform Modernization (DATA) | 1.75 / 4.0 | 🟠 Needs Work |
| Security Baseline (SEC) | 1.33 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.13 / 4.0 | ❌ Not Present |
| **Overall** | **1.93 / 4.0** | **🟠 Needs Work** |

**Scoring Notes:**
- **INF**: 7 of 11 questions scored (INF-Q2, INF-Q3, INF-Q8, INF-Q9 Not Evaluated). Score = (1+4+1+1+1+1+3)/7 = 12/7 ≈ 1.71
- **APP**: 4 of 6 questions scored (APP-Q3, APP-Q4 Not Evaluated). Score = (4+4+3+4)/4 = 15/4 = 3.75
- **DATA**: 4 of 4 questions scored. Score = (1+1+1+4)/4 = 7/4 = 1.75
- **SEC**: 6 of 7 questions scored (SEC-Q2 Not Evaluated). Score = (1+1+1+2+1+2)/6 = 8/6 ≈ 1.33
- **OPS**: 8 of 9 questions scored (OPS-Q2 Not Evaluated). Score = (1+1+1+1+2+1+1+1)/8 = 9/8 ≈ 1.13
- **Overall**: (1.71+3.75+1.75+1.33+1.13)/5 = 9.67/5 ≈ 1.93

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC exists — all infrastructure (if any were needed) would be manually created. | Blocks reproducible environments, disaster recovery, and automated provisioning. Triggers Move to Modern DevOps pathway. |
| 2 | INF-Q1: Managed Compute | 1 | No compute infrastructure defined — library is distributed via PyPI with no runtime deployment. | No managed compute adoption path exists. If the library were to be deployed as a service, all compute infrastructure would need to be created from scratch. Triggers Move to Containers pathway. |
| 3 | SEC-Q5: Secrets Management | 2 | PyPI API token and Codecov token stored in GitHub Secrets without rotation configuration. No dedicated secrets management service (Secrets Manager, Vault). | Secrets lack rotation and centralized lifecycle management. Acceptable for a library's publish pipeline but below best practice. |
| 4 | SEC-Q7: Application Security Pipeline | 2 | Dependabot covers GitHub Actions only — not Python dependencies. Pre-commit includes mypy and flake8 but no dedicated SAST tool (Semgrep, SonarQube). | Vulnerabilities in Python dependencies may go undetected. No dedicated security scanning gates in the CI pipeline. |
| 5 | OPS-Q6: Integration Testing | 2 | Comprehensive unit test suite (99% coverage requirement) but no integration tests against live services or external dependencies. | For a library, unit tests are the primary validation mechanism. However, cross-version compatibility testing (which exists) partially compensates. |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** INF-Q11 = 3 (CI/CD pipeline exists). GitHub Actions workflows for continuous integration and release are fully operational with multi-platform test matrices.
- **What it enables:** An agent that triggers test runs across the Python version matrix, checks build/lint status, monitors Codecov coverage trends, and manages PyPI releases via tag creation. The agent could automate the release workflow (changelog validation → tag creation → PyPI publish verification).
- **Additional steps:** The GitHub Actions API is already available. No additional configuration needed beyond agent authentication via GitHub App or PAT.
- **Effort:** Low — agent can use existing GitHub Actions API directly.

### RAG-Based Knowledge Agent

- **Prerequisite:** Comprehensive documentation exists in the repository — Sphinx docs (`docs/api-guide.rst`, `docs/guide.rst`, `docs/getting-started.rst`), `README.rst`, and `CHANGELOG.rst` provide extensive API documentation, usage guides, and release history.
- **What it enables:** A knowledge agent powered by Amazon Bedrock that indexes the Arrow documentation corpus and answers developer questions about API usage, timezone handling, date parsing formats, locale support, and migration between Arrow versions. This is particularly valuable given Arrow's rich API surface (datetime creation, formatting, shifting, humanization, dehumanization, spans, ranges, locales).
- **Additional steps:** Documentation is in reStructuredText format — needs parsing/chunking for RAG ingestion. Consider generating HTML via Sphinx first for cleaner text extraction.
- **Effort:** Medium — documentation exists but requires indexing pipeline setup and Bedrock integration.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 4 — application has well-defined module boundaries. Primary trigger not met. |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1 = 1 (no compute infrastructure); no container definitions found. Note: this is a PyPI library — containerization applies only if the library is evolved into a deployable service. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 — no proprietary SQL or commercial database engines detected. |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 is Not Evaluated (no persistent data store). Trigger condition cannot be evaluated. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 4 (sync is correct for stateless-utility). No data processing workloads detected. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (no IaC). Supporting: OPS-Q5 = 1 (no deployment strategy), OPS-Q6 = 2 (unit tests only). |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in context ("Python library for human-friendly date and time handling"). |

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model:**
Arrow has no compute infrastructure. It is a pure Python library distributed via PyPI (`pip install arrow`). There are no EC2 instances, no ECS tasks, no Lambda functions, and no Dockerfiles. The library is consumed as a dependency by other applications.

**Containerization Context:**
This pathway is technically triggered because INF-Q1 = 1 and no container definitions exist. However, Arrow is a library — not a deployable service. Containerization is relevant only if the library were to be evolved into a standalone datetime-as-a-service API. The recommendations below apply to that scenario.

**If Evolving to a Deployable Service:**
- Create a Dockerfile with a Python 3.13+ base image (slim variant for minimal footprint)
- Use Amazon EKS (preferred per analysis preferences) for container orchestration
- Store container images in Amazon ECR with image scanning enabled
- Use EKS with Fargate for serverless container execution to minimize operational overhead
- Alternatively, consider AWS Lambda for a serverless function approach — Arrow's stateless nature is ideal for Lambda's execution model

**Avoid:**
- Self-managed Kubernetes clusters (per preferences)

**Representative AWS Services:** EKS, Fargate, ECR, App Runner

**Migration Approach:** If service-ification is pursued, a refactor-then-containerize approach is recommended — add a thin API layer (FastAPI/Flask) over the existing library, then package as a container.

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 1):**
No infrastructure-as-code exists in the repository. The library has no deployment infrastructure to codify, but the CI/CD pipeline configuration itself (GitHub Actions workflows) represents the library's operational infrastructure. There are no CloudWatch alarms, no Route 53 health checks, no backup plans, and no operational resources defined in IaC.

**Current CI/CD State (INF-Q11 = 3):**
The library has a well-configured CI/CD pipeline via GitHub Actions:
- **Continuous Integration** (`.github/workflows/continuous_integration.yml`): Multi-platform test matrix (Ubuntu, macOS, Windows × Python 3.8–3.14 + PyPy), tox-based test execution, Codecov coverage reporting, linting via pre-commit, docs validation
- **Release** (`.github/workflows/release.yml`): Tag-triggered PyPI publishing via flit
- **Dependabot** (`.github/dependabot.yml`): Weekly updates for GitHub Actions dependencies only

**Deployment Strategy Gaps (OPS-Q5 = 1):**
No deployment strategy exists because this is a library published to PyPI. There is no blue/green or canary release mechanism for PyPI packages. A staged release approach (test-PyPI → production-PyPI) could be implemented.

**Testing Gaps (OPS-Q6 = 2):**
Comprehensive unit tests exist with 99% coverage requirement, but no integration tests or contract tests validate compatibility with consuming applications.

**Recommendations:**
1. **Extend Dependabot** to cover `pip` ecosystem (Python dependencies) in addition to GitHub Actions — this is a low-effort, high-impact improvement
2. **Add test-PyPI staging** to the release pipeline — publish to test.pypi.org first, validate installation, then publish to production PyPI
3. **Add SAST scanning** — integrate Semgrep or Bandit into the CI pipeline for Python-specific security analysis
4. **Add dependency vulnerability scanning** — add `pip-audit` or `safety` to the CI pipeline to catch known vulnerabilities in python-dateutil and other dependencies
5. **Consider IaC for operational resources** — if monitoring or alerting is added (e.g., PyPI download dashboards, GitHub Actions cost tracking), define those resources in IaC

**Representative AWS Services:** CodeBuild (alternative to GitHub Actions), CodePipeline, CloudWatch (for operational dashboards if needed)

**Relevant AWS Prescriptive Guidance:**
- [Getting Started with DevOps on AWS](https://docs.aws.amazon.com/prescriptive-guidance/latest/strategy-devops/welcome.html)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute infrastructure is defined anywhere in the repository. There are no Terraform files, CloudFormation templates, CDK stacks, Helm charts, or any IaC defining ECS, EKS, Lambda, Fargate, or EC2 resources. Arrow is a pure Python library published to PyPI — it has no runtime compute footprint. Users install it via `pip install arrow` and import it into their own applications. |
| **Gap** | No managed compute — the library has no deployment model. If Arrow were to be offered as a standalone service (e.g., a datetime-as-a-service API), all compute infrastructure would need to be created from scratch. |
| **Recommendation** | If the library is evolved into a deployable service, adopt EKS with Fargate (preferred per analysis preferences) or AWS Lambda for serverless execution. Arrow's stateless, pure-computation nature is ideal for Lambda's execution model. Avoid self-managed Kubernetes (per preferences). |
| **Evidence** | No `.tf`, `template.yaml`, `cdk.json`, `Dockerfile`, `Chart.yaml`, or Kubernetes manifests found in repository. `pyproject.toml` defines flit as the build system for PyPI publishing. |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy a database. No database drivers, ORM configurations, or database connection strings exist in the source code or dependencies. `requirements/requirements.txt` contains only `python-dateutil`, `backports.zoneinfo`, and `tzdata` — no database-related packages. INF-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `requirements/requirements.txt`, `pyproject.toml` (dependencies section), `arrow/` source files — no database imports. |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Workflow orchestration is not applicable by design — no multi-step workflows exist. All operations are single-call datetime computations (parse, format, shift, humanize) with no multi-service coordination, no state machines, and no sequential processing pipelines. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `arrow/api.py`, `arrow/factory.py`, `arrow/arrow.py` — all operations are synchronous, single-call, pure functions. |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | This service is a `stateless-utility`. Synchronous request/response is the correct design for this archetype — no messaging or streaming infrastructure is needed. Arrow performs pure datetime computation with no cross-service communication, no event emission, and no state changes requiring propagation. Adopting async messaging would add operational complexity without architectural benefit. |
| **Gap** | N/A — synchronous is the correct design for this archetype. |
| **Recommendation** | Async messaging is NOT recommended for this library. The current synchronous design is architecturally correct for a stateless utility performing datetime computation. |
| **Evidence** | `arrow/` source files — no SQS, SNS, Kafka, EventBridge, or messaging SDK imports. No message producers or consumers. Pure synchronous computation. |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No network infrastructure is defined. No VPC, subnets, security groups, NACLs, or network segmentation exists because there is no deployed workload. Arrow is a library consumed as a dependency — it does not expose network services. |
| **Gap** | No network security configuration. This is expected for a library with no deployment infrastructure. If the library were deployed as a service, all network infrastructure would need to be created. |
| **Recommendation** | If deploying as a service, define VPC with private subnets, least-privilege security groups, and VPC endpoints for AWS service access. Consider VPC Lattice for service-to-service networking. |
| **Evidence** | No `.tf` or IaC files containing `aws_vpc`, `aws_subnet`, or `aws_security_group` resources. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or AppSync entry point exists. Arrow is a library — it exposes a Python API (module-level functions and classes), not an HTTP/gRPC API. There is no network-level entry point to configure. |
| **Gap** | No managed API entry point. Expected for a library. If evolved into a service, an API Gateway or ALB would be needed. |
| **Recommendation** | If deploying as a service, use Amazon API Gateway (preferred per analysis preferences) as the entry point with throttling, request validation, and authentication. API Gateway pairs well with Lambda for serverless datetime-as-a-service. |
| **Evidence** | No IaC files. No `aws_api_gateway_*`, `aws_lb_*`, or `aws_appsync_*` resources. |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. There is no deployed workload to scale — Arrow is a library. No ASGs, ECS service scaling, Lambda concurrency settings, or DynamoDB auto-scaling are defined. |
| **Gap** | No auto-scaling. Expected for a library with no deployment infrastructure. |
| **Recommendation** | If deploying as a service, configure auto-scaling appropriate to the compute model. Lambda handles scaling automatically. For EKS/ECS, configure target-tracking scaling policies based on request volume. |
| **Evidence** | No IaC files. No `aws_autoscaling_*` or `aws_appautoscaling_*` resources. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no persistent state to back up. No databases, S3 buckets, EBS volumes, or other data stores are defined. Arrow is a stateless library with no data-at-rest surface. INF-Q8 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No IaC files. No `aws_rds_*`, `aws_dynamodb_*`, `aws_s3_bucket`, or `aws_backup_plan` resources. No database drivers in dependencies. |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload requiring HA evaluation. Arrow is a library published to PyPI — it has no runtime compute, no API surface, and no persistent data store. Multi-AZ deployment is not applicable. INF-Q9 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No IaC files. No compute resources, no load balancers, no database resources with `multi_az` settings. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No infrastructure-as-code files exist in the repository. No Terraform (`.tf`), CloudFormation, CDK, Helm, or Kustomize files were found. The library has no infrastructure to codify — it is published to PyPI and consumed as a dependency. The CI/CD pipeline (GitHub Actions) is defined as code in `.github/workflows/`, which is the closest equivalent to IaC for this library. |
| **Gap** | Zero IaC coverage. While this is expected for a library, if operational resources are ever needed (monitoring dashboards, alerting, PyPI publish verification), they should be defined in IaC from the start. |
| **Recommendation** | If operational infrastructure is added (e.g., CloudWatch dashboards for PyPI download monitoring, SNS alerts for build failures), define it in Terraform or CDK. For a library, the primary IaC opportunity is codifying operational/DR resources. |
| **Evidence** | No `.tf`, `template.yaml`, `template.json`, `cdk.json`, `Chart.yaml`, or `kustomization.yaml` files found anywhere in the repository. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Well-configured CI/CD pipeline exists via GitHub Actions with two workflows: (1) **Continuous Integration** (`.github/workflows/continuous_integration.yml`) — runs on PRs, pushes to master, and monthly schedule. Multi-platform test matrix: 3 OS (Ubuntu, macOS, Windows) × 8 Python versions (3.8, 3.9, 3.10, 3.11, 3.12, 3.13, 3.14, PyPy 3.11). Uses tox for test execution, Codecov for coverage reporting, and pre-commit for linting (black, flake8, mypy, isort, pyupgrade). Includes docs validation with Sphinx. (2) **Release** (`.github/workflows/release.yml`) — triggered by version tags (`*.*.*`) or manual dispatch. Publishes to PyPI via flit using PYPI_API_TOKEN stored in GitHub Secrets. |
| **Gap** | No IaC deployment track (no IaC exists to deploy). The pipeline covers application code testing and publishing but lacks security scanning stages (no SAST, no dependency vulnerability scanning for Python packages). Dependabot is configured only for GitHub Actions, not Python dependencies. Release pipeline publishes directly to production PyPI with no test-PyPI staging step. |
| **Recommendation** | (1) Add `pip-audit` or `safety` to the CI pipeline for Python dependency vulnerability scanning. (2) Extend `.github/dependabot.yml` to include `pip` package ecosystem. (3) Add a test-PyPI staging step to the release pipeline before production publish. (4) Add Semgrep or Bandit for Python SAST in the lint job. |
| **Evidence** | `.github/workflows/continuous_integration.yml`, `.github/workflows/release.yml`, `.github/dependabot.yml`, `.pre-commit-config.yaml`, `tox.ini` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Python 3.8+ with modern tooling. The library supports Python 3.8 through 3.14 and PyPy 3.11 (per `pyproject.toml` classifiers and CI matrix). Uses PEP 484 type hints throughout the codebase with a `py.typed` marker file for PEP 561 compliance. Modern typing constructs used: `Final`, `Literal`, `TypedDict`, `overload`, `Union`, `Optional`, `Generator`, `ClassVar`. Development tooling is current: black (code formatting), mypy (strict type checking per `setup.cfg`), flake8 with flake8-bugbear and flake8-annotations, isort, pyupgrade. Build system uses flit (modern PEP 517/518 compliant). No AWS SDK usage (not applicable for a datetime library). |
| **Gap** | Minimum supported Python version is 3.8, which reached end-of-life in October 2024. This is a minor gap — the library already supports 3.14 and the 3.8 support is for backward compatibility. |
| **Recommendation** | Consider dropping Python 3.8 support in the next major release to reduce maintenance burden and enable newer Python features (walrus operator, `dict | dict` merge, `match` statements, `type` aliases). This is a library-appropriate recommendation — not a cloud-native concern. |
| **Evidence** | `pyproject.toml` (classifiers, requires-python = ">=3.8"), `arrow/py.typed`, `setup.cfg` (mypy strict configuration), `.pre-commit-config.yaml` (black, flake8, mypy, isort, pyupgrade), `.github/workflows/continuous_integration.yml` (test matrix) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Well-structured modular library with clear module boundaries and clean interfaces. The package is organized into focused modules: `arrow.py` (core Arrow class, 1906 lines), `factory.py` (ArrowFactory with flexible construction), `parser.py` (DateTimeParser and TzinfoParser, 938 lines), `formatter.py` (DateTimeFormatter, 141 lines), `locales.py` (internationalization, 6655 lines), `api.py` (module-level convenience API), `util.py` (helper functions), `constants.py` (shared constants). Dependencies flow cleanly: `api.py` → `factory.py` → `arrow.py` / `parser.py` → `locales.py` / `constants.py` / `util.py`. No circular dependencies detected. Each module has a single responsibility. The `__init__.py` provides a clean public API surface. |
| **Gap** | N/A — the module structure is well-defined with clear boundaries. |
| **Recommendation** | No decomposition needed. The library's modular structure is appropriate for its purpose. |
| **Evidence** | `arrow/__init__.py`, `arrow/api.py`, `arrow/arrow.py`, `arrow/factory.py`, `arrow/parser.py`, `arrow/formatter.py`, `arrow/locales.py`, `arrow/util.py`, `arrow/constants.py` |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Sync request/response is the correct design; async not needed. Arrow is a library that performs pure datetime computation — it has no inter-service communication, no HTTP clients calling downstream services, and no message queues. All calls are synchronous function invocations within a single Python process. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `arrow/` source files — no HTTP clients (requests, httpx, aiohttp), no gRPC stubs, no message queue clients. |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. No operations exceed 30 seconds — not applicable by design. Arrow operations (datetime parsing, formatting, timezone conversion, humanization) complete in microseconds to milliseconds. There are no batch operations, no network calls, and no I/O-bound operations that could exceed 30 seconds. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `arrow/arrow.py`, `arrow/parser.py`, `arrow/factory.py` — all operations are CPU-bound pure computation with no blocking I/O. |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Library uses semantic versioning — current version is `1.4.0` (defined in `arrow/_version.py`). Releases are triggered by Git tags matching `*.*.*` pattern (per `.github/workflows/release.yml`). The library is published to PyPI where consumers pin versions in their dependency manifests. A comprehensive `CHANGELOG.rst` documents changes per release. The public API is explicitly defined via `__all__` in `arrow/__init__.py`. |
| **Gap** | No formal deprecation policy documented in code or configuration. No programmatic deprecation warnings (e.g., `warnings.warn(..., DeprecationWarning)`) for API surface changes. No API compatibility contracts beyond implicit semver promises. While semver provides the versioning framework, there is no mechanism to warn consumers of upcoming breaking changes before they happen. |
| **Recommendation** | Add deprecation warnings for API changes planned for the next major version. Document a deprecation policy (e.g., "deprecated features emit warnings for at least one minor release before removal"). Consider adding `__deprecated__` annotations or runtime `warnings.warn()` calls for any API surfaces planned for removal. |
| **Evidence** | `arrow/_version.py` (`__version__ = "1.4.0"`), `.github/workflows/release.yml` (tag-triggered publish), `CHANGELOG.rst`, `arrow/__init__.py` (`__all__` definition) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No service-to-service communication exists — Arrow is a library with no runtime service dependencies. There are no hard-coded service endpoints, no service registry integrations, no DNS-based discovery, and no environment variables pointing to downstream services. The library's only external dependency is `python-dateutil` (consumed as a Python import, not a network service). This is the correct state for a stateless utility library. |
| **Gap** | N/A — no service discovery is needed for a library. |
| **Recommendation** | No action needed. |
| **Evidence** | `arrow/` source files — no HTTP client imports, no environment variable lookups for service URLs, no service mesh configuration. `requirements/requirements.txt` — only `python-dateutil`, `backports.zoneinfo`, `tzdata`. |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No unstructured data storage exists. Arrow is a datetime computation library — it does not store, manage, or process documents, images, or other unstructured data. No S3 buckets, no Textract calls, no document parsing libraries, no file system storage patterns detected. |
| **Gap** | No unstructured data storage capability. This is expected for a datetime computation library with no data management responsibilities. |
| **Recommendation** | N/A for current use case. If the library were extended to handle date-related document parsing (e.g., extracting dates from documents), consider Amazon S3 for storage and Textract for document parsing. |
| **Evidence** | `arrow/` source files — no file I/O operations beyond Python stdlib datetime manipulation. `requirements/requirements.txt` — no S3, Textract, or document parsing dependencies. |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database connections or data access patterns exist. Arrow performs pure datetime computation — it does not query databases, access data stores, or implement repository/DAO patterns. There are no database driver imports (no SQLAlchemy, no pymongo, no redis, no JDBC), no connection pools, and no query builders anywhere in the source code. |
| **Gap** | No data access layer. This is expected for a stateless computation library with no persistent data requirements. |
| **Recommendation** | N/A for current use case. |
| **Evidence** | `arrow/` source files — imports limited to `datetime`, `calendar`, `re`, `sys`, `typing`, `dateutil`, `zoneinfo`. No database-related imports. `requirements/requirements.txt` — no database driver packages. |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database engines are used. Arrow has no database dependency — no RDS, DynamoDB, DocumentDB, or any other database engine is referenced in IaC or application code. There are no engine version pins and no EOL concerns related to databases. |
| **Gap** | No database engine version management. Expected for a library with no database usage. |
| **Recommendation** | N/A for current use case. |
| **Evidence** | No IaC files. No database connection strings or driver imports in source code. No database-related entries in `requirements/requirements.txt` or `pyproject.toml`. |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All business logic resides in the application (library) layer. Arrow's datetime computation logic — parsing, formatting, timezone conversion, humanization, dehumanization, spans, ranges — is implemented entirely in Python source code (`arrow/arrow.py`, `arrow/parser.py`, `arrow/formatter.py`, `arrow/locales.py`, `arrow/factory.py`). There are no stored procedures, no triggers, no proprietary SQL constructs, and no database coupling whatsoever. |
| **Gap** | N/A — all logic is in the application layer. This is the ideal state. |
| **Recommendation** | No action needed. The library correctly keeps all logic in the application layer. |
| **Evidence** | `arrow/arrow.py` (1906 lines of datetime logic), `arrow/parser.py` (938 lines of parsing logic), `arrow/formatter.py` (141 lines of formatting logic), `arrow/locales.py` (6655 lines of internationalization logic). No `.sql` files, no `CREATE PROCEDURE`, no ORM bypass patterns. |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging is configured. No IaC files exist that would define `aws_cloudtrail` resources, CloudWatch log groups, or log retention policies. Arrow is a library with no deployed infrastructure — there is nothing to audit-log at the infrastructure level. |
| **Gap** | No audit logging. Expected for a library with no deployment infrastructure. If the library were deployed as a service, CloudTrail would need to be enabled. |
| **Recommendation** | If deploying as a service, enable CloudTrail with log file validation and immutable storage (S3 with Object Lock). Enable CloudWatch Logs for application-level logging. |
| **Evidence** | No IaC files. No `aws_cloudtrail` or `aws_cloudwatch_log_group` resources. |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no database, S3 bucket, EBS volume, or similar. Arrow is a stateless library with no persistent storage. SEC-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No IaC files defining data stores. No `aws_s3_bucket`, `aws_rds_*`, `aws_dynamodb_*`, or `aws_ebs_*` resources. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API authentication exists because no HTTP/gRPC API endpoints exist. Arrow is a library consumed as a Python import — it does not expose network endpoints. There are no auth middleware, no API Gateway authorizers, no Cognito user pools, no OAuth2 flows, and no Bearer token validation in the codebase. |
| **Gap** | No API authentication. Expected for a library. If the library were exposed as a service, all API endpoints would need authentication. |
| **Recommendation** | If deploying as a service, implement OAuth2/JWT authentication on all endpoints via Amazon API Gateway authorizers (preferred per analysis preferences) backed by Amazon Cognito. |
| **Evidence** | `arrow/` source files — no auth-related imports, no middleware, no token validation. No API Gateway or Cognito resources in IaC. |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No identity provider integration exists. Arrow is a library that does not manage user authentication, authorization, or identity. No Cognito, Okta, SAML, or OIDC configuration detected. |
| **Gap** | No centralized identity. Expected for a utility library. |
| **Recommendation** | If deploying as a service, integrate with Amazon Cognito or an external IdP via OIDC federation. |
| **Evidence** | `arrow/` source files — no identity-related imports. No `aws_cognito_*` resources in IaC. No OIDC/SAML configuration files. |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No plaintext credentials exist in the repository source code, configuration files, or version-controlled environment files. Two secrets are used in CI/CD: (1) `PYPI_API_TOKEN` — referenced in `.github/workflows/release.yml` as `${{ secrets.PYPI_API_TOKEN }}` for PyPI publishing via flit, and (2) `CODECOV_TOKEN` — referenced in `.github/workflows/continuous_integration.yml` as `${{ secrets.CODECOV_TOKEN }}` for coverage upload. Both are stored in GitHub Secrets (encrypted at rest by GitHub). However, no rotation is configured, and GitHub Secrets is not a dedicated secrets management service (no automated rotation, no centralized key management, no audit trail beyond GitHub's own audit log). |
| **Gap** | Secrets are in GitHub Secrets without rotation configuration. No dedicated secrets management service (AWS Secrets Manager, HashiCorp Vault) is used. Rotation is not configured for either token. This is Score 2 because no plaintext credentials exist, but production credentials are kept in an environment-variable-equivalent store without rotation. |
| **Recommendation** | (1) Configure periodic rotation for the PYPI_API_TOKEN — PyPI supports scoped API tokens that can be rotated. (2) For a library project, GitHub Secrets is an acceptable secrets store, but document the rotation schedule. (3) If migrating CI/CD to AWS, use AWS Secrets Manager with rotation Lambda for CI/CD secrets. |
| **Evidence** | `.github/workflows/release.yml` (`${{ secrets.PYPI_API_TOKEN }}`), `.github/workflows/continuous_integration.yml` (`${{ secrets.CODECOV_TOKEN }}`). Searched entire repository — no `password=`, `secret=`, `api_key=` patterns in source code. No `.env` files committed. |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute resources exist to harden or patch. Arrow is a library with no EC2 instances, no containers, and no server infrastructure. No SSM Patch Manager, no AWS Inspector, no hardened AMIs, and no vulnerability scanning of compute resources. The CI runners are GitHub-hosted (managed by GitHub, not by the project). |
| **Gap** | No compute hardening. Expected for a library with no compute infrastructure. |
| **Recommendation** | If deploying as a service with containers, use hardened base images (Bottlerocket for EKS, or AWS-maintained Python images). Enable Amazon Inspector for vulnerability scanning. If using EC2, configure SSM Patch Manager. |
| **Evidence** | No Dockerfile, no IaC compute resources, no SSM configuration. `.github/workflows/` uses `ubuntu-latest`, `macos-latest`, `windows-latest` GitHub-hosted runners. |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Partial security scanning exists in the CI pipeline: (1) **Dependabot** (`.github/dependabot.yml`) is configured to update GitHub Actions dependencies weekly — but it does NOT cover the `pip` ecosystem, so Python dependency vulnerabilities (in `python-dateutil`, `backports.zoneinfo`, `tzdata`, and test dependencies) are not monitored. (2) **Pre-commit hooks** (`.pre-commit-config.yaml`) include mypy (static type checking with strict mode), flake8 with flake8-bugbear (bug-prone pattern detection) and flake8-annotations (annotation checking), pyupgrade (Python syntax modernization), and pygrep-hooks (python-no-eval, python-check-blanket-noqa, python-check-mock-methods). These provide code quality and type safety checks but are not dedicated SAST tools. (3) **No dedicated SAST** — no SonarQube, Semgrep, CodeGuru, or Bandit configured. (4) **No container scanning** — no containers exist to scan. (5) **No pip-audit or safety** in the CI pipeline for dependency vulnerability checking. |
| **Gap** | Dependabot covers GitHub Actions only, not Python dependencies. No dedicated SAST tool. No dependency vulnerability scanning for Python packages. The pre-commit hooks provide type safety and code quality but do not substitute for security-focused static analysis. |
| **Recommendation** | (1) Extend `.github/dependabot.yml` to include `package-ecosystem: "pip"` with `directory: "/"` to monitor Python dependencies. (2) Add `pip-audit` to the CI pipeline (e.g., `pip-audit -r requirements/requirements.txt` in the lint job). (3) Add Bandit or Semgrep for Python-specific SAST scanning. These are low-effort, high-value improvements for a library consumed by many downstream projects. |
| **Evidence** | `.github/dependabot.yml` (GitHub Actions only), `.pre-commit-config.yaml` (mypy, flake8, pygrep-hooks — code quality, not SAST), `.github/workflows/continuous_integration.yml` (no security scanning steps), `tox.ini` (no security tool invocations) |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumentation exists. No OpenTelemetry SDK, no X-Ray SDK, no tracing libraries in dependencies. Arrow is a library — it does not emit traces or propagate trace IDs. Note: the TD specifies that OPS-Q1 applies to libraries because "libraries can instrument tracing that propagates through dependent applications." Arrow does not currently instrument tracing that would propagate through consuming applications. |
| **Gap** | No tracing instrumentation. For a widely-used library, adding OpenTelemetry instrumentation hooks would allow consuming applications to trace datetime operations as part of their request spans — useful for profiling datetime-heavy workloads. |
| **Recommendation** | Consider adding optional OpenTelemetry instrumentation support. This could be an optional dependency (`arrow[telemetry]`) that adds span creation for high-level operations (parsing, formatting, timezone conversion) when OpenTelemetry is available in the consumer's environment. Low priority given the library's stateless nature. |
| **Evidence** | `requirements/requirements.txt` — no `opentelemetry-*`, `aws-xray-sdk`, or tracing packages. `arrow/` source files — no tracing imports or instrumentation. |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no user-facing surface for which SLOs are meaningful. Arrow is a library with no API surface (`has_api_surface=false`) and no persistent data store (`has_persistent_data_store=false`). SLO definitions (latency, availability, error budgets) do not apply to a library consumed as a dependency. OPS-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No IaC files. No API endpoints. No CloudWatch alarms or SLO definitions. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom metrics are published. No CloudWatch, no Prometheus, no StatsD, and no business metric emission exists. Arrow is a library — it does not publish metrics about business outcomes or infrastructure health. PyPI download counts (available via PyPI Stats / pypistats.org) are the closest equivalent to business metrics but are not managed by this repository. |
| **Gap** | No business metrics. For a library, relevant metrics might include PyPI download trends, GitHub issue resolution time, and test coverage trends (Codecov is configured for coverage but is a CI tool, not a business metrics platform). |
| **Recommendation** | Low priority for a library. If operational visibility is desired, consider tracking PyPI download trends and GitHub community health metrics via a lightweight dashboard. |
| **Evidence** | `arrow/` source files — no `put_metric_data`, no StatsD, no Prometheus client imports. No CloudWatch dashboard definitions. |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting is configured. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no error rate monitoring. The only monitoring-adjacent capability is Codecov (coverage trend tracking in CI) and GitHub's built-in notifications for CI failures. |
| **Gap** | No alerting. For a library, relevant alerts might include CI failure notifications, coverage regression alerts, and security advisory alerts for dependencies. |
| **Recommendation** | Low priority. Consider configuring GitHub Actions failure notifications to a team channel (Slack/Teams). Codecov already provides coverage regression detection. For dependency security, enabling Dependabot for pip (see SEC-Q7) would provide automated vulnerability alerts. |
| **Evidence** | No IaC files with alarm definitions. No `aws_cloudwatch_metric_alarm` resources. No PagerDuty/OpsGenie configuration. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy exists in the traditional sense. Arrow is published to PyPI via a tag-triggered GitHub Action (`.github/workflows/release.yml`) — this is a release pipeline, not a deployment pipeline. There is no blue/green, no canary, no rolling deployment, and no traffic shifting. The release process is: create Git tag → GitHub Action triggers → flit builds and publishes to PyPI → consumers update at their own pace via `pip install --upgrade arrow`. |
| **Gap** | No staged release mechanism. The release pipeline publishes directly to production PyPI with no intermediate validation (no test-PyPI staging, no installation verification, no smoke test of the published package). |
| **Recommendation** | Add a test-PyPI staging step: (1) Publish to test.pypi.org first. (2) Install from test.pypi.org in a clean environment. (3) Run a smoke test (import arrow, basic operations). (4) If successful, publish to production PyPI. This provides a safety net for packaging issues without adding significant complexity. |
| **Evidence** | `.github/workflows/release.yml` (direct-to-PyPI publish on tag), `tox.ini` (publish environment: `flit publish --setup-py`) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Comprehensive unit test suite exists with strict coverage requirements. Configuration in `tox.ini` sets `--cov-fail-under=99` (99% branch coverage minimum). Tests run across 8 Python versions (3.8–3.14 + PyPy 3.11) and 3 operating systems (Ubuntu, macOS, Windows) — this cross-version, cross-platform testing serves as a form of integration testing for a library, validating compatibility across diverse environments. Test files cover all modules: `tests/test_api.py`, `tests/test_arrow.py`, `tests/test_factory.py`, `tests/test_formatter.py`, `tests/test_locales.py`, `tests/test_parser.py`, `tests/test_util.py`. However, these are unit tests — they test the library in isolation, not integration with consuming applications or external systems. |
| **Gap** | No integration tests against consuming applications. No contract tests validating that Arrow's API behaves consistently when called from different frameworks (Django, Flask, FastAPI). No compatibility tests with common datetime ecosystems (pytz, pendulum, dateutil edge cases). The 99% coverage and cross-platform matrix partially compensate, making this a moderate gap rather than a critical one. |
| **Recommendation** | Consider adding compatibility tests with popular consuming frameworks (Django ORM datetime fields, SQLAlchemy DateTime columns, pandas Timestamp interop). For a library, downstream compatibility is the integration surface. |
| **Evidence** | `tox.ini` (`--cov-fail-under=99`, `--cov-branch`), `.github/workflows/continuous_integration.yml` (test matrix), `tests/` directory (8 test files) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks or incident response automation exists. No SSM Automation documents, no Lambda-based remediation, no structured incident workflow. For a library, "incidents" are typically bug reports, security advisories, or breaking changes — the response is code fixes and releases, not infrastructure remediation. |
| **Gap** | No formalized incident response. For a library, this means no documented process for responding to security vulnerabilities in Arrow's code or dependencies, no documented hotfix release procedure, and no automation for emergency releases. |
| **Recommendation** | Create a `SECURITY.md` file documenting the vulnerability disclosure process and expected response timelines. Document the hotfix release procedure (branch from tag → fix → new tag → publish). Consider automating security advisory response with GitHub Security Advisories. |
| **Evidence** | No `SECURITY.md`, no runbook files, no SSM documents, no incident response automation. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership is defined. No CODEOWNERS file for observability assets, no per-service dashboards, no alarms with named owners, and no SLO definitions with team attribution. The repository has no `CODEOWNERS` file at all. Codecov provides coverage tracking but without ownership attribution. |
| **Gap** | No observability ownership. For a library, this means no defined owner for CI health, no escalation path for build failures, and no team attribution for release quality. |
| **Recommendation** | Add a `CODEOWNERS` file to the repository root defining ownership for CI/CD configurations, test files, and release workflows. This establishes accountability for pipeline health. |
| **Evidence** | No `CODEOWNERS` file. No dashboard definitions. No alarm configurations with owners. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resources exist to tag. Arrow has no IaC, no deployed infrastructure, and no AWS resources. There are no `tags` blocks in Terraform, no `default_tags` in provider configuration, and no tag policies. |
| **Gap** | No resource tagging. Expected for a library with no AWS infrastructure. |
| **Recommendation** | N/A for current use case. If AWS infrastructure is added, implement consistent tagging from the start with `default_tags` in the Terraform AWS provider. |
| **Evidence** | No IaC files. No AWS resources to tag. |





## Learning Materials

The following learning resources are mapped to the triggered pathways:

### Move to Containers
- [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM) — Learning plan for container orchestration with EKS (preferred per analysis preferences)
- [Move to Containers with Amazon ECS](https://skillbuilder.aws/learning-plan/CDA8Y4JRRR) — Learning plan for container orchestration with ECS
- [EKS Workshop](https://www.eksworkshop.com/) — Hands-on workshop for Amazon EKS

### Move to Modern DevOps
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) — Learning plan for modern DevOps practices
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) — Foundational DevOps concepts on AWS

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `arrow/__init__.py` | APP-Q1, APP-Q2, APP-Q5 | Public API surface definition (`__all__`), module imports |
| `arrow/_version.py` | APP-Q5 | Library version (`__version__ = "1.4.0"`) |
| `arrow/api.py` | INF-Q3, APP-Q2, APP-Q3 | Module-level convenience API, clean factory delegation |
| `arrow/arrow.py` | INF-Q3, APP-Q2, APP-Q4, DATA-Q4 | Core Arrow class (1906 lines), datetime computation logic |
| `arrow/factory.py` | INF-Q3, APP-Q2, APP-Q3 | ArrowFactory with flexible datetime construction |
| `arrow/parser.py` | APP-Q2, APP-Q4, DATA-Q4 | DateTimeParser and TzinfoParser (938 lines) |
| `arrow/formatter.py` | APP-Q2, DATA-Q4 | DateTimeFormatter (141 lines) |
| `arrow/locales.py` | APP-Q2, DATA-Q4 | Internationalization support (6655 lines) |
| `arrow/util.py` | APP-Q2 | Helper functions (next_weekday, is_timestamp, validate_ordinal) |
| `arrow/constants.py` | APP-Q2 | Shared constants (MAX_TIMESTAMP, DEFAULT_LOCALE, etc.) |
| `arrow/py.typed` | APP-Q1 | PEP 561 type hint marker file |
| `pyproject.toml` | APP-Q1, INF-Q1, INF-Q2, DATA-Q1, DATA-Q2, DATA-Q3 | Build system (flit), dependencies, Python version classifiers |
| `requirements/requirements.txt` | INF-Q2, DATA-Q1, DATA-Q2, OPS-Q1, APP-Q6 | Runtime dependencies (python-dateutil, backports.zoneinfo, tzdata) |
| `requirements/requirements-tests.txt` | OPS-Q6 | Test dependencies (pytest, pytest-cov, pytest-mock, dateparser, pytz, simplejson) |
| `requirements/requirements-docs.txt` | Quick Agent Wins | Documentation build dependencies (Sphinx, sphinx_rtd_theme) |
| `.github/workflows/continuous_integration.yml` | INF-Q11, SEC-Q5, SEC-Q7, OPS-Q5, OPS-Q6 | CI pipeline with multi-platform test matrix, codecov integration |
| `.github/workflows/release.yml` | INF-Q11, SEC-Q5, OPS-Q5 | PyPI release pipeline (tag-triggered, flit publish) |
| `.github/dependabot.yml` | INF-Q11, SEC-Q7 | Dependabot configuration (GitHub Actions only, not pip) |
| `.pre-commit-config.yaml` | APP-Q1, INF-Q11, SEC-Q7 | Pre-commit hooks (black, flake8, mypy, isort, pyupgrade, pygrep-hooks) |
| `tox.ini` | INF-Q11, OPS-Q5, OPS-Q6 | Test environment config, pytest settings (99% coverage), publish environment |
| `setup.cfg` | APP-Q1 | Strict mypy configuration |
| `Makefile` | INF-Q11 | Local development workflow (build, test, lint, docs) |
| `.readthedocs.yaml` | Quick Agent Wins | ReadTheDocs configuration for documentation hosting |
| `docs/index.rst` | Quick Agent Wins | Sphinx documentation index |
| `docs/api-guide.rst` | Quick Agent Wins | API documentation (auto-generated from docstrings) |
| `docs/guide.rst` | Quick Agent Wins | User's guide with usage examples |
| `docs/getting-started.rst` | Quick Agent Wins | Getting started guide |
| `README.rst` | Quick Agent Wins | Project overview, features, quick start guide |
| `CHANGELOG.rst` | APP-Q5, Quick Agent Wins | Release history and change documentation |
