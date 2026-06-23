"""
rdn — The Coherent reason:// Substrate

One clean, local-first package that unifies:
- Persistent handoffs and project memory with a simple API
- Optional participation in the public reason:// Xchange network
- Local artifact integrity metadata
- Clean resolution from the reason:// Xport registry

The simplest coherent API agents and humans should reach for:

    import rdn as reason
    reason.remember("Fixed the race with prior handoff context", tags=["infra"])
    art = reason.resolve("reason://ops/ecs/failures")

This package is the open public on-ramp to the reason:// ecosystem.
"""

from __future__ import annotations

__version__ = "0.4.0"

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
