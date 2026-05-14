# Modernization Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | realworld-apps--angular-realworld-example-app |
| **Date** | 2025-05-07 |
| **Repo Type** | application |
| **Service Archetype** | stateless-utility (auto-detected) |
| **Priority** | P2 |
| **Tags** | typescript, frontend, angular |
| **Context** | Angular reference implementation of the RealWorld spec. |
| **Overall Score** | 2.18 / 4.0 |
| **Surface Flags** | has_persistent_data_store=false, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=false, has_multi_instance_deployment=false |

**Archetype Justification**: This is a frontend-only Angular SPA with no backend, no database connections, no write operations to any owned data store, and no server-side API surface. All data operations are delegated to an external API (`https://api.realworld.show/api`). The application performs stateless rendering of data fetched from a remote service. Classified as `stateless-utility`.

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure, Platform, and DevOps (INF) | 1.50 / 4.0 | 🟠 Needs Work | Critical |
| Application Architecture (APP) | 2.50 / 4.0 | 🟡 Partial | Needs Work |
| Data Platform Modernization (DATA) | 4.00 / 4.0 | ✅ Mature | Ready |
| Security Baseline (SEC) | 1.50 / 4.0 | ❌ Not Ready | Critical |
| Operations & Observability (OPS) | 1.38 / 4.0 | ❌ Not Ready | Critical |
| **Overall** | **2.18 / 4.0** | **🟠 Needs Work** | |

**Scoring Notes:**
- INF: INF-Q10=1, INF-Q11=2 (9 questions Not Evaluated) → (1+2)/2 = 1.50
- APP: APP-Q1=4, APP-Q2=1, APP-Q5=3, APP-Q6=2 (2 questions Not Evaluated) → (4+1+3+2)/4 = 2.50
- DATA: DATA-Q2=4, DATA-Q4=4 (2 questions N/A) → (4+4)/2 = 4.00
- SEC: SEC-Q1=1, SEC-Q3=2, SEC-Q4=1, SEC-Q5=2, SEC-Q6=1, SEC-Q7=2 (1 question Not Evaluated) → (1+2+1+2+1+2)/6 = 1.50
- OPS: OPS-Q1=1, OPS-Q3=1, OPS-Q4=1, OPS-Q5=2, OPS-Q6=3, OPS-Q7=1, OPS-Q8=1, OPS-Q9=1 (1 question Not Evaluated) → (1+1+1+2+3+1+1+1)/8 = 1.38
- Overall: (1.50+2.50+4.00+1.50+1.38)/5 = 2.18

### Classification

**Tier: Remediation Required**

This repo has 8 High findings, 5 Medium findings, 1 Low finding. Matched rule: "2-11 High → Remediation Required."

MOD classification is deliberately softer than ARA classification on "1 High." ARA gates on agent safety — a single High is a deployment blocker. MOD measures modernization maturity — a single High is typically one modernization gap rather than a deployment blocker. With 8 High findings, this repository requires significant modernization work across infrastructure automation, security baseline, and operations before it can be considered cloud-native ready.

**Classification Consistency Check:** V5 overall score 2.18 → V5 band "Needs Work" (1.5–2.4). V6 tier "Remediation Required". Per the equivalence table, V5 "Needs Work" ≡ V6 "Remediation Required" → **consistent**.

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC — all infrastructure (Netlify hosting) is configured manually outside the repository. | Cannot reproduce environments, no disaster recovery, no infrastructure audit trail. |
| 2 | APP-Q2: Monolith vs Microservices | 1 | Single-page application is a tightly-coupled frontend monolith with no module boundaries for independent deployment. | Cannot independently scale or deploy features; all changes require full application rebuild. |
| 3 | SEC-Q1: Audit Logging | 1 | No CloudTrail or equivalent audit logging configured. | No forensic capability, compliance gaps, unable to trace actions in production. |
| 4 | SEC-Q4: Centralized Identity Integration | 1 | Application manages its own JWT authentication with no external IdP integration. | Inconsistent access policies, increased attack surface, no SSO capability. |
| 5 | OPS-Q1: Distributed Tracing | 1 | No distributed tracing or observability instrumentation. | Cannot diagnose request-flow issues, no visibility into API call failures or latency. |

---

## Quick Agent Wins

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository (README.md, CLAUDE.md, e2e/SELECTORS.md, OpenAPI spec at realworld/specs/api/openapi.yml).
- **What it enables:** A knowledge agent that indexes existing documentation and the OpenAPI spec to answer developer questions about the RealWorld API contract, testing patterns, and application architecture.
- **Additional steps:** The OpenAPI spec already exists in structured form. Index README, CLAUDE.md, and the e2e selectors documentation for developer onboarding queries.
- **Effort:** Low

### DevOps Agent

- **Prerequisite:** CI/CD pipeline exists (INF-Q11 = 2). GitHub Actions workflows for build, lint, E2E tests, and security tests are in place.
- **What it enables:** An agent that triggers builds, checks workflow status, and manages GitHub Releases — currently the deploy workflow already automates release creation.
- **Additional steps:** The existing workflows cover build and test but lack deployment automation to a hosting platform via IaC. Adding structured deployment outputs would enhance the agent surface.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2=1 (monolith), INF-Q10=1 (no IaC) |
| 2 | Move to Containers | Not Triggered | — | — | No deployed workload exists; this is a static SPA deployed to Netlify. Containerization is not the correct modernization path for a static frontend. |
| 3 | Move to Open Source | Not Triggered | — | — | No commercial database engines detected; frontend-only application. |
| 4 | Move to Managed Databases | Not Triggered | — | — | has_persistent_data_store=false; no database in this frontend application. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads exist; stateless-utility frontend. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10=1 (no IaC), INF-Q11=2 (partial CI/CD), OPS-Q5=2 (no canary/blue-green), OPS-Q6=3 (integration tests exist). |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current State:**
- APP-Q2=1: The application is a single-page application monolith — one Angular build producing one deployable bundle. All features (articles, auth, profiles, settings, editor) are tightly coupled in a single deployment unit with shared state management (RxJS BehaviorSubjects in singleton services).
- INF-Q10=1: No infrastructure-as-code exists. Hosting is configured manually on Netlify (evidenced by `src/_redirects`).

**Recommendations:**
- Consider decomposing the frontend into micro-frontends using Module Federation or Angular's built-in lazy loading with independent deployment pipelines per feature domain (articles, profiles, auth).
- For the hosting layer: adopt AWS CloudFront + S3 for static hosting defined via CDK or Terraform, enabling per-feature-module deployments with independent invalidation.
- Leverage API Gateway to proxy and version the backend API calls, enabling the frontend to evolve independently of the backend contract.

**Representative AWS Services:** CloudFront, S3, API Gateway, CodePipeline, CDK

**Patterns:** Micro-frontend architecture, Module Federation, Strangler Fig (for gradual extraction of feature modules)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current State:**
- INF-Q10=1: No IaC. Hosting infrastructure (Netlify) is manually configured. No Terraform, CDK, CloudFormation, or Helm definitions exist.
- INF-Q11=2: CI/CD exists via GitHub Actions with build, lint, and E2E test workflows. However, deployment to hosting is not automated via IaC — the deploy workflow creates GitHub Releases (zip artifacts) but does not deploy to production infrastructure.
- OPS-Q5=2: Deployment is a rolling update model (Netlify auto-deploys on main push) with no canary, blue/green, or traffic shifting capability.

**Recommendations:**
- Define hosting infrastructure in Terraform or CDK: CloudFront distribution + S3 bucket + Route 53 DNS + ACM certificate.
- Enhance GitHub Actions pipeline with: deployment to S3/CloudFront, cache invalidation, and environment promotion (staging → production).
- Add canary deployment via CloudFront Functions or weighted routing between S3 object versions.
- Integrate security scanning (Dependabot, npm audit) into CI pipeline as a blocking gate.

**Representative AWS Services:** CodePipeline, CodeBuild, CloudFormation/CDK, S3, CloudFront, Route 53

**Learning Materials:**
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Decomposition Strategy

APP-Q2 scored 1 (tightly-coupled monolith), triggering this section.

### Current Monolith Analysis

The Angular application is structured as a single SPA with:
- **Feature modules**: `article`, `profile`, `settings` (under `src/app/features/`)
- **Core module**: `auth`, `interceptors`, `layout` (under `src/app/core/`)
- **Shared module**: `pipes`, `components` (under `src/app/shared/`)

Module boundaries exist at the directory level but all features share:
- A single `UserService` (global auth state via RxJS BehaviorSubject)
- A single set of HTTP interceptors (api, token, error)
- A single router configuration (`app.routes.ts`)
- A single build output (one Angular bundle)

### Recommended Approach: Conditional / Adaptive

| Approach | Description | Rationale |
|----------|-------------|-----------|
| **Conditional / Adaptive** | Deploy the SPA as-is to AWS (S3 + CloudFront), then selectively extract high-value features as independently deployable micro-frontends. | This is a reference/demo app. The Angular feature module structure provides natural seams for future micro-frontend extraction, but the current scale (< 60 source files) does not justify full decomposition. Prioritize infrastructure automation and DevOps maturity first. |

### Pattern Recommendations

| Pattern | Application |
|---------|-------------|
| **Module Federation** | Extract feature modules (articles, profiles) into independently deployable remotes loaded at runtime via Angular's lazy loading + Webpack Module Federation or Native Federation. |
| **Anti-corruption Layer** | If multiple micro-frontends consume the backend API, introduce a shared API client library as an ACL to prevent divergent API consumption patterns. |

### Effort Factors

| Factor | Signal | Analysis |
|--------|--------|-----------|
| Module boundaries | Clear feature directories with lazy-loaded routes | Low effort (boundaries exist) |
| Data coupling | Shared `UserService` global state | Medium effort (auth state must be shared across micro-frontends) |
| CI/CD maturity | Partial (build exists, deploy is manual) | Medium effort (must build per-module pipelines) |
| Test coverage | E2E tests cover critical workflows | Low effort (regression protection exists) |

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This application has no deployed workload managed by this repository. It is a static SPA whose build output (HTML/CSS/JS) is deployed to Netlify — a third-party hosting platform configured outside this codebase. No compute resources (EC2, ECS, EKS, Lambda, Fargate) are defined or referenced. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No IaC files, no Dockerfile, no deployment manifests. `src/_redirects` indicates Netlify hosting. |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system does not deploy a database. It is a frontend-only application that delegates all data persistence to an external API at `https://api.realworld.show/api`. INF-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/app/core/interceptors/api.interceptor.ts` — all HTTP requests are prefixed with the external API URL. No database driver imports, no connection strings, no database IaC resources. |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Workflow orchestration is not applicable by design — no multi-step workflows exist for a stateless frontend SPA that delegates all business operations to an external API. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No Step Functions, Temporal, or workflow definitions. Application logic is limited to rendering data fetched from external API. |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Synchronous HTTP is the correct design for a frontend SPA consuming a REST API. No messaging or streaming infrastructure is needed — the application makes synchronous HTTP calls to the external backend and renders responses. Adopting async messaging is NOT recommended for this architecture. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/app/features/article/services/articles.service.ts`, `src/app/core/auth/services/user.service.ts` — all communication is synchronous HTTP via Angular HttpClient. |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This application has no deployed workload managed by this repository. No VPC, subnets, security groups, or network infrastructure exists. The application runs as static files served by a CDN (Netlify). |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No IaC files defining VPC, subnets, or security groups. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This application has no server-side API surface. It is a client-side SPA that consumes an external API. No API Gateway, ALB, or CloudFront configuration is managed by this repository. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No IaC defining API Gateway, ALB, or CloudFront. Static hosting on Netlify with `_redirects` for SPA routing. |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This application has no deployed compute workload to scale. Static assets are served by Netlify's CDN which handles scaling transparently. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No ASG, ECS service scaling, or Lambda concurrency configuration. No compute resources defined. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no persistent state to back up. INF-Q8 does not apply. The application is a stateless frontend — source code is version-controlled in git (the only "backup" that matters). |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database, no S3 buckets, no EBS volumes, no persistent data stores defined. |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed workload requiring HA evaluation. INF-Q9 does not apply. Static assets are served by Netlify's globally distributed CDN. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No compute resources, no database resources, no multi-AZ configuration. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No infrastructure-as-code exists in this repository. The hosting infrastructure (Netlify) is configured entirely outside the codebase through the Netlify web UI or CLI — no Terraform, CDK, CloudFormation, or Helm definitions are present. The only infrastructure signal is `src/_redirects` (a Netlify-specific SPA routing rule). |
| **Gap** | 0% IaC coverage. Infrastructure is manually configured (ClickOps on Netlify). If the hosting platform were migrated to AWS (CloudFront + S3), there would be no reproducible definition. |
| **Recommendation** | Define hosting infrastructure in Terraform or CDK: S3 bucket for static assets, CloudFront distribution with OAC, Route 53 DNS records, ACM certificate for TLS. This enables environment reproducibility and disaster recovery. |
| **Evidence** | No `.tf`, `cdk.json`, `template.yaml`, or Helm chart files found. `src/_redirects` confirms Netlify hosting. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | GitHub Actions workflows exist for build (`.github/workflows/deploy.yml`), format checking (`.github/workflows/lint.yml`), E2E testing (`.github/workflows/playwright.yml`), and security testing (`.github/workflows/security-tests.yml`). The build workflow creates GitHub Release artifacts (zip files) but does NOT deploy to production hosting. Deployment to Netlify happens outside this pipeline (likely via Netlify's own git integration). |
| **Gap** | Build is automated but deployment is not controlled by the CI/CD pipeline in this repository. No IaC deployment pipeline exists. The pipeline produces artifacts but does not deploy them to production infrastructure. |
| **Recommendation** | Extend the GitHub Actions pipeline to deploy build artifacts to AWS (S3 upload + CloudFront invalidation). Add environment promotion (staging → production) with approval gates. Define infrastructure deployment via CDK deploy or Terraform apply in the pipeline. |
| **Evidence** | `.github/workflows/deploy.yml` (build + release), `.github/workflows/lint.yml`, `.github/workflows/playwright.yml`, `.github/workflows/security-tests.yml` |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | TypeScript 5.9.3 with Angular 21.x (latest major version), ES2022 target, strict mode enabled. This is the most current combination of language version and framework version available. Angular 21 uses standalone components, zoneless change detection, and the modern `@angular/build:application` builder. The ecosystem has first-class tooling for cloud-native SPA development. |
| **Gap** | None. |
| **Recommendation** | No action needed. The language and framework are at the leading edge. |
| **Evidence** | `package.json` — TypeScript ~5.9.3, Angular 21.1.1/21.2.4. `tsconfig.json` — target ES2022, strict: true, module: "preserve", moduleResolution: "bundler". |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application is a single deployable unit — one Angular build produces one bundle deployed as a monolithic SPA. While the code has feature directories (`features/article`, `features/profile`, `features/settings`), they are not independently deployable. All features share global state (`UserService`, `JwtService`), a single router, shared interceptors, and produce a single build artifact. |
| **Gap** | Tightly-coupled monolith with no independent deployment capability. All features must be built and deployed together. A change to the settings page requires rebuilding and redeploying the entire application including articles, profiles, and auth. |
| **Recommendation** | For a reference/demo application of this size (< 60 source files), full microservice decomposition is not warranted. However, if independent deployment is desired: adopt Angular Module Federation to enable per-feature-module builds and deployments. The existing lazy-loaded route structure provides natural decomposition seams. |
| **Evidence** | `angular.json` — single project `angular-conduit` with single build output. `src/app/app.routes.ts` — single router with all feature routes. `src/app/app.config.ts` — single application configuration. |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. Sync request/response is the correct design for a frontend SPA consuming a REST API. All HTTP calls are synchronous (request → response) via Angular HttpClient, which is the appropriate pattern for a browser-based client application. Async messaging infrastructure (SQS, SNS, EventBridge) is not applicable to frontend applications. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | `src/app/features/article/services/articles.service.ts`, `src/app/core/auth/services/user.service.ts` — all service methods return `Observable<T>` from HTTP calls (synchronous request/response pattern). |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `stateless-utility`. No operations exceed 30 seconds — not applicable by design. All user interactions result in HTTP requests to the external API that return within typical web response times. The frontend performs no batch processing, no heavy computation, and no long-running operations. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | All service methods make single HTTP calls. No background job frameworks, no Web Workers for long computation, no polling patterns for long-running operations. |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The consumed API has a versioned OpenAPI specification (v2.0.0 at `realworld/specs/api/openapi.yml`). The API base URL uses a path-based approach (`/api/...`) though without explicit version numbering in URL paths (e.g., `/api/v1/`). The API contract is formally documented with OpenAPI 3.1.0, which provides a stable versioning reference even without URL path versioning. |
| **Gap** | No explicit version segment in the API URL path (e.g., `/v1/articles`). Version is tracked in the OpenAPI spec metadata but not enforced in the URL structure. |
| **Recommendation** | If the backend were owned by this team, add URL path versioning (e.g., `/api/v1/`) to enable backward-compatible evolution. Since this frontend consumes an external API, the recommendation is to pin the OpenAPI spec version and add contract testing to detect breaking changes. |
| **Evidence** | `realworld/specs/api/openapi.yml` — version 2.0.0, OpenAPI 3.1.0. `src/app/core/interceptors/api.interceptor.ts` — base URL `https://api.realworld.show/api` with no version path. |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The external API endpoint is hard-coded in `src/app/core/interceptors/api.interceptor.ts` as `https://api.realworld.show/api`. There is no environment variable configuration, no service discovery mechanism, and no build-time configuration injection. Changing the API endpoint requires modifying source code and rebuilding. |
| **Gap** | Hard-coded API endpoint with no externalized configuration. Cannot switch between environments (dev, staging, production) without code changes. |
| **Recommendation** | Externalize the API base URL using Angular's `environment.ts` files or runtime configuration injection (e.g., `/assets/config.json` loaded at startup). This enables environment-specific deployments without rebuilds. |
| **Evidence** | `src/app/core/interceptors/api.interceptor.ts` — `url: \`https://api.realworld.show/api${req.url}\`` |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a frontend-only SPA with no owned data storage. Unstructured data (article content, images) is managed by the external backend API. This question does not apply to a frontend application that does not store or manage unstructured data. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No S3 buckets, no file storage, no document management. All content is fetched from `api.realworld.show`. |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The application has a well-structured, unified data access layer. All API communication flows through dedicated service classes (`ArticlesService`, `CommentsService`, `TagsService`, `ProfileService`, `UserService`) in clearly defined service directories. No component directly calls `HttpClient` — all data access is mediated through these services. HTTP interceptors (`apiInterceptor`, `tokenInterceptor`, `errorInterceptor`) provide cross-cutting concerns at a single point of control. |
| **Gap** | None. |
| **Recommendation** | No action needed. The service layer pattern is well-implemented with consistent data access patterns. |
| **Evidence** | `src/app/features/article/services/articles.service.ts`, `src/app/features/article/services/comments.service.ts`, `src/app/features/article/services/tags.service.ts`, `src/app/features/profile/services/profile.service.ts`, `src/app/core/auth/services/user.service.ts`, `src/app/core/interceptors/` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a frontend-only application with no database. No database engine versions to evaluate. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database IaC resources, no connection strings, no database drivers in `package.json`. |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL. This is a frontend application with all business logic in the application layer (TypeScript services). Data operations are delegated to the external API — no direct database interaction exists. |
| **Gap** | None. |
| **Recommendation** | No action needed. |
| **Evidence** | No `.sql` files, no database-specific code, no ORM configuration. All data access via HTTP to external API. |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging is configured. No infrastructure exists in this repository to enable audit logging. The application runs as static files on Netlify with no server-side component under this team's control. |
| **Gap** | No audit logging infrastructure. User actions (login, article creation, profile changes) are not logged in any audit trail controlled by this repository. |
| **Recommendation** | When migrating to AWS hosting (CloudFront + S3): enable CloudTrail for the AWS account, configure CloudFront access logging to S3, and consider adding client-side event logging (e.g., via Amazon Kinesis Data Firehose or CloudWatch RUM) for user action audit trails. |
| **Evidence** | No `aws_cloudtrail` in IaC, no logging configuration, no CloudWatch resources. |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no database, S3 bucket, EBS volume, or similar. SEC-Q2 does not apply. The application is a static frontend with no owned data stores. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No data stores defined in IaC or referenced in application code. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application implements JWT token-based authentication via `JwtService` (localStorage) and `tokenInterceptor` (attaches `Authorization: Token <jwt>` header). However, this is client-side token management for consuming an external API — not server-side API authentication. The token is stored in localStorage (vulnerable to XSS). There is no API Gateway authorizer, no Cognito integration, and no OAuth2 flow. Authentication is a simple username/password → JWT exchange with the external backend. |
| **Gap** | No OAuth2/OIDC flow. Token stored in localStorage (XSS-vulnerable). No API Gateway with authorizer for server-side validation. Authentication relies entirely on the external API's token issuance. |
| **Recommendation** | When deploying with AWS infrastructure: integrate with Amazon Cognito for OAuth2/OIDC-based authentication flow with PKCE, use httpOnly cookies or Cognito hosted UI for token management (avoids localStorage XSS risk), and add an API Gateway authorizer for server-side token validation. |
| **Evidence** | `src/app/core/auth/services/jwt.service.ts` — localStorage token storage. `src/app/core/interceptors/token.interceptor.ts` — `Authorization: Token` header injection. |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application manages its own authentication entirely with no external identity provider integration. Login/register flows (`UserService.login()`, `UserService.register()`) send credentials directly to the backend API. There is no Cognito, Okta, SAML, or OIDC federation. |
| **Gap** | No centralized IdP integration. No SSO capability. Authentication is entirely self-managed between the frontend and the external API's `/users/login` endpoint. |
| **Recommendation** | Integrate with Amazon Cognito as the identity provider. Use Cognito Hosted UI for login/register flows with OAuth2/OIDC. This enables SSO, social login providers, MFA, and centralized identity governance. |
| **Evidence** | `src/app/core/auth/services/user.service.ts` — `login()` posts to `/users/login`, `register()` posts to `/users`. No Cognito, OIDC, or SAML configuration anywhere. |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No plaintext credentials are committed to the repository. CI/CD secrets (AWS credentials, API keys) are stored in GitHub Actions secrets (referenced as `${{ secrets.AWS_ACCESS_KEY_ID }}`, `${{ secrets.ATXCI_API_KEY }}`). However, there is no AWS Secrets Manager, no Vault, and no rotation configured. The JWT token is stored in browser localStorage at runtime (client-side, not a server-side secrets management concern). |
| **Gap** | No dedicated secrets management service. CI/CD secrets are in GitHub's secret store (acceptable for CI) but no rotation policy exists. No Secrets Manager or Vault integration. |
| **Recommendation** | When migrating to AWS-managed infrastructure: use AWS Secrets Manager for any service credentials, configure automated rotation for API keys, and use OIDC federation for GitHub Actions → AWS (eliminating static AWS access keys). |
| **Evidence** | `.github/workflows/deploy.yml` — `secrets.AWS_ACCESS_KEY_ID`, `secrets.AWS_SECRET_ACCESS_KEY`, `secrets.ATXCI_API_KEY`. No plaintext credentials in source. |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute hardening or patching strategy exists. The application has no server-side compute under its control — it is deployed as static files. There are no EC2 instances, no container images, no AMIs to harden. No vulnerability scanning (Inspector, Snyk) is configured for the runtime environment. |
| **Gap** | No vulnerability scanning of the deployment environment. No container image scanning (because no containers exist). No SSM Patch Manager (because no EC2). |
| **Recommendation** | When migrating to AWS: if containerized (e.g., nginx serving static files in ECS), use ECR image scanning and Bottlerocket base images. If staying static (S3+CloudFront), this question becomes less critical — focus on dependency vulnerability scanning in CI (see SEC-Q7). |
| **Evidence** | No Dockerfile, no EC2, no container images, no SSM configuration, no Inspector/Snyk configuration. |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The repository has security-focused E2E tests (`.github/workflows/security-tests.yml` running Playwright tests tagged `@security`, including `e2e/xss-security.spec.ts`). However, there is no SAST tool (SonarQube, Semgrep, CodeGuru), no Dependabot configuration, no `npm audit` step in CI, and no container scanning. The security tests are behavioral (testing XSS protection) rather than static analysis. |
| **Gap** | No SAST tool in CI. No dependency vulnerability scanning (no Dependabot, no `npm audit` in pipeline). Security tests are limited to XSS behavioral testing via Playwright. |
| **Recommendation** | Add Dependabot for automated dependency vulnerability alerts. Add `npm audit --audit-level=critical` as a blocking step in the CI pipeline. Consider adding Semgrep or ESLint security plugin for SAST. These are low-effort, high-impact additions for a frontend application. |
| **Evidence** | `.github/workflows/security-tests.yml` — security-tagged Playwright tests. `e2e/xss-security.spec.ts` — XSS security test. No `.snyk`, no `dependabot.yml`, no `npm audit` in any workflow. |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing is instrumented. No OpenTelemetry SDK, no X-Ray instrumentation, no trace ID propagation in HTTP headers. The application makes HTTP calls to an external API with no correlation IDs or trace context. |
| **Gap** | No tracing instrumentation. Cannot correlate frontend HTTP requests with backend processing. No visibility into request latency breakdown. |
| **Recommendation** | Add OpenTelemetry browser SDK or AWS CloudWatch RUM for frontend performance monitoring and trace context propagation. This enables correlation of frontend user actions with backend API call performance. |
| **Evidence** | No OpenTelemetry, X-Ray, or tracing libraries in `package.json`. No trace header propagation in interceptors. |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no user-facing surface for which SLOs are meaningful. It is a static SPA with no server-side infrastructure under this team's control. SLOs would apply to the backend API (owned externally) or to the hosting CDN (managed by Netlify). OPS-Q2 does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No SLO definitions, no CloudWatch alarms, no error budget tracking. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics are published. No analytics, no CloudWatch custom metrics, no conversion tracking, no user engagement metrics. The only telemetry is the Angular CLI analytics flag in `angular.json`. |
| **Gap** | No business outcome metrics. Cannot measure user engagement, article creation rates, authentication success rates, or any business KPIs. |
| **Recommendation** | Add CloudWatch RUM for real user monitoring. Instrument key user journeys (login success rate, article creation, page load times) with custom metrics. Consider Amazon Pinpoint for user engagement analytics. |
| **Evidence** | `angular.json` — `"analytics": "2fd54eca-..."` (Angular CLI analytics only). No custom metrics, no analytics SDK in `package.json`. |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting is configured. No CloudWatch alarms, no error rate monitoring, no latency alerts. No monitoring infrastructure exists in this repository. |
| **Gap** | No alerting. If the external API becomes unavailable or the frontend build breaks, there is no automated notification. |
| **Recommendation** | When migrating to AWS hosting: configure CloudWatch alarms on CloudFront error rates (4xx, 5xx), add synthetic canaries (CloudWatch Synthetics) for critical user journeys, and set up anomaly detection on request latency. |
| **Evidence** | No CloudWatch, no PagerDuty/OpsGenie integration, no alerting configuration. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Deployment is a rolling update via Netlify's git integration — push to `main` triggers a build and immediate production deployment. There is no canary, blue/green, or staged rollout. The GitHub Actions workflow produces release artifacts but does not control the production deployment. |
| **Gap** | No staged rollout. No ability to test changes on a subset of users before full deployment. No rollback mechanism beyond reverting a git commit. |
| **Recommendation** | Adopt CloudFront with weighted routing or Lambda@Edge for canary deployments. Deploy new versions to a secondary S3 prefix and shift traffic gradually. Alternatively, use CloudFront Functions for A/B testing and staged rollouts. |
| **Evidence** | `.github/workflows/deploy.yml` — creates GitHub Release artifacts. `src/_redirects` — Netlify SPA routing. No canary/blue-green configuration. |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Comprehensive E2E integration tests exist via Playwright, covering critical workflows: articles CRUD, authentication, comments, navigation, settings, social interactions, URL navigation, error handling, and XSS security. These tests run in CI (`.github/workflows/playwright.yml`). Unit tests (Vitest) cover core services. The test suite exercises the full application against the live external API. |
| **Gap** | Tests run against the live external API (`api.realworld.show`) — no contract testing or mock API for isolated integration testing. Test reliability depends on external API availability. |
| **Recommendation** | Add API contract tests using the existing OpenAPI spec (`realworld/specs/api/openapi.yml`) to detect breaking changes. Consider adding a mock API server (MSW or similar) for CI stability to avoid false failures from external API downtime. |
| **Evidence** | `.github/workflows/playwright.yml`, `e2e/articles.spec.ts`, `e2e/auth.spec.ts`, `e2e/xss-security.spec.ts`, `src/app/core/auth/services/user.service.spec.ts` and other `*.spec.ts` files. |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, no incident response automation, no self-healing patterns. No Systems Manager Automation documents, no Lambda-based remediation, no structured incident workflows. |
| **Gap** | Incident response is entirely ad hoc. No documented procedures for common failure scenarios (API downtime, deployment failures, CDN issues). |
| **Recommendation** | Create runbooks for common incidents: external API unavailability (the app already handles this gracefully with retry logic in UserService), deployment rollback procedures, CDN cache invalidation. When on AWS: use SSM Automation documents or Step Functions for automated remediation. |
| **Evidence** | No runbook files, no SSM documents, no automated remediation. The application does have built-in resilience (retry with exponential backoff in `user.service.ts`), but no operational runbooks exist. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership defined. No service-level dashboards, no alarms with named owners, no SLO definitions tied to teams. No CODEOWNERS file referencing observability assets. |
| **Gap** | No observability ownership. No one is explicitly responsible for monitoring the application's health. |
| **Recommendation** | Define a CODEOWNERS file covering observability configurations. When AWS monitoring is added, create per-service dashboards with named owners and team tags on CloudWatch resources. |
| **Evidence** | No CODEOWNERS file, no dashboard definitions, no alarm configurations, no team-tagged monitoring resources. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging exists because no AWS resources are defined in this repository. No IaC with `default_tags`, no tag policies, no cost allocation tags. |
| **Gap** | No tagging governance. When AWS resources are eventually provisioned, there is no tagging standard in place. |
| **Recommendation** | When migrating to AWS: establish a tagging standard (Environment, Service, Owner, CostCenter) and enforce it via Terraform `default_tags` or CDK Aspects. Configure AWS Organizations Tag Policies and AWS Config required-tags rules. |
| **Evidence** | No IaC files, no resource tags, no tagging policies. |

---

## Learning Materials

### Move to Cloud Native
- [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

### Move to Modern DevOps
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `package.json` | APP-Q1 | TypeScript 5.9.3, Angular 21.x dependencies |
| `angular.json` | APP-Q1, APP-Q2, OPS-Q3 | Single project build config, CLI analytics |
| `tsconfig.json` | APP-Q1 | ES2022 target, strict mode |
| `src/app/core/interceptors/api.interceptor.ts` | INF-Q2, APP-Q6 | Hard-coded external API URL |
| `src/app/core/interceptors/token.interceptor.ts` | SEC-Q3 | JWT token injection |
| `src/app/core/interceptors/error.interceptor.ts` | SEC-Q3 | Global error handling, 401 interception |
| `src/app/core/auth/services/jwt.service.ts` | SEC-Q3, SEC-Q5 | localStorage token management |
| `src/app/core/auth/services/user.service.ts` | SEC-Q4, OPS-Q7, APP-Q3 | Self-managed auth, retry logic |
| `src/app/features/article/services/articles.service.ts` | DATA-Q2, APP-Q3 | Unified service layer, HTTP calls |
| `src/app/app.routes.ts` | APP-Q2 | Single router with all feature routes |
| `src/app/app.config.ts` | APP-Q2 | Single application configuration |
| `.github/workflows/deploy.yml` | INF-Q11, SEC-Q5, OPS-Q5 | Build pipeline, secrets in GitHub, release creation |
| `.github/workflows/lint.yml` | INF-Q11 | Format checking workflow |
| `.github/workflows/playwright.yml` | OPS-Q6 | E2E test workflow in CI |
| `.github/workflows/security-tests.yml` | SEC-Q7 | Security-focused E2E tests |
| `e2e/xss-security.spec.ts` | SEC-Q7 | XSS security test |
| `src/_redirects` | INF-Q10 | Netlify SPA routing, indicates hosting platform |
| `realworld/specs/api/openapi.yml` | APP-Q5 | OpenAPI 3.1.0 spec, API versioning |
| `README.md` | Quick Agent Wins | Developer documentation |
| `CLAUDE.md` | Quick Agent Wins | AI assistant documentation |
