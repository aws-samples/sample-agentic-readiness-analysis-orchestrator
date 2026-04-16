# ARA — Remaining Tasks

### 1. Portfolio reports
- Rewrite `example-reports/online-boutique/agentic-readiness-assessment/online-boutique-portfolio-ara-report.md` with TD lens (43 questions, archetypes) against original code
- Generate `example-reports/online-boutique/agentic-readiness-assessment-v2/online-boutique-portfolio-ara-report.md` with TD lens + repo changes
- Portfolio TD may need updating to reference 43 questions and archetype data

### 2. Update the dashboard
- `example-reports/online-boutique/agentic-readiness.html` needs updating to reflect new data
- Add delta/comparison view between the two snapshots (before/after repo changes)
- Update question IDs in the JS data
- Add archetype column to service table
- Show "Not Evaluated" count per service

### 3. Publish updated TD to ATX
- Run `atx custom def publish` for the updated `agentic-readiness-assessment` TD

### 4. Run real ATX assessment (optional validation)
- Re-run the full portfolio assessment against the modified microservices-demo repo using ATX
- Compare ATX-generated reports vs simulated reports to validate consistency

### 5. Update POWER.md / orchestrator
- Update the agentic-assessment-orchestrator POWER.md to document:
  - 43 question set
  - Service archetype classification
  - Core/extended evaluation tiers
  - New `service_archetype` field in ATX config generation
- Update portfolio config schema if needed for `service_archetype` per-repo field
