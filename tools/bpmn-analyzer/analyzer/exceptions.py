"""
Exception hierarchy for the BPMN analyzer.

All exceptions inherit from BPMNAnalysisError so callers can catch broadly
or narrowly. Each exception carries structured context (file path, detected
version/vendor, supported versions) so the orchestrator can surface actionable
messages in the TD report rather than raw stack traces.
"""
from __future__ import annotations

from dataclasses import dataclass, field


class BPMNAnalysisError(Exception):
    """Base exception for all BPMN analysis failures."""

    def __init__(self, message: str, *, file_path: str = "", context: dict | None = None):
        super().__init__(message)
        self.file_path = file_path
        self.context = context or {}


class MalformedBPMN(BPMNAnalysisError):
    """File is not valid XML or not valid BPMN structure."""
    pass


class UnsupportedBPMNVersion(BPMNAnalysisError):
    """BPMN version detected but not supported by this analyzer."""

    def __init__(
        self,
        message: str,
        *,
        file_path: str = "",
        detected_version: str = "",
        supported_versions: list[str] | None = None,
    ):
        super().__init__(message, file_path=file_path, context={
            "detected_version": detected_version,
            "supported_versions": supported_versions or ["2.0"],
        })
        self.detected_version = detected_version
        self.supported_versions = supported_versions or ["2.0"]


class UnsupportedVendor(BPMNAnalysisError):
    """Vendor namespace detected but no extractor registered for it."""

    def __init__(
        self,
        message: str,
        *,
        file_path: str = "",
        vendor_namespaces: list[str] | None = None,
        registered_vendors: list[str] | None = None,
    ):
        super().__init__(message, file_path=file_path, context={
            "vendor_namespaces": vendor_namespaces or [],
            "registered_vendors": registered_vendors or [],
        })
        self.vendor_namespaces = vendor_namespaces or []
        self.registered_vendors = registered_vendors or []


class VendorExtractorError(BPMNAnalysisError):
    """A vendor extractor raised an unexpected exception during extraction."""

    def __init__(
        self,
        message: str,
        *,
        file_path: str = "",
        vendor_name: str = "",
        original_error: Exception | None = None,
    ):
        super().__init__(message, file_path=file_path, context={
            "vendor_name": vendor_name,
            "original_error": str(original_error) if original_error else "",
        })
        self.vendor_name = vendor_name
        self.original_error = original_error


# ---------------------------------------------------------------------------
# Warning dataclass (non-fatal, included in report output)
# ---------------------------------------------------------------------------

@dataclass
class AnalysisWarning:
    """Non-fatal issue encountered during analysis. Surfaced in JSON output."""
    code: str           # machine-readable: unsupported_vendor, vendor_error, etc.
    message: str        # human-readable explanation
    vendor: str = ""
    file_path: str = ""
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = {"code": self.code, "message": self.message}
        if self.vendor:
            d["vendor"] = self.vendor
        if self.details:
            d["details"] = self.details
        return d
