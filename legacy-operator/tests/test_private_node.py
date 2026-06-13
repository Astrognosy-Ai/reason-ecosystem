import json
import threading
from urllib.request import Request, urlopen

from rdn.node.server import PrivateWARFNodeServer, PrivateWARFRequestHandler


def _start_node(tmp_path):
    db_path = tmp_path / "node" / "warf-node.db"
    server = PrivateWARFNodeServer(("127.0.0.1", 0), PrivateWARFRequestHandler, db_path=str(db_path))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def _request_json(url, method="GET", payload=None):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(url, data=data, headers=headers, method=method)
    with urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def test_private_node_remember_recall_and_resolve(tmp_path):
    server, thread = _start_node(tmp_path)
    base_url = f"http://127.0.0.1:{server.server_address[1]}"

    try:
        health = _request_json(f"{base_url}/api/health")
        assert health["status"] == "ok"

        remember = _request_json(
            f"{base_url}/api/remember",
            method="POST",
            payload={
                "content": "Implemented the private node",
                "tags": ["handoff", "ReasonRDN"],
                "project": "astrognosy",
                "reason_address": "reason://astrognosy/handoff/abc12345",
                "meta": {"protocol": "ReasonRDN/v1"},
            },
        )
        assert remember["status"] == "remembered"

        recall = _request_json(f"{base_url}/api/recall?query=private&project=astrognosy&limit=10")
        assert recall["status"] == "ok"
        assert recall["results"]
        assert recall["results"][0]["address"] == "reason://astrognosy/handoff/abc12345"

        resolve = _request_json(f"{base_url}/api/resolve?address=reason://astrognosy/handoff/abc12345")
        assert resolve["status"] == "ok"
        assert resolve["result"]["content"] == "Implemented the private node"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
