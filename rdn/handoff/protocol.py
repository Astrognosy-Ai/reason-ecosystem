"""
rdn/handoff/protocol.py

High-level handoff orchestrator.

This layer captures rich structural context from operators and agents,
produces a stable integrity fingerprint using proprietary Positional
Correlation Fields (PCF) mathematics (protected IP — see _pcf.py),
and deposits the result via the unified memory client.

Public consumers should only interact with:
- ReasonRDN.deposit_handoff(...)
- ReasonRDN.resolve_handoff(...)
- The "structural_hash" field present in returned artifacts

The internal correlation mathematics are deliberately not exposed.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from rdn.client import RDNClient

# Import the proprietary PCF implementation privately.
# This import path and the contents of _pcf.py are not part of the public API.
from . import _pcf as _pcf


class ReasonRDN:
    """
    Orchestrates high-utility, privacy-preserving handoffs between agents,
    sessions, and the desktop operator.

    Internally uses proprietary Positional Correlation Fields (PCF) to
    generate stable structural fingerprints. These fingerprints are stored
    as `structural_hash` on artifacts and can be used by consumers for
    relevance verification without exposing the underlying math.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        node_url: Optional[str] = None,
        mirror_local: Optional[bool] = None,
    ):
        # Private instance of the protected fingerprint engine.
        self._fingerprint_engine = _pcf._PCFEngine()
        self.client = RDNClient(
            db_path=db_path,
            node_url=node_url,
            mirror_local=True if mirror_local is None else mirror_local,
        )

    def deposit_handoff(
        self,
        project: str,
        summary: str,
        state_tokens: List[str],
        tags: Optional[List[str]] = None,
    ) -> Dict:
        """
        Deposit a handoff artifact.

        A proprietary structural fingerprint is computed from the provided
        state_tokens and stored under the `structural_hash` key in the
        artifact's metadata. This enables later consumers to assess relevance
        to their current context.
        """
        fingerprint = self._fingerprint_engine.compute_fingerprint(state_tokens)

        meta = {
            "protocol": "ReasonRDN/v1",
            "structural_hash": fingerprint,
            "integrity": "verified",
            # strength is a lightweight diagnostic only; the real power is in the
            # protected correlation method that produced the hash.
            "fingerprint_strength": self._fingerprint_engine.fingerprint_strength(state_tokens),
        }

        final_tags = tags or ["handoff", "ReasonRDN"]
        result = self.client.remember(
            content=summary,
            tags=final_tags,
            project=project,
            meta=meta,
        )
        if isinstance(result, dict):
            result.setdefault("structural_hash", fingerprint)
        return result

    def resolve_handoff(self, project: str) -> Optional[Dict]:
        """
        Return the most recent handoff artifact for the project.

        Callers can inspect the `structural_hash` (and optionally re-compute
        a fingerprint from their own current state tokens using public
        guidance) to decide whether the handoff is still relevant.
        """
        results = self.client.recall(
            query="handoff",
            tags=["ReasonRDN", "handoff"],
            project=project,
            limit=5,
        )

        if not results:
            return None

        return results[0]
