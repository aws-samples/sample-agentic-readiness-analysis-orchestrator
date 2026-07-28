"""
Camunda 7 vendor extractor — extracts dependencies from camunda: namespace extensions.

Camunda C7 service tasks use extension attributes to specify Java class delegates,
expression delegates, and external task topics. These are strong signals for
downstream system dependencies.
"""
from lxml import etree

from analyzer.dependency_extractor import (
    Dependency, DependencyType, DependencyTier,
    VendorExtractor, register_vendor,
)
from parser.bpmn_parser import BPMNProcess


class CamundaC7Extractor(VendorExtractor):
    NAMESPACES = {"camunda": "http://camunda.org/schema/1.0/bpmn"}
    VENDOR_NAME = "camunda-c7"

    def extract(self, root, process_el, process):
        deps = []
        ns = self.NAMESPACES

        for el in process_el.iter():
            local_tag = etree.QName(el.tag).localname
            if local_tag not in ("serviceTask", "sendTask", "businessRuleTask"):
                continue

            task_id = el.get("id", "")
            task_name = el.get("name", "") or task_id

            # camunda:class — Java delegate class (strong signal)
            java_class = el.get(f"{{{ns['camunda']}}}class", "")
            if java_class:
                deps.append(Dependency(
                    source_task_id=task_id,
                    source_task_name=task_name,
                    target_type=DependencyType.SERVICE_ENDPOINT,
                    target_ref=java_class,
                    confidence="high",
                    bpmn_element=task_id,
                    vendor=self.VENDOR_NAME,
                    metadata={"attribute": "camunda:class"},
                ))
                continue

            # camunda:delegateExpression — Spring bean reference
            delegate = el.get(f"{{{ns['camunda']}}}delegateExpression", "")
            if delegate:
                deps.append(Dependency(
                    source_task_id=task_id,
                    source_task_name=task_name,
                    target_type=DependencyType.SERVICE_ENDPOINT,
                    target_ref=delegate,
                    confidence="high",
                    bpmn_element=task_id,
                    vendor=self.VENDOR_NAME,
                    metadata={"attribute": "camunda:delegateExpression"},
                ))
                continue

            # camunda:expression — inline expression (weaker signal)
            expression = el.get(f"{{{ns['camunda']}}}expression", "")
            if expression:
                deps.append(Dependency(
                    source_task_id=task_id,
                    source_task_name=task_name,
                    target_type=DependencyType.SERVICE_ENDPOINT,
                    target_ref=expression,
                    confidence="medium",
                    bpmn_element=task_id,
                    vendor=self.VENDOR_NAME,
                    metadata={"attribute": "camunda:expression"},
                ))
                continue

            # camunda:type="external" with camunda:topic — external task pattern
            task_type = el.get(f"{{{ns['camunda']}}}type", "")
            topic = el.get(f"{{{ns['camunda']}}}topic", "")
            if task_type == "external" and topic:
                deps.append(Dependency(
                    source_task_id=task_id,
                    source_task_name=task_name,
                    target_type=DependencyType.SERVICE_ENDPOINT,
                    target_ref=f"external:{topic}",
                    confidence="high",
                    bpmn_element=task_id,
                    vendor=self.VENDOR_NAME,
                    metadata={"attribute": "camunda:topic", "pattern": "external-task"},
                ))

        return deps


# Auto-register
register_vendor(CamundaC7Extractor())
