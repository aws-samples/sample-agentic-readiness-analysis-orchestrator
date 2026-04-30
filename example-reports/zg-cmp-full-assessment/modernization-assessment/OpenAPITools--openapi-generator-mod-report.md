# Modernization Readiness Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | openapi-generator |
| **Date** | 2026-04-29 |
| **Repo Type** | application |
| **Service Archetype** | stateless-utility (auto-detected) |
| **Priority** | P2 |
| **Tags** | java, code-generation, api |
| **Context** | Code-generation toolkit that produces clients/servers from OpenAPI specs. |
| **Overall Score** | 1.91 / 4.0 |

**Archetype Justification**: No database connections, no persistent state, and no message queue consumers detected. The online module's POST endpoints perform stateless transformations (OpenAPI spec input → generated code output to temp directory). Classified as stateless-utility.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.73 / 4.0 | 🟠 Needs Work |
| Application Architecture (APP) | 2.83 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 2.25 / 4.0 | 🟠 Needs Work |
| Security Baseline (SEC) | 1.29 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.44 / 4.0 | ❌ Not Present |
| **Overall** | **1.91 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC exists — all infrastructure would be manually created (ClickOps). | Blocks reproducible deployments, disaster recovery, and environment consistency. Triggers Move to Modern DevOps pathway. |
| 2 | SEC-Q3: API Authentication | 1 | All online module API endpoints are open with no authentication. | Unauthenticated APIs are a security vulnerability; any internet-facing deployment is at risk of abuse. |
| 3 | SEC-Q1: Audit Logging | 1 | No CloudTrail or audit logging configuration found. | No forensic capability for incident investigation or compliance. |
| 4 | OPS-Q1: Distributed Tracing | 1 | No X-Ray, OpenTelemetry, or tracing instrumentation found. | Debugging production issues in the online service requires guesswork without end-to-end tracing. |
| 5 | INF-Q1: Managed Compute | 1 | No managed compute (ECS/EKS/Fargate/Lambda) IaC found; Dockerfiles exist but target DockerHub distribution only. | No elastic scaling, no operational automation — online service runs on bare Docker with no orchestration. |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** INF-Q11 ≥ 2 (scored 3). CI/CD pipeline exists with extensive GitHub Actions workflows (`openapi-generator.yaml`, `docker-release.yml`, `maven-release.yml`), CircleCI, and Bitrise.
- **What it enables:** An agent that triggers Maven/Docker builds, checks CI status across 100+ workflow files, monitors test results, and manages release pipelines via GitHub Actions API. Could also automate sample regeneration checks.
- **Additional steps:** GitHub Actions API access needs to be configured for agent invocation. Workflow dispatch triggers should be added to key workflows to allow agent-initiated runs.
- **Effort:** Low

### RAG-based Knowledge Agent

- **Prerequisite:** Extensive documentation exists in the repository — `docs/` directory with 30+ markdown files covering installation, configuration, customization, debugging, templating, and migration. `README.md` (121 KB), `CONTRIBUTING.md`, and wiki references provide rich knowledge corpus.
- **What it enables:** A RAG-based knowledge agent that indexes the documentation corpus and answers developer questions about code generation options, template customization, generator configuration, and migration from Swagger Codegen. Particularly valuable given the project's 200+ generator configurations.
- **Additional steps:** Documentation needs to be indexed into a vector store (Amazon Bedrock Knowledge Base with OpenSearch Serverless recommended per preferences). Some docs reference external wiki pages that would need separate ingestion.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 (modular monolith with clear boundaries) — primary trigger not met. |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 1 (primary met), but Dockerfiles exist (supporting condition not met — container definitions found). |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (no stored procedures/proprietary SQL) — primary trigger not met. |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = 1 (primary met), but no databases exist in this application — no databases to migrate to managed services. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 4 (stateless-utility, sync is correct design) — primary trigger not met. No data processing workloads exist. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (no IaC — primary trigger met). OPS-Q5 = 2 (direct deployment, supporting). |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in context ("Code-generation toolkit that produces clients/servers from OpenAPI specs"). |

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

#### Current State

- **IaC Coverage (INF-Q10 = 1):** Zero infrastructure-as-code exists in the repository. No Terraform, CloudFormation, CDK, Helm charts, or Kustomize manifests were found. If the online service is deployed to AWS, all infrastructure is manually created (ClickOps). This is the primary trigger for this pathway.
- **CI/CD State (INF-Q11 = 3):** Extensive CI/CD automation exists for build, test, and artifact publishing. GitHub Actions handles unit tests, sample verification, Docker image publishing to DockerHub, and Maven artifact publishing to Maven Central. CircleCI runs parallel integration tests. Bitrise handles Swift client tests. However, no deployment pipeline exists for deploying the online service to AWS infrastructure.
- **Deployment Strategy (OPS-Q5 = 2):** Docker images are published directly to DockerHub (snapshot on master push, stable on tag). No canary, blue/green, or staged rollout exists for the online service deployment.
- **Integration Testing (OPS-Q6 = 3):** Maven plugin integration tests run in CI. Sample generation verification ensures generated code is up-to-date. Unit tests run in dedicated CI jobs. However, no end-to-end API tests exist for the online module.

#### Recommendations

1. **Adopt Infrastructure as Code with CDK or Terraform:**
   - Define the online service's AWS infrastructure in code — EKS cluster (preferred per technology preferences), API Gateway (preferred), VPC with private subnets, and supporting resources.
   - Use CDK (Java, aligning with the project's primary language) or Terraform for IaC.
   - Start with the online service deployment: EKS on Fargate (avoids self-managed Kubernetes per preferences), API Gateway as the entry point, and CloudWatch for observability.

2. **Extend CI/CD with Deployment Pipelines:**
   - Add a deployment stage to `docker-release.yml` that deploys the online service Docker image to EKS after publishing to ECR (instead of only DockerHub).
   - Implement canary or blue/green deployment using AWS CodeDeploy with EKS, or Argo Rollouts.
   - Add environment promotion (dev → staging → production) with approval gates.

3. **Add Deployment Strategy:**
   - Implement blue/green deployments for the online service using EKS with ALB target groups or API Gateway stage variables.
   - Add health check validation between deployment stages.

4. **Extend Integration Testing:**
   - Add end-to-end API tests for the online module's `/gen/clients`, `/gen/servers`, and `/gen/download` endpoints.
   - Run integration tests against a deployed staging environment before production promotion.

#### Representative AWS Services
- **IaC:** AWS CDK (Java), CloudFormation
- **Compute:** Amazon EKS on Fargate (preferred), Amazon ECR for container images
- **API:** Amazon API Gateway (preferred) as managed entry point
- **CI/CD:** AWS CodePipeline, AWS CodeBuild, AWS CodeDeploy
- **Observability:** Amazon CloudWatch, AWS X-Ray

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed compute (ECS, EKS, Fargate, Lambda) infrastructure-as-code was found. Dockerfiles exist for CLI (`modules/openapi-generator-cli/Dockerfile`, `.hub.cli.dockerfile`) and online module (`modules/openapi-generator-online/Dockerfile`, `.hub.online.dockerfile`), but these target DockerHub distribution and local development — not managed container orchestration on AWS. The `docker-compose.yml` is for the documentation site (Docusaurus), not the application. |
| **Gap** | All compute is unmanaged. No ECS tasks, EKS deployments, Lambda functions, or Fargate configurations exist. The online service has no AWS deployment infrastructure. |
| **Recommendation** | Deploy the online service to Amazon EKS on Fargate (preferred per technology preferences). Create EKS cluster IaC, define Kubernetes deployments for the online module, and push images to Amazon ECR instead of (or in addition to) DockerHub. Avoid self-managed Kubernetes (per preferences). |
| **Evidence** | `Dockerfile`, `.hub.cli.dockerfile`, `.hub.online.dockerfile`, `modules/openapi-generator-online/Dockerfile`, `modules/openapi-generator-cli/Dockerfile`, `docker-compose.yml` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No databases exist in this application — no RDS, DynamoDB, DocumentDB, or any database definitions in IaC or source code. The application is a stateless code generator with no persistence layer. The online module uses an in-memory `HashMap` (`fileMap`) to track generated files temporarily (`GenApiService.java`). |
| **Gap** | No managed database infrastructure exists. While the application currently has no persistence needs, the in-memory `HashMap` for tracking generated files is not durable and will lose state on restart. |
| **Recommendation** | If the online service scales or requires durable file tracking, consider Amazon DynamoDB (preferred per technology preferences) for generated file metadata with TTL-based expiration. For the current stateless design, this is a low-priority gap. |
| **Evidence** | `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java` (in-memory fileMap), `pom.xml` (no database driver dependencies) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No multi-step workflows exist in this application. The code generation process is a single synchronous operation: parse OpenAPI spec → generate code → zip output → return download link. There are no multi-service orchestration needs, no saga patterns, and no complex workflow coordination. This is consistent with the `stateless-utility` archetype. |
| **Gap** | N/A — No multi-step workflows exist. Dedicated workflow orchestration is not applicable for this archetype. |
| **Recommendation** | Dedicated workflow orchestration (e.g., AWS Step Functions) is not needed for this stateless code-generation service. No action required. |
| **Evidence** | `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java` (single-step generation), `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java` |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Synchronous HTTP request/response is the correct design for this `stateless-utility` archetype. The online module serves synchronous REST API calls for code generation. No messaging or streaming infrastructure is needed — the service takes an OpenAPI spec as input and returns generated code as output. There are no cross-service state changes, no event-driven processing needs, and no fan-out patterns. |
| **Gap** | N/A — Synchronous HTTP is appropriate for this archetype. |
| **Recommendation** | Adopting async messaging is NOT recommended — it would add operational complexity without architectural benefit for a stateless code generation service. No action required. |
| **Evidence** | `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApi.java` (synchronous REST endpoints), `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, security groups, NACLs, or network segmentation configuration found. No IaC defining any network infrastructure. The online module's Dockerfile exposes port 8080 directly with `EXPOSE 8080` and no network isolation. The `OpenAPI2SpringBoot.java` configures CORS to allow all origins (`allowedOrigins("*")`). |
| **Gap** | No network security infrastructure exists. If deployed, the service would lack VPC isolation, private subnets, and network segmentation. Wide-open CORS configuration increases attack surface. |
| **Recommendation** | Deploy the online service in a VPC with private subnets. Place Amazon API Gateway (preferred) in front as the public entry point, routing to the service in private subnets. Restrict CORS to known consumer domains. Define security groups with least-privilege rules. |
| **Evidence** | `modules/openapi-generator-online/Dockerfile` (EXPOSE 8080), `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/OpenAPI2SpringBoot.java` (CORS `allowedOrigins("*")`) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or any managed entry point configuration found. The online module's Spring Boot application listens on port 8080 directly. The `GENERATOR_HOST` environment variable allows overriding the host in download links but does not constitute a managed entry point. |
| **Gap** | Services are exposed directly with no gateway or load balancer. No throttling, authentication, request validation, or traffic management at the entry point. |
| **Recommendation** | Place Amazon API Gateway (preferred per technology preferences) in front of the online service. Configure throttling to prevent abuse, add API key or OAuth2 authentication, and enable request validation. API Gateway also provides usage plans and API documentation generation. |
| **Evidence** | `modules/openapi-generator-online/src/main/resources/application.properties` (`server.port=8080`), `.hub.online.dockerfile` (`EXPOSE 8080`, `ENV GENERATOR_HOST=""`), `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java` (GENERATOR_HOST usage) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration found. No ASG, ECS auto-scaling, Kubernetes HPA, Lambda concurrency, or any scaling mechanism exists in the repository. |
| **Gap** | No auto-scaling — all capacity would be statically provisioned. The online service cannot respond to traffic spikes or scale down during low demand. |
| **Recommendation** | When deploying to EKS (preferred), configure Horizontal Pod Autoscaler (HPA) based on CPU/memory utilization and request rate. With Fargate, leverage Fargate auto-scaling profiles. Consider Karpenter for node auto-scaling. |
| **Evidence** | No IaC files found defining auto-scaling resources. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration found. No `aws_backup_plan`, no RDS `backup_retention_period`, no S3 versioning, no EBS snapshot policies. The application currently has no persistent data stores to back up — generated files are temporary and stored on local filesystem. |
| **Gap** | No backup or recovery infrastructure exists. While the stateless design minimizes data loss risk, there is no disaster recovery plan for the service itself. |
| **Recommendation** | If DynamoDB or other persistent storage is added for file tracking, enable automated backups with point-in-time recovery. For the current stateless design, focus on infrastructure recovery through IaC (deploy from code rather than restore from backup). |
| **Evidence** | No IaC files found defining backup resources. `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java` (temp file generation with `Files.createTempDirectory`). |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ configuration found. No IaC defining availability zones, cross-zone load balancing, or fault isolation. The online service has no HA architecture. |
| **Gap** | All resources would be in a single AZ. An AZ failure would take down the entire online service with no automatic recovery. |
| **Recommendation** | Deploy the EKS cluster across 2+ availability zones. When using Fargate, tasks automatically spread across AZs. Configure API Gateway with regional endpoint for built-in multi-AZ resilience. |
| **Evidence** | No IaC files found defining AZ configuration. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No infrastructure-as-code exists in the repository. No Terraform (`.tf`), CloudFormation (`template.yaml`/`.json`), CDK stacks, Helm charts, or Kustomize manifests were found. All infrastructure for any AWS deployment would need to be manually created. |
| **Gap** | 0% IaC coverage. Infrastructure changes are manual, error-prone, and non-reproducible. This is the primary trigger for the Move to Modern DevOps pathway. |
| **Recommendation** | Adopt IaC using AWS CDK (Java, aligning with the project's primary language) or Terraform. Start with defining the online service's deployment infrastructure: VPC, EKS cluster, API Gateway, ECR repository, CloudWatch log groups, and alarms. Store IaC in the same repository or a dedicated infrastructure repository. |
| **Evidence** | Repository-wide scan found no `.tf`, `.tfvars`, `template.yaml`, `template.json`, `cdk.json`, `Chart.yaml`, `kustomization.yaml`, or any IaC files. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Extensive CI/CD automation exists for build, test, and artifact publishing. GitHub Actions provides: build and unit tests (`openapi-generator.yaml`), Linux matrix tests across JDK 11/17 (`linux.yaml`), Maven plugin integration tests (`linux.yaml` with `-Pintegration`), Docker image publishing to DockerHub (`docker-release.yml`), Maven Central publishing (`maven-release.yml`), 90+ sample language test workflows, documentation and sample verification. CircleCI runs 4 parallel test nodes. Bitrise handles Swift client tests on macOS. |
| **Gap** | No deployment pipeline for the online service to AWS. CI/CD covers build and publish but does not deploy to any infrastructure. No automated rollback capability. |
| **Recommendation** | Extend the CI/CD pipeline with a deployment stage that deploys the online service to EKS after publishing to ECR. Add environment promotion (dev → staging → production) with approval gates and automated rollback on health check failures. |
| **Evidence** | `.github/workflows/openapi-generator.yaml`, `.github/workflows/linux.yaml`, `.github/workflows/docker-release.yml`, `.github/workflows/maven-release.yml`, `.circleci/config.yml`, `bitrise.yml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Java 11 is the primary language, as specified in `.java-version`, `.sdkmanrc` (`java=11.0.23-tem`), and `pom.xml` (`<maven.compiler.source>11</maven.compiler.source>`). Maven 3.8.8 is the build system. Java has first-class AWS SDK coverage, broad cloud-native tooling (Spring Boot, Micronaut, Quarkus), and a mature ecosystem for containerization and serverless. The online module uses Spring Boot 2.5.14. |
| **Gap** | Spring Boot 2.5.x is past end-of-life (EOL was Nov 2022). Java 11 reaches EOL in Sep 2026. While the language choice is excellent, the framework version is outdated. |
| **Recommendation** | Upgrade Spring Boot to 3.x (requires Java 17+ migration) for continued security patches and modern features. The JDK 17 build matrix in `linux.yaml` confirms compatibility is being tested. |
| **Evidence** | `.java-version` (11), `.sdkmanrc` (`java=11.0.23-tem, maven=3.8.8`), `pom.xml` (`maven.compiler.source=11`), `modules/openapi-generator-online/pom.xml` (`spring-boot.version=2.5.14`) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Multi-module Maven project with well-defined module boundaries: `openapi-generator-core` (core abstractions), `openapi-generator` (code generation engine with 200+ language generators), `openapi-generator-cli` (CLI entry point), `openapi-generator-online` (Spring Boot REST service), `openapi-generator-maven-plugin`, `openapi-generator-gradle-plugin`, `openapi-generator-mill-plugin`. The online module is a separate deployable unit. Module dependencies flow uni-directionally: core → generator → cli/online/plugins. This is a modular monolith with clear module boundaries and no circular dependencies. |
| **Gap** | The CLI and online module share the same generator engine (tight coupling by design for this use case). The online module is independently deployable but shares the `openapi-generator` JAR. This is appropriate architecture for a code-generation toolkit — not a gap requiring decomposition. |
| **Recommendation** | Current modular monolith architecture is appropriate for a code-generation toolkit. No decomposition needed. Maintain clean module boundaries as the project evolves. |
| **Evidence** | `pom.xml` (module declarations), `modules/openapi-generator-core/`, `modules/openapi-generator/`, `modules/openapi-generator-cli/`, `modules/openapi-generator-online/` |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Synchronous request/response is the correct design for this `stateless-utility` archetype. The online module serves synchronous HTTP requests: GET `/gen/clients` (list generators), GET `/gen/servers` (list generators), POST `/gen/clients/{language}` (generate client), POST `/gen/servers/{framework}` (generate server), GET `/gen/download/{fileId}` (download generated code). There are no downstream service calls, no inter-service communication, and no event-driven patterns. Async is not needed. |
| **Gap** | N/A — Synchronous communication is the correct design for a stateless code-generation service. |
| **Recommendation** | No conversion to async is recommended. Synchronous HTTP is appropriate for this archetype and would only add operational complexity without architectural benefit. |
| **Evidence** | `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApi.java` (all synchronous `@RequestMapping` endpoints) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | For the `stateless-utility` archetype, most operations complete quickly. The code generation process is synchronous — it parses the OpenAPI spec, generates code files, zips them, and returns a download link. For typical API specs, this completes in seconds. However, the `generate()` method in `Generator.java` processes the spec synchronously with no timeout configuration. Very large or complex OpenAPI specs with extensive model hierarchies could potentially exceed 30 seconds, particularly on constrained compute. |
| **Gap** | No timeout or async fallback exists for the generation endpoint. While most operations are fast, there is no protection against long-running generation requests for unusually large specs. |
| **Recommendation** | Add a request timeout to the Spring Boot configuration (`spring.mvc.async.request-timeout`). For very large specs, consider returning a `202 Accepted` with a job ID and status polling endpoint. This is a minor enhancement, not a critical gap, given the `stateless-utility` archetype. |
| **Evidence** | `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java` (synchronous `generate()` method with no timeout), `modules/openapi-generator-online/src/main/resources/application.properties` (no timeout configured) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy exists. The online module's endpoints use unversioned paths: `/gen/clients`, `/gen/servers`, `/gen/download/{fileId}`, `/gen/clients/{language}`, `/gen/servers/{framework}`. No `/v1/` prefix, no version headers, no versioning annotations. The `GenApiService.java` constructs download links using `/api/gen/download/` with no version segment. |
| **Gap** | No versioning — breaking changes would be deployed directly, affecting all consumers simultaneously. |
| **Recommendation** | Adopt URL-path versioning (e.g., `/v1/gen/clients`, `/v1/gen/servers`) as it is the simplest and most visible approach. When deploying behind API Gateway (preferred), use API Gateway stages for version management. |
| **Evidence** | `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApi.java` (`@RequestMapping(value = "/gen/clients")` — no version prefix), `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java` (download link path construction) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The online service uses the `GENERATOR_HOST` environment variable to determine the base URL for download links. This is a simple environment variable-based configuration, not dynamic service discovery. The service is a single standalone service with no need for inter-service discovery. |
| **Gap** | Environment variables for endpoints but no dynamic discovery. Acceptable for a single-service architecture but would need upgrading if additional services are added. |
| **Recommendation** | For the current single-service architecture, environment variable configuration is adequate. If the service expands, register it in AWS Cloud Map or API Gateway's service catalog for dynamic discovery. |
| **Evidence** | `.hub.online.dockerfile` (`ENV GENERATOR_HOST=""`), `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java` (`System.getenv("GENERATOR_HOST")`) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Generated code files are stored in temporary directories on the local filesystem (`Files.createTempDirectory("codegen-tmp")`) and zipped for download. No S3 usage, no managed object storage, no Textract or parsing capabilities. Generated artifacts are ephemeral — they are deleted after download. |
| **Gap** | Data on local file systems with no managed object storage. Generated artifacts are not durable and cannot be retrieved after initial download. |
| **Recommendation** | Store generated artifacts in Amazon S3 with pre-signed URLs for download. This enables durability, CDN distribution via CloudFront, and usage analytics. Add S3 lifecycle policies to automatically expire old artifacts. |
| **Evidence** | `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java` (`Files.createTempDirectory("codegen-tmp")`), `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java` (`FileUtils.deleteDirectory` after download) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | While this application has no traditional database, its data access pattern for OpenAPI spec input is centralized. All spec parsing flows through the `swagger-parser` library (`OpenAPIParser`) in `Generator.java`. The code generation configuration is centralized through `CodegenConfigLoader`. The generated file tracking is centralized in `GenApiService.java`'s `fileMap`. This represents a consistent, centralized data handling pattern even without a persistence layer. |
| **Gap** | The in-memory `fileMap` in `GenApiService.java` is not a proper data access layer — it's a static `HashMap` with no eviction policy, no thread-safety guarantees under high load, and no durability. |
| **Recommendation** | If persistence is added, implement a proper repository/DAO pattern for file metadata. For the current design, consider replacing the `HashMap` with a `ConcurrentHashMap` with TTL-based eviction to prevent memory leaks from unclaimed downloads. |
| **Evidence** | `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java` (centralized OpenAPI parsing), `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java` (centralized file tracking) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No databases exist in this application, so there are no database engine versions to pin or manage. No RDS instances, DynamoDB tables, DocumentDB clusters, or any database resources are defined in IaC or referenced in source code. |
| **Gap** | No database engine version management exists. While no databases are currently needed, there is no foundation for database lifecycle management if persistence is added in the future. |
| **Recommendation** | If databases are added (e.g., DynamoDB for file metadata), ensure engine versions are explicitly pinned in IaC with documented upgrade procedures. For DynamoDB (preferred), version management is handled by AWS. |
| **Evidence** | No database-related IaC, configuration files, or driver dependencies found in repository-wide scan. |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs exist. All business logic is in the Java application layer — code generation logic in `Generator.java`, configuration loading in `CodegenConfigLoader`, and API handling in `GenApiService.java`. No SQL files, no ORM configurations, no database-coupled logic of any kind. |
| **Gap** | N/A — No database-coupled business logic exists. This is the ideal state. |
| **Recommendation** | Maintain this pattern — keep all business logic in the application layer. If persistence is added, use application-layer data access (e.g., DynamoDB SDK) rather than stored procedures. |
| **Evidence** | `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java`, `pom.xml` (no database driver dependencies), repository-wide scan found no `.sql` files in application modules. |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or audit logging configuration found in the repository. No IaC defining logging infrastructure. Application logging uses SLF4J (`LoggerFactory.getLogger(Generator.class)`) for operational logs, but there is no structured audit trail for API requests, user actions, or security events. The `GenApiService.java` uses `System.out.println` for some operational logging — not structured, not auditable. |
| **Gap** | No CloudTrail or equivalent audit logging. No forensic capability for incident investigation or compliance. |
| **Recommendation** | Enable AWS CloudTrail for API-level audit logging. Add structured access logging to the Spring Boot application using a request filter. Configure CloudWatch Logs for centralized log aggregation with appropriate retention policies. |
| **Evidence** | `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java` (SLF4J logging), `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java` (`System.out.println` usage) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest configuration found. No KMS keys, no encrypted data stores, no encryption settings in IaC. The application currently has no persistent data stores to encrypt. Generated files are stored in OS temp directories without encryption. |
| **Gap** | No encryption at rest configured. Temporary generated files containing potentially sensitive API client code are unencrypted on disk. |
| **Recommendation** | When deploying to AWS, ensure all data stores (S3 for generated artifacts, DynamoDB for metadata) use customer-managed KMS keys. Configure EBS encryption on EC2/EKS nodes. |
| **Evidence** | No IaC files found defining KMS keys or encryption configuration. `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java` (unencrypted temp file storage). |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All online module API endpoints are open with no authentication. The `GenApi.java` interface defines endpoints with no auth annotations, no security configuration, and no middleware. The `OpenAPI2SpringBoot.java` configures wide-open CORS (`allowedOrigins("*")`) with no Spring Security dependency. No API Gateway authorizers, no Cognito, no OAuth2/JWT validation. |
| **Gap** | No API authentication — endpoints are completely open. Any internet-facing deployment is vulnerable to abuse (uncontrolled code generation consuming compute resources). |
| **Recommendation** | Add API Gateway (preferred) with API key authentication for basic protection, or Cognito user pools for OAuth2/JWT-based authentication. At minimum, add rate limiting to prevent abuse. Spring Security can be added for application-level auth as a defense-in-depth measure. |
| **Evidence** | `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApi.java` (no auth annotations), `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/OpenAPI2SpringBoot.java` (CORS `allowedOrigins("*")`, no Spring Security), `modules/openapi-generator-online/pom.xml` (no `spring-boot-starter-security` dependency) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity provider integration. No Cognito, OIDC, SAML, Okta, or any IdP configuration found. The application has no authentication at all, so there is no identity management to centralize. |
| **Gap** | Application has no identity management — neither standalone nor centralized. |
| **Recommendation** | Integrate with Amazon Cognito for centralized identity management when adding authentication. Cognito provides user pools, OAuth2/OIDC flows, and federation with external IdPs. API Gateway can enforce Cognito authorization natively. |
| **Evidence** | No identity-related configuration, dependencies, or code found in repository-wide scan. |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | CI/CD secrets are managed through GitHub Actions secrets (`DOCKER_USERNAME`, `DOCKER_PASSWORD`, `GPG_PRIVATE_KEY`, `GPG_PASSPHRASE`, `OSS_USERNAME`, `OSS_PASSWORD`, `GRADLE_ENTERPRISE_ACCESS_KEY`), which is appropriate for CI/CD. The `sec.gpg.enc` file stores an encrypted GPG key for artifact signing. However, no application-level secrets management exists — no AWS Secrets Manager, no HashiCorp Vault, no secret rotation. The `GENERATOR_HOST` environment variable is non-secret. |
| **Gap** | CI/CD secrets are managed but no application-level secrets management infrastructure exists. No secret rotation capability. If the application ever needs credentials (e.g., database, API keys), there is no secrets management foundation. |
| **Recommendation** | When deploying to AWS, use AWS Secrets Manager for any application credentials. Integrate Secrets Manager with EKS using the AWS Secrets and Configuration Provider (ASCP) for automatic secret injection. |
| **Evidence** | `.github/workflows/docker-release.yml` (GitHub secrets usage), `.github/workflows/maven-release.yml` (GPG and Maven Central secrets), `sec.gpg.enc` (encrypted GPG key) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute hardening or vulnerability scanning found. Dockerfiles use `eclipse-temurin:17-jre` and `eclipse-temurin:17.0.9_9-jre-focal` base images — standard JRE images without hardening (not CIS-benchmarked, not Bottlerocket, not distroless). No SSM Patch Manager, no AWS Inspector, no Snyk container scanning. The Dockerfile in `modules/openapi-generator-online/` pins a specific JRE version (`17.0.9_9-jre-focal`), but `.hub.online.dockerfile` uses `eclipse-temurin:17-jre` (floating tag). |
| **Gap** | No evidence of patching strategy, no vulnerability scanning, no hardened base images. Floating Docker tags risk pulling unverified image updates. |
| **Recommendation** | Switch to distroless or hardened base images. Pin all Docker image tags to specific digests. Add container image scanning (Amazon ECR image scanning or Snyk) to the CI/CD pipeline. Consider Amazon Inspector for runtime vulnerability assessment. |
| **Evidence** | `Dockerfile` (`FROM maven:3-eclipse-temurin-17`), `.hub.cli.dockerfile` (`FROM eclipse-temurin:17-jre`), `.hub.online.dockerfile` (`FROM eclipse-temurin:17-jre`), `modules/openapi-generator-online/Dockerfile` (`FROM eclipse-temurin:17.0.9_9-jre-focal`), `modules/openapi-generator-cli/Dockerfile` (`FROM eclipse-temurin:17.0.9_9-jre-focal`) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Dependabot is configured (`.github/dependabot.yml`) for GitHub Actions and limited Maven dependencies (only `com.gradle.*`). Static analysis tools are available in the `static-analysis` Maven profile: SpotBugs, PMD, and Checkstyle. ForbiddenAPIs plugin is configured in the main build. However, Dependabot is narrowly scoped (only `com.gradle.*` for Maven), static analysis is in a separate profile (not run in default CI), and there are no blocking security gates. No SAST tool (SonarQube, Semgrep, CodeGuru Reviewer) is integrated into CI. No container scanning. |
| **Gap** | Dependency scanning is too narrow (only `com.gradle.*` updates for Maven). Static analysis tools exist but are not integrated as blocking CI gates. No SAST tool in CI pipeline. No container scanning. |
| **Recommendation** | Expand Dependabot scope to all Maven dependencies (remove the `allow` filter). Integrate the `static-analysis` profile into the main CI pipeline (`openapi-generator.yaml`). Add a SAST tool (Amazon CodeGuru Reviewer or Semgrep) to the CI pipeline. Add ECR container image scanning to the Docker build pipeline. |
| **Evidence** | `.github/dependabot.yml` (narrow `allow` filter for Maven), `pom.xml` (`static-analysis` profile with SpotBugs/PMD, `forbiddenapis` plugin), `spotbugs-exclude.xml`, `google_checkstyle.xml` |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumentation found. No X-Ray SDK, no OpenTelemetry dependencies, no `traceparent` or `X-Amzn-Trace-Id` header propagation. The `pom.xml` and `modules/openapi-generator-online/pom.xml` contain no tracing dependencies. Application logging is limited to SLF4J. |
| **Gap** | No distributed tracing — debugging production issues in the online service requires manual log analysis with no request correlation. |
| **Recommendation** | Add OpenTelemetry Java agent or AWS X-Ray SDK to the online module. For EKS deployment, use the ADOT (AWS Distro for OpenTelemetry) Collector as a sidecar or DaemonSet. This enables request tracing across API Gateway → EKS → application layers. |
| **Evidence** | `modules/openapi-generator-online/pom.xml` (no tracing dependencies), `pom.xml` (no OpenTelemetry or X-Ray SDK) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found. No error budgets, no SLO monitoring, no availability or latency targets defined. No CloudWatch alarms for p99/p95 latency, no SLO dashboards. |
| **Gap** | No SLOs — no formal definition of acceptable service levels for the online code-generation API. |
| **Recommendation** | Define SLOs for the online service: availability (e.g., 99.9%), latency (e.g., p99 < 10s for code generation), and error rate (e.g., < 1% 5xx). Monitor using CloudWatch with anomaly detection. |
| **Evidence** | No SLO definition files, no CloudWatch alarm configurations, no monitoring dashboards found in repository. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics publishing found. No CloudWatch `put_metric_data` calls, no custom metrics middleware, no business KPI tracking. The only logging is operational (`LOGGER.debug` in `Generator.java`, `System.out.println` in `GenApiService.java`). |
| **Gap** | No business metrics — cannot track code generation volumes, popular languages/frameworks, failure rates by generator type, or usage patterns. |
| **Recommendation** | Add custom CloudWatch metrics for: generation requests by language, generation success/failure rate, generation latency distribution, download completion rate. These metrics drive informed decisions about generator investment and capacity planning. |
| **Evidence** | `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java` (only `LOGGER.debug`), `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java` (`System.out.println` only) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting configured. No CloudWatch alarms, no anomaly detection, no PagerDuty/OpsGenie integration. No threshold-based or anomaly-based alerting of any kind. |
| **Gap** | No alerting — failures, latency spikes, and error rate increases go undetected until users report them. |
| **Recommendation** | Configure CloudWatch alarms on error rates (5xx responses), latency (p99), and resource utilization (CPU/memory). Add anomaly detection for baseline deviation. Integrate with SNS → PagerDuty/OpsGenie for on-call notification. |
| **Evidence** | No alerting configuration found in repository-wide scan. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Docker images are published to DockerHub via GitHub Actions (`docker-release.yml`). Snapshot images are pushed on every master commit; stable images are tagged on release tags. Maven artifacts are published to Maven Central on master push (`maven-release.yml`). However, there is no deployment strategy for the online service — images are published to DockerHub but not deployed to any infrastructure. The Docker release is a direct push with no staged rollout. |
| **Gap** | Rolling/direct deployment with no canary or blue/green strategy. No staged rollout, no traffic shifting, no automated rollback. |
| **Recommendation** | When deploying to EKS, implement canary deployments using Argo Rollouts or AWS App Mesh with traffic shifting. Use API Gateway canary releases for API version rollouts. Add health check validation between deployment stages. |
| **Evidence** | `.github/workflows/docker-release.yml` (direct DockerHub push), `.github/workflows/maven-release.yml` (direct Maven Central publish) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive testing exists across multiple CI systems. GitHub Actions runs unit tests (`openapi-generator.yaml` test job), Maven plugin integration tests (`linux.yaml` with `-Pintegration`), Gradle plugin tests (`linux.yaml` with `buildGoSdk`), sample generation verification (regenerating and verifying no changes), and documentation verification. CircleCI runs 4 parallel test nodes with Docker-based integration tests (spins up petstore container). JaCoCo code coverage is configured. 90+ sample language test workflows validate generated code compiles and passes tests. |
| **Gap** | No end-to-end API tests for the online module's REST endpoints. No contract tests for the API. The online module's integration testing is limited to Spring Boot test starter — no tests against running Docker containers of the online service itself. |
| **Recommendation** | Add API integration tests for the online module: test `/gen/clients`, `/gen/servers`, `/gen/download` endpoints with real OpenAPI specs. Use Testcontainers to spin up the online service in Docker and run end-to-end tests. Add contract tests to prevent API regressions. |
| **Evidence** | `.github/workflows/openapi-generator.yaml` (unit test job), `.github/workflows/linux.yaml` (integration tests), `.circleci/config.yml` (parallel test nodes with Docker), `pom.xml` (JaCoCo configuration), `modules/openapi-generator-online/pom.xml` (`spring-boot-starter-test` dependency) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, no automated incident response, no self-healing patterns found. No SSM Automation documents, no Lambda-based remediation, no Step Functions for incident workflows. No runbook files in any format. |
| **Gap** | No runbooks — incident response is entirely ad hoc. |
| **Recommendation** | Create runbooks for common incidents: high error rate, high latency, pod crashes, disk space exhaustion from generated files. Start with markdown runbooks in the repository and graduate to SSM Automation documents for automated remediation. |
| **Evidence** | No runbook files (markdown, YAML, JSON) found in repository-wide scan. No SSM or remediation-related code. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The `.github/CODEOWNERS` file defines team ownership for core modules (`@OpenAPITools/generator-core-team` for core Java files, docs), build infrastructure (`@OpenAPITools/build` for CI, Maven wrapper), and individual generator maintainers (e.g., `@ravinikam` for cpp-qt-client). This provides clear code ownership. However, there are no observability assets to own — no dashboards, no alarms, no SLO definitions with team attribution. |
| **Gap** | Code ownership exists but no observability ownership. CODEOWNERS covers source code but not operational infrastructure (because none exists). |
| **Recommendation** | When observability infrastructure is created, extend CODEOWNERS to cover observability configs (CloudWatch dashboards, alarm definitions). Define per-service alarm ownership aligned with the existing team structure. |
| **Evidence** | `.github/CODEOWNERS` (team ownership for core, build, individual generators) |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging found — because no AWS IaC resources exist. No `default_tags`, no `tags` blocks, no Tag Policies, no Config rules for tagging. Docker image labels are configured in `docker-release.yml` (OCI labels for `org.opencontainers.image.created`, `title`, `revision`, `version`), which demonstrates labeling awareness for container images but not AWS resource tagging. |
| **Gap** | No resource tagging — when AWS infrastructure is created, there is no tagging standard or enforcement mechanism. |
| **Recommendation** | When creating IaC, establish a mandatory tagging standard: `Environment`, `Service`, `Owner`, `CostCenter`. Enforce via Terraform `default_tags` provider configuration or CDK Aspects. Activate cost allocation tags in AWS Billing. |
| **Evidence** | `.github/workflows/docker-release.yml` (OCI container labels present but not AWS resource tags), no IaC files with `tags` configuration. |

---

## Learning Materials

### Move to Modern DevOps (Triggered)

- [Move to Modern DevOps — AWS SkillBuilder Learning Plan](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)
- [AWS CDK Workshop](https://cdkworkshop.com/) — Recommended for Java-based IaC aligned with the project's primary language
- [Amazon EKS Workshop](https://www.eksworkshop.com/) — For EKS deployment (preferred per technology preferences)
- [AWS Well-Architected DevOps Lens](https://docs.aws.amazon.com/wellarchitected/latest/devops-guidance/devops-guidance.html)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `pom.xml` | INF-Q2, INF-Q10, INF-Q11, APP-Q1, APP-Q2, DATA-Q4, SEC-Q7 | Root Maven POM — defines modules, Java version (11), build plugins (JaCoCo, Checkstyle, SpotBugs, PMD, ForbiddenAPIs), and dependencies |
| `modules/openapi-generator-online/pom.xml` | APP-Q1, SEC-Q3, OPS-Q1, OPS-Q6 | Online module POM — Spring Boot 2.5.14, SpringFox, test dependencies |
| `Dockerfile` | INF-Q1, SEC-Q6 | Root Dockerfile for development builds (maven:3-eclipse-temurin-17) |
| `.hub.cli.dockerfile` | INF-Q1, SEC-Q6 | Multi-stage Dockerfile for CLI Docker image (eclipse-temurin:17-jre) |
| `.hub.online.dockerfile` | INF-Q1, INF-Q6, APP-Q6, SEC-Q6 | Multi-stage Dockerfile for online service Docker image (EXPOSE 8080, GENERATOR_HOST env var) |
| `modules/openapi-generator-online/Dockerfile` | INF-Q1, SEC-Q6 | Online module Dockerfile (eclipse-temurin:17.0.9_9-jre-focal) |
| `modules/openapi-generator-cli/Dockerfile` | INF-Q1, SEC-Q6 | CLI module Dockerfile (eclipse-temurin:17.0.9_9-jre-focal) |
| `docker-compose.yml` | INF-Q1 | Docusaurus documentation site compose file (not application) |
| `.github/workflows/openapi-generator.yaml` | INF-Q11, OPS-Q6 | Main CI workflow — build, unit tests, documentation verification, sample generation |
| `.github/workflows/linux.yaml` | INF-Q11, OPS-Q6 | Linux test matrix (JDK 11/17), Maven plugin integration tests, Gradle plugin tests |
| `.github/workflows/docker-release.yml` | INF-Q11, OPS-Q5, SEC-Q5 | Docker image publishing to DockerHub (snapshot on master, stable on tag) |
| `.github/workflows/maven-release.yml` | INF-Q11, OPS-Q5, SEC-Q5 | Maven Central publishing with GPG signing |
| `.circleci/config.yml` | INF-Q11, OPS-Q6 | CircleCI — 4 parallel test nodes with Docker-based integration tests |
| `bitrise.yml` | INF-Q11 | Bitrise CI for Swift client testing on macOS |
| `.github/dependabot.yml` | SEC-Q7 | Dependabot — github-actions (daily) and limited maven (weekly, com.gradle.* only) |
| `.github/CODEOWNERS` | OPS-Q8 | Team ownership — generator-core-team, build team, individual generator maintainers |
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApi.java` | INF-Q4, APP-Q3, APP-Q5, SEC-Q3 | REST API interface — unversioned `/gen/*` endpoints, no auth annotations |
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java` | INF-Q3, INF-Q4, INF-Q8, APP-Q4, DATA-Q1, DATA-Q4, SEC-Q1, SEC-Q2 | Code generation engine — synchronous processing, temp file creation, SLF4J logging |
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java` | INF-Q2, INF-Q3, INF-Q6, APP-Q5, APP-Q6, DATA-Q1, DATA-Q2, SEC-Q1, OPS-Q3 | Service implementation — in-memory fileMap, GENERATOR_HOST env var, System.out.println |
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/OpenAPI2SpringBoot.java` | INF-Q5, SEC-Q3 | Spring Boot entry point — CORS allowedOrigins("*"), no Spring Security |
| `modules/openapi-generator-online/src/main/resources/application.properties` | INF-Q6, APP-Q4 | Application config — server.port=8080, no timeout config, no tracing config |
| `.java-version` | APP-Q1 | Java version pinning (11) |
| `.sdkmanrc` | APP-Q1 | SDKMAN configuration (java=11.0.23-tem, maven=3.8.8) |
| `spotbugs-exclude.xml` | SEC-Q7 | SpotBugs exclusion rules |
| `google_checkstyle.xml` | SEC-Q7 | Google Java Style checkstyle configuration |
| `sec.gpg.enc` | SEC-Q5 | Encrypted GPG key for artifact signing |
| `docs/` | Quick Agent Wins | 30+ documentation files covering installation, configuration, customization, debugging, and migration |
| `README.md` | Quick Agent Wins | 121 KB comprehensive README with usage, generators list, and configuration |
| `CONTRIBUTING.md` | Quick Agent Wins | Contribution guidelines |
