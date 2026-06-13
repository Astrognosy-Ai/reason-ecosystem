"""
rdn.reason — THE coherent, simplified high-level API for the entire stack.

This is the "one thing" you (and agents) should use.

It unifies:
- Local ReasonRDN handoffs (repo state, decisions, insights)
- Seamless auto-deposit to the warf Xchange broker (warf.astrognosy.com)
- Routing through astragnostic-api for real PCF scoring (protected)
- Resolution from the reason:// Xport registry (reason.astrognosy.com)

All PCF math stays hidden. Only safe structural fingerprints + content are exposed.

Usage (the simple coherent way):
    import rdn.reason as reason

    reason.remember("Fixed the race using structural correlation...", tags=["infra"])
    artifact = reason.resolve("reason://ops/deployment/ecs-failures")   # hits Xport when Xchange mode
    result = reason.xchange_arbitrate("best fix for X?", packages=[...])

Or the full client:
    from rdn.reason import Reason
    r = Reason(xchange=True)
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .client import RDNClient, XPORT_URL, XCHANGE_BROKER_URL

# Simple persistent metrics for the agnostic harness
METRICS_FILE = Path.home() / ".reason-rdn" / "harness_metrics.json"

class HarnessMetrics:
    """Lightweight, local-first metrics tracker for the reason harness.
    Tracks token savings estimates, velocity (handoffs/time), ship rate, vibe stars, etc.
    Agnostic to specific agents/models — works across the stack.
    """
    def __init__(self):
        self.path = METRICS_FILE
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self) -> Dict:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text())
            except Exception:
                pass
        return {
            "total_handoffs": 0,
            "total_recalls": 0,
            "estimated_tokens_saved": 0,  # rough: each recall vs full re-reason ~1500-4000 tokens
            "sessions": 0,
            "vibe_stars": 0,  # fun positive signal metric
            "last_activity": None,
            "workflow_suggestions": [],
        }

    def _save(self):
        self.path.write_text(json.dumps(self.data, indent=2))

    def record_handoff(self, content: str, tags: List[str] = None, tokens_used: int = None):
        self.data["total_handoffs"] += 1
        self.data["last_activity"] = datetime.utcnow().isoformat()
        if tags and "positive" in [t.lower() for t in tags]:
            self.data["vibe_stars"] += 1
        if tokens_used:
            # Record the cost of creating this high-quality artifact
            self.data.setdefault("tokens_invested", 0)
            self.data["tokens_invested"] += tokens_used
        self._save()

    def record_recall(self, query: str, tokens_saved: int = None):
        self.data["total_recalls"] += 1
        if tokens_saved:
            self.data["estimated_tokens_saved"] += tokens_saved
        else:
            # Fallback rough estimate only when agents don't report real numbers
            self.data["estimated_tokens_saved"] += 2200
        self.data["last_activity"] = datetime.utcnow().isoformat()
        self._save()

    def record_xchange_share(self):
        self.data["vibe_stars"] += 2  # sharing to collective is high vibe
        self._save()

    def get_velocity(self) -> float:
        """Handoffs per active day (very approximate)."""
        if not self.data["last_activity"]:
            return 0.0
        # simplistic
        return round(self.data["total_handoffs"] / max(1, (self.data["total_recalls"] or 1) / 5), 1)

    def get_ship_rate(self) -> float:
        """% of handoffs that led to recalls (proxy for usefulness)."""
        if self.data["total_handoffs"] == 0:
            return 0.0
        return round((self.data["total_recalls"] / self.data["total_handoffs"]) * 100, 1)

    def get_suggestions(self) -> List[str]:
        suggestions = []
        if self.data["total_recalls"] > 5 and self.data["estimated_tokens_saved"] > 10000:
            suggestions.append("High recall rate — you are benefiting from prior external winners. Consider Xchange share with a precise reason:// URI so a strong new artifact can compete under Xtend to become the new canonical for that URI.")
        if self.data["vibe_stars"] > 3:
            suggestions.append("Strong positive signal! Ship high-signal structured handoffs via Xchange (with reason:// URI when possible) so they can win Xtend promotion in the external WARF network.")
        if self.get_ship_rate() < 20:
            suggestions.append("Ship rate low — add more structured state_tokens in handoffs. This improves local recall precision and gives artifacts a better chance in external Xtend comparisons against the current placeholder + corpus for a URI.")
        self.data["workflow_suggestions"] = suggestions[:3]
        self._save()
        return self.data["workflow_suggestions"]

    def summary(self) -> Dict:
        return {
            "estimated_tokens_saved": self.data["estimated_tokens_saved"],
            "velocity": self.get_velocity(),
            "ship_rate": self.get_ship_rate(),
            "vibe_stars": self.data["vibe_stars"],
            "total_handoffs": self.data["total_handoffs"],
            "suggestions": self.get_suggestions(),
        }

_harness_metrics = HarnessMetrics()


# The single coherent high-level namespace (what agents and humans should reach for)
class Reason:
    """
    One coherent object for local + full warf/Xchange/Xport stack.

    Automatically handles the split:
    - Broker (warf.astrognosy.com) for deposits and arbitration (triggers astragnostic)
    - Xport (reason.astrognosy.com) for clean reason:// resolution
    """

    def __init__(self, xchange: bool = False):
        self._client = RDNClient()
        self._xchange_mode = xchange or bool(os.environ.get("REASON_USE_XCHANGE"))
        if self._xchange_mode:
            self._client.broker_url = XCHANGE_BROKER_URL
            self._client.xport_url = XPORT_URL
            self._client.node_url = XCHANGE_BROKER_URL

    def remember(self, content: str, **kwargs) -> Dict[str, Any]:
        """Unified deposit. Goes to Xchange broker when in Xchange mode."""
        if self._xchange_mode:
            return self._client.share_to_xchange(content, **kwargs)
        return self._client.remember(content, **kwargs)

    def resolve(self, uri_or_address: str) -> Optional[Dict[str, Any]]:
        """Smart resolve. Prefers Xport for reason:// URIs when Xchange mode is on."""
        if self._xchange_mode and uri_or_address.startswith("reason://"):
            return self._client.resolve_from_xport(uri_or_address)
        return self._client.resolve(uri_or_address)

    def xchange_arbitrate(self, query_text: str, packages: List[Dict[str, Any]], **kwargs):
        if not self._xchange_mode:
            raise RuntimeError("Enable Xchange mode (REASON_USE_XCHANGE=1 or Reason(xchange=True))")
        return self._client.xchange_arbitrate(query_text, packages, **kwargs)

    def list_prefix(self, prefix: str, limit: int = 20):
        """List artifacts under a reason:// prefix (great for browsing with partial URIs)."""
        return self._client.list_prefix(prefix, limit=limit)

    @property
    def status(self):
        return {
            "xchange_mode": self._xchange_mode,
            "broker": getattr(self._client, "broker_url", None),
            "xport": getattr(self._client, "xport_url", None),
            "local_available": self._client.available,
        }


# Back-compat + advanced SDK bridge (thin, safe)
class ReasonClient(Reason):
    """Xport-focused client (for resolution of promoted reason:// artifacts)."""
    def __init__(self, endpoint: str = XPORT_URL, **kwargs):
        super().__init__(xchange=False)
        # Override for pure Xport resolution
        self._client.xport_url = endpoint
        self._client.node_url = endpoint


class WARFClient(Reason):
    """Broker-focused client (for deposits + full arbitration that hits astragnostic)."""
    def __init__(self, broker_endpoint: str = XCHANGE_BROKER_URL, **kwargs):
        super().__init__(xchange=True)
        self._client.broker_url = broker_endpoint
        self._client.node_url = broker_endpoint


# Module-level convenience (the "simplest coherent API")
_default_reason = None

def _get_default():
    global _default_reason
    if _default_reason is None:
        _default_reason = Reason(xchange=bool(os.environ.get("REASON_USE_XCHANGE")))
    return _default_reason

def remember(content: str, tokens_used: int = None, **kwargs):
    """Coherent remember. Pass tokens_used=1234 for accurate harness accounting."""
    res = _get_default().remember(content, **kwargs)
    _harness_metrics.record_handoff(content, kwargs.get("tags"), tokens_used=tokens_used)
    if kwargs.get("xchange_share") or os.environ.get("REASON_USE_XCHANGE"):
        _harness_metrics.record_xchange_share()
    return res

def resolve(uri_or_address: str, tokens_saved: int = None):
    """Coherent resolve. Pass tokens_saved=... (from the agent) for real metrics."""
    res = _get_default().resolve(uri_or_address)
    _harness_metrics.record_recall(str(uri_or_address), tokens_saved=tokens_saved)
    return res

def xchange_arbitrate(query_text: str, packages: List[Dict[str, Any]], **kwargs):
    res = _get_default().xchange_arbitrate(query_text, packages, **kwargs)
    _harness_metrics.record_xchange_share()
    return res

def status():
    base = _get_default().status
    base.update(_harness_metrics.summary())
    base["recent_uris"] = get_recent_uris()
    # Top level prefixes from recent for quick visibility
    prefixes = set()
    for u in get_recent_uris()[:5]:
        if u.startswith("reason://"):
            parts = u[len("reason://"):].split("/")
            if parts:
                prefixes.add("reason://" + parts[0])
    base["top_prefixes"] = sorted(list(prefixes))[:5]
    return base

def harness_metrics():
    """Direct access to the agnostic harness metrics (tokens, velocity, suggestions, etc)."""
    return _harness_metrics.summary()


def list_prefix(prefix: str, limit: int = 20):
    """List artifacts currently registered under a reason:// prefix.
    Example: list_prefix("reason://warf") or list_prefix("warf") returns
    all known URIs starting with that prefix. Useful for autocomplete / browsing.
    """
    return _get_default().list_prefix(prefix, limit=limit)


# Recent URIs for quick access / persistence across sessions
RECENT_URIS_FILE = Path.home() / ".reason-rdn" / "recent_uris.json"

def _load_recent_uris():
    if RECENT_URIS_FILE.exists():
        try:
            data = json.loads(RECENT_URIS_FILE.read_text())
            return [u for u in data if isinstance(u, str) and u.startswith("reason://")][:10]
        except Exception:
            pass
    return []

def _save_recent_uris(uris):
    RECENT_URIS_FILE.parent.mkdir(parents=True, exist_ok=True)
    RECENT_URIS_FILE.write_text(json.dumps(uris, indent=2))

_recent_uris = _load_recent_uris()

def add_recent_uri(uri: str):
    """Add a reason:// URI to the recent list (for quick access in dashboard/CLI)."""
    global _recent_uris
    if uri and uri.startswith("reason://"):
        if uri in _recent_uris:
            _recent_uris.remove(uri)
        _recent_uris.insert(0, uri)
        _recent_uris = _recent_uris[:10]
        _save_recent_uris(_recent_uris)

def get_recent_uris():
    """Return the list of recently used reason:// URIs."""
    return list(_recent_uris)


# Public record helpers for direct paths (CLI direct deposits, etc) so token accounting
# works without double-submitting artifacts. The high-level remember/resolve already use these.
def record_handoff(content: str, tags: List[str] = None, tokens_used: int = None):
    """Record a handoff for harness metrics (tokens invested, vibe, etc).
    Use this from direct deposit paths (e.g. CLI using low-level handoff) to ensure
    accurate token accounting without re-performing the remember.
    Also used internally by the high-level remember/resolve wrappers.
    """
    _harness_metrics.record_handoff(content, tags, tokens_used)


def record_recall(query: str, tokens_saved: int = None):
    """Record a recall for harness metrics (tokens saved).
    Use this from direct recall/resolve paths to ensure accurate savings numbers.
    """
    _harness_metrics.record_recall(query, tokens_saved)


# Thin shims for people coming from the advanced reason_py SDK (safe, no PCF exposure)
class ReasonClient(Reason):
    """Xport-focused (defaults to reason.astrognosy.com for resolution)."""
    def __init__(self, endpoint: str = None, **kwargs):
        super().__init__(xchange=False)
        if endpoint:
            self._client.xport_url = endpoint
            self._client.node_url = endpoint


class WARFClient(Reason):
    """Broker-focused (for deposits/arbitration that route to astragnostic-api)."""
    def __init__(self, broker_endpoint: str = None, **kwargs):
        super().__init__(xchange=True)
        if broker_endpoint:
            self._client.broker_url = broker_endpoint
            self._client.node_url = broker_endpoint
