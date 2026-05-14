# Agentic Readiness Analysis Report

**Target**: apache/flink-connector-aws
**Date**: 2026-04-30
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**TD Version**: 3g1ipe93e5d2wb6n5d4yqaf9
**Repository Type**: monorepo
**Service Archetype**: stateless-utility (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, streaming, flink, aws
**Context**: Apache Flink connectors for AWS services (Kinesis, DynamoDB, SQS, etc.)

**Archetype Justification**: All modules are Java library JARs (Source/Sink implementations) embedded into consumer Flink applications. No module exposes an HTTP server, owns persistent state, or runs as a standalone service. Connectors are pure data pipeline components — stateless-utility is the appropriate classification.

**Dev-Library-Application Override (INFO)**: This monorepo is classified as `monorepo` but every module within it functions as a library (Java JAR with no deployable entry point, no Dockerfile, no IaC). The `stateless-utility` archetype is detected and all 5 surface flags are `false`. Per Step 1.5, the **dev-library-application** override applies: the `library` N/A mapping (ENG-Q1 through ENG-Q5 are N/A) is used as baseline, and surface-flag downgrades are applied to remaining questions. The original `repo_type` value `monorepo` is preserved.

- **Surface flags**:
  - has_persistent_data_store: false — Connectors are clients TO data stores (Kinesis, DynamoDB, SQS); they do not own persistent state.
  - has_http_rpc_surface: false — No HTTP server, no REST endpoints, no GraphQL. These are Flink Source/Sink implementations.
  - has_auth_surface: false — Connectors delegate authentication to the AWS SDK credential provider chain. No auth endpoints.
  - has_write_operations: false — While sink connectors write to AWS services, the connectors themselves are libraries, not agent-callable services.
  - has_logging_of_user_data: false — Logging is diagnostic only (SLF4J). No user PII is logged.

---

## Readiness Profile: Agent-Ready

**BLOCKERs**: 0 | **RISK-SAFETY**: 0 | **RISK-QUALITY**: 1 | **INFOs**: 30

Cleared for autonomous operation. Instrument observability. Define scope explicitly. Run controlled pilot first.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK-SAFETY | 0 |
| RISK-QUALITY | 1 |
| INFO | 30 |
| N/A | 5 |
| Not Evaluated (extended) | 7 |
| **Total** | **43** |

**Core Questions Evaluated**: 19 (24 core minus 5 N/A from library override)
**Extended Questions Triggered**: 0
**Extended Questions Not Triggered**: 7
**Questions N/A (repo_type: monorepo + dev-library-application override)**: 5
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
- **Finding**: The connectors use Flink's `@Experimental` annotation on public API classes (e.g., `KinesisStreamsSource`, `DynamoDbStreamsSource`, `KinesisStreamsSourceBuilder`), indicating the API surface is not yet stable. Internal serializers use versioned serialization (e.g., `KinesisShardSplitSerializer` with `CURRENT_VERSION = 2` and `COMPATIBLE_VERSIONS = {0, 1, 2}`, `DynamoDbStreamsSourceEnumeratorStateSerializer` with `CURRENT_VERSION = 0`). Maven version is `6.0-SNAPSHOT`. However, no breaking change detection tooling (e.g., `buf breaking`, OpenAPI diff, semver enforcement) is integrated into the CI pipeline. The CI pipeline runs compile, unit tests, e2e tests, and license checking — but does not include API contract validation or breaking change detection.
- **Gap**: No automated breaking change detection in CI. Agent tool bindings could break silently when library versions change. The `@Experimental` annotation signals instability but does not prevent breaking changes from shipping.
- **Compensating Controls**:
  - Pin connector versions in consumer applications using Maven dependency management to prevent unexpected breakage.
  - Monitor release notes and changelogs for the Apache Flink connector releases before upgrading.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Integrate API binary compatibility checking (e.g., `japicmp-maven-plugin` or Revapi) into the CI pipeline to automatically detect breaking changes to `@PublicEvolving` and `@Public` annotated classes before release.
- **Evidence**: `KinesisStreamsSource.java` (`@Experimental` annotation), `KinesisShardSplitSerializer.java` (versioned serialization), `.github/workflows/common.yml` (CI pipeline — no contract testing step), `pom.xml` (version `6.0-SNAPSHOT`)

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: These are Java library JARs, not HTTP services. They expose a Java API (Source/Sink builders) documented via Javadoc annotations and extensive Markdown documentation in `docs/content/docs/connectors/`. The `KinesisStreamsSourceBuilder`, `DynamoDbStreamsSourceBuilder`, `SqsSinkBuilder`, `KinesisFirehoseSinkBuilder`, and `DynamoDbSinkBuilder` provide fluent builder APIs. Documentation covers usage examples, configuration options, and operational guidance.
- **Implication**: Agent integration with these connectors would occur at the Flink job configuration level, not via HTTP API calls. Tool bindings would target the builder API surface.
- **Recommendation**: No action needed for library consumers. If wrapping connectors in an agent-accessible service, expose the builder parameters via a well-documented REST API.
- **Evidence**: `docs/content/docs/connectors/datastream/kinesis.md`, `docs/content/docs/connectors/datastream/dynamodb.md`, `docs/content/docs/connectors/datastream/sqs.md`, `docs/content/docs/connectors/datastream/firehose.md`, `KinesisStreamsSourceBuilder.java`, `DynamoDbStreamsSourceBuilder.java`

### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — machine-readable spec is not applicable. These are Java libraries; their API contracts are expressed via typed Java classes, Javadoc annotations (`@Experimental`, `@PublicEvolving`, `@Internal`), and Maven dependency coordinates. No OpenAPI, AsyncAPI, or GraphQL spec exists because there is no HTTP surface to describe.
- **Implication**: Agent tool generation would use Java class metadata and documentation rather than OpenAPI specs.
- **Recommendation**: No action needed. Library API contracts are expressed through typed exports and annotations.
- **Evidence**: `KinesisStreamsSource.java` (`@Experimental`), `AWSConfigConstants.java` (`@PublicEvolving`)

### API-Q3: Structured Error Responses
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — structured error responses are not applicable. Libraries communicate errors via typed Java exceptions: `KinesisStreamsSourceException`, `SqsSinkException`, `DynamoDbSinkException`, `KinesisFirehoseException`, `AWSAuthenticationException`. The `FatalExceptionClassifier` chain in each sink writer distinguishes retryable from fatal errors (e.g., `ResourceNotFoundException` is fatal, throttling is retryable).
- **Implication**: Consuming applications receive well-typed exceptions with clear retryable/fatal semantics. This is the library-appropriate equivalent of structured error responses.
- **Recommendation**: No action needed. Exception hierarchy is well-designed for programmatic error handling.
- **Evidence**: `SqsSinkWriter.java` (exception classifier chain), `DynamoDbSinkWriter.java` (DYNAMODB_FATAL_EXCEPTION_CLASSIFIER), `AWSExceptionClassifierUtil.java`

### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Agent scope is read-only; idempotency of write operations is informational only. The DynamoDB sink supports deduplication via `overwriteByPartitionKeys` (idempotent PUT operations). Kinesis and SQS sinks do not implement client-side idempotency — they rely on at-least-once delivery semantics with Flink checkpointing.
- **Implication**: For write-enabled agent scenarios, DynamoDB sink offers idempotency; Kinesis/SQS sinks would need consumer-side deduplication.
- **Recommendation**: No action for read-only scope. For future write-enabled scenarios, consider documenting idempotency guarantees per connector.
- **Evidence**: `DynamoDbSinkWriter.java` (overwriteByPartitionKeys deduplication logic)

### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: Library outputs are Java objects (Flink DataStream elements), not HTTP responses. Deserialization schemas convert raw AWS records (Kinesis `Record`, DynamoDB Streams `Record`) into typed Java objects. Response format depends entirely on the `DeserializationSchema` configured by the consumer.
- **Implication**: Data format is consumer-defined. Connectors are format-agnostic transport layers.
- **Recommendation**: No action needed.
- **Evidence**: `KinesisStreamsRecordEmitter.java`, `DynamoDbStreamsRecordEmitter.java`

### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: As a library, rate limit headers are not applicable (no HTTP responses). However, the connectors document AWS service-level throttling behavior. The `KinesisStreamsSource` configures exponential backoff retry strategies for `LimitExceededException` responses from AWS APIs. Configurable retry parameters exist: `RETRY_STRATEGY_MIN_DELAY_OPTION`, `RETRY_STRATEGY_MAX_DELAY_OPTION`, `RETRY_STRATEGY_MAX_ATTEMPTS_OPTION`.
- **Implication**: Rate limiting is handled at the AWS service level and the connector implements proper backoff. Consuming applications inherit this behavior.
- **Recommendation**: No action needed.
- **Evidence**: `KinesisStreamsSource.java` (createExpBackoffRetryStrategyBuilder), `AWSConfigOptions.java`

### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: The connectors fully support AWS SDK credential provider chain with 8 authentication methods: `ENV_VAR`, `SYS_PROP`, `PROFILE`, `BASIC`, `ASSUME_ROLE`, `WEB_IDENTITY_TOKEN`, `CUSTOM`, and `AUTO`. The library enables machine identity (IAM roles, service accounts, web identity tokens) but does not enforce a specific method — that is the consumer's responsibility. All credential handling is delegated to `AWSGeneralUtil.getCredentialsProvider()`.
- **Implication**: As a library, authentication is fully configurable by consuming applications. The connector supports all standard AWS machine identity mechanisms.
- **Recommendation**: No action needed. Consumers should use `ASSUME_ROLE` or `WEB_IDENTITY_TOKEN` for production deployments.
- **Evidence**: `AWSConfigConstants.java` (CredentialProvider enum), `AWSGeneralUtil.java` (getCredentialsProvider method)

### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: INFO
- **Finding**: Library delegates permission scoping entirely to IAM policies configured by consuming applications. The connectors accept any `AwsCredentialsProvider` via configuration properties. Scoped permissions (e.g., `kinesis:GetRecords` vs `kinesis:PutRecords`) are enforced at the IAM policy level, not within the library. Since `has_auth_surface` is `false` and this is a dev-library-application, scope enforcement is a consumer responsibility.
- **Implication**: Consuming applications must configure IAM policies with least-privilege for each connector. The library does not restrict or validate IAM scope.
- **Recommendation**: Document recommended minimum IAM permissions per connector in the documentation (e.g., Kinesis Source needs `kinesis:GetRecords`, `kinesis:ListShards`, `kinesis:DescribeStream`).
- **Evidence**: `AWSClientUtil.java` (credentialsProvider passed to client builder), `AWSGeneralUtil.java`

### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO
- **Finding**: Action-level authorization is fully delegated to AWS IAM. Each connector calls specific AWS API actions (e.g., `kinesis:GetRecords` for source, `dynamodb:BatchWriteItem` for sink). IAM policies can restrict an agent identity to read-only actions (source operations) while denying write actions (sink operations) on the same resource. Since `has_auth_surface` is `false`, this is a consumer responsibility.
- **Implication**: IAM natively supports action-level authorization for all AWS services the connectors interact with.
- **Recommendation**: No action needed at the library level. Consumers should configure IAM policies with action-level restrictions.
- **Evidence**: `KinesisStreamsSource.java` (uses `KinesisClient` for read operations), `DynamoDbSinkWriter.java` (uses `DynamoDbAsyncClient.batchWriteItem`)

### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: Archetype calibration for stateless-utility → INFO. Connectors are stateless data pipeline components that do not propagate user identity. They authenticate as a single service identity (the IAM role of the Flink job) to AWS services. There is no on-behalf-of flow or user context propagation.
- **Implication**: Identity propagation is not applicable at the connector level. If agent use cases require per-user data access scoping, this must be implemented at the Flink application layer.
- **Recommendation**: No action needed.
- **Evidence**: `AWSClientUtil.java` (single credentials provider per client instance)

### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: No hardcoded credentials found in the codebase. The connectors accept credentials via configuration properties (`aws.credentials.provider`, `aws.credentials.provider.basic.accesskeyid`, etc.) and support all AWS SDK credential provider types including `ASSUME_ROLE` and `WEB_IDENTITY_TOKEN` (which use short-lived credentials). The `BASIC` provider type accepts access keys via configuration, but these are not hardcoded — they are passed at runtime by the consuming application. No `.env` files or hardcoded secrets were found.
- **Implication**: Credential management is clean. The library supports rotation-friendly auth methods (IAM roles, web identity tokens).
- **Recommendation**: No action needed. Document that `BASIC` credential provider should be avoided in production in favor of `ASSUME_ROLE` or `AUTO`.
- **Evidence**: `AWSConfigConstants.java`, `AWSGeneralUtil.java` (getCredentialsProvider), grep scan for `password=`, `secret=` patterns returned no results

### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY, but has_auth_surface=false AND has_write_operations=false → INFO
- **Finding**: System does not execute agent-invoked write operations — audit logging is a consumer responsibility. The library/utility is called by applications that own the audit context. AWS CloudTrail captures all API calls made by the connectors at the AWS service level, providing immutable audit logging of connector operations.
- **Implication**: Audit logging exists at the AWS platform layer (CloudTrail) regardless of what the library implements.
- **Recommendation**: No action needed at the library level. Consuming applications should ensure CloudTrail is enabled for all accounts where connectors operate.
- **Evidence**: `AWSClientUtil.java` (all API calls go through standard AWS SDK which is CloudTrail-logged)

### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: System does not issue or enforce agent identities — suspension is a consumer responsibility. Libraries and utilities are invoked by applications that own identity lifecycle. IAM roles and API keys used by the connectors can be suspended via standard AWS IAM controls (role deactivation, policy removal, STS session revocation).
- **Implication**: Identity suspension is handled at the IAM/STS layer, not at the library level.
- **Recommendation**: No action needed.
- **Evidence**: `AWSConfigConstants.java` (credentials configured externally)

### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY, but has_write_operations=false AND has_http_rpc_surface=false AND stateless-utility archetype → INFO
- **Finding**: System exposes no write operations in the agent context — compensation logic is not applicable. The connectors are libraries embedded in Flink jobs. Flink's checkpointing mechanism provides exactly-once semantics and rollback capability at the framework level.
- **Implication**: Compensation is handled by Flink's checkpointing, not by the connector library.
- **Recommendation**: No action needed.
- **Evidence**: `KinesisStreamsSource.java` (checkpointing via SplitEnumerator state serialization), `DynamoDbStreamsSource.java`

### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agents do not perform writes, so concurrency controls for write operations are informational only. The Flink framework handles concurrent shard processing via its split-based parallelism model. DynamoDB sink supports `overwriteByPartitionKeys` for deduplication of concurrent writes.
- **Implication**: Concurrency is managed by the Flink runtime, not the connector library.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `DynamoDbSinkWriter.java` (overwriteByPartitionKeys), `KinesisStreamsSource.java` (split-based parallelism)

### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: INFO
- **Finding**: Extended question triggered (connectors call external AWS services). Base severity: RISK-SAFETY. **Dev-library-application downgrade to INFO**: The RISK-SAFETY rationale for STATE-Q4 is "Runaway agent loops cascade through dependencies" — this presupposes an agent-callable surface (`has_http_rpc_surface`) through which agent traffic reaches the system and cascades outward. Since `has_http_rpc_surface` is `false`, there is no agent-to-system call path that would trigger cascading failures. The connectors are embedded in consumer Flink jobs; the consumer application (not the library) is the agent-callable surface and owns circuit-breaker responsibility. The connectors implement robust retry and resilience patterns: `KinesisStreamsSource` uses `StandardRetryStrategy` with exponential backoff and half-jitter for `LimitExceededException`, `DynamoDbStreamsSource` uses `AdaptiveRetryStrategy`, and all sink writers use `FatalExceptionClassifier` chains distinguishing retryable from fatal errors.
- **Implication**: Resilience patterns are well-implemented via AWS SDK retry strategies. The library handles transient failures gracefully. Circuit-breaker enforcement for agent traffic is the responsibility of the consuming application that wraps these connectors.
- **Recommendation**: No action needed at the library level. Consuming applications exposing these connectors to agents should implement circuit breakers at their service layer.
- **Evidence**: `KinesisStreamsSource.java` (createExpBackoffRetryStrategyBuilder), `DynamoDbStreamsSource.java` (AdaptiveRetryStrategy), `DynamoDbSinkWriter.java` (DYNAMODB_FATAL_EXCEPTION_CLASSIFIER)

### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: System exposes no HTTP/RPC surface — API-layer rate limiting is not applicable. Libraries invoked by consuming applications inherit the consumer's rate limiting. AWS service-level throttling (e.g., Kinesis `LimitExceededException`) is handled by the exponential backoff retry strategies built into each connector.
- **Implication**: Rate limiting is enforced by AWS services and handled by connector retry logic.
- **Recommendation**: No action needed.
- **Evidence**: `KinesisStreamsSource.java` (retryOnExceptionOrCauseInstanceOf LimitExceededException)

### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agents cannot modify records, trigger spend, or delete data. Transaction limits for write operations are informational only. The Flink async sink framework provides configurable `maxBatchSize`, `maxInFlightRequests`, `maxBufferedRequests`, and `maxBatchSizeInBytes` parameters that bound write operations when used by consuming applications.
- **Implication**: Blast radius controls are available at the Flink framework level for consuming applications.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `DynamoDbSinkWriter.java` (AsyncSinkWriterConfiguration parameters), `SqsSinkWriter.java`

### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agents do not make state changes, so draft/pending states are informational only. The connectors are data pipeline libraries — they do not implement application-level state machines or approval workflows.
- **Implication**: HITL patterns would be implemented at the consuming application or orchestration layer, not in the connector library.
- **Recommendation**: No action needed.
- **Evidence**: No evidence of draft/pending patterns — expected for library connectors.

### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agents do not execute write operations, so approval gates are informational only. The connectors do not implement approval workflows — they are data transport libraries.
- **Implication**: Approval gates would be implemented at the orchestration layer.
- **Recommendation**: No action needed.
- **Evidence**: No evidence of approval patterns — expected for library connectors.

### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: Dev-library-application override applies. Libraries do not own staging environments — their consumers do. However, the repository provides excellent local testing capability: E2E tests use testcontainers and a real Flink distribution for integration testing against localstack-equivalent AWS services. The `flink-connector-aws-e2e-tests` module contains end-to-end tests for Kinesis Streams, Kinesis Firehose, SQS, and Glue Schema Registry.
- **Implication**: Consumers can test connector behavior locally using the provided e2e test patterns as a reference.
- **Recommendation**: No action needed.
- **Evidence**: `flink-connector-aws-e2e-tests/README.md`, `flink-connector-aws-e2e-tests/pom.xml` (run-end-to-end-tests profile)

### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Dev-library-application override → INFO. Connectors are data transport layers; they do not own the data they transport. No PII/PHI/financial/credential data is stored, processed, or logged by the library itself. Data flows through the connectors as opaque byte arrays or AWS SDK record objects.
- **Implication**: Data classification is the responsibility of consuming applications that produce/consume data through these connectors.
- **Recommendation**: No action needed at the library level.
- **Evidence**: `KinesisStreamsRecordEmitter.java`, `DynamoDbStreamsRecordEmitter.java` — data is passed through deserialization schema without inspection

### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY, but has_persistent_data_store=false AND has_logging_of_user_data=false → INFO
- **Finding**: No persistent data store and no user-data logging — residency requirements do not apply at the library level. The connectors connect to AWS services in a configured region (via `aws.region` property). Data residency is enforced by the AWS service endpoints and IAM policies configured by consuming applications.
- **Implication**: Data residency is controlled by consumer configuration of `aws.region` and AWS service-level controls.
- **Recommendation**: No action needed.
- **Evidence**: `AWSConfigConstants.java` (`AWS_REGION` configuration), `AWSGeneralUtil.java` (getRegion)

### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: System does not log user data and holds no user data — PII-in-logs risk is not applicable. Logging is diagnostic only (SLF4J) — log messages contain operational metadata (batch sizes, error counts, shard IDs) but never user data payloads. Example: `LOG.warn("DynamoDB Sink failed to persist and will retry {} entries.", requestEntries.size(), err)` logs the count, not the content.
- **Implication**: No PII leakage risk from connector logging.
- **Recommendation**: No action needed.
- **Evidence**: `DynamoDbSinkWriter.java` (LOG.warn with size only), `SqsSinkWriter.java` (LOG.warn with size and first entry toString — note: `requestEntries.get(0).toString()` could potentially log message content if SQS messages contain PII, but this is diagnostic and controlled by the consumer's data)

### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality scoring or completeness metrics exist at the connector level. Connectors are transport layers — data quality is a property of the data flowing through them, not something the connector measures. The Kinesis source exposes a `millisBehindLatest` metric that indicates data freshness/lag.
- **Implication**: Data quality monitoring should be implemented at the consuming application level. The `millisBehindLatest` metric provides a useful freshness signal.
- **Recommendation**: No action needed at the library level. Consumers should implement data quality checks in their Flink pipelines.
- **Evidence**: `KinesisShardMetrics.java` (millisBehindLatest gauge), `MetricConstants.java`

### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Configuration property names are clear and semantically meaningful. Examples: `aws.region`, `aws.credentials.provider`, `aws.http-client.max-concurrency`, `aws.http-client.read-timeout`. Java class names follow clear naming conventions: `KinesisStreamsSource`, `DynamoDbSinkWriter`, `SqsSinkBuilder`. Metric names are descriptive: `millisBehindLatest`, `KinesisStreamSource`, `stream`, `shardId`, `accountId`, `region`.
- **Implication**: No data dictionary needed — field names are self-documenting.
- **Recommendation**: No action needed.
- **Evidence**: `AWSConfigConstants.java`, `MetricConstants.java`, `KinesisSourceConfigOptions.java`

### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog or metadata layer exists. The connectors are transport libraries — they do not hold data that would appear in a catalog. Schema information for Kinesis/DynamoDB data is defined by consuming applications via `DeserializationSchema` implementations. The Glue Schema Registry integration (`flink-formats-aws`) provides schema registry support for Avro and JSON formats.
- **Implication**: Schema management is available via AWS Glue Schema Registry integration for consumers who need it.
- **Recommendation**: No action needed.
- **Evidence**: `flink-formats-aws/flink-avro-glue-schema-registry/`, `flink-formats-aws/flink-json-glue-schema-registry/`

### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: Library/utility — tracing and correlation are consumer concerns. The library's obligation is to propagate trace context if provided. The connectors use SLF4J for logging (consumer provides the logging implementation). No OpenTelemetry or X-Ray instrumentation is embedded in the library. Flink's metrics framework (used by `KinesisShardMetrics`, `DynamoDbStreamsShardMetrics`) provides observability hooks that consumers can integrate with their monitoring stack.
- **Implication**: Consumers can add tracing at the Flink application level. The connector does not block trace propagation.
- **Recommendation**: Consider adding OpenTelemetry context propagation support in future versions for enhanced observability.
- **Evidence**: `KinesisShardMetrics.java` (Flink metrics integration), SLF4J usage across all modules

### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Library/utility — alerting on error rates and latency is a consumer concern. The connectors expose Flink metrics (e.g., `numRecordsSendErrorsCounter`, `numRecordsSendPartialFailure`, `millisBehindLatest`) that consuming applications can use to configure alerts. No built-in alerting thresholds exist at the library level.
- **Implication**: Consumers have all necessary metrics to configure alerting. The library provides the signals; consumers set the thresholds.
- **Recommendation**: No action needed. Document recommended alerting thresholds for each metric.
- **Evidence**: `DynamoDbSinkWriter.java` (numRecordsSendErrorsCounter, numRecordsSendPartialFailure), `KinesisShardMetrics.java` (millisBehindLatest)

### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: The connectors publish operational metrics via Flink's metrics framework: `millisBehindLatest` (stream processing lag), `numRecordsSendErrorsCounter` (write errors), `numRecordsSendPartialFailure` (partial batch failures). These are infrastructure/operational metrics, not business outcome metrics. Business outcome metrics are the responsibility of consuming applications.
- **Implication**: Business outcome metrics (e.g., records processed per second, end-to-end latency) should be implemented at the Flink application level using the connector metrics as building blocks.
- **Recommendation**: No action needed.
- **Evidence**: `KinesisShardMetrics.java`, `DynamoDbSinkWriter.java`, `SqsSinkWriter.java`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: These are Java library JARs, not HTTP services. The connectors expose a well-documented Java API via builder pattern classes (`KinesisStreamsSourceBuilder`, `DynamoDbStreamsSourceBuilder`, `SqsSinkBuilder`, `DynamoDbSinkBuilder`, `KinesisFirehoseSinkBuilder`). Comprehensive Markdown documentation exists in `docs/content/docs/connectors/` covering DataStream and Table API usage for each connector. No REST, GraphQL, or AsyncAPI interface exists because the connectors are embedded libraries consumed within Flink jobs.
- **Gap**: No HTTP API surface — the library exposes Java APIs documented via Javadoc and Markdown. This is expected and appropriate for a library project.
- **Recommendation**: No action needed. If agents need to interact with these connectors, expose them via a wrapper service with a documented REST API.
- **Evidence**: `docs/content/docs/connectors/datastream/kinesis.md`, `KinesisStreamsSourceBuilder.java`, `DynamoDbStreamsSourceBuilder.java`, `SqsSinkBuilder.java`

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — machine-readable spec is not applicable. Library API contracts are expressed via typed Java classes with Flink annotations (`@Experimental`, `@PublicEvolving`, `@Internal`).
- **Gap**: N/A — libraries express contracts via typed exports, not OpenAPI specs.
- **Recommendation**: No action needed.
- **Evidence**: `KinesisStreamsSource.java` (`@Experimental`), `AWSConfigConstants.java` (`@PublicEvolving`)

#### API-Q3: Structured Error Responses
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — structured error responses are not applicable. Libraries communicate errors via typed exceptions with retryable/fatal classification: `KinesisStreamsSourceException`, `SqsSinkException` (with `SqsFailFastSinkException` subclass), `DynamoDbSinkException`, `KinesisFirehoseException`. `FatalExceptionClassifier` chains in each sink writer classify AWS errors (e.g., `ResourceNotFoundException` → fatal, `LimitExceededException` → retryable).
- **Gap**: N/A — exception hierarchy is the library-appropriate equivalent.
- **Recommendation**: No action needed.
- **Evidence**: `SqsSinkWriter.java`, `DynamoDbSinkWriter.java`, `AWSExceptionClassifierUtil.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only scope — idempotency is informational. DynamoDB sink supports deduplication via `overwriteByPartitionKeys`. Kinesis/SQS sinks rely on Flink checkpointing for at-least-once delivery.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action needed.
- **Evidence**: `DynamoDbSinkWriter.java` (overwriteByPartitionKeys)

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: Library outputs are Java objects (Flink DataStream elements), not HTTP responses. Format depends on the consumer-configured `DeserializationSchema`.
- **Gap**: N/A — format-agnostic transport layer.
- **Recommendation**: No action needed.
- **Evidence**: `KinesisStreamsRecordEmitter.java`, `DynamoDbStreamsRecordEmitter.java`

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
- **Finding**: As a library, rate limit headers are not applicable. Connectors implement exponential backoff retry strategies for AWS service-level throttling (e.g., `LimitExceededException`). Configurable retry parameters: `RETRY_STRATEGY_MIN_DELAY_OPTION`, `RETRY_STRATEGY_MAX_DELAY_OPTION`, `RETRY_STRATEGY_MAX_ATTEMPTS_OPTION`.
- **Gap**: N/A — rate limiting is at the AWS service level.
- **Recommendation**: No action needed.
- **Evidence**: `KinesisStreamsSource.java`, `AWSConfigOptions.java`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Connectors fully support AWS SDK credential provider chain with 8 auth methods: `ENV_VAR`, `SYS_PROP`, `PROFILE`, `BASIC`, `ASSUME_ROLE`, `WEB_IDENTITY_TOKEN`, `CUSTOM`, `AUTO`. Machine identity is enabled but not enforced — consumer's responsibility.
- **Gap**: N/A — library provides all necessary auth mechanisms.
- **Recommendation**: Consumers should use `ASSUME_ROLE` or `WEB_IDENTITY_TOKEN` for production.
- **Evidence**: `AWSConfigConstants.java` (CredentialProvider enum), `AWSGeneralUtil.java`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: INFO
- **Finding**: Library delegates permission scoping to IAM. Connectors accept any `AwsCredentialsProvider`. Scoped permissions enforced at IAM policy level, not in library. Dev-library-application — scope enforcement is consumer responsibility.
- **Gap**: N/A — IAM handles scoping.
- **Recommendation**: Document minimum IAM permissions per connector.
- **Evidence**: `AWSClientUtil.java`, `AWSGeneralUtil.java`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO
- **Finding**: Action-level authorization delegated to AWS IAM. Each connector calls specific API actions (e.g., `kinesis:GetRecords`, `dynamodb:BatchWriteItem`). IAM policies can restrict by action. Dev-library-application — consumer responsibility.
- **Gap**: N/A — IAM natively supports action-level auth.
- **Recommendation**: No action needed.
- **Evidence**: `KinesisStreamsSource.java`, `DynamoDbSinkWriter.java`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: Archetype calibration for stateless-utility → INFO. Connectors authenticate as single service identity (Flink job IAM role). No on-behalf-of flow or user context propagation.
- **Gap**: N/A — not applicable for stateless-utility connectors.
- **Recommendation**: No action needed.
- **Evidence**: `AWSClientUtil.java`

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: No hardcoded credentials found. Credentials accepted via configuration properties at runtime. Supports rotation-friendly methods (`ASSUME_ROLE`, `WEB_IDENTITY_TOKEN`). No `.env` files or hardcoded secrets in codebase. Grep scan for `password=`, `secret=` returned no results.
- **Gap**: N/A — clean credential management.
- **Recommendation**: Document that `BASIC` credential provider should be avoided in production.
- **Evidence**: `AWSConfigConstants.java`, `AWSGeneralUtil.java`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY, but has_auth_surface=false AND has_write_operations=false → INFO
- **Finding**: System does not execute agent-invoked write operations — audit logging is consumer responsibility. AWS CloudTrail captures all API calls at the service level.
- **Gap**: N/A — audit logging exists at the AWS platform layer (CloudTrail).
- **Recommendation**: Ensure CloudTrail is enabled in all accounts where connectors operate.
- **Evidence**: `AWSClientUtil.java` (standard AWS SDK calls are CloudTrail-logged)

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: System does not issue or enforce agent identities — suspension is consumer responsibility. IAM roles/keys can be suspended via standard AWS IAM controls.
- **Gap**: N/A — identity lifecycle managed at IAM/STS layer.
- **Recommendation**: No action needed.
- **Evidence**: `AWSConfigConstants.java`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY, but has_write_operations=false AND has_http_rpc_surface=false AND stateless-utility archetype → INFO
- **Finding**: System exposes no write operations in the agent context. Flink's checkpointing mechanism provides exactly-once semantics and rollback at the framework level.
- **Gap**: N/A — compensation handled by Flink runtime.
- **Recommendation**: No action needed.
- **Evidence**: `KinesisStreamsSource.java` (checkpoint state serialization), `DynamoDbStreamsSource.java`

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
- **Finding**: Read-only agents do not perform writes. Flink handles concurrent shard processing via split-based parallelism. DynamoDB sink supports `overwriteByPartitionKeys` for deduplication.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action needed.
- **Evidence**: `DynamoDbSinkWriter.java`, `KinesisStreamsSource.java`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: INFO
- **Finding**: Extended question triggered (connectors call external AWS services). Base severity: RISK-SAFETY. **Dev-library-application downgrade to INFO**: The RISK-SAFETY rationale ("Runaway agent loops cascade through dependencies") presupposes an agent-callable surface (`has_http_rpc_surface`) through which agent traffic reaches the system. Since `has_http_rpc_surface` is `false`, there is no agent-to-system call path for cascading failures. Circuit-breaker responsibility belongs to the consuming application. The connectors implement robust retry and resilience patterns: `KinesisStreamsSource` uses `StandardRetryStrategy` with exponential backoff and half-jitter, `DynamoDbStreamsSource` uses `AdaptiveRetryStrategy`, and all sink writers use `FatalExceptionClassifier` chains distinguishing retryable from fatal errors.
- **Gap**: No standalone circuit breaker pattern (e.g., Resilience4j). Retry logic is via AWS SDK retry strategies — functionally equivalent for this use case. Circuit-breaker enforcement for agent traffic is the consuming application's responsibility.
- **Recommendation**: No action needed at the library level. Consuming applications exposing these connectors to agents should implement circuit breakers at their service layer.
- **Evidence**: `KinesisStreamsSource.java` (createExpBackoffRetryStrategyBuilder), `DynamoDbStreamsSource.java` (AdaptiveRetryStrategy), `DynamoDbSinkWriter.java`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — API-layer rate limiting is not applicable. AWS service-level throttling handled by connector retry logic.
- **Gap**: N/A — libraries inherit consumer rate limiting.
- **Recommendation**: No action needed.
- **Evidence**: `KinesisStreamsSource.java` (LimitExceededException retry)

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agents cannot modify data. Flink async sink framework provides configurable batch limits (`maxBatchSize`, `maxInFlightRequests`, `maxBufferedRequests`).
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action needed.
- **Evidence**: `DynamoDbSinkWriter.java` (AsyncSinkWriterConfiguration), `SqsSinkWriter.java`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agents do not make state changes. Connectors are data pipeline libraries with no application-level state machines or approval workflows.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action needed.
- **Evidence**: No draft/pending patterns found — expected for library connectors.

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agents do not execute write operations. Connectors do not implement approval workflows — they are data transport libraries.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action needed.
- **Evidence**: No approval patterns found — expected for library connectors.

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: Dev-library-application override applies. Libraries do not own staging environments. The repository provides local testing via E2E tests using testcontainers and a real Flink distribution. `flink-connector-aws-e2e-tests` contains 5 e2e test modules (Kinesis Streams, Kinesis Firehose, SQS, Avro Glue Schema Registry, JSON Glue Schema Registry).
- **Gap**: N/A — staging is consumer responsibility. Local testing capability is excellent.
- **Recommendation**: No action needed.
- **Evidence**: `flink-connector-aws-e2e-tests/README.md`, `flink-connector-aws-e2e-tests/pom.xml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Dev-library-application override → INFO. Connectors are data transport layers — they do not own or inspect data. No PII/PHI/financial/credential data is stored, processed, or logged by the library. Data flows through as opaque byte arrays or AWS SDK record objects.
- **Gap**: N/A — data classification is consumer responsibility.
- **Recommendation**: No action needed.
- **Evidence**: `KinesisStreamsRecordEmitter.java`, `DynamoDbStreamsRecordEmitter.java`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY, but has_persistent_data_store=false AND has_logging_of_user_data=false → INFO
- **Finding**: No persistent data store and no user-data logging. Data residency enforced by AWS service endpoints and `aws.region` configuration.
- **Gap**: N/A — residency controlled at AWS service level.
- **Recommendation**: No action needed.
- **Evidence**: `AWSConfigConstants.java` (`AWS_REGION`), `AWSGeneralUtil.java` (getRegion)

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
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`. Archetype calibration for stateless-utility → INFO if evaluated.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: System does not log user data and holds no user data — PII-in-logs risk is not applicable. Stateless-utility archetype → INFO. Logging is diagnostic only (SLF4J): batch sizes, error counts, shard IDs. Example: `LOG.warn("DynamoDB Sink failed to persist and will retry {} entries.", requestEntries.size(), err)`.
- **Gap**: Minor observation: `SqsSinkWriter.java` logs `requestEntries.get(0).toString()` on failure, which could include message body. However, this is controlled by consumer data and occurs only on error paths.
- **Recommendation**: Consider replacing `requestEntries.get(0).toString()` with a size-only log message for defense-in-depth PII protection.
- **Evidence**: `DynamoDbSinkWriter.java`, `SqsSinkWriter.java`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality scoring exists at connector level — expected for transport libraries. Kinesis source exposes `millisBehindLatest` metric for freshness/lag indication.
- **Gap**: N/A — data quality is a consumer concern.
- **Recommendation**: No action needed.
- **Evidence**: `KinesisShardMetrics.java` (millisBehindLatest), `MetricConstants.java`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: The connectors use Flink's `@Experimental` annotation on public API classes (e.g., `KinesisStreamsSource`, `DynamoDbStreamsSource`, `KinesisStreamsSourceBuilder`), indicating the API surface is not yet stable. Internal serializers use versioned serialization (e.g., `KinesisShardSplitSerializer` with `CURRENT_VERSION = 2` and `COMPATIBLE_VERSIONS = {0, 1, 2}`, `DynamoDbStreamsSourceEnumeratorStateSerializer` with `CURRENT_VERSION = 0`). Maven version is `6.0-SNAPSHOT`. No breaking change detection tooling is integrated into the CI pipeline.
- **Gap**: No automated breaking change detection in CI. Agent tool bindings could break silently when library versions change. `@Experimental` signals instability but does not prevent breaking changes from shipping.
- **Recommendation**: Integrate API binary compatibility checking (e.g., `japicmp-maven-plugin` or Revapi) into the CI pipeline to detect breaking changes to `@PublicEvolving` and `@Public` annotated classes before release.
- **Evidence**: `KinesisStreamsSource.java` (`@Experimental`), `KinesisShardSplitSerializer.java` (versioned serialization), `.github/workflows/common.yml`, `pom.xml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Configuration names are clear: `aws.region`, `aws.credentials.provider`, `aws.http-client.max-concurrency`. Java class names are descriptive: `KinesisStreamsSource`, `DynamoDbSinkWriter`. Metric names are semantic: `millisBehindLatest`, `KinesisStreamSource`, `stream`, `shardId`.
- **Gap**: N/A — naming is self-documenting.
- **Recommendation**: No action needed.
- **Evidence**: `AWSConfigConstants.java`, `MetricConstants.java`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. Connectors are transport libraries. AWS Glue Schema Registry integration (`flink-formats-aws`) provides schema registry support for Avro and JSON formats, enabling schema discovery for consumers.
- **Gap**: N/A — catalog is consumer concern.
- **Recommendation**: No action needed.
- **Evidence**: `flink-formats-aws/flink-avro-glue-schema-registry/`, `flink-formats-aws/flink-json-glue-schema-registry/`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: Library/utility — tracing and correlation are consumer concerns. Connectors use SLF4J for logging. No OpenTelemetry or X-Ray instrumentation embedded. Flink's metrics framework provides observability hooks.
- **Gap**: N/A — tracing pipeline is consumer concern.
- **Recommendation**: Consider adding OpenTelemetry context propagation support in future versions.
- **Evidence**: `KinesisShardMetrics.java`, SLF4J usage across all modules

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Library/utility — alerting is a consumer concern. Connectors expose Flink metrics (`numRecordsSendErrorsCounter`, `numRecordsSendPartialFailure`, `millisBehindLatest`) for consumers to configure alerts.
- **Gap**: N/A — library provides signals, consumers set thresholds.
- **Recommendation**: Document recommended alerting thresholds per metric.
- **Evidence**: `DynamoDbSinkWriter.java`, `KinesisShardMetrics.java`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Connectors publish operational metrics via Flink: `millisBehindLatest`, `numRecordsSendErrorsCounter`, `numRecordsSendPartialFailure`. Business outcome metrics are consumer responsibility.
- **Gap**: N/A — business metrics are consumer concern.
- **Recommendation**: No action needed.
- **Evidence**: `KinesisShardMetrics.java`, `DynamoDbSinkWriter.java`, `SqsSinkWriter.java`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: N/A
- **Finding**: This is a `library` repository (dev-library-application override). This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: N/A
- **Finding**: This is a `library` repository (dev-library-application override). This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q3: Rollback Capability
- **Severity**: N/A
- **Finding**: This is a `library` repository (dev-library-application override). This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q4: API Test Coverage
- **Severity**: N/A
- **Finding**: This is a `library` repository (dev-library-application override). This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: N/A
- **Finding**: This is a `library` repository (dev-library-application override). This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java` | API-Q2, AUTH-Q1, AUTH-Q2, AUTH-Q5, AUTH-Q6, AUTH-Q7, DATA-Q2, DISC-Q2 |
| `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/util/AWSGeneralUtil.java` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q5, DATA-Q2 |
| `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/util/AWSClientUtil.java` | AUTH-Q1, AUTH-Q3, AUTH-Q4, AUTH-Q6 |
| `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/sink/throwable/AWSExceptionClassifierUtil.java` | API-Q3 |
| `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/KinesisStreamsSource.java` | API-Q2, API-Q8, AUTH-Q3, STATE-Q1, STATE-Q4, STATE-Q5 |
| `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/KinesisStreamsSourceBuilder.java` | API-Q1 |
| `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/split/KinesisShardSplitSerializer.java` | DISC-Q1 |
| `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/metrics/KinesisShardMetrics.java` | DATA-Q7, OBS-Q1, OBS-Q2, OBS-Q3 |
| `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/metrics/MetricConstants.java` | DATA-Q7, DISC-Q2 |
| `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/exception/KinesisStreamsSourceException.java` | API-Q3 |
| `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbSinkWriter.java` | API-Q3, API-Q4, AUTH-Q3, STATE-Q3, STATE-Q4, STATE-Q6, DATA-Q6, OBS-Q2, OBS-Q3 |
| `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/source/DynamoDbStreamsSource.java` | STATE-Q1, STATE-Q4 |
| `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/source/DynamoDbStreamsSourceBuilder.java` | API-Q1 |
| `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/source/enumerator/DynamoDbStreamsSourceEnumeratorStateSerializer.java` | DISC-Q1 |
| `flink-connector-aws/flink-connector-sqs/src/main/java/org/apache/flink/connector/sqs/sink/SqsSinkWriter.java` | API-Q3, STATE-Q6, DATA-Q6, OBS-Q3 |
| `flink-connector-aws/flink-connector-sqs/src/main/java/org/apache/flink/connector/sqs/sink/SqsSinkException.java` | API-Q3 |
| `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/reader/KinesisStreamsRecordEmitter.java` | API-Q5, DATA-Q1 |
| `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/source/reader/DynamoDbStreamsRecordEmitter.java` | API-Q5, DATA-Q1 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/push_pr.yml` | DISC-Q1, ENG-Q1 (INFO), ENG-Q2 (INFO) |
| `.github/workflows/common.yml` | DISC-Q1, ENG-Q2 (INFO), ENG-Q4 (INFO) |
| `.github/workflows/nightly.yml` | ENG-Q2 (INFO) |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `pom.xml` | DISC-Q1, ENG-Q3 (INFO) |
| `flink-connector-aws-e2e-tests/pom.xml` | HITL-Q3 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `.asf.yaml` | ENG-Q1 (INFO) |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| `docs/content/docs/connectors/datastream/kinesis.md` | API-Q1 |
| `docs/content/docs/connectors/datastream/dynamodb.md` | API-Q1 |
| `docs/content/docs/connectors/datastream/sqs.md` | API-Q1 |
| `docs/content/docs/connectors/datastream/firehose.md` | API-Q1 |
| `flink-connector-aws-e2e-tests/README.md` | HITL-Q3 |

### Format Libraries
| File | Questions Referenced |
|------|---------------------|
| `flink-formats-aws/flink-avro-glue-schema-registry/` | DISC-Q3 |
| `flink-formats-aws/flink-json-glue-schema-registry/` | DISC-Q3 |
