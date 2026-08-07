# ARA Scoring Model

> **Purpose:** Loaded by the Agentic Readiness Analysis (ARA) TD. Defines the evaluation tiers, severity model, unified severity/category display names, RISK-tier assignment, service-archetype classification, and the readiness-profile table. Read this before assigning any severity or profile.

---

### Evaluation Tiers

Not all 43 questions are evaluated for every service. Questions are organized into two tiers:

**Core (25 questions)** — Always evaluated for applicable repo types. These directly determine whether an agent can safely call this service:

| Section | Core Questions | Why Core |
|---------|---------------|----------|
| AUTH | Q1, Q2, Q3, Q4, Q5, Q6, Q7 (all 7) | Identity is always critical for agent safety |
| API | Q1, Q2, Q3, Q4 | Minimum viable integration surface |
| STATE | Q1, Q5, Q6 | Write safety and rate protection |
| DATA | Q1, Q2, Q4, Q6 | Data classification, residency, input validation, PII protection |
| OBS | Q1, Q2 | Debuggability of agent-initiated requests |
| ENG | Q1, Q2, Q3 | Infrastructure governance and deployment safety |
| HITL | Q3 | Agent testing environment |
| DISC | Q1 | Schema stability for agent tool bindings |

**Extended (18 questions)** — Evaluated only when triggered by service characteristics (archetype, scope, or detected patterns). When not triggered, recorded as "Not Evaluated (extended)" and excluded from scoring.

| Question | Trigger Condition |
|----------|------------------|
| API-Q5 | Always evaluated as INFO |
| API-Q6 | Service has operations >30s OR long-running workflows |
| API-Q7 | Service has state changes (stateful-crud, orchestrator) |
| API-Q8 | Always evaluated as INFO |
| STATE-Q2 | Service has persistent state (stateful-crud, data-gateway, orchestrator) |
| STATE-Q3 | agent_scope is write-enabled AND service has persistent state |
| STATE-Q4 | Service has external dependencies (calls other services or external APIs) |
| STATE-Q7 | Service is P0 priority OR is on the critical path |
| HITL-Q1 | agent_scope is write-enabled |
| HITL-Q2 | agent_scope is write-enabled |
| DATA-Q3 | Service has list/query endpoints with potentially unbounded results |
| DATA-Q5 | Service has persistent state (stateful-crud, data-gateway, orchestrator) |
| DATA-Q7 | Always evaluated as INFO |
| DISC-Q2 | Always evaluated as INFO |
| DISC-Q3 | Always evaluated as INFO |
| OBS-Q3 | Always evaluated as INFO |
| ENG-Q4 | Always evaluated (but INFO for stateless-utility) |
| ENG-Q5 | Service has persistent data stores |

### Evaluation Tier by Repo Type and Archetype

| Configuration | N/A | Core | Extended Triggered | Total Evaluated |
|--------------|-----|------|--------------------|-----------------|
| application / stateless-utility / read-only | 0 | 25 | ~3 (INFOs only) | ~28 |
| application / stateless-utility / write-enabled | 0 | 25 | ~5 | ~30 |
| application / stateful-crud / read-only | 0 | 25 | ~10 | ~35 |
| application / stateful-crud / write-enabled | 0 | 25 | ~14 | ~39 |
| application / orchestrator / read-only | 0 | 25 | ~8 | ~33 |
| application / orchestrator / write-enabled | 0 | 25 | ~11 | ~36 |
| application / data-gateway / read-only | 0 | 25 | ~7 | ~32 |
| application / event-processor / read-only | 0 | 25 | ~4 | ~29 |
| infrastructure-only | 29 | 14 | 0 | 14 |
| deployment-config | 35 | 8 | 0 | 8 |
| library | 5 | 25 | ~8 | ~33 |
| monorepo | per-service | per-service | per-service | per-service |

Each question is scored using a severity model:

| Severity | Meaning | Implication |
|----------|---------|-------------|
| **BLOCKER** | Must resolve before any agent deployment. | Creates compliance exposure, data integrity risk, or failure-at-scale risk. |
| **RISK-SAFETY** | Affects agent safety — unaddressed could cause the agent to cause harm. | Determines readiness profile. Must address for safe agent operation. |
| **RISK-QUALITY** | Affects agent effectiveness, not safety. | No profile impact — informational for prioritization. Address as capacity allows. |
| **INFO** | No immediate gating impact. Shapes architecture decisions. | Feeds agent design and orchestration decisions. Not a deployment gate. |

Five questions are **conditional BLOCKERs** (⚡) — their severity depends on context (typically `agent_scope` write-enabled vs read-only): API-Q4, STATE-Q1, AUTH-Q6, DATA-Q1, and DATA-Q2. DATA-Q1 additionally uses a tiered sub-check model (see its section for B1/B2/B3 evaluation).

**The severity in each question's heading is the ceiling.** A question's severity MUST come from its `#### <question_id>:` heading and MAY NOT be raised above it, no matter how severe the evidence found is. Only two mechanisms move a severity, and both are enumerated in this document:

- The **9 ⚡ questions** (the 5 conditional BLOCKERs above, plus the scope-calibrated HITL-Q1, HITL-Q2, STATE-Q3, STATE-Q6) resolve per `agent_scope`, as specified in each question's own section.
- **Surface-flag and archetype calibration** only ever DOWNGRADES (see Step 0.3).

Every other question carries the fixed severity in its heading. In particular, severe evidence on a RISK-SAFETY question — hardcoded production credentials on AUTH-Q5, SQL injection on DATA-Q4 — is reported AS RISK-SAFETY. Escalating it to BLOCKER is a rubric violation, not a judgement call: `blocker_count` feeds the readiness profile arithmetic directly (see Readiness Profile Determination), so a single unauthorized escalation silently moves the repository to a stricter tier than the rubric assigns. Describe the severity of the evidence in the finding's `evidence` and `recommendation` text; do not encode it in the severity field.

### Unified Severity and Category Display Names

A unified severity vocabulary and canonical category display names are emitted on every finding so that a single webapp and portfolio aggregator can consume ARA and MOD findings side-by-side.

#### Unified Severity Mapping

Every finding carries a unified severity tag alongside its native ARA severity:

| Native ARA Severity | Unified Severity | `ara_metadata.safety_impact` |
|---|---|---|
| BLOCKER (unconditional) | High | true if agent-safety hazard, else false |
| BLOCKER (conditional, resolved as BLOCKER) | High | per conditional-resolution reasoning |
| RISK-SAFETY | Medium | true (always) |
| RISK-QUALITY | Medium | false (always) |
| INFO (when finding emitted) | Low | false |
| Passing question | (no finding) | n/a |
| N/A / Not Evaluated | (no finding, recorded in `evaluations[]`) | n/a |

The unified severity is emitted as the top-level `severity` field on each finding. The native ARA severity is preserved in `ara_metadata.native_severity`.

#### Category Display Names

Every finding carries both a short `category_id` code (the rubric section identifier, used as question_id prefix) and a webapp-facing `category` display name. The canonical mapping:

| `category_id` (short code) | `category` (display name) |
|---|---|
| `API` | API Surface |
| `AUTH` | Authentication & Authorization |
| `STATE` | State Management |
| `HITL` | Human-in-the-Loop |
| `DATA` | Data Accessibility |
| `DISC` | Discovery & Documentation |
| `OBS` | Observability |
| `ENG` | Engineering Maturity |

Both `category_id` and `category` are REQUIRED fields on every finding. Consumers (webapp filter chips, portfolio aggregation) use the display name directly.

#### DATA-Q* Namespace Collision

The short code `DATA` is shared between ARA and the Modernization analysis (MOD). ARA `DATA-Q1`..`DATA-Q7` and MOD `DATA-Q1`..`DATA-Q4` are DIFFERENT questions and MUST NOT be conflated. The unique join key across analysis types is `(analysis_type, question_id)`, never `question_id` alone. ARA `DATA` disambiguates to display name "Data Accessibility"; MOD `DATA` disambiguates to "Data Platform".

### RISK Tier Assignment

Each RISK-severity question is assigned to exactly one tier. The assignment is static — it does not depend on service characteristics. Scope-calibrated RISK questions (HITL-Q1, HITL-Q2, STATE-Q3, STATE-Q6) only count toward totals when agent_scope is write-enabled (they downgrade to INFO under read-only scope).

**RISK-SAFETY (16 questions):**

| Question ID | Topic | Safety Rationale |
|-------------|-------|------------------|
| AUTH-Q2 | Scoped permissions | Overly broad agent permissions create blast radius risk |
| AUTH-Q3 | Action-level authorization | Agent could delete when only read is intended |
| AUTH-Q4 | Identity propagation | Agent-on-behalf-of-user privilege escalation risk |
| AUTH-Q5 | Credential management | Hardcoded/unrotated credentials exposable via prompt injection |
| AUTH-Q6 | Audit logging | No audit trail for agent actions = undetectable harm |
| AUTH-Q7 | Identity suspension | Cannot revoke a compromised agent identity |
| STATE-Q1 | Compensation/rollback | Agent-initiated writes cannot be undone |
| STATE-Q3 | Concurrency controls | Race conditions from concurrent agent instances corrupt state |
| STATE-Q4 | Circuit breakers | Runaway agent loops cascade through dependencies |
| STATE-Q5 | Rate limiting | Agent traffic storms overwhelm services |
| STATE-Q6 | Blast radius limits | Agent error blast radius unbounded without transaction limits |
| DATA-Q1 | Sensitive data scoping | Agent-facing APIs leak sensitive fields (B1 read-only, or B2 access differentiation missing) |
| DATA-Q2 | Data residency | Agent moves data across compliance boundaries |
| DATA-Q6 | PII in logs | Agent actions leak PII into observable surfaces |
| HITL-Q1 | Draft/pending state | No draft state for reversible agent-proposed writes |
| HITL-Q2 | Approval gates | No human approval option for high-risk agent actions |

**RISK-QUALITY (17 questions):**

| Question ID | Topic | Quality Rationale |
|-------------|-------|-------------------|
| API-Q2 | Machine-readable spec | Agent tool generation requires manual work |
| API-Q3 | Structured errors | Agent cannot distinguish retriable vs terminal errors |
| API-Q6 | Async operation support | Long-running ops fail against agent timeouts |
| STATE-Q2 | Queryable current state | Agent cannot inspect state before action |
| STATE-Q7 | Degradation signaling | Agent reasons on stale/degraded data without awareness |
| DATA-Q3 | Pagination | Agent gets unbounded result sets |
| DATA-Q4 | Input validation | Agent sends malformed payloads without rejection |
| DATA-Q5 | Temporal metadata | Agent cannot reason about data freshness |
| DISC-Q1 | Schema versioning | Agent tool bindings break silently |
| OBS-Q1 | Tracing | Cannot debug agent-initiated requests |
| OBS-Q2 | Alerting | No alerts for agent anomalies |
| ENG-Q1 | Infra governance | No IaC = manual, error-prone changes |
| ENG-Q2 | CI/CD + contracts | Agent tool breakage not caught in pipeline |
| ENG-Q3 | Rollback | Cannot roll back agent-breaking deployments |
| ENG-Q4 | Test coverage | Insufficient test coverage for agent paths |
| ENG-Q5 | Encryption at rest | Data at rest unencrypted |
| HITL-Q3 | Sandbox/staging | No safe environment to test agent behavior |

Note: The 5 conditional BLOCKER questions (API-Q4, STATE-Q1, AUTH-Q6, DATA-Q1, DATA-Q2) resolve to different severities based on `agent_scope`. When the conditional resolves to RISK (read-only scope), their *base* severity is RISK-SAFETY — so STATE-Q1, AUTH-Q6, and DATA-Q2 appear in the RISK-SAFETY tier table above. When the conditional resolves to BLOCKER (write-enabled scope), they are counted as BLOCKERs, not RISK-SAFETY. The tier label applies only when the resolved severity is RISK. DATA-Q1 is additionally tiered: B1 resolves to BLOCKER (write-enabled) or RISK-SAFETY (read-only), B2 resolves to RISK-SAFETY when triggered, B3 resolves to INFO when triggered; the overall DATA-Q1 severity is the highest sub-check that fires. AUTH-Q7 is NOT a conditional BLOCKER — it is an unconditional RISK-SAFETY.

### Service Archetype Classification

Beyond `repo_type` (which determines N/A questions for non-application repos), this analysis classifies application repositories by **service archetype** — a characterization of runtime behavior that determines which extended questions are triggered.

| Archetype | Description | Detection Signals |
|-----------|-------------|-------------------|
| **stateless-utility** | Pure-function services with no persistent state, no user-specific data, and no write operations. | No database connections, no cache writes. All operations read-only and deterministic. Data is public or reference-grade. |
| **stateful-crud** | Services that own persistent state and expose CRUD operations on business entities. | Database connections. Create/Update/Delete endpoints. Entity lifecycle management. User-specific data. |
| **orchestrator** | Services that coordinate multi-service workflows by calling other services. | High fan-out (calls 3+ downstream services). Saga/workflow patterns. |
| **data-gateway** | Read-heavy data access layer — APIs over databases, search indexes, or data lakes. | Database queries dominate logic. Pagination, filtering, sorting. Read-heavy traffic. |
| **event-processor** | Services that consume events/messages and process them asynchronously. | Message queue consumers (SQS, Kafka, SNS). No synchronous API surface (or minimal). |

If the archetype cannot be determined with confidence, default to `stateful-crud` (the most conservative — triggers the most extended questions).

The output is a **four-artifact bundle** (per the Four-Artifact Output Contract below) containing:
- `{repo-name}-ara-report.md` — richest narrative
- `{repo-name}-ara-report.json` — canonical machine-readable contract
- `{repo-name}-ara-report.html` — single self-contained HTML visualization
- `{repo-name}-ara-report.metadata.json` — version compatibility sidecar

The MD report contains:
- Metadata header (repo name, date, repo_type, agent_scope)
- Readiness profile (Agent-Ready, Pilot-Ready, Pilot-Ready (Safety Concerns), Remediation Required, or Not Agent-Integrable)
- BLOCKER/RISK-SAFETY/RISK-QUALITY/INFO summary counts (excluding N/A questions)
- BLOCKERs section with remediation guidance
- RISKs section grouped by tier (RISK-SAFETY first, then RISK-QUALITY) with compensating control options
- INFOs section
- Detailed findings for all 43 questions (including N/A questions in N/A format)
- Evidence index with file references
- Prioritized remediation guidance per BLOCKER and RISK finding

Controls evaluated here may exist at the application layer, the platform layer (API Gateway, service mesh, IAM), or the agent architecture layer. ARA checks end-to-end presence — where a control is implemented is an architecture decision, not a scoring factor.

The readiness profile is determined by BLOCKER count and RISK-SAFETY count only. RISK-QUALITY has no effect on profile assignment:

| Readiness Profile | BLOCKERs | RISK-SAFETY | RISK-QUALITY | Recommendation |
|-------------------|----------|-------------|--------------|----------------|
| **Agent-Ready** | 0 | 0 | Any | Broad deployment |
| **Pilot-Ready** | 0 | 1–2 | Any | Narrow pilot |
| **Pilot-Ready (Safety Concerns)** | 0 | 3+ | Any | Supervised pilot, prioritize safety remediation |
| **Remediation Required** | 1–2 | Any | Any | Remediate BLOCKERs first |
| **Not Agent-Integrable** | 3+ | Any | Any | Deferred or descoped |

This analysis does NOT cover agent architecture (orchestration design, prompt engineering, model selection, RAG pipelines, MCP servers), agent-level AI governance (model policy, prompt-injection defense, safety evaluation), or general cloud modernization (managed compute, monolith decomposition, deployment strategies, DevOps maturity). Those concerns belong in the Modernization Readiness Analysis or agent-side governance reviews.
