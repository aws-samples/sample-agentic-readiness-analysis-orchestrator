# Agentic Readiness Assessment Report

**Target**: bpmn-miwg-test-suite
**Date**: 2025-07-14
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: stateless-utility (auto-detected)
**Agent Scope**: read-only
**Priority**: P1
**Tags**: standard-bpmn, multi-vendor, omg-official
**Context**: OMG official BPMN 2.0 Model Interchange test cases with reference models exported from multiple vendor tools.

**Archetype Justification**: Repository contains no application source code, no database connections, no API endpoints, no message queues, and no write operations. It is a static data repository of BPMN 2.0 reference test models packaged via Maven with no runtime service characteristics — consistent with `stateless-utility` (no persistent state, all data is public/reference-grade).

---

## Readiness Profile: Not Agent-Integrable

**BLOCKERs**: 3 | **RISK-SAFETY**: 8 | **RISK-QUALITY**: 10 | **INFOs**: 11

Exclude from agent toolset or plan major remediation before re-evaluation. This repository is fundamentally a BPMN 2.0 test data archive, not a deployable service with APIs. It lacks every foundational capability required for agent integration: no API surface, no authentication mechanism, and no data classification controls. Agentic consumption of this repository's data would require building an entirely new service layer on top of the static test files.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 3 |
| RISK-SAFETY | 8 |
| RISK-QUALITY | 10 |
| INFO | 11 |
| N/A | 0 |
| Not Evaluated (extended) | 11 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 8
**Extended Questions Not Triggered**: 11
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateless-utility (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### API-Q1: Documented API Interface

- **Severity**: BLOCKER
- **Finding**: The repository contains no application source code and exposes no API surface whatsoever. There are no REST endpoints (no Express routes, Flask/FastAPI routes, Spring `@RestController`, or any server code), no GraphQL schemas, no AsyncAPI specifications, and no gRPC service definitions. The `pom.xml` references BPMN MIWG analysis tools (`bounds-generator`, `submission-counter`, `bpmn-miwg-maven-plugin`) as Maven dependencies, but these are build-time tools, not runtime API services. The repository is a static data archive of BPMN 2.0 reference models and vendor test results.
- **Gap**: No API interface exists for an agent to consume. Integration would require direct file access (reading `.bpmn` XML files and `.json` metadata from the filesystem or Git), which creates brittle, non-auditable coupling.
- **Remediation**:
  - **Immediate**: Define whether agentic access to this test data is needed. If so, build a lightweight read-only API service (e.g., a REST API over the BPMN reference models and test results) as a separate repository.
  - **Target State**: A documented REST or GraphQL API that exposes test case metadata (`test-case-structure.json`), vendor tool registry (`tools-tested-by-miwg.json`), and BPMN reference model retrieval.
  - **Estimated Effort**: High — requires building a new service from scratch.
  - **Dependencies**: None
- **Evidence**: `pom.xml`, `README.md`, absence of any `.java`, `.py`, `.js`, `.ts`, `.go`, `.cs`, `.rb`, `.php` source files (confirmed via directory scan).

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The repository has no application authentication mechanism. There is no OAuth2 client credentials flow, no API key authentication, no mTLS configuration, no service account definitions, no Cognito app clients, and no API Gateway authorizers. The GitHub Actions workflows use `secrets.GITHUB_TOKEN` and `secrets.TSTEPHEN_GITHUB_MIWG_TOKEN` for CI/CD publishing to GitHub Packages and GitHub Pages, but these are CI/CD pipeline credentials, not application-level machine identity authentication. There is no application runtime to authenticate against.
- **Gap**: No machine identity authentication exists. An agent cannot authenticate to this system because there is no system to authenticate against — only static files in a Git repository.
- **Remediation**:
  - **Immediate**: If agent access is planned, define the authentication model for the new API service (see API-Q1 remediation). Implement OAuth2 client credentials or API key authentication with principal attribution.
  - **Target State**: Machine identity authentication with per-agent principal attribution and audit trail.
  - **Estimated Effort**: High — requires building an API service first (dependency on API-Q1).
  - **Dependencies**: API-Q1 (must have an API before auth can be applied to it).
- **Evidence**: `.github/workflows/maven.yml` (CI/CD credentials only), `.github/workflows/release.yml`, `pom.xml`, absence of any authentication code or configuration.

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: No data classification scheme exists in the repository. The BPMN reference models (`Reference/*.bpmn`) contain synthetic test process definitions (e.g., "Invoice Collaboration", "Buying at Amazon", "Vacation Request") — these are not real customer data. However, `tools-tested-by-miwg.json` contains personally identifiable information: maintainer email addresses in obfuscated form (e.g., `konstantin.krehl(at)kkrehl.de`, `maciej.barelkowski(at)camunda.com`, `falko.menge(at)camunda.com`, `developers(at)cardanit.com`, `j.back(at)mid.de`, `tim(at)knowprocess.com`, `antonin.abherve(at)softeam.fr`, `produktmanagement(at)mid.de`). Maintainer names are also present. While the data is published under Creative Commons Attribution 3.0 (public), there are no field-level classification tags, no data classification policies, and no controls preventing an agent from retrieving PII without explicit authorization.
- **Gap**: No sensitive data classification at the field level. PII (email addresses, personal names) exists in `tools-tested-by-miwg.json` without classification tags or access controls.
- **Remediation**:
  - **Immediate**: Classify all data fields in `tools-tested-by-miwg.json` and document that maintainer email addresses and names are PII (even if publicly licensed). Add classification metadata to JSON files.
  - **Target State**: Field-level data classification tags on all data files. Classification policy document. Access controls on PII fields if an API is built.
  - **Estimated Effort**: Low — data volume is small and data types are well-understood.
  - **Dependencies**: None — can be remediated independently.
- **Evidence**: `tools-tested-by-miwg.json` (contains PII: email addresses, names), `Reference/*.bpmn` (synthetic test data), `LICENSE.txt` (Creative Commons Attribution 3.0).
## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No application-level authorization model exists. The GitHub Actions workflows define CI/CD-level permissions (`contents: read`, `deployments: write`, `id-token: write`, `packages: write`), but these are pipeline permissions, not application access controls. There are no IAM policies, no role-per-service definitions, no API Gateway resource policies, and no condition keys restricting agent access to specific resources.
- **Gap**: No scoped permissions model. An agent identity cannot be granted read-only access to specific resources without inheriting broader privileges because there is no authorization layer.
- **Compensating Controls**:
  - Restrict agent access to the Git repository at the GitHub organization level using team-based permissions.
  - If an API is built (per API-Q1), implement least-privilege IAM policies from the start.
- **Remediation Timeline**: 60–90 days (dependent on API-Q1 remediation).
- **Recommendation**: Design a scoped permissions model as part of any new API service built over this data.
- **Evidence**: `.github/workflows/maven.yml` (CI/CD permissions only), absence of IAM policies, RBAC definitions, or API Gateway resource policies.

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization exists. There is no ABAC, no fine-grained RBAC, no permission matrices, and no middleware checking `canRead`, `canWrite`, or `canDelete`. No application code exists to enforce action-level controls.
- **Gap**: Cannot enforce action-level authorization (e.g., allow read but deny delete) because there is no application runtime with authorization checks.
- **Compensating Controls**:
  - The repository is read-only data; direct Git access inherently limits to read operations for non-maintainers.
  - GitHub branch protection rules restrict write access to the master branch.
- **Remediation Timeline**: 60–90 days (dependent on API-Q1 remediation).
- **Recommendation**: Implement action-level authorization as part of any new API service, ensuring agents can be restricted to specific operations (e.g., read test cases but not modify them).
- **Evidence**: Absence of any application source code, RBAC definitions, or authorization middleware.

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No immutable audit logging exists. There is no CloudTrail configuration, no CloudWatch log retention policies, no S3 bucket with object lock for logs, and no audit log infrastructure. GitHub provides Git commit history as an implicit audit trail for repository changes, but this is not application-level audit logging of API access by authenticated principals.
- **Gap**: No audit trail for agent-initiated access. Cannot prove compliance or conduct forensics on agent behavior.
- **Compensating Controls**:
  - Git commit history provides an immutable record of data changes (but not data reads).
  - GitHub audit logs (at the organization level) track repository access events.
- **Remediation Timeline**: 30–60 days (can be implemented as part of a new API service).
- **Recommendation**: When building an API service, implement immutable audit logging from day one with CloudTrail or equivalent, logging the authenticated principal for every operation.
- **Evidence**: Absence of `aws_cloudtrail`, CloudWatch, or any audit logging configuration in the repository.

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No mechanism exists to suspend or revoke individual agent identities. There are no API key revocation endpoints, no IAM role deactivation procedures, no service account disable mechanisms, and no Cognito user pool configurations. Without an application runtime, there is nothing to revoke access to.
- **Gap**: Cannot isolate a misbehaving agent without taking down broader platform access because there is no identity management layer.
- **Compensating Controls**:
  - GitHub personal access tokens can be revoked at the GitHub level if used for Git-based access.
  - GitHub organization admins can remove repository access for specific accounts.
- **Remediation Timeline**: 60–90 days (dependent on API-Q1 and AUTH-Q1 remediation).
- **Recommendation**: Design agent identity lifecycle management (creation, suspension, revocation) as part of any new API service.
- **Evidence**: Absence of any identity management, API key management, or access revocation mechanisms.

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No compensation or rollback mechanisms exist. There are no saga patterns, no two-phase commit, no explicit undo endpoints, no compensating transactions, and no Step Functions. The repository is purely static data — there are no multi-step operations to roll back.
- **Gap**: No rollback capability for multi-step operations. However, as a static data repository with read-only agent scope, the practical risk is minimal.
- **Compensating Controls**:
  - Git version control provides full history of all data changes, enabling manual rollback of any data modifications.
  - Read-only agent scope eliminates write-operation rollback concerns.
- **Remediation Timeline**: 90+ days (only relevant if a write-enabled API is built).
- **Recommendation**: If a write-enabled API is built over this data, implement compensation patterns from the start. For read-only scope, this is low priority.
- **Evidence**: Absence of any application code, saga patterns, or rollback mechanisms.

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting or throttling exists. There is no API Gateway throttling configuration, no WAF rate rules, no application-level rate limiting middleware, and no `aws_api_gateway_usage_plan` in IaC. There is no API surface to protect — the repository is accessed directly via Git or the GitHub API, which has its own rate limits.
- **Gap**: No rate limiting on any integration surface. A runaway agent loop accessing this data via Git operations could hit GitHub's rate limits but would not be controlled at the application level.
- **Compensating Controls**:
  - GitHub API has built-in rate limits (5,000 requests/hour for authenticated users) that provide a natural ceiling.
  - Git clone operations are inherently bounded by repository size.
- **Remediation Timeline**: 30–60 days (implement as part of a new API service).
- **Recommendation**: When building an API service, implement rate limiting from the start using API Gateway usage plans or application-level middleware.
- **Evidence**: Absence of API Gateway, WAF, rate limiting middleware, or any throttling configuration.

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The data is publicly available under a Creative Commons Attribution 3.0 Unported License. The repository is hosted on GitHub (US-based infrastructure). All BPMN reference models are synthetic test data (process diagrams), not regulated customer data. The `tools-tested-by-miwg.json` contains publicly submitted vendor information including maintainer email addresses from EU-based individuals (German, French, Italian domains), which could technically be subject to GDPR as personal data of EU data subjects. However, this data was voluntarily submitted for public publication.
- **Gap**: No formal data residency documentation. No assessment of whether EU maintainer email addresses in `tools-tested-by-miwg.json` require GDPR-compliant handling when sent to an LLM provider.
- **Compensating Controls**:
  - Data is publicly licensed under CC-BY-3.0, reducing (but not eliminating) residency concerns.
  - Agent can be configured to exclude PII fields when sending data to LLM endpoints.
- **Remediation Timeline**: 30 days (documentation exercise).
- **Recommendation**: Document that BPMN test data is public/synthetic and not subject to data residency restrictions. Separately assess whether EU maintainer PII requires GDPR-compliant handling and consider redacting PII from agent-accessible data views.
- **Evidence**: `LICENSE.txt` (CC-BY-3.0), `tools-tested-by-miwg.json` (EU maintainer emails), `Reference/*.bpmn` (synthetic BPMN models).

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No PII redaction exists. There is no log scrubbing middleware, no PII masking libraries, no CloudWatch log filters, and no Macie integration. The `tools-tested-by-miwg.json` file contains email addresses and maintainer names that are not masked. If an agent processes this data and the data appears in LLM prompt/response pairs or agent logs, PII would be exposed without redaction. GitHub Actions CI logs may also contain build output that references file paths with vendor names and contact information.
- **Gap**: PII (maintainer emails, personal names) in `tools-tested-by-miwg.json` is not redacted and could leak into agent logs or LLM interactions.
- **Compensating Controls**:
  - Agent orchestration layer can implement PII filtering before sending data to LLM endpoints.
  - Build a redacted view of `tools-tested-by-miwg.json` that strips maintainer contact fields.
- **Remediation Timeline**: 14–30 days (low effort to redact or mask PII fields).
- **Recommendation**: Create a redacted version of `tools-tested-by-miwg.json` for agent consumption that strips `maintainer` email fields. Implement PII detection in the agent orchestration layer.
- **Evidence**: `tools-tested-by-miwg.json` (contains unmasked email addresses and names).

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No machine-readable API specification exists. There are no OpenAPI/Swagger files, no AsyncAPI specifications, no GraphQL schema files, and no Smithy models in the repository. This is expected because there is no API (see API-Q1 BLOCKER).
- **Gap**: No machine-readable spec for agent tool generation. Every integration would require manual tool authoring.
- **Compensating Controls**:
  - The `test-case-structure.json` and `tools-tested-by-miwg.json` files provide structured JSON schemas that could be documented as an informal interface specification.
  - BPMN 2.0 XML schema (`Reference/xsdTypes.xsd`) provides a formal schema for the data format.
- **Remediation Timeline**: 60–90 days (build specification alongside API service).
- **Recommendation**: When building an API service, generate an OpenAPI specification from code annotations to keep it in sync with implementation.
- **Evidence**: Absence of any `openapi.*`, `swagger.*`, `*.graphql`, `*.gql`, `*.smithy`, or `asyncapi.*` files.

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No application code exists to evaluate error response structures. There are no error handling patterns, no structured error response formats, and no error code definitions because there is no application runtime.
- **Gap**: No structured error responses. An agent would have no way to distinguish retriable errors from terminal errors.
- **Compensating Controls**:
  - N/A — no API exists to return errors.
- **Remediation Timeline**: 60–90 days (implement as part of API service).
- **Recommendation**: When building an API service, implement consistent structured error responses with error codes, messages, and retryable indicators from the start.
- **Evidence**: Absence of any application source code.

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: GitHub Actions workflows properly use GitHub Secrets for credential management. `secrets.GITHUB_TOKEN` (auto-provided by GitHub) and `secrets.TSTEPHEN_GITHUB_MIWG_TOKEN` (personal access token stored as a repository secret) are referenced by name, not hardcoded. No `.env` files are committed. The `pom.xml` references `${env.GITHUB_ACTOR}` and `${env.GITHUB_TOKEN}` environment variables passed through Maven, which is acceptable practice. However, there is no secrets management system (AWS Secrets Manager, HashiCorp Vault) and no automated credential rotation.
- **Gap**: CI/CD credentials are managed via GitHub Secrets (acceptable for CI/CD) but there is no application-level secrets management system with rotation capability.
- **Compensating Controls**:
  - GitHub Secrets provides encrypted storage and access control for CI/CD credentials.
  - Personal access tokens can be set to expire (though rotation is manual).
- **Remediation Timeline**: 30–60 days.
- **Recommendation**: Ensure `TSTEPHEN_GITHUB_MIWG_TOKEN` has an expiration date and is rotated periodically. When building an API service, use AWS Secrets Manager or equivalent with automated rotation.
- **Evidence**: `.github/workflows/maven.yml` (`secrets.GITHUB_TOKEN`, `secrets.TSTEPHEN_GITHUB_MIWG_TOKEN`), `pom.xml` (`${env.GITHUB_ACTOR}`, `${env.GITHUB_TOKEN}`).

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No dedicated sandbox or staging environment exists. The repository can be cloned locally and the Maven build can be run (`mvn -P analysis`), which provides a local testing capability. GitHub Actions CI runs on every push and PR to master, providing automated build validation. However, there is no Docker Compose for local testing, no synthetic data generators, and no production-equivalent staging environment because there is no production service to mirror.
- **Gap**: No sandbox environment with production-equivalent data shape for agent testing. The concept of "staging" is not applicable since there is no production service.
- **Compensating Controls**:
  - Git clone provides a complete local copy of all data for testing.
  - GitHub Actions CI provides automated validation on every change.
- **Remediation Timeline**: 30–60 days (build alongside API service).
- **Recommendation**: When building an API service, create a Docker Compose configuration for local testing with seed data from the reference models.
- **Evidence**: `pom.xml` (Maven build), `.github/workflows/maven.yml` (CI workflow), absence of `docker-compose.yml` or staging environment configuration.

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The repository uses BPMN 2.0 as its data schema standard — an OMG-maintained specification with formal versioning. The `Reference/xsdTypes.xsd` provides XML Schema Definition types. The `pom.xml` versions the test suite artifact (`0.4-SNAPSHOT`). GitHub releases use year-based tags (e.g., `2026`). The `test-case-structure.json` provides structured metadata about test cases. However, there is no API contract versioning (no `/v1/` URL patterns, no `Accept-Version` headers) because there is no API. There are no breaking change detection tools in CI and no consumer-driven contract tests.
- **Gap**: While BPMN 2.0 schema provides data format stability, there is no API contract versioning or breaking change detection. Agent tool bindings would break silently if data structure changes occur.
- **Compensating Controls**:
  - BPMN 2.0 is a stable, OMG-governed standard unlikely to change frequently.
  - Git-based versioning (tags, releases) provides traceability of data changes.
- **Remediation Timeline**: 30–60 days.
- **Recommendation**: Add JSON Schema definitions for `test-case-structure.json` and `tools-tested-by-miwg.json`. Implement schema validation in CI to detect breaking changes to these files.
- **Evidence**: `Reference/xsdTypes.xsd`, `pom.xml` (version `0.4-SNAPSHOT`), `test-case-structure.json`, absence of API contract versioning or breaking change detection in CI.

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No application observability exists. There is no OpenTelemetry SDK, no X-Ray instrumentation, no `traceparent` header propagation, no structured JSON logging, and no `request_id` or `correlation_id` fields. GitHub Actions provides CI build logs, but these are not application-level observability. There is no application runtime to instrument.
- **Gap**: No tracing or structured logging. Agent-initiated requests to this data cannot be traced or debugged through the system.
- **Compensating Controls**:
  - GitHub Actions build logs provide CI/CD-level observability.
  - Git commit history tracks all data changes.
- **Remediation Timeline**: 60–90 days (implement as part of API service).
- **Recommendation**: When building an API service, instrument with OpenTelemetry from the start. Implement structured JSON logging with correlation IDs.
- **Evidence**: Absence of any observability instrumentation, logging configuration, or tracing libraries.

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No alerting exists. There are no CloudWatch alarms, no anomaly detection configuration, no PagerDuty/OpsGenie integration, and no SLO-based alerting. There is no API surface to monitor for error rates or latency.
- **Gap**: No alerting on any agent-facing surface. Degradation would be undetected.
- **Compensating Controls**:
  - GitHub Actions CI failures are reported via GitHub notifications.
  - GitHub provides uptime monitoring for GitHub Pages.
- **Remediation Timeline**: 30–60 days (implement as part of API service).
- **Recommendation**: When building an API service, configure CloudWatch alarms on error rates, latency, and 5xx responses from the start.
- **Evidence**: Absence of any alerting configuration, CloudWatch alarms, or monitoring integration.

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Infrastructure as Code exists in the repository. There are no Terraform files, no CloudFormation templates, no CDK stacks, no Helm charts, and no Kubernetes manifests. The infrastructure is entirely GitHub-hosted: GitHub Pages for static site hosting, GitHub Packages for Maven artifact distribution, and GitHub Actions for CI/CD. None of this infrastructure is defined as IaC in the repository — it is configured through the GitHub UI and `.github/workflows/` YAML files. No drift detection is configured.
- **Gap**: No IaC governance for the integration surface. Infrastructure changes are not subject to peer review or drift detection.
- **Compensating Controls**:
  - GitHub Actions workflow files (`.github/workflows/`) are version-controlled and subject to PR review.
  - GitHub's platform provides infrastructure management for Pages, Packages, and Actions.
- **Remediation Timeline**: 60–90 days.
- **Recommendation**: If migrating to a cloud-hosted API service, define all infrastructure as Terraform or CDK from the start, with PR-based review and drift detection.
- **Evidence**: Absence of any `.tf`, `.tfvars`, `template.yaml`, `template.json`, `cdk.json`, `Chart.yaml`, or `kustomization.yaml` files.

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: GitHub Actions CI exists (`.github/workflows/maven.yml`) and runs on push and PR to master. The Maven build executes the `analysis` profile which runs BPMN MIWG analysis tools (`bpmn-miwg-maven-plugin`) during the `test` phase — this validates BPMN model interchange compliance. However, there are no API contract tests (no Pact, no OpenAPI spec validation, no schema comparison tools) because there is no API. The release workflow (`.github/workflows/release.yml`) creates ZIP artifacts on release publication.
- **Gap**: CI/CD exists but has no API contract testing capability. Changes to data structures (`test-case-structure.json`, `tools-tested-by-miwg.json`) are not validated against a schema in CI.
- **Compensating Controls**:
  - BPMN MIWG analysis tools validate BPMN interchange compliance in CI.
  - PR review process provides manual change detection.
- **Remediation Timeline**: 14–30 days.
- **Recommendation**: Add JSON Schema validation for `test-case-structure.json` and `tools-tested-by-miwg.json` to the CI pipeline. This would catch breaking changes to the data structures that agents might consume.
- **Evidence**: `.github/workflows/maven.yml` (CI with BPMN analysis), `.github/workflows/release.yml` (release ZIP), `pom.xml` (`bpmn-miwg-maven-plugin` in `analysis` profile).

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No automated rollback capability exists. There is no blue/green deployment, no CodeDeploy rollback triggers, no Helm rollback, no feature flags, and no canary deployment. The GitHub Actions workflow deploys to GitHub Pages via `peaceiris/actions-gh-pages@v4` with `keep_files: true`, which means deployments are additive — old content is preserved. Git provides version control rollback capability (`git revert`). The release workflow creates versioned ZIP files that can be re-released.
- **Gap**: No automated rollback. Recovery from a bad deployment requires manual Git revert and re-triggering the CI workflow.
- **Compensating Controls**:
  - Git history provides full rollback capability via `git revert` or tag-based restoration.
  - GitHub Pages deployments can be rolled back by force-pushing to the `gh-pages` branch.
  - Release ZIP files are versioned and archived.
- **Remediation Timeline**: 30–60 days.
- **Recommendation**: Add a manual rollback workflow to GitHub Actions that can restore a previous GitHub Pages deployment from a known-good Git tag.
- **Evidence**: `.github/workflows/maven.yml` (deployment to GitHub Pages), `.github/workflows/release.yml` (release ZIP creation), absence of automated rollback triggers.
## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No write endpoints exist. The repository contains no application source code and no API surface. There are no POST, PUT, PATCH, or DELETE endpoints to evaluate for idempotency. The repository is read-only test data.
- **Implication**: No action required for read-only scope. If a write-enabled API is built in the future, idempotency must be designed in from the start.
- **Recommendation**: When building a write-enabled API, implement idempotency keys on all write endpoints.
- **Evidence**: Absence of any application source code or API endpoints.

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: The repository contains data in two primary formats: BPMN 2.0 XML (`.bpmn` files in `Reference/` and vendor directories) and JSON (`.json` metadata files: `test-case-structure.json`, `tools-tested-by-miwg.json`, `bpmn-analysis.json`). BPMN XML follows the OMG BPMN 2.0 XML schema. JSON files are well-structured with human-readable keys. No API exists to return responses, but these file formats represent the data an agent would consume.
- **Implication**: BPMN XML requires XML parsing which is more complex for LLM consumption than JSON. An agent service would benefit from offering JSON representations of BPMN models alongside the raw XML. The existing JSON metadata files (`test-case-structure.json`, `tools-tested-by-miwg.json`) are well-suited for agent consumption.
- **Recommendation**: When building an API, provide JSON response format for all endpoints. Offer BPMN XML as a secondary format for tools that need the native representation.
- **Evidence**: `Reference/A.1.0.bpmn` (BPMN 2.0 XML), `test-case-structure.json` (JSON), `tools-tested-by-miwg.json` (JSON), `bpmn-analysis.json` (JSON).

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No API exists to document rate limits for. No rate limit headers (`X-RateLimit-Remaining`, `Retry-After`) are returned because there is no HTTP API surface. The repository is accessed via Git, which is subject to GitHub's platform rate limits.
- **Implication**: When building an API, rate limit documentation and headers should be included from the start to enable agent self-throttling.
- **Recommendation**: When building an API, document rate limits in the OpenAPI spec and return standard rate limit headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`).
- **Evidence**: Absence of any API surface or rate limit configuration.

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: No identity propagation code exists. There is no JWT parsing middleware, no OAuth2 on-behalf-of flows, no token exchange patterns, and no user context headers. No application runtime exists that would require identity propagation.
- **Implication**: For `stateless-utility` archetype with public/reference data, identity propagation has minimal security impact — downgraded to INFO. If the data were user-specific or tenant-specific, this would be a higher-severity finding.
- **Recommendation**: When building an API, design identity propagation to distinguish agent-as-self from agent-on-behalf-of-user if the service will serve multiple consumer types.
- **Evidence**: Absence of any authentication or identity propagation code.

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No concurrency control mechanisms exist. There is no optimistic locking, no pessimistic locking, no DynamoDB conditional writes, and no conflict resolution logic. There is no application code or database to apply concurrency controls to.
- **Implication**: For read-only agent scope, concurrency controls are not needed — multiple agents can read the same static data simultaneously without conflict. Relevant only if write operations are added in the future.
- **Recommendation**: If a write-enabled API is built, implement optimistic locking (version fields, ETags) on all write endpoints.
- **Evidence**: Absence of any application source code or database access layer.

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits exist. There are no configurable limits on agent-initiated actions (maximum records modified, maximum spend, maximum delete operations) because there is no write-enabled API surface. The repository contains static data that cannot be modified through an API.
- **Implication**: For read-only agent scope, transaction limits are not needed — agents cannot modify records, trigger spend, or delete data. Relevant only if write operations are added in the future.
- **Recommendation**: If a write-enabled API is built, implement configurable transaction limits per agent identity from the start.
- **Evidence**: Absence of any application source code or write-enabled endpoints.

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No formal data quality metrics exist. However, the BPMN MIWG test cases are maintained as OMG-official reference standards with community-driven quality assurance. The `test-case-structure.json` provides structured metadata about test cases including categories, descriptions, and variations. The `bpmn-analysis.json` (6.8 MB, 160,167 lines) contains detailed process analysis with constraint metrics, task scores, and compliance data — this represents a form of data quality assessment. The BPMN MIWG analysis tools (`bpmn-miwg-maven-plugin`) run automated comparison tests on vendor submissions.
- **Implication**: While no formal data quality score exists, the community-driven testing process and automated analysis tools provide implicit quality assurance. Agents consuming this data should be aware that vendor test results vary in completeness.
- **Recommendation**: Consider publishing a data quality dashboard summarizing the completeness and freshness of vendor test submissions (using `lastResultsSubmitted` from `tools-tested-by-miwg.json`).
- **Evidence**: `test-case-structure.json`, `tools-tested-by-miwg.json` (`lastResultsSubmitted` fields), `bpmn-analysis.json` (analysis results), `pom.xml` (`bpmn-miwg-maven-plugin`).

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names across the repository are consistently semantic and human-readable. BPMN models use standard BPMN 2.0 element names (`startEvent`, `task`, `endEvent`, `sequenceFlow`, `exclusiveGateway`). JSON files use descriptive field names: `tools-tested-by-miwg.json` uses `vendor`, `tool`, `version`, `website`, `supportsBpmn2`, `hasImport`, `hasExport`, `hasRoundtrip`, `lastResultsSubmitted`, `openSource`. `test-case-structure.json` uses `categories`, `category`, `name`, `description`, `cases`, `variations`, `variation`, `tool`. No legacy abbreviations or cryptic codes were found.
- **Implication**: The semantic clarity of field names is excellent — agents using LLM-based reasoning can interpret field names without a data dictionary. This is a strength of the repository's design.
- **Recommendation**: Maintain the current naming conventions. Document them as a standard for any new fields added.
- **Evidence**: `tools-tested-by-miwg.json`, `test-case-structure.json`, `Reference/A.1.0.bpmn`.

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No formal data catalog tool (AWS Glue Data Catalog, Collibra, Alation, DataHub) is used. However, the repository has effective informal metadata: `test-case-structure.json` serves as a comprehensive catalog of test cases organized by category (A: Layout, B: Conformance class coverage, C: Complex scenarios) with descriptions, variations, and originating tools. `tools-tested-by-miwg.json` serves as a vendor tool registry with 37 entries including capabilities, versions, and participation history. The `README.md` provides detailed documentation of the repository structure and test procedures.
- **Implication**: The existing JSON files provide a usable metadata layer for agent tool builders. Formalizing these as a discoverable catalog would accelerate agent integration.
- **Recommendation**: Consider publishing `test-case-structure.json` and `tools-tested-by-miwg.json` as a discoverable metadata API. Add JSON Schema definitions to formalize the structure.
- **Evidence**: `test-case-structure.json`, `tools-tested-by-miwg.json`, `README.md`.

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No runtime business outcome metrics exist. There are no `cloudwatch.put_metric_data` calls, no custom dashboards, and no business KPI alarms. The `bpmn-analysis.json` contains detailed BPMN process analysis results (constraint metrics, task complexity scores, migration verdicts) generated by the BPMN MIWG analysis tools, but these are static analysis outputs, not runtime business metrics.
- **Implication**: When agents consume this system, business metrics (e.g., test case coverage across vendors, pass/fail rates, vendor participation trends) would be the primary signal for agent interaction quality. These could be derived from the existing JSON data.
- **Recommendation**: Consider generating and publishing aggregate metrics: vendor participation rates, test case coverage completeness, BPMN interchange compliance scores by tool.
- **Evidence**: `bpmn-analysis.json`, absence of any runtime business metrics or dashboards.

### ENG-Q4: API Test Coverage

- **Severity**: INFO
- **Finding**: No API test suites exist (no Postman/Newman collections, no pytest API tests, no REST Assured tests). The Maven build runs BPMN MIWG analysis tools (`bpmn-miwg-maven-plugin`) during the `test` phase in the `analysis` profile, which validates BPMN model interchange compliance — this is test data validation, not API testing. There are no API endpoints to test. The `bpmn-analysis.json` (160,167 lines) represents the output of this analysis.
- **Implication**: For `stateless-utility` archetype, API test coverage is evaluated as INFO. The existing BPMN interchange validation provides data quality assurance, which is the most relevant form of testing for this repository.
- **Recommendation**: When building an API service, implement API test suites covering input validation, output format, error responses, and edge cases. Run them in CI.
- **Evidence**: `pom.xml` (`bpmn-miwg-maven-plugin` in `analysis` profile), `.github/workflows/maven.yml` (CI executes `mvn -P analysis deploy`), `bpmn-analysis.json` (analysis output).
## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: BLOCKER
- **Finding**: The repository contains no application source code and exposes no API surface. No REST endpoints, GraphQL schemas, AsyncAPI specs, or gRPC services exist. The `pom.xml` references BPMN MIWG analysis tools as Maven dependencies but these are build-time tools, not runtime APIs. This is a static data archive of BPMN 2.0 reference models and vendor test results.
- **Gap**: No API interface for agent consumption. Integration requires direct file/Git access — brittle and non-auditable.
- **Recommendation**: Build a lightweight read-only API service over the BPMN reference models and test results if agentic access is needed.
- **Evidence**: `pom.xml`, `README.md`, absence of any application source files (`.java`, `.py`, `.js`, `.ts`, `.go`, etc.).

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI/Swagger, AsyncAPI, GraphQL schema, or Smithy files exist. Expected given no API exists (API-Q1).
- **Gap**: No machine-readable spec for agent tool generation.
- **Recommendation**: Generate OpenAPI spec alongside any future API service.
- **Evidence**: Absence of `openapi.*`, `swagger.*`, `*.graphql`, `*.gql`, `*.smithy`, `asyncapi.*` files.

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: No application code exists. No error handling patterns, error response formats, or error code definitions.
- **Gap**: No structured error responses for agent consumption.
- **Recommendation**: Implement structured error responses (error code, message, retryable indicator) in any future API service.
- **Evidence**: Absence of any application source code.

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No write endpoints exist. The repository is read-only test data with no application code.
- **Gap**: N/A for read-only scope.
- **Recommendation**: If write-enabled API is built, implement idempotency keys on all write endpoints.
- **Evidence**: Absence of any application source code or API endpoints.

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: Data exists in BPMN 2.0 XML (`.bpmn` files) and JSON (`.json` metadata files). Both formats are well-structured. BPMN XML follows OMG standard schema. JSON files use descriptive keys.
- **Implication**: BPMN XML is more complex for LLM consumption than JSON. JSON metadata files are well-suited for agents.
- **Recommendation**: Provide JSON response format for all API endpoints; offer BPMN XML as secondary format.
- **Evidence**: `Reference/A.1.0.bpmn`, `test-case-structure.json`, `tools-tested-by-miwg.json`, `bpmn-analysis.json`.

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows. No runtime operations exist — the repository is static data.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has state changes (stateful-crud, orchestrator). No state changes exist — the repository is static test data.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No API exists. No rate limit headers returned. Repository accessed via Git/GitHub API with platform-level rate limits.
- **Implication**: Rate limit documentation needed when API is built.
- **Recommendation**: Document rate limits and return `X-RateLimit-*` headers in any future API.
- **Evidence**: Absence of any API surface or rate limit configuration.

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: No application authentication mechanism. No OAuth2, API keys, mTLS, service accounts, Cognito, or API Gateway authorizers. GitHub Actions uses `secrets.GITHUB_TOKEN` and `secrets.TSTEPHEN_GITHUB_MIWG_TOKEN` for CI/CD only — not application auth. No application runtime to authenticate against.
- **Gap**: No machine identity authentication. Agent cannot authenticate because no system exists to authenticate against.
- **Recommendation**: Implement OAuth2 client credentials or API key authentication with principal attribution in any future API service.
- **Evidence**: `.github/workflows/maven.yml`, `.github/workflows/release.yml`, `pom.xml`, absence of auth code.

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: No application-level authorization model. GitHub Actions CI/CD permissions (`contents: read`, `deployments: write`, `id-token: write`, `packages: write`) are pipeline-level, not application access controls.
- **Gap**: No scoped permissions model for agent identities.
- **Recommendation**: Design scoped permissions as part of any future API service.
- **Evidence**: `.github/workflows/maven.yml` (CI/CD permissions only), absence of IAM policies or RBAC definitions.

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization. No ABAC, RBAC, permission matrices, or authorization middleware. No application code exists.
- **Gap**: Cannot enforce action-level authorization.
- **Recommendation**: Implement action-level authorization in any future API service.
- **Evidence**: Absence of application source code or authorization configurations.

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: No identity propagation code. No JWT parsing, OAuth2 on-behalf-of flows, or token exchange patterns. Downgraded to INFO for `stateless-utility` archetype with public/reference data.
- **Implication**: Minimal security impact for public data. Relevant if future API serves user-specific data.
- **Recommendation**: Design identity propagation if future API serves multiple consumer types.
- **Evidence**: Absence of authentication or identity propagation code.

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: GitHub Actions uses GitHub Secrets (`secrets.GITHUB_TOKEN`, `secrets.TSTEPHEN_GITHUB_MIWG_TOKEN`) — proper CI/CD practice. No `.env` files committed. `pom.xml` references `${env.GITHUB_ACTOR}` and `${env.GITHUB_TOKEN}`. No application-level secrets management (AWS Secrets Manager, Vault) or automated rotation.
- **Gap**: No secrets management system with rotation capability.
- **Recommendation**: Ensure `TSTEPHEN_GITHUB_MIWG_TOKEN` has expiration. Use Secrets Manager for any future API.
- **Evidence**: `.github/workflows/maven.yml`, `pom.xml`.

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No immutable audit logging. No CloudTrail, CloudWatch, or immutable log storage. Git commit history provides implicit change audit but not API access audit.
- **Gap**: No audit trail for agent-initiated access.
- **Recommendation**: Implement immutable audit logging with CloudTrail or equivalent in any future API service.
- **Evidence**: Absence of `aws_cloudtrail`, CloudWatch, or audit logging configuration.

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No mechanism to suspend or revoke agent identities. No API key revocation, IAM role deactivation, or service account disable. No application runtime to manage access to.
- **Gap**: Cannot isolate a misbehaving agent.
- **Recommendation**: Design agent identity lifecycle management in any future API service.
- **Evidence**: Absence of identity management or access revocation mechanisms.

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No compensation or rollback mechanisms. No saga patterns, two-phase commit, undo endpoints, or Step Functions. The repository is purely static data with no multi-step operations.
- **Gap**: No rollback capability. Practical risk is minimal for read-only static data.
- **Recommendation**: Implement compensation patterns if a write-enabled API is built. Low priority for read-only scope.
- **Evidence**: Absence of any application code, saga patterns, or rollback mechanisms.

#### STATE-Q2: Queryable Current State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator). No persistent state exists.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No concurrency controls. No optimistic locking, pessimistic locking, conditional writes, or conflict resolution. No application code or database exists.
- **Gap**: No concurrency controls. Not needed for read-only access to static data.
- **Recommendation**: Implement optimistic locking if write-enabled API is built.
- **Evidence**: Absence of any application source code or database access layer.

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs). No runtime external dependencies — Maven build-time dependencies only.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting or throttling. No API Gateway throttling, WAF rules, or application-level rate limiting middleware. No API surface exists to protect. Repository accessed via Git/GitHub API with platform-level rate limits.
- **Gap**: No rate limiting on any integration surface.
- **Recommendation**: Implement rate limiting via API Gateway usage plans in any future API service.
- **Evidence**: Absence of API Gateway, WAF, or rate limiting configuration.

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits. No configurable limits on agent-initiated actions. No write-enabled API surface exists.
- **Gap**: Not applicable for read-only static data access.
- **Recommendation**: Implement transaction limits per agent identity if write-enabled API is built.
- **Evidence**: Absence of any application source code or write-enabled endpoints.

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. Priority is P1 and not identified as critical path.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled. Current scope is read-only.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled. Current scope is read-only.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: No dedicated sandbox or staging environment. Repository can be cloned locally with `mvn -P analysis` build capability. GitHub Actions CI runs on push/PR. No Docker Compose, no synthetic data generators, no production-equivalent staging.
- **Gap**: No sandbox with production-equivalent data shape for agent testing.
- **Recommendation**: Create Docker Compose configuration for local testing when building an API service.
- **Evidence**: `pom.xml`, `.github/workflows/maven.yml`, absence of `docker-compose.yml`.

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: No data classification scheme. BPMN reference models contain synthetic test data (not real customer data). `tools-tested-by-miwg.json` contains PII: maintainer email addresses (e.g., `konstantin.krehl(at)kkrehl.de`, `maciej.barelkowski(at)camunda.com`, `j.back(at)mid.de`, `tim(at)knowprocess.com`) and personal names. Data is publicly licensed under CC-BY-3.0 but has no field-level classification.
- **Gap**: PII exists without classification tags or access controls.
- **Recommendation**: Classify all data fields. Add classification metadata to JSON files. Apply access controls on PII fields if API is built.
- **Evidence**: `tools-tested-by-miwg.json` (PII), `Reference/*.bpmn` (synthetic), `LICENSE.txt` (CC-BY-3.0).

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Data publicly available under CC-BY-3.0. Hosted on GitHub (US). BPMN models are synthetic. `tools-tested-by-miwg.json` contains EU maintainer emails that could be subject to GDPR. Data was voluntarily submitted for public publication.
- **Gap**: No formal data residency documentation. No GDPR assessment for EU maintainer PII.
- **Recommendation**: Document data residency status. Assess GDPR implications for EU maintainer PII. Consider redacting PII from agent-accessible views.
- **Evidence**: `LICENSE.txt`, `tools-tested-by-miwg.json`, `Reference/*.bpmn`.

#### DATA-Q3: Selective Query Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has list/query endpoints with potentially unbounded results. No API endpoints exist.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway). No persistent state.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator). No persistent state exists.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: No PII redaction. No log scrubbing, PII masking, CloudWatch filters, or Macie integration. `tools-tested-by-miwg.json` contains unmasked email addresses and maintainer names. PII could leak into agent logs or LLM prompt/response pairs.
- **Gap**: PII not redacted — could leak into agent interactions.
- **Recommendation**: Create redacted version of `tools-tested-by-miwg.json` for agent consumption. Implement PII detection in agent orchestration layer.
- **Evidence**: `tools-tested-by-miwg.json` (unmasked emails and names).

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No formal data quality metrics. BPMN MIWG test cases are OMG-official reference standards. `test-case-structure.json` provides structured metadata. `bpmn-analysis.json` (6.8 MB) contains detailed process analysis. BPMN MIWG analysis tools provide automated compliance testing.
- **Implication**: Community-driven quality assurance provides implicit quality. Vendor test results vary in completeness.
- **Recommendation**: Publish data quality dashboard using `lastResultsSubmitted` from `tools-tested-by-miwg.json`.
- **Evidence**: `test-case-structure.json`, `tools-tested-by-miwg.json`, `bpmn-analysis.json`, `pom.xml`.

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: Repository uses BPMN 2.0 (OMG standard) as data schema. `Reference/xsdTypes.xsd` provides XSD types. `pom.xml` versions artifact (`0.4-SNAPSHOT`). GitHub releases use year-based tags. No API contract versioning (no API exists). No breaking change detection in CI. No consumer-driven contract tests.
- **Gap**: No API contract versioning or breaking change detection. Data structure changes could break agent tool bindings.
- **Recommendation**: Add JSON Schema definitions for metadata files. Implement schema validation in CI.
- **Evidence**: `Reference/xsdTypes.xsd`, `pom.xml`, `test-case-structure.json`.

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Excellent semantic naming throughout. BPMN uses standard element names (`startEvent`, `task`, `endEvent`). JSON uses descriptive keys (`vendor`, `tool`, `version`, `website`, `hasImport`, `hasExport`). Test case IDs follow systematic convention (A.1.0, B.1.0, C.1.0). No legacy abbreviations found.
- **Implication**: LLM-based agents can interpret field names without a data dictionary. A strength of this repository.
- **Recommendation**: Maintain current naming conventions.
- **Evidence**: `tools-tested-by-miwg.json`, `test-case-structure.json`, `Reference/A.1.0.bpmn`.

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog tool. Effective informal metadata: `test-case-structure.json` catalogs test cases by category with descriptions. `tools-tested-by-miwg.json` is a vendor tool registry with 37 entries. `README.md` documents repository structure and test procedures.
- **Implication**: Existing JSON files provide a usable metadata layer for agent tool builders.
- **Recommendation**: Publish JSON files as discoverable metadata API. Add JSON Schema definitions.
- **Evidence**: `test-case-structure.json`, `tools-tested-by-miwg.json`, `README.md`.

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: No application observability. No OpenTelemetry, X-Ray, structured JSON logging, or correlation IDs. GitHub Actions provides CI build logs only. No application runtime to instrument.
- **Gap**: Agent-initiated requests cannot be traced or debugged.
- **Recommendation**: Instrument with OpenTelemetry and structured logging when building API service.
- **Evidence**: Absence of observability instrumentation or logging configuration.

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No alerting. No CloudWatch alarms, anomaly detection, PagerDuty/OpsGenie, or SLO-based alerting. No API surface to monitor.
- **Gap**: No alerting on agent-facing surface.
- **Recommendation**: Configure CloudWatch alarms when building API service.
- **Evidence**: Absence of alerting configuration or monitoring integration.

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No runtime business metrics. `bpmn-analysis.json` contains static analysis results (constraint metrics, task scores) but these are build-time outputs, not runtime metrics.
- **Implication**: Business metrics (vendor participation, compliance scores) could be derived from existing data.
- **Recommendation**: Generate aggregate metrics from existing JSON data.
- **Evidence**: `bpmn-analysis.json`, absence of runtime metrics or dashboards.

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: No IaC. No Terraform, CloudFormation, CDK, Helm, or Kubernetes manifests. Infrastructure is GitHub-hosted (Pages, Packages, Actions). `.github/workflows/` define CI/CD but not infrastructure. No drift detection.
- **Gap**: No IaC governance for integration surface.
- **Recommendation**: Define all infrastructure as Terraform/CDK if migrating to cloud-hosted API service.
- **Evidence**: Absence of `.tf`, `.tfvars`, `template.yaml`, `cdk.json`, `Chart.yaml`, or `kustomization.yaml`.

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: GitHub Actions CI exists (`.github/workflows/maven.yml`), runs on push/PR to master. Maven `analysis` profile runs BPMN MIWG analysis tools during `test` phase. No API contract tests (no Pact, OpenAPI validation, schema comparison). Release workflow creates ZIP artifacts.
- **Gap**: CI exists but no API contract testing. Data structure changes not validated against schema.
- **Recommendation**: Add JSON Schema validation for metadata files to CI pipeline.
- **Evidence**: `.github/workflows/maven.yml`, `.github/workflows/release.yml`, `pom.xml`.

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: No automated rollback. No blue/green, CodeDeploy, Helm rollback, feature flags, or canary deployment. GitHub Pages deployed via `peaceiris/actions-gh-pages@v4` with `keep_files: true`. Git provides manual rollback. Release ZIP files are versioned.
- **Gap**: No automated rollback. Recovery requires manual Git revert.
- **Recommendation**: Add manual rollback workflow to GitHub Actions for GitHub Pages deployments.
- **Evidence**: `.github/workflows/maven.yml`, `.github/workflows/release.yml`.

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: No API test suites (no Postman, pytest API tests, REST Assured). Maven `test` phase runs BPMN MIWG analysis tools — data validation, not API testing. No API endpoints to test. Evaluated as INFO for `stateless-utility` archetype.
- **Implication**: BPMN interchange validation provides data quality assurance — the most relevant form of testing.
- **Recommendation**: Implement API test suites when building API service.
- **Evidence**: `pom.xml` (`bpmn-miwg-maven-plugin`), `.github/workflows/maven.yml`, `bpmn-analysis.json`.

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent data stores. No databases, S3 buckets, or persistent stores. Data stored in Git/GitHub.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated
## Evidence Index

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/maven.yml` | API-Q1, AUTH-Q1, AUTH-Q2, AUTH-Q5, AUTH-Q6, HITL-Q3, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4 |
| `.github/workflows/release.yml` | AUTH-Q1, ENG-Q2, ENG-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `pom.xml` | API-Q1, AUTH-Q1, AUTH-Q5, DISC-Q1, HITL-Q3, DATA-Q7, ENG-Q2, ENG-Q4 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `test-case-structure.json` | API-Q5, DATA-Q7, DISC-Q1, DISC-Q2, DISC-Q3 |
| `tools-tested-by-miwg.json` | API-Q5, DATA-Q1, DATA-Q2, DATA-Q6, DATA-Q7, DISC-Q2, DISC-Q3 |
| `bpmn-analysis.json` | API-Q5, DATA-Q7, OBS-Q3, ENG-Q4 |

### Source Code (Shell Scripts)
| File | Questions Referenced |
|------|---------------------|
| `publish.sh` | (inventoried — no questions directly cite) |
| `yaoqiang.sh` | (inventoried — no questions directly cite) |

### Data Files
| File | Questions Referenced |
|------|---------------------|
| `Reference/A.1.0.bpmn` | API-Q5, DISC-Q2 |
| `Reference/xsdTypes.xsd` | DISC-Q1 |
| `Reference/*.bpmn` (all reference models) | DATA-Q1, DATA-Q2 |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| `README.md` | API-Q1, DISC-Q3 |
| `LICENSE.txt` | DATA-Q1, DATA-Q2 |
| `.gitignore` | (inventoried — no questions directly cite) |
