"""
Dependency Extractor — discovers system dependencies from BPMN 2.0 elements.

Architecture:
  Base extractor handles standard BPMN 2.0 elements (dataStoreReference,
  messageFlow, callActivity, serviceTask with implementation attribute).

  Vendor-specific extractors register via the vendors/ package and handle
  platform-specific extension attributes (camunda:class, zeebe:taskDefinition,
  drools: extensions, etc.).

  Adding a new vendor: create a file in vendors/ that subclasses
  VendorExtractor, declare NAMESPACES and implement extract(). The registry
  auto-discovers it.

Error handling:
  - Malformed XML or missing <process>: raises MalformedBPMN
  - Unsupported vendor namespaces: logged as warnings in the report
  - Vendor extractor crashes: isolated, logged as warnings, pipeline continues
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from lxml import etree

from parser.bpmn_parser import BPMNProcess, ProcessElement, ElementType
from analyzer.exceptions import (
    AnalysisWarning,
    MalformedBPMN,
    VendorExtractorError,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

class DependencyTier(Enum):
    DECLARED = "declared"
    INFERRED = "inferred"
    UNKNOWN = "unknown"


class DependencyType(Enum):
    SERVICE_ENDPOINT = "service_endpoint"
    DATA_STORE = "data_store"
    MESSAGE_FLOW = "message_flow"
    CALL_ACTIVITY = "call_activity"
    ERROR_BOUNDARY = "error_boundary"
    VENDOR_SPECIFIC = "vendor_specific"


@dataclass
class Dependency:
    source_task_id: str
    source_task_name: str
    target_type: DependencyType
    target_ref: str
    confidence: str = "medium"          # high / medium / low
    tier: DependencyTier = DependencyTier.INFERRED
    bpmn_element: str = ""
    vendor: str = "bpmn-2.0"            # which extractor found it
    metadata: dict = field(default_factory=dict)


@dataclass
class DependencyReport:
    declared: list[Dependency] = field(default_factory=list)
    inferred: list[Dependency] = field(default_factory=list)
    unknown: list[UnknownDependency] = field(default_factory=list)
    warnings: list[AnalysisWarning] = field(default_factory=list)


@dataclass
class UnknownDependency:
    source_task_id: str
    source_task_name: str
    reason: str


# ---------------------------------------------------------------------------
# Vendor extractor base class + registry
# ---------------------------------------------------------------------------

class VendorExtractor:
    """Base class for vendor-specific dependency extractors."""

    # Subclasses declare the XML namespaces they handle.
    # Example: {"camunda": "http://camunda.org/schema/1.0/bpmn"}
    NAMESPACES: dict[str, str] = {}

    # Human-readable vendor name for reporting.
    VENDOR_NAME: str = "unknown"

    def extract(
        self,
        root: etree._Element,
        process_el: etree._Element,
        process: BPMNProcess,
    ) -> list[Dependency]:
        """Extract vendor-specific dependencies. Override in subclasses."""
        return []


class _VendorRegistry:
    """Auto-discovers and manages vendor extractors."""

    def __init__(self):
        self._extractors: list[VendorExtractor] = []

    def register(self, extractor: VendorExtractor):
        self._extractors.append(extractor)

    def get_matching(self, root: etree._Element) -> list[VendorExtractor]:
        """Return extractors whose namespaces appear in the document."""
        doc_namespaces = set(root.nsmap.values())
        matching = []
        for ext in self._extractors:
            if any(ns in doc_namespaces for ns in ext.NAMESPACES.values()):
                matching.append(ext)
        return matching

    def get_unmatched_vendor_namespaces(self, root: etree._Element) -> list[str]:
        """Return document namespaces that look vendor-specific but have no extractor.

        Filters out standard BPMN/XML namespaces to only flag genuinely
        unhandled vendor extensions.
        """
        doc_namespaces = set(root.nsmap.values())
        handled = set()
        for ext in self._extractors:
            handled.update(ext.NAMESPACES.values())

        # Standard namespaces to ignore (not vendor-specific)
        standard_ns = {
            BPMN_NS,
            "http://www.omg.org/spec/BPMN/20100524/DI",
            "http://www.omg.org/spec/DD/20100524/DC",
            "http://www.omg.org/spec/DD/20100524/DI",
            "http://www.w3.org/2001/XMLSchema-instance",
            "http://www.w3.org/2001/XMLSchema",
            "http://www.bpsim.org/schemas/1.0",
        }

        return sorted(doc_namespaces - handled - standard_ns)

    def registered_vendor_names(self) -> list[str]:
        return [ext.VENDOR_NAME for ext in self._extractors]

    def all(self) -> list[VendorExtractor]:
        return list(self._extractors)


_registry = _VendorRegistry()


def register_vendor(extractor: VendorExtractor):
    """Register a vendor extractor. Called at import time by vendor modules."""
    _registry.register(extractor)


# ---------------------------------------------------------------------------
# Standard BPMN 2.0 extractor
# ---------------------------------------------------------------------------

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
_NS = {"bpmn": BPMN_NS}


def _extract_standard_dependencies(
    root: etree._Element,
    process_el: etree._Element,
    process: BPMNProcess,
) -> tuple[list[Dependency], list[UnknownDependency]]:
    """Extract dependencies from standard BPMN 2.0 elements."""
    deps: list[Dependency] = []
    unknowns: list[UnknownDependency] = []

    # 1. serviceTask with implementation attribute
    for el in process_el.findall("bpmn:serviceTask", _NS):
        task_id = el.get("id", "")
        task_name = el.get("name", "") or task_id
        impl = el.get("implementation", "")
        operation_ref = el.get("operationRef", "")

        if impl and impl.lower() not in ("", "##unspecified", "##webservice"):
            deps.append(Dependency(
                source_task_id=task_id,
                source_task_name=task_name,
                target_type=DependencyType.SERVICE_ENDPOINT,
                target_ref=impl,
                confidence="high",
                bpmn_element=task_id,
                vendor="bpmn-2.0",
            ))
        elif operation_ref:
            deps.append(Dependency(
                source_task_id=task_id,
                source_task_name=task_name,
                target_type=DependencyType.SERVICE_ENDPOINT,
                target_ref=operation_ref,
                confidence="medium",
                bpmn_element=task_id,
                vendor="bpmn-2.0",
            ))

    # 2. dataStoreReference elements
    for el in process_el.findall("bpmn:dataStoreReference", _NS):
        store_id = el.get("id", "")
        store_name = el.get("name", "") or store_id
        data_store_ref = el.get("dataStoreRef", "")
        # Find which tasks reference this data store via dataInputAssociation/dataOutputAssociation
        referencing_tasks = _find_tasks_referencing(process_el, store_id)
        for task_id, task_name in referencing_tasks:
            deps.append(Dependency(
                source_task_id=task_id,
                source_task_name=task_name,
                target_type=DependencyType.DATA_STORE,
                target_ref=store_name,
                confidence="high",
                bpmn_element=store_id,
                vendor="bpmn-2.0",
                metadata={"dataStoreRef": data_store_ref} if data_store_ref else {},
            ))
        if not referencing_tasks:
            # Data store exists but no task references it directly
            deps.append(Dependency(
                source_task_id="",
                source_task_name="(process-level)",
                target_type=DependencyType.DATA_STORE,
                target_ref=store_name,
                confidence="medium",
                bpmn_element=store_id,
                vendor="bpmn-2.0",
            ))

    # 3. messageFlow elements (at definitions level, not process level)
    definitions_el = root
    for el in definitions_el.findall("bpmn:collaboration/bpmn:messageFlow", _NS):
        flow_id = el.get("id", "")
        flow_name = el.get("name", "") or flow_id
        source_ref = el.get("sourceRef", "")
        target_ref = el.get("targetRef", "")
        # Determine which end is in our process
        source_name = _resolve_element_name(process, source_ref)
        target_name = _resolve_element_name(process, target_ref)
        if source_ref in process.elements:
            deps.append(Dependency(
                source_task_id=source_ref,
                source_task_name=source_name,
                target_type=DependencyType.MESSAGE_FLOW,
                target_ref=target_name or target_ref,
                confidence="high",
                bpmn_element=flow_id,
                vendor="bpmn-2.0",
                metadata={"direction": "outbound"},
            ))
        elif target_ref in process.elements:
            deps.append(Dependency(
                source_task_id=target_ref,
                source_task_name=target_name,
                target_type=DependencyType.MESSAGE_FLOW,
                target_ref=source_name or source_ref,
                confidence="high",
                bpmn_element=flow_id,
                vendor="bpmn-2.0",
                metadata={"direction": "inbound"},
            ))

    # 4. callActivity elements
    for el in process_el.findall("bpmn:callActivity", _NS):
        task_id = el.get("id", "")
        task_name = el.get("name", "") or task_id
        called_element = el.get("calledElement", "")
        if called_element:
            deps.append(Dependency(
                source_task_id=task_id,
                source_task_name=task_name,
                target_type=DependencyType.CALL_ACTIVITY,
                target_ref=called_element,
                confidence="high",
                bpmn_element=task_id,
                vendor="bpmn-2.0",
            ))

    # 5. User tasks with no system references -> unknown
    for elem_id, elem in process.elements.items():
        if elem.element_type == ElementType.USER_TASK:
            # Check if this user task has any data associations
            has_system_ref = any(
                d.source_task_id == elem_id
                for d in deps
            )
            if not has_system_ref:
                unknowns.append(UnknownDependency(
                    source_task_id=elem_id,
                    source_task_name=elem.name or elem_id,
                    reason="User task with no system references in BPMN model",
                ))

    return deps, unknowns


def _find_tasks_referencing(
    process_el: etree._Element, store_id: str
) -> list[tuple[str, str]]:
    """Find tasks that reference a data store via data associations."""
    results = []
    for tag in ("serviceTask", "userTask", "task", "scriptTask", "businessRuleTask"):
        for el in process_el.findall(f"bpmn:{tag}", _NS):
            # Check dataInputAssociation and dataOutputAssociation
            for assoc_tag in ("dataInputAssociation", "dataOutputAssociation"):
                for assoc in el.findall(f"bpmn:{assoc_tag}", _NS):
                    for source in assoc.findall("bpmn:sourceRef", _NS):
                        if source.text and source.text.strip() == store_id:
                            results.append((el.get("id", ""), el.get("name", "")))
                    for target in assoc.findall("bpmn:targetRef", _NS):
                        if target.text and target.text.strip() == store_id:
                            results.append((el.get("id", ""), el.get("name", "")))
    return results


def _resolve_element_name(process: BPMNProcess, ref: str) -> str:
    """Resolve an element ID to its name, or return empty string."""
    if ref in process.elements:
        return process.elements[ref].name or ref
    return ""


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def extract_dependencies(
    bpmn_path: str,
    process: BPMNProcess,
) -> DependencyReport:
    """
    Extract all dependencies from a BPMN file.

    Uses standard BPMN 2.0 extraction plus any registered vendor extractors
    whose namespaces are detected in the document.

    Error handling:
      - Malformed XML: raises MalformedBPMN
      - Missing <process>: returns empty report with warning
      - Vendor extractor crash: isolated, logged as warning, pipeline continues
      - Unrecognized vendor namespaces: logged as warnings
    """
    warnings: list[AnalysisWarning] = []

    # Parse XML (may raise on malformed input)
    try:
        tree = etree.parse(bpmn_path)
    except etree.XMLSyntaxError as exc:
        raise MalformedBPMN(
            f"Dependency extraction failed: not valid XML: {exc}",
            file_path=bpmn_path,
            context={"original_error": str(exc)},
        ) from exc
    except OSError as exc:
        raise MalformedBPMN(
            f"Dependency extraction failed: cannot read file: {exc}",
            file_path=bpmn_path,
            context={"original_error": str(exc)},
        ) from exc

    root = tree.getroot()

    # Find the process element (handle both bpmn: and bpmn2: prefixes)
    process_el = root.find("bpmn:process", _NS)
    if process_el is None:
        # Try without namespace prefix (some exporters use default namespace)
        for child in root:
            try:
                if etree.QName(child.tag).localname == "process":
                    process_el = child
                    break
            except (ValueError, TypeError):
                continue
    if process_el is None:
        warnings.append(AnalysisWarning(
            code="no_process_element",
            message="No <process> element found; dependency extraction skipped",
            file_path=bpmn_path,
        ))
        return DependencyReport(warnings=warnings)

    # Standard BPMN 2.0 extraction
    inferred, unknowns = _extract_standard_dependencies(root, process_el, process)

    # Vendor-specific extraction (isolated per vendor)
    for vendor_ext in _registry.get_matching(root):
        try:
            vendor_deps = vendor_ext.extract(root, process_el, process)
            inferred.extend(vendor_deps)
        except Exception as exc:
            logger.warning(
                "Vendor extractor %s failed on %s: %s",
                vendor_ext.VENDOR_NAME, bpmn_path, exc,
            )
            warnings.append(AnalysisWarning(
                code="vendor_extractor_error",
                message=(
                    f"Vendor extractor '{vendor_ext.VENDOR_NAME}' raised an error "
                    f"and was skipped: {exc}"
                ),
                vendor=vendor_ext.VENDOR_NAME,
                file_path=bpmn_path,
                details={"error_type": type(exc).__name__, "error": str(exc)},
            ))

    # Detect unhandled vendor namespaces
    unmatched = _registry.get_unmatched_vendor_namespaces(root)
    if unmatched:
        warnings.append(AnalysisWarning(
            code="unsupported_vendor_namespace",
            message=(
                f"Document contains vendor namespace(s) with no registered extractor: "
                f"{', '.join(unmatched)}. Vendor-specific dependencies may be missed."
            ),
            file_path=bpmn_path,
            details={
                "unmatched_namespaces": unmatched,
                "registered_vendors": _registry.registered_vendor_names(),
            },
        ))

    # Deduplicate by (source_task_id, target_ref, target_type)
    seen = set()
    deduped = []
    for d in inferred:
        key = (d.source_task_id, d.target_ref, d.target_type)
        if key not in seen:
            seen.add(key)
            deduped.append(d)

    return DependencyReport(
        declared=[],  # Populated by orchestrator from portfolio-config.yaml
        inferred=deduped,
        unknown=unknowns,
        warnings=warnings,
    )


def to_dict(report: DependencyReport) -> dict:
    """Serialize a DependencyReport to a JSON-compatible dict."""
    result = {
        "declared": [_dep_to_dict(d) for d in report.declared],
        "inferred": [_dep_to_dict(d) for d in report.inferred],
        "unknown": [
            {
                "source_task_id": u.source_task_id,
                "source_task_name": u.source_task_name,
                "reason": u.reason,
            }
            for u in report.unknown
        ],
    }
    if report.warnings:
        result["warnings"] = [w.to_dict() for w in report.warnings]
    return result


def _dep_to_dict(d: Dependency) -> dict:
    result = {
        "source_task_id": d.source_task_id,
        "source_task_name": d.source_task_name,
        "target_type": d.target_type.value,
        "target_ref": d.target_ref,
        "confidence": d.confidence,
        "bpmn_element": d.bpmn_element,
        "vendor": d.vendor,
    }
    if d.metadata:
        result["metadata"] = d.metadata
    return result
