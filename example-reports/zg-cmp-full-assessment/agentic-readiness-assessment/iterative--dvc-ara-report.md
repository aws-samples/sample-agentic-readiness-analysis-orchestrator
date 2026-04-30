# Agentic Readiness Assessment Report

**Target**: dvc (Data Version Control)
**Date**: 2026-04-29
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application (user-provided)
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only (user-provided)
**Priority**: P2
**Tags**: python, ml, data
**Context**: Data Version Control: git-for-ML-data, models, and experiments.

**Archetype Justification**: DVC manages persistent state (local file cache, SQLite databases via dvc-data, .dvc metadata files, experiment tracking databases) and performs CRUD operations on data artifacts (add, push, pull, remove, gc). It has external dependencies (remote storage providers: S3, GCS, Azure, SSH) and uses Celery/Kombu for task queuing. This matches the stateful-crud archetype.

---

## Readiness Profile: Not Agent-Integrable

**BLOCKERs**: 3 | **RISK-SAFETY**: 9 | **RISK-QUALITY**: 18 | **INFOs**: 12

Exclude from agent toolset or plan major remediation before re-evaluation. DVC in its current form is a CLI tool and Python library without HTTP/REST API surface, machine identity authentication, or data classification controls. Agents cannot safely or reliably integrate with DVC as a target system without significant architectural changes. Consider wrapping DVC functionality behind a purpose-built API service with proper authentication, authorization, audit logging, and data classification before attempting agent integration.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 3 |
| RISK-SAFETY | 9 |
| RISK-QUALITY | 18 |
| INFO | 12 |
| N/A | 0 |
| Not Evaluated (extended) | 1 |
| **Total** | **43** |

*Note: AUTH-Q4 (Identity Propagation) and AUTH-Q5 (Credential Management) carry base severity "RISK" and are counted under RISK-QUALITY for summary purposes, as they are not in the RISK-SAFETY tier table and do not affect the readiness profile.*

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 18
**Extended Questions Not Triggered**: 1 (STATE-Q7)
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### API-Q1: Documented API Interface

- **Severity**: BLOCKER
- **Finding**: DVC exposes a Python programmatic API (`dvc.api` module with functions: `open`, `read`, `get_url`, `metrics_show`, `params_show`, `exp_show`, `exp_save`, `artifacts_show`, `DVCFileSystem`) and a CLI interface (`dvc` command with subcommands). It does **not** expose REST, HTTP, GraphQL, or AsyncAPI endpoints. There is no network-accessible API interface. Agent integration would require either: (a) importing the `dvc` Python package directly, (b) invoking CLI commands via subprocess, or (c) wrapping DVC behind a custom HTTP service.
- **Gap**: No documented REST/HTTP/GraphQL interface exists for remote agent consumption. The Python API and CLI are local-only integration surfaces — an agent running in a separate process, container, or service cannot call DVC over a network protocol.
- **Remediation**:
  - **Immediate**: Build a thin HTTP wrapper (e.g., FastAPI or Flask) around the `dvc.api` module exposing key operations (`read`, `get_url`, `metrics_show`, `params_show`, `exp_show`) as REST endpoints. Generate an OpenAPI specification from the wrapper.
  - **Target State**: A documented REST API with OpenAPI spec, deployed as a microservice, exposing DVC read operations for agent consumption.
  - **Estimated Effort**: Medium (2–4 weeks for initial wrapper + spec)
  - **Dependencies**: Resolves in parallel with AUTH-Q1 (the wrapper service needs authentication).
- **Evidence**: `dvc/api/__init__.py`, `dvc/api/data.py`, `dvc/api/show.py`, `dvc/api/experiments.py`, `dvc/cli/__init__.py`

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: DVC itself does not implement any authentication mechanism. Authentication is fully delegated to remote storage providers (S3 via IAM credentials, GCS via service accounts, Azure via AD/SAS tokens, SSH via keys). The `dvc/config_schema.py` shows direct credential fields (`access_key_id`, `secret_access_key`, `session_token` for S3; `credentialpath` for GCS; `client_id`/`client_secret` for Azure; `keyfile` for SSH). There is no concept of a DVC-level service account, no OAuth2 client credentials flow, and no machine identity attribution in any log or audit trail.
- **Gap**: No machine identity authentication mechanism at the DVC application layer. An agent calling DVC cannot be authenticated or attributed as a distinct principal. All callers with file system access or valid cloud credentials are indistinguishable.
- **Remediation**:
  - **Immediate**: If wrapping DVC behind an HTTP API (per API-Q1 remediation), implement OAuth2 client credentials or API key authentication on the wrapper service. Map agent identities to distinct service accounts with attributed audit logs.
  - **Target State**: Each agent identity authenticates with a distinct credential (API key or OAuth2 client ID), and every operation is logged with the authenticated principal.
  - **Estimated Effort**: Medium (2–3 weeks, concurrent with API-Q1 wrapper)
  - **Dependencies**: Depends on API-Q1 (HTTP wrapper) being built first. Identity before data access — fix this before DATA-Q1.
- **Evidence**: `dvc/config_schema.py` (credential fields), `dvc/data_cloud.py` (remote auth delegation), `dvc/config.py` (config loading)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: DVC manages arbitrary data files — ML training data, models, datasets — without any data classification or sensitivity tagging. The `.dvc` files contain only hash checksums (`md5`, `sha256`) and file metadata (`size`, `nfiles`, `path`), not the data content itself. DVC has no mechanism to classify whether tracked data contains PII, PHI, financial records, or credentials. There is no integration with AWS Macie, no field-level encryption, no data classification tags, and no access controls based on data sensitivity. The sensitivity of data depends entirely on what users choose to track — DVC itself is classification-agnostic.
- **Gap**: No data classification exists at any level. An agent with access to DVC can retrieve any tracked data without sensitivity-aware access controls. If DVC tracks datasets containing PII or regulated data, an agent could retrieve and forward that data to an LLM endpoint without any guardrails.
- **Remediation**:
  - **Immediate**: Inventory all datasets tracked by DVC and classify them by sensitivity (PII, PHI, financial, public). Implement access controls in the API wrapper service (per API-Q1) that check data classification before returning results.
  - **Target State**: Data classification metadata stored alongside `.dvc` files or in a classification registry. API wrapper enforces classification-aware access controls. Agent identities are granted access only to data classifications their use case requires.
  - **Estimated Effort**: High (4–8 weeks — requires data inventory, classification, and enforcement)
  - **Dependencies**: Depends on API-Q1 (wrapper) and AUTH-Q1 (identity) for enforcement. Classification should proceed in parallel.
- **Evidence**: `dvc/schema.py` (DATA_SCHEMA has no classification fields), `dvc/output.py`, `dvc/dvcfile.py`

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: DVC defers all permission scoping to cloud storage providers. The DVC configuration (`dvc/config_schema.py`) accepts cloud credentials directly (`access_key_id`, `secret_access_key`, `credentialpath`, etc.) but provides no mechanism to scope what a caller can do within DVC itself. Any process with valid credentials can perform any DVC operation — `push`, `pull`, `gc`, `destroy`. Permission boundaries exist only at the cloud provider level (IAM policies for S3, GCS IAM, Azure RBAC).
- **Gap**: No DVC-level scoped permissions. An agent identity cannot be granted read-only access to specific DVC-tracked artifacts without also having access to all artifacts on the same remote storage.
- **Compensating Controls**:
  - Use separate cloud provider credentials with minimal IAM policies (e.g., S3 `GetObject` only on specific prefixes) for agent access.
  - If wrapping DVC in an API service (per API-Q1), implement RBAC at the wrapper layer to restrict which operations and datasets agents can access.
- **Remediation Timeline**: 30–60 days (concurrent with API wrapper development)
- **Recommendation**: Define IAM policies scoped to the specific S3 prefixes/buckets that agents need. Implement permission middleware in the API wrapper service.
- **Evidence**: `dvc/config_schema.py` (credential fields without scope), `dvc/data_cloud.py` (uses credentials as-is)

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: DVC has no internal action-level authorization. Any caller with valid credentials can invoke any DVC operation: `dvc add`, `dvc push`, `dvc pull`, `dvc gc` (garbage collect), `dvc destroy`, `dvc remove`. There is no RBAC, no ABAC, and no permission matrix distinguishing read from write from delete operations. The CLI dispatch (`dvc/cli/__init__.py`) calls `args.func(args)` directly without any authorization check.
- **Gap**: An agent identity cannot be restricted to read operations only at the DVC level. Action-level authorization must be enforced externally.
- **Compensating Controls**:
  - Restrict agent to read-only operations at the wrapper API level (only expose `GET` endpoints for `metrics_show`, `params_show`, `read`, `get_url`, `exp_show`).
  - Use file-system-level permissions (read-only mount) to prevent the agent from modifying the DVC working directory.
- **Remediation Timeline**: 30–60 days (part of API wrapper development)
- **Recommendation**: Implement action-level authorization in the API wrapper service. Define which agent identities can invoke which DVC operations.
- **Evidence**: `dvc/cli/__init__.py` (no authorization checks), `dvc/commands/` (no permission middleware)

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: DVC has no audit logging infrastructure. The analytics module (`dvc/analytics.py`) sends usage telemetry (command class, return code, DVC version, user_id, system info, hashed git remote URL) to `analytics.dvc.org` — but this is product telemetry, not an audit trail. Standard Python logging (`dvc/logger.py`) outputs to stdout/stderr using `ColorFormatter` — not structured, not immutable, not retained. There is no CloudTrail integration, no immutable log storage, and no log file validation.
- **Gap**: No immutable audit trail for DVC operations. Cannot determine which agent (or human) performed which operation. No forensic capability for agent-initiated actions.
- **Compensating Controls**:
  - Implement structured audit logging in the API wrapper service, writing to CloudWatch Logs with log file integrity validation.
  - Configure CloudTrail for the underlying cloud storage (S3, GCS) to capture object-level operations attributed to the agent's IAM principal.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add structured JSON audit logging to the API wrapper service. Include agent identity, operation, target artifact, timestamp, and outcome. Ship logs to an immutable store (S3 with Object Lock, CloudWatch Logs).
- **Evidence**: `dvc/analytics.py` (telemetry, not audit), `dvc/logger.py` (ColorFormatter, stdout/stderr), `dvc/log.py`

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: DVC has no concept of agent identities and therefore no mechanism to suspend or revoke them. There are no API keys, no service accounts managed by DVC, and no account disable mechanisms. If an agent's credentials need to be revoked, this must happen at the cloud provider level (e.g., deactivating IAM access keys, revoking SAS tokens) — but DVC itself has no role in this process and cannot initiate or enforce suspension.
- **Gap**: No ability to suspend a specific agent identity at the DVC application layer. Suspension requires external action on cloud provider credentials.
- **Compensating Controls**:
  - If using an API wrapper, implement API key management with immediate revocation capability.
  - Use short-lived cloud credentials (STS temporary credentials with short TTL) for agents, reducing the window of exposure.
- **Remediation Timeline**: 30–60 days (part of API wrapper identity management)
- **Recommendation**: Implement API key management in the wrapper service with a `/admin/keys/{key_id}/revoke` endpoint for immediate suspension.
- **Evidence**: `dvc/config_schema.py` (no identity management), `dvc/config.py` (no account/identity concepts)

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: DVC relies on Git for rollback of metadata changes (`.dvc` files, `dvc.lock`). The command `dvc checkout` can restore the working directory to match the state described in `.dvc` files. `git revert` and `git checkout` can undo changes to DVC metadata. However, there is no explicit saga pattern, no compensating transactions, and no programmatic rollback API. Data pushed to remote storage is not automatically cleaned up if a multi-step operation fails partway through. The lock mechanism (`dvc/lock.py`, `dvc/rwlock.py`) prevents concurrent corruption but does not provide transaction rollback.
- **Gap**: No application-level compensation or rollback mechanism. Git provides metadata undo, but data pushed to remote storage cannot be automatically rolled back. No saga pattern for multi-step workflows.
- **Compensating Controls**:
  - For read-only agent scope, rollback is less critical since no write operations are performed.
  - Use Git branch-based isolation for any experimental agent workflows.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: For the API wrapper service, implement idempotent read operations with caching. If write operations are added later, implement explicit compensation endpoints.
- **Evidence**: `dvc/lock.py` (locking, not rollback), `dvc/rwlock.py` (read-write locks), `dvc/repo/checkout.py`

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: DVC does not implement circuit breakers, retry logic, or timeout configurations for its external dependency calls. Remote storage operations (push, pull, fetch) go through `dvc/data_cloud.py` → `dvc_data.hashfile.transfer` → cloud provider libraries (boto3 for S3, google-cloud-storage for GCS, etc.). DVC relies entirely on the underlying library's default timeout and retry behavior. There is no Resilience4j equivalent, no `@CircuitBreaker` annotations, no exponential backoff configuration at the DVC application level. The `dvc/config_schema.py` does expose `read_timeout` and `connect_timeout` for some remote types (S3, HTTP, Azure), but these are pass-through to the underlying library.
- **Gap**: No circuit breaker pattern. A runaway agent making repeated DVC calls that fail against a degraded remote storage will continue to bombard the storage provider without backing off at the DVC application level.
- **Compensating Controls**:
  - Implement circuit breakers in the API wrapper service (e.g., using `pybreaker` or `tenacity` with circuit breaker mode).
  - Set conservative timeouts in DVC remote configuration (`read_timeout`, `connect_timeout`).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add circuit breaker middleware to the API wrapper service. Configure DVC remote timeouts explicitly in `.dvc/config`.
- **Evidence**: `dvc/data_cloud.py` (no circuit breaker), `dvc/config_schema.py` (`read_timeout`, `connect_timeout` pass-through)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: DVC does not implement rate limiting or throttling for any of its operations. There is no API Gateway, no rate limiting middleware, no `express-rate-limit` equivalent. DVC is designed as a CLI tool invoked by human users — not as a service handling machine-speed requests. The `jobs` configuration parameter in remote config controls parallelism of file transfers, but this is not a rate limit — it's a concurrency setting for a single operation.
- **Gap**: No rate limiting at the DVC application level. An agent invoking DVC operations in a tight loop could overwhelm the local file system, the DVC cache, or the remote storage provider.
- **Compensating Controls**:
  - Implement rate limiting in the API wrapper service (e.g., `slowapi` for FastAPI).
  - Use API Gateway throttling if the wrapper is deployed behind API Gateway.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add rate limiting to the API wrapper service with configurable per-agent-identity limits.
- **Evidence**: `dvc/config_schema.py` (`jobs` is concurrency, not rate limiting), `dvc/data_cloud.py`

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: DVC stores data in user-configured remote storage locations. The region and jurisdiction of data storage is determined entirely by the remote URL configuration (e.g., `s3://bucket-name` where the bucket's region is set in AWS). DVC itself has no data residency enforcement — it does not validate, restrict, or audit which regions data is stored in or retrieved from. The `dvc/config_schema.py` includes a `region` field for S3 remotes, but this is a credential/connection parameter, not a residency enforcement mechanism.
- **Gap**: No DVC-level data residency enforcement. If an agent retrieves DVC-tracked data and sends it to an LLM endpoint in a different region or jurisdiction, DVC has no mechanism to prevent or detect this cross-boundary data movement.
- **Compensating Controls**:
  - Enforce data residency at the cloud provider level (S3 bucket policies with `aws:RequestedRegion` conditions).
  - In the API wrapper service, validate that data responses do not leave the designated region.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document data residency requirements for all DVC remotes. Configure cloud provider policies to enforce region boundaries.
- **Evidence**: `dvc/config_schema.py` (`region` field for S3), `dvc/data_cloud.py`

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: DVC logging (`dvc/logger.py`) uses Python's standard `logging` module with a custom `ColorFormatter`. Logs are written to stdout/stderr as human-readable text with color codes — not structured JSON. There is no PII redaction, log scrubbing, or masking middleware. The analytics module (`dvc/analytics.py`) collects and sends `user_id` (generated by `iterative-telemetry`), `git_remote_hash` (hashed), `system_info`, and `remotes` information. Error messages in `dvc/exceptions.py` include file paths, remote URLs, and command details that could contain sensitive information. The `dvc/database.py` module logs database connection errors without redacting connection strings.
- **Gap**: No PII redaction in any logging path. If DVC processes datasets containing PII, file paths, error messages, or debug logs could leak sensitive information.
- **Compensating Controls**:
  - Implement log scrubbing in the API wrapper service before any logs are persisted.
  - Configure DVC log level to WARNING or higher in agent-facing deployments to minimize verbose logging.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add PII redaction middleware to the API wrapper service. Audit all DVC log messages for sensitive data patterns.
- **Evidence**: `dvc/logger.py` (ColorFormatter, no redaction), `dvc/analytics.py` (user_id collected), `dvc/database.py` (connection errors logged), `dvc/exceptions.py` (paths in error messages)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or equivalent machine-readable specification exists. The Python API contract is defined by `dvc/api/__init__.py` `__all__` exports with docstrings in individual module files (`dvc/api/data.py`, `dvc/api/show.py`, `dvc/api/experiments.py`). The CLI specification is available via `dvc --help` and subcommand help text. Neither format is machine-readable for automated agent tool generation.
- **Gap**: No machine-readable API specification for agent tool generation. Building agent tools requires manual inspection of Python docstrings and CLI help text.
- **Compensating Controls**:
  - Use Python introspection (type hints, docstrings) to semi-automatically generate tool definitions.
  - If building an API wrapper (per API-Q1), auto-generate OpenAPI spec from FastAPI route definitions.
- **Remediation Timeline**: 30–60 days (concurrent with API wrapper)
- **Recommendation**: Generate OpenAPI spec from the API wrapper service. Publish as a versioned artifact.
- **Evidence**: `dvc/api/__init__.py` (no machine-readable spec), `dvc/api/data.py` (docstrings only)

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: DVC uses a custom exception hierarchy rooted in `DvcException` (`dvc/exceptions.py`) with ~30 specific exception types: `InvalidArgumentError`, `OutputNotFoundError`, `ConfigError`, `PathMissingError`, `FileMissingError`, etc. The CLI returns integer exit codes (0 for success, 251 for config errors, 252 for keyboard interrupt, 253 for not-a-DVC-repo, 254 for parser errors, 255 for general DVC exceptions — per `dvc/cli/__init__.py`). Python API raises typed exceptions. However, there are no structured error response bodies (no error code, no machine-readable category, no retryable boolean) since there is no HTTP API.
- **Gap**: No structured machine-readable error responses. CLI exit codes provide coarse error classification but not enough granularity for agent retry logic. Python exceptions are typed but require Python-level exception handling.
- **Compensating Controls**:
  - Map DVC exception types to structured error responses in the API wrapper service.
  - Include `error_code`, `message`, `retryable` boolean in wrapper API error responses.
- **Remediation Timeline**: 30–60 days (concurrent with API wrapper)
- **Recommendation**: Define a structured error response schema for the API wrapper service mapping DVC exceptions to HTTP status codes and machine-readable error bodies.
- **Evidence**: `dvc/exceptions.py` (exception hierarchy), `dvc/cli/__init__.py` (exit codes 251-255)

#### API-Q6: Asynchronous Operation Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: DVC has long-running operations — `push`, `pull`, `fetch` to remote storage can take minutes to hours for large datasets. DVC uses Celery/Kombu for experiment queue task execution (`dvc/repo/experiments/queue/celery.py`, `dvc/repo/experiments/queue/tasks.py`). However, there is no formal polling API, no job status endpoint, and no webhook callback for operation completion. The experiment queue provides background execution for experiments but not for general data operations. Progress is reported via `Tqdm` progress bars (`dvc/progress.py`) which are CLI-only.
- **Gap**: No async pattern for long-running operations accessible to agents. Push/pull operations block the caller with no status polling capability.
- **Compensating Controls**:
  - Implement async job submission with polling in the API wrapper service.
  - Use background workers (Celery) in the wrapper to handle long-running DVC operations.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add async job endpoints to the API wrapper: `POST /jobs` to submit, `GET /jobs/{id}` to poll status.
- **Evidence**: `dvc/repo/experiments/queue/celery.py`, `dvc/repo/experiments/queue/tasks.py`, `dvc/progress.py`, `pyproject.toml` (celery, kombu dependencies)

#### AUTH-Q4: Identity Propagation and Delegation — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: DVC is a local CLI tool with no service-to-service identity propagation. When DVC interacts with remote storage, it uses credentials configured in `.dvc/config` or environment variables directly. There is no JWT parsing, no OAuth2 on-behalf-of flows, no token exchange, and no user context headers. DVC cannot distinguish between an agent acting under its own identity versus acting on behalf of a specific human user.
- **Gap**: No identity propagation or delegation mechanism. All DVC operations use the same configured credentials regardless of the initiating principal.
- **Compensating Controls**:
  - Implement identity propagation in the API wrapper service using JWT tokens with subject (user) and actor (agent) claims.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Design the API wrapper with identity propagation: accept JWT tokens with both user identity and agent identity claims.
- **Evidence**: `dvc/config_schema.py` (direct credentials), `dvc/data_cloud.py` (credential pass-through)

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Credentials for remote storage are managed via DVC config files (`.dvc/config`, `.dvc/config.local`), environment variables, and cloud provider credential files. The `dvc/config_schema.py` defines direct credential fields: `access_key_id`, `secret_access_key`, `session_token` (S3), `credentialpath` (GCS), `client_id`, `client_secret` (Azure), `password` (SSH, HTTP, WebDAV), `sas_token` (Azure), `token` (WebDAV, DVC Studio). No integration with AWS Secrets Manager, HashiCorp Vault, or any secrets management system. `.dvc/config.local` is gitignored but credentials are stored in plaintext on disk. The DVC Studio token is stored in config under `studio.token`.
- **Gap**: No secrets management integration. Credentials stored in config files or environment variables. No rotation support — changing credentials requires manual config updates.
- **Compensating Controls**:
  - Use cloud provider credential chains (IAM instance profiles, IRSA for EKS) instead of static credentials in DVC config.
  - Store credentials in environment variables sourced from Secrets Manager at runtime, not in config files.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Remove static credentials from DVC config. Use IAM roles and credential chains. If building an API wrapper, retrieve credentials from Secrets Manager with rotation.
- **Evidence**: `dvc/config_schema.py` (credential fields: `access_key_id`, `secret_access_key`, `password`, `sas_token`, `client_secret`, `token`), `dvc/env.py` (`DVC_STUDIO_TOKEN`)

#### STATE-Q2: Queryable Current State — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: DVC provides state query capabilities through both CLI and Python API: `dvc status` (workspace status vs. remote), `dvc data status` (data pipeline status), `dvc diff` (changes between revisions), `dvc metrics show` / `dvc.api.metrics_show()` (metric values), `dvc params show` / `dvc.api.params_show()` (parameter values), `dvc exp show` / `dvc.api.exp_show()` (experiment status). State is queryable but only through local CLI or Python API — not via a network-accessible interface.
- **Gap**: State is queryable locally but not remotely. An agent needs local file system access or Python import access to query DVC state.
- **Compensating Controls**:
  - Expose state query operations via the API wrapper service.
- **Remediation Timeline**: 30–60 days (part of API wrapper)
- **Recommendation**: Expose `status`, `diff`, `metrics_show`, `params_show`, `exp_show` as API wrapper endpoints.
- **Evidence**: `dvc/repo/status.py`, `dvc/repo/diff.py`, `dvc/api/show.py`, `dvc/api/experiments.py`

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: DVC provides some filtering capabilities: `dvc ls` lists files with path filtering, `dvc metrics show` accepts target file arguments, `dvc exp show` supports `--num` (limit commits) and `--rev` (specific revisions). The Python API `exp_show()` accepts `revs` and `num` parameters. However, there is no traditional pagination (`limit`, `offset`, `cursor`), no field-level filtering, and no result size limits. Results are bounded by the repository scope (number of tracked files, experiments, etc.) rather than explicit query parameters.
- **Gap**: Limited filtering capabilities. No pagination for large result sets. An agent querying experiment history could receive unbounded results.
- **Compensating Controls**:
  - Implement pagination and filtering in the API wrapper service.
  - Use `num` parameter in `exp_show` to limit results.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add pagination parameters (`limit`, `offset`, `cursor`) to API wrapper endpoints.
- **Evidence**: `dvc/api/experiments.py` (`num` parameter), `dvc/api/show.py` (target-based filtering)

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: DVC itself serves as the system of record for data versioning metadata. The `.dvc` files and `dvc.lock` files are the authoritative records linking data files to their content-addressed hashes. Content-addressed storage (hash-based) provides natural deduplication and consistency. However, there is no formal system-of-record designation documentation, no master data management process, and no cross-system conflict resolution when DVC data overlaps with other data stores.
- **Gap**: No formal system-of-record documentation. No conflict resolution for data that exists in multiple systems.
- **Compensating Controls**:
  - Document DVC as the system of record for ML data versioning in architecture documentation.
- **Remediation Timeline**: 30 days
- **Recommendation**: Create formal data ownership documentation designating DVC as the system of record for ML data versioning.
- **Evidence**: `dvc/schema.py` (DATA_SCHEMA), `dvc/dvcfile.py`

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: DVC tracks data versions through Git commits, which provide timestamps (commit date). The `.dvc` files themselves contain hash info (`md5`, `sha256`), file size, and path — but no explicit `created_at`, `updated_at`, or `event_time` fields. Git provides the temporal metadata layer. There is no freshness signaling (no `Cache-Control`, `X-Data-Age`, or `last_refreshed` headers), no consistency level indication, and no timezone normalization beyond what Git provides.
- **Gap**: No explicit temporal metadata in DVC file format. Temporal information is only available through Git commit history. No freshness signaling for cached or stale data.
- **Compensating Controls**:
  - Use Git commit timestamps as temporal metadata when serving data through the API wrapper.
  - Add `Last-Modified` and `X-Data-Version` headers to API wrapper responses.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Include Git commit timestamps and DVC file hashes in API wrapper response headers for temporal context.
- **Evidence**: `dvc/schema.py` (no temporal fields in DATA_SCHEMA), `dvc/dvcfile.py`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing (no OpenTelemetry, no X-Ray, no `traceparent` header propagation). Logging uses Python's `logging` module with a custom `ColorFormatter` (`dvc/logger.py`) that outputs human-readable text with ANSI color codes. A custom `TRACE` logging level is added below `DEBUG`. Logs are written to stdout (INFO and below) and stderr (WARNING and above) via `LoggerHandler` which writes through `Tqdm.write()`. No structured JSON logging, no correlation IDs, no request IDs.
- **Gap**: No distributed tracing and no structured logging. Agent-initiated operations cannot be traced through the system. Log analysis requires parsing human-readable text.
- **Compensating Controls**:
  - Implement OpenTelemetry instrumentation in the API wrapper service.
  - Use structured JSON logging in the wrapper with correlation IDs.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenTelemetry tracing and structured JSON logging to the API wrapper service.
- **Evidence**: `dvc/logger.py` (ColorFormatter, no JSON, no trace IDs), `dvc/log.py`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No runtime alerting infrastructure for the DVC tool itself. CI/CD has Slack notifications for test failures on main branch (`.github/workflows/tests.yaml` — Slack webhook). No CloudWatch alarms, no PagerDuty/OpsGenie integration, no anomaly detection. DVC is designed as a CLI tool invoked by users, not as a running service with SLOs.
- **Gap**: No alerting thresholds for error rates or latency. If DVC operations fail or slow down when consumed by agents, there is no automated detection.
- **Compensating Controls**:
  - Implement alerting in the API wrapper service (CloudWatch alarms on 5xx rate and p99 latency).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add CloudWatch alarms to the API wrapper service for error rate and latency thresholds.
- **Evidence**: `.github/workflows/tests.yaml` (Slack notification for CI failures only)

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No IaC files exist in the repository. No Terraform, CloudFormation, CDK, Helm, or Kustomize definitions. DVC is distributed as a PyPI package (`pip install dvc`), not deployed as cloud infrastructure. There is no API Gateway, no IAM role definitions, no network configuration, and no deployment infrastructure defined as code. This is expected for a CLI tool/library, but it means there is no agent-facing integration surface governed by IaC.
- **Gap**: No infrastructure governance because there is no infrastructure to govern. The absence is expected for a CLI tool but becomes a gap when wrapping DVC as a service.
- **Compensating Controls**:
  - When building the API wrapper service, define all infrastructure (API Gateway, IAM, secrets, networking) as IaC from the start.
- **Remediation Timeline**: 60–90 days (part of wrapper service deployment)
- **Recommendation**: Define the API wrapper service infrastructure using Terraform or CDK. Include peer review requirements and drift detection.
- **Evidence**: No IaC files found in repository. Confirmed via `find` command: no `.tf`, `.tfvars`, `template.yaml`, `cdk.json`, `Chart.yaml`, `kustomization.yaml`, or `Dockerfile` files exist.

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI/CD exists via GitHub Actions: `tests.yaml` (tests across Python 3.9–3.14, 3 OS, with pytest-xdist parallel execution), `build.yaml` (package build + PyPI publish), `codeql.yml` (CodeQL security analysis), `plugin_tests.yaml` (plugin compatibility testing), `benchmarks.yaml` (performance benchmarks). Pre-commit hooks include ruff (linting), mypy (type checking), codespell. Codecov for coverage measurement. Dependabot for dependency updates. However, there are no API contract tests (no Pact, no OpenAPI validation, no schema comparison), no breaking change detection for the Python API, and no consumer-driven contract testing.
- **Gap**: CI/CD exists but lacks API contract testing. Changes to the `dvc.api` Python API or CLI interface are not automatically validated for backward compatibility.
- **Compensating Controls**:
  - The `__all__` exports in `dvc/api/__init__.py` serve as an informal contract. Add tests that validate `__all__` contents don't change unexpectedly.
  - Pin `dvc` version in agent tool definitions to avoid unexpected breaking changes.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add API contract tests that validate the `dvc.api` public interface. Add breaking change detection for the Python API.
- **Evidence**: `.github/workflows/tests.yaml`, `.github/workflows/build.yaml`, `.github/workflows/codeql.yml`, `.pre-commit-config.yaml`, `pyproject.toml`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: DVC is distributed as a PyPI package. Rollback means users installing a previous version (`pip install dvc==X.Y.Z`). GitHub releases and PyPI versioning support versioned distribution. The `build.yaml` workflow publishes to PyPI on release and test-pypi on main branch pushes. There is no blue/green deployment, no canary, no CodeDeploy — these concepts are not applicable for a library/CLI tool. `setuptools_scm` provides automatic version numbering from Git tags.
- **Gap**: No automated rollback capability in the traditional deployment sense. Rollback requires users to manually downgrade the package version. No automated rollback trigger.
- **Compensating Controls**:
  - Pin agent tool dependencies to specific DVC versions.
  - If building an API wrapper, implement blue/green deployment with automated rollback.
- **Remediation Timeline**: 30–60 days (part of wrapper service deployment)
- **Recommendation**: Pin DVC version in agent dependencies. Implement rollback capability in the API wrapper service deployment.
- **Evidence**: `.github/workflows/build.yaml` (PyPI publish), `pyproject.toml` (setuptools_scm)

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Extensive test suite exists: `tests/unit/` (unit tests including `test_api.py`, `test_config.py`, `test_dvcfile.py`, etc.), `tests/func/` (functional tests), `tests/integration/` (integration tests). Coverage measured with `pytest-cov` and reported to Codecov (threshold: auto with 2% tolerance per `.github/codecov.yml`). Parallel test execution with `pytest-xdist`. Tests cover the Python API (`tests/unit/test_api.py`), CLI, data cloud, config, experiments, and more. However, there are no formal API contract tests, no consumer-driven contract tests (Pact), and no automated validation of the public Python API surface stability.
- **Gap**: Good functional test coverage but no formal API contract tests for the `dvc.api` public interface.
- **Compensating Controls**:
  - The existing test suite covers API functionality even without formal contract tests.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add explicit contract tests for the `dvc.api` public interface. Validate input/output types, error responses, and edge cases.
- **Evidence**: `tests/unit/test_api.py`, `tests/func/`, `tests/integration/`, `pyproject.toml` (pytest config), `.github/codecov.yml`

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The DVC local cache (stored in `.dvc/cache/` by default) is not encrypted by DVC. Files are stored using their content hash as the filename — data is accessible to anyone with file system access. For remote storage, DVC supports encryption configuration: `dvc/config_schema.py` defines `sse` (server-side encryption type), `sse_kms_key_id` (KMS key for S3), `sse_customer_algorithm`, and `sse_customer_key` for S3 remotes. GCS and Azure encryption depends on provider-side configuration. Remote encryption is configurable but not enforced — it's opt-in.
- **Gap**: Local cache is not encrypted. Remote encryption is opt-in, not enforced. No validation that encryption is enabled for remotes containing sensitive data.
- **Compensating Controls**:
  - Configure S3 remotes with `sse: aws:kms` and `sse_kms_key_id` in DVC config.
  - Use encrypted file systems (LUKS, EBS encryption) for local cache.
- **Remediation Timeline**: 30 days
- **Recommendation**: Enable encryption at rest for all DVC remotes. Document encryption configuration as a mandatory setup step. Consider encrypting the local cache directory.
- **Evidence**: `dvc/config_schema.py` (`sse`, `sse_kms_key_id`, `sse_customer_algorithm`, `sse_customer_key` fields)

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `tests/docker-compose.yml` provides a git-server container for testing but is limited to test infrastructure (SSH-based git server with OpenSSH). DVC experiments provide a form of isolation through experiment branches. The pytest test suite includes unit, functional, and integration tests with fixtures in `tests/conftest.py`. However, there is no production-equivalent staging environment with seed data, no synthetic data generators for agent testing, and no documented sandbox setup for agent integration testing.
- **Gap**: No sandbox or staging environment for agent testing. Existing test infrastructure is developer-focused, not agent-testing-focused.
- **Compensating Controls**:
  - Use DVC experiments feature as a sandbox for agent testing (experiment branches isolate changes).
  - Create a dedicated test DVC repository with non-sensitive sample data.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a dedicated sandbox DVC repository with sample ML data, metrics, and experiments. Document setup for agent integration testing.
- **Evidence**: `tests/docker-compose.yml` (git-server only), `tests/conftest.py`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: DVC uses `setuptools_scm` for automatic version management from Git tags. The Python API contract is defined by `dvc/api/__init__.py` `__all__` exports. There is no formal schema versioning, no schema registry, no breaking change detection in CI, no consumer-driven contract tests (Pact), and no API version negotiation. The DVC file format schemas (`dvc/schema.py`) define lockfile schema versions (`"schema": "2.0"`) but this is for internal file format compatibility, not API versioning. CLI commands have evolving interfaces without formal deprecation processes.
- **Gap**: No formal API versioning or breaking change detection. Agent tool bindings could break silently when DVC is upgraded.
- **Compensating Controls**:
  - Pin DVC version in agent dependencies.
  - Monitor DVC release notes for breaking changes before upgrading.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add API stability tests that fail when the `dvc.api.__all__` contract changes. Implement semantic versioning discipline for the Python API surface.
- **Evidence**: `dvc/api/__init__.py` (`__all__` exports), `dvc/schema.py` (lockfile schema "2.0"), `pyproject.toml` (setuptools_scm)

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: DVC write operations are naturally idempotent due to content-addressed storage (hash-based). Running `dvc add` on the same file twice produces the same `.dvc` metadata. `dvc push` is idempotent — pushing the same content to remote storage is a no-op. DVC's content-addressing model means duplicate operations produce duplicate results.
- **Implication**: If agent scope is expanded to write-enabled in the future, DVC's content-addressed storage provides natural idempotency for most operations. This is a strength.
- **Recommendation**: Document idempotency guarantees for each DVC operation. If expanding to write scope, verify idempotency for all write operations the agent will invoke.
- **Evidence**: `dvc/data_cloud.py` (content-addressed push/pull), `dvc/schema.py` (hash-based DATA_SCHEMA)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: DVC Python API returns Python objects — file objects from `dvc.api.open()`, strings from `dvc.api.read()`, dicts from `dvc.api.metrics_show()`, `dvc.api.params_show()`, and `dvc.api.exp_show()`. CLI outputs human-readable text by default with some commands supporting `--json` or `--show-json` flags. No HTTP content-type negotiation since there is no HTTP API.
- **Implication**: The Python API returns well-structured Python dicts that are easily serializable to JSON. This is favorable for agent integration — the API wrapper can directly serialize these returns.
- **Recommendation**: Use JSON serialization of Python API returns in the wrapper service. Ensure all response types are JSON-serializable.
- **Evidence**: `dvc/api/show.py` (returns dict), `dvc/api/experiments.py` (returns list of dicts), `dvc/api/data.py` (returns file objects)

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: DVC does not emit webhooks, SNS/EventBridge events, or real-time notifications for state changes. The `dvc-studio-client` dependency provides integration with DVC Studio for experiment tracking (push experiment data to Studio). Analytics telemetry is sent to `analytics.dvc.org`. Git hooks (`.pre-commit-config.yaml` defines `dvc-pre-commit`, `dvc-pre-push`, `dvc-post-checkout` hooks) provide event-driven triggers at the Git layer. No native event emission system.
- **Implication**: Agents cannot reactively respond to DVC state changes. Agent workflows must be poll-based or triggered externally. Git hooks provide a potential integration point for event-driven workflows.
- **Recommendation**: If reactive agent behavior is needed, implement event emission in the API wrapper service (e.g., publish to SNS/EventBridge when metrics or experiments change). Use Git hooks as event triggers.
- **Evidence**: `.pre-commit-config.yaml` (DVC Git hooks), `pyproject.toml` (dvc-studio-client dependency), `dvc/analytics.py`

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: DVC is a CLI tool with no concept of API rate limits or rate limit headers. Remote storage providers (S3, GCS, Azure) enforce their own rate limits, but DVC does not document or surface these limits. No `X-RateLimit-Remaining` or `Retry-After` headers. The `jobs` configuration parameter controls file transfer parallelism but is not a rate limiting mechanism.
- **Implication**: Agents using DVC operations have no rate limit awareness. Cloud provider rate limits may be hit unexpectedly with no guidance from DVC on how to handle them.
- **Recommendation**: Document cloud provider rate limits relevant to DVC operations. If building an API wrapper, implement and document rate limits with standard headers.
- **Evidence**: `dvc/config_schema.py` (`jobs` parameter), `dvc/data_cloud.py`

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: DVC implements file locking (`dvc/lock.py`) using `zc.lockfile` and `flufl.lock` (HardlinkLock) to prevent concurrent DVC operations from corrupting the workspace. Read-write locks (`dvc/rwlock.py`) implement a `RWLock` pattern that distinguishes readers from writers — multiple readers can proceed concurrently, but writers require exclusive access. The rwlock tracks PIDs and commands for each lock holder.
- **Implication**: DVC's locking mechanisms are well-designed for concurrent CLI usage. For read-only agent scope, multiple agents can read concurrently without conflicts. This is a strength.
- **Recommendation**: If expanding to write scope, verify that DVC's locking mechanisms work correctly under agent-speed concurrent access patterns.
- **Evidence**: `dvc/lock.py` (Lock, HardlinkLock), `dvc/rwlock.py` (RWLock with read/write separation)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: DVC has no configurable transaction limits. Operations like `dvc gc` (garbage collection) can delete cache files without configurable limits. `dvc destroy` removes the entire DVC structure. No per-agent, per-session, or per-operation limits exist. The `--force` flag bypasses confirmation prompts for destructive operations.
- **Implication**: For read-only agent scope, transaction limits are less critical since no modifications are performed. If expanding to write scope, the lack of blast radius controls is a safety concern.
- **Recommendation**: If expanding to write scope, implement transaction limits in the API wrapper (e.g., maximum files per operation, maximum data size per request).
- **Evidence**: `dvc/commands/gc.py`, `dvc/commands/destroy.py`, `dvc/prompt.py` (confirmation prompts)

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: DVC experiments provide a form of pending/draft state — experiments can be queued (`dvc/repo/experiments/queue/`), run in isolation (experiment branches), compared, and selectively applied (`dvc exp apply`). However, for general data operations (add, push, pull), there is no draft/pending state. Operations take effect immediately when invoked.
- **Implication**: The experiment queue provides a natural "propose and confirm" pattern for ML experiments. For read-only agent scope, draft states are not needed. For future write-enabled scope, the experiment queue could serve as a human-in-the-loop mechanism.
- **Recommendation**: Leverage DVC experiments as a draft/review mechanism for agent-proposed changes when expanding to write scope.
- **Evidence**: `dvc/repo/experiments/queue/` (experiment queue), `dvc/repo/experiments/` (experiment management)

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: DVC has no configurable approval gates. Operations execute immediately when invoked. The `--force` flag bypasses interactive confirmation prompts. `dvc/prompt.py` provides `confirm()` and `ask()` functions for CLI-based user confirmation before destructive operations, but these are interactive TTY prompts — not programmatic approval workflows.
- **Implication**: For read-only agent scope, approval gates are not needed. For future write-enabled scope, approval gates would need to be implemented in the API wrapper service.
- **Recommendation**: If expanding to write scope, implement approval gate endpoints in the API wrapper (e.g., `POST /operations/{id}/approve`).
- **Evidence**: `dvc/prompt.py` (interactive confirmation only)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: DVC does not provide data quality scoring, completeness metrics, or data profiling. DVC tracks file integrity through content-addressable hashing (md5, sha256) — it can detect corruption or changes but does not assess quality. No null rate monitoring, duplicate detection, or freshness SLAs. Data quality is entirely the responsibility of the data producer, not DVC.
- **Implication**: Agents cannot assess data quality through DVC alone. Agent decisions based on DVC data have no quality guarantee from the DVC layer.
- **Recommendation**: Integrate data quality tooling (Great Expectations, Deequ) into the ML pipeline alongside DVC. Surface quality scores through DVC metrics.
- **Evidence**: `dvc/schema.py` (no quality fields), `dvc/output.py` (hash-based integrity only)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: DVC uses readable, semantically meaningful field names throughout. Python code uses clear names: `hash_info`, `meta`, `version_id`, `repo`, `remote`, `stage`, `output`, `dependency`. The DVC file format uses clear keys: `outs`, `deps`, `md5`, `path`, `cache`, `size`, `nfiles`. Config keys are readable: `core.remote`, `cache.dir`, `remote.<name>.url`. No legacy abbreviated codes requiring a data dictionary.
- **Implication**: Field names are self-documenting and LLM-friendly. This is a strength for agent integration — no data dictionary required.
- **Recommendation**: Maintain current naming conventions. Document field semantics in the API wrapper service's OpenAPI spec.
- **Evidence**: `dvc/schema.py`, `dvc/config_schema.py`, `dvc/api/__init__.py`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No formal data catalog exists (no AWS Glue Data Catalog, Collibra, Alation, or DataHub). DVC itself acts as a metadata layer for data versioning — `.dvc` files and `dvc.lock` describe tracked data. `dvc.api.params_show()` and `dvc.api.metrics_show()` provide programmatic metadata access. DVC artifacts (`dvc/api/artifacts.py`) support artifact discovery. The DVC Python API provides a basic metadata query interface.
- **Implication**: DVC serves as its own metadata layer. For agent tool discovery, DVC's API provides sufficient metadata access. A formal data catalog would accelerate tool definition for complex deployments.
- **Recommendation**: Consider registering DVC datasets in a data catalog (e.g., Glue Data Catalog) for enterprise-scale agent deployments.
- **Evidence**: `dvc/api/artifacts.py`, `dvc/api/show.py`, `dvc/dvcfile.py`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: DVC has `iterative-telemetry` for usage analytics (`dvc/analytics.py`). Analytics reports include: `cmd_class` (command used), `cmd_return_code`, `dvc_version`, `is_binary`, `scm_class`, `system_info`, `user_id`, `group_id`, `remotes`, `git_remote_hash`. Reports are sent to `analytics.dvc.org`. Codecov tracks test coverage. No custom business metrics, no CloudWatch `put_metric_data`, no resolution rate or conversion tracking.
- **Implication**: Usage telemetry provides basic operational metrics but not business outcome metrics. When agents consume DVC, there is no way to measure whether agent interactions produce good ML outcomes.
- **Recommendation**: Define business outcome metrics (e.g., experiment success rate, model quality improvement) and surface them through DVC metrics.
- **Evidence**: `dvc/analytics.py` (telemetry collection), `.github/codecov.yml`

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: BLOCKER
- **Finding**: DVC exposes a Python programmatic API (`dvc.api` module: `open`, `read`, `get_url`, `metrics_show`, `params_show`, `exp_show`, `exp_save`, `artifacts_show`, `DVCFileSystem`) and a CLI interface (`dvc` command). No REST/HTTP/GraphQL/AsyncAPI endpoints exist. Agent integration requires local Python import or subprocess CLI invocation.
- **Gap**: No network-accessible API interface for remote agent consumption.
- **Recommendation**: Build an HTTP API wrapper around `dvc.api` with OpenAPI specification.
- **Evidence**: `dvc/api/__init__.py`, `dvc/api/data.py`, `dvc/api/show.py`, `dvc/api/experiments.py`, `dvc/cli/__init__.py`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or equivalent machine-readable specification exists. The Python API is defined by `dvc/api/__init__.py` `__all__` exports with docstrings.
- **Gap**: No machine-readable API specification for automated agent tool generation.
- **Recommendation**: Generate OpenAPI spec from the API wrapper service.
- **Evidence**: `dvc/api/__init__.py`, `dvc/api/data.py`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: DVC uses a custom exception hierarchy (`DvcException` base in `dvc/exceptions.py`) with ~30 typed exceptions. CLI returns exit codes (0, 251–255). No HTTP structured error bodies since there is no HTTP API.
- **Gap**: No structured machine-readable error responses with error codes, messages, and retryable booleans.
- **Recommendation**: Map DVC exception types to structured error responses in the API wrapper service.
- **Evidence**: `dvc/exceptions.py`, `dvc/cli/__init__.py`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: DVC write operations are naturally idempotent due to content-addressed storage. `dvc add` and `dvc push` produce the same results for the same input.
- **Gap**: N/A for read-only scope.
- **Recommendation**: Document idempotency guarantees if expanding to write scope.
- **Evidence**: `dvc/data_cloud.py`, `dvc/schema.py`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: Python API returns dicts and file objects. CLI outputs text with optional `--json` for some commands.
- **Gap**: No HTTP response format. Python objects are well-structured for JSON serialization.
- **Recommendation**: Use JSON serialization in the API wrapper.
- **Evidence**: `dvc/api/show.py`, `dvc/api/experiments.py`, `dvc/api/data.py`

#### API-Q6: Asynchronous Operation Support
- **Severity**: RISK-QUALITY
- **Finding**: Long-running operations (push, pull, fetch) exist. Celery/Kombu used for experiment queue but no formal polling API or webhook callbacks for general operations.
- **Gap**: No async pattern for long-running operations accessible to agents.
- **Recommendation**: Implement async job submission with polling in the API wrapper.
- **Evidence**: `dvc/repo/experiments/queue/celery.py`, `dvc/repo/experiments/queue/tasks.py`, `dvc/progress.py`, `pyproject.toml`

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No webhooks, SNS/EventBridge events, or real-time notifications. DVC Studio integration via `dvc-studio-client`. Git hooks provide event triggers at the VCS layer.
- **Gap**: No native event emission for agent-reactive workflows.
- **Recommendation**: Implement event emission in the API wrapper if reactive agent behavior is needed.
- **Evidence**: `.pre-commit-config.yaml`, `pyproject.toml`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No API rate limits or rate limit headers. DVC is a CLI tool. Remote storage providers have their own limits.
- **Gap**: No rate limit documentation or headers for agent self-throttling.
- **Recommendation**: Document cloud provider rate limits. Implement rate limit headers in the API wrapper.
- **Evidence**: `dvc/config_schema.py`, `dvc/data_cloud.py`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: DVC does not implement authentication. Auth is delegated to remote storage providers (S3 IAM, GCS service accounts, Azure AD/SAS). Config schema shows direct credential fields but no DVC-level identity management.
- **Gap**: No machine identity authentication at the DVC application layer. Callers are indistinguishable.
- **Recommendation**: Implement OAuth2 client credentials or API key authentication on the API wrapper service.
- **Evidence**: `dvc/config_schema.py`, `dvc/data_cloud.py`, `dvc/config.py`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: DVC defers permission scoping to cloud providers. No DVC-level permission boundaries. Any valid credentials grant full DVC operation access.
- **Gap**: No DVC-level scoped permissions for agent identities.
- **Recommendation**: Use minimal IAM policies and implement RBAC in the API wrapper.
- **Evidence**: `dvc/config_schema.py`, `dvc/data_cloud.py`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No internal RBAC or ABAC. CLI dispatch (`args.func(args)`) has no authorization checks. All callers can invoke all operations.
- **Gap**: No action-level authorization at the DVC level.
- **Recommendation**: Implement action-level authorization in the API wrapper service.
- **Evidence**: `dvc/cli/__init__.py`, `dvc/commands/`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-QUALITY
- **Finding**: No JWT parsing, token exchange, or on-behalf-of flows. DVC uses configured credentials directly for all operations. Cannot distinguish agent-as-self from agent-on-behalf-of-user.
- **Gap**: No identity propagation mechanism.
- **Recommendation**: Implement JWT-based identity propagation in the API wrapper.
- **Evidence**: `dvc/config_schema.py`, `dvc/data_cloud.py`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: Credentials stored in DVC config files and environment variables. Config schema defines `access_key_id`, `secret_access_key`, `password`, `sas_token`, `client_secret`, `token`. No Secrets Manager or Vault integration. `.dvc/config.local` is gitignored but plaintext.
- **Gap**: No secrets management integration. No credential rotation support.
- **Recommendation**: Use IAM roles and credential chains. Integrate Secrets Manager for the API wrapper.
- **Evidence**: `dvc/config_schema.py`, `dvc/env.py`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No audit logging infrastructure. Analytics telemetry (`dvc/analytics.py`) is product telemetry, not audit trail. Logging goes to stdout/stderr via `ColorFormatter`.
- **Gap**: No immutable audit trail for DVC operations.
- **Recommendation**: Add structured JSON audit logging to the API wrapper with immutable storage.
- **Evidence**: `dvc/analytics.py`, `dvc/logger.py`, `dvc/log.py`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No agent identity concept in DVC. No API key revocation, no account disable. Credential revocation must happen at cloud provider level.
- **Gap**: No ability to suspend a specific agent identity at the DVC level.
- **Recommendation**: Implement API key management with revocation in the wrapper service.
- **Evidence**: `dvc/config_schema.py`, `dvc/config.py`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: DVC relies on Git for metadata rollback (`git revert`, `git checkout`). `dvc checkout` restores workspace state. No explicit saga pattern, compensating transactions, or programmatic rollback API. File locking prevents concurrent corruption but doesn't provide transaction rollback.
- **Gap**: No application-level compensation or rollback. Git provides metadata undo only.
- **Recommendation**: Implement idempotent read operations with caching in the API wrapper.
- **Evidence**: `dvc/lock.py`, `dvc/rwlock.py`, `dvc/repo/checkout.py`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK-QUALITY
- **Finding**: DVC provides state queries: `dvc status`, `dvc diff`, `dvc metrics show`, `dvc params show`, `dvc exp show` via CLI and Python API (`dvc.api.metrics_show()`, `dvc.api.params_show()`, `dvc.api.exp_show()`). State is queryable locally.
- **Gap**: State is queryable locally only — not via network interface.
- **Recommendation**: Expose state query operations via the API wrapper.
- **Evidence**: `dvc/repo/status.py`, `dvc/repo/diff.py`, `dvc/api/show.py`, `dvc/api/experiments.py`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: File locking (`zc.lockfile`, `flufl.lock`) and read-write locks (`dvc/rwlock.py`) prevent concurrent corruption. Multiple readers can proceed concurrently.
- **Gap**: N/A for read-only scope. Locking mechanisms are present and well-designed.
- **Recommendation**: Verify locking under agent-speed access if expanding to write scope.
- **Evidence**: `dvc/lock.py`, `dvc/rwlock.py`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: No circuit breakers, no application-level retry logic, no exponential backoff. DVC relies on underlying cloud library defaults for timeout/retry. `read_timeout` and `connect_timeout` config fields are pass-through only.
- **Gap**: No circuit breaker pattern for external dependency calls.
- **Recommendation**: Add circuit breaker middleware to the API wrapper. Configure DVC remote timeouts.
- **Evidence**: `dvc/data_cloud.py`, `dvc/config_schema.py`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting at the DVC level. `jobs` config parameter controls parallelism, not rate limiting. DVC is a CLI tool not designed for machine-speed request handling.
- **Gap**: No rate limiting. Agent loops could overwhelm storage providers.
- **Recommendation**: Add rate limiting to the API wrapper service.
- **Evidence**: `dvc/config_schema.py`, `dvc/data_cloud.py`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. `dvc gc` and `dvc destroy` have no limit controls. `--force` bypasses confirmation prompts.
- **Gap**: No transaction limits. Less critical for read-only scope.
- **Recommendation**: Implement transaction limits in the API wrapper if expanding to write scope.
- **Evidence**: `dvc/commands/gc.py`, `dvc/commands/destroy.py`, `dvc/prompt.py`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. DVC is P2 priority and not on the critical path.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: DVC experiments provide a form of pending state (experiment queue, isolated branches). No draft/pending state for general data operations.
- **Gap**: Limited draft/pending capability. N/A for read-only scope.
- **Recommendation**: Leverage DVC experiments as a draft mechanism for future write-enabled scope.
- **Evidence**: `dvc/repo/experiments/queue/`, `dvc/repo/experiments/`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable approval gates. Operations execute immediately. `dvc/prompt.py` provides interactive TTY confirmation prompts only.
- **Gap**: No programmatic approval workflow. N/A for read-only scope.
- **Recommendation**: Implement approval gate endpoints in the API wrapper if expanding to write scope.
- **Evidence**: `dvc/prompt.py`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: `tests/docker-compose.yml` provides git-server for testing. DVC experiments offer isolation. pytest suite exists. No production-equivalent staging with seed data for agent testing.
- **Gap**: No sandbox or staging environment for agent integration testing.
- **Recommendation**: Create a dedicated sandbox DVC repository with sample ML data for agent testing.
- **Evidence**: `tests/docker-compose.yml`, `tests/conftest.py`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: DVC manages arbitrary data files without data classification or sensitivity tagging. `.dvc` files contain hash checksums only. No PII detection, no Macie integration, no field-level encryption, no data classification tags.
- **Gap**: No data classification at any level. Agent can retrieve any tracked data without sensitivity controls.
- **Recommendation**: Inventory and classify all DVC-tracked datasets. Implement classification-aware access controls in the API wrapper.
- **Evidence**: `dvc/schema.py`, `dvc/output.py`, `dvc/dvcfile.py`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Data stored in user-configured remote storage. Region determined by remote URL. No DVC-level residency enforcement. `region` field in S3 config is a connection parameter, not enforcement.
- **Gap**: No data residency enforcement at the DVC level.
- **Recommendation**: Document residency requirements. Enforce at cloud provider level with bucket policies.
- **Evidence**: `dvc/config_schema.py`, `dvc/data_cloud.py`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: Some filtering (`dvc ls`, target arguments for `metrics show`, `--num` and `--rev` for `exp show`). No traditional pagination (`limit`, `offset`, `cursor`). Results bounded by repository scope.
- **Gap**: Limited filtering. No pagination for large result sets.
- **Recommendation**: Add pagination to API wrapper endpoints.
- **Evidence**: `dvc/api/experiments.py`, `dvc/api/show.py`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: DVC serves as system of record for data versioning via `.dvc` files and `dvc.lock`. Content-addressed storage provides deduplication. No formal SoR documentation or cross-system conflict resolution.
- **Gap**: No formal system-of-record documentation.
- **Recommendation**: Document DVC as SoR for ML data versioning.
- **Evidence**: `dvc/schema.py`, `dvc/dvcfile.py`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: Temporal metadata via Git commit timestamps only. No `created_at`/`updated_at` in DVC file format. No freshness signaling or cache headers.
- **Gap**: No explicit temporal metadata in DVC files. No freshness signaling.
- **Recommendation**: Include Git timestamps and hash versions in API wrapper response headers.
- **Evidence**: `dvc/schema.py`, `dvc/dvcfile.py`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: No PII redaction in logging. `ColorFormatter` outputs human-readable text. Analytics collects `user_id`. Error messages include file paths and URLs. `dvc/database.py` logs connection errors without redaction.
- **Gap**: No PII redaction in any logging path.
- **Recommendation**: Add PII redaction middleware to the API wrapper. Audit DVC log messages for sensitive patterns.
- **Evidence**: `dvc/logger.py`, `dvc/analytics.py`, `dvc/database.py`, `dvc/exceptions.py`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality scoring or profiling. DVC tracks file integrity via hashing but not quality. No null rate monitoring, duplicate detection, or freshness SLAs.
- **Gap**: No data quality awareness. Agents cannot assess data quality through DVC.
- **Recommendation**: Integrate data quality tooling (Great Expectations) into the ML pipeline.
- **Evidence**: `dvc/schema.py`, `dvc/output.py`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: `setuptools_scm` for version management. Python API contract defined by `__all__` exports. No formal schema versioning, schema registry, breaking change detection, or consumer-driven contract tests. Lockfile schema version ("2.0") is for internal format only.
- **Gap**: No formal API versioning or breaking change detection.
- **Recommendation**: Add API stability tests and semantic versioning for the Python API.
- **Evidence**: `dvc/api/__init__.py`, `dvc/schema.py`, `pyproject.toml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Readable, self-documenting field names throughout. Python: `hash_info`, `meta`, `repo`, `remote`. DVC files: `outs`, `deps`, `md5`, `path`. Config: `core.remote`, `cache.dir`. No legacy abbreviations.
- **Gap**: None. Field names are LLM-friendly.
- **Recommendation**: Maintain current naming conventions.
- **Evidence**: `dvc/schema.py`, `dvc/config_schema.py`, `dvc/api/__init__.py`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog (no Glue, Collibra, DataHub). DVC itself acts as metadata layer. `.dvc` files and `dvc.lock` describe data. `dvc.api.params_show()`, `dvc.api.metrics_show()` provide metadata access.
- **Gap**: No formal data catalog beyond DVC's own metadata.
- **Recommendation**: Consider registering DVC datasets in a data catalog for enterprise-scale deployments.
- **Evidence**: `dvc/api/artifacts.py`, `dvc/api/show.py`, `dvc/dvcfile.py`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: No OpenTelemetry, X-Ray, or distributed tracing. Custom `ColorFormatter` outputs human-readable text to stdout/stderr. Custom `TRACE` log level. No structured JSON logging, no correlation IDs, no request IDs.
- **Gap**: No distributed tracing and no structured logging.
- **Recommendation**: Add OpenTelemetry and structured JSON logging to the API wrapper.
- **Evidence**: `dvc/logger.py`, `dvc/log.py`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No runtime alerting. CI/CD has Slack notifications for test failures on main only. No CloudWatch alarms, no PagerDuty integration.
- **Gap**: No alerting for agent-facing operations.
- **Recommendation**: Add CloudWatch alarms to the API wrapper service.
- **Evidence**: `.github/workflows/tests.yaml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: `iterative-telemetry` tracks usage analytics (command, return code, version, user_id). Codecov for coverage. No custom business metrics or CloudWatch `put_metric_data`.
- **Gap**: No business outcome metrics. Cannot measure agent interaction quality.
- **Recommendation**: Define and surface business outcome metrics through DVC metrics.
- **Evidence**: `dvc/analytics.py`, `.github/codecov.yml`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: No IaC files. DVC is a PyPI package, not cloud infrastructure. No API Gateway, IAM, or network config defined as code. Expected for a CLI tool, but a gap when wrapping as a service.
- **Gap**: No infrastructure governance. No agent-facing integration surface.
- **Recommendation**: Define API wrapper infrastructure as IaC (Terraform/CDK) from the start.
- **Evidence**: No IaC files found (confirmed via file system search)

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI/CD: `tests.yaml` (Python 3.9–3.14, 3 OS), `build.yaml` (PyPI publish), `codeql.yml` (security), `plugin_tests.yaml`, pre-commit hooks (ruff, mypy, codespell), Codecov, Dependabot. No API contract tests, no breaking change detection.
- **Gap**: CI/CD exists but lacks API contract testing for `dvc.api`.
- **Recommendation**: Add API contract tests for the `dvc.api` public interface.
- **Evidence**: `.github/workflows/tests.yaml`, `.github/workflows/build.yaml`, `.github/workflows/codeql.yml`, `.pre-commit-config.yaml`, `pyproject.toml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: PyPI-based distribution. Rollback = `pip install dvc==X.Y.Z`. `build.yaml` publishes to PyPI. No blue/green, canary, or CodeDeploy — N/A for a library. `setuptools_scm` for versioning.
- **Gap**: No automated rollback. Manual version downgrade required.
- **Recommendation**: Pin DVC version in agent dependencies. Implement rollback in API wrapper deployment.
- **Evidence**: `.github/workflows/build.yaml`, `pyproject.toml`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: Extensive test suite: `tests/unit/test_api.py`, `tests/func/`, `tests/integration/`. pytest-cov + Codecov (auto threshold, 2% tolerance). pytest-xdist for parallel execution. Good functional coverage but no formal API contract tests.
- **Gap**: Good test coverage but no formal API contract tests for `dvc.api`.
- **Recommendation**: Add explicit contract tests for the public Python API surface.
- **Evidence**: `tests/unit/test_api.py`, `tests/func/`, `tests/integration/`, `pyproject.toml`, `.github/codecov.yml`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK-QUALITY
- **Finding**: Local cache not encrypted by DVC. Remote encryption configurable: `sse`, `sse_kms_key_id`, `sse_customer_algorithm`, `sse_customer_key` for S3. GCS/Azure encryption depends on provider config. Encryption is opt-in, not enforced.
- **Gap**: Local cache unencrypted. Remote encryption opt-in.
- **Recommendation**: Enable encryption for all DVC remotes. Encrypt local cache directory.
- **Evidence**: `dvc/config_schema.py`

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `dvc/api/__init__.py` | API-Q1, API-Q2, DISC-Q1, DISC-Q2 |
| `dvc/api/data.py` | API-Q1, API-Q2, API-Q5 |
| `dvc/api/show.py` | API-Q1, API-Q5, STATE-Q2, DATA-Q3, DISC-Q3 |
| `dvc/api/experiments.py` | API-Q1, API-Q5, STATE-Q2, DATA-Q3 |
| `dvc/api/artifacts.py` | DISC-Q3 |
| `dvc/cli/__init__.py` | API-Q1, API-Q3, AUTH-Q3 |
| `dvc/__main__.py` | API-Q1 |
| `dvc/exceptions.py` | API-Q3, DATA-Q6 |
| `dvc/config_schema.py` | AUTH-Q1, AUTH-Q2, AUTH-Q4, AUTH-Q5, STATE-Q4, STATE-Q5, DATA-Q2, API-Q8, ENG-Q5, DISC-Q2 |
| `dvc/config.py` | AUTH-Q1, AUTH-Q7 |
| `dvc/data_cloud.py` | AUTH-Q1, AUTH-Q2, AUTH-Q4, STATE-Q4, STATE-Q5, DATA-Q2, API-Q8 |
| `dvc/analytics.py` | AUTH-Q6, DATA-Q6, OBS-Q3, API-Q7 |
| `dvc/logger.py` | AUTH-Q6, DATA-Q6, OBS-Q1 |
| `dvc/log.py` | AUTH-Q6, OBS-Q1 |
| `dvc/lock.py` | STATE-Q1, STATE-Q3 |
| `dvc/rwlock.py` | STATE-Q1, STATE-Q3 |
| `dvc/prompt.py` | HITL-Q2, STATE-Q6 |
| `dvc/schema.py` | DATA-Q1, DATA-Q4, DATA-Q5, DATA-Q7, API-Q4, DISC-Q1, DISC-Q2 |
| `dvc/output.py` | DATA-Q1, DATA-Q7 |
| `dvc/dvcfile.py` | DATA-Q1, DATA-Q4, DATA-Q5, DISC-Q3 |
| `dvc/database.py` | DATA-Q6 |
| `dvc/env.py` | AUTH-Q5 |
| `dvc/progress.py` | API-Q6 |
| `dvc/repo/status.py` | STATE-Q2 |
| `dvc/repo/diff.py` | STATE-Q2 |
| `dvc/repo/checkout.py` | STATE-Q1 |
| `dvc/repo/experiments/queue/celery.py` | API-Q6 |
| `dvc/repo/experiments/queue/tasks.py` | API-Q6 |
| `dvc/repo/experiments/queue/` | HITL-Q1 |
| `dvc/repo/experiments/` | HITL-Q1 |
| `dvc/commands/` | AUTH-Q3 |
| `dvc/commands/gc.py` | STATE-Q6 |
| `dvc/commands/destroy.py` | STATE-Q6 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/tests.yaml` | ENG-Q2, OBS-Q2 |
| `.github/workflows/build.yaml` | ENG-Q2, ENG-Q3 |
| `.github/workflows/codeql.yml` | ENG-Q2 |
| `.github/workflows/plugin_tests.yaml` | ENG-Q2 |
| `.github/codecov.yml` | ENG-Q4, OBS-Q3 |
| `.github/dependabot.yml` | ENG-Q2 |
| `.pre-commit-config.yaml` | ENG-Q2, API-Q7 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `tests/docker-compose.yml` | HITL-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `pyproject.toml` | API-Q6, ENG-Q2, ENG-Q3, ENG-Q4, DISC-Q1 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `.dvc/config` | AUTH-Q5 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| `tests/unit/test_api.py` | ENG-Q4 |
| `tests/func/` | ENG-Q4 |
| `tests/integration/` | ENG-Q4 |
| `tests/conftest.py` | HITL-Q3 |
