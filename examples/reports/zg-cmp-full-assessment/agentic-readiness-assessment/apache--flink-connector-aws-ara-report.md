# Agentic Readiness Assessment Report

**Target**: apache/flink-connector-aws
**Date**: 2026-04-29
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: monorepo
**Service Archetype**: library (unified assessment — auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, streaming, flink, aws
**Context**: Apache Flink connectors for AWS services (Kinesis, DynamoDB, SQS, etc.)

**Archetype Justification**: All modules in this monorepo are connector libraries (JAR artifacts) consumed by downstream Apache Flink applications. No module has its own deployment infrastructure, API surface, or operational characteristics — they expose Java programmatic APIs, not REST/GraphQL endpoints. The repository is assessed as a unified library ecosystem since all modules share the same build system, CI/CD pipeline, security model, and base library (`flink-connector-aws-base`).

> **Important Context**: This repository is a collection of Apache Flink connector libraries, not a deployable service. Agents would not call these connectors directly — they would interact with Flink applications that embed these connectors. Many assessment questions are evaluated against the library's design-time properties (what controls exist in the code) rather than runtime behavior. Findings should be interpreted in this context.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 5 | **RISK-QUALITY**: 10 | **INFOs**: 17

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days. Both BLOCKERs relate to the library's lack of a direct agent-consumable API surface and absence of sensitive data classification — areas where the consuming application must provide these controls.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 5 |
| RISK-QUALITY | 10 |
| INFO | 17 |
| N/A | 0 |
| Not Evaluated (extended) | 11 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 8
**Extended Questions Not Triggered**: 11
**Questions N/A (repo_type: monorepo)**: 0
**Service Archetype**: library (auto-detected, unified assessment)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### API-Q1: Documented API Interface

- **Severity**: BLOCKER
- **Finding**: The connectors expose programmatic Java APIs (builder patterns such as `KinesisStreamsSinkBuilder`, `DynamoDbSinkBuilder`, `SqsSinkBuilder`, `KinesisStreamsSourceBuilder`, `DynamoDbStreamsSourceBuilder`) consumed via Flink's DataStream and Table APIs. No REST, GraphQL, or AsyncAPI interfaces exist. No HTTP server, no API Gateway, no REST endpoints. Integration requires embedding these libraries in a JVM application and invoking them programmatically.
- **Gap**: There is no agent-consumable API interface (REST, GraphQL, AsyncAPI). Agents cannot call Java builder patterns directly. An intermediate API layer (e.g., a REST wrapper or MCP server) would need to be built to expose these connector capabilities to agents.
- **Remediation**:
  - **Immediate**: Build a thin REST or MCP server wrapper around the connector libraries that exposes connector configuration and management operations as HTTP endpoints.
  - **Target State**: A documented REST/MCP API surface exists that agents can consume to configure, deploy, and manage Flink connector jobs.
  - **Estimated Effort**: High — requires creating a new application layer.
  - **Dependencies**: None
- **Evidence**: `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbSinkBuilder.java`, `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/KinesisStreamsSourceBuilder.java`, `docs/content/docs/connectors/datastream/kinesis.md`

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: The connector libraries pass data through — they serialize/deserialize records to/from AWS services (Kinesis, DynamoDB, SQS, Firehose) but do not classify, tag, or enforce access controls on data content. No data classification tags, no field-level encryption, no PII detection. The `DynamoDbWriteRequest` carries raw `Map<String, AttributeValue>` items. The `KinesisDeserializationSchema` processes raw byte arrays. Data classification is entirely the responsibility of the consuming application.
- **Gap**: No mechanism exists within the library to classify sensitive data (PII, PHI, financial records, credentials) at the field level or prevent an agent from retrieving it without explicit authorization. Since this is a library, the consuming application must implement these controls, but the library provides no hooks or interfaces to facilitate data classification.
- **Remediation**:
  - **Immediate**: Document data classification requirements for downstream consumers. Provide guidance on implementing field-level encryption using AWS SDK features (e.g., DynamoDB client-side encryption).
  - **Target State**: Library provides optional hooks (e.g., a `DataClassifier` interface) or documentation guiding consumers to classify and protect sensitive data fields before they pass through the connectors.
  - **Estimated Effort**: Medium
  - **Dependencies**: None
- **Evidence**: `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbWriteRequest.java`, `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/serialization/KinesisDeserializationSchema.java`

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The library does not implement IAM policy scoping — it delegates to whatever `AwsCredentialsProvider` is configured. The `AWSGeneralUtil.getCredentialsProvider()` method accepts any configured credential type without validating whether the credentials are scoped to least privilege. The library cannot distinguish between an agent identity with read-only access and one with full administrative access.
- **Gap**: No mechanism within the library to validate or enforce that configured credentials follow least-privilege principles. Scoped permissions are entirely the responsibility of the deploying application's IAM configuration.
- **Compensating Controls**:
  - Enforce least-privilege IAM policies at the AWS account level for any role used by agents interacting with applications built on these connectors.
  - Use `ASSUME_ROLE` credential provider with a narrowly-scoped IAM role rather than `BASIC` credentials.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document IAM policy templates for common connector use cases (e.g., Kinesis read-only, DynamoDB write-only) to guide consumers in configuring least-privilege access.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/util/AWSGeneralUtil.java`, `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java`

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No audit logging configuration exists within the library. The library does not log the authenticated principal for any operation. Logging is configured via Log4j2 with a simple `PatternLayout` (`%d{HH:mm:ss,SSS} %-5p %-60c %x - %m%n`) that does not include caller identity, request IDs, or principal attribution. CloudTrail logging would be configured at the AWS account level, not in the connector library. The library's log messages (e.g., in `DynamoDbSinkWriter`) log record counts and error details but not the authenticated identity.
- **Gap**: No immutable, tamper-evident audit log that records the authenticated principal for operations performed through these connectors. The library delegates entirely to AWS CloudTrail at the account level.
- **Compensating Controls**:
  - Ensure AWS CloudTrail is enabled and configured with log file validation in all accounts where these connectors run.
  - Configure CloudTrail S3 bucket with object lock for immutability.
- **Remediation Timeline**: 30–60 days (at the AWS account/platform level)
- **Recommendation**: Document CloudTrail requirements as a prerequisite for agent-enabled deployments. Consider adding structured logging with principal identity fields to the connector's log output.
- **Evidence**: `flink-connector-aws-base/src/main/resources/log4j2.properties`, `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbSinkWriter.java`

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The library supports configuring `AWS_REGION` via `AWSConfigConstants.AWS_REGION`, which determines where data is sent/retrieved. The `AWSGeneralUtil.getRegion()` method extracts the region from properties. For Kinesis source, the region is derived from the stream ARN. No data residency enforcement mechanism exists in the library — it will send data to whichever region is configured without validating compliance constraints.
- **Gap**: No data residency enforcement. The library does not validate whether configured regions comply with data sovereignty requirements (GDPR, LGPD, etc.). An agent or misconfigured application could transmit data to a non-compliant region.
- **Compensating Controls**:
  - Enforce region constraints through IAM policies with `aws:RequestedRegion` condition keys.
  - Implement organization-level Service Control Policies (SCPs) restricting allowed AWS regions.
- **Remediation Timeline**: 30–60 days (at the AWS account/platform level)
- **Recommendation**: Document data residency considerations for consumers. Consider adding a `ValidRegions` configuration option that restricts which regions the connectors can target.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java` (AWS_REGION constant), `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/util/AWSGeneralUtil.java` (getRegion method)

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The connectors use Flink's `AsyncSinkWriter` pattern which handles buffering and retries for failed writes. `DynamoDbSinkWriter` retries unprocessed items from `BatchWriteItemResponse`. `KinesisStreamsSinkWriter` and `KinesisFirehoseSinkWriter` follow similar retry patterns. However, no saga, compensation, or rollback patterns exist. The connectors write forward only — if step 3 of a 5-step operation fails, steps 1 and 2 cannot be undone. Flink's checkpointing provides at-least-once guarantees (re-processing from the last checkpoint on failure) but does not provide application-level compensation.
- **Gap**: No compensation or rollback mechanism for multi-step operations. Write operations are fire-and-retry, not compensatable.
- **Compensating Controls**:
  - Flink's checkpointing mechanism provides exactly-once processing semantics for source-side operations and at-least-once for sinks, serving as a partial mitigation.
  - Scope agent interactions to read-only operations initially to avoid partial state issues.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: For write-enabled agent use cases, implement compensating transactions at the application layer wrapping these connectors.
- **Evidence**: `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbSinkWriter.java` (handlePartiallyUnprocessedRequest, handleFullyFailedRequest methods)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, Swagger, GraphQL schema, or Smithy model exists in the repository. The API surface is defined by Java class interfaces annotated with `@PublicEvolving` and `@Internal` (Flink annotation framework). Documentation exists as Markdown files in `docs/content/docs/connectors/` with code examples for each connector (Kinesis, DynamoDB, SQS, Firehose).
- **Gap**: No machine-readable specification that agent frameworks could use to auto-generate tool definitions. Integration requires manual tool authoring from Java source or documentation.
- **Compensating Controls**:
  - Use the comprehensive Markdown documentation in `docs/` to manually author agent tool definitions.
  - Generate Javadoc as a structured reference for tool building.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: If an API wrapper is built (per API-Q1 remediation), generate an OpenAPI spec for it. For the library itself, consider publishing a machine-readable capability manifest.
- **Evidence**: `docs/content/docs/connectors/datastream/kinesis.md`, `docs/content/docs/connectors/datastream/dynamodb.md`, `docs/content/docs/connectors/datastream/sqs.md`, `docs/content/docs/connectors/datastream/firehose.md`

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The library implements structured exception classification via `AWSExceptionHandler`, `FatalExceptionClassifier`, and service-specific classifiers. `DynamoDbSinkWriter` classifies exceptions into fatal (non-retryable) categories: `ResourceNotFoundException`, `ConditionalCheckFailedException`, `ValidationException`, `StsException` (invalid credentials), and `SdkClientException` (misconfigured client). The `AWSExceptionClassifierUtil.withAWSServiceErrorCode()` method classifies based on `AwsErrorDetails.errorCode()`. This provides a clear retryable-vs-fatal distinction.
- **Gap**: While the library has internal structured exception handling, it does not expose structured error codes or error bodies in a format consumable by external agents. Exceptions are Java-level, not HTTP-level. No error code enumeration or error response schema is published.
- **Compensating Controls**:
  - Document the exception hierarchy and error classification logic for consumers building agent-facing wrappers.
  - The existing `FatalExceptionClassifier` chain can be leveraged by wrapper applications to provide structured error responses.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Publish the exception classification taxonomy as part of the library's public documentation.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/sink/throwable/AWSExceptionHandler.java`, `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/sink/throwable/AWSExceptionClassifierUtil.java`, `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbSinkWriter.java`

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The library does not implement action-level authorization. It passes credentials through to AWS SDK calls. Authorization is enforced by AWS service-side IAM policies. For example, DynamoDB IAM policies can distinguish between `dynamodb:PutItem` and `dynamodb:DeleteItem` actions. The library's `DynamoDbSinkWriter` supports both PUT and DELETE operations via `DynamoDbWriteRequestType`, but authorization is AWS-side, not library-side.
- **Gap**: The library itself has no mechanism to restrict an agent to read-only operations if the configured IAM credentials allow write access. Authorization enforcement is delegated entirely to AWS IAM.
- **Compensating Controls**:
  - Configure AWS IAM policies with action-level restrictions (e.g., allow `kinesis:GetRecords` but deny `kinesis:PutRecord`).
  - Use separate IAM roles for read vs. write connector instances.
- **Remediation Timeline**: 30 days (IAM policy configuration)
- **Recommendation**: Document recommended IAM policy templates with action-level restrictions for each connector type.
- **Evidence**: `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbWriteRequestType.java`, `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/util/AWSClientUtil.java`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The library uses Flink's `@PublicEvolving` and `@Internal` annotations to signal API stability levels. ArchUnit tests enforce architecture constraints across all connector modules (archunit-violations directories exist in each module). No formal schema versioning, no OpenAPI diff, no consumer-driven contract testing (Pact), and no breaking change detection tools. URL-based versioning is not applicable (no HTTP APIs). The project version is `6.0-SNAPSHOT` following Maven versioning.
- **Gap**: No automated breaking change detection for the Java API surface. Agent tool bindings built against this library could break silently when API signatures change between versions.
- **Compensating Controls**:
  - ArchUnit tests provide some structural stability guarantees.
  - The `@PublicEvolving` annotation signals that annotated APIs may change between minor versions, providing a manual stability signal.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add binary compatibility checks (e.g., `japicmp-maven-plugin` or `revapi-maven-plugin`) to the CI pipeline to detect breaking API changes automatically.
- **Evidence**: `flink-connector-aws-base/src/test/resources/archunit.properties`, `flink-connector-aws-base/archunit-violations/`, `pom.xml` (version 6.0-SNAPSHOT)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing instrumentation (X-Ray, OpenTelemetry) exists in the library. Logging uses SLF4J with Log4j2 backend. The log4j2.properties configuration uses `PatternLayout` (`%d{HH:mm:ss,SSS} %-5p %-60c %x - %m%n`) — not structured JSON. No `trace_id`, `request_id`, or `correlation_id` fields in log output. The library exposes Flink-native metrics (`KinesisShardMetrics`, `DynamoDbStreamsShardMetrics`) with `millisBehindLatest` gauges and `numRecordsSendErrors` / `numRecordsSendPartialFailure` counters, but these are Flink metrics, not distributed traces.
- **Gap**: No distributed tracing for agent-initiated requests through the connectors. Log output is unstructured. Debugging agent-initiated failures requires correlating Flink metrics and AWS CloudTrail logs manually.
- **Compensating Controls**:
  - Flink's built-in metric system provides operational visibility at the connector level.
  - AWS X-Ray can be enabled at the AWS SDK level by the consuming application.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Consider adding OpenTelemetry instrumentation or X-Ray SDK integration as an optional feature. Switch to structured JSON logging format.
- **Evidence**: `flink-connector-aws-base/src/main/resources/log4j2.properties`, `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/metrics/KinesisShardMetrics.java`, `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/metrics/MetricConstants.java`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration exists in the library. The connectors expose Flink metrics (`numRecordsSendErrors`, `numRecordsSendPartialFailure`, `millisBehindLatest`) that could be used as input for alerting, but no CloudWatch alarms, PagerDuty integration, or SLO-based alerting is configured. Alerting is the responsibility of the deploying application's monitoring stack.
- **Gap**: No pre-configured alerting for error rates or latency degradation. Consumers must set up their own alerting based on Flink metrics.
- **Compensating Controls**:
  - Flink's metric system can be integrated with external monitoring tools (Prometheus, CloudWatch, Datadog).
  - The `millisBehindLatest` metric provides a ready-made signal for latency alerting.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document recommended alerting thresholds and CloudWatch alarm configurations for each connector type.
- **Evidence**: `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/metrics/MetricConstants.java`, `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/source/metrics/MetricConstants.java`

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The repository has a GitHub Actions CI/CD pipeline (`.github/workflows/push_pr.yml`, `common.yml`, `nightly.yml`) that runs on push/PR with `mvn clean install` including unit tests and e2e tests (LocalStack-based and optional real-AWS tests). ArchUnit tests enforce code architecture constraints. However, there is no API contract testing (no Pact, no OpenAPI validation, no breaking change detection). The pipeline tests functionality but does not catch API-breaking changes systematically.
- **Gap**: No automated detection of breaking changes in the public Java API. An API change that breaks agent tool bindings would not be caught by the CI pipeline.
- **Compensating Controls**:
  - ArchUnit tests provide structural constraints as a partial mitigation.
  - The `@PublicEvolving` annotation regime provides a manual stability contract.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `japicmp-maven-plugin` or `revapi-maven-plugin` to the Maven build to detect binary-incompatible API changes.
- **Evidence**: `.github/workflows/push_pr.yml`, `.github/workflows/common.yml`, `flink-connector-aws-base/src/test/resources/archunit.properties`

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The e2e tests use Testcontainers with a custom `LocalstackContainer` class that provides mock AWS services for local testing. The CI pipeline runs both LocalStack-based e2e tests and optional real-AWS tests (gated by credentials). No separate staging or sandbox environment configuration exists beyond the test infrastructure. The LocalStack-based testing provides production-equivalent service mocks but is test-scoped — not a persistent staging environment.
- **Gap**: No persistent staging or sandbox environment for agents to test against. The LocalStack infrastructure exists only during test execution.
- **Compensating Controls**:
  - LocalStack-based test infrastructure can be extended to provide a persistent sandbox for agent testing.
  - AWS provides free-tier services that can serve as a low-risk testing environment.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a persistent LocalStack-based sandbox environment for agent integration testing.
- **Evidence**: `flink-connector-aws-base/src/test/java/org/apache/flink/connector/aws/testutils/LocalstackContainer.java`, `.github/workflows/common.yml`

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: DynamoDB sink supports `overwriteByPartitionKeys` for batch deduplication within the sink buffer. Kinesis sink uses partition keys for record placement. These provide partial idempotency but are not full idempotency-key patterns.
- **Implication**: When expanding to write-enabled agent scope, full idempotency support will need to be assessed more rigorously. The existing deduplication is a good foundation.
- **Recommendation**: For future write-enabled scope, implement idempotency keys at the application layer wrapping these connectors.
- **Evidence**: `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbSinkBuilder.java` (setOverwriteByPartitionKeys)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: The connectors process binary/serialized data — byte arrays (`byte[]`) and Java objects. Input records are serialized via `SerializationSchema` implementations. Output records are deserialized via `DeserializationSchema` or `KinesisDeserializationSchema`. Supported formats include JSON (via `SimpleStringSchema`, `JsonSerializationSchema`), Avro (via Glue Schema Registry integration), and custom formats. The data format is determined by the consuming application, not the library.
- **Implication**: Agents consuming data through applications built with these connectors would receive data in whatever format the application configures. JSON is the most agent-friendly option.
- **Recommendation**: When building agent-facing wrappers, prefer JSON serialization schemas for LLM-compatible output.
- **Evidence**: `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/serialization/KinesisDeserializationSchema.java`, `docs/content/docs/connectors/datastream/kinesis.md` (Deserialization Schema section)

### AUTH-Q1: Machine Identity Authentication

- **Severity**: INFO (capability present — library supports machine identity through AWS credential providers)
- **Finding**: The library explicitly supports machine identity authentication through the `AWSConfigConstants.CredentialProvider` enum: `ASSUME_ROLE` (STS role assumption), `WEB_IDENTITY_TOKEN` (Kubernetes/EKS pod identity), `AUTO` (default credential chain including EC2/ECS instance roles), and `CUSTOM` (user-provided credential class). Principal attribution is handled by AWS CloudTrail at the account level — the library itself does not log principal identity but the underlying AWS SDK API calls will be recorded in CloudTrail with the caller's identity.
- **Implication**: Machine identity is well-supported at the AWS SDK level. Agent identities can be configured as IAM roles with `ASSUME_ROLE` credential provider.
- **Recommendation**: Use `ASSUME_ROLE` or `WEB_IDENTITY_TOKEN` credential providers for agent-operated connector instances to ensure clear identity attribution.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java` (CredentialProvider enum), `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/util/AWSGeneralUtil.java` (getCredentialsProvider method)

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO (library archetype — stateless-utility/data-gateway calibration applies)
- **Finding**: No identity propagation patterns in the library. The connectors authenticate directly to AWS services using configured credentials. There is no concept of "user context" or "on-behalf-of" flows — the library operates as a single-identity data pipeline component.
- **Implication**: If agents need to act on behalf of different users, the application layer must manage identity context. The library treats all operations as service-to-service calls.
- **Recommendation**: For multi-tenant agent use cases, implement identity context at the application layer and configure separate connector instances with different IAM roles per tenant.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/util/AWSClientUtil.java`

### AUTH-Q5: Credential Management

- **Severity**: INFO (library supports secure credential patterns but also allows insecure ones)
- **Finding**: The library supports multiple credential provider types. The `BASIC` type accepts access key ID and secret key as configuration properties, which could be hardcoded. However, more secure alternatives are available and documented: `ENV_VAR`, `SYS_PROP`, `PROFILE`, `ASSUME_ROLE`, `WEB_IDENTITY_TOKEN`, `AUTO`, and `CUSTOM`. The documentation in `docs/content/docs/connectors/datastream/kinesis.md` explicitly shows `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in example code (as placeholder values). No Secrets Manager or Vault integration exists within the library, but `CUSTOM` credential providers could integrate with these systems.
- **Implication**: The library provides the hooks for secure credential management but does not enforce it. Consumers using `BASIC` credentials could hardcode secrets.
- **Recommendation**: Deprecate or add warnings for `BASIC` credential provider usage. Document best practices for using `ASSUME_ROLE` with Secrets Manager-backed credential rotation.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java`, `docs/content/docs/connectors/datastream/kinesis.md`

### AUTH-Q7: Agent Identity Suspension

- **Severity**: INFO (library delegates to AWS IAM — suspension capability exists at platform level)
- **Finding**: No identity suspension mechanism within the library. Identity management (creation, suspension, revocation) is handled at the AWS IAM level. IAM roles can be deactivated, API keys can be deleted, and STS sessions can be invalidated — all outside the library's scope.
- **Implication**: Agent identity suspension is possible through AWS IAM operations but requires platform-level tooling, not library-level changes.
- **Recommendation**: Ensure IAM role deactivation and session revocation procedures are documented for agent identities used with these connectors.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java` (credential provider configuration)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: DynamoDB sink supports `overwriteByPartitionKeys` for within-batch deduplication. No optimistic locking (ETags, version fields, `If-Match` headers) or pessimistic locking in the library. DynamoDB conditional writes are supported by the underlying SDK but not exposed through the connector's API.
- **Implication**: For read-only agents, concurrency controls are not a concern. If expanding to write-enabled scope, concurrency controls must be implemented at the application layer.
- **Recommendation**: For future write-enabled scope, consider exposing DynamoDB conditional writes through the connector API.
- **Evidence**: `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbSinkWriter.java`

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: INFO (library provides configurable concurrency but is not an API-layer rate limiter — assessed as INFO for library context)
- **Finding**: The HTTP client max concurrency is configurable via `AWSConfigConstants.HTTP_CLIENT_MAX_CONCURRENCY`. The `AsyncSinkWriter` provides `maxInFlightRequests`, `maxBatchSize`, and `maxBufferedRequests` configuration that limits throughput. For Kinesis source, the `KinesisStreamsSource` uses exponential backoff retry strategies with configurable min/max delay and max attempts. These are throughput controls, not rate limiters in the traditional API sense.
- **Implication**: The library provides throughput knobs that can prevent overwhelming AWS services, but these are client-side controls, not server-side rate limiters.
- **Recommendation**: Document recommended concurrency settings for agent-operated connector instances to prevent runaway traffic.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java` (HTTP_CLIENT_MAX_CONCURRENCY), `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbSinkBuilder.java` (DEFAULT_MAX_IN_FLIGHT_REQUESTS)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `AsyncSinkWriter` provides configurable limits: `maxBatchSize` (DynamoDB default: 25), `maxBufferedRequests` (default: 10000), `maxBatchSizeInBytes`, `maxRecordSizeInBytes`, and `maxTimeInBufferMS` (default: 5000ms). These are per-instance batch limits, not per-agent transaction limits. No per-identity or per-session transaction caps exist.
- **Implication**: For read-only agents, blast radius is limited to read throughput. For future write-enabled scope, per-agent transaction limits should be implemented at the application layer.
- **Recommendation**: For future write-enabled scope, implement per-agent transaction limits at the wrapper application level.
- **Evidence**: `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbSinkBuilder.java`

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft/pending state patterns in the library. The connectors write directly to AWS services. There is no concept of staging writes before committing them.
- **Implication**: For read-only agents, draft states are not relevant. For future write-enabled scope, draft states should be implemented at the application layer.
- **Recommendation**: For write-enabled use cases, implement a staging layer between the agent and the sink connectors.
- **Evidence**: No evidence found — absence is itself a finding.

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval gate mechanisms in the library. All operations execute immediately when invoked.
- **Implication**: For read-only agents, approval gates are not relevant. For future write-enabled scope, approval gates should be implemented at the orchestration layer.
- **Recommendation**: For write-enabled use cases, implement approval workflows in the agent orchestration layer.
- **Evidence**: No evidence found — absence is itself a finding.

### DATA-Q6: PII Redaction in Logs

- **Severity**: INFO (assessed as INFO because the library's logging does not log raw record data, reducing the PII leakage risk)
- **Finding**: The library uses SLF4J with Log4j2. Log messages in `DynamoDbSinkWriter` log record counts and error details (e.g., `"DynamoDB Sink failed to persist and will retry {} entries."`) but do not log raw record data, attribute values, or payloads. No explicit PII redaction middleware or log scrubbing exists. The `log4j2.properties` root logger level is set to `OFF` in the library's main resources, meaning the library does not produce logs by default — the consuming application controls log levels.
- **Implication**: Low risk of PII leakage through the library's own log statements. However, at DEBUG level, exception stack traces could include data fragments.
- **Recommendation**: Add explicit documentation warning consumers not to enable DEBUG logging in production when processing PII data.
- **Evidence**: `flink-connector-aws-base/src/main/resources/log4j2.properties`, `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbSinkWriter.java`

### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The repository contains 147 test Java source files including unit tests for each connector module (`DynamoDbSinkWriterTest`, `KinesisStreamsSinkWriterTest`, `SqsSinkWriterTest`, etc.), integration tests (`DynamoDbSinkITCase`, `KinesisStreamsSinkITCase`, `KinesisStreamsSourceITCase`), e2e tests (`KinesisFirehoseTableITTest`, `SqsSinkITTest`), architecture tests (`TestCodeArchitectureTest`), and packaging tests (`PackagingITCase`). No API contract tests exist (no Pact, no OpenAPI validation), meaning API signature changes could go undetected.
- **Gap**: No formal contract tests to validate API compatibility. Functional test coverage is good but does not test for breaking API changes.
- **Compensating Controls**:
  - Existing comprehensive functional test suite reduces the risk of behavioral regressions.
  - ArchUnit architecture tests provide structural constraints.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `japicmp-maven-plugin` for binary compatibility checks and consider Pact testing for critical API surfaces.
- **Evidence**: `flink-connector-aws/flink-connector-dynamodb/src/test/java/org/apache/flink/connector/dynamodb/sink/DynamoDbSinkITCase.java`, `flink-connector-aws/flink-connector-aws-kinesis-streams/src/test/java/org/apache/flink/connector/kinesis/source/KinesisStreamsSourceITCase.java`, `flink-connector-aws-e2e-tests/`

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: BLOCKER
- **Finding**: The connectors expose programmatic Java APIs (builder patterns: `KinesisStreamsSinkBuilder`, `DynamoDbSinkBuilder`, `SqsSinkBuilder`, `KinesisStreamsSourceBuilder`, `DynamoDbStreamsSourceBuilder`) consumed via Flink's DataStream and Table APIs. No REST, GraphQL, or AsyncAPI interfaces exist. No HTTP server, no API Gateway. Integration requires embedding these libraries in a JVM application.
- **Gap**: No agent-consumable API interface (REST, GraphQL, AsyncAPI). Agents cannot call Java builder patterns directly.
- **Recommendation**: Build a REST/MCP wrapper around the connector libraries to expose agent-consumable endpoints.
- **Evidence**: `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbSinkBuilder.java`, `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/KinesisStreamsSourceBuilder.java`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, Swagger, GraphQL schema, or Smithy model exists. The API is defined by Java class interfaces with `@PublicEvolving` and `@Internal` annotations. Documentation in `docs/content/docs/connectors/` provides Markdown-based reference.
- **Gap**: No machine-readable spec for auto-generating agent tool definitions.
- **Recommendation**: If API wrapper is built, generate OpenAPI spec. Consider publishing a capability manifest.
- **Evidence**: `docs/content/docs/connectors/datastream/kinesis.md`, `docs/content/docs/connectors/datastream/dynamodb.md`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Structured exception classification via `AWSExceptionHandler`, `FatalExceptionClassifier`, and service-specific classifiers (`DYNAMODB_FATAL_EXCEPTION_CLASSIFIER`). Clear retryable-vs-fatal distinction using `AwsErrorDetails.errorCode()`.
- **Gap**: Exception handling is Java-level, not HTTP-level. No published error code enumeration.
- **Recommendation**: Publish exception taxonomy in library documentation.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/sink/throwable/AWSExceptionHandler.java`, `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbSinkWriter.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: DynamoDB sink supports `overwriteByPartitionKeys` for batch deduplication. Kinesis sink uses partition keys. Partial idempotency exists but not full idempotency-key patterns.
- **Gap**: No full idempotency-key support for write endpoints.
- **Recommendation**: For write-enabled scope, implement idempotency keys at the application layer.
- **Evidence**: `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbSinkBuilder.java`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: Connectors process binary/serialized data (byte arrays, Java objects). Supported formats include JSON, Avro (GSR), and custom. Format determined by consuming application.
- **Implication**: Agents would receive data in application-configured format. JSON is most agent-friendly.
- **Recommendation**: Prefer JSON serialization for agent-facing wrappers.
- **Evidence**: `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/serialization/KinesisDeserializationSchema.java`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `library`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `library`, agent_scope: `read-only`.
- **Trigger**: Service has state changes (stateful-crud, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit documentation within the library. HTTP client configuration supports `aws.http-client.max-concurrency` and `aws.http-client.read-timeout`. AWS service limits for Kinesis and DynamoDB are documented externally by AWS but not referenced in the library's API documentation. No `X-RateLimit-Remaining` or `Retry-After` header handling.
- **Implication**: Agents calling applications built with these connectors would need external rate limit awareness.
- **Recommendation**: Document AWS service rate limits in the library documentation for consumer awareness.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java` (HTTP_CLIENT_MAX_CONCURRENCY)

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Library supports machine identity via `ASSUME_ROLE`, `WEB_IDENTITY_TOKEN`, `AUTO`, and `CUSTOM` credential providers. Delegates to AWS SDK v2 `AwsCredentialsProvider`. Principal attribution via AWS CloudTrail.
- **Gap**: Library provides the mechanism but does not enforce machine identity — `BASIC` credentials (static keys) are also supported.
- **Recommendation**: Use `ASSUME_ROLE` or `WEB_IDENTITY_TOKEN` for agent identities.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: Library does not implement IAM policy scoping. Delegates to configured `AwsCredentialsProvider` without validating least privilege.
- **Gap**: No mechanism to validate credentials follow least-privilege principles.
- **Recommendation**: Document IAM policy templates for common use cases.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/util/AWSGeneralUtil.java`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization in library. Authorization enforced by AWS IAM. DynamoDB supports `dynamodb:PutItem` vs `dynamodb:DeleteItem` at IAM level.
- **Gap**: Library has no mechanism to restrict operations if IAM credentials allow them.
- **Recommendation**: Document recommended IAM policies with action-level restrictions.
- **Evidence**: `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbWriteRequestType.java`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: No identity propagation patterns. Connectors authenticate directly to AWS services with configured credentials. No "on-behalf-of" flows.
- **Gap**: No user context propagation.
- **Recommendation**: Implement identity context at application layer for multi-tenant use cases.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/util/AWSClientUtil.java`

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: Supports `BASIC` (static keys), `ENV_VAR`, `SYS_PROP`, `PROFILE`, `ASSUME_ROLE`, `WEB_IDENTITY_TOKEN`, `AUTO`, and `CUSTOM`. No Secrets Manager integration, but `CUSTOM` provider can integrate with any secrets backend.
- **Gap**: `BASIC` credential type enables hardcoded secrets. No enforcement of secure credential patterns.
- **Recommendation**: Deprecate or warn on `BASIC` provider usage.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No audit logging in library. Log4j2 `PatternLayout` does not include caller identity. CloudTrail configured at AWS account level.
- **Gap**: No immutable audit log recording authenticated principal for operations.
- **Recommendation**: Document CloudTrail requirements. Consider structured logging with identity fields.
- **Evidence**: `flink-connector-aws-base/src/main/resources/log4j2.properties`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: No identity suspension in library. Handled at AWS IAM level (role deactivation, session revocation).
- **Gap**: No library-level identity suspension.
- **Recommendation**: Document IAM procedures for agent identity revocation.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: `AsyncSinkWriter` handles buffering and retries. `DynamoDbSinkWriter` retries unprocessed items. No saga/compensation/rollback patterns. Write-forward only. Flink checkpointing provides at-least-once guarantees.
- **Gap**: No compensation or rollback for multi-step operations.
- **Recommendation**: Implement compensating transactions at the application layer for write-enabled use cases.
- **Evidence**: `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbSinkWriter.java`

#### STATE-Q2: Queryable Current State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `library`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: DynamoDB sink supports `overwriteByPartitionKeys` deduplication. No optimistic locking, ETags, or pessimistic locking.
- **Gap**: No concurrency controls for concurrent write operations.
- **Recommendation**: For write-enabled scope, expose DynamoDB conditional writes through the connector API.
- **Evidence**: `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbSinkWriter.java`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `library`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: HTTP client max concurrency configurable via `AWSConfigConstants.HTTP_CLIENT_MAX_CONCURRENCY`. `AsyncSinkWriter` provides `maxInFlightRequests`, `maxBatchSize`. Exponential backoff retry strategies. These are client-side throughput controls, not API-layer rate limiters.
- **Gap**: No server-side rate limiting. Client-side controls only.
- **Recommendation**: Document recommended concurrency settings for agent-operated instances.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `AsyncSinkWriter` provides `maxBatchSize` (DynamoDB: 25), `maxBufferedRequests` (10000), `maxBatchSizeInBytes`, `maxRecordSizeInBytes`. Per-instance batch limits, not per-agent transaction limits.
- **Gap**: No per-agent or per-session transaction caps.
- **Recommendation**: For write-enabled scope, implement per-agent limits at wrapper level.
- **Evidence**: `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbSinkBuilder.java`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `library`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft/pending state patterns. Connectors write directly to AWS services.
- **Gap**: No staging/draft mechanism.
- **Recommendation**: For write-enabled scope, implement staging layer.
- **Evidence**: No evidence found — absence is itself a finding.

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval gate mechanisms. Operations execute immediately.
- **Gap**: No approval workflow support.
- **Recommendation**: For write-enabled scope, implement approval workflows at orchestration layer.
- **Evidence**: No evidence found — absence is itself a finding.

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: E2e tests use Testcontainers with `LocalstackContainer` for local testing. CI pipeline includes LocalStack-based and optional real-AWS tests. Test-scoped sandbox functionality only.
- **Gap**: No persistent staging environment. Testing infrastructure is ephemeral and test-scoped only.
- **Recommendation**: Create persistent LocalStack sandbox for agent integration testing.
- **Evidence**: `flink-connector-aws-base/src/test/java/org/apache/flink/connector/aws/testutils/LocalstackContainer.java`, `.github/workflows/common.yml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: No data classification, field-level encryption, or PII detection. Connectors pass data through (serialize/deserialize) without classifying or tagging content.
- **Gap**: No mechanism to classify sensitive data at field level or prevent unauthorized agent access.
- **Recommendation**: Document data classification requirements. Provide hooks for data classification.
- **Evidence**: `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbWriteRequest.java`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Library supports `AWS_REGION` configuration. No data residency enforcement — sends data to any configured region.
- **Gap**: No validation of region compliance with data sovereignty requirements.
- **Recommendation**: Document residency considerations. Consider `ValidRegions` config option.
- **Evidence**: `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java`

#### DATA-Q3: Selective Query Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `library`, agent_scope: `read-only`.
- **Trigger**: Service has list/query endpoints with potentially unbounded results
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `library`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `library`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: SLF4J/Log4j2 logging. Log messages log counts and errors, not raw record data. Root logger level `OFF` by default. No explicit PII redaction.
- **Gap**: No PII scrubbing middleware. DEBUG-level logs could include data fragments.
- **Recommendation**: Warn consumers against DEBUG logging when processing PII.
- **Evidence**: `flink-connector-aws-base/src/main/resources/log4j2.properties`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality scores or completeness metrics. Connectors expose Flink metrics (`numRecordsSendErrors`, `numRecordsSendPartialFailure`) for operational quality.
- **Implication**: Planning input for agent design — agents should not assume data quality guarantees.
- **Recommendation**: Document data quality expectations for consumers.
- **Evidence**: `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbSinkWriter.java` (metrics counters)

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: Uses `@PublicEvolving` and `@Internal` annotations for stability signals. ArchUnit tests enforce architecture. No formal schema versioning, contract testing, or breaking change detection.
- **Gap**: No automated breaking change detection for Java API surface.
- **Recommendation**: Add `japicmp-maven-plugin` for binary compatibility checks.
- **Evidence**: `flink-connector-aws-base/src/test/resources/archunit.properties`, `pom.xml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are semantically meaningful Java identifiers: `DynamoDbWriteRequest`, `KinesisShardSplit`, `StartingPosition`, `overwriteByPartitionKeys`, `millisBehindLatest`, `numRecordsSendErrors`. No legacy abbreviations or cryptic codes.
- **Implication**: Agent tool definitions can use these names directly without a data dictionary.
- **Recommendation**: No action needed — naming quality is good.
- **Evidence**: `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbWriteRequest.java`, `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/metrics/MetricConstants.java`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog or metadata layer (no Glue Data Catalog integration for the library itself, no Collibra/DataHub). Documentation exists in `docs/` as Markdown. The Glue Schema Registry format modules (`flink-avro-glue-schema-registry`, `flink-json-glue-schema-registry`) integrate with AWS Glue Schema Registry for schema management, but this is for data serialization, not for the library's own metadata.
- **Implication**: Agent tool builders must rely on documentation and source code for understanding capabilities.
- **Recommendation**: No immediate action. Documentation is sufficient for current needs.
- **Evidence**: `docs/content/docs/connectors/datastream/`, `flink-formats-aws/flink-avro-glue-schema-registry/`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing (X-Ray, OpenTelemetry). Log4j2 with `PatternLayout` (not JSON). No trace/correlation IDs. Flink-native metrics (`KinesisShardMetrics`, `DynamoDbStreamsShardMetrics`) provide operational visibility.
- **Gap**: No distributed tracing or structured logging for agent-initiated requests.
- **Recommendation**: Add OpenTelemetry/X-Ray instrumentation. Switch to JSON logging.
- **Evidence**: `flink-connector-aws-base/src/main/resources/log4j2.properties`, `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/metrics/KinesisShardMetrics.java`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No alerting in library. Flink metrics (`numRecordsSendErrors`, `millisBehindLatest`) available for external alerting.
- **Gap**: No pre-configured alerting.
- **Recommendation**: Document recommended alerting thresholds for each connector.
- **Evidence**: `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/metrics/MetricConstants.java`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Custom metrics exposed via Flink's metric system: `numRecordsSendErrors`, `numRecordsSendPartialFailure` (sink-side), `millisBehindLatest` (source-side). These are operational metrics that can serve as business outcome proxies.
- **Implication**: These metrics can be used to assess agent effectiveness when agents interact with applications using these connectors.
- **Recommendation**: Document how to expose these metrics to external monitoring systems.
- **Evidence**: `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/metrics/MetricConstants.java`, `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/source/metrics/MetricConstants.java`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `library`, agent_scope: `read-only`. No deployment infrastructure in the repository — this is a library published to Maven Central.
- **Trigger**: Always evaluated (but INFO for stateless-utility)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: GitHub Actions CI pipeline on push/PR. Unit tests, e2e tests (LocalStack + real-AWS), ArchUnit architecture tests. No API contract testing (Pact, OpenAPI diff).
- **Gap**: No automated breaking change detection in CI.
- **Recommendation**: Add `japicmp-maven-plugin` to CI.
- **Evidence**: `.github/workflows/push_pr.yml`, `.github/workflows/common.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `library`, agent_scope: `read-only`. Library published to Maven Central — "rollback" means consumers revert dependency versions.
- **Trigger**: Always evaluated for non-stateless-utility
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: 147 test files: unit tests per connector, integration tests (ITCase), e2e tests, architecture tests, packaging tests. No API contract tests (no Pact, no OpenAPI validation).
- **Gap**: No formal contract tests — functional coverage is present but API signature stability is not tested automatically.
- **Recommendation**: Add contract testing if agent tool bindings are formalized.
- **Evidence**: `flink-connector-aws/flink-connector-dynamodb/src/test/java/`, `flink-connector-aws-e2e-tests/`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `library`, agent_scope: `read-only`. The library does not manage data stores — encryption at rest is configured in the target AWS services (DynamoDB, Kinesis, SQS).
- **Trigger**: Service has persistent data stores
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigConstants.java` | AUTH-Q1, AUTH-Q2, AUTH-Q4, AUTH-Q5, AUTH-Q7, DATA-Q2, STATE-Q5, API-Q8 |
| `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/config/AWSConfigOptions.java` | AUTH-Q5, STATE-Q5 |
| `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/util/AWSGeneralUtil.java` | AUTH-Q1, AUTH-Q2, DATA-Q2 |
| `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/util/AWSClientUtil.java` | AUTH-Q3, AUTH-Q4 |
| `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/sink/throwable/AWSExceptionHandler.java` | API-Q3 |
| `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/sink/throwable/AWSExceptionClassifierUtil.java` | API-Q3 |
| `flink-connector-aws-base/src/main/java/org/apache/flink/connector/aws/util/AWSCredentialFatalExceptionClassifiers.java` | API-Q3 |
| `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbSinkBuilder.java` | API-Q1, API-Q4, STATE-Q6 |
| `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbSinkWriter.java` | API-Q3, AUTH-Q6, STATE-Q1, STATE-Q3, DATA-Q6, DATA-Q7 |
| `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbWriteRequest.java` | DATA-Q1 |
| `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/sink/DynamoDbWriteRequestType.java` | AUTH-Q3 |
| `flink-connector-aws/flink-connector-dynamodb/src/main/java/org/apache/flink/connector/dynamodb/source/metrics/MetricConstants.java` | OBS-Q2, OBS-Q3 |
| `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/KinesisStreamsSource.java` | API-Q1 |
| `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/KinesisStreamsSourceBuilder.java` | API-Q1 |
| `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/metrics/KinesisShardMetrics.java` | OBS-Q1 |
| `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/metrics/MetricConstants.java` | OBS-Q1, OBS-Q2, OBS-Q3, DISC-Q2 |
| `flink-connector-aws/flink-connector-aws-kinesis-streams/src/main/java/org/apache/flink/connector/kinesis/source/serialization/KinesisDeserializationSchema.java` | API-Q5, DATA-Q1 |
| `flink-connector-aws-base/src/test/java/org/apache/flink/connector/aws/testutils/LocalstackContainer.java` | HITL-Q3 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `flink-connector-aws-base/src/main/resources/log4j2.properties` | AUTH-Q6, OBS-Q1, DATA-Q6 |
| `flink-connector-aws-base/src/test/resources/archunit.properties` | DISC-Q1, ENG-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/push_pr.yml` | ENG-Q2 |
| `.github/workflows/common.yml` | ENG-Q2, HITL-Q3 |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| `docs/content/docs/connectors/datastream/kinesis.md` | API-Q1, API-Q2, API-Q5, AUTH-Q5 |
| `docs/content/docs/connectors/datastream/dynamodb.md` | API-Q2 |
| `docs/content/docs/connectors/datastream/sqs.md` | API-Q2 |
| `docs/content/docs/connectors/datastream/firehose.md` | API-Q2 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `pom.xml` (root) | DISC-Q1 |

### Architecture Test Artifacts
| File | Questions Referenced |
|------|---------------------|
| `flink-connector-aws-base/archunit-violations/` | DISC-Q1 |
| `flink-connector-aws/flink-connector-dynamodb/archunit-violations/` | DISC-Q1 |
| `flink-connector-aws/flink-connector-aws-kinesis-streams/archunit-violations/` | DISC-Q1 |
| `flink-connector-aws/flink-connector-sqs/archunit-violations/` | DISC-Q1 |
| `flink-connector-aws/flink-connector-aws-kinesis-firehose/archunit-violations/` | DISC-Q1 |
