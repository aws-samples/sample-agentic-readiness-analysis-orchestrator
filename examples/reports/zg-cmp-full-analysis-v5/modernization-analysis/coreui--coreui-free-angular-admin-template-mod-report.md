# Modernization Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | coreui-free-angular-admin-template |
| **Date** | 2026-04-30 |
| **TD Version** | 3g1iuew7esd4bia3qcdwvael |
| **Repo Type** | application |
| **Service Archetype** | stateless-utility (auto-detected) |
| **Priority** | P2 |
| **Tags** | html, frontend, angular |
| **Context** | CoreUI Angular admin dashboard template. |
| **Preferences** | Prefer: eks, aurora, dynamodb, api-gateway, eventbridge, bedrock · Avoid: self-managed-kafka, self-managed-kubernetes, oracle |
| **Surface Flags** | has_persistent_data_store=false, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=false, has_multi_instance_deployment=false |
| **Overall Score** | **1.55 / 4.0** |

**Archetype Justification**: No database connections, no backend API endpoints, no message queue consumers, and no downstream service calls detected. All data is hardcoded in component files (mock users, mock notifications, mock charts). This is a pure frontend Angular dashboard template with no server-side runtime, classified as stateless-utility.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.57 / 4.0 | 🟠 Needs Work |
| Application Architecture (APP) | 2.25 / 4.0 | 🟠 Needs Work |
| Data Platform Modernization (DATA) | 1.75 / 4.0 | 🟠 Needs Work |
| Security Baseline (SEC) | 1.17 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.00 / 4.0 | ❌ Not Present |
| **Overall** | **1.55 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | OPS-Q5: Deployment Strategy | 1 | No deployment strategy — CI/CD pipeline only builds and tests, no deploy stage exists | Blocks safe, repeatable delivery; manual deployments are error-prone and slow (triggers Move to Modern DevOps) |
| 2 | INF-Q10: IaC Coverage | 1 | Zero infrastructure defined as code — no Terraform, CDK, CloudFormation, or Helm files | All infrastructure creation is manual/ClickOps; no reproducibility, no disaster recovery path (triggers Move to Modern DevOps) |
| 3 | SEC-Q7: Application Security Pipeline | 1 | No SAST, DAST, or dependency vulnerability scanning in CI/CD | Vulnerabilities in dependencies reach production undetected; no security gates |
| 4 | INF-Q1: Managed Compute | 1 | No compute infrastructure defined — no ECS, EKS, Lambda, or EC2 resources | Application has no deployment target; cannot be hosted on AWS without infrastructure provisioning (triggers Move to Containers) |
| 5 | SEC-Q1: Audit Logging | 1 | No CloudTrail or equivalent audit logging configured | No ability to trace actions or perform forensic analysis after incidents |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** INF-Q11 = 2 (≥ 2). CI/CD pipeline exists at `.github/workflows/build-check.yml` with automated build and test stages across 3 OS platforms (ubuntu, windows, macOS).
- **What it enables:** A DevOps agent could trigger builds, check build status across the 3-OS matrix, report build failures, and manage CI workflow operations via the GitHub Actions API.
- **Additional steps:** Add deployment stages to the pipeline for full DevOps agent utility. Currently only build/test is automated — deploying the built static assets (e.g., to S3 + CloudFront or EKS) would expand the agent's operational surface.
- **Effort:** Medium

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository — `README.md` (comprehensive setup, usage, and project structure guide), `CHANGELOG.md` (detailed version history with dependency updates and vulnerability patches), `.github/CONTRIBUTING.md`, `.github/SUPPORT.md`, `.github/COMMIT_CONVENTION.md`.
- **What it enables:** A RAG-based knowledge agent could index the README, CHANGELOG, contributing guidelines, and CoreUI documentation references to answer developer questions about setup, version compatibility, upgrade procedures, and project conventions.
- **Additional steps:** Index external CoreUI documentation (https://coreui.io/angular/docs/) as an additional knowledge source for comprehensive coverage.
- **Effort:** Low

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 — application has well-defined module boundaries via lazy-loaded routes; primary trigger (APP-Q2 < 3) not met |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1 = 1 (no compute infrastructure) AND no container definitions (Dockerfile, docker-compose, K8s manifests) found |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 — no stored procedures or proprietary SQL; no commercial database engines detected |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = Not Evaluated — no databases exist in this repository to migrate |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 4 (sync is correct for archetype); no data processing workloads detected |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (no IaC), INF-Q11 = 2 (no deploy stage); OPS-Q5 = 1 (no deployment strategy), OPS-Q6 = 1 (no integration tests) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context |

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model:**
No compute infrastructure exists. The repository is a pure frontend Angular SPA template (`package.json`, `angular.json`) with no IaC defining any compute resources — no `aws_ecs_*`, `aws_eks_*`, `aws_lambda_*`, `aws_instance`, no Kubernetes manifests, no Helm charts. The built artifacts (static HTML/CSS/JS in `dist/`) have no defined deployment target.

**Container Readiness Indicators:**
- ✅ Application builds to static assets (`ng build` → `dist/coreui-free-angular-admin-template/`) — straightforward to containerize with an Nginx or Node.js static server
- ✅ No database connections or persistent state to configure
- ✅ No secrets or environment-specific configuration required at build time
- ✅ Build process is well-defined in `package.json` scripts (`npm run build`)
- ❌ No Dockerfile exists — needs to be created
- ❌ No container orchestration configuration (no ECS task definitions, no Kubernetes manifests)

**Recommended Approach:**
Given that this is a static SPA, containerization is straightforward:

1. **Create a Dockerfile** using a multi-stage build: Stage 1 builds the Angular app with Node.js; Stage 2 serves static assets with Nginx Alpine
2. **Deploy to Amazon EKS** (preferred per preferences) with a Kubernetes Deployment and Service
3. **Alternative:** Deploy built static assets directly to S3 + CloudFront (simpler for static content, avoids container overhead entirely). This is the recommended first step before containerization — static asset hosting on S3/CloudFront is more cost-effective and operationally simpler for a pure SPA

**Representative AWS Services:** Amazon EKS (preferred), Amazon ECR, Amazon S3 + CloudFront (for static hosting alternative), AWS App Runner

**Migration Approach:**
- **Phase 1 (Quick Win):** Deploy static assets to S3 with CloudFront distribution — no containerization needed, lowest effort
- **Phase 2 (If dynamic features added):** Create Dockerfile, push to ECR, deploy to EKS with Helm chart

**Guidance:** [AWS Containers Strategy](https://aws.amazon.com/containers/) · [EKS Workshop](https://www.eksworkshop.com/)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 1):**
Zero infrastructure defined as code. No `.tf`, `cdk.json`, `template.yaml`, `Chart.yaml`, or `kustomization.yaml` files exist. All infrastructure (if any) would be manually created. The repository contains only application source code and CI configuration.

**Current CI/CD State (INF-Q11 = 2):**
A GitHub Actions workflow exists at `.github/workflows/build-check.yml` providing:
- ✅ Automated build on push, PR, and daily schedule (cron `15 4 * * *`)
- ✅ Multi-platform testing (ubuntu-latest, windows-latest, macOS-latest)
- ✅ Node.js 24.x with `npm ci` for deterministic installs
- ✅ Unit tests run as prebuild step (`ng test --watch=false`)
- ❌ **No deployment stage** — pipeline stops after `npm run build`
- ❌ No IaC deployment automation
- ❌ No artifact publishing (built assets are not pushed to S3, ECR, or any artifact store)

**Deployment Strategy Gaps (OPS-Q5 = 1):**
No deployment strategy of any kind. No CodeDeploy, no Helm releases, no Argo Rollouts, no traffic shifting configurations.

**Testing Gaps (OPS-Q6 = 1):**
Only unit tests exist (`*.spec.ts` files with Vitest). No integration tests, no E2E tests in CI, no contract tests.

**Recommended DevOps Toolchain:**
1. **IaC:** Define infrastructure with AWS CDK (TypeScript — matches the existing codebase language) or Terraform
   - S3 bucket + CloudFront distribution for static hosting
   - Or EKS cluster resources if containerizing (preferred per preferences)
2. **CI/CD Pipeline Enhancement:**
   - Add deployment stages to `.github/workflows/build-check.yml`:
     - `deploy-staging` → deploy to staging environment after build
     - `deploy-production` → deploy to production with manual approval gate
   - Add `npm audit` step for dependency vulnerability scanning (SEC-Q7 improvement)
   - Add artifact upload step (S3 sync or ECR push)
3. **Deployment Strategy:** Implement blue/green or canary deployment via CloudFront distribution switching (for static hosting) or EKS rolling updates (for containerized deployment)
4. **Testing:** Add E2E tests using Playwright (already a devDependency) and run them in CI

**Representative AWS Services:** AWS CDK, CodePipeline, CodeBuild, CodeDeploy, CloudFormation, S3, CloudFront, Amazon EKS (preferred)

**Guidance:** [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute infrastructure is defined in this repository. No Terraform resources (`aws_ecs_*`, `aws_eks_*`, `aws_lambda_*`, `aws_instance`), no CloudFormation templates, no CDK stacks, no Kubernetes manifests, and no Helm charts were found. The repository contains only Angular frontend source code that builds to static assets (`dist/coreui-free-angular-admin-template/`). |
| **Gap** | All compute is undefined — the application has no deployment target on AWS. No managed compute (ECS, EKS, Lambda, Fargate) or even raw EC2 is provisioned. |
| **Recommendation** | For a static SPA, deploy built assets to S3 + CloudFront (simplest path). If dynamic server-side rendering is added, containerize with a multi-stage Dockerfile and deploy to Amazon EKS (preferred). Define all compute infrastructure as code using AWS CDK (TypeScript). |
| **Evidence** | No `.tf`, `cdk.json`, `template.yaml`, `Chart.yaml`, `kustomization.yaml`, `Dockerfile`, or `docker-compose.yml` files found in the repository. |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy a database. INF-Q2 does not apply. No database resources exist in IaC (none exists), no database drivers or connection configurations in `package.json` dependencies, and no database-related imports in source code. All data is hardcoded in TypeScript component files. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `package.json` — no database drivers (no `pg`, `mysql2`, `mongoose`, `typeorm`, `prisma`, `sequelize`). No `.env` files with connection strings. |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Workflow orchestration is not applicable by design — no multi-step workflows exist for a pure frontend dashboard template. There are no business processes to orchestrate, no Step Functions, no Temporal SDK, no workflow definitions. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No `aws_sfn_*` in IaC. No workflow SDK imports in source code. No multi-step business operations detected. |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | This service is a `stateless-utility`. Synchronous client-side rendering is the correct design for a frontend dashboard template — no messaging infrastructure is needed. The application renders UI components in the browser with hardcoded data; there are no cross-service state changes, no event streams, and no message queues. |
| **Gap** | None — synchronous design is appropriate for this archetype. |
| **Recommendation** | Adopting async messaging is NOT recommended for this archetype — it would add operational complexity without architectural benefit. If the application evolves to include a backend with cross-service communication, EventBridge (preferred) or SQS should be evaluated at that time. |
| **Evidence** | No `aws_sqs_*`, `aws_sns_*`, `aws_msk_*`, `aws_kinesis_*`, `aws_eventbridge_*` in IaC. No messaging SDK imports in `package.json`. No event-driven handler patterns in source code. |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No network security configuration exists. No VPC, subnets, security groups, NACLs, or network segmentation defined. No IaC files exist to define any networking resources. |
| **Gap** | No network security infrastructure — services have no VPC, no private subnets, no security group rules. |
| **Recommendation** | When deploying to AWS, define a VPC with private subnets using AWS CDK. For S3 + CloudFront hosting, configure CloudFront with OAC (Origin Access Control) to restrict direct S3 access. For EKS deployment (preferred), create a VPC with public/private subnet tiers, security groups with least-privilege rules, and VPC endpoints for AWS service access. |
| **Evidence** | No `.tf` or IaC files found. No `aws_vpc`, `aws_subnet`, `aws_security_group` resources. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, AppSync, ALB, or CloudFront is defined as an entry point. No IaC exists to define any entry point infrastructure. |
| **Gap** | No managed entry point with throttling, auth, or request validation. |
| **Recommendation** | For static SPA hosting, deploy behind CloudFront with custom error pages for SPA routing, WAF rules for DDoS protection, and origin access control for S3. For API endpoints (if a backend is added), use Amazon API Gateway (preferred) with throttling, authorization, and request validation. |
| **Evidence** | No `aws_api_gateway_*`, `aws_apigatewayv2_*`, `aws_lb_*`, `aws_cloudfront_distribution` in IaC. |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. No compute infrastructure is defined, so there is nothing to scale. |
| **Gap** | No auto-scaling — all capacity would be statically provisioned if infrastructure existed. |
| **Recommendation** | When deploying, choose inherently scalable services: S3 + CloudFront scales automatically for static content delivery. If deploying to EKS (preferred), configure Horizontal Pod Autoscaler (HPA) and Cluster Autoscaler with appropriate min/max settings. |
| **Evidence** | No `aws_autoscaling_*`, `aws_appautoscaling_*` resources. No scaling policies. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no persistent state to back up. INF-Q8 does not apply. No databases, S3 buckets, EBS volumes, or other data stores are defined. All application data is hardcoded in source files and version-controlled in Git. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No `aws_rds_*`, `aws_dynamodb_*`, `aws_s3_bucket`, `aws_backup_plan` in IaC. No database connections in source code. |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload requiring HA evaluation. INF-Q9 does not apply. No compute resources, no load balancers, no multi-AZ configuration exists. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No `aws_instance`, `aws_ecs_service`, `aws_eks_cluster`, `aws_lb` resources. No `multi_az` or `availability_zones` configuration. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero infrastructure is defined as code. No Terraform files (`.tf`), no CDK stacks (`cdk.json`), no CloudFormation templates (`template.yaml`), no Helm charts (`Chart.yaml`), and no Kustomize files (`kustomization.yaml`) exist in the repository. |
| **Gap** | 0% IaC coverage — all infrastructure (if any) would be created manually via ClickOps. |
| **Recommendation** | Adopt AWS CDK (TypeScript) to define all infrastructure as code. TypeScript matches the existing codebase language, reducing the learning curve. Start with the deployment target (S3 + CloudFront stack or EKS stack) and expand to include monitoring, alarms, and CI/CD pipeline resources. |
| **Evidence** | File scan found 0 IaC files across the entire repository. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | A GitHub Actions workflow exists at `.github/workflows/build-check.yml` that automates build and test on push, PR, and a daily schedule. It runs across 3 OS platforms (ubuntu-latest, windows-latest, macOS-latest) with Node.js 24.x. The `prebuild` script runs unit tests (`ng test --watch=false`) before building. However, there is **no deployment stage** — the pipeline stops after `npm run build`. No artifact publishing, no deployment automation, no IaC deployment. A second workflow (`.github/workflows/stale.yml`) manages stale issues but is not deployment-related. |
| **Gap** | Build is automated but deployment is entirely absent. No deploy stage, no artifact upload, no environment promotion. No IaC deployment automation. |
| **Recommendation** | Extend `.github/workflows/build-check.yml` with deployment stages: (1) Add `aws s3 sync` step to deploy built assets to S3 staging after successful build, (2) Add production deployment with manual approval gate, (3) Add `npm audit` step for dependency scanning, (4) Add artifact caching/upload for build reproducibility. |
| **Evidence** | `.github/workflows/build-check.yml` — build + test only, no deploy stage. `.github/workflows/stale.yml` — issue management only. |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | TypeScript 5.9.3 with Angular 21.2.5 — a modern cloud-native language at the current version with the latest framework. TypeScript/Node.js has first-class AWS SDK coverage via `@aws-sdk/*`. The `package.json` specifies Node.js `^20.19.0 || ^22.12.0 || ^24.0.0`. Angular 21 is the latest major version with modern features: standalone components, signals, control flow, and lazy-loaded routes. |
| **Gap** | None — language and framework are current. |
| **Recommendation** | Maintain current Angular and TypeScript versions. When adding AWS backend services, leverage `@aws-sdk/client-*` v3 packages (TypeScript-native). |
| **Evidence** | `package.json` — `typescript: ~5.9.3`, `@angular/core: ^21.2.5`. `tsconfig.json` — `target: ES2022`, `strict: true`. |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Single deployable Angular SPA with well-defined module boundaries. The application uses lazy-loaded routes (`loadChildren`/`loadComponent` in `src/app/app.routes.ts`) for each view section: dashboard, theme, base, buttons, forms, icons, notifications, widgets, charts, and pages. Components are standalone (no `NgModule` dependencies), organized in clear directory structures with separate route definitions per view module (`routes.ts` in each view directory). No circular dependencies detected between modules. |
| **Gap** | Minor — this is a modular monolith (single deployable unit) rather than independently deployable services. However, for a frontend dashboard template, this is an appropriate architecture. The module boundaries are clean and could support future extraction if needed. |
| **Recommendation** | The modular monolith architecture is appropriate for this frontend template. If the application grows significantly, consider micro-frontend architecture to enable independent deployment of view modules. No immediate decomposition needed. |
| **Evidence** | `src/app/app.routes.ts` — lazy-loaded routes for 10 view modules. `src/app/views/` — each view module has its own `routes.ts` and self-contained components. |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Sync request/response is the correct design; async communication is not needed. This is a pure client-side SPA with no inter-service communication — it renders UI components in the browser without calling any backend APIs or downstream services. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No HTTP client imports (no `HttpClient`, no `axios`, no `fetch` calls to backend services) in application source code. No message publishing patterns. All data is hardcoded in component files. |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. No operations exceed 30 seconds — not applicable by design. The application renders UI components and charts with hardcoded data; there are no API calls, batch operations, or data processing that could exceed 30 seconds. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No background job frameworks, no async/polling patterns, no job status APIs, no Lambda invocations in source code. |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy exists. The application does not expose any API endpoints — it is a client-side SPA that serves as a UI template. No OpenAPI specs, no `/v1/` URL patterns, no version headers, no changelog for API contracts. |
| **Gap** | No API versioning — though contextually this is because no APIs are exposed rather than a neglected practice. |
| **Recommendation** | If a backend API is added to serve this dashboard, implement API versioning from the start using URL path versioning (`/v1/`) with Amazon API Gateway (preferred). Define the API contract using OpenAPI specification and maintain a versioning changelog. |
| **Evidence** | No `openapi.yaml`, `swagger.yaml`, `.graphql` files found. No API route definitions in source code. `src/app/app.routes.ts` defines only client-side Angular routes. |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No service discovery mechanism exists. The application is a single SPA with no backend service dependencies. All routes in `src/app/app.routes.ts` are internal Angular client-side routes (e.g., `/dashboard`, `/theme/colors`). No hard-coded service endpoints, no environment variables pointing to backend services, no API Gateway as catalog. |
| **Gap** | No service discovery — though contextually this is because no inter-service communication exists. |
| **Recommendation** | When backend services are added, configure service discovery from the start. For EKS deployments (preferred), use Kubernetes DNS-based service discovery. For cross-cluster communication, evaluate AWS Cloud Map or API Gateway as a service catalog. Avoid hard-coding service endpoints in configuration. |
| **Evidence** | `src/app/app.config.ts` — only router and icon providers configured, no HTTP interceptors or service URLs. No environment files with backend endpoints. |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No unstructured data storage exists. Static assets (images, SVGs, favicon) are stored in `src/assets/` within the repository source tree. No S3 buckets, no EFS, no EBS volumes, no cloud storage of any kind is defined. No document parsing capabilities (Textract, Tika). |
| **Gap** | All unstructured data (images, icons, brand assets) is stored in the local repository filesystem with no cloud storage or parsing pipeline. |
| **Recommendation** | When deploying to AWS, migrate static assets to S3 with CloudFront for global distribution. For the current static asset set (~20 images and SVGs), this is a straightforward S3 sync during deployment. |
| **Evidence** | `src/assets/` — contains images, brand SVGs, and favicons stored in the repository. No `aws_s3_bucket` in IaC. |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database access layer exists. All application data is hardcoded directly in TypeScript component files: mock user data in `src/app/views/dashboard/dashboard.component.ts` (6 user objects), mock messages in `src/app/layout/default-layout/default-header/default-header.component.ts` (5 messages, 5 notifications, 3 status items, 5 tasks), and chart data generated with `Math.random()` in `src/app/views/dashboard/dashboard-charts-data.ts`. No database imports, no ORM, no repository/DAO pattern. |
| **Gap** | No data access layer — data is scattered as hardcoded arrays across multiple component files with no centralized data service. |
| **Recommendation** | When adding a backend, implement a centralized data access layer using Angular services with `HttpClient`. Define TypeScript interfaces for data contracts and use a service per domain entity. For the backend, use DynamoDB (preferred) with a repository pattern. |
| **Evidence** | `src/app/views/dashboard/dashboard.component.ts` — hardcoded `users: IUser[]` array. `src/app/layout/default-layout/default-header/default-header.component.ts` — hardcoded `newMessages`, `newNotifications`, `newStatus`, `newTasks` arrays. `src/app/views/dashboard/dashboard-charts-data.ts` — random chart data generation. |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database engines are detected. No IaC defines any database resources. No database connection strings, no engine version pins, no migration files. The application has no database dependency whatsoever. |
| **Gap** | No database engine version management — though contextually this is because no database exists. |
| **Recommendation** | When adding a database, pin engine versions explicitly in IaC, document a version-update procedure, and ensure no EOL engines are selected. For new deployments, use Aurora PostgreSQL (preferred) or DynamoDB (preferred) with explicit version configuration. |
| **Evidence** | No `aws_rds_instance`, `aws_dynamodb_table`, or database resources in IaC. No database drivers in `package.json`. No SQL migration files. |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs exist. There is no database at all. All business logic and data presentation logic is in the application layer (TypeScript Angular components). |
| **Gap** | None — all logic is in the application layer, which is the correct pattern. |
| **Recommendation** | Maintain this pattern when adding a database. Keep business logic in the application layer and use the database for data persistence only. Avoid stored procedures and proprietary SQL constructs to maintain database engine portability. |
| **Evidence** | No `.sql` files in repository. No `CREATE PROCEDURE`, `CREATE TRIGGER`, `CREATE FUNCTION` patterns. No ORM bypass patterns. |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging is configured. No IaC exists to define logging infrastructure. No `aws_cloudtrail` resources, no log file validation, no immutable log storage. |
| **Gap** | No audit logging — no ability to trace actions or perform forensic analysis. |
| **Recommendation** | When deploying to AWS, enable CloudTrail with log file validation and store logs in an S3 bucket with Object Lock for immutability. Define CloudTrail configuration in AWS CDK as part of the IaC foundation. |
| **Evidence** | No IaC files found. No `aws_cloudtrail` resources. |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no database, S3 bucket, EBS volume, or similar managed storage defined in IaC. SEC-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No `aws_s3_bucket`, `aws_rds_*`, `aws_dynamodb_*`, `aws_ebs_volume` in IaC. `has_at_rest_data_surface=false`. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API authentication exists. The application does not expose any API endpoints. Login and Register pages exist as UI template components (`src/app/views/pages/login/login.component.ts`, `src/app/views/pages/register/register.component.ts`) but contain no actual authentication logic — they are purely presentational HTML forms with CoreUI styling. No auth middleware, no API Gateway authorizers, no Cognito user pools, no OAuth2 flows, no Bearer token validation. |
| **Gap** | No API authentication — login/register forms are non-functional UI templates with no backend integration. |
| **Recommendation** | When adding authentication, integrate with Amazon Cognito (centralized IdP) using the Cognito Hosted UI or Amplify Auth library for Angular. Implement JWT validation on all API endpoints via API Gateway authorizers (preferred). |
| **Evidence** | `src/app/views/pages/login/login.component.ts` — empty component class with no methods, no auth service injection. `src/app/views/pages/register/register.component.ts` — same. No auth interceptors in `src/app/app.config.ts`. |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No identity provider integration. No Cognito, no OIDC/SAML configuration, no SSO setup. The login and register pages are purely decorative UI templates without any authentication backend. No `@aws-amplify/auth`, no `angular-oauth2-oidc`, no OIDC client in dependencies. |
| **Gap** | No centralized identity — the application manages no authentication at all (neither its own nor federated). |
| **Recommendation** | Integrate with Amazon Cognito for user authentication and authorization. Use Cognito User Pools with OIDC for standards-based authentication. Enable SSO for organizational users via Cognito identity federation with external IdPs. |
| **Evidence** | `package.json` — no auth-related dependencies. No `aws_cognito_*` in IaC. `src/app/app.config.ts` — no auth providers configured. |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No plaintext credentials exist in the repository — no `.env` files, no hardcoded passwords, no API keys, no database connection strings. The only secret-like value is `${{ secrets.GITHUB_TOKEN }}` in `.github/workflows/stale.yml`, which is a GitHub-managed secret (not stored in the repository). The application has no backend connections and therefore no production credentials to manage. |
| **Gap** | No secrets management system configured — though no secrets currently exist to manage. No AWS Secrets Manager, no Vault, no rotation configured. |
| **Recommendation** | When adding backend services requiring credentials (database passwords, API keys), use AWS Secrets Manager with automated rotation from day one. Never store credentials in environment variables, `.env` files, or application configuration. |
| **Evidence** | `.gitignore` — no `.env` patterns (`.env` files don't exist). Full repository search found no hardcoded credentials. `.github/workflows/stale.yml` — uses `${{ secrets.GITHUB_TOKEN }}` (GitHub-managed). |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute resources exist to harden or patch. No EC2 instances, no containers, no AMIs. No SSM Patch Manager, no AWS Inspector, no Snyk integration, no hardened base images. |
| **Gap** | No compute hardening or patching strategy. |
| **Recommendation** | When deploying to EKS (preferred), use hardened base images (Bottlerocket for EKS nodes, Nginx Alpine for container images). Enable AWS Inspector for vulnerability scanning. Configure SSM Patch Manager for any EC2 instances. |
| **Evidence** | No Dockerfile, no AMI references, no `aws_ssm_patch_baseline`, no Inspector configuration. |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SAST, DAST, or dependency vulnerability scanning tools are integrated into the CI/CD pipeline. The `.github/workflows/build-check.yml` workflow runs only `npm ci`, Playwright install, and `npm run build`. No Dependabot configuration (`.github/dependabot.yml` does not exist), no `npm audit` step, no Snyk, no SonarQube, no CodeGuru Reviewer. Notably, the CHANGELOG shows manual vulnerability tracking — the maintainers manually override vulnerable dependencies (e.g., `undici` overrides in `package.json`) rather than using automated scanning. |
| **Gap** | No security scanning in CI/CD — vulnerabilities in dependencies reach production undetected. Manual vulnerability tracking in CHANGELOG is reactive, not preventive. |
| **Recommendation** | (1) Add a Dependabot configuration (`.github/dependabot.yml`) for automated dependency update PRs. (2) Add `npm audit --audit-level=high` step to the build-check workflow to fail on known vulnerabilities. (3) Add a SAST tool (e.g., Semgrep or CodeGuru) for code pattern scanning. (4) Consider Snyk for comprehensive dependency and container scanning. |
| **Evidence** | `.github/workflows/build-check.yml` — no security scanning steps. No `.github/dependabot.yml`. No `.snyk` policy file. `CHANGELOG.md` — shows manual vulnerability tracking (undici overrides, tar patches). |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing is instrumented. No OpenTelemetry SDK, no X-Ray instrumentation, no trace ID propagation. No tracing libraries in `package.json` dependencies (no `@opentelemetry/*`, no `aws-xray-sdk`). |
| **Gap** | No distributed tracing — debugging failures across service boundaries would be impossible if backend services were added. |
| **Recommendation** | When adding backend services, instrument with OpenTelemetry SDK from day one. For Angular frontend, add `@opentelemetry/sdk-trace-web` for browser-side tracing that propagates trace context to backend APIs. |
| **Evidence** | `package.json` — no tracing-related dependencies. No tracing configuration in source code. |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no user-facing surface for which SLOs are meaningful. OPS-Q2 does not apply. No API surface and no persistent data store exist — there is nothing to define SLOs against. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `has_api_surface=false`, `has_persistent_data_store=false`. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom metrics are published. No CloudWatch `put_metric_data` calls, no business metric dashboards, no custom metrics infrastructure. The application is a frontend template with no backend to emit business metrics. |
| **Gap** | No business metrics — only infrastructure metrics (if any existed) would be available. |
| **Recommendation** | When deploying with CloudFront, enable CloudFront metrics and create dashboards for cache hit ratio, error rates, and latency. When adding a backend, publish business metrics (page views, user actions, feature usage) using CloudWatch custom metrics or a Real User Monitoring (RUM) solution. |
| **Evidence** | No CloudWatch SDK imports. No metrics publishing code in source files. |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting is configured. No CloudWatch alarms, no anomaly detection, no PagerDuty or OpsGenie integration. No operational alerting of any kind. |
| **Gap** | No alerting — operational issues would go undetected until user reports. |
| **Recommendation** | When deploying, configure CloudWatch alarms for CloudFront 4xx/5xx error rates and origin latency. Add anomaly detection on traffic patterns to detect unusual spikes or drops. Integrate with PagerDuty or OpsGenie for alerting. |
| **Evidence** | No `aws_cloudwatch_metric_alarm`, no alerting configuration in IaC or source code. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy exists. The CI/CD pipeline (`.github/workflows/build-check.yml`) only builds and tests — there is no deployment step. No CodeDeploy, no Helm canary, no Argo Rollouts, no Lambda traffic shifting, no ALB weighted target groups, no feature flags. |
| **Gap** | No deployment strategy — direct-to-production (or no deployment at all) with no staged rollout, no canary, no blue/green. |
| **Recommendation** | For S3 + CloudFront hosting, implement blue/green deployment by maintaining two S3 origins and switching the CloudFront origin after validation. For EKS (preferred), implement rolling deployments with readiness probes and consider Argo Rollouts for canary deployments. |
| **Evidence** | `.github/workflows/build-check.yml` — no deploy steps. No deployment-related IaC or configuration files. |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The CI/CD pipeline runs unit tests via Vitest (`prebuild: ng test --watch=false`). Component spec files exist for most components (`*.spec.ts` — approximately 40+ spec files across views and components). However, these are **unit tests** only — they test individual components in isolation. No integration tests, no E2E tests, no API test suites, no contract tests, no Playwright E2E tests in CI (despite Playwright being installed for Vitest browser testing). |
| **Gap** | No integration tests — only component-level unit tests. No end-to-end testing of user workflows (navigation, form interaction, dashboard rendering). |
| **Recommendation** | Add Playwright E2E tests (already a devDependency: `playwright: ^1.58.2`) to test critical user journeys: dashboard loading, navigation between routes, theme switching, chart rendering. Run E2E tests in the CI pipeline as a separate job after the build step. |
| **Evidence** | `package.json` — `prebuild: ng test --watch=false` (unit tests only). `*.spec.ts` files — component unit tests. `playwright: ^1.58.2` in devDependencies (installed but not used for E2E in CI). |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response automation exists. No runbooks (markdown, YAML, JSON), no Systems Manager Automation documents, no Lambda-based remediation, no Step Functions for incident workflows. No self-healing patterns. |
| **Gap** | No incident response — all response would be ad hoc if issues occurred. |
| **Recommendation** | When deploying to AWS, create runbooks for common incidents (CloudFront cache invalidation, deployment rollback, dependency vulnerability response). Store runbooks as markdown in a `docs/runbooks/` directory. Automate critical runbooks using Systems Manager Automation documents. |
| **Evidence** | No runbook files in repository. No automation documents. No remediation Lambda functions. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership is defined. No per-service dashboards, no alarms with named owners, no SLO definitions with team attribution. No CODEOWNERS file referencing observability assets. No team tags on resources. |
| **Gap** | No observability ownership — monitoring is entirely absent, not just unowned. |
| **Recommendation** | When deploying, establish observability ownership by creating a `CODEOWNERS` file that assigns observability configuration to the team. Create per-service dashboards in CloudWatch with team attribution. |
| **Evidence** | No CODEOWNERS file. No dashboard definitions. No alarm configurations. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resources are defined in IaC, so no tagging exists. No `default_tags` in Terraform provider, no `tags` on resources, no Tag Policies, no tagging standard. |
| **Gap** | No resource tagging — cost allocation, ownership tracking, and environment identification would be impossible. |
| **Recommendation** | When creating IaC, implement a tagging standard from day one. Define `default_tags` in the CDK stack or Terraform provider block with required tags: `Environment`, `Application`, `Team`, `CostCenter`. Enforce tagging via AWS Config rules. |
| **Evidence** | No IaC files with any tag definitions. |

---

## Learning Materials

The following learning resources are mapped to the 2 triggered pathways:

### Move to Containers
- [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM)
- [Move to Containers with Amazon ECS](https://skillbuilder.aws/learning-plan/CDA8Y4JRRR)
- [EKS Workshop](https://www.eksworkshop.com/)

### Move to Modern DevOps
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `package.json` | INF-Q1, INF-Q2, INF-Q4, INF-Q11, APP-Q1, APP-Q5, APP-Q6, DATA-Q3, SEC-Q4, SEC-Q5, SEC-Q7, OPS-Q1, OPS-Q6 | Node.js/Angular dependency manifest — TypeScript 5.9.3, Angular 21.2.5, CoreUI 5.6.21. No database drivers, no auth libraries, no tracing SDKs, no AI frameworks. |
| `angular.json` | INF-Q1, INF-Q10 | Angular CLI configuration — build output to `dist/`, production budgets, SCSS preprocessing. No deployment configuration. |
| `tsconfig.json` | APP-Q1 | TypeScript configuration — `target: ES2022`, `strict: true`, `moduleResolution: bundler`. |
| `.github/workflows/build-check.yml` | INF-Q11, OPS-Q5, OPS-Q6, SEC-Q7 | GitHub Actions CI workflow — build + test on push/PR/schedule across 3 OS platforms. No deploy stage, no security scanning. |
| `.github/workflows/stale.yml` | INF-Q11, SEC-Q5 | Stale issue management workflow. Uses `${{ secrets.GITHUB_TOKEN }}` (GitHub-managed secret). |
| `src/main.ts` | APP-Q1 | Angular application bootstrap entry point — `bootstrapApplication(AppComponent, appConfig)`. |
| `src/app/app.config.ts` | APP-Q6, SEC-Q3, SEC-Q4 | Application configuration — router providers, icon service. No auth providers, no HTTP interceptors, no service URLs. |
| `src/app/app.routes.ts` | APP-Q2, APP-Q5, APP-Q6 | Route definitions — 10 lazy-loaded view modules, login/register/error pages. All client-side Angular routes. |
| `src/app/app.component.ts` | APP-Q1, APP-Q2 | Root component — router outlet, color mode service, icon set initialization. Modern Angular patterns (inject, signals). |
| `src/app/app.component.spec.ts` | OPS-Q6 | Unit test for AppComponent — basic creation and title checks using Vitest. |
| `src/app/views/dashboard/dashboard.component.ts` | DATA-Q2, APP-Q2 | Dashboard view — hardcoded `IUser[]` array with 6 mock users, chart form controls. |
| `src/app/views/dashboard/dashboard-charts-data.ts` | DATA-Q2 | Chart data service — generates random chart data with `Math.random()`. No backend data source. |
| `src/app/layout/default-layout/default-layout.component.ts` | APP-Q2 | Layout component — sidebar navigation, header, footer. Uses CoreUI sidebar components. |
| `src/app/layout/default-layout/default-header/default-header.component.ts` | DATA-Q2 | Header component — hardcoded mock messages (5), notifications (5), status items (3), tasks (5). |
| `src/app/layout/default-layout/_nav.ts` | APP-Q2 | Sidebar navigation configuration — hierarchical nav items for all view modules. |
| `src/app/views/pages/login/login.component.ts` | SEC-Q3, SEC-Q4 | Login page — empty component class with no authentication logic. Purely presentational UI template. |
| `src/app/views/pages/register/register.component.ts` | SEC-Q3, SEC-Q4 | Register page — empty component class with no registration logic. Purely presentational UI template. |
| `src/components/public-api.ts` | APP-Q2 | Component library public API — exports docs-related components (DocsCallout, DocsExample, DocsComponents, DocsIcons, DocsLink). |
| `README.md` | Quick Agent Wins | Comprehensive documentation — setup instructions, project structure, versioning policy, community links. |
| `CHANGELOG.md` | Quick Agent Wins, SEC-Q7 | Detailed version history with dependency updates and manual vulnerability tracking (undici, tar, hono, express-rate-limit overrides). |
| `.editorconfig` | INF-Q10 | Editor configuration — consistent formatting (UTF-8, 2-space indent). Not IaC. |
| `.gitignore` | SEC-Q5 | Git ignore rules — no `.env` patterns (because `.env` files don't exist). Ignores build output, node_modules, IDE files. |
