"""
rdn/handoff/engine.py

DEPRECATED / INTERNAL ACCESS ONLY.

The Positional Correlation Fields (PCF) implementation has been moved
to the private module `rdn.handoff._pcf` for IP protection reasons.

External code should never import from here.

Use the high-level `ReasonRDN` class instead. It handles fingerprinting
internally using protected mathematics and surfaces only `structural_hash`
on artifacts.
"""

from __future__ import annotations

import warnings

from . import _pcf as _pcf

warnings.warn(
    "rdn.handoff.engine is deprecated and will be removed. "
    "Do not rely on PCFEngine directly. Use ReasonRDN for handoffs. "
    "The internal Positional Correlation Fields mathematics are proprietary.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export for anyone who was doing deep imports (will warn).
PCFEngine = _pcf._PCFEngine
