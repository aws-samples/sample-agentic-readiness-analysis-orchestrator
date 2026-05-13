# BPMN Analyzer

Deterministic analysis engine for BPMN 2.0 process models. Parses BPMN XML, extracts structural constraints from the process topology, scores each task for agentic AI suitability, and produces a structured JSON report consumed by the BAO (BPMN Agentic Opportunity) Transformation Definition.

Based on the [BPMN Agentic Analyzer](https://gitlab.aws.dev/jmselmi/bpmn-agentic-analyser) by Jihed Mselmi (Sr. SSA, Containers, EMEA). Constraint extraction approach based on BPMN2Constraints (Bergman, Rebmann, Kampik -- SAP Signavio, BPM 2023).

## What It Does

1. **Parses** BPMN 2.0 XML into a structured process model (tasks, gateways, flows, events, data associations) with version detection (rejects BPMN 1.x with actionable error)
2. **Extracts** 13 types of declarative constraints from the process topology (ordering, exclusion, co-existence, chain succession, etc.) -- fully deterministic, no LLM
3. **Discovers** system dependencies from BPMN elements: service endpoints, data stores, message flows, call activities, and vendor-specific extensions (Camunda C7/C8, jBPM)
4. **Scores** each task on four dimensions: AI benefit (0-1), complexity (0-1), risk (0-1), integration effort (0-1)
5. **Classifies** each task as agent-suitable, service-suitable, or human-required
6. **Estimates** per-task LLM inference cost (tokens, model recommendation, monthly projection)
7. **Outputs** a structured JSON report for downstream consumption

## Usage

```bash
# Analyze a BPMN file, output JSON to stdout
python run_analysis.py --bpmn path/to/process.bpmn

# Save to file
python run_analysis.py --bpmn path/to/process.bpmn --output report.json

# Custom daily volume for cost projection
python run_analysis.py --bpmn path/to/process.bpmn --volume 500 --output report.json
```

## Output Format

```json
{
  "process": {
    "name": "loan_approval",
    "id": "loan_approval",
    "total_elements": 13,
    "total_flows": 14
  },
  "constraints": {
    "total": 37,
    "density": 2.85,
    "ordering": 12,
    "exclusion": 6,
    "coexistence": 8
  },
  "tasks": [
    {
      "element_id": "manual_review",
      "element_name": "Manual Underwriter Review",
      "element_type": "userTask",
      "scores": {
        "ai_benefit": 0.70,
        "complexity": 0.30,
        "risk": 0.35,
        "effort": 0.50,
        "composite": 0.160
      },
      "migration_type": "agent",
      "cost_estimate": {
        "tokens_per_invocation": 1400,
        "recommended_model": "sonnet-4",
        "cost_per_1k_usd": 0.02
      }
    }
  ],
  "summary": {
    "total_tasks": 7,
    "agent_count": 2,
    "service_count": 4,
    "human_count": 1,
    "total_estimated_monthly_cost_usd": 1.20
  },
  "dependencies": {
    "declared": [],
    "inferred": [
      {
        "source_task_id": "ServiceTask_1",
        "source_task_name": "Archive Invoice",
        "target_type": "service_endpoint",
        "target_ref": "org.camunda.bpm.example.invoice.service.ArchiveInvoiceService",
        "confidence": "high",
        "vendor": "camunda-c7",
        "metadata": {"attribute": "camunda:class"}
      }
    ],
    "unknown": [
      {
        "source_task_id": "manual_review",
        "source_task_name": "Manual Underwriter Review",
        "reason": "User task with no system references in BPMN model"
      }
    ]
  }
}
```

## Architecture

```
run_analysis.py          # Entry point: BPMN file -> JSON report
  |
  ├── parser/
  │   └── bpmn_parser.py           # BPMN 2.0 XML -> BPMNProcess dataclass (version detection)
  |
  ├── analyzer/
  │   ├── constraint_extractor.py  # BPMNProcess -> ConstraintProfile (13 constraint types)
  │   ├── dependency_extractor.py  # BPMN elements -> DependencyReport (declared/inferred/unknown)
  │   ├── exceptions.py            # Exception hierarchy (MalformedBPMN, UnsupportedBPMNVersion, etc.)
  │   ├── vendors/                 # Vendor-specific dependency extractors (auto-discovered)
  │   │   ├── __init__.py          # Auto-imports all vendor modules, resilient to load errors
  │   │   ├── camunda_c7.py        # camunda:class, delegateExpression, expression, external tasks
  │   │   ├── camunda_c8.py        # zeebe:taskDefinition job types
  │   │   └── jbpm.py              # drools:packageName (stub, extensible)
  │   ├── process_analyzer.py      # LLM-powered process understanding (optional, not used in dry-run)
  │   ├── pattern_evaluator.py     # Multi-agent pattern scoring (graph/swarm/workflow/agents-as-tools)
  │   └── cross_process_analyzer.py # Cross-process domain matching (multi-file analysis)
  |
  └── augmentor/
      ├── task_evaluator.py        # Task scoring + agent/service/human classification + cost estimation
      └── connector_generator.py   # BPM connector generation (not used in analysis pipeline)
```

## Dependency Extraction

The analyzer discovers system dependencies from BPMN elements and vendor-specific extensions:

**Standard BPMN 2.0** (always runs):
- `serviceTask` with `implementation` or `operationRef` attributes
- `dataStoreReference` elements with data associations
- `messageFlow` elements between participants
- `callActivity` elements referencing external processes
- `userTask` elements with no system references (flagged as "unknown")

**Vendor-specific** (auto-detected by XML namespace):
- **Camunda C7**: `camunda:class`, `camunda:delegateExpression`, `camunda:expression`, external task topics
- **Camunda C8**: `zeebe:taskDefinition` job types
- **jBPM**: `drools:packageName` (stub, extensible for work item handlers)

### Adding a New Vendor Extractor

1. Create a file in `analyzer/vendors/` (e.g., `appian.py`)
2. Subclass `VendorExtractor`, set `NAMESPACES` and `VENDOR_NAME`
3. Implement `extract()` returning a list of `Dependency` objects
4. Call `register_vendor()` at module level

The registry auto-discovers vendor modules at import time. If a vendor module fails to load (syntax error, missing dependency), it's logged and skipped without crashing the pipeline.

## Error Handling

The analyzer uses a custom exception hierarchy for actionable error reporting:

| Exception | When | Example |
|-----------|------|---------|
| `MalformedBPMN` | Invalid XML or no `<process>` element | Corrupted file, non-BPMN XML |
| `UnsupportedBPMNVersion` | BPMN 1.x namespace detected | Legacy process models |
| `VendorExtractorError` | Vendor extractor crashes | Bug in a vendor module |

All exceptions carry structured context (file path, detected version, supported versions) so the orchestrator can surface actionable messages. Vendor extractor failures are isolated: one vendor crashing doesn't affect others or the standard BPMN extraction.

Unsupported vendor namespaces (detected but no extractor registered) produce warnings in the JSON output, not errors. The analysis continues with standard BPMN extraction.

## Key Design Decisions

**Deterministic extraction.** The parser and constraint extractor use no LLM. They read BPMN XML and compute structural facts (ordering, branching, parallelism) directly from the graph topology. This ensures reproducible results with no hallucination risk.

**Scoring model.** Task scoring uses keyword matching, BPMN element types, and structural position (dependency count, gateway context) to compute four dimensions. The composite score weights AI benefit highest (0.40) and penalizes risk (0.30) and effort (0.15).

**Cost estimation.** Token estimates are based on task complexity (simple: 200 input tokens, moderate: 500, complex: 1000) plus system prompt (500) and tool calls (300 per outgoing flow). Model selection follows complexity thresholds. Cost calculation uses published Bedrock pricing.

## Dependencies

- `lxml` -- XML parsing
- `boto3` -- AWS SDK (only needed for full LLM analysis, not dry-run)
- Python 3.10+

Install: `pip install -r requirements.txt`

## Testing

```bash
python -m pytest tests/ -v
```

58 tests covering: parser, constraint extraction, task scoring, dependency extraction, vendor extractors, exception handling, serialization, and full pipeline determinism.

## Contributing

This module is part of the [Agentic Assessment Orchestrator](../../README.md). When modifying:

1. **Do not change the JSON output schema** without updating the BPMN Opportunity Transformation Definition (`../bpmn-opportunity-assessment/transformation_definition.md`) which consumes it
2. **Scoring model changes** should be validated against the AgentStorming worked examples (order fulfillment, KYC, loan origination, insurance claims, demand planning, prior authorization)
3. **New constraint types** should be added to `constraint_extractor.py` with corresponding test cases
4. **New vendor extractors** go in `analyzer/vendors/` -- subclass `VendorExtractor`, set `NAMESPACES`, implement `extract()`, call `register_vendor()`
5. **Run tests** before committing: `python -m pytest tests/ -v` (58 tests, all must pass)

## License

MIT-0 (same as parent repository)
