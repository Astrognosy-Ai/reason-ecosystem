"""
rdn — The Coherent Reason Substrate (local + full warf Xchange stack)

One clean package that unifies:
- Local-first handoffs & repo memory (the original ReasonRDN strengths)
- Auto-deposit to the warf Xchange broker (warf.astrognosy.com on Railway)
- Real PCF scoring in astragnostic-api (AWS ECS — the domain-agnostic engine)
- Clean resolution from the reason:// Xport registry (reason.astrognosy.com)

The simplest coherent API (this is what agents and humans should reach for):

    import rdn as reason
    reason.remember("Fixed the race with structural correlation", tags=["infra"])
    art = reason.resolve("reason://ops/ecs/failures")
    result = reason.xchange_arbitrate("best approach?", packages=[...])

PCF math is fully protected (safe local fingerprints here + the real engine lives in astragnostic-api).
"""

from __future__ import annotations

__version__ = "0.4.0"  # IP-protected coherent substrate

from .client import (
    RDNClient,
    XCHANGE_URL,
    XCHANGE_BROKER_URL,
    XPORT_URL,
    REASON_XPORT_URL,
)
from .handoff.protocol import ReasonRDN
from .reason import (
    Reason,           # THE coherent high-level object
    remember,         # module-level simplest API
    resolve,
    list_prefix,
    xchange_arbitrate,
    status,
    harness_metrics,
    record_handoff,
    record_recall,
    ReasonClient,
    WARFClient,
)
from .node.server import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_STORAGE_DIR,
    port_file_path,
    default_db_path,
    serve,
    main as node_main,
)

__all__ = [
    "RDNClient",
    "ReasonRDN",
    "Reason",
    "remember",
    "resolve",
    "list_prefix",
    "add_recent_uri",
    "get_recent_uris",
    "xchange_arbitrate",
    "status",
    "harness_metrics",
    "record_handoff",
    "record_recall",
    "ReasonClient",
    "WARFClient",
    "XCHANGE_URL",
    "XCHANGE_BROKER_URL",
    "XPORT_URL",
    "REASON_XPORT_URL",
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "DEFAULT_STORAGE_DIR",
    "port_file_path",
    "default_db_path",
    "serve",
    "node_main",
]
