"""
jBPM vendor extractor -- extracts dependencies from drools: namespace extensions.

jBPM/Red Hat Process Automation Manager uses drools:metaData elements for
element metadata and drools:onEntry/onExit for action scripts. The process
element itself carries drools:packageName and drools:version.

This is a stub for MVP. Future enhancements:
  - Extract work item handler references from task definitions
  - Parse drools:import for external class dependencies
  - Extract signal/message event references
"""
from lxml import etree

from analyzer.dependency_extractor import (
    Dependency, DependencyType,
    VendorExtractor, register_vendor,
)
from parser.bpmn_parser import BPMNProcess


class JBPMExtractor(VendorExtractor):
    NAMESPACES = {"drools": "http://www.jboss.org/drools"}
    VENDOR_NAME = "jbpm"

    def extract(self, root, process_el, process):
        deps = []
        ns = self.NAMESPACES["drools"]

        # Extract drools:packageName from process element (signals Java package dependency)
        pkg = process_el.get(f"{{{ns}}}packageName", "")
        if pkg:
            deps.append(Dependency(
                source_task_id=process_el.get("id", ""),
                source_task_name=process_el.get("name", "") or process_el.get("id", ""),
                target_type=DependencyType.VENDOR_SPECIFIC,
                target_ref=f"java-package:{pkg}",
                confidence="medium",
                bpmn_element=process_el.get("id", ""),
                vendor=self.VENDOR_NAME,
                metadata={"attribute": "drools:packageName"},
            ))

        # Future: extract work item handler references, signal events, etc.

        return deps


# Auto-register
register_vendor(JBPMExtractor())
