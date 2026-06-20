"""
rdn/handoff/engine.py

DEPRECATED / INTERNAL ACCESS ONLY.

The PCF engine module has been consolidated into the internal module `rdn.handoff._pcf`.

External code should never import from here. Use the high-level `ReasonRDN`
class instead, which handles fingerprinting internally.
"""

from __future__ import annotations

import warnings

from . import _pcf as _pcf

warnings.warn(
    "rdn.handoff.engine is deprecated and will be removed. "
    "Do not rely on PCFEngine directly. Use ReasonRDN for handoffs.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export for anyone who was doing deep imports (will warn).
PCFEngine = _pcf._PCFEngine
