# Modernization Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | angular-realworld |
| **Date** | 2025-07-15 |
| **TD Version** | modernization-assessment (version ID not available via CLI) |
| **Repo Type** | application |
| **Service Archetype** | stateless-utility (auto-detected) |
| **Priority** | P2 |
| **Tags** | typescript, frontend, angular |
| **Context** | Angular reference implementation of the RealWorld spec. |
| **Preferences** | Prefer: eks, aurora, dynamodb, api-gateway, eventbridge, bedrock · Avoid: self-managed-kafka, self-managed-kubernetes, oracle |
| **Surface Flags** | has_persistent_data_store=false, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=false, has_multi_instance_deployment=false |
| **Overall Score** | **1.84 / 4.0** |

**Archetype Justification**: No database connections, no owned persistent state, no message queue consumers, and all operations are synchronous HTTP calls to a single external backend API (`https://api.realworld.show/api`). The application is a client-side Angular SPA that renders UI and delegates all data persistence and business logic to the RealWorld backend. Classified as `stateless-utility`.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.17 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 2.50 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 2.50 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.67 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.38 / 4.0 | ❌ Not Present |
| **Overall** | **1.84 / 4.0** | **🟠 Needs Work** |

> **Note:** 9 questions were excluded from scoring as Not Evaluated (archetype-N/A) due to surface-flag gates or archetype calibration. This frontend SPA has no deployed infrastructure, no database, no data-at-rest surface, and no server-side API endpoints — those evaluation surfaces genuinely do not exist for this codebase. The scored questions reflect the areas where this repository *does* have evaluable content.

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: IaC Coverage | 1 | No infrastructure-as-code found in the repository. All infrastructure (if any) is manually created. | Blocks reproducible deployments, disaster recovery, and environment consistency. Triggers Move to Modern DevOps pathway. |
| 2 | INF-Q1: Managed Compute | 1 | No compute resources defined — no ECS, EKS, Lambda, Fargate, or EC2 in IaC. Static build output is zipped as a GitHub release. | The application has no defined deployment target on AWS. Hosting on S3+CloudFront or ECS would provide scalable, managed serving. Triggers Move to Containers pathway. |
| 3 | APP-Q6: Service Discovery | 1 | Backend API endpoint is hardcoded as `https://api.realworld.show/api` in `api.interceptor.ts`. No environment-based configuration or service discovery. | Hardcoded endpoints create deployment coupling — cannot switch backends for dev/staging/production without code changes. |
| 4 | SEC-Q1: Audit Logging | 1 | No CloudTrail or audit logging configuration. No IaC to define any AWS logging resources. | No audit trail for security events, compliance gaps, and inability to perform forensic analysis. |
| 5 | INF-Q11: CI/CD Automation | 2 | CI/CD pipelines exist for build and test (GitHub Actions) but deployment is limited to creating a GitHub release zip. No automated deployment to infrastructure. | Manual deployment to hosting infrastructure introduces inconsistency and slows release cycles. Triggers Move to Modern DevOps pathway. |

---

## Quick Agent Wins

### API-aware Agent

- **Prerequisite:** APP-Q5 >= 2 ✅ (Score 2) and structured JSON responses detected. The OpenAPI 3.1.0 spec exists at `realworld/specs/api/openapi.yml` with full schema definitions for all endpoints (articles, comments, users, profiles, tags).
- **What it enables:** An API-aware agent that discovers and invokes the RealWorld API endpoints as tools — querying articles, managing comments, and performing user operations via natural language.
- **Additional steps:** The OpenAPI spec is comprehensive (version 2.0.0, all CRUD operations documented). An agent could use this spec directly for tool discovery. Consider generating a client SDK from the spec for type-safe agent interactions.
- **Effort:** Low

### DevOps Agent

- **Prerequisite:** INF-Q11 >= 2 ✅ (Score 2). GitHub Actions CI/CD pipelines exist for build (`deploy.yml`), e2e tests (`playwright.yml`), format checks (`lint.yml`), and security tests (`security-tests.yml`).
- **What it enables:** A DevOps agent that triggers builds, checks workflow status, monitors test results, and manages GitHub releases via the GitHub Actions API.
- **Additional steps:** The current pipeline has no deployment-to-infrastructure stage. Adding a deployment target (S3+CloudFront or ECS) would expand the agent's operational surface.
- **Effort:** Low

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository. `README.md` provides project overview, functionality breakdown, and getting-started guide. `CLAUDE.md` provides development commands and code style guidance. `e2e/SELECTORS.md` provides test selector documentation. The OpenAPI spec at `realworld/specs/api/openapi.yml` provides comprehensive API documentation.
- **What it enables:** A RAG-based knowledge agent using existing documentation as a knowledge base for answering developer questions about the project structure, API, and development workflows.
- **Additional steps:** Index the README, CLAUDE.md, OpenAPI spec, and inline code comments (which are extensive — e.g., `user.service.ts` has thorough JSDoc). Consider adding architecture decision records (ADRs) to enrich the knowledge base.
- **Effort:** Low

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 (modular monolith with clear boundaries). Primary trigger not met. |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1 = 1 (no compute defined), no container definitions found. No existing Lambda/Fargate/ECS — guard does not prevent triggering. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (no stored procedures). No commercial database engines detected. Primary trigger not met. |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = Not Evaluated (no database exists). No database to migrate. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = Not Evaluated. No data processing workloads exist. Contextual guard prevents triggering. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (no IaC). INF-Q11 = 2 (partial CI/CD, no deployment automation). OPS-Q5 = 1 (no deployment strategy). |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in context ("Angular reference implementation of the RealWorld spec." contains none of the 17 AI signal terms). |

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model:** No compute resources are defined in the repository. The Angular SPA builds to a static directory (`dist/angular-conduit/browser/`) which is zipped and uploaded as a GitHub release artifact. There is no IaC defining how or where this static content is served.

**Container Readiness Indicators:**
- The application is a static Angular SPA build — it can be served from any static file server or CDN
- No server-side runtime dependencies (no SSR, no Express server)
- Build process is well-defined: `bun run build` produces the static output
- No Dockerfile exists currently

**Recommendation:**

For a static Angular SPA, containerization is one of two viable paths:

1. **S3 + CloudFront (Preferred for SPAs):** Host the static build output in an S3 bucket with CloudFront as the CDN. This is the most cost-effective and operationally simple approach for frontend SPAs. Use API Gateway (preferred per technology preferences) as the entry point for API routing.

2. **EKS with NGINX container (Preferred if EKS already exists):** Per technology preferences (`prefer: eks`), if an EKS cluster exists in the portfolio, containerize the SPA with an NGINX Dockerfile and deploy as a Kubernetes service. This provides consistent operational model across services.

**Representative AWS Services:** S3, CloudFront, API Gateway, EKS (preferred), ECR, CodePipeline

**Migration Approach:** Create a Dockerfile with NGINX to serve the static build, or configure S3 static website hosting with CloudFront distribution. Both approaches are well-documented and low-risk for a static SPA.

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 1):** No infrastructure-as-code exists. Zero Terraform, CloudFormation, CDK, Helm, or Kustomize files found. If hosting infrastructure exists for this application, it was created manually.

**Current CI/CD State (INF-Q11 = 2):** GitHub Actions workflows exist for:
- Build and release (`.github/workflows/deploy.yml`) — builds the Angular app and creates a GitHub release with a zip artifact
- E2E testing (`.github/workflows/playwright.yml`) — runs Playwright tests on push/PR
- Format checking (`.github/workflows/lint.yml`) — runs Prettier format check
- Security testing (`.github/workflows/security-tests.yml`) — runs XSS security tests

However, the "deployment" is limited to creating a GitHub release zip. There is no automated deployment to any hosting infrastructure.

**Deployment Strategy Gaps (OPS-Q5 = 1):** No blue/green, canary, or rolling deployment. The build output is zipped and published as a GitHub release — it is not deployed to any running environment automatically.

**Testing Gaps (OPS-Q6 = 4):** Testing is actually a strength — comprehensive Playwright e2e tests and Vitest unit tests run in CI. This provides a solid foundation for adding deployment automation.

**Recommended DevOps Toolchain:**
1. **IaC:** Define hosting infrastructure with CDK or Terraform — S3 bucket, CloudFront distribution, Route 53 DNS, and API Gateway
2. **CI/CD Enhancement:** Extend the existing GitHub Actions workflows to deploy the static build to S3 after a successful build and test pass
3. **Deployment Strategy:** Implement CloudFront invalidation after S3 upload for instant rollout, or use CloudFront's staged distribution for canary-style rollout

**Representative AWS Services:** CloudFormation/CDK, CodePipeline, CodeBuild, S3, CloudFront, Route 53, CloudWatch

**Links to Guidance:**
- [AWS DevOps on SkillBuilder](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute resources are defined anywhere in the repository. No Terraform (`aws_ecs_*`, `aws_eks_*`, `aws_lambda_*`, `aws_instance`), no CloudFormation, no CDK, no Helm charts, and no Kubernetes manifests were found. The Angular application builds to a static directory (`dist/angular-conduit/browser/`) which is zipped and uploaded as a GitHub release artifact (`.github/workflows/deploy.yml`). There is no definition of where or how this static content is served in production. |
| **Gap** | The application has no compute model defined. Static SPA content requires hosting — either on managed services (S3+CloudFront) or containerized (EKS/ECS with NGINX). Without a defined compute model, the deployment target is unknown. |
| **Recommendation** | Define the hosting infrastructure in IaC. For a static Angular SPA, the recommended approach is S3 static website hosting with CloudFront as the CDN and API Gateway (preferred) as the API entry point. If EKS (preferred) is already available in the portfolio, containerize with NGINX and deploy to the existing cluster. |
| **Evidence** | `.github/workflows/deploy.yml` (line: `cd dist/angular-conduit/browser && zip -r ../../../build.zip .`), `angular.json` (outputPath: `dist/angular-conduit`). No `.tf`, `template.yaml`, `cdk.json`, `Chart.yaml`, `Dockerfile`, or Kubernetes manifests found. |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy a database. The Angular SPA has no database connections, no database drivers in `package.json`, and no database infrastructure in IaC (no IaC exists). All data persistence is delegated to the external RealWorld backend API (`https://api.realworld.show/api`). INF-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `package.json` (no database driver dependencies), `src/app/core/interceptors/api.interceptor.ts` (all data access via HTTP to external API). |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Workflow orchestration is not applicable by design — no multi-step workflows exist for a stateless Angular SPA that delegates all business logic to a backend API. The application's operations are synchronous HTTP requests: GET articles, POST comments, PUT user settings. None of these involve multi-step orchestration within the frontend. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/app/features/article/services/articles.service.ts`, `src/app/features/article/services/comments.service.ts`, `src/app/core/auth/services/user.service.ts` — all operations are single HTTP requests. |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Synchronous HTTP is the correct design for a frontend SPA — the application makes synchronous HTTP requests to the backend API via Angular's `HttpClient` and renders responses in the browser. There is no need for async messaging infrastructure (SQS, SNS, EventBridge, Kafka). Adding async messaging to a frontend SPA would be architectural overhead with no benefit. |
| **Gap** | N/A |
| **Recommendation** | Adopting async messaging is NOT recommended — it would add operational complexity without architectural benefit for this frontend application. |
| **Evidence** | `src/app/core/interceptors/api.interceptor.ts` (all requests are synchronous HTTP), `package.json` (no messaging SDKs). |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or network segmentation definitions found. No IaC exists in the repository to define any network infrastructure. The application makes outbound HTTPS calls to `https://api.realworld.show/api` from the browser — the backend API's network security is outside the scope of this frontend repository. |
| **Gap** | If this SPA is deployed on AWS (e.g., behind CloudFront or in an EKS cluster), no network security configuration exists to govern that deployment. |
| **Recommendation** | When deploying to AWS, define the network layer in IaC: CloudFront with WAF for DDoS protection and bot filtering, or VPC with private subnets if containerized on EKS. For a static SPA served via S3+CloudFront, use CloudFront OAC (Origin Access Control) to restrict S3 access. |
| **Evidence** | No `.tf` files, no CloudFormation templates, no `aws_vpc`, `aws_subnet`, or `aws_security_group` resources found in the repository. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or any managed entry point is defined in IaC. The application itself is a frontend SPA — its API entry point is the external backend at `https://api.realworld.show/api`. However, the SPA itself needs a serving entry point (CloudFront distribution, ALB, or similar) which is not defined. |
| **Gap** | No managed entry point defined for serving the SPA or proxying API requests. |
| **Recommendation** | Define a CloudFront distribution in IaC to serve the static SPA. Configure API Gateway (preferred per technology preferences) as the managed entry point for API routing with throttling, auth, and request validation. |
| **Evidence** | No `aws_api_gateway_*`, `aws_apigatewayv2_*`, `aws_lb_*`, or `aws_cloudfront_distribution` found. |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration found. No `aws_autoscaling_*` or `aws_appautoscaling_*` resources. Since no compute infrastructure is defined, there is nothing to auto-scale. CloudFront and S3 provide inherent auto-scaling for static content serving, but these are not configured. |
| **Gap** | No auto-scaling configured because no infrastructure is defined. |
| **Recommendation** | When infrastructure is defined, ensure auto-scaling is configured. If using S3+CloudFront (inherently scalable), this is handled automatically. If using EKS (preferred), configure Horizontal Pod Autoscaler and Cluster Autoscaler. |
| **Evidence** | No IaC files found in the repository. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no persistent state to back up. The Angular SPA is a stateless frontend — all data is persisted by the backend API. There is no S3 bucket, RDS instance, DynamoDB table, or any data store defined in this repository. INF-Q8 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database resources, no S3 buckets, no persistent storage defined. `has_persistent_data_store=false`, `has_at_rest_data_surface=false`. |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload requiring HA evaluation. No IaC defines compute, no Dockerfile exists, and no deployment manifests are present. The application's HA posture is determined by the hosting infrastructure, which is not defined in this repository. INF-Q9 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `has_deployed_workload=false`. No compute resources, Dockerfiles, or deployment manifests found. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No infrastructure-as-code found in the repository. Zero Terraform files (`.tf`), CloudFormation templates, CDK constructs (`cdk.json`), Helm charts (`Chart.yaml`), or Kustomize overlays (`kustomization.yaml`) exist. If any hosting infrastructure exists for this application (S3 bucket, CloudFront distribution, DNS records), it was created manually or exists in a separate repository. |
| **Gap** | 0% IaC coverage. All infrastructure — if it exists — is manually created (ClickOps). This means infrastructure changes are non-reproducible, error-prone, and cannot be version-controlled or reviewed. |
| **Recommendation** | Define all hosting infrastructure in IaC. Use CDK (TypeScript, matching the application language) or Terraform to define: S3 bucket for static hosting, CloudFront distribution, Route 53 DNS, WAF rules, and CloudWatch alarms. Store IaC in this repository or a dedicated infrastructure repository with cross-references. |
| **Evidence** | `find . -type f \( -name "*.tf" -o -name "cdk.json" -o -name "Chart.yaml" -o -name "kustomization.yaml" \)` returned no results (excluding `node_modules`). |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GitHub Actions CI/CD pipelines exist with 4 workflows: (1) **Build and Release** (`.github/workflows/deploy.yml`) — builds the Angular app with `bun run build`, zips the output, creates a GitHub release, and includes an ATX transform job. (2) **Playwright Tests** (`.github/workflows/playwright.yml`) — runs e2e tests on push/PR. (3) **Format Check** (`.github/workflows/lint.yml`) — runs Prettier format checks. (4) **Security Tests** (`.github/workflows/security-tests.yml`) — runs XSS security tests via Playwright. Build is automated but deployment is limited to creating a GitHub release artifact — there is no automated deployment to hosting infrastructure (no S3 upload, no CloudFront invalidation, no EKS deployment). |
| **Gap** | Build and test automation exists, but deployment automation is absent. The "deploy" step only creates a GitHub release zip — it does not deploy the artifact to any hosting environment. No IaC automation (no `terraform plan/apply` or `cdk deploy` in pipelines). |
| **Recommendation** | Extend the existing GitHub Actions pipeline to include a deployment stage: upload the build artifact to S3, invalidate the CloudFront cache, and optionally trigger a smoke test. Add IaC validation and deployment stages when IaC is introduced (e.g., `cdk diff` on PR, `cdk deploy` on merge to main). |
| **Evidence** | `.github/workflows/deploy.yml`, `.github/workflows/playwright.yml`, `.github/workflows/lint.yml`, `.github/workflows/security-tests.yml`. |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | TypeScript ~5.9.3 with Angular 21.x (the latest major version as of assessment date), targeting ES2022, with strict compiler options enabled (`strict: true`, `noImplicitReturns`, `noFallthroughCasesInSwitch`, `strictTemplates`). Node.js >=20.11.1 required. The framework ecosystem is modern: Angular 21 with zoneless change detection (`provideZonelessChangeDetection()`), standalone components, signal-based state management (`signal()`), and `@rx-angular/template` for reactive patterns. RxJS 7.8.2. Build tooling uses Vite via `@analogjs/vite-plugin-angular` for unit tests. Bun is the package manager. |
| **Gap** | No gaps. This is a fully modern TypeScript/Angular stack at current versions with best-practice configuration. |
| **Recommendation** | No action needed. Continue tracking Angular major releases and TypeScript updates. |
| **Evidence** | `package.json` (Angular 21.1.1/21.2.4, TypeScript ~5.9.3, Node >=20.11.1), `tsconfig.json` (ES2022, strict: true), `src/app/app.config.ts` (`provideZonelessChangeDetection()`). |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Single deployable unit (Angular SPA), but with a well-structured modular architecture: `core/` (auth, interceptors, layout, models), `features/` (article, profile, settings — each with their own services, components, models, and pages), and `shared/` (reusable pipes and components). Lazy-loaded routes (`loadComponent()` and `loadChildren()` in `app.routes.ts`) provide code-splitting at the module level. Each feature module has its own service layer with clear interfaces. No circular dependencies observed — features reference core services but do not cross-reference each other. This is effectively a well-structured modular monolith with clear module boundaries. |
| **Gap** | Minor — the application is a single deployable unit (as expected for a frontend SPA), but the modular structure has some coupling: all features share the same `UserService` from `core/auth`, and the `api.interceptor.ts` applies a single base URL globally. These are appropriate for a frontend SPA and do not represent architectural debt. |
| **Recommendation** | No decomposition needed — this is a frontend SPA, and a single deployable unit is the correct architecture. The modular structure (core/features/shared) is well-organized. If the application grows significantly, consider micro-frontends for independent team ownership, but this is not currently warranted. |
| **Evidence** | `src/app/app.routes.ts` (lazy-loaded routes), `src/app/features/article/`, `src/app/features/profile/`, `src/app/features/settings/`, `src/app/core/`, `src/app/shared/`. |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Synchronous request/response is the correct design for a frontend SPA — the Angular application makes synchronous HTTP requests to the backend API via `HttpClient` and renders the responses in the browser UI. There is no inter-service communication to evaluate (this is a client-side application, not a backend service). The single communication channel (browser → RealWorld API) is inherently synchronous HTTP and this is architecturally correct. |
| **Gap** | N/A |
| **Recommendation** | N/A. Converting to async communication is not applicable for a browser-based SPA. |
| **Evidence** | `src/app/core/interceptors/api.interceptor.ts`, `src/app/features/article/services/articles.service.ts`, `src/app/core/auth/services/user.service.ts` — all use Angular `HttpClient` for synchronous HTTP requests. |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. No operations exceed 30 seconds — not applicable by design. All operations are HTTP requests to the backend API that return in typical API response times (milliseconds to low seconds). The frontend performs no long-running computation, no batch processing, and no file processing. The only potentially variable-latency operation is the initial auth check (`getCurrentUser()` in `app.config.ts`), which has a well-designed exponential backoff retry mechanism for 5XX errors — but this is resilience handling, not a long-running operation. |
| **Gap** | N/A |
| **Recommendation** | N/A. Async job infrastructure is not applicable for this frontend SPA. |
| **Evidence** | `src/app/core/auth/services/user.service.ts` (retry with exponential backoff: 2s → 4s → 8s → 16s cap), `src/app/features/article/services/articles.service.ts` (standard HTTP CRUD). |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The RealWorld API has an OpenAPI 3.1.0 spec at `realworld/specs/api/openapi.yml` with version `2.0.0` in the `info.version` field. However, the Angular application's `api.interceptor.ts` hardcodes the base URL as `https://api.realworld.show/api` with no version segment in the URL path (no `/v1/` or `/v2/`). Individual service methods use relative paths like `/articles`, `/users/login`, `/profiles/` — no versioning is applied at the endpoint level. The OpenAPI spec also uses the unversioned URL as the server: `https://api.realworld.show/api`. |
| **Gap** | No API versioning strategy applied in the request paths. The `info.version: 2.0.0` in the OpenAPI spec indicates a version exists in documentation but is not reflected in the URL structure or headers. If the backend introduces breaking changes, all consumers are affected simultaneously. |
| **Recommendation** | Adopt a versioning strategy. Add version prefix to the API base URL (e.g., `https://api.realworld.show/api/v2`) or use `Accept-Version` headers. Update the `api.interceptor.ts` to include the version, and update the OpenAPI spec server URL to match. |
| **Evidence** | `src/app/core/interceptors/api.interceptor.ts` (`https://api.realworld.show/api`), `realworld/specs/api/openapi.yml` (`info.version: 2.0.0`, `servers[0].url: https://api.realworld.show/api`). |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The backend API endpoint is hardcoded directly in the source code: `api.interceptor.ts` contains `url: \`https://api.realworld.show/api${req.url}\``. This URL is not configurable via environment variables, configuration files, or any service discovery mechanism. Changing the backend API URL requires modifying source code and rebuilding the application. The e2e test helpers (`e2e/helpers/api.ts`) also hardcode `const API_BASE = 'https://api.realworld.show/api'`. |
| **Gap** | All backend API endpoints are hardcoded in source code. No environment-based configuration, no Angular environment files, no runtime configuration injection. This prevents using different backends for development, staging, and production without code changes. |
| **Recommendation** | Externalize the API base URL using Angular's environment mechanism or runtime configuration injection. Options: (1) Use Angular environment files (`environment.ts` / `environment.prod.ts`) with different API URLs per build target. (2) Use a runtime configuration file loaded at app startup (`/assets/config.json`) for environment-agnostic builds. (3) Use environment variables injected at container startup if containerized. |
| **Evidence** | `src/app/core/interceptors/api.interceptor.ts` (hardcoded `https://api.realworld.show/api`), `e2e/helpers/api.ts` (hardcoded `const API_BASE = 'https://api.realworld.show/api'`). |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No unstructured data storage exists in this repository. The Angular SPA does not handle file uploads, document storage, or image management. The `marked` library (v17.0.1) is used to render markdown from the API response client-side (`src/app/shared/pipes/markdown.pipe.ts`), but the markdown content itself is stored and served by the backend API. User profile images are URLs stored in the backend database — the frontend only renders `<img>` tags with those URLs. No S3 references, no file system operations, and no document parsing infrastructure. |
| **Gap** | No unstructured data storage or parsing capability. This is expected for a frontend SPA — unstructured data management is a backend concern. |
| **Recommendation** | If the RealWorld application needs to handle user-uploaded content (article images, file attachments), implement S3 pre-signed URL uploads from the frontend with Textract or other parsing services on the backend. This is a backend architecture decision, not a frontend one. |
| **Evidence** | `package.json` (`marked: ^17.0.1`), `src/app/shared/pipes/markdown.pipe.ts` (client-side markdown rendering), no S3 SDK imports. |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All data access is through a consistent, well-structured service layer. Five Angular services form the data access layer: `ArticlesService` (CRUD for articles, favorites), `CommentsService` (CRUD for comments), `TagsService` (read tags), `ProfileService` (get/follow/unfollow profiles), and `UserService` (auth, CRUD current user). All services use Angular's `HttpClient` consistently and return typed `Observable` responses. The `api.interceptor.ts` provides a single point of URL prefixing, and the `token.interceptor.ts` provides unified auth token injection. The `error.interceptor.ts` normalizes error formats across all HTTP calls. No direct HTTP calls exist outside the service layer — all components access data through these services. |
| **Gap** | No gaps. The data access pattern is exemplary — centralized, consistent, type-safe, and well-documented. |
| **Recommendation** | No action needed. The service layer pattern is mature and well-implemented. |
| **Evidence** | `src/app/features/article/services/articles.service.ts`, `src/app/features/article/services/comments.service.ts`, `src/app/features/article/services/tags.service.ts`, `src/app/features/profile/services/profile.service.ts`, `src/app/core/auth/services/user.service.ts`, `src/app/core/interceptors/api.interceptor.ts`, `src/app/core/interceptors/token.interceptor.ts`, `src/app/core/interceptors/error.interceptor.ts`. |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database is defined in this repository. The Angular SPA does not manage any database — it delegates all data persistence to the external RealWorld backend API. There are no database engine version pins, no migration files, and no database configuration of any kind. The question evaluates database engine lifecycle management, which does not exist in this frontend-only codebase. |
| **Gap** | No database engine version management because no database exists in scope. This is expected for a frontend SPA. |
| **Recommendation** | N/A for this frontend repository. Database engine version management is the responsibility of the backend service that hosts the RealWorld API. |
| **Evidence** | No `.sql` files, no database driver dependencies in `package.json`, no database resources in IaC (no IaC exists). |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, proprietary SQL, or database coupling of any kind. All business logic in the frontend is in the Angular application layer (TypeScript services and components). Data operations are delegated to the backend API via HTTP. There is no SQL in the repository, no ORM configuration, and no database schema definitions. |
| **Gap** | No gaps. The application has zero database coupling from the frontend, which is the correct architecture. |
| **Recommendation** | No action needed. |
| **Evidence** | No `.sql` files found. No `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION` patterns. `package.json` contains no database-related dependencies. |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail, audit logging, or any logging infrastructure defined. No IaC exists to configure CloudTrail, CloudWatch Logs, or any logging service. The Angular SPA performs client-side `console.error` on bootstrap failure (`src/main.ts`: `.catch(err => console.error(err))`) but has no structured logging infrastructure. |
| **Gap** | No audit logging configured. If this application is deployed on AWS, there is no audit trail for API calls, deployments, or security events. |
| **Recommendation** | When AWS infrastructure is defined, enable CloudTrail with log file validation and S3 storage. For the frontend, consider adding client-side error tracking (e.g., CloudWatch RUM or a third-party service) to capture JavaScript errors and performance metrics. |
| **Evidence** | No `aws_cloudtrail` resources. No IaC files found. `src/main.ts` (only logging: `console.error`). |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no database, S3 bucket, EBS volume, or similar. The Angular SPA is a stateless frontend with no server-side storage. Client-side localStorage (`jwtToken`) is browser storage, not an AWS data-at-rest surface. SEC-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `has_at_rest_data_surface=false`. No S3, RDS, EBS, EFS, or DynamoDB resources defined. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | JWT token-based authentication is implemented. The `token.interceptor.ts` attaches the JWT token as an `Authorization: Token <jwt>` header on all HTTP requests when a token exists. The `jwt.service.ts` manages token lifecycle (save/get/destroy) using `localStorage`. The `error.interceptor.ts` handles 401 responses globally — purging auth for expired tokens on all endpoints except `/user` (which has its own 4XX vs 5XX error handling in `user.service.ts`). Login and registration flows (`auth.component.ts`) use email/password credentials submitted via POST to the backend API. The auth state machine (`UserService`) distinguishes between 'loading', 'authenticated', 'unauthenticated', and 'unavailable' states with auto-retry for 5XX errors. |
| **Gap** | The authentication uses a custom `Token` scheme (not standard `Bearer`) per the RealWorld API spec. There is no OAuth2/OIDC flow — authentication is email/password against the backend API. This is a constraint of the RealWorld spec, not a frontend-specific gap. Token refresh is not implemented (only retry on 5XX). |
| **Recommendation** | For production deployment, consider migrating to OAuth2/OIDC with Amazon Cognito as the identity provider. This would provide standardized token management (access/refresh tokens), MFA support, and centralized identity management. The current JWT implementation is functional for the RealWorld demo spec. |
| **Evidence** | `src/app/core/interceptors/token.interceptor.ts`, `src/app/core/auth/services/jwt.service.ts`, `src/app/core/auth/services/user.service.ts`, `src/app/core/interceptors/error.interceptor.ts`, `src/app/core/auth/auth.component.ts`. |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application manages its own authentication entirely with no external IdP integration. Login is email/password against the RealWorld API (`POST /users/login`). Registration is email/password/username against the API (`POST /users`). No Cognito, Okta, Auth0, SAML, or OIDC integration. No SSO. No MFA support. This is by design per the RealWorld specification, which defines its own simple auth mechanism. |
| **Gap** | No centralized identity provider integration. Authentication is entirely self-managed within the RealWorld API. This means no SSO across applications, no centralized user management, no MFA, and no federation with enterprise identity providers. |
| **Recommendation** | Integrate with Amazon Cognito (or another centralized IdP). Cognito provides: user pools for email/password auth, social login, MFA, token management (access/refresh/ID tokens), and federation with SAML/OIDC enterprise providers. This would replace the custom `/users/login` and `/users` endpoints with Cognito-hosted UI or embedded authentication flows. |
| **Evidence** | `src/app/core/auth/auth.component.ts` (email/password form), `src/app/core/auth/services/user.service.ts` (`login()` → `POST /users/login`), `package.json` (no Cognito SDK, no OIDC libraries). |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No plaintext credentials found in source code or configuration files. The API base URL (`https://api.realworld.show/api`) in `api.interceptor.ts` is not a secret — it is a public API endpoint. JWT tokens are managed client-side in `localStorage` (`jwt.service.ts`), which is standard browser-based auth practice (though `httpOnly` cookies would be more secure against XSS). GitHub Actions workflows reference secrets appropriately using `${{ secrets.AWS_ACCESS_KEY_ID }}`, `${{ secrets.AWS_SECRET_ACCESS_KEY }}`, `${{ secrets.ATXCI_API_KEY }}`, etc. No `.env` files are committed to the repository. No hardcoded passwords, API keys, or credentials found. However, there is no rotation mechanism — JWT tokens do not expire until the backend invalidates them. |
| **Gap** | While no plaintext credentials exist in source, there is no secrets management infrastructure (no Secrets Manager, no Vault). The frontend has no server-side secrets to manage, but the GitHub Actions workflows reference AWS credentials that should be managed with short-lived credentials (OIDC federation) rather than static access keys. |
| **Recommendation** | Replace static AWS credential secrets in GitHub Actions with GitHub OIDC federation to AWS IAM, eliminating the need for long-lived `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` secrets. For enhanced frontend security, consider using `httpOnly` cookies for JWT storage instead of `localStorage` to mitigate XSS token theft. |
| **Evidence** | `src/app/core/interceptors/api.interceptor.ts` (public URL, not a secret), `src/app/core/auth/services/jwt.service.ts` (localStorage token management), `.github/workflows/deploy.yml` (`${{ secrets.AWS_ACCESS_KEY_ID }}`, `${{ secrets.ATXCI_API_KEY }}`). No `.env` files committed. |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute resources exist to harden. No Dockerfile (no container image to scan), no AMIs (no EC2 instances), no server-side compute of any kind defined in the repository. The application builds to static files served by a web server not defined here. There is no SSM Patch Manager, no Inspector, no vulnerability scanning of the runtime environment. |
| **Gap** | No compute hardening because no compute is defined. When a deployment target is established (EKS, S3+CloudFront, etc.), hardening will be needed. |
| **Recommendation** | When containerized: use a minimal base image (NGINX Alpine or Bottlerocket for EKS), enable ECR image scanning, and implement a patching pipeline. When using S3+CloudFront: configure Security Headers (CSP, HSTS, X-Frame-Options) via CloudFront response headers policy. |
| **Evidence** | No Dockerfile, no AMI references, no `aws_ssm_patch_baseline`, no Inspector configuration. |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | XSS security tests exist and run in CI via Playwright (`.github/workflows/security-tests.yml`). The `e2e/xss-security.spec.ts` file contains comprehensive XSS payload testing across image URLs, article descriptions, and article body markdown — testing for `onerror`, `onload`, `javascript:` protocol, `<script>`, `<svg onload>`, `<iframe>`, and event handler injection via direct API bypass. This is a form of DAST (Dynamic Application Security Testing). However: no SAST tool (no SonarQube, Semgrep, CodeGuru), no dependency scanning (no Dependabot config in this repo — only in the `realworld` submodule), no `npm audit` or `bun audit` in the CI pipeline, and no container scanning (no containers). |
| **Gap** | The security pipeline has XSS DAST coverage (a strong practice) but lacks dependency vulnerability scanning and SAST. No Dependabot, no `npm audit`, no Snyk, and no SAST tool in the pipeline. |
| **Recommendation** | Add dependency scanning: configure Dependabot for this repository (`.github/dependabot.yml`) to monitor npm dependencies. Add `bun audit` or `npm audit` as a step in the CI pipeline. Consider adding Semgrep or SonarQube for SAST to catch code-level security issues. The existing XSS security tests are a strong foundation to build on. |
| **Evidence** | `.github/workflows/security-tests.yml`, `e2e/xss-security.spec.ts` (comprehensive XSS payload tests). No `.github/dependabot.yml` in the main repository (only in `realworld/.github/dependabot.yml` submodule). No SAST tool configuration. |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumentation found. No OpenTelemetry SDK, no AWS X-Ray SDK, and no `traceparent` or `X-Amzn-Trace-Id` header propagation in the interceptors. The `api.interceptor.ts`, `token.interceptor.ts`, and `error.interceptor.ts` handle URL prefixing, auth tokens, and error normalization respectively — none inject trace context headers. `package.json` contains no tracing-related dependencies. |
| **Gap** | No trace ID propagation from the frontend to the backend. This means backend traces cannot be correlated with specific frontend user actions or sessions. |
| **Recommendation** | Add OpenTelemetry browser instrumentation (`@opentelemetry/sdk-trace-web`) to propagate trace context to the backend API. Configure the `api.interceptor.ts` to inject `traceparent` headers. This enables end-to-end tracing from user click → frontend HTTP → backend API → database. |
| **Evidence** | `package.json` (no tracing dependencies), `src/app/core/interceptors/api.interceptor.ts` (no trace context injection). |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no user-facing surface for which SLOs are meaningful. The Angular SPA does not define HTTP endpoints — it is a client-side application served as static files. SLOs would apply to: (1) the hosting infrastructure (CloudFront latency, S3 availability) — which is not defined in this repo, and (2) the backend API — which is owned by the RealWorld backend, not this frontend. OPS-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `has_api_surface=false`, `has_persistent_data_store=false`. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom metrics published. No CloudWatch metrics, no analytics integration, no event tracking. The application does not emit any telemetry about user behavior (article views, login success/failure rates, comment creation rates, favorite actions). No `cloudwatch.put_metric_data` calls, no analytics SDKs (Google Analytics, Amplitude, Mixpanel), and no custom dashboards. |
| **Gap** | No business outcome metrics. The application has no visibility into how users interact with it — no conversion funnels, no feature usage tracking, no error rate by feature. |
| **Recommendation** | Add client-side analytics: CloudWatch RUM for real user monitoring (page load times, JS errors, user flows), or a lightweight analytics library for business events (article created, user registered, article favorited). These metrics inform modernization and feature prioritization decisions. |
| **Evidence** | `package.json` (no analytics dependencies), no `putMetricData` or analytics SDK calls in source code. |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting or anomaly detection configured. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no error rate monitoring, no latency tracking. Since no AWS infrastructure is defined, there are no resources to monitor. The application has no mechanism to detect or alert on degraded performance, increased error rates, or backend API unavailability (beyond the client-side retry logic in `user.service.ts`). |
| **Gap** | No anomaly detection or alerting. Issues are only discovered when users report them. |
| **Recommendation** | When hosting infrastructure is defined: configure CloudWatch alarms on CloudFront 4XX/5XX error rates, origin latency, and cache hit ratios. Add CloudWatch RUM alarms for client-side JS error rate spikes. Set up composite alarms for correlated failures (e.g., high error rate + high latency). |
| **Evidence** | No IaC files, no CloudWatch alarm definitions, no monitoring configuration. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The deployment process in `.github/workflows/deploy.yml` builds the Angular app, zips the build output, and creates a GitHub release artifact. There is no automated deployment to hosting infrastructure — no S3 upload, no CloudFront invalidation, no EKS deployment, no Lambda@Edge update. No blue/green, canary, or rolling deployment strategy. The build is published as a release artifact, but how it reaches production is undefined. |
| **Gap** | No deployment strategy. The "deployment" is a GitHub release zip — not an actual deployment to infrastructure. There is no staged rollout, no traffic shifting, and no rollback mechanism. |
| **Recommendation** | Implement a deployment pipeline that uploads the build to S3, invalidates the CloudFront cache, and validates the deployment with a smoke test. For staged rollouts: use CloudFront's cache invalidation with a monitoring window, or use Lambda@Edge for A/B testing. For container deployments on EKS (preferred): configure Argo Rollouts for canary or blue/green deployments. |
| **Evidence** | `.github/workflows/deploy.yml` (`cd dist/angular-conduit/browser && zip -r ../../../build.zip .`, `softprops/action-gh-release@v1`). No `aws s3 sync`, no `aws cloudfront create-invalidation`, no deployment manifests. |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Comprehensive end-to-end tests with Playwright covering all critical user workflows: articles (create, edit, delete, favorite, unfavorite, view from feed), authentication (register, login, logout, invalid login, session persistence, invalid token handling), comments (CRUD), error handling, health checks, navigation, null field handling, settings, social features (follow/unfollow), URL navigation, user fetch errors, and XSS security. 12+ e2e spec files in `e2e/`. Unit tests with Vitest for services (`jwt.service.spec.ts` — 30+ tests, `user.service.spec.ts` — 20+ tests, `articles.service.spec.ts`, `comments.service.spec.ts`, `tags.service.spec.ts`, `profile.service.spec.ts`). E2e tests run in CI (`.github/workflows/playwright.yml`) on every push and PR. Security tests run in a separate CI workflow (`.github/workflows/security-tests.yml`). Playwright configuration includes retries (2 in CI), trace capture on first retry, and screenshot on failure. |
| **Gap** | No gaps. Testing coverage is exemplary — comprehensive e2e tests, unit tests for all services, XSS security tests, all running in CI. |
| **Recommendation** | No action needed. Consider adding visual regression testing (Playwright's `toHaveScreenshot()`) and performance budgets as the application grows. |
| **Evidence** | `e2e/articles.spec.ts`, `e2e/auth.spec.ts`, `e2e/comments.spec.ts`, `e2e/error-handling.spec.ts`, `e2e/health.spec.ts`, `e2e/navigation.spec.ts`, `e2e/xss-security.spec.ts`, `e2e/social.spec.ts`, `e2e/settings.spec.ts`, `e2e/null-fields.spec.ts`, `e2e/url-navigation.spec.ts`, `e2e/user-fetch-errors.spec.ts`, `.github/workflows/playwright.yml`, `.github/workflows/security-tests.yml`, `vitest.config.ts`, `src/app/core/auth/services/*.spec.ts`, `src/app/features/*/services/*.spec.ts`. |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, no automation documents, no self-healing patterns, and no incident response workflows. No SSM Automation documents, no Lambda-based remediation, no Step Functions for incident workflows. The only resilience pattern is the auto-retry with exponential backoff in `user.service.ts` for 5XX errors during auth initialization — but this is application-level resilience, not operational incident response. |
| **Gap** | No incident response automation. When issues occur, response is entirely ad hoc. |
| **Recommendation** | Create runbooks for common scenarios: (1) Backend API unavailable — the frontend already handles this with retry logic, but document the expected behavior and escalation path. (2) CloudFront cache issues — document invalidation procedures. (3) Build failures — document rollback to previous release. Start with markdown runbooks, then graduate to SSM Automation documents when AWS infrastructure is defined. |
| **Evidence** | No runbook files, no SSM documents, no remediation Lambda functions. `src/app/core/auth/services/user.service.ts` (application-level retry only). |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership defined. No per-service dashboards, no alarms with named owners, no SLO definitions with team attribution. No `CODEOWNERS` file in the repository (only in the `realworld` submodule: `realworld/.github/CODEOWNERS`). No observability assets exist to own — no CloudWatch dashboards, no alarms, no monitoring configuration. |
| **Gap** | No observability ownership. No dashboards, no alarms, and no team attribution for monitoring assets. |
| **Recommendation** | When infrastructure is defined: create a CloudFront dashboard (request count, error rates, latency, cache hit ratio), a deployment dashboard (build times, deployment frequency, failure rate), and define ownership in a `CODEOWNERS` file. Add team tags to CloudWatch resources. |
| **Evidence** | No `CODEOWNERS` in the root repository. No CloudWatch dashboards or alarms. No observability configuration files. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resources are defined in this repository, so no tagging exists. No `default_tags` in Terraform provider, no `tags` on resources, no Tag Policies, and no AWS Config rules for required tags. When AWS infrastructure is created for this application, tagging governance will need to be established from scratch. |
| **Gap** | No resource tagging because no resources exist. When infrastructure is defined, tagging must be established from the start. |
| **Recommendation** | When IaC is created, define a tagging standard from day one. Include at minimum: `Environment` (dev/staging/prod), `Team` (owner), `Service` (angular-realworld), `CostCenter`, and `ManagedBy` (terraform/cdk). Use `default_tags` in the Terraform provider or CDK aspects to enforce tags automatically. |
| **Evidence** | No IaC files, no AWS resources, no tags. |

---

## Learning Materials

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to Containers** | [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM) · [Move to Containers with Amazon ECS](https://skillbuilder.aws/learning-plan/CDA8Y4JRRR) · [EKS Workshop](https://www.eksworkshop.com/) |
| **Move to Modern DevOps** | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `package.json` | APP-Q1, INF-Q1, INF-Q2, INF-Q4, DATA-Q1, DATA-Q4, SEC-Q4, SEC-Q7, OPS-Q1, OPS-Q3 | Dependencies, language versions, build scripts |
| `angular.json` | INF-Q1 | Build configuration, output path |
| `tsconfig.json` | APP-Q1 | TypeScript compiler options, ES2022 target |
| `src/main.ts` | SEC-Q1 | Application bootstrap, error handling |
| `src/app/app.config.ts` | APP-Q1 | Zoneless change detection, interceptor chain, app initialization |
| `src/app/app.routes.ts` | APP-Q2 | Lazy-loaded routes, modular structure |
| `src/app/core/interceptors/api.interceptor.ts` | APP-Q5, APP-Q6, INF-Q2, INF-Q4, OPS-Q1 | Hardcoded API base URL |
| `src/app/core/interceptors/token.interceptor.ts` | SEC-Q3 | JWT token injection in Authorization header |
| `src/app/core/interceptors/error.interceptor.ts` | SEC-Q3, DATA-Q2 | Global 401 handling, error normalization |
| `src/app/core/auth/services/jwt.service.ts` | SEC-Q3, SEC-Q5 | localStorage token management |
| `src/app/core/auth/services/user.service.ts` | APP-Q4, SEC-Q3, OPS-Q7, INF-Q3 | Auth state machine, retry with exponential backoff |
| `src/app/core/auth/auth.component.ts` | SEC-Q3, SEC-Q4 | Email/password login form |
| `src/app/features/article/services/articles.service.ts` | APP-Q2, APP-Q4, DATA-Q2, INF-Q3 | Article CRUD via HttpClient |
| `src/app/features/article/services/comments.service.ts` | DATA-Q2, INF-Q3 | Comment CRUD via HttpClient |
| `src/app/features/article/services/tags.service.ts` | DATA-Q2 | Tags read via HttpClient |
| `src/app/features/profile/services/profile.service.ts` | DATA-Q2 | Profile get/follow/unfollow via HttpClient |
| `src/app/shared/pipes/markdown.pipe.ts` | DATA-Q1 | Client-side markdown rendering with DomSanitizer |
| `.github/workflows/deploy.yml` | INF-Q1, INF-Q11, OPS-Q5, SEC-Q5 | Build, zip, GitHub release, ATX transform |
| `.github/workflows/playwright.yml` | INF-Q11, OPS-Q6 | E2E test pipeline |
| `.github/workflows/lint.yml` | INF-Q11 | Format check pipeline |
| `.github/workflows/security-tests.yml` | INF-Q11, SEC-Q7, OPS-Q6 | XSS security test pipeline |
| `e2e/xss-security.spec.ts` | SEC-Q7, OPS-Q6 | Comprehensive XSS payload testing |
| `e2e/articles.spec.ts` | OPS-Q6 | Article workflow e2e tests |
| `e2e/auth.spec.ts` | OPS-Q6 | Authentication workflow e2e tests |
| `e2e/health.spec.ts` | OPS-Q6 | Health check e2e tests |
| `e2e/helpers/api.ts` | APP-Q6 | Hardcoded API base URL in test helpers |
| `realworld/specs/api/openapi.yml` | APP-Q5 | OpenAPI 3.1.0 spec, version 2.0.0 |
| `src/app/core/auth/services/jwt.service.spec.ts` | OPS-Q6 | Unit tests for JWT service |
| `src/app/core/auth/services/user.service.spec.ts` | OPS-Q6 | Unit tests for User service |
| `vitest.config.ts` | OPS-Q6 | Unit test configuration (Vitest + jsdom) |
| `playwright.config.ts` | OPS-Q6 | E2E test configuration (Playwright + Chromium) |
| `README.md` | Quick Agent Wins | Project documentation, functionality overview |
| `CLAUDE.md` | Quick Agent Wins | Development commands, code style guidance |
| `src/app/features/` | APP-Q2 | Feature modules: article, profile, settings |
| `src/app/core/` | APP-Q2 | Core modules: auth, interceptors, layout, models |
| `src/app/shared/` | APP-Q2 | Shared modules: pipes, components |
