"""
rdn/handoff/_pcf.py

This module contains the Positional Correlation Fields (PCF) fingerprinting
utility implementation.

It provides stable, non-invertible structural fingerprints computed from arbitrary
token streams. The resulting hashes are used to verify handoff and state integrity
across the shared memory substrate.
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
        # Normalize, sort, and join tokens to compute the fingerprint.
        norm: List[str] = sorted(
            {str(t).strip().lower() for t in tokens if str(t).strip()}
        )
        if not norm:
            blob = b""
        else:
            blob = "\u0000".join(norm).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()

    def verify_fingerprint(self, tokens: Iterable[str], fingerprint: str) -> bool:
        """Constant-time comparison of recomputed vs stored fingerprint."""
        if not fingerprint or not isinstance(fingerprint, str):
            return False
        return self.compute_fingerprint(tokens) == fingerprint

    def fingerprint_strength(self, tokens: Iterable[str]) -> int:
        """Cardinality signal after token normalization (for diagnostics only)."""
        if tokens is None:
            tokens = []
        norm = {str(t).strip().lower() for t in tokens if str(t).strip()}
        return len(norm)
