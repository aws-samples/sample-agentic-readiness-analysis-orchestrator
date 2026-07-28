"""
BPMN 2.0 XML Parser — extracts process elements into a structured graph.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from lxml import etree

from analyzer.exceptions import MalformedBPMN, UnsupportedBPMNVersion


BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
NS = {"bpmn": BPMN_NS}

# Known BPMN namespace patterns for version detection
_BPMN_NS_VERSIONS = {
    "http://www.omg.org/spec/BPMN/20100524/MODEL": "2.0",
    "http://www.omg.org/spec/BPMN/2.0": "2.0",
    # BPMN 1.x namespaces (not supported)
    "http://www.omg.org/spec/BPMN/1.0": "1.0",
    "http://www.omg.org/spec/BPMN/1.1": "1.1",
    "http://www.omg.org/spec/BPMN/1.2": "1.2",
    "http://schemas.xmlsoap.org/bpmn": "1.x",
}

SUPPORTED_VERSIONS = {"2.0"}


class ElementType(Enum):
    START_EVENT = "startEvent"
    END_EVENT = "endEvent"
    TASK = "task"
    SERVICE_TASK = "serviceTask"
    USER_TASK = "userTask"
    SCRIPT_TASK = "scriptTask"
    BUSINESS_RULE_TASK = "businessRuleTask"
    EXCLUSIVE_GATEWAY = "exclusiveGateway"
    PARALLEL_GATEWAY = "parallelGateway"
    INCLUSIVE_GATEWAY = "inclusiveGateway"
    SUBPROCESS = "subProcess"
    TIMER_EVENT = "intermediateCatchEvent"


@dataclass
class SequenceFlow:
    id: str
    source_ref: str
    target_ref: str
    name: str = ""
    condition: str = ""


@dataclass
class ProcessElement:
    id: str
    name: str
    element_type: ElementType
    properties: dict = field(default_factory=dict)
    incoming: list[str] = field(default_factory=list)
    outgoing: list[str] = field(default_factory=list)


@dataclass
class BPMNProcess:
    id: str
    name: str
    elements: dict[str, ProcessElement] = field(default_factory=dict)
    flows: dict[str, SequenceFlow] = field(default_factory=dict)
    start_events: list[str] = field(default_factory=list)
    end_events: list[str] = field(default_factory=list)


def parse_bpmn(file_path: str) -> BPMNProcess:
    """Parse a BPMN 2.0 XML file and return a structured process.

    Raises:
        MalformedBPMN: file is not valid XML or has no recognizable BPMN structure
        UnsupportedBPMNVersion: file uses a BPMN version other than 2.0
    """
    # Parse XML
    try:
        tree = etree.parse(file_path)
    except etree.XMLSyntaxError as exc:
        raise MalformedBPMN(
            f"Not valid XML: {exc}",
            file_path=file_path,
            context={"original_error": str(exc)},
        ) from exc
    except OSError as exc:
        raise MalformedBPMN(
            f"Cannot read file: {exc}",
            file_path=file_path,
            context={"original_error": str(exc)},
        ) from exc

    root = tree.getroot()

    # Detect BPMN version from root namespace
    detected_version = _detect_bpmn_version(root, file_path)
    if detected_version and detected_version not in SUPPORTED_VERSIONS:
        raise UnsupportedBPMNVersion(
            f"BPMN {detected_version} is not supported. "
            f"Supported versions: {', '.join(sorted(SUPPORTED_VERSIONS))}",
            file_path=file_path,
            detected_version=detected_version,
            supported_versions=sorted(SUPPORTED_VERSIONS),
        )

    process_el = root.find("bpmn:process", NS)
    if process_el is None:
        # Try matching by localname (handles default-namespace exports)
        for child in root:
            try:
                if etree.QName(child.tag).localname == "process":
                    process_el = child
                    break
            except (ValueError, TypeError):
                # Skip non-element nodes (comments, processing instructions)
                continue
    if process_el is None:
        raise MalformedBPMN(
            "No <process> element found. File may not be a BPMN document.",
            file_path=file_path,
        )

    process = BPMNProcess(
        id=process_el.get("id", ""),
        name=process_el.get("name", ""),
    )

    # Parse all known element types
    element_tags = [e.value for e in ElementType]
    for tag in element_tags:
        for el in process_el.findall(f"bpmn:{tag}", NS):
            elem = _parse_element(el, tag)
            process.elements[elem.id] = elem
            if tag == "startEvent":
                process.start_events.append(elem.id)
            elif tag == "endEvent":
                process.end_events.append(elem.id)

    # Parse sequence flows
    for flow_el in process_el.findall("bpmn:sequenceFlow", NS):
        flow = _parse_flow(flow_el)
        process.flows[flow.id] = flow
        # Wire up incoming/outgoing on elements
        if flow.source_ref in process.elements:
            process.elements[flow.source_ref].outgoing.append(flow.id)
        if flow.target_ref in process.elements:
            process.elements[flow.target_ref].incoming.append(flow.id)

    return process


def _parse_element(el: etree._Element, tag: str) -> ProcessElement:
    """Parse a single BPMN element."""
    elem = ProcessElement(
        id=el.get("id", ""),
        name=el.get("name", ""),
        element_type=ElementType(tag),
    )
    # Extract extension properties
    for ext in el.findall("bpmn:extensionElements/*", NS):
        local_tag = etree.QName(ext.tag).localname if "}" in ext.tag else ext.tag
        elem.properties[local_tag] = ext.text or ""
    # Also grab raw text children as properties (non-namespaced extensions)
    for child in el:
        local_tag = etree.QName(child.tag).localname if "}" in child.tag else child.tag
        if local_tag == "extensionElements":
            for sub in child:
                sub_tag = etree.QName(sub.tag).localname if "}" in sub.tag else sub.tag
                elem.properties[sub_tag] = sub.text or ""
    return elem


def _parse_flow(el: etree._Element) -> SequenceFlow:
    """Parse a sequence flow element."""
    condition = ""
    cond_el = el.find("bpmn:conditionExpression", NS)
    if cond_el is not None and cond_el.text:
        condition = cond_el.text.strip()
    return SequenceFlow(
        id=el.get("id", ""),
        source_ref=el.get("sourceRef", ""),
        target_ref=el.get("targetRef", ""),
        name=el.get("name", ""),
        condition=condition,
    )


def _detect_bpmn_version(root: etree._Element, file_path: str) -> str:
    """Detect BPMN version from root element namespace.

    Returns version string ("2.0", "1.0", etc.) or empty string if
    no BPMN namespace is recognized (could be CMMN, DMN, or non-BPMN XML).
    """
    # Check root tag namespace
    root_ns = etree.QName(root.tag).namespace or ""
    if root_ns in _BPMN_NS_VERSIONS:
        return _BPMN_NS_VERSIONS[root_ns]

    # Check all declared namespaces on root element
    for prefix, uri in (root.nsmap or {}).items():
        if uri in _BPMN_NS_VERSIONS:
            return _BPMN_NS_VERSIONS[uri]

    # Check if root localname suggests BPMN
    local = etree.QName(root.tag).localname or ""
    if local.lower() == "definitions":
        # Looks like BPMN structure but unknown namespace
        return ""

    return ""
