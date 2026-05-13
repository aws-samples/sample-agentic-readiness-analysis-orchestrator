# Agentic Readiness Assessment Report

**Target**: apache--flink-connector-aws
**Date**: 2026-05-07
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**TD Version**: agentic-readiness-assessment
**Repository Type**: monorepo
**Service Archetype**: stateless-utility (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, streaming, flink, aws
**Context**: Apache Flink connectors for AWS services (Kinesis, DynamoDB, SQS, etc.)

**Archetype Justification**: All modules in this monorepo are connector libraries (no deployable entry points, no persistent data stores, no HTTP/RPC surface, no authentication enforcement). They are consumed by downstream Flink applications and do not own operational infrastructure.

**Surface flags**:
- has_persistent_data_store: false
- has_http_rpc_surface: false
- has_auth_surface: false
- has_write_operations: false
- has_logging_of_user_data: false

**Dev-library-application override applied**: This monorepo contains exclusively library modules (Flink connectors). All modules export Java/Python APIs without owning deployable services, API surfaces, data stores, or infrastructure. The `library` N/A mapping from Step 1 is applied (ENG-Q1 through ENG-Q5 are N/A). Surface-flag downgrades further reduce applicable questions. The original `repo_type` value (`monorepo`) is preserved above.

---

## Readiness Profile: Agent-Ready

**BLOCKERs**: 0 | **RISK-SAFETY**: 0 | **RISK-QUALITY**: 3 | **INFOs**: 23

This repo has 0 High findings, 3 Medium findings, and 0 of the Mediums are safety-impact. 0 High findings with ≤1 safety-impact Medium → Agent-Ready.

The V6 classification maps as follows: 0 High, 3 Medium (all RISK-QUALITY, none safety-impact) → Agent-Ready. The V5 Readiness Profile and V6 Classification are aligned: both yield Agent-Ready because there are no BLOCKERs and no RISK-SAFETY findings.

Cleared for autonomous operation. Instrument observability. Define scope explicitly. Run controlled pilot first.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK-SAFETY | 0 |
| RISK-QUALITY | 3 |
| INFO | 23 |
| N/A | 5 |
| Not Evaluated (extended) | 12 |
| **Total** | **43** |

**Core Questions Evaluated**: 19 (24 core minus 5 N/A from library repo_type)
**Extended Questions Triggered**: 4
**Extended Questions Not Triggered**: 12
**Questions N/A (repo_type: library via dev-library-application override)**: 5
**Service Archetype**: stateless-utility (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

No BLOCKERs identified.

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

No RISK-SAFETY findings identified.

### RISK-QUALITY — Address as Capacity Allows

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The repository uses semantic versioning (currently v6.0-SNAPSHOT targeting Flink 2.0.0) and maintains comprehensive documentation of connector APIs in `docs/content/docs/connectors/`. However, there is no automated breaking-change detection in CI (no `buf breaking`, no OpenAPI diff, no consumer-driven contract tests like Pact). The CI pipeline validates compilation and tests but does not detect API-breaking changes to the public connector interfaces (builders, configuration options, serialization schemas) before merge.
- **Gap**: No automated API contract testing or breaking-change detection tooling in the CI pipeline. Public API surface changes could break downstream Flink applications without early detection.
- **Compensating Controls**:
  - ArchUnit architecture tests (`TestCodeArchitectureTest.java` in each module) enforce some structural rules
  - Maven shade plugin with relocation prevents classpath conflicts
  - Flink connector parent POM enforces dependency convergence
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add API compatibility checking via tools like `japicmp-maven-plugin` or `revapi-maven-plugin` to the CI pipeline. Configure to fail builds on binary-incompatible changes to public API classes.
- **Evidence**: `.github/workflows/common.yml`, `pom.xml`, `flink-connector-aws/flink-connector-aws-kinesis-streams/src/test/java/org/apache/flink/connector/kinesis/source/TestCodeArchitectureTest.java`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The library uses SLF4J throughout with plain-text PatternLayout logging (`%d{HH:mm:ss,SSS} %-5p %-60c %x - %m%n`). Root logger is set to OFF in production JARs (correct for a library). No structured JSON logging, no MDC/NDC context enrichment, and no OpenTelemetry/X-Ray instrumentation hooks are provided. The library does not propagate or enrich trace context.
- **Gap**: No structured logging support and no distributed tracing hooks. Consuming applications that integrate these connectors cannot correlate connector-internal log events with their own trace context without additional instrumentation work.
- **Compensating Controls**:
  - SLF4J abstraction allows consuming applications to configure any logging backend (including JSON formatters)
  - Flink's built-in metrics system is used for operational visibility (MetricListener in tests confirms metric emission)
- **Remediation Timeline**: 90–120 days
- **Recommendation**: Consider adding MDC context propagation for trace IDs in key connector operations (source reads, sink writes). This would allow consuming Flink applications to correlate connector activity with their distributed traces without modifying connector source.
- **Evidence**: `flink-connector-aws-base/src/main/resources/log4j2.properties`, `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/reader/fanout/FanOutKinesisShardSubscription.java`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The library emits Flink metrics (confirmed by `MetricListener` usage in tests and metric registration in source/sink implementations) but does not provide pre-configured alerting thresholds or CloudWatch alarm definitions. This is expected for a library — alerting is a consumer responsibility. However, there is no documentation of recommended alert configurations for consuming applications.
- **Gap**: No recommended alerting thresholds documented for consuming applications to implement. Consumers must independently determine appropriate error rate and latency thresholds for connector operations.
- **Compensating Controls**:
  - Flink's metric system exposes connector metrics (records sent, bytes sent, request latency) that consumers can alert on
  - Fatal exception classification provides clear signal separation between retryable and terminal failures
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a "Monitoring & Alerting" section to connector documentation recommending specific Flink metrics to alert on (e.g., `numRecordsSendErrors`, `currentSendTime`) with suggested thresholds.
- **Evidence**: `docs/content/docs/connectors/datastream/kinesis.md`, `flink-connector-aws/flink-connector-aws-kinesis-streams/src/test/java/org/apache/flink/connector/kinesis/source/reader/PollingKinesisShardSplitReaderTest.java`

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: The library exposes well-documented Java/Python APIs via builder patterns (e.g., `KinesisStreamsSink.builder()`, `KinesisStreamsSource.builder()`, `DynamoDbSink.builder()`). APIs are documented in `docs/content/docs/connectors/` with examples in Java, Scala, and Python. These are programmatic APIs consumed by Flink applications, not HTTP/REST endpoints.
- **Implication**: Agent integration with this library would be through consuming Flink applications that use these connectors, not direct API calls. Agent tool definitions should target the Flink applications built with these connectors.
- **Recommendation**: No action required. The library's API surface is well-documented for its intended consumers.
- **Evidence**: `docs/content/docs/connectors/datastream/kinesis.md`, `docs/content/docs/connectors/datastream/dynamodb.md`, `docs/content/docs/connectors/datastream/sqs.md`, `docs/content/docs/connectors/datastream/firehose.md`

### API-Q2: Machine-Readable API Specification

- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — machine-readable spec is not applicable. The library exposes typed Java APIs (builders, configuration classes) that serve as the contract. Python type hints in `pyflink/datastream/connectors/kinesis.py` provide equivalent specification for Python consumers. Flink Table Factory service registrations (`META-INF/services/org.apache.flink.table.factories.Factory`) provide machine-discoverable integration points.
- **Implication**: Agent tool bindings for this library would be generated from the Java class signatures and Javadoc, not from OpenAPI specs.
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/resources/META-INF/services/org.apache.flink.table.factories.Factory`

### API-Q3: Structured Error Responses

- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — structured error responses are not applicable. The library communicates errors via typed exceptions (`KinesisStreamsSourceException`, `KinesisStreamsException`, `DynamoDbSinkException`, `AWSAuthenticationException`) with clear exception hierarchies and error classification (fatal vs. retryable via `AWSExceptionClassifierUtil`).
- **Implication**: Consuming applications inherit well-classified error signals. The exception hierarchy distinguishes auth failures, throttling, resource not found, and transient errors — enabling robust retry logic in consuming applications.
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/util/AWSCredentialFatalExceptionClassifiers.java`, `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/sink/throwable/AWSExceptionClassifierUtil.java`

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agent scope — idempotency evaluation is informational. The library's sink connectors (KinesisStreamsSink, DynamoDbSink, SqsSink) implement at-least-once delivery semantics. DynamoDB sink uses conditional writes with partition key deduplication within batches. Kinesis sink supports `failOnError` mode. No explicit idempotency key support at the connector library level (this is typically an application-layer concern for Flink jobs).
- **Implication**: Consuming applications using these sinks should implement idempotency at the Flink job level if write-enabled agents trigger data pipeline operations.
- **Recommendation**: Document idempotency patterns for consuming applications in connector documentation.
- **Evidence**: `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbSink.java`, `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/sink/KinesisStreamsSink.java`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: The library processes binary and JSON data through configurable serialization/deserialization schemas. AWS Glue Schema Registry support provides Avro and JSON format handling. Response data is structured per the consuming application's deserialization schema choice.
- **Implication**: Agents consuming applications built with these connectors will receive data in whatever format the Flink application's deserialization schema produces — typically JSON or Avro.
- **Recommendation**: No action required.
- **Evidence**: `flink-formats-aws/flink-avro-glue-schema-registry/`, `flink-formats-aws/flink-json-glue-schema-registry/`

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: The library implements AIMD (Additive Increase Multiplicative Decrease) congestion control in sink writers with configurable parameters (`maxInFlightRequests`, `maxBatchSize`, `maxBufferedRequests`). AWS service rate limits (Kinesis 5MB/batch, 1MB/record, DynamoDB 25-item batch) are documented and enforced in code. However, these are internal library behaviors, not API-layer rate limit headers.
- **Implication**: Rate limiting is self-managed within the connector library. Consuming applications benefit from built-in backpressure handling without additional configuration.
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/sink/KinesisStreamsSinkWriter.java`, `docs/content/docs/connectors/datastream/kinesis.md`

### AUTH-Q1: Machine Identity Authentication

- **Severity**: INFO
- **Finding**: The library supports 8 credential provider types including machine-identity patterns: `AUTO` (default — uses EC2/ECS instance profiles), `ASSUME_ROLE` (STS with role ARN, session name, external ID), `WEB_IDENTITY_TOKEN` (OIDC/IRSA for EKS), and `CUSTOM` (user-provided class via reflection). The `AUTO` provider chain follows AWS SDK default resolution order (env vars → system props → web identity token → profile → EC2/ECS metadata). However, the library does not itself authenticate agents — it provides credential mechanisms for consuming Flink applications to configure.
- **Implication**: Machine identity authentication is a consuming-application concern. The library provides flexible credential provider support that consuming applications can configure per deployment environment.
- **Recommendation**: No action required — credential provider flexibility is comprehensive.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java`, `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/util/AWSGeneralUtil.java`

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: INFO
- **Finding**: The library delegates authorization to the configured AWS IAM roles/policies. Each connector module requires specific AWS API permissions (e.g., Kinesis sink needs `kinesis:PutRecords`, DynamoDB sink needs `dynamodb:BatchWriteItem`). Permission scoping is an IAM policy configuration concern for consuming applications, not enforced within the library. The library does not conflate permissions across services.
- **Implication**: Consuming applications should configure least-privilege IAM roles per connector type. The library's modular design (separate JARs per service) naturally supports permission isolation.
- **Recommendation**: Add IAM permission reference documentation for each connector (minimum required permissions per connector operation).
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java`, `docs/content/docs/connectors/datastream/kinesis.md`

### AUTH-Q3: Action-Level Authorization

- **Severity**: INFO
- **Finding**: The library separates source (read) and sink (write) connectors as distinct classes and modules. A Flink application can be configured with read-only access (KinesisStreamsSource) without write permissions, or write-only (KinesisStreamsSink) without read permissions. Action-level authorization is enforced via IAM policies on the credentials provided to each connector instance.
- **Implication**: The library architecture supports action-level authorization through its source/sink separation. Consuming applications should assign different IAM roles to source vs. sink connectors.
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/KinesisStreamsSource.java`, `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/sink/KinesisStreamsSink.java`

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: The library supports nested role assumption (credential provider for the assumed role can itself be configured with another credential provider). This enables role chaining patterns. WEB_IDENTITY_TOKEN support enables IRSA (IAM Roles for Service Accounts) in EKS. However, there is no on-behalf-of user flow — the library operates under a single service identity per connector instance.
- **Implication**: Identity propagation is not applicable at the library level. Consuming Flink applications operate under service identities, not on behalf of individual users.
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java`

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: No hardcoded credentials found in source code. The library supports multiple externalized credential mechanisms (environment variables, system properties, AWS profiles, instance metadata, web identity tokens). CI uses GitHub Secrets for AWS credentials with conditional execution. The `BASIC` credential provider type allows direct access key/secret in configuration (intended for testing), but this is a configuration choice made by the consuming application, not hardcoded in the library. The library relies on AWS SDK's built-in credential refresh for rotation.
- **Implication**: Credential management is delegated to consuming applications. The library's flexibility supports both development (explicit keys) and production (instance profiles, IRSA) patterns.
- **Recommendation**: Consider adding a WARNING log message when `BASIC` credential provider is used, recommending `AUTO` or `ASSUME_ROLE` for production deployments.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java`, `.github/workflows/common.yml`

### AUTH-Q6: Immutable Audit Logging ⚡

- **Severity**: INFO
- **Conditional**: System does not execute agent-invoked write operations — audit logging is a consumer responsibility. The library/utility is called by applications that own the audit context.
- **Finding**: The library does not implement audit logging — it is a connector library consumed by Flink applications. Audit logging of connector operations (records sent, records read) is the responsibility of the consuming Flink application and the AWS services being accessed (CloudTrail covers AWS API calls made by the configured credentials).
- **Implication**: AWS CloudTrail automatically logs all AWS API calls made through these connectors. Consuming applications should ensure CloudTrail is enabled in their deployment accounts.
- **Recommendation**: No action required at the library level.
- **Evidence**: `flink-connector-aws-base/src/main/resources/log4j2.properties`

### AUTH-Q7: Agent Identity Suspension

- **Severity**: INFO
- **Finding**: System does not issue or enforce agent identities — suspension is a consumer responsibility. Libraries and utilities are invoked by applications that own identity lifecycle. The library operates under whatever credentials are provided by the consuming application. Identity suspension is achieved by revoking the IAM role or API keys configured in the consuming application.
- **Implication**: Identity suspension for agents using these connectors is managed at the IAM/credential layer, not within the library.
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/util/AWSGeneralUtil.java`

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO. Additionally, the library exposes no write operations owned by the library itself — writes are delegated to AWS services.
- **Finding**: The library implements at-least-once delivery semantics for sinks with Flink checkpointing. DynamoDB sink enforces 25-item batch limits and partition key deduplication. Kinesis sink supports `failOnError` mode for strict error handling. However, there is no compensation/rollback pattern within the library — it writes to AWS services and relies on Flink's checkpoint/restart mechanism for fault tolerance.
- **Implication**: Rollback of writes made through these connectors would require application-level compensation logic in the consuming Flink job.
- **Recommendation**: No action required at the library level.
- **Evidence**: `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbSink.java`, `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/sink/KinesisStreamsSink.java`

### STATE-Q4: Circuit Breakers and Resilience

- **Severity**: INFO
- **Finding**: The library explicitly disables circuit breakers (`.circuitBreakerEnabled(false)`) in favor of exponential backoff with half-jitter retry (50 max attempts, 300ms–1000ms base delay). Fatal exception classification (`AWSCredentialFatalExceptionClassifiers`) provides fast-fail for non-retryable errors (STS failures, SDK misconfiguration). AIMD congestion control in sinks provides adaptive rate limiting. Recoverable exception list in EFO source triggers subscription re-activation.
- **Implication**: The library uses retry + fatal classification + congestion control instead of circuit breakers. This is a deliberate design choice — circuit breakers at the connector level could interfere with Flink's own failure handling and checkpointing mechanisms.
- **Recommendation**: Document the resilience design rationale (why circuit breakers are disabled) in connector documentation to help consuming applications understand the error propagation model.
- **Evidence**: `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/KinesisStreamsSource.java`, `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/util/AWSCredentialFatalExceptionClassifiers.java`

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: INFO
- **Finding**: System exposes no HTTP/RPC surface — API-layer rate limiting is not applicable. The library implements internal rate limiting via AIMD congestion control (additive increase +10, multiplicative decrease ×0.99) in sink writers. Buffer-based backpressure with configurable `maxBufferedRequests` (default 10,000) prevents overwhelming AWS services. AWS service-level rate limits are enforced by the SDK retry strategy.
- **Implication**: Rate limiting is self-contained within the library. Consuming applications benefit from built-in protection against overwhelming AWS services.
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/sink/KinesisStreamsSinkWriter.java`

### DATA-Q1: Sensitive Data Classification ⚡

- **Severity**: INFO
- **Finding**: Not a data-handling target — no PII/PHI/financial/credential data is stored, processed, or logged by the library itself. The library is a pass-through connector that serializes/deserializes data between Flink and AWS services. The data content is determined by the consuming application's data model, not by the library. The library does not inspect, classify, or persist the data flowing through it.
- **Implication**: Data classification is a consuming-application responsibility. The library handles opaque byte streams.
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/sink/KinesisStreamsSink.java`

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: INFO
- **Conditional**: No persistent data store and no user-data logging — residency requirements do not apply.
- **Finding**: The library does not store or replicate data. It connects to AWS services in whatever region is configured by the consuming application. Region configuration is explicit via `AWSConfigConstants.AWS_REGION` — the library does not make cross-region calls unless explicitly configured to do so.
- **Implication**: Data residency is enforced by the consuming application's region configuration and the AWS service's data handling. The library respects the configured region.
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java`

### DATA-Q6: PII Redaction in Logs

- **Severity**: INFO
- **Finding**: System does not log user data and holds no user data — PII-in-logs risk is not applicable. Library logging is limited to operational messages (subscription activation, shard assignment, error conditions). Log messages reference AWS resource identifiers (stream ARN, shard ID, consumer ARN) but do not log data content flowing through the connector. Root logger is set to OFF in production JARs.
- **Implication**: PII risk in logs is a consuming-application concern. The library's logging does not include data payloads.
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws-base/src/main/resources/log4j2.properties`, `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/reader/fanout/FanOutKinesisShardSubscription.java`

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: INFO
- **Finding**: Library/utility — staging environments are a consumer concern. The library provides comprehensive test infrastructure: MiniCluster-based E2E tests, Localstack integration, mock proxies (`TestKinesisStreamProxy`), and conditional AWS E2E tests activated via Maven profiles. Consuming applications can test against these patterns.
- **Implication**: The library's test infrastructure serves as a reference for consuming applications building their own staging environments.
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws-e2e-tests/README.md`, `.github/workflows/common.yml`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: The library emits Flink operational metrics (records sent/received, bytes, latency, errors) via Flink's metrics system. No business-outcome metrics are defined — this is expected for a connector library that is agnostic to business domain.
- **Implication**: Business outcome metrics are a consuming-application responsibility. The library provides the operational metrics foundation that consuming applications can build on.
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws/flink-connector-aws-kinesis-streams/src/test/java/org/apache/flink/connector/kinesis/source/reader/PollingKinesisShardSplitReaderTest.java`

### ENG-Q4: API Test Coverage

- **Severity**: INFO
- **Finding**: The library has comprehensive test coverage: 147 Java test files + 1 Python test file covering unit tests, integration tests, architecture tests, packaging tests, and E2E tests. Tests run in CI across JDK 11, 17, 21 with nightly builds against Flink SNAPSHOT. Architecture tests (ArchUnit) enforce structural rules. However, there are no consumer-driven contract tests (Pact) validating the public API contract from a consumer perspective.
- **Implication**: Test coverage is strong but focused on internal correctness rather than contract stability for downstream consumers.
- **Recommendation**: Consider adding API compatibility tests via `japicmp-maven-plugin` to detect binary incompatible changes.
- **Evidence**: `.github/workflows/common.yml`, `flink-connector-aws/flink-connector-aws-kinesis-streams/src/test/`, `flink-connector-aws-e2e-tests/`

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names and configuration keys are human-readable and semantically meaningful. Configuration constants use clear naming (`aws.credentials.provider`, `aws.region`, `aws.endpoint`, `aws.trust.all.certificates`). Java class and method names follow standard conventions (`KinesisStreamsSinkBuilder`, `setMaxBatchSize`, `setFailOnError`). No legacy abbreviations detected.
- **Implication**: Agent tool generation from these APIs would benefit from the clear naming — LLMs can reason about `setMaxBufferedRequests` without a data dictionary.
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java`, `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/sink/KinesisStreamsSink.java`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: The library integrates with AWS Glue Schema Registry (Avro and JSON format modules) which serves as a data catalog for serialization schemas. Table Factory service registrations (`META-INF/services`) provide Flink's service discovery mechanism. Connector documentation in `docs/` describes available configuration options and data formats.
- **Implication**: Schema discovery for agent tool bindings is supported through Glue Schema Registry integration and Flink's service loader mechanism.
- **Recommendation**: No action required.
- **Evidence**: `flink-formats-aws/flink-avro-glue-schema-registry/`, `flink-formats-aws/flink-json-glue-schema-registry/`, `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/resources/META-INF/services/org.apache.flink.table.factories.Factory`

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: The library does not implement data quality scoring — it is a transport connector. Data quality is determined by the upstream producers and downstream consumers. The library provides exact-once semantics (source with checkpointing) and at-least-once delivery (sinks), which are data integrity guarantees rather than quality metrics.
- **Implication**: Data quality monitoring is a consuming-application concern.
- **Recommendation**: No action required.
- **Evidence**: `docs/content/docs/connectors/datastream/kinesis.md`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: The library exposes well-documented programmatic Java/Python APIs via builder patterns. Comprehensive documentation exists in `docs/content/docs/connectors/` covering DataStream and Table/SQL APIs for all connectors. No HTTP/REST API surface exists — this is a library consumed programmatically.
- **Gap**: N/A — library APIs are documented appropriately for their consumer type.
- **Recommendation**: No action required.
- **Evidence**: `docs/content/docs/connectors/datastream/kinesis.md`, `docs/content/docs/connectors/datastream/dynamodb.md`, `docs/content/docs/connectors/datastream/sqs.md`, `docs/content/docs/connectors/datastream/firehose.md`

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — machine-readable spec is not applicable. Library contracts are expressed via typed Java APIs, Python type hints, and Flink Table Factory service registrations.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/resources/META-INF/services/org.apache.flink.table.factories.Factory`

#### API-Q3: Structured Error Responses
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — structured error responses are not applicable. The library communicates errors via typed Java exceptions with clear classification (fatal vs. retryable).
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/util/AWSCredentialFatalExceptionClassifiers.java`, `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/sink/throwable/AWSExceptionClassifierUtil.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agent scope. The library's sink connectors implement at-least-once delivery with DynamoDB supporting partition key deduplication within batches.
- **Gap**: No explicit idempotency key support at the connector library level.
- **Recommendation**: Document idempotency patterns for consuming applications.
- **Evidence**: `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbSink.java`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: Data format is configurable via deserialization schemas (JSON, Avro via Glue Schema Registry). Binary and structured formats both supported.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `flink-formats-aws/flink-avro-glue-schema-registry/`, `flink-formats-aws/flink-json-glue-schema-registry/`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has state changes (stateful-crud, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: The library implements AIMD congestion control and documents AWS service rate limits. No HTTP-layer rate limit headers (not applicable for a library).
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/sink/KinesisStreamsSinkWriter.java`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: The library provides comprehensive credential provider support (8 types including ASSUME_ROLE, WEB_IDENTITY_TOKEN, AUTO chain) but does not itself authenticate agents. Authentication is a consuming-application concern. The library does not issue or validate identities.
- **Gap**: N/A — library delegates authentication to consuming applications and AWS SDK.
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java`, `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/util/AWSGeneralUtil.java`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: INFO
- **Finding**: The library's modular architecture (separate JARs per AWS service) naturally supports permission isolation. Each connector requires specific AWS API permissions. Scoping is enforced via IAM policies configured by consuming applications.
- **Gap**: No IAM permission reference documentation per connector.
- **Recommendation**: Add minimum-required IAM permissions documentation per connector.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO
- **Finding**: Source (read) and sink (write) connectors are separate classes and modules, enabling IAM-based action-level authorization by the consuming application.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/KinesisStreamsSource.java`, `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/sink/KinesisStreamsSink.java`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: Supports nested role assumption and IRSA patterns. No on-behalf-of user flow (not applicable for connector library).
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java`

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: No hardcoded credentials. Multiple externalized credential mechanisms supported. CI uses GitHub Secrets. Library relies on AWS SDK credential refresh for rotation.
- **Gap**: `BASIC` credential provider allows direct key/secret in config with no warning.
- **Recommendation**: Consider logging a WARNING when BASIC provider is used.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java`, `.github/workflows/common.yml`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: INFO
- **Conditional**: System does not execute agent-invoked write operations — audit logging is a consumer responsibility.
- **Finding**: Library does not implement audit logging. AWS CloudTrail covers API calls made through configured credentials.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws-base/src/main/resources/log4j2.properties`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: System does not issue or enforce agent identities — suspension is a consumer responsibility.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/util/AWSGeneralUtil.java`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO. System exposes no write operations owned by the library.
- **Finding**: At-least-once delivery semantics with Flink checkpointing. No library-level compensation/rollback.
- **Gap**: N/A for library scope.
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/sink/KinesisStreamsSink.java`

#### STATE-Q2: Queryable Current State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The library handles concurrent shard processing via Flink's split-based parallelism (FLIP-27). DynamoDB sink deduplicates by partition key within batches. No explicit optimistic locking at the connector level (delegated to Flink's checkpoint mechanism and AWS service-level conflict handling).
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbSink.java`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: INFO
- **Finding**: Circuit breakers explicitly disabled. Library uses exponential backoff with half-jitter (50 attempts, 300ms–1000ms), fatal exception classification, and AIMD congestion control as its resilience strategy. This is a deliberate design choice for Flink connector semantics.
- **Gap**: No circuit breaker — deliberate choice documented in code.
- **Recommendation**: Document resilience design rationale in connector docs.
- **Evidence**: `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/KinesisStreamsSource.java`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface. Internal AIMD rate limiting protects AWS services from connector overload.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/sink/KinesisStreamsSinkWriter.java`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The library enforces batch size limits (DynamoDB 25-item max, Kinesis 500 records/5MB max) and configurable buffer limits (`maxBufferedRequests`). These are service-limit enforcement, not agent-specific transaction limits.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbSink.java`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: Library provides MiniCluster-based E2E tests, Localstack integration, mock proxies, and conditional AWS E2E tests. Staging is a consumer concern.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws-e2e-tests/README.md`, `.github/workflows/common.yml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification ⚡
- **Severity**: INFO
- **Finding**: Not a data-handling target — no PII/PHI/financial/credential data is stored, processed, or logged by the library. The library is a pass-through transport connector.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/sink/KinesisStreamsSink.java`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: No persistent data store and no user-data logging — residency requirements do not apply.
- **Finding**: Library does not store data. Region is configured by consuming application.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java`

#### DATA-Q3: Selective Query Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has list/query endpoints with potentially unbounded results
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: System does not log user data and holds no user data — PII-in-logs risk is not applicable. Logging references AWS resource identifiers only.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws-base/src/main/resources/log4j2.properties`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: Library does not implement data quality scoring. Transport connector is agnostic to data quality — consuming applications own this concern.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `docs/content/docs/connectors/datastream/kinesis.md`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: Semantic versioning used (v6.0-SNAPSHOT). No automated breaking-change detection in CI. Public API surface changes could break downstream consumers without early warning.
- **Gap**: No API compatibility checking tools (japicmp, revapi) or consumer-driven contract tests in CI pipeline.
- **Recommendation**: Add `japicmp-maven-plugin` or `revapi-maven-plugin` to CI for binary compatibility checks.
- **Evidence**: `.github/workflows/common.yml`, `pom.xml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: All field names and configuration keys are human-readable and semantically meaningful. No legacy abbreviations.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: AWS Glue Schema Registry integration provides schema catalog. Flink service loader mechanism provides connector discovery. Documentation in `docs/` describes available options.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `flink-formats-aws/flink-avro-glue-schema-registry/`, `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/resources/META-INF/services/org.apache.flink.table.factories.Factory`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: SLF4J with plain-text PatternLayout. No structured JSON logging, no MDC context enrichment, no OpenTelemetry/X-Ray hooks. Root logger OFF (correct for library).
- **Gap**: No trace context propagation or structured logging support for consuming applications.
- **Recommendation**: Add MDC context propagation for trace IDs in key connector operations.
- **Evidence**: `flink-connector-aws-base/src/main/resources/log4j2.properties`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Library emits Flink metrics but provides no recommended alerting thresholds documentation. Alerting is a consumer concern but guidance is lacking.
- **Gap**: No monitoring/alerting guidance in documentation.
- **Recommendation**: Add recommended alerting thresholds documentation for key connector metrics.
- **Evidence**: `docs/content/docs/connectors/datastream/kinesis.md`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Library emits operational metrics via Flink's metrics system. Business metrics are a consuming-application concern.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `flink-connector-aws/flink-connector-aws-kinesis-streams/src/test/java/org/apache/flink/connector/kinesis/source/reader/PollingKinesisShardSplitReaderTest.java`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: N/A
- **Finding**: This is a `library` repository (via dev-library-application override). This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: N/A
- **Finding**: This is a `library` repository (via dev-library-application override). This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q3: Rollback Capability
- **Severity**: N/A
- **Finding**: This is a `library` repository (via dev-library-application override). This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q4: API Test Coverage
- **Severity**: N/A
- **Finding**: This is a `library` repository (via dev-library-application override). This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: N/A
- **Finding**: This is a `library` repository (via dev-library-application override). This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, DATA-Q2, API-Q8, DISC-Q2 |
| `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/util/AWSGeneralUtil.java` | AUTH-Q1, AUTH-Q7 |
| `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/util/AWSCredentialFatalExceptionClassifiers.java` | API-Q3, STATE-Q4 |
| `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/sink/throwable/AWSExceptionClassifierUtil.java` | API-Q3 |
| `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/sink/KinesisStreamsSink.java` | API-Q4, STATE-Q1, DATA-Q1 |
| `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/sink/KinesisStreamsSinkWriter.java` | API-Q8, STATE-Q5, STATE-Q6 |
| `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/KinesisStreamsSource.java` | AUTH-Q3, STATE-Q4 |
| `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/reader/fanout/FanOutKinesisShardSubscription.java` | OBS-Q1, DATA-Q6 |
| `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbSink.java` | API-Q4, STATE-Q1, STATE-Q3, STATE-Q6 |
| `flink-connector-aws/flink-connector-aws-kinesis-streams/src/test/java/org/apache/flink/connector/kinesis/source/reader/PollingKinesisShardSplitReaderTest.java` | OBS-Q2, OBS-Q3 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/common.yml` | DISC-Q1, OBS-Q2, HITL-Q3, AUTH-Q5, ENG-Q4 |
| `.github/workflows/push_pr.yml` | DISC-Q1 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `pom.xml` | DISC-Q1 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `flink-connector-aws-base/src/main/resources/log4j2.properties` | OBS-Q1, AUTH-Q6, DATA-Q6 |
| `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/resources/META-INF/services/org.apache.flink.table.factories.Factory` | API-Q2, DISC-Q3 |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| `docs/content/docs/connectors/datastream/kinesis.md` | API-Q1, OBS-Q2, DATA-Q7 |
| `docs/content/docs/connectors/datastream/dynamodb.md` | API-Q1 |
| `docs/content/docs/connectors/datastream/sqs.md` | API-Q1 |
| `docs/content/docs/connectors/datastream/firehose.md` | API-Q1 |
| `flink-connector-aws-e2e-tests/README.md` | HITL-Q3 |

### Format/Schema Libraries
| File | Questions Referenced |
|------|---------------------|
| `flink-formats-aws/flink-avro-glue-schema-registry/` | API-Q5, DISC-Q3 |
| `flink-formats-aws/flink-json-glue-schema-registry/` | API-Q5, DISC-Q3 |
