"""
tests/test_coherent_memory.py

Real tests for the coherent unified ReasonRDN memory system (post-restructure).

These exercise the actual stack:
- rdn.node.server (in-process)
- rdn.client.RDNClient (unified, node + local fallback)
- rdn.handoff.ReasonRDN + local artifact hash metadata
- Cross visibility (deposit via high-level, recall/resolve via client)
- HarnessMetrics + public record_handoff/record_recall (for real token accounting
  when using the harness as on-ramp to the external reason:// network)
"""

import tempfile
import os
import threading
import time
import sqlite3

import pytest

from rdn.node.server import PrivateWARFNodeServer, PrivateWARFRequestHandler, default_db_path
from rdn.handoff import ArtifactFingerprint, ReasonRDN
from rdn.client import RDNClient

# Token accounting / harness metrics records for network participation.
from rdn.reason import record_handoff, record_recall, harness_metrics


@pytest.fixture
def in_process_node():
    """Start a real private node in a temp dir and yield (node_url, db_path)."""
    with tempfile.TemporaryDirectory() as td:
        storage = os.path.join(td, "node")
        db_path = default_db_path(storage)
        os.makedirs(storage, exist_ok=True)

        server = PrivateWARFNodeServer(("127.0.0.1", 0), PrivateWARFRequestHandler, db_path=db_path)
        port = server.server_address[1]
        node_url = f"http://127.0.0.1:{port}"

        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        time.sleep(0.25)

        try:
            yield node_url, db_path
        finally:
            try:
                server.shutdown()
                server.server_close()
            except Exception:
                pass
            thread.join(timeout=2)


def test_artifact_fingerprint_basic():
    eng = ArtifactFingerprint()
    tokens = ["main", "src/foo.py", "fix the thing", "Main", "src/foo.py"]
    fp = eng.compute(tokens)
    assert isinstance(fp, str) and len(fp) == 64
    assert eng.verify(tokens, fp) is True
    assert eng.verify(tokens + ["extra"], fp) is False
    assert eng.strength(tokens) == 3


def test_end_to_end_node_handoff_and_resolve(in_process_node):
    node_url, _ = in_process_node

    # High-level deposit via handoff + client -> HTTP node.
    rdn = ReasonRDN(node_url=node_url)
    tokens = ["repo:ReasonRDN", "branch:coherent", "touched:rdn/client.py", "infra-fix"]
    res = rdn.deposit_handoff(
        project="ReasonRDN",
        summary="Made the memory system coherent with a unified client and clean handoff metadata.",
        state_tokens=tokens,
        tags=["infra", "handoff", "coherent"]
    )
    assert res["status"] == "remembered"
    addr = res["address"]
    assert addr.startswith("reason://ReasonRDN/handoff/")

    # Unified client recall (node path)
    c = RDNClient(node_url=node_url)
    results = c.recall(query="coherent", project="ReasonRDN", limit=10)
    assert len(results) >= 1
    assert "coherent" in results[0]["content"].lower()
    assert results[0]["source"] == "node"

    # Resolve (contract is now "artifact")
    art = c.resolve(addr)
    assert art is not None
    assert art["address"] == addr
    assert "artifact_hash" in (art.get("meta") or {})

    eng = ArtifactFingerprint()
    stored = (art["meta"] or {}).get("artifact_hash")
    assert eng.verify(tokens, stored) is True


def test_local_fallback_when_no_node():
    c = RDNClient(node_url="http://127.0.0.1:1")  # will fail health
    c.available = False
    c.node_url = None

    res = c.remember("Pure local path still works", tags=["fallback-test"], project="ReasonRDN")
    assert res["status"] == "remembered"
    assert res["source"] == "local"

    rec = c.recall(query="local path", project="ReasonRDN", limit=5)
    assert len(rec) >= 1
    assert "fallback" in rec[0].get("content", "").lower() or "local" in rec[0].get("content", "").lower()


def test_harness_metrics_record_functions(tmp_path, monkeypatch):
    """Test the public record_handoff / record_recall helpers.

    These ensure that direct/low-level deposit paths (e.g. CLI handoff layer)
    and high-level paths correctly feed HarnessMetrics with tokens_used /
    tokens_saved so the on-ramp can show accurate savings from reason:// artifacts.
    """
    metrics_file = tmp_path / "harness_metrics.json"

    import rdn.reason as reason_mod

    # Point the module at a temp file and recreate the singleton so tests
    # don't touch ~/.reason-rdn and are isolated.
    monkeypatch.setattr(reason_mod, "METRICS_FILE", metrics_file)
    reason_mod._harness_metrics = reason_mod.HarnessMetrics()

    # Start clean
    m0 = reason_mod.harness_metrics()
    assert m0["total_handoffs"] == 0
    assert m0["estimated_tokens_saved"] == 0
    # total_recalls is internal only (not exposed in public summary/harness_metrics())

    # Record a handoff with tokens + "positive" tag (should bump vibe_stars)
    reason_mod.record_handoff(
        "Fixed critical race using prior handoff context",
        tags=["infra", "positive", "coherent"],
        tokens_used=1450,
    )
    m1 = reason_mod.harness_metrics()
    assert m1["total_handoffs"] == 1
    assert m1["estimated_tokens_saved"] == 0
    assert m1["vibe_stars"] >= 1   # from positive tag

    # Record a recall with saved tokens.
    reason_mod.record_recall(
        "reason://ReasonRDN/handoff/abc12345",
        tokens_saved=920,
    )
    m2 = reason_mod.harness_metrics()
    # total_recalls is internal (not in public summary); check via the backing data for the test
    assert reason_mod._harness_metrics.data["total_recalls"] == 1
    assert m2["estimated_tokens_saved"] == 920

    # Summary shape (what status / dashboard / MCP harness_status expose)
    summary = reason_mod.harness_metrics()
    assert "velocity" in summary
    assert "ship_rate" in summary
    assert "suggestions" in summary
    assert "total_handoffs" in summary

    # Also exercise the high-level wrappers (they call the records internally)
    # This path is what `import rdn as reason; reason.remember(..., tokens_used=...)` uses.
    reason_mod.remember("High-level remember with tokens", tokens_used=300, tags=["test"])
    m3 = reason_mod.harness_metrics()
    assert m3["total_handoffs"] == 2

    reason_mod.resolve("reason://test/uri", tokens_saved=150)
    m4 = reason_mod.harness_metrics()
    assert reason_mod._harness_metrics.data["total_recalls"] == 2
    assert m4["estimated_tokens_saved"] == 920 + 150
