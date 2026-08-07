# MOD Question Bank — Steps 2–6

> **Purpose:** Loaded by the Modernization Readiness Analysis (MOD) TD after Discovery and archetype/surface detection (SKILL.md Steps 1–1.6). This is the authoritative catalog of all 37 questions across the 5 sections (INF, APP, DATA, SEC, OPS), each scored 1–4 with its rubric and any archetype calibration. Evaluate every applicable question here against the repository evidence, honoring the N/A and surface-gate rules in the spine.

---

### Step 2: Infrastructure, Platform, and DevOps (INF-Q1 through INF-Q11)

These questions evaluate the compute, networking, platform services, and deployment practices underpinning the application. Before evaluating each question, check the N/A mapping for the resolved `repo_type`. If the question is N/A, record it in the N/A display format and skip evaluation.

#### INF-Q1: Managed Compute

**Question:** What percentage of compute workloads use managed container orchestration (EKS, ECS, Fargate) or serverless (Lambda) vs raw EC2?

**Why it matters:** Managed compute provides elastic scaling, reduced operational overhead, and faster deployment cycles. EC2 requires manual scaling, patching, and capacity planning. Modernization starts with moving off self-managed compute.

| Score | Criteria |
|-------|----------|
| **4** | All primary workloads run on ECS/EKS/Lambda/Fargate. EC2 used only for edge cases (bastion hosts, license-locked software). Measured by service count: ≤1 EC2-based service remains. |
| **3** | Mix of managed and EC2, with managed compute for primary workloads. |
| **2** | Primarily EC2 with some containerization or Lambda for auxiliary functions. |
| **1** | All compute on raw EC2 or on-premises with no managed services. |

> **Look for:** Terraform `aws_ecs_*`, `aws_eks_*`, `aws_lambda_*` vs `aws_instance`; CloudFormation resource types; Dockerfile presence; Kubernetes manifests.

#### INF-Q2: Managed Databases

**Question:** Are databases fully managed (RDS/Aurora/DynamoDB/DocumentDB/Neptune/Timestream) vs self-managed?

**Why it matters:** Self-managed databases — regardless of where they run (EC2, containers, on-premises) — introduce maintenance windows, manual patching, and operational overhead. Migrating to managed services eliminates ops burden and enables automatic backups, failover, and scaling.

> **Note:** This question is **surface-gated** (Step 1.6). If `has_persistent_data_store` is `false` — the system does not deploy any database, managed or self-managed — record the question as **"Not Evaluated (archetype-N/A)"** and skip evaluation. A build tool, pure utility, or frontend-only application has no database and should not receive Score 1 for "no managed database."

| Score | Criteria |
|-------|----------|
| **4** | All databases are managed services with automated failover. |
| **3** | Main production databases managed; some auxiliary or secondary self-managed instances remain. |
| **2** | Main production databases are managed services but deployed single-AZ or without Multi-AZ failover enabled. OR: mix of managed and self-managed — at least one production database is self-hosted (e.g., MySQL on EC2, PostgreSQL in Docker). |
| **1** | All databases self-managed on EC2, containers, or on-premises. |

> **Look for:** Terraform `aws_rds_*`, `aws_dynamodb_*`, `aws_docdb_*`, `aws_neptune_*`, `aws_timestreamwrite_*` vs compute resources running database software; connection strings pointing to self-hosted instances; database engine installation in Dockerfiles or user-data scripts.

#### INF-Q3: Workflow Orchestration

**Question:** Are workflow orchestration services used (Step Functions, MWAA, Temporal, Camunda) or are workflows primarily implemented as hardcoded application logic?

**Why it matters:** Dedicated workflow orchestration provides visual workflow management, error handling, retry logic, and state management. Without it, all orchestration logic is buried in code — harder to maintain, debug, and evolve. However, not every service has workflows to orchestrate. A pure read-only utility or a simple CRUD service may have nothing multi-step to coordinate, and penalizing it for not adopting Step Functions would recommend complexity where none is warranted.

> **Note:** This question uses archetype-sensitive calibration. A `stateless-utility` with no multi-step workflows records as "Not Evaluated (archetype-N/A)" rather than defaulting to Score 4. See the archetype rubric below.

**Archetype Calibration:** This question is archetype-sensitive. Apply the rubric below that matches the detected `service_archetype`. If `repo_type` is not `application` (and therefore no archetype was detected), use the `stateful-crud` column as the default.

> **Not Evaluated (archetype-N/A) rule:** If the resolved archetype column indicates the question does not apply (the rubric cell says "not applicable by design" or equivalent — for INF-Q3 this is `stateless-utility` Score 4), record the question as **"Not Evaluated (archetype-N/A)"** in the report and exclude it from category and overall score averaging. Do not report a default Score 4. Use the Not-Evaluated display format defined in the N/A Mapping section above.

| Score | stateless-utility | data-gateway | stateful-crud | orchestrator | event-processor |
|-------|------------------|--------------|---------------|--------------|-----------------|
| **4** | No multi-step workflows exist — not applicable by design → **Not Evaluated (archetype-N/A)**. | No multi-step workflows exist in the read path; any background maintenance jobs use managed orchestration. | Dedicated workflow orchestration service in use for business-critical multi-step operations. | Step Functions, Temporal, or equivalent coordinates all multi-service workflows with error handling and retries. | Event pipeline uses managed orchestration (Step Functions, EventBridge Pipes) for multi-step processing. |
| **3** | — | Some background jobs orchestrated, others in code; minimal impact on read path. | Partial adoption — some workflows orchestrated, others still in code. | Partial adoption — primary workflow orchestrated, auxiliary flows still in code. | Primary pipeline orchestrated; some event chains still handled inline. |
| **2** | — | Background jobs are hardcoded state machines. | Simple state machines in code with some structure, but no dedicated service. | Fan-out coordination is in code with basic structure but no dedicated orchestrator. | Multi-step event processing is ad hoc in handler code. |
| **1** | Multi-step processes exist despite the utility framing and are entirely hardcoded (indicates archetype may be misclassified). | Multi-step orchestration buried in application code with no structure. | No orchestration — all workflow logic hardcoded in application code. | No orchestration despite fan-out — tight coupling and no retry/error strategy. This is an anti-pattern for this archetype. | Event chains are fully hardcoded with no orchestration primitives. |

When the score is 4 for `stateless-utility` or `data-gateway` because no workflows exist, the **Recommendation** field should state that dedicated workflow orchestration is not applicable for this archetype and does not represent a gap. When the score is 1 for `orchestrator`, explicitly call out that this is an anti-pattern for the archetype and elevate the recommendation priority.

> **Look for:** `aws_sfn_*` in Terraform; Temporal SDK imports; workflow YAML definitions; state machine patterns in code. For archetype detection cross-check: count of downstream service calls, presence of multi-step business operations.

#### INF-Q4: Async Messaging and Streaming

**Question:** Is there managed messaging or streaming infrastructure (SQS, SNS, EventBridge, MSK, Kinesis, Amazon MQ) vs self-managed Kafka/RabbitMQ, or no messaging at all?

**Why it matters:** Managed messaging and streaming enable event-driven architectures with reduced operational overhead. Self-managed message brokers require patching, scaling, and monitoring. However, async is not universally the right answer — synchronous HTTP or gRPC is the correct design for read-only utility services and read-heavy data gateways, and forcing async into those designs adds operational complexity without architectural benefit. This rubric calibrates expectations by archetype so that services scoring 4 reflect the correct design for their role, not a uniform "async everywhere" bar.

> **Note:** This question uses archetype-sensitive calibration. Synchronous HTTP is the correct design for stateless-utility and data-gateway services and scores 4. See the archetype rubric below.

**Archetype Calibration:** This question is archetype-sensitive. Apply the rubric below that matches the detected `service_archetype`. If `repo_type` is not `application` (and therefore no archetype was detected), use the `stateful-crud` column as the default.

| Score | stateless-utility | data-gateway | stateful-crud | orchestrator | event-processor |
|-------|------------------|--------------|---------------|--------------|-----------------|
| **4** | Synchronous HTTP/gRPC is the correct design and is in use; no messaging needed. Any outbound signals (e.g., telemetry) use managed services. | Synchronous reads dominate (correct); any write-back, cache invalidation, or indexing flows use managed messaging. | Managed messaging (SQS, SNS, EventBridge) for cross-service state changes and notifications; synchronous reads where appropriate. | Managed messaging and/or streaming (EventBridge, SQS, MSK, Kinesis) for fan-out and decoupling; Step Functions for coordination. | Managed event source (SQS, Kafka/MSK, Kinesis, EventBridge) with structured consumer patterns. |
| **3** | Sync dominates; a small amount of async exists and is on managed services. | Synchronous dominant with some managed async for auxiliary flows. | Managed messaging for key flows; synchronous HTTP for others where async would genuinely help but is not yet in place. | Managed messaging for some flows; synchronous HTTP or self-managed components for others. | Managed primary event source; some auxiliary flows are self-managed. |
| **2** | Any self-managed messaging is in use without clear need (suggests archetype may be misclassified). | Self-managed messaging for write-back or indexing flows. | Self-managed messaging (Kafka, RabbitMQ on EC2/containers) for cross-service flows. | Self-managed messaging for orchestration fan-out. | Self-managed event broker is primary source. |
| **1** | Self-managed broker used despite no real need — pure overhead. | No async where async would reduce read-path coupling, OR self-managed broker without justification. | No messaging where state changes cross service boundaries — tight synchronous coupling between services that should be decoupled. | Synchronous-only fan-out across 3+ services. This is an anti-pattern for this archetype — cascading failures and timeout amplification are structural risks. | Polling a REST endpoint instead of consuming events (wrong archetype) or no broker at all. |

When the score is 4 for `stateless-utility` or `data-gateway` because synchronous communication is the correct design, the **Finding** field should state that synchronous is appropriate for this archetype and the **Recommendation** should explicitly note that adopting async messaging is NOT recommended — it would add operational complexity without architectural benefit. When the score is 1 for `orchestrator` due to synchronous-only fan-out, flag it as an anti-pattern in the **Gap** field.

> **Look for:** `aws_sqs_*`, `aws_sns_*`, `aws_msk_*`, `aws_kinesis_*`, `aws_eventbridge_*`, `aws_mq_*` in IaC; SDK imports for messaging/streaming (boto3 SQS/SNS, `@aws-sdk/client-sqs`, Kafka/Kinesis clients, ActiveMQ/RabbitMQ clients); event-driven handler patterns; stream consumer patterns; for archetype cross-check: count of downstream service calls, presence of write endpoints, presence of event emission on state changes.

#### INF-Q5: Network Security

**Question:** Are services deployed in a VPC with private subnets, security groups, NACLs, and proper network segmentation?

**Why it matters:** Network segmentation limits blast radius of failures and security incidents. Services exposed directly to the internet without proper network controls are a security and operational risk.

| Score | Criteria |
|-------|----------|
| **4** | Services in private subnets, least-privilege security groups, proper segmentation, and managed networking services in use (VPC endpoints / PrivateLink, VPC Lattice, IPAM for address management, or zero-trust patterns). |
| **3** | Services in private subnets with least-privilege security groups and network segmentation present, but no managed networking services layered on top. |
| **2** | VPC with subnets but some overly permissive rules (0.0.0.0/0 in security groups) or missing segmentation between tiers. |
| **1** | Services deployed in the default VPC or to public subnets without isolation (e.g., public-facing EC2 with 0.0.0.0/0 ingress, no custom VPC). |

> **Look for:** `aws_vpc`, `aws_subnet`, `aws_security_group`; subnet tiers (public vs private); security group rules; overly permissive rules (0.0.0.0/0); default-VPC usage; managed networking signals — `aws_vpc_endpoint`, `aws_vpclattice_*`, `aws_vpc_ipam_*`, AWS PrivateLink configurations.

> **⚠️ Scoring limitation — external context dependency:** VPC, subnet, and security group configurations are often managed in a dedicated infrastructure or networking repository rather than in application repos. The absence of network security IaC in the scanned repository does not confirm that the application runs without network isolation — it may be deployed into a VPC managed elsewhere. A Score of 1 has a moderate false-positive rate for application repos that do not own their networking layer. When `additionalPlanContext` provides network security evidence, use that to override the code-scan result.

#### INF-Q6: API Entry Point

**Question:** Is there an API Gateway, AppSync, ALB, or CloudFront as the entry point vs direct service exposure?

**Why it matters:** A managed entry point provides throttling, authentication, request validation, and a single point of control. Direct service exposure lacks these protections and makes it harder to manage traffic patterns.

| Score | Criteria |
|-------|----------|
| **4** | API Gateway with throttling, auth, and request validation. |
| **3** | ALB or CloudFront with basic routing and health checks. |
| **2** | Load balancer present but minimal configuration (no auth, no throttling). |
| **1** | Services exposed directly with no gateway or load balancer. |

> **Look for:** `aws_api_gateway_*`, `aws_apigatewayv2_*`, `aws_appsync_*`, `aws_lb_*`, `aws_iot_*` in IaC; throttling and auth config on gateway; AppSync schema and resolver configurations; IoT Core topic rules.

#### INF-Q7: Auto-Scaling

**Question:** Are auto-scaling mechanisms configured for compute, database, and other workloads?

**Why it matters:** Without auto-scaling, workloads cannot respond to traffic spikes or scale down during low demand. This leads to either over-provisioning (cost waste) or under-provisioning (degraded experience). Auto-scaling applies beyond compute — DynamoDB capacity, Aurora replicas, ElastiCache shards, and other managed services also benefit from dynamic scaling.

| Score | Criteria |
|-------|----------|
| **4** | All scalable resource types have auto-scaling configured with appropriate min/max — compute (ECS/EKS/EC2 ASG/Lambda concurrency), data (DynamoDB capacity, Aurora replicas), and other managed services where applicable. Mature deployments also use business-metric-driven scaling policies (custom CloudWatch metrics on requests-in-flight, orders-per-second, queue depth) where purely technical metrics (CPU, memory) are insufficient signals of load. |
| **3** | Auto-scaling configured on primary workloads with workload-appropriate thresholds (custom target tracking or step policies) covering both compute and data layers. Auxiliary resources may use static capacity. |
| **2** | Auto-scaling exists but uses only default/out-of-box settings (e.g., default ECS target tracking without tuning), OR coverage is limited to compute with no scaling on data or other managed services. No custom scaling policies or scheduled scaling. |
| **1** | No auto-scaling — all capacity is statically provisioned. |

> **Look for:** `aws_autoscaling_*`, `aws_appautoscaling_*`; scaling policies; min/max capacity settings; Lambda concurrency limits; DynamoDB auto-scaling; Aurora auto-scaling configuration; ElastiCache shard scaling.

#### INF-Q8: Backup and Recovery

**Question:** Are automated backups configured for data stores with defined retention periods and tested restore procedures?

**Why it matters:** Without automated backups and tested restores, a data loss event can wipe application state and cause cascading failures. This is a foundational reliability requirement. (WAF: REL 9)

| Score | Criteria |
|-------|----------|
| **4** | All production data stores have automated backups with defined retention; PITR enabled where supported; restore procedures documented and tested; cross-region backup replication configured for critical data. |
| **3** | Automated backups configured but missing PITR or missing on some data stores; no documented restore testing. |
| **2** | Backups on main production database only; no backup plans for other data stores; no restore testing. |
| **1** | No backup configuration found; or backup_retention_period = 0. |

> **Look for:** `backup_retention_period` on RDS; `point_in_time_recovery` on DynamoDB; `aws_backup_plan` resources; S3 versioning; EBS snapshot lifecycle policies.

#### INF-Q9: High Availability and Fault Isolation

**Question:** Are production workloads deployed across multiple Availability Zones with fault isolation?

**Why it matters:** Single-AZ production deployments are one of the most common high-risk issues. An AZ failure takes down the entire workload with no automatic recovery. Multi-AZ ensures survivability without human intervention. (WAF: REL 10, REL 11)

| Score | Criteria |
|-------|----------|
| **4** | All production compute and data stores span 2+ AZs; load balancers with cross-zone enabled. |
| **3** | Main production database is Multi-AZ; stateful compute or caches are multi-AZ; stateless compute may be single-AZ if replaceable via ASG/service across AZs. |
| **2** | Main production database is single-AZ OR stateful compute is single-AZ; other compute spans multiple AZs but fault isolation is not explicit. |
| **1** | All resources in a single AZ; or no AZ configuration found. |

> **Look for:** `multi_az = true` on RDS; `availability_zones` spanning 2+ AZs in ASGs/ECS; subnet configurations across multiple AZs.

#### INF-Q10: Infrastructure as Code Coverage

**Question:** What percentage of infrastructure is defined in IaC vs manually created?

**Why it matters:** Low IaC coverage means infrastructure changes are manual, error-prone, and non-reproducible. IaC is the foundation for automated deployments, environment consistency, and disaster recovery.

| Score | Criteria |
|-------|----------|
| **4** | 90%+ of infrastructure defined in IaC (compute, networking, databases, messaging, and operational/DR resources — monitoring, alarms, backup plans, health checks). |
| **3** | 70-90% IaC coverage — primary resources covered, some auxiliary resources manual. |
| **2** | Partial IaC — some resources defined, but significant manual infrastructure. |
| **1** | No IaC — all infrastructure created manually (ClickOps). |

> **Look for:** Presence and coverage of .tf files, CDK stacks, CloudFormation templates, Helm charts. Check whether IaC covers compute, networking, databases, messaging, and operational resources (CloudWatch alarms, Route 53 health checks, Backup plans, and other DR-related resources).

> **⚠️ Scoring limitation — external context dependency:** Infrastructure as Code is sometimes maintained in a dedicated infrastructure repository (e.g., a Terraform monorepo or a platform team's CDK project) rather than alongside application source code. The absence of IaC files in the scanned repository does not always confirm that infrastructure is manually provisioned — it may be managed in a separate repo. A Score of 1 has a moderate false-positive rate for application repos in organizations that separate IaC from application code. When `additionalPlanContext` provides IaC evidence (e.g., referencing a companion infra repo), use that to override the code-scan result.

> **Scoring guidance for percentages:** The denominator is "infrastructure resources this service depends on" — compute, networking, databases, messaging, monitoring, DNS, and secrets. Count resource categories with IaC definitions vs those without. If only the repo's own resources are visible (no evidence of external infra), score based on what IS present: if all visible infrastructure has IaC definitions, score 3 (not 4, since unobservable resources may be manual) unless `additionalPlanContext` confirms full coverage.

#### INF-Q11: CI/CD Automation

**Question:** Are CI/CD pipelines automated with build, test, and deploy stages for both application code and infrastructure as code, or are deployments manual?

**Why it matters:** Manual deployments create bottlenecks, are error-prone, and prevent rapid iteration. Automated pipelines enable continuous delivery with consistent quality gates. CI/CD automation alone is not sufficient for modern agent-facing APIs — pipelines must also include security validation (SAST, DAST, dependency scanning). See **SEC-Q7** for the security-pipeline evaluation that pairs with INF-Q11's automation scoring.

| Score | Criteria |
|-------|----------|
| **4** | Full CI/CD automation covering both application code and infrastructure-as-code changes, with test, build, deploy, and automated rollback stages. |
| **3** | CI/CD pipelines exist for application code and IaC with build and deploy stages, but limited automated testing, OR automation on one track (application or IaC) with manual steps on the other. |
| **2** | Partial automation — build is automated but deployment is manual or semi-manual for application code and/or IaC changes. |
| **1** | No CI/CD — all application and infrastructure deployments are manual scripts or ClickOps. |

> **Look for:** .github/workflows/, buildspec.yml, appspec.yml, Jenkinsfile, CodePipeline definitions in IaC; pipeline stages with automated test, build, and deploy steps.


### Step 3: Application Architecture (APP-Q1 through APP-Q6)

These questions evaluate the application's structural maturity, decomposition readiness, and communication patterns. Before evaluating each question, check the N/A mapping for the resolved `repo_type`. If the question is N/A, record it in the N/A display format and skip evaluation.

#### APP-Q1: Programming Languages

**Question:** What programming languages are used and how mature is their ecosystem for cloud-native development?

**Why it matters:** Language choice determines the breadth of AWS SDK support, the depth of cloud-native tooling, and the availability of modern framework ecosystems. Languages with first-class AWS SDK coverage and mature cloud-native libraries enable faster modernization; languages with narrower AWS tooling require more custom integration work to reach the same outcomes. Within a given language, the version/framework/SDK combination matters too — modern Java with a current Spring Boot and AWS SDK v2 is materially different from Java 8 with Spring Boot 2.1 and SDK v1, and modern .NET (Core/.NET 6+) is materially different from .NET Framework 4.x.

> **Two-axis calibration:** Score based on both (a) *language/runtime modernity* and (b) *framework/SDK modernity*. A modern language version with lagging framework/SDK lands in Score 3; compound regression across both axes lands in Score 2.

| Score | Criteria |
|-------|----------|
| **4** | Modern cloud-native language at a current version with matching modern framework and SDK. Examples: Python 3.10+, Node.js 18+ / TypeScript, Go 1.20+, Java 17+ / Kotlin with Spring Boot 3.x and AWS SDK v2; modern .NET (6/7/8/9/10) with current ASP.NET Core and AWS SDK for .NET v3. First-class AWS SDK coverage, broad cloud-native tooling, mature framework ecosystems. |
| **3** | Cloud-native language at a modern version but with **framework or SDK lag** — e.g., Java 17 on Spring Boot 2.7, Node.js 18+ on Express with AWS SDK v2 partial adoption, Python 3.10+ on an older web framework, or Rust (good AWS SDK coverage but narrower cloud-native tooling ecosystem). Language choice is not the blocker; modernization is an SDK/framework upgrade. |
| **2** | Compound legacy signals — **language version AND framework AND SDK all regressed**. Examples: Java 8 with Spring Boot 2.x and AWS SDK v1; .NET Framework 4.x with legacy ASP.NET (pre-Core) and AWS SDK for .NET v2 or older; Python 2.x; end-of-life Node.js with an unsupported framework. Also includes PHP, Ruby, or Perl — functional AWS SDK but limited cloud-native tooling depth regardless of version. These require a version upgrade in addition to framework/SDK modernization. |
| **1** | Languages with limited or no AWS SDK and effectively no cloud-native tooling (e.g., COBOL, VB6, Classic ASP, PowerBuilder) — requires custom integration or migration planning for cloud services. |

> **Look for:** File extensions; dependency manifests (package.json, requirements.txt, pom.xml/build.gradle, go.mod, *.csproj). Record the *version* alongside the language (e.g., `Java 8` vs `Java 17`, `.NET Framework 4.8` vs `.NET 8`), the framework version (Spring Boot 2.1 vs 3.x, ASP.NET Framework vs ASP.NET Core), and the AWS SDK major version (v1 vs v2 for Java/JS, v2 vs v3 for .NET) — all three axes drive the score.

#### APP-Q2: Monolith vs Microservices

**Question:** Is the application a single deployable unit or multiple independently deployable services?

**Why it matters:** Monoliths limit independent scaling, deployment, and team autonomy. Understanding the current decomposition state and coupling level determines the modernization strategy — containerize, migrate to serverless (Lambda), strangler fig extraction, or full decomposition.

| Score | Criteria |
|-------|----------|
| **4** | Microservices or modular monolith with well-defined module boundaries, no circular dependencies, clear interfaces. |
| **3** | Modular monolith with separate schemas per module (or per-service databases), clear module interfaces, no circular dependencies. OR: microservices that share a database instance but use separate schemas. |
| **2** | Monolith with identifiable modules but shared database schemas, direct cross-module data access, or circular call dependencies between modules. |
| **1** | Tightly-coupled monolith with no clear module boundaries, pervasive shared state. |

> **Look for:** Single deployable vs multiple service directories; Helm charts for multiple services; Docker Compose with multiple services; IaC for multiple ECS tasks or Lambda functions. For monoliths: package/module structure, dependency graphs, circular dependencies, shared mutable state, database coupling.

> **Scoring guidance for Score 2 vs 3 boundary:** The key differentiator is *database schema isolation*. Score 3 requires that modules/services own their data — either separate databases or separate schemas within the same instance where cross-schema access is via API, not direct table joins. Score 2 applies when modules share tables, use cross-module foreign keys, or access each other's data via direct SQL rather than through defined interfaces. If the evidence is ambiguous (single database but you cannot determine whether cross-module queries exist), default to Score 2.

#### APP-Q3: Async vs Sync Communication

**Question:** What percentage of inter-service communication is asynchronous vs synchronous HTTP?

**Why it matters:** Synchronous-only architectures create tight coupling, cascading failures, and timeout risks. Async patterns enable decoupling, resilience, and better handling of variable-latency operations. However, the correct async/sync ratio depends on what the service does. A pure utility or read-heavy data gateway has no inherent need for async communication — forcing it in would be complexity for its own sake. An orchestrator or event-processor with primarily synchronous coupling, in contrast, is an anti-pattern for its archetype.

> **Note:** This question uses archetype-sensitive calibration. A `stateless-utility` where sync is the correct design records as "Not Evaluated (archetype-N/A)" rather than defaulting to Score 4. See the archetype rubric below.

**Archetype Calibration:** This question is archetype-sensitive. Apply the rubric below that matches the detected `service_archetype`. If `repo_type` is not `application` (and therefore no archetype was detected), use the `stateful-crud` column as the default.

> **Not Evaluated (archetype-N/A) rule:** If the resolved archetype column indicates the question does not apply (for APP-Q3 this is `stateless-utility` Score 4: "Sync request/response is the correct design; async not needed"), record the question as **"Not Evaluated (archetype-N/A)"** and exclude it from category and overall score averaging. Do not report a default Score 4.

| Score | stateless-utility | data-gateway | stateful-crud | orchestrator | event-processor |
|-------|------------------|--------------|---------------|--------------|-----------------|
| **4** | Sync request/response is the correct design; async not needed → **Not Evaluated (archetype-N/A)**. | Sync reads are correct; any write-back, cache invalidation, or indexing uses async. | 50%+ async for cross-service state propagation, or async available for all long-running operations. | Async dominates for fan-out; sync reserved for reads and fast-returning calls. | Primary input is async (event/queue); any outbound calls are async where appropriate. |
| **3** | — | Sync-dominant with async available for auxiliary flows that need it. | Mix of async and sync with async for key workflows. | Mix of async and sync; primary workflows async, some fan-out still sync. | Async input; some sync outbound calls that could be async. |
| **2** | — | Sync-only with no async path for flows that would benefit (e.g., reindexing blocks read traffic). | Primarily synchronous with some async for background jobs. | Primarily synchronous fan-out with limited async. | Mixed input model with significant sync coupling. |
| **1** | Sync with no ability to add async where rare outbound signals would genuinely benefit. | Sync-only across all paths with visible queueing or timeout issues. | All communication synchronous HTTP with no async patterns. | Synchronous-only fan-out across 3+ services — cascading failure risk. Anti-pattern for this archetype. | Entirely synchronous (polling loops, sync RPCs) — archetype mismatch. |

When the score is 4 for `stateless-utility` or `data-gateway` because synchronous is the correct design, the **Finding** should state this explicitly and the **Recommendation** should NOT propose converting to async. When the score is 1 for `orchestrator` or `event-processor`, flag it as an archetype anti-pattern in the **Gap** field.

> **Look for:** HTTP client calls (axios, requests, RestTemplate, fetch, gRPC stubs) vs message publishing patterns; event-driven handlers; queue consumers; Lambda event source mappings. Cross-check: count of downstream calls and whether they are unary vs fire-and-forget.

#### APP-Q4: Long-Running Process Handling

**Question:** Are operations over 30 seconds handled asynchronously with status polling or callbacks?

**Why it matters:** Blocking calls for long-running operations create timeout risks, poor user experience, and resource waste. Async patterns with status tracking enable better resource utilization and user feedback. However, many services have no operations that exceed 30 seconds — a pure utility doing stateless computation or a data-gateway doing indexed reads has no long-running work to offload. In those cases, this question is not a gap and should not drive a recommendation.

> **Note:** This question uses archetype-sensitive calibration. A `stateless-utility` with no long-running operations records as "Not Evaluated (archetype-N/A)" rather than defaulting to Score 4. See the archetype rubric below.

**Archetype Calibration:** This question is archetype-sensitive. Apply the rubric below that matches the detected `service_archetype`. If `repo_type` is not `application` (and therefore no archetype was detected), use the `stateful-crud` column as the default.

> **Not Evaluated (archetype-N/A) rule:** If the resolved archetype column indicates the question does not apply (for APP-Q4 this is `stateless-utility` Score 4: "No operations exceed 30 seconds — not applicable by design"), record the question as **"Not Evaluated (archetype-N/A)"** and exclude it from category and overall score averaging. Do not report a default Score 4.

| Score | stateless-utility | data-gateway | stateful-crud | orchestrator | event-processor |
|-------|------------------|--------------|---------------|--------------|-----------------|
| **4** | No operations exceed 30 seconds — not applicable by design → **Not Evaluated (archetype-N/A)**. | No user-facing operations exceed 30 seconds; any heavy reindexing or export jobs are async with status polling. | All operations over 30 seconds implemented as async jobs with status polling or callbacks. | All long-running coordination uses Step Functions, polling, or callback patterns. | Event handlers are async by design; long-running processing within a handler uses checkpointing or sub-workflows. |
| **3** | — | Most heavy operations are async; a rarely-hit export path may still block. | Most long-running operations async; some blocking calls remain. | Most long-running coordination async; edge cases still block. | Most handlers safely bounded; a few may exceed timeout without checkpointing. |
| **2** | — | Some heavy reads are synchronous and risk timeout. | Some background job processing but inconsistent patterns. | Some long-running coordination still blocks with risk of timeout. | Handlers occasionally exceed timeout; retries cause duplicate side effects. |
| **1** | A synchronous operation exceeding 30 seconds exists, contradicting the utility framing (archetype likely misclassified). | Unbounded synchronous queries blocking the read path. | All operations synchronous regardless of duration. | All long-running coordination synchronous — caller must hold connection open. | Handlers routinely exceed timeout with no checkpointing — processing lost on retry. |

When the score is 4 for `stateless-utility` or `data-gateway` because no long-running operations exist, the **Finding** should state this and the **Recommendation** should note that async job infrastructure is not applicable for the current surface. This question should not trigger a pathway recommendation in that case.

> **Look for:** Background job frameworks (Celery, Bull, SQS workers); async/polling patterns; job status APIs; Lambda async invocations; Step Functions for long processes. Cross-check: existence of operations whose latency is data-volume or network-dependent (batch exports, bulk updates, external provider calls with variable SLA).

#### APP-Q5: API Versioning Strategy

**Question:** Is there a consistent API versioning strategy (URL paths, headers, query parameters)?

**Why it matters:** Without versioning, API changes break all consumers simultaneously. Versioning enables graceful migration and backward compatibility.

| Score | Criteria |
|-------|----------|
| **4** | Consistent versioning strategy with backward compatibility guarantees. |
| **3** | Versioning strategy exists and is applied to most endpoints (e.g., /v1/ paths, version headers), but some newer or internal endpoints don't follow the convention. |
| **2** | Versioning applied ad hoc — fewer than half of endpoints use versioning, or multiple conflicting versioning schemes coexist (e.g., some use URL paths, others use headers). |
| **1** | No versioning — breaking changes deployed directly. |

> **Look for:** /v1/, /v2/ URL patterns; Accept-Version headers; versioning annotations; changelog files.

#### APP-Q6: Service Discovery

**Question:** Is there a service registry, API catalog, or service mesh for service-to-service communication?

**Why it matters:** Hard-coded service endpoints create deployment coupling and make it difficult to scale, relocate, or replace services. Service discovery enables dynamic routing and decoupled deployments.

| Score | Criteria |
|-------|----------|
| **4** | Service discovery mechanism present; no hard-coded service endpoints. |
| **3** | Partial service discovery — some services use discovery, others use hard-coded endpoints. |
| **2** | Environment variables for endpoints but no dynamic discovery. |
| **1** | All service endpoints hard-coded in application code or configuration. |

> **Look for:** AWS Service Discovery, Istio, Consul; API Gateway as catalog; environment variables with hard-coded endpoints vs service discovery.


### Step 4: Data Platform Modernization (DATA-Q1 through DATA-Q4)

These questions evaluate the data layer's modernization state — managed services, schema health, and migration readiness. Before evaluating each question, check the N/A mapping for the resolved `repo_type`. If the question is N/A, record it in the N/A display format and skip evaluation.

#### DATA-Q1: Unstructured Data Storage

**Question:** Are documents and unstructured data stored in managed object storage (S3) with parsing capabilities (Textract, Tika)?

**Why it matters:** Unstructured data locked in file systems, local storage, or legacy document management systems is inaccessible for modern workloads. S3 with parsing pipelines enables search, analytics, and AI integration. Assessing current access patterns (frequency, size, format) helps identify S3 adoption opportunities and migration paths.

| Score | Criteria |
|-------|----------|
| **4** | Unstructured data stored in S3 with parsing pipeline available. |
| **3** | Data in S3 but no automated parsing or extraction pipeline. |
| **2** | Data in managed storage but not S3 (EFS, EBS volumes) with limited accessibility. Note: Amazon S3 File Gateway (mountable S3 access) can bridge filesystem-dependent applications without data duplication. |
| **1** | Data on local file systems, legacy document management, or inaccessible storage. |

> **Look for:** `aws_s3_bucket`; Textract calls; document parsing libraries; PDF/image processing.

#### DATA-Q2: Unified Data Access Layer

**Question:** Is there a unified data access layer vs scattered database connections throughout the code?

**Why it matters:** Scattered data access means multiple integration points, inconsistent query patterns, and difficulty enforcing data contracts. A unified layer provides a single point of control for data access.

| Score | Criteria |
|-------|----------|
| **4** | Unified data access layer; single point of data contract. |
| **3** | Mostly centralized with some direct access in auxiliary code paths. |
| **2** | Repository/DAO pattern in some modules but inconsistent across the codebase. |
| **1** | Database imports and queries scattered across many modules with no pattern. |

> **Look for:** Centralized repository/DAO layer vs database imports spread across many modules; data access pattern consistency.

#### DATA-Q3: Database Engine Version and EOL

**Question:** Does IaC or deployment configuration specify the database engine version, and have any engines approaching or past end-of-life (EOL) been identified?

**Why it matters:** EOL database engines introduce security vulnerabilities and lack modern features. Unversioned or implicitly-latest configurations are also a risk signal. Engine version awareness is a prerequisite for migration planning.

| Score | Criteria |
|-------|----------|
| **4** | All database engine versions explicitly pinned in IaC; no engines at or past EOL; documented version-update procedure exists covering downtime windows, rollback, and risk acknowledgment. |
| **3** | Versions pinned but some approaching EOL within 12 months. |
| **2** | Some versions pinned, others implicit; EOL status unknown. |
| **1** | No version pinning; engines at or past EOL detected. |

> **Look for:** Engine version parameters in `aws_rds_instance`, `aws_docdb_cluster`, `aws_elasticache_*`; engine version strings in docker-compose or Helm values; absence of explicit version pinning.

#### DATA-Q4: Stored Procedures and Schema Complexity

**Question:** Does the application rely on stored procedures, triggers, or proprietary SQL constructs (e.g., T-SQL, PL/SQL)?

**Why it matters:** Stored procedures and proprietary SQL tightly couple business logic to the database engine, creating migration blockers. High stored procedure usage signals that database modernization will require significant effort beyond a lift-and-shift — logic extraction and schema refactoring become prerequisites.

| Score | Criteria |
|-------|----------|
| **4** | No stored procedures or proprietary SQL; all business logic in application layer. |
| **3** | Minimal stored procedures for performance-critical operations only. |
| **2** | Moderate stored procedure usage with some proprietary SQL constructs. |
| **1** | Heavy reliance on stored procedures, triggers, and proprietary SQL across the application. |

> **Look for:** `.sql` files containing `CREATE PROCEDURE`, `CREATE TRIGGER`, `CREATE FUNCTION`; ORM bypass patterns (raw SQL execution); references to proprietary SQL dialects in migration files.


### Step 5: Security Baseline (SEC-Q1 through SEC-Q7)

These questions evaluate the foundational security posture required for any modernization initiative. Before evaluating each question, check the N/A mapping for the resolved `repo_type`. If the question is N/A, record it in the N/A display format and skip evaluation.

#### SEC-Q1: Audit Logging

**Question:** Is CloudTrail enabled with immutable logs?

**Why it matters:** Audit logging is a compliance and operational requirement for any production system. Immutable logs ensure that actions can be traced and forensic analysis is possible after incidents.

| Score | Criteria |
|-------|----------|
| **4** | CloudTrail enabled with log file validation and immutable storage (S3 Object Lock). |
| **3** | CloudTrail enabled but without immutable storage or log validation. |
| **2** | Partial logging — some services logged, others not. |
| **1** | No CloudTrail or equivalent audit logging. |

> **Note:** This question is **surface-gated** (Step 1.6). Evaluate SEC-Q1 only when the repo contains **account/foundation-level IaC** (CloudTrail, AWS Config, GuardDuty, Organization SCPs, centralized logging). Application-level IaC repos (ECS tasks, RDS instances, Lambda functions for a single service) are **Not Evaluated** — CloudTrail is an account-level concern that belongs in the foundation infrastructure repo, not in each application repo. See "SEC-Q1 Account-Level Scope Determination" in Step 1.6 for the full decision logic.

> **Look for:** `aws_cloudtrail` in IaC; CloudTrail log file validation enabled; S3 bucket with object lock for logs; CloudWatch log retention policies.

> **⚠️ Scoring limitation — external context dependency:** CloudTrail is an AWS account-level service typically configured once per account or organization, not per-application repository. This question is surface-gated — only repos with account/foundation-level IaC are evaluated (see gate note above). Even when evaluated, the absence of `aws_cloudtrail` in a foundation IaC repo may indicate it's managed at the organization level rather than per-account. When `additionalPlanContext` provides audit logging evidence (e.g., confirming account-level CloudTrail exists), use that to override the code-scan result.

#### SEC-Q2: Encryption at Rest

**Question:** Is KMS used for sensitive data at rest?

**Why it matters:** Encryption at rest is a baseline security requirement. Customer-managed KMS keys provide control over key rotation, access policies, and audit trails.

> **Note:** This question is **surface-gated** (Step 1.6). If `has_at_rest_data_surface` is `false` — the system has no deployed data-at-rest surface (no database, S3 bucket, EBS volume, EFS file system, or similar managed storage) — record the question as **"Not Evaluated (archetype-N/A)"** and skip evaluation. A library or CLI tool with no runtime state to encrypt should not receive Score 1 for "no encryption at rest."

| Score | Criteria |
|-------|----------|
| **4** | Customer-managed KMS keys for all sensitive data stores, with centralized key management and documented rotation policy. |
| **3** | Customer-managed KMS keys on most sensitive data stores, OR AWS-managed encryption enabled across all data stores. Rotation may not be defined. |
| **2** | Mix of encryption types with coverage gaps — some data stores have customer-managed keys, others use AWS-managed, and at least one sensitive data store has no encryption configured. |
| **1** | No encryption at rest configured. |

> **Look for:** `kms_key_id` on S3/RDS/DynamoDB/EBS; `aws_kms_key` resources; encryption config on data stores.

#### SEC-Q3: API Authentication

**Question:** Is there per-request authentication with OAuth2/JWT on all API endpoints?

**Why it matters:** Unauthenticated APIs are a security vulnerability. Per-request authentication ensures that every call is authorized and attributable.

| Score | Criteria |
|-------|----------|
| **4** | All API endpoints use token-based auth (OAuth2/JWT); intentionally public endpoints protected by API Gateway with throttling and validation. |
| **3** | Token-based auth (OAuth2/JWT) on all external endpoints. Internal/private-subnet endpoints may lack auth if network isolation is enforced (security groups, VPC endpoints). |
| **2** | API key or static credential authentication without token-based auth. OR: token-based auth on fewer than half of endpoints. |
| **1** | No API authentication — endpoints are open. |

> **Look for:** Auth middleware; API Gateway authorizers; Cognito user pools; OAuth2 flows; Bearer token validation; @Authenticated annotations.

#### SEC-Q4: Centralized Identity Integration

**Question:** Does the application integrate with a centralized identity provider (Cognito, Okta, Ping), or does it manage its own authentication independently?

**Why it matters:** Applications with their own auth systems create inconsistency and increase attack surface. Detecting whether the app integrates with a centralized IdP signals modernization maturity. Apps with standalone auth are harder to integrate into unified access policies.

| Score | Criteria |
|-------|----------|
| **4** | Application integrates with centralized IdP; SSO enabled. |
| **3** | Application uses centralized IdP for most flows; some legacy auth paths remain. |
| **2** | Application has its own auth but can federate with external IdPs. |
| **1** | Application manages its own authentication entirely with no external IdP integration. |

> **Look for:** `aws_cognito_*`; OIDC/SAML configuration; identity provider federation; SSO configuration.

#### SEC-Q5: Secrets Management

**Question:** Are secrets (database credentials, API keys, tokens) managed through a dedicated secrets management system (AWS Secrets Manager, HashiCorp Vault) with rotation, or are they hardcoded in code, environment variables, or configuration files?

**Why it matters:** Hardcoded secrets are a critical security vulnerability and a common finding in legacy applications. Secrets management with rotation and audit trails is a baseline security requirement for any production system, not just agentic workloads. The presence of plaintext credentials anywhere in the repository — source code, application configs, or version-controlled env files — is a materially different posture than a system that uses parameter store or env vars without rotation, even when some secrets are already in a managed store. Score 1 reflects any plaintext credential presence; Score 2 reflects no-plaintext but no-rotation; Score 3 reflects managed secrets with rotation.

| Score | Criteria |
|-------|----------|
| **4** | All secrets in Secrets Manager or Vault with automated rotation configured; no hardcoded credentials; no production credentials in environment variables or parameter store without encryption. |
| **3** | Secrets Manager or Vault used for all production credentials (database passwords, API keys, service tokens) with automated rotation configured on at least the highest-risk secrets. Some non-critical configs (feature flags, non-secret configuration) may still be in environment variables. No plaintext credentials in source. |
| **2** | No plaintext credentials in source or version control, but production credentials are kept in environment variables, parameter store without encryption, or CloudFormation `NoEcho` parameters. Rotation is not configured. Includes cases where *some* secrets are in Secrets Manager/Vault but at least one production credential is still in plain env vars or unencrypted parameter store. |
| **1** | Plaintext credentials present anywhere in the repository — source files, application configs, version-controlled env files (`.env`, `application.properties`, `application.yaml`), or connection strings in IaC without parameter/secret references. Score 1 applies even when a secrets manager exists elsewhere in the system, because any plaintext secret is a deployment-blocking issue. |

> **Look for:** `aws_secretsmanager_*` in IaC; Vault client imports; hardcoded patterns (`password=`, `secret=`, `api_key=`, `DB_PASSWORD=` values in code, YAML, `.env`, `.properties`); `.env` or `application.properties` files committed to git; connection strings with embedded credentials. For Score 2/3 differentiation, also check: whether parameter store usage references KMS-encrypted `SecureString` vs plain `String`; whether Secrets Manager resources have `rotation_lambda_arn` or `rotation_rules` attached; whether the `NoEcho` parameters in CloudFormation are backed by Secrets Manager at runtime.

#### SEC-Q6: Compute Hardening and Patching

**Question:** Are compute resources hardened with managed patching and vulnerability scanning?

**Why it matters:** Unpatched compute resources are high-value targets. Managed patching and vulnerability scanning are baseline security requirements. (WAF: SEC 6)

| Score | Criteria |
|-------|----------|
| **4** | SSM Patch Manager or equivalent configured; vulnerability scanning (Inspector/Snyk) enabled; hardened base images. |
| **3** | Some patching automation but not comprehensive; or vulnerability scanning present but not integrated into CI/CD. |
| **2** | Manual patching process; default AMIs with no hardening. |
| **1** | No evidence of patching strategy; no vulnerability scanning. |

> **Look for:** SSM Agent in user-data; `aws_ssm_patch_baseline`; AWS Inspector or Snyk; hardened AMI references (CIS, Bottlerocket); EC2 Image Builder pipelines.

#### SEC-Q7: Application Security Pipeline

**Question:** Are SAST, DAST, or dependency vulnerability scanning tools integrated into the CI/CD pipeline?

**Why it matters:** Without automated security scanning, vulnerabilities in dependencies or application code reach production undetected. Embedding security validation in the pipeline is a baseline practice. (WAF: SEC 11)

| Score | Criteria |
|-------|----------|
| **4** | SAST + dependency scanning in CI/CD with security gates blocking on critical findings; container scanning if applicable. |
| **3** | At least one scanning tool in CI/CD but missing container scanning or no blocking gate. |
| **2** | Dependency scanning configured (e.g., Dependabot, npm audit) and running, but no SAST tool. OR: SAST tool configured but only runs on-demand, not in every pipeline execution. |
| **1** | No security scanning tools configured — no Dependabot, no SAST, no container scanning. Pipeline has no security validation step. |

> **Look for:** SonarQube, Semgrep, CodeGuru Reviewer in CI/CD; Dependabot config; `npm audit` or `pip-audit` in pipeline; ECR image scanning; `.snyk` policy files.


### Step 6: Operations & Observability (OPS-Q1 through OPS-Q9)

These questions evaluate the operational maturity and observability practices that support reliable, evolvable systems. Before evaluating each question, check the N/A mapping for the resolved `repo_type`. If the question is N/A, record it in the N/A display format and skip evaluation.

#### OPS-Q1: Distributed Tracing

**Question:** Is distributed tracing (X-Ray, OpenTelemetry, or partner solution) instrumented with trace ID propagation across service boundaries?

**Why it matters:** Without end-to-end tracing, debugging failures across service boundaries is guesswork. Distributed tracing is foundational for understanding request flows, identifying bottlenecks, and diagnosing production issues in any distributed system.

| Score | Criteria |
|-------|----------|
| **4** | End-to-end distributed tracing with propagated trace IDs across all service boundaries. |
| **3** | Tracing on primary services; some gaps in propagation. |
| **2** | Basic tracing on individual services but no cross-service propagation. |
| **1** | No distributed tracing instrumented. |

> **Look for:** OpenTelemetry SDK in dependency manifests, X-Ray instrumentation, traceparent/X-Amzn-Trace-Id header propagation.

#### OPS-Q2: SLO Definitions

**Question:** Are SLOs defined for critical user journeys?

**Why it matters:** Without SLOs, you cannot measure whether the system is meeting user expectations or degrading over time. SLOs drive prioritization of operational improvements and modernization investments.

| Score | Criteria |
|-------|----------|
| **4** | SLOs defined and monitored for all critical user-facing journeys with error budgets. |
| **3** | SLOs defined for primary journeys; monitoring in place but no error budget tracking. |
| **2** | Basic availability/latency alarms but no formal SLO definitions. |
| **1** | No SLOs — no formal definition of acceptable service levels. |

> **Note:** This question is **surface-gated** (Step 1.6). If `has_api_surface` is `false` AND `has_persistent_data_store` is `false` — the system has no user-facing surface for which SLOs are meaningful — record the question as **"Not Evaluated (archetype-N/A)"** and skip evaluation.

> **Look for:** SLO definitions in code or config; CloudWatch alarms on p99/p95 latency; error budget tracking; SLO dashboards.

> **⚠️ Scoring limitation — external context dependency:** SLO definitions typically reside in external monitoring platforms (CloudWatch, Datadog, Grafana, PagerDuty) rather than in source code or IaC. A Score of 1 on this question indicates that no SLO evidence was found *in the repository being scanned* — it does not confirm that SLOs are absent from the operational environment. This question has a high false-positive rate for code-only analyses. When `additionalPlanContext` provides SLO evidence (e.g., via a future `external_observability` field), use that to override the code-scan result. This question is classified as **non-core (P2)** because the absence of in-repo SLO artifacts is not a reliable signal of operational immaturity.

> **Scoring guidance for code-only analyses:** Score 2 (not 1) when CloudWatch alarms on latency/error-rate exist in IaC even without formal SLO naming — the presence of threshold-based alarms implies implicit SLOs. Score 1 only when NO monitoring artifacts exist at all. This prevents systematic Score-1 inflation across portfolios where SLO tooling lives externally.

#### OPS-Q3: Business Metrics

**Question:** Are custom metrics published for business outcomes, not just infrastructure metrics?

**Why it matters:** Infrastructure metrics (CPU, memory) tell you if the system is running, not if it's delivering value. Business metrics (conversion rates, resolution times, error rates by feature) drive informed modernization decisions.

| Score | Criteria |
|-------|----------|
| **4** | Business outcome metrics published alongside infrastructure metrics with dashboards. |
| **3** | Some business metrics tracked but not systematically across all features. |
| **2** | Infrastructure metrics only with ad hoc business reporting. |
| **1** | No custom metrics — only default CloudWatch infrastructure metrics. |

> **Look for:** `cloudwatch.put_metric_data` for business events; custom dashboards; business KPI alarms.

#### OPS-Q4: Anomaly Detection and Alerting

**Question:** Is there anomaly detection or alerting on error rates and latency?

**Why it matters:** Static threshold-based alerting misses gradual degradation and novel failure modes. Anomaly detection catches unexpected behavior patterns that fixed thresholds cannot.

| Score | Criteria |
|-------|----------|
| **4** | Anomaly detection enabled on error rates and latency for all critical paths. |
| **3** | Anomaly detection on primary paths; static thresholds on secondary paths. |
| **2** | Static threshold alarms only (e.g., CPU > 80%, error rate > 5%). |
| **1** | No alerting configured. |

> **Look for:** CloudWatch anomaly detection; error rate alarms; latency p99 alarms; PagerDuty/OpsGenie integration; composite alarms.

#### OPS-Q5: Deployment Strategy

**Question:** Is the deployment strategy blue/green, canary, or straight to production?

**Why it matters:** Direct-to-production deployments with no staged rollout eliminate the window to catch regressions before they affect all users. Canary and blue/green deployments enable safe, incremental releases.

| Score | Criteria |
|-------|----------|
| **4** | Canary or blue/green deployments; no direct-to-production releases. |
| **3** | Blue/green for primary services; direct deployment for auxiliary services. |
| **2** | Rolling deployments with basic health checks but no traffic shifting. |
| **1** | Direct-to-production deployment with no staged rollout. |

> **Note:** This question is **surface-gated** (Step 1.6). If `has_deployed_workload` is `false` — the repo has no Dockerfile with deployment manifests, no IaC defining compute, and no deployment configuration — record the question as **"Not Evaluated (archetype-N/A)"** and skip evaluation. A source-code-only repo whose deployment is managed in a separate GitOps or deployment-config repo should not receive Score 1 for "no deployment strategy."

> **Look for:** CodeDeploy deployment config; Helm canary; Argo Rollouts; Lambda traffic shifting; ALB weighted target groups; feature flags.

> **⚠️ Scoring limitation — external context dependency:** Deployment strategies are frequently configured in external systems (AWS CodeDeploy, ArgoCD, Spinnaker, Flux CD) or in separate deployment/GitOps repositories rather than in the application source repo. This question is surface-gated by `has_deployed_workload` — repos without deployment artifacts are Not Evaluated. For repos that DO have deployment artifacts, the absence of canary/blue-green evidence does not confirm that deployments are direct-to-production — deployment orchestration may exist in a separate system. When `additionalPlanContext` provides deployment strategy evidence, use that to override the code-scan result.

#### OPS-Q6: Integration Testing

**Question:** Are there integration tests for critical workflows that run in the CI pipeline?

**Why it matters:** Unit tests alone don't catch integration failures — broken API contracts, database schema drift, or misconfigured infrastructure. Integration tests validate that the system works end-to-end.

| Score | Criteria |
|-------|----------|
| **4** | Integration test suites covering all critical workflows, run in CI pipeline. |
| **3** | Integration tests for primary workflows; some gaps in coverage. |
| **2** | Some integration tests but not run consistently in CI. |
| **1** | No integration tests — only unit tests or no automated tests at all. |

> **Look for:** Integration test directories; test containers; pytest-integration; API test suites (Postman/Newman); contract tests; end-to-end test pipelines in CI.

#### OPS-Q7: Incident Response Automation

**Question:** Are incident response workflows automated, and do runbooks exist in machine-readable or structured form?

**Why it matters:** Manual incident response is slow and error-prone. Automated runbooks and self-healing patterns reduce mean-time-to-recovery and free teams to focus on prevention rather than firefighting.

| Score | Criteria |
|-------|----------|
| **4** | Self-healing automation resolves a defined class of incidents without human intervention; runbooks are versioned and machine-readable. |
| **3** | Automated runbooks for common incidents; manual escalation for complex ones. |
| **2** | Runbooks exist as documentation but are not automated. |
| **1** | No runbooks — incident response is entirely ad hoc. |

> **Look for:** Runbook files (markdown, YAML, JSON); Systems Manager Automation documents; Lambda-based remediation; Step Functions for incident workflows; self-healing patterns.

#### OPS-Q8: Observability Ownership

**Question:** Does the application have defined observability ownership — service-level dashboards, alarms with named owners, and SLO definitions tied to specific teams?

**Why it matters:** Without clear ownership of observability assets, monitoring gaps emerge. Detecting whether the repo has CODEOWNERS for observability configs, named alarm owners, or team-specific dashboards signals operational maturity.

| Score | Criteria |
|-------|----------|
| **4** | Per-service dashboards and alarms with named owners; SLO definitions with team attribution. |
| **3** | Dashboards and alarms exist for most services; some gaps in ownership attribution. |
| **2** | Ad hoc observability — alarms exist but no clear ownership or team attribution. |
| **1** | No observability ownership — monitoring is reactive and fragmented. |

> **Look for:** SLO definition files with named owners; CODEOWNERS referencing observability assets; per-service dashboards and alarms; team tags on CloudWatch resources.

#### OPS-Q9: Resource Tagging Governance

**Question:** Are AWS resources consistently tagged for cost allocation, ownership, and environment identification?

**Why it matters:** Without consistent tagging, organizations cannot track costs per workload, identify resource ownership during incidents, or enforce budget controls. Tagging is foundational to cloud financial management and blast radius analysis. (WAF: COST 1-3)

| Score | Criteria |
|-------|----------|
| **4** | All resources tagged with consistent keys; tag enforcement via IaC (required tags in modules) combined with Tag Policies in AWS Organizations and AWS Config rules; cost allocation tags activated. |
| **3** | Most resources tagged but inconsistent key naming or missing on some resource types; no enforcement. |
| **2** | Some resources tagged but many untagged; no tagging standard. |
| **1** | No tags found on resources; or only Name tags with no cost/ownership attribution. |

> **Look for:** `default_tags` in Terraform provider; `tags` on resources; `required-tags` Config rules; Tag Policies in AWS Organizations. SCPs are generally not recommended for tag enforcement — per-service action variance and policy-size limits make them unreliable for tagging; reserve SCPs for security guardrails.


