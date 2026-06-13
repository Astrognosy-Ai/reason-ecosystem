from rdn.network.client import RDNClient


class DummyResponse:
    def __init__(self, payload=None, raise_json=False):
        self._payload = payload
        self._raise_json = raise_json

    def raise_for_status(self):
        return None

    def json(self):
        if self._raise_json:
            raise ValueError("invalid json")
        return self._payload


def test_node_request_invalid_json_returns_none(monkeypatch):
    client = RDNClient(node_url="http://localhost:8765")
    monkeypatch.setattr(
        "rdn.network.client.requests.request",
        lambda *args, **kwargs: DummyResponse(raise_json=True),
    )

    assert client._node_request("GET", "/api/health") is None


def test_remember_falls_back_to_local_on_node_error(monkeypatch):
    client = RDNClient(node_url="http://localhost:8765")
    monkeypatch.setattr(client, "_node_request", lambda *args, **kwargs: {"status": "error"})
    monkeypatch.setattr(
        client,
        "_remember_local",
        lambda *args, **kwargs: {"status": "remembered", "source": "local", "address": "reason://x/y/z"},
    )

    result = client.remember("hello", ["handoff"], "astrognosy")
    assert result["status"] == "remembered"
    assert result["source"] == "local"


def test_recall_node_ignores_invalid_entries(monkeypatch):
    client = RDNClient(node_url="http://localhost:8765")
    monkeypatch.setattr(
        client,
        "_node_request",
        lambda *args, **kwargs: {
            "results": [
                {"address": "reason://a/handoff/1", "project": "a", "tags": ["handoff"], "content": "ok"},
                "bad-entry",
                {"address": "reason://b/handoff/2", "project": "b", "tags": ["other"], "content": "skip"},
            ]
        },
    )

    results = client._recall_node(query="handoff", tags=["handoff"], project=None, limit=10)
    assert len(results) == 1
    assert results[0]["address"] == "reason://a/handoff/1"
    assert results[0]["source"] == "node"
