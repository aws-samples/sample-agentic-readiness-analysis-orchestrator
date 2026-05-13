# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | bpmn-miwg-test-suite |
| **Date** | 2025-07-15 |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P1 |
| **Tags** | standard-bpmn, multi-vendor, omg-official |
| **Context** | OMG official BPMN 2.0 Model Interchange test cases with reference models exported from multiple vendor tools. |
| **Overall Score** | 1.28 / 4.0 |

**Archetype Justification**: Auto-detection was inconclusive — the repository contains no application runtime code, no database connections, no API endpoints, and no entry points. The `pom.xml` packages BPMN XML test data into a jar artifact using Maven. Since no runtime signals exist to classify an archetype, the conservative default `stateful-crud` is applied per TD rules.

> **Note:** This repository is classified as `application` per the provided context, but it functions as a **test data repository** — it packages BPMN 2.0 XML reference models and vendor test results into a Maven jar. It contains no application source code, no deployable services, no infrastructure-as-code, and no database configurations. The low overall score reflects this reality: the repository was not designed to be a cloud-deployed application and lacks the artifacts that a modernization assessment evaluates.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.09 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 1.17 / 4.0 | ❌ Not Present |
| Data Platform Modernization (DATA) | 1.75 / 4.0 | 🟠 Needs Work |
| Security Baseline (SEC) | 1.29 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.11 / 4.0 | ❌ Not Present |
| **Overall** | **1.28 / 4.0** | **❌ Not Present** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC files found — all infrastructure (if any) is manual or absent. | Blocks reproducible deployments, disaster recovery, and environment consistency. Foundation for all modernization pathways. |
| 2 | INF-Q1: Managed Compute | 1 | No compute infrastructure defined — no EC2, ECS, EKS, Lambda, or Fargate resources. | No cloud compute foundation exists. Any modernization requires establishing compute infrastructure from scratch. |
| 3 | APP-Q2: Monolith vs Microservices | 1 | Single jar packaging with no module boundaries, no microservices, no deployable application architecture. | Triggers Move to Cloud Native pathway. No decomposition possible without first establishing an application architecture. |
| 4 | SEC-Q7: Application Security Pipeline | 1 | No SAST, DAST, or dependency scanning in CI/CD pipeline. | Vulnerabilities in dependencies (Maven, BPMN tools) go undetected. Security gate absent from build process. |
| 5 | OPS-Q5: Deployment Strategy | 1 | Direct push to GitHub Pages with no staged rollout, canary, or blue/green deployment. | Regressions in analysis results or site content affect all users immediately with no rollback mechanism. |

---

## Quick Agent Wins

No Quick Agent Wins identified. The system lacks the foundational capabilities (API documentation, CI/CD automation beyond basic build/deploy, structured logging, workflow orchestration) needed to support agent integration. While a CI/CD pipeline exists (INF-Q11 = 3), it is a build/publish pipeline for test data — not a deployment pipeline for a running application. Address the gaps identified in this assessment before pursuing agent opportunities.

**Prerequisite evaluation:**
- ❌ API docs exist (APP-Q5 = 1) — No API endpoints or documentation.
- ❌ Database with clear schema (DATA-Q2 = 1) — No database.
- ✅ CI/CD pipeline exists (INF-Q11 = 3) — GitHub Actions pipeline exists, but it builds and publishes static test data, not a deployable application. A DevOps agent would have limited value in this context.
- ✅ Documentation exists — README.md provides comprehensive documentation about the test suite. However, there is no application to build a knowledge agent around — the documentation describes test procedures for external BPMN tools, not internal system behavior.
- ❌ Workflow orchestration (INF-Q3 = 1) — No orchestration.
- ❌ Structured logging/tracing (OPS-Q1 = 1) — No observability.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2 = 1 (primary), INF-Q1 = 1 (supporting), APP-Q3 = 1 (supporting), APP-Q4 = 1 (supporting) |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1 = 1 (primary), no container definitions found (supporting). No Lambda/Fargate/ECS detected — guard not triggered. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 — no stored procedures or proprietary SQL. No commercial database engines detected. |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = 1 but no databases exist at all — no self-managed databases to migrate. Pathway is not meaningful without existing databases. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 1 but no data processing workloads exist. Contextual guard prevents trigger — no streaming, ETL, or analytics artifacts found. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (primary), OPS-Q5 = 1 (supporting), OPS-Q6 = 2 (supporting) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. Context: "OMG official BPMN 2.0 Model Interchange test cases" contains no AI-related signal terms. |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:**
The repository is a single Maven jar project (`pom.xml`) that packages BPMN 2.0 XML reference models and PNG images into a distributable artifact. There is no application runtime — no entry point (`main()`), no server, no API surface. The "application" is a test data packaging pipeline, not a deployed service. APP-Q2 scored 1 (tightly-coupled monolith) because the entire repository is a single deployable unit with no module boundaries or service separation.

**Compute Model Gaps:**
INF-Q1 scored 1 — no compute infrastructure exists. There are no EC2 instances, no ECS/EKS clusters, no Lambda functions, and no Fargate tasks defined in the repository. The only "deployment" is publishing static HTML analysis results to GitHub Pages.

**Communication Pattern Gaps:**
APP-Q3 scored 1 and APP-Q4 scored 1 — there are no inter-service communication patterns because there are no services. No async messaging, no synchronous HTTP calls between services, no long-running process handling.

**Recommended Decomposition Approach:**
Given that this repository is a test data suite rather than a running application, the Move to Cloud Native pathway should be interpreted as: **if this test suite needs to become a cloud-deployed service** (e.g., an automated BPMN validation API), it would need to be designed from scratch as cloud-native rather than decomposed from an existing monolith. See the Decomposition Strategy section below for approach options.

**Representative AWS Services:** Lambda, API Gateway, Step Functions, EventBridge, S3, ECS/EKS
**Recommended Patterns:** If building a BPMN validation service — Hexagonal Architecture for clean service boundaries, Event Sourcing for tracking test submissions over time.
**AWS Prescriptive Guidance:** [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model:**
No compute infrastructure exists. The Maven build runs in GitHub Actions (ubuntu-latest runner) and produces a jar artifact and static HTML site. There are no Dockerfiles, no docker-compose files, and no Kubernetes manifests.

**Container Readiness Indicators:**
- The Maven build process (`mvn -P analysis --batch-mode deploy`) is self-contained and could be containerized for reproducible builds
- The build depends on JDK 11 (set up in GitHub Actions) and Maven — standard containerizable toolchain
- The output (jar artifact + static site) could be served from a containerized web server

**Recommended Container Orchestration:**
If the BPMN analysis tooling needs to be containerized for local development or deployment beyond GitHub Actions, start with a Dockerfile for the Maven build environment. For serving the analysis results, a lightweight container (nginx or similar) could host the static site.

**Representative AWS Services:** ECR (for storing container images), ECS or EKS (for orchestration), App Runner (for simple web hosting)
**Migration Approach:** Lift-and-containerize the Maven build into a Docker image, then evaluate whether a persistent web service is needed.
**AWS Guidance:** [Containerize applications](https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-containers/welcome.html)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage:**
INF-Q10 scored 1 — no infrastructure-as-code exists in the repository. There are no Terraform files, CloudFormation templates, CDK constructs, or Helm charts. All infrastructure (GitHub Pages hosting, GitHub Packages) is configured through GitHub settings, not code.

**Current CI/CD State:**
INF-Q11 scored 3 — GitHub Actions workflows exist:
- `maven.yml`: Builds with Maven, deploys to GitHub Packages, publishes analysis results to GitHub Pages via `peaceiris/actions-gh-pages@v4`
- `release.yml`: Creates a zip release artifact when a GitHub release is published
These provide basic CI/CD but lack testing gates, security scanning, and deployment strategies.

**Deployment Strategy Gaps:**
OPS-Q5 scored 1 — the GitHub Actions pipeline pushes directly to GitHub Pages with no staged rollout. There is no canary deployment, no blue/green strategy, and no rollback mechanism.

**Testing Gaps:**
OPS-Q6 scored 2 — the Maven `analysis` profile runs BPMN MIWG analysis tools during the test phase, providing automated validation of BPMN files. However, there are no integration tests for the CI/CD pipeline itself, and no test coverage reporting.

**Recommended DevOps Improvements:**
1. **Add IaC for GitHub Pages hosting** — Define infrastructure configuration in code (even if minimal for a static site)
2. **Add dependency scanning** — Configure Dependabot or `mvn dependency:analyze` in the pipeline to catch vulnerable Maven dependencies
3. **Add SAST scanning** — Integrate a static analysis tool for the BPMN XML validation
4. **Implement deployment verification** — Add a post-deploy check that validates the GitHub Pages site is serving correctly after deployment

**Representative AWS Services:** CodeBuild, CodePipeline, CloudFormation/CDK (if migrating hosting to AWS), S3 + CloudFront (for static site hosting with deployment controls)
**AWS Prescriptive Guidance:** [Getting Started with DevOps on AWS](https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-devops/welcome.html)

---

## Decomposition Strategy

> **Conditional Section:** Included because APP-Q2 = 1 (< 3).

### Context

The bpmn-miwg-test-suite repository scored 1 on APP-Q2 (Monolith vs Microservices). However, this is not a traditional monolith — it is a test data packaging project with no application source code. The "monolith" is a Maven build that packages BPMN XML files into a jar artifact and generates HTML analysis reports. Decomposition in the traditional sense (extracting microservices from a monolith) does not directly apply.

**If the OMG BPMN MIWG decides to modernize this into a cloud-deployed service**, the following approaches would apply:

### Decomposition Approach Options

| Approach | Description | When to Use | Level of Effort | Recommendation |
|----------|-------------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Build new BPMN validation services alongside the existing Maven-based pipeline. Gradually migrate analysis capabilities to cloud services while keeping the current GitHub Actions workflow running. | If the goal is incremental migration to AWS-hosted BPMN validation with minimal disruption to existing contributors. | **Medium** — 3-6 months for initial service, ongoing migration. | ✅ **Recommended.** Build a cloud-native BPMN validation API while maintaining the existing GitHub-based workflow for contributors. |
| **Conditional / Adaptive** | Containerize the Maven build as-is, then selectively extract high-value capabilities (e.g., BPMN XML validation, report generation) into separate services. | If the team wants quick containerization wins before committing to full service decomposition. | **Low to Medium** — containerization in 1-2 weeks, selective extraction over 2-6 months. | ✅ **Recommended as a starting point.** Low risk, immediate reproducibility benefit. |
| **Big-Bang Rewrite** | Rewrite the entire test suite infrastructure as a modern cloud-native platform from scratch. | Not recommended for this repository — the existing Maven pipeline works and is well-understood by OMG MIWG contributors. | **High** — 6-12 months. Risk of breaking contributor workflows. | ⚠️ **Not recommended.** The current pipeline serves its purpose. Incremental improvement is safer. |

### Pattern Recommendations

| Pattern | Purpose | When to Apply |
|---------|---------|---------------|
| **Hexagonal Architecture** | Structure any new BPMN validation service with clear ports (HTTP API, S3 events) and adapters (BPMN parser, report generator). | If building a cloud-native BPMN validation API. |
| **Event Sourcing** | Track test submissions, tool versions, and validation results as an event stream. | If building a historical record of BPMN interchange test results. |

### Effort Estimation

| Factor | Current State | Effort Impact |
|--------|--------------|---------------|
| Module boundaries | No modules — single Maven build | Medium — need to design service boundaries from scratch |
| Data coupling | No database — all data is flat files in Git | Low — no database migration needed |
| Stored procedures | None (DATA-Q4 = 4) | Low — no database logic to extract |
| Communication patterns | None | Low — no existing patterns to migrate |
| CI/CD maturity | GitHub Actions exists (INF-Q11 = 3) | Low — pipeline exists and can be extended |
| Test coverage | BPMN analysis tools run as tests (OPS-Q6 = 2) | Medium — validation exists but needs expansion |

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute infrastructure is defined in the repository. There are no Terraform resources (`aws_ecs_*`, `aws_eks_*`, `aws_lambda_*`, `aws_instance`), no CloudFormation templates, no CDK constructs, and no Kubernetes manifests. The only compute is the GitHub Actions runner (`ubuntu-latest`) used for CI/CD builds. The repository packages BPMN XML test data into a Maven jar — it does not deploy a running application. |
| **Gap** | Complete absence of managed compute infrastructure. No EC2, ECS, EKS, Lambda, or Fargate resources defined. |
| **Recommendation** | If the BPMN MIWG test suite needs to be deployed as a cloud service (e.g., BPMN validation API), define compute infrastructure using IaC. Consider Lambda for the BPMN analysis tooling (event-driven, stateless) or ECS/Fargate for containerized builds. For static site hosting, consider S3 + CloudFront instead of GitHub Pages. |
| **Evidence** | `pom.xml` (jar packaging, no compute resources), `.github/workflows/maven.yml` (GitHub Actions runner only), absence of any `.tf`, `template.yaml`, `cdk.json`, `Dockerfile`, or Kubernetes manifests in repository. |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database infrastructure exists. No `aws_rds_*`, `aws_dynamodb_*`, `aws_docdb_*` resources in IaC (no IaC exists). No database connection strings, driver imports, or ORM configurations found in the repository. The repository stores all data as flat BPMN XML files and PNG images in Git. |
| **Gap** | No database infrastructure — neither managed nor self-managed. All data is stored as flat files in Git. |
| **Recommendation** | If the test suite evolves to require persistent structured data (e.g., test results database, tool registry), use a managed database service (DynamoDB for tool/test metadata, Aurora PostgreSQL for relational test result storage). |
| **Evidence** | Absence of any database-related IaC, configuration files, connection strings, or ORM imports across the entire repository. `tools-tested-by-miwg.json` and `test-case-structure.json` serve as flat-file data stores. |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No workflow orchestration services are defined. No `aws_sfn_*` (Step Functions), no Temporal SDK imports, no workflow YAML definitions. The Maven build pipeline (`mvn -P analysis --batch-mode deploy`) executes BPMN analysis as a linear build process — not a managed orchestration workflow. The `publish.sh` script is a sequential shell script with no error handling, retry logic, or state management. Using stateful-crud archetype calibration: while no multi-step business workflows exist, the absence of any orchestration for the analysis pipeline (which involves multiple steps: scan, generate bounds, copy resources, run MIWG tests, generate site) represents a gap. |
| **Gap** | No dedicated workflow orchestration. The analysis pipeline is a sequential Maven build with no managed state, retry, or error handling. |
| **Recommendation** | If the analysis pipeline needs reliability and visibility, consider AWS Step Functions to orchestrate the BPMN analysis workflow: trigger on new submissions → validate BPMN XML → generate analysis → publish results. This would replace the current linear Maven build with a managed, observable workflow. |
| **Evidence** | `pom.xml` (Maven lifecycle, no orchestration), `publish.sh` (sequential shell script), `.github/workflows/maven.yml` (linear GitHub Actions workflow). |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No messaging or streaming infrastructure exists. No SQS, SNS, EventBridge, MSK, Kinesis, or Amazon MQ resources defined. No message queue consumers or event-driven handlers found. Using stateful-crud archetype calibration: the absence of async messaging for cross-service state changes represents a gap. However, the repository has no services to communicate between — this is a test data packaging project. |
| **Gap** | No messaging infrastructure. The repository has no inter-service communication of any kind. |
| **Recommendation** | If the test suite evolves into a multi-service architecture (e.g., submission intake → validation → report generation → notification), implement managed messaging with EventBridge for event routing and SQS for decoupled processing. For now, messaging is not needed for a test data packaging repository. |
| **Evidence** | Absence of any messaging/streaming IaC resources, SDK imports, or event-driven patterns in the entire repository. |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or NACL configurations found. No network segmentation. The repository does not define any AWS networking resources. The only "deployment" is to GitHub Pages (external to AWS). |
| **Gap** | Complete absence of network security configuration. No VPC, no private subnets, no security groups. |
| **Recommendation** | If migrating to AWS, define a VPC with private subnets for any compute resources, least-privilege security groups, and VPC endpoints for AWS service access. For a static site, network security is managed by CloudFront/S3 access controls. |
| **Evidence** | Absence of any `aws_vpc`, `aws_subnet`, `aws_security_group` resources or networking configuration in the repository. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, AppSync, ALB, or CloudFront is configured as an entry point. The repository does not expose any API. The GitHub Pages site is the only user-facing endpoint, served directly by GitHub's infrastructure with no AWS entry point. |
| **Gap** | No managed API entry point. No throttling, authentication, or request validation at the entry point level. |
| **Recommendation** | If building a BPMN validation API, use API Gateway (HTTP API) with throttling and request validation. For the static analysis results site, consider CloudFront as a CDN with caching and DDoS protection. |
| **Evidence** | Absence of any `aws_api_gateway_*`, `aws_apigatewayv2_*`, `aws_lb_*`, or `aws_cloudfront_*` resources. |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. No `aws_autoscaling_*` or `aws_appautoscaling_*` resources. No Lambda concurrency limits, no DynamoDB auto-scaling. There are no scalable resources in the repository. |
| **Gap** | No auto-scaling — no scalable resources exist to configure auto-scaling for. |
| **Recommendation** | Auto-scaling would become relevant when compute resources are provisioned. If using Lambda for BPMN validation, concurrency limits serve as the scaling mechanism. If using ECS, configure application auto-scaling with target tracking. |
| **Evidence** | Absence of any auto-scaling resources or configuration in the repository. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No automated backup configuration exists. No `aws_backup_plan`, no `backup_retention_period` on any database, no S3 versioning, no EBS snapshot policies. The repository's data is version-controlled in Git, which provides a form of backup through commit history, but this is not a managed backup strategy with defined retention periods or tested restores. |
| **Gap** | No backup and recovery strategy. Git commit history is the only "backup" mechanism. |
| **Recommendation** | The Git repository on GitHub provides reasonable backup for the BPMN test data. If migrating data to AWS, enable S3 versioning for BPMN files and configure AWS Backup for any databases. Implement cross-region replication for critical data. |
| **Evidence** | Absence of any `aws_backup_*` resources, `backup_retention_period` parameters, or S3 versioning configuration. |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ configuration exists. No `multi_az = true` on databases, no `availability_zones` spanning multiple AZs in ASGs. No AWS resources are defined to evaluate for fault isolation. GitHub Pages (the current hosting platform) is managed by GitHub with its own availability guarantees. |
| **Gap** | No HA configuration — no AWS resources exist to configure for high availability. |
| **Recommendation** | When provisioning AWS resources, ensure all production compute and data stores span 2+ AZs. For a static site on S3 + CloudFront, high availability is built into the service. |
| **Evidence** | Absence of any multi-AZ configuration, availability zone specifications, or load balancer cross-zone settings. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No infrastructure-as-code files found in the repository. No `.tf` (Terraform), no CloudFormation templates, no `cdk.json` (CDK), no Helm charts, no Kustomize files, no Ansible playbooks. All infrastructure — GitHub Pages hosting, GitHub Packages artifact publishing — is configured through GitHub's web UI or implicit conventions, not code. |
| **Gap** | Zero IaC coverage. All infrastructure is manually configured or platform-managed (GitHub). |
| **Recommendation** | Define infrastructure as code even for simple setups. If staying on GitHub: use GitHub's Terraform provider to manage repository settings, branch protection rules, and Pages configuration. If migrating to AWS: define all resources (S3, CloudFront, IAM roles, CodePipeline) in Terraform or CDK. |
| **Evidence** | Absence of any `.tf`, `*.cfn.yaml`, `*.cfn.json`, `cdk.json`, `Chart.yaml`, `kustomization.yaml`, or `*.yml` Ansible playbooks in the repository. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Two GitHub Actions workflows exist: (1) `.github/workflows/maven.yml` — triggered on push/PR to master and manual dispatch; builds with Maven using JDK 11, deploys jar to GitHub Packages, uploads site artifacts, and publishes analysis results to GitHub Pages via `peaceiris/actions-gh-pages@v4`. (2) `.github/workflows/release.yml` — triggered on release publication; creates a zip of Reference BPMN/PNG files and attaches it to the GitHub release. The pipeline includes build and deploy stages. The Maven `analysis` profile runs BPMN MIWG tools during the test phase, providing automated validation. |
| **Gap** | No automated rollback mechanism. No security scanning stage. No approval gates or environment promotion. Limited automated testing — only BPMN analysis tool validation, no unit tests or integration tests for the pipeline itself. |
| **Recommendation** | Add dependency vulnerability scanning (e.g., `mvn dependency-check:check` via OWASP Dependency-Check plugin, or Dependabot). Add a post-deployment validation step that checks the GitHub Pages site is serving correctly. Consider adding branch protection rules requiring status checks before merge. |
| **Evidence** | `.github/workflows/maven.yml` (build + deploy pipeline), `.github/workflows/release.yml` (release artifact pipeline), `pom.xml` (Maven `analysis` profile with `bpmn-miwg-maven-plugin` test execution). |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The `pom.xml` specifies `<java.version>1.6</java.version>` as the target Java version, though the GitHub Actions workflow sets up JDK 11 for the actual build. There is no Java source code in the repository — the Maven build packages BPMN XML files and invokes external BPMN MIWG tools (dependencies: `bounds-generator` and `submission-counter` from `org.omg.bpmn.miwg`). The repository also contains two shell scripts (`publish.sh`, `yaoqiang.sh`) for local test execution. The effective language ecosystem is Java (for the build toolchain) targeting an older version. |
| **Gap** | Java 1.6 target version is outdated (EOL since February 2013). While JDK 11 is used for building, the `java.version` property suggests the artifact targets Java 1.6 compatibility, limiting use of modern Java features and cloud-native libraries. |
| **Recommendation** | Update `<java.version>` in `pom.xml` to at least Java 11 (LTS) or preferably Java 17/21 (current LTS). This unlocks modern language features, improved performance, and better AWS SDK compatibility. Since no Java source code exists in the repository, this change affects only the compiled bytecode target level. |
| **Evidence** | `pom.xml` (`<java.version>1.6</java.version>`), `.github/workflows/maven.yml` (`java-version: '11'`), `publish.sh`, `yaoqiang.sh`. |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The entire repository is a single Maven project producing a single jar artifact (`test-suite-0.4-SNAPSHOT.jar`). There are no separate modules, no multi-module Maven structure, no independent services, and no deployable entry points. The jar packages BPMN XML test data — it is not an application with module boundaries. The 30+ vendor directories (e.g., `ADONIS 17.0/`, `Trisotech Workflow Modeler 12.13.0/`) are data directories, not application modules. |
| **Gap** | Tightly-coupled single artifact with no module boundaries. However, this is a test data repository, not an application — the concept of monolith vs microservices does not naturally apply. |
| **Recommendation** | If evolving into a cloud service, design from the start with service boundaries: (1) BPMN validation service, (2) report generation service, (3) test result storage service, (4) static site hosting. Use the Strangler Fig pattern to build services alongside the existing Maven pipeline. |
| **Evidence** | `pom.xml` (`<packaging>jar</packaging>`, single `<artifactId>test-suite</artifactId>`), absence of multi-module structure or multiple Dockerfiles/Helm charts. |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No inter-service communication exists. There are no HTTP client calls, no message publishing patterns, no event-driven handlers, no queue consumers. The repository is a test data packaging project — it does not have services that communicate with each other. Using stateful-crud archetype calibration: the absence of async communication for cross-service state propagation represents a gap, but there are no services to communicate between. |
| **Gap** | No communication patterns — async or sync. The repository has no services to communicate. |
| **Recommendation** | If building a multi-service architecture, implement EventBridge for event-driven communication between services (e.g., new submission → validation → report generation). Use SQS for reliable message delivery between processing stages. |
| **Evidence** | Absence of any HTTP client libraries, message queue SDKs, or event-driven patterns in the repository. |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No long-running process handling patterns found. The Maven build and BPMN analysis are batch processes that run to completion in the GitHub Actions runner. There are no async job frameworks, no status polling APIs, no callback patterns. The `bpmn-miwg-maven-plugin` runs during the test phase and completes synchronously. Using stateful-crud archetype calibration: while the Maven build process may take several minutes for large submissions, there is no application runtime with user-facing operations to evaluate for long-running process handling. |
| **Gap** | No async job processing for long-running operations. The Maven build runs synchronously in CI. |
| **Recommendation** | If the BPMN analysis needs to handle large or variable-duration workloads, implement async processing with Step Functions or SQS. Expose a status polling API (e.g., `GET /analysis/{id}/status`) for consumers to check progress. |
| **Evidence** | `pom.xml` (synchronous Maven lifecycle), `.github/workflows/maven.yml` (single build step with no async patterns). |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API endpoints exist, so no versioning strategy is applicable. The repository does not expose any HTTP APIs, REST endpoints, or GraphQL schemas. The Maven artifact versioning (`0.4-SNAPSHOT`) is for the jar package, not API versioning. The JSON configuration files (`test-case-structure.json`, `tools-tested-by-miwg.json`) have no versioning scheme. |
| **Gap** | No API versioning — no APIs exist to version. |
| **Recommendation** | If building a BPMN validation API, implement URL-path versioning (e.g., `/v1/validate`, `/v1/results`) from the start. Include backward compatibility guarantees in the API contract. |
| **Evidence** | Absence of any API specification files (OpenAPI, AsyncAPI, GraphQL), absence of HTTP routing in source code. |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No service discovery mechanism exists. There are no service registries, no service mesh configurations, no API catalogs. The repository has no services that need to discover each other. The only external endpoint references are in `pom.xml` (GitHub Packages repository URLs) and `.github/workflows/maven.yml` (GitHub Pages deployment). |
| **Gap** | No service discovery — no services exist to discover. |
| **Recommendation** | If building a multi-service architecture, implement AWS Cloud Map for service discovery or use API Gateway as a centralized service catalog. Avoid hard-coding service endpoints — use environment variables with DNS-based discovery. |
| **Evidence** | `pom.xml` (hard-coded repository URLs), absence of service discovery configuration. |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The repository contains extensive unstructured data — BPMN XML files (`.bpmn`) and PNG images across 30+ vendor directories and the `Reference/` directory. All data is stored as flat files in Git, not in managed object storage. There are no S3 bucket definitions, no Textract or document parsing pipelines, and no data indexing or search capabilities. The `Reference/` directory contains 61 files (BPMN, PNG, PDF, VSD, XSD). |
| **Gap** | All unstructured data (BPMN XML, PNG images, PDF files) stored in Git as flat files. No managed object storage, no parsing pipeline, no search capability. |
| **Recommendation** | Migrate BPMN test data to S3 for scalable storage, versioning, and accessibility. Implement a parsing pipeline using Lambda + S3 events to validate and index BPMN XML on upload. Enable S3 versioning for audit trails. Consider Amazon Textract or custom XML parsing for automated BPMN model analysis. |
| **Evidence** | `Reference/` directory (BPMN, PNG, PDF, VSD files), 30+ vendor result directories with BPMN/PNG files stored in Git. Absence of `aws_s3_bucket` or any object storage configuration. |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No data access layer exists. The repository's data is accessed directly as files from the filesystem. The Maven build reads BPMN files from directories using filesystem paths defined in `pom.xml` resource includes. The `test-case-structure.json` and `tools-tested-by-miwg.json` files serve as flat-file data stores with no abstraction layer, no API, and no query capability. |
| **Gap** | No unified data access layer. Data is accessed through filesystem operations with no abstraction. |
| **Recommendation** | If building a cloud service, implement a data access layer that abstracts BPMN test data storage (S3) from consumption (API). Use a repository pattern for test case and tool metadata access. Consider DynamoDB or Aurora for structured metadata with S3 for binary assets. |
| **Evidence** | `pom.xml` (filesystem-based resource includes), `test-case-structure.json` (flat-file data), `tools-tested-by-miwg.json` (flat-file data). |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database engines are defined in the repository. There are no RDS instances, DynamoDB tables, DocumentDB clusters, or ElastiCache resources with engine versions to evaluate. The only version-related configuration is the Maven artifact version (`0.4-SNAPSHOT`) and the `bpmn-miwg-tools.version` property (`0.6.0`), which are build tool versions, not database engine versions. |
| **Gap** | No database engine versions to evaluate — no databases exist. |
| **Recommendation** | When introducing database infrastructure, always pin engine versions explicitly in IaC. Choose engines with long-term support and document a version update procedure. |
| **Evidence** | `pom.xml` (Maven versions only, no database engine references). Absence of any database IaC or configuration. |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs exist in the repository. There are no `.sql` files with `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION`. There are no ORM bypass patterns or raw SQL execution. All logic (the BPMN MIWG analysis tools) runs in the application layer via Maven plugins. The repository contains no database coupling whatsoever — all business logic is external to any database engine. |
| **Gap** | N/A — this criterion is fully met. No stored procedures or proprietary SQL. |
| **Recommendation** | No action needed. When introducing database infrastructure, maintain this pattern — keep all business logic in the application layer, not in database stored procedures. |
| **Evidence** | Absence of any `.sql` files, stored procedures, triggers, or proprietary SQL constructs in the entire repository. |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging is configured in the repository. There are no `aws_cloudtrail` resources, no log file validation settings, no S3 bucket with object lock for audit logs. The only logging is implicit through GitHub's audit log for repository actions and GitHub Actions workflow execution logs. |
| **Gap** | No AWS audit logging. No immutable log storage. Reliance on GitHub's platform-level audit logs only. |
| **Recommendation** | If migrating to AWS, enable CloudTrail with log file validation and store logs in an S3 bucket with Object Lock for immutability. Enable CloudWatch log retention for application logs. |
| **Evidence** | Absence of any `aws_cloudtrail`, CloudWatch log group, or audit logging configuration in the repository. |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest is configured. There are no `aws_kms_key` resources, no `kms_key_id` parameters on data stores, and no encryption configuration. The repository does not define any AWS data stores that would require encryption. GitHub encrypts repository data at rest on their platform. |
| **Gap** | No AWS encryption at rest configuration. No KMS key management. |
| **Recommendation** | When provisioning AWS data stores, enable encryption at rest with customer-managed KMS keys for all sensitive data stores. Define key rotation policies. |
| **Evidence** | Absence of any `aws_kms_key` resources or `kms_key_id` parameters in the repository. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API authentication is configured because no API endpoints exist. There are no auth middleware configurations, no API Gateway authorizers, no Cognito user pools, no OAuth2 flows, no Bearer token validation. The repository is a test data suite, not an API service. |
| **Gap** | No API authentication — no APIs exist to authenticate. |
| **Recommendation** | If building a BPMN validation API, implement OAuth2/JWT authentication from the start. Use API Gateway authorizers with Cognito or a custom Lambda authorizer. Ensure all endpoints require authentication except explicitly public ones (protected with throttling and validation). |
| **Evidence** | Absence of any authentication middleware, API Gateway authorizer configurations, or OAuth/JWT libraries. |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity provider integration exists. No Cognito user pools, no OIDC/SAML configuration, no SSO setup, no identity federation. The repository does not have user authentication. GitHub's authentication is used for repository access, but this is platform-level, not application-level. |
| **Gap** | No identity provider integration. No centralized authentication for the application. |
| **Recommendation** | If building a user-facing BPMN tool submission portal, integrate with a centralized IdP (Amazon Cognito for AWS-native, or federate with OMG's identity provider). Enable SSO for MIWG members. |
| **Evidence** | Absence of any `aws_cognito_*`, OIDC, SAML, or identity provider configuration in the repository. |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The GitHub Actions workflows use proper secrets management practices. `GITHUB_TOKEN` is automatically provided by GitHub Actions (managed by the platform). `TSTEPHEN_GITHUB_MIWG_TOKEN` is stored as a GitHub Actions secret (`secrets.TSTEPHEN_GITHUB_MIWG_TOKEN`) — not hardcoded in code. No credentials are committed to version control. The `.gitignore` file excludes build artifacts but does not reference `.env` files (none exist). No hardcoded passwords, API keys, or secret values found in any repository files. |
| **Gap** | No automated rotation for the `TSTEPHEN_GITHUB_MIWG_TOKEN` secret. No AWS Secrets Manager or Vault integration (repository is not deployed on AWS). Secrets management is GitHub-native only. |
| **Recommendation** | For the current GitHub-hosted setup, the secrets management is appropriate. If migrating to AWS, use AWS Secrets Manager for all credentials with automated rotation. Rotate the `TSTEPHEN_GITHUB_MIWG_TOKEN` periodically as a best practice. |
| **Evidence** | `.github/workflows/maven.yml` (`${{ secrets.GITHUB_TOKEN }}`, `${{ secrets.TSTEPHEN_GITHUB_MIWG_TOKEN }}`), `.github/workflows/release.yml` (`${{ secrets.GITHUB_TOKEN }}`). No hardcoded credentials found in `pom.xml`, `publish.sh`, `yaoqiang.sh`, or any other file. |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute hardening or patching strategy exists. There are no SSM Patch Manager configurations, no vulnerability scanning (Inspector, Snyk) enabled, no hardened base images. The GitHub Actions workflow uses `ubuntu-latest` (managed by GitHub) — this is platform-managed, not user-configured. No EC2 instances, no custom AMIs, no container images to harden. |
| **Gap** | No compute hardening — no owned compute resources to harden. Reliance on GitHub-managed runners. |
| **Recommendation** | When introducing AWS compute resources, use hardened base images (Bottlerocket for containers, CIS-hardened AMIs for EC2). Enable AWS Inspector for vulnerability scanning. Configure SSM Patch Manager for automated patching. |
| **Evidence** | `.github/workflows/maven.yml` (`runs-on: ubuntu-latest` — GitHub-managed). Absence of any compute hardening, vulnerability scanning, or patching configuration. |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SAST, DAST, or dependency vulnerability scanning tools are configured in the CI/CD pipeline. The GitHub Actions workflows (`maven.yml`, `release.yml`) have no security scanning steps. No Dependabot configuration file (`.github/dependabot.yml`) exists. No OWASP Dependency-Check Maven plugin is configured. No SonarQube, Semgrep, or CodeGuru integration. No container scanning (no containers to scan). The `pom.xml` has two Maven dependencies (`bounds-generator`, `submission-counter`) from the BPMN MIWG tools project that are not scanned for vulnerabilities. |
| **Gap** | Zero security scanning in the pipeline. No dependency scanning, no SAST, no container scanning. Maven dependencies are not checked for known vulnerabilities. |
| **Recommendation** | Add Dependabot configuration (`.github/dependabot.yml`) to monitor Maven dependency vulnerabilities. Add OWASP Dependency-Check Maven plugin to the build (`mvn dependency-check:check`). Consider adding a SAST step for BPMN XML validation to detect malformed or potentially malicious BPMN files submitted by vendors. |
| **Evidence** | `.github/workflows/maven.yml` (no security scanning steps), `.github/workflows/release.yml` (no security scanning), `pom.xml` (no security scanning plugins). Absence of `.github/dependabot.yml`, `.snyk`, or any security scanning configuration. |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing is instrumented. No OpenTelemetry SDK in dependency manifests, no X-Ray instrumentation, no `traceparent` or `X-Amzn-Trace-Id` header propagation. The repository has no running services to trace. The Maven build produces logs in the GitHub Actions console but no structured tracing. |
| **Gap** | No distributed tracing. No running services exist to instrument. |
| **Recommendation** | If building cloud services, instrument with OpenTelemetry from the start. Use X-Ray for AWS-native tracing or export to CloudWatch with OTLP. Ensure trace ID propagation across all service boundaries. |
| **Evidence** | `pom.xml` (no tracing dependencies), absence of OpenTelemetry, X-Ray, or tracing libraries in any configuration. |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions exist. No formal service level objectives for availability, latency, or error rates. No error budget tracking. No CloudWatch alarms on p99/p95 latency. The GitHub Pages site (analysis results) has no SLO — it relies on GitHub's platform availability. |
| **Gap** | No SLOs defined. No formal definition of acceptable service levels for the analysis results site or the build pipeline. |
| **Recommendation** | Define SLOs for the BPMN analysis pipeline: (1) build success rate target (e.g., 95% of builds succeed), (2) GitHub Pages availability target, (3) analysis report freshness target (reports updated within 24 hours of submission). |
| **Evidence** | Absence of any SLO definition files, CloudWatch alarms, or error budget tracking in the repository. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics are published. No `cloudwatch.put_metric_data` calls, no custom dashboards, no business KPI tracking. The repository does not publish metrics about BPMN interchange test results, tool participation rates, or submission trends. The `bpmn-analysis.json` file contains historical analysis data but is stored as a static file, not published as metrics. |
| **Gap** | No business metrics. Analysis results and tool participation data are not tracked as metrics. |
| **Recommendation** | Publish business metrics for the BPMN MIWG: number of tools tested, test pass rates by vendor, interchange quality trends over time, number of test case categories covered. Use CloudWatch custom metrics or a dashboard service to visualize trends. |
| **Evidence** | `bpmn-analysis.json` (static data file, not metrics), `tools-tested-by-miwg.json` (37 tools listed but no trend tracking). Absence of any metrics publishing in pipeline or application. |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting is configured. No CloudWatch anomaly detection, no error rate alarms, no latency alarms, no PagerDuty/OpsGenie integration. The GitHub Actions workflows do not send notifications on failure beyond GitHub's default email notifications. |
| **Gap** | No anomaly detection or proactive alerting. Build failures are only visible through GitHub's default notification system. |
| **Recommendation** | Configure GitHub Actions failure notifications to a team channel (Slack, Teams). If migrating to AWS, set up CloudWatch alarms for build pipeline failures and analysis result anomalies (e.g., sudden drop in tool test results). |
| **Evidence** | `.github/workflows/maven.yml` (no failure notification steps), `.github/workflows/release.yml` (no alerting). Absence of any monitoring or alerting configuration. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Deployments go straight to production with no staged rollout. The `maven.yml` workflow deploys directly to GitHub Pages using `peaceiris/actions-gh-pages@v4` — this pushes the analysis site to the `gh-pages` branch immediately with no canary, blue/green, or rolling deployment strategy. The `release.yml` workflow creates release artifacts directly on publication. There is no deployment verification step, no rollback mechanism, and no traffic shifting. |
| **Gap** | Direct-to-production deployment. No staged rollout. No rollback capability. No deployment verification. |
| **Recommendation** | For a static site, implement a two-stage deployment: (1) deploy to a preview/staging URL, (2) validate the site renders correctly, (3) promote to production. If using S3 + CloudFront, use CloudFront functions or OAC to implement blue/green deployment for the static site. |
| **Evidence** | `.github/workflows/maven.yml` (`peaceiris/actions-gh-pages@v4` — direct push to gh-pages), `.github/workflows/release.yml` (direct release artifact upload). |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The Maven `analysis` profile binds the `bpmn-miwg-maven-plugin` to the `test` phase, which runs BPMN MIWG analysis tools against the repository's BPMN files during the build. This provides automated validation of BPMN XML interchange results — a form of integration testing specific to the BPMN domain. The `maven-antrun-plugin` also runs `RepoScanner` and `BoundaryCreator` during `process-resources`. However, these are not traditional integration tests — they are analysis tools that generate reports rather than asserting pass/fail criteria. There are no unit tests, no API integration tests, and no test coverage reporting. |
| **Gap** | Automated BPMN analysis runs during build but does not gate deployments — analysis results are published regardless of findings. No pass/fail criteria defined. No traditional integration or unit tests. |
| **Recommendation** | Add a build gate that fails the pipeline if BPMN analysis detects critical interchange issues (e.g., missing required BPMN elements in vendor submissions). Add XML schema validation as a pre-build test step to ensure all submitted BPMN files are well-formed. |
| **Evidence** | `pom.xml` (Maven `analysis` profile with `bpmn-miwg-maven-plugin` bound to `test` phase), `.github/workflows/maven.yml` (`mvn -P analysis --batch-mode deploy`). |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response workflows or runbooks exist. No Systems Manager Automation documents, no Lambda-based remediation, no Step Functions for incident workflows. No runbook files (markdown, YAML, JSON) found in the repository. When the GitHub Actions build fails or the GitHub Pages site is unreachable, there is no documented or automated response procedure. |
| **Gap** | No incident response automation. No runbooks. Incident response is entirely ad hoc. |
| **Recommendation** | Create runbooks for common issues: (1) GitHub Actions build failure troubleshooting, (2) GitHub Pages site downtime response, (3) corrupted BPMN submission handling. Store runbooks as markdown files in the repository. If migrating to AWS, use SSM Automation documents for self-healing patterns. |
| **Evidence** | Absence of any runbook files, incident response documentation, or automated remediation in the repository. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership is defined. No per-service dashboards, no alarms with named owners, no SLO definitions with team attribution. No CODEOWNERS file referencing observability assets. The repository has no monitoring infrastructure to own. |
| **Gap** | No observability ownership. No monitoring infrastructure. No team attribution for any operational concerns. |
| **Recommendation** | Add a CODEOWNERS file defining ownership of CI/CD workflows, analysis configurations, and the reference test data. Define who is responsible for monitoring the GitHub Actions pipeline and the GitHub Pages site health. |
| **Evidence** | Absence of any CODEOWNERS file, observability dashboards, alarms, or team-attributed monitoring configuration. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging exists because no AWS resources are defined. There are no `default_tags` in a Terraform provider, no `tags` on any resources, no tag enforcement policies. The repository has no AWS resources to tag. |
| **Gap** | No resource tagging — no AWS resources exist to tag. |
| **Recommendation** | When provisioning AWS resources, define a tagging standard from the start. Required tags should include: `Environment`, `Project` (bpmn-miwg), `Owner`, `CostCenter`. Enforce tags via IaC defaults and AWS Config rules. |
| **Evidence** | Absence of any AWS resource definitions or tagging configuration in the repository. |

---

## Learning Materials

Learning materials for the 3 triggered pathways:

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to Cloud Native** | [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |
| **Move to Containers** | [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM) · [Move to Containers with Amazon ECS](https://skillbuilder.aws/learning-plan/CDA8Y4JRRR) · [EKS Workshop](https://www.eksworkshop.com/) |
| **Move to Modern DevOps** | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `pom.xml` | INF-Q1, INF-Q2, INF-Q3, INF-Q4, INF-Q10, INF-Q11, APP-Q1, APP-Q2, APP-Q3, APP-Q4, APP-Q5, DATA-Q1, DATA-Q2, DATA-Q3, OPS-Q1, OPS-Q6 | Maven build configuration: jar packaging, Java 1.6 target, BPMN MIWG tools dependencies, analysis profile with test plugin, resource includes for BPMN/PNG files. No IaC, no database, no compute resources. |
| `.github/workflows/maven.yml` | INF-Q1, INF-Q11, SEC-Q5, SEC-Q6, SEC-Q7, OPS-Q4, OPS-Q5, OPS-Q6 | GitHub Actions CI/CD workflow: JDK 11 setup, Maven build with analysis profile, deploy to GitHub Packages, publish to GitHub Pages. Uses `secrets.GITHUB_TOKEN` and `secrets.TSTEPHEN_GITHUB_MIWG_TOKEN`. No security scanning steps. Direct deployment to production. |
| `.github/workflows/release.yml` | INF-Q11, SEC-Q5, SEC-Q7, OPS-Q5 | GitHub Actions release workflow: creates zip of Reference BPMN/PNG files on release publication. Uses `secrets.GITHUB_TOKEN`. |
| `README.md` | Discovery, Quick Agent Wins | Comprehensive documentation of test suite structure, test procedures (import, export, roundtrip, cross), submission guidelines, repository structure, and verified reference models. |
| `test-case-structure.json` | DATA-Q2 | JSON configuration defining BPMN test case categories (A: Layout, B: Conformance, C: Complex scenarios), individual test cases, and reference model provenance. Flat-file data store with no abstraction layer. |
| `tools-tested-by-miwg.json` | DATA-Q2, OPS-Q3 | JSON configuration listing 37 BPMN tools with vendor, version, capabilities (import/export/roundtrip), participation history. Flat-file data store with no trend tracking or metrics. |
| `Reference/` directory | DATA-Q1, APP-Q2 | 61 reference files: BPMN XML (`.bpmn`), PNG images, PDF documents, VSD files, XSD schema. Test reference data stored as flat files in Git. |
| `publish.sh` | INF-Q3 | Shell script for local analysis and publication: git pull, Maven build, copy results. Sequential execution with no error handling or orchestration. |
| `yaoqiang.sh` | APP-Q1 | Shell script for running Yaoqiang BPMN Editor tests locally. References external Java application. |
| `.gitignore` | SEC-Q5 | Git ignore rules for IDE files, build artifacts, and temp files. No `.env` files referenced (none exist). |
| `LICENSE.txt` | Discovery | Creative Commons Attribution 3.0 Unported License. |
| `bpmn-analysis.json` | OPS-Q3 | Historical BPMN analysis data stored as static JSON file. Not published as metrics. |
| 30+ vendor directories | DATA-Q1, APP-Q2 | Vendor test result directories (e.g., `ADONIS 17.0/`, `Trisotech Workflow Modeler 12.13.0/`) containing BPMN export/import/roundtrip files and PNG screenshots. Data directories, not application modules. |
