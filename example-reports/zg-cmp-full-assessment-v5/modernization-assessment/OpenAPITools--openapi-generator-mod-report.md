# Modernization Readiness Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | openapi-generator |
| **Date** | 2026-04-30 |
| **TD Version** | Modernization Readiness Assessment v1.0 |
| **Repo Type** | application |
| **Service Archetype** | stateless-utility (auto-detected) |
| **Priority** | P2 |
| **Tags** | java, code-generation, api |
| **Context** | Code-generation toolkit that produces clients/servers from OpenAPI specs. |
| **Preferences** | Prefer: eks, aurora, dynamodb, api-gateway, eventbridge, bedrock · Avoid: self-managed-kafka, self-managed-kubernetes, oracle |
| **Surface Flags** | has_persistent_data_store=false, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=true, has_multi_instance_deployment=false |
| **Overall Score** | **1.94 / 4.0** |

**Archetype Justification**: No database connections, cache writes, or message queue consumers detected. The primary function is stateless code generation from OpenAPI specifications via CLI (`openapi-generator-cli`) and HTTP endpoints (`openapi-generator-online`). All operations are stateless transformations — input spec in, generated code out — with no persistent state owned by the application. Classified as `stateless-utility`.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.71 / 4.0 | 🟠 Needs Work |
| Application Architecture (APP) | 2.00 / 4.0 | 🟠 Needs Work |
| Data Platform Modernization (DATA) | 3.25 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.50 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.22 / 4.0 | ❌ Not Present |
| **Overall** | **1.94 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: IaC Coverage | 1 | No Infrastructure as Code — all infrastructure is undefined or manually provisioned. | Blocks reproducible deployments, disaster recovery, and environment consistency. Directly triggers Move to Modern DevOps pathway. |
| 2 | INF-Q1: Managed Compute | 1 | No managed compute infrastructure defined. Dockerfiles exist for packaging but no IaC deploys them to ECS, EKS, Lambda, or Fargate. | The online module Docker image is published to DockerHub with no managed deployment target. Blocks containerized service delivery on AWS. |
| 3 | SEC-Q3: API Authentication | 1 | The online Spring Boot module exposes HTTP endpoints with zero authentication — no OAuth2, JWT, API key, or any auth middleware. CORS is wide open (`*`). | Any internet-facing deployment of the online generator is fully unauthenticated, allowing unrestricted code generation and resource consumption. |
| 4 | OPS-Q1: Distributed Tracing | 1 | No distributed tracing or observability instrumentation. No OpenTelemetry, X-Ray, or equivalent in dependencies. | No visibility into request flows or performance characteristics when the online module is deployed as a service. |
| 5 | INF-Q5: Network Security | 1 | No VPC, security groups, network policies, or any network segmentation defined. No IaC exists to define network topology. | If the online service is deployed, it would have no network-level protection by default. |

---

## Quick Agent Wins

### RAG-based Knowledge Agent

- **Prerequisite:** Extensive documentation exists — `docs/` directory with 30+ markdown files covering installation, configuration, customization, debugging, templating, plugins, and generator-specific documentation in `docs/generators/`. Additionally, `README.md` (1,371 lines), `CONTRIBUTING.md`, and `CODE_OF_CONDUCT.md` provide comprehensive project guidance.
- **What it enables:** A RAG-based knowledge agent that indexes all project documentation and can answer developer questions about generator usage, template customization, plugin configuration, and contribution workflows. Given the complexity of the 200+ generators and their configuration options, this would significantly reduce onboarding friction.
- **Additional steps:** Index the `docs/` directory and `README.md` into a vector store (Amazon Bedrock Knowledge Bases with OpenSearch Serverless). Consider also indexing the generator-specific YAML configuration files in `bin/configs/` for generator option discovery.
- **Effort:** Medium

### DevOps Agent

- **Prerequisite:** INF-Q11 = 3. Extensive CI/CD pipelines exist — 100+ GitHub Actions workflows covering build, test, Docker image publishing, and Maven Central release. CircleCI with 4 parallel test nodes. Bitrise for Swift testing.
- **What it enables:** A DevOps agent that monitors build status across GitHub Actions/CircleCI/Bitrise, triggers sample regeneration workflows, checks release readiness, and manages the Docker image + Maven Central publishing pipeline via API.
- **Additional steps:** GitHub Actions API access is available. The agent would need access to workflow dispatch triggers and status endpoints. Consider adding a workflow dispatch trigger to the main build workflow for agent-initiated builds.
- **Effort:** Low

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 (modular architecture with well-defined boundaries). Primary trigger not met. |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 1 but Dockerfiles exist (root, CLI, online modules). Contextual guard prevents trigger — container definitions found. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (no stored procedures). No commercial database engines detected. Primary trigger not met. |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = Not Evaluated (no persistent data store). No databases to migrate. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 4 (stateless-utility, sync is correct). No data processing workloads exist. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (no IaC). Supporting: OPS-Q5 = 1 (no deployment strategy), OPS-Q6 = 3 (integration tests exist). |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. Context mentions "Code-generation toolkit" with no AI-related signal terms. |

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10):** No Infrastructure as Code exists in the repository. There are no Terraform files, CloudFormation templates, CDK stacks, Helm charts, or Kustomize manifests. All infrastructure for deploying the online generator service or supporting the build pipeline would need to be manually provisioned. This is the primary trigger.

**Current CI/CD State (INF-Q11):** The project has mature build and publish automation — GitHub Actions with 100+ workflow files covering build (JDK 11/17 matrix), unit tests, sample generation verification, documentation checks, Docker image builds, DockerHub publishing, and Maven Central release. CircleCI provides 4-node parallel integration testing. Bitrise handles Swift sample testing. However, there is no deployment-to-AWS pipeline — the CI/CD covers build-and-publish but not deploy-to-environment.

**Deployment Strategy Gaps (OPS-Q5):** No deployment strategy exists. Docker images are pushed to DockerHub and Maven artifacts to Central — these are artifact publishing, not service deployment. There are no blue/green, canary, or rolling deployment configurations.

**Testing Gaps (OPS-Q6):** Integration tests exist — the Maven plugin has a `-Pintegration` profile using `maven-invoker-plugin`, and CircleCI runs extensive multi-node tests against a live Petstore API. However, integration tests for the online module's HTTP endpoints are limited.

**Recommended DevOps Toolchain:**
- **IaC:** AWS CDK or Terraform to define ECS/Fargate infrastructure for the online module, with ECR for container registry (replacing DockerHub for AWS deployments)
- **CI/CD Enhancement:** Extend GitHub Actions with AWS CodeDeploy or direct ECS deployment steps for the online module
- **Deployment Strategy:** Implement blue/green deployment for the online module using ECS with Application Load Balancer
- **Container Registry:** Amazon ECR for AWS-native image management, keeping DockerHub for public distribution

**Representative AWS Services:** CodeBuild, CodePipeline, CodeDeploy, CloudFormation/CDK, ECR, ECS Fargate, Application Load Balancer

**Links:**
- [AWS DevOps Prescriptive Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/strategy-modernizing-applications/)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC defines compute resources for this project. No `aws_ecs_*`, `aws_eks_*`, `aws_lambda_*`, or `aws_instance` resources exist. Dockerfiles exist for packaging the CLI tool (`Dockerfile`, `.hub.cli.dockerfile`, `modules/openapi-generator-cli/Dockerfile`) and the online module (`.hub.online.dockerfile`, `modules/openapi-generator-online/Dockerfile`), but these are used solely for building container images published to DockerHub — there is no infrastructure defining how these images are deployed to managed compute. |
| **Gap** | Docker images are published to DockerHub but no managed compute deployment exists. The online module (`openapi-generator-online`) runs as a Spring Boot web service on port 8080 but has no deployment target defined in IaC. |
| **Recommendation** | Define ECS Fargate task definitions for the online module using AWS CDK or Terraform. Use Amazon ECR as the container registry for AWS deployments. For the CLI tool, consider AWS Lambda with container image support for on-demand code generation, or EKS (preferred per preferences) for sustained workloads. |
| **Evidence** | `Dockerfile`, `.hub.cli.dockerfile`, `.hub.online.dockerfile`, `modules/openapi-generator-online/Dockerfile`, `modules/openapi-generator-cli/Dockerfile`, `.github/workflows/docker-release.yml` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy a database. The `has_persistent_data_store` surface flag is `false` — no database connections, drivers, or database infrastructure exist in the repository. The application is a stateless code-generation toolkit that reads OpenAPI specifications and generates code without any persistent state. INF-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `pom.xml` (no database driver dependencies), `modules/openapi-generator-online/pom.xml` (no database dependencies), `modules/openapi-generator-online/src/main/resources/application.properties` (no database connection configuration) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Workflow orchestration is not applicable by design — no multi-step workflows exist. The application performs single-step stateless transformations: it accepts an OpenAPI specification and produces generated code in a single synchronous operation. There are no multi-service coordination, saga patterns, or sequential workflow steps to orchestrate. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApi.java` (single-step request/response endpoints), `modules/openapi-generator-cli/pom.xml` (CLI tool with no workflow dependencies) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Synchronous HTTP/gRPC is the correct design for this stateless-utility and is in use. The online module exposes synchronous REST endpoints (`/gen/clients/{language}`, `/gen/servers/{framework}`, `/gen/download/{fileId}`) that accept an OpenAPI spec and return generated code. No messaging infrastructure is needed — each request is self-contained with no cross-service state propagation, event emission, or asynchronous processing requirements. |
| **Gap** | None. Synchronous communication is the architecturally correct pattern for this service. |
| **Recommendation** | Adopting async messaging is NOT recommended for this service. It would add operational complexity (message broker management, consumer scaling, dead-letter handling) without architectural benefit. The stateless request/response model is the correct design. |
| **Evidence** | `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApi.java`, `pom.xml` (no SQS, SNS, Kafka, or messaging dependencies) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, security groups, NACLs, or any network segmentation is defined. No IaC exists in the repository to define network topology. The online module Docker image exposes port 8080 directly with no network-level access controls. |
| **Gap** | If the online module is deployed as a service, it would have no network-level protection. No private subnets, no security group rules, no VPC endpoints. |
| **Recommendation** | When deploying the online module to AWS, define VPC infrastructure with private subnets for the compute layer and public subnets only for the ALB/API Gateway entry point. Use security groups with least-privilege rules. Consider API Gateway (preferred per preferences) as the entry point with VPC Link to private ECS/EKS tasks. |
| **Evidence** | Repository-wide search for `.tf`, `.cfn.yaml`, `cdk.json` returned zero IaC files. No `aws_vpc`, `aws_subnet`, or `aws_security_group` definitions found. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or any managed entry point is configured. The online module's Spring Boot application serves directly on port 8080 (`server.port=8080` in `application.properties`). Docker images expose this port directly (`EXPOSE 8080` in Dockerfiles). |
| **Gap** | Direct service exposure with no throttling, authentication enforcement, request validation, or traffic management at the entry point. |
| **Recommendation** | Deploy Amazon API Gateway (preferred per preferences) as the entry point for the online module. Configure throttling to prevent abuse, request validation for the `/gen/clients` and `/gen/servers` endpoints, and integrate with Cognito or JWT authorizers for authentication. API Gateway also provides usage plans and API keys for rate-limited public access. |
| **Evidence** | `modules/openapi-generator-online/src/main/resources/application.properties` (`server.port=8080`), `modules/openapi-generator-online/Dockerfile` (`EXPOSE 8080`), `.hub.online.dockerfile` (`EXPOSE 8080`) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. No `aws_autoscaling_*`, `aws_appautoscaling_*`, Lambda concurrency limits, or any scaling policies are defined. No IaC exists to configure scaling for any resource. |
| **Gap** | The online module cannot scale in response to traffic spikes or scale down during low demand. If deployed as a single container, it has fixed capacity. |
| **Recommendation** | When deploying to ECS Fargate or EKS (preferred), configure Application Auto Scaling with target tracking policies based on CPU utilization and request count per target. Define min/max capacity boundaries appropriate for the expected code-generation workload. |
| **Evidence** | Repository-wide search returned zero IaC files. No auto-scaling resources or configurations found. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no persistent state to back up. The `has_persistent_data_store` and `has_at_rest_data_surface` surface flags are both `false`. The application is a stateless code-generation toolkit — it does not store data between requests. Generated code is returned to the caller or temporarily stored for download, but no durable state requires backup. INF-Q8 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `pom.xml`, `modules/openapi-generator-online/pom.xml` (no database or storage dependencies) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload requiring HA evaluation. The `has_deployed_workload` surface flag is `false` — Dockerfiles exist for building container images, but no IaC (Terraform, CloudFormation, CDK, Helm, Kubernetes manifests) defines a deployment target on AWS. The images are published to DockerHub for consumer use, not deployed as a managed service by this repository. INF-Q9 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `Dockerfile`, `.hub.cli.dockerfile`, `.hub.online.dockerfile`, `.github/workflows/docker-release.yml` (publishes to DockerHub only — no AWS deployment) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No Infrastructure as Code exists in the repository. A comprehensive search for Terraform files (`.tf`, `.tfvars`), CloudFormation templates (`template.yaml`, `*.cfn.yaml`), CDK entry points (`cdk.json`), Helm charts (`Chart.yaml`), and Kustomize (`kustomization.yaml`) returned zero results. All infrastructure — if any exists for deployment of the online module — is either manually provisioned or undefined. |
| **Gap** | 0% IaC coverage. No infrastructure is defined in code. This means deployments are not reproducible, environments cannot be consistently provisioned, and disaster recovery requires manual reconstruction. |
| **Recommendation** | Start with IaC for the online module's deployment infrastructure: define ECS/EKS cluster, task definitions, ALB/API Gateway, VPC networking, and ECR repository in CDK (TypeScript or Java — aligns with the Java ecosystem). Treat IaC as a first-class deliverable alongside the application code. Store IaC in this repository or a dedicated infrastructure repository. |
| **Evidence** | Repository-wide `find` for `.tf`, `.tfvars`, `template.yaml`, `cdk.json`, `Chart.yaml`, `kustomization.yaml` returned zero results. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Extensive CI/CD automation covers build and publish workflows across multiple platforms: (1) **GitHub Actions** — 100+ workflow files including `openapi-generator.yaml` (build, unit test, documentation checks, sample generation), `linux.yaml` (JDK 11/17 matrix build, Gradle plugin tests, Maven plugin integration tests), `windows.yaml` (Windows build matrix), `docker.yaml` (Docker build tests), `docker-release.yml` (multi-arch DockerHub publishing on tag/master push), `maven-release.yml` (Maven Central publishing with GPG signing). (2) **CircleCI** — 4-node parallel integration testing with Docker-based test infrastructure. (3) **Bitrise** — Swift sample testing on macOS. Build, test, and artifact publishing are fully automated. However, no deployment-to-environment pipeline exists — the CI/CD covers build/publish but not deploy. |
| **Gap** | No deployment automation for the online module to any cloud environment. The pipeline publishes artifacts (Docker images to DockerHub, JARs to Maven Central) but does not deploy them to a running environment. No IaC pipeline exists (no IaC to deploy). |
| **Recommendation** | Extend the GitHub Actions pipeline with a deployment stage that deploys the online module to AWS. Use CodeDeploy with ECS blue/green deployment or direct ECS task definition updates. Add environment-specific pipeline stages (dev → staging → production) with approval gates. |
| **Evidence** | `.github/workflows/openapi-generator.yaml`, `.github/workflows/linux.yaml`, `.github/workflows/windows.yaml`, `.github/workflows/docker.yaml`, `.github/workflows/docker-release.yml`, `.github/workflows/maven-release.yml`, `.circleci/config.yml`, `bitrise.yml` |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | **Java 11** (`maven.compiler.source=11` in root `pom.xml`, `.java-version` = `11`, `.sdkmanrc` = `java=11.0.23-tem`). The Dockerfiles use `eclipse-temurin:17` for building but the source is compiled to Java 11 target. **Spring Boot 2.5.14** in the online module (`spring-boot.version` in `modules/openapi-generator-online/pom.xml`) — this version reached end of OSS support in May 2023. **Springfox 3.0.0** for Swagger UI — Springfox is effectively unmaintained (last release 2020). No AWS SDK present. Framework and SDK versions are both regressed: Java 11 is still supported but nearing end-of-life consideration (September 2027 for LTS), Spring Boot 2.5.x is past EOL, and Springfox is abandoned. |
| **Gap** | Compound legacy signals: Java 11 + Spring Boot 2.5.14 (EOL) + Springfox 3.0.0 (unmaintained). The online module's framework stack requires a multi-axis upgrade: Java 11→17+, Spring Boot 2.5→3.x, Springfox→SpringDoc OpenAPI. |
| **Recommendation** | Upgrade the online module to Java 17 (already used in Docker build stage), Spring Boot 3.x (latest LTS), and replace Springfox with SpringDoc OpenAPI 2.x. The CLI and core modules can also benefit from Java 17 target compilation for modern language features and performance improvements. |
| **Evidence** | `pom.xml` (`maven.compiler.source=11`), `.java-version` (`11`), `.sdkmanrc` (`java=11.0.23-tem`), `modules/openapi-generator-online/pom.xml` (`spring-boot.version=2.5.14`, `springfox-version=3.0.0`), `Dockerfile` (`FROM maven:3-eclipse-temurin-17`) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Multi-module Maven project with 7 well-defined modules: `openapi-generator-core` (SPI/interfaces), `openapi-generator` (core library with 200+ generator implementations), `openapi-generator-cli` (command-line executable), `openapi-generator-maven-plugin` (Maven build plugin), `openapi-generator-gradle-plugin` (Gradle build plugin), `openapi-generator-mill-plugin` (Mill build plugin), `openapi-generator-online` (Spring Boot web service). Each module has clear boundaries: core provides the SPI, generator implements code generation, CLI/plugins/online consume the generator as a dependency. Circular dependencies are not present — the dependency graph flows from core → generator → CLI/plugins/online. The online module is independently deployable as a Docker image. |
| **Gap** | This is a modular monolith appropriate for its purpose (code-generation toolkit). The modules are build-time dependencies, not independently deployed microservices — which is the correct architecture for a library/toolkit. The online module shares the generator library at build time but is independently deployable. Minor gap: all modules share the same Maven reactor version and release cycle. |
| **Recommendation** | The current modular architecture is appropriate for a code-generation toolkit. No decomposition is recommended. Consider whether the online module warrants its own release cycle independent of the CLI and library releases, which would enable faster iteration on the web service without full project releases. |
| **Evidence** | `pom.xml` (module list in `openapi-generator` profile), `modules/openapi-generator-core/pom.xml`, `modules/openapi-generator/pom.xml`, `modules/openapi-generator-cli/pom.xml`, `modules/openapi-generator-online/pom.xml` |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Async vs sync communication is not applicable by design — synchronous request/response is the correct and only communication pattern for a code-generation tool. The online module accepts an OpenAPI spec via HTTP POST and returns generated code synchronously. There is no inter-service communication, no downstream service calls, and no state propagation that would benefit from async patterns. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApi.java` (synchronous REST endpoints only) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Long-running process handling is not applicable by design — no operations exceed 30 seconds in the typical code-generation workflow. Code generation for a single spec is a CPU-bound in-memory operation that completes in seconds. There are no batch exports, external provider calls, or data-volume-dependent operations that would create long-running processes. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApi.java`, `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java` |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy exists. The online module's endpoints (`/api/gen/clients/{language}`, `/api/gen/servers/{framework}`, `/api/gen/download/{fileId}`) have no version prefix (no `/v1/`, `/v2/`), no `Accept-Version` headers, and no versioning annotations. The Springfox configuration does not define API versions. The Swagger/OpenAPI spec for the online module uses `DocumentationType.SWAGGER_2` with no version-specific routing. |
| **Gap** | Breaking changes to the online module's API would affect all consumers simultaneously. No mechanism exists to introduce backward-incompatible changes while maintaining support for existing clients. |
| **Recommendation** | Introduce URL-path versioning (`/api/v1/gen/clients/{language}`) as the simplest approach. Configure Spring's `@RequestMapping` with version prefixes. Document the versioning strategy and backward-compatibility guarantees. |
| **Evidence** | `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApiController.java` (`@RequestMapping("/api")`), `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApi.java` (unversioned endpoint paths), `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/configuration/OpenAPIDocumentationConfig.java` |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The online module uses environment variables for configuration — `GENERATOR_HOST` environment variable controls the generated download URL host (read in `OpenAPIDocumentationConfig.java`). No service registry, service mesh, or dynamic discovery exists. The `docker-compose.yml` defines a single `docusaurus` service for the documentation website, not the online generator. The application is a single-service deployment — there are no downstream services to discover. |
| **Gap** | The `GENERATOR_HOST` environment variable is the only configurable endpoint. While adequate for a single-service deployment, this approach would not scale if the online module needed to communicate with additional services. |
| **Recommendation** | For the current single-service architecture, environment variables are sufficient. If the online module evolves to call additional services (e.g., template repositories, authentication services), adopt AWS Cloud Map or ECS Service Connect for service discovery. API Gateway (preferred) would serve as the public-facing discovery point. |
| **Evidence** | `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/configuration/OpenAPIDocumentationConfig.java` (`System.getenv("GENERATOR_HOST")`), `docker-compose.yml` |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Generated code output goes to the local filesystem. The CLI tool writes generated files to the local directory specified by the user. The online module generates code and packages it as a zip file served through a temporary file on the container's local filesystem (`/gen/download/{fileId}` endpoint). No S3 buckets, managed object storage, or document parsing capabilities (Textract, Tika) are used. |
| **Gap** | Generated artifacts are stored only on the local filesystem with no managed storage. For the online module, this means generated code is ephemeral and lost on container restart. No S3 integration for durable artifact storage. |
| **Recommendation** | For the online module, store generated code artifacts in S3 with pre-signed URLs for download. This provides durable storage, enables analytics on generation patterns, and supports horizontal scaling (multiple container instances can serve the same artifacts). Consider S3 lifecycle policies to auto-expire generated artifacts after a configurable period. |
| **Evidence** | `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java`, `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApi.java` (`/gen/download/{fileId}` endpoint) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The application has a well-defined, centralized data access pattern. All input data (OpenAPI specifications) is accessed through a single library — `swagger-parser` (version 2.1.38, defined in `pom.xml`). The parser handles reading specs from files, URLs, and inline strings with a consistent API. There are no scattered database connections because the application has no database. Generated code output follows a consistent template engine pattern through `jmustache` and `handlebars` templating libraries. The data flow is clean: spec in → parser → code model → template engine → generated files out. |
| **Gap** | None. The data access pattern is centralized and consistent. |
| **Recommendation** | No action needed. The current unified approach through swagger-parser is well-architected. |
| **Evidence** | `modules/openapi-generator/pom.xml` (`swagger-parser` dependency), `pom.xml` (`swagger-parser.version=2.1.38`) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No database engine is used by this application. The code-generation toolkit is stateless and has no database infrastructure — no RDS, DynamoDB, DocumentDB, or any database resources are defined in IaC (no IaC exists) or referenced in application configuration. There are no database engine versions to pin and no EOL concerns for database engines. |
| **Gap** | None. No database engine version or EOL risk exists. |
| **Recommendation** | No action needed. If a database is introduced in the future (e.g., for the online module to persist generation history or user preferences), ensure engine versions are explicitly pinned in IaC from the start. Prefer Aurora PostgreSQL (per preferences) if relational storage is needed, or DynamoDB (preferred) for key-value patterns. |
| **Evidence** | `pom.xml` (no database driver dependencies), `modules/openapi-generator-online/src/main/resources/application.properties` (no database connection properties) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs exist. All business logic resides in the Java application layer — specifically in the code generation engine (`modules/openapi-generator/src/main/java/org/openapitools/codegen/`) and template files. The application has no database, so there is no database-coupled logic. Code generation logic is purely in-memory transformation using Mustache/Handlebars templates. |
| **Gap** | None. All business logic is in the application layer. |
| **Recommendation** | No action needed. The clean separation of business logic from any data layer is a strength. |
| **Evidence** | `modules/openapi-generator/src/main/java/org/openapitools/codegen/` (all business logic in Java), repository-wide search for `.sql` files returned zero results |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging is configured. No IaC exists to define CloudTrail trails, log file validation, S3 log storage, or CloudWatch log retention. The application uses SLF4J/Logback for application-level logging (`logback-classic` dependency in `modules/openapi-generator-cli/pom.xml`), but this is not audit logging — it's operational debug logging with no immutable storage or forensic capabilities. |
| **Gap** | No audit trail exists for API calls to the online module or for infrastructure actions. If the online module is deployed as a service, there is no mechanism to trace who generated what code, when, or from which spec. |
| **Recommendation** | When deploying to AWS, enable CloudTrail with log file validation and S3 Object Lock for immutable log storage. For the online module, implement application-level audit logging that records: caller identity, requested language/framework, spec hash, and generation timestamp. Send structured audit logs to CloudWatch Logs with defined retention. |
| **Evidence** | Repository-wide search for IaC files returned zero results. `modules/openapi-generator-cli/pom.xml` (`logback-classic` dependency — operational logging only) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no database, S3 bucket, EBS volume, or similar. The `has_at_rest_data_surface` flag is `false`. The application is a stateless code-generation toolkit that does not persist data. SEC-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | Repository-wide search for IaC files returned zero results. No S3, RDS, DynamoDB, EBS, or EFS resources defined. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The online module's API endpoints have zero authentication. No OAuth2, JWT, API key, or any authentication middleware is configured. The `OpenAPI2SpringBoot.java` class configures CORS to allow all origins (`registry.addMapping("/**").allowedOrigins("*").allowedHeaders("Content-Type")`) but has no security configuration. No Spring Security dependency exists in `modules/openapi-generator-online/pom.xml`. No API Gateway authorizers are defined (no API Gateway exists). All endpoints — including code generation endpoints that consume CPU resources — are fully open. |
| **Gap** | Any internet-facing deployment of the online generator allows unrestricted, unauthenticated access. This enables abuse (e.g., denial-of-service via resource-intensive code generation requests) and provides no caller attribution for audit or rate limiting. |
| **Recommendation** | Add Spring Security dependency to the online module and configure at minimum API key authentication. For AWS deployment, implement authentication at the API Gateway layer (preferred) using Cognito User Pools or JWT authorizers. For the public-facing online generator (api.openapi-generator.tech), implement rate limiting via API Gateway usage plans with API keys. |
| **Evidence** | `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/OpenAPI2SpringBoot.java` (CORS `allowedOrigins("*")`, no security config), `modules/openapi-generator-online/pom.xml` (no spring-security dependency) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No identity provider integration exists. No Cognito, Okta, Ping, OIDC, or SAML configuration is present. The online module has no authentication at all (see SEC-Q3), so there is no identity system to centralize. |
| **Gap** | The application manages no authentication and has no IdP integration. Users of the online generator are entirely anonymous. |
| **Recommendation** | When implementing authentication (SEC-Q3), integrate with a centralized IdP. For AWS deployments, use Amazon Cognito (integrates well with API Gateway, preferred). For the public-facing generator, OAuth2/OIDC via GitHub (aligning with the developer audience) would provide a natural identity source. |
| **Evidence** | `modules/openapi-generator-online/pom.xml` (no identity provider dependencies), `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/` (no auth configuration files) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | CI/CD pipelines use GitHub Actions secrets correctly — `maven-release.yml` references `secrets.GPG_PRIVATE_KEY`, `secrets.GPG_PASSPHRASE`, `secrets.OSS_USERNAME`, `secrets.OSS_PASSWORD`; `docker-release.yml` references `secrets.DOCKER_USERNAME`, `secrets.DOCKER_PASSWORD`. These are stored in GitHub's encrypted secrets store, not hardcoded. One concern: `modules/openapi-generator-gradle-plugin/gradle.properties` contains `signing.password=unset` — a placeholder that, while not a real credential, follows a pattern that could lead to credential leakage. The encrypted GPG key file `sec.gpg.enc` exists in the repository root — this is encrypted but its presence in version control is a minor concern. No application-level secrets management (AWS Secrets Manager, Vault) is in place because the application has no runtime secrets to manage. |
| **Gap** | No production secrets management infrastructure (Secrets Manager, Vault) is configured. This is currently a low-risk gap because the application has no runtime secrets (no database credentials, no API keys). However, the `signing.password=unset` pattern in gradle.properties and `sec.gpg.enc` in the repo root are minor hygiene concerns. Rotation is not configured for any secrets. |
| **Recommendation** | The current approach (GitHub Actions secrets for CI/CD) is adequate for the build/publish pipeline. If the online module is deployed to AWS with authentication (per SEC-Q3/Q4 recommendations), store runtime secrets (API keys, IdP client secrets) in AWS Secrets Manager with automated rotation. Remove `signing.password=unset` from `gradle.properties` and use environment variables instead. |
| **Evidence** | `.github/workflows/maven-release.yml` (`secrets.GPG_PRIVATE_KEY`, `secrets.OSS_USERNAME`, etc.), `.github/workflows/docker-release.yml` (`secrets.DOCKER_USERNAME`, `secrets.DOCKER_PASSWORD`), `modules/openapi-generator-gradle-plugin/gradle.properties` (`signing.password=unset`), `sec.gpg.enc` |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute hardening or patching strategy exists. Dockerfiles use `eclipse-temurin:17-jre` and `eclipse-temurin:17.0.9_9-jre-focal` base images — these are standard JRE images, not hardened (not CIS-benchmarked, not Bottlerocket). No SSM Patch Manager, AWS Inspector, or vulnerability scanning is configured for the container images. The specific version pin `17.0.9_9-jre-focal` in `modules/openapi-generator-online/Dockerfile` and `modules/openapi-generator-cli/Dockerfile` is outdated (TemuRin 17.0.9 was released in 2023). |
| **Gap** | Container base images are not hardened and use pinned but outdated JRE versions. No vulnerability scanning of container images. No patching automation. |
| **Recommendation** | Switch to distroless or minimal base images (e.g., `eclipse-temurin:17-jre-alpine` or Amazon Corretto). Enable ECR image scanning for vulnerability detection. Add container image scanning (Trivy, Snyk Container) to the Docker build pipeline in `.github/workflows/docker.yaml`. Update the pinned base image version in module-level Dockerfiles. |
| **Evidence** | `Dockerfile` (`FROM maven:3-eclipse-temurin-17`), `.hub.cli.dockerfile` (`FROM eclipse-temurin:17-jre`), `.hub.online.dockerfile` (`FROM eclipse-temurin:17-jre`), `modules/openapi-generator-online/Dockerfile` (`FROM eclipse-temurin:17.0.9_9-jre-focal`), `modules/openapi-generator-cli/Dockerfile` (`FROM eclipse-temurin:17.0.9_9-jre-focal`) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Multiple static analysis tools are configured in the Maven build under the `static-analysis` profile: (1) **SpotBugs** (`spotbugs-maven-plugin` v3.1.12.2) with custom exclusion filter (`spotbugs-exclude.xml`). (2) **PMD** (`maven-pmd-plugin` v3.12.0) with `category/java/errorprone.xml` ruleset. (3) **Checkstyle** (`maven-checkstyle-plugin` v3.1.0) with Google style (`google_checkstyle.xml`), runs on every build (`verify` phase). (4) **forbiddenapis** (v3.5.1) checks for unsafe, deprecated, internal, non-portable, and reflection APIs — runs on every build. (5) **Dependabot** configured for GitHub Actions (daily) and Maven dependencies (weekly, limited to `com.gradle.*`). (6) **Violations Maven Plugin** aggregates SpotBugs, PMD, and Checkstyle results with configurable violation thresholds. However: Dependabot coverage is limited to only `com.gradle.*` Maven dependencies (not all dependencies). No container image scanning. No SAST tool beyond SpotBugs/PMD. No DAST. SpotBugs version (3.1.12.2) is outdated. |
| **Gap** | Dependabot covers only a tiny fraction of Maven dependencies (`com.gradle.*`). No container image scanning despite publishing Docker images to DockerHub. SpotBugs and PMD are configured in a `static-analysis` profile that must be explicitly activated — they do not run in the default build. No blocking security gate in the CI pipeline. |
| **Recommendation** | Expand Dependabot to cover all Maven dependencies (remove the `allow` filter). Add container image scanning (Trivy or ECR scanning) to the Docker build workflows. Upgrade SpotBugs to the current version (4.x). Consider adding the `static-analysis` profile activation to the CI pipeline (currently only runs when explicitly invoked). Add a security gate that blocks merges on critical SpotBugs/PMD findings. |
| **Evidence** | `pom.xml` (SpotBugs, PMD, Checkstyle, forbiddenapis plugin configurations), `spotbugs-exclude.xml`, `google_checkstyle.xml`, `.github/dependabot.yml` (`allow: com.gradle.*`), `.github/workflows/openapi-generator.yaml` (no security scanning step) |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumentation exists. No OpenTelemetry SDK, X-Ray SDK, or equivalent tracing library is present in any `pom.xml` dependency. The grep for "opentelemetry", "x-ray", "xray", "otel" in module POMs and source code returned only false positives related to code generation template configuration (trace ID parameters in generated clients), not actual tracing instrumentation in the tool itself. |
| **Gap** | No visibility into request flows or performance characteristics when the online module is deployed as a service. No trace ID propagation between the Spring Boot entry point and internal code generation processing. |
| **Recommendation** | Add OpenTelemetry Java Agent to the online module's Docker image for zero-code instrumentation. This provides request tracing, latency histograms, and error tracking with minimal effort. For AWS deployment, configure the OTEL exporter to send traces to AWS X-Ray. |
| **Evidence** | `modules/openapi-generator-online/pom.xml` (no tracing dependencies), `pom.xml` (no OpenTelemetry or X-Ray SDK in dependency tree) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions exist. No formal service level objectives, error budgets, or latency targets are defined in any configuration file, IaC, or documentation. The `has_api_surface` flag is `true` (online module exposes HTTP endpoints), so SLOs are meaningful for this service but are entirely absent. |
| **Gap** | No formal definition of acceptable service levels for the online code generation API. Without SLOs, there is no way to measure whether the service is meeting user expectations or degrading over time. |
| **Recommendation** | Define SLOs for the online module's critical endpoints: (1) Availability SLO (e.g., 99.5% uptime for `/gen/clients` and `/gen/servers`), (2) Latency SLO (e.g., p99 < 10s for code generation requests), (3) Error rate SLO (e.g., < 1% 5xx error rate). Implement SLO monitoring with CloudWatch alarms when deployed to AWS. |
| **Evidence** | Repository-wide search for SLO definitions, error budget configurations, or latency targets returned zero results. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics are published. No CloudWatch `put_metric_data`, no Prometheus/Micrometer metrics, and no business KPI tracking exists. The application logs via SLF4J but does not emit structured metrics on generation success/failure rates, popular languages/frameworks, spec complexity, or generation latency by language. |
| **Gap** | No insight into how the code generation service is being used. Infrastructure metrics (if any) would only show CPU/memory, not whether the service is delivering value (e.g., which generators are most popular, what error rates look like by generator). |
| **Recommendation** | Add Micrometer metrics (integrates with Spring Boot) to the online module to track: generations per language, generation latency by language, error rate by error type, spec parse success/failure. Export metrics to CloudWatch when deployed to AWS. |
| **Evidence** | `modules/openapi-generator-online/pom.xml` (no Micrometer, Prometheus, or metrics dependencies), repository-wide search for `put_metric_data`, `MeterRegistry`, `@Timed` returned zero relevant results |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting is configured. No CloudWatch alarms, no error rate thresholds, no latency monitoring, no PagerDuty/OpsGenie integration. No IaC exists to define any monitoring resources. |
| **Gap** | No alerting on error rates, latency spikes, or resource exhaustion. If the online module experiences degradation, there is no automated detection or notification. |
| **Recommendation** | When deploying to AWS, configure CloudWatch alarms on: (1) ECS task health, (2) ALB 5xx error rate > 1%, (3) p99 latency exceeding SLO target, (4) CPU utilization > 80%. Enable CloudWatch anomaly detection on error rates for the primary endpoints. Integrate with SNS for alerting. |
| **Evidence** | Repository-wide search for IaC files returned zero results. No alarm definitions, monitoring configurations, or alerting integrations found. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy exists. The `docker-release.yml` pushes Docker images to DockerHub and `maven-release.yml` publishes JARs to Maven Central — these are artifact publishing pipelines, not deployment strategies. There is no blue/green, canary, rolling, or any staged deployment to a running environment. No CodeDeploy configuration, no Helm canary, no Argo Rollouts, no Lambda traffic shifting, and no ALB weighted target groups are defined. |
| **Gap** | If the online module were deployed as a service, updates would require a manual deployment process with no staged rollout, no automatic rollback, and no traffic shifting. |
| **Recommendation** | Implement ECS blue/green deployment using CodeDeploy (integrates with the existing GitHub Actions pipeline). Configure automatic rollback on CloudWatch alarm triggers. For the preferred EKS path, consider Argo Rollouts for canary deployments with automated analysis. |
| **Evidence** | `.github/workflows/docker-release.yml` (publishes to DockerHub only), `.github/workflows/maven-release.yml` (publishes to Maven Central only). No deployment-to-environment pipeline exists. |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Integration tests exist across multiple layers: (1) **Maven Plugin Integration Tests**: `modules/openapi-generator-maven-plugin/pom.xml` defines an `integration` profile using `maven-invoker-plugin` (v3.6.0). The `linux.yaml` workflow runs `mvn clean verify -Pintegration` for the Maven plugin. (2) **CircleCI Integration Tests**: `.circleci/config.yml` runs 4-node parallel integration tests that spin up a Docker Petstore API (`swaggerapi/petstore`) and test against it — real HTTP-based integration testing. (3) **Gradle Plugin Integration Tests**: `linux.yaml` runs `gradle --project-dir modules/openapi-generator-gradle-plugin/samples/local-spec buildGoSdk`. (4) **Docker Build Tests**: `docker.yaml` builds and tests the CLI Docker image with actual code generation. However, the online module's HTTP API endpoints do not have dedicated integration tests in the CI pipeline. |
| **Gap** | No integration tests for the online module's REST API. The `/gen/clients`, `/gen/servers`, and `/gen/download` endpoints are not tested as HTTP endpoints in CI. CircleCI integration tests focus on the CLI and generated code, not the online web service. |
| **Recommendation** | Add integration tests for the online module using Spring Boot Test with `@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)` and `TestRestTemplate`. Test the full request cycle: submit spec → generate code → download artifact. Include these tests in the CI pipeline. |
| **Evidence** | `modules/openapi-generator-maven-plugin/pom.xml` (`integration` profile), `.circleci/config.yml` (Docker-based integration testing), `.github/workflows/linux.yaml` (Maven plugin integration tests, Gradle plugin tests), `.github/workflows/docker.yaml` (Docker build and CLI test) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, automation documents, self-healing patterns, or incident response workflows exist. No Systems Manager Automation documents, no Lambda-based remediation, no Step Functions for incident workflows. No markdown or YAML runbook files are present in the repository. |
| **Gap** | Incident response is entirely ad hoc. If the online module experiences issues when deployed, there is no documented or automated response procedure. |
| **Recommendation** | Create runbooks for common operational scenarios: (1) Online module health check failure → restart ECS task, (2) High error rate → rollback to previous Docker image, (3) Resource exhaustion → scale out ECS service. Start with markdown runbooks; evolve to SSM Automation documents for self-healing. |
| **Evidence** | Repository-wide search for runbook files, SSM documents, or incident response configurations returned zero results. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership is defined. `.github/CODEOWNERS` exists and defines code ownership for core modules (e.g., `@OpenAPITools/generator-core-team` for core Java files, `@OpenAPITools/build` for CI/build files), but there are no observability assets to own — no dashboards, no alarms, no SLO definitions. The CODEOWNERS file does not reference any monitoring or observability configurations. |
| **Gap** | No per-service dashboards, no alarms with named owners, no SLO definitions with team attribution. Observability infrastructure is entirely absent. |
| **Recommendation** | When observability infrastructure is established (per OPS-Q1 through OPS-Q4 recommendations), assign ownership to the core team. Add observability configuration files to CODEOWNERS. Create a per-service CloudWatch dashboard for the online module. |
| **Evidence** | `.github/CODEOWNERS` (code ownership only, no observability assets referenced) |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging exists because no AWS resources are defined. No IaC exists, so there are no resources to tag. No `default_tags` in Terraform provider, no `tags` on CloudFormation resources, no tagging standards or policies. |
| **Gap** | If AWS resources are provisioned for the online module, there is no tagging standard, no cost allocation strategy, and no ownership attribution. |
| **Recommendation** | When creating IaC (per INF-Q10 recommendation), establish a tagging standard from the start. Required tags: `Environment` (dev/staging/prod), `Service` (openapi-generator-online), `Team` (generator-core-team), `CostCenter`, `Repository`. Define these as `default_tags` in the Terraform provider or CDK `Tags.of()` scope. |
| **Evidence** | Repository-wide search for IaC files returned zero results. No AWS resources or tagging configurations found. |

---

## Learning Materials

### Move to Modern DevOps (Triggered)

| Resource | Link |
|----------|------|
| Move to Modern DevOps Learning Plan | [AWS SkillBuilder](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) |
| Getting Started with DevOps on AWS | [AWS SkillBuilder](https://skillbuilder.aws/learn/R4B13K95YQ) |
| AWS Cloud Design Patterns | [AWS Prescriptive Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |

No other pathways were triggered — no additional pathway-specific learning materials applicable.

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `pom.xml` | INF-Q1, INF-Q2, INF-Q4, INF-Q10, APP-Q1, APP-Q2, DATA-Q2, DATA-Q3, DATA-Q4, SEC-Q7, OPS-Q1, OPS-Q3 | Root Maven POM — defines Java version (11), module structure, build plugins (SpotBugs, PMD, Checkstyle, forbiddenapis), dependency versions (swagger-parser, Jackson, SLF4J). No database, messaging, or AWS SDK dependencies. |
| `.java-version` | APP-Q1 | Java version file specifying Java 11. |
| `.sdkmanrc` | APP-Q1 | SDKMan configuration specifying `java=11.0.23-tem`. |
| `modules/openapi-generator-online/pom.xml` | INF-Q2, APP-Q1, SEC-Q3, SEC-Q4, OPS-Q1, OPS-Q3 | Online module POM — Spring Boot 2.5.14, Springfox 3.0.0. No database, security, tracing, or metrics dependencies. |
| `modules/openapi-generator-online/src/main/resources/application.properties` | INF-Q2, INF-Q6, DATA-Q3 | Spring Boot config — port 8080, Springfox path, Jackson settings. No database connection properties. |
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/OpenAPI2SpringBoot.java` | SEC-Q3 | Main Spring Boot class — CORS `allowedOrigins("*")`, no security configuration. |
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApi.java` | INF-Q3, INF-Q4, APP-Q3, APP-Q4, APP-Q5, DATA-Q1 | API interface — unversioned endpoints `/gen/clients`, `/gen/servers`, `/gen/download`. Synchronous REST only. |
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApiController.java` | APP-Q5 | Controller — `@RequestMapping("/api")`, no version prefix. |
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/configuration/OpenAPIDocumentationConfig.java` | APP-Q5, APP-Q6 | Swagger/Springfox configuration — reads `GENERATOR_HOST` env var. |
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java` | APP-Q4, DATA-Q1 | Code generation service — stateless generation logic. |
| `modules/openapi-generator-online/Dockerfile` | INF-Q1, INF-Q6, SEC-Q6 | Online module Dockerfile — `eclipse-temurin:17.0.9_9-jre-focal`, `EXPOSE 8080`. |
| `modules/openapi-generator-cli/Dockerfile` | INF-Q1, SEC-Q6 | CLI module Dockerfile — `eclipse-temurin:17.0.9_9-jre-focal`. |
| `modules/openapi-generator-cli/pom.xml` | INF-Q3, SEC-Q1 | CLI module POM — `logback-classic` for operational logging. Main class: `org.openapitools.codegen.OpenAPIGenerator`. |
| `modules/openapi-generator/pom.xml` | APP-Q2, DATA-Q2, DATA-Q4 | Core generator module POM — `swagger-parser`, `jmustache`, `handlebars`, `jackson-databind`. All business logic in Java. |
| `Dockerfile` | INF-Q1, INF-Q9, SEC-Q6 | Root Dockerfile — `maven:3-eclipse-temurin-17`, builds full project for development. |
| `.hub.cli.dockerfile` | INF-Q1, INF-Q6, SEC-Q6 | DockerHub CLI image — multi-stage build, `eclipse-temurin:17-jre` runtime. |
| `.hub.online.dockerfile` | INF-Q1, INF-Q6, SEC-Q6 | DockerHub online image — multi-stage build, `eclipse-temurin:17-jre` runtime, `EXPOSE 8080`. |
| `docker-compose.yml` | APP-Q6 | Docker Compose — defines `docusaurus` documentation service only, not the online generator. |
| `.github/workflows/openapi-generator.yaml` | INF-Q11, SEC-Q7 | Main CI workflow — build, unit test, documentation checks, sample generation. No security scanning step. |
| `.github/workflows/linux.yaml` | INF-Q11, OPS-Q6 | Linux CI — JDK 11/17 matrix, Gradle plugin tests, Maven plugin integration tests. |
| `.github/workflows/windows.yaml` | INF-Q11 | Windows CI — JDK 11/17 matrix build and test. |
| `.github/workflows/docker.yaml` | INF-Q11, OPS-Q6 | Docker CI — builds and tests all Dockerfiles, runs CLI code generation test. |
| `.github/workflows/docker-release.yml` | INF-Q1, INF-Q9, OPS-Q5, SEC-Q5 | Docker release — multi-arch build and push to DockerHub on tag/master. Uses `secrets.DOCKER_USERNAME/PASSWORD`. |
| `.github/workflows/maven-release.yml` | INF-Q11, OPS-Q5, SEC-Q5 | Maven release — publishes to Maven Central with GPG signing. Uses `secrets.GPG_PRIVATE_KEY`, `secrets.OSS_USERNAME/PASSWORD`. |
| `.circleci/config.yml` | INF-Q11, OPS-Q6 | CircleCI — 4-node parallel integration tests with Docker Petstore API. |
| `bitrise.yml` | INF-Q11 | Bitrise — Swift sample testing on macOS. |
| `.github/dependabot.yml` | SEC-Q7 | Dependabot — GitHub Actions daily, Maven weekly (limited to `com.gradle.*`). |
| `.github/CODEOWNERS` | OPS-Q8 | Code ownership — core team, build team, and language-specific maintainers. No observability assets referenced. |
| `spotbugs-exclude.xml` | SEC-Q7 | SpotBugs exclusion filter — suppresses specific patterns, excludes test classes and samples. |
| `google_checkstyle.xml` | SEC-Q7 | Checkstyle configuration — Google Java Style. |
| `modules/openapi-generator-gradle-plugin/gradle.properties` | SEC-Q5 | Contains `signing.password=unset` — placeholder credential pattern. |
| `sec.gpg.enc` | SEC-Q5 | Encrypted GPG key file in repository root. |
| `modules/openapi-generator-maven-plugin/pom.xml` | OPS-Q6 | Maven plugin POM — `integration` profile with `maven-invoker-plugin` for integration tests. |
| `modules/openapi-generator/src/main/java/org/openapitools/codegen/` | DATA-Q4, APP-Q2 | Core code generation engine — 200+ generator implementations, all business logic in Java application layer. |
| `docs/` | Quick Agent Wins | 30+ documentation files covering installation, configuration, customization, templating, plugins, and migration. |
| `README.md` | Quick Agent Wins | Comprehensive project README (1,371 lines) with installation, usage, and contributor information. |
