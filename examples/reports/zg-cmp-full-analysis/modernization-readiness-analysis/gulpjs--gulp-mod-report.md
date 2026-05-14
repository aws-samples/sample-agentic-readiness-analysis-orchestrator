# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | gulp |
| **Date** | 2026-04-29 |
| **Repo Type** | application |
| **Service Archetype** | stateless-utility (auto-detected) |
| **Priority** | P2 |
| **Tags** | javascript, build-tool |
| **Context** | Streaming JavaScript build-system toolkit. |
| **Overall Score** | 1.82 / 4.0 |

**Archetype Justification**: No database connections, no external service calls, no write operations to any backend. The package is a build-system toolkit that operates on local file streams. All operations are local file I/O with no network persistence. Classified as stateless-utility.

> **Note:** This repository is functionally a library — an npm package with no deployable infrastructure, no running services, and no cloud resources. The user specified `repo_type: "application"`, so all 37 questions are evaluated. Many infrastructure, security, and operations questions score 1 because the corresponding capabilities are absent by design (a build tool has no VPC, no databases, no API gateway). These scores accurately reflect the repository's cloud modernization readiness and are not penalizing — they identify what would need to be built if this package were ever deployed as a cloud service.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.73 / 4.0 | 🟠 Needs Work |
| Application Architecture (APP) | 3.00 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 1.75 / 4.0 | 🟠 Needs Work |
| Security Baseline (SEC) | 1.29 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.33 / 4.0 | ❌ Not Present |
| **Overall** | **1.82 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | No IaC files exist — zero infrastructure is defined in code | Blocks all infrastructure automation; no reproducible deployments; triggers Move to Modern DevOps pathway |
| 2 | INF-Q1: Managed Compute | 1 | No compute infrastructure defined — no ECS, EKS, Lambda, or EC2 | No cloud deployment exists; triggers Move to Cloud Native and Move to Containers pathways |
| 3 | SEC-Q7: Application Security Pipeline | 1 | No SAST, DAST, or dependency vulnerability scanning in CI/CD pipeline | Vulnerabilities in dependencies reach consumers undetected; critical for widely-used npm package |
| 4 | INF-Q5: Network Security | 1 | No VPC, security groups, or network segmentation defined | No network isolation for any future cloud deployment |
| 5 | SEC-Q1: Audit Logging | 1 | No CloudTrail or audit logging configured | No audit trail for compliance or forensic analysis |

---

## Quick Agent Wins

### DevOps Agent

- **Prerequisite:** INF-Q11 = 3 (CI/CD pipeline exists). GitHub Actions workflows (`dev.yml`, `release.yml`) provide automated build, test, coverage, and release automation via release-please.
- **What it enables:** An agent that triggers CI builds, checks test status across the Node.js version matrix (22, 24) and OS matrix (ubuntu, windows, macos), monitors release-please PRs, and manages npm publish workflows. The agent could also monitor Coveralls coverage trends and flag regressions.
- **Additional steps:** Generate an API surface for interacting with the GitHub Actions workflows (e.g., via GitHub REST API). Consider adding structured JSON output from test runs to enable programmatic parsing by the agent.
- **Effort:** Low — existing CI/CD pipeline provides the automation surface; agent orchestrates via GitHub API.

### RAG-Based Knowledge Agent

- **Prerequisite:** Extensive documentation exists in the repository. The `docs/` directory contains 40+ Markdown files covering API reference (`docs/api/`), getting-started guides (`docs/getting-started/`), 25 recipes (`docs/recipes/`), plugin authoring guides (`docs/writing-a-plugin/`), and FAQ. `README.md` and `CONTRIBUTING.md` provide additional context.
- **What it enables:** A RAG-based knowledge agent that indexes all documentation and answers developer questions about gulp's API, task creation, plugin authoring, glob patterns, and streaming patterns. Could serve as an interactive documentation assistant for the 3000+ gulp plugin ecosystem.
- **Additional steps:** Index the `docs/` directory and `README.md` as the knowledge corpus. Consider generating embeddings using Amazon Bedrock for vector-based retrieval. The documentation is well-structured with clear headings and code examples, making it ideal for chunking and retrieval.
- **Effort:** Medium — documentation corpus exists and is well-structured; embedding generation and vector store setup needed.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2 = 2 (< 3, single package monolith) + INF-Q1 = 1 (< 3, no managed compute) |
| 2 | Move to Containers | Triggered | Medium | Medium | INF-Q1 = 1 (< 3, no compute) + no container definitions found; no Lambda/Fargate/ECS detected |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (not < 3) — no stored procedures or proprietary SQL; no commercial database engines detected |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = 1 (< 3) technically met, but no databases exist at all (neither self-managed nor managed) — pathway is not meaningful for a library with no data layer |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 4 (not < 3, stateless-utility calibration) — no data processing workloads exist |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (< 3, no IaC) + OPS-Q5 = 2 (< 3, no staged deployment) |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in context ("Streaming JavaScript build-system toolkit.") |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:**
The gulp package (v5.0.1) is a single npm package that composes three independent libraries — Undertaker (task management), vinyl-fs (file streams), and glob-watcher (file watching) — into a unified Gulp class with a singleton export (`index.js`). APP-Q2 scored 2: identifiable module boundaries exist via the dependency packages, but the Gulp singleton instance creates shared state across all operations. This is a single deployable unit published to npm.

**Compute Model Gaps:**
INF-Q1 scored 1: No cloud compute infrastructure exists. The package runs locally on developer machines via the `gulp` CLI command (`bin/gulp.js` → `gulp-cli`). There is no server, no container, no Lambda function, and no IaC defining any compute resources.

**Communication Pattern Context:**
APP-Q3 and APP-Q4 both scored 4 due to stateless-utility archetype calibration — synchronous, local function calls are the correct design for this build tool. These do not represent gaps.

**Recommended Decomposition Approach:**
See the [Decomposition Strategy](#decomposition-strategy) section below. For a build-tool library, traditional microservice decomposition does not directly apply. The recommended approach is Conditional/Adaptive: the component packages (undertaker, vinyl-fs, glob-watcher) are already independently published npm packages. If gulp were to become a cloud-deployed service (e.g., a remote build service), the Strangler Fig pattern would apply — extracting build capabilities into independent, containerized services.

**Representative AWS Services:** Lambda, API Gateway, Step Functions, EventBridge, ECS on EKS (per preference for EKS)
**Recommended Patterns:** Strangler Fig, Hexagonal Architecture (Ports and Adapters)
**AWS Prescriptive Guidance:** [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)

---

### Pathway: Move to Containers

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current Compute Model:**
No compute infrastructure exists. The package is distributed via npm and runs locally on developer machines. No EC2 instances, no AMIs, no auto-scaling groups are defined in any IaC (because no IaC exists). `bin/gulp.js` is a 3-line CLI entry point that delegates to `gulp-cli`.

**Container Readiness Indicators:**
- **Dependencies:** Well-defined in `package.json` with 4 runtime dependencies (glob-watcher, gulp-cli, undertaker, vinyl-fs)
- **Node.js version:** Requires Node.js >= 22 (modern, container-friendly)
- **No port bindings:** The package does not listen on any network port
- **Config externalization:** Minimal configuration — the package reads `gulpfile.js` from the user's project directory

**Recommended Container Orchestration Platform:**
Per preferences (`prefer: ["eks"]`, `avoid: ["self-managed-kubernetes"]`), if containerization is pursued for a remote build service scenario, use **Amazon EKS** with managed node groups or **Fargate** profiles to avoid self-managed Kubernetes overhead. For simpler use cases, **AWS App Runner** could host a containerized build-as-a-service API.

**Representative AWS Services:** ECS, EKS, Fargate, ECR, App Runner
**Migration Approach:** If the goal is to offer gulp builds as a cloud service, create a Dockerfile based on `node:22-slim`, install the package, and expose an API for submitting build tasks. A lift-and-containerize approach would start with a simple container running gulp CLI commands.
**AWS Container Migration Guidance:** [Containers on AWS](https://aws.amazon.com/containers/) · [EKS Workshop](https://www.eksworkshop.com/)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 1):**
Zero infrastructure is defined in code. No Terraform files (`.tf`), no CloudFormation templates, no CDK stacks, no Helm charts, and no Kustomize overlays were found in the repository. All infrastructure required for a cloud deployment would need to be created from scratch.

**Current CI/CD State (INF-Q11 = 3):**
CI/CD automation exists and is functional:
- `dev.yml`: Automated lint (ESLint), test (Mocha + nyc), and coverage (Coveralls) across a matrix of Node.js 22/24 and ubuntu/windows/macos-13. Runs on push to main and PR events.
- `release.yml`: Automated releases via Google's release-please-action, generating changelogs and version bumps.
- `atx-transform.yml`: AWS Transform CLI integration for automated code transformations.

The pipeline has automated build and test but lacks deployment stages (expected for a library — npm publish is managed via release-please).

**Deployment Strategy Gaps (OPS-Q5 = 2):**
npm publish via release-please is a direct-to-production release — once merged, the package is published to the npm registry with no staged rollout, canary testing, or gradual availability. For a library consumed by thousands of projects, a staged approach (e.g., npm dist-tags with `next` before promoting to `latest`) would reduce blast radius of regressions.

**Recommended DevOps Toolchain:**
Per preferences (`prefer: ["eventbridge"]`):
1. **IaC adoption:** Use AWS CDK (TypeScript, aligning with the JavaScript ecosystem) or Terraform to define any future cloud infrastructure.
2. **Staged npm publishing:** Add a `next` dist-tag workflow stage before promoting to `latest`.
3. **Security scanning:** Add `npm audit` and a SAST tool (e.g., Semgrep or Amazon CodeGuru Reviewer) to the CI pipeline.
4. **Dependency monitoring:** Enable Dependabot or Renovate for automated dependency updates.

**Representative AWS Services:** CodeBuild, CodePipeline, CDK, CloudWatch, X-Ray
**AWS DevOps Prescriptive Guidance:** [Getting Started with DevOps on AWS](https://docs.aws.amazon.com/prescriptive-guidance/latest/strategy-devops/welcome.html)

---

## Decomposition Strategy

> **Context:** APP-Q2 scored 2 — the gulp package is a single deployable unit (npm package) with identifiable module boundaries via its dependency packages, but shared state through the Gulp singleton instance. This section provides decomposition guidance adapted to the library/build-tool context.

### Current Monolith Characteristics

The gulp package (`index.js`, 53 lines) is a thin facade that composes three independent npm packages:

| Module | Package | Responsibility |
|--------|---------|----------------|
| **Task Management** | `undertaker` (^2.0.0) | `task()`, `series()`, `parallel()`, `registry()`, `tree()`, `lastRun()` |
| **File Streams** | `vinyl-fs` (^4.0.2) | `src()`, `dest()`, `symlink()` |
| **File Watching** | `glob-watcher` (^6.0.0) | `watch()` |
| **CLI** | `gulp-cli` (^3.1.0) | Command-line interface and gulpfile loading |

**Shared state:** The `Gulp` class inherits from `Undertaker` and creates a singleton instance (`var inst = new Gulp(); module.exports = inst;`). All method bindings (`this.watch.bind(this)`, etc.) share the same instance, meaning task registrations, file system state, and watch configurations are coupled through the singleton.

**Module boundaries:** Clear — each dependency is an independent npm package with its own repository, versioning, and test suite. Cross-module dependencies are minimal (only the `watch()` method bridges `glob-watcher` with `undertaker` via `this.parallel(task)`).

### Decomposition Approach Options

| Approach | Description | Applicability to Gulp | Level of Effort | Recommendation |
|----------|-------------|----------------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Incrementally extract services while keeping the monolith running | Applicable if migrating to a cloud build service: extract file streaming, task orchestration, and watch services independently while maintaining the npm package as the facade | Medium (6-12 months) | ✅ Recommended if building a cloud-hosted build service |
| **Conditional / Adaptive** | Containerize as-is, then selectively extract high-value modules | Most practical: containerize the gulp CLI as a build worker, then extract vinyl-fs and undertaker into separate microservices only if needed for independent scaling | Low to Medium (2-6 months) | ✅ **Recommended for this repository** — the component packages are already independently published; further decomposition only needed for cloud service scenarios |
| **Big-Bang Rewrite** | Rewrite as microservices from scratch | Not applicable — the existing architecture is well-structured with clear boundaries. A rewrite would be high risk with no proportional benefit | Very High (12+ months) | ⚠️ Recommended against |

### Pattern Recommendations

| Pattern | Purpose | Applicability to Gulp | AWS Prescriptive Guidance |
|---------|---------|----------------------|---------------------------|
| **Hexagonal Architecture** | Structure services with clear boundaries between business logic, ports, and adapters | **Highly applicable** — gulp already partially follows this pattern. `undertaker` is the core, `vinyl-fs` is a file-system adapter, `glob-watcher` is a file-system port. Formalizing this would make each component testable and portable. | [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |
| **Anti-corruption Layer** | Isolate new services from legacy data models | Applicable if extracting file streaming into a cloud service — the ACL would translate between local file paths and S3 object keys | [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) |
| **Event Sourcing** | Capture state changes as event sequences | Low applicability — gulp tasks are ephemeral; no persistent state changes to track | [Event sourcing pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html) |
| **Saga Pattern** | Manage distributed transactions across services | Low applicability — no multi-step business transactions in the build tool; task orchestration is handled by `undertaker/bach` | [Saga pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html) |

### Effort Estimation Factors

| Factor | Analysis | Signal |
|--------|-----------|--------|
| Module boundaries | **Low effort** — clear package structure, independent npm packages, minimal cross-dependencies | `package.json` dependencies show clean separation |
| Data coupling | **Low effort** — no shared database, no persistent state beyond in-memory singleton | `index.js` singleton is the only coupling point |
| Stored procedures | **Not applicable** — no database, no SQL | No `.sql` files found |
| Communication patterns | **Low effort** — all communication is synchronous local function calls (correct for stateless-utility) | `index.js` method delegation pattern |
| CI/CD maturity | **Low effort** — automated pipeline exists with multi-platform matrix testing | `.github/workflows/dev.yml` |
| Test coverage | **Low effort** — integration tests exist covering src, dest, watch, and CLI execution | `test/index.test.js`, `test/src.js`, `test/dest.js`, `test/watch.js` |

**Calibrated Effort Estimate:** Low — the package is already well-decomposed at the npm package level. If a cloud service deployment is the goal, containerization of the existing package is the recommended first step (2-4 weeks), with selective extraction of components only if independent scaling requirements emerge.

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute infrastructure is defined anywhere in the repository. No Terraform files (`.tf`), CloudFormation templates, CDK stacks, or any IaC artifacts were found. No `aws_ecs_*`, `aws_eks_*`, `aws_lambda_*`, or `aws_instance` resources exist. The package runs locally on developer machines via the `gulp` CLI (`bin/gulp.js` → `gulp-cli`). |
| **Gap** | All compute is on developer machines with no managed services. No cloud compute footprint exists. |
| **Recommendation** | If deploying as a cloud service, adopt containerized compute on Amazon EKS (per preference) with Fargate profiles to avoid self-managed node overhead. For serverless build tasks, consider AWS Lambda for short-lived file transformations. |
| **Evidence** | `bin/gulp.js`, `package.json`, absence of any `.tf`, `.cfn.yaml`, `cdk.json`, `Dockerfile` files |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database resources are defined in any configuration or IaC. No `aws_rds_*`, `aws_dynamodb_*`, `aws_docdb_*` resources. No database connection strings, no ORM configurations, no SQL migration files. The package has no data persistence layer — it operates on local file streams. |
| **Gap** | No database infrastructure exists (neither managed nor self-managed). |
| **Recommendation** | If a data persistence layer is needed for a cloud build service (e.g., build job metadata, artifact registry), adopt Amazon DynamoDB (per preference) for job tracking or Aurora for relational data. No action needed for the current library use case. |
| **Evidence** | `package.json` (no database driver dependencies), `index.js` (no database imports), absence of any database configuration files |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | **Archetype: stateless-utility.** No multi-step workflows exist that would require dedicated orchestration services. The package itself provides task orchestration (via `undertaker`/`bach`) for user-defined build tasks, but this is the library's purpose — not an infrastructure gap. No Step Functions, Temporal, or MWAA resources are needed. |
| **Gap** | N/A — dedicated workflow orchestration is not applicable for this archetype. The absence of Step Functions or equivalent is correct by design. |
| **Recommendation** | No action needed. Dedicated workflow orchestration is not applicable for a stateless build-tool library. If the tool is later deployed as a cloud build service, AWS Step Functions could orchestrate multi-step build pipelines. |
| **Evidence** | `index.js` (Undertaker-based task orchestration is the library's core feature), `package.json` (`undertaker` dependency) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | **Archetype: stateless-utility.** Synchronous local operations are the correct design for this build-system toolkit. The package processes local file streams via vinyl-fs — all I/O is synchronous Node.js stream piping with no network messaging. No messaging infrastructure is needed. |
| **Gap** | N/A — synchronous local I/O is appropriate for this archetype. Adopting async messaging would add operational complexity without architectural benefit. |
| **Recommendation** | Adopting async messaging is NOT recommended for this build tool — it would add operational complexity without architectural benefit. If the package is later deployed as a cloud build service, Amazon EventBridge (per preference) could be used for build event notifications. Avoid self-managed Kafka (per preference). |
| **Evidence** | `index.js` (synchronous stream piping via vinyl-fs), `package.json` (no messaging client dependencies) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, security groups, NACLs, or network configuration found. No IaC files define any network resources. The package runs locally on developer machines with no network deployment. |
| **Gap** | No network security configuration exists. No VPC, no private subnets, no security groups. |
| **Recommendation** | If deploying as a cloud service, define a VPC with private subnets, least-privilege security groups, and VPC endpoints for AWS service access. Use VPC Lattice for service-to-service communication within the VPC. |
| **Evidence** | Absence of any `.tf`, CloudFormation, or CDK files defining `aws_vpc`, `aws_subnet`, `aws_security_group` |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, CloudFront, or any load balancer is defined. The package has no network-facing API — it is a CLI tool invoked locally. |
| **Gap** | No managed API entry point exists. |
| **Recommendation** | If exposing build capabilities as a cloud service, use Amazon API Gateway (per preference) as the entry point with throttling, authentication, and request validation. API Gateway would front an EKS-hosted or Lambda-hosted build API. |
| **Evidence** | Absence of `aws_api_gateway_*`, `aws_apigatewayv2_*`, `aws_lb_*` in any IaC, `bin/gulp.js` (local CLI entry point only) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration found. No `aws_autoscaling_*` or `aws_appautoscaling_*` resources. No Lambda concurrency limits. No IaC exists to configure scaling. |
| **Gap** | No auto-scaling — all capacity would be statically provisioned in any deployment scenario. |
| **Recommendation** | If deploying on EKS (per preference), configure Horizontal Pod Autoscaler (HPA) and Cluster Autoscaler. If using Lambda for build tasks, configure reserved concurrency limits. |
| **Evidence** | Absence of any IaC defining auto-scaling resources |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration found. No `aws_backup_plan` resources, no `backup_retention_period` settings, no S3 versioning, no EBS snapshot policies. No data stores exist to back up. |
| **Gap** | No backup or recovery procedures exist. |
| **Recommendation** | No action needed for the current library use case. If a data persistence layer is added for a cloud service, configure automated backups with defined retention periods and PITR where supported. |
| **Evidence** | Absence of any backup-related IaC resources, absence of any data stores |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No multi-AZ configuration found. No `multi_az = true` settings, no `availability_zones` spanning multiple AZs. No IaC exists to define any deployment topology. |
| **Gap** | No high availability configuration — no multi-AZ deployment exists. |
| **Recommendation** | If deploying as a cloud service on EKS (per preference), configure node groups across 2+ AZs with cross-zone load balancing. For any RDS/Aurora databases, enable Multi-AZ. |
| **Evidence** | Absence of any IaC defining AZ configuration |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No IaC files found in the repository. No Terraform (`.tf`, `.tfvars`), no CloudFormation templates, no CDK stacks (`cdk.json`), no Helm charts (`Chart.yaml`), no Kustomize (`kustomization.yaml`). Zero percent of infrastructure is defined in code — because no cloud infrastructure exists. |
| **Gap** | No IaC — all infrastructure (if any were to exist) would need to be created manually. This is the most fundamental DevOps gap. |
| **Recommendation** | Adopt IaC using AWS CDK (TypeScript — aligns with the JavaScript ecosystem) or Terraform to define any future cloud infrastructure. Start with the CI/CD pipeline infrastructure and build worker compute resources. |
| **Evidence** | Complete absence of `.tf`, `.cfn.yaml`, `.cfn.json`, `cdk.json`, `Chart.yaml`, `kustomization.yaml` files in the entire repository |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GitHub Actions CI/CD pipelines are defined and functional. `dev.yml` runs automated lint (ESLint via `npm run lint`), test (Mocha via `npm test`), and coverage (Coveralls) across a matrix of Node.js versions (22, 24) and operating systems (ubuntu-latest, windows-latest, macos-13). Runs on push to main and pull requests. `release.yml` uses Google's release-please-action for automated semver releases and changelog generation. `atx-transform.yml` provides AWS Transform CLI integration. |
| **Gap** | Pipeline has automated build and test but no deployment stages (expected for a library). No security scanning (SAST, dependency audit) in the pipeline. No staged release process (npm publish is direct-to-production). |
| **Recommendation** | Add `npm audit` as a CI step for dependency vulnerability scanning. Add a SAST tool (Semgrep or Amazon CodeGuru Reviewer). Implement staged npm publishing with `next` dist-tag before promoting to `latest`. |
| **Evidence** | `.github/workflows/dev.yml` (lint + test + coverage matrix), `.github/workflows/release.yml` (release-please automation), `.github/workflows/atx-transform.yml` (ATX integration) |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | JavaScript (Node.js) is the sole programming language. The package uses CommonJS (`index.js`) with ESM support (`index.mjs`). Node.js >= 22 is required (`engines` in `package.json`). JavaScript has first-class AWS SDK coverage (`@aws-sdk/*`), broad cloud-native tooling, and a mature npm ecosystem with 2M+ packages. |
| **Gap** | No gap — JavaScript/Node.js has first-class AWS SDK support and mature cloud-native tooling. |
| **Recommendation** | No action needed. JavaScript is well-positioned for cloud-native development. The Node.js 22+ requirement ensures access to modern runtime features (ESM, top-level await, native fetch). |
| **Evidence** | `index.js` (CommonJS), `index.mjs` (ESM), `package.json` (`"engines": {"node": ">=22"}`), `eslint.config.js` |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Single npm package (single deployable unit to npm). `index.js` defines a `Gulp` class that inherits from `Undertaker` and attaches methods from `vinyl-fs` and `glob-watcher`. A singleton instance is exported (`var inst = new Gulp(); module.exports = inst;`). The package has identifiable module boundaries — `undertaker` (task management), `vinyl-fs` (file streams), `glob-watcher` (file watching) are independent npm packages with their own repos. However, the singleton pattern creates shared global state: task registrations, file system state, and watch configurations are all coupled through the single Gulp instance. |
| **Gap** | Single deployable unit with shared state through the Gulp singleton. Module boundaries are clear at the dependency level but the singleton export couples all functionality. No independent deployment of components is possible within the package itself. |
| **Recommendation** | The component packages are already independently published (undertaker, vinyl-fs, glob-watcher can be used directly). For the gulp package itself, consider a modular monolith pattern: formalize the module boundaries with explicit interfaces and eliminate the singleton export in favor of factory functions that allow independent instances. See the Decomposition Strategy section for detailed approach options. |
| **Evidence** | `index.js` (singleton pattern: `var inst = new Gulp(); module.exports = inst;`), `package.json` (4 runtime dependencies), `CONTRIBUTING.md` (documents module separation) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | **Archetype: stateless-utility.** Synchronous request/response is the correct design for this build tool. There is no inter-service communication — all operations are local function calls within a single Node.js process. `gulp.src()` reads files from the local filesystem as streams, `gulp.dest()` writes them back, and `gulp.watch()` monitors filesystem changes. The only communication pattern is synchronous Node.js stream piping, which is architecturally correct for a build-system toolkit. |
| **Gap** | No gap — synchronous local communication is appropriate for this archetype. |
| **Recommendation** | Converting to async inter-service communication is NOT recommended — this is a standalone build tool with no service-to-service boundaries. The current synchronous stream piping model is the correct architectural choice. |
| **Evidence** | `index.js` (synchronous method delegation: `Gulp.prototype.src = vfs.src;`), `index.mjs` (re-exports bound methods), `package.json` (no HTTP client or messaging dependencies) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | **Archetype: stateless-utility.** No operations exceed 30 seconds by design. The package processes local file streams — read, transform, and write operations are bounded by local I/O performance, not network latency or external service response times. `gulp.watch()` is a long-running process by design (monitoring filesystem changes), but it uses an event-driven model (chokidar) rather than blocking synchronous calls. All user-defined tasks support async completion via callbacks, promises, streams, and observables (documented in `docs/getting-started/4-async-completion.md`). |
| **Gap** | No gap — no operations exceed 30 seconds by design. The build tool's operations are bounded by local I/O. |
| **Recommendation** | Async job infrastructure is not applicable for the current build-tool surface. If deployed as a cloud build service where build jobs could exceed 30 seconds, implement async job processing with status polling using AWS Step Functions and DynamoDB (per preference) for job state tracking. |
| **Evidence** | `index.js` (stream-based operations with callback support), `docs/getting-started/4-async-completion.md` (async completion patterns) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The package uses semantic versioning (semver) for npm versioning — currently v5.0.1. Semver is applied consistently: `CHANGELOG.md` documents v5.0.0 breaking changes (Node.js 10.13+ minimum, stream encoding changes, glob behavior changes) and v5.0.1 bug fixes. The `release.yml` workflow uses release-please for automated semver version bumps. The library's API surface (module exports: src, dest, watch, task, series, parallel, etc.) is versioned via package.json semver. No HTTP API versioning (URL paths, headers) is present because there is no HTTP API. |
| **Gap** | Semver versioning is applied consistently but there is no explicit versioning strategy for the module export API beyond npm semver — no deprecation policy for individual API methods, no per-method versioning. |
| **Recommendation** | Document API deprecation policy for individual methods (e.g., `@deprecated` JSDoc annotations with migration guidance). Consider adding TypeScript type definitions (`.d.ts`) for compile-time API contract enforcement. The semver approach is appropriate for an npm library. |
| **Evidence** | `package.json` (`"version": "5.0.1"`), `CHANGELOG.md` (v5.0.0 breaking changes documented), `.github/workflows/release.yml` (release-please semver automation) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No service discovery mechanism exists — there are no services to discover. The package is a standalone library with no inter-service communication. No AWS Service Discovery, Istio, Consul, or environment variables pointing to service endpoints. No hard-coded service endpoints either, because the package does not call any external services. |
| **Gap** | No service discovery — no services exist to discover. |
| **Recommendation** | No action needed for the current library use case. If deployed as a microservices architecture, adopt AWS Cloud Map for service discovery or Kubernetes DNS-based discovery on EKS (per preference). |
| **Evidence** | `index.js` (no external service calls), `package.json` (no HTTP client dependencies), absence of any service endpoint configuration |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No S3 usage, no unstructured data storage, no document management system. The library processes local files via vinyl-fs streams (reading from filesystem globs, transforming via plugins, writing back to filesystem), but it does not persist unstructured data to any cloud storage. No `aws_s3_bucket` resources, no Textract calls, no document parsing libraries in dependencies. |
| **Gap** | No managed object storage for unstructured data. All file operations are local filesystem only. |
| **Recommendation** | If building a cloud build service, store build artifacts and intermediate files in Amazon S3 with lifecycle policies. Use S3 as the vinyl-fs adapter target (replacing local filesystem writes). Consider Amazon S3 File Gateway for seamless S3 integration without changing filesystem-based code paths. |
| **Evidence** | `index.js` (`Gulp.prototype.src = vfs.src; Gulp.prototype.dest = vfs.dest;` — local filesystem only), `package.json` (no S3 SDK dependency) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database access exists in the codebase. The library does not connect to any database — there are no scattered database connections because there are no database connections at all. Data access is limited to local filesystem I/O via the vinyl-fs library. |
| **Gap** | No data access layer exists because no database is used. |
| **Recommendation** | No action needed for the current library use case. If a data persistence layer is added for a cloud service, implement a centralized data access layer using a repository/DAO pattern from the start. |
| **Evidence** | `index.js` (no database imports), `package.json` (no database driver or ORM dependencies) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No database engines defined in IaC or configuration. No database of any kind exists in the repository — no RDS, DynamoDB, DocumentDB, or self-managed database. No engine version parameters, no version pinning, no migration files. |
| **Gap** | No database engine version management — no databases exist. |
| **Recommendation** | No action needed for the current library use case. If databases are added for a cloud service, explicitly pin engine versions in IaC and establish a version-update procedure. Prefer Aurora (per preference) with PostgreSQL or MySQL compatibility. Avoid Oracle (per preference). |
| **Evidence** | Absence of any database configuration, IaC resources, or connection strings in the entire repository |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, no triggers, no proprietary SQL constructs. No `.sql` files exist in the repository. All business logic is in the JavaScript application layer — the Gulp class, Undertaker task management, vinyl-fs file streaming, and glob-watcher file monitoring are all implemented in JavaScript. No database coupling exists. |
| **Gap** | No gap — all business logic is in the application layer with zero database coupling. |
| **Recommendation** | No action needed. The architecture is clean from a database coupling perspective. If databases are added for a cloud service, maintain this pattern: keep all business logic in the application layer and use databases only for data persistence. |
| **Evidence** | `index.js` (all logic in JavaScript), `package.json` (no database dependencies), absence of any `.sql` files |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging configured. No IaC defining `aws_cloudtrail` resources. No CloudWatch log retention policies. No log file validation or immutable storage configuration. No cloud infrastructure exists to generate audit logs. |
| **Gap** | No audit logging infrastructure exists. |
| **Recommendation** | If deploying cloud infrastructure, enable CloudTrail with log file validation and store logs in an S3 bucket with Object Lock for immutability. Configure CloudWatch log groups with appropriate retention periods. |
| **Evidence** | Absence of any CloudTrail, CloudWatch, or logging configuration in the repository |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No KMS keys or encryption configuration found. No `aws_kms_key` resources, no `kms_key_id` parameters on any data stores. No data stores exist to encrypt — the package processes local files only. |
| **Gap** | No encryption at rest configuration — no data stores exist. |
| **Recommendation** | If deploying cloud infrastructure with data stores, use customer-managed KMS keys for all sensitive data stores. Configure key rotation policies. For S3 build artifact storage, enable default encryption with SSE-KMS. |
| **Evidence** | Absence of any KMS or encryption configuration in the repository |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API endpoints exist to authenticate. No auth middleware, no OAuth2/JWT validation, no Cognito user pools, no Bearer token validation. The package is a CLI tool with no network-facing API surface. |
| **Gap** | No API authentication — no API exists. |
| **Recommendation** | If exposing a cloud build service API, implement OAuth2/JWT authentication using Amazon Cognito user pools or API Gateway authorizers (per preference for API Gateway). All endpoints should require token-based authentication. |
| **Evidence** | `bin/gulp.js` (CLI entry point, no HTTP server), `index.js` (no HTTP server, no auth middleware), `package.json` (no auth-related dependencies) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No centralized identity provider integration. No Cognito, no OIDC/SAML configuration, no IdP federation. The package has no authentication system — it is a CLI tool that runs with the invoking user's filesystem permissions. |
| **Gap** | No identity provider integration — no authentication system exists. |
| **Recommendation** | If deploying as a cloud service, integrate with Amazon Cognito for user authentication and enable SSO with an organizational IdP (Okta, Ping, Azure AD). |
| **Evidence** | Absence of any Cognito, OIDC, SAML, or authentication configuration in the repository |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | No secrets are hardcoded in application source code — `index.js`, `index.mjs`, and `bin/gulp.js` contain no credentials, API keys, or tokens. No `.env` files are committed to the repository (`.gitignore` excludes common secret file patterns). CI/CD workflows use GitHub Secrets for sensitive values: `secrets.GITHUB_TOKEN` for release automation and Coveralls, `secrets.ATXCI_API_URL` and `secrets.ATXCI_API_KEY` for ATX integration, and OIDC role assumption (`role-to-assume: ${{ vars.ATXCI_AWS_ROLE_ARN }}`) in `atx-transform.yml`. GitHub Secrets is an appropriate secrets management mechanism for CI/CD. |
| **Gap** | Secrets are managed via GitHub Secrets (appropriate for CI/CD) but no formal rotation policy is documented. No AWS Secrets Manager or HashiCorp Vault integration for runtime secrets (not needed for current library use case). |
| **Recommendation** | Document a secrets rotation policy for GitHub Secrets (especially `ATXCI_API_KEY`). For any future cloud service, use AWS Secrets Manager with automated rotation for database credentials and API keys. The current GitHub Secrets approach is appropriate for library CI/CD. |
| **Evidence** | `.github/workflows/dev.yml` (`secrets.GITHUB_TOKEN`, `secrets.ATXCI_API_URL`, `secrets.ATXCI_API_KEY`), `.github/workflows/atx-transform.yml` (OIDC: `role-to-assume`), `index.js` (no hardcoded credentials), `.gitignore` (excludes `.lock-wscript` and common artifacts) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No compute resources to harden. No SSM Patch Manager, no AWS Inspector, no hardened AMI references. CI/CD runs on GitHub-managed `ubuntu-latest` runners (which are maintained by GitHub). No EC2 instances, containers, or other compute resources are defined. |
| **Gap** | No compute hardening or patching strategy — no compute resources exist to harden. |
| **Recommendation** | If deploying compute resources on EKS (per preference), use Bottlerocket OS for container-optimized, hardened nodes. Enable AWS Inspector for vulnerability scanning on container images. Configure SSM Patch Manager for any EC2 instances. |
| **Evidence** | `.github/workflows/dev.yml` (runs on `ubuntu-latest` — GitHub-managed), absence of any compute hardening configuration |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SAST, DAST, or dependency vulnerability scanning tools are integrated into the CI/CD pipeline. The pipeline runs ESLint (linting, not security scanning) and Mocha tests. No `npm audit` step in any workflow. No Dependabot configuration (`.github/dependabot.yml` not found). No Snyk policy file (`.snyk` not found). No container scanning (no containers exist). The `.tidelift.yml` file configures Tidelift CI for dependency outdatedness checks but is not active security scanning in the pipeline. `SECURITY.md` provides a vulnerability reporting process via Tidelift but does not add scanning to the pipeline. |
| **Gap** | No security scanning in the CI/CD pipeline. For a widely-used npm package (gulp is installed by millions of projects), this is a critical gap — vulnerabilities in dependencies could propagate to all consumers. |
| **Recommendation** | Add `npm audit --audit-level=high` as a CI step in `dev.yml` to catch known dependency vulnerabilities. Enable Dependabot or Renovate for automated dependency update PRs. Add a SAST tool (e.g., Semgrep, Amazon CodeGuru Reviewer) for static analysis. These are high-priority additions for a widely-consumed package. |
| **Evidence** | `.github/workflows/dev.yml` (lint + test only, no security scanning steps), `.tidelift.yml` (outdatedness checks, not security scanning), `.github/SECURITY.md` (vulnerability reporting only), absence of `.github/dependabot.yml`, absence of `.snyk` |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumentation found. No OpenTelemetry SDK in `package.json` dependencies. No X-Ray instrumentation. No `traceparent` or `X-Amzn-Trace-Id` header propagation. The package has no network-based service communication to trace. |
| **Gap** | No distributed tracing — no service boundaries exist to trace across. |
| **Recommendation** | If deploying as a cloud service with multiple components, instrument OpenTelemetry SDK for distributed tracing with X-Ray as the backend. For the library itself, consider adding OpenTelemetry instrumentation hooks so consuming applications can trace gulp build operations. |
| **Evidence** | `package.json` (no OpenTelemetry or X-Ray dependencies), `index.js` (no tracing instrumentation) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found. No CloudWatch alarms on latency or error rates. No error budget tracking. No formal definition of acceptable service levels. The package is a library — SLOs are not typically defined for npm packages (they are defined for the services that consume them). |
| **Gap** | No SLOs defined — not applicable for a library, but would be critical for a cloud service. |
| **Recommendation** | No action needed for the current library use case. If deployed as a cloud build service, define SLOs for build completion time (p99 latency), build success rate, and API availability. Track error budgets using CloudWatch composite alarms. |
| **Evidence** | Absence of any SLO definitions, CloudWatch alarms, or error budget tracking in the repository |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom metrics published. No `cloudwatch.put_metric_data` calls. No business KPI tracking. The package uses Coveralls for code coverage tracking (a development metric, not a business metric). npm download counts are tracked externally by the npm registry but are not instrumented in the package. |
| **Gap** | No business metrics — only development metrics (code coverage via Coveralls). |
| **Recommendation** | For the library: consider adding telemetry opt-in for anonymous usage analytics (build times, plugin usage patterns) to inform development priorities. For a cloud build service: publish custom CloudWatch metrics for build completion rates, average build duration, and plugin failure rates. |
| **Evidence** | `.github/workflows/dev.yml` (Coveralls coverage tracking), `package.json` (nyc coverage reporter), absence of any CloudWatch or metrics instrumentation |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No anomaly detection or alerting configured. No CloudWatch anomaly detection, no error rate alarms, no latency alarms, no PagerDuty/OpsGenie integration. No cloud infrastructure exists to monitor. |
| **Gap** | No alerting configured — no infrastructure to alert on. |
| **Recommendation** | If deploying cloud infrastructure, configure CloudWatch anomaly detection on error rates and p99 latency for all critical paths. Set up composite alarms with PagerDuty or OpsGenie integration for on-call escalation. |
| **Evidence** | Absence of any CloudWatch alarms, anomaly detection, or alerting configuration in the repository |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | `release.yml` uses Google's release-please-action for automated npm releases — it creates release PRs with semver version bumps and changelogs. When merged, the package is published directly to the npm registry. This is a rolling deployment to production (npm `latest` tag) with no staged rollout, no canary testing, and no gradual availability. For a library consumed by thousands of projects, a direct-to-production publish means all consumers upgrading get the new version simultaneously. Basic health checks exist in the form of the CI test matrix, which must pass before release. |
| **Gap** | Direct-to-production npm publish with no staged rollout. No canary or blue/green equivalent for library releases. No npm dist-tag staging (e.g., publishing to `next` before `latest`). |
| **Recommendation** | Implement staged npm publishing: publish first to a `next` dist-tag for early adopter validation, then promote to `latest` after a soak period. Add a workflow step that runs the test suite against the published `next` version before promotion. This reduces blast radius for regressions in a widely-consumed package. |
| **Evidence** | `.github/workflows/release.yml` (release-please direct-to-production), `package.json` (`"version": "5.0.1"`) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Integration test suite exists using Mocha with nyc for coverage. Tests cover primary workflows: `test/index.test.js` (module exports, CLI execution against `.cjs` and `.mjs` gulpfiles), `test/src.js` (file reading via globs, stream output, buffer/stream modes), `test/dest.js` (file writing, directory creation, streaming writes), `test/watch.js` (filesystem change detection, task execution on change, parallel task integration, Japanese character path support). Tests run in the CI pipeline (`dev.yml`) across a matrix of Node.js 22/24 and ubuntu/windows/macos-13. The CLI integration tests (`cp.exec('node ' + cli, ...)`) verify end-to-end functionality. |
| **Gap** | Tests exist and run in CI for primary workflows. Coverage may have gaps in edge cases (e.g., error handling paths, large file handling, symbolic link edge cases). No contract tests for the public API surface. |
| **Recommendation** | Add contract tests for the public API surface to catch breaking changes before release. Consider adding property-based testing for glob pattern handling (a common source of edge case bugs). Integrate test coverage threshold enforcement in CI to prevent coverage regression. |
| **Evidence** | `test/index.test.js` (module export tests + CLI integration), `test/src.js` (file stream tests), `test/dest.js` (file write tests), `test/watch.js` (file watch tests), `.github/workflows/dev.yml` (test matrix execution), `package.json` (`"test": "nyc mocha --async-only"`) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks or automated incident response workflows found. No Systems Manager Automation documents, no Lambda-based remediation, no Step Functions for incident workflows. `SECURITY.md` exists but only documents the vulnerability reporting process via Tidelift — it is not an incident response runbook. No self-healing patterns are implemented. |
| **Gap** | No incident response automation — response is entirely ad hoc. |
| **Recommendation** | For the library: create runbooks for common release issues (npm publish failures, broken builds, security vulnerability response). For a cloud service: implement automated incident response using AWS Systems Manager Automation documents and Step Functions for common failure patterns. |
| **Evidence** | `.github/SECURITY.md` (vulnerability reporting process only), absence of any runbook files, SSM documents, or automated remediation |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No per-service dashboards, no alarms with named owners, no SLO definitions with team attribution. The repository has Coveralls integration for code coverage tracking, which provides a development quality signal but is not operational observability. No CODEOWNERS file referencing observability assets. No team tags on any resources. |
| **Gap** | No observability ownership — no operational monitoring exists to own. |
| **Recommendation** | For the library: add a CODEOWNERS file to define ownership of CI/CD workflows and test infrastructure. For a cloud service: create per-service dashboards with named owners and SLO definitions with team attribution. |
| **Evidence** | `.github/workflows/dev.yml` (Coveralls integration for coverage), absence of CODEOWNERS file, absence of any dashboard or alarm definitions |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resources exist to tag. No IaC with `tags` blocks, no `default_tags` in Terraform provider configuration, no `required-tags` AWS Config rules. No Tag Policies or SCPs. The package has no cloud infrastructure footprint. |
| **Gap** | No resource tagging — no cloud resources exist. |
| **Recommendation** | If deploying cloud infrastructure, establish a tagging standard from day one: `Environment`, `Service`, `Owner`, `CostCenter` as required tags. Use `default_tags` in the Terraform provider or CDK `Tags.of()` for consistent application. Enable Tag Policies in AWS Organizations for enforcement. |
| **Evidence** | Absence of any IaC files with tag configuration, absence of any AWS resource definitions |

---

## Learning Materials

The following learning resources are mapped to the triggered pathways identified in this analysis:

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
| `index.js` | INF-Q1, INF-Q3, INF-Q4, APP-Q2, APP-Q3, APP-Q4, DATA-Q1, DATA-Q2, DATA-Q4, SEC-Q3, SEC-Q5, OPS-Q1 | Main entry point; Gulp class definition with singleton export; stream method delegation; no database, networking, or external service calls |
| `index.mjs` | APP-Q1, APP-Q3 | ESM wrapper re-exporting bound methods from CommonJS index.js |
| `bin/gulp.js` | INF-Q1, INF-Q6, SEC-Q3 | CLI entry point (3 lines); delegates to gulp-cli; no HTTP server |
| `package.json` | INF-Q1, INF-Q2, INF-Q3, INF-Q4, APP-Q1, APP-Q2, APP-Q5, DATA-Q1, DATA-Q2, DATA-Q4, SEC-Q3, SEC-Q5, OPS-Q1, OPS-Q3, OPS-Q6 | Dependency manifest; 4 runtime deps (glob-watcher, gulp-cli, undertaker, vinyl-fs); 7 dev deps; Node.js >= 22 engine requirement; semver v5.0.1 |
| `.github/workflows/dev.yml` | INF-Q11, SEC-Q5, SEC-Q6, SEC-Q7, OPS-Q3, OPS-Q5, OPS-Q6, OPS-Q8 | CI pipeline: lint, test matrix (Node 22/24 × ubuntu/windows/macos), Coveralls coverage; uses GitHub Secrets for ATXCI credentials |
| `.github/workflows/release.yml` | INF-Q11, APP-Q5, OPS-Q5 | Automated release via release-please; semver version bumps; direct-to-production npm publish |
| `.github/workflows/atx-transform.yml` | INF-Q11, SEC-Q5 | AWS Transform CLI integration; OIDC role assumption; GitHub App Token for PR creation |
| `.github/SECURITY.md` | SEC-Q7, OPS-Q7 | Vulnerability reporting process via Tidelift; supported versions table (4.x.x) |
| `.tidelift.yml` | SEC-Q7 | Tidelift CI configuration; dependency outdatedness checks for eslint, expect, mocha |
| `eslint.config.js` | APP-Q1 | ESLint configuration using gulp team's shared config; ESM support for `.mjs` files |
| `CHANGELOG.md` | APP-Q5 | Version history; v5.0.0 breaking changes documented; v5.0.1 bug fixes |
| `CONTRIBUTING.md` | APP-Q2 | Documents module separation: Undertaker (task management), vinyl-fs (file streams), glob-watcher (file watching), gulp-cli (CLI) |
| `README.md` | Quick Agent Wins | Comprehensive project overview; sample gulpfile; API documentation links |
| `docs/api/` (15 files) | Quick Agent Wins, APP-Q5 | Complete API reference: concepts, src, dest, watch, task, series, parallel, registry, tree, lastRun, symlink, vinyl |
| `docs/getting-started/` (9 files) | Quick Agent Wins, APP-Q4 | Getting started guides: quick-start, creating-tasks, async-completion, working-with-files, globs, plugins, watching |
| `docs/recipes/` (25 files) | Quick Agent Wins | Usage recipes: browserify, BrowserSync, incremental builds, stream factories, templating, etc. |
| `docs/writing-a-plugin/` (6 files) | Quick Agent Wins | Plugin authoring guides: dealing with streams, using buffers, testing, guidelines |
| `test/index.test.js` | OPS-Q6 | Integration tests: module exports verification, CLI execution against gulpfile.cjs and gulpfile.mjs |
| `test/src.js` | OPS-Q6 | Integration tests: file reading via globs, stream output, buffer/stream modes, deep globs |
| `test/dest.js` | OPS-Q6 | Integration tests: file writing, directory creation, streaming writes, non-read file handling |
| `test/watch.js` | OPS-Q6 | Integration tests: filesystem change detection, task execution, parallel tasks, destructuring, Japanese character paths |
| `.editorconfig` | — | Code formatting standards (spaces, UTF-8, LF line endings) |
| `.npmrc` | — | npm configuration: package-lock=false |
| `.prettierignore` | — | Prettier exclusions: coverage/, .nyc_output/, CHANGELOG.md |
| `.gitignore` | SEC-Q5 | Excludes node_modules, coverage, build artifacts; no `.env` files present |
