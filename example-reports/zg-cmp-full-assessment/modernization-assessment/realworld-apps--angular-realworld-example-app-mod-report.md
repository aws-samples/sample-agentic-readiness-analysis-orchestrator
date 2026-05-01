# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | angular-realworld |
| **Date** | 2026-04-29 |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P2 |
| **Tags** | typescript, frontend, angular |
| **Context** | Angular reference implementation of the RealWorld spec. |
| **Overall Score** | 1.57 / 4.0 |

**Archetype Justification**: This is a client-side SPA that performs CRUD operations against an external API (`https://api.realworld.show/api`) but owns no persistent state or server-side infrastructure. Server-side archetype signals are ambiguous for a browser application — no database connections, no message queues, no server-side endpoints. Defaulting to `stateful-crud` as the conservative choice per TD rules, since the app performs CRUD operations (articles, comments, profiles, users) even though they are proxied to an external backend.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.09 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.00 / 4.0 | 🟠 Needs Work |
| Data Platform Modernization (DATA) | 2.25 / 4.0 | 🟠 Needs Work |
| Security Baseline (SEC) | 1.29 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.22 / 4.0 | ❌ Not Present |
| **Overall** | **1.57 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC exists — all infrastructure (if any) is manually created or undefined. | Blocks reproducible deployments, disaster recovery, and environment consistency. Foundation for all other modernization. |
| 2 | INF-Q1: Managed Compute | 1 | No compute infrastructure defined. SPA deployed as a zip artifact with no managed hosting (S3+CloudFront, Amplify, ECS, EKS). | No scalable hosting, no CDN, no managed deployment target. Triggers Move to Containers and Move to Cloud Native pathways. |
| 3 | INF-Q11: CI/CD Automation | 2 | CI/CD exists (GitHub Actions) with build and basic deployment (zip release), but no automated rollback, no deployment strategy, limited test gates. | Deployments are not safe or repeatable. Triggers Move to Modern DevOps pathway. |
| 4 | SEC-Q7: Application Security Pipeline | 1 | No SAST, DAST, or dependency vulnerability scanning in CI/CD. XSS e2e tests exist but are not standard scanning tools. | Vulnerabilities in dependencies or application code reach production undetected. |
| 5 | APP-Q6: Service Discovery | 1 | API base URL hardcoded in source code (`https://api.realworld.show/api`). No environment variable, no service discovery. | Cannot deploy to different environments without code changes. Blocks multi-environment deployments. |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** INF-Q11 = 2 (CI/CD pipeline exists with GitHub Actions workflows for build, test, and release).
- **What it enables:** An agent that triggers GitHub Actions workflows, checks build/test status, manages releases, and provides deployment status updates. The existing 4 workflows (`deploy.yml`, `lint.yml`, `playwright.yml`, `security-tests.yml`) provide the automation surface for agent orchestration.
- **Additional steps:** Expose GitHub Actions API access for the agent. Consider adding workflow dispatch triggers (already present on `deploy.yml`) to enable agent-initiated deployments.
- **Effort:** Low — agent can use GitHub Actions API directly to trigger workflows and query status.

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository — `README.md` (project overview, setup instructions, functionality breakdown), `CLAUDE.md` (commands reference, code style guidelines), `CODE_OF_CONDUCT.md`, `e2e/SELECTORS.md`, and extensive JSDoc comments throughout service files (e.g., `UserService` auth state documentation, `errorInterceptor` error handling strategy).
- **What it enables:** A RAG-based knowledge agent that indexes repository documentation and code comments to answer developer questions about the project structure, setup procedures, testing strategies, and authentication flows.
- **Additional steps:** Index markdown files and JSDoc-commented source files into a vector store. The existing documentation covers project setup, architecture decisions, and testing approaches — sufficient for an initial knowledge base.
- **Effort:** Medium — requires setting up a vector store (e.g., Amazon OpenSearch with vector engine) and building an indexing pipeline for repository documentation.

### Data Query Agent

- **Prerequisite:** DATA-Q2 = 3 (Angular services form a centralized data access layer — `ArticlesService`, `CommentsService`, `TagsService`, `ProfileService`, `UserService` encapsulate all API interactions).
- **What it enables:** An agent that queries the external RealWorld API through the existing service layer patterns. Could provide natural language queries like "show articles by user X" or "list comments on article Y" by translating to the appropriate service method calls.
- **Additional steps:** The agent would need to interact with the external API (`api.realworld.show`) directly rather than through the browser-based Angular services. Generate an OpenAPI spec from the known API endpoints to enable full tool discovery. Current service code documents the complete API surface (articles CRUD, comments CRD, profiles, tags, users).
- **Effort:** Medium — requires generating an OpenAPI spec and configuring the agent to call the external API directly.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2 = 2 (monolith SPA), INF-Q1 = 1 (no managed compute), APP-Q3 = 1 (all sync communication) |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1 = 1 (no compute infrastructure), no container definitions found |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (no stored procedures or proprietary SQL). Primary trigger not met. |
| 4 | Move to Managed Databases | Triggered | Medium | Medium | INF-Q2 = 1 (no database infrastructure defined). Note: score reflects absence, not self-management. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | Contextual guard: no evidence of data processing workloads. No streaming, ETL, or analytics artifacts found. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (no IaC), OPS-Q5 = 1 (no deployment strategy), OPS-Q6 = 3 (e2e tests exist) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. Context: "Angular reference implementation of the RealWorld spec." |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:**
This is a monolithic Single Page Application (Angular 21) deployed as a single unit — a zip file of static browser assets. The SPA has a well-organized modular structure (`core/`, `features/`, `shared/`) with clean boundaries between modules, but all modules are compiled and deployed as one artifact. The application communicates exclusively via synchronous HTTP calls to a single external API (`https://api.realworld.show/api`). There is no backend service, no infrastructure definition, and no managed compute platform.

**Compute Model Gaps (INF-Q1 = 1):**
No compute infrastructure is defined. The SPA is built to `dist/angular-conduit/browser/` and packaged as a zip for GitHub Releases. There is no S3 static hosting, no CloudFront CDN, no ECS/EKS container deployment, no Lambda@Edge, and no AWS Amplify configuration.

**Communication Pattern Gaps (APP-Q3 = 1):**
All communication is synchronous HTTP via Angular `HttpClient`. RxJS observables provide asynchronous handling within the browser but all external communication is request/response. No event-driven patterns, no message queues, no WebSocket connections.

**Recommended Decomposition Approach:**
For a frontend SPA, "cloud native" means deploying to managed hosting with CDN distribution, API Gateway integration, and potentially micro-frontend decomposition if independent team scaling is needed. See the Decomposition Strategy section below.

**Recommended AWS Services (respecting preferences for EKS, API Gateway):**
- **Amazon S3 + CloudFront** — Static SPA hosting with global CDN distribution
- **Amazon API Gateway** (preferred) — Managed API entry point with throttling, auth, and request validation
- **AWS Amplify Hosting** — Alternative managed hosting with CI/CD integration
- **Amazon EKS** (preferred) — If the application evolves to include a backend service layer

**Recommended Patterns:**
- Strangler Fig — Incrementally extract backend capabilities from the external API into owned microservices
- Anti-corruption Layer — Isolate the frontend from backend API contract changes via an API Gateway transformation layer
- Hexagonal Architecture — Structure any new backend services with clear port/adapter boundaries

**References:**
- [AWS Prescriptive Guidance: Strangler Fig Pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)
- [AWS Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model (INF-Q1 = 1):**
No compute infrastructure exists. The application is an Angular SPA built to `dist/angular-conduit/browser/` and deployed as a zip file via GitHub Releases (`deploy.yml`). There are no Dockerfiles, no container orchestration manifests, no Kubernetes resources, and no Helm charts.

**Contextual Note:**
For a static SPA, containerization is one hosting option but not necessarily the best first step. S3+CloudFront or AWS Amplify may be more cost-effective for serving static browser assets. However, containerization becomes valuable if the application evolves to include a backend service layer (e.g., a BFF — Backend For Frontend — or SSR — Server-Side Rendering).

**Container Readiness Indicators:**
- ✅ Application builds to static files (`dist/angular-conduit/browser/`) — trivially containerizable with nginx
- ✅ No local file system dependencies beyond build output
- ✅ Build process is well-defined (`bun run build` via `angular.json`)
- ⚠️ API URL is hardcoded in source (`api.interceptor.ts`) — needs externalization via environment variable injection at build time or runtime

**Recommended Container Orchestration (respecting preference for EKS, avoiding self-managed-kubernetes):**
- **Amazon EKS** (preferred) with Fargate for serverless pod execution — eliminates node management overhead
- **Amazon ECR** for container image registry
- **AWS App Runner** — Simpler alternative if full Kubernetes orchestration is not needed

**Migration Approach:**
1. Create a multi-stage Dockerfile: build stage (Node.js/Bun) → serve stage (nginx:alpine)
2. Externalize the API URL via build-time or runtime environment variable injection
3. Push image to Amazon ECR
4. Deploy to EKS with Fargate or App Runner
5. Add CloudFront as CDN layer in front of the container service

**References:**
- [AWS Container Migration Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/containers-provision-environment/welcome.html)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Database Topology (INF-Q2 = 1):**
No database infrastructure is defined in this repository. This is a frontend SPA that relies entirely on an external API (`https://api.realworld.show/api`) for data persistence. The score of 1 reflects the complete absence of database infrastructure, not the presence of self-managed databases.

**Contextual Note:**
This pathway is triggered because INF-Q2 < 3, but the trigger is due to absence rather than self-management. If this application evolves to include its own backend, managed database services should be adopted from the start rather than self-managing database instances.

**Recommended Managed Database Services (respecting preferences for Aurora, DynamoDB; avoiding Oracle):**
- **Amazon Aurora** (preferred) — For relational data (articles, users, comments match a relational model well)
- **Amazon DynamoDB** (preferred) — For high-throughput read patterns (article feeds, tag listings) if a NoSQL model fits
- **Amazon ElastiCache** — For session management and caching if a backend service is introduced

**Data Access Patterns (DATA-Q2 = 3):**
The Angular service layer (`ArticlesService`, `CommentsService`, `TagsService`, `ProfileService`, `UserService`) provides a clean domain-oriented data access pattern. If building a backend, these same domain boundaries can inform the database schema design.

**References:**
- [AWS Database Migration Guide](https://docs.aws.amazon.com/prescriptive-guidance/latest/migration-databases/welcome.html)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 1):**
No infrastructure-as-code exists. There are no Terraform files, CloudFormation templates, CDK stacks, or Helm charts. All infrastructure — if any exists beyond the GitHub repository — is manually created.

**Current CI/CD State (INF-Q11 = 2):**
GitHub Actions workflows exist with 4 pipelines:
- `deploy.yml` — Build with Bun, create zip, publish GitHub Release. Also includes an ATX transform job.
- `lint.yml` — Prettier format checking on push/PR to main.
- `playwright.yml` — Playwright e2e tests on push/PR to main.
- `security-tests.yml` — XSS security e2e tests on push/PR to main.

Build is automated but deployment is a zip file uploaded to GitHub Releases — no deployment to a running environment, no rollback, no staged releases.

**Deployment Strategy Gaps (OPS-Q5 = 1):**
The current deployment creates a GitHub Release with a zip file. There is no blue/green deployment, no canary release, no traffic shifting, no CodeDeploy integration. This is effectively "download and manually deploy."

**Testing Gaps (OPS-Q6 = 3):**
Playwright e2e tests are a strength — they cover authentication, article CRUD, comments, settings, navigation, and XSS security. Tests run in CI on every push/PR. However, tests run against the live external API (`api.realworld.show`), introducing external dependency flakiness. Unit tests exist via Vitest for core services.

**Recommended DevOps Toolchain (respecting preferences):**
1. **Infrastructure as Code:** AWS CDK (TypeScript, matching the application language) or Terraform to define hosting infrastructure
2. **CI/CD Pipeline Enhancement:**
   - Add `bun run test` (Vitest unit tests) as a required CI step
   - Add dependency vulnerability scanning (`npm audit` or Snyk)
   - Add SAST scanning (Semgrep or SonarQube)
   - Deploy to AWS (S3+CloudFront, Amplify, or EKS) instead of GitHub Releases
3. **Deployment Strategy:** Implement blue/green or canary deployments via CloudFront origin switching or EKS rolling updates
4. **Automated Rollback:** Configure rollback triggers based on error rate metrics

**Representative AWS Services:**
- **AWS CDK** — IaC in TypeScript
- **AWS CodePipeline + CodeBuild** — Managed CI/CD (or continue with GitHub Actions + AWS deployment)
- **AWS CodeDeploy** — Managed deployment with blue/green and canary strategies
- **Amazon CloudWatch** — Monitoring and alerting for deployment health

**References:**
- [AWS DevOps Prescriptive Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/strategy-devops/welcome.html)

## Decomposition Strategy

APP-Q2 scored 2 — the application is a modular monolith SPA with identifiable module boundaries but a single deployable unit. This section provides decomposition guidance.

### Context: Frontend SPA Decomposition

This is a **client-side SPA**, not a server-side monolith. Decomposition for a frontend application means different things than for a backend service:
- **Micro-frontends** — Independent frontend modules that can be deployed and scaled independently
- **Backend extraction** — Creating backend services that the SPA currently delegates to an external API
- **Static hosting modernization** — Moving from zip-file releases to managed hosting with CDN

### Approach Options

| Approach | Description | When to Use | Level of Effort | Recommendation |
|----------|-------------|-------------|-----------------|----------------|
| **Conditional / Adaptive** | Deploy the SPA to managed static hosting (S3+CloudFront or Amplify) first. Then selectively extract backend services if the application evolves beyond a reference implementation. | APP-Q2 = 2 and the team has limited capacity. The SPA's modular structure is appropriate for its current scope. | **Low to Medium** — Static hosting in 1-2 weeks, selective extraction over 3-6 months. | ✅ **Recommended.** The SPA's current modular structure is appropriate. Focus on hosting modernization first. |
| **Strangler Fig (Parallel Track)** | Incrementally build owned backend services (articles, users, comments) to replace dependency on the external API. SPA routes API calls to owned services one domain at a time. | If the team needs to own the full stack and the external API dependency must be eliminated. | **Medium to High** — 3-12 months to build and migrate all API domains. | ✅ **Recommended only if the external API dependency needs to be eliminated.** |
| **Micro-Frontend Decomposition** | Split the SPA into independently deployable micro-frontends (e.g., article module, profile module, auth module) using Module Federation or similar. | If multiple teams need independent deployment cycles for different feature domains. | **High** — 6-12 months for a full micro-frontend architecture. | ⚠️ **Not recommended for this reference app.** The current modular monolith structure is appropriate for a single-team application. Micro-frontends add significant complexity. |

### Pattern Recommendations

| Pattern | Purpose | When to Apply | AWS Prescriptive Guidance |
|---------|---------|---------------|---------------------------|
| **Anti-corruption Layer (ACL)** | Isolate the SPA from the external API's contract. If building owned backend services, the ACL prevents external API design decisions from leaking into new services. | When building backend services to replace the external API dependency. Place an API Gateway transformation layer between the SPA and backend services. | [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) |
| **Hexagonal Architecture** | Structure each new backend service with clear boundaries between business logic (core), external interfaces (ports), and infrastructure adapters. | Every new backend service — ensures testability and portability. | [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |

### Effort Estimation Factors

| Factor | Assessment Finding | Effort Signal |
|--------|-------------------|---------------|
| Module boundaries | Clear package/module structure: `core/` (auth, interceptors, layout, models), `features/` (article, profile, settings), `shared/` (components, pipes). No circular dependencies. | **Low** — Clean module boundaries enable straightforward extraction. |
| Data coupling | All data access goes through a single external API. No shared database schemas. Each Angular service owns its domain. | **Low** — No database coupling to untangle. |
| Stored procedures | None — no database, no stored procedures. | **Low** — No database migration required. |
| Communication patterns | All synchronous HTTP to external API. No async patterns. | **Low** — Simple communication model to replicate or improve. |
| CI/CD maturity | GitHub Actions exists but deployment is basic (zip release). No multi-service deployment capability. | **Medium** — Pipeline needs enhancement to support multi-service deployment. |
| Test coverage | Playwright e2e tests cover critical workflows. Vitest unit tests cover core services. | **Low** — Existing tests provide regression safety during extraction. |

**Calibrated Effort Estimate:** **Low to Medium** for the recommended Conditional/Adaptive approach. Static hosting modernization can be completed in 1-2 weeks. Backend service extraction (if needed) would be incremental, with each service domain (articles, users, comments) requiring 2-4 weeks.

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute infrastructure is defined in this repository. The Angular SPA is built to static files (`dist/angular-conduit/browser/`) and packaged as a zip file for GitHub Releases (`deploy.yml`). There is no Terraform, CloudFormation, CDK, or any IaC defining ECS, EKS, Lambda, Fargate, or EC2 resources. No Dockerfiles or Kubernetes manifests exist. The application has no managed compute hosting — no S3 static hosting, no CloudFront CDN, no AWS Amplify. |
| **Gap** | Complete absence of compute infrastructure. The application has no deployment target beyond GitHub Releases. |
| **Recommendation** | Deploy the SPA to Amazon S3 with CloudFront CDN for global distribution. Alternatively, use AWS Amplify Hosting for simplified CI/CD integration. If backend services are added, deploy to Amazon EKS (preferred) with Fargate. |
| **Evidence** | No `.tf`, `template.yaml`, `cdk.json`, `Dockerfile`, or Kubernetes manifests found. `deploy.yml` creates a zip and uploads to GitHub Releases. `angular.json` defines build output to `dist/angular-conduit`. |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database infrastructure is defined. This is a client-side SPA that delegates all data persistence to an external API (`https://api.realworld.show/api`). There are no `aws_rds_*`, `aws_dynamodb_*`, or any database-related IaC resources. No database connection strings, no ORM configurations, no migration files. |
| **Gap** | No database infrastructure owned by this repository. The application depends entirely on an external API for data persistence. |
| **Recommendation** | If building a backend, adopt managed database services from the start: Amazon Aurora (preferred) for relational data, Amazon DynamoDB (preferred) for high-throughput read patterns. Avoid self-managing database instances. |
| **Evidence** | No IaC files found. No database-related imports in source code. All data operations go through HTTP services (`ArticlesService`, `CommentsService`, etc.) to external API. |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No workflow orchestration services or patterns detected. Archetype: `stateful-crud`. Under the stateful-crud rubric, score 1 means "No orchestration — all workflow logic hardcoded in application code." The SPA itself has no multi-step workflow orchestration — all operations are direct HTTP CRUD calls. No Step Functions, Temporal, MWAA, or state machine patterns. |
| **Gap** | No workflow orchestration exists. For the current SPA scope, this is expected — frontend SPAs rarely need server-side workflow orchestration. However, if backend services are introduced, multi-step workflows (e.g., article creation with media processing, notification fanout) would benefit from managed orchestration. |
| **Recommendation** | If backend services are introduced, adopt AWS Step Functions for multi-step business workflows rather than implementing orchestration in application code. For the current frontend-only scope, this is not an immediate gap. |
| **Evidence** | No `aws_sfn_*` in IaC (no IaC exists). No Temporal SDK imports. No workflow YAML definitions. No state machine patterns in source code. |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No messaging or streaming infrastructure detected. Archetype: `stateful-crud`. Under the stateful-crud rubric, score 1 means "No messaging where state changes cross service boundaries — tight synchronous coupling between services that should be decoupled." All communication from the SPA to the external API is synchronous HTTP via Angular `HttpClient`. No SQS, SNS, EventBridge, Kinesis, or MSK. No event-driven patterns beyond RxJS in-browser observables. |
| **Gap** | No async messaging infrastructure. For a client-side SPA communicating with a single external API, this is expected. However, if backend services are built, state change propagation (e.g., article published → notify followers, comment added → update counts) should use managed messaging. |
| **Recommendation** | If building backend services, adopt Amazon EventBridge (preferred) for event-driven communication and Amazon SQS for reliable message processing. Avoid self-managed Kafka or RabbitMQ. |
| **Evidence** | No `aws_sqs_*`, `aws_sns_*`, `aws_eventbridge_*`, `aws_msk_*` in IaC. No messaging SDK imports in source code. All external communication is HTTP via `HttpClient`. |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No network security configuration exists. No VPC, security groups, NACLs, or network segmentation defined. The application has no IaC at all. The SPA runs entirely in the browser and communicates with an external API over HTTPS. |
| **Gap** | Complete absence of network infrastructure. No VPC, no private subnets, no security groups. |
| **Recommendation** | When deploying to AWS, define a VPC with proper network segmentation. For S3+CloudFront hosting, configure CloudFront with Origin Access Control. For EKS deployment, use private subnets for pods and VPC endpoints for AWS service access. |
| **Evidence** | No `aws_vpc`, `aws_subnet`, `aws_security_group` or any network-related IaC resources. No IaC files exist in the repository. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or managed entry point configured. The SPA communicates directly with the external API at `https://api.realworld.show/api` (hardcoded in `api.interceptor.ts`). No throttling, authentication gateway, or request validation layer exists. |
| **Gap** | No managed entry point. The SPA accesses the external API directly from the browser with no intermediate gateway. |
| **Recommendation** | Deploy Amazon API Gateway (preferred) as the entry point for API traffic. API Gateway provides throttling, authentication (Cognito authorizers), request validation, and CORS management. Alternatively, CloudFront can serve as a unified entry point for both static assets and API proxying. |
| **Evidence** | `src/app/core/interceptors/api.interceptor.ts` — hardcoded URL `https://api.realworld.show/api`. No `aws_api_gateway_*`, `aws_lb_*`, `aws_cloudfront_*` in IaC. |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. No IaC defining any scalable resources. No `aws_autoscaling_*`, `aws_appautoscaling_*`, or Lambda concurrency limits. |
| **Gap** | No auto-scaling. No compute resources exist to scale. |
| **Recommendation** | When deploying compute resources, configure auto-scaling from the start. S3+CloudFront hosting scales automatically. For EKS, configure Horizontal Pod Autoscaler. For any backend services, configure appropriate scaling policies. |
| **Evidence** | No IaC files. No auto-scaling configuration. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup or recovery configuration exists. No `aws_backup_plan`, no RDS backup retention, no DynamoDB PITR, no S3 versioning. The application has no data stores to back up. |
| **Gap** | No backup infrastructure. The application depends on the external API for data persistence. |
| **Recommendation** | When introducing managed databases, enable automated backups with defined retention periods. For Aurora, enable PITR and Multi-AZ. For DynamoDB, enable PITR. For S3 buckets, enable versioning. |
| **Evidence** | No IaC files. No backup-related configuration. |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No high availability or fault isolation configuration exists. No multi-AZ deployment, no cross-zone load balancing, no AZ-aware resource placement. |
| **Gap** | No HA configuration. No infrastructure exists to configure HA for. |
| **Recommendation** | When deploying to AWS, use multi-AZ configurations from the start. S3+CloudFront provides inherent HA. For EKS, deploy across multiple AZs. For databases, use Multi-AZ Aurora or DynamoDB (global tables for cross-region). |
| **Evidence** | No IaC files. No AZ configuration. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No infrastructure-as-code exists in this repository. There are no Terraform files (`.tf`), no CloudFormation templates, no CDK stacks (`cdk.json`), no Helm charts, no Kustomize files, no Ansible playbooks. All infrastructure — if any exists — is manually created or undefined. |
| **Gap** | 0% IaC coverage. Complete ClickOps or undefined infrastructure. |
| **Recommendation** | Adopt IaC immediately. Use AWS CDK with TypeScript (matching the application's language) to define all infrastructure: hosting (S3, CloudFront), DNS (Route 53), monitoring (CloudWatch), and any future compute/database resources. Alternatively, use Terraform for multi-cloud flexibility. |
| **Evidence** | No `.tf`, `template.yaml`, `template.json`, `cdk.json`, `Chart.yaml`, `kustomization.yaml`, or Ansible files found anywhere in the repository. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GitHub Actions CI/CD workflows exist with 4 pipelines: (1) `deploy.yml` — builds with Bun, creates zip of build output, publishes GitHub Release; also includes an ATX transform job. (2) `lint.yml` — Prettier format checking on push/PR. (3) `playwright.yml` — Playwright e2e tests on push/PR. (4) `security-tests.yml` — XSS security e2e tests on push/PR. Build is automated, but deployment is a zip file uploaded to GitHub Releases — not a deployment to a running environment. No automated rollback, no infrastructure deployment. |
| **Gap** | Build is automated but deployment is semi-manual. There is no deployment to a live AWS environment, no automated rollback, no deployment gates beyond format checking. Unit tests (`vitest`) are not run in CI (only e2e tests). |
| **Recommendation** | Enhance the CI/CD pipeline: (1) Add `bun run test` as a required CI step for unit tests. (2) Add dependency vulnerability scanning (`npm audit`). (3) Replace zip-release deployment with deployment to AWS (S3+CloudFront, Amplify, or EKS). (4) Add automated rollback on deployment failure. |
| **Evidence** | `.github/workflows/deploy.yml`, `.github/workflows/lint.yml`, `.github/workflows/playwright.yml`, `.github/workflows/security-tests.yml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The application is written in TypeScript 5.9 with Angular 21. TypeScript/JavaScript has first-class AWS SDK coverage (`@aws-sdk/*`), broad cloud-native tooling (CDK, Amplify, Lambda runtimes), and a mature framework ecosystem. The project also uses RxJS 7.8, `marked` for markdown rendering, and `@rx-angular/cdk` + `@rx-angular/template` for reactive patterns. |
| **Gap** | None — TypeScript/JavaScript is a top-tier language for AWS cloud-native development. |
| **Recommendation** | No language change needed. When adding AWS infrastructure (CDK, Lambda functions, backend services), TypeScript is the natural choice and enables code sharing between frontend and backend. |
| **Evidence** | `package.json` — `typescript: ~5.9.3`, `@angular/core: 21.2.4`. `tsconfig.json` — `target: ES2022`, `module: ES2022`. |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application is a single deployable Angular SPA with a modular internal structure. Module organization: `core/` (auth services, HTTP interceptors, layout components, shared models), `features/` (article, profile, settings — each with its own components, models, pages, services), `shared/` (reusable components and pipes). Routes are lazily loaded via `loadComponent()` and `loadChildren()` in `app.routes.ts`. Each feature module has clear boundaries — `features/article/` does not import from `features/profile/` and vice versa. Dependencies flow from features → core and features → shared, with no circular imports detected. However, this is a single deployable unit — all modules compile into one browser bundle. |
| **Gap** | Single deployable monolith SPA. While the internal module structure is clean and well-organized, all code is deployed as one artifact. There is no independent deployment capability per feature. The application also depends on a single external API with a hardcoded URL, creating tight coupling to the external service. |
| **Recommendation** | For the current scope as a reference implementation, the monolith SPA structure is appropriate. If multiple teams need independent deployment cycles, consider micro-frontend decomposition using Module Federation. See the Decomposition Strategy section for detailed guidance. |
| **Evidence** | `angular.json` — single project `angular-conduit` with one build output. `src/app/app.routes.ts` — all routes in one file with lazy loading. `src/app/core/`, `src/app/features/`, `src/app/shared/` — well-defined module boundaries. |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Archetype: `stateful-crud`. All external communication is synchronous HTTP via Angular `HttpClient`. The services (`ArticlesService`, `CommentsService`, `TagsService`, `ProfileService`, `UserService`) make HTTP GET/POST/PUT/DELETE calls to the external API. RxJS observables provide in-browser asynchronous handling but all external communication is request/response. No message queue producers, no event-driven patterns, no WebSocket connections. Under the stateful-crud rubric, score 1 means "All communication synchronous HTTP with no async patterns." |
| **Gap** | 100% synchronous HTTP communication. No async messaging patterns for cross-service state propagation. |
| **Recommendation** | If backend services are introduced, adopt async communication for state change propagation: Amazon EventBridge (preferred) for event-driven communication, Amazon SQS for reliable processing. The current Angular services are well-structured to add WebSocket or Server-Sent Events for real-time updates (e.g., new comments, article updates). |
| **Evidence** | `src/app/features/article/services/articles.service.ts` — all `HttpClient` GET/POST/PUT/DELETE calls. `src/app/core/auth/services/user.service.ts` — synchronous HTTP for login/register/update. No SQS/SNS/EventBridge imports or usage. |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Archetype: `stateful-crud`. No operations exceeding 30 seconds are detected in the application. All operations are standard HTTP CRUD requests: article CRUD, comment CRD, profile get/follow/unfollow, user login/register/update, tags list. These are expected to complete within normal HTTP timeout windows. The app does not have file upload, batch processing, or any operations with data-volume-dependent latency. Under the stateful-crud rubric, score 3 means "Most long-running operations async; some blocking calls remain." While no explicit async job handling exists, there are also no operations that require it. |
| **Gap** | No explicit async job handling patterns. If operations exceeding 30 seconds are introduced (e.g., bulk article import, media processing), there is no infrastructure for status polling or callbacks. |
| **Recommendation** | No immediate action needed. If long-running operations are introduced, implement async patterns with status polling: submit job via POST, receive job ID, poll status endpoint until complete. AWS Step Functions can orchestrate long-running workflows. |
| **Evidence** | `src/app/features/article/services/articles.service.ts` — standard CRUD operations. `src/app/core/auth/services/user.service.ts` — login/register/update are simple HTTP calls. No file upload, batch processing, or heavy computation detected in any service. |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy exists. The application calls the external API at `https://api.realworld.show/api` with no version path segment (no `/v1/`, `/v2/`). No Accept-Version headers. No version query parameters. All API endpoints are unversioned: `/articles`, `/users/login`, `/profiles/:username`, `/tags`. If the external API introduces breaking changes, all consumers are affected simultaneously. |
| **Gap** | No versioning — breaking changes in the API would break the application. No backward compatibility guarantees. |
| **Recommendation** | Introduce API versioning: (1) If building an owned backend, include version prefix in all API paths (e.g., `/v1/articles`). (2) If continuing to use the external API, introduce an API Gateway (preferred) as a proxy layer that can transform between API versions. (3) Document the API contract to track breaking changes. |
| **Evidence** | `src/app/core/interceptors/api.interceptor.ts` — API URL `https://api.realworld.show/api` with no version segment. `src/app/features/article/services/articles.service.ts` — endpoints like `/articles`, `/articles/feed`, `/articles/:slug`. No versioning patterns in any service file. |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The API base URL is hardcoded in source code: `https://api.realworld.show/api` in `api.interceptor.ts`. There is no environment variable configuration, no service discovery mechanism, no API catalog, and no dynamic routing. The URL cannot be changed without modifying and redeploying the source code. |
| **Gap** | All service endpoints hardcoded in application code. Cannot deploy to different environments (dev, staging, prod) without code changes. No service discovery mechanism. |
| **Recommendation** | Externalize the API URL via environment variable injection at build time (Angular `environment.ts` files) or runtime (config file loaded at startup). Use Amazon API Gateway as a stable entry point that can route to different backend environments. |
| **Evidence** | `src/app/core/interceptors/api.interceptor.ts` — `const apiReq = req.clone({ url: \`https://api.realworld.show/api${req.url}\` })`. No `environment.ts` files. No `.env` files. No service discovery imports. |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No unstructured data storage exists. The SPA does not store any data server-side — it is a browser-based application. The only client-side storage is the JWT token in browser `localStorage` (`jwt.service.ts`). No S3 buckets, no EFS, no document storage. Article body content (markdown) is stored and retrieved via the external API. User avatar images are referenced by URL but not stored by this application. |
| **Gap** | No managed object storage. If the application needs to handle file uploads (images, documents), there is no storage infrastructure. |
| **Recommendation** | If file upload capabilities are needed, provision Amazon S3 for unstructured data storage with appropriate lifecycle policies. For document parsing (if applicable), integrate Amazon Textract. |
| **Evidence** | `src/app/core/auth/services/jwt.service.ts` — localStorage for JWT only. No S3 SDK imports. No file upload patterns in source code. |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The Angular application has a well-structured data access layer with domain-specific services: `ArticlesService` (article CRUD, favorites), `CommentsService` (comment CRD), `TagsService` (tag list), `ProfileService` (profile get, follow/unfollow), `UserService` (auth, user CRUD). Each service encapsulates all HTTP calls for its domain via Angular `HttpClient`. The `apiInterceptor` provides a centralized URL prefix mechanism. The `tokenInterceptor` adds authentication headers centrally. The `errorInterceptor` provides centralized error handling. This is a clean service layer pattern. |
| **Gap** | While the service layer is well-organized, all services route to a single external API with no abstraction layer between the services and the HTTP transport. Direct `HttpClient` usage means the transport mechanism is coupled to the service layer. A repository/adapter pattern would provide more flexibility. |
| **Recommendation** | The current service layer is a good foundation. If building a backend, maintain this domain-oriented pattern. Consider adding an adapter/repository layer between the services and the HTTP transport to enable easier backend swapping. |
| **Evidence** | `src/app/features/article/services/articles.service.ts`, `src/app/features/article/services/comments.service.ts`, `src/app/features/article/services/tags.service.ts`, `src/app/features/profile/services/profile.service.ts`, `src/app/core/auth/services/user.service.ts`, `src/app/core/interceptors/api.interceptor.ts`, `src/app/core/interceptors/token.interceptor.ts`, `src/app/core/interceptors/error.interceptor.ts` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database engine version management exists. This is a frontend SPA with no database infrastructure defined. No IaC specifying database engine versions, no Helm values with engine versions, no docker-compose with database images. The application depends entirely on the external API for data persistence. |
| **Gap** | No database version management. If databases are introduced, engine version pinning and EOL tracking need to be established. |
| **Recommendation** | When introducing databases, explicitly pin engine versions in IaC. Track EOL dates and plan upgrades proactively. For Aurora (preferred), specify `engine_version` in CDK/Terraform. |
| **Evidence** | No IaC files. No database configuration. No docker-compose files. |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs exist. This is a frontend SPA with no database interaction — all data operations are HTTP REST calls to the external API. There are no `.sql` files, no ORM configurations, no raw SQL execution. All business logic resides in the Angular application layer (components and services). |
| **Gap** | None — no database coupling. |
| **Recommendation** | Maintain this pattern. When building backend services, keep business logic in the application layer. Avoid stored procedures and proprietary SQL to maintain database portability. |
| **Evidence** | No `.sql` files. No ORM imports. No `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION` patterns. No database-related imports in any source file. |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No audit logging configuration exists. No CloudTrail, no CloudWatch Logs, no application-level audit logging. The application has no IaC defining any logging infrastructure. Client-side errors are caught by `errorInterceptor` and re-thrown but not logged to any persistent service. |
| **Gap** | No audit logging. No ability to trace actions or perform forensic analysis. |
| **Recommendation** | When deploying to AWS, enable CloudTrail with log file validation and S3 object lock for immutable storage. For the frontend application, add client-side error reporting to a service like CloudWatch RUM or a third-party error tracking service. |
| **Evidence** | No `aws_cloudtrail` in IaC. No logging configuration. `src/app/core/interceptors/error.interceptor.ts` catches errors but only re-throws them for component handling. |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest configuration exists. No KMS keys, no encrypted data stores, no encryption configuration in IaC. The application has no data stores to encrypt. Client-side storage (localStorage JWT) is not encrypted at the application level (browser handles storage security). |
| **Gap** | No encryption at rest configuration. |
| **Recommendation** | When introducing data stores, enable encryption at rest with customer-managed KMS keys. For S3, enable default encryption. For Aurora/DynamoDB, configure KMS encryption. Define a key rotation policy. |
| **Evidence** | No IaC files. No KMS configuration. No encryption-related code or configuration. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application implements JWT token-based authentication at the client level. `token.interceptor.ts` adds an `Authorization: Token <jwt>` header to all HTTP requests when a token exists. `user.service.ts` manages authentication state (login, register, getCurrentUser, logout). `jwt.service.ts` handles token storage in localStorage. `error.interceptor.ts` handles 401 responses by purging auth state. However, this is all client-side implementation — there is no server-side API Gateway authorizer, no Cognito integration, no OAuth2 flow, no OIDC. The external API handles actual authentication validation. |
| **Gap** | Token-based auth exists at the client level but there is no server-side enforcement visible in this repository. No API Gateway with authorizers, no Cognito user pools, no OAuth2/OIDC flows. Authentication depends entirely on the external API's implementation. |
| **Recommendation** | When building owned backend services, implement proper server-side authentication: Amazon Cognito user pools with OAuth2/OIDC, API Gateway authorizers for all endpoints, and token rotation. Replace the custom `Token` header scheme with standard `Bearer` JWT. |
| **Evidence** | `src/app/core/interceptors/token.interceptor.ts` — adds `Authorization: Token <jwt>` header. `src/app/core/auth/services/user.service.ts` — login/register/getCurrentUser flows. `src/app/core/auth/services/jwt.service.ts` — localStorage token management. `src/app/core/interceptors/error.interceptor.ts` — 401 handling. |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application manages its own authentication entirely. Users register via `POST /users` and login via `POST /users/login` (both in `user.service.ts`). JWT tokens are stored in browser localStorage. There is no integration with a centralized identity provider — no Cognito, no Okta, no Ping, no OIDC/SAML federation, no SSO configuration. |
| **Gap** | Application manages its own authentication with no external IdP integration. |
| **Recommendation** | Integrate Amazon Cognito as the centralized identity provider. Cognito provides user pools, OAuth2/OIDC flows, social login (Google, Facebook, Apple), MFA, and SSO. This eliminates custom auth code and provides enterprise-grade identity management. |
| **Evidence** | `src/app/core/auth/services/user.service.ts` — custom login/register/logout implementation. `src/app/core/auth/services/jwt.service.ts` — custom token management. No Cognito, OIDC, or SAML configuration. |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The API URL (`https://api.realworld.show/api`) is hardcoded in source code (`api.interceptor.ts`). JWT tokens are stored in browser localStorage — standard for SPAs but not the most secure option (vulnerable to XSS; HttpOnly cookies are more secure). CI/CD workflows use GitHub Secrets for AWS credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`) and API keys (`ATXCI_API_KEY`, `ATXCI_API_URL`). No Secrets Manager, HashiCorp Vault, or AWS SSM Parameter Store. No `.env` files committed to the repository. |
| **Gap** | No dedicated secrets management service. CI/CD credentials are in GitHub Secrets (acceptable for CI) but there is no runtime secrets management for the application. API URL is hardcoded. |
| **Recommendation** | Externalize configuration (including API URL) via environment variables or a config service. When deploying backend services, use AWS Secrets Manager with automated rotation for database credentials and API keys. Consider moving JWT storage from localStorage to HttpOnly cookies for improved XSS protection. |
| **Evidence** | `src/app/core/interceptors/api.interceptor.ts` — hardcoded API URL. `src/app/core/auth/services/jwt.service.ts` — `window.localStorage['jwtToken']`. `.github/workflows/deploy.yml` — references `secrets.AWS_ACCESS_KEY_ID`, `secrets.ATXCI_API_KEY`. No `.env` files committed. |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute resources exist to harden or patch. No EC2 instances, no ECS tasks, no container images, no AMIs. The application runs entirely in the browser. No SSM Patch Manager, no vulnerability scanning (Inspector/Snyk), no hardened base images. |
| **Gap** | No compute hardening. No patching strategy. |
| **Recommendation** | When deploying compute resources (containers, EC2), implement: SSM Patch Manager for automated OS patching, AWS Inspector or Snyk for vulnerability scanning, hardened base images (Bottlerocket for containers, CIS-hardened AMIs for EC2). |
| **Evidence** | No IaC files. No Dockerfiles. No AMI references. No SSM configuration. |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No standard SAST, DAST, or dependency vulnerability scanning tools are integrated into the CI/CD pipeline. The `security-tests.yml` workflow runs Playwright-based XSS e2e tests (`e2e/xss-security.spec.ts`), which test for specific XSS vectors in image URLs, article descriptions, and article body markdown. While this is a form of security testing, it is custom-built and narrowly scoped — the test file itself includes a disclaimer: "These tests are NOT a comprehensive security audit." No Dependabot configuration, no `npm audit` in CI, no Snyk, no SonarQube, no Semgrep. No container scanning (no containers). |
| **Gap** | No standard security scanning tools. Custom XSS e2e tests exist but are not a substitute for SAST, dependency scanning, or comprehensive DAST. |
| **Recommendation** | Add to the CI pipeline: (1) `npm audit` or Snyk for dependency vulnerability scanning. (2) Semgrep or ESLint security rules for SAST. (3) Configure Dependabot for automated dependency update PRs. (4) Consider OWASP ZAP for comprehensive DAST. The existing XSS tests are a good complement but not a replacement for standard scanning tools. |
| **Evidence** | `.github/workflows/security-tests.yml` — runs `bun run test:e2e:security`. `e2e/xss-security.spec.ts` — custom XSS tests. No `.snyk` file. No `dependabot.yml`. No `npm audit` in any workflow. No SonarQube or Semgrep configuration. |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumentation exists. No OpenTelemetry SDK in dependencies, no X-Ray integration, no `traceparent` or `X-Amzn-Trace-Id` header propagation. The application has no observability infrastructure. HTTP requests from the SPA to the external API carry no trace context. |
| **Gap** | No distributed tracing. Cannot trace request flows from browser to API or debug cross-service failures. |
| **Recommendation** | Add OpenTelemetry browser instrumentation for client-side tracing. When building backend services, instrument with OpenTelemetry and export to AWS X-Ray. Propagate trace context (`traceparent` header) across service boundaries. Consider Amazon CloudWatch RUM for real-user monitoring. |
| **Evidence** | No `@opentelemetry/*` in `package.json`. No X-Ray SDK. No trace ID headers in interceptors. |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions exist. No error budget tracking, no CloudWatch alarms on p99/p95 latency, no SLO dashboards. No formal definition of acceptable service levels for any user journey (page load time, API response time, error rate). |
| **Gap** | No SLOs defined. Cannot measure whether the application is meeting user expectations. |
| **Recommendation** | Define SLOs for critical user journeys: home page load time (p95 < 2s), article page render time (p95 < 1.5s), API error rate (< 1%). Use CloudWatch RUM to measure real-user performance and CloudWatch Synthetics for synthetic monitoring. |
| **Evidence** | No SLO definition files. No CloudWatch alarm configuration. No monitoring infrastructure. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics are published. No `cloudwatch.put_metric_data` calls, no analytics integration, no business KPI tracking. The application does not measure business outcomes (article creation rate, user engagement, conversion rates). Only default browser DevTools provide any performance data. |
| **Gap** | No business metrics. Infrastructure metrics (if any existed) would not indicate whether the application is delivering value. |
| **Recommendation** | Implement client-side analytics: track article views, comment creation rate, user registration rate, and session duration. Use Amazon CloudWatch RUM or a third-party analytics service. These metrics inform prioritization of modernization investments. |
| **Evidence** | No analytics imports in `package.json`. No metrics collection code in source files. |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting or anomaly detection configured. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no static threshold alerts, no anomaly detection. The application has no monitoring infrastructure. |
| **Gap** | No alerting. Degradation or failures would go unnoticed until users report them. |
| **Recommendation** | When deploying to AWS, configure CloudWatch alarms: error rate anomaly detection, latency p99 alerts, and availability checks. Integrate with Amazon SNS or PagerDuty for alert routing. |
| **Evidence** | No CloudWatch configuration. No alerting configuration. No monitoring infrastructure. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The deployment strategy is direct-to-production via GitHub Releases. `deploy.yml` builds the application, creates a zip file from `dist/angular-conduit/browser/`, and publishes it as a GitHub Release with tag `build-<run_number>`. There is no blue/green deployment, no canary release, no traffic shifting, no CodeDeploy integration, no health check-based rollback. Old releases are cleaned up after 7 days. |
| **Gap** | Direct-to-production deployment with no staged rollout, no traffic shifting, and no automated rollback. A bad deployment would immediately affect all users. |
| **Recommendation** | Implement staged deployments: (1) For S3+CloudFront hosting, use CloudFront staging distributions or origin failover for blue/green. (2) For EKS, use rolling updates with readiness probes or Argo Rollouts for canary. (3) Add health checks and automated rollback triggers. |
| **Evidence** | `.github/workflows/deploy.yml` — `softprops/action-gh-release@v1` creates releases. No CodeDeploy. No traffic shifting. No canary configuration. |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Playwright e2e tests cover critical user workflows and run in CI. Test files: `auth.spec.ts` (login, register), `articles.spec.ts` (article CRUD), `comments.spec.ts` (comment CRD), `settings.spec.ts` (user settings), `navigation.spec.ts` (page navigation), `social.spec.ts` (follow/unfollow), `xss-security.spec.ts` (XSS protection), `error-handling.spec.ts`, `health.spec.ts`, `null-fields.spec.ts`, `user-fetch-errors.spec.ts`, `url-navigation.spec.ts`. Tests run in CI via `playwright.yml` on push/PR to main. Vitest unit tests exist for core services (`jwt.service.spec.ts`, `user.service.spec.ts`, `articles.service.spec.ts`, `comments.service.spec.ts`, `tags.service.spec.ts`, `profile.service.spec.ts`) with comprehensive coverage of service methods. |
| **Gap** | E2e tests run against the live external API (`api.realworld.show`), introducing external dependency flakiness. Unit tests exist but are not explicitly run as a CI step (only e2e tests via `playwright.yml`). No contract tests. |
| **Recommendation** | (1) Add `bun run test` (Vitest) as a required CI step. (2) Consider running e2e tests against a local mock API for deterministic results. (3) Add API contract tests to catch breaking changes from the external API early. |
| **Evidence** | `.github/workflows/playwright.yml` — runs `bun run test:e2e` in CI. `e2e/*.spec.ts` — 12 test files covering critical workflows. `src/app/**/services/*.spec.ts` — 5 unit test files with comprehensive service testing. `playwright.config.ts` — configuration with `webServer` pointing to `localhost:4200`. |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response automation exists. No runbooks (markdown, YAML, or JSON), no SSM Automation documents, no Lambda-based remediation, no self-healing patterns. No documented incident response procedures. |
| **Gap** | No incident response automation. Response to incidents is entirely ad hoc. |
| **Recommendation** | Create runbooks for common incidents (deployment failures, API unavailability, performance degradation). When deploying to AWS, implement SSM Automation documents for automated remediation (e.g., CloudFront cache invalidation, ECS service restart). |
| **Evidence** | No runbook files. No SSM configuration. No Lambda remediation functions. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership exists. No service-level dashboards, no alarm owners, no SLO definitions with team attribution. No CODEOWNERS file referencing observability assets. No per-service dashboards or alarms. |
| **Gap** | No observability ownership. No monitoring assets exist to own. |
| **Recommendation** | When deploying to AWS, establish observability ownership: create per-service dashboards, assign alarm owners, define SLOs with team attribution. Add a CODEOWNERS file that includes observability configuration files. |
| **Evidence** | No dashboard configuration. No alarm configuration. No CODEOWNERS file. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging exists. No IaC with tags, no `default_tags` in any Terraform provider configuration, no tag enforcement policies. The application has no AWS resources to tag. |
| **Gap** | No tagging governance. Cannot track costs, ownership, or environment association. |
| **Recommendation** | When creating IaC, establish a tagging standard from the start. Required tags: `Environment`, `Service`, `Team`, `CostCenter`. Use `default_tags` in Terraform or CDK's `Tags.of()` for consistent application. Enforce with AWS Config rules and Tag Policies in AWS Organizations. |
| **Evidence** | No IaC files. No AWS resources. No tagging configuration. |

## Learning Materials

The following learning resources are mapped to the triggered pathways from this assessment:

### Move to Cloud Native
- [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

### Move to Containers
- [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM)
- [Move to Containers with Amazon ECS](https://skillbuilder.aws/learning-plan/CDA8Y4JRRR)
- [EKS Workshop](https://www.eksworkshop.com/)

### Move to Managed Databases
- [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)
- [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)

### Move to Modern DevOps
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `package.json` | APP-Q1, INF-Q11, OPS-Q1 | Dependencies, scripts, language/framework versions (Angular 21, TypeScript 5.9, RxJS 7.8) |
| `angular.json` | INF-Q1, APP-Q2 | Build configuration, single project output to `dist/angular-conduit` |
| `tsconfig.json` | APP-Q1 | TypeScript configuration (ES2022 target, strict mode) |
| `src/main.ts` | APP-Q2 | Application entry point — single bootstrap |
| `src/app/app.config.ts` | APP-Q2, SEC-Q3 | Application configuration, interceptor registration, auth initialization |
| `src/app/app.routes.ts` | APP-Q2 | Route definitions with lazy loading, auth guards |
| `src/app/core/interceptors/api.interceptor.ts` | APP-Q5, APP-Q6, INF-Q6, SEC-Q5 | Hardcoded API URL `https://api.realworld.show/api` |
| `src/app/core/interceptors/token.interceptor.ts` | SEC-Q3 | JWT token injection on HTTP requests (`Authorization: Token`) |
| `src/app/core/interceptors/error.interceptor.ts` | SEC-Q1, SEC-Q3 | Centralized HTTP error handling, 401 logout |
| `src/app/core/auth/services/user.service.ts` | SEC-Q3, SEC-Q4, APP-Q3, APP-Q4 | Auth state management (login, register, getCurrentUser, logout, auto-retry) |
| `src/app/core/auth/services/jwt.service.ts` | SEC-Q3, SEC-Q5 | JWT token localStorage management |
| `src/app/features/article/services/articles.service.ts` | APP-Q3, APP-Q4, DATA-Q2 | Article CRUD operations, HTTP client usage |
| `src/app/features/article/services/comments.service.ts` | APP-Q3, DATA-Q2 | Comment CRD operations |
| `src/app/features/article/services/tags.service.ts` | DATA-Q2 | Tag list retrieval |
| `src/app/features/profile/services/profile.service.ts` | APP-Q3, DATA-Q2 | Profile get, follow, unfollow operations |
| `src/app/core/auth/services/jwt.service.spec.ts` | OPS-Q6 | Unit tests for JWT service (Vitest) |
| `src/app/core/auth/services/user.service.spec.ts` | OPS-Q6 | Unit tests for User service (Vitest) |
| `src/app/features/article/services/articles.service.spec.ts` | OPS-Q6 | Unit tests for Articles service (Vitest) |
| `src/app/features/article/services/comments.service.spec.ts` | OPS-Q6 | Unit tests for Comments service (Vitest) |
| `src/app/features/article/services/tags.service.spec.ts` | OPS-Q6 | Unit tests for Tags service (Vitest) |
| `src/app/features/profile/services/profile.service.spec.ts` | OPS-Q6 | Unit tests for Profile service (Vitest) |
| `.github/workflows/deploy.yml` | INF-Q1, INF-Q11, OPS-Q5, SEC-Q5 | Build + zip + GitHub Release deployment; ATX transform job; GitHub Secrets usage |
| `.github/workflows/lint.yml` | INF-Q11 | Prettier format check on push/PR |
| `.github/workflows/playwright.yml` | INF-Q11, OPS-Q6 | Playwright e2e tests in CI on push/PR |
| `.github/workflows/security-tests.yml` | INF-Q11, SEC-Q7 | XSS security e2e tests in CI |
| `e2e/xss-security.spec.ts` | SEC-Q7 | Custom XSS security tests (image URL injection, markdown body, article description) |
| `e2e/auth.spec.ts` | OPS-Q6 | E2e tests for authentication flows |
| `e2e/articles.spec.ts` | OPS-Q6 | E2e tests for article CRUD |
| `e2e/comments.spec.ts` | OPS-Q6 | E2e tests for comment operations |
| `e2e/settings.spec.ts` | OPS-Q6 | E2e tests for user settings |
| `e2e/navigation.spec.ts` | OPS-Q6 | E2e tests for page navigation |
| `e2e/social.spec.ts` | OPS-Q6 | E2e tests for follow/unfollow |
| `e2e/playwright.base.ts` | OPS-Q6 | Shared Playwright configuration |
| `playwright.config.ts` | OPS-Q6 | Playwright config with Angular dev server |
| `vitest.config.ts` | OPS-Q6 | Vitest unit test configuration |
| `README.md` | Quick Agent Wins | Project documentation, setup instructions, functionality overview |
| `CLAUDE.md` | Quick Agent Wins | Commands reference, code style guidelines |
| `src/app/core/` | APP-Q2 | Core module (auth, interceptors, layout, models) |
| `src/app/features/` | APP-Q2 | Feature modules (article, profile, settings) |
| `src/app/shared/` | APP-Q2 | Shared module (components, pipes) |
