"""
Public handoff fingerprint helper.

This module provides a small deterministic integrity hash for local handoff
metadata. It is intentionally not a scoring engine and does not implement any
protected ranking, arbitration, or promotion logic.
"""

from __future__ import annotations

import hashlib
from typing import Iterable, List


class ArtifactFingerprint:
    """Compute stable local hashes for handoff integrity checks."""

    def compute(self, tokens: Iterable[str]) -> str:
        if tokens is None:
            tokens = []
        norm: List[str] = sorted(
            {str(t).strip().lower() for t in tokens if str(t).strip()}
        )
        blob = b"" if not norm else "\x00".join(norm).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()

    def verify(self, tokens: Iterable[str], fingerprint: str) -> bool:
        if not fingerprint or not isinstance(fingerprint, str):
            return False
        return self.compute(tokens) == fingerprint

    def strength(self, tokens: Iterable[str]) -> int:
        if tokens is None:
            tokens = []
        norm = {str(t).strip().lower() for t in tokens if str(t).strip()}
        return len(norm)
