"""
Process Analyzer — Uses an LLM to understand the business intent
behind a BPMN process and identify domain boundaries for agent design.

When structural constraints are available, they are included in the prompt
so the LLM can ground its analysis in formal process topology facts.
"""
from dataclasses import dataclass, field
from parser.bpmn_parser import BPMNProcess, ElementType


@dataclass
class DomainCluster:
    """A group of related BPMN elements that form a business domain."""
    name: str
    description: str
    elements: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    needs_human: bool = False


@dataclass
class ProcessUnderstanding:
    """The analyzed understanding of a BPMN process."""
    use_case: str
    business_goal: str
    domains: list[DomainCluster] = field(default_factory=list)
    decision_points: list[dict] = field(default_factory=list)
    integration_points: list[dict] = field(default_factory=list)
    human_touchpoints: list[dict] = field(default_factory=list)


def build_analysis_prompt(process: BPMNProcess, constraint_profile=None) -> str:
    """
    Build a prompt that asks the LLM to understand the BPMN process.
    When a constraint profile is provided, structural facts are included
    so the LLM can ground its domain clustering and decision analysis.
    """
    # Summarize elements by type
    elements_summary = []
    for elem in process.elements.values():
        elements_summary.append(
            f"  - [{elem.element_type.value}] {elem.name or elem.id}"
            + (f" (properties: {elem.properties})" if elem.properties else "")
        )

    # Summarize flows with conditions
    flows_summary = []
    for flow in process.flows.values():
        line = f"  - {flow.source_ref} → {flow.target_ref}"
        if flow.name:
            line += f" [{flow.name}]"
        if flow.condition:
            line += f" when: {flow.condition}"
        flows_summary.append(line)

    # Build constraints section if available
    constraints_section = ""
    if constraint_profile and constraint_profile.total_constraints > 0:
        constraint_lines = []
        for c in constraint_profile.constraints:
            if c.target:
                constraint_lines.append(
                    f"  - [{c.constraint_type.value}] {c.source} → {c.target}: {c.description}"
                )
            else:
                constraint_lines.append(
                    f"  - [{c.constraint_type.value}] {c.source}: {c.description}"
                )

        constraints_section = f"""
STRUCTURAL CONSTRAINTS (extracted from BPMN topology — these are facts):
  Total: {constraint_profile.total_constraints} constraints
  Density: {constraint_profile.constraint_density:.2f} constraints/element
  Ordering: {constraint_profile.ordering_constraints} | Exclusion: {constraint_profile.exclusion_constraints} | Co-existence: {constraint_profile.coexistence_constraints}

{chr(10).join(constraint_lines)}

Use these constraints to ground your analysis:
- Succession/precedence constraints reveal the true execution order
- Exclusive_choice/not_coexistence constraints show mutually exclusive paths
- Co_existence constraints show tasks that always run together
- High constraint density on a group of elements = tightly coupled domain
"""

    return f"""Analyze this BPMN business process and help me understand it deeply.

Process: {process.name or process.id}

Elements:
{chr(10).join(elements_summary)}

Flows:
{chr(10).join(flows_summary)}
{constraints_section}
Please provide:

1. USE CASE: What business use-case does this process serve? (one paragraph)

2. BUSINESS GOAL: What is the desired outcome? (one sentence)

3. DOMAIN CLUSTERS: Group the elements into logical business domains.
   For each domain, provide:
   - Name (e.g., "Credit Analysis", "Risk Evaluation")
   - Description of what this domain handles
   - Which BPMN elements belong to it (use element IDs)
   - What capabilities/tools this domain needs
   - Whether it requires human involvement
   Use the structural constraints to identify tightly coupled elements
   that belong in the same domain.

4. DECISION POINTS: For each gateway/decision:
   - What business question is being answered?
   - What data drives this decision?
   - Could an AI agent make this decision? With what confidence?
   Use exclusive_choice constraints to understand the branching logic.

5. INTEGRATION POINTS: What external systems/APIs does this process touch?

6. HUMAN TOUCHPOINTS: Where is human judgment truly needed vs. where was it
   just a BPM limitation?

Format your response as structured JSON matching this schema:
{{
  "use_case": "string",
  "business_goal": "string",
  "domains": [
    {{
      "name": "string",
      "description": "string",
      "elements": ["element_id", ...],
      "capabilities": ["what this domain needs to do", ...],
      "needs_human": true/false
    }}
  ],
  "decision_points": [
    {{
      "element_id": "string",
      "business_question": "string",
      "data_needed": ["string", ...],
      "ai_suitable": true/false,
      "confidence_note": "string"
    }}
  ],
  "integration_points": [
    {{
      "element_id": "string",
      "system": "string",
      "purpose": "string"
    }}
  ],
  "human_touchpoints": [
    {{
      "element_id": "string",
      "reason": "string",
      "truly_needs_human": true/false,
      "alternative": "string"
    }}
  ]
}}"""


def parse_analysis_response(response_json: dict) -> ProcessUnderstanding:
    """Parse the LLM's analysis response into a ProcessUnderstanding."""
    domains = []
    for d in response_json.get("domains", []):
        domains.append(DomainCluster(
            name=d["name"],
            description=d["description"],
            elements=d.get("elements", []),
            capabilities=d.get("capabilities", []),
            needs_human=d.get("needs_human", False),
        ))

    return ProcessUnderstanding(
        use_case=response_json.get("use_case", ""),
        business_goal=response_json.get("business_goal", ""),
        domains=domains,
        decision_points=response_json.get("decision_points", []),
        integration_points=response_json.get("integration_points", []),
        human_touchpoints=response_json.get("human_touchpoints", []),
    )
