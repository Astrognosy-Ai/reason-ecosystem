"""
tests/test_coherent_memory.py

Real tests for the coherent unified ReasonRDN memory system (post-restructure).

These exercise the actual stack:
- rdn.node.server (in-process)
- rdn.client.RDNClient (unified, node + local fallback)
- rdn.handoff.ReasonRDN + PCFEngine (the novel fingerprint handoff layer)
- Cross visibility (deposit via high-level, recall/resolve via client)
- HarnessMetrics + public record_handoff/record_recall (for real token accounting
  when using the harness as on-ramp to the external WARF/Xtend/reason:// flywheel)
"""

import tempfile
import os
import threading
import time
import sqlite3

import pytest

from rdn.node.server import PrivateWARFNodeServer, PrivateWARFRequestHandler, default_db_path
from rdn.handoff import ReasonRDN
from rdn.client import RDNClient
from rdn.handoff.engine import PCFEngine

# New token accounting / harness metrics records (for external WARF/Xtend flywheel participation)
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


def test_pcf_engine_basic():
    eng = PCFEngine()
    tokens = ["main", "src/foo.py", "fix the thing", "Main", "src/foo.py"]
    fp = eng.compute_fingerprint(tokens)
    assert isinstance(fp, str) and len(fp) == 64
    assert eng.verify_fingerprint(tokens, fp) is True
    assert eng.verify_fingerprint(tokens + ["extra"], fp) is False
    assert eng.fingerprint_strength(tokens) == 3  # after normalization/dedup


def test_end_to_end_node_handoff_and_resolve(in_process_node):
    node_url, _ = in_process_node

    # High-level deposit (PCF + client -> HTTP node)
    rdn = ReasonRDN(node_url=node_url)
    tokens = ["repo:ReasonRDN", "branch:coherent", "touched:rdn/client.py", "infra-fix"]
    res = rdn.deposit_handoff(
        project="ReasonRDN",
        summary="Made the memory system actually coherent and novel (unified client + real PCF).",
        state_tokens=tokens,
        tags=["infra", "pcf", "coherent"]
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
    assert "structural_hash" in (art.get("meta") or {})

    # The PCF fingerprint stored in the artifact can be independently verified
    eng = PCFEngine()
    stored = (art["meta"] or {}).get("structural_hash")
    assert eng.verify_fingerprint(tokens, stored) is True


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
    """Test the new public record_handoff / record_recall (added for real
    token accounting across CLI, dash, and MCP when participating in the
    external WARF + Xtend flywheel).

    These ensure that direct/low-level deposit paths (e.g. CLI handoff layer)
    and high-level paths correctly feed HarnessMetrics with tokens_used /
    tokens_saved so the on-ramp can show accurate savings from reason://
    promoted artifacts and nudge users to produce promotable work.
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
        "Fixed critical race using structural correlation for Xtend",
        tags=["infra", "positive", "coherent"],
        tokens_used=1450,
    )
    m1 = reason_mod.harness_metrics()
    assert m1["total_handoffs"] == 1
    assert m1["estimated_tokens_saved"] == 0
    assert m1["vibe_stars"] >= 1   # from positive tag

    # Record a recall with saved tokens (simulating benefit from a promoted
    # external winner on reason://)
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
