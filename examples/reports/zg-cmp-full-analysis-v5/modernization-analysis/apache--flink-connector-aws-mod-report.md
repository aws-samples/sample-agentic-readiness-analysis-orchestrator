# Modernization Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | flink-connector-aws |
| **Date** | 2026-04-30 |
| **TD Version** | 3g1iuew7esd4bia3 |
| **Repo Type** | monorepo |
| **Service Archetype** | stateless-utility (auto-detected) |
| **Priority** | P2 |
| **Tags** | java, streaming, flink, aws |
| **Context** | Apache Flink connectors for AWS services (Kinesis, DynamoDB, SQS, etc.) |
| **Preferences** | Prefer: eks, aurora, dynamodb, api-gateway, eventbridge, bedrock · Avoid: self-managed-kafka, self-managed-kubernetes, oracle |
| **Overall Score** | 2.1 / 4.0 |

**Archetype Justification**: All modules are Java library JARs (Source/Sink connector implementations) published to Maven Central and embedded into consumer Flink applications. No module exposes an HTTP server, owns persistent state, or runs as a standalone deployable service. The connectors are pure data pipeline components with no database connections, no write endpoints, and no downstream service calls. Classified as `stateless-utility`.

> **Note**: While the user specified `repo_type: "monorepo"`, every module within this repository functions as a library (Java JAR with no deployable entry point, no Dockerfile, no IaC). The `monorepo` classification is preserved per user specification, but all 5 surface flags are `false`, which results in several surface-gated questions being recorded as Not Evaluated (archetype-N/A).

**Surface Flags**: has_persistent_data_store=false, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=false, has_multi_instance_deployment=false

---

<!-- SECTION 2: SCORE SUMMARY -->
## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.3 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 3.3 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 2.5 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.8 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.6 / 4.0 | 🟠 Needs Work |
| **Overall** | **2.1 / 4.0** | **🟠 Needs Work** |

**Scoring Notes:**
- INF category: 7 questions scored (INF-Q2, INF-Q3, INF-Q8, INF-Q9 excluded as Not Evaluated via surface gates/archetype-N/A). Score = (1+1+1+1+1+1+3)/7 = 9/7 = 1.3
- APP category: 4 questions scored (APP-Q3 and APP-Q4 excluded as Not Evaluated/archetype-N/A for stateless-utility). Score = (3+4+3+3)/4 = 13/4 = 3.3
- DATA category: 4 questions scored (all evaluated). Score = (2+3+1+4)/4 = 10/4 = 2.5
- SEC category: 6 questions scored (SEC-Q2 excluded as Not Evaluated via surface gate). Score = (1+3+3+2+1+1)/6 = 11/6 = 1.8
- OPS category: 8 questions scored (OPS-Q2 excluded as Not Evaluated via surface gate). Score = (1+3+1+1+3+1+2+1)/8 = 13/8 = 1.6
- Overall: (1.3 + 3.3 + 2.5 + 1.8 + 1.6) / 5 = 10.5 / 5 = 2.1

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q1: Managed Compute | 1 | No compute infrastructure defined — library has no deployable workload | No infrastructure to modernize; consuming applications own compute decisions |
| 2 | INF-Q10: IaC Coverage | 1 | No infrastructure-as-code files found anywhere in the repository | No reproducible infrastructure; all deployment is delegated to consumers |
| 3 | SEC-Q7: Application Security Pipeline | 1 | No SAST, dependency scanning, or container scanning in CI/CD pipeline | Vulnerabilities in dependencies may reach consumers undetected |
| 4 | SEC-Q1: Audit Logging | 1 | No CloudTrail or audit logging configuration | Expected for library; consuming application owns audit logging |
| 5 | SEC-Q6: Compute Hardening | 1 | No compute resources to harden; no vulnerability scanning configured | Dependency vulnerabilities are the primary security risk for libraries |

---

## Quick Agent Wins

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists — rich connector documentation found in `docs/content/docs/connectors/datastream/` (Kinesis, DynamoDB, Firehose, SQS) in both English and Chinese, plus `README.md` with build instructions. Total documentation exceeds 80KB across 8+ markdown files.
- **What it enables:** A RAG-based knowledge agent could index all connector documentation and provide natural-language answers to developer questions about configuration options, credential setup, source/sink builder patterns, serialization/deserialization schemas, and troubleshooting. This would reduce onboarding time for teams adopting the connectors.
- **Additional steps:** Generate a searchable index of the documentation. Consider adding API Javadoc as an additional knowledge source.
- **Effort:** Low — documentation is already structured and comprehensive.

### DevOps Agent

- **Prerequisite:** INF-Q11 = 3 (CI/CD pipeline exists with GitHub Actions). The pipeline includes compile, test, e2e tests (local and AWS), licensing checks, and nightly builds.
- **What it enables:** A DevOps agent could trigger builds, check CI status, report test failures, and manage the nightly build schedule. It could also surface build failures from the nightly SNAPSHOT build against Flink 2.0-SNAPSHOT.
- **Additional steps:** The agent would need GitHub API access to the `apache/flink-connector-aws` repository workflows.
- **Effort:** Low — GitHub Actions API provides direct programmatic access to workflow status and triggers.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 4 — monorepo has well-defined module boundaries with clean separation |
| 2 | Move to Containers | Not Triggered | — | — | No deployable compute — this is a library published to Maven Central, not a service |
| 3 | Move to Open Source | Not Triggered | — | — | Repository is already open source (Apache 2.0). No commercial DB engines detected — all connectors target AWS managed services (DynamoDB, Kinesis, SQS) |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 Not Evaluated — no database to manage. Library connects TO managed AWS services |
| 5 | Move to Managed Analytics | Not Triggered | — | — | Library provides streaming connectors but does not deploy analytics infrastructure. No self-managed streaming detected |
| 6 | Move to Modern DevOps | Triggered | Medium | Medium | INF-Q10 = 1 (no IaC). While expected for a library, the CI/CD pipeline (INF-Q11 = 3) lacks security scanning (SEC-Q7 = 1) and deployment strategy is N/A |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in context ("Apache Flink connectors for AWS services"). Context does not mention AI, agent, LLM, or related terms |

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Trigger Analysis:**
- **INF-Q10 = 1** (Primary trigger met): No IaC files exist in the repository. While this is expected for a library project (libraries don't provision infrastructure), the absence means there is no reproducible build infrastructure definition.
- **INF-Q11 = 3** (Primary trigger NOT met): CI/CD automation exists and is well-structured with GitHub Actions.
- **OPS-Q5 = 1** (Supporting): No deployment strategy — expected for a library (no deployable service), but the Maven Central publishing process could benefit from automation.
- **OPS-Q6 = 3** (Supporting trigger NOT met): Integration tests exist and run in CI.

**Current State:**
- CI/CD pipeline is well-automated for build, test, and e2e testing via GitHub Actions (`push_pr.yml`, `common.yml`, `nightly.yml`).
- Testing covers compile, unit tests, local e2e tests (Testcontainers), and conditional AWS e2e tests with real credentials.
- Nightly builds run against Flink 2.0-SNAPSHOT to catch upstream regressions.
- Multi-JDK testing: Java 11, 17, 21.
- **Missing:** No SAST or dependency vulnerability scanning in the pipeline. No Dependabot configuration. No OWASP dependency check.
- **Missing:** No automated Maven Central release pipeline (releases are likely manual via Apache release process).

**Recommendations:**
1. **Add dependency vulnerability scanning** — Configure Dependabot or OWASP `dependency-check-maven` plugin in the build pipeline to catch CVEs in the 50+ transitive dependencies (AWS SDK v2, Netty, Jackson, Guava, etc.).
2. **Add SAST scanning** — Integrate SpotBugs or SonarQube into the Maven build to catch security and quality issues. The existing Checkstyle and Spotless plugins handle style but not security patterns.
3. **Consider automated release pipeline** — While Apache projects have governance constraints on releases, a semi-automated release pipeline with staging validation would reduce release friction.

**Representative AWS Services:** CodeBuild (for enhanced CI), CodeArtifact (for Maven dependency caching), Amazon Inspector (for dependency scanning).

**Learning Resources:**
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute infrastructure is defined anywhere in the repository. No Terraform files, CloudFormation templates, CDK stacks, Helm charts, Kubernetes manifests, or any IaC defining compute resources (ECS, EKS, Lambda, EC2) were found. No Dockerfiles exist. This is a library monorepo — each module produces a JAR artifact published to Maven Central, not a deployable service. Compute decisions are delegated to consuming applications. |
| **Gap** | No compute infrastructure to evaluate. This is architecturally appropriate for a library project. |
| **Recommendation** | No action needed. Compute infrastructure is the responsibility of applications that consume these connector libraries. If the team builds companion infrastructure (e.g., a Flink cluster for testing), define it in IaC. |
| **Evidence** | Absence: No `.tf`, `*.cfn.yaml`, `cdk.json`, `Dockerfile`, `docker-compose.yml`, or Kubernetes manifests found in repository scan. |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy a database. The connectors connect TO AWS managed services (DynamoDB, Kinesis, SQS) as client libraries but do not own or deploy any database infrastructure. `has_persistent_data_store=false`. INF-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database resources in IaC (none exists). No database connection/pool configuration in library source. Connectors use AWS SDK v2 clients to call DynamoDB, Kinesis, SQS, Firehose APIs. |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Workflow orchestration is not applicable by design — no multi-step workflows exist. Each connector module is a stateless data pipeline component (Source or Sink) that plugs into the Flink runtime. The Flink runtime itself handles checkpointing, exactly-once semantics, and failure recovery. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No `aws_sfn_*` in IaC. No Temporal SDK imports. No workflow definitions. All source files implement Flink Source/Sink interfaces (`KinesisStreamsSource.java`, `DynamoDbSink.java`, `SqsSink.java`). |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed messaging or streaming infrastructure is deployed by this repository. The repository IS a streaming connector library — it provides connectors for Kinesis Data Streams, Kinesis Data Firehose, DynamoDB Streams, and SQS. However, it does not deploy any messaging infrastructure itself. The connectors use AWS SDK v2 async clients (`KinesisAsyncClient`, `DynamoDbStreamsAsyncClient`, `SqsAsyncClient`) to interact with managed AWS services, but no infrastructure definition exists. |
| **Gap** | No messaging/streaming infrastructure defined. As a library, this is architecturally expected — the consuming application and its infrastructure own the streaming topology. |
| **Recommendation** | No infrastructure action needed for the library itself. The archetype-calibrated score for `stateless-utility` would normally be 4 ("synchronous is correct design"), but since this is evaluated at monorepo level with the default rubric (no archetype override applied at INF level for monorepo), the score reflects the literal absence of messaging infrastructure. |
| **Evidence** | No `aws_sqs_*`, `aws_sns_*`, `aws_msk_*`, `aws_kinesis_*` in IaC. Library source code uses `software.amazon.awssdk.services.kinesis`, `software.amazon.awssdk.services.sqs`, `software.amazon.awssdk.services.firehose` as client SDKs. |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, security groups, NACLs, or network configuration exists. This is a library — it has no deployed resources requiring network security configuration. Network security is the responsibility of the consuming application's infrastructure. |
| **Gap** | No network security configuration. Architecturally expected for a library. |
| **Recommendation** | No action needed. Consuming applications should deploy connector workloads in private subnets with least-privilege security groups per their infrastructure standards. |
| **Evidence** | No `aws_vpc`, `aws_subnet`, `aws_security_group` resources. No IaC files of any kind. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, AppSync, ALB, or CloudFront configuration exists. This library does not expose API endpoints — it provides Source/Sink connectors embedded in Flink applications. The library has no HTTP server, no REST endpoints, and no API surface. |
| **Gap** | No API entry point. Expected for a library. |
| **Recommendation** | No action needed. This is a library with no API surface to protect. |
| **Evidence** | `has_api_surface=false`. No HTTP framework imports. No API Gateway or ALB resources. |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. This is a library with no deployed compute to scale. Scaling of Flink applications using these connectors is managed by the Flink cluster (task parallelism) and the underlying compute infrastructure of the consuming application. |
| **Gap** | No auto-scaling configuration. Expected for a library. |
| **Recommendation** | No action needed. Auto-scaling is the responsibility of the consuming application's Flink cluster deployment. |
| **Evidence** | No `aws_autoscaling_*` or `aws_appautoscaling_*` resources. No IaC files. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no persistent state to back up. The library does not own databases, S3 buckets, or any data stores. `has_persistent_data_store=false` and `has_at_rest_data_surface=false`. INF-Q8 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database resources, no S3 buckets, no EBS volumes. No IaC files. |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload requiring HA evaluation. The library produces JAR artifacts — it has no running compute, no deployable service, and no infrastructure requiring multi-AZ configuration. `has_deployed_workload=false`. INF-Q9 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No Dockerfiles, no IaC defining compute. No ECS tasks, EKS deployments, Lambda functions, or EC2 instances. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No infrastructure-as-code files exist in the repository. Scanned for `.tf`, `.tfvars`, `template.yaml`, `template.json`, `cdk.json`, `Chart.yaml`, `kustomization.yaml`, and Ansible playbooks — none found. This is a library monorepo with no infrastructure to codify. |
| **Gap** | Zero IaC coverage. While expected for a library, if the team ever adds test infrastructure (e.g., Localstack configurations, test Flink clusters, CI/CD infrastructure), it should be defined in IaC. |
| **Recommendation** | Consider adding IaC for CI/CD infrastructure if the team manages its own build agents or test environments. For the library itself, no IaC is needed. |
| **Evidence** | Full repository scan: 0 IaC files found. Build configuration is Maven-only (`pom.xml`). CI/CD is GitHub Actions YAML (not infrastructure IaC). |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Well-automated CI/CD pipeline via GitHub Actions. Three workflow files found: (1) `push_pr.yml` — triggers on push, PR, and manual dispatch; runs compile and test matrix against Flink 2.0.0 on Java 11, 17, 21; also runs Python tests. (2) `common.yml` — reusable workflow with compile, test, e2e test (local Testcontainers), AWS e2e test (conditional on credentials), and license check. (3) `nightly.yml` — nightly build against Flink 2.0-SNAPSHOT for upstream regression detection. Pipeline covers build, unit test, integration test, e2e test, and licensing validation. |
| **Gap** | No security scanning in the pipeline (no SAST, no dependency vulnerability scanning, no Dependabot). No automated release/publish pipeline (Maven Central releases are managed through Apache release process). The pipeline does not have automated rollback since there is no deployment target. |
| **Recommendation** | Add dependency vulnerability scanning (OWASP `dependency-check-maven` or Dependabot) to catch CVEs in the ~50+ transitive dependencies. Add SpotBugs or SonarQube for SAST. These are medium-effort improvements that significantly increase library security posture. |
| **Evidence** | `.github/workflows/push_pr.yml`, `.github/workflows/common.yml`, `.github/workflows/nightly.yml`. Pipeline steps: checkout → setup-java (11/17/21) → maven build → e2e tests → AWS e2e tests (conditional) → license check. |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Primary language is **Java 11** (minimum requirement per README). CI tests on Java 11, 17, and 21. AWS SDK v2 (2.40.3) — the modern, current AWS SDK for Java. Flink 2.0.0 target — the latest major Flink version. Jackson BOM 2.14.3, Netty 4.1.86.Final. Python bindings exist in `flink-python/` module. Build system is Maven. No Spring Boot (Flink framework is the runtime). The library uses `@PublicEvolving` and `@Experimental` Flink annotations across 56 source files for API stability classification. |
| **Gap** | Java 11 is the minimum target rather than Java 17+. While the CI tests on 17 and 21, the project targets Java 11 as the baseline. Java 11 LTS extended support ends September 2026. The framework is not Spring Boot (using Flink runtime), so framework-lag analysis is N/A — Flink 2.0.0 is the current major version. |
| **Recommendation** | Plan migration of the minimum Java target from 11 to 17 before Java 11 EOL. The CI already validates Java 17 and 21 compatibility, so the migration path is well-tested. This aligns with Flink's own roadmap. |
| **Evidence** | `pom.xml` — `<flink.version>2.0.0</flink.version>`, `<aws.sdkv2.version>2.40.3</aws.sdkv2.version>`. `README.md` — "Prerequisites: Java 11". `.github/workflows/push_pr.yml` — `java: ['11, 17, 21']`. |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Well-structured modular monorepo with clean module boundaries and no circular dependencies. Module hierarchy: `flink-connector-aws-base` (shared base) → `flink-connector-aws` parent containing `flink-connector-dynamodb`, `flink-connector-aws-kinesis-streams`, `flink-connector-aws-kinesis-firehose`, `flink-connector-sqs` → `flink-sql-connector-*` (fat JARs) → `flink-formats-aws` (serialization) → `flink-python` (Python bindings) → `flink-connector-aws-e2e-tests` (test-only). Each connector is an independently releasable Maven module with its own `pom.xml`, source directory, and test suite. Shared code is properly isolated in the base module. |
| **Gap** | None — module boundaries are well-defined with clear interfaces. |
| **Recommendation** | No action needed. The modular monorepo structure is appropriate for a family of related connector libraries. |
| **Evidence** | Root `pom.xml` — `<modules>` defines 5 top-level modules. `flink-connector-aws/pom.xml` — defines 7 sub-modules. Each module has independent `src/main/java/` and `src/test/java/` trees. Base module (`flink-connector-aws-base`) provides shared utilities (`AWSConfigConstants`, `AWSClientUtil`, `AWSGeneralUtil`). ArchUnit architecture tests enforce module boundaries. |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Async vs sync communication patterns are not applicable by design — the library has no inter-service communication. Each connector module is a standalone JAR that provides Flink Source/Sink implementations. Communication between the connector and AWS services uses the AWS SDK v2 async client (`KinesisAsyncClient`, `DynamoDbStreamsAsyncClient`, `SqsAsyncClient`), which is the correct SDK choice, but this is library-to-cloud-service communication, not inter-service communication. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `KinesisAsyncStreamProxy.java`, `KinesisStreamProxy.java` — use SDK async/sync clients. No HTTP clients calling other microservices. No message queue producers/consumers. |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Long-running process handling is not applicable by design — the library delegates long-running operations to the Flink runtime. Flink manages checkpointing, exactly-once semantics, shard discovery, and failure recovery. The connectors implement Flink's Source and Sink interfaces which handle async data processing natively through Flink's split-based parallelism model. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `KinesisStreamsSource.java`, `DynamoDbStreamsSource.java` — implement Flink's `Source` interface. `KinesisStreamsSinkWriter.java`, `DynamoDbSinkWriter.java` — implement Flink's sink writer interface with async buffered writes. |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The library uses Maven artifact versioning (`6.0-SNAPSHOT`) for release management. Public API stability is managed through Flink annotations: `@PublicEvolving` (API may change between minor versions), `@Experimental` (API may change between patch versions), and `@Public` (stable API). These annotations are applied across 56 source files, providing clear API stability contracts to consumers. However, this is library versioning, not REST API versioning. |
| **Gap** | No formal changelog or migration guide between major versions. API stability annotations exist but consumers must read Javadoc to understand which APIs are stable vs evolving. No automated API compatibility checking in the CI pipeline (e.g., japicmp). |
| **Recommendation** | Add `japicmp-maven-plugin` to the build to automatically detect breaking API changes between versions. Add a CHANGELOG.md or MIGRATION.md for major version transitions. |
| **Evidence** | `pom.xml` — `<version>6.0-SNAPSHOT</version>`. 56 files with `@PublicEvolving`/`@Experimental` annotations. No CHANGELOG.md found. |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | AWS service endpoints are configurable through `AWSConfigConstants` — specifically `AWS_REGION` and `AWS_ENDPOINT` (custom endpoint override). The credential provider supports multiple patterns (`AUTO`, `ENV_VAR`, `SYS_PROP`, `PROFILE`, `ASSUME_ROLE`, `WEB_IDENTITY_TOKEN`, `CUSTOM`). The SDK v2 resolves service endpoints dynamically based on region. Custom endpoint override allows consumers to point connectors at localstack, VPC endpoints, or alternative endpoints. This is appropriate service discovery for a library consuming AWS managed services. |
| **Gap** | No formal service registry or catalog. However, for a library that connects to AWS managed services, the SDK's region-based endpoint resolution IS the service discovery mechanism. |
| **Recommendation** | No action needed. The AWS SDK v2's endpoint resolution mechanism is the appropriate service discovery pattern for connectors targeting AWS managed services. |
| **Evidence** | `AWSConfigConstants.java` — `AWS_REGION`, `AWS_ENDPOINT`. `AWSClientUtil.java` — `updateEndpointOverride()`. `AWSGeneralUtil.java` — `getRegion()`. |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The library does not store unstructured data itself. Documentation files (markdown, YAML) exist in `docs/` directory but are not application data — they are developer documentation. The connectors provide the plumbing for consumers to move data into/out of AWS services (including S3 via Firehose), but the library itself has no S3 bucket definitions, no document parsing pipelines, and no unstructured data management. Test fixtures include SQL files and Avro schemas but these are test resources, not application data. |
| **Gap** | Documentation is stored as markdown files in the repository but not in a managed object storage or content management system. This is standard for open-source projects. |
| **Recommendation** | No action needed for the library. Documentation is appropriately stored in the repository for open-source distribution. |
| **Evidence** | `docs/content/docs/connectors/datastream/` — markdown documentation files. No `aws_s3_bucket` resources. No Textract or parsing library imports. |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The library has a well-structured data access pattern. The base module (`flink-connector-aws-base`) provides a centralized utility layer: `AWSClientUtil` for AWS SDK client creation, `AWSGeneralUtil` for credential management and validation, `AWSConfigConstants` for configuration key definitions. Each connector module follows a consistent pattern: `Sink` (builder → writer → serializer), `Source` (builder → enumerator → reader → split → proxy → metrics), and `Table` (dynamic table factory → options). The `proxy` classes (`KinesisStreamProxy`, `KinesisAsyncStreamProxy`, `DynamoDbStreamsProxy`) provide a clean abstraction over the raw AWS SDK clients. |
| **Gap** | Minor inconsistency: the DynamoDB connector has a separate `client` package (`DynamoDbAsyncClientProvider`, `SdkClientProvider`) while other connectors inline client creation. The SQS connector also has a `client` package. The Kinesis connector does not have this abstraction. |
| **Recommendation** | Consider standardizing the client provider pattern across all connectors to match the DynamoDB/SQS `SdkClientProvider` pattern. This would improve consistency. |
| **Evidence** | `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/util/AWSClientUtil.java` — centralized client creation. `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java` — centralized config. Consistent sink/source/table pattern across all 4 connector modules. |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database engine version pinning exists anywhere in the repository. No IaC files define database resources, so no engine versions are specified. The repo_type is `monorepo` and per the TD's N/A mapping, all 37 questions apply — DATA-Q3 has no surface gate and must be evaluated. The connectors target AWS managed services (DynamoDB, Kinesis, SQS, Firehose) which are serverless/fully managed and do not have user-specified engine versions. However, no database engine definitions or version management exists in IaC or deployment configuration. |
| **Gap** | No database engine version management. While this library does not deploy databases, the absence of any version pinning or engine lifecycle management means Score 1 per the rubric: "No version pinning; engines at or past EOL detected." In this case, there are no engines to pin because no IaC exists. |
| **Recommendation** | No immediate action required for the library itself. If companion infrastructure or test environments are added that include database resources (e.g., DynamoDB Local version in Testcontainers, or RDS for testing), pin engine versions explicitly and track EOL dates. |
| **Evidence** | No IaC files. No database engine version parameters. No `aws_rds_instance`, `aws_docdb_cluster`, or `aws_elasticache_*` resources. No engine version strings in docker-compose or Helm values (none exist). |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL. The SQL files found in the repository are Flink SQL connector examples and test fixtures — not database stored procedures. Examples: `create-table.sql` (Flink SQL DDL for DynamoDB connector table), `datagen.sql` (Flink SQL data generation), `send-orders.sql` (Firehose e2e test), `filter-large-orders.sql` (Kinesis e2e test), `example_dynamodb.sql` (DynamoDB sink example). All SQL is Flink SQL dialect, not T-SQL or PL/SQL. All business logic is in the Java application layer. |
| **Gap** | None — all logic is in the application layer. |
| **Recommendation** | No action needed. |
| **Evidence** | `flink-connector-aws/flink-connector-dynamodb/src/test/resources/create-table.sql`, `datagen.sql` — Flink SQL DDL. `flink-connector-aws-e2e-tests/*/src/test/resources/*.sql` — Flink SQL e2e test queries. `flink-connector-aws/flink-connector-dynamodb/src/test/java/*/examples/*.sql` — Flink SQL examples. |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or audit logging configuration exists. This is a library — audit logging is the responsibility of the consuming application's infrastructure. The library does include SLF4J-based logging (`log4j2.properties` in each module) for operational logging of connector behavior (shard discovery, metric updates, error handling), but this is application-level logging, not audit logging. |
| **Gap** | No audit logging. Expected for a library. |
| **Recommendation** | No action needed for the library itself. Consuming applications should configure CloudTrail for API-level audit logging of the AWS services these connectors interact with. |
| **Evidence** | No `aws_cloudtrail` resources. `log4j2.properties` files in each module provide operational logging. |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no database, S3 bucket, EBS volume, or similar. `has_at_rest_data_surface=false`. SEC-Q2 does not apply. The library interacts with AWS services that have their own encryption-at-rest settings, but those are managed by the consuming application's infrastructure. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No IaC files. No data store definitions. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The library provides comprehensive AWS credential provider support through `AWSConfigConstants.CredentialProvider` enum: `AUTO` (default chain), `ENV_VAR`, `SYS_PROP`, `PROFILE`, `BASIC` (static credentials), `ASSUME_ROLE` (IAM role assumption with STS), `WEB_IDENTITY_TOKEN` (OIDC/Kubernetes service account integration), and `CUSTOM` (user-provided class). This is not REST API authentication but AWS API authentication for service calls. The credential provider chain supports nested role assumption (`roleCredentialsProvider` allows recursive assume-role). The `BASIC` provider with static access keys is supported but documented as one option among many secure alternatives. |
| **Gap** | The `BASIC` credential provider allows hardcoding access keys in configuration, which is a security anti-pattern. While the library must support this for backward compatibility, the default (`AUTO`) uses the secure credential chain. Documentation examples should prioritize `ASSUME_ROLE` and `WEB_IDENTITY_TOKEN` over `BASIC`. |
| **Recommendation** | Add deprecation warnings for `BASIC` credential provider in documentation. Highlight `AUTO`, `ASSUME_ROLE`, and `WEB_IDENTITY_TOKEN` as recommended patterns. Consider adding a runtime warning when `BASIC` provider is used. |
| **Evidence** | `AWSConfigConstants.java` — `CredentialProvider` enum with 8 provider types. `AWSGeneralUtil.java` — `getCredentialsProvider()` implementation with full provider chain. |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The library supports integration with centralized identity providers through `ASSUME_ROLE` (IAM role assumption via STS) and `WEB_IDENTITY_TOKEN` (OIDC web identity — standard for Kubernetes/EKS service accounts using IAM Roles for Service Accounts). The `AUTO` default provider chain also supports instance metadata (EC2/ECS task roles) and environment credentials. These patterns integrate with centralized IAM and federated identity providers. |
| **Gap** | No direct Cognito or Okta integration — but these are irrelevant for a library connecting to AWS service APIs. The relevant identity integration is IAM + OIDC, which is well-supported. |
| **Recommendation** | No action needed. The credential provider chain appropriately supports centralized identity patterns for AWS service authentication. |
| **Evidence** | `AWSConfigConstants.java` — `ASSUME_ROLE`, `WEB_IDENTITY_TOKEN`, `AUTO`. `AWSGeneralUtil.java` — `getAssumeRoleCredentialProvider()`, `getWebIdentityTokenFileCredentialsProvider()`. |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No plaintext credentials found in the repository source code, configuration files, or version-controlled env files. The CI/CD pipeline uses GitHub Secrets (`secrets.FLINK_AWS_USER`, `secrets.FLINK_AWS_PASSWORD`) for AWS e2e test credentials, which is appropriate for CI/CD. However, the library's `BASIC` credential provider pattern accepts access keys via Java Properties, which at runtime could be backed by plaintext configuration. No Secrets Manager or Vault integration exists in the library itself — credential management is delegated to the consuming application through the credential provider pattern. The `AUTO` and `ASSUME_ROLE` providers do not require static secrets. |
| **Gap** | No Secrets Manager integration. The library relies on the consuming application to manage credentials securely. The `BASIC` provider pattern could lead to hardcoded credentials in consumer configurations if misused. |
| **Recommendation** | Document best practices for credential management in the connector documentation. Recommend `AUTO`, `WEB_IDENTITY_TOKEN`, or `ASSUME_ROLE` over `BASIC`. Consider adding an optional Secrets Manager credential provider that retrieves secrets at runtime. |
| **Evidence** | `.github/workflows/common.yml` — `secrets.FLINK_AWS_USER`, `secrets.FLINK_AWS_PASSWORD` (GitHub Secrets, not plaintext). No `.env` files committed. No hardcoded credential patterns found in source scan. |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute resources to harden. No SSM Patch Manager, no AWS Inspector, no hardened AMIs. This is a library with no deployed compute. No Dockerfiles means no container image to scan. The library's dependencies (AWS SDK v2, Netty, Jackson, Guava) are the primary vulnerability surface, but no dependency vulnerability scanning is configured. |
| **Gap** | No vulnerability scanning for the library's dependency tree. The repository has ~50+ transitive dependencies that could contain CVEs. |
| **Recommendation** | While there is no compute to harden, add dependency vulnerability scanning (OWASP `dependency-check-maven` plugin or GitHub Dependabot) to detect CVEs in transitive dependencies. This is the library-equivalent of compute hardening. |
| **Evidence** | No Dockerfiles. No `aws_ssm_patch_baseline`. No AWS Inspector. No `.snyk` or `dependabot.yml` configuration. |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SAST, DAST, or dependency vulnerability scanning tools are integrated into the CI/CD pipeline. The pipeline includes: (1) `apache-rat-plugin` for license header validation, (2) `spotless-maven-plugin` for code formatting, (3) `maven-checkstyle-plugin` for style checks, (4) `maven-enforcer-plugin` for dependency convergence. These are quality tools, not security tools. No Dependabot configuration, no `.snyk` policy, no OWASP dependency check, no SonarQube, no SpotBugs, no Semgrep. |
| **Gap** | Zero security scanning in the pipeline. For a widely-used open-source library with 50+ transitive dependencies (including Netty, Jackson, Guava, AWS SDK), this is a significant gap. Vulnerabilities in these dependencies directly affect all consuming applications. |
| **Recommendation** | **High priority:** Add OWASP `dependency-check-maven` plugin to the Maven build and GitHub Dependabot for automated dependency CVE alerts. Add SpotBugs with `findsecbugs` plugin for SAST. These can be added incrementally without disrupting the existing pipeline. |
| **Evidence** | `.github/workflows/common.yml` — no security scanning steps. `pom.xml` — `apache-rat-plugin`, `spotless-maven-plugin`, `maven-checkstyle-plugin` (quality, not security). No `dependabot.yml` in `.github/`. |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumentation found in the library. No OpenTelemetry SDK, no X-Ray SDK, no trace ID propagation. The connectors interact with AWS services via SDK v2 (which supports X-Ray tracing when configured at the SDK level), but the library itself does not instrument or propagate trace contexts. Searched for "OpenTelemetry", "opentelemetry", "X-Ray", "xray", "tracing" — no matches found. |
| **Gap** | No tracing instrumentation. For a library used in distributed streaming pipelines, trace context propagation would enable end-to-end visibility across Flink jobs and downstream services. |
| **Recommendation** | Consider adding OpenTelemetry trace context propagation to the connector's record metadata. This would allow consuming Flink applications to correlate records flowing through Kinesis/DynamoDB/SQS connectors with upstream and downstream traces. This is a valuable enhancement for observability-aware consumers. |
| **Evidence** | Full source search: 0 matches for OpenTelemetry, X-Ray, or tracing imports. No `opentelemetry-api` or `aws-xray-recorder-sdk` in `pom.xml` dependencies. |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no user-facing surface for which SLOs are meaningful. `has_api_surface=false` and `has_persistent_data_store=false`. The library is consumed by Flink applications which define their own SLOs. OPS-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No SLO definitions. No CloudWatch alarms. No API endpoints. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The connectors expose custom metrics through Flink's metric system. The Kinesis Streams connector publishes `millisBehindLatest` per shard — a business-relevant metric indicating consumer lag. The DynamoDB Streams connector publishes equivalent shard-level metrics. Metrics are organized hierarchically: `KinesisStreamSource` → `accountId` → `region` → `stream` → `shardId` → `millisBehindLatest`. This enables consumers to monitor connector health through Flink's metric exporters (Prometheus, CloudWatch, etc.). |
| **Gap** | Metrics are limited to source connectors. Sink connectors (DynamoDB Sink, Kinesis Streams Sink, Firehose Sink, SQS Sink) do not publish custom metrics beyond Flink's built-in async sink metrics (numRecordsSend, numRecordsSendErrors). Additional business metrics like records-per-second, batch size distribution, or throttling events would improve sink observability. |
| **Recommendation** | Add custom metrics to sink connectors for throttling rate, batch size, and write latency. These complement Flink's built-in async sink metrics and provide connector-specific observability. |
| **Evidence** | `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/metrics/KinesisShardMetrics.java` — `millisBehindLatest` gauge. `MetricConstants.java` — metric group constants. `DynamoDbStreamsShardMetrics.java` — equivalent DynamoDB Streams metrics. |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configuration exists. This is a library — alerting is the responsibility of the consuming application's monitoring infrastructure. The library publishes metrics (see OPS-Q3) but does not configure alarms or anomaly detection on those metrics. |
| **Gap** | No alerting. Expected for a library. |
| **Recommendation** | No action needed for the library. Document recommended CloudWatch alarms for consuming applications (e.g., alarm on `millisBehindLatest` exceeding threshold, alarm on error rate). |
| **Evidence** | No CloudWatch alarms. No PagerDuty/OpsGenie integration. No alerting configuration. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy — this is a library published to Maven Central. There is no deployable service requiring blue/green, canary, or rolling deployment. The library is consumed as a Maven/Gradle dependency by Flink applications, which manage their own deployment strategies. |
| **Gap** | No deployment strategy. Expected for a library. |
| **Recommendation** | No action needed. The Maven Central release process is the "deployment" mechanism for libraries. |
| **Evidence** | No `appspec.yml`, no CodeDeploy configuration, no Helm canary, no Argo Rollouts. Library versioning via Maven (`6.0-SNAPSHOT`). |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Strong integration testing presence. Three levels of testing: (1) **Unit tests** in each connector module (Mockito-based). (2) **Integration tests** using Testcontainers for local testing — `KinesisStreamsSinkITCase`, `DynamoDbSinkITCase`, `DynamoDbDynamicSinkITCase`, `KinesisFirehoseSinkITCase` use local container replicas (Kinesalite, DynamoDB Local). (3) **E2E tests** in `flink-connector-aws-e2e-tests` module — 5 test suites covering Kinesis Streams, Kinesis Firehose, SQS, Avro Glue Schema Registry, and JSON Glue Schema Registry. E2E tests run against local Flink cluster (downloaded binary). AWS-specific e2e tests (with real AWS credentials) run conditionally when `FLINK_AWS_USER` and `FLINK_AWS_PASSWORD` secrets are available. Architecture tests via ArchUnit enforce structural rules. All tests run in the CI pipeline. |
| **Gap** | AWS e2e tests are conditional on credentials and may not run in all CI contexts (e.g., forked PRs from external contributors). Some connector modules may have testing gaps — the SQS e2e test exists but the DynamoDB e2e test module is absent from the e2e test parent. |
| **Recommendation** | Ensure all connectors have e2e test coverage. Consider expanding Testcontainers-based integration tests to reduce reliance on real AWS credentials for CI. |
| **Evidence** | `flink-connector-aws-e2e-tests/pom.xml` — 5 e2e test modules. `.github/workflows/common.yml` — e2e test step, AWS e2e test step (conditional). Testcontainers: `KinesaliteContainer.java`, `DynamoDbContainer.java`, `LocalstackContainer.java`. ArchUnit: `TestCodeArchitectureTest.java` in each module. |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response automation, no runbooks, no SSM Automation documents. This is a library — incident response is the responsibility of the consuming application's operations team. |
| **Gap** | No runbooks. Expected for a library. |
| **Recommendation** | Consider adding troubleshooting guides to the documentation (e.g., common error patterns, throttling recovery, shard rebalancing). These would serve as informal runbooks for consuming teams. |
| **Evidence** | No runbook files. No SSM Automation documents. No Lambda-based remediation. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Partial observability ownership. The `.github/boring-cyborg.yml` configuration provides PR labeling by component (`component=Connectors/DynamoDB`, `component=BuildSystem`, `component=Documentation`), which is a lightweight form of code ownership attribution. No CODEOWNERS file found. No per-service dashboards (expected for a library). No SLO definitions with team attribution. |
| **Gap** | No CODEOWNERS file. The boring-cyborg labels are limited to DynamoDB connector and build system — other connectors (Kinesis, Firehose, SQS) are not labeled. |
| **Recommendation** | Add a CODEOWNERS file mapping each connector module to its maintainers. Expand boring-cyborg labels to cover all connectors (Kinesis, Firehose, SQS, Formats). |
| **Evidence** | `.github/boring-cyborg.yml` — `component=Connectors/DynamoDB`, `component=BuildSystem`, `component=Documentation`. No CODEOWNERS file. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging. This is a library with no AWS resources to tag. No IaC files defining resources, no `default_tags`, no `required-tags` Config rules. |
| **Gap** | No resource tagging. Expected for a library. |
| **Recommendation** | No action needed. Resource tagging is the responsibility of consuming applications' infrastructure. |
| **Evidence** | No IaC files. No `tags` blocks. No AWS resources defined. |

---

## Learning Materials

### Triggered Pathways

**Move to Modern DevOps:**
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `pom.xml` | APP-Q1, APP-Q2, APP-Q5, INF-Q11, SEC-Q7 | Root POM with module definitions, dependency versions (AWS SDK v2 2.40.3, Flink 2.0.0), build plugins |
| `.github/workflows/push_pr.yml` | INF-Q11, OPS-Q6 | CI trigger configuration — push/PR/manual, JDK matrix (11, 17, 21), Python tests |
| `.github/workflows/common.yml` | INF-Q11, OPS-Q6, SEC-Q5, SEC-Q7 | Reusable CI workflow — compile, test, e2e, AWS e2e (conditional), license check |
| `.github/workflows/nightly.yml` | INF-Q11 | Nightly build against Flink 2.0-SNAPSHOT |
| `.github/boring-cyborg.yml` | OPS-Q8 | PR labeling bot — component-based labels (DynamoDB, BuildSystem, Documentation) |
| `README.md` | APP-Q1 | Build prerequisites — Java 11, Maven 3.8.5 |
| `flink-connector-aws-base/src/main/java/.../AWSConfigConstants.java` | SEC-Q3, SEC-Q4, SEC-Q5, APP-Q6 | AWS credential provider enum (8 types), region config, endpoint override |
| `flink-connector-aws-base/src/main/java/.../AWSGeneralUtil.java` | SEC-Q3, SEC-Q4 | Credential provider implementation — full chain including ASSUME_ROLE, WEB_IDENTITY_TOKEN |
| `flink-connector-aws-base/src/main/java/.../AWSClientUtil.java` | APP-Q6, DATA-Q2 | Centralized AWS SDK client creation — async/sync, user agent, endpoint override |
| `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/.../metrics/KinesisShardMetrics.java` | OPS-Q3 | Custom Flink metrics — millisBehindLatest per shard |
| `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/.../metrics/MetricConstants.java` | OPS-Q3 | Metric group and name constants |
| `flink-connector-aws/flink-connector-dynamodb/src/main/java/.../metrics/DynamoDbStreamsShardMetrics.java` | OPS-Q3 | DynamoDB Streams shard-level metrics |
| `flink-connector-aws-e2e-tests/pom.xml` | OPS-Q6 | E2E test parent — 5 test modules, Maven profiles for local and AWS e2e |
| `flink-connector-aws/flink-connector-dynamodb/src/test/resources/create-table.sql` | DATA-Q4 | Flink SQL DDL — test fixture, not stored procedure |
| `flink-connector-aws/flink-connector-dynamodb/src/test/resources/datagen.sql` | DATA-Q4 | Flink SQL data generation — test fixture |
| `flink-connector-aws-e2e-tests/flink-connector-aws-kinesis-firehose-e2e-tests/src/test/resources/send-orders.sql` | DATA-Q4 | Flink SQL e2e test query |
| `flink-connector-aws-e2e-tests/flink-connector-aws-kinesis-streams-e2e-tests/src/test/resources/filter-large-orders.sql` | DATA-Q4 | Flink SQL e2e test query |
| `docs/content/docs/connectors/datastream/kinesis.md` | DATA-Q1, Quick Agent Wins | Kinesis connector documentation (~37KB) |
| `docs/content/docs/connectors/datastream/dynamodb.md` | DATA-Q1, Quick Agent Wins | DynamoDB connector documentation (~18KB) |
| `docs/content/docs/connectors/datastream/firehose.md` | Quick Agent Wins | Firehose connector documentation |
| `docs/content/docs/connectors/datastream/sqs.md` | Quick Agent Wins | SQS connector documentation |
| `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/.../KinesisStreamsSource.java` | APP-Q4, INF-Q3 | Flink Source implementation |
| `flink-connector-aws/flink-connector-dynamodb/src/main/java/.../DynamoDbSink.java` | APP-Q4 | Flink Sink implementation |
| `flink-connector-aws/flink-connector-sqs/src/main/java/.../SqsSink.java` | APP-Q4 | Flink Sink implementation |
| `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/.../proxy/KinesisAsyncStreamProxy.java` | APP-Q3 | Async SDK client wrapper for Kinesis fan-out |
| `flink-python/pom.xml` | APP-Q1 | Python bindings module |
| `tools/maven/checkstyle.xml` | SEC-Q7 | Code style configuration (quality, not security) |
