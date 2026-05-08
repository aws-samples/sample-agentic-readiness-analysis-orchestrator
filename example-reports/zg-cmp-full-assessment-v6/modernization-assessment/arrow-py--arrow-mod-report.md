# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | arrow |
| **Date** | 2026-05-07 |
| **TD Version** | modernization-assessment |
| **Repo Type** | library |
| **Priority** | P2 |
| **Tags** | python, library |
| **Context** | Python library for human-friendly date and time handling. |
| **Overall Score** | 2.96 / 4.0 |

**Surface Flags**: has_persistent_data_store=false, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=false, has_multi_instance_deployment=false

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | N/A | N/A — all questions not applicable for library | Ready |
| Application Architecture (APP) | 3.33 / 4.0 | 🟡 Partial | Needs Work |
| Data Platform Modernization (DATA) | 4.00 / 4.0 | ✅ Mature | Ready |
| Security Baseline (SEC) | 2.50 / 4.0 | 🟡 Partial | Critical |
| Operations & Observability (OPS) | 2.00 / 4.0 | 🟠 Needs Work | Needs Work |
| **Overall** | **2.96 / 4.0** | **🟡 Partial** | |

**Classification:** 🟡 **Pilot-Ready** (1 High, 3 Medium, 3 Low findings. Rule matched: "1 High → Pilot-Ready")

MOD classification treats 1 High as Pilot-Ready (a single modernization gap) rather than Remediation Required. This differs from ARA classification where 1 High is an agent-deployment gate that maps to Remediation Required.

**Scoring Notes:**
- INF: N/A (all 11 questions not applicable for library)
- APP: (3+4+4+4+3+2) / 6 = 20/6 = 3.33
- DATA: (4+4+4+4) / 4 = 16/4 = 4.00
- SEC: (1+4+2+3) / 4 = 10/4 = 2.50 (SEC-Q2, SEC-Q3, SEC-Q4 are Not Evaluated due to surface gating)
- OPS: 2/1 = 2.00 (OPS-Q2 through OPS-Q9 are N/A for library)
- Overall: (3.33 + 4.00 + 2.50 + 2.00) / 4 = 11.83/4 = 2.96

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | SEC-Q1: Audit Logging | 1 | No CloudTrail or audit logging configuration exists | No audit trail for library build/release operations |
| 2 | OPS-Q1: Distributed Tracing | 2 | No distributed tracing instrumentation in the library | Consumers cannot propagate traces through Arrow operations |
| 3 | SEC-Q6: Compute Hardening and Patching | 2 | CI runners use default images with no hardening; Dependabot covers GitHub Actions only | Build environment not hardened; Python dependency scanning absent |
| 4 | APP-Q6: Service Discovery | 2 | No formal API catalog or registry for the library's public surface | Discovery of Arrow's capabilities relies solely on documentation |
| 5 | APP-Q1: Programming Languages | 3 | Python 3.8 minimum still supported (approaching EOL); pyupgrade targets py36 | Maintaining legacy Python version support limits adoption of modern features |

---

## Quick Agent Wins

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists — comprehensive RST documentation in `docs/` directory, `README.rst`, `CHANGELOG.rst`, and Sphinx-generated API docs via ReadTheDocs.
- **What it enables:** A knowledge agent that indexes Arrow's documentation, changelog, and source docstrings to answer developer questions about date/time handling patterns, API usage, and migration between versions.
- **Additional steps:** Documentation is already structured in RST format suitable for indexing. Could generate an OpenAPI-like interface description from the typed Python API for tool-use discovery.
- **Effort:** Low

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (GitHub Actions workflows for testing, linting, and PyPI release).
- **What it enables:** An agent that monitors CI status, triggers releases, checks test coverage trends, and manages Dependabot PRs.
- **Additional steps:** GitHub Actions API is already the control surface. Agent would need repository access token.
- **Effort:** Low

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Applicable | — | — | This is a `library` repository. This pathway does not apply. |
| 2 | Move to Containers | Not Applicable | — | — | This is a `library` repository. This pathway does not apply. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 — no stored procedures or proprietary SQL. No commercial database engines detected. |
| 4 | Move to Managed Databases | Not Applicable | — | — | This is a `library` repository. This pathway does not apply. |
| 5 | Move to Managed Analytics | Not Applicable | — | — | This is a `library` repository. This pathway does not apply. |
| 6 | Move to Modern DevOps | Not Applicable | — | — | This is a `library` repository. This pathway does not apply. |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. |

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Python library supporting Python 3.8–3.14. Uses modern tooling: `pyproject.toml` with Flit (PEP 517/518), type annotations with `py.typed` marker, mypy strict mode, and modern formatting (black, isort). However, minimum supported version is Python 3.8 (EOL October 2024) and `pyupgrade` targets `--py36-plus` rather than a more recent baseline. The library uses `python-dateutil` and `backports.zoneinfo` for legacy Python versions. |
| **Gap** | Python 3.8 has reached end-of-life. The `pyupgrade --py36-plus` target is two major versions behind the minimum supported version (3.8). This limits adoption of modern Python features (walrus operator, pattern matching, `zoneinfo` stdlib). |
| **Recommendation** | Raise minimum Python version to 3.9+ to eliminate `backports.zoneinfo` dependency and align with actively supported Python versions. Update `pyupgrade` target to `--py38-plus` or `--py39-plus`. |
| **Evidence** | `pyproject.toml` (requires-python = ">=3.8", classifiers include 3.8–3.14), `.pre-commit-config.yaml` (pyupgrade args: --py36-plus), `requirements/requirements.txt` (backports.zoneinfo dependency) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | This is a well-structured Python library with clear module boundaries: `arrow.py` (core Arrow class), `parser.py` (date parsing), `formatter.py` (date formatting), `factory.py` (factory pattern), `locales.py` (internationalization), `api.py` (public module API), `util.py` (utilities), and `constants.py` (constants). Each module has a single responsibility with clean imports and no circular dependencies. The public API is explicitly defined in `__init__.py` with `__all__`. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `arrow/__init__.py`, `arrow/arrow.py`, `arrow/parser.py`, `arrow/formatter.py`, `arrow/factory.py`, `arrow/locales.py`, `arrow/api.py` |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | This is a pure computation library with no inter-service communication. All operations are synchronous in-process function calls — date creation, parsing, formatting, humanization, and timezone conversion. No HTTP clients, gRPC stubs, message queue producers, or any inter-process communication exists. Synchronous in-process execution is the correct and only applicable pattern for a date/time library. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `arrow/arrow.py`, `arrow/parser.py`, `arrow/factory.py` — no network or IPC imports |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No operations in this library approach 30 seconds. All operations are pure computation: datetime arithmetic, string parsing, string formatting, locale lookups, and timezone conversions. These are CPU-bound in-memory operations completing in microseconds to milliseconds. No I/O, no network calls, no database queries. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `arrow/arrow.py`, `arrow/parser.py`, `arrow/formatter.py` — all operations are pure computation |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The library uses semantic versioning (current version 1.4.0 in `arrow/_version.py`). Version is published in `__version__` and used by Flit for package metadata. A comprehensive `CHANGELOG.rst` documents changes per version. The library's public API is explicitly defined via `__all__` in `__init__.py`. Release tags follow `*.*.*` pattern triggering the PyPI publish workflow. |
| **Gap** | No explicit deprecation policy or deprecation warnings in the codebase for API changes. While the versioning convention exists, there is no programmatic enforcement of backward compatibility (e.g., no deprecation decorators, no API stability annotations). |
| **Recommendation** | Add explicit deprecation warnings (using Python's `warnings.warn` with `DeprecationWarning`) for any API changes before removal. Consider documenting a formal deprecation policy (e.g., "deprecated features are removed after 2 minor versions"). |
| **Evidence** | `arrow/_version.py` (__version__ = "1.4.0"), `CHANGELOG.rst`, `arrow/__init__.py` (__all__ list), `.github/workflows/release.yml` (tag-based release) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The library is discoverable via PyPI (the standard Python package registry) and has ReadTheDocs documentation. The `pyproject.toml` includes project URLs for documentation, source, and issues. However, there is no machine-readable API specification (no OpenAPI equivalent for Python libraries). Discoverability relies on documentation, docstrings, and the `py.typed` marker for IDE support. |
| **Gap** | No formal machine-readable API catalog or interface description beyond Python type stubs and docstrings. For a library, "service discovery" translates to API discoverability — the ability for tools and agents to programmatically understand the library's interface. |
| **Recommendation** | The `py.typed` marker and type annotations provide basic machine-readable API information for IDE tooling. Consider generating a structured API reference (e.g., via Sphinx autodoc JSON output) that could serve as a machine-readable interface catalog for agent-based tool discovery. |
| **Evidence** | `pyproject.toml` (project.urls), `arrow/py.typed` (type stub marker), `docs/` (Sphinx documentation), `arrow/__init__.py` (__all__ exports) |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | This library does not store or manage unstructured data. It is a pure computation library for date/time operations — no file storage, no document management, no data persistence of any kind. All data is transient (in-memory datetime objects). |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No file I/O, S3, or storage-related imports in any source file |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No database connections or data access patterns exist. The library performs pure computation on datetime objects passed in by callers. There is no data layer to evaluate. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database drivers, ORM imports, or connection configurations in any source file |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No database engines are used by this library. There are no database dependencies, IaC database resources, or database connection configurations. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database-related files or dependencies in `pyproject.toml` or `requirements/` |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or SQL of any kind. All business logic (date/time computation, parsing, formatting, localization) is implemented in the Python application layer. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No `.sql` files, no SQL-related imports, no database coupling |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging configuration exists in the repository. The library has no infrastructure and no deployed service, so CloudTrail is not directly applicable. However, there is no audit trail for build/release operations — the PyPI publish workflow (`release.yml`) has no audit logging, no signed artifacts, and no provenance attestation. |
| **Gap** | No audit trail for library build and release operations. No artifact signing, no SLSA provenance, no build attestation. PyPI token is used via secret but no audit of when/how releases are triggered beyond GitHub's built-in audit log. |
| **Recommendation** | Adopt PyPI Trusted Publishers (OIDC-based publishing) to eliminate long-lived API tokens and provide cryptographic provenance. Consider adding Sigstore signing for release artifacts to create a verifiable audit trail. Enable GitHub audit log streaming if organizational compliance requires it. |
| **Evidence** | `.github/workflows/release.yml` (FLIT_PASSWORD from secrets, no artifact signing), absence of any `.sigstore`, `cosign`, or provenance configuration |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no database, S3 bucket, EBS volume, or similar. SEC-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This library has no API surface requiring authentication. It is imported as a Python package — there are no HTTP endpoints, gRPC services, or network-accessible interfaces. SEC-Q3 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This library has no authentication system and no user identity management. It is a computation library with no user-facing surface. SEC-Q4 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No plaintext credentials in the repository. The PyPI API token is stored in GitHub Secrets (`secrets.PYPI_API_TOKEN`) and referenced in the release workflow. The Codecov token is similarly stored in GitHub Secrets (`secrets.CODECOV_TOKEN`). No `.env` files, no hardcoded passwords, no connection strings, no API keys in source code. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `.github/workflows/release.yml` (FLIT_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}), `.github/workflows/continuous_integration.yml` (token: ${{ secrets.CODECOV_TOKEN }}) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | CI runs on GitHub-hosted runners (ubuntu-latest, macos-latest, windows-latest) which receive automatic patching from GitHub. Dependabot is configured for GitHub Actions version updates (`.github/dependabot.yml`). However, Dependabot only monitors `github-actions` ecosystem — Python package vulnerabilities are not monitored. No vulnerability scanning tool (Snyk, pip-audit, Safety) is configured. No hardened runner images or container-based isolation. |
| **Gap** | No Python dependency vulnerability scanning. Dependabot monitors only GitHub Actions versions, not the Python `requirements/` files or `pyproject.toml` dependencies. No CVE scanning for `python-dateutil`, `backports.zoneinfo`, or test dependencies. |
| **Recommendation** | Add `pip` ecosystem to Dependabot configuration to monitor Python dependency vulnerabilities. Alternatively, add `pip-audit` or `safety` to the CI pipeline for explicit vulnerability scanning. Consider using GitHub's native dependency review action for PR-time vulnerability checks. |
| **Evidence** | `.github/dependabot.yml` (only github-actions ecosystem), `.github/workflows/continuous_integration.yml` (no security scanning steps), `requirements/` (unmonitored Python dependencies) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The CI pipeline includes multiple code quality tools that provide partial security coverage: `flake8` with `flake8-bugbear` (catches common bugs), `mypy` in strict mode (catches type-safety issues), `pyupgrade` (modernizes code patterns), and `python-no-eval` pygrep hook (explicitly blocks eval() usage). Dependabot monitors GitHub Actions versions. Pre-commit hooks enforce code quality on every commit. However, there is no dedicated SAST tool (Bandit, Semgrep) and no dependency vulnerability scanning (pip-audit, Safety). |
| **Gap** | No dedicated SAST tool for security-specific analysis (e.g., Bandit for Python security anti-patterns). No dependency vulnerability scanning for Python packages. The existing tools provide code quality but not focused security analysis. |
| **Recommendation** | Add Bandit (Python security linter) to the pre-commit hooks or CI pipeline for SAST coverage. Add `pip-audit` as a CI step for dependency vulnerability scanning. These are low-effort additions that complement the existing quality tooling. |
| **Evidence** | `.pre-commit-config.yaml` (python-no-eval hook, flake8-bugbear, mypy strict), `.github/workflows/continuous_integration.yml` (tox -e lint), `.github/dependabot.yml` (github-actions only) |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No distributed tracing instrumentation exists in the library. No OpenTelemetry SDK, no X-Ray instrumentation, no trace context propagation. The library operates as pure computation with no awareness of distributed tracing contexts. While Arrow is typically used within applications that may have tracing, the library itself does not propagate or create trace spans for its operations. |
| **Gap** | No OpenTelemetry instrumentation. Libraries that perform significant computation (parsing, timezone conversion) can benefit from span creation so that consuming applications can attribute time spent in Arrow operations. No trace context awareness means Arrow operations appear as opaque blocks in application traces. |
| **Recommendation** | Consider adding optional OpenTelemetry instrumentation (as an optional dependency) that creates spans for parsing and timezone conversion operations. This is a common pattern for Python libraries (e.g., `opentelemetry-instrumentation-*` packages). At minimum, ensure the library does not inadvertently break trace context propagation in async contexts. |
| **Evidence** | No `opentelemetry` in any dependency file, no tracing imports in source code, no span creation patterns |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

---

## Learning Materials

No pathways triggered — no pathway-specific learning materials applicable. Refer to the [AWS SkillBuilder](https://skillbuilder.aws/) catalog for general cloud architecture training.

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `pyproject.toml` | APP-Q1, APP-Q5, DATA-Q3 | Build configuration, Python version requirements, dependencies, project metadata |
| `.pre-commit-config.yaml` | APP-Q1, SEC-Q7 | Code quality hooks including pyupgrade, flake8-bugbear, mypy, python-no-eval |
| `.github/workflows/continuous_integration.yml` | SEC-Q6, SEC-Q7, OPS-Q1 | CI pipeline with test matrix, linting, coverage upload |
| `.github/workflows/release.yml` | SEC-Q1, SEC-Q5 | PyPI release workflow with secrets-based token |
| `.github/dependabot.yml` | SEC-Q6, SEC-Q7 | Dependabot configuration (GitHub Actions only) |
| `arrow/__init__.py` | APP-Q2, APP-Q5, APP-Q6 | Public API surface definition with __all__ |
| `arrow/_version.py` | APP-Q5 | Version string (1.4.0) |
| `arrow/arrow.py` | APP-Q2, APP-Q3, APP-Q4 | Core Arrow class implementation |
| `arrow/parser.py` | APP-Q2, APP-Q4 | Date parsing module |
| `arrow/formatter.py` | APP-Q2, APP-Q4 | Date formatting module |
| `arrow/factory.py` | APP-Q2, APP-Q3 | Factory pattern for Arrow creation |
| `arrow/locales.py` | APP-Q2 | Internationalization (6,654 lines) |
| `arrow/api.py` | APP-Q2 | Module-level API facade |
| `arrow/py.typed` | APP-Q6 | PEP 561 type stub marker |
| `requirements/requirements.txt` | APP-Q1, SEC-Q6 | Core dependencies (python-dateutil, backports.zoneinfo, tzdata) |
| `requirements/requirements-tests.txt` | SEC-Q6 | Test dependencies |
| `setup.cfg` | APP-Q1 | mypy strict configuration |
| `tox.ini` | SEC-Q7 | Test runner, lint, and publish configuration |
| `CHANGELOG.rst` | APP-Q5 | Version history documentation |
| `docs/` | APP-Q6 | Sphinx documentation source |
