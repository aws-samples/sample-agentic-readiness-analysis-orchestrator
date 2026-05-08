# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | OpenAPITools--openapi-generator |
| **Date** | 2026-05-07 |
| **TD Version** | modernization-assessment |
| **Repo Type** | application |
| **Service Archetype** | stateless-utility (auto-detected) |
| **Priority** | P2 |
| **Tags** | java, code-generation, api |
| **Context** | Code-generation toolkit that produces clients/servers from OpenAPI specs. |
| **Overall Score** | 1.97 / 4.0 |
| **Surface Flags** | has_persistent_data_store=false, has_at_rest_data_surface=false, has_deployed_workload=true, has_api_surface=true, has_multi_instance_deployment=false |

**Archetype Justification**: No database connections or persistent state detected. The primary function is stateless code generation from OpenAPI specifications via CLI or REST endpoint. All operations are read-only transformations (spec in → code out). Classified as stateless-utility.

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | 1.67 / 4.0 | 🟠 Needs Work | Critical |
| Application Architecture (APP) | 2.50 / 4.0 | 🟡 Partial | Needs Work |
| Data Platform Modernization (DATA) | 2.50 / 4.0 | 🟡 Partial | Needs Work |
| Security Baseline (SEC) | 1.67 / 4.0 | 🟠 Needs Work | Critical |
| Operations & Observability (OPS) | 1.50 / 4.0 | ❌ Not Present | Needs Work |
| **Overall** | **1.97 / 4.0** | **🟠 Needs Work** | **Remediation Required** |

**Scoring Notes:**
- INF: Questions scored: INF-Q1=1, INF-Q5=1, INF-Q6=2, INF-Q7=1, INF-Q10=2, INF-Q11=3. Sum=10, Count=6. Score=10/6=1.67
- APP: Questions scored: APP-Q1=2, APP-Q2=4, APP-Q5=2, APP-Q6=2. Sum=10, Count=4. Score=10/4=2.50
- DATA: Questions scored: DATA-Q1=2, DATA-Q2=3. Sum=5, Count=2. Score=5/2=2.50
- SEC: Questions scored: SEC-Q1=1, SEC-Q3=2, SEC-Q4=1, SEC-Q5=2, SEC-Q6=2, SEC-Q7=2. Sum=10, Count=6. Score=10/6=1.67
- OPS: Questions scored: OPS-Q1=1, OPS-Q3=1, OPS-Q4=1, OPS-Q5=3, OPS-Q6=3, OPS-Q7=1, OPS-Q8=1, OPS-Q9=1. Sum=12, Count=8. Score=12/8=1.50

**Classification:** Remediation Required

This repo has 3 High findings, 18 Medium findings, 4 Low findings. The matched rule is "2-11 High → Remediation Required." MOD's classification rule differs from ARA: ARA's "1 High" is an agent-deployment gate (safety concern); MOD's "1 High" is typically a single modernization gap and maps to Pilot-Ready instead of the stricter Remediation Required threshold. With 3 High findings (INF-Q1, INF-Q5, SEC-Q1 — all core questions scoring 1), this repo requires remediation on foundational infrastructure and security dimensions before it meets cloud-native readiness.

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q1: Managed Compute | 1 | No managed compute — Docker images exist but no container orchestration (ECS/EKS/Fargate) or serverless deployment | Cannot auto-scale, no managed health checks, manual deployment model |
| 2 | SEC-Q1: Audit Logging | 1 | No CloudTrail or audit logging configuration found | No traceability for production operations or security forensics |
| 3 | SEC-Q4: Centralized Identity | 1 | No identity provider integration; online service has no authentication | Open API surface with no access control |
| 4 | INF-Q5: Network Security | 1 | No VPC, security group, or network segmentation configuration | Services deployed without network isolation |
| 5 | OPS-Q1: Distributed Tracing | 1 | No distributed tracing instrumentation | Cannot trace requests through the online service or diagnose latency issues |

## Quick Agent Wins

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists (APP-Q5 >= 2). The repository contains extensive documentation in `docs/`, `website/`, `README.md`, `CONTRIBUTING.md`, and per-generator documentation in `docs/generators/` (100+ files).
- **What it enables:** A RAG-based knowledge agent that indexes the project's documentation, configuration reference, and generator guides to answer developer questions about generator usage, customization, and template authoring.
- **Additional steps:** Index the `docs/` directory and `website/` content into a vector store. Add an API surface (e.g., via Amazon Bedrock Knowledge Bases) for querying.
- **Effort:** Medium

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 >= 2). The repository has 105 GitHub Actions workflows covering build, test, and release.
- **What it enables:** A DevOps agent that triggers sample regeneration, checks build status across the 105 workflows, and manages releases to Maven Central and Docker Hub.
- **Additional steps:** Expose GitHub Actions API for agent interaction; define agent permissions for workflow dispatch.
- **Effort:** Medium

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 4 (already well-decomposed modular architecture); primary trigger not met |
| 2 | Move to Containers | Not Triggered | — | — | Dockerfiles exist; contextual guard: already containerized (Dockerfile, multi-stage builds present) |
| 3 | Move to Open Source | Not Triggered | — | — | No commercial database engines detected; no proprietary SQL |
| 4 | Move to Managed Databases | Not Triggered | — | — | No persistent data store; INF-Q2 is Not Evaluated (archetype-N/A) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads; stateless-utility archetype with no streaming/ETL artifacts |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 2 (partial IaC coverage — no infrastructure definitions for deployment environment) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context |

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:**
- INF-Q10 = 2: No IaC defines the deployment environment for the online service or CLI tool distribution. Docker images are built but deployment targets (ECS tasks, EKS deployments, Lambda, etc.) are not codified.
- INF-Q11 = 3: CI/CD pipelines are extensive (105 workflows) with build, test, and Maven Central/Docker Hub release. However, IaC deployments are not automated because no IaC exists.
- OPS-Q5 = 3: Docker releases follow a basic push-to-registry model. No canary or blue/green deployment for the online service.
- OPS-Q6 = 3: Integration tests exist (CircleCI runs integration against Petstore) but coverage is focused on generated sample compilation, not the online service's runtime behavior.

**Recommended Actions:**
1. Define IaC for the online service deployment (prefer EKS per preferences, or ECS Fargate for simplicity)
2. Add deployment automation to the CI/CD pipeline for the online service
3. Implement blue/green or canary deployment for the online service using AWS CodeDeploy or EKS rolling updates
4. Add integration tests that validate the online service endpoint after deployment

**Representative AWS Services:** CodeBuild, CodePipeline, CodeDeploy, EKS, ECR, CloudFormation/CDK

**Learning Materials:**
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All compute is defined only as Docker images (Dockerfile, .hub.cli.dockerfile, .hub.online.dockerfile) without any managed container orchestration or serverless deployment. Images are published to Docker Hub but no ECS, EKS, Fargate, Lambda, or App Runner resources are defined. The online module runs as a standalone Spring Boot JAR in a Docker container with no orchestration layer. |
| **Gap** | No managed compute adoption. Docker images exist but are deployed manually or via Docker Hub pull with no orchestration, auto-scaling, or health management. |
| **Recommendation** | Deploy the online service to EKS (per preferences) or ECS Fargate with managed health checks, auto-scaling, and service discovery. Define the deployment as IaC using CDK or Terraform. |
| **Evidence** | `Dockerfile`, `.hub.cli.dockerfile`, `.hub.online.dockerfile`, `modules/openapi-generator-online/Dockerfile` — no `aws_ecs_*`, `aws_eks_*`, `aws_lambda_*` resources found anywhere in the repository. |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy a database. INF-Q2 does not apply. The openapi-generator is a stateless code generation tool with no persistent data store. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database connections, drivers, or ORM configurations found in any pom.xml or source code. No `aws_rds_*`, `aws_dynamodb_*` or similar resources. |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Workflow orchestration is not applicable by design — no multi-step workflows exist. The code generation process is a single-pass transformation (spec → code) with no state machine, saga, or multi-service coordination. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No `aws_sfn_*`, Temporal, or workflow SDK imports. Code generation is synchronous single-pass. |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Synchronous HTTP/gRPC is the correct design and is in use; no messaging needed. The online module accepts a POST request with an OpenAPI spec and returns generated code synchronously. This is architecturally correct for a stateless code generation utility. |
| **Gap** | N/A |
| **Recommendation** | Adopting async messaging is NOT recommended — it would add operational complexity without architectural benefit for this stateless utility. |
| **Evidence** | No SQS, SNS, Kafka, EventBridge, or messaging SDK imports. `modules/openapi-generator-online/` handles requests synchronously via Spring Boot `@RestController`. |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, NACL, or network segmentation configuration found. The online service exposes port 8080 via Docker with no network isolation defined. No IaC exists to provision networking infrastructure. |
| **Gap** | Services would be deployed without network isolation — no private subnets, no security groups, no network segmentation. |
| **Recommendation** | Define VPC with private subnets for the online service. Deploy behind an ALB or API Gateway in public subnets with the application in private subnets. Use security groups with least-privilege rules. Consider VPC endpoints for AWS service access. |
| **Evidence** | No `.tf` files with `aws_vpc`, `aws_subnet`, `aws_security_group`. No CloudFormation networking resources. `.hub.online.dockerfile` exposes port 8080 directly. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The online service runs on port 8080 with Spring Boot's embedded Tomcat. Docker Hub documentation suggests direct access to the container. No API Gateway, ALB, or CloudFront configuration exists in IaC or deployment configs. The Springfox Swagger UI is available at the service root for documentation. |
| **Gap** | No managed API entry point — no throttling, authentication, request validation, or traffic management at the gateway level. |
| **Recommendation** | Place the online service behind API Gateway (per preferences, consider API Gateway REST API or HTTP API) with throttling, authentication, and request validation. Alternatively, use an ALB with WAF rules if deploying to EKS. |
| **Evidence** | `modules/openapi-generator-online/src/main/resources/application.properties` (server.port=8080), `.hub.online.dockerfile` (EXPOSE 8080), Springfox swagger configuration. |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration found. The online service runs as a single Docker container with no scaling mechanisms. No ASG, ECS service scaling, or Lambda concurrency configuration exists. |
| **Gap** | Service cannot respond to traffic spikes. A single container handles all load with no horizontal scaling. |
| **Recommendation** | Deploy to EKS with Horizontal Pod Autoscaler (HPA) or ECS with target tracking scaling policies. Define min/max capacity based on expected traffic patterns. Code generation is CPU-intensive, so CPU-based scaling is appropriate. |
| **Evidence** | No `aws_autoscaling_*`, `aws_appautoscaling_*`, Kubernetes HPA, or ECS scaling policies found. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no persistent state to back up. INF-Q8 does not apply. The code generator is stateless — all outputs are returned to the caller or written to local filesystem during CLI use. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database, S3 bucket, EBS volume, or persistent storage defined. No `backup_retention_period` or `aws_backup_plan` resources. |

#### INF-Q9: High Availability

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload requiring HA evaluation. While `has_deployed_workload=true` (Dockerfiles exist), `has_multi_instance_deployment=false` — no deployment configuration defines multi-instance or multi-AZ deployment. The single Docker container model does not constitute an HA-evaluable deployment. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No multi-AZ configuration, no ASG, no ECS service with desired_count>1, no Kubernetes Deployment with replicas>1. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Dockerfiles define the container build (partial IaC for the application packaging layer). However, no infrastructure definitions exist for deploying those containers — no compute provisioning, networking, load balancing, monitoring, or operational resources are defined in any IaC format. The CI/CD workflows define build and release but not infrastructure provisioning. |
| **Gap** | 0% of deployment infrastructure is defined in IaC. Only container build definitions (Dockerfiles) exist, but no target deployment environment is codified. |
| **Recommendation** | Define the full deployment stack in IaC (prefer CDK or Terraform): VPC, EKS cluster or ECS cluster, service definitions, load balancer, auto-scaling, monitoring, and alarms. Start with the online service as the first workload to deploy via IaC. |
| **Evidence** | `Dockerfile`, `.hub.cli.dockerfile`, `.hub.online.dockerfile` exist. No `.tf`, `template.yaml`, `cdk.json`, `Chart.yaml`, or `kustomization.yaml` files found (excluding generated samples in `samples/`). |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Extensive CI/CD automation with 105 GitHub Actions workflows covering build, unit test, integration test (CircleCI), Docker image build, Maven Central release (with GPG signing), and Docker Hub release. The pipeline includes build, test, and publish stages. However, no deployment automation exists (no CodeDeploy, no EKS/ECS deployment step) because no deployment target infrastructure is defined. |
| **Gap** | CI/CD covers build and artifact publishing but lacks deployment automation to a running environment. The pipeline ends at "push to Docker Hub / Maven Central" with no automated deployment to compute infrastructure. |
| **Recommendation** | Extend the release pipeline with a deployment stage that deploys the online service Docker image to EKS/ECS. Add health check verification post-deployment. Consider implementing GitOps (ArgoCD or Flux) for the EKS deployment. |
| **Evidence** | `.github/workflows/openapi-generator.yaml` (build + test), `.github/workflows/maven-release.yml` (Maven Central publish), `.github/workflows/docker-release.yml` (Docker Hub push), `.github/workflows/docker.yaml` (Docker build test), `.circleci/config.yml` (integration tests). |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Java 11 compile target with Spring Boot 2.5.14 (online module) and Springfox 3.0.0 (deprecated). The runtime uses JDK 17 in Docker. This represents compound legacy: Java 11 (not current LTS), Spring Boot 2.5.x (EOL since November 2023), and Springfox (abandoned in favor of SpringDoc). No AWS SDK is used. |
| **Gap** | Java 11 + Spring Boot 2.5.14 + Springfox 3.0.0 represents compound regression across language version AND framework. Spring Boot 2.5.x is EOL and no longer receives security patches. Springfox is unmaintained. |
| **Recommendation** | Upgrade to Java 17 (compile target, aligning with Docker runtime), Spring Boot 3.x, and replace Springfox with SpringDoc OpenAPI. This unblocks access to modern Spring features, Jakarta EE namespace, and continued security support. |
| **Evidence** | `pom.xml` line 1230: `<maven.compiler.source>11</maven.compiler.source>`, `modules/openapi-generator-online/pom.xml` line 15: `<spring-boot.version>2.5.14</spring-boot.version>`, line 16: `<springfox-version>3.0.0</springfox-version>`. Docker images use `eclipse-temurin:17`. |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Well-decomposed modular architecture with 7 independently-buildable Maven modules: `openapi-generator-core` (interfaces), `openapi-generator` (engine), `openapi-generator-cli` (CLI interface), `openapi-generator-online` (REST service), `openapi-generator-maven-plugin`, `openapi-generator-gradle-plugin`, `openapi-generator-mill-plugin`. Each module has clear boundaries, separate POMs, and no circular dependencies. The online service is independently deployable (has its own Dockerfile and Spring Boot application). |
| **Gap** | N/A — well-structured modular architecture. |
| **Recommendation** | No decomposition needed. The current module structure is appropriate for a code generation toolkit. |
| **Evidence** | `pom.xml` modules section, separate `modules/*/pom.xml` for each module, independent Dockerfiles for `openapi-generator-cli` and `openapi-generator-online`. |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Sync request/response is the correct design; async not needed. The online module accepts synchronous POST requests with OpenAPI specs and returns generated code. The CLI processes specs synchronously from the filesystem. No inter-service communication exists. |
| **Gap** | N/A |
| **Recommendation** | N/A — synchronous request/response is architecturally correct for this stateless code generation utility. Converting to async would add complexity without benefit. |
| **Evidence** | `modules/openapi-generator-online/src/main/java/` — Spring Boot REST controllers handle requests synchronously. No message queue clients, event handlers, or async patterns. |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. No operations exceed 30 seconds — not applicable by design. Code generation from OpenAPI specs is CPU-bound but completes in seconds for typical specifications. Large specs may take longer via CLI (local filesystem, no timeout concern), but the online service handles typical requests within HTTP timeout bounds. |
| **Gap** | N/A |
| **Recommendation** | N/A — no long-running process infrastructure is needed for this utility. If very large spec generation becomes a concern for the online service, consider adding a queue-based async generation endpoint, but this is not currently a gap. |
| **Evidence** | No background job frameworks, no async/polling patterns, no job status APIs found in `modules/openapi-generator-online/`. |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The online service has a Swagger/OpenAPI documentation endpoint configured via Springfox but no API versioning strategy is visible. The API path is `/api-docs` for the Swagger spec. No `/v1/`, `/v2/` URL patterns, no version headers, and no versioning annotations found in the online module controllers. |
| **Gap** | No API versioning on the online service. Breaking changes to the generation API would affect all consumers simultaneously. |
| **Recommendation** | Implement URL-path versioning (e.g., `/v1/generate`) for the online service API. Document the versioning strategy and backward compatibility guarantees. |
| **Evidence** | `modules/openapi-generator-online/src/main/resources/application.properties`: `springfox.documentation.swagger.v2.path=/api-docs`. No version path segments in controller annotations. |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The online service is a standalone Spring Boot application with a fixed port (8080) configured in `application.properties`. No service discovery mechanism, service mesh, or dynamic endpoint resolution is configured. The Docker container exposes a static port. For a single-service deployment this is adequate, but does not support multi-instance or dynamic routing. |
| **Gap** | No service discovery mechanism. Endpoint is statically configured. |
| **Recommendation** | When deploying to EKS (per preferences), leverage Kubernetes service discovery (ClusterIP services, DNS-based discovery). If using ECS, configure AWS Cloud Map for service discovery. |
| **Evidence** | `application.properties`: `server.port=8080`. `.hub.online.dockerfile`: `EXPOSE 8080`. No service registry, Consul, or Cloud Map configuration. |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The project stores templates (Mustache/Handlebars) and generated code samples on the local filesystem. Template files are packaged within the JAR (`modules/openapi-generator/src/main/resources/`). Generated output is written to local filesystem in CLI mode or returned as HTTP response in online mode. No S3 or managed object storage is used for template storage or output persistence. |
| **Gap** | Templates and generated outputs are stored locally. No managed object storage for persisting generated code, caching common generations, or storing custom templates. |
| **Recommendation** | For the online service, consider using S3 to persist generated code outputs with expiring presigned URLs for download. This enables async generation for large specs and avoids memory pressure from holding large outputs in-flight. |
| **Evidence** | Template files in `modules/openapi-generator/src/main/resources/` (Mustache templates). No `aws_s3_bucket` or S3 SDK usage found. |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The code generation engine has a well-structured internal data access pattern. Templates are loaded through a unified `TemplateManager` and code generation flows through a centralized `DefaultGenerator` class. Configuration is accessed through `CodegenConfig` interfaces. The data access pattern for reading OpenAPI specs is centralized through the Swagger Parser library. This is a mostly-centralized design with clean interfaces. |
| **Gap** | Minor — some generators access template resources directly rather than through the centralized template management layer, but this is consistent within the module boundary pattern. |
| **Recommendation** | No significant action needed. The current centralized design is appropriate for a template-based code generator. |
| **Evidence** | `modules/openapi-generator/src/main/java/org/openapitools/codegen/` — `DefaultGenerator.java`, `CodegenConfig.java` interfaces, template loading via centralized resource resolution. |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `application` repository with no database. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `application` repository with no database. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail, audit logging configuration, or any form of request/action logging infrastructure found. The online service uses SLF4J with basic console logging but no structured audit trail for API requests, generation events, or administrative actions. No log aggregation, immutable storage, or log retention policies are defined. |
| **Gap** | No audit logging for the online service. API calls are not traceable. No forensic analysis capability. |
| **Recommendation** | Enable CloudTrail for the AWS account hosting the service. Add structured request logging (JSON format) to the online service with correlation IDs. Ship logs to CloudWatch Logs with defined retention. Consider S3 with Object Lock for immutable audit storage. |
| **Evidence** | `pom.xml`: `<slf4j.version>1.7.36</slf4j.version>` (basic logging only). No `aws_cloudtrail`, CloudWatch Logs configuration, or log aggregation setup found. |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no database, S3 bucket, EBS volume, or similar. SEC-Q2 does not apply. The code generator is stateless and does not persist data. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No data stores, S3 buckets, EBS volumes, or EFS file systems defined in any configuration. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The online service has no authentication. The Spring Boot application exposes its code generation API on port 8080 with no auth middleware, no API Gateway authorizer, no OAuth2/JWT validation, and no API key requirement. The Springfox configuration provides Swagger UI without any security. The application.properties contains no security configuration. |
| **Gap** | API endpoints are open — no authentication mechanism protects the online code generation service. |
| **Recommendation** | Add API authentication via API Gateway with Cognito authorizer or JWT validation. At minimum, implement API key authentication for rate limiting. For internal deployment, network isolation (VPC private subnet) combined with IAM-based auth via API Gateway would be appropriate. |
| **Evidence** | `modules/openapi-generator-online/src/main/resources/application.properties` — no security config. No Spring Security dependency in `modules/openapi-generator-online/pom.xml`. No auth annotations in controllers. |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No identity provider integration exists. The online service has no authentication at all — no Cognito, no OIDC, no SAML, no SSO. The application manages no user accounts or sessions. It is a stateless utility with no access control. |
| **Gap** | No centralized identity integration. The service is completely open. |
| **Recommendation** | Integrate with a centralized identity provider (Cognito or corporate IdP via OIDC) when deploying to production. For internal-only deployment, consider IAM authentication via API Gateway. |
| **Evidence** | No `aws_cognito_*` resources, no OIDC/SAML configuration, no Spring Security imports, no identity provider federation. |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | CI/CD secrets are managed through GitHub Actions secrets (GPG_PRIVATE_KEY, GPG_PASSPHRASE, OSS_USERNAME, OSS_PASSWORD, GRADLE_ENTERPRISE_ACCESS_KEY) — these are not hardcoded in source. The encrypted GPG key file (`sec.gpg.enc`) is committed but encrypted. No plaintext credentials are present in source code or configuration files. However, no AWS Secrets Manager, Vault, or runtime secrets management is configured for the application itself. |
| **Gap** | No runtime secrets management system. CI secrets are properly handled via GitHub Actions, but if the service were deployed to AWS, no mechanism exists for managing runtime credentials (database passwords, API keys for downstream services, etc.). |
| **Recommendation** | When deploying to AWS, use Secrets Manager or SSM Parameter Store (SecureString) for any runtime configuration that contains sensitive values. Configure secrets rotation for long-lived credentials. |
| **Evidence** | `.github/workflows/maven-release.yml` uses `${{ secrets.GPG_PRIVATE_KEY }}`, `${{ secrets.OSS_USERNAME }}`. `sec.gpg.enc` is encrypted. No plaintext secrets in `application.properties` or source code. |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Docker images use `eclipse-temurin:17-jre` as the base (a well-maintained, regularly-updated JDK image). Multi-stage builds minimize the attack surface by only including the JRE and application JAR in the final image. However, no vulnerability scanning (Inspector, Snyk, Trivy) is configured for the Docker images, and no patching automation exists. |
| **Gap** | No container image vulnerability scanning. No automated patching or rebuild triggers when base image updates are available. |
| **Recommendation** | Add container image scanning in CI (ECR image scanning, Trivy, or Snyk Container). Configure Dependabot or Renovate to automatically update the base image version. Consider using Bottlerocket or a minimal base image for production. |
| **Evidence** | `.hub.cli.dockerfile`: `FROM eclipse-temurin:17-jre`, `.hub.online.dockerfile`: `FROM eclipse-temurin:17-jre` (multi-stage). No Trivy, Snyk, or Inspector configuration in workflows. |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Static analysis tools are configured in the Maven build: SpotBugs (findbugs), PMD, and Checkstyle run during the `verify` phase via the `static-analysis` Maven profile. The `forbiddenapis` plugin checks for unsafe JDK API usage. However, these are code quality tools, not security-focused SAST. No dependency vulnerability scanning (Dependabot, OWASP dependency-check, Snyk) is configured. No container scanning. No security gate that blocks the pipeline on critical findings. |
| **Gap** | No dependency vulnerability scanning (no Dependabot, no OWASP dependency-check). No SAST tool focused on security vulnerabilities (SpotBugs/PMD are quality tools). No container image scanning. No blocking security gate. |
| **Recommendation** | Enable Dependabot for dependency vulnerability alerts. Add OWASP dependency-check or Snyk to the Maven build. Consider adding CodeGuru Reviewer or Semgrep for security-focused SAST. Add ECR image scanning for container images. Configure a pipeline gate that blocks releases with critical/high vulnerabilities. |
| **Evidence** | `pom.xml` static-analysis profile: SpotBugs 3.1.12.2, PMD 3.12.0, Checkstyle 3.1.0. `forbiddenapis` 3.5.1. No Dependabot config (`.github/dependabot.yml`), no Snyk config, no OWASP dependency-check plugin. |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumentation found. No OpenTelemetry SDK, no X-Ray agent, no tracing library in dependencies. The online service uses only SLF4J for basic logging with no trace ID propagation or request correlation. |
| **Gap** | No tracing capability. Cannot trace requests through the online service or correlate logs across components. |
| **Recommendation** | Add OpenTelemetry Java agent to the online service Docker image. Configure X-Ray as the tracing backend. This enables request tracing, latency analysis, and error correlation with minimal code changes (auto-instrumentation). |
| **Evidence** | No OpenTelemetry, X-Ray, or Zipkin dependencies in any `pom.xml`. No `traceparent` or `X-Amzn-Trace-Id` header handling. SLF4J 1.7.36 is the only logging framework. |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | While `has_api_surface=true`, the online service has no deployed monitoring infrastructure to evaluate SLOs against. No CloudWatch alarms, no latency metrics, no error budget tracking. Without a deployed environment, SLO evaluation is premature. This is gated by the absence of deployed monitoring infrastructure rather than the absence of an API surface. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No SLO definitions, no CloudWatch alarms, no monitoring configuration. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom metrics are published. No CloudWatch PutMetricData calls, no metrics SDK, no business event tracking. The service does not track generation success/failure rates, languages generated, spec sizes, or generation latency as metrics. |
| **Gap** | No business metrics — cannot measure generation throughput, success rates by language, or usage patterns. |
| **Recommendation** | Add custom CloudWatch metrics for: generation requests (count, by language/framework), generation failures (count, by error type), generation latency (p50, p95, p99), spec size distribution. This enables usage-based scaling and feature prioritization. |
| **Evidence** | No CloudWatch SDK dependency, no `putMetricData` calls, no metrics instrumentation in source code. |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting configured. No CloudWatch alarms, no anomaly detection, no PagerDuty/OpsGenie integration. The service has no monitoring infrastructure to detect degradation or failures. |
| **Gap** | No alerting — service degradation or failures would go unnoticed until user reports. |
| **Recommendation** | Define CloudWatch alarms for error rate, latency p99, and CPU utilization. Enable CloudWatch anomaly detection on latency and error rate metrics. Configure SNS notifications to an ops channel for alarm state changes. |
| **Evidence** | No `aws_cloudwatch_metric_alarm`, no alarm definitions, no monitoring integration found. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Docker images are published to Docker Hub via GitHub Actions release workflow. The online service Docker image uses multi-stage builds for consistent artifacts. While no deployment target (EKS/ECS) is defined, the Docker Hub release process is automated and produces versioned images (tagged with release version). This provides a foundation for blue/green or canary deployment once a target environment is defined. |
| **Gap** | No deployment strategy for the online service beyond Docker Hub push. No canary, blue/green, or staged rollout because no deployment target exists. |
| **Recommendation** | When deploying to EKS, implement rolling updates with readiness probes. Consider ArgoCD for GitOps-based deployment with automatic rollback on failed health checks. |
| **Evidence** | `.github/workflows/docker-release.yml` publishes versioned images. Multi-stage Dockerfiles produce consistent artifacts. No CodeDeploy, Argo Rollouts, or deployment strategy configuration. |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Integration tests exist via CircleCI that spins up a Petstore mock service and runs generated client tests against it. The CI matrix tests generated samples across 60+ languages/frameworks. However, integration tests for the online service's own API (testing the generation endpoint with various specs) are not clearly defined as a separate test suite. The focus is on validating generated code quality rather than the online service's runtime behavior. |
| **Gap** | Integration testing focuses on generated code compilation/functionality, not on the online service's own HTTP API behavior (error handling, timeouts, large specs, concurrent requests). |
| **Recommendation** | Add integration tests that exercise the online service's API: POST specs of varying sizes, verify error responses for malformed specs, test concurrent generation requests, and validate output format consistency. Run these in CI against a Docker container of the online service. |
| **Evidence** | `.circleci/config.yml` runs integration tests with Petstore mock. 90+ `samples-*` workflows test generated code. No dedicated online service API test suite found. |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, no incident response automation, no self-healing patterns. No Systems Manager Automation documents, no Lambda-based remediation, no incident workflow definitions. |
| **Gap** | Incident response would be entirely ad hoc. No documented procedures for common failure scenarios. |
| **Recommendation** | Create runbooks for common scenarios: online service health check failure (restart container), high memory usage during large spec generation (scale out), Maven Central publish failure (retry procedure). Store as SSM Automation documents for automated execution. |
| **Evidence** | No runbook files, no SSM documents, no incident automation found in the repository. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership defined. No CODEOWNERS for monitoring configs, no per-service dashboards, no team-attributed alarms. The repository has no monitoring infrastructure to own. |
| **Gap** | No observability ownership — monitoring is nonexistent, not just unowned. |
| **Recommendation** | When deploying to AWS, define observability ownership in CODEOWNERS. Create a service dashboard with key metrics (generation latency, error rate, throughput). Assign alarm ownership to the team responsible for the online service. |
| **Evidence** | No CODEOWNERS file referencing monitoring assets, no dashboard definitions, no team-attributed alarms. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging found — no IaC exists to tag. Docker images are tagged with version numbers but no AWS resource tagging governance (cost allocation, ownership, environment) is defined. |
| **Gap** | No tagging governance. When AWS resources are created for deployment, there is no standard for cost allocation, ownership, or environment identification. |
| **Recommendation** | Define a tagging standard before creating AWS resources: Environment (dev/staging/prod), Service (openapi-generator-online), Team, CostCenter. Implement via `default_tags` in Terraform provider or CDK aspects. Enable AWS Config `required-tags` rule. |
| **Evidence** | No `default_tags`, no `tags` blocks, no Tag Policies, no AWS Config rules found. |

## Learning Materials

- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `pom.xml` | INF-Q11, APP-Q1, SEC-Q7 | Root Maven POM — Java 11 target, dependency versions, static analysis plugins |
| `modules/openapi-generator-online/pom.xml` | APP-Q1, SEC-Q3 | Online module POM — Spring Boot 2.5.14, Springfox 3.0.0 |
| `modules/openapi-generator-online/src/main/resources/application.properties` | INF-Q6, APP-Q5, APP-Q6 | Spring Boot config — port 8080, Springfox path |
| `Dockerfile` | INF-Q1, INF-Q10 | Full development build Docker image |
| `.hub.cli.dockerfile` | INF-Q1, SEC-Q6 | CLI Docker Hub release image (multi-stage, eclipse-temurin:17-jre) |
| `.hub.online.dockerfile` | INF-Q1, INF-Q6, SEC-Q6 | Online service Docker Hub release image (multi-stage) |
| `.github/workflows/openapi-generator.yaml` | INF-Q11 | Main build + unit test workflow (JDK 11) |
| `.github/workflows/maven-release.yml` | INF-Q11, SEC-Q5 | Maven Central release workflow with GPG signing |
| `.github/workflows/docker-release.yml` | INF-Q11, OPS-Q5 | Docker Hub release workflow |
| `.github/workflows/docker.yaml` | INF-Q11 | Docker build test workflow |
| `.circleci/config.yml` | OPS-Q6 | CircleCI integration tests with Petstore mock |
| `sec.gpg.enc` | SEC-Q5 | Encrypted GPG key for Maven Central signing |
| `modules/openapi-generator/src/main/resources/` | DATA-Q1 | Template files (Mustache) for code generation |
| `docs/` | Quick Agent Wins | Project documentation (100+ files) |
| `website/` | Quick Agent Wins | Docusaurus documentation site |
| `spotbugs-exclude.xml` | SEC-Q7 | SpotBugs analysis exclusion rules |
| `google_checkstyle.xml` | SEC-Q7 | Checkstyle configuration |
