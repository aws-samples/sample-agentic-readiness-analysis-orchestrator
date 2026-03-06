
## Name
Portfolio Agentic Readiness Assessment

## Objective
Aggregate individual repository agentic readiness assessments to produce a sophisticated portfolio-level analysis that identifies cross-service dependencies, shared infrastructure patterns, integration opportunities, organization-wide modernization priorities, and a dependency-aware coordinated multi-service roadmap with risk assessment and resource allocation recommendations.

## Summary
This transformation consumes multiple individual agentic readiness assessment reports (agentic-readiness-report.md files) from different repositories and produces a comprehensive portfolio-level view with advanced analysis capabilities. It performs intelligent discovery and parsing of assessment reports, constructs service dependency graphs with coupling analysis, identifies cross-cutting concerns and patterns across services, calculates portfolio-wide readiness metrics, performs blast radius and risk assessment, identifies integration opportunities and shared service extraction candidates, generates dependency-aware phased roadmaps, and provides resource allocation and team structure recommendations.

The transformation follows a 5-stage pipeline architecture:
1. **Discovery**: Recursively locate all assessment reports in directory structure
2. **Parsing**: Extract metadata, scores, findings, technology stack, and dependencies from each report
3. **Analysis**: Construct dependency graphs, identify patterns, calculate portfolio metrics
4. **Synthesis**: Generate phased roadmaps, assess risks, identify integration opportunities
5. **Report Generation**: Create comprehensive Markdown report with validation

The output is a detailed Markdown report saved as `portfolio-agentic-readiness-report.md` containing:
- Executive dashboard with portfolio-wide scores and readiness distribution
- Portfolio readiness overview with technology stack summary
- Service dependency map with coupling scores and critical path analysis
- Cross-cutting concerns analysis across all five categories
- Dependency-aware portfolio modernization roadmap with four phases
- Integration opportunities (shared services, event-driven architecture, consolidation)
- Resource allocation recommendations (team structure, skill gaps, training)
- Risk analysis with likelihood × impact matrix and mitigation strategies
- Service-by-service summary with dependencies and phase assignments
- Assessment inventory and recommended next steps

## Entry Criteria
- At least 2 individual agentic readiness assessment reports exist in `agentic-readiness-assessment` directories
- Assessment reports are accessible at specified paths or in a common directory structure
- Write permissions exist to create the output directory and portfolio report file
- Individual reports follow the expected structure with scores, findings, and metadata

## Implementation Steps

### Step 1: Discovery — Locate Assessment Reports

Scan the target directory structure to find all individual assessment reports:

**Discovery Process:**
- Recursively search for directories named `agentic-readiness-assessment` in the directory tree
- Within each `agentic-readiness-assessment` directory, locate files matching the pattern `*-agentic-readiness-report.md`
- For each report found, extract the project name from the filename (the prefix before `-agentic-readiness-report.md`)
- Extract the repository path (parent directory of the `agentic-readiness-assessment` folder) and assessment date
- Validate that each report follows the expected structure (Executive Summary, category scores, detailed findings)
- Create an inventory of all services assessed with their locations
- Validate minimum requirement: at least 2 reports must be discovered

**Input Options:**
- A parent directory containing multiple repository folders, OR
- A list of explicit paths to assessment reports

**Validation:**
- Verify each path exists and is readable
- Exclude files that don't match the expected report structure
- Log warnings for inaccessible or malformed files
- Terminate with clear error if fewer than 2 valid reports found

### Step 2: Parse Individual Assessments

For each assessment report found, extract comprehensive data:

**Service Metadata:**
- Service/repository name (from path or metadata)
- Assessment date (validate YYYY-MM-DD format)
- Overall readiness score (validate 0.0-4.0 range)
- Category scores for all five categories (Infrastructure, Application, Data, Security, Operations)

**Detailed Findings:**
- Extract all criterion-level findings with scores, gaps, and recommendations
- Parse findings tables to extract criterion IDs (e.g., INF-Q1, APP-Q2)
- Extract effort estimates where available
- Top 5 priorities from each service

**Technology Stack:**
- Programming languages in use
- Database engines (managed vs self-managed)
- Compute patterns (EC2, Lambda, ECS, EKS, containers)
- IaC tools (Terraform, CloudFormation, CDK)
- CI/CD tools and pipeline maturity

**Architecture Patterns:**
- Monolith vs microservices status (from APP-Q4 findings)
- API patterns and versioning
- Communication patterns (synchronous vs asynchronous)
- Data access patterns

**Dependencies and Integration Points:**
- Synchronous dependencies: Search for REST API calls, gRPC calls, direct service references
- Asynchronous dependencies: Search for message queue references, event bus subscriptions, pub/sub patterns
- Shared databases: Detect database references appearing in multiple services
- Shared infrastructure: Common API gateways, load balancers, authentication systems, observability infrastructure

**Error Handling:**
- Log warnings for missing sections (use defaults)
- Log warnings for malformed scores (exclude from aggregations)
- Log warnings for missing metadata (use defaults)
- Handle duplicate service names with disambiguation using repository path

### Step 3: Cross-Service Dependency Analysis

Construct and analyze the service dependency graph:

**Dependency Graph Construction:**
- Create directed graph with services as nodes and dependencies as edges
- Classify each dependency by type:
  - **Synchronous**: REST/gRPC calls, direct service-to-service communication
  - **Asynchronous**: Message queues, event buses, pub/sub patterns
  - **Shared Database**: Multiple services accessing same database
  - **Shared Infrastructure**: Common API gateways, load balancers, auth systems

**Coupling Score Calculation:**
For each service pair, calculate coupling level:
- **High**: Synchronous dependency + shared database OR 3+ dependency types
- **Medium**: Synchronous dependency OR 2 dependency types
- **Low**: Asynchronous only OR shared infrastructure only

**Graph Metrics:**
- **Fan-in**: Count of services that depend on this service (dependents)
- **Fan-out**: Count of services this service depends on (dependencies)
- **Blast Radius**: Transitive impact calculation using breadth-first search from service node
- **Foundation Services**: Identify services with fan-in >= 3 AND fan-out <= 1
- **Leaf Services**: Identify services with fan-in <= 1 AND fan-out >= 2

**Circular Dependency Detection:**
- Use Tarjan's strongly connected components algorithm
- Any SCC with size > 1 indicates a circular dependency
- Flag all circular dependencies as architectural risks requiring Phase 0 resolution

**Critical Path Analysis:**
- Identify services that must be modernized first due to high fan-in
- Map dependency chains to determine sequencing constraints
- Calculate blast radius for each service (percentage of portfolio affected by failure)

**Integration Complexity Assessment:**
- Count integration points per service
- Identify services with highest coupling (most critical to modernize)
- Identify isolated services (can be parallelized)

### Step 4: Portfolio-Wide Pattern Analysis

Identify patterns, anti-patterns, and opportunities across the portfolio:

**Cross-Cutting Concerns Identification:**
- Group findings by criterion ID (e.g., INF-Q1, APP-Q2, DATA-Q3)
- For each criterion, count services with score < 3.0
- If count >= 3 services, flag as cross-cutting concern
- Calculate portfolio impact percentage (affected services / total services)
- Generate portfolio-level recommendations addressing all affected services

**Technology Stack Consolidation:**
- Count distinct programming languages in use
- Count distinct database engines (identify self-managed vs managed)
- Count distinct deployment patterns and compute types
- Identify opportunities for standardization
- Calculate diversity metrics and consolidation ROI

**Anti-Pattern Detection:**
- Group findings by criterion ID
- For each criterion, count services with score < 2.0 (critical gaps)
- If count >= 3, flag as repeated anti-pattern
- Assign severity based on count and business impact
- Identify root causes (organizational, technical, knowledge gaps)

**Shared Strengths Identification:**
- Group findings by criterion ID
- For each criterion, count services with score >= 3.5 (agent-ready)
- If count >= 3, flag as shared strength
- Identify reusable patterns and centers of excellence
- Recommend replication to other services

**Reusable Pattern Recognition:**
- Identify capabilities present in some services but missing in others
- Find successful implementations that can be templates
- Identify teams that can mentor others
- Map knowledge transfer opportunities


### Step 5: Calculate Portfolio Metrics

Generate comprehensive portfolio-level metrics and scores:

**Portfolio Readiness Score:**
- Calculate arithmetic mean of all service overall scores
- Calculate category-level portfolio scores (mean for each of 5 categories)
- Identify highest and lowest scoring services per category
- Calculate score variance to assess portfolio consistency

**Readiness Distribution:**
- **Agent-Ready** (3.5-4.0): Count and percentage of services
- **Partial** (2.5-3.4): Count and percentage of services
- **Needs Work** (1.5-2.4): Count and percentage of services
- **Not Ready** (<1.5): Count and percentage of services

**Modernization Effort Estimation:**
- Classify overall portfolio modernization effort as High, Medium, or Low
- Identify quick wins that benefit multiple services
- Classify effort for shared infrastructure improvements (Phase 0) as High, Medium, or Low

**Technology Stack Summary:**
- Count and percentage of services using each programming language
- Count and percentage of services using each database engine
- Count and percentage of services using each compute pattern
- Identify self-managed vs managed database distribution
- Calculate technology diversity metrics

**Risk Metrics:**
- Count of high-risk dependencies (score < 2.0 AND fan-in >= 3)
- Count of single points of failure (blast radius >= 50%)
- Count of circular dependencies
- Count of services with data availability risks
- Count of services with observability blind spots

### Step 6: Generate Dependency-Aware Portfolio Roadmap

Create a four-phase roadmap with dependency-aware sequencing:

**Phase Assignment Algorithm:**

**Phase 0 — Foundation (Months 0-1):**
- Cross-cutting concerns affecting 3+ services (portfolio-level solutions)
- Shared infrastructure improvements benefiting multiple services
- Circular dependency breaking activities (must be resolved first)
- Organizational enablers (training, tooling, standards)

**Phase 1 — Core Services (Months 1-3):**
- Foundation services (fan-in >= 3, fan-out <= 1) - must go first
- Services with no dependencies (can start immediately)
- Services with score < 2.0 AND high blast radius (critical risks)
- Establish patterns and reference implementations

**Phase 2 — Dependent Services (Months 3-6):**
- Services depending only on Phase 1 services
- Services with moderate dependencies (2-3 dependencies)
- Services with score 2.0-3.0 (moderate gaps)
- Replicate proven patterns from Phase 1

**Phase 3 — Optimization (Months 6-9):**
- Leaf services (fan-in <= 1, fan-out >= 2)
- Services with score >= 3.0 (minor gaps only)
- Optional enhancements and advanced capabilities
- Continuous improvement and optimization

**Sequencing Validation:**
- Verify no service is assigned to a phase before its dependencies
- Verify all services assigned to exactly one phase
- Verify total effort sums correctly across phases
- Flag any sequencing violations for manual review

**For Each Service Assignment, Include:**
- Service name and priority (P0/P1/P2)
- Current score and target state
- Key activities required
- Dependencies (services that must complete first)
- Services blocked (services waiting on this one)
- Estimated effort: High, Medium, or Low

### Step 7: Integration Opportunities

Identify specific opportunities for cross-service improvements:

**Shared Service Extraction:**
- Search findings for functionality mentioned in 3+ services
- Common candidates: authentication, logging, caching, notification, file processing
- For each opportunity:
  - List affected services
  - Describe current state (duplicated implementation)
  - Propose shared service solution
  - List benefits (reduced duplication, consistency, faster development)
  - Classify implementation effort as High, Medium, or Low
  - Assign priority (High/Medium/Low) based on impact and number of services affected

**Event-Driven Architecture Opportunities:**
- Identify services with synchronous dependencies (APP-Q3 score < 3)
- Check if message queues exist in portfolio (INF-Q4 score >= 3 in any service)
- For each opportunity:
  - Describe current synchronous integration
  - Propose event-driven solution (EventBridge, SNS/SQS, MSK)
  - List benefits (decoupling, resilience, scalability)
  - Classify effort as High, Medium, or Low

**API Gateway Consolidation:**
- Identify services with separate API gateways (INF-Q7 findings)
- Propose unified API gateway strategy
- Benefits: consistent auth, rate limiting, monitoring, cost reduction
- Classify effort as High, Medium, or Low

**Observability Unification:**
- Identify services with different observability stacks (OPS-Q1, OPS-Q2 findings)
- Propose unified observability platform
- Benefits: end-to-end tracing, consistent metrics, reduced tool sprawl
- Classify effort as High, Medium, or Low

### Step 8: Risk Assessment

Perform comprehensive risk analysis across the portfolio:

**High-Risk Dependency Identification:**
- Identify services with score < 2.0 AND fan-in >= 3 (many services depend on them)
- These are critical services in poor condition that pose portfolio-wide risk
- Calculate likelihood based on service score (High: <2.0, Medium: 2.0-3.0, Low: >=3.0)
- Calculate impact based on blast radius (High: >=50%, Medium: 25-50%, Low: <25%)

**Single Points of Failure (SPOF):**
- Identify services with blast radius >= 50% of portfolio
- Check findings for redundancy mentions (HA, multi-AZ, failover)
- If no redundancy mentioned AND high blast radius, flag as SPOF
- Prioritize SPOF mitigation in Phase 0 or Phase 1

**Circular Dependency Risks:**
- All circular dependencies detected in Step 3 are architectural risks
- Circular dependencies prevent independent deployment and scaling
- Must be broken in Phase 0 before service-level modernization

**Data Availability Risks:**
- Identify services with self-managed databases (DATA-Q2 score < 4) AND high fan-in
- Self-managed databases are harder to scale and maintain
- When many services depend on them, availability risk is amplified

**Observability Blind Spots:**
- Identify services without distributed tracing (OPS-Q1 score < 3) AND high fan-out
- Services that call many others need tracing to debug issues
- Without tracing, troubleshooting cross-service issues is difficult

**Risk Matrix Generation:**
- Create likelihood × impact matrix with 9 cells (High/High, High/Medium, etc.)
- Assign priority: Critical (High/High), High (High/Med or Med/High), Medium (others), Low (Low/Low)
- For each risk, generate specific mitigation recommendation
- Include mitigation effort level (High/Medium/Low) and recommended phase

### Step 9: Resource Allocation Recommendations

Provide team structure and resource planning guidance:

**Team Structure Recommendation:**
- IF cross-cutting concerns count >= 5, THEN recommend centralized platform team
- IF cross-cutting concerns count < 5, THEN recommend federated model with embedded platform engineers
- Platform team responsibilities: Shared infrastructure, platform capabilities, standards, tooling
- Service team responsibilities: Service-specific modernization, feature development

**Platform Team Sizing:**
- IF cross-cutting concerns count >= 5, THEN recommend a dedicated platform team
- IF cross-cutting concerns count < 5, THEN a smaller embedded platform function may suffice
- Platform team scope scales with the number of shared infrastructure improvements needed

**Service Team Sizing:**
- Recommend team structure based on number of services and phase parallelization
- Services in the same phase can be worked concurrently by separate teams
- Consider skill mix: senior engineers for complex services, junior for simpler ones

**Skill Gap Analysis:**
- Extract required skills from roadmap activities (e.g., "containerize application" requires Docker/ECS skills)
- Extract current skills from assessment findings (e.g., "team has experience with Lambda")
- Compare required vs current to identify gaps
- Common gaps: IaC (Terraform/CDK), containers (Docker/ECS/EKS), serverless (Lambda), observability (X-Ray/CloudWatch)

**Training Recommendations:**
- For each skill gap, recommend specific AWS Skill Builder courses or workshops from the catalog below
- Prioritize training for Phase 0 and Phase 1 skills (needed first)
- Consider certification paths for critical skills (e.g., AWS Solutions Architect, DevOps Engineer)
- Only include links from categories that are relevant to the portfolio-wide skill gaps identified

**Learning Materials Catalog:**

Include relevant links only from the following categories based on portfolio-wide skill gaps:

*Module 2: Move to Cloud Native (Containers and Serverless):*
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for microservices decomposition: Strangler Fig, Anti-corruption Layer, Saga patterns, Event Sourcing, Circuit Breaker, API routing, Hexagonal Architecture, and more
- AWS Modernization Pathways: Move to Cloud Native Serverless — https://skillbuilder.aws/learning-plan/CMK2J48MVN/aws-modernization-pathways-move-to-cloud-native-serverless-includes-labs/EFUPP53B4Q
- Lambda Foundations — https://skillbuilder.aws/learn/XHRS91KKK6/aws-lambda-foundations/R85JRN3APC
- Architecting Serverless Applications — https://skillbuilder.aws/learn/MRWENY7FSX/architecting-serverless-applications/QVFY2JHVEH
- Amazon API Gateway for Serverless Applications — https://skillbuilder.aws/learn/GQA6FHWPJD/amazon-api-gateway-for-serverless-applications/JVRZ3PSW4H
- Deploying Serverless Applications — https://skillbuilder.aws/learn/M531VCW415/deploying-serverless-applications/SMY21G7FYZ
- Introduction to Amazon DynamoDB (Lab) — https://skillbuilder.aws/learn/6DYXN7K7ZQ/lab--introduction-to-amazon-dynamodb/GZ3EU55RYJ
- Amazon DynamoDB for Serverless Architecture — https://skillbuilder.aws/learn/SY1Y83VKTB/amazon-dynamodb-for-serverless-architectures/K9NM3PHH3S
- Modernize a Monolith to ECS and Fargate using Application Discovery — https://skillbuilder.aws/learn/1YXAWYH2WA/modernize-a-monolith-to-ecs-and-fargate-using-application-discovery/AQ37WHN3K1
- Meeting Simulator: Transform Monolithic App into Serverless Microservices — https://skillbuilder.aws/learn/HUKQHYU9TB/meeting-simulator-transforming-our-monolithic-app-into-serverless-microservices/NS6S2J7YR7

*Module 3: Move to Containers with Amazon ECS and EKS:*
- AWS Modernization Pathways: Move to Containers with Amazon EKS — https://skillbuilder.aws/learning-plan/GNYBZ9X9EM/aws-modernization-pathways-move-to-containers-with-amazon-eks-includes-labs/1HB9MKXD2N
- AWS Modernization Pathways: Move to Containers with Amazon ECS — https://skillbuilder.aws/learning-plan/CDA8Y4JRRR/aws-modernization-pathways-move-to-containers-with-amazon-ecs-includes-labs/1UB9AW4KYN
- Introduction to Containers — https://skillbuilder.aws/learn/CUCA1DK47V/introduction-to-containers/XJ58VC1FF5
- AWS Fargate Getting Started — https://skillbuilder.aws/learn/6QS9CM1V7K/aws-fargate-getting-started/EDX6V7B5YR
- Amazon ECR Getting Started — https://skillbuilder.aws/learn/M494WWS5EF/amazon-ecr-getting-started/N5CQ7DC6HT
- Amazon EKS Primer — https://skillbuilder.aws/learn/Z521GMBP1J/amazon-eks-primer/NGM5AF9K72
- Deploy Applications on Amazon EKS (Lab) — https://skillbuilder.aws/learn/2B5XUE2V9C/lab--deploy-applications-on-amazon-elastic-kubernetes-service-eks/SM5HZNTY9J
- Amazon ECS Getting Started — https://skillbuilder.aws/learn/CY2F57HH7V/amazon-ecs-getting-started/4QUDNRVSNC
- Working with Amazon Elastic Container Service (Lab) — https://skillbuilder.aws/learn/CV6ZEU3NHE/working-with-amazon-elastic-container-service/X989GB8H74
- EKS Workshop — https://www.eksworkshop.com/
- EKS Auto Mode Workshop — https://catalog.workshops.aws/workshops/aadbd25d-43fa-4ac3-ae88-32d729af8ed4

*Module 4: Move to Managed Databases:*
- AWS Modernization Pathways: Move to Managed Databases — https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC/aws-modernization-pathways-move-to-managed-databases-includes-labs/2S2QZKG9DV
- Introduction to Building with AWS Databases — https://skillbuilder.aws/learn/HYKKWEN9ZS/introduction-to-building-with-aws-databases/V7RVH2KY91
- Selecting your Data Migration Strategy with AWS — https://skillbuilder.aws/learn/RKGP54WJPP/selecting-your-data-migration-strategy-with-aws/D38U3CZEYR
- AWS Database Migration Service (DMS) Getting Started — https://skillbuilder.aws/learn/ND246G8Y3W/aws-database-migration-service-aws-dms-getting-started/QK5CCBP464
- Introduction to AWS Database Migration Service (Lab) — https://skillbuilder.aws/learn/CX63W1TFSH/introduction-to-aws-database-migration-service/3DJVXSU4SE
- Amazon RDS for Oracle Getting Started — https://skillbuilder.aws/learn/YMYMJUMAET/amazon-rds-for-oracle-getting-started/74GQB3CA9U
- Amazon RDS for SQL Server Getting Started — https://skillbuilder.aws/learn/WSV85JHZFF/amazon-rds-for-sql-server-getting-started/E446MXPEYH
- Migrating RDS MySQL to Aurora (Lab) — https://skillbuilder.aws/learn/RZF2GBUUWX/migrating-rds-mysql-to-aurora-with-read-replica/SMG825PXTK
- Amazon DocumentDB Getting Started — https://skillbuilder.aws/learn/5RTP1DW5WQ/amazon-documentdb-with-mongodb-compatibility-getting-started/JDFWRT5GPD
- Amazon Keyspaces Getting Started — https://skillbuilder.aws/learn/KHGZNGWXKV/amazon-keyspaces-getting-started/MXK17GET8G
- Amazon RDS for MariaDB Getting Started — https://skillbuilder.aws/learn/DAFQM637NV/amazon-rds-for-mariadb-getting-started/N2Z47FGXSE
- AWS PartnerCast: Vector Databases for Generative AI Applications — https://skillbuilder.aws/learn/UQ74USQJHU/aws-partnercast--vector-databases-for-generative-ai-applications--technical/7DKMBAPCST

*Module 5: Move to Managed Analytics:*
- AWS Modernization Pathways: Move to Managed Analytics — https://skillbuilder.aws/learning-plan/RWZA84NMVV/aws-modernization-pathways-move-to-managed-analytics--includes-labs/9BAKK2QQQU

*Module 6: Move to Modern DevOps:*
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
- Working with AWS CodeCommit — https://skillbuilder.aws/learn/SH4UVGQX6S/working-with-aws-codecommit/Y9UGFPK95M
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
- AWS CloudFormation Getting Started — https://skillbuilder.aws/learn/RH22P2RXU4/aws-cloudformation-getting-started/KEK5BT6HSE
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
- Monitor Java Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/PMCTXKYK1Y/monitor-java-applications-using-amazon-cloudwatch-application-signals/15ZK4ETKE9
- Monitor .NET Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/255DDEDPV5/monitor-net-applications-using-amazon-cloudwatch-application-signals/1WZ1NT16HJ
- Monitor Python Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/JMPDZD64MV/monitor-python-applications-using-amazon-cloudwatch-application-signals/2JP3J2MPCK
- AWS Developer: CI/CD Automation — https://skillbuilder.aws/learn/C1KF8ZJ1D8/aws-developer--cicd-automation/KY1E1JS9FA
- AWS PartnerCast: Automate EKS Deployments With GitOps Using ArgoCD and GitHub Actions — https://skillbuilder.aws/learn/D9U7XMXP31/aws-partnercast--tech-talks--automate-eks-deployments-with-gitops-using-argocd-and-github-actions--technical/Z4M9Z8FY88
- AWS PartnerCast: Next-Gen Platform Engineering: Combining EKS, GitOps & Amazon Q for Intelligent DevOps — https://skillbuilder.aws/learn/FJBV2YWNSS/aws-partnercast--tech-talks--nextgen-platform-engineering-combining-eks-gitops--amazon-q-for-intelligent-devops--technical/NZ284HRTVG
- AWS PartnerCast: Unleash Innovation with a Cloud Operating Model and Platform Engineering — https://skillbuilder.aws/learn/EG2A78NXEC/aws-partnercast--tech-talks--unleash-innovation-with-a-cloud-operating-model-and-platform-engineering--technical/CC8ZTK88QK
- EKS Workshop: Automation — https://www.eksworkshop.com/docs/automation/
- EKS SaaS GitOps Workshop — https://catalog.workshops.aws/eks-saas-gitops/en-US/03-lab1

*Module 7: Move to AI:*
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
- Introduction to Generative AI: Art of the Possible — https://skillbuilder.aws/learn/ZEVZZ1D4AS/introduction-to-generative-ai--art-of-the-possible/Y7MTGJCW1U
- Planning a Generative AI Project — https://skillbuilder.aws/learn/HU1FQRGDDZ/planning-a-generative-ai-project/SYR3SCPSHC
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
- Essentials for Prompt Engineering — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
- AWS SimuLearn: Prompt Engineering with Amazon Bedrock — https://skillbuilder.aws/learn/FC13FQVQYG/aws-simulearn-prompt-engineering-with-amazon-bedrock/QDGW58VYHP
- Optimizing Foundation Models — https://skillbuilder.aws/learn/CDYTAJCKGY/optimizing-foundation-models/PVR1FRGN1T
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
- Amazon Q Developer Getting Started — https://skillbuilder.aws/learn/BQMRXE8AB4/amazon-q-developer-getting-started/JY4XXGZDJA
- Re-imagine Developer Experience using Amazon Q Developer (Lab) — https://skillbuilder.aws/learn/F7D8YHMVYK/lab--reimagine-developer-experience-using-amazon-q-developer/ZWRC749F68
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
- DevOps and AI on AWS: CloudWatch Anomaly Detection (Lab) — https://skillbuilder.aws/learn/RWYVJ73MXP/lab--devops-and-ai-on-aws-cloudwatch-anomaly-detection/BRPDNZUGU7
- Introduction to AWS DevOps Agent (Lab) — https://skillbuilder.aws/learn/2BMGKG58ZU/introduction-to-aws-devops-agent/S61EE8J7S9
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
- AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84

**External Support Recommendations:**
- Recommend AWS Professional Services or consulting partners for:
  - High-risk activities (e.g., database migration, architecture redesign)
  - Skill gaps that cannot be filled internally in time
  - Accelerating Phase 0 shared infrastructure work
  - Knowledge transfer and training
- Estimate external support duration: typically a few months for platform work, shorter for individual services


### Step 10: Map Portfolio to AWS Modernization Pathways

Aggregate individual service pathway triggers to produce a portfolio-level modernization pathway plan. This replaces the traditional multi-meeting pathway definition process with data-driven pathway assignment.

**Pathway Definitions:**

The AWS Modernization Pathways framework recognizes there is no "one-size-fits-all" approach. A customer portfolio may be divided into multiple pathways depending on workloads and priorities; these pathways can be executed in parallel.

- **Move to Cloud Native**: Decompose monolith applications into loosely coupled distributed architectures using microservices (Lambda, API Gateway, Step Functions, EventBridge)
- **Move to Containers**: Containerize existing workloads and adopt fully managed container orchestration services (ECS, EKS, Fargate, ECR)
- **Move to Open Source**: Move away from commercial workloads/licenses to open source for flexibility and reduced cost (RDS open source engines, EKS, Amazon Linux)
- **Move to Managed Databases**: Adopt fully managed purpose-built cloud native databases for scalability and reduced operational burden (Aurora, RDS, DynamoDB, DocumentDB, ElastiCache)
- **Move to Managed Analytics**: Adopt fully managed, cost-optimized data lake and real-time analytics (Redshift, Kinesis, MSK Serverless, Athena, Lake Formation)
- **Move to Modern DevOps**: Adopt modern philosophies, practices, and tools for high-velocity application delivery (CodeCommit, CodeBuild, CodePipeline, CodeDeploy, CloudFormation, CDK, X-Ray)
- **Move to AI**: Leverage AWS AI services to transform applications with AI capabilities, bridging traditional modernization and AI-driven computing (Amazon Bedrock, Amazon Bedrock AgentCore, Amazon Q, SageMaker)

**Per-Service Pathway Trigger Rules:**

For each service in the portfolio, evaluate pathway triggers based on individual assessment scores:

- **Move to Cloud Native**: APP-Q4 < 4 OR INF-Q1 < 3 OR APP-Q3 < 3 OR APP-Q10 < 3
- **Move to Containers**: INF-Q1 < 3 OR APP-Q4 < 4 (monolith needing containerization) OR no container definitions found
- **Move to Open Source**: DATA-Q11 < 3 (proprietary SQL) OR INF-Q2 findings mention commercial database engines
- **Move to Managed Databases**: INF-Q2 < 4 (self-managed databases) OR DATA-Q2 < 4 (self-hosted vector DB) OR DATA-Q10 < 4 (EOL engines)
- **Move to Managed Analytics**: INF-Q8 < 3 (self-managed streaming) OR DATA-Q4 < 3 (data source sprawl) OR no managed analytics detected
- **Move to Modern DevOps**: INF-Q5 < 3 OR INF-Q6 < 3 OR OPS-Q9 < 3 OR OPS-Q10 < 3 OR OPS-Q1 < 3
- **Move to AI**: APP-Q13 < 3 OR DATA-Q1 < 3 OR DATA-Q3 < 3 OR OPS-Q3 < 3 OR OPS-Q6 < 3

**Portfolio Pathway Aggregation:**

For each pathway:
- Count the number of services that trigger it
- Calculate the percentage of portfolio affected
- Determine portfolio-level priority:
  - High: Pathway triggered for >= 60% of services OR triggered for any P0 foundation service
  - Medium: Pathway triggered for 30-59% of services
  - Low: Pathway triggered for < 30% of services
- Aggregate estimated effort level (High/Medium/Low) across all affected services
- Identify common trigger criteria (which specific gaps are most prevalent)

**Cross-Pathway Dependency Analysis:**

Identify dependencies between pathways at the portfolio level:
- Move to Containers is often a prerequisite for Move to Cloud Native (containerize before decomposing)
- Move to Open Source may be a prerequisite for Move to Managed Databases (migrate off proprietary first)
- Move to Modern DevOps enables faster execution of all other pathways (CI/CD accelerates delivery)
- Move to Managed Databases and Move to Cloud Native are prerequisites for Move to AI (data foundations and service boundaries needed for agent tools)

**Parallel Execution Planning:**

- Group pathways into parallel execution tracks based on dependencies
- Map pathway execution to the 4-phase roadmap (Phase 0-3)
- Identify which services can pursue multiple pathways simultaneously
- Calculate total portfolio effort accounting for parallelization

**Pathway-to-Learning Materials Mapping:**

Each pathway maps directly to a learning materials module:
- Move to Cloud Native → Module 2: Move to Cloud Native (Containers and Serverless)
- Move to Containers → Module 3: Move to Containers with Amazon ECS and EKS
- Move to Open Source → Module 4: Move to Managed Databases (open source engines section)
- Move to Managed Databases → Module 4: Move to Managed Databases
- Move to Managed Analytics → Module 5: Move to Managed Analytics
- Move to Modern DevOps → Module 6: Move to Modern DevOps
- Move to AI → Module 7: Move to AI

### Step 11: Generate the Portfolio Agentic Readiness Report

**Output Location:**
- Create a directory named `agentic-readiness-assessment` in the portfolio root directory if it doesn't already exist
- Create the report file with the naming pattern: `{portfolio-name}-portfolio-agentic-readiness-report.md`
  - `{portfolio-name}` should be derived from the parent directory name or a user-provided portfolio identifier
  - Example: For a portfolio named "microservices-platform", create `microservices-platform-portfolio-agentic-readiness-report.md`
- Full path example: `agentic-readiness-assessment/microservices-platform-portfolio-agentic-readiness-report.md`

**Report Structure:**

Create the report file with exactly this structure:

```markdown
# Portfolio Agentic Readiness Assessment Report
**Portfolio**: <portfolio name or parent directory>
**Services Assessed**: <count>
**Assessment Date**: <date>
**Assessed by**: AWS Transform Custom — Portfolio Agentic Readiness Assessment

---

## Table of Contents

1. Executive Dashboard
2. Portfolio Readiness Overview
3. Service Dependency Map
4. Cross-Cutting Concerns
5. Portfolio Modernization Roadmap
   - Phase 0 — Foundation (Months 0-1)
   - Phase 1 — Core Services (Months 1-3)
   - Phase 2 — Dependent Services (Months 3-6)
   - Phase 3 — Optimization (Months 6-9)
6. AWS Modernization Pathways
7. Integration Opportunities
8. Resource Allocation Recommendations
9. Recommended Self-Paced Learning Materials
10. Risk Analysis
11. Service-by-Service Summary
12. Appendix: Assessment Inventory

---

## Executive Dashboard

<2-3 paragraph executive summary highlighting portfolio-wide readiness, critical dependencies, top priorities, and expected timeline for agentic enablement.>

### Portfolio Readiness Score: X.X / 4.0

| Category | Portfolio Score | Distribution | Status |
|----------|----------------|--------------|--------|
| Infrastructure & Platform | X.X / 4.0 | ✅ N services, 🟡 N services, 🟠 N services, ❌ N services | <emoji> |
| Application Architecture | X.X / 4.0 | ✅ N services, 🟡 N services, 🟠 N services, ❌ N services | <emoji> |
| Data Foundations | X.X / 4.0 | ✅ N services, 🟡 N services, 🟠 N services, ❌ N services | <emoji> |
| Identity, Security & Governance | X.X / 4.0 | ✅ N services, 🟡 N services, 🟠 N services, ❌ N services | <emoji> |
| Operations & Observability | X.X / 4.0 | ✅ N services, 🟡 N services, 🟠 N services, ❌ N services | <emoji> |

**Readiness Distribution:**
- ✅ Agent-Ready (3.5-4.0): N services (X%)
- 🟡 Partial (2.5-3.4): N services (X%)
- 🟠 Needs Work (1.5-2.4): N services (X%)
- ❌ Not Ready (< 1.5): N services (X%)

### Key Metrics

| Metric | Value | Insight |
|--------|-------|---------|
| Total Services | N | <insight> |
| Average Readiness Score | X.X / 4.0 | <insight> |
| Services Ready for Agents | N (X%) | <insight> |
| Critical Dependencies | N | <insight> |
| Shared Infrastructure Gaps | N | <insight> |
| Estimated Modernization Effort | High/Medium/Low | <insight> |
| Expected Timeline | X months | <insight> |

---

## Portfolio Readiness Overview

### Technology Stack Summary

**Programming Languages:**
- Language 1: N services (X%)
- Language 2: N services (X%)
- <list all languages with counts>

**Database Engines:**
- Engine 1: N services (X%)
- Engine 2: N services (X%)
- <list all databases with counts>

**Compute Patterns:**
- Serverless (Lambda): N services (X%)
- Containers (ECS/EKS): N services (X%)
- EC2: N services (X%)
- Monolith: N services (X%)

**Deployment Maturity:**
- Full CI/CD: N services (X%)
- Partial CI/CD: N services (X%)
- Manual deployment: N services (X%)

### Common Strengths

<List 3-5 capabilities that are present across multiple services and can be leveraged>

### Common Gaps

<List 5-7 gaps that appear across multiple services and should be addressed at portfolio level>

---

## Service Dependency Map

### High-Level Architecture

<Describe the overall service architecture, key integration patterns, and data flows>

### Service Dependency Matrix

| Service | Depends On | Depended On By | Coupling Score | Priority |
|---------|------------|----------------|----------------|----------|
| Service A | Service B, Service C | Service D, Service E | High/Medium/Low | P0/P1/P2 |
| <list all services> |

**Coupling Score Definitions:**
- High: Synchronous dependencies, shared databases, tight coupling
- Medium: Async dependencies, some shared infrastructure
- Low: Minimal dependencies, loose coupling

**Priority Definitions:**
- P0: Critical path services that block others
- P1: Important services with moderate dependencies
- P2: Leaf services with minimal dependencies

### Critical Path Analysis

<Identify the critical path of services that must be modernized first due to dependencies>

1. **Foundation Services** (must be modernized first):
   - Service A: <reason>
   - Service B: <reason>

2. **Dependent Services** (can be modernized after foundation):
   - Service C: depends on Service A
   - Service D: depends on Service B

3. **Independent Services** (can be parallelized):
   - Service E, Service F, Service G

### Integration Points

**Synchronous Integrations:**
- Service A → Service B: REST API, <details>
- <list all sync integrations>

**Asynchronous Integrations:**
- Service A → Service C: SQS queue, <details>
- <list all async integrations>

**Shared Infrastructure:**
- Database X: used by Service A, Service B, Service C
- API Gateway Y: fronts Service D, Service E
- <list all shared components>

---

## Cross-Cutting Concerns

### Infrastructure & Platform

**Portfolio Score: X.X / 4.0**

<Analyze common infrastructure patterns and gaps across all services>

**Common Patterns:**
- <pattern 1>: present in N services
- <pattern 2>: present in N services

**Critical Gaps:**
1. <gap 1>: affects N services
   - Impact: <describe impact>
   - Recommendation: <portfolio-level solution>

2. <gap 2>: affects N services
   - Impact: <describe impact>
   - Recommendation: <portfolio-level solution>

### Application Architecture

**Portfolio Score: X.X / 4.0**

<Analyze common application patterns and gaps>

### Data Foundations

**Portfolio Score: X.X / 4.0**

<Analyze common data patterns and gaps>

### Identity, Security & Governance

**Portfolio Score: X.X / 4.0**

<Analyze common security patterns and gaps>

### Operations & Observability

**Portfolio Score: X.X / 4.0**

<Analyze common operational patterns and gaps>

---

## Portfolio Modernization Roadmap

<Account for cross-service dependencies, shared infrastructure, and organizational capacity. Sequence work to minimize risk and maximize value delivery.>

### Sequencing Principles

1. **Foundation First**: Shared infrastructure and platform capabilities before service-specific work
2. **Dependency Order**: Upstream services before downstream dependents
3. **Risk Mitigation**: High-risk changes sequenced to minimize blast radius
4. **Parallel Tracks**: Independent services can be modernized concurrently
5. **Quick Wins**: Early wins build momentum and demonstrate value

### Phase 0 — Foundation (Months 0-1)

**Objective**: Establish shared capabilities and organizational readiness

**Shared Infrastructure:**
- <infrastructure improvement 1>: benefits N services
- <infrastructure improvement 2>: benefits N services

**Platform Capabilities:**
- <platform capability 1>: enables service-level work
- <platform capability 2>: enables service-level work

**Organizational Enablers:**
- Training: <topics>
- Tooling: <tools>
- Standards: <standards>

**Expected Outcomes:**
- <outcome 1>
- <outcome 2>

**Estimated Effort**: High/Medium/Low

### Phase 1 — Core Services (Months 1-3)

**Objective**: Modernize foundational services that others depend on

**Services in Scope:**
1. **Service A** (P0, Score: X.X/4.0)
   - Current State: <summary>
   - Target State: <summary>
   - Key Activities:
     - <activity 1>
     - <activity 2>
   - Dependencies: None (foundation service)
   - Blocks: Service C, Service D
   - Estimated Effort: High/Medium/Low

2. **Service B** (P0, Score: X.X/4.0)
   - <same structure>

**Cross-Service Activities:**
- <activity that spans multiple services>

**Expected Outcomes:**
- <outcome 1>
- <outcome 2>

**Estimated Effort**: High/Medium/Low

### Phase 2 — Dependent Services (Months 3-6)

**Objective**: Modernize services that depend on Phase 1 services

**Services in Scope:**
1. **Service C** (P1, Score: X.X/4.0)
   - Current State: <summary>
   - Target State: <summary>
   - Key Activities:
     - <activity 1>
     - <activity 2>
   - Dependencies: Service A (Phase 1)
   - Blocks: None
   - Estimated Effort: High/Medium/Low

2. **Service D** (P1, Score: X.X/4.0)
   - <same structure>

**Parallel Tracks:**
- Services E, F, G can be modernized concurrently (no dependencies)

**Expected Outcomes:**
- <outcome 1>
- <outcome 2>

**Estimated Effort**: High/Medium/Low

### Phase 3 — Optimization (Months 6-9)

**Objective**: Optimize cross-service workflows and implement advanced capabilities

**Activities:**
- Implement distributed tracing across all services
- Optimize cross-service data flows
- Implement advanced agentic capabilities
- Consolidate and standardize patterns
- Continuous improvement

**Expected Outcomes:**
- <outcome 1>
- <outcome 2>

**Estimated Effort**: High/Medium/Low

### Total Portfolio Effort

**Total Estimated Effort**: High/Medium/Low
**Expected Timeline**: X months (with Y parallel tracks)

---

## AWS Modernization Pathways

Based on the portfolio-wide assessment findings, the following AWS Modernization Pathways have been identified for each service. The AWS Modernization Pathways framework recognizes there is no "one-size-fits-all" approach — a customer portfolio may be divided into multiple pathways depending on workloads and priorities, and these pathways can be executed in parallel.

### Portfolio Pathway Summary

| Pathway | Services Triggered | % of Portfolio | Priority | Est. Effort |
|---------|--------------------|----------------|----------|-------------|
| Move to Cloud Native | N services | X% | High/Medium/Low | High/Medium/Low |
| Move to Containers | N services | X% | High/Medium/Low | High/Medium/Low |
| Move to Open Source | N services | X% | High/Medium/Low | High/Medium/Low |
| Move to Managed Databases | N services | X% | High/Medium/Low | High/Medium/Low |
| Move to Managed Analytics | N services | X% | High/Medium/Low | High/Medium/Low |
| Move to Modern DevOps | N services | X% | High/Medium/Low | High/Medium/Low |
| Move to AI | N services | X% | High/Medium/Low | High/Medium/Low |

### Per-Service Pathway Assignment

| Service | Cloud Native | Containers | Open Source | Managed DB | Managed Analytics | Modern DevOps | Move to AI |
|---------|-------------|------------|-------------|------------|-------------------|---------------|------------|
| Service A | ✅ | ✅ | — | ✅ | — | ✅ | ✅ |
| Service B | — | ✅ | — | — | — | ✅ | — |
| <list all services> |

### Pathway Dependencies and Parallel Execution

<Describe cross-pathway dependencies and how pathways can be executed in parallel across the portfolio.>

**Sequential Dependencies:**
- <pathway A> should precede <pathway B> because <reason>
- <pathway C> should precede <pathway D> because <reason>

**Parallel Execution Tracks:**
- **Track 1**: <pathways that can run concurrently across the portfolio>
- **Track 2**: <pathways that can run concurrently>
- **Track 3**: <pathways that can run concurrently>

### Pathway Details

<For each triggered pathway, include a subsection:>

#### Move to <Pathway Name>

- **Services Affected**: Service A, Service B, Service C (N total)
- **Portfolio Priority**: High/Medium/Low
- **Common Trigger Criteria**:
  - <criterion ID> score < X: affects N services
  - <criterion ID> score < X: affects N services
- **Representative AWS Services**: <list>
- **Key Activities**:
  1. <portfolio-level activity>
  2. <per-service activity>
- **Cross-Service Synergies**: <shared patterns, reusable templates, common tooling>
- **Estimated Effort**: High/Medium/Low across N services
- **Roadmap Phase Alignment**: Phase 0/1/2/3
- **Relevant Learning Materials**: Module X — <module name>

<Repeat for each triggered pathway>

### Example: Parallel Pathway Execution for a Single Service

<Pick one representative service and show how it simultaneously pursues multiple pathways. For example:>

**Service A** simultaneously pursues:
- Move to Cloud Native: Break monolith into microservices
- Move to Containers: Containerize application runtime
- Move to Modern DevOps: Implement CI/CD pipelines
- Move to Managed Databases: Migrate to managed data tier
- Move to AI: Integrate agentic capabilities

---

## Integration Opportunities

### Shared Service Extraction

<Identify common functionality that could be extracted into shared services>

**Opportunity 1: <service name>**
- Current State: Duplicated in Service A, Service B, Service C
- Proposed Solution: Extract into shared service
- Benefits: <benefits>
- Effort: High/Medium/Low
- Priority: High/Medium/Low

### Event-Driven Architecture

<Identify opportunities to replace sync calls with async events>

**Opportunity 1: <integration name>**
- Current State: Service A calls Service B synchronously
- Proposed Solution: Event-driven with EventBridge/SNS
- Benefits: <benefits>
- Effort: High/Medium/Low
- Priority: High/Medium/Low

### API Gateway Consolidation

<Identify opportunities for unified API management>

### Observability Unification

<Identify opportunities for standardized observability>

---

## Resource Allocation Recommendations

### Team Structure

**Recommended Approach**: <centralized platform team + embedded service teams / federated / other>

**Platform Team** (X people):
- Responsibilities: Shared infrastructure, platform capabilities, standards
- Skills Required: <skills>

**Service Teams**:
- Responsibilities: Service-specific modernization
- Skills Required: <skills>

### Skill Gaps

<Identify skills needed but not currently available>

1. **Skill 1**: Required for <activities>, currently <available/not available>
2. **Skill 2**: Required for <activities>, currently <available/not available>

### Training Recommendations

<Recommend training programs based on common gaps>

### External Support

<Recommend where external consultants or AWS Professional Services could accelerate>

---

## Recommended Self-Paced Learning Materials

<Include relevant links only from the following categories based on portfolio-wide skill gaps identified in the Resource Allocation section. Focus on gaps that affect multiple services across the portfolio.>

**Module 2: Move to Cloud Native (Containers and Serverless):**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for microservices decomposition: Strangler Fig, Anti-corruption Layer, Saga patterns, Event Sourcing, Circuit Breaker, API routing, Hexagonal Architecture, and more
- AWS Modernization Pathways: Move to Cloud Native Serverless — https://skillbuilder.aws/learning-plan/CMK2J48MVN/aws-modernization-pathways-move-to-cloud-native-serverless-includes-labs/EFUPP53B4Q
- Lambda Foundations — https://skillbuilder.aws/learn/XHRS91KKK6/aws-lambda-foundations/R85JRN3APC
- Architecting Serverless Applications — https://skillbuilder.aws/learn/MRWENY7FSX/architecting-serverless-applications/QVFY2JHVEH
- Amazon API Gateway for Serverless Applications — https://skillbuilder.aws/learn/GQA6FHWPJD/amazon-api-gateway-for-serverless-applications/JVRZ3PSW4H
- Deploying Serverless Applications — https://skillbuilder.aws/learn/M531VCW415/deploying-serverless-applications/SMY21G7FYZ
- Introduction to Amazon DynamoDB (Lab) — https://skillbuilder.aws/learn/6DYXN7K7ZQ/lab--introduction-to-amazon-dynamodb/GZ3EU55RYJ
- Amazon DynamoDB for Serverless Architecture — https://skillbuilder.aws/learn/SY1Y83VKTB/amazon-dynamodb-for-serverless-architectures/K9NM3PHH3S
- Modernize a Monolith to ECS and Fargate using Application Discovery — https://skillbuilder.aws/learn/1YXAWYH2WA/modernize-a-monolith-to-ecs-and-fargate-using-application-discovery/AQ37WHN3K1
- Meeting Simulator: Transform Monolithic App into Serverless Microservices — https://skillbuilder.aws/learn/HUKQHYU9TB/meeting-simulator-transforming-our-monolithic-app-into-serverless-microservices/NS6S2J7YR7

**Module 3: Move to Containers with Amazon ECS and EKS:**
- AWS Modernization Pathways: Move to Containers with Amazon EKS — https://skillbuilder.aws/learning-plan/GNYBZ9X9EM/aws-modernization-pathways-move-to-containers-with-amazon-eks-includes-labs/1HB9MKXD2N
- AWS Modernization Pathways: Move to Containers with Amazon ECS — https://skillbuilder.aws/learning-plan/CDA8Y4JRRR/aws-modernization-pathways-move-to-containers-with-amazon-ecs-includes-labs/1UB9AW4KYN
- Introduction to Containers — https://skillbuilder.aws/learn/CUCA1DK47V/introduction-to-containers/XJ58VC1FF5
- AWS Fargate Getting Started — https://skillbuilder.aws/learn/6QS9CM1V7K/aws-fargate-getting-started/EDX6V7B5YR
- Amazon ECR Getting Started — https://skillbuilder.aws/learn/M494WWS5EF/amazon-ecr-getting-started/N5CQ7DC6HT
- Amazon EKS Primer — https://skillbuilder.aws/learn/Z521GMBP1J/amazon-eks-primer/NGM5AF9K72
- Deploy Applications on Amazon EKS (Lab) — https://skillbuilder.aws/learn/2B5XUE2V9C/lab--deploy-applications-on-amazon-elastic-kubernetes-service-eks/SM5HZNTY9J
- Amazon ECS Getting Started — https://skillbuilder.aws/learn/CY2F57HH7V/amazon-ecs-getting-started/4QUDNRVSNC
- Working with Amazon Elastic Container Service (Lab) — https://skillbuilder.aws/learn/CV6ZEU3NHE/working-with-amazon-elastic-container-service/X989GB8H74
- EKS Workshop — https://www.eksworkshop.com/
- EKS Auto Mode Workshop — https://catalog.workshops.aws/workshops/aadbd25d-43fa-4ac3-ae88-32d729af8ed4

**Module 4: Move to Managed Databases:**
- AWS Modernization Pathways: Move to Managed Databases — https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC/aws-modernization-pathways-move-to-managed-databases-includes-labs/2S2QZKG9DV
- Introduction to Building with AWS Databases — https://skillbuilder.aws/learn/HYKKWEN9ZS/introduction-to-building-with-aws-databases/V7RVH2KY91
- Selecting your Data Migration Strategy with AWS — https://skillbuilder.aws/learn/RKGP54WJPP/selecting-your-data-migration-strategy-with-aws/D38U3CZEYR
- AWS Database Migration Service (DMS) Getting Started — https://skillbuilder.aws/learn/ND246G8Y3W/aws-database-migration-service-aws-dms-getting-started/QK5CCBP464
- Introduction to AWS Database Migration Service (Lab) — https://skillbuilder.aws/learn/CX63W1TFSH/introduction-to-aws-database-migration-service/3DJVXSU4SE
- Amazon RDS for Oracle Getting Started — https://skillbuilder.aws/learn/YMYMJUMAET/amazon-rds-for-oracle-getting-started/74GQB3CA9U
- Amazon RDS for SQL Server Getting Started — https://skillbuilder.aws/learn/WSV85JHZFF/amazon-rds-for-sql-server-getting-started/E446MXPEYH
- Migrating RDS MySQL to Aurora (Lab) — https://skillbuilder.aws/learn/RZF2GBUUWX/migrating-rds-mysql-to-aurora-with-read-replica/SMG825PXTK
- Amazon DocumentDB Getting Started — https://skillbuilder.aws/learn/5RTP1DW5WQ/amazon-documentdb-with-mongodb-compatibility-getting-started/JDFWRT5GPD
- Amazon Keyspaces Getting Started — https://skillbuilder.aws/learn/KHGZNGWXKV/amazon-keyspaces-getting-started/MXK17GET8G
- Amazon RDS for MariaDB Getting Started — https://skillbuilder.aws/learn/DAFQM637NV/amazon-rds-for-mariadb-getting-started/N2Z47FGXSE
- AWS PartnerCast: Vector Databases for Generative AI Applications — https://skillbuilder.aws/learn/UQ74USQJHU/aws-partnercast--vector-databases-for-generative-ai-applications--technical/7DKMBAPCST

**Module 5: Move to Managed Analytics:**
- AWS Modernization Pathways: Move to Managed Analytics — https://skillbuilder.aws/learning-plan/RWZA84NMVV/aws-modernization-pathways-move-to-managed-analytics--includes-labs/9BAKK2QQQU

**Module 6: Move to Modern DevOps:**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
- Working with AWS CodeCommit — https://skillbuilder.aws/learn/SH4UVGQX6S/working-with-aws-codecommit/Y9UGFPK95M
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
- AWS CloudFormation Getting Started — https://skillbuilder.aws/learn/RH22P2RXU4/aws-cloudformation-getting-started/KEK5BT6HSE
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
- Monitor Java Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/PMCTXKYK1Y/monitor-java-applications-using-amazon-cloudwatch-application-signals/15ZK4ETKE9
- Monitor .NET Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/255DDEDPV5/monitor-net-applications-using-amazon-cloudwatch-application-signals/1WZ1NT16HJ
- Monitor Python Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/JMPDZD64MV/monitor-python-applications-using-amazon-cloudwatch-application-signals/2JP3J2MPCK
- AWS Developer: CI/CD Automation — https://skillbuilder.aws/learn/C1KF8ZJ1D8/aws-developer--cicd-automation/KY1E1JS9FA
- AWS PartnerCast: Automate EKS Deployments With GitOps Using ArgoCD and GitHub Actions — https://skillbuilder.aws/learn/D9U7XMXP31/aws-partnercast--tech-talks--automate-eks-deployments-with-gitops-using-argocd-and-github-actions--technical/Z4M9Z8FY88
- AWS PartnerCast: Next-Gen Platform Engineering: Combining EKS, GitOps & Amazon Q for Intelligent DevOps — https://skillbuilder.aws/learn/FJBV2YWNSS/aws-partnercast--tech-talks--nextgen-platform-engineering-combining-eks-gitops--amazon-q-for-intelligent-devops--technical/NZ284HRTVG
- AWS PartnerCast: Unleash Innovation with a Cloud Operating Model and Platform Engineering — https://skillbuilder.aws/learn/EG2A78NXEC/aws-partnercast--tech-talks--unleash-innovation-with-a-cloud-operating-model-and-platform-engineering--technical/CC8ZTK88QK
- EKS Workshop: Automation — https://www.eksworkshop.com/docs/automation/
- EKS SaaS GitOps Workshop — https://catalog.workshops.aws/eks-saas-gitops/en-US/03-lab1

**Module 7: Move to AI:**
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
- Introduction to Generative AI: Art of the Possible — https://skillbuilder.aws/learn/ZEVZZ1D4AS/introduction-to-generative-ai--art-of-the-possible/Y7MTGJCW1U
- Planning a Generative AI Project — https://skillbuilder.aws/learn/HU1FQRGDDZ/planning-a-generative-ai-project/SYR3SCPSHC
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
- Essentials for Prompt Engineering — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
- AWS SimuLearn: Prompt Engineering with Amazon Bedrock — https://skillbuilder.aws/learn/FC13FQVQYG/aws-simulearn-prompt-engineering-with-amazon-bedrock/QDGW58VYHP
- Optimizing Foundation Models — https://skillbuilder.aws/learn/CDYTAJCKGY/optimizing-foundation-models/PVR1FRGN1T
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
- Amazon Q Developer Getting Started — https://skillbuilder.aws/learn/BQMRXE8AB4/amazon-q-developer-getting-started/JY4XXGZDJA
- Re-imagine Developer Experience using Amazon Q Developer (Lab) — https://skillbuilder.aws/learn/F7D8YHMVYK/lab--reimagine-developer-experience-using-amazon-q-developer/ZWRC749F68
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
- DevOps and AI on AWS: CloudWatch Anomaly Detection (Lab) — https://skillbuilder.aws/learn/RWYVJ73MXP/lab--devops-and-ai-on-aws-cloudwatch-anomaly-detection/BRPDNZUGU7
- Introduction to AWS DevOps Agent (Lab) — https://skillbuilder.aws/learn/2BMGKG58ZU/introduction-to-aws-devops-agent/S61EE8J7S9
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
- AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84

Only include links from categories that are relevant to the portfolio-wide gaps found in this assessment.

---

## Risk Analysis

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| <risk 1> | High/Medium/Low | High/Medium/Low | <mitigation strategy> |
| <risk 2> | High/Medium/Low | High/Medium/Low | <mitigation strategy> |

### Organizational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| <risk 1> | High/Medium/Low | High/Medium/Low | <mitigation strategy> |
| <risk 2> | High/Medium/Low | High/Medium/Low | <mitigation strategy> |

### Dependency Risks

<Identify risks related to service dependencies>

### Single Points of Failure

<Identify critical services or infrastructure with no redundancy>

---

## Service-by-Service Summary

### Service A

- **Overall Score**: X.X / 4.0 <emoji>
- **Repository**: <path>
- **Assessment Date**: <date>
- **Category Scores**:
  - Infrastructure: X.X / 4.0
  - Application: X.X / 4.0
  - Data: X.X / 4.0
  - Security: X.X / 4.0
  - Operations: X.X / 4.0
- **Top Priorities**:
  1. <priority 1>
  2. <priority 2>
  3. <priority 3>
- **Dependencies**: <list>
- **Depended On By**: <list>
- **Modernization Pathways**: <list of triggered pathways for this service>
- **Modernization Phase**: Phase 0/1/2/3
- **Estimated Effort**: High/Medium/Low

<Repeat for all services>

---

## Appendix: Assessment Inventory

### Reports Analyzed

| Service | Repository Path | Assessment Date | Overall Score | Report Path |
|---------|----------------|-----------------|---------------|-------------|
| Service A | /path/to/repo | YYYY-MM-DD | X.X / 4.0 | /path/to/report |
| <list all services> |

### Assessment Methodology

- Individual assessments performed using: AWS Transform Custom — Agentic Readiness Assessment
- Portfolio assessment performed using: AWS Transform Custom — Portfolio Agentic Readiness Assessment
- Assessment criteria: 56 total criteria across 5 categories
- Scoring scale: 1-4 (Not Present, Needs Work, Partial, Agent-Ready)

---

## Recommended Next Steps

1. **Immediate (Week 1)**:
   - <action 1>
   - <action 2>

2. **Short-term (Month 1)**:
   - <action 1>
   - <action 2>

3. **Medium-term (Months 1-3)**:
   - <action 1>
   - <action 2>

4. **Long-term (Months 3-9)**:
   - <action 1>
   - <action 2>
```

## Validation / Exit Criteria

1. The directory `agentic-readiness-assessment` is created in the portfolio root (or already exists)
2. The report file `{portfolio-name}-portfolio-agentic-readiness-report.md` is created in the `agentic-readiness-assessment` directory
3. The report contains an Executive Dashboard with portfolio-wide scores
4. The report contains a Service Dependency Map with all services listed
5. The report contains Cross-Cutting Concerns analysis for all 5 categories
6. The report contains a Portfolio Modernization Roadmap with 4 phases
7. The roadmap respects dependency order (services are sequenced correctly)
8. The report contains an AWS Modernization Pathways section with all 7 pathways evaluated, per-service pathway assignments, and parallel execution plan
9. The report contains Integration Opportunities with specific recommendations
10. The report contains Resource Allocation Recommendations
11. The report contains a Recommended Self-Paced Learning Materials section with relevant links based on portfolio-wide skill gaps
12. The report contains Risk Analysis with specific risks identified
13. The report contains Service-by-Service Summary for all assessed services with pathway assignments
14. The report contains an Appendix listing all reports analyzed
15. All scores and metrics are calculated correctly from source reports
16. No source files were modified during the assessment

## Error Handling

### Fatal Errors (Terminate Execution)

**Insufficient Reports:**
- Error: Fewer than 2 individual assessment reports discovered
- Message: "Portfolio assessment requires at least 2 individual assessment reports. Found: {count}"
- Action: Terminate with exit code 1

**File Access Errors:**
- Error: Output file path is not writable
- Message: "Output path is not writable: {path}. Check permissions."
- Action: Terminate with exit code 1

**No Valid Reports:**
- Error: All discovered reports failed parsing validation
- Message: "No valid assessment reports found. All {count} discovered reports failed structure validation."
- Action: Terminate with exit code 1

### Warnings (Continue with Degraded Data)

**Missing Report Sections:**
- Warning: Assessment report missing required sections (e.g., no detailed findings)
- Action: Extract available data, use defaults for missing sections, log warning, continue
- Impact: Service may have incomplete data but is still included in portfolio analysis

**Malformed Scores:**
- Warning: Score not in "X.X / 4.0" format
- Action: Log warning, exclude service from score aggregations, continue
- Impact: Portfolio scores calculated without this service's contribution

**Missing Metadata:**
- Warning: Required metadata field missing (e.g., assessment date, tech stack)
- Action: Use default value, log warning, continue
- Impact: Service included with default/placeholder values

**Ambiguous Service References:**
- Warning: Cannot definitively identify service dependencies from findings
- Action: Proceed with partial dependency analysis, log warning, continue
- Impact: Dependency graph may be incomplete but analysis continues

**Duplicate Service Names:**
- Warning: Multiple services have the same name
- Action: Disambiguate using repository path, log warning, continue
- Impact: Services distinguished by path suffix in reports

### Edge Cases (Handle Gracefully)

**No Cross-Cutting Concerns:**
- Scenario: All gaps are service-specific (no criterion affects 3+ services)
- Action: State explicitly in report: "No cross-cutting concerns identified. All gaps are service-specific."
- Impact: Phase 0 may be empty or contain only shared infrastructure work

**Isolated Services:**
- Scenario: Service has no dependencies and no dependents
- Action: Assign to Phase 2 by default, note it can be parallelized
- Impact: Service can be modernized independently at any time

**Circular Dependencies:**
- Scenario: Strongly connected components detected in dependency graph
- Action: Flag all cycles as Phase 0 activities (must be broken first), continue with roadmap
- Impact: Affected services cannot be independently deployed until cycle is broken

**All Services High-Scoring:**
- Scenario: All services have scores >= 3.5 (agent-ready)
- Action: Generate roadmap focused on optimization and advanced capabilities
- Impact: Shorter timeline, focus on Phase 3 activities

**All Services Low-Scoring:**
- Scenario: All services have scores < 2.0 (not ready)
- Action: Generate roadmap with extended Phase 0 and Phase 1, recommend external support
- Impact: Longer timeline, higher investment required

## Constraints and Guardrails

**Read-Only Operation:**
- This transformation MUST NOT modify any source files
- Individual assessment reports are read-only inputs
- Only output is the new portfolio-agentic-readiness-report.md file

**Minimum Portfolio Size:**
- At least 2 individual assessment reports required
- Single-service "portfolios" are not supported (use individual assessment instead)

**Dependency Accuracy:**
- Only map dependencies explicitly mentioned or clearly inferred from findings
- Do NOT invent service relationships not evidenced in reports
- When in doubt, omit dependency rather than guess incorrectly

**Score Calculation Integrity:**
- Portfolio scores MUST be arithmetic means of service scores
- Do NOT adjust or normalize scores
- Exclude malformed scores from calculations rather than guessing values

**Sequencing Logic:**
- Roadmap phases MUST respect dependency order
- Upstream services MUST be assigned to earlier phases than dependents
- If dependency ordering cannot be satisfied, flag as circular dependency

**Effort Estimation:**
- Use High, Medium, or Low effort levels instead of numeric estimates (person-months, person-weeks, dollar amounts)
- High: Significant structural changes, multiple teams involved, long duration
- Medium: Moderate changes, single team can handle, weeks of work
- Low: Quick wins, minor changes, days of work
- Effort levels MUST be consistent across the report (same criteria applied everywhere)

**Risk Assessment:**
- Identify real risks based on findings, not generic risks
- Each risk MUST reference specific services and findings
- Do NOT include boilerplate risks without evidence

**Recommendation Specificity:**
- All recommendations MUST reference specific services and findings
- Avoid generic advice like "improve security" without specifics
- Each recommendation MUST include estimated effort and priority

**Modernization Pathways:**
- All 7 AWS Modernization Pathways MUST be evaluated against per-service trigger criteria
- Pathway triggers are based on individual service assessment scores, not portfolio averages
- A pathway is triggered for a service when ANY of its trigger conditions are met
- Multiple pathways executing in parallel is the norm, not the exception
- Portfolio-level pathway priority MUST be calculated from percentage of services triggered
- Cross-pathway dependencies MUST be identified and reflected in the parallel execution plan
- Each triggered pathway MUST map to the corresponding learning materials module
- Per-service pathway assignments MUST be included in the Service-by-Service Summary
