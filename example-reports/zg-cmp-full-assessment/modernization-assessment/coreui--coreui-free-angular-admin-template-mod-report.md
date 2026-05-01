# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | coreui-free-angular-admin-template |
| **Date** | 2026-04-29 |
| **Repo Type** | application |
| **Service Archetype** | stateless-utility (auto-detected) |
| **Priority** | P2 |
| **Tags** | html, frontend, angular |
| **Context** | CoreUI Angular admin dashboard template. |
| **Overall Score** | 1.63 / 4.0 |

**Archetype Justification**: No database connections, no API calls to backend services, no write operations detected. This is a client-side Angular SPA template with no backend runtime. Classified as stateless-utility as the closest match; archetype calibration has limited applicability for pure frontend applications.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.64 / 4.0 | 🟠 Needs Work |
| Application Architecture (APP) | 2.67 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 1.75 / 4.0 | 🟠 Needs Work |
| Security Baseline (SEC) | 1.00 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.11 / 4.0 | ❌ Not Present |
| **Overall** | **1.63 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | SEC-Q7: Application Security Pipeline | 1 | No SAST, DAST, or dependency vulnerability scanning in CI/CD pipeline | Vulnerabilities in dependencies (e.g., undici CVEs noted in CHANGELOG) reach production undetected; blocks secure modernization |
| 2 | INF-Q1: Managed Compute | 1 | No compute infrastructure defined — no ECS, EKS, Lambda, or even EC2 | Application cannot be deployed to AWS; foundational blocker for all modernization pathways |
| 3 | INF-Q10: Infrastructure as Code Coverage | 1 | 0% IaC coverage — all infrastructure is undefined or manual | No reproducible infrastructure; prevents automated deployment, disaster recovery, and environment consistency |
| 4 | OPS-Q5: Deployment Strategy | 1 | No deployment automation — CI/CD workflow only builds, does not deploy | No path to production; manual deployments are error-prone and block rapid iteration |
| 5 | INF-Q5: Network Security | 1 | No VPC, subnets, security groups, or network segmentation defined | When deployed, application has no network isolation; security and blast-radius risk |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 2). The `.github/workflows/build-check.yml` workflow runs `npm ci`, installs Playwright, and executes `npm run build` across 3 OS platforms on push/PR/schedule.
- **What it enables:** A DevOps agent that triggers builds, checks build status across platforms, and monitors scheduled build results. As deployment stages are added, the agent can orchestrate deployments and manage releases.
- **Additional steps:** Extend the existing build-check workflow with deployment stages (e.g., deploy to S3 + CloudFront, or deploy to EKS). Once deployment is automated, the agent can manage the full CI/CD lifecycle.
- **Effort:** Medium — the build pipeline exists but deployment must be added before the agent provides full value.

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository. `README.md` contains comprehensive content (Quick Start, Installation, Basic Usage, What's Included, directory structure). `CHANGELOG.md` contains 858 lines of version history and dependency update details. `.github/CONTRIBUTING.md`, `.github/SUPPORT.md`, and `.github/COMMIT_CONVENTION.md` provide contributor guidance.
- **What it enables:** A RAG-based knowledge agent that indexes existing documentation and answers developer questions about the CoreUI template — setup instructions, version compatibility, component usage, and upgrade history.
- **Additional steps:** Index `README.md`, `CHANGELOG.md`, and `.github/` documentation files. Consider generating API documentation from Angular component source files for deeper component-level knowledge.
- **Effort:** Low — documentation corpus exists and can be indexed directly using Amazon Bedrock with a knowledge base backed by the existing markdown files.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2 = 2 (monolithic SPA), INF-Q1 = 1 (no compute infrastructure) |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1 = 1 (no compute), no container definitions found |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 — no stored procedures or proprietary SQL; no commercial DB engines detected |
| 4 | Move to Managed Databases | Triggered | Medium | Medium | INF-Q2 = 1 (no database infrastructure), DATA-Q3 = 1 (no engine versions defined). Note: no databases exist yet — pathway applies when backend is added |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 4 (archetype-calibrated) — no data processing workloads exist |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (0% IaC), INF-Q11 = 2 (build-only CI, no deploy), OPS-Q5 = 1 (no deployment strategy), OPS-Q6 = 2 (unit tests only) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context |

---

### Pathway: Move to Cloud Native

**Status:** Triggered  
**Priority:** High  
**Estimated Effort:** High

**Current Architecture State:**  
The application is a monolithic Angular 21 SPA (APP-Q2 = 2) built as a single deployable unit. It has modular internal structure with 10 lazy-loaded route modules (dashboard, theme, base, buttons, forms, icons, notifications, widgets, charts, pages), standalone components, and clear separation between layout (`src/app/layout/`) and feature views (`src/app/views/`). However, the entire application is bundled and deployed as one artifact.

**Compute Model Gaps (INF-Q1 = 1):**  
No compute infrastructure is defined. There is no Terraform, CloudFormation, CDK, or any IaC defining how or where this application runs. The application has no deployment target.

**Communication Pattern Context:**  
APP-Q3 and APP-Q4 scored 4 due to archetype calibration (stateless-utility) — synchronous client-side rendering is the correct design for a frontend SPA. These are not genuine gaps for this application type.

**Recommended Approach:**  
For this frontend SPA, "cloud native" means deploying via a modern, managed hosting strategy rather than backend microservices decomposition:

1. **Immediate:** Containerize the Angular build output and deploy to **Amazon EKS** (preferred per technology preferences) with an NGINX or Node.js server, or deploy the static build artifacts to **Amazon S3 + CloudFront** for a serverless static hosting model.
2. **API Layer:** When backend functionality is needed, build APIs as independent services behind **Amazon API Gateway** (preferred), using **Amazon EventBridge** (preferred) for event-driven patterns.
3. **Micro-Frontend (Future):** If independent deployment of feature modules is needed, adopt Module Federation to extract lazy-loaded routes into independently deployable micro-frontends.

**Representative AWS Services:** Amazon EKS, Amazon API Gateway, Amazon EventBridge, Amazon CloudFront, Amazon S3, AWS CDK  
**Recommended Patterns:** Strangler Fig (for gradual backend extraction), Anti-corruption Layer (between frontend and new backend services)  
**AWS Prescriptive Guidance:** [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Containers

**Status:** Triggered  
**Priority:** Medium  
**Estimated Effort:** Medium

**Current Compute Model (INF-Q1 = 1):**  
No compute infrastructure exists. The Angular SPA has no Dockerfile, no docker-compose.yml, no Kubernetes manifests. The application is built via `ng build` producing static artifacts in `dist/coreui-free-angular-admin-template/`.

**Contextual Guard Passed:** Compute is not already on Lambda/Fargate/ECS — there is no compute infrastructure at all.

**Container Readiness Indicators:**
- ✅ Build output is well-defined (`dist/coreui-free-angular-admin-template/` per angular.json)
- ✅ No server-side dependencies requiring special runtime configuration
- ✅ Production build with output hashing configured (`"outputHashing": "all"`)
- ✅ No environment-specific secrets in source code
- ⚠️ No Dockerfile exists — needs creation
- ⚠️ No health check endpoint (pure SPA)

**Recommended Container Orchestration Platform:**  
**Amazon EKS** (preferred per technology preferences). Avoid self-managed Kubernetes per stated preferences.

**Migration Approach — Lift-and-Containerize:**
1. Create a multi-stage Dockerfile: Stage 1 builds the Angular app (`npm ci && npm run build`), Stage 2 copies build artifacts into an NGINX image.
2. Push the container image to **Amazon ECR**.
3. Deploy to **Amazon EKS** with Helm charts defining the deployment, service, and ingress.
4. Configure an **Application Load Balancer** ingress for routing.

**Representative AWS Services:** Amazon EKS, Amazon ECR, AWS App Runner (alternative lightweight option)  
**AWS Container Migration Guidance:** [Containers on AWS](https://aws.amazon.com/containers/)

---

### Pathway: Move to Managed Databases

**Status:** Triggered  
**Priority:** Medium  
**Estimated Effort:** Medium

**Current Database Topology (INF-Q2 = 1):**  
No database infrastructure exists. This is a frontend template with hardcoded mock data (user arrays in `dashboard.component.ts`, message arrays in `default-header.component.ts`). No database connections, no ORM, no migration files.

**Practical Relevance:**  
This pathway is technically triggered because INF-Q2 = 1, but the recommendation is forward-looking — it applies when backend services are added to this frontend template. The mock data currently hardcoded in components will need to be served from a persistent data store.

**Recommended Managed Database Targets (per preferences):**
- **Amazon Aurora** (preferred) — for relational data (user profiles, application settings, transactional data)
- **Amazon DynamoDB** (preferred) — for high-throughput, low-latency access patterns (session data, notification feeds, real-time dashboard metrics)
- Avoid Oracle per stated preferences

**When to Act:** When backend services are created to replace hardcoded mock data, start with managed database services from day one. Do not introduce self-managed databases.

**Representative AWS Services:** Amazon Aurora, Amazon DynamoDB, Amazon ElastiCache  
**Migration Tools:** AWS DMS, AWS SCT (when migrating from existing databases in the future)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered  
**Priority:** High  
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 1):**  
0% IaC coverage. No Terraform, CloudFormation, CDK, or Helm files exist. All infrastructure (if any) is undefined.

**Current CI/CD State (INF-Q11 = 2):**  
A GitHub Actions workflow (`.github/workflows/build-check.yml`) exists with:
- Multi-platform build verification (Ubuntu, Windows, macOS)
- Node.js 24 setup, `npm ci`, Playwright install, `npm run build`
- Runs on push, PR to main/v5.*, daily schedule, and manual trigger
- `prebuild` script executes `ng test --watch=false` (unit tests run before build)

**Gaps:**
- ❌ No deployment stage — build artifacts are produced but never deployed
- ❌ No IaC — infrastructure must be defined before it can be deployed
- ❌ No deployment strategy (OPS-Q5 = 1) — no blue/green, canary, or any release strategy
- ⚠️ Unit tests exist but no integration tests against deployed services (OPS-Q6 = 2)
- ❌ No security scanning in pipeline (SEC-Q7 = 1)

**Recommended DevOps Toolchain (per preferences):**

1. **IaC:** Define infrastructure using **AWS CDK** (TypeScript, matching the application language) or Terraform. Define EKS cluster, networking, and supporting services.
2. **CI/CD Pipeline Enhancement:**
   - Add `npm audit` or Snyk scanning step to the existing GitHub Actions workflow
   - Add Docker build and push to ECR
   - Add deployment step using `kubectl` or Helm to deploy to EKS
   - Add smoke test after deployment
3. **Deployment Strategy:** Implement rolling deployments with health checks initially, then graduate to canary deployments using Argo Rollouts or AWS CodeDeploy.
4. **Dependency Scanning:** Add `.github/dependabot.yml` for automated dependency updates (the `undici` override in package.json shows manual vulnerability management is already happening).

**Representative AWS Services:** AWS CDK, Amazon ECR, Amazon EKS, AWS CodeBuild, AWS CodePipeline, AWS CodeDeploy  
**AWS DevOps Prescriptive Guidance:** [DevOps on AWS](https://aws.amazon.com/devops/)

---

## Decomposition Strategy

> **Conditional section — included because APP-Q2 = 2 (< 3)**

### Context

The CoreUI Angular admin template is a single deployable SPA with well-organized modular structure. It uses Angular's lazy-loading to split the application into feature modules loaded on demand. This is a **frontend** monolith — traditional backend decomposition patterns (Saga, Event Sourcing for distributed transactions) have limited direct applicability.

### Recommended Approach: Conditional / Adaptive

| Approach | Description | Applicability | Level of Effort | Recommendation |
|----------|-------------|---------------|-----------------|----------------|
| **Conditional / Adaptive** | Containerize the SPA as-is first, then selectively extract micro-frontends if business requirements demand independent deployment of features. Not all modules need to become independently deployable. | ✅ Best fit — the SPA has modular structure with lazy-loaded routes. Containerization is straightforward. Micro-frontend extraction is optional and demand-driven. | **Low to Medium** — containerization in 1–2 weeks, selective micro-frontend extraction over 1–3 months if needed. | ✅ **Recommended.** Start with container deployment; graduate to micro-frontends only if independent feature deployment is needed. |
| **Strangler Fig (Parallel Track)** | Incrementally extract route modules into independently deployable micro-frontends using Module Federation, while keeping the main app running. | Applicable if multiple teams need to deploy features independently. | **Medium** — 3–6 months for full Module Federation setup. | ✅ Recommended if team scale demands independent deployment. |
| **Big-Bang Rewrite** | Rewrite as separate micro-frontend applications from scratch. | Not applicable — the existing code is well-structured with modern Angular 21 and standalone components. | **Very High** — unnecessary effort. | ⚠️ **Not recommended.** The current codebase is modern, well-organized, and does not warrant a rewrite. |

### Pattern Recommendations for Frontend Decomposition

| Pattern | Purpose | Applicability |
|---------|---------|---------------|
| **Module Federation** | Split Angular lazy-loaded routes into independently built and deployed remote modules. Each feature module (dashboard, forms, charts, etc.) can be deployed independently. | When multiple teams own different feature areas and need independent release cycles. |
| **API Gateway (for Backend)** | When backend services are added, use Amazon API Gateway as the single entry point. Frontend communicates with API Gateway, which routes to backend microservices. | When backend services are introduced — establishes clean separation between frontend and backend. |
| **Anti-corruption Layer** | When integrating the frontend with new backend APIs, use a lightweight BFF (Backend-for-Frontend) layer to translate between the frontend's data model and backend API contracts. | When multiple backend services have different API styles and the frontend needs a unified interface. |

### Effort Calibration

| Factor | Assessment | Signal |
|--------|-----------|--------|
| Module boundaries | Clear — 10 lazy-loaded route modules with standalone components | Low effort |
| Data coupling | None — no shared database, no backend state | Low effort |
| Stored procedures | None | Low effort |
| Communication patterns | Client-side only — no inter-service communication | Low effort |
| CI/CD maturity | Build pipeline exists but no deployment | Medium effort (deployment must be added first) |
| Test coverage | 48 spec files covering most components | Low risk during extraction |

**Overall Effort Estimate:** Low for containerization and deployment; Medium for micro-frontend extraction if pursued.

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute infrastructure is defined in the repository. There are no Terraform files, CloudFormation templates, CDK stacks, or any IaC defining ECS, EKS, Lambda, Fargate, or EC2 resources. The application is a client-side Angular SPA with no deployment target specified. |
| **Gap** | All compute is undefined — the application has no path to a production deployment on AWS. |
| **Recommendation** | Define compute infrastructure using AWS CDK (TypeScript). Deploy the containerized Angular application to **Amazon EKS** (preferred). Alternatively, for a simpler static hosting model, deploy build artifacts to Amazon S3 with CloudFront distribution. |
| **Evidence** | No `.tf`, `.cfn.yaml`, `cdk.json`, or Helm chart files found in repository root or any subdirectory. |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database infrastructure exists. No `aws_rds_*`, `aws_dynamodb_*`, or any database resource definitions in IaC. No database connection strings, ORM configurations, or database drivers in `package.json`. The application uses hardcoded mock data. |
| **Gap** | No database infrastructure — data is hardcoded in component files (`dashboard.component.ts`, `default-header.component.ts`). When backend functionality is added, databases will need to be provisioned. |
| **Recommendation** | When adding backend data persistence, adopt managed database services from day one: **Amazon Aurora** (preferred) for relational data, **Amazon DynamoDB** (preferred) for high-throughput access patterns. Avoid self-managed databases and Oracle (per stated preferences). |
| **Evidence** | `package.json` — no database driver dependencies. `src/app/views/dashboard/dashboard.component.ts` — hardcoded `users` array. No `.sql` files, no ORM configuration files. |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No multi-step workflows exist in this application. It is a client-side Angular SPA that renders UI components and chart data. All operations are synchronous client-side rendering. This is the correct outcome for a stateless-utility archetype — there are no workflows to orchestrate. |
| **Gap** | N/A — dedicated workflow orchestration is not applicable for this archetype and does not represent a gap. |
| **Recommendation** | No action needed. Workflow orchestration services (e.g., AWS Step Functions) are not applicable for a pure frontend SPA template. If backend orchestration needs arise (e.g., multi-step form submission workflows), adopt Step Functions at that time. |
| **Evidence** | No `aws_sfn_*` in IaC. No Temporal SDK imports. No multi-step business operations in source code. All components perform client-side rendering only. |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Synchronous client-side rendering is the correct design for this Angular SPA template. No backend messaging or streaming is needed. The application has no inter-service communication, no event publishing, and no message consumption. This is appropriate for a stateless-utility frontend. |
| **Gap** | N/A — adopting async messaging is NOT recommended for this application type. It would add operational complexity without architectural benefit. |
| **Recommendation** | No action needed. When backend services are added, adopt **Amazon EventBridge** (preferred) for event-driven communication between services. Avoid self-managed Kafka per stated preferences. |
| **Evidence** | No SQS, SNS, EventBridge, MSK, or Kinesis references. No message queue client libraries in `package.json`. No event handler patterns in source code. |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No network security configuration exists. No VPC, subnets, security groups, NACLs, or network segmentation defined in IaC. No infrastructure files of any kind exist in the repository. |
| **Gap** | When deployed, the application will have no network isolation. Network security must be designed from scratch. |
| **Recommendation** | Define a VPC with private subnets for backend services, public subnets for load balancers, and least-privilege security groups. Use VPC endpoints for AWS service access. For EKS (preferred), configure network policies for pod-level network segmentation. |
| **Evidence** | No `aws_vpc`, `aws_subnet`, `aws_security_group` resources. No IaC files found in repository. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or any managed entry point is defined. The application has no deployment infrastructure. |
| **Gap** | No managed entry point for traffic routing, throttling, or authentication. |
| **Recommendation** | Deploy **Amazon API Gateway** (preferred) as the entry point for backend APIs when added. Use **Amazon CloudFront** as the CDN and entry point for the frontend static assets, providing caching, HTTPS termination, and DDoS protection via AWS Shield. |
| **Evidence** | No `aws_api_gateway_*`, `aws_apigatewayv2_*`, `aws_lb_*`, `aws_cloudfront_*` resources. No IaC files found. |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration. No compute resources are defined to scale. |
| **Gap** | No auto-scaling — all capacity will need to be configured when infrastructure is created. |
| **Recommendation** | When deploying to EKS (preferred), configure Horizontal Pod Autoscaler (HPA) for the frontend containers. For S3 + CloudFront hosting, auto-scaling is inherent. For backend services, configure auto-scaling on compute, DynamoDB capacity, and Aurora replicas. |
| **Evidence** | No `aws_autoscaling_*`, `aws_appautoscaling_*` resources. No IaC files found. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration. No data stores are defined that require backup. |
| **Gap** | No backup infrastructure. When databases are added, backup and recovery must be configured from day one. |
| **Recommendation** | When adding databases, enable automated backups with PITR: Aurora automated backups with cross-region replication for critical data, DynamoDB point-in-time recovery, S3 versioning for object storage. Define an AWS Backup plan covering all data stores. |
| **Evidence** | No `backup_retention_period`, `point_in_time_recovery`, `aws_backup_plan` resources. No data stores defined. |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No high availability configuration. No multi-AZ deployment, no cross-AZ load balancing. No infrastructure defined. |
| **Gap** | No HA configuration — single points of failure will exist if infrastructure is created without multi-AZ design. |
| **Recommendation** | Design infrastructure for multi-AZ from day one. EKS (preferred) nodes should span 2+ AZs. Aurora (preferred) should be deployed as Multi-AZ. ALB should have cross-zone load balancing enabled. |
| **Evidence** | No `multi_az`, `availability_zones` configurations. No IaC files found. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | 0% IaC coverage. No Terraform files, CDK stacks, CloudFormation templates, or Helm charts exist in the repository. All infrastructure is either undefined or would need to be created manually. |
| **Gap** | No IaC — infrastructure changes would be manual, error-prone, and non-reproducible. This is a foundational gap blocking all other modernization efforts. |
| **Recommendation** | Adopt **AWS CDK** (TypeScript — matching the application language) to define all infrastructure as code. Start with: VPC and networking, EKS cluster (preferred), ECR repository, deployment configuration. Alternatively, Terraform is a viable option for teams with existing Terraform expertise. |
| **Evidence** | No `.tf`, `.tfvars`, `cdk.json`, `*.cfn.yaml`, `*.cfn.json`, `Chart.yaml`, `kustomization.yaml` files found anywhere in the repository. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | A GitHub Actions workflow exists (`.github/workflows/build-check.yml`) that provides build verification: `npm ci`, Playwright browser install, and `npm run build` (which runs `ng test --watch=false` via the `prebuild` script before building). The workflow runs on push, PRs to main/v5.*, daily schedule (4:15 AM UTC), and manual trigger. It tests across 3 OS platforms (Ubuntu, Windows, macOS) with Node.js 24. A separate stale bot (`.github/workflows/stale.yml`) manages issue/PR lifecycle. |
| **Gap** | Build is automated but deployment is entirely missing. No deployment stage, no artifact publishing to a registry, no infrastructure deployment. The pipeline stops at build verification. |
| **Recommendation** | Extend the existing GitHub Actions workflow or create a new deployment workflow: add Docker build and push to ECR, add deployment to EKS via Helm or `kubectl`, add smoke tests post-deployment, add automated rollback on failure. Consider AWS CodePipeline for more complex deployment orchestration. |
| **Evidence** | `.github/workflows/build-check.yml` — build verification workflow. `.github/workflows/stale.yml` — stale issue management. `package.json` — `prebuild` script runs `ng test --watch=false`. |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | TypeScript 5.9 is the primary language, used with Angular 21.2.x framework. TypeScript has first-class AWS SDK coverage (`@aws-sdk/*` packages), broad cloud-native tooling (AWS CDK is TypeScript-native), and a mature ecosystem for serverless, container, and full-stack development. |
| **Gap** | No gap — TypeScript is a top-tier language for AWS cloud-native development. |
| **Recommendation** | No action needed. TypeScript is an excellent choice. When adding backend services, leverage the same TypeScript ecosystem for consistency (e.g., AWS CDK for IaC, Node.js/Express or NestJS for backend APIs). |
| **Evidence** | `package.json` — `"typescript": "~5.9.3"`. `tsconfig.json` — strict mode enabled, ES2022 target. 78 non-spec TypeScript source files. |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Single deployable unit (monolithic SPA) with well-organized modular internal structure. The application uses Angular's lazy-loading to split into 10 feature modules: dashboard, theme, base, buttons, forms, icons, notifications, widgets, charts, and pages. Each module has its own `routes.ts` file. Standalone components are used throughout. Clear separation exists between layout (`src/app/layout/`) and feature views (`src/app/views/`). However, the entire application is built and deployed as a single bundle. |
| **Gap** | Monolith with identifiable modules but deployed as a single unit. All features share the same build, deployment, and release cycle. No independent deployability for individual modules. |
| **Recommendation** | See **Decomposition Strategy** section. Short-term: containerize the SPA as-is. Medium-term: if independent feature deployment is needed, adopt Angular Module Federation to extract lazy-loaded routes into independently deployable micro-frontends. |
| **Evidence** | `src/app/app.routes.ts` — 10 lazy-loaded child route modules. `src/app/views/` — 10 feature directories. `angular.json` — single project definition with one build target. |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Synchronous client-side rendering is the correct design for this Angular SPA. No inter-service communication exists — no HttpClient calls, no gRPC stubs, no message publishing patterns, no fetch() calls. All data is rendered client-side from hardcoded values. This is appropriate for a stateless-utility archetype. |
| **Gap** | N/A — synchronous is the correct design for this application type. |
| **Recommendation** | No action needed. Synchronous client-side rendering is appropriate. When backend services are added, evaluate communication patterns at that time based on the backend service archetypes. Converting the frontend to async communication is NOT recommended. |
| **Evidence** | `grep -rn "HttpClient\|fetch(" --include="*.ts"` — no results. No HTTP client libraries in `package.json`. `src/app/app.config.ts` — no `provideHttpClient()` in providers. |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No operations exceed 30 seconds. All operations are client-side UI rendering: component instantiation, chart data generation (`DashboardChartsData` generates random values synchronously), navigation, and theme switching. This is not applicable by design for a UI template. |
| **Gap** | N/A — async job infrastructure is not applicable for the current application surface. |
| **Recommendation** | No action needed. When backend services are added that involve long-running operations (e.g., report generation, data exports), implement async job processing with status polling at that time. |
| **Evidence** | `src/app/views/dashboard/dashboard-charts-data.ts` — chart data generated synchronously with `Math.random()`. No background job frameworks, no async invocation patterns. |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy. The application is a frontend SPA that does not expose any APIs. No `/v1/` URL patterns, no version headers, no API endpoints of any kind. The router defines client-side routes only (`/dashboard`, `/theme`, `/base`, etc.). |
| **Gap** | No API versioning — when backend APIs are created, versioning must be designed from the start. |
| **Recommendation** | When creating backend APIs behind Amazon API Gateway (preferred), adopt URL-path versioning (`/v1/users`, `/v2/users`) as the standard. Define versioning strategy before the first API endpoint is published. Use API Gateway stage variables for version management. |
| **Evidence** | `src/app/app.routes.ts` — client-side routes only, no API endpoints. No OpenAPI spec files. No `/v1/`, `/v2/` patterns in source code. |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No service discovery mechanism. The application has no backend service communication — no HttpClient usage, no service addresses in environment variables, no service registry configuration. The frontend has no backends to discover. |
| **Gap** | No service discovery — when backend services are introduced, a discovery mechanism must be established. |
| **Recommendation** | When deploying backend services to EKS (preferred), use Kubernetes native service discovery (DNS-based service resolution within the cluster). For cross-cluster or cross-account communication, adopt AWS Cloud Map or service mesh (e.g., AWS App Mesh or Istio). Frontend should resolve backend endpoints via environment-injected configuration or API Gateway base URL. |
| **Evidence** | No `HttpClient` imports. No environment files with service URLs. No service registry or mesh configuration. |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No unstructured data storage. The application bundles static assets (images, icons) at build time in `src/assets/`. These are compiled into the distribution bundle, not stored in managed object storage. No S3 references, no file upload functionality, no document management. |
| **Gap** | Static assets are bundled in the application rather than served from managed object storage. No document storage capability exists. |
| **Recommendation** | Move static assets (images, avatars) to **Amazon S3** served via **CloudFront** CDN. This reduces bundle size, enables independent asset updates, and provides a foundation for user-uploaded content when the application evolves beyond a template. |
| **Evidence** | `src/assets/` — contains static images. `angular.json` — assets configured as build-time inclusions. No S3, Textract, or document processing references. |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No data access layer. All data is hardcoded directly in component files. `DashboardComponent` contains a hardcoded `users` array with 6 mock users. `DashboardChartsData` generates random chart data with `Math.random()`. `DefaultHeaderComponent` contains hardcoded `newMessages`, `newNotifications`, `newStatus`, and `newTasks` arrays. No HTTP calls to backend APIs, no repository pattern, no data services. |
| **Gap** | Data is scattered as hardcoded arrays in individual components with no centralized data access pattern. When real backend APIs are introduced, data access will need to be structured. |
| **Recommendation** | When adding backend data, implement Angular services as a unified data access layer: one service per domain entity (UserService, NotificationService, etc.) with HttpClient calls routed through a centralized API configuration. This creates the abstraction needed for eventual backend integration. |
| **Evidence** | `src/app/views/dashboard/dashboard.component.ts` — hardcoded `users: IUser[]` array. `src/app/views/dashboard/dashboard-charts-data.ts` — `random()` method generates mock chart data. `src/app/layout/default-layout/default-header/default-header.component.ts` — hardcoded `newMessages`, `newNotifications`, `newStatus`, `newTasks` arrays. |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database engine versions defined. No databases are in use. No IaC defining database resources, no connection strings, no database drivers in `package.json`. |
| **Gap** | No database versioning — when databases are added, engine versions must be explicitly pinned in IaC from day one. |
| **Recommendation** | When adding databases, explicitly pin engine versions in IaC. For Aurora (preferred), specify `engine_version`. For DynamoDB (preferred), version management is handled by AWS. Establish a documented version-update procedure. |
| **Evidence** | No `aws_rds_instance`, `aws_docdb_cluster`, `aws_elasticache_*` resources. No database connection strings. No database drivers in `package.json`. |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL. All business logic (chart rendering, UI state management, theme handling) is in the TypeScript application layer. No database coupling exists. |
| **Gap** | No gap — all logic is in the application layer, which is the ideal state. |
| **Recommendation** | No action needed. When adding databases, maintain this pattern — keep business logic in the application layer and avoid stored procedures to preserve database portability. |
| **Evidence** | No `.sql` files. No `CREATE PROCEDURE`, `CREATE TRIGGER`, `CREATE FUNCTION` patterns. No ORM configuration. No database queries in source code. |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or audit logging configuration. No IaC exists to define logging infrastructure. |
| **Gap** | No audit logging — all API and infrastructure actions would be untraced. |
| **Recommendation** | When creating AWS infrastructure, enable CloudTrail with log file validation and store logs in an S3 bucket with Object Lock for immutability. Define CloudWatch log groups for application logs with appropriate retention periods. |
| **Evidence** | No `aws_cloudtrail` resources. No IaC files of any kind. |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest configuration. No data stores are defined to encrypt. |
| **Gap** | No encryption — when data stores are created, encryption must be configured from day one. |
| **Recommendation** | When creating data stores, enable encryption at rest with customer-managed KMS keys: S3 bucket encryption (SSE-KMS), Aurora encryption, DynamoDB encryption with CMK. Define a centralized key management strategy. |
| **Evidence** | No `kms_key_id`, `aws_kms_key` resources. No data stores defined in IaC. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API authentication implemented. The login page (`src/app/views/pages/login/`) is a static UI template — the `LoginComponent` class is empty with no form submission handler, no auth service call, no token handling. The register page is similarly empty. No auth guards on routes, no HttpInterceptor for token injection, no OAuth2/JWT handling. |
| **Gap** | Login/register pages are non-functional UI mockups. No actual authentication flow exists. |
| **Recommendation** | Integrate with **Amazon Cognito** for centralized authentication. Implement Angular auth guards using Cognito tokens. Use an HttpInterceptor to attach JWT tokens to API requests. Configure API Gateway (preferred) authorizers backed by Cognito user pools. |
| **Evidence** | `src/app/views/pages/login/login.component.ts` — empty class body. `src/app/views/pages/register/register.component.ts` — empty class body. No `@angular/fire`, `amazon-cognito-identity-js`, `oidc-client`, or auth libraries in `package.json`. No route guards in `src/app/app.routes.ts`. |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No identity provider integration. No Cognito, Okta, OIDC, or SAML configuration. The login and register pages are UI templates with no backend authentication logic. |
| **Gap** | No identity provider — the application has no authentication system, centralized or otherwise. |
| **Recommendation** | Adopt **Amazon Cognito** as the centralized identity provider. Configure Cognito User Pool with appropriate password policies, MFA, and account recovery. Enable SSO federation if the organization uses an external IdP (Okta, Azure AD, etc.). |
| **Evidence** | No `aws_cognito_*` resources. No OIDC/SAML configuration. No auth library dependencies in `package.json`. |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No secrets management infrastructure. No AWS Secrets Manager or Vault references. No `.env` files committed to the repository. No hardcoded secrets detected in source code (the application has no backend credentials to manage). The `undici` override in `package.json` addresses known CVEs but is not a secrets management practice. |
| **Gap** | No secrets management — when backend services with credentials are introduced, a secrets management solution must be in place. |
| **Recommendation** | When adding backend services, use **AWS Secrets Manager** for all credentials (database passwords, API keys, third-party tokens). Configure automatic rotation. Reference secrets in IaC without hardcoding values. For the frontend, use environment-specific build configurations (not committed to git) for API base URLs. |
| **Evidence** | No `aws_secretsmanager_*` resources. No Vault client imports. No `.env` files. No `password=`, `secret=`, `api_key=` patterns in source code. |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute hardening or patching configuration. No compute resources are defined. No SSM Patch Manager, no Inspector, no hardened AMI references. |
| **Gap** | No compute security — when infrastructure is created, hardening and patching must be configured. |
| **Recommendation** | When deploying to EKS (preferred), use Bottlerocket OS for worker nodes (hardened, minimal attack surface, automated updates). Enable Amazon Inspector for container vulnerability scanning. Configure ECR image scanning on push. |
| **Evidence** | No `aws_ssm_patch_baseline`, `aws_inspector_*` resources. No hardened AMI references. No IaC files. |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SAST, DAST, or dependency vulnerability scanning in the CI/CD pipeline. The `build-check.yml` workflow runs `npm ci` and `npm run build` only — no `npm audit`, no Snyk, no SonarQube, no CodeGuru. No `.github/dependabot.yml` configuration file exists. The CHANGELOG shows manual vulnerability management (e.g., `undici` override to mitigate 6 CVEs), indicating awareness of dependency vulnerabilities but no automated detection. |
| **Gap** | No automated security scanning — vulnerabilities are managed manually, as evidenced by the `undici` override. Dependencies may have undetected vulnerabilities. |
| **Recommendation** | 1) Add `npm audit --audit-level=high` step to the build-check workflow. 2) Create `.github/dependabot.yml` for automated dependency update PRs. 3) Add a SAST tool (Semgrep or SonarQube) to the pipeline. 4) When Dockerfiles are added, enable ECR image scanning. |
| **Evidence** | `.github/workflows/build-check.yml` — no security scanning steps. No `.github/dependabot.yml`. No `.snyk` file. `package.json` — manual `"undici": "^7.24.0"` override for CVE mitigation. |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumented. No OpenTelemetry SDK, X-Ray instrumentation, or any tracing library in `package.json`. No trace ID propagation headers. |
| **Gap** | No tracing — when backend services are added, debugging cross-service failures will be impossible without tracing. |
| **Recommendation** | When adding backend services, instrument with **AWS X-Ray** or **OpenTelemetry**. For the Angular frontend, add OpenTelemetry browser instrumentation to capture frontend performance traces that propagate to backend services via `traceparent` headers. |
| **Evidence** | No `@opentelemetry/*`, `aws-xray-sdk`, or tracing libraries in `package.json`. No trace header propagation in source code. |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLOs defined. No SLO configuration files, no error budget tracking, no availability or latency alarms. |
| **Gap** | No SLOs — cannot measure whether the application meets user expectations. |
| **Recommendation** | When deploying to production, define SLOs for frontend performance: page load time p95 < 3s, Core Web Vitals (LCP, FID, CLS), and availability. Use CloudWatch RUM (Real User Monitoring) to measure frontend SLOs. |
| **Evidence** | No SLO definition files. No CloudWatch alarm configurations. No monitoring configuration of any kind. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics. No CloudWatch `putMetricData`, no analytics integration, no custom event tracking. The dashboard displays mock chart data only. |
| **Gap** | No business metrics — only mock data displayed with no real analytics. |
| **Recommendation** | When productionizing, add frontend analytics: user engagement metrics, feature usage tracking, and error rates by component. Use CloudWatch RUM or a frontend analytics service to publish custom metrics alongside infrastructure metrics. |
| **Evidence** | No metrics SDK in `package.json`. `src/app/views/dashboard/dashboard-charts-data.ts` — displays `Math.random()` generated data, not real metrics. |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configured. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no composite alarms. |
| **Gap** | No alerting — production issues would go undetected. |
| **Recommendation** | When deploying to production, configure CloudWatch alarms for: frontend error rates (4xx/5xx from CloudFront), latency p99 thresholds, and anomaly detection on traffic patterns. Integrate with an incident management tool (PagerDuty, OpsGenie, or AWS Incident Manager). |
| **Evidence** | No `aws_cloudwatch_metric_alarm` resources. No alerting configuration. No IaC files. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy. The CI/CD workflow (`.github/workflows/build-check.yml`) only builds the application — there is no deployment stage. No blue/green, no canary, no rolling deployment, no direct-to-production deployment. The application has never been deployed via automation. |
| **Gap** | No deployment automation — builds are produced but never deployed. This is a fundamental operational gap. |
| **Recommendation** | Implement a deployment pipeline: 1) For S3 + CloudFront hosting: use `aws s3 sync` with CloudFront invalidation, enabling instant rollback via previous S3 versions. 2) For EKS (preferred): use Helm with rolling deployments and health checks, graduating to canary deployments via Argo Rollouts. |
| **Evidence** | `.github/workflows/build-check.yml` — workflow ends at `npm run build`, no deployment steps. No CodeDeploy, no Helm release, no `kubectl apply` steps. |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The project has 48 `.spec.ts` test files covering most Angular components. Unit tests use Vitest with Playwright for browser-based testing. The `prebuild` script in `package.json` runs `ng test --watch=false` before every build, ensuring tests pass before artifact creation. Tests use `TestBed` to create component fixtures and verify component creation. However, these are component-level unit tests that verify individual components render correctly — not integration tests that validate end-to-end user workflows or API contract compliance. |
| **Gap** | Component-level tests exist but no end-to-end integration tests for critical user workflows (login flow, dashboard rendering with real data, navigation between features). |
| **Recommendation** | Add Playwright end-to-end tests for critical user workflows: page navigation, dashboard data rendering, theme switching, responsive layout verification. When backend APIs are added, add API contract tests to validate frontend-backend integration. |
| **Evidence** | 48 `.spec.ts` files across `src/app/`. `package.json` — `"prebuild": "ng test --watch=false"`, `"vitest": "^4.1.0"`, `"playwright": "^1.58.2"`. `angular.json` — test builder configured with `ChromiumHeadless`. |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response automation. No runbooks in any format (markdown, YAML, JSON). No SSM Automation documents. No self-healing patterns. No incident workflows defined. |
| **Gap** | No incident response — all responses would be ad hoc. |
| **Recommendation** | When deploying to production, create runbooks for common scenarios: frontend deployment rollback, CloudFront cache invalidation, EKS pod restart procedures. Start with markdown runbooks, then automate with SSM Automation documents. |
| **Evidence** | No runbook files in repository. No `AWS::SSM::Document` resources. No Lambda-based remediation. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership. No service-level dashboards, no alarms with named owners, no CODEOWNERS file for observability configurations. No monitoring infrastructure exists. |
| **Gap** | No observability ownership — no defined responsibility for monitoring or alerting. |
| **Recommendation** | When deploying to production, create a CloudWatch dashboard for the frontend service with key metrics (error rate, latency, cache hit ratio). Define CODEOWNERS for observability configuration files. Assign team ownership for alarm response. |
| **Evidence** | No dashboard definitions. No CODEOWNERS file. No alarm configurations with owner tags. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tagging. No AWS resources are defined in IaC to tag. No tagging standard documented. |
| **Gap** | No tagging governance — when resources are created, cost allocation, ownership tracking, and environment identification will be impossible without tags. |
| **Recommendation** | When creating IaC, define a mandatory tagging standard: `Environment`, `Service`, `Owner`, `CostCenter` as minimum required tags. Enforce via `default_tags` in Terraform provider or CDK aspects. Enable AWS Cost Allocation tags for financial management. |
| **Evidence** | No `default_tags`, no `tags` on resources. No IaC files. No Tag Policy or Config rule definitions. |

---

## Learning Materials

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to Cloud Native** | [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |
| **Move to Containers** | [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM) · [Move to Containers with Amazon ECS](https://skillbuilder.aws/learning-plan/CDA8Y4JRRR) · [EKS Workshop](https://www.eksworkshop.com/) |
| **Move to Managed Databases** | [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W) |
| **Move to Modern DevOps** | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `package.json` | INF-Q2, INF-Q11, APP-Q1, APP-Q2, APP-Q3, APP-Q4, DATA-Q3, SEC-Q3, SEC-Q4, SEC-Q5, SEC-Q7, OPS-Q1, OPS-Q6 | Dependency manifest — TypeScript 5.9, Angular 21.2.x, CoreUI 5.6.x, Vitest, Playwright, undici override. prebuild script. |
| `angular.json` | INF-Q1, APP-Q2, DATA-Q1 | Angular project configuration — single project, production build with output hashing, assets inclusion. |
| `tsconfig.json` | APP-Q1 | TypeScript configuration — strict mode, ES2022 target. |
| `src/main.ts` | APP-Q1 | Application entry point — bootstraps AppComponent with appConfig. |
| `src/app/app.config.ts` | INF-Q3, INF-Q4, APP-Q3 | Application providers — Router with lazy-loading, animations, icons. No HttpClient, no auth providers. |
| `src/app/app.routes.ts` | APP-Q2, APP-Q5, APP-Q6, SEC-Q3 | Route definitions — 10 lazy-loaded feature modules, login/register pages, 404/500 error pages. No auth guards. |
| `src/app/app.component.ts` | APP-Q2 | Root component — color mode service, icon set, router outlet. |
| `src/app/views/dashboard/dashboard.component.ts` | DATA-Q2 | Dashboard — hardcoded `users: IUser[]` array with 6 mock users, chart initialization. |
| `src/app/views/dashboard/dashboard-charts-data.ts` | DATA-Q2, OPS-Q3 | Chart data service — generates random chart data with `Math.random()`. |
| `src/app/layout/default-layout/default-layout.component.ts` | APP-Q2 | Layout component — sidebar navigation, main container, footer/header. |
| `src/app/layout/default-layout/default-header/default-header.component.ts` | DATA-Q2 | Header — hardcoded `newMessages`, `newNotifications`, `newStatus`, `newTasks` arrays. |
| `src/app/views/pages/login/login.component.ts` | SEC-Q3, SEC-Q4 | Login page — empty component class, no authentication logic. |
| `src/app/views/pages/register/register.component.ts` | SEC-Q3, SEC-Q4 | Register page — empty component class, no registration logic. |
| `.github/workflows/build-check.yml` | INF-Q11, SEC-Q7, OPS-Q5, OPS-Q6 | CI workflow — npm ci, Playwright install, npm run build on 3 OS platforms. No deploy, no security scanning. |
| `.github/workflows/stale.yml` | INF-Q11 | Stale issue/PR management workflow. |
| `README.md` | Quick Agent Wins | Comprehensive documentation — Quick Start, Installation, Usage, project structure, versioning. |
| `CHANGELOG.md` | Quick Agent Wins, SEC-Q7 | 858-line version history — dependency updates, vulnerability mitigation (undici CVEs). |
| `src/assets/` | DATA-Q1 | Static images bundled at build time, not served from managed object storage. |
| `.editorconfig` | Discovery | Editor configuration — UTF-8, 2-space indent, single quotes for TypeScript. |
| `.gitignore` | SEC-Q5 | Git ignore rules — excludes dist/, node_modules/, IDE files. No evidence of .env files. |
| `src/components/` | Discovery | Demo-only components — docs-callout, docs-example, docs-link, docs-icons. |
| `.github/CODE_OF_CONDUCT.md` | Discovery | Community documentation. |
| `.github/CONTRIBUTING.md` | Quick Agent Wins | Contributor guidelines. |
| `.github/SUPPORT.md` | Quick Agent Wins | Support documentation. |
| `.github/COMMIT_CONVENTION.md` | Quick Agent Wins | Commit convention guidelines. |
