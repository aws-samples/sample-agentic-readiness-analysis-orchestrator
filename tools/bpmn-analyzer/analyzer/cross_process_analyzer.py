"""
Cross-Process Analyzer — Identifies shared capability domains across
multiple BPMN processes using Jaccard similarity of capability keyword sets.

When analyzing multiple BPMN files, this module compares domain clusters
from each process's ProcessUnderstanding and recommends reusable agents
that can serve multiple workflows.
"""
from dataclasses import dataclass, field
from itertools import combinations

from analyzer.process_analyzer import ProcessUnderstanding


@dataclass
class SharedDomain:
    """A business capability domain shared across multiple processes."""
    domain_name: str
    matching_processes: list[str] = field(default_factory=list)
    shared_capabilities: list[str] = field(default_factory=list)
    process_specific_capabilities: dict[str, list[str]] = field(default_factory=dict)
    similarity: float = 0.0
    recommendation: str = ""  # "single_reusable_agent" | "separate_with_shared_tools"


@dataclass
class ReusableAgent:
    """A recommended agent that can serve multiple processes."""
    name: str = ""
    served_processes: list[str] = field(default_factory=list)
    shared_tools: list[str] = field(default_factory=list)
    process_specific_extensions: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class CrossProcessAnalysis:
    """Result of cross-process domain matching analysis."""
    shared_domains: list[SharedDomain] = field(default_factory=list)
    reusable_agents: list[ReusableAgent] = field(default_factory=list)
    summary: str = ""


def _jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    """Jaccard index: |A ∩ B| / |A ∪ B|. Returns 0.0 for two empty sets."""
    union = set_a | set_b
    if not union:
        return 0.0
    return len(set_a & set_b) / len(union)


def analyze_cross_process(
    understandings: list[tuple[str, ProcessUnderstanding]],
) -> CrossProcessAnalysis:
    """
    Compare domain clusters across processes using Jaccard similarity
    of capability keyword sets.

    Args:
        understandings: List of (process_name, ProcessUnderstanding) tuples.

    Returns:
        CrossProcessAnalysis with shared domains, reusable agents, and summary.

    Thresholds:
        - similarity >= 0.6 → shared domain
        - shared > 70% of capabilities → recommend single_reusable_agent
        - shared 40-70% of capabilities → recommend separate_with_shared_tools
        - all similarities < 0.4 → no significant overlap
    """
    if len(understandings) < 2:
        return CrossProcessAnalysis(
            summary="Cross-process analysis requires at least two processes.",
        )

    shared_domains: list[SharedDomain] = []

    # Build a flat list of (process_name, domain) pairs for pairwise comparison
    process_domains: list[tuple[str, str, set[str]]] = []
    for proc_name, understanding in understandings:
        for domain in understanding.domains:
            caps = {c.lower().strip() for c in domain.capabilities if c.strip()}
            process_domains.append((proc_name, domain.name, caps))

    # Compare every pair of domains across different processes
    for i, j in combinations(range(len(process_domains)), 2):
        proc_a, domain_a, caps_a = process_domains[i]
        proc_b, domain_b, caps_b = process_domains[j]

        # Only compare domains from different processes
        if proc_a == proc_b:
            continue

        sim = _jaccard_similarity(caps_a, caps_b)
        if sim < 0.6:
            continue

        # Shared domain found
        shared_caps = sorted(caps_a & caps_b)
        all_caps = caps_a | caps_b
        shared_ratio = len(shared_caps) / len(all_caps) if all_caps else 0.0

        if shared_ratio > 0.7:
            recommendation = "single_reusable_agent"
        elif shared_ratio >= 0.4:
            recommendation = "separate_with_shared_tools"
        else:
            recommendation = "separate_with_shared_tools"

        # Compute process-specific capabilities
        process_specific: dict[str, list[str]] = {}
        specific_a = sorted(caps_a - caps_b)
        specific_b = sorted(caps_b - caps_a)
        if specific_a:
            process_specific[proc_a] = specific_a
        if specific_b:
            process_specific[proc_b] = specific_b

        # Use a combined domain name
        domain_name = domain_a if domain_a == domain_b else f"{domain_a} / {domain_b}"

        shared_domains.append(SharedDomain(
            domain_name=domain_name,
            matching_processes=sorted({proc_a, proc_b}),
            shared_capabilities=shared_caps,
            process_specific_capabilities=process_specific,
            similarity=sim,
            recommendation=recommendation,
        ))

    # Build reusable agents from shared domains
    reusable_agents: list[ReusableAgent] = []
    for sd in shared_domains:
        agent_name = sd.domain_name.lower().replace(" ", "_").replace("/", "_")
        reusable_agents.append(ReusableAgent(
            name=f"{agent_name}_agent",
            served_processes=sd.matching_processes,
            shared_tools=sd.shared_capabilities,
            process_specific_extensions=sd.process_specific_capabilities,
        ))

    # Build summary
    if shared_domains:
        domain_names = [sd.domain_name for sd in shared_domains]
        summary = (
            f"Found {len(shared_domains)} shared domain(s) across processes: "
            f"{', '.join(domain_names)}. "
            f"Recommended {len(reusable_agents)} reusable agent(s)."
        )
    else:
        # Check if all similarities are below 0.4
        max_sim = 0.0
        for i, j in combinations(range(len(process_domains)), 2):
            proc_a = process_domains[i][0]
            proc_b = process_domains[j][0]
            if proc_a == proc_b:
                continue
            caps_a = process_domains[i][2]
            caps_b = process_domains[j][2]
            sim = _jaccard_similarity(caps_a, caps_b)
            max_sim = max(max_sim, sim)

        if max_sim < 0.4:
            summary = (
                "No significant domain overlap detected across processes. "
                "Recommend independent agent architectures for each process."
            )
        else:
            summary = (
                "Some domain similarity detected but below the shared domain "
                "threshold (0.6). Consider reviewing capabilities for potential sharing."
            )

    return CrossProcessAnalysis(
        shared_domains=shared_domains,
        reusable_agents=reusable_agents,
        summary=summary,
    )
