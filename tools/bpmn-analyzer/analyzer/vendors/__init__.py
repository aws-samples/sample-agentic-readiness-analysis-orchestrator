"""
Vendor-specific BPMN dependency extractors.

Each module in this package implements a VendorExtractor subclass that handles
platform-specific extension attributes. Extractors are auto-registered at
import time.

To add a new vendor:
  1. Create a new .py file in this directory
  2. Subclass VendorExtractor
  3. Set NAMESPACES and VENDOR_NAME
  4. Implement extract()
  5. Call register_vendor() at module level

The base dependency_extractor auto-discovers matching vendors by checking
which XML namespaces are present in the BPMN document.

Error handling:
  If a vendor module fails to import (syntax error, missing dependency),
  it is logged and skipped rather than crashing the entire pipeline.
"""
import importlib
import logging
import pkgutil
from pathlib import Path

logger = logging.getLogger(__name__)

# Auto-import all modules in this package to trigger registration.
# Each module is isolated: import failures are logged, not propagated.
_pkg_dir = Path(__file__).parent
_load_errors: list[dict] = []

for _importer, _modname, _ispkg in pkgutil.iter_modules([str(_pkg_dir)]):
    try:
        importlib.import_module(f".{_modname}", __package__)
    except Exception as exc:
        logger.warning(
            "Failed to load vendor extractor module '%s': %s", _modname, exc,
        )
        _load_errors.append({
            "module": _modname,
            "error_type": type(exc).__name__,
            "error": str(exc),
        })


def get_load_errors() -> list[dict]:
    """Return any errors encountered during vendor module auto-discovery."""
    return list(_load_errors)
