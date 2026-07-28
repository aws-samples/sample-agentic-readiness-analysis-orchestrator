"""
Camunda 8 vendor extractor — extracts dependencies from zeebe: namespace extensions.

Camunda C8 uses Zeebe-specific task definitions with job types and task headers.
"""
from lxml import etree

from analyzer.dependency_extractor import (
    Dependency, DependencyType,
    VendorExtractor, register_vendor,
)
from parser.bpmn_parser import BPMNProcess


class CamundaC8Extractor(VendorExtractor):
    NAMESPACES = {"zeebe": "http://camunda.org/schema/zeebe/1.0"}
    VENDOR_NAME = "camunda-c8"

    def extract(self, root, process_el, process):
        deps = []
        ns = self.NAMESPACES["zeebe"]

        for el in process_el.iter():
            local_tag = etree.QName(el.tag).localname
            if local_tag not in ("serviceTask", "sendTask", "businessRuleTask", "scriptTask"):
                continue

            task_id = el.get("id", "")
            task_name = el.get("name", "") or task_id

            # Look for zeebe:taskDefinition in extensionElements
            for ext_els in el.iter():
                if etree.QName(ext_els.tag).localname == "taskDefinition" and ns in ext_els.tag:
                    job_type = ext_els.get("type", "")
                    if job_type:
                        deps.append(Dependency(
                            source_task_id=task_id,
                            source_task_name=task_name,
                            target_type=DependencyType.SERVICE_ENDPOINT,
                            target_ref=f"zeebe:{job_type}",
                            confidence="high",
                            bpmn_element=task_id,
                            vendor=self.VENDOR_NAME,
                            metadata={"attribute": "zeebe:taskDefinition.type"},
                        ))

        return deps


# Auto-register
register_vendor(CamundaC8Extractor())
