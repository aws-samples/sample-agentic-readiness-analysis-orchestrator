# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | apache--flink-connector-aws |
| **Date** | 2026-05-07 |
| **Repo Type** | monorepo |
| **Priority** | P2 |
| **Tags** | java, streaming, flink, aws |
| **Context** | Apache Flink connectors for AWS services (Kinesis, DynamoDB, SQS, etc.) |
| **Overall Score** | 2.68 / 4.0 |

**Surface Flags**: has_persistent_data_store=false, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=false, has_multi_instance_deployment=false

> **Note**: While classified as `monorepo`, this repository is a multi-module Maven library project that publishes connector JARs to Maven Central. It contains no deployable services, no infrastructure-as-code, no containers, and no runtime entry points. The multiple Maven modules (kinesis-streams, firehose, dynamodb, sqs, glue-schema-registry) are not independently deployable services — they are library artifacts consumed by downstream Flink applications. Several infrastructure-oriented questions are gated by surface flags and recorded as Not Evaluated.

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | 2.00 / 4.0 | 🟠 Needs Work | Critical |
| Application Architecture (APP) | 3.50 / 4.0 | ✅ Mature | Ready |
| Data Platform Modernization (DATA) | 3.67 / 4.0 | ✅ Mature | Ready |
| Security Baseline (SEC) | 2.00 / 4.0 | 🟠 Needs Work | Critical |
| Operations & Observability (OPS) | 2.25 / 4.0 | 🟠 Needs Work | Needs Work |
| **Overall** | **2.68 / 4.0** | **🟡 Partial** |  |

### Scoring Notes

- **INF**: INF-Q1 through INF-Q9 = Not Evaluated (surface-gated: no deployed workload, no database, no API surface). INF-Q10=2, INF-Q11=2 → (2+2)/2 = **2.00**
- **APP**: APP-Q1=3, APP-Q2=4, APP-Q3=Not Evaluated, APP-Q4=Not Evaluated, APP-Q5=4, APP-Q6=3 → (3+4+4+3)/4 = 14/4 = **3.50**
- **DATA**: DATA-Q1=3, DATA-Q2=4, DATA-Q3=Not Evaluated (no database), DATA-Q4=4 → (3+4+4)/3 = 11/3 = **3.67**
- **SEC**: SEC-Q1=1, SEC-Q2=Not Evaluated, SEC-Q3=Not Evaluated, SEC-Q4=Not Evaluated, SEC-Q5=2, SEC-Q6=2, SEC-Q7=3 → (1+2+2+3)/4 = 8/4 = **2.00**
- **OPS**: OPS-Q1=3, OPS-Q2=Not Evaluated, OPS-Q3=Not Evaluated, OPS-Q4=Not Evaluated, OPS-Q5=Not Evaluated, OPS-Q6=3, OPS-Q7=1, OPS-Q8=2, OPS-Q9=Not Evaluated → (3+3+1+2)/4 = 9/4 = **2.25**
- **Overall**: (2.00 + 3.50 + 3.67 + 2.00 + 2.25) / 5 = 13.42 / 5 = **2.68**

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | SEC-Q1: Audit Logging | 1 | No CloudTrail or audit logging configuration in the repository | No audit trail for build/release processes; compliance gap for library governance |
| 2 | OPS-Q7: Incident Response Automation | 1 | No runbooks or incident response automation found | Ad hoc response to build failures or security advisories; slower remediation |
| 3 | INF-Q10: Infrastructure as Code Coverage | 2 | No IaC for infrastructure — CI/CD defined in GitHub Actions only; no reproducible environment definitions | CI/CD environment not codified as IaC; environment drift risk for build agents |
| 4 | INF-Q11: CI/CD Automation | 2 | CI/CD pipeline exists with build and test stages but no automated release/publish workflow and no security scanning gate | Manual release process limits velocity; no automated quality gates for security |
| 5 | SEC-Q5: Secrets Management | 2 | CI secrets stored as GitHub Actions secrets (not a dedicated secrets manager); no rotation configured | Static credentials without rotation create long-lived exposure risk |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 2; GitHub Actions workflows present with build, test, and e2e stages)
- **What it enables:** An agent that triggers builds, checks build status, monitors nightly test results, and reports failures across the multi-JDK matrix
- **Additional steps:** GitHub API integration already possible via existing workflows; would benefit from structured build status reporting
- **Effort:** Low

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository (`docs/` directory with connector documentation in Markdown, plus comprehensive README.md)
- **What it enables:** A knowledge agent that indexes connector documentation, API patterns, and configuration options to answer developer questions about using the Flink AWS connectors
- **Additional steps:** Documentation is spread across `docs/content/docs/connectors/` — would benefit from indexing all Markdown content
- **Effort:** Low

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 4 — library modules are well-decomposed with clear boundaries. No monolith to decompose. |
| 2 | Move to Containers | Not Triggered | — | — | This is a library project with no compute workload to containerize. No Dockerfile needed — distributed as Maven JARs. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 — no stored procedures or proprietary SQL. No commercial database engines detected. |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 Not Evaluated — no database deployed by this project. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 Not Evaluated — this IS the streaming connector library (not a consumer of streaming infrastructure). No data processing workloads to migrate. |
| 6 | Move to Modern DevOps | Triggered | Medium | Medium | INF-Q10 = 2 (partial IaC), INF-Q11 = 2 (partial CI/CD automation) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. |

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current State:**
- **IaC Coverage (INF-Q10 = 2):** CI/CD is defined in GitHub Actions YAML, but there is no infrastructure-as-code beyond the pipeline definitions. Build environments, Maven repository settings, and release configurations are not codified as reproducible IaC.
- **CI/CD Automation (INF-Q11 = 2):** Build and test stages are fully automated across JDK 11/17/21, including E2E tests. However, the release/publish workflow to Maven Central is not automated in the repository, and there is no security scanning gate (SAST, dependency vulnerability scanning) integrated into the pipeline.

**Gaps Identified:**
1. No automated release pipeline (Maven Central publishing requires manual steps)
2. No SAST or dependency scanning in CI/CD (SEC-Q7 = 3 — only basic license checking exists)
3. No IaC for build environment reproducibility
4. No automated rollback or canary strategy (not applicable for a library, but staged releases via Maven staging repos could be automated)

**Recommendations:**
- Add automated dependency vulnerability scanning (e.g., `mvn org.owasp:dependency-check-maven:check`) to the CI pipeline
- Automate Maven Central release via GitHub Actions (Apache has standard release workflows)
- Add SAST scanning (e.g., CodeQL GitHub Action) as a required check
- Consider adding Dependabot or Renovate for automated dependency updates

**Representative AWS Services:** CodeBuild (for reproducible build environments), CodeArtifact (for artifact management), CodeGuru Reviewer (for automated code review)

**Learning Materials:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This repository is a library project with no deployed compute workload. It publishes JAR artifacts consumed by downstream Flink applications. No EC2, ECS, EKS, Lambda, or other compute resources are defined or needed. Surface flag `has_deployed_workload=false`. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No IaC files, no Dockerfiles, no Kubernetes manifests found in repository. |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy a database. INF-Q2 does not apply. The repository provides connectors TO databases (DynamoDB) but does not itself provision or manage any database. Surface flag `has_persistent_data_store=false`. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database resources in IaC (no IaC exists); no database connection strings in application code; SQL files are Flink SQL DDL/DML for testing only. |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This is a library project with no runtime workflows to orchestrate. No multi-step business processes exist — the library provides connector components consumed by external Flink applications that handle their own orchestration. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No Step Functions, Temporal, or workflow definitions. No multi-step coordination in source code. |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This repository IS the streaming connector library — it provides Flink connectors for Kinesis Streams, Kinesis Firehose, DynamoDB Streams, SQS, and Glue Schema Registry. It does not itself consume or produce messages at runtime. The library enables downstream applications to use managed AWS messaging/streaming services. Surface flag `has_deployed_workload=false`. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | Source code in `flink-connector-aws/flink-connector-aws-kinesis-streams/`, `flink-connector-aws/flink-connector-sqs/` implements connectors for these services. No runtime messaging infrastructure deployed. |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This is a library project with no deployed services or network infrastructure. No VPC, subnets, security groups, or network configuration exists because the library has no runtime deployment. Surface flag `has_deployed_workload=false`. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No IaC files, no network configuration, no deployment manifests. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This is a library project with no API surface exposed as a running service. APIs are Java builder-pattern interfaces consumed as compile-time dependencies. Surface flag `has_api_surface=false`. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No API Gateway, ALB, or load balancer configurations. No HTTP endpoints defined. |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This is a library project with no deployed workload requiring auto-scaling. Surface flag `has_deployed_workload=false`. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No compute resources, no auto-scaling configuration, no IaC. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no persistent state to back up. INF-Q8 does not apply. Surface flags `has_persistent_data_store=false`, `has_at_rest_data_surface=false`. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No databases, no S3 buckets, no persistent storage defined. |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload requiring HA evaluation. INF-Q9 does not apply. Surface flags `has_deployed_workload=false`, `has_api_surface=false`. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No compute resources, no multi-AZ configuration, no deployment manifests. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | CI/CD pipeline definitions exist in GitHub Actions YAML (`.github/workflows/`), which constitutes partial IaC for the build/test/release process. However, there is no infrastructure-as-code for build environments, Maven repository configurations, or release infrastructure beyond the workflow definitions themselves. |
| **Gap** | No IaC beyond CI/CD workflow files. Build environment configuration (JDK versions, Maven settings, caching) is defined inline in workflow YAML rather than as reusable, versioned infrastructure modules. No Terraform, CDK, or CloudFormation for any supporting infrastructure. |
| **Recommendation** | For a library project, the primary IaC surface is the CI/CD pipeline itself. Consider codifying build environment requirements as a reusable composite action or container definition. If AWS resources are used for E2E testing (the pipeline references AWS credentials), those test resources should be defined in IaC. |
| **Evidence** | `.github/workflows/push_pr.yml`, `.github/workflows/common.yml`, `.github/workflows/nightly.yml`, `.github/workflows/atx-transform.yml` |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GitHub Actions CI/CD pipeline automates build and test stages comprehensively: multi-JDK matrix (11, 17, 21), unit tests, E2E tests (local and AWS), license checking, and nightly builds against Flink SNAPSHOT. However, the release/publish workflow to Maven Central is not automated in this repository, and deployment is effectively manual or handled externally by the Apache release process. |
| **Gap** | No automated release pipeline in the repository. Build is automated but the final deployment (publishing to Maven Central) requires manual steps or external tooling. No security scanning (SAST, dependency vulnerability checking) integrated as a pipeline gate. |
| **Recommendation** | Add an automated release workflow for Maven Central publishing (Apache projects typically use `maven-release-plugin` with GitHub Actions). Integrate dependency vulnerability scanning (OWASP dependency-check or Snyk) as a CI step. Add CodeQL or similar SAST as a required check. |
| **Evidence** | `.github/workflows/push_pr.yml` (build + test), `.github/workflows/common.yml` (compile, test, e2e, license check), `.github/workflows/nightly.yml` (nightly SNAPSHOT builds). No release workflow found. |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Primary language is Java 11 with an active migration to Java 17 (ATX Transform workflow in progress). AWS SDK v2 (2.40.3) is already in use — no SDK version lag. Framework is Apache Flink 2.0.0 (latest major version). Python 3.8+ bindings also present. The language version (Java 11) is the primary lag — it is approaching end of extended support. AWS SDK v2 and Flink 2.0.0 are both current. |
| **Gap** | Java 11 is the current source level, which is one LTS version behind Java 17 (current target) and two behind Java 21 (latest LTS). Java 11 is still supported but lacks modern language features (records, sealed classes, pattern matching) that improve code quality. |
| **Recommendation** | Complete the Java 11 → 17 migration (already in progress via ATX Transform workflow). This will bring the source level to the current LTS with modern language features while maintaining compatibility with the Flink 2.0.0 runtime. |
| **Evidence** | `pom.xml` — `<flink.version>2.0.0</flink.version>`, `<aws.sdkv2.version>2.40.3</aws.sdkv2.version>`. `.github/workflows/push_pr.yml` — tests against JDK 11, 17, 21. `.github/workflows/atx-transform.yml` — Java 11→17 migration. |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The repository is a well-structured multi-module Maven project with clear module boundaries. Each connector (Kinesis Streams, Firehose, DynamoDB, SQS) is an independent module with its own `pom.xml`, source tree, and test suite. Modules depend on a shared `flink-connector-aws-base` for common utilities but have no circular dependencies. Each module produces an independent artifact (JAR) that can be consumed separately. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | Root `pom.xml` defines modules: `flink-connector-aws-base`, `flink-connector-aws`, `flink-formats-aws`, `flink-python`, `flink-connector-aws-e2e-tests`. Each sub-module has independent source and test trees. ArchUnit tests enforce architectural boundaries. |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This is a library project with no inter-service communication. The library itself implements both synchronous and asynchronous communication patterns for downstream consumers (Kinesis producer/consumer, SQS producer, DynamoDB sink), but the library does not perform inter-service communication at its own runtime. This question evaluates a runtime communication pattern that does not apply to a library artifact. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | Source code implements connectors for async services (Kinesis, SQS) but has no runtime service-to-service calls. |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This is a library project with no runtime processes. The connectors it provides handle long-running stream processing when embedded in a Flink application, but the library itself does not execute long-running operations independently. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No main() entry points, no runtime processes, no HTTP endpoints. |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The project follows semantic versioning (currently 6.0-SNAPSHOT) with Maven artifact versioning. API stability is maintained through the `@PublicEvolving` and `@Internal` Flink annotations that signal API stability guarantees to consumers. The version is explicitly defined in the root POM and propagated to all modules. Breaking changes are scoped to major version bumps (aligning with Flink major versions). |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | Root `pom.xml`: `<version>6.0-SNAPSHOT</version>`. Flink annotation-based API stability markers in source code. Maven artifact versioning with SNAPSHOT/release cycle. |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | As a library project, "service discovery" manifests as dependency resolution — consumers discover and use the library via Maven coordinates. The library itself configures AWS service endpoints through AWS SDK v2 client configuration, which supports custom endpoint resolution, region-based endpoint discovery, and VPC endpoint configuration. Endpoint configuration is externalized via configuration properties (`AWSConfigConstants.AWS_ENDPOINT`, `AWSConfigConstants.AWS_REGION`). |
| **Gap** | AWS endpoint configuration uses environment variable and property-based configuration. While this is appropriate for a library, there is no integration with dynamic service discovery (e.g., CloudMap, Consul) for the downstream Flink applications that consume these connectors. |
| **Recommendation** | N/A for the library itself — endpoint configuration via properties is the correct pattern. Downstream applications consuming these connectors should use AWS SDK v2's endpoint discovery features or VPC endpoints for private connectivity. |
| **Evidence** | `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java` — defines `AWS_ENDPOINT`, `AWS_REGION`, `TRUST_ALL_CERTIFICATES` configuration options. |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The library provides connectors that write to AWS data services (Kinesis Firehose delivers to S3, DynamoDB stores structured data). The Kinesis Firehose connector enables downstream applications to deliver streaming data to S3 for storage and analytics. The library itself does not store unstructured data, but it facilitates S3-based storage via Firehose delivery streams. Documentation is stored as Markdown files in the repository. |
| **Gap** | No automated parsing pipeline for documentation or unstructured artifacts within the project itself (documentation is static Markdown). |
| **Recommendation** | N/A — the library's primary purpose is enabling data flow to managed AWS storage services. Documentation format is appropriate for a library project. |
| **Evidence** | `flink-connector-aws/flink-connector-aws-kinesis-firehose/` — Firehose sink connector enables S3 delivery. `docs/` directory contains Markdown documentation. |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The library implements a clean, unified data access architecture. All AWS service interactions go through a centralized base module (`flink-connector-aws-base`) that provides: `AWSClientUtil` for standardized client creation, `AWSGeneralUtil` for credential management, and `AWSConfigConstants`/`AWSConfigOptions` for configuration. Each connector module builds on this unified base layer with connector-specific implementations. There is no scattered AWS SDK usage — all client creation and configuration flows through the base module. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/util/AWSClientUtil.java`, `AWSGeneralUtil.java`, `AWSConfigConstants.java`. All connector modules depend on `flink-connector-aws-base`. |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy any database. The library provides connectors to DynamoDB (a serverless, fully managed service with no user-managed engine versions). No database engine version pinning is applicable because no database is provisioned by this project. Surface flag `has_persistent_data_store=false`. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database resources in any configuration. DynamoDB connector connects to a fully managed service. |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs. All business logic resides in the Java application layer (connector implementations). SQL files in the repository are Flink SQL DDL/DML statements used for testing connector integration with Flink's SQL layer — they are not database stored procedures. The library uses standard, portable data access patterns through the AWS SDK v2. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | SQL files in `flink-connector-aws-e2e-tests/` and `flink-connector-aws/flink-connector-dynamodb/src/test/` are Flink SQL (e.g., `CREATE TABLE ... WITH ('connector' = 'dynamodb')`), not stored procedures. No `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION` patterns found. |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail, audit logging, or equivalent logging infrastructure is configured in this repository. The library uses Log4j2 for application-level logging (debug/info/error), but there is no audit trail for builds, releases, or security events. GitHub Actions provides some inherent audit logging for workflow runs, but this is not explicitly configured or managed. |
| **Gap** | No audit logging infrastructure. For a library project, the relevant audit surface is: who triggered releases, what dependencies changed, what security advisories were addressed. None of this is explicitly tracked beyond GitHub's default audit log. |
| **Recommendation** | Enable GitHub audit log streaming to a centralized log store for release tracking. Consider adding a CHANGELOG.md with automated generation from commit history. For the Apache release process, ensure release signing and verification steps are documented and auditable. |
| **Evidence** | No `aws_cloudtrail`, no audit log configuration. Log4j2 configs (`log4j2.properties`, `log4j2-test.properties`) are for application debugging only. |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no database, S3 bucket, EBS volume, or similar. SEC-Q2 does not apply. The library provides connectors that may write to encrypted destinations, but it does not own or configure encryption for any data store. Surface flag `has_at_rest_data_surface=false`. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No IaC defining data stores. No S3, RDS, DynamoDB, or EBS resources. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This is a library project with no API endpoints to authenticate. The library IMPLEMENTS AWS authentication for downstream consumers (supporting ENV_VAR, PROFILE, ASSUME_ROLE, WEB_IDENTITY_TOKEN, CUSTOM, AUTO credential providers), but it does not expose APIs that require authentication. Surface flag `has_api_surface=false`. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java` — credential provider types. No HTTP endpoints. |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This is a library project with no application-level authentication. The library supports AWS credential providers including ASSUME_ROLE and WEB_IDENTITY_TOKEN (which integrate with centralized identity), but it does not itself authenticate users. Surface flag `has_api_surface=false`. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `AWSConfigConstants.CredentialProvider` enum supports `WEB_IDENTITY_TOKEN`, `ASSUME_ROLE` — enabling IdP integration for downstream applications. |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | CI/CD secrets (AWS credentials for E2E tests, ATX API keys) are stored as GitHub Actions secrets — referenced via `${{ secrets.FLINK_AWS_USER }}`, `${{ secrets.FLINK_AWS_PASSWORD }}`, etc. No plaintext credentials found in source code or committed configuration files. However, GitHub Actions secrets are static (no rotation), not managed by a dedicated secrets manager, and the E2E tests use username/password credentials rather than short-lived role assumption. The ATX workflow correctly uses OIDC role assumption (`ATXCI_AWS_ROLE_ARN`). |
| **Gap** | E2E test credentials (`FLINK_AWS_USER`, `FLINK_AWS_PASSWORD`) are static GitHub secrets without rotation. The ATX workflow uses OIDC (good), but E2E tests still use long-lived static credentials. No Secrets Manager or Vault integration. |
| **Recommendation** | Migrate E2E test authentication from static credentials to OIDC-based role assumption (matching the ATX workflow pattern). This eliminates long-lived credentials. If static credentials are required, implement GitHub secret rotation automation. |
| **Evidence** | `.github/workflows/common.yml` — `FLINK_AWS_USER: ${{ secrets.FLINK_AWS_USER }}`, `FLINK_AWS_PASSWORD: ${{ secrets.FLINK_AWS_PASSWORD }}`. `.github/workflows/atx-transform.yml` — OIDC role assumption (better pattern). |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | CI runs on `ubuntu-latest` GitHub-hosted runners (maintained by GitHub with regular patching). JDK versions are explicitly set via `actions/setup-java@v3`. Maven is pinned to 3.8.6 via `stCarolas/setup-maven@v4.5`. However, there is no vulnerability scanning of the build environment, no hardened base images, and no evidence of dependency vulnerability scanning in the pipeline. |
| **Gap** | No vulnerability scanning of dependencies or build environment. Reliance on `ubuntu-latest` provides basic patching but no hardening. Third-party GitHub Actions used without version pinning to SHA (e.g., `actions/checkout@v3` rather than a specific SHA). |
| **Recommendation** | Pin third-party GitHub Actions to specific commit SHAs for supply chain security. Add `mvn org.owasp:dependency-check-maven:check` or similar to the CI pipeline to scan for vulnerable dependencies. Consider using GitHub's Dependabot for automated dependency update PRs. |
| **Evidence** | `.github/workflows/common.yml` — `runs-on: ubuntu-latest`, `uses: actions/setup-java@v3`, `uses: stCarolas/setup-maven@v4.5`, `uses: actions/checkout@v3`. |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The CI pipeline includes Apache RAT (license checking), Checkstyle (code style), Spotless (formatting), and ArchUnit (architecture enforcement). These provide code quality gates but not security-specific scanning. No SAST tool (CodeQL, SonarQube, Semgrep) or dependency vulnerability scanner (OWASP dependency-check, Snyk) is integrated. The license check step does verify compliance but is not a security tool. |
| **Gap** | No SAST or dependency vulnerability scanning in the CI pipeline. The existing quality tools (Checkstyle, ArchUnit, RAT) enforce code style and architecture but do not detect security vulnerabilities. |
| **Recommendation** | Add CodeQL GitHub Action (free for open source) for SAST. Add OWASP dependency-check Maven plugin or GitHub Dependabot for dependency vulnerability alerts. These integrate with the existing GitHub Actions pipeline with minimal configuration. |
| **Evidence** | `.github/workflows/common.yml` — license check step. `pom.xml` — `apache-rat-plugin`, `spotless-maven-plugin`, `maven-checkstyle-plugin`. `tools/maven/checkstyle.xml`. No CodeQL, SonarQube, Snyk, or OWASP dependency-check configuration. |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The library uses SLF4J/Log4j2 logging throughout all modules with consistent logging patterns. While not distributed tracing per se, the library is designed to operate within the Flink ecosystem which supports OpenTelemetry integration. The connector base utilities support request ID propagation through AWS SDK v2 clients (which natively support X-Ray tracing when the downstream application configures it). The library does not introduce tracing barriers. |
| **Gap** | No explicit OpenTelemetry or X-Ray instrumentation in the connector code itself. Tracing depends on the consuming Flink application's configuration. The library could instrument connector operations (source reads, sink writes) with trace spans for better observability. |
| **Recommendation** | Consider adding optional OpenTelemetry instrumentation to connector operations (e.g., span around Kinesis putRecords, DynamoDB batchWriteItem). This would provide visibility into connector performance when the consuming application has tracing enabled. AWS SDK v2 already supports automatic X-Ray tracing. |
| **Evidence** | Log4j2 configuration in every module (`src/main/resources/log4j2.properties`). AWS SDK v2 (2.40.3) in `pom.xml` supports X-Ray tracing natively. No explicit OpenTelemetry SDK dependency. |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no user-facing surface for which SLOs are meaningful. OPS-Q2 does not apply. The library does not serve traffic or expose endpoints — SLOs are the responsibility of downstream applications consuming these connectors. Surface flags `has_api_surface=false`, `has_persistent_data_store=false`. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No deployed service, no API surface, no traffic serving. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This is a library project with no runtime business outcomes to measure. The library exposes Flink metrics (counter, gauge) for connector operations when embedded in a Flink application, but these are Flink framework metrics, not standalone business metrics. Surface flag `has_deployed_workload=false`. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No CloudWatch metric publishing. Flink metric integration is handled by the Flink runtime framework. |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This is a library project with no deployed workload requiring anomaly detection. Alerting on library behavior is the responsibility of the consuming Flink application. Surface flag `has_deployed_workload=false`. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No CloudWatch alarms, no anomaly detection configuration. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This is a library project distributed via Maven Central. "Deployment" is artifact publication, not service deployment. The library uses Maven's SNAPSHOT/release lifecycle and Apache's release process. There is no blue/green or canary — these concepts don't apply to library publishing. Surface flag `has_deployed_workload=false`. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `<version>6.0-SNAPSHOT</version>` in `pom.xml`. No deployment manifests or service deployment configurations. |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive integration and E2E test suites exist. The `flink-connector-aws-e2e-tests/` module contains E2E tests for all major connectors (Kinesis Streams, Firehose, SQS, Glue Schema Registry Avro/JSON). Tests run against real Flink distributions and (conditionally) against real AWS services. TestContainers is used for local integration tests. E2E tests are integrated into the CI pipeline (`.github/workflows/common.yml` — "Run e2e tests" step). |
| **Gap** | AWS E2E tests only run when `FLINK_AWS_USER` secrets are available — meaning they may not run on external PRs (only on builds with secret access). Some connector modules may have less E2E coverage than others. |
| **Recommendation** | Consider adding LocalStack-based integration tests that can run without AWS credentials, enabling E2E coverage on all PRs including external contributions. This removes the dependency on real AWS credentials for integration validation. |
| **Evidence** | `flink-connector-aws-e2e-tests/` — 5 E2E test modules. `.github/workflows/common.yml` — "Run e2e tests" and "Run AWS e2e tests" steps. `HAS_AWS_CREDS` conditional for AWS tests. `pom.xml` — TestContainers 1.17.2 dependency. |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, incident response automation, or structured response procedures found in the repository. Build failures are handled ad hoc. There are no Systems Manager Automation documents, no remediation Lambda functions, and no structured escalation procedures for common issues (dependency conflicts, failing E2E tests, security advisories). |
| **Gap** | No incident response automation. No runbooks for common failure scenarios (build breaks, dependency CVEs, Flink incompatibilities). No automated triage or notification beyond default GitHub Actions failure emails. |
| **Recommendation** | Create structured runbooks (in Markdown) for common scenarios: build failure triage, dependency CVE response, Flink version compatibility issues, release rollback procedures. Consider GitHub Actions for automated security advisory responses (e.g., auto-create issues for CVE notifications). |
| **Evidence** | No runbook files (no `runbooks/`, `docs/operations/`, or `.github/ISSUE_TEMPLATE/` with incident templates). No automation documents. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The repository has a `CODEOWNERS`-like structure via `.asf.yaml` (Apache Software Foundation configuration) that defines committer access. However, there are no per-module dashboards, no named owners for specific operational aspects, and no SLO definitions tied to teams. The CI nightly workflow provides some monitoring of build health but without explicit ownership attribution. |
| **Gap** | No per-module ownership for build health, no defined responsibilities for dependency management or security responses, no structured observability of library usage or issues. |
| **Recommendation** | Define CODEOWNERS file mapping modules to responsible maintainers. Add GitHub issue templates for module-specific bug reports. Consider adding a `SECURITY.md` with named security contacts and response SLAs. |
| **Evidence** | `.asf.yaml` — ASF project configuration. No `CODEOWNERS` file. No per-module ownership docs. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This is a library project with no AWS resources to tag. Resource tagging is not applicable because no infrastructure is provisioned. Surface flag `has_deployed_workload=false`. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No IaC, no AWS resources, no tagging configuration. |

---

## Learning Materials

- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `pom.xml` | APP-Q1, APP-Q2, APP-Q5, OPS-Q1, OPS-Q6 | Root Maven POM defining module structure, dependency versions (AWS SDK v2 2.40.3, Flink 2.0.0, JDK config), build plugins |
| `.github/workflows/push_pr.yml` | APP-Q1, INF-Q11 | CI pipeline triggering on push/PR with multi-JDK matrix |
| `.github/workflows/common.yml` | INF-Q11, SEC-Q5, SEC-Q6, OPS-Q6 | Reusable CI workflow with compile, test, E2E, license check stages |
| `.github/workflows/nightly.yml` | INF-Q11 | Nightly build against Flink SNAPSHOT |
| `.github/workflows/atx-transform.yml` | APP-Q1, SEC-Q5 | ATX automation workflow with OIDC auth |
| `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java` | APP-Q6, SEC-Q3, SEC-Q4 | AWS configuration constants including credential provider types and endpoint configuration |
| `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/util/AWSClientUtil.java` | DATA-Q2 | Centralized AWS client creation utility |
| `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/util/AWSGeneralUtil.java` | DATA-Q2 | Centralized AWS credential management utility |
| `flink-connector-aws-e2e-tests/` | OPS-Q6 | E2E test modules for all connectors |
| `tools/maven/checkstyle.xml` | SEC-Q7 | Checkstyle code quality rules |
| `.asf.yaml` | OPS-Q8 | Apache Software Foundation project configuration |
| `docs/` | DATA-Q1 | Documentation directory with connector docs |
| `flink-connector-aws/flink-connector-aws-kinesis-streams/` | INF-Q4 | Kinesis Streams connector source |
| `flink-connector-aws/flink-connector-sqs/` | INF-Q4 | SQS connector source |
| `flink-connector-aws/flink-connector-aws-kinesis-firehose/` | DATA-Q1 | Firehose connector enabling S3 delivery |
| `flink-connector-aws-e2e-tests/*/src/test/resources/*.sql` | DATA-Q4 | Flink SQL DDL/DML test files (not stored procedures) |
