"""
warf_ecosystem_client.py

Unified HTTP memory client for warf-mcp to talk to ReasonRDN's embedded node.

Supports:
  - Local discovery (via ~/.reason-rdn/private-node/private-node.port)
  - Remote node (via REASON_NODE_URL env var or config)
  - Fallback to local SQLite

Example usage:
    from warf_ecosystem_client import EcosystemMemory
    
    mem = EcosystemMemory()  # auto-discovers node
    mem.remember("My insight", tags=["ai", "reasoning"], project="astrognosy")
    results = mem.recall("insight", limit=5)
    resolved = mem.resolve("reason://astrognosy/handoff/abc123")
"""

from __future__ import annotations
import json
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Optional

try:
    import urllib.request
    import urllib.error
except ImportError:
    urllib = None


class EcosystemMemory:
    """
    HTTP client for ReasonRDN's embedded node or remote WARF node.
    Falls back to local SQLite if node is unavailable.
    """
    
    def __init__(self, node_url: str | None = None):
        self.home = Path.home()
        self.storage_dir = self.home / ".reason-rdn" / "private-node"
        self.local_db = self.home / ".reason-rdn" / "private-node" / "warf-node.db"
        
        # Detect node URL: env var > config file > local discovery > None
        self.node_url = node_url or os.environ.get("REASON_NODE_URL")
        
        if not self.node_url:
            self.node_url = self._discover_local_node()
        
        # Ensure local DB schema
        self._ensure_local_schema()
        
        self.available = False
        if self.node_url:
            # Quick health check
            try:
                health = self._http_get(f"{self.node_url}/api/health")
                if health and health.get("status") == "ok":
                    self.available = True
            except Exception:
                pass
    
    def _discover_local_node(self) -> str | None:
        """Discover local node by reading port file."""
        port_file = self.storage_dir / "private-node.port"
        if port_file.exists():
            try:
                port = int(port_file.read_text(encoding="utf-8").strip())
                return f"http://127.0.0.1:{port}"
            except Exception:
                pass
        return None
    
    def _ensure_local_schema(self):
        """Ensure local fallback DB has correct schema (matches rdn/node/server.py)."""
        self.local_db.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.local_db))
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS warf_artifacts (
                artifact_id TEXT PRIMARY KEY,
                address TEXT NOT NULL UNIQUE,
                domain TEXT NOT NULL,
                category TEXT NOT NULL,
                task TEXT NOT NULL,
                deposited_at TEXT NOT NULL,
                audit_hash TEXT NOT NULL,
                metadata_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_warf_domain_time ON warf_artifacts(domain, deposited_at DESC);
        """)
        conn.commit()
        conn.close()
    
    def _http_get(self, url: str) -> dict | None:
        """GET request helper."""
        if not urllib:
            return None
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = resp.read().decode("utf-8")
                return json.loads(data)
        except (urllib.error.URLError, json.JSONDecodeError, Exception):
            return None
    
    def _http_post(self, url: str, payload: dict) -> dict | None:
        """POST request helper."""
        if not urllib:
            return None
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, method="POST")
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=5) as resp:
                respdata = resp.read().decode("utf-8")
                return json.loads(respdata)
        except (urllib.error.URLError, json.JSONDecodeError, Exception):
            return None
    
    def remember(
        self,
        content: str,
        tags: list[str] | None = None,
        project: str = "astrognosy",
        reason_address: str | None = None,
        meta: dict | None = None,
    ) -> dict:
        """
        Deposit content to memory (node if available, else local DB).
        Returns result dict with address and artifact_id.
        """
        if tags is None:
            tags = []
        if meta is None:
            meta = {}
        
        payload = {
            "content": content,
            "tags": tags,
            "project": project,
            "reason_address": reason_address,
            "meta": meta,
        }
        
        # Try HTTP node first
        if self.node_url and self.available:
            try:
                result = self._http_post(f"{self.node_url}/api/remember", payload)
                if result and result.get("status") == "remembered":
                    return result
            except Exception:
                pass
        
        # Fallback to local DB
        return self._remember_local(payload)
    
    def _remember_local(self, payload: dict) -> dict:
        """Store in local DB (matches rdn/node/server.py format)."""
        import hashlib
        
        content = str(payload.get("content", "")).strip()
        tags = payload.get("tags", [])
        project = str(payload.get("project", "")).strip() or "unknown"
        reason_address = payload.get("reason_address")
        if not reason_address:
            task_slug = hashlib.md5(content[:50].encode("utf-8")).hexdigest()[:8]
            reason_address = f"reason://{project}/handoff/{task_slug}"
        
        # Build metadata (content stored here, not separate column)
        metadata = {
            "content": content,
            "tags": [str(tag) for tag in tags if str(tag).strip()],
            "project": project,
            "reason_address": reason_address,
            "stored_at": datetime.now(timezone.utc).isoformat(),
        }
        if isinstance(payload.get("meta"), dict):
            metadata.update(payload["meta"])
        
        audit_hash = hashlib.sha256(json.dumps(metadata, sort_keys=True, ensure_ascii=True).encode("utf-8")).hexdigest()
        artifact_id = hashlib.sha1(f"{reason_address}:{audit_hash}".encode("utf-8")).hexdigest()
        task_slug = reason_address.rsplit("/", 1)[-1]
        deposited_at = metadata["stored_at"]
        
        conn = sqlite3.connect(str(self.local_db))
        conn.execute(
            """INSERT OR REPLACE INTO warf_artifacts 
               (artifact_id, address, domain, category, task, deposited_at, audit_hash, metadata_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                artifact_id,
                reason_address,
                project,
                "memory",
                task_slug,
                deposited_at,
                audit_hash,
                json.dumps(metadata, ensure_ascii=True),
            ),
        )
        conn.commit()
        conn.close()
        
        return {
            "status": "remembered",
            "address": reason_address,
            "artifact_id": artifact_id,
            "project": project,
            "source": "local",
        }
    
    def recall(
        self,
        query: str,
        project: str = "astrognosy",
        limit: int = 10,
    ) -> list[dict]:
        """
        Search memory (node if available, else local DB).
        Returns list of matching artifacts.
        """
        # Try HTTP node first
        if self.node_url and self.available:
            try:
                result = self._http_get(
                    f"{self.node_url}/api/recall?query={urllib.parse.quote(query)}&project={project}&limit={limit}"
                )
                if result and result.get("status") == "ok":
                    return result.get("results", [])
            except Exception:
                pass
        
        # Fallback to local DB
        return self._recall_local(query, project, limit)
    
    def _recall_local(self, query: str, project: str, limit: int) -> list[dict]:
        """Search local DB (simple substring match on metadata)."""
        conn = sqlite3.connect(str(self.local_db))
        cursor = conn.cursor()
        cursor.execute(
            """SELECT artifact_id, address, domain, category, task, deposited_at, audit_hash, metadata_json
               FROM warf_artifacts
               WHERE domain = ? AND (metadata_json LIKE ?)
               ORDER BY deposited_at DESC LIMIT ?""",
            (project, f"%{query}%", limit),
        )
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            try:
                meta = json.loads(row[7])
            except (json.JSONDecodeError, TypeError):
                meta = {}
            
            results.append({
                "artifact_id": row[0],
                "address": row[1],
                "domain": row[2],
                "category": row[3],
                "task": row[4],
                "deposited_at": row[5],
                "audit_hash": row[6],
                "content": meta.get("content", ""),
                "tags": meta.get("tags", []),
                "meta": meta,
                "source": "local",
            })
        return results
    
    def resolve(self, address: str) -> dict | None:
        """
        Fetch a single artifact by address.
        Returns artifact dict or None if not found.
        """
        # Try HTTP node first
        if self.node_url and self.available:
            try:
                result = self._http_get(f"{self.node_url}/api/resolve?address={urllib.parse.quote(address)}")
                if result and result.get("status") == "ok":
                    return result.get("artifact")
            except Exception:
                pass
        
        # Fallback to local DB
        return self._resolve_local(address)
    
    def _resolve_local(self, address: str) -> dict | None:
        """Fetch single artifact from local DB by address."""
        conn = sqlite3.connect(str(self.local_db))
        cursor = conn.cursor()
        cursor.execute(
            """SELECT artifact_id, address, domain, category, task, deposited_at, audit_hash, metadata_json
               FROM warf_artifacts
               WHERE address = ?""",
            (address,),
        )
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        try:
            meta = json.loads(row[7])
        except (json.JSONDecodeError, TypeError):
            meta = {}
        
        return {
            "artifact_id": row[0],
            "address": row[1],
            "domain": row[2],
            "category": row[3],
            "task": row[4],
            "deposited_at": row[5],
            "audit_hash": row[6],
            "content": meta.get("content", ""),
            "tags": meta.get("tags", []),
            "meta": meta,
            "source": "local",
        }


if __name__ == "__main__":
    # Quick smoke test
    mem = EcosystemMemory()
    print(f"Node available: {mem.available}")
    print(f"Node URL: {mem.node_url}")
    print(f"Local DB: {mem.local_db}")
    
    # Test remember/recall
    mem.remember("smoke test", tags=["test"], project="test")
    results = mem.recall("smoke", project="test", limit=5)
    print(f"Recalled {len(results)} results")
