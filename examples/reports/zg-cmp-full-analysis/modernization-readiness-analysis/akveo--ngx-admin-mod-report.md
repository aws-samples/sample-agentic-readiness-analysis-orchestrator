# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | ngx-admin |
| **Date** | 2025-07-16 |
| **Repo Type** | application |
| **Service Archetype** | stateless-utility (auto-detected) |
| **Priority** | P2 |
| **Tags** | typescript, frontend, angular |
| **Context** | Angular admin dashboard template. |
| **Overall Score** | 1.73 / 4.0 |

**Archetype Justification**: No database connections, no writes, no downstream service calls detected. All data sourced from in-memory mock services (`@core/mock/`). Application is a pure frontend Angular 15 dashboard template with no backend integration — all 19 data service interfaces in `@core/data/` are backed by hardcoded mock implementations.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.64 / 4.0 | 🟠 Needs Work |
| Application Architecture (APP) | 2.67 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 2.25 / 4.0 | 🟠 Needs Work |
| Security Baseline (SEC) | 1.00 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.11 / 4.0 | ❌ Not Present |
| **Overall** | **1.73 / 4.0** | **🟠 Needs Work** |

**Scoring notes:**
- INF = (1+1+4+4+1+1+1+1+1+1+2) / 11 = 18 / 11 = 1.64
- APP = (4+2+4+4+1+1) / 6 = 16 / 6 = 2.67
- DATA = (1+3+1+4) / 4 = 9 / 4 = 2.25
- SEC = (1+1+1+1+1+1+1) / 7 = 7 / 7 = 1.00
- OPS = (1+1+2+1+1+1+1+1+1) / 9 = 10 / 9 = 1.11
- Overall = (1.64+2.67+2.25+1.00+1.11) / 5 = 8.67 / 5 = 1.73

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | SEC-Q1 through SEC-Q7: Security Baseline | 1.0 avg | Entire security baseline missing — no audit logging, no encryption, no authentication, hardcoded API key, no secrets management, no patching, no security scanning. | Security is a blocking prerequisite for any production deployment or modernization initiative. |
| 2 | INF-Q10: IaC Coverage | 1 | No Infrastructure as Code — zero IaC files (Terraform, CDK, CloudFormation, or Helm) found in the repository. | Without IaC, infrastructure is not reproducible, not version-controlled, and cannot be deployed consistently across environments. Blocks all infrastructure modernization. |
| 3 | INF-Q1: Managed Compute | 1 | No compute infrastructure defined — no ECS, EKS, Lambda, Fargate, or EC2 resources. Application is deployed via rsync to a remote server. | No managed compute means no auto-scaling, no health checks, no container orchestration — prevents cloud-native operation. |
| 4 | OPS-Q5: Deployment Strategy | 1 | Deployment is a raw rsync of build artifacts directly to a server — no blue/green, no canary, no rolling updates, no rollback capability. | Direct-to-production deployment with no staged rollout means every deployment is a full-risk event with no recovery mechanism. |
| 5 | INF-Q11: CI/CD Automation | 2 | Travis CI runs lint + build. GitHub Actions deploys via rsync. No automated testing in deployment pipeline, no rollback automation. | Partial CI without testing in the deployment path means regressions reach production undetected. |

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** INF-Q11 = 2 (≥ 2). Travis CI pipeline exists (`.travis.yml`) with lint and build stages. GitHub Actions deploys via rsync (`.github/workflows/demoDeploy.yml`).
- **What it enables:** An agent that triggers builds, checks CI status, and manages deployment workflows via the existing Travis CI and GitHub Actions pipelines. The agent can monitor build results, flag lint failures, and orchestrate the simple rsync-based deploy process.
- **Additional steps:** Expose CI/CD status via GitHub API or webhooks. Consider migrating from Travis CI to a unified GitHub Actions pipeline to simplify the agent's integration surface.
- **Effort:** Low

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository — `README.md` (detailed project overview, installation notes, feature list), `CONTRIBUTING.md` (222 lines of contribution guidelines, coding rules, commit conventions), `DEV_DOCS.md` (links to Nebular dev docs), `CHANGELOG.md`.
- **What it enables:** A RAG-based knowledge agent that indexes existing documentation and provides answers to developer questions about ngx-admin setup, contribution workflow, Nebular component usage, and project conventions. Reduces onboarding time for new contributors.
- **Additional steps:** Index the existing markdown files into a vector store (e.g., Amazon Bedrock Knowledge Base with S3 as the data source). Extend documentation coverage to include architecture decisions and module relationships for richer retrieval.
- **Effort:** Medium

> **Note:** The Data query agent prerequisite (DATA-Q2 = 3 ≥ 2) is technically met, but all data is currently mock/hardcoded in `@core/mock/` services. A data query agent would only become useful once the template connects to a real backend with persistent data stores.

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2 = 2 (< 3, primary); INF-Q1 = 1 (< 3, supporting) |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1 = 1 (< 3); no Dockerfile or container definitions found; no existing Lambda/Fargate/ECS compute |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (not < 3); no commercial database engines detected |
| 4 | Move to Managed Databases | Triggered | Medium | Low | INF-Q2 = 1 (< 3, primary); no managed or self-managed databases defined — infrastructure gap for when backend is added |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 4 (not < 3, archetype-calibrated); no data processing workloads exist |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (< 3, primary); INF-Q11 = 2 (< 3, primary); OPS-Q5 = 1 (< 3, supporting); OPS-Q6 = 1 (< 3, supporting) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in context ("Angular admin dashboard template") |

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:** The application is a single Angular 15 SPA (Single Page Application) bundled as static assets and deployed via rsync. It is a UI monolith with identifiable lazy-loaded modules (`pages-routing.module.ts` defines 10+ lazy-loaded route modules), but remains a single deployable unit. All data is served from in-memory mock services (`@core/mock/`). The `@core/data/` abstract classes define 19 data service interfaces — these represent the seams where a real backend would integrate.

**Compute Model Gaps (INF-Q1):** No compute infrastructure exists. The application is deployed as static files to a remote server via rsync. There is no ECS, EKS, Lambda, Fargate, or even EC2 definition.

**Communication Pattern Gaps (APP-Q3, APP-Q4):** The stateless-utility archetype calibration means synchronous patterns are correct for this frontend template (both score 4). These are not gaps.

**Recommended Approach:**
1. **Containerize the Angular SPA** — Create a Dockerfile using nginx or a Node.js-based server. Host on Amazon EKS (preferred per preferences) with an EKS-managed node group.
2. **Add API Gateway** — Use Amazon API Gateway (preferred per preferences) as the entry point for when the template evolves to connect to backend services.
3. **Consider S3 + CloudFront** — For a static SPA, the most cloud-native approach is hosting static assets on S3 with CloudFront CDN. This is the simplest and most cost-effective cloud-native deployment for frontend-only applications.
4. **Decompose when backend arrives** — When the mock services are replaced with real backend APIs, use the `@core/data/` interface boundaries as natural service decomposition seams.

**Representative AWS Services:** Amazon S3 (static hosting), CloudFront (CDN), API Gateway, EKS (if container-based hosting preferred), Lambda@Edge (for SSR if needed), EventBridge (preferred per preferences, for event-driven patterns when backend is added).

**AWS Prescriptive Guidance:**
- [Strangler Fig Pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model (INF-Q1):** No compute infrastructure defined. The application is a static Angular build deployed via `rsync -r --delete-after dist/. "$REMOTE_URL":"$ADDRESS"` to a remote server (`.github/workflows/demoDeploy.yml`). No Dockerfile, no docker-compose.yml, no Kubernetes manifests found.

**Container Readiness Indicators:**
- ✅ The application builds to static assets (`dist/` directory via `ng build --configuration production`)
- ✅ Dependencies are defined in `package.json` — reproducible builds
- ✅ Environment configuration is externalized via `src/environments/environment.ts` and `environment.prod.ts`
- ✅ No local file system dependencies for runtime data
- ⚠️ No health check endpoint defined (would need to add for container orchestration)

**Recommended Container Orchestration:** Amazon EKS (preferred per preferences). However, for a static frontend SPA, containerization may be over-engineering. Consider this priority order:
1. **S3 + CloudFront** (simplest, lowest cost for static SPA)
2. **EKS with nginx container** (if container orchestration is a portfolio requirement)
3. **AWS App Runner** (managed container hosting, minimal config)

Avoid self-managed Kubernetes (per preferences).

**Migration Approach:** Lift-and-containerize:
1. Create a multi-stage Dockerfile: Stage 1 builds the Angular app (`npm run build:prod`), Stage 2 copies `dist/` into an nginx image.
2. Push to Amazon ECR.
3. Deploy to EKS or App Runner.
4. Replace rsync deployment with container image promotion through CI/CD.

**Representative AWS Services:** Amazon ECR, Amazon EKS (preferred), AWS App Runner, AWS Fargate.

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Low

**Current Database Topology (INF-Q2):** No database infrastructure exists — neither managed nor self-managed. All data is served from in-memory mock services in `@core/mock/`. The 19 data service interfaces in `@core/data/` (UserData, ElectricityData, SmartTableData, etc.) define the data access contracts but are backed entirely by hardcoded TypeScript arrays.

**Context:** This pathway triggers because INF-Q2 = 1 (no databases). While the template currently has no database needs, when the mock services are replaced with real backend APIs, databases will be required. This pathway recommends starting with managed databases from day one rather than introducing self-managed databases.

**Recommended Managed Database Targets:**
- **Amazon DynamoDB** (preferred per preferences) — For dashboard widget data, user activity, traffic analytics. DynamoDB's key-value model maps well to the mock data shapes (user lists, chart data series, time-series metrics).
- **Amazon Aurora** (preferred per preferences) — For relational data needs (smart table data, country orders with joins). Aurora PostgreSQL recommended over Oracle (avoided per preferences).

**Representative AWS Services:** Amazon DynamoDB (preferred), Amazon Aurora (preferred), Amazon ElastiCache (for dashboard caching).

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 1):** No IaC files found in the repository. Zero Terraform, CDK, CloudFormation, or Helm files. All infrastructure is presumably manually created or managed outside the repository.

**Current CI/CD State (INF-Q11 = 2):**
- `.travis.yml` — Runs `npm run lint:ci` and `npm run build:prod` on push to master/demo branches. Uses Node.js 10 (outdated). No test stage.
- `.github/workflows/demoDeploy.yml` — Builds with `npm run build:demo:prod` and deploys via rsync with SSH key. No test stage, no approval gate, no rollback.
- `.github/workflows/docsDeploy.yml` — Deploys documentation to GitHub Pages.

**Deployment Strategy Gaps (OPS-Q5 = 1):** Direct rsync to production server. No blue/green, no canary, no rollback.

**Testing Gaps (OPS-Q6 = 1):** Karma/Jasmine test framework configured in `karma.conf.js` but no test files found. Protractor e2e setup exists (`e2e/` directory) but contains only `tsconfig.e2e.json` — no actual test specs.

**Recommended DevOps Toolchain:**
1. **IaC:** AWS CDK (TypeScript) or Terraform — define all infrastructure (S3, CloudFront, or EKS cluster) as code. CDK TypeScript aligns with the repository's existing TypeScript expertise.
2. **CI/CD:** Consolidate to GitHub Actions (retire Travis CI). Add stages: lint → test → build → deploy-staging → approval → deploy-production.
3. **Deployment Strategy:** S3 + CloudFront with cache invalidation for static hosting. Or EKS with blue/green via CodeDeploy.
4. **Testing:** Add unit tests (Karma/Jasmine is already configured), integration tests, and e2e tests (migrate from Protractor to Cypress or Playwright, as Protractor is deprecated).
5. **Security:** Add `npm audit` and SAST scanning (e.g., Semgrep) to CI pipeline.

**Representative AWS Services:** AWS CDK, CodeBuild, CodePipeline, CodeDeploy, CloudFormation, CloudWatch, X-Ray.

**AWS Prescriptive Guidance:**
- [Getting Started with DevOps on AWS](https://docs.aws.amazon.com/prescriptive-guidance/latest/strategy-devops/welcome.html)

---

## Decomposition Strategy

> **Conditional section** — Included because APP-Q2 = 2 (< 3).

### Context

This is a **frontend Angular SPA template**, not a backend monolith. Traditional microservices decomposition (Strangler Fig, service extraction) does not directly apply to a single-page frontend application. However, the template's architecture shows identifiable module boundaries that can guide evolution toward a more modular, potentially micro-frontend architecture when the application grows beyond a template.

**Current module structure** (from `pages-routing.module.ts`):
- `dashboard` — IoT dashboard with 10+ widget components
- `e-commerce` — E-commerce dashboard with charts, maps, analytics
- `layout` — Layout showcase (tabs, accordion, stepper, lists)
- `forms` — Form input examples
- `ui-features` — Typography, icons, grid, search
- `modal-overlays` — Dialogs, tooltips, popovers, windows
- `extra-components` — Calendar, chat, progress bars, spinners
- `maps` — Google Maps, Leaflet, search map
- `charts` — Chart.js, D3, ECharts
- `editors` — CKEditor, TinyMCE
- `tables` — Smart table, tree grid
- `miscellaneous` — 404 page

### Recommended Approach: Conditional / Adaptive

| Approach | Description | When to Use | Level of Effort | Recommendation |
|----------|-------------|-------------|-----------------|----------------|
| **Conditional / Adaptive** | Containerize the SPA as-is (or host on S3 + CloudFront). When the template evolves to connect to real backend services, selectively extract high-value modules as independently deployable micro-frontends using Module Federation or separate SPA builds. | ✅ **Current situation** — APP-Q2 = 2, frontend-only, limited team capacity assumed (P2 priority, minimal maintenance repo state). | **Low to Medium** — Containerization or S3 hosting in 1-2 weeks. Selective extraction over 3-12 months as needed. | ✅ **Recommended.** Lowest risk path. Get cloud-native hosting first, decompose later as needs arise. |
| **Strangler Fig (Parallel Track)** | Extract individual page modules (e.g., e-commerce dashboard, IoT dashboard) as separate micro-frontends while keeping the shell running. Use Module Federation to compose them at runtime. | When specific dashboard modules need independent deployment cycles, separate team ownership, or different technology stacks. | **Medium to High** — 6-12 months. Requires Module Federation setup, shared shell architecture, and per-module CI/CD. | Viable but premature for a template in minimal maintenance mode. |
| **Big-Bang Rewrite** | Rewrite the entire dashboard as separate micro-frontends from scratch. | Almost never applicable for a frontend template. | **Very High** — Not recommended. | ⚠️ **Not recommended.** No justification for a rewrite of a functional template. |

### Pattern Recommendations

| Pattern | Purpose | Application to This Frontend |
|---------|---------|------------------------------|
| **Anti-corruption Layer (ACL)** | Isolate new backend service integrations from the existing mock data contracts. | When replacing `@core/mock/` services with real API clients, wrap the API layer in an ACL so the `@core/data/` interfaces remain stable. Components consuming data continue to use the same abstract classes. |
| **Hexagonal Architecture** | Structure each module with clear boundaries between UI logic, data access, and external integrations. | The existing `@core/data/` (ports) and `@core/mock/` (adapters) pattern already follows this — extend it by creating real API adapters alongside the mock adapters. |

### Effort Estimation

| Factor | Current Signal | Effort Impact |
|--------|---------------|---------------|
| Module boundaries | Clear — 10+ lazy-loaded route modules with distinct feature areas | Low — boundaries are well-defined |
| Data coupling | Low — all data access goes through `@core/data/` abstract interfaces | Low — clean data contracts |
| Communication patterns | Synchronous, appropriate for frontend (stateless-utility) | N/A — no inter-service communication to refactor |
| CI/CD maturity | Low — no IaC, rsync deployment, no testing | Medium — CI/CD must be built before any decomposition |
| Test coverage | None — no unit or e2e tests found | High — decomposition without tests is risky |

**Calibrated Effort Estimate:** Low for containerization / S3 hosting (1-2 weeks). Medium for CI/CD modernization (2-4 weeks). The decomposition itself is not the bottleneck — the DevOps foundation is.

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute infrastructure is defined in the repository. No Terraform, CDK, CloudFormation, or Helm resources for ECS, EKS, Lambda, Fargate, or EC2. The application is deployed as static files via `rsync` from `.github/workflows/demoDeploy.yml` to a remote server using SSH keys. |
| **Gap** | No managed compute — the application has no cloud-native compute platform. Deployment is a raw file copy to an unmanaged server. |
| **Recommendation** | For a static SPA, host on Amazon S3 with CloudFront CDN (simplest, most cost-effective). If container orchestration is a portfolio requirement, containerize with nginx and deploy to Amazon EKS (preferred per preferences). Define compute infrastructure in IaC (CDK TypeScript recommended). |
| **Evidence** | `.github/workflows/demoDeploy.yml` (rsync deployment), absence of `*.tf`, `cdk.json`, `template.yaml`, `Dockerfile`, `Chart.yaml` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database infrastructure found — no `aws_rds_*`, `aws_dynamodb_*`, or any database resource definitions in IaC (no IaC exists). No database connection strings in source code. All data is served from in-memory mock services in `@core/mock/`. The 19 data service interfaces in `@core/data/` are backed entirely by hardcoded TypeScript arrays. |
| **Gap** | No database infrastructure exists. When the template evolves to use real data, databases will need to be provisioned. |
| **Recommendation** | When adding backend data, start with managed databases from day one. Use Amazon DynamoDB (preferred) for key-value/document data and Amazon Aurora PostgreSQL (preferred) for relational data. Avoid Oracle (per preferences). Define database resources in IaC. |
| **Evidence** | `src/app/@core/mock/users.service.ts` (hardcoded data), `src/app/@core/data/users.ts` (abstract interface), `src/app/@core/core.module.ts` (DATA_SERVICES provider array) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | **Archetype calibration: stateless-utility.** No multi-step workflows exist in this frontend template. The application renders UI components and displays mock data — there are no business workflows, no multi-step operations, no state machines, and no orchestration logic. This is the correct design for a stateless-utility archetype. |
| **Gap** | N/A — no workflows exist, and none are needed for this archetype. |
| **Recommendation** | Dedicated workflow orchestration is not applicable for this stateless-utility frontend template. This does not represent a gap. If the application evolves to include backend workflows (e.g., multi-step data processing), adopt AWS Step Functions at that point. |
| **Evidence** | `src/app/pages/` (UI components only, no workflow logic), `src/app/@core/mock/` (static data providers) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | **Archetype calibration: stateless-utility.** Synchronous HTTP is the correct design for this frontend template. The application makes no downstream service calls, has no message queue consumers, no event handlers, and no streaming infrastructure. All data is rendered from in-memory mock services. Async messaging would add operational complexity without architectural benefit. |
| **Gap** | N/A — synchronous is appropriate for this archetype. |
| **Recommendation** | Adopting async messaging is NOT recommended for this frontend template — it would add operational complexity without architectural benefit. If the application evolves to include backend services with cross-service state propagation, adopt Amazon EventBridge (preferred per preferences). Avoid self-managed Kafka (per preferences). |
| **Evidence** | `package.json` (no SQS/SNS/Kafka/EventBridge SDK dependencies), `src/app/@core/` (no message queue consumers or event handlers) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or NACL definitions found. No IaC exists to define network infrastructure. The deployment target (rsync destination) has no visible network security configuration in the repository. |
| **Gap** | No network security infrastructure defined. The application's hosting environment has no documented network isolation. |
| **Recommendation** | When deploying to AWS, define a VPC with public and private subnets in IaC. For S3 + CloudFront hosting: configure CloudFront with WAF, restrict S3 bucket to CloudFront Origin Access Identity. For EKS hosting: deploy in private subnets with managed networking (VPC endpoints, security groups). |
| **Evidence** | Absence of `*.tf`, `cdk.json`, or CloudFormation templates containing VPC/subnet/SG resources |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, AppSync, ALB, or CloudFront is configured as an entry point. The application is accessed directly via the rsync-deployed server with no managed entry point providing throttling, authentication, or request validation. |
| **Gap** | No managed entry point. Direct server exposure without throttling, caching, or auth enforcement at the edge. |
| **Recommendation** | Add Amazon CloudFront as the CDN and entry point for the static SPA. Configure with WAF for request filtering and rate limiting. If backend APIs are added, use Amazon API Gateway (preferred per preferences) as the API entry point with throttling and authentication. |
| **Evidence** | `.github/workflows/demoDeploy.yml` (rsync to bare server), absence of API Gateway or CloudFront IaC |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration found. No ASG, ECS service auto-scaling, Lambda concurrency limits, DynamoDB capacity scaling, or any scaling policies defined. |
| **Gap** | No scaling capability. The current single-server rsync deployment cannot scale under load. |
| **Recommendation** | For S3 + CloudFront: scaling is inherent (S3 scales automatically, CloudFront distributes at edge). For EKS: configure Horizontal Pod Autoscaler (HPA) with CPU/request-based metrics. Define scaling policies in IaC. |
| **Evidence** | Absence of auto-scaling resources in any configuration file |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration found. No `aws_backup_plan`, no `backup_retention_period`, no S3 versioning, no EBS snapshot policies. The application has no persistent data stores requiring backup (all data is mock), but no disaster recovery plan exists for the hosting infrastructure. |
| **Gap** | No backup or recovery infrastructure. If the deployment server fails, there is no automated recovery. |
| **Recommendation** | For S3 hosting: enable S3 versioning on the static asset bucket. For any future databases: enable automated backups with retention, PITR, and cross-region replication. Document restore procedures. Store build artifacts in S3 with versioning as an alternative to server-based deployment. |
| **Evidence** | Absence of backup-related IaC resources |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ configuration found. No evidence of availability zone distribution for any resource. The rsync deployment targets a single server with no failover. |
| **Gap** | Single point of failure. If the deployment target server fails, the application is unavailable with no automatic recovery. |
| **Recommendation** | For S3 + CloudFront: high availability is inherent (S3 is multi-AZ by default, CloudFront distributes globally). For EKS: deploy across 2+ AZs with node groups in multiple subnets. This is the primary reason S3 + CloudFront is recommended for static SPA hosting. |
| **Evidence** | `.github/workflows/demoDeploy.yml` (single rsync target), absence of multi-AZ IaC configuration |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero IaC files found in the repository. No Terraform (`.tf`), CDK (`cdk.json`), CloudFormation (`template.yaml`), Helm (`Chart.yaml`), Kustomize (`kustomization.yaml`), or Ansible files. All infrastructure is created and managed outside the repository (ClickOps or undocumented processes). |
| **Gap** | 0% IaC coverage. Infrastructure is entirely manual and not version-controlled. |
| **Recommendation** | Adopt IaC for all infrastructure. AWS CDK with TypeScript is recommended — it aligns with the existing TypeScript codebase and enables type-safe infrastructure definitions. Start with the hosting infrastructure (S3 bucket, CloudFront distribution, or EKS cluster) and CI/CD pipeline resources. |
| **Evidence** | Full repository scan — no `*.tf`, `cdk.json`, `template.yaml`, `Chart.yaml`, `kustomization.yaml`, or Ansible playbook files found |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Two CI/CD systems are partially configured: (1) **Travis CI** (`.travis.yml`) — runs `npm run lint:ci` and `npm run build:prod` on push to master/demo branches, using Node.js 10 (significantly outdated). (2) **GitHub Actions** (`.github/workflows/demoDeploy.yml`) — builds and deploys via rsync with SSH key on push to demo branch. A separate workflow (`.github/workflows/docsDeploy.yml`) deploys documentation. Build is automated but deployment is semi-manual (no approval gate, no test stage, no rollback). |
| **Gap** | No automated testing in the deployment pipeline. No rollback mechanism. Node.js 10 in Travis CI is 4+ major versions behind. Two competing CI systems (Travis CI and GitHub Actions) with no unified pipeline. |
| **Recommendation** | Consolidate to GitHub Actions. Retire Travis CI. Build a unified pipeline: lint → unit test → build → deploy-to-staging → approval gate → deploy-to-production. Add `npm audit` for dependency scanning. Implement automated rollback (e.g., CloudFront cache invalidation to previous version, or EKS rollback). |
| **Evidence** | `.travis.yml`, `.github/workflows/demoDeploy.yml`, `.github/workflows/docsDeploy.yml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The application is written in **TypeScript** (~4.9.5) with Angular 15. TypeScript has first-class AWS SDK coverage (`@aws-sdk/*` packages), broad cloud-native tooling (CDK, Lambda, Amplify), and a mature framework ecosystem. The project also uses SCSS for styling and HTML for templates. |
| **Gap** | No gap — TypeScript is a Tier 1 language for AWS cloud-native development. |
| **Recommendation** | Continue with TypeScript. When adding AWS infrastructure, use AWS CDK for TypeScript to maintain a single-language codebase for both application and infrastructure code. |
| **Evidence** | `package.json` (`"typescript": "~4.9.5"`), `tsconfig.json` (target ES2022), `src/app/**/*.ts` (all source files) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application is a **single deployable unit** — a single Angular SPA that builds to one `dist/` bundle. However, it has identifiable module boundaries: `pages-routing.module.ts` defines 10+ lazy-loaded route modules (dashboard, e-commerce, charts, forms, maps, tables, etc.), and the `@core/data/` and `@core/mock/` layers provide clean data abstraction. There are no circular dependencies between page modules — each lazy-loaded module is self-contained with its own routing module and component tree. The shared dependency surface is limited to `@core/` (data services) and `@theme/` (layout/styling). |
| **Gap** | Single deployable unit with shared database schema patterns (all mock services share the same in-memory data layer). While module boundaries are clear, all modules are bundled into one build artifact with no independent deployment capability. |
| **Recommendation** | For a frontend template, this is an expected architecture. The clean module boundaries are a strength. When the application grows, consider Angular Module Federation for micro-frontend decomposition. See the Decomposition Strategy section for detailed approach options. |
| **Evidence** | `src/app/pages/pages-routing.module.ts` (10+ lazy-loaded modules), `src/app/@core/data/` (19 abstract data interfaces), `src/app/@core/mock/` (19 mock service implementations), `angular.json` (single build output to `dist/`) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | **Archetype calibration: stateless-utility.** Synchronous request/response is the correct design for this frontend template. The application makes no inter-service calls — all data comes from in-memory mock services returned as RxJS Observables via `observableOf()`. There is no HTTP client usage, no REST API calls, no gRPC stubs, and no message publishing patterns. The only external communication is the Google Analytics `ga()` call in `analytics.service.ts`, which is fire-and-forget. |
| **Gap** | N/A — synchronous is the correct design for this archetype. |
| **Recommendation** | Async communication is NOT recommended for this frontend template. When the mock services are replaced with real API clients (using Angular's `HttpClient`), implement appropriate patterns: retry logic, circuit breakers (e.g., via RxJS operators), and error handling. If the backend uses EventBridge (preferred), the frontend can consume events via WebSocket or SSE for real-time dashboard updates. |
| **Evidence** | `src/app/@core/mock/users.service.ts` (returns `observableOf()` with hardcoded data), `src/app/@core/utils/analytics.service.ts` (only external call — `ga()` fire-and-forget), `package.json` (no HTTP client libraries beyond Angular's built-in `HttpClientModule`) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | **Archetype calibration: stateless-utility.** No operations exceed 30 seconds. All data rendering is instantaneous from in-memory mock data. The `NbDummyAuthStrategy` in `core.module.ts` has a simulated 3-second delay (`delay: 3000`) for login, which is well under 30 seconds and is a deliberate UX simulation. No API calls, no background processing, no long-running computations. |
| **Gap** | N/A — no long-running operations exist, and none are expected for this archetype. |
| **Recommendation** | Async job infrastructure is not applicable for the current surface. If the application evolves to include long-running operations (e.g., report generation, data export), implement async patterns with status polling (e.g., POST to initiate → GET to check status). |
| **Evidence** | `src/app/@core/core.module.ts` (`NbDummyAuthStrategy.setup({ delay: 3000 })`), `src/app/@core/mock/` (all services return synchronous `observableOf()`) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy exists. The application does not expose any API endpoints — it is a frontend-only SPA. The Angular routes use paths like `/pages/dashboard`, `/auth/login` with no versioning in URL structure. The `@core/data/` interfaces define data contracts but without version annotations. |
| **Gap** | No API versioning. When the template connects to backend APIs, there is no versioning strategy to manage breaking changes. |
| **Recommendation** | Define a versioning strategy before connecting to backend services. For the frontend's API consumption layer: version API client modules (e.g., `api/v1/`, `api/v2/`). For any backend APIs created: use URL path versioning (`/v1/users`, `/v2/users`) with Amazon API Gateway (preferred) managing version routing. |
| **Evidence** | `src/app/app-routing.module.ts` (no versioned routes), `src/app/@core/data/` (unversioned interfaces) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No service discovery mechanism present. The application has no service-to-service communication — all data is from local mock services. The only external endpoint reference is the Google Maps API key hardcoded in `app.module.ts`. No environment variables for service endpoints, no service registry, no API catalog. |
| **Gap** | No service discovery. When the template connects to backend services, service endpoints will need to be managed. |
| **Recommendation** | When adding backend service integration, use environment-specific configuration (Angular environment files) for service endpoints at minimum. For production: configure Amazon API Gateway (preferred) as a unified API surface that abstracts backend service locations from the frontend. |
| **Evidence** | `src/app/app.module.ts` (hardcoded Google Maps API key), `src/environments/environment.ts` (only `production: false` flag, no service URLs) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No unstructured data storage exists. The application has static assets (images in `src/assets/images/`, GeoJSON in `src/assets/leaflet-countries/countries.geo.json`, map data in `src/assets/map/world.json`) served as bundled files from the `dist/` directory. There is no S3, EFS, or any managed object storage. All data is embedded in the application build. |
| **Gap** | No managed object storage. Static assets and data files are bundled with the application rather than stored in accessible, managed storage. |
| **Recommendation** | Move static assets and data files (images, GeoJSON, map data) to Amazon S3. Serve via CloudFront CDN for better caching, reduced bundle size, and independent asset management. This is a quick win that reduces the Angular build size and enables asset updates without redeployment. |
| **Evidence** | `src/assets/images/` (21 image files), `src/assets/leaflet-countries/countries.geo.json`, `src/assets/map/world.json`, `src/assets/data/news.json` |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The `@core/data/` directory contains 19 abstract class definitions that serve as data service interfaces (e.g., `UserData`, `ElectricityData`, `SmartTableData`). The `@core/mock/` directory contains corresponding concrete implementations (e.g., `UserService extends UserData`). All data services are registered via Angular's dependency injection in `core.module.ts` using the `DATA_SERVICES` array with `{ provide: UserData, useClass: UserService }` pattern. This is a clean, centralized data access pattern — components consume abstract interfaces and are decoupled from the data source. |
| **Gap** | Minor gap: some page-level services access data directly without going through the `@core/data/` interface layer (e.g., `country-orders-map.service.ts` in the e-commerce module contains its own data). The abstraction is good but not 100% enforced. |
| **Recommendation** | Maintain and extend this pattern when adding real API backends. Replace `@core/mock/` implementations with `@core/api/` implementations that call real HTTP endpoints, while keeping the `@core/data/` interfaces unchanged. This is the Anti-corruption Layer pattern already in place. |
| **Evidence** | `src/app/@core/data/users.ts` (abstract `UserData` class), `src/app/@core/mock/users.service.ts` (`UserService extends UserData`), `src/app/@core/core.module.ts` (`DATA_SERVICES` array with 19 provider mappings) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database infrastructure exists — no engine versions to evaluate. No `aws_rds_instance`, no `aws_docdb_cluster`, no database engine definitions in IaC (no IaC exists). No database connection strings or driver configurations in source code. No SQL migration files. |
| **Gap** | No database engine version management because no databases exist. When databases are introduced, engine version pinning and EOL tracking must be established from day one. |
| **Recommendation** | When adding databases, explicitly pin engine versions in IaC (e.g., `engine_version = "15.4"` for Aurora PostgreSQL). Establish a version update procedure covering downtime windows, rollback, and risk acknowledgment. Track engine EOL dates and plan upgrades proactively. |
| **Evidence** | Full repository scan — no database-related IaC, migration files, or connection configurations found |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs. The application has no database at all — all business logic (data filtering, transformation, formatting) is in the TypeScript application layer within `@core/mock/` services and page-level components. No `.sql` files found. No ORM configurations. No raw SQL execution patterns. |
| **Gap** | No gap — all logic is in the application layer, which is the ideal state for database portability. |
| **Recommendation** | Maintain this pattern when adding databases. Keep business logic in the application layer. Use an ORM (e.g., TypeORM, Prisma) for data access rather than stored procedures. This ensures database engine portability and avoids vendor lock-in. |
| **Evidence** | Full repository scan — no `.sql` files, no `CREATE PROCEDURE`/`CREATE TRIGGER`/`CREATE FUNCTION` patterns, no ORM configuration |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging found. No `aws_cloudtrail` in IaC (no IaC exists). No application-level audit logging configured. The only logging-related code is the Google Analytics `AnalyticsService` which tracks page views and events but is disabled by default (`this.enabled = false`). |
| **Gap** | No audit logging. No ability to trace user actions, API calls, or infrastructure changes. |
| **Recommendation** | When deploying to AWS, enable CloudTrail with log file validation and immutable storage (S3 Object Lock). For the frontend application: implement structured audit logging for user actions (login, data changes) using a centralized logging service. |
| **Evidence** | `src/app/@core/utils/analytics.service.ts` (disabled GA tracking), absence of CloudTrail IaC |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No KMS keys, no encryption configuration found. No `aws_kms_key` resources, no `kms_key_id` on any data store (no data stores exist). The application has no persistent data requiring encryption — all data is mock/hardcoded. |
| **Gap** | No encryption at rest configuration. When data stores are added, encryption must be configured from day one. |
| **Recommendation** | When deploying to AWS with data stores: enable encryption at rest on all S3 buckets (SSE-KMS with customer-managed keys), RDS/Aurora instances, DynamoDB tables, and any other data stores. Configure key rotation policies. Use AWS-managed keys as a minimum, customer-managed keys for sensitive data. |
| **Evidence** | Full repository scan — no KMS or encryption configuration found |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application uses `NbDummyAuthStrategy` from `@nebular/auth` configured in `core.module.ts`. This is a demo/mock authentication strategy that accepts any credentials with a simulated 3-second delay — it does not validate credentials against any backend service. The auth module supports login, register, logout, request-password, and reset-password routes (`app-routing.module.ts`) but all are backed by the dummy strategy. |
| **Gap** | No real authentication. The dummy auth strategy provides no security — any credentials are accepted. No OAuth2, JWT, API keys, or token validation. |
| **Recommendation** | Replace `NbDummyAuthStrategy` with a real authentication strategy. Use Amazon Cognito with `NbOAuth2AuthStrategy` or `NbPasswordAuthStrategy` backed by Cognito User Pools. This provides JWT-based authentication, user management, and MFA out of the box. Nebular's auth module already supports OAuth2 flows. |
| **Evidence** | `src/app/@core/core.module.ts` (`NbDummyAuthStrategy.setup({ name: 'email', delay: 3000 })`), `src/app/app-routing.module.ts` (auth routes using Nebular components) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity provider integration. The `NbDummyAuthStrategy` does not connect to any external IdP. The `NbSimpleRoleProvider` in `core.module.ts` returns a hardcoded `'guest'` role for all users. No OIDC, SAML, or federation configuration found. Social login links (GitHub, Facebook, Twitter) are configured in the auth forms but are non-functional — they link to Akveo's social pages, not OAuth flows. |
| **Gap** | No external identity provider. Authentication is entirely self-contained (and mock). No SSO capability. |
| **Recommendation** | Integrate with Amazon Cognito as the centralized IdP. Configure OIDC federation for SSO. Replace the hardcoded `NbSimpleRoleProvider` with a Cognito-backed role provider that reads roles from JWT claims. If organizational SSO is needed, configure Cognito with SAML federation to corporate IdPs (Okta, Azure AD). |
| **Evidence** | `src/app/@core/core.module.ts` (`NbSimpleRoleProvider` returning `observableOf('guest')`, social links pointing to Akveo pages) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | **Hardcoded API key detected.** A Google Maps API key is hardcoded directly in `src/app/app.module.ts`: `messageGoogleMapKey: 'AIzaSyA_wNuCzia92MAmdLRzmqitRGvCF7wCZPY'`. In the GitHub Actions workflow (`.github/workflows/demoDeploy.yml`), SSH keys and remote URLs are managed via GitHub Secrets (`secrets.SSH_KEY`, `secrets.KNOWN_HOSTS`, `secrets.REMOTE_URL`), which is better practice, but the Google Maps key in source code is committed to version control. No AWS Secrets Manager or HashiCorp Vault usage. |
| **Gap** | API key hardcoded in source code and committed to version control. No secrets management system in use. |
| **Recommendation** | Move the Google Maps API key to environment configuration (Angular environment files) at minimum, or to AWS Secrets Manager / SSM Parameter Store for production. Restrict the API key in Google Cloud Console (HTTP referrer restrictions). Rotate the exposed key immediately. For all future secrets: use AWS Secrets Manager with automated rotation. |
| **Evidence** | `src/app/app.module.ts` (line with `messageGoogleMapKey: 'AIzaSyA_wNuCzia92MAmdLRzmqitRGvCF7wCZPY'`), `.github/workflows/demoDeploy.yml` (GitHub Secrets for SSH_KEY, REMOTE_URL) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute hardening or patching strategy found. No SSM Patch Manager, no AWS Inspector, no Snyk, no hardened AMI references. The deployment target server's patching state is unknown and not managed through the repository. No vulnerability scanning of any kind is configured. |
| **Gap** | No patching strategy. The deployment server's security posture is not managed in code. No vulnerability scanning for the compute environment. |
| **Recommendation** | For S3 + CloudFront hosting: compute hardening is less relevant (no servers to patch). For EKS hosting: use Bottlerocket AMIs (hardened, minimal OS), enable ECR image scanning, and configure AWS Inspector for container vulnerability scanning. Add dependency vulnerability scanning (npm audit, Snyk) to CI pipeline regardless of hosting model. |
| **Evidence** | Absence of SSM, Inspector, or vulnerability scanning configuration |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SAST, DAST, or dependency vulnerability scanning tools are integrated into any CI/CD pipeline. Travis CI runs only lint + build. GitHub Actions runs only build + rsync deploy. No Dependabot configuration (no `.github/dependabot.yml`). No `npm audit` in any pipeline. No SonarQube, Semgrep, CodeGuru, or Snyk. The only code quality tool is ESLint (`.eslintrc.json`) which checks code style, not security. |
| **Gap** | Zero security scanning in CI/CD. Known vulnerabilities in the 40+ npm dependencies are not detected. No security gates block deployments with critical vulnerabilities. |
| **Recommendation** | Immediately add: (1) `npm audit --audit-level=high` as a CI step to catch known dependency vulnerabilities. (2) Dependabot configuration for automated dependency updates. (3) SAST tool (Semgrep or SonarQube) for code-level security scanning. (4) Consider GitHub Advanced Security for secret scanning and code scanning. These are low-effort, high-impact additions to the existing GitHub Actions workflow. |
| **Evidence** | `.travis.yml` (lint + build only), `.github/workflows/demoDeploy.yml` (build + rsync only), `.eslintrc.json` (style linting only), absence of `.github/dependabot.yml` |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumented. No OpenTelemetry SDK, no X-Ray instrumentation, no trace ID propagation. The `package.json` contains no tracing-related dependencies. The application makes no inter-service calls, so cross-service tracing is not currently needed, but even client-side tracing (performance monitoring, user journey tracking) is absent. |
| **Gap** | No tracing of any kind. When the application connects to backend services, there will be no visibility into request flows or latency. |
| **Recommendation** | Add client-side performance monitoring using AWS X-Ray SDK for JavaScript or OpenTelemetry browser instrumentation. When backend services are added, propagate trace IDs (W3C `traceparent` header) through all HTTP calls. For EKS deployment: enable X-Ray daemon sidecar or OpenTelemetry Collector. |
| **Evidence** | `package.json` (no tracing dependencies), absence of OpenTelemetry or X-Ray configuration |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found. No availability, latency, or error rate targets are defined anywhere in the repository. No CloudWatch alarms, no error budget tracking, no SLO dashboards. |
| **Gap** | No formal service level objectives. Without SLOs, there is no way to measure whether the application meets user expectations. |
| **Recommendation** | Define SLOs for the frontend: page load time (p95 < 3s), availability (99.9%), error rate (< 0.1%). When deployed to AWS, implement SLOs using CloudWatch with alarms on CloudFront metrics (4xx/5xx error rates, latency). Track error budgets to guide deployment decisions. |
| **Evidence** | Full repository scan — no SLO definitions, alarms, or error budget configuration found |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application has a Google Analytics integration via `AnalyticsService` (`src/app/@core/utils/analytics.service.ts`). It tracks page views on route changes and custom events via `ga('send', ...)`. However, the analytics service is **disabled by default** (`this.enabled = false`) and there is no mechanism to enable it from configuration. This is infrastructure-only with ad hoc business reporting — the tracking code exists but is inoperative. |
| **Gap** | Analytics code exists but is disabled. No active business metric tracking. No custom CloudWatch metrics. |
| **Recommendation** | Enable the analytics service with a configurable flag from environment configuration. Migrate from legacy Google Analytics (`ga()`) to GA4 or a cloud-native solution (Amazon Pinpoint for user analytics, CloudWatch custom metrics for business KPIs). Track dashboard usage patterns, feature adoption, and user engagement metrics. |
| **Evidence** | `src/app/@core/utils/analytics.service.ts` (`this.enabled = false`, `ga('send', {hitType: 'pageview', ...})`) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configured. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no static threshold alarms, no composite alarms. The application has no monitoring infrastructure of any kind. |
| **Gap** | No alerting. If the application fails, there is no automated notification. Degradation is detected only when users report issues. |
| **Recommendation** | When deployed to AWS: configure CloudWatch alarms on CloudFront error rates (4xx, 5xx) and origin latency. Enable CloudWatch anomaly detection for automatic baseline learning. Set up SNS notifications to on-call channels (PagerDuty, Slack, or OpsGenie). For S3 hosting: monitor S3 request errors and CloudFront cache hit ratio. |
| **Evidence** | Full repository scan — no alerting or monitoring configuration found |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Deployment is a direct rsync to production: `rsync -r --delete-after dist/. "$REMOTE_URL":"$ADDRESS"` (`.github/workflows/demoDeploy.yml`). This replaces all files on the server in a single operation with no staged rollout, no health checks, no traffic shifting, and no rollback capability. If the rsync fails midway, the server may be in an inconsistent state. |
| **Gap** | Direct-to-production deployment with no staged rollout. No blue/green, no canary, no rolling updates. No rollback mechanism. |
| **Recommendation** | For S3 + CloudFront: deploy to S3 and create a CloudFront invalidation. Use versioned S3 objects for instant rollback. For EKS: use CodeDeploy with blue/green deployment strategy. Add health checks and automatic rollback on failure. Consider feature flags (LaunchDarkly or AWS AppConfig) for gradual feature rollout. |
| **Evidence** | `.github/workflows/demoDeploy.yml` (`rsync -r --delete-after dist/. ...`) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No integration or e2e tests found. The test infrastructure is configured but empty: Karma/Jasmine is configured in `karma.conf.js` and `src/test.ts`, but no `*.spec.ts` test files exist in the repository. Protractor e2e is configured in `protractor.conf.js` with an `e2e/` directory, but it contains only `tsconfig.e2e.json` and `.eslintrc.json` — no actual test specs. The `package.json` has test scripts (`test`, `test:coverage`, `e2e`) but they would find no tests to run. |
| **Gap** | Zero test coverage. Test infrastructure exists (Karma, Jasmine, Protractor) but no tests are written. This means any change — including module extraction or backend integration — carries high regression risk. |
| **Recommendation** | Prioritize writing tests before any modernization work. Start with component unit tests for critical dashboard components using Karma/Jasmine. Migrate from Protractor (deprecated) to Cypress or Playwright for e2e tests. Add integration tests that validate data service interfaces (`@core/data/` contracts). Run all tests in the CI pipeline before deployment. |
| **Evidence** | `karma.conf.js` (configured but no spec files), `e2e/` (tsconfig only), `protractor.conf.js` (configured but no specs), `package.json` (test scripts defined but no tests exist) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, no incident response automation, no self-healing patterns. No Systems Manager Automation documents, no Lambda-based remediation, no incident workflow definitions. No markdown runbooks in the repository. |
| **Gap** | No incident response capability. Incidents are handled entirely ad hoc. |
| **Recommendation** | Create runbooks for common incidents: deployment failure, server unreachable, high error rate. Start with markdown runbooks in the repository. When deployed to AWS: use Systems Manager Automation documents for automated remediation (e.g., CloudFront cache invalidation on error spike, S3 deployment rollback). |
| **Evidence** | Full repository scan — no runbook files, no SSM Automation documents, no incident response configuration |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership defined. No CODEOWNERS file referencing observability assets. No per-service dashboards. No alarms with named owners. No SLO definitions with team attribution. No team tags on any resources. |
| **Gap** | No observability ownership. Monitoring responsibility is undefined. |
| **Recommendation** | Create a CODEOWNERS file that assigns observability configuration ownership. When deployed to AWS: create a CloudWatch dashboard for the frontend application with key metrics (error rates, latency, cache hit ratio). Assign alarm owners. Define SLOs with team attribution. |
| **Evidence** | Absence of `CODEOWNERS`, absence of dashboard or alarm configurations |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tags found. No IaC exists, so there are no resources to tag. No `default_tags` in Terraform provider, no tag definitions in CDK, no `required-tags` Config rules. |
| **Gap** | No tagging governance. When AWS resources are created, there is no standard for cost allocation, ownership, or environment identification. |
| **Recommendation** | Establish a tagging standard before creating AWS resources. Required tags should include: `Environment` (dev/staging/prod), `Project` (ngx-admin), `Owner` (team name), `CostCenter`. Implement tags in IaC using `default_tags` (Terraform) or CDK Tags (CDK). Enforce with AWS Organizations Tag Policies and AWS Config rules. |
| **Evidence** | Absence of any IaC or resource configuration with tags |

---

## Learning Materials

The following learning resources are mapped to the triggered pathways:

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
| `package.json` | APP-Q1, INF-Q4, INF-Q11, OPS-Q1, OPS-Q6 | Dependencies (Angular 15, TypeScript 4.9.5, Nebular 11), scripts (lint, build, test), no tracing/security dependencies |
| `angular.json` | APP-Q2, INF-Q1 | Single build output to `dist/`, single project configuration |
| `tsconfig.json` | APP-Q1 | TypeScript target ES2022, module es2020 |
| `.travis.yml` | INF-Q11, SEC-Q7, OPS-Q6 | Node.js 10, lint + build only, no test/deploy stage |
| `.github/workflows/demoDeploy.yml` | INF-Q1, INF-Q11, OPS-Q5, SEC-Q5 | rsync deployment, SSH key from secrets, no test/approval/rollback |
| `.github/workflows/docsDeploy.yml` | INF-Q11 | Documentation deployment to GitHub Pages |
| `src/app/app.module.ts` | SEC-Q5, APP-Q6 | Hardcoded Google Maps API key (`AIzaSyA_wNuCzia92MAmdLRzmqitRGvCF7wCZPY`), module imports |
| `src/app/app-routing.module.ts` | APP-Q2, APP-Q5, SEC-Q3 | Root routing with lazy-loaded pages module, auth routes |
| `src/app/@core/core.module.ts` | SEC-Q3, SEC-Q4, DATA-Q2, INF-Q3, APP-Q4 | NbDummyAuthStrategy, NbSimpleRoleProvider, DATA_SERVICES array (19 providers) |
| `src/app/@core/data/users.ts` | DATA-Q2 | Abstract `UserData` class — data interface pattern |
| `src/app/@core/mock/users.service.ts` | APP-Q3, DATA-Q2, INF-Q2 | Mock service with hardcoded data using `observableOf()` |
| `src/app/@core/utils/analytics.service.ts` | OPS-Q3, SEC-Q1 | Google Analytics integration (disabled by default) |
| `src/app/pages/pages-routing.module.ts` | APP-Q2, Decomposition Strategy | 10+ lazy-loaded route modules defining feature boundaries |
| `src/app/@core/data/` | DATA-Q2, DATA-Q4, APP-Q2 | 19 abstract data service interfaces |
| `src/app/@core/mock/` | DATA-Q2, INF-Q2, INF-Q3, APP-Q3 | 19 mock service implementations with hardcoded data |
| `src/environments/environment.ts` | APP-Q6 | Environment config — only `production: false`, no service URLs |
| `src/environments/environment.prod.ts` | APP-Q6 | Production environment config — only `production: true` |
| `karma.conf.js` | OPS-Q6 | Test runner configured (Karma/Jasmine/Chrome) but no test files |
| `protractor.conf.js` | OPS-Q6 | E2e test runner configured but no test specs |
| `e2e/` | OPS-Q6 | E2e directory — contains only `tsconfig.e2e.json`, no specs |
| `.eslintrc.json` | SEC-Q7 | ESLint config — Angular-specific linting rules, no security rules |
| `README.md` | Quick Agent Wins | Project documentation — setup, features, themes |
| `CONTRIBUTING.md` | Quick Agent Wins | Contribution guidelines (222 lines) |
| `DEV_DOCS.md` | Quick Agent Wins | Developer docs pointer to Nebular |
| `src/assets/images/` | DATA-Q1 | 21 static image files bundled with application |
| `src/assets/leaflet-countries/countries.geo.json` | DATA-Q1 | GeoJSON data bundled with application |
| `src/assets/map/world.json` | DATA-Q1 | Map data bundled with application |
| `src/assets/data/news.json` | DATA-Q1 | News data bundled with application |
| `src/app/pages/e-commerce/country-orders/map/country-orders-map.service.ts` | DATA-Q2 | Page-level service bypassing `@core/data/` abstraction |
