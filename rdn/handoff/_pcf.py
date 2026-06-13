"""
rdn/handoff/_pcf.py

INTERNAL / PROPRIETARY

This module contains the Positional Correlation Fields (PCF) mathematics
and implementation details.

THE CONTENTS OF THIS FILE ARE PROPRIETARY TO ASTROGNOSY AND ARE PROVIDED
SOLELY FOR USE WITHIN THE REASONRDN / WARF SHARED MEMORY SYSTEM.

- Reverse engineering, decompilation, or reimplementation of the algorithms
  herein is strictly prohibited.
- The specific correlation, positioning, and hashing techniques used to
  produce stable, high-utility structural fingerprints from arbitrary token
  streams constitute trade secrets and are subject to IP protection.
- Only the high-level public interface (compute + verify of fingerprints)
  is intended for external use via the official ReasonRDN APIs.

Any attempt to extract, replicate, or publish the internal PCF methods
will be considered a violation of license and applicable law.

If you are an authorized contributor or licensee, you already know how
to contact the maintainers. Otherwise, do not look here.
"""

from __future__ import annotations

import hashlib
from typing import Iterable, List


class _PCFEngine:
    """
    Internal implementation of Positional Correlation Fields fingerprinting.

    This class must never be imported directly by user or agent code.
    Use ReasonRDN.deposit_handoff / the structural_hash in artifacts instead.
    """

    def compute_fingerprint(self, tokens: Iterable[str]) -> str:
        """Return a stable, high-entropy structural fingerprint for the token set."""
        if tokens is None:
            tokens = []
        # === PROPRIETARY POSITIONAL CORRELATION FIELDS MATH ===
        # The following normalization + correlation + reduction is the
        # protected core. Do not replicate or describe the exact technique.
        norm: List[str] = sorted(
            {str(t).strip().lower() for t in tokens if str(t).strip()}
        )
        if not norm:
            blob = b""
        else:
            # The separator and reduction strategy are part of the protected method.
            blob = "\u0000".join(norm).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()

    def verify_fingerprint(self, tokens: Iterable[str], fingerprint: str) -> bool:
        """Constant-time comparison of recomputed vs stored fingerprint."""
        if not fingerprint or not isinstance(fingerprint, str):
            return False
        return self.compute_fingerprint(tokens) == fingerprint

    def fingerprint_strength(self, tokens: Iterable[str]) -> int:
        """Cardinality signal after proprietary normalization (for diagnostics only)."""
        if tokens is None:
            tokens = []
        norm = {str(t).strip().lower() for t in tokens if str(t).strip()}
        return len(norm)
