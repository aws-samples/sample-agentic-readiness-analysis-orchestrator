# MOD Report Template

> **Purpose:** Loaded by the Modernization Readiness Analysis (MOD) TD when compiling findings into the markdown report artifact. Defines the report section order, metadata header, overall and category score table, top-5 gaps, pathway summary table, pathway detail subsections, conditional decomposition strategy, detailed findings for all 37 questions, learning materials, and evidence index.

---

## Report Template

The analysis emits a **four-artifact bundle** per the Four-Artifact Output Contract below: `{repo-name}-mod-report.md` (narrative), `{repo-name}-mod-report.json` (canonical JSON), `{repo-name}-mod-report.html` (self-contained HTML), and `{repo-name}-mod-report.metadata.json` (version sidecar). This section specifies the MD structure. The MD MUST contain all sections listed below in the specified order. Every section is required unless explicitly marked as conditional.

### Report Section Order

1. **Metadata Header**
2. **Overall and Category Score Table**
3. **Top 5 Gaps**
4. **Pathway Summary Table** (all 7 pathways)
5. **Pathway Detail Subsections** (triggered pathways only)
6. **Decomposition Strategy** (conditional — only when APP-Q2 < 3)
7. **Detailed Findings for All 37 Questions**
8. **Learning Materials**
9. **Evidence Index**

---

### Section 1: Metadata Header

```markdown
# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | {repo-name} |
| **Date** | {analysis-date} |
| **TD Version** | {version ID of the published TD that produced this report — resolve via `atx custom def get -n modernization-readiness-analysis`} |
| **Repo Type** | {repo_type} |
| **Service Archetype** | {archetype} ({auto-detected or user-provided}) — omit row if repo_type is not `application` |
| **Priority** | {priority or "—" if not provided} |
| **Tags** | {tags as comma-separated list or "—" if not provided} |
| **Context** | {context or "—" if not provided} |
| **Overall Score** | {overall-score} / 4.0 |
```

If `repo_type` was not provided and defaulted to `application`, include a note: "Repo type defaulted to `application` (not specified in analysis context)."

If `repo_type` was provided but unrecognized, include a warning: "Unrecognized repo_type '{value}', defaulted to `application`."

If `service_archetype` was auto-detected, include the one- to two-sentence justification produced in Step 1.5 immediately below the metadata table under the heading `**Archetype Justification**:`.

### Section 2: Overall and Category Score Table

```markdown
## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | {score} / 4.0 | {rating} |
| Application Architecture (APP) | {score} / 4.0 | {rating} |
| Data Platform Modernization (DATA) | {score} / 4.0 | {rating} |
| Security Baseline (SEC) | {score} / 4.0 | {rating} |
| Operations & Observability (OPS) | {score} / 4.0 | {rating} |
| **Overall** | **{score} / 4.0** | **{rating}** |
```

**Rating labels:**

| Score Range | Rating |
|-------------|--------|
| 3.5 – 4.0 | ✅ Mature |
| 2.5 – 3.4 | 🟡 Partial |
| 1.5 – 2.4 | 🟠 Needs Work |
| < 1.5 | ❌ Not Ready |

If a category score is "N/A" (all questions in that category are N/A or Not Evaluated for the detected repo_type and archetype), display:

```markdown
| Application Architecture (APP) | N/A | N/A — all questions not applicable for {repo_type}/{archetype} |
```

**Scoring rules:**
- Category score = arithmetic mean of non-N/A, non-Not-Evaluated question scores in that category.
- Overall score = arithmetic mean of non-N/A category scores (each category weighted equally).
- Both N/A and Not-Evaluated (archetype-N/A) questions are excluded from numerator and denominator.
- If all questions in a category are N/A or Not Evaluated, category score = "N/A", excluded from overall average.

### Section 3: Top 5 Gaps

```markdown
## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | {question-id}: {question-title} | {score} | {one-line gap description} | {impact on modernization} |
| 2 | ... | ... | ... | ... |
| 3 | ... | ... | ... | ... |
| 4 | ... | ... | ... | ... |
| 5 | ... | ... | ... | ... |
```

Select the 5 questions with the lowest scores (excluding N/A). Break ties by prioritizing questions that trigger pathways. If fewer than 5 non-N/A questions have gaps (score < 4), include only those with gaps.

### Section 4: Pathway Summary Table

```markdown
## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | {status} | {priority} | {effort} | {criteria} |
| 2 | Move to Containers | {status} | {priority} | {effort} | {criteria} |
| 3 | Move to Open Source | {status} | {priority} | {effort} | {criteria} |
| 4 | Move to Managed Databases | {status} | {priority} | {effort} | {criteria} |
| 5 | Move to Managed Analytics | {status} | {priority} | {effort} | {criteria} |
| 6 | Move to Modern DevOps | {status} | {priority} | {effort} | {criteria} |
| 7 | Move to AI | {status} | {priority} | {effort} | {criteria} |
```

All 7 pathways MUST appear in this table. Status values: Triggered, Not Triggered, Not Applicable.

### Section 5: Pathway Detail Subsections

For each **Triggered** pathway, include a detail subsection with the content specified in Step 7 ("When Triggered, Include in Pathway Detail Section"). Do not include detail subsections for Not Triggered or Not Applicable pathways.

```markdown
### Pathway: {Pathway Name}

**Status:** Triggered
**Priority:** {High / Medium / Low}
**Estimated Effort:** {High / Medium / Low}

{Pathway-specific detail content as specified in Step 7}
```

### Section 6: Decomposition Strategy (Conditional)

**Include this section ONLY when APP-Q2 < 3.** If APP-Q2 >= 3, omit this section entirely.

```markdown
## Decomposition Strategy

{Content from Step 8 — approach options, pattern recommendations, effort estimation}
```

### Section 7: Detailed Findings for All 37 Questions

```markdown
## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | {1-4 or N/A} |
| **Finding** | {What was discovered — cite specific files and resources} |
| **Gap** | {What's missing or needs improvement, or N/A} |
| **Recommendation** | {Specific action to close the gap, or N/A} |
| **Evidence** | {File paths and resource names cited} |

{Repeat for all 37 questions across all 5 sections}
```

**All 37 questions MUST appear** in this section. N/A questions are listed using the N/A display format:

```markdown
| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `{repo_type}` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |
```

Questions are grouped by section in the same order as the evaluation steps:
1. Infrastructure, Platform, and DevOps (INF-Q1 through INF-Q11)
2. Application Architecture (APP-Q1 through APP-Q6)
3. Data Platform Modernization (DATA-Q1 through DATA-Q4)
4. Security Baseline (SEC-Q1 through SEC-Q7)
5. Operations & Observability (OPS-Q1 through OPS-Q9)

### Section 8: Learning Materials

```markdown
## Learning Materials

Include relevant links based on triggered pathways. Only include learning materials for pathways with status "Triggered."
```

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to Cloud Native** | [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |
| **Move to Containers** | [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM) · [Move to Containers with Amazon ECS](https://skillbuilder.aws/learning-plan/CDA8Y4JRRR) · [EKS Workshop](https://www.eksworkshop.com/) |
| **Move to Open Source** | [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) (covers open source engine migration) |
| **Move to Managed Databases** | [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W) |
| **Move to Managed Analytics** | [Move to Managed Analytics](https://skillbuilder.aws/learning-plan/RWZA84NMVV) |
| **Move to Modern DevOps** | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |
| **Move to AI** | [Move to AI](https://skillbuilder.aws/learning-plan/VDFEE4ACCV) · [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ) · [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD) |

If no pathways are triggered, include: "No pathways triggered — no pathway-specific learning materials applicable. Refer to the [AWS SkillBuilder](https://skillbuilder.aws/) catalog for general cloud architecture training."

### Section 9: Evidence Index

```markdown
## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| {relative/path/to/file} | {Question IDs that cite this file} | {Brief description of what this file evidences} |
| ... | ... | ... |
```

The evidence index compiles all file references cited across the detailed findings into a single lookup table. This enables reviewers to trace any finding back to the specific file that supports it.

Include every file path that appears in any finding's evidence field. Group by directory for readability if the list exceeds 20 entries.


