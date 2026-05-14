# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | flink-connector-aws |
| **Date** | 2026-04-29 |
| **Repo Type** | monorepo |
| **Service Archetype** | N/A — individual modules are connector libraries with no deployable entry points; archetype detection is not meaningful at the monorepo level |
| **Priority** | P2 |
| **Tags** | java, streaming, flink, aws |
| **Context** | Apache Flink connectors for AWS services (Kinesis, DynamoDB, SQS, etc.) |
| **Overall Score** | 2.16 / 4.0 |

**Archetype Justification**: This monorepo contains connector library modules (flink-connector-dynamodb, flink-connector-aws-kinesis-streams, flink-connector-aws-kinesis-firehose, flink-connector-sqs, flink-connector-aws-base, flink-formats-aws, flink-python). None have a `main()` entry point, Dockerfile, or IaC definitions. They are published as Maven artifacts consumed by other applications. While classified as `monorepo` by the user, each module functions as a `library` — this context is critical for interpreting infrastructure and operations scores, many of which reflect the absence of deployable infrastructure rather than modernization gaps.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.18 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 3.83 / 4.0 | ✅ Mature |
| Data Platform Modernization (DATA) | 2.50 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.86 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.44 / 4.0 | ❌ Not Present |
| **Overall** | **2.16 / 4.0** | **🟠 Needs Work** |

> **Important Context**: The low INF and OPS scores reflect the library nature of this monorepo. Connector libraries do not provision infrastructure, deploy services, or define operational runbooks. These scores are structurally expected for a library-type project classified as a monorepo. The APP category — which evaluates code architecture, modularity, and communication patterns — scores at the Mature level, reflecting well-engineered connector libraries.

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC definitions exist in the repository — 0% coverage | No reproducible infrastructure; however, as a library project, IaC is not traditionally required. Build/release automation improvements are the relevant modernization vector. |
| 2 | SEC-Q7: Application Security Pipeline | 2 | No SAST, DAST, or dependency vulnerability scanning (Dependabot, Snyk) in CI/CD pipeline | Vulnerabilities in 60+ transitive dependencies (AWS SDK, Netty, Jackson, Guava) could reach consumers undetected. High-impact for a widely-used open-source library. |
| 3 | SEC-Q5: Secrets Management | 2 | No Secrets Manager or Vault integration; credentials passed via properties/env vars | Library consumers must manage their own secrets; library provides no guidance or integration patterns for managed secret retrieval. |
| 4 | OPS-Q1: Distributed Tracing | 1 | No OpenTelemetry or X-Ray instrumentation in connector libraries | Consuming applications lose trace context when passing through these connectors, breaking end-to-end observability chains. |
| 5 | DATA-Q1: Unstructured Data Storage | 1 | No unstructured data storage or parsing capabilities | Not applicable to connector libraries — connectors transport data, they don't store it. Low priority for this project type. |

---

## Quick Agent Wins

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository — 14 detailed Markdown files across `docs/content/docs/connectors/datastream/` (kinesis.md at 37KB, dynamodb.md at 18KB, firehose.md, sqs.md) and `docs/content/docs/connectors/table/` (kinesis.md, dynamodb.md, firehose.md). README.md provides build instructions.
- **What it enables:** A RAG-based knowledge agent that indexes the connector documentation and answers developer questions about configuration options, deployment patterns, troubleshooting, and usage examples. Could be powered by Amazon Bedrock with the documentation corpus as the knowledge base.
- **Additional steps:** Convert Markdown documentation to a format suitable for embedding (chunking strategy needed for the 37KB kinesis.md file). Set up a vector store (Amazon OpenSearch Service with vector engine) and an embedding pipeline.
- **Effort:** Medium

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 3) — GitHub Actions workflows in `.github/workflows/` with push/PR builds, e2e tests, nightly builds, and licensing checks.
- **What it enables:** A DevOps agent that triggers builds via GitHub Actions API, checks build status, monitors nightly build failures, and assists with release management (Maven Central publishing). Could also monitor test failures and provide root-cause summaries.
- **Additional steps:** GitHub Actions API access needs to be configured for the agent. The agent would need access to GitHub Secrets for AWS credentials used in e2e tests.
- **Effort:** Low

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 4 — modules are well-modularized with clear boundaries. Primary trigger not met. |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 1 but contextual guard prevents trigger: this is a library repo, not EC2/VM-based. Connectors are not running on compute — they are Maven artifacts consumed by other applications. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (no stored procedures), no commercial DB engines detected. Primary trigger not met. |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = 1 but no databases exist to migrate. Connectors connect TO AWS services but don't provision or manage any databases. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 1 but contextual guard prevents trigger: the repo itself does not run data processing workloads. The connectors enable streaming for consuming applications but have no self-use streaming/ETL artifacts. |
| 6 | Move to Modern DevOps | Triggered | Medium | Medium | INF-Q10 = 1 (no IaC — 0% coverage). Supporting: OPS-Q5 = 1 (no deployment strategy), OPS-Q6 = 4 (strong integration testing). While IaC is not traditionally needed for libraries, build automation, release pipeline, and security scanning improvements are relevant. |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. Context is "Apache Flink connectors for AWS services" — contains no AI-related signal terms. |

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current State:**
- **IaC Coverage (INF-Q10 = 1):** No infrastructure-as-code definitions exist. As a library project, this is structurally expected — there are no AWS resources to provision. However, the build and release process could benefit from IaC-like governance: reproducible build environments, release pipeline definitions, and dependency update automation.
- **CI/CD Automation (INF-Q11 = 3):** GitHub Actions workflows provide solid CI with compile, test, e2e test, and licensing check stages. Nightly builds run against Flink SNAPSHOT. However, there is no automated release pipeline to Maven Central, no automated dependency update mechanism, and no security scanning in the pipeline.
- **Deployment Strategy (OPS-Q5 = 1):** Libraries are published to Maven Central but with no staged rollout strategy. A canary release process (publishing to a staging repository before Maven Central) would reduce the risk of publishing broken artifacts.
- **Integration Testing (OPS-Q6 = 4):** Strong foundation — TestContainers-based integration tests with LocalStack and Kinesalite, plus dedicated e2e test module with real AWS service testing when credentials are available.

**Recommendations (contextualized for library project, respecting preferences):**
1. **Add dependency vulnerability scanning** — Integrate Dependabot (`.github/dependabot.yml`) or Snyk to automatically detect vulnerabilities in the 60+ transitive dependencies (AWS SDK v2 2.40.3, Netty 4.1.86, Jackson 2.14.3, Guava 32.1.3). This is the highest-impact DevOps improvement for a widely-consumed open-source library.
2. **Add SAST scanning** — Integrate SonarQube, Semgrep, or CodeGuru Reviewer into the GitHub Actions pipeline to catch code-level security issues before merge.
3. **Automate release pipeline** — Define a release workflow in GitHub Actions that automates Maven Central publishing (GPG signing, staging repository promotion, Nexus release). This reduces manual error risk during releases.
4. **Add build environment reproducibility** — Consider containerized builds or pinned tool versions beyond the current Maven 3.8.6 setup. If containerizing the build, prefer EKS-based runners over self-managed Kubernetes (per preferences).

**Representative AWS Services:** CodeBuild, CodePipeline, ECR (for containerized build environments), CodeGuru Reviewer

**Links:**
- [AWS DevOps prescriptive guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-devops/welcome.html)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute resource definitions found in the repository. No Terraform (`aws_ecs_*`, `aws_eks_*`, `aws_lambda_*`, `aws_instance`), no CloudFormation templates, no CDK stacks. This monorepo contains connector libraries published as Maven artifacts — they do not provision or run on compute infrastructure. They are consumed by other Flink applications that run on managed compute (EKS, EMR, etc.). |
| **Gap** | No compute infrastructure defined. This is structurally expected for a library project — libraries are not deployed as running services. |
| **Recommendation** | No action required for the library modules themselves. Consuming applications should deploy on managed compute (prefer EKS for Flink workloads per preferences). |
| **Evidence** | No `.tf`, `.cfn.yaml`, `cdk.json`, or `Dockerfile` files found in repository. `pom.xml` defines Maven packaging (`pom`, `jar`) with no deployment plugins. |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database resource definitions found. The connectors connect TO DynamoDB, Kinesis Data Streams, and SQS (via AWS SDK v2 clients — `DynamoDbAsyncClient`, `KinesisAsyncClient`, `KinesisClient`, `SqsAsyncClient`, `FirehoseAsyncClient`) but do not provision these services. Database provisioning is the responsibility of consuming applications. |
| **Gap** | No managed database configuration. This is structurally expected — connectors are libraries, not database owners. |
| **Recommendation** | No action required. Consumers deploying these connectors should use managed AWS services (DynamoDB, Kinesis) which are already the target services these connectors interface with. |
| **Evidence** | `AWSClientUtil.java` — creates AWS SDK clients; `DynamoDbStreamsSource.java` — connects to user-provided stream ARN; `KinesisStreamsSource.java` — connects to user-provided stream ARN. |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No workflow orchestration services (Step Functions, MWAA, Temporal, Camunda) found. No multi-step workflow patterns in the connector code. Each connector implements a focused data pipeline pattern (source → deserialize → emit, or receive → serialize → sink) without multi-service coordination. |
| **Gap** | No workflow orchestration. For library connectors, this is expected — connectors are single-purpose components, not workflow orchestrators. |
| **Recommendation** | No action required. Consuming applications that need workflow orchestration for Flink job management should use AWS Step Functions or EventBridge to coordinate pipeline deployments. |
| **Evidence** | No `aws_sfn_*` resources, no Temporal SDK imports. Source code in `DynamoDbStreamsSource.java`, `KinesisStreamsSource.java` implements single-purpose source/sink patterns. |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed messaging or streaming infrastructure definitions found within the repository (no `aws_sqs_*`, `aws_sns_*`, `aws_msk_*`, `aws_kinesis_*` in IaC). The connectors themselves ARE the messaging/streaming integration layer — they provide Flink sources and sinks for Kinesis Data Streams, Kinesis Firehose, DynamoDB Streams, and SQS. However, the repository does not provision these services for its own use. |
| **Gap** | No self-provisioned messaging infrastructure. This is structurally expected for connector libraries that interface with messaging services without owning them. |
| **Recommendation** | No action required for the library itself. The connectors already enable managed messaging/streaming integration for consuming applications. Consumers should use managed services (prefer EventBridge for event routing, avoid self-managed Kafka per preferences). |
| **Evidence** | `KinesisStreamsSink.java` — writes to Kinesis Data Streams via `KinesisAsyncClient`; `SqsSink.java` — writes to SQS via `SqsAsyncClient`; `KinesisFirehoseSink.java` — writes to Firehose via `FirehoseAsyncClient`. All connectors use AWS SDK v2 async clients for managed services. |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or network segmentation definitions found. The library does support endpoint override configuration (`AWSConfigConstants.AWS_ENDPOINT`) and TLS trust configuration (`AWSConfigConstants.TRUST_ALL_CERTIFICATES`), enabling consumers to configure VPC endpoints and private connectivity. |
| **Gap** | No network security configuration defined. Expected for a library project — network security is the responsibility of the deploying application. |
| **Recommendation** | Document best practices for deploying connectors in private subnets with VPC endpoints to DynamoDB, Kinesis, SQS, and Firehose. Consider adding `TRUST_ALL_CERTIFICATES` deprecation warnings (currently defaults to `false`, which is correct). |
| **Evidence** | `AWSConfigConstants.java` — defines `AWS_ENDPOINT` and `TRUST_ALL_CERTIFICATES` configuration keys. `AWSGeneralUtil.java` — `TRUST_ALL_CERTIFICATES` default is `false`. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or AppSync definitions found. Connectors are libraries, not services — they don't expose HTTP endpoints. They provide Flink Source/Sink APIs (Java interfaces) consumed programmatically. |
| **Gap** | No API entry point. Structurally expected for libraries. |
| **Recommendation** | No action required. If consumers need API Gateway integration for Flink job management, that should be built in the consuming application layer (prefer API Gateway per preferences). |
| **Evidence** | No `aws_api_gateway_*`, `aws_lb_*`, or `aws_appsync_*` resources. Source code exposes Java builder APIs: `DynamoDbSink.builder()`, `KinesisStreamsSource.builder()`, `SqsSink.builder()`. |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration found. The connectors do support Flink's built-in parallelism scaling (shard-to-subtask assignment in `KinesisShardAssigner`, `DynamoDbStreamsShardAssigner`) which enables Flink's autoscaling when deployed on managed platforms. |
| **Gap** | No auto-scaling definitions. Expected for libraries — auto-scaling is configured in the deployment platform (Flink on EKS, EMR, etc.). |
| **Recommendation** | No action required. Document recommended autoscaling configurations for Flink jobs using these connectors (e.g., Kubernetes HPA for EKS-based Flink deployments, prefer EKS per preferences). |
| **Evidence** | `DynamoDbStreamsShardAssigner.java`, `KinesisShardAssigner.java` — shard assignment interfaces that enable Flink parallelism scaling. No `aws_autoscaling_*` resources. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup or recovery configuration found. The connectors support Flink checkpointing for exactly-once semantics — `KinesisStreamsSource` and `DynamoDbStreamsSource` implement `Source` interface with checkpoint serialization (`KinesisShardSplitSerializer`, `DynamoDbStreamsShardSplitSerializer`). This enables state recovery through Flink's checkpoint mechanism. |
| **Gap** | No backup configuration defined in the library. State recovery is delegated to Flink's checkpoint mechanism and the consuming application's configuration. |
| **Recommendation** | No action required for the library. Document recommended checkpoint and savepoint configurations for consuming applications. |
| **Evidence** | `KinesisStreamsSource.java` — implements `getEnumeratorCheckpointSerializer()`, `getSplitSerializer()`. `DynamoDbStreamsSource.java` — implements `getEnumeratorCheckpointSerializer()`, `getSplitSerializer()`. |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ or fault isolation configuration found. The connectors are region-aware (extract region from stream ARN via `AWSGeneralUtil.getRegionFromArn()`) but do not define AZ-level fault isolation. High availability is provided by the underlying AWS services (Kinesis, DynamoDB, SQS are inherently multi-AZ) and the Flink runtime. |
| **Gap** | No HA configuration in the library. Expected — HA is handled by AWS managed services and the Flink deployment platform. |
| **Recommendation** | No action required. The target AWS services (DynamoDB, Kinesis, SQS) provide built-in multi-AZ availability. |
| **Evidence** | `AWSGeneralUtil.java` — `getRegionFromArn()` extracts region; no AZ-specific configuration. `DynamoDbStreamsSource.java` — connects to region-level DynamoDB Streams endpoint. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC files found in the repository — no `.tf`, `.tfvars`, `.cfn.yaml`, `.cfn.json`, `cdk.json`, `Chart.yaml`, `kustomization.yaml`, or Ansible playbooks. 0% IaC coverage. The project uses Maven as the build system (`pom.xml`) with declarative dependency and plugin management, which serves an analogous role for library projects. |
| **Gap** | No infrastructure-as-code. For a library project, this is partially expected — there are no AWS resources to provision. However, the build environment, CI/CD pipeline configuration, and release process could benefit from more declarative/reproducible definitions. |
| **Recommendation** | Consider defining build environment specifications declaratively (e.g., GitHub Actions matrix already specifies JDK versions 11/17/21 and Maven 3.8.6). Add Dependabot configuration (`.github/dependabot.yml`) for automated dependency updates — this is the IaC-equivalent governance mechanism for library projects. |
| **Evidence** | No IaC files found. Root `pom.xml` defines Maven build configuration. `.github/workflows/` define CI pipeline but no release automation or infrastructure provisioning. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GitHub Actions CI/CD pipeline is well-structured with multiple stages: (1) Compile and test via `mvn clean install` with convergence checking, (2) E2e tests against local containers, (3) AWS e2e tests with real AWS credentials when available, (4) Licensing check via Apache RAT. Pipeline runs on push, PR, and nightly (against Flink SNAPSHOT). Multi-JDK testing (11, 17, 21) and Python test pipeline. |
| **Gap** | No automated release pipeline to Maven Central. No automated dependency updates (Dependabot/Renovate). No security scanning stage in the pipeline. Deployment (publishing) is likely manual. |
| **Recommendation** | (1) Add automated release workflow for Maven Central publishing. (2) Add Dependabot/Renovate for dependency updates. (3) Add SAST and dependency vulnerability scanning stages to the pipeline. These are the most impactful DevOps improvements for a library project. |
| **Evidence** | `.github/workflows/push_pr.yml` — triggers on push/PR with matrix build; `.github/workflows/common.yml` — reusable workflow with compile, test, e2e, licensing stages; `.github/workflows/nightly.yml` — nightly build against Flink 2.0-SNAPSHOT. |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Primary language is Java (157 main source files, 147 test files) with Python bindings in `flink-python/`. The project targets Java 11 as the minimum with CI testing on JDK 11, 17, and 21. Java has first-class AWS SDK v2 coverage (`software.amazon.awssdk` packages used extensively), mature cloud-native tooling, and the broadest Flink ecosystem support. |
| **Gap** | No gaps. Java is the optimal language choice for Flink connectors with comprehensive AWS SDK support. |
| **Recommendation** | Continue with Java. Consider adding Java 21 as the primary build target as the Flink ecosystem migrates forward. |
| **Evidence** | `pom.xml` — `flink.version=2.0.0`, `aws.sdkv2.version=2.40.3`. `.github/workflows/push_pr.yml` — `java: '11, 17, 21'`. 157 Java source files across 7 modules. |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The repository is a well-modularized multi-module Maven project with clear module boundaries: `flink-connector-aws-base` (shared AWS client utilities), `flink-connector-dynamodb` (DynamoDB sink/source), `flink-connector-aws-kinesis-streams` (Kinesis source/sink), `flink-connector-aws-kinesis-firehose` (Firehose sink), `flink-connector-sqs` (SQS sink), `flink-formats-aws` (Glue Schema Registry formats), `flink-python` (Python bindings). Each connector is independently consumable. Dependencies flow one direction: connectors depend on base, not on each other. ArchUnit tests enforce architectural rules. |
| **Gap** | No gaps. Module boundaries are well-defined with no circular dependencies. |
| **Recommendation** | Maintain the current modular architecture. The separation of base utilities from individual connectors enables independent evolution and versioning. |
| **Evidence** | Root `pom.xml` — `<modules>` lists 5 top-level modules. Each connector has its own `pom.xml` with dependency on `flink-connector-aws-base`. ArchUnit tests (`.archunit.properties` in each module) enforce architecture rules. |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Connectors implement comprehensive async communication patterns using AWS SDK v2 async clients. Sinks use `DynamoDbAsyncClient`, `KinesisAsyncClient` (via `KinesisAsyncStreamProxy`), `FirehoseAsyncClient`, and `SqsAsyncClient` for non-blocking writes. Sources use both sync and async patterns: `DynamoDbStreamsSource` uses `DynamoDbStreamsClient` (sync) for polling with configurable idle times between polls, while `KinesisStreamsSource` supports both polling (sync `KinesisClient`) and Enhanced Fan-Out (async `KinesisAsyncClient` via `FanOutKinesisShardSplitReader`). All sinks extend `AsyncSinkBase` which provides the async buffering protocol. |
| **Gap** | No gaps. The async/sync balance is appropriate — sinks are fully async, sources use the appropriate pattern for their protocol (polling vs streaming). |
| **Recommendation** | No action required. The current design correctly uses async for high-throughput sinks and supports both polling and streaming (EFO) for sources. |
| **Evidence** | `DynamoDbSink.java` — extends `AsyncSinkBase`, uses `DynamoDbAsyncClient`. `KinesisStreamsSink.java` — extends `AsyncSinkBase`. `SqsSink.java` — extends `AsyncSinkBase`, uses `SqsAsyncClient`. `KinesisStreamsSource.java` — supports POLLING (sync) and EFO (async) reader types. `FanOutKinesisShardSplitReader.java` — async streaming reader. |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Connectors handle long-running streaming operations natively through Flink's source/sink framework. Sources implement continuous unbounded streaming (`Boundedness.CONTINUOUS_UNBOUNDED`) with split-based reading and Flink checkpoint support. `KinesisStreamsSource` uses shard split readers with configurable polling intervals and exponential backoff retry strategies. `DynamoDbStreamsSource` uses polling with configurable idle times between empty and non-empty polls. All operations are checkpoint-recoverable — no blocking synchronous calls for stream reading. |
| **Gap** | No gaps. Long-running stream processing is the core use case, and it's implemented with proper async patterns, checkpointing, and retry strategies. |
| **Recommendation** | No action required. The current design with Flink's checkpoint mechanism, exponential backoff strategies, and configurable polling intervals is well-suited for continuous streaming. |
| **Evidence** | `KinesisStreamsSource.java` — `getBoundedness()` returns `CONTINUOUS_UNBOUNDED`; uses `StandardRetryStrategy` with exponential backoff. `DynamoDbStreamsSource.java` — configurable `DYNAMODB_STREAMS_GET_RECORDS_IDLE_TIME_BETWEEN_EMPTY_POLLS` and `DYNAMODB_STREAMS_GET_RECORDS_IDLE_TIME_BETWEEN_NON_EMPTY_POLLS`. |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The project uses Maven-based semantic versioning (currently `6.0-SNAPSHOT`, implying version 6.0 release). The Flink API stability annotations (`@PublicEvolving`, `@Experimental`, `@Internal`) provide API contract guarantees: `@PublicEvolving` APIs may change between minor versions, `@Internal` APIs are not part of the public contract, and `@Experimental` APIs may change at any time. This is a mature API versioning system for library projects. However, no changelog or API migration guide was found. |
| **Gap** | No formal changelog file or API migration guide documenting breaking changes between versions. The annotation-based system provides compile-time contract signals but no runtime versioning. |
| **Recommendation** | Add a CHANGELOG.md documenting breaking changes per version. Consider generating API compatibility reports (e.g., using japicmp Maven plugin) in CI to detect accidental API breaks. |
| **Evidence** | `pom.xml` — `<version>6.0-SNAPSHOT</version>`. `AWSConfigConstants.java` — `@PublicEvolving`. `DynamoDbSink.java` — `@PublicEvolving`. `DynamoDbStreamsSource.java` — `@Experimental`. `AWSClientUtil.java` — `@Internal`. |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Connectors use Flink's Table Factory service discovery via Java SPI (`META-INF/services/org.apache.flink.table.factories.Factory`). Each connector registers its table factory implementation: DynamoDB registers `DynamoDbDynamicSinkFactory`/`DynamoDbDynamicTableFactory`, Kinesis Streams registers `KinesisDynamicTableFactory`, Firehose registers `KinesisFirehoseDynamicTableFactory`, SQS registers `SqsDynamicTableFactory`. No hard-coded service endpoints — all AWS endpoints are configurable via `AWSConfigConstants.AWS_ENDPOINT` and `AWSConfigConstants.AWS_REGION`. |
| **Gap** | No gaps. SPI-based discovery is the standard pattern for Flink connectors, and all AWS endpoints are fully configurable. |
| **Recommendation** | No action required. The SPI-based discovery and configurable endpoint pattern is the correct approach for Flink connector libraries. |
| **Evidence** | `flink-connector-dynamodb/src/main/resources/META-INF/services/org.apache.flink.table.factories.Factory`, `flink-connector-aws-kinesis-streams/src/main/resources/META-INF/services/org.apache.flink.table.factories.Factory`, `flink-connector-sqs/src/main/resources/META-INF/services/org.apache.flink.table.factories.Factory`, `flink-connector-aws-kinesis-firehose/src/main/resources/META-INF/services/org.apache.flink.table.factories.Factory`. `AWSConfigConstants.java` — `AWS_ENDPOINT`, `AWS_REGION` configuration keys. |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No unstructured data storage or parsing capabilities found. The connectors transport structured streaming data (DynamoDB records, Kinesis records, SQS messages) — they do not store unstructured documents. No S3 bucket definitions, no Textract integration, no document parsing libraries. |
| **Gap** | No unstructured data storage. This is not applicable to connector libraries — connectors transport data, they don't store it. |
| **Recommendation** | No action required. If a Flink S3 connector is needed, it exists in a separate Flink connector repository. |
| **Evidence** | No `aws_s3_bucket` resources, no Textract SDK imports, no document parsing libraries in `pom.xml`. |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Each connector implements a well-structured data access layer with clear separation of concerns. The base module (`flink-connector-aws-base`) provides shared utilities: `AWSClientUtil` for AWS SDK client creation (both sync and async), `AWSGeneralUtil` for credential provider management, region handling, and HTTP client configuration. Each connector has its own proxy/client layer: `DynamoDbStreamsProxy` (implements `StreamProxy` interface), `KinesisStreamProxy`, `KinesisAsyncStreamProxy`, `DynamoDbAsyncClientProvider`, `SqsAsyncClientProvider`. Data access is centralized per connector with consistent patterns across all modules. |
| **Gap** | No gaps. Data access is centralized through proxy/client provider abstractions with consistent patterns. |
| **Recommendation** | Maintain the current pattern. Consider extracting common async client provider patterns into the base module if SQS and DynamoDB providers diverge. |
| **Evidence** | `AWSClientUtil.java` — centralized AWS client creation. `AWSGeneralUtil.java` — centralized credential and HTTP client management. `DynamoDbStreamsProxy.java`, `KinesisStreamProxy.java`, `KinesisAsyncStreamProxy.java` — per-connector proxy implementations. `SqsAsyncClientProvider.java`, `DynamoDbAsyncClientProvider.java` — client provider pattern. |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database engine definitions or version pins found. The connectors interface with AWS managed services (DynamoDB, Kinesis, SQS) which don't have user-managed engine versions. The AWS SDK version is pinned (`aws.sdkv2.version=2.40.3`), which is the relevant version dependency for these connectors. |
| **Gap** | No database engine version management. Not applicable — the target services are fully managed AWS services without user-facing engine versions. |
| **Recommendation** | No action required for database engine versions. Continue pinning the AWS SDK version and keep it current. The current version (2.40.3) is recent. |
| **Evidence** | `pom.xml` — `<aws.sdkv2.version>2.40.3</aws.sdkv2.version>`. No database engine version parameters found. |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs. All connector logic is in the Java application layer. The connectors use AWS SDK API calls (BatchWriteItem for DynamoDB, PutRecords for Kinesis, SendMessageBatch for SQS) — no SQL of any kind. Business logic (serialization, buffering, retry, checkpointing) resides entirely in the connector code. |
| **Gap** | No gaps. All logic is in the application layer with no database coupling. |
| **Recommendation** | No action required. |
| **Evidence** | `DynamoDbSinkWriter.java` — uses BatchWriteItem via SDK. `KinesisStreamsSink.java` — uses PutRecords via SDK. `SqsSinkWriter.java` — uses SendMessageBatch via SDK. No `.sql` files in repository. |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or audit logging configuration. The connectors use SLF4J logging (`LoggerFactory.getLogger()`) for operational logging (debug-level metric updates, error-level exception handling) but do not configure or enable AWS audit logging. Audit logging is the responsibility of the consuming application and the AWS account where the services run. |
| **Gap** | No audit logging. Expected for a library — CloudTrail configuration is at the AWS account level, not the library level. |
| **Recommendation** | No action required for the library. Document that consuming applications should enable CloudTrail for DynamoDB, Kinesis, and SQS API call auditing. |
| **Evidence** | `DynamoDbStreamsShardMetrics.java` — uses `LoggerFactory.getLogger()`. No `aws_cloudtrail` resources. |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No KMS or encryption configuration in the library. The target AWS services (DynamoDB, Kinesis, SQS) support encryption at rest natively — DynamoDB uses AWS-managed or CMK encryption, Kinesis supports KMS encryption, SQS supports SSE. The connectors delegate encryption entirely to the underlying services. |
| **Gap** | No encryption configuration. Expected for a library — encryption is configured on the service, not in the connector library. |
| **Recommendation** | No action required. Document that consumers should enable encryption on their DynamoDB tables (SSE with KMS), Kinesis streams (KMS encryption), and SQS queues (SSE). |
| **Evidence** | No `kms_key_id` references, no `aws_kms_key` resources. Connectors pass through data without handling encryption themselves. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive AWS authentication support through 8 credential provider types defined in `AWSConfigConstants.CredentialProvider`: AUTO (default credential chain), BASIC (access key/secret key), ENV_VAR (environment variables), SYS_PROP (Java system properties), PROFILE (AWS profile), ASSUME_ROLE (STS role assumption), WEB_IDENTITY_TOKEN (OIDC/Kubernetes), CUSTOM (user-provided class). The `AWSGeneralUtil.getCredentialsProvider()` method implements all 8 types with proper validation. STS integration supports nested role assumption and configurable STS endpoints. |
| **Gap** | Authentication is robust but BASIC credential provider type allows plaintext access key/secret key in configuration properties, which is a security risk if configuration is stored in version control. No explicit warning or deprecation of BASIC type. |
| **Recommendation** | Add deprecation warning for BASIC credential provider type in documentation. Recommend AUTO, ASSUME_ROLE, or WEB_IDENTITY_TOKEN as preferred options. Consider adding Secrets Manager credential provider type for integration with AWS Secrets Manager. |
| **Evidence** | `AWSConfigConstants.java` — defines `CredentialProvider` enum with 8 types. `AWSGeneralUtil.java` — `getCredentialsProvider()` implements all 8 types including STS `AssumeRoleRequest` and `WebIdentityTokenFileCredentialsProvider`. |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Connectors integrate with AWS IAM through the credential provider chain. The WEB_IDENTITY_TOKEN provider type enables OIDC federation (used in EKS with IRSA), and ASSUME_ROLE supports STS-based role assumption with external ID. The AUTO provider type uses the default credential chain which includes ECS task roles, EC2 instance roles, and SSO credentials. This is centralized identity through AWS IAM. |
| **Gap** | No explicit SAML or SSO configuration support. The library relies on AWS SDK's built-in credential chain for identity federation rather than providing additional centralized identity abstractions. |
| **Recommendation** | No action required. The WEB_IDENTITY_TOKEN and AUTO credential providers already support modern identity federation patterns (IRSA on EKS, ECS task roles). |
| **Evidence** | `AWSConfigConstants.java` — `WEB_IDENTITY_TOKEN`, `ASSUME_ROLE` credential types. `AWSGeneralUtil.java` — `getWebIdentityTokenFileCredentialsProvider()` and `getAssumeRoleCredentialProvider()` implementations. `AWSConfigOptions.java` — `AWS_WEB_IDENTITY_TOKEN_FILE`, `AWS_ROLE_ARN_OPTION`. |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No explicit integration with AWS Secrets Manager, HashiCorp Vault, or Parameter Store. Credentials are managed through the AWS SDK credential provider chain — they can come from environment variables, system properties, instance profiles, OIDC tokens, or configuration properties. The BASIC credential type accepts plaintext access key/secret key in properties, but the AUTO type (default chain) and WEB_IDENTITY_TOKEN type avoid hardcoded credentials entirely. No secrets are hardcoded in the source code. |
| **Gap** | No Secrets Manager integration for retrieving database credentials, API keys, or other secrets needed by consuming applications. The BASIC credential type enables plaintext credential injection without rotation. |
| **Recommendation** | Consider adding a Secrets Manager credential provider type (e.g., `SECRETS_MANAGER`) that retrieves AWS credentials from Secrets Manager with automatic rotation support. This would enable consumers to avoid passing credentials through configuration properties. |
| **Evidence** | `AWSConfigConstants.java` — BASIC type accepts `accessKeyId` and `secretKey` as configuration properties. No `aws_secretsmanager_*` SDK imports, no Vault client imports. No hardcoded secrets found in source code. |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute hardening or patching configuration. This is a library project — there are no EC2 instances, containers, or AMIs to harden. The library's own "patching" is handled through dependency updates in Maven. |
| **Gap** | No compute hardening. Not applicable for a library project. |
| **Recommendation** | No action required for compute hardening. Add automated dependency update scanning (Dependabot/Renovate) to keep the library's dependencies patched against known vulnerabilities. |
| **Evidence** | No `aws_ssm_patch_baseline`, no AMI references, no Inspector configuration. `pom.xml` defines dependency versions but no automated vulnerability scanning. |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | CI/CD includes code quality tools: Checkstyle (code style enforcement), Spotless (code formatting), ArchUnit (architecture rule enforcement), Apache RAT (license header checking). These are valuable but are NOT security tools. No SAST (SonarQube, Semgrep, CodeGuru Reviewer), no DAST, no dependency vulnerability scanning (Dependabot, Snyk, OWASP Dependency-Check), and no container scanning. |
| **Gap** | No SAST or dependency vulnerability scanning in CI/CD. For a widely-used open-source library with 60+ transitive dependencies (including AWS SDK v2, Netty, Jackson, Guava, protobuf), this is a significant gap — vulnerabilities in transitive dependencies could propagate to all consuming applications. |
| **Recommendation** | (1) Add Dependabot (`.github/dependabot.yml`) for automated dependency vulnerability alerts and PRs. (2) Add OWASP Dependency-Check or Snyk to the Maven build (`mvn org.owasp:dependency-check-maven:check`). (3) Consider adding CodeGuru Reviewer for Java-specific security analysis. These are high-priority improvements given the library's wide distribution. |
| **Evidence** | `pom.xml` — `apache-rat-plugin`, `maven-checkstyle-plugin`, `spotless-maven-plugin`. `.github/workflows/common.yml` — licensing check step but no security scan step. No `.github/dependabot.yml`, no `.snyk` file. |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumentation found. No OpenTelemetry SDK, no X-Ray SDK, no `traceparent` or `X-Amzn-Trace-Id` header propagation. The connectors expose Flink metrics (gauge-based `millisBehindLatest`) but do not propagate trace context across the source-to-sink boundary. |
| **Gap** | No trace context propagation. When consuming applications use distributed tracing, trace context is lost at the Flink connector boundary. This breaks end-to-end observability chains. |
| **Recommendation** | Consider adding OpenTelemetry trace context propagation to connector sources and sinks. Kinesis records support user-defined attributes that could carry `traceparent` headers. This would enable consuming applications to maintain trace continuity through Flink jobs. |
| **Evidence** | No `opentelemetry` or `xray` dependencies in `pom.xml`. `KinesisShardMetrics.java`, `DynamoDbStreamsShardMetrics.java` — expose Flink gauge metrics but no tracing. |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found. Libraries don't typically define SLOs — SLOs are defined by the consuming application's service level. The connector does provide `millisBehindLatest` metrics that consuming applications can use to define SLOs on stream processing lag. |
| **Gap** | No SLOs. Expected for a library project. |
| **Recommendation** | Document recommended SLO configurations for consuming applications using these connectors (e.g., `millisBehindLatest < 60000` for near-real-time processing). |
| **Evidence** | `KinesisShardMetrics.java` — exposes `millisBehindLatest` gauge. `DynamoDbStreamsShardMetrics.java` — exposes `millisBehindLatest` gauge. No SLO definition files. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Connectors publish custom Flink metrics through the Flink MetricGroup system. `KinesisShardMetrics` and `DynamoDbStreamsShardMetrics` publish `millisBehindLatest` gauges with hierarchical metric groups (source → account → region → stream → shard). These are operational/infrastructure metrics relevant to stream processing lag, not business outcome metrics. However, for a connector library, infrastructure metrics ARE the appropriate metric type. |
| **Gap** | Metrics are limited to `millisBehindLatest`. No throughput metrics (records/second, bytes/second), no error rate metrics, no retry count metrics exposed through the Flink metric system. |
| **Recommendation** | Add additional connector-level metrics: records processed per second, batch write success/failure counts, retry rates, and backpressure indicators. These would provide consuming applications with richer observability. |
| **Evidence** | `KinesisShardMetrics.java` — `MILLIS_BEHIND_LATEST` gauge. `DynamoDbStreamsShardMetrics.java` — `MILLIS_BEHIND_LATEST` gauge. `MetricConstants.java` (Kinesis/DynamoDB) — defines metric group names. |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configuration. Expected for a library — alerting is configured in the consuming application's monitoring stack. The `millisBehindLatest` metrics can be used for anomaly detection by consuming applications. |
| **Gap** | No alerting. Expected for a library project. |
| **Recommendation** | Document recommended CloudWatch alarm configurations for consuming applications (e.g., anomaly detection on `millisBehindLatest`, static thresholds on error rates). |
| **Evidence** | No CloudWatch alarm definitions, no PagerDuty/OpsGenie integration. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy defined. Libraries are published to Maven Central as artifacts, not deployed as running services. The CI pipeline handles build and test but not publishing/release. No staged rollout, blue/green, or canary deployment for library releases. |
| **Gap** | No deployment strategy. For libraries, the equivalent is a staged release process (staging repository → release). |
| **Recommendation** | Implement a staged Maven Central release pipeline: publish to Sonatype staging repository, run post-publish validation, then promote to Maven Central. This provides a "canary" equivalent for library releases. |
| **Evidence** | `.github/workflows/common.yml` — `MVN_VALIDATION_DIR` is a local file repository, not a remote staging repository. No release workflow found. |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Comprehensive integration testing infrastructure: (1) TestContainers-based tests using `LocalstackContainer` for AWS service emulation, `KinesaliteContainer` for Kinesis emulation, `DynamoDbContainer` for DynamoDB. (2) Dedicated e2e test module (`flink-connector-aws-e2e-tests`) with tests for Kinesis Streams, Kinesis Firehose, SQS, and Glue Schema Registry. (3) Real AWS integration tests when credentials are available (`FLINK_AWS_USER`/`FLINK_AWS_PASSWORD` secrets). (4) ArchUnit architecture tests enforcing module boundaries. (5) Tests run in CI on every push/PR and nightly. |
| **Gap** | No gaps. Integration testing is thorough with both local (container-based) and real AWS testing. |
| **Recommendation** | No action required. The testing strategy is mature and comprehensive. |
| **Evidence** | `flink-connector-aws-e2e-tests/README.md` — documents e2e test setup. `.github/workflows/common.yml` — e2e test stage, AWS e2e test stage (conditional on credentials). ITCase files: `DynamoDbSinkITCase.java`, `KinesisStreamsSourceITCase.java`, `KinesisStreamsSinkITCase.java`, `KinesisFirehoseSinkITCase.java`. |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response runbooks or automation found. Expected for a library project — incident response is handled by the consuming application's operations team. |
| **Gap** | No runbooks. Expected for libraries. |
| **Recommendation** | Consider adding troubleshooting guides in the documentation for common connector issues (connection timeouts, throttling, shard split handling, checkpoint failures). |
| **Evidence** | No runbook files (markdown, YAML, JSON), no Systems Manager documents, no Lambda-based remediation. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CODEOWNERS file, no observability ownership definitions, no per-service dashboards. The Apache Flink project uses JIRA for issue tracking and mailing lists for communication, but no formal observability ownership is defined in the repository. |
| **Gap** | No observability ownership. Partially expected for an open-source library project where ownership is community-based rather than team-based. |
| **Recommendation** | Consider adding a CODEOWNERS file mapping module directories to committer groups for code review accountability. |
| **Evidence** | No `.github/CODEOWNERS` file. `.asf.yaml` defines notification channels (commits, issues, PRs) but not ownership. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging configuration. The library does not provision AWS resources, so there are no resources to tag. The connector does set a user agent prefix (`AWSClientUtil.formatFlinkUserAgentPrefix()`) which provides attribution in AWS API call logs — this is the library-equivalent of resource tagging. |
| **Gap** | No resource tagging. Not applicable for a library project. |
| **Recommendation** | No action required. The user agent prefix provides API call attribution. Consumers should apply resource tags to their own DynamoDB tables, Kinesis streams, and SQS queues. |
| **Evidence** | `AWSClientUtil.java` — `formatFlinkUserAgentPrefix()` sets `SdkAdvancedClientOption.USER_AGENT_PREFIX`. No `tags` configuration in any resource definitions. |

---

## Learning Materials

The following learning resources are mapped to the triggered pathway:

### Move to Modern DevOps
- [Move to Modern DevOps — AWS SkillBuilder Learning Plan](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

No other pathways were triggered — no additional pathway-specific learning materials apply.

**General Resources:**
- [AWS SkillBuilder](https://skillbuilder.aws/) — Comprehensive cloud architecture training catalog
- [Apache Flink Documentation](https://nightlies.apache.org/flink/flink-docs-stable/) — Flink-specific development resources

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `pom.xml` | INF-Q10, INF-Q11, APP-Q1, APP-Q2, SEC-Q7, DATA-Q3 | Root Maven POM defining module structure, dependency versions, build plugins |
| `.github/workflows/push_pr.yml` | INF-Q11, OPS-Q6 | CI pipeline trigger configuration, JDK matrix (11, 17, 21) |
| `.github/workflows/common.yml` | INF-Q11, OPS-Q5, OPS-Q6, SEC-Q7 | Reusable CI workflow with compile, test, e2e, licensing stages |
| `.github/workflows/nightly.yml` | INF-Q11 | Nightly build against Flink 2.0-SNAPSHOT |
| `flink-connector-aws-base/src/main/java/.../AWSConfigConstants.java` | SEC-Q3, SEC-Q4, SEC-Q5, INF-Q5, APP-Q6 | AWS credential provider types (8 types), endpoint configuration, HTTP settings |
| `flink-connector-aws-base/src/main/java/.../AWSConfigOptions.java` | SEC-Q3, SEC-Q4 | Flink ConfigOption definitions for AWS configuration |
| `flink-connector-aws-base/src/main/java/.../AWSClientUtil.java` | INF-Q2, DATA-Q2, OPS-Q9 | AWS SDK client creation (sync and async), user agent configuration |
| `flink-connector-aws-base/src/main/java/.../AWSGeneralUtil.java` | SEC-Q3, SEC-Q4, SEC-Q5, INF-Q5, DATA-Q2 | Credential provider implementation (8 types), HTTP client configuration, region handling |
| `flink-connector-aws/flink-connector-dynamodb/src/main/java/.../DynamoDbSink.java` | APP-Q3, DATA-Q4 | DynamoDB async sink extending AsyncSinkBase |
| `flink-connector-aws/flink-connector-dynamodb/src/main/java/.../DynamoDbStreamsSource.java` | APP-Q4, INF-Q8, INF-Q9 | DynamoDB Streams source with checkpoint support, polling with configurable intervals |
| `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/.../KinesisStreamsSource.java` | APP-Q3, APP-Q4, INF-Q8 | Kinesis source with POLLING and EFO reader types, retry strategies |
| `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/.../KinesisStreamsSink.java` | APP-Q3, INF-Q4 | Kinesis async sink |
| `flink-connector-aws/flink-connector-aws-kinesis-firehose/src/main/java/.../KinesisFirehoseSink.java` | APP-Q3, INF-Q4 | Firehose async sink |
| `flink-connector-aws/flink-connector-sqs/src/main/java/.../SqsSink.java` | APP-Q3, INF-Q4 | SQS async sink extending AsyncSinkBase |
| `flink-connector-aws/flink-connector-dynamodb/src/main/java/.../DynamoDbStreamsShardMetrics.java` | OPS-Q1, OPS-Q2, OPS-Q3 | Flink gauge metrics for millisBehindLatest |
| `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/.../KinesisShardMetrics.java` | OPS-Q1, OPS-Q2, OPS-Q3 | Flink gauge metrics for millisBehindLatest |
| `flink-connector-aws/flink-connector-dynamodb/src/main/resources/META-INF/services/org.apache.flink.table.factories.Factory` | APP-Q6 | SPI service discovery for DynamoDB Table Factory |
| `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/resources/META-INF/services/org.apache.flink.table.factories.Factory` | APP-Q6 | SPI service discovery for Kinesis Table Factory |
| `flink-connector-aws/flink-connector-sqs/src/main/resources/META-INF/services/org.apache.flink.table.factories.Factory` | APP-Q6 | SPI service discovery for SQS Table Factory |
| `flink-connector-aws/flink-connector-aws-kinesis-firehose/src/main/resources/META-INF/services/org.apache.flink.table.factories.Factory` | APP-Q6 | SPI service discovery for Firehose Table Factory |
| `flink-connector-aws-e2e-tests/README.md` | OPS-Q6 | E2e test documentation and setup instructions |
| `flink-connector-aws/flink-connector-dynamodb/src/test/.../DynamoDbSinkITCase.java` | OPS-Q6 | DynamoDB sink integration test |
| `flink-connector-aws/flink-connector-aws-kinesis-streams/src/test/.../KinesisStreamsSourceITCase.java` | OPS-Q6 | Kinesis source integration test |
| `docs/content/docs/connectors/datastream/kinesis.md` | Quick Agent Wins | Kinesis connector documentation (37KB, 586 lines) |
| `docs/content/docs/connectors/datastream/dynamodb.md` | Quick Agent Wins | DynamoDB connector documentation (18KB, 312 lines) |
| `docs/content/docs/connectors/datastream/firehose.md` | Quick Agent Wins | Firehose connector documentation |
| `docs/content/docs/connectors/datastream/sqs.md` | Quick Agent Wins | SQS connector documentation |
| `.asf.yaml` | OPS-Q8 | Apache Software Foundation configuration, notification channels |
| `README.md` | Quick Agent Wins | Build instructions, project overview |
