# Report accuracy scores

> **GENERATED FILE — do not edit.** Regenerate with:
> `harness/score-reports.py --show-baseline --markdown harness/SCORES.md`
> (or add `--markdown` to any `--update-baseline` run).

Source: [`harness/golden-accuracy-baseline.json`](golden-accuracy-baseline.json)

Each score is an LLM grader's assessment of how well a generated report is **grounded in the fixture's actual source code** — fabrications and misses count against it. This is the *accuracy* axis, and it is what the judge compares a TD change against. It is NOT the ARA tier or the MOD band, which are the report's own verdicts about the app and appear here as context.

**Sample depth: 1 run per fixture (single draw).** There is no measured variance yet, so the judge falls back to the observed noise floor — **ARA 0.10**, **MOD 0.02** per fixture. Because the entire observed ARA range is about 0.10 wide, ARA scores here **cannot be used to rank fixtures against each other**; only the deterministic defects below are safe to act on at this depth.

## ARA — 11 reports

Mean **0.76**, range 0.72–0.82.

| Score | Repo | Checks | Tier / blockers |
|---|---|---|---|
| 0.72 | `legacy-document-portal` | **1 FAIL** | Not Agent-Integrable / 3 |
| 0.72 | `legacy-helpdesk-tickets` | **1 FAIL** | Not Agent-Integrable / 3 |
| 0.72 | `legacy-loan-calculator` | PASS | Not Agent-Integrable / 3 |
| 0.72 | `legacy-partner-soap` | **1 FAIL** | Not Agent-Integrable / 3 |
| 0.72 | `legacy-shipping-api` | **1 FAIL** | Remediation Required / 1 |
| 0.72 | `legacy-timesheet-webforms` | **1 FAIL** | Not Agent-Integrable / 3 |
| 0.78 | `legacy-crm-desktop` | PASS | Not Agent-Integrable / 3 |
| 0.78 | `legacy-payroll-system` | PASS | Remediation Required / 2 |
| 0.82 | `legacy-pricing-cgi` | PASS | Remediation Required / 2 |
| 0.82 | `legacy-storefront-rails` | PASS | Not Agent-Integrable / 3 |
| 0.82 | `monolith` | PASS | Remediation Required / 1 |

## MOD — 11 reports

Mean **0.90**, range 0.85–0.92.

| Score | Repo | Checks | MOD score / band |
|---|---|---|---|
| 0.85 | `monolith` | PASS | 1.89 / Needs Work |
| 0.88 | `legacy-partner-soap` | PASS | 1.09 / Not Ready |
| 0.88 | `legacy-pricing-cgi` | PASS | 2.0 / Needs Work |
| 0.88 | `legacy-shipping-api` | PASS | 1.77 / Needs Work |
| 0.92 | `legacy-crm-desktop` | PASS | 1.15 / Not Ready |
| 0.92 | `legacy-document-portal` | PASS | 1.18 / Not Ready |
| 0.92 | `legacy-helpdesk-tickets` | PASS | 1.15 / Not Ready |
| 0.92 | `legacy-loan-calculator` | PASS | 1.15 / Not Ready |
| 0.92 | `legacy-payroll-system` | PASS | 1.0 / Not Ready |
| 0.92 | `legacy-storefront-rails` | PASS | 1.18 / Not Ready |
| 0.92 | `legacy-timesheet-webforms` | PASS | 1.09 / Not Ready |

## Deterministic defects — 5 across 5 reports

Arithmetic contradictions inside a single report — **actionable now**, independent of sample depth.

| Severity | Repo | Check | Detail |
|---|---|---|---|
| high | `legacy-document-portal` (ARA) | severity_counter_undercount | risk_safety_count=8 but 9 findings are natively RISK-SAFETY (undercount by 1; no exclusion rule can lower a counter below the enumerated findings) |
| medium | `legacy-helpdesk-tickets` (ARA) | severity_counter_undercount | risk_quality_count=8 but 10 findings are natively RISK-QUALITY (undercount by 2; no exclusion rule can lower a counter below the enumerated findings) |
| medium | `legacy-partner-soap` (ARA) | severity_counter_undercount | risk_quality_count=9 but 11 findings are natively RISK-QUALITY (undercount by 2; no exclusion rule can lower a counter below the enumerated findings) |
| medium | `legacy-shipping-api` (ARA) | severity_counter_undercount | risk_quality_count=8 but 9 findings are natively RISK-QUALITY (undercount by 1; no exclusion rule can lower a counter below the enumerated findings) |
| medium | `legacy-timesheet-webforms` (ARA) | severity_counter_undercount | risk_quality_count=6 but 10 findings are natively RISK-QUALITY (undercount by 4; no exclusion rule can lower a counter below the enumerated findings) |

## Per-report grader notes

<details><summary>Fabrications and misses per report (21 reports)</summary>

### `legacy-crm-desktop` (ARA) — 0.78

The report accurately identifies the critical issues in this legacy VB6 desktop application: no API surface, hardcoded credentials, SQL injection vulnerability, and lack of authentication. The service archetype (stateful-crud) and tier (Not Agent-Integrable) are correctly determined. However, the report contains some severity inconsistencies and the BLOCKER count (3) doesn't match the findings marked as BLOCKER (API-Q1, AUTH-Q1, AUTH-Q5), while several RISK-SAFETY findings could arguably be BLOCKERs given the system's actual write capabilities.

- **MISS** [High] README.md line 12: File share corruption vulnerability explicitly documented
- **MISS** [Medium] README.md line 13: No multi-user locking - explicit concurrency problem

### `legacy-crm-desktop` (MOD) — 0.92

The report is highly accurate and well-grounded in the actual repository source. All findings correctly identify real issues visible in the code (hardcoded credentials, SQL injection risk, VB6 desktop app, Access database, no IaC/CI/CD). The service archetype (stateful-crud), pathway triggers, and severity assessments are all justified by the evidence. Minor issues include the Move to Containers pathway being somewhat conceptually awkward for a VB6 app that cannot actually be containerized.

- **MISS** [High] frmCustomer.frm: SQL injection vulnerability in cmdSave_Click

### `legacy-document-portal` (ARA) — 0.72

The report accurately identifies the legacy ColdFusion application's severe limitations for agentic integration, correctly flagging SQL injection, lack of API surface, and missing machine authentication as blockers. However, there is a severity counter undercount (8 reported vs 9 actual RISK-SAFETY findings), and the archetype classification as 'data-gateway' is debatable given this is more of a document portal application. The evidence citations are generally accurate and tied to specific files.

- **FABRICATION** API-Q1: While no write endpoints are shown in the provided .cfm files, the README mentions 'Uploaded files written to local disk' indicating upload functionality exists somewhere (likely a missing upload.cfm), making 'read-only' characterization incomplete. However, this is minor as the visible codebase supports the classification.
- **MISS** [BLOCKER] download.cfm lines 6-8: Path traversal vulnerability in download.cfm - filename from DB used directly in file path without sanitization
- **MISS** [RISK-SAFETY] README.md Known Issues: Session fixation vulnerability - no token rotation on login
- **MISS** [RISK-SAFETY] README.md Known Issues: No HTTPS - runs HTTP only
- **MISS** [RISK-SAFETY] README.md: EOL software with critical CVEs (ColdFusion 8, SQL Server 2005, Windows Server 2008)

### `legacy-document-portal` (MOD) — 0.92

The report is highly accurate and well-grounded in the repository source. It correctly identifies the ColdFusion 8 application, SQL Server 2005 database, local file storage, SQL injection vulnerabilities, plaintext credentials, and lack of any modern infrastructure. The pathways are appropriately triggered based on actual evidence, and the service archetype (stateful-crud) is correct. Minor issues include some findings citing evidence='null' when the absence of files is itself the evidence.

- **MISS** [High] index.cfm line with 'WHERE title LIKE '%#url.q#%': SQL injection vulnerability in index.cfm via string concatenation
- **MISS** [High] download.cfm - filename from DB used directly in filepath without sanitization: Path traversal vulnerability in download.cfm

### `legacy-helpdesk-tickets` (ARA) — 0.72

The report correctly identifies the major issues in this legacy Django application including SQL injection vulnerabilities, hardcoded credentials, lack of API, and EOL software stack. However, it undercounts RISK-QUALITY findings (reports 8 but lists 10), and several INFO-level findings mentioned in evaluations are not actually present in the findings array, creating question coverage gaps. The archetype detection and tier classification are appropriate given the blockers identified.

- **MISS** [BLOCKER] tickets/views.py lines 11-14 and 23-25: SQL injection vulnerability should be flagged as a BLOCKER or at minimum RISK-SAFETY, not just RISK-QUALITY under DATA-Q4

### `legacy-helpdesk-tickets` (MOD) — 0.92

The report is highly accurate and well-grounded in the repository source. It correctly identifies the critical issues (SQL injection, hardcoded credentials, EOL software), properly classifies the service archetype as stateful-crud, and triggers the appropriate modernization pathways. The evidence citations consistently match what exists in the source files, though it misses explicitly calling out the SQL injection vulnerabilities as BLOCKER/High severity findings in their own right.

- **MISS** [BLOCKER] tickets/views.py: SQL injection vulnerabilities in ticket_list() and ticket_search() using raw string formatting with user input
- **MISS** [High] tickets/views.py: XSS vulnerability in ticket_search() - user-controlled data rendered directly into HTML without escaping
- **MISS** [High] helpdesk/settings.py: DEBUG = True in production explicitly documented and visible in settings.py

### `legacy-loan-calculator` (ARA) — 0.72

The report correctly identifies the repository as a legacy Struts 1.3 application with critical issues like hardcoded credentials, SQL injection, and no API surface. The tier classification (Not Agent-Integrable) is consistent with the 3 BLOCKERs identified. However, the report significantly undersells the SQL injection vulnerability (marking it RISK-QUALITY/Medium when it's a critical security flaw), and the read-only agent scope assumption is questionable given the application clearly performs write operations.

- **FABRICATION** AUTH-Q5: The evidence mentions 'also duplicated in db.properties' in the code comment, but no db.properties file exists in the repository. The report correctly identifies the hardcoded credentials in LoanAction.java, but the code comment reference to a non-existent file is misleading context.
- **MISS** [BLOCKER] src/com/acme/loan/LoanAction.java lines 47-50: SQL Injection vulnerability severely underweighted - applicant name concatenated directly into SQL string
- **MISS** [RISK-SAFETY] README.md: Thread-safety bugs explicitly documented in README - ActionForms hold mutable shared state
- **MISS** [Medium] src/com/acme/loan/LoanAction.java lines 46-53: No connection pooling - creates new JDBC connection per request without closing properly

### `legacy-loan-calculator` (MOD) — 0.92

The report is highly accurate and well-grounded in the repository source. It correctly identifies the critical issues (hardcoded credentials, SQL injection vulnerability, EOL technologies, no IaC/CI/CD) and appropriately triggers pathways based on actual evidence. The service archetype (stateful-crud) and repository classification (application) are correct. Minor issues include one speculative finding about unstructured data storage and the SQL injection vulnerability being mentioned but not elevated to a dedicated High-severity finding.

- **FABRICATION** DATA-Q1: This is speculation - the source code shows no evidence of document handling, file storage, or BLOB columns. The application only stores loan application data (applicant, principal, rate, term, officer) via a simple INSERT statement. There's no indication documents are part of this system.
- **MISS** [BLOCKER] src/com/acme/loan/LoanAction.java: SQL Injection vulnerability - applicant name directly concatenated into SQL string without parameterization

### `legacy-partner-soap` (ARA) — 0.72

The report correctly identifies the service archetype, major security vulnerabilities (SQL injection, XXE, hardcoded credentials), and appropriately classifies this as 'Not Agent-Integrable' due to multiple BLOCKERs. However, there is a severity counter undercount (risk_quality_count=9 but 11 RISK-QUALITY findings exist), some questionable severity classifications (SQL injection/XXE as RISK-QUALITY rather than BLOCKER/RISK-SAFETY), and the agent_scope='read-only' determination is inconsistent with a service that only has write operations.

- **MISS** [BLOCKER] src/com/acme/partner/PurchaseOrderService.java lines 33-36: SQL injection vulnerability should be a BLOCKER or at minimum RISK-SAFETY, not RISK-QUALITY
- **MISS** [BLOCKER] src/com/acme/partner/PurchaseOrderService.java lines 28-30: XXE vulnerability should be BLOCKER or RISK-SAFETY, not implicitly folded into DATA-Q4 as RISK-QUALITY
- **MISS** [RISK-SAFETY] README.md line 8: WS-Security PasswordText over plain HTTP is a critical security issue not explicitly called out

### `legacy-partner-soap` (MOD) — 0.88

The report is largely accurate and well-grounded in the repository source. It correctly identifies critical security issues (hardcoded credentials, XXE vulnerability, SQL injection), infrastructure gaps (no IaC, no CI/CD, EOL runtime), and appropriately triggers pathways. However, it misses explicitly calling out the SQL injection vulnerability as a High-severity finding despite mentioning it in passing, and the XXE vulnerability is only mentioned in SEC-Q7 description rather than as its own finding.

- **MISS** [BLOCKER] src/com/acme/partner/PurchaseOrderService.java lines 38-39: SQL Injection vulnerability - direct string concatenation of user input into SQL query
- **MISS** [High] src/com/acme/partner/PurchaseOrderService.java lines 30-32: XXE (XML External Entity) vulnerability - DocumentBuilderFactory with no security features enabled

### `legacy-payroll-system` (ARA) — 0.78

The report accurately identifies the core problems with this legacy COBOL payroll system: no API surface, hardcoded plaintext FTP credentials, no authentication/authorization model, and plaintext transmission of PII. Evidence citations are grounded in the actual source files. However, there are minor issues with question coverage (42 total instead of 43) and some findings could be more precisely scoped to what the source actually shows versus architectural assumptions.

- **FABRICATION** AUTH-Q1: While technically correct that these don't exist, the report implies the system should have these. The source shows this is a mainframe batch system with no HTTP surface - these technologies are not applicable to the architecture. The finding is valid but overstates the gap by framing it against modern API patterns.
- **MISS** [High] src/PAYRUN.cbl line 35: Outdated FICA wage base hardcoded as 132900.00 (2019 value) - payroll calculations are using stale tax parameters
- **MISS** [Medium] src/PAYRUN.cbl line 44: State tax calculation explicitly removed ('STATE TAX TABLE LOOKUP REMOVED IN 2011, DONE MANUALLY')

### `legacy-pricing-cgi` (ARA) — 0.82

The report is largely accurate about this legacy C++ CGI pricing application. It correctly identifies the lack of structured API (HTML-only output), absence of authentication, buffer overflow risks in pricing.cpp, and missing observability. The archetype (stateless-utility) and repo_type (application) are correct. However, the report inflates some findings by treating AUTH-Q1 as a BLOCKER when the service has no authentication surface by design for a read-only pricing lookup, and some INFO findings referenced in evaluations are not actually emitted in the findings array.

- **FABRICATION** API-Q5: The evaluation says 'Finding emitted' but API-Q5 does not appear in the findings array. The status is 'pass' but no corresponding INFO finding exists.
- **FABRICATION** API-Q8: The evaluation says 'Finding emitted' but API-Q8 does not appear in the findings array despite claiming a finding was emitted.
- **FABRICATION** AUTH-Q4: AUTH-Q4 does not appear in the findings array despite the evaluation claiming a finding was emitted.
- **FABRICATION** AUTH-Q6: AUTH-Q6 does not appear in the findings array despite claiming emission.
- **FABRICATION** AUTH-Q7: AUTH-Q7 does not appear in the findings array despite claiming emission.

### `legacy-pricing-cgi` (MOD) — 0.88

The report is largely accurate and well-grounded in the repository source. It correctly identifies the service archetype as stateless-utility, accurately detects the containerized state with Dockerfile and k8s manifests, and appropriately triggers only the Modern DevOps pathway while correctly NOT triggering Move to Containers (already containerized) or Move to Managed Databases (no database). Most findings cite real files and patterns. Minor issues include not explicitly flagging the buffer overflow and XSS vulnerabilities as High-severity security findings.

- **MISS** [High] pricing.cpp lines 14-21: Buffer overflow vulnerabilities via strcpy without bounds checking
- **MISS** [High] pricing.cpp line 50 (printf with sku): Reflected XSS vulnerability - user input printed without escaping

### `legacy-shipping-api` (ARA) — 0.72

The report is largely accurate about the repository's structure and issues, correctly identifying the hardcoded credentials, lack of authentication sophistication, missing observability, and absence of input validation. However, it has a severity counter undercount (reports 8 RISK-QUALITY but lists 9 such findings), and the service archetype classification as 'data-gateway' is questionable given the POST /quote endpoint performs business logic computation. The report correctly identifies most real issues in the source code with proper file/line citations.

- **FABRICATION** API-Q4: While technically true that /quote has no database writes, the evaluation status 'pass' is misleading - the question about idempotent write operations should note that POST /quote returns different results for identical inputs if the magic numbers change, and the archetype classification affects this assessment
- **MISS** [High] server.js lines 26-27: NoSQL injection vulnerability - unvalidated query params passed directly to MongoDB filter
- **MISS** [Medium] server.js lines 22-34: MongoDB connection not reused - new connection per request causes resource exhaustion

### `legacy-shipping-api` (MOD) — 0.88

The report is largely accurate and well-grounded in the repository source. It correctly identifies the critical issues (hardcoded credentials, EOL MongoDB 2.4, no CI/CD, self-managed database) and appropriately triggers Move to Managed Databases and Move to Modern DevOps pathways while correctly NOT triggering Move to Containers (since Dockerfile/K8s manifests exist). The service archetype as data-gateway is reasonable. Minor issues include some evidence citations that could be more precise and one potentially inflated finding.

- **FABRICATION** DATA-Q1: While technically true there's no S3, the application is a simple rate lookup API. The source shows MongoDB stores rate data appropriately for this use case. Framing absence of S3 as a High-severity gap for a data-gateway service is arguably inflated - the repo doesn't indicate any need for object storage.

### `legacy-storefront-rails` (ARA) — 0.82

The report is largely accurate about this legacy Rails repository, correctly identifying critical security issues like SQL injection, mass assignment vulnerabilities, and hardcoded credentials. The tier classification of 'Not Agent-Integrable' with 3 BLOCKERs is appropriate. However, some findings slightly overstate issues (e.g., claiming 'no documented API' when routes do exist), and the count arithmetic shows inconsistencies (29 total findings but 3+26+9=38 by severity).

- **FABRICATION** OBS-Q1: While accurate that no tracing exists, the evidence field is null despite the README.md explicitly mentioning the architecture and logging patterns. The claim is true but lacks specific file evidence.
- **MISS** [BLOCKER] app/controllers/orders_controller.rb lines 9-11: SQL injection vulnerability in index action with direct string interpolation
- **MISS** [RISK-SAFETY] README.md line 17: Session secret stored in source control

### `legacy-storefront-rails` (MOD) — 0.92

The report is highly accurate and well-grounded in the repository source. It correctly identifies the critical issues (plaintext credentials, EOL components, SQL injection risk, no IaC/CI-CD), accurately classifies the service archetype as stateful-crud, and appropriately triggers pathways for containers, managed databases, cloud-native, and modern DevOps. The findings cite actual files and patterns present in the source. Minor weaknesses include not explicitly calling out the SQL injection vulnerability as a distinct High-severity security finding.

- **MISS** [High] app/controllers/orders_controller.rb: SQL injection vulnerability via string interpolation in find_by_sql
- **MISS** [High] app/controllers/orders_controller.rb and README.md: Mass assignment vulnerability explicitly documented

### `legacy-timesheet-webforms` (ARA) — 0.72

The report accurately identifies the repository as a legacy ASP.NET WebForms application with critical security issues (SQL injection, plaintext credentials, no API surface). However, there is a counter undercount issue where risk_quality_count=6 but 10 findings are marked as RISK-QUALITY. The service archetype detection and most findings are well-grounded in the source code, with specific file/line citations. The tier classification of 'Not Agent-Integrable' is consistent with the 3 BLOCKERs identified.

- **MISS** [BLOCKER] Timesheet.aspx.vb lines 20-23 and 34-39: SQL Injection vulnerability severity should be higher
- **MISS** [RISK-SAFETY] web.config line 10-11 (requireSSL='false'): Forms authentication cookie sent without SSL is a significant security issue

### `legacy-timesheet-webforms` (MOD) — 0.92

The report is highly accurate and well-grounded in the repository source. All findings correctly identify real issues present in the code (SQL injection, plaintext credentials, EOL software, no IaC/CI-CD). The pathways are appropriately triggered based on actual evidence, and the stateful-crud archetype is correctly identified. Minor issues include one questionable High severity finding (DATA-Q1 for unstructured storage) and some findings that could have cited specific line numbers.

- **FABRICATION** DATA-Q1: The application is a timesheet entry system with no evidence it needs unstructured data storage. The README and code show only structured relational data (timesheets table). Marking absence of S3 as a High/P1 gap is arguably fabricating a requirement not supported by the source.

### `monolith` (ARA) — 0.82

The report is largely accurate and well-grounded in the actual source code. Key findings about session-based auth (AUTH-Q1), hardcoded credential fallbacks (AUTH-Q5), lack of rate limiting (STATE-Q5), and absence of OpenAPI specs (API-Q2) are all verifiable in index.php and the CloudFormation template. However, there are minor inaccuracies in line number citations and one questionable severity assessment for the archetype classification.

- **FABRICATION** AUTH-Q1: The session check for API calls is at line ~203-207 (checking $_SESSION['user']), but the cited lines are approximately correct. The claim itself is accurate - the code does use session-based auth exclusively for API endpoints.

### `monolith` (MOD) — 0.85

The report is largely accurate and well-grounded in the actual repository source. It correctly identifies the monolithic PHP architecture, hardcoded credentials, lack of CI/CD, session-based auth, and containerized deployment. Pathway triggers are mostly appropriate - Move to Cloud Native and Move to Modern DevOps are correctly triggered while Move to Containers is correctly not triggered since Dockerfile exists. Minor issues include some line number imprecision and the APP-Q2 finding overstates the line count.

- **FABRICATION** APP-Q2: The index.php file is approximately 2000 lines, not 3193. While the monolithic nature is accurate, the line count is inflated.
- **FABRICATION** DATA-Q2: Counting the actual route handlers in index.php shows approximately 20 distinct API endpoints, not 25+. Minor exaggeration but the scattered query pattern observation is accurate.

</details>
