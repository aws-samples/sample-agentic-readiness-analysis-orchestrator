# Modernization Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | gulpjs--gulp |
| **Date** | 2026-05-07 |
| **TD Version** | modernization-analysis |
| **Repo Type** | library |
| **Priority** | P2 |
| **Tags** | javascript, build-tool |
| **Context** | Streaming JavaScript build-system toolkit. |
| **Overall Score** | 2.38 / 4.0 |

**Surface Flags**: has_persistent_data_store=false, has_at_rest_data_surface=false, has_deployed_workload=false, has_api_surface=false, has_multi_instance_deployment=false

---

## Score Summary

| Category | Score | Rating | Severity Status |
|----------|-------|--------|-----------------|
| Infrastructure & DevOps (INF) | N/A | N/A — all questions not applicable for library | Ready |
| Application Architecture (APP) | 2.83 / 4.0 | 🟡 Partial | Needs Work |
| Data Platform Modernization (DATA) | 3.67 / 4.0 | ✅ Mature | Ready |
| Security Baseline (SEC) | 2.00 / 4.0 | 🟠 Needs Work | Critical |
| Operations & Observability (OPS) | 1.00 / 4.0 | ❌ Not Ready | Needs Work |
| **Overall** | **2.38 / 4.0** | **🟠 Needs Work** |  |

**Scoring Notes:**
- INF: All 11 questions N/A for library repo_type. Category excluded from overall.
- APP: (3+2+4+4+2+2) / 6 = 17/6 = 2.83
- DATA: DATA-Q1=4, DATA-Q2=3, DATA-Q3=N/A (no database, surface-gated), DATA-Q4=4 → (4+3+4)/3 = 11/3 = 3.67
- SEC: SEC-Q1=1, SEC-Q2=Not Evaluated (surface-gated), SEC-Q3=1, SEC-Q4=1, SEC-Q5=4, SEC-Q6=2, SEC-Q7=3 → (1+1+1+4+2+3)/6 = 12/6 = 2.00
- OPS: OPS-Q1=1 (only non-N/A question). OPS-Q2 through OPS-Q9 all N/A. Category score = 1.00.
- Overall: average of non-N/A categories = (2.83 + 3.67 + 2.00 + 1.00) / 4 = 9.50 / 4 = 2.38

---

## V6 Classification

**Tier: Pilot-Ready**

**Classification Rationale:** This repo has 1 High finding (SEC-Q1: audit logging, core question scoring 1), 7 Medium findings (OPS-Q1 score 1 non-core, SEC-Q3 score 1 non-core, SEC-Q4 score 1 non-core, APP-Q2 score 2, APP-Q5 score 2, APP-Q6 score 2, SEC-Q6 score 2), and 2 Low findings (APP-Q1 score 3, SEC-Q7 score 3). Rule matched: "1 High → Pilot-Ready." Note: ARA's "1 High" is an agent-deployment gate; MOD's "1 High" is typically a single modernization gap and maps to Pilot-Ready instead of Remediation Required.

**Classification Consistency Check:** ⚠️ **DIVERGENT** — The V5 overall score of 2.38 yields V5 band "Needs Work" (1.5–2.4), which is equivalent to V6 "Remediation Required" per the equivalence table. However, V6 severity counts (1 High) map to "Pilot-Ready." Reason: The single High finding (SEC-Q1: audit logging) is a genuine gap but does not represent systemic modernization deficiency — 6 of the 7 Medium findings reflect expected characteristics of a library repo_type (no API auth, no identity integration, no distributed tracing) rather than actionable remediation items. The V5 numeric score is depressed by these library-inherent Score 1 evaluations, while V6 severity correctly classifies them as non-core (Medium) rather than critical (High).

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | OPS-Q1: Distributed Tracing | 1 | No distributed tracing instrumented in the library | Consumers cannot trace operations through gulp in their distributed builds |
| 2 | SEC-Q1: Audit Logging | 1 | No audit logging for library operations | No structured logging of task execution or file transformation events |
| 3 | SEC-Q3: API Authentication | 1 | No API authentication (library exposes no HTTP API) | Expected for a local build tool — no network surface exists |
| 4 | SEC-Q4: Centralized Identity | 1 | No centralized identity integration | Expected for a local build tool — no user identity handling |
| 5 | APP-Q2: Monolith vs Microservices | 2 | Single monolithic class coupling all functionality | Limited decomposability; all functionality in one Gulp constructor |

---

## Quick Agent Wins

No Quick Agent Wins identified. This is a library repository with no deployed infrastructure, no API surface, no CI/CD deployment pipeline (only build/publish), and no structured logging. The system lacks the foundational capabilities (API documentation, deployment automation, structured logging) needed to support agent integration. Address the gaps identified in this analysis before pursuing agent opportunities.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Applicable | — | — | This is a `library` repository. This pathway does not apply. |
| 2 | Move to Containers | Not Applicable | — | — | This is a `library` repository. This pathway does not apply. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (no stored procedures); no commercial DB engines detected. Trigger conditions not met. |
| 4 | Move to Managed Databases | Not Applicable | — | — | This is a `library` repository. This pathway does not apply. |
| 5 | Move to Managed Analytics | Not Applicable | — | — | This is a `library` repository. This pathway does not apply. |
| 6 | Move to Modern DevOps | Not Applicable | — | — | This is a `library` repository. This pathway does not apply. |
| 7 | Move to AI | Not Triggered | — | — | No AI/agent intent detected in portfolio or service context. |

---

## Detailed Findings

### Infrastructure & DevOps (INF)

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

---

### Application Architecture (APP)

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 3 — Low |
| **Finding** | The library is written in JavaScript (Node.js >= 22) with dual CJS/ESM module support. Uses modern Node.js version requirement. However, the source code uses legacy patterns: `var` declarations, `util.inherits()` for prototypal inheritance, and callback-style APIs rather than ES6 classes, `const`/`let`, and async/await. No TypeScript. AWS SDK is not used (not relevant for a build tool). |
| **Gap** | Language version is modern (Node.js 22+) but code style is legacy JavaScript — `var`, `util.inherits()`, callback patterns. This is a framework/SDK lag signal within the JavaScript ecosystem. |
| **Recommendation** | Consider modernizing source code to ES6+ patterns (classes, const/let, async/await) to improve maintainability and align with the Node.js 22+ requirement. This is a code quality improvement, not a blocking modernization gap. |
| **Evidence** | `package.json` (engines.node >= 22), `index.js` (var, util.inherits), `index.mjs` (ESM wrapper) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 2 — Medium |
| **Finding** | Gulp is a single npm package that delegates to 4 tightly-coupled core dependencies: `glob-watcher`, `gulp-cli`, `undertaker`, and `vinyl-fs`. The main `index.js` constructs a single Gulp class that inherits from Undertaker and attaches methods from vinyl-fs and glob-watcher. While there are clear module boundaries at the npm level, the Gulp class directly couples all functionality into a single constructor — it is a monolithic design within the library context. |
| **Gap** | Single deployable unit with direct coupling to all 4 dependencies through prototypal inheritance and property assignment. No interface abstraction between the core modules. Modules are separate npm packages but assembled monolithically. |
| **Recommendation** | For a library of this size (~60 lines of core logic), the current single-package architecture is appropriate. The delegation to separate npm packages (undertaker, vinyl-fs, glob-watcher) already provides module boundaries. No decomposition needed. |
| **Evidence** | `index.js` (single Gulp constructor coupling all modules), `package.json` (4 runtime dependencies) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | As a library, gulp does not have inter-service communication. Its internal APIs use Node.js streams (async by nature) and callback/promise patterns. The streaming paradigm is the core architectural choice and is appropriate for a build tool library. No sync vs async communication gap exists because there are no service boundaries. |
| **Gap** | N/A |
| **Recommendation** | N/A — library has no inter-service communication to evaluate. |
| **Evidence** | `index.js` (stream-based API via vinyl-fs), `package.json` (glob-watcher for async file watching) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Gulp's design is inherently asynchronous — all task execution is async (via Undertaker's series/parallel), file watching is non-blocking (glob-watcher), and stream processing is event-driven. The library correctly handles long-running operations through its streaming architecture. |
| **Gap** | N/A |
| **Recommendation** | N/A — long-running operations (build tasks, file watching) are already handled asynchronously by design. |
| **Evidence** | `index.js` (async task execution via Undertaker, stream-based I/O via vinyl-fs, async watch via glob-watcher) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 2 — Medium |
| **Finding** | The library uses semver versioning (currently v5.0.1) for the npm package itself, which provides backward compatibility guarantees at the package level. However, there is no formal API versioning strategy within the library's exported surface — no versioned interfaces, no deprecation annotations, and no documented API compatibility policy beyond standard semver. The `exports` field in package.json provides CJS/ESM entry points but not versioned API paths. |
| **Gap** | No formal API versioning strategy beyond npm semver. No deprecation annotations or versioned interfaces for consumers relying on specific API shapes. |
| **Recommendation** | For an npm library, semver is the standard versioning mechanism and is already in place. Consider adding JSDoc `@deprecated` annotations for methods planned for removal in future majors, and documenting API stability guarantees per export in the README. |
| **Evidence** | `package.json` (version: "5.0.1", exports field), absence of @deprecated annotations in source |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 — Medium |
| **Finding** | The library requires its dependencies via hardcoded `require()` calls in `index.js`. While this is the standard Node.js module resolution pattern for libraries, the library has no plugin discovery mechanism — plugins are loaded by consumers, not discovered dynamically. The gulp plugin ecosystem relies on naming conventions (gulp-*) rather than a registry or discovery service. |
| **Gap** | No dynamic plugin discovery mechanism. Dependencies are hardcoded require statements. Plugin ecosystem relies on naming convention only. |
| **Recommendation** | For a build-tool library, the current require-based dependency resolution is appropriate. The plugin ecosystem (3000+ gulp plugins) uses npm as the discovery registry with the `gulp-*` naming convention. No architectural change needed for service discovery. |
| **Evidence** | `index.js` (hardcoded require statements for all 4 dependencies) |

---

### Data Platform Modernization (DATA)

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Gulp is a build tool that processes files via Node.js streams (vinyl-fs). It reads source files from the filesystem and writes outputs to the filesystem. This is the correct design for a local build tool — it transforms files on the developer's machine. There is no unstructured data storage concern because the library does not persist data; it transforms streams. |
| **Gap** | N/A |
| **Recommendation** | N/A — file streaming is the correct data handling pattern for a build tool library. |
| **Evidence** | `index.js` (vfs.src, vfs.dest for stream-based file I/O) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 — Low |
| **Finding** | The library has a unified data access pattern through vinyl-fs — all file operations go through `gulp.src()` and `gulp.dest()`, providing a consistent stream-based API for file I/O. This is a clean, centralized data access pattern. However, the watch functionality (`glob-watcher`) operates through a separate code path that does not go through vinyl-fs. |
| **Gap** | Watch functionality uses a separate access path (glob-watcher) outside the primary vinyl-fs data access layer. Minor inconsistency. |
| **Recommendation** | The current design is architecturally sound for a build tool. The separation between file transformation (vinyl-fs) and file watching (glob-watcher) is a valid design decision. No change needed. |
| **Evidence** | `index.js` (Gulp.prototype.src = vfs.src, Gulp.prototype.dest = vfs.dest, watch uses glob-watcher separately) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This library does not use any database. No database engine versions to evaluate. `has_persistent_data_store` is false. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No database dependencies in `package.json`; no SQL files or ORM configurations in repository. |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs. All logic is in the application (library) layer. The library has no database interaction whatsoever. |
| **Gap** | N/A |
| **Recommendation** | N/A — no database coupling exists. |
| **Evidence** | No SQL files, no database driver dependencies in `package.json`, no ORM configurations. |

---

### Security Baseline (SEC)

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 — High |
| **Finding** | No audit logging infrastructure. No CloudTrail or equivalent logging configured. As a library published to npm, there is no runtime infrastructure to audit. The library itself does not produce audit logs for its operations (task execution, file transformations). |
| **Gap** | No audit logging for library operations. No structured logging of task execution, file operations, or build activities. |
| **Recommendation** | Consider adding structured logging output (via a logging interface that consumers can configure) for task execution events. This would enable consumers to integrate gulp operations into their audit trails. However, for a build-tool library this is a low-priority enhancement. |
| **Evidence** | No logging library in `package.json` dependencies; no log output statements in `index.js`. |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This system has no deployed data-at-rest surface — no database, S3 bucket, EBS volume, or similar. SEC-Q2 does not apply. `has_at_rest_data_surface` is false. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | No IaC, no storage resources, no runtime deployment — pure library published to npm. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 — Medium |
| **Finding** | The library exposes no HTTP API endpoints. It is consumed programmatically via `require('gulp')` or `import gulp from 'gulp'`. There is no network-facing surface to authenticate. The CLI (`bin/gulp.js`) runs locally and does not accept network requests. |
| **Gap** | No API authentication — but this is expected for a build-tool library with no network surface. This score reflects absence rather than a security vulnerability. |
| **Recommendation** | No action needed. A build-tool library consumed locally does not require API authentication. If gulp were to expose a remote build server API in the future, authentication would be required at that point. |
| **Evidence** | `bin/gulp.js` (CLI entry point, local execution only), `index.js` (no HTTP server, no network listeners) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 — Medium |
| **Finding** | No centralized identity provider integration. The library does not handle user identity or authentication. It runs as a local build tool on the developer's machine. |
| **Gap** | No identity integration — expected for a local build tool library. |
| **Recommendation** | No action needed. A local build-tool library does not require centralized identity integration. |
| **Evidence** | No auth-related dependencies in `package.json`; no identity configuration files in repository. |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No plaintext credentials in the repository. The library source code contains no secrets, API keys, or credentials. CI/CD workflows use GitHub Secrets for tokens (`${{ secrets.GITHUB_TOKEN }}`, `${{ secrets.ATXCI_API_URL }}`, `${{ secrets.ATXCI_API_KEY }}`). No `.env` files committed. |
| **Gap** | N/A |
| **Recommendation** | N/A — secrets are properly managed through GitHub Secrets in CI/CD workflows. |
| **Evidence** | `.github/workflows/dev.yml` (secrets referenced via `${{ secrets.* }}`), no `.env` files, no hardcoded credentials in source. |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 — Medium |
| **Finding** | The CI/CD pipeline runs on GitHub Actions with `ubuntu-latest`, `windows-latest`, and `macos-13` runners. These are GitHub-managed and auto-patched. However, there is no explicit vulnerability scanning of the library code or its dependencies in the pipeline. The `package.json` uses `overrides` to pin specific versions of transitive dependencies (`diff`, `serialize-javascript`) suggesting awareness of vulnerable transitive deps, but this is manual rather than automated. |
| **Gap** | No automated vulnerability scanning in CI/CD. Dependency version overrides suggest manual security awareness but no systematic approach. |
| **Recommendation** | Add Dependabot or npm audit to the CI pipeline to automate dependency vulnerability detection. The manual overrides in package.json demonstrate security awareness but should be augmented with automated scanning. |
| **Evidence** | `.github/workflows/dev.yml` (GitHub-managed runners), `package.json` (overrides for diff and serialize-javascript) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 3 — Low |
| **Finding** | The repository has ESLint configured for static analysis (eslint.config.js with eslint-config-gulp), and the CI pipeline runs linting before tests (`npm run lint`). The `overrides` in package.json patch known vulnerable transitive dependencies. However, there is no dedicated SAST tool (SonarQube, Semgrep) and no automated dependency scanning (Dependabot, Snyk, npm audit) integrated into the pipeline. |
| **Gap** | No dedicated SAST tool or automated dependency vulnerability scanning in CI/CD. ESLint provides code quality but not security-specific analysis. |
| **Recommendation** | Add a `.github/dependabot.yml` configuration to enable automated dependency vulnerability alerts. Consider adding `npm audit` as a CI step. For a library of this size, a full SAST tool may be overkill — Dependabot + npm audit would be sufficient. |
| **Evidence** | `.github/workflows/dev.yml` (eslint in pipeline), `eslint.config.js`, `package.json` (no security scanning dependencies), absence of `.github/dependabot.yml` |

---

### Operations & Observability (OPS)

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 — Medium |
| **Finding** | No distributed tracing instrumentation in the library. No OpenTelemetry SDK, X-Ray instrumentation, or trace ID propagation. The library does not emit traces or propagate trace context through its streaming pipeline. |
| **Gap** | No tracing instrumentation. Consumers cannot trace operations through gulp's task execution or file streaming pipeline. In CI/CD environments where gulp runs as part of a larger distributed build system, this prevents end-to-end visibility. |
| **Recommendation** | Consider adding optional OpenTelemetry instrumentation for task execution spans (task start/end, duration, success/failure). This would allow consumers using distributed tracing to see gulp operations in their traces. Implement as an opt-in plugin or optional dependency to avoid adding overhead for users who don't need tracing. |
| **Evidence** | No OpenTelemetry or tracing dependencies in `package.json`; no trace-related code in `index.js`. |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `library` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |

---

## Learning Materials

No pathways triggered — no pathway-specific learning materials applicable. Refer to the [AWS SkillBuilder](https://skillbuilder.aws/) catalog for general cloud architecture training.

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `package.json` | APP-Q1, APP-Q2, APP-Q5, APP-Q6, DATA-Q1, DATA-Q3, DATA-Q4, SEC-Q5, SEC-Q6, SEC-Q7, OPS-Q1 | Dependency manifest, version, engines, exports, overrides |
| `index.js` | APP-Q1, APP-Q2, APP-Q3, APP-Q4, APP-Q6, DATA-Q1, DATA-Q2, SEC-Q3, OPS-Q1 | Main library source — Gulp constructor, prototypal inheritance, stream API |
| `index.mjs` | APP-Q1 | ESM wrapper for dual CJS/ESM support |
| `bin/gulp.js` | SEC-Q3 | CLI entry point — local execution only |
| `.github/workflows/dev.yml` | SEC-Q5, SEC-Q6, SEC-Q7 | CI/CD pipeline — lint, test, coverage across Node 22/24 on 3 OSes |
| `.github/workflows/release.yml` | SEC-Q5 | Release automation via release-please |
| `eslint.config.js` | SEC-Q7 | ESLint configuration for static analysis |
| `.npmrc` | APP-Q1 | Package configuration (package-lock=false) |
