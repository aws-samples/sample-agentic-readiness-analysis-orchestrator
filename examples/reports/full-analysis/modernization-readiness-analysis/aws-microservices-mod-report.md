# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | aws-microservices |
| **Date** | 2026-05-18 |
| **TD Version** | modernization-readiness-analysis |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P0 |
| **Tags** | microservices, serverless, event-driven |
| **Context** | Event-driven serverless microservices (product, basket, ordering) with Lambda, DynamoDB, EventBridge, SQS. The agent will invoke these as tools for order status lookups and return processing. |
| **Overall Score** | 2.40 / 4.0 |

**Archetype Justification**: Three microservices (product, basket, ordering) each own DynamoDB tables and expose CRUD endpoints via API Gateway. The basket service also publishes events for cross-service communication. The dominant pattern is stateful CRUD operations on business entities (products, shopping baskets, orders). Classified as stateful-crud.

**Surface Flags**: has_persistent_data_store=true, has_at_rest_data_surface=true, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=true, has_iac_provisioning_aws_resources=true

---

## Classification

**Tier: 🟠 Remediation Required**

This repo has 3 High findings, 18 Medium findings, 4 Low findings. Rule matched: "2-11 High → Remediation Required."

MOD classification note: MOD's "1 High" maps to Pilot-Ready (a single modernization gap), unlike ARA where "1 High" is a deployment blocker for agent safety. MOD measures modernization maturity — High findings indicate significant operational gaps requiring remediation before the system can be considered cloud-native ready, but they are not deployment blockers in the same sense as ARA.

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure & DevOps (INF) | 2.82 / 4.0 | 🟡 Partial | Critical |
| Application Architecture (APP) | 2.83 / 4.0 | 🟡 Partial | Needs Work |
| Data Platform (DATA) | 3.50 / 4.0 | ✅ Mature | Needs Work |
| Security Baseline (SEC) | 1.83 / 4.0 | 🟠 Needs Work | Critical |
| Operations & Observability (OPS) | 1.00 / 4.0 | ❌ Not Ready | Critical |
| **Overall** | **2.40 / 4.0** | **🟠 Needs Work** | — |

### Scoring Notes

- INF: (4+4+2+4+2+3+3+1+4+3+1) / 11 = 31/11 = 2.82
- APP: (2+4+4+4+1+2) / 6 = 17/6 = 2.83
- DATA: (4+2+4+4) / 4 = 14/4 = 3.50
- SEC: (3+1+1+4+1+1) / 6 = 11/6 = 1.83 (SEC-Q1 excluded as Not Evaluated)
- OPS: (1+1+1+1+1+1+1+1+1) / 9 = 9/9 = 1.00
- Overall: (2.82+2.83+3.50+1.83+1.00) / 5 = 11.98/5 = 2.40

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q11: CI/CD Automation | 1 | No CI/CD pipeline — all deployments manual | Blocks automated delivery; triggers Modern DevOps pathway |
| 2 | OPS-Q5: Deployment Strategy | 1 | No deployment strategy — direct manual `cdk deploy` | No safety net for production releases; risk of outages |
| 3 | OPS-Q6: Integration Testing | 1 | No automated tests — test file is placeholder | Cannot validate system behavior; regression risk on changes |
| 4 | SEC-Q3: API Authentication | 1 | API Gateway endpoints completely open — no auth | Security vulnerability; unauthorized access to all APIs |
| 5 | INF-Q8: Backup and Recovery | 1 | No backups on DynamoDB; RemovalPolicy.DESTROY set | Data loss risk; no recovery capability |

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 4 — already microservices with well-defined boundaries |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 4 — compute already on Lambda (serverless); contextual guard blocks |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 — no stored procedures or proprietary SQL |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = 4 — all databases fully managed (DynamoDB) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 4 — managed messaging (EventBridge, SQS) already in use |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q11 = 1 (no CI/CD); supporting: OPS-Q5 = 1, OPS-Q6 = 1 |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context |

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:**
- **IaC Coverage (INF-Q10 = 3):** All primary infrastructure is defined in CDK (Lambda, DynamoDB, API Gateway, EventBridge, SQS), but no operational/DR resources (CloudWatch alarms, backup plans, health checks) are codified.
- **CI/CD Automation (INF-Q11 = 1):** No CI/CD pipeline exists. No `.github/workflows/`, no `buildspec.yml`, no `Jenkinsfile`, no CodePipeline definition. All deployments are manual via `cdk deploy`.
- **Deployment Strategy (OPS-Q5 = 1):** No canary, blue/green, or rolling deployment. Manual `cdk deploy` goes directly to production.
- **Integration Testing (OPS-Q6 = 1):** The only test file (`test/aws-microservices.test.ts`) has all assertions commented out. No integration tests exist.

**Recommended Approach:**

1. **Implement CI/CD Pipeline:** Create a GitHub Actions workflow (or AWS CodePipeline if preferred) with stages for lint, build, test, and deploy. Use `cdk diff` for change validation and `cdk deploy` with approval gates for production. Align with preference for GitOps.
2. **Add Integration Tests:** Implement CDK infrastructure tests (assertions on synthesized templates) and API integration tests (Postman/Newman or custom test scripts) that validate endpoint behavior.
3. **Adopt Deployment Safety:** Configure Lambda traffic shifting (weighted aliases with `AutoPublishAlias` + `DeploymentPreference`) for canary deployments. Use CloudFormation rollback triggers.
4. **Extend IaC for Operations:** Add CloudWatch alarms, DynamoDB PITR, and dashboard definitions to CDK stacks.

**Representative AWS Services:** CodePipeline, CodeBuild, CodeDeploy, CloudFormation (via CDK), CloudWatch, X-Ray

**References:**
- [AWS CDK Pipelines](https://docs.aws.amazon.com/cdk/v2/guide/cdk_pipeline.html)
- [Lambda deployment preferences](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/automating-updates-to-serverless-apps.html)

---

## Detailed Findings

### Infrastructure & DevOps (INF)

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 4 — ✅ Mature |
| **Finding** | All compute workloads run on AWS Lambda (serverless). Three Lambda functions (product, basket, ordering) are defined via `NodejsFunction` CDK constructs. No EC2 instances or self-managed containers. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `lib/microservice.ts` — defines all three Lambda functions with `Runtime.NODEJS_14_X` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 4 — ✅ Mature |
| **Finding** | All databases are DynamoDB (fully managed, serverless). Three tables (product, basket, order) defined with `BillingMode.PAY_PER_REQUEST`. DynamoDB provides automatic Multi-AZ replication, automatic failover, and zero-downtime scaling. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `lib/database.ts` — defines three DynamoDB tables |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 — 🟠 Needs Work |
| **Finding** | The checkout flow is a multi-step business operation (validate basket → publish event → delete basket) implemented directly in the basket Lambda handler. No dedicated workflow orchestration service (Step Functions, Temporal) is used. The EventBridge + SQS pattern provides decoupling but not orchestration with error handling and compensation logic. Archetype calibration (stateful-crud): multi-step operations exist and are hardcoded. |
| **Gap** | The checkout flow has no error handling for partial failures. If the EventBridge publish succeeds but the basket delete fails (or vice versa), there is no compensation logic or retry strategy. |
| **Recommendation** | Implement the checkout flow as a Step Functions state machine that coordinates: validate basket → publish event → delete basket, with error handling and compensation at each step. This aligns with the event-driven architecture preference. |
| **Evidence** | `src/basket/index.js` — `checkoutBasket` function performs sequential operations without orchestration |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 4 — ✅ Mature |
| **Finding** | Managed messaging infrastructure is in use for cross-service state changes: EventBridge custom bus (SwnEventBus) publishes checkout events, SQS (OrderQueue) decouples EventBridge from the ordering Lambda consumer. Synchronous reads via API Gateway are appropriate for CRUD operations. This is the correct pattern for stateful-crud archetype — async for cross-service state propagation, sync for reads. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `lib/eventbus.ts` — EventBridge bus and rule; `lib/queue.ts` — SQS OrderQueue with Lambda event source |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 2 — 🟠 Needs Work |
| **Finding** | Serverless architecture (Lambda + DynamoDB + API Gateway) communicates via AWS service endpoints with IAM-based access control. Lambda functions are not deployed in a VPC (acceptable for DynamoDB-only access). CDK grants least-privilege IAM permissions (table.grantReadWriteData, bus.grantPutEventsTo). However, API Gateway endpoints are publicly accessible without WAF, resource policies, or IP restrictions. No VPC endpoints or managed networking services (VPC Lattice, PrivateLink) are configured. |
| **Gap** | API Gateway REST APIs are publicly exposed without WAF protection or resource policies. No rate limiting beyond API Gateway defaults. No managed networking services layered on. |
| **Recommendation** | Add AWS WAF to API Gateway stages to protect against common web exploits. Configure API Gateway resource policies to restrict access. Consider API Gateway usage plans with throttling. |
| **Evidence** | `lib/apigateway.ts` — `LambdaRestApi` with no WAF, no resource policy, no auth configuration |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 3 — 🟡 Partial |
| **Finding** | Three API Gateway REST APIs serve as managed entry points for the microservices (Product Service, Basket Service, Order Service). Route-based configuration with specific methods (GET, POST, PUT, DELETE) on defined resources. API Gateway provides default throttling (10K req/s account-level). |
| **Gap** | No explicit throttling configuration per API. No request validation (request models/validators). No authentication. |
| **Recommendation** | Configure API Gateway request validators and models to reject malformed requests before they reach Lambda. Add usage plans with API keys for throttling control. Add Cognito or Lambda authorizers for authentication. |
| **Evidence** | `lib/apigateway.ts` — three `LambdaRestApi` constructs with route definitions |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 3 — 🟡 Partial |
| **Finding** | Lambda functions auto-scale inherently (no configuration needed). DynamoDB tables use `PAY_PER_REQUEST` billing mode which auto-scales read/write capacity without explicit configuration. SQS scales consumers automatically via Lambda event source mapping. |
| **Gap** | No Lambda reserved concurrency configured (risk of runaway invocations consuming account concurrency). No explicit Lambda provisioned concurrency for cold-start-sensitive endpoints. No DynamoDB consumed-capacity alarms. |
| **Recommendation** | Configure reserved concurrency on Lambda functions to prevent one service from consuming the account's Lambda concurrency pool. Add CloudWatch alarms on DynamoDB consumed capacity for visibility. Consider provisioned concurrency for latency-sensitive endpoints. |
| **Evidence** | `lib/microservice.ts` — Lambda functions with no concurrency config; `lib/database.ts` — `BillingMode.PAY_PER_REQUEST` |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 — ❌ Not Ready |
| **Finding** | No backup configuration found on any data store. DynamoDB tables are created with `removalPolicy: RemovalPolicy.DESTROY` (tables deleted on stack deletion). No Point-in-Time Recovery (PITR) enabled. No AWS Backup plans. No cross-region backup replication. |
| **Gap** | All three DynamoDB tables (product, basket, order) have no PITR, no backup plans, and RemovalPolicy.DESTROY — a production data loss risk. |
| **Recommendation** | Enable DynamoDB Point-in-Time Recovery on all tables (`pointInTimeRecovery: true`). Change `removalPolicy` to `RemovalPolicy.RETAIN` for production. Consider AWS Backup for scheduled backups with defined retention. |
| **Evidence** | `lib/database.ts` — `removalPolicy: RemovalPolicy.DESTROY`, no `pointInTimeRecovery` configuration |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 4 — ✅ Mature |
| **Finding** | All production workloads inherently span multiple AZs. Lambda functions execute across AZs within a region automatically. DynamoDB provides automatic Multi-AZ replication with synchronous writes across three facilities. API Gateway and EventBridge are regional multi-AZ services. SQS is a distributed multi-AZ service. No single-AZ components exist. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | All services (Lambda, DynamoDB, API Gateway, EventBridge, SQS) are inherently multi-AZ managed services |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 3 — 🟡 Partial |
| **Finding** | All primary infrastructure resources are defined in CDK: Lambda functions, DynamoDB tables, API Gateway APIs, EventBridge bus/rules, and SQS queue. Well-structured constructs with clear separation (database.ts, microservice.ts, apigateway.ts, eventbus.ts, queue.ts). |
| **Gap** | No operational/DR resources in IaC: no CloudWatch alarms, no CloudWatch dashboards, no DynamoDB PITR configuration, no backup plans, no Lambda dead-letter queues, no Route 53 health checks. |
| **Recommendation** | Extend CDK stacks to include operational resources: CloudWatch alarms on Lambda errors/duration/throttles, DynamoDB consumed capacity alarms, dashboards, and backup configuration. Add Lambda DLQs for failed async invocations. |
| **Evidence** | `lib/` directory — 5 CDK construct files covering compute, data, API, events, and queue. No `monitoring.ts` or `alarms.ts` constructs. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 1 — ❌ Not Ready |
| **Finding** | No CI/CD pipeline exists in the repository. No `.github/workflows/`, no `buildspec.yml`, no `Jenkinsfile`, no CodePipeline or CodeBuild definitions in CDK. The only deployment mechanism is manual `cdk deploy` from a developer's machine. |
| **Gap** | All deployments are manual. No automated build, test, or deploy stages. No quality gates. No automated rollback capability. |
| **Recommendation** | Implement a CI/CD pipeline using CDK Pipelines (self-mutating pipeline) or GitHub Actions with CDK deploy. Include stages: lint → build → unit test → synth → deploy-staging → integration-test → deploy-production. Align with GitOps preferences. |
| **Evidence** | No CI/CD configuration files found in repository. No pipeline definitions in CDK stacks. |

---

### Application Architecture (APP)

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 2 — 🟠 Needs Work |
| **Finding** | Lambda handlers use JavaScript (ES6 modules) with AWS SDK v3 (modern). CDK infrastructure uses TypeScript 3.9.7 (significantly outdated, current is 5.x). Lambda runtime is Node.js 14.x which is past End-of-Life (EOL November 2023). CDK version is 2.17.0 (current is 2.150+). |
| **Gap** | Node.js 14.x is EOL — no security patches. TypeScript 3.9.7 and CDK 2.17.0 are significantly outdated. While AWS SDK v3 is current, the runtime and framework versions create compound legacy signals. |
| **Recommendation** | Upgrade Lambda runtime to Node.js 20.x or 22.x. Upgrade CDK to latest 2.x release. Upgrade TypeScript to 5.x. These are independent version bumps that can be done incrementally. |
| **Evidence** | `lib/microservice.ts` — `Runtime.NODEJS_14_X`; `package.json` — `"aws-cdk": "2.17.0"`, `"typescript": "~3.9.7"` |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 4 — ✅ Mature |
| **Finding** | Three independently deployable microservices with well-defined boundaries: Product (CRUD on products), Basket (CRUD + checkout event), Ordering (event consumer + order queries). Each service owns its own DynamoDB table (no shared database). Inter-service communication is via EventBridge/SQS (async, decoupled). No circular dependencies. Clear interfaces. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/product/`, `src/basket/`, `src/ordering/` — separate service directories; `lib/database.ts` — three separate tables; `lib/eventbus.ts` — async cross-service communication |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 4 — ✅ Mature |
| **Finding** | Cross-service communication is 100% asynchronous: the basket checkout publishes to EventBridge, which routes to SQS, consumed by the ordering Lambda. No synchronous HTTP calls between services. Client-to-service communication is synchronous via API Gateway (appropriate for CRUD reads/writes). This matches the stateful-crud archetype ideal: async for cross-service state propagation, sync for client-facing operations. Archetype calibration (stateful-crud): async available for all cross-service state changes. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/basket/index.js` — `checkoutBasket` publishes to EventBridge; `lib/eventbus.ts` — EventBridge→SQS rule; `src/ordering/index.js` — SQS event source consumption |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 4 — ✅ Mature |
| **Finding** | No operations exceed 30 seconds. All CRUD operations are sub-second DynamoDB calls (GetItem, PutItem, Query, Scan on small datasets). The checkout flow is inherently async — the basket Lambda publishes an event and returns immediately; the ordering Lambda processes asynchronously via SQS. Lambda timeout is not explicitly configured (default 3 seconds), which is appropriate for the operation types. Archetype calibration (stateful-crud): all operations are fast, long-running work is offloaded to async event processing. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js` — all operations are DynamoDB calls or EventBridge publishes (sub-second) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 — ❌ Not Ready |
| **Finding** | No API versioning strategy exists. API Gateway routes are unversioned: `/product`, `/basket`, `/order`. No `/v1/` prefix, no version headers, no versioning annotations. Breaking changes would be deployed directly to all consumers. |
| **Gap** | No versioning mechanism. Any API changes (field additions/removals, behavior changes) break all consumers simultaneously. |
| **Recommendation** | Implement URL-based versioning (`/v1/product`, `/v1/basket`, `/v1/order`) in API Gateway resource paths. Document versioning policy and deprecation timelines. This is critical if agents will invoke these APIs as tools — versioning prevents agent breakage during API evolution. |
| **Evidence** | `lib/apigateway.ts` — routes defined as `/product`, `/basket/{userName}`, `/order` with no version prefix |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 — 🟠 Needs Work |
| **Finding** | DynamoDB table names and EventBridge bus name are passed to Lambda functions via environment variables set by CDK at deploy time. The EventBridge bus name ('SwnEventBus') is hardcoded in CDK. EventBridge itself provides decoupling (services publish to a bus, rules route to targets), but bus and table names are static. No dynamic service discovery. |
| **Gap** | Service configuration (table names, bus names) is hardcoded in CDK and passed via environment variables. No service registry, no API catalog, no dynamic discovery for the API Gateway endpoints. |
| **Recommendation** | For a serverless architecture, consider using AWS Systems Manager Parameter Store or AppConfig for service configuration. Document API endpoints in an API catalog. EventBridge schema registry can serve as a discovery mechanism for event contracts. |
| **Evidence** | `lib/microservice.ts` — environment variables for `DYNAMODB_TABLE_NAME`, `EVENT_BUSNAME`; `lib/eventbus.ts` — hardcoded `eventBusName: 'SwnEventBus'` |

---

### Data Platform (DATA)

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 4 — ✅ Mature |
| **Finding** | The system handles only structured data in DynamoDB: products (id, name, description, imageFile, price, category), baskets (userName, items), and orders (userName, orderDate, order details). The `imageFile` field stores URL references to externally hosted images — no unstructured data processing requirements exist within this system. No file uploads, document processing, or binary object storage is needed. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `lib/database.ts` — DynamoDB tables with structured key schemas; `src/product/index.js` — product attributes are all structured fields |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 2 — 🟠 Needs Work |
| **Finding** | Each service has a `ddbClient.js` that creates a DynamoDB client instance, but this is only client initialization — not a data access layer. The actual data access logic (command construction, marshalling, query building) is scattered throughout the Lambda handler functions (`index.js`). Each handler directly constructs `GetItemCommand`, `PutItemCommand`, `ScanCommand`, `QueryCommand` with inline parameters. No repository/DAO pattern. |
| **Gap** | DynamoDB commands are constructed inline in handler functions with no abstraction. Changing table schema, access patterns, or adding caching would require touching every handler function. No consistent error handling for data operations. |
| **Recommendation** | Extract data access into repository modules per service (e.g., `productRepository.js`, `basketRepository.js`, `orderRepository.js`) that encapsulate DynamoDB operations and provide typed interfaces. This improves testability and maintainability. |
| **Evidence** | `src/product/index.js` — DynamoDB commands constructed directly in handler; `src/basket/index.js` — same pattern; `src/ordering/index.js` — same pattern |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 4 — ✅ Mature |
| **Finding** | DynamoDB is a serverless managed database with no user-managed engine versions. AWS manages all database engine updates transparently with zero downtime. No version pinning is possible or needed. No EOL risk exists for DynamoDB. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `lib/database.ts` — DynamoDB `Table` construct has no engine version parameter (managed by AWS) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 — ✅ Mature |
| **Finding** | DynamoDB has no stored procedures, triggers (in the traditional database sense), or proprietary SQL. All business logic resides in the Lambda application layer. Data operations use the DynamoDB API (GetItem, PutItem, Query, Scan, UpdateItem, DeleteItem) — no proprietary query language beyond standard DynamoDB expressions. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js` — all business logic in application code using DynamoDB API |

---

### Security Baseline (SEC)

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | Audit logging (CloudTrail) is an AWS account-level service provisioned once per account or organization — not per-application. This repo contains application-level IaC only (Lambda, DynamoDB, API Gateway, EventBridge, SQS) which is the correct scope for an application repo. CloudTrail evaluation belongs in the foundation/account-level infrastructure repo. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 3 — 🟡 Partial |
| **Finding** | DynamoDB tables have default encryption at rest using AWS-owned keys (enabled automatically by AWS). No explicit KMS key configuration in CDK. SQS queue does not specify KMS encryption. All DynamoDB data is encrypted at rest by default, but without customer-managed keys the organization has no control over key rotation policies or key access auditing. |
| **Gap** | No customer-managed KMS keys. Cannot control key rotation or audit key access. SQS queue messages are not explicitly encrypted with KMS (uses Amazon SQS-managed encryption by default). |
| **Recommendation** | Add customer-managed KMS keys for DynamoDB tables and SQS queue. Configure key rotation policies. This provides audit trail via CloudTrail key usage logs and enables fine-grained access control. |
| **Evidence** | `lib/database.ts` — DynamoDB tables with no `encryptionKey` property; `lib/queue.ts` — SQS queue with no KMS configuration |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 — ❌ Not Ready |
| **Finding** | No authentication is configured on any API Gateway endpoint. All three REST APIs (Product Service, Basket Service, Order Service) are completely open to the public internet. No authorizers (Cognito, Lambda, IAM), no API keys, no usage plans. Any user can perform CRUD operations on products, baskets, and orders without authentication. |
| **Gap** | All API endpoints are unauthenticated. Critical security vulnerability — unauthorized users can create/modify/delete products, access any user's basket, and read any order. |
| **Recommendation** | Add Cognito User Pool authorizer or Lambda authorizer to all API Gateway methods. At minimum, protect write operations (POST, PUT, DELETE) immediately. Configure API Gateway API keys with usage plans for rate limiting. Consider AWS IAM authorization for service-to-service calls if agents will invoke these APIs. |
| **Evidence** | `lib/apigateway.ts` — `LambdaRestApi` and `addMethod()` calls with no `authorizer` or `authorizationType` parameter |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 — ❌ Not Ready |
| **Finding** | No identity provider integration exists. No Cognito User Pool, no OIDC/SAML configuration, no external IdP federation. The application has no authentication at all — it does not manage its own auth nor integrate with any centralized identity provider. |
| **Gap** | No identity management of any kind. Cannot attribute actions to users, enforce access policies, or integrate with organizational SSO. |
| **Recommendation** | Integrate Amazon Cognito as the centralized identity provider. Create a User Pool with appropriate authentication flows (SRP, OAuth2/OIDC). Configure API Gateway Cognito authorizers. This enables SSO integration and federated identity in the future. |
| **Evidence** | No Cognito, OIDC, SAML, or identity provider references in any file |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 4 — ✅ Mature |
| **Finding** | The application has no secrets to manage. All AWS service access (DynamoDB, EventBridge, SQS) uses IAM roles automatically provided by the Lambda execution environment. No database passwords, no API keys, no tokens exist. CDK grants least-privilege IAM permissions (e.g., `table.grantReadWriteData(lambda)`, `bus.grantPutEventsTo(lambda)`). Environment variables contain only non-secret configuration (table names, event bus name). |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `lib/microservice.ts` — environment variables contain table names and event config only; `lib/database.ts` — `grantReadWriteData` for IAM; `lib/eventbus.ts` — `grantPutEventsTo` for IAM |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 — ❌ Not Ready |
| **Finding** | Lambda runtime is Node.js 14.x which is past End-of-Life (EOL November 2023). AWS no longer provides security patches for this runtime. No vulnerability scanning (Inspector, Snyk) is configured. No dependency scanning (npm audit, Dependabot). Lambda manages the underlying OS, but the runtime version is the customer's responsibility. |
| **Gap** | EOL runtime receiving no security patches. No vulnerability scanning on dependencies. AWS SDK v3 packages at version ^3.55.0/^3.58.0 are outdated (current is 3.500+). |
| **Recommendation** | Immediately upgrade Lambda runtime to Node.js 20.x or 22.x. Add Dependabot or Snyk for dependency vulnerability scanning. Update `@aws-sdk/*` packages to latest versions. Consider AWS Lambda runtime management controls for automatic minor version updates. |
| **Evidence** | `lib/microservice.ts` — `Runtime.NODEJS_14_X`; `src/basket/package.json` — `@aws-sdk/client-dynamodb: ^3.55.0`; `src/product/package.json` — same outdated versions |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 — ❌ Not Ready |
| **Finding** | No CI/CD pipeline exists, therefore no security scanning tools are integrated. No SAST tools (SonarQube, Semgrep, CodeGuru). No dependency scanning (Dependabot, npm audit, Snyk). No `.snyk` policy file. No container scanning (not applicable — no containers). |
| **Gap** | No security validation of any kind in the development workflow. Vulnerable dependencies and code security issues reach production undetected. |
| **Recommendation** | When implementing CI/CD (see INF-Q11), integrate: (1) `npm audit` or Snyk for dependency scanning, (2) Semgrep or CodeGuru for SAST, (3) CDK-nag for IaC security best practices. Configure blocking gates on critical findings. |
| **Evidence** | No CI/CD configuration files; no `.snyk`, no `dependabot.yml`, no security tool configuration |

---

### Operations & Observability (OPS)

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 — ❌ Not Ready |
| **Finding** | No distributed tracing is instrumented. Lambda functions do not have X-Ray active tracing enabled (no `tracing: lambda.Tracing.ACTIVE` in CDK). No OpenTelemetry SDK in any dependency manifest. No trace ID propagation between services. The EventBridge → SQS → Lambda flow has no trace context propagation configured. |
| **Gap** | Cannot trace requests across the three microservices. Cannot correlate a checkout event from basket through EventBridge/SQS to the ordering service. Debugging cross-service failures is guesswork. |
| **Recommendation** | Enable X-Ray active tracing on all Lambda functions (`tracing: Tracing.ACTIVE`). Enable X-Ray tracing on API Gateway stages. AWS SDK v3 supports X-Ray trace propagation automatically when active tracing is enabled. Consider AWS Distro for OpenTelemetry (ADOT) Lambda layer for richer instrumentation. |
| **Evidence** | `lib/microservice.ts` — no `tracing` property on Lambda functions; no OpenTelemetry in `package.json` files |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 — ❌ Not Ready |
| **Finding** | No SLO definitions found. No CloudWatch alarms on latency or error rates. No error budget tracking. No formal definition of acceptable service levels for any of the three APIs. No monitoring artifacts exist in the IaC. |
| **Gap** | No SLOs defined for critical user journeys (product browsing, basket checkout, order queries). Cannot measure whether the system meets user expectations. |
| **Recommendation** | Define SLOs for critical paths: (1) Product API p99 latency < 200ms, availability > 99.9%; (2) Checkout success rate > 99.5%; (3) Order query p99 < 500ms. Implement as CloudWatch alarms and composite alarms in CDK. |
| **Evidence** | No CloudWatch alarm resources in CDK; no SLO definition files; no monitoring construct |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 — ❌ Not Ready |
| **Finding** | No custom business metrics are published. No CloudWatch `putMetricData` calls in any Lambda handler. Only default Lambda metrics (invocations, errors, duration) are available. No tracking of business outcomes (orders placed, checkout success/failure, products created). |
| **Gap** | Cannot measure business value delivery. No visibility into checkout conversion rates, order volumes, or product catalog health. |
| **Recommendation** | Add custom CloudWatch metrics in Lambda handlers: orders-placed, checkout-success, checkout-failure, products-created. Use CloudWatch Embedded Metric Format (EMF) for zero-latency metric publication from Lambda. |
| **Evidence** | `src/basket/index.js`, `src/ordering/index.js`, `src/product/index.js` — no metrics publishing code |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 — ❌ Not Ready |
| **Finding** | No alerting configured. No CloudWatch alarms (static threshold or anomaly detection). No integration with PagerDuty, OpsGenie, or SNS topics for incident notification. No composite alarms. |
| **Gap** | No automated detection of failures, latency spikes, or error rate increases. Incidents are discovered by users, not monitoring systems. |
| **Recommendation** | Add CloudWatch alarms: Lambda error rate > 1%, Lambda duration p99 > threshold, DynamoDB throttled requests > 0, SQS dead-letter queue message count > 0. Add SNS topic for alarm notifications. Consider CloudWatch anomaly detection for latency baselines. |
| **Evidence** | No CloudWatch alarm resources in CDK; no SNS topics for alerting |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 — ❌ Not Ready |
| **Finding** | No deployment strategy exists. Deployments are manual `cdk deploy` directly to production. No canary deployments, no blue/green, no traffic shifting. No Lambda aliases with weighted routing. No CloudFormation rollback triggers configured. |
| **Gap** | Any deployment goes directly to production with no staged rollout. A bad deployment affects all users immediately with no automatic rollback. |
| **Recommendation** | Implement Lambda canary deployments using `AutoPublishAlias` with `DeploymentPreference` (canary or linear traffic shifting). Configure CloudFormation rollback triggers on Lambda error rate alarms. This provides safe, incremental releases with automatic rollback. |
| **Evidence** | No deployment configuration; no CI/CD pipeline; no Lambda alias or deployment preference configuration in `lib/microservice.ts` |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 1 — ❌ Not Ready |
| **Finding** | The only test file (`test/aws-microservices.test.ts`) is a placeholder with all assertions commented out. Contains only an empty test: `test('SQS Queue Created', () => {})`. No integration tests, no API tests, no contract tests. Jest is configured but not used. |
| **Gap** | No automated testing of any kind. Cannot validate that infrastructure deploys correctly, APIs respond as expected, or the EventBridge→SQS→Lambda flow works end-to-end. |
| **Recommendation** | Implement: (1) CDK assertion tests validating synthesized CloudFormation templates, (2) Integration tests that deploy to a test environment and validate API endpoints, (3) EventBridge→SQS flow tests using test events. Use the existing Jest configuration. |
| **Evidence** | `test/aws-microservices.test.ts` — empty placeholder test; `jest.config.js` — configured but unused |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 — ❌ Not Ready |
| **Finding** | No runbooks, no automated remediation, no SSM Automation documents, no incident response workflows. No Lambda-based self-healing. No dead-letter queues configured for failed Lambda invocations. |
| **Gap** | Incident response is entirely ad hoc. No documented procedures for common failures (Lambda throttling, DynamoDB capacity issues, EventBridge delivery failures). |
| **Recommendation** | Create runbooks for common scenarios: (1) Lambda throttling → increase reserved concurrency, (2) DynamoDB throttling → check access patterns, (3) SQS DLQ messages → investigate and replay. Add Lambda DLQs for failed async invocations. Consider SSM Automation for common remediation actions. |
| **Evidence** | No runbook files; no SSM resources in CDK; no DLQ configuration on Lambda functions |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 — ❌ Not Ready |
| **Finding** | No observability ownership defined. No per-service dashboards. No named alarm owners. No CODEOWNERS file. No team attribution on monitoring resources. No SLO definitions tied to specific teams. |
| **Gap** | No clear ownership of service health. Monitoring gaps will emerge without attribution. |
| **Recommendation** | Add CODEOWNERS file. Create per-service CloudWatch dashboards (product-dashboard, basket-dashboard, ordering-dashboard) in CDK. Tag monitoring resources with team ownership. |
| **Evidence** | No CODEOWNERS file; no dashboard definitions in CDK; no team attribution in any configuration |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 — ❌ Not Ready |
| **Finding** | No tags on any resources. DynamoDB tables, Lambda functions, API Gateways, EventBridge bus, and SQS queue are all created without tags. No cost allocation tags. No environment tags. No ownership tags. No CDK `Tags.of()` calls or stack-level tagging. |
| **Gap** | Cannot track costs per service, identify resource ownership, or distinguish environments. No tagging governance. |
| **Recommendation** | Add CDK stack-level tags using `Tags.of(this).add()`: Environment, Service, Team, CostCenter. Use CDK Aspects for tag enforcement across all constructs. Activate cost allocation tags in AWS Billing. |
| **Evidence** | `lib/database.ts`, `lib/microservice.ts`, `lib/queue.ts`, `lib/eventbus.ts` — no `tags` properties on any resource; no `Tags.of()` calls |

---

## Learning Materials

### Move to Modern DevOps (Triggered)

- [Move to Modern DevOps — AWS Skill Builder Learning Plan](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)
- [AWS CDK Pipelines](https://docs.aws.amazon.com/cdk/v2/guide/cdk_pipeline.html)
- [AWS Lambda Deployment Preferences](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/automating-updates-to-serverless-apps.html)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `lib/microservice.ts` | INF-Q1, INF-Q7, APP-Q1, SEC-Q6, OPS-Q1, OPS-Q5 | Lambda function definitions with Runtime.NODEJS_14_X |
| `lib/database.ts` | INF-Q2, INF-Q7, INF-Q8, INF-Q9, DATA-Q1, DATA-Q3, SEC-Q2, OPS-Q9 | DynamoDB tables with PAY_PER_REQUEST, RemovalPolicy.DESTROY |
| `lib/apigateway.ts` | INF-Q5, INF-Q6, APP-Q5, SEC-Q3, APP-Q6 | API Gateway REST APIs without auth/WAF/versioning |
| `lib/eventbus.ts` | INF-Q4, APP-Q3, APP-Q6, SEC-Q5 | EventBridge bus and routing rules |
| `lib/queue.ts` | INF-Q4, INF-Q9, SEC-Q2 | SQS OrderQueue with Lambda event source |
| `lib/aws-microservices-stack.ts` | INF-Q10 | Main CDK stack orchestrating all constructs |
| `src/product/index.js` | APP-Q4, DATA-Q2, DATA-Q4, OPS-Q3 | Product Lambda handler with inline DynamoDB operations |
| `src/basket/index.js` | INF-Q3, APP-Q3, APP-Q4, DATA-Q2, OPS-Q3 | Basket Lambda handler with checkout flow |
| `src/ordering/index.js` | APP-Q3, APP-Q4, DATA-Q2, OPS-Q3 | Ordering Lambda handler consuming SQS events |
| `src/basket/package.json` | APP-Q1, SEC-Q6 | AWS SDK v3 dependencies at ^3.55.0 |
| `src/product/package.json` | APP-Q1, SEC-Q6 | AWS SDK v3 dependencies at ^3.55.0 |
| `package.json` | APP-Q1 | Root CDK dependencies: CDK 2.17.0, TypeScript 3.9.7 |
| `test/aws-microservices.test.ts` | OPS-Q6 | Empty placeholder test file |
| `src/basket/ddbClient.js` | DATA-Q2 | DynamoDB client initialization (no DAO pattern) |
