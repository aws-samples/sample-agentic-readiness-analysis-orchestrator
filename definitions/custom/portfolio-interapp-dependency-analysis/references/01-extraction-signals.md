# Extraction Signal Catalog

> **Purpose:** Loaded by the Portfolio Inter-Application Dependency (IAD) TD at Step 3. Defines
> which MOD questions carry integration signal, what each signal looks like in practice, the
> regular-expression seeds for mechanical extraction, and the third-party platform list used for
> external-node classification.

The patterns below are **seeds, not a parser.** Apply judgment over the prose first; use the
regular expressions to catch what judgment missed and to extract structured resource names
(catalogs, UNC paths, queue names) once a signal has been identified. A signal recognized only by
regex, with no surrounding prose supporting it, is low confidence.

---

## 1. High-Yield MOD Question IDs

MOD asks 38 questions across 5 categories. Integration signal concentrates in the questions below,
because answering them *requires* describing how the application talks to other systems. Read every
finding, but weight these.

| Question ID | Question subject | Signal it yields | Typical edge type |
|---|---|---|---|
| `INF-Q4` | Async Messaging and Streaming | Named peer calls; queue/topic/bus names; explicit statements that communication is synchronous | `async`, or `sync` when async is absent |
| `APP-Q3` | Async vs Sync Communication | Protocol and direction of inter-service calls | `sync`, `async` |
| `APP-Q2` | Monolith vs Microservices | Deployable units; shared database catalogs; shared DAL and library coupling | `shared_db` |
| `APP-Q6` | Service Discovery | Hardcoded endpoints, config-driven service URLs, registries (Eureka, Consul) | `sync`, `shared_infra` |
| `DATA-Q2` | Unified Data Access Layer | Shared data-access layers and the stores behind them | `shared_db` |
| `INF-Q2` | Managed Databases | Database engines and named instances or catalogs | `shared_db` |
| `DATA-Q1` | Unstructured Data Storage | UNC file shares, network paths, blob/object locations | `shared_infra` |
| `DATA-Q4` | Stored Procedures and Schema Complexity | Linked servers, cross-database procedures, cross-schema access | `shared_db` |
| `INF-Q3` | Workflow Orchestration | Schedulers, job servers, orchestrators (Hangfire, SQL Agent, Control-M) | `shared_infra` |
| `INF-Q6` | API Entry Point | Gateways, load balancers, reverse proxies, shared IIS hosts | `shared_infra` |
| `SEC-Q*` | Identity and access | Shared identity providers, SSO, LDAP, domain auth | `shared_infra` |
| `OPS-Q*` | Observability | Shared logging services and sinks — often a genuine shared-infra dependency | `shared_infra` |

Also read, outside `findings[]`:

- `top_gaps[].gap` and `.impact` — condensed restatements, occasionally naming a peer the finding did not.
- `decomposition_strategy.effort_factors.data_coupling` — direct statements about shared data.
- `decomposition_strategy.effort_factors.communication_patterns` — direct statements about call style.
- `metadata.archetype_justification` — frequently summarizes the integration surface in one sentence.

---

## 2. Reading Sentiment vs Mechanism

MOD scores the *absence* of a modern pattern, so its findings routinely describe real coupling in
the course of marking it down. Extract the mechanism; ignore the sentiment.

| Report text | Wrong reading | Correct extraction |
|---|---|---|
| "No messaging or streaming infrastructure exists. The AnyCompany.Billing.Gateway calls AnyCompany.Settlement.Worker via synchronous HTTP." | No dependency | `sync` edge, `AnyCompany.Billing.Gateway` → `AnyCompany.Settlement.Worker`, protocol HTTP |
| "No async messaging, no event-driven patterns. All cross-service communication is synchronous — RPC calls via XMLHttpRequest, SOAP web service calls to internal endpoints." | No dependency | `sync` edges to internal SOAP endpoints, protocols `XMLHttpRequest`, `SOAP` |
| "The WCF WSDL references MSMQ bindings but this is a reference file only — no active messaging implementation exists." | `async` MSMQ edge | **No edge.** The prose explicitly negates the implementation. Record as an unresolved signal with reason `mechanism_unclear`. |
| "All data access goes through a shared DAL layer connected to the same `AnyCompanyLedgerDb` SQL Server database and multi-tenant Oracle databases." | Internal detail | `shared_db` edges to resource nodes `AnyCompanyLedgerDb` (SQL Server) and the named Oracle stores |
| "Calls 3 external SOAP endpoints (CustomerService, InquiryService, AccountService) on the same vendor platform." | 3 internal services | 3 `sync` edges to **external** nodes, grouped under the named vendor platform |

The third row is the important discipline: an explicit negation ("reference file only", "not
implemented", "no active", "commented out", "legacy, unused") suppresses the edge. Scan for negation
in the same sentence before emitting.

---

## 3. Pattern Seeds

### 3.1 Named service peers

.NET and Java estates name deployable units predictably.

```
\b([A-Z][A-Za-z0-9]*(?:\.[A-Z][A-Za-z0-9]*)*\.(?:API|WebAPI|Web|Svc|Service|Services|Host|Worker))\b
\b([A-Z][A-Za-z0-9]{2,}(?:Service|Svc|API|WebAPI|Processor|Importer|Exporter|Gateway|Scheduler))\b
```

Discard matches that are: the reporting repo's own alias; a framework or library type
(`HttpClient`, `IHostedService`, `BackgroundService`, `HttpHandlerService` unless it resolves to an
inventory entry); or a .NET namespace root (`System.*`, `Microsoft.*`, `Newtonsoft.*`, `AWSSDK.*`).

**Also discard bare role words.** A candidate name must identify a *particular* service, not a
category of service. Reject a match whose stripped key (SKILL.md 2.2) is empty, or whose whole name
is one of:

```
API  WebAPI  Web  Service  Services  Svc  WebService  WebServices  Worker  WorkerService
Host  App  Application  Gateway  Scheduler  Processor  Importer  Exporter  Client  Server
BackgroundService  HostedService  WindowsService  UseWindowsService  AddHostedService
```

Reject specification and format names too — these describe an interface *style*, not a service:

```
OpenAPI  Swagger  OData  GraphQL  JSONAPI  RestAPI  SoapAPI  WebApiConfig  MinimalAPI
```

These appear constantly in MOD prose as common nouns ("the WebAPI exposes…", "registered as a
WorkerService") and as framework API calls. Treated as service names they generate enormous volumes
of unresolvable noise that buries the real gaps: on a portfolio of roughly a hundred repositories, the bare word `WebAPI`
alone accounted for over two hundred spurious candidate signals — an order of magnitude more
than any genuine unresolved service.

A name composed only of a derived organization prefix plus a role word (`AnyCompanyServices`, `AnyCompanyApi`)
is likewise a category, not a service. Require at least one distinguishing token beyond prefix and
role suffix.

### 3.2 UNC file shares and network paths

```
\\\\[A-Za-z0-9_.\-]+\\[^\s,;:)"'`\]]+
```

Normalize to `\\{host}\{share}`, **lowercased** — drop deeper path segments, since
`\\anycompany-fs1\Data\Incoming\` and `\\anycompany-fs1\Data\Archive\` are one shared resource, not
two. The host and share together are the resource node; subdirectories are not.

Lowercasing is required, not cosmetic: SMB paths are case-insensitive and different reports spell the
same share differently (`\\anycompany-fs1\Data` and `\\anycompany-fs1\data`). Without normalization one
share splits into two clusters, each with a fraction of its true membership — which understates the
coordination risk of what is often the most widely shared resource in a legacy estate. Preserve the
original casing for display, but cluster on the lowercased key.

### 3.3 Database catalogs and instances

```
(?:Initial\s+Catalog|Database|Data\s+Source|Server)\s*=\s*([A-Za-z0-9_.\-\\]+)
\b(?:database|catalog|schema)\s+(?:named\s+)?[`"']?([A-Za-z][A-Za-z0-9_]{2,})[`"']?
\b([A-Za-z][A-Za-z0-9_]{2,})\s+(?:SQL\s+Server|Oracle|PostgreSQL)\s+database\b
\blinked\s+server\s+[`"']?([A-Za-z0-9_.\-\\]+)[`"']?
```

Reject generic words that the second pattern will otherwise capture:

- **Determiners and descriptors:** `the`, `this`, `that`, `same`, `main`, `production`, `primary`,
  `secondary`, `shared`, `multi`, `tenant`, `legacy`, `central`, `common`, `local`, `remote`.
- **Quantity words:** `multiple`, `several`, `various`, `many`, `numerous`, `both`, `each`, `all`,
  `two`, `three`, `four`, `five`, `six`, `seven`, `eight`, `nine`, `ten`, `dozens`, `20+`.

The quantity words matter specifically because MOD prose is full of counts — "read and write
operations across 20+ SQL Server databases", "three Oracle databases" — and a naive capitalized-word
capture turns `Multiple` and `Three` into database *names*. A phrase stating a count of databases
without naming them is a **coverage gap**, not a resource node: record it as an unresolved signal with
reason `no_alias_match` so it appears in closable gaps, where the customer can supply the real names.

Require a catalog name to appear in at least one repo as a capitalized or mixed-case identifier, and
to contain at least one character that is not a lowercase dictionary word, before accepting it as a
resource node.

### 3.4 Queues, topics, and buses

```
\b(MSMQ|SQS|SNS|EventBridge|Kafka|RabbitMQ|Service\s*Bus|ActiveMQ|Kinesis)\b
\b(?:queue|topic|exchange)\s+(?:named\s+)?[`"']?([A-Za-z0-9_.$\\\-]+)[`"']?
```

### 3.5 SOAP and WCF endpoints

```
https?://[A-Za-z0-9.\-]+(?::\d+)?/[A-Za-z0-9._/\-]*(?:webservice|webservices|svc|asmx|wsdl)[A-Za-z0-9._/\-]*
\b([A-Za-z0-9_.\-]+\.(?:asmx|svc|wsdl))\b
```

A SOAP namespace URI (`http://vendor-platform.example.com/webservices/`) identifies the *owning system* even
when no code calls it. Resolve the host against the alias registry and `external_systems`; if it
resolves to neither, it is an `external` node named by its host.

### 3.6 COM+ and in-process components

```
\bCOM\+\b[^.]{0,80}?\b([A-Z][A-Za-z0-9]*\.[A-Za-z][A-Za-z0-9]*)\b
\b([A-Z][A-Za-z0-9]*\.[A-Za-z][A-Za-z0-9]*)\b[^.]{0,40}?\bCOM\+
```

COM+ components registered on a shared host are a `shared_infra` dependency, and a component
invoked across application boundaries is `sync`. Classic-ASP estates also share framework includes
(for example a common `inc_framework.asp`); a named shared include used by multiple repos is a
`shared_infra` resource.

### 3.7 Identity, scheduling, logging, and discovery

```
\b(OAuth2?|OIDC|SAML|LDAP|Active\s*Directory|Cognito|ADFS|Kerberos|Windows\s+Authentication)\b
\b(Hangfire|Quartz|SQL\s+Server\s+Agent|Control-M|Autosys|Task\s+Scheduler|cron)\b
\b(Eureka|Consul|Zookeeper|service\s+registry)\b
\b(NLog|log4net|Serilog|Splunk|ELK|Elasticsearch)\b
```

#### A bare technology name is NEVER a resource node

This is the single most important rule in this catalogue, because violating it silently destroys the
analysis.

`OIDC`, `SAML`, `OAuth2`, `LDAP`, `NLog`, `log4net`, `Quartz`, `Hangfire`, `Kerberos` are
**protocols, libraries, and standards** — categories of technology, not identifiable shared
facilities. A resource node requires a **named instance**: a specific identity provider, a specific
scheduler host, a specific log sink.

| Report text | Resource node? |
|---|---|
| "No modern identity integration (OAuth2/OIDC/SAML), no external IdP federation." | **No.** This is a *gap* statement — it says the technology is absent. |
| "Add OpenTelemetry SDK with X-Ray exporter." | **No.** A recommendation describing a system that does not exist. |
| "Authenticates against the corporate Active Directory domain `ANYCOMPANY`." | **Yes** — `shared_infra`, named `ANYCOMPANY`. |
| "Logs are written to the shared CentralLogging service." | **Yes** — resolve the named service against the inventory; it is likely an `internal` node, not a resource. |
| "Jobs are scheduled by the shared Quartz cluster on `ANYCO-BATCH1`." | **Yes** — `shared_infra`, named `ANYCO-BATCH1`. |

Require **both** of the following before creating a `shared_infra` resource node from §3.7:

1. A **specific name** — a host, domain, instance, cluster, tenant, or service identifier. Not just
   the technology, and **not a common noun following an instance keyword.** Patterns that look for
   `server <NAME>` or `host <NAME>` will otherwise capture ordinary prose like "server urls are
   hardcoded" or "server addresses in config" as resources named `urls` and `addresses`. Reject
   captures matching: `url`, `urls`, `address`, `addresses`, `name`, `names`, `path`, `paths`,
   `endpoint`, `endpoints`, `setting`, `settings`, `string`, `strings`, `value`, `values`, `config`,
   `credential`, `credentials`, `connection`, `connections`, `instance`, `instances`, `cluster`,
   `details`, `info`, `information`.
2. **Evidence of sharing** — the prose indicates the facility is used across applications, or a
   dedicated repo for it exists in the inventory. A repository whose own purpose is SSO, logging, or
   service registry makes the dependency concrete and **internal**: prefer resolving to that
   inventory entry over inventing a resource node.

Why this matters quantitatively: on a portfolio of roughly a hundred repositories, treating bare protocol names as resources
produced clusters spanning roughly three-quarters of the portfolio for `oidc`, `saml`, and `oauth2` —
because that many reports *recommended adopting them*. Those three alone generated tens of thousands
of derived service pairs from zero real dependencies, outnumbering the genuine edges by more than two
orders of magnitude. A graph in that
state is worse than an empty one, because it looks substantive.

Apply the same test to database and file-share detection: a named catalog (`AnyCompanyLedgerDb`) is a
resource; the words "SQL Server" are not.

---

## 4. External System Classification

A candidate name that does not resolve to an inventory entry may still be a real dependency on a
third-party or out-of-scope system. Classify it as an `external` node when any of the following
holds:

| Rule | Confidence | Notes |
|---|---|---|
| The name appears in `external_systems` from `additionalPlanContext` | `high` | Customer-asserted. The primary mechanism. |
| The prose explicitly marks it external ("external", "third-party", "vendor", "SaaS", "hosted by", "partner") | `high` | The report is telling you directly. |
| The name matches a technology-platform term from §4.1 | `medium` | Infrastructure, not an application. |
| The name is the host of a URL or SOAP namespace whose domain is not a portfolio service | `medium` | Record the host as the node name. |
| A proper-noun product or company name sits adjacent to an integration verb ("calls", "integrates with", "sends to", "receives from") | `low` | Report as external, but list it under closable gaps so the customer confirms. |

**Vendor names are deliberately not enumerated in this TD.** Every industry has its own, they change,
and a baked-in list would be both incomplete and stale while giving a false impression of coverage.
The `external_systems` context field is the supported mechanism — seed it per engagement, ideally
from the customer's own application inventory or integration catalogue. Step 7.3 emits the specific
`external_systems` entries that would resolve the remaining unknowns, so the list builds itself
across runs.

### 4.1 Technology-platform terms

These are generic, cross-industry infrastructure and middleware names. Matching one indicates the
candidate is a *platform or facility*, not an application, and should become an `external` or
`resource` node rather than an unresolved service:

**Hosting and application servers:** IIS, Windows Server, Tomcat, WebLogic, WebSphere, JBoss, Nginx,
Apache, Kestrel.

**Directory and identity:** Active Directory, LDAP, ADFS, Kerberos, Okta, Auth0, Ping, Cognito.

**Integration middleware and ETL:** BizTalk, MuleSoft, Informatica, Boomi, TIBCO, WebMethods, SSIS,
Talend, OLEDB, ODBC, JDBC.

**Reporting and documents:** SQL Server Reporting Services, SSRS, Crystal Reports, Power BI,
Tableau, SharePoint.

**Developer and delivery platforms:** Azure DevOps, GitHub, GitLab, Bitbucket, Jenkins, TeamCity,
Octopus Deploy, Artifactory, Nexus.

**Observability:** Splunk, Elasticsearch, ELK, Datadog, New Relic, AppDynamics, Dynatrace, Grafana.

Match case-insensitively on substring, against the candidate name **and** its surrounding clause.
Where a clause names a platform and several endpoints on it, record the platform in the node's
`platform` field so those endpoints group together rather than appearing as unrelated external
systems.

---

## 5. Signal Quality Rubric

Assign each signal a quality before it becomes an edge. Quality caps the resulting edge's
confidence.

| Quality | Criteria | Edge confidence cap |
|---|---|---|
| Strong | Prose names both endpoints and the mechanism, in one sentence, with no negation | `high` |
| Moderate | Prose names one endpoint plus the mechanism; the other endpoint is the reporting repo | `medium` |
| Weak | Mechanism is named but the peer is generic ("internal endpoints", "downstream services", "other services") | `low`, **and** only if a resource or external node can be named; otherwise unresolved |
| Rejected | Negated, hypothetical ("would require", "should introduce", "if adopted"), or purely a recommendation | no edge |

The **Rejected** row deserves care: MOD `recommendation` fields are full of prospective
architecture ("Introduce SQS or EventBridge for cross-service state change communication"). That
sentence describes a system that does not exist. Mine `recommendation` only for peer *names* that
corroborate an edge already established by `description` or `gap` — never as the sole basis for one.
