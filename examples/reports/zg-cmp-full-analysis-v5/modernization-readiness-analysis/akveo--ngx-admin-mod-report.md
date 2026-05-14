# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | ngx-admin |
| **Date** | 2026-04-30 |
| **TD Version** | 3g1iuew7esd4bia3qcdwvael |
| **Repo Type** | application |
| **Service Archetype** | stateless-utility (auto-detected) |
| **Priority** | P2 |
| **Tags** | typescript, frontend, angular |
| **Context** | Angular admin dashboard template. |
| **Surface Flags** | has_persistent_data_store=false, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=false, has_multi_instance_deployment=false |
| **Overall Score** | 1.51 / 4.0 |

**Archetype Justification**: No backend server, no database connections, no message queue consumers, no persistent state, and no write endpoints detected. All data is served from in-memory mock services (`@core/mock/`). This is a pure client-side Angular SPA template with no runtime backend — classified as `stateless-utility`, the closest archetype match for a frontend-only application with no server-side operations.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.57 / 4.0 | 🟠 Needs Work |
| Application Architecture (APP) | 1.75 / 4.0 | 🟠 Needs Work |
| Data Platform Modernization (DATA) | 2.25 / 4.0 | 🟠 Needs Work |
| Security Baseline (SEC) | 1.00 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.00 / 4.0 | ❌ Not Present |
| **Overall** | **1.51 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | SEC-Q5: Secrets Management | 1 | Google Maps API key hardcoded in source code (`app.module.ts`) | Plaintext credential in version control; deployment-blocking security issue |
| 2 | INF-Q10: IaC Coverage | 1 | No infrastructure-as-code — all infrastructure is manual (ClickOps) or undefined | Blocks reproducible deployments, disaster recovery, and environment consistency; triggers Move to Modern DevOps pathway |
| 3 | INF-Q1: Managed Compute | 1 | No managed compute — static SPA deployed via rsync with no AWS compute services | No elastic scaling, no managed patching, no container orchestration; triggers Move to Cloud Native and Move to Containers pathways |
| 4 | OPS-Q6: Integration Testing | 1 | No test files found (no `*.spec.ts`); no integration or unit tests in CI pipeline | High regression risk during any modernization effort; no safety net for changes |
| 5 | SEC-Q7: Application Security Pipeline | 1 | No SAST, dependency scanning, or container scanning in CI/CD pipeline | Vulnerabilities in dependencies reach production undetected; 40+ npm dependencies with no automated scanning |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 2). GitHub Actions workflows (`demoDeploy.yml`, `docsDeploy.yml`) and Travis CI (`.travis.yml`) provide build and deployment automation.
- **What it enables:** An agent that triggers builds, checks build status, monitors deployment outcomes, and manages release coordination across the Travis CI and GitHub Actions pipelines.
- **Additional steps:** Consolidate CI/CD to a single platform (recommend GitHub Actions) and add webhook/API integrations for agent-triggered builds. The current rsync-based deployment lacks API surface for programmatic control.
- **Effort:** Medium

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository. `README.md` provides comprehensive project overview, installation notes, feature descriptions, and links to external Nebular documentation. `DEV_DOCS.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, and `CODE_OF_CONDUCT.md` provide additional developer-facing documentation.
- **What it enables:** A knowledge agent that indexes existing documentation and answers developer questions about the ngx-admin template — setup instructions, available components, theming, module structure, and Nebular integration.
- **Additional steps:** Generate structured documentation from the Angular component tree (use Compodoc, which is already configured in `package.json` scripts). Index the `@core/data/` interfaces and `@core/mock/` services for data model questions.
- **Effort:** Low

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=2 (primary: monolithic SPA), INF-Q1=1 (supporting: no managed compute) |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1=1 (no managed compute), no container definitions found; guard passes — no existing Lambda/Fargate/ECS |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4=4 — no proprietary SQL or stored procedures; no commercial database engines detected |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 is Not Evaluated (no database exists); no database to migrate |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4=4; no data processing workloads exist in the repository |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1 (primary: no IaC), INF-Q11=2 (primary: partial CI/CD), OPS-Q5=1 (supporting: no deployment strategy), OPS-Q6=1 (supporting: no integration tests) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in context ("Angular admin dashboard template.") |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:**
The ngx-admin application is a monolithic Angular 15 Single Page Application (APP-Q2 = 2). It is a single deployable unit with well-organized lazy-loaded feature modules (`dashboard`, `e-commerce`, `forms`, `tables`, `maps`, `charts`, `editors`, `layout`, `ui-features`, `extra-components`, `modal-overlays`, `miscellaneous`) but all modules share state via `CoreModule` services and are deployed as one artifact. All data is hardcoded in `@core/mock/` services with no real backend.

**Compute Model Gaps:**
No managed compute exists (INF-Q1 = 1). The application is deployed via `rsync` to a remote host from `demoDeploy.yml`. No AWS compute services (ECS, EKS, Lambda, Fargate) are configured. No IaC exists to define any infrastructure.

**Communication Pattern Gaps:**
APP-Q3 and APP-Q4 are Not Evaluated (archetype-N/A for stateless-utility). As a frontend-only SPA, synchronous patterns are correct.

**Recommended Decomposition Approach:**
For a frontend admin template, the modernization path is not traditional microservices decomposition. Instead:
1. **Host as static site on S3 + CloudFront** — move from rsync deployment to S3 static hosting with CloudFront CDN (aligns with preference for API Gateway for any future backend API).
2. **Externalize mock data into real backend services** — replace `@core/mock/` with real API calls to backend services on EKS (aligns with EKS preference). Use API Gateway as the entry point.
3. **Adopt micro-frontend patterns** if the dashboard needs independent team ownership of feature modules.

See Decomposition Strategy section for detailed approach options.

**Representative AWS Services:** Amazon S3, CloudFront, API Gateway, Amazon EKS (preferred), EventBridge (preferred for future event-driven patterns), Lambda (for lightweight backend functions)

**Recommended Patterns:** Strangler Fig (incrementally replace mock services with real APIs), Anti-corruption Layer (between Angular frontend and new backend services), Hexagonal Architecture (for new backend services)

**AWS Prescriptive Guidance:** [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model:**
No compute infrastructure exists (INF-Q1 = 1). The Angular SPA is built via `npm run build:demo:prod` and deployed by `rsync` to a remote host. No Dockerfile, no `docker-compose.yml`, no Kubernetes manifests were found.

**Container Readiness Indicators:**
- Build output is a static `dist/` directory (Angular compiled assets) — trivially containerizable
- No server-side runtime dependencies (no Node.js server required for production — static files only)
- Dependencies are managed via `package.json` / `package-lock.json` — reproducible builds
- The application uses `node-sass` 4.14.1, which has native binary compilation requirements and is deprecated — should migrate to `sass` (Dart Sass) before containerizing

**Recommended Container Orchestration Platform:**
Given the preference for EKS: Deploy as a containerized Nginx/static-file server on **Amazon EKS** (preferred). For a static SPA, the simplest path is:
1. Create a multi-stage Dockerfile: Stage 1 builds the Angular app, Stage 2 copies `dist/` into an Nginx Alpine image
2. Push to Amazon ECR
3. Deploy to EKS with Helm chart (avoid self-managed Kubernetes per preferences)

**Alternative (simpler for static content):** Host directly on **S3 + CloudFront** without containers. This is the most cost-effective approach for a static SPA and avoids unnecessary container orchestration overhead for static files. Containerization becomes relevant when backend services are added.

**Representative AWS Services:** Amazon EKS (preferred), Amazon ECR, AWS Fargate (for serverless container execution on EKS), Amazon S3 + CloudFront (for static hosting alternative)

**Migration Approach:** Lift-and-containerize — the static SPA can be containerized directly with a simple Nginx Dockerfile. No refactoring required for containerization.

**AWS Container Migration Guidance:** [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 1):**
No infrastructure-as-code exists in the repository. No Terraform, CDK, CloudFormation, or Helm files were found. All infrastructure (hosting, DNS, SSL) is presumably managed manually.

**Current CI/CD State (INF-Q11 = 2):**
- **Travis CI** (`.travis.yml`): Runs `lint:ci` + `build:prod` on Node.js 10 (severely outdated). No test execution, no deployment.
- **GitHub Actions** (`demoDeploy.yml`): Builds on Node.js 12 (outdated) and deploys via `rsync` to a remote host using SSH keys. No test stage, no security scanning, no staged rollout.
- **GitHub Actions** (`docsDeploy.yml`): Deploys docs to GitHub Pages on Node.js 12.
- Two CI platforms in use (Travis CI + GitHub Actions) with no coordination — duplicated effort and inconsistent configuration.

**Deployment Strategy Gaps (OPS-Q5 = 1):**
Direct-to-production deployment via rsync. No blue/green, no canary, no rollback capability. A failed deployment requires manual SSH intervention.

**Testing Gaps (OPS-Q6 = 1):**
No test files (`*.spec.ts`) exist despite Karma and Protractor being configured in `karma.conf.js` and `protractor.conf.js`. No unit tests, no integration tests, no end-to-end tests in any CI pipeline.

**Recommended DevOps Toolchain:**
1. **Consolidate to GitHub Actions** — retire Travis CI. Standardize on Node.js 18+ (already used in `atx-transform.yml`).
2. **Add IaC with CDK or Terraform** — define S3 bucket, CloudFront distribution, Route 53 records, and CI/CD pipeline as code.
3. **Implement test stages** — add unit tests (Karma/Jasmine), component tests, and e2e tests (Cypress replacing deprecated Protractor) to the CI pipeline.
4. **Add security scanning** — configure Dependabot for dependency updates, add `npm audit` to CI, integrate SAST tooling (ESLint security rules).
5. **Implement deployment strategy** — for S3/CloudFront: use CloudFront invalidation with staged rollout. For EKS: use Helm-based canary deployments.

**Representative AWS Services:** CodePipeline, CodeBuild, CloudFormation/CDK, S3, CloudFront, CodeDeploy, X-Ray, CloudWatch

**AWS DevOps Prescriptive Guidance:** [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Decomposition Strategy

> **Included because APP-Q2 = 2 (< 3).** The application is a monolithic Angular SPA with identifiable modules but a single deployment unit.

### Context

The ngx-admin application is a frontend-only Angular SPA. Traditional backend monolith decomposition patterns (Strangler Fig for extracting backend services, Saga for distributed transactions) apply differently here. The primary decomposition opportunities are:

1. **Externalizing mock data into real backend API services** — the `@core/mock/` layer currently serves hardcoded data. Replacing this with real API calls creates the first service boundary.
2. **Hosting modernization** — moving from rsync-to-server to S3/CloudFront or containerized hosting.
3. **Micro-frontend adoption** — if the dashboard grows to require independent team ownership of feature modules.

### Approach Options

| Approach | Description | When to Use | Level of Effort | Recommendation |
|----------|-------------|-------------|-----------------|----------------|
| **Conditional / Adaptive** | Containerize or host the Angular SPA on S3/CloudFront first, then selectively build backend services to replace mock data providers as business needs require. Not all mock services need real backends immediately. | APP-Q2 = 2 and the team has limited capacity. This is a template/demo app — full decomposition may not be needed yet. | **Low to Medium** — S3/CloudFront hosting in 1-2 weeks; selective backend service creation over 2-6 months per service. | ✅ **Recommended.** Start with hosting modernization (S3 + CloudFront or containerized Nginx on EKS per preference), then incrementally build backend services behind API Gateway as the dashboard moves from demo to production use. |
| **Strangler Fig (Parallel Track)** | Keep the existing mock data layer operational while building real backend services one at a time. Replace mock services with API-calling services using the existing `@core/data/` abstract interfaces as the switchover point. | When the dashboard is actively being productionized and multiple mock services need real backends. The existing abstract data interface pattern (`UserData`, `SmartTableData`, etc.) provides clean switchover points. | **Medium** — 3-6 months for core data services. Each mock-to-real migration is bounded by the abstract interface. | ✅ **Recommended when productionizing.** The existing `@core/data/` abstraction layer acts as a natural Anti-corruption Layer — swap mock implementations for real API service implementations without changing component code. |
| **Big-Bang Rewrite** | Rewrite the entire frontend as a micro-frontend architecture with independently deployable modules. | Almost never for this repository. The existing modular Angular structure with lazy-loading is already well-organized. | **Very High** — 6-12+ months. High risk for marginal gain given the current clean module structure. | ⚠️ **Recommended against.** The existing Angular module structure with lazy-loading provides adequate separation. Micro-frontends add significant complexity (module federation, shared state management, deployment orchestration) that is not warranted for an admin dashboard. |

### Pattern Recommendations

| Pattern | Purpose | When to Apply | AWS Prescriptive Guidance |
|---------|---------|---------------|---------------------------|
| **Anti-corruption Layer (ACL)** | The existing `@core/data/` abstract interfaces already serve as an ACL between the UI components and data sources. When building real backend services, maintain this boundary — the Angular components should not know whether data comes from mock services or real APIs. | Every mock-to-real migration. The `UserData` abstract class is the ACL — swap `UserService` (mock) for `UserApiService` (real HTTP calls) via Angular DI. | [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) |
| **Hexagonal Architecture (Ports and Adapters)** | Structure each new backend service with clear boundaries between business logic, API interfaces (ports), and infrastructure (adapters — DynamoDB, Aurora, etc.). | Every new backend service created to replace mock data. Ensures services are testable and portable across AWS services. | [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |

### Effort Estimation Factors

| Factor | This Repository's Signal | Effort Impact |
|--------|--------------------------|---------------|
| Module boundaries | Well-organized: 12 lazy-loaded feature modules with clear routing boundaries | Low — clean module boundaries reduce extraction effort |
| Data coupling | `@core/mock/` provides centralized mock data via abstract interfaces; no shared mutable database | Low — the abstract interface pattern provides clean switchover points |
| Stored procedures | None — all logic in TypeScript application layer (DATA-Q4 = 4) | Low — no database coupling to untangle |
| Communication patterns | No inter-service communication (frontend-only) | Low — no existing sync patterns to refactor |
| CI/CD maturity | Partial automation (INF-Q11 = 2) — build works but deployment is rsync-based | Medium — need to build proper CI/CD before deploying multiple services |
| Test coverage | No tests exist (OPS-Q6 = 1) | High risk — no safety net for refactoring. Add tests before any extraction. |

**Calibrated Effort Estimate:** Low for hosting modernization (1-2 weeks for S3/CloudFront). Medium for first backend service (4-6 weeks including CI/CD setup). The primary blocker is the complete absence of tests — establishing test coverage should precede any architectural changes.

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed compute services are defined anywhere in the repository. No IaC files exist (no Terraform, CDK, CloudFormation, or Helm). No Dockerfile or container definitions were found. The application is a static Angular SPA deployed via `rsync` from `.github/workflows/demoDeploy.yml` to a remote host using SSH keys. The deployment command is: `rsync -r --delete-after dist/. "${{ secrets.REMOTE_URL }}":"${{ secrets.ADDRESS }}"`. This suggests a manually provisioned server (likely EC2 or bare metal) with no managed compute orchestration. |
| **Gap** | All compute is unmanaged — no ECS, EKS, Lambda, Fargate, or even documented EC2 instances. The hosting model is opaque (rsync to an unknown server). No auto-scaling, no managed patching, no container orchestration. |
| **Recommendation** | For a static SPA, the optimal hosting model is **S3 + CloudFront** — zero server management, automatic scaling, global CDN, and HTTPS. Alternatively, if backend services will be added, containerize and deploy to **Amazon EKS** (preferred per analysis preferences). Define hosting infrastructure as code using CDK or Terraform. |
| **Evidence** | `.github/workflows/demoDeploy.yml` (rsync deployment), `package.json` (build scripts), absence of any IaC files, absence of Dockerfile |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy a database. INF-Q2 does not apply. The ngx-admin application is a frontend-only Angular SPA where all data is served from in-memory mock services (`@core/mock/`). No database connections, drivers, or database resources exist in IaC or source code. `has_persistent_data_store=false`. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `package.json` (no database drivers), `src/app/@core/mock/` (all mock data services), absence of any `.tf`, `.cfn.yaml`, or database configuration files |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Workflow orchestration is not applicable by design — no multi-step workflows exist for a frontend-only SPA template. All page navigation is client-side Angular routing; there are no server-side workflows, batch processes, or multi-service coordination patterns. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/app/app-routing.module.ts` (client-side routes only), `src/app/pages/pages-routing.module.ts` (lazy-loaded modules), absence of Step Functions, Temporal, or workflow definitions |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | This service is a `stateless-utility`. Synchronous HTTP is the correct design for a frontend-only SPA — no messaging or streaming infrastructure is needed. The application makes no outbound HTTP calls to external services (only loads local JSON assets from `src/assets/`). No SQS, SNS, EventBridge, Kafka, or any messaging client libraries exist in `package.json`. This is the correct architecture for this archetype. |
| **Gap** | None — synchronous patterns are appropriate for this archetype. |
| **Recommendation** | Adopting async messaging is NOT recommended for the current frontend-only architecture — it would add operational complexity without architectural benefit. If backend services are added in the future, consider **Amazon EventBridge** (preferred) for event-driven communication between services. Avoid self-managed Kafka per preferences. |
| **Evidence** | `package.json` (no messaging client libraries), `src/app/@core/mock/` (all data is in-memory), absence of any queue/stream/event handler patterns in source code |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnets, security groups, NACLs, or any network configuration exists in the repository. No IaC files define any networking resources. The `demoDeploy.yml` workflow deploys via rsync over SSH to a remote host whose network configuration is not visible in the repository. The deployment target address is stored in GitHub Secrets (`REMOTE_URL`, `ADDRESS`) — the network posture of the hosting environment cannot be assessed from the repository alone. |
| **Gap** | No network security configuration exists in the repository. The hosting environment's network posture is completely opaque — no evidence of private subnets, security groups, or network segmentation. |
| **Recommendation** | Define network infrastructure as code. If moving to S3 + CloudFront, use CloudFront with OAI/OAC to restrict S3 access. If deploying to EKS (preferred), define VPC with private subnets, configure security groups with least-privilege rules, and use VPC endpoints for AWS service access. Consider VPC Lattice for service-to-service networking when backend services are added. |
| **Evidence** | Absence of any `.tf`, `.cfn.yaml`, or Kubernetes network policy files; `.github/workflows/demoDeploy.yml` (rsync to unknown host) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, AppSync, or any managed entry point is configured. No IaC exists to define any entry point resources. The application is deployed directly to a remote server via rsync — the entry point configuration (web server, HTTPS, domain routing) is not defined in the repository. |
| **Gap** | No managed API or content delivery entry point. The hosting setup lacks visible throttling, authentication, or request validation at the edge. |
| **Recommendation** | Deploy behind **Amazon CloudFront** for static content delivery with HTTPS, caching, and WAF integration. If backend APIs are added, use **Amazon API Gateway** (preferred) as the API entry point with throttling, authentication, and request validation. |
| **Evidence** | Absence of any IaC defining `aws_api_gateway_*`, `aws_lb_*`, `aws_cloudfront_distribution`, or similar resources |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. No IaC defines any scalable resources. The rsync-deployed hosting model has no visible scaling mechanism. For a static SPA, auto-scaling is inherently provided by S3/CloudFront or managed container services — but neither is in use. |
| **Gap** | No auto-scaling — the hosting model cannot respond to traffic spikes. The current rsync-to-server deployment is implicitly fixed-capacity. |
| **Recommendation** | Moving to **S3 + CloudFront** inherently provides auto-scaling for static content (CloudFront scales automatically). If deploying to EKS (preferred), configure Horizontal Pod Autoscaler with appropriate min/max replicas. |
| **Evidence** | Absence of any IaC defining `aws_autoscaling_*`, `aws_appautoscaling_*`, or Kubernetes HPA |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no persistent state to back up. INF-Q8 does not apply. The ngx-admin application is a frontend-only SPA with no databases, S3 buckets, EBS volumes, or other persistent data stores. All data is hardcoded in `@core/mock/` services. Source code is backed up via Git version control. `has_persistent_data_store=false` AND `has_at_rest_data_surface=false`. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | Absence of any database resources, S3 buckets, or persistent storage in IaC or source code |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload requiring HA evaluation. INF-Q9 does not apply. No IaC defines deployable compute (no ECS, EKS, Lambda, or EC2 resources). The rsync-based deployment does not constitute a managed deployed workload with HA requirements assessable from the repository. `has_deployed_workload=false`. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | Absence of any IaC defining compute resources; `.github/workflows/demoDeploy.yml` (rsync, not a managed deployment) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No infrastructure-as-code files exist in the repository. No Terraform (`.tf`), CDK (`cdk.json`), CloudFormation (`template.yaml`), Helm (`Chart.yaml`), Kustomize (`kustomization.yaml`), or Ansible playbooks were found. All infrastructure is either manually created or undefined. The hosting environment for the rsync deployment is not documented in the repository. |
| **Gap** | 0% IaC coverage. All infrastructure is manual (ClickOps) or undocumented. This means infrastructure changes are non-reproducible, environment consistency cannot be guaranteed, and disaster recovery requires manual reconstruction. |
| **Recommendation** | Define all infrastructure as code using **AWS CDK** (TypeScript — matches the existing language expertise) or **Terraform**. Start with the hosting stack: S3 bucket, CloudFront distribution, Route 53 DNS records, ACM certificate. Then add CI/CD pipeline definition as code. Target 90%+ IaC coverage to achieve Score 4. |
| **Evidence** | Full repository scan: no `.tf`, `.tfvars`, `cdk.json`, `template.yaml`, `template.json`, `Chart.yaml`, `kustomization.yaml`, or playbook files found |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Two CI platforms are in use with partial automation: (1) **Travis CI** (`.travis.yml`) runs `lint:ci` + `build:prod` on Node.js 10 (severely outdated — Node.js 10 reached EOL April 2021). No test execution, no deployment. (2) **GitHub Actions** (`demoDeploy.yml`) runs `npm install`, `npm run build:demo:prod`, and deploys via `rsync` on Node.js 12 (EOL April 2022). No test stage, no security scanning. (3) **GitHub Actions** (`docsDeploy.yml`) deploys docs to GitHub Pages on Node.js 12. (4) **GitHub Actions** (`atx-transform.yml`) runs ATX transforms on Node.js 18. Build is automated but deployment is semi-manual rsync. No IaC automation. No automated testing in any pipeline beyond linting. |
| **Gap** | Deployment is semi-manual (rsync). No test stages in any CI pipeline. No IaC change automation. Two CI platforms with duplicated, inconsistent configuration. Node.js versions severely outdated (10, 12) in Travis CI and main deploy workflows. |
| **Recommendation** | Consolidate to **GitHub Actions** and retire Travis CI. Upgrade all workflows to Node.js 18+. Add test stages (`npm test`), security scanning (`npm audit`), and deploy via **AWS CDK deploy** or **S3 sync + CloudFront invalidation** instead of rsync. Add IaC validation stage for infrastructure changes. |
| **Evidence** | `.travis.yml` (Node.js 10, lint+build only), `.github/workflows/demoDeploy.yml` (Node.js 12, rsync deploy), `.github/workflows/docsDeploy.yml` (Node.js 12, docs deploy), `.github/workflows/atx-transform.yml` (Node.js 18, ATX CI) |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application uses **TypeScript 4.9.5** with **Angular 15.2.10** and the **Nebular 11.0.1** UI framework. TypeScript is a modern cloud-native language with first-class AWS SDK coverage and broad tooling ecosystem. Angular 15 is a recent but not current version — Angular 17+ is current, making this one major version behind. Nebular 11 is tightly coupled to Angular 15. Other notable dependencies: RxJS 6.6.2 (current is RxJS 7+), Bootstrap 4.3.1 (current is 5+), chart.js 2.7.1 (current is 4+), echarts 4.9.0 (current is 5+), leaflet 1.2.0 (current is 1.9+). The `node-sass` 4.14.1 dependency is deprecated — the ecosystem has moved to Dart Sass (`sass` package). No AWS SDK is present (no backend). |
| **Gap** | Framework lag — Angular 15 is one major version behind current (17+). Several key dependencies are significantly outdated: `node-sass` is deprecated, RxJS 6.x is behind RxJS 7.x, Bootstrap 4.x is behind 5.x. The `node-sass` dependency creates build complexity due to native binary compilation requirements. |
| **Recommendation** | Upgrade Angular to version 17+ (or latest LTS). Replace `node-sass` with `sass` (Dart Sass) to eliminate native binary compilation issues. Upgrade RxJS to 7.x, Bootstrap to 5.x. Evaluate whether Nebular can be upgraded or replaced with Angular Material or PrimeNG for broader ecosystem support. |
| **Evidence** | `package.json` (Angular 15.2.10, TypeScript 4.9.5, node-sass 4.14.1, RxJS 6.6.2), `tsconfig.json` (ES2022 target) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application is a **single deployable Angular SPA** — a monolith by definition. However, it has **well-organized module boundaries**: 12 lazy-loaded feature modules (`dashboard`, `e-commerce`, `forms`, `tables`, `maps`, `charts`, `editors`, `layout`, `ui-features`, `extra-components`, `modal-overlays`, `miscellaneous`) loaded via `loadChildren` in `pages-routing.module.ts`. The architecture follows a clean separation: `@core/` for data and services, `@theme/` for shared UI components, and `pages/` for feature modules. Shared state is managed via `CoreModule` services (19 data service providers registered in `core.module.ts` via DI). The `@core/data/` interfaces define abstract data contracts with `@core/mock/` providing concrete implementations — a pattern that supports clean replacement of data sources. |
| **Gap** | Single deployment unit with shared state via CoreModule. While module boundaries are clean, all 19 data services are registered globally in CoreModule — no module-level data isolation. The mock data layer creates tight coupling between the UI and data representation. However, the abstract interface pattern mitigates this significantly. |
| **Recommendation** | The modular structure is a strength. For modernization: (1) Maintain the existing lazy-loaded module boundaries as potential micro-frontend extraction points. (2) Replace `@core/mock/` implementations with real API-calling services, leveraging the existing `@core/data/` abstractions as the Anti-corruption Layer. (3) Do NOT force micro-frontend decomposition unless team ownership requires it — the current structure is adequate for a single-team admin dashboard. |
| **Evidence** | `src/app/pages/pages-routing.module.ts` (12 lazy-loaded modules), `src/app/@core/core.module.ts` (19 data services), `src/app/@core/data/users.ts` (abstract interface example), `src/app/@core/mock/users.service.ts` (mock implementation example) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Sync request/response is the correct design for a frontend-only SPA — async inter-service communication does not apply. The application makes no outbound HTTP calls to external APIs; all data is served from in-memory mock services. Client-side RxJS Observables are used for reactive data flow within the SPA, but this is internal component communication, not inter-service communication. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/app/@core/mock/` (all data in-memory), `package.json` (no HTTP client libraries for external API calls), `src/app/@core/data/users.ts` (Observable-based internal data flow) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. No operations exceed 30 seconds — not applicable by design. The Angular SPA performs only client-side rendering, mock data retrieval (in-memory, sub-millisecond), and UI interactions. No server-side processing, no bulk operations, no external API calls with variable latency. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/app/@core/mock/` (all data returned via `observableOf()` — synchronous in-memory), absence of any background job frameworks or long-running process patterns |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy exists. The application is a frontend-only SPA with no server-side API endpoints to version. Client-side routes (defined in `app-routing.module.ts` and `pages-routing.module.ts`) do not use versioning — they are internal SPA navigation routes (`/pages/dashboard`, `/pages/charts`, `/auth/login`). No OpenAPI, Swagger, AsyncAPI, or GraphQL schema files were found. |
| **Gap** | No API surface exists to version. When backend services are built to replace mock data, API versioning will need to be established from the start. |
| **Recommendation** | When building backend services, define API contracts using **OpenAPI specifications** from day one. Implement URL-path versioning (`/v1/users`, `/v1/orders`) on API Gateway (preferred). Establish a versioning strategy before the first backend API is deployed. |
| **Evidence** | `src/app/app-routing.module.ts` (client-side routes only), `src/app/pages/pages-routing.module.ts` (feature routes), absence of any OpenAPI/Swagger/AsyncAPI/GraphQL files |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No service discovery mechanism exists. The application is a frontend-only SPA with no service-to-service communication. The only external endpoint reference is the Google Maps API key hardcoded in `app.module.ts` (`AIzaSyA_wNuCzia92MAmdLRzmqitRGvCF7wCZPY`). No HTTP client calls to external services were found — all data is from `@core/mock/` in-memory services. No environment variables for service endpoints, no service registry, no API catalog. |
| **Gap** | No service discovery — though no services exist to discover currently. When backend services are built, service endpoints will need dynamic discovery rather than hardcoding. |
| **Recommendation** | When building backend services on EKS (preferred), use **Kubernetes Service DNS** for intra-cluster discovery and **API Gateway** (preferred) as the external entry point. Configure Angular environment files (`environment.ts`, `environment.prod.ts`) to inject API Gateway endpoint URLs at build time rather than hardcoding service addresses. |
| **Evidence** | `src/environments/environment.ts` (no service URLs), `src/environments/environment.prod.ts` (only `production: true`), `src/app/@core/mock/` (all data in-memory, no HTTP calls) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No managed object storage (S3) is used. Static assets are stored in the `src/assets/` directory within the repository and deployed as part of the Angular build output. This includes: GeoJSON map data (`src/assets/map/world.json`, `src/assets/leaflet-countries/`), image files (`src/assets/images/`), and editor skins (`src/assets/skins/`). All data files are committed directly to the Git repository and served as static files from the web server. |
| **Gap** | All unstructured data is on local file systems (bundled in the Angular build output). No managed object storage, no parsing pipeline, no content management. |
| **Recommendation** | When productionizing, move static assets to **Amazon S3** with CloudFront CDN. For map data and images, S3 provides versioning, lifecycle management, and global distribution. If document processing is needed, integrate **Amazon Textract** for document parsing. |
| **Evidence** | `src/assets/` (static files), `angular.json` (assets configuration), absence of any S3 bucket references |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application has a **well-structured data access pattern** using Angular's dependency injection. Abstract data interfaces are defined in `@core/data/` (e.g., `UserData`, `SmartTableData`, `ElectricityData` — 19 abstract classes total). Concrete mock implementations are in `@core/mock/` (e.g., `UserService`, `SmartTableService` — 19 service classes). All data services are registered centrally in `core.module.ts` via the `DATA_SERVICES` array using `{ provide: UserData, useClass: UserService }` pattern. UI components inject the abstract data class, not the concrete implementation — allowing seamless swapping from mock to real API services. |
| **Gap** | While the pattern is centralized and well-designed, all data is mock (hardcoded in-memory). The abstraction layer has not been tested with real API backends. Some auxiliary data (map GeoJSON, static JSON) is loaded directly via `HttpClient` rather than through the centralized data service layer. |
| **Recommendation** | Maintain the existing `@core/data/` abstraction pattern as the foundation for real backend integration. When building API services, create new implementation classes (e.g., `UserApiService`) that call backend APIs via `HttpClient` and register them in place of mock services. Migrate direct `HttpClient` JSON loads to the same data service pattern for consistency. |
| **Evidence** | `src/app/@core/data/users.ts` (abstract interface), `src/app/@core/mock/users.service.ts` (mock implementation), `src/app/@core/core.module.ts` (centralized DI registration with 19 data services) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database engines are defined in the repository. No IaC defines any database resources (no `aws_rds_instance`, `aws_dynamodb_table`, or similar). No database connection strings, driver dependencies, or migration files exist. No engine version pinning because no database exists. While the frontend-only nature of this app means no database is expected, the Score 1 reflects the genuine absence — if/when a database is added, engine version management will need to be established from scratch. |
| **Gap** | No database infrastructure to assess for version management. When databases are added for backend services, engine version pinning and EOL tracking will need to be established. |
| **Recommendation** | When adding databases, use **Amazon Aurora** (preferred) or **Amazon DynamoDB** (preferred) depending on the access pattern. Explicitly pin engine versions in IaC from day one and establish a documented version-update procedure. Avoid Oracle per preferences. |
| **Evidence** | `package.json` (no database drivers), absence of any `.sql` files, absence of any database IaC resources |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs exist. All business logic resides in the TypeScript application layer. The `@core/mock/` services contain all data transformation and filtering logic in TypeScript (e.g., `UserService.getContacts()` returns filtered in-memory arrays). No SQL files, no ORM configuration, no database schema definitions. This is the ideal state — all logic in the application layer with no database coupling. |
| **Gap** | None — no stored procedures or proprietary SQL. |
| **Recommendation** | Maintain this pattern when building backend services. Keep all business logic in the application layer (TypeScript/Node.js services or Java services on EKS). Use ORM or query builders for data access rather than stored procedures. This ensures database portability between Aurora, DynamoDB, and other engines. |
| **Evidence** | `src/app/@core/mock/` (all logic in TypeScript), absence of any `.sql` files, absence of `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION` patterns |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging configuration exists. No IaC defines any logging resources. The application has a basic `AnalyticsService` (`src/app/@core/utils/analytics.service.ts`) that tracks page views via Google Analytics (`ga()` function calls), but this is client-side analytics tracking, not audit logging. No server-side logging, no CloudWatch log groups, no log retention policies. |
| **Gap** | No audit logging. No ability to trace user actions, API calls, or infrastructure changes. |
| **Recommendation** | When deploying to AWS, enable **AWS CloudTrail** with log file validation and immutable storage (S3 Object Lock). Define CloudTrail resources in IaC. For the frontend, consider CloudFront access logs for request-level auditing. |
| **Evidence** | `src/app/@core/utils/analytics.service.ts` (Google Analytics only), absence of any `aws_cloudtrail` or CloudWatch IaC |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no database, S3 bucket, EBS volume, or similar. SEC-Q2 does not apply. The ngx-admin application is a frontend-only SPA with all data hardcoded in source code. `has_at_rest_data_surface=false`. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | Absence of any data storage resources in IaC or source code |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application uses `@nebular/auth` with `NbDummyAuthStrategy` — a **dummy authentication strategy** that auto-succeeds after a 3-second delay. This is configured in `core.module.ts`: `NbDummyAuthStrategy.setup({ name: 'email', delay: 3000 })`. Auth routes exist (login, register, logout, request-password, reset-password) in `app-routing.module.ts`, but they use the dummy strategy and provide no real authentication. No JWT, no OAuth2, no Cognito, no real token-based authentication. The role provider returns a hardcoded `'guest'` role (`NbSimpleRoleProvider`). |
| **Gap** | No real authentication. The NbDummyAuthStrategy is a demo stub — it does not validate credentials, issue tokens, or integrate with any identity provider. Any user can access all dashboard content without authentication. |
| **Recommendation** | Replace `NbDummyAuthStrategy` with a real authentication strategy. Integrate with **Amazon Cognito** for user authentication — Nebular's `@nebular/auth` supports custom auth strategies. Implement JWT-based authentication with Cognito User Pools. For the frontend-only use case, use Cognito Hosted UI for login flows. |
| **Evidence** | `src/app/@core/core.module.ts` (NbDummyAuthStrategy configuration, NbSimpleRoleProvider with hardcoded 'guest' role), `src/app/app-routing.module.ts` (auth routes using dummy strategy) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application manages its own dummy authentication with no external identity provider integration. `NbDummyAuthStrategy` is not connected to any IdP (Cognito, Okta, SAML, OIDC). The role provider (`NbSimpleRoleProvider`) returns a hardcoded `'guest'` role with no identity federation. No SSO configuration exists. |
| **Gap** | No centralized identity integration. No external IdP, no SSO, no OIDC/SAML federation. The application cannot participate in organizational identity governance. |
| **Recommendation** | Integrate with **Amazon Cognito** as the centralized identity provider. Configure Cognito User Pool with OIDC/SAML federation for organizational SSO. Replace `NbSimpleRoleProvider` with a Cognito-backed role provider that maps Cognito groups to Nebular security roles. |
| **Evidence** | `src/app/@core/core.module.ts` (NbDummyAuthStrategy, NbSimpleRoleProvider), absence of any Cognito, OIDC, or SAML configuration |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | A **Google Maps API key is hardcoded in source code**: `src/app/app.module.ts` contains `messageGoogleMapKey: 'AIzaSyA_wNuCzia92MAmdLRzmqitRGvCF7wCZPY'`. This plaintext credential is committed to the Git repository and exposed in the compiled JavaScript bundle. No Secrets Manager, no Vault, no environment variable substitution for secrets. The `demoDeploy.yml` workflow uses GitHub Secrets for SSH keys and deployment URLs (`SSH_KEY`, `KNOWN_HOSTS`, `REMOTE_URL`, `ADDRESS`) — these are properly managed in GitHub Secrets, but the Google Maps API key in source code is a plaintext credential violation. |
| **Gap** | Plaintext API key in source code. Score 1 applies because any plaintext secret is a deployment-blocking issue, even when other secrets (GitHub Actions) are properly managed. |
| **Recommendation** | Remove the hardcoded Google Maps API key from source code immediately. Use **Angular environment files** with build-time substitution to inject API keys, or use **AWS Secrets Manager** for runtime secret retrieval. For the frontend, restrict the Google Maps API key by HTTP referrer in the Google Cloud Console to limit abuse if the key is exposed in client-side JavaScript. |
| **Evidence** | `src/app/app.module.ts` (line: `messageGoogleMapKey: 'AIzaSyA_wNuCzia92MAmdLRzmqitRGvCF7wCZPY'`), `.github/workflows/demoDeploy.yml` (GitHub Secrets for SSH — properly managed) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute hardening or patching strategy exists. No SSM Patch Manager, no AWS Inspector, no vulnerability scanning configured. No hardened AMIs or container base images referenced (no Dockerfiles exist). No Dependabot configuration (`.github/dependabot.yml` not found). The Travis CI and GitHub Actions workflows use default runner images with no hardening. The deployment target server's patching posture is not visible from the repository. |
| **Gap** | No vulnerability scanning, no patching automation, no hardened images. The 40+ npm dependencies include packages with known vulnerabilities (node-sass 4.14.1 is deprecated with known security issues). |
| **Recommendation** | Configure **GitHub Dependabot** for automated dependency update PRs. Add `npm audit` to the CI pipeline to catch known vulnerabilities. If containerizing, use hardened base images (e.g., distroless or Alpine) and enable **Amazon ECR image scanning**. Replace deprecated `node-sass` with `sass` (Dart Sass). |
| **Evidence** | `package.json` (node-sass 4.14.1 — deprecated), absence of `.github/dependabot.yml`, absence of `npm audit` in any CI pipeline, absence of any security scanning configuration |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No application security scanning is integrated into any CI pipeline. No SAST tools (SonarQube, Semgrep, CodeGuru). No dependency vulnerability scanning (no Dependabot, no `npm audit`, no Snyk). No container scanning (no Dockerfiles to scan). Travis CI runs only `lint:ci` + `build:prod`. GitHub Actions `demoDeploy.yml` runs only `npm install`, `build`, and `rsync`. No security gates, no vulnerability blocking thresholds. |
| **Gap** | Zero security scanning in the CI/CD pipeline. Vulnerabilities in the 40+ npm dependencies are not detected before deployment. No SAST analysis of TypeScript code. |
| **Recommendation** | Add security scanning to the GitHub Actions pipeline: (1) Configure **Dependabot** for automated npm dependency updates. (2) Add `npm audit --audit-level=high` as a blocking CI step. (3) Integrate a SAST tool — ESLint with security plugins (`eslint-plugin-security`) for TypeScript, or **Amazon CodeGuru Reviewer** for automated code reviews. (4) If containerizing, enable ECR image scanning. |
| **Evidence** | `.travis.yml` (lint + build only), `.github/workflows/demoDeploy.yml` (no security stages), absence of `.github/dependabot.yml`, absence of `.snyk`, absence of `sonar-project.properties` |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing is instrumented. No OpenTelemetry SDK, X-Ray SDK, or tracing libraries exist in `package.json`. The `AnalyticsService` (`src/app/@core/utils/analytics.service.ts`) provides client-side Google Analytics page-view tracking via the `ga()` function, but this is marketing analytics, not distributed tracing. No `traceparent` or `X-Amzn-Trace-Id` header propagation. No trace context in any HTTP requests. |
| **Gap** | No distributed tracing. When backend services are added, there will be no ability to trace requests across service boundaries. |
| **Recommendation** | When building backend services, instrument with **AWS X-Ray** or **OpenTelemetry** from day one. For the Angular frontend, use the **OpenTelemetry JavaScript SDK** to generate browser-side spans and propagate trace context to backend API calls. This enables end-to-end tracing from user click to backend service response. |
| **Evidence** | `package.json` (no OpenTelemetry, X-Ray, or tracing dependencies), `src/app/@core/utils/analytics.service.ts` (Google Analytics only) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no user-facing surface for which SLOs are meaningful. OPS-Q2 does not apply. The ngx-admin application is a frontend-only SPA with no server-side API endpoints and no persistent data store. SLOs (latency p99, error rate, availability) require a server-side surface to measure against. `has_api_surface=false` AND `has_persistent_data_store=false`. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | Absence of any server-side endpoints, absence of any SLO definition files or CloudWatch alarm configurations |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics are published. No CloudWatch `put_metric_data` calls, no custom metric dashboards. The `AnalyticsService` provides Google Analytics page-view tracking, but this is client-side marketing analytics, not operational business metrics. No conversion tracking, no feature usage metrics, no error rate tracking by feature area. |
| **Gap** | No business outcome metrics. Only client-side page-view analytics via Google Analytics (which is disabled by default — `this.enabled = false` in the constructor). |
| **Recommendation** | When productionizing: (1) Enable and configure Google Analytics or migrate to a modern analytics solution. (2) Add custom CloudWatch metrics for business outcomes when backend services are built (e.g., dashboard load times, API response rates, feature usage counts). (3) Create CloudWatch dashboards for operational visibility. |
| **Evidence** | `src/app/@core/utils/analytics.service.ts` (`enabled = false` by default, Google Analytics only) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting is configured. No CloudWatch alarms, no threshold-based alerts, no anomaly detection. No PagerDuty, OpsGenie, or alerting integration. No error tracking service (no Sentry, Datadog, or Bugsnag). |
| **Gap** | Zero alerting. If the deployed application fails, there is no automated notification — failures are detected only by user reports. |
| **Recommendation** | When deploying to AWS: (1) Configure **CloudWatch alarms** on CloudFront error rates (4xx, 5xx) and cache hit ratios. (2) Enable **CloudWatch anomaly detection** on error rates for the hosting layer. (3) Integrate with SNS for alert notifications. (4) For the frontend, add **Real User Monitoring (RUM)** via CloudWatch RUM to track client-side errors and performance. |
| **Evidence** | Absence of any CloudWatch alarm definitions, absence of any alerting configuration in IaC or source code |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Direct-to-production deployment with no staged rollout. The `demoDeploy.yml` workflow executes `rsync -r --delete-after dist/. "$REMOTE_URL":"$ADDRESS"` — this replaces all files on the production server in a single operation with the `--delete-after` flag. No blue/green deployment, no canary release, no traffic shifting. No rollback capability beyond re-running the previous deployment. A failed build deployed to production affects all users immediately with no mitigation. |
| **Gap** | Direct rsync to production — the most fragile deployment strategy possible. No staged rollout, no traffic shifting, no automated rollback. |
| **Recommendation** | For S3 + CloudFront: deploy to S3, create a CloudFront invalidation, and use **CloudFront Functions** or **Lambda@Edge** for traffic shifting. For EKS (preferred): implement **canary deployments** using Argo Rollouts or Flagger with gradual traffic shifting. At minimum, implement versioned S3 deployments with instant rollback via CloudFront origin switching. |
| **Evidence** | `.github/workflows/demoDeploy.yml` (rsync --delete-after), absence of any CodeDeploy, canary, or blue/green configuration |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | **No test files exist in the repository.** A search for `*.spec.ts` files found zero results. The test infrastructure is configured (Karma in `karma.conf.js`, Protractor in `protractor.conf.js`, Jasmine test framework in devDependencies) but no actual test files have been written. The `src/test.ts` file is the Karma test bootstrapper, but there are no spec files for it to execute. The `e2e/` directory contains only `tsconfig.e2e.json` and `.eslintrc.json` — no e2e test specs. Travis CI runs only `lint:ci` and `build:prod` — no test execution. GitHub Actions workflows do not include any test stages. |
| **Gap** | Zero test coverage. No unit tests, no integration tests, no end-to-end tests. The test infrastructure exists but has never been populated with tests. This is the highest-risk gap for any modernization effort — changes cannot be validated against regressions. |
| **Recommendation** | Establish test coverage before any modernization work: (1) Add unit tests for `@core/mock/` services and `@theme/` pipes/components using Karma/Jasmine. (2) Add component tests for critical page components. (3) Replace deprecated **Protractor** (EOL August 2023) with **Cypress** or **Playwright** for e2e testing. (4) Add `npm test` as a required CI stage in GitHub Actions. (5) Enforce minimum code coverage thresholds. |
| **Evidence** | `find . -name "*.spec.ts"` returned 0 results, `karma.conf.js` (test runner configured but unused), `protractor.conf.js` (e2e runner configured but no specs), `.travis.yml` (no test stage), `e2e/` directory (no spec files) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response workflows, runbooks, or automation exist. No Systems Manager Automation documents, no Lambda-based remediation, no Step Functions for incident workflows. No runbook files (markdown, YAML, JSON) in the repository. No on-call or escalation configuration. |
| **Gap** | No incident response capability. When the deployed application fails, there is no documented procedure, no automated remediation, and no escalation path. |
| **Recommendation** | When deploying to AWS: (1) Create runbooks for common incidents (deployment failure rollback, high error rate, SSL certificate expiry). (2) Implement automated rollback via **SSM Automation** or GitHub Actions workflow dispatch. (3) Define escalation paths with SNS topics and on-call integration. |
| **Evidence** | Absence of any runbook files, SSM documents, or incident response automation in the repository |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership is defined. No CODEOWNERS file references observability assets. No per-service dashboards, no alarms with named owners, no SLO definitions with team attribution. No `.github/CODEOWNERS` file exists for any part of the repository. |
| **Gap** | No observability ownership. Monitoring is entirely absent, making ownership attribution impossible. |
| **Recommendation** | When establishing observability: (1) Create a `.github/CODEOWNERS` file with team ownership for monitoring configurations. (2) Define per-feature dashboards in CloudWatch with team attribution tags. (3) Assign alarm ownership to specific team members for incident routing. |
| **Evidence** | Absence of CODEOWNERS file, absence of any observability dashboard or alarm definitions |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging exists. No IaC defines any AWS resources, so there are no resources to tag. No `default_tags` in Terraform provider config, no `tags` on any resources, no tag policies or enforcement. |
| **Gap** | No tagging strategy. When AWS resources are created for this application, cost allocation, ownership, and environment identification will need to be established. |
| **Recommendation** | When creating IaC, establish a tagging standard from day one. Use `default_tags` in the Terraform AWS provider (or CDK `Tags.of()`) to apply mandatory tags: `Environment`, `Service`, `Team`, `CostCenter`. Enable tag enforcement via AWS Config rules and Tag Policies in AWS Organizations. |
| **Evidence** | Absence of any IaC files, absence of any resource tagging configuration |

---

## Learning Materials

The following learning resources are linked to the 3 triggered modernization pathways:

### Move to Cloud Native
- [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

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
| `package.json` | INF-Q1, INF-Q4, APP-Q1, APP-Q3, APP-Q6, DATA-Q3, SEC-Q6, OPS-Q1 | Dependency manifest — Angular 15.2.10, TypeScript 4.9.5, node-sass 4.14.1, no database/messaging/tracing/AI dependencies |
| `angular.json` | INF-Q1, DATA-Q1 | Angular build configuration — assets, styles, scripts, build targets |
| `tsconfig.json` | APP-Q1 | TypeScript compiler configuration — ES2022 target |
| `.travis.yml` | INF-Q11, OPS-Q6, SEC-Q7 | Travis CI — Node.js 10, lint + build only, no tests, no security scanning |
| `.github/workflows/demoDeploy.yml` | INF-Q1, INF-Q5, INF-Q11, OPS-Q5, SEC-Q5 | GitHub Actions — Node.js 12, rsync deployment, SSH key secrets |
| `.github/workflows/docsDeploy.yml` | INF-Q11 | GitHub Actions — docs deployment to GitHub Pages |
| `.github/workflows/atx-transform.yml` | INF-Q11 | GitHub Actions — ATX transform workflow, Node.js 18 |
| `src/app/app.module.ts` | SEC-Q5, INF-Q6 | Root Angular module — hardcoded Google Maps API key (`AIzaSyA_wNuCzia92MAmdLRzmqitRGvCF7wCZPY`) |
| `src/app/@core/core.module.ts` | APP-Q2, SEC-Q3, SEC-Q4, DATA-Q2 | Core module — NbDummyAuthStrategy, NbSimpleRoleProvider, 19 data service registrations |
| `src/app/app-routing.module.ts` | APP-Q5, APP-Q6, SEC-Q3 | Root routing — client-side routes, auth routes with dummy strategy |
| `src/app/pages/pages-routing.module.ts` | APP-Q2 | Feature routing — 12 lazy-loaded feature modules |
| `src/app/@core/data/users.ts` | APP-Q2, APP-Q3, DATA-Q2 | Abstract data interface example — Observable-based UserData contract |
| `src/app/@core/mock/users.service.ts` | APP-Q2, DATA-Q2, DATA-Q4 | Mock data service example — hardcoded in-memory data |
| `src/app/@core/mock/mock-data.module.ts` | DATA-Q2 | Mock data module — registers all 19 mock services |
| `src/app/@core/utils/analytics.service.ts` | OPS-Q1, OPS-Q3 | Google Analytics tracking — page views only, disabled by default |
| `src/environments/environment.ts` | APP-Q6 | Development environment config — no service URLs |
| `src/environments/environment.prod.ts` | APP-Q6 | Production environment config — only `production: true` flag |
| `src/assets/` | DATA-Q1 | Static assets — GeoJSON map data, images, editor skins |
| `karma.conf.js` | OPS-Q6 | Karma test runner config — configured but no spec files exist |
| `protractor.conf.js` | OPS-Q6 | Protractor e2e config — configured but no spec files exist |
| `e2e/` | OPS-Q6 | E2E test directory — only tsconfig and eslintrc, no test specs |
| `README.md` | Quick Agent Wins | Project documentation — installation, features, links |
| `.eslintrc.json` | INF-Q11 | ESLint configuration — Angular-specific rules |
| `src/app/pages/pages.module.ts` | APP-Q2 | Pages module — imports feature modules |
| `src/app/@theme/theme.module.ts` | APP-Q2 | Theme module — shared UI components, layouts, pipes |
