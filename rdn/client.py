"""
rdn.client - Unified memory client for the ReasonRDN / WARF ecosystem.

This is the easy, production on-ramp for local-first memory + seamless
federation into the full Astrognosy warf stack.

Architecture (what actually happens on auto-deposit to Xchange):
- Your local RDN / handoff / agent tools deposit here.
- When configured for Xchange (REASON_USE_XCHANGE or node_url = warf.astrognosy.com):
  - Calls go to the Railway reference **broker** (the public Xchange node, Postgres lives here).
  - The broker forwards actual scoring to the **astragnostic-api** (AWS ECS) —
    our domain-agnostic pride-and-joy engine that implements PCF and all its
    variants (structural, semantic, xfer, etc.).
  - After scoring + Xtend quality gate, high-kappa winners can be promoted
    to the reason:// Xport registry for public resolution.

Our local _pcf.py provides a protected, IP-safe structural fingerprint for
local handoffs and basic integrity. The real heavyweight PCF math and
multi-domain implementations live in astragnostic-api (never exposed here).

Features:
- Zero-config local private node + auto Xchange federation
- Explicit broker (warf.astrognosy.com) vs xport (reason.astrognosy.com) awareness. Broker for deposits/arbitration (routes to astragnostic-api), Xport for clean reason:// resolution after promotion.
- High-level xchange_arbitrate, share_to_xchange, resolve_from_xport
- Works great from agents via MCP / CLI or directly
- Full token/auth support for the live stack
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    import requests  # Preferred for robustness
except ImportError:
    requests = None

try:
    from urllib import request as urllib_request
    from urllib import error as urllib_error
    from urllib.parse import quote as url_quote
except Exception:
    urllib_request = None  # type: ignore
    urllib_error = None  # type: ignore
    url_quote = lambda s: s  # type: ignore

logger = logging.getLogger("rdn.client")

DEFAULT_DB_DIR = Path.home() / ".reason-rdn" / "private-node"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "warf-node.db"
PORT_FILE = DEFAULT_DB_DIR / "private-node.port"
CONFIG_FILE = Path.home() / ".reason-ecosystem.cfg"

# The official warf Xchange reference broker (Railway).
# Public front door for deposits, shares, arbitration.
# Forwards scoring + Xtend quality gate (vs current placeholder + corpus for the URI)
# to the grand master astragnostic-api at https://api.pcfic.com (AWS ECS).
# This engine serves workloads for both WARF and Pacific products.
# Use for feeding the collective (Xchange mode).
XCHANGE_BROKER_URL = "https://warf.astrognosy.com"

# Xport / reason:// public registry.
# Primary: https://reason.astrognosy.com and https://xport.astrognosy.com
# Where high-kappa winners (after broker + astragnostic-api + Xtend promotion)
# become the canonical artifact for that exact reason:// URI.
# Use for resolve("reason://...") to get the current best-known reasoning.
XPORT_URL = "https://reason.astrognosy.com"

# Backwards-compatible alias for the broker (the main place you send deposits/shares/arbitration).
XCHANGE_URL = XCHANGE_BROKER_URL

# Convenience alias
REASON_XPORT_URL = XPORT_URL

# Environment variable fallbacks for node URL (order of precedence)
ENV_NODE_KEYS = ("RDN_NODE_URL", "REASON_NODE_URL", "WARF_NODE_URL", "XCHANGE_NODE_URL")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_payload(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def _project_address(project: str, content: str) -> str:
    slug = hashlib.md5(content[:50].encode("utf-8")).hexdigest()[:8]
    return f"reason://{project}/handoff/{slug}"


class RDNClient:
    """
    Unified client for depositing and retrieving ReasonRDN handoff artifacts.

    Prefers a running HTTP node (local embedded or remote). Falls back to local SQLite.
    Both paths produce artifacts with identical shape and integrity fields.
    """

    def __init__(
        self,
        node_url: Optional[str] = None,
        db_path: Optional[str | Path] = None,
        timeout: float = 8.0,
        mirror_local: bool = True,
    ):
        self.timeout = timeout
        self.mirror_local = mirror_local
        self.logger = logger

        # Storage
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self._ensure_local_schema()

        # Node discovery priority (full-stack aware):
        # 1. Explicit node_url param
        # 2. Xchange mode (REASON_USE_XCHANGE=1 etc.) -> Railway broker (warf.astrognosy.com)
        #    Broker forwards PCF scoring to astragnostic-api (AWS ECS, the real engine).
        # 3. Env vars
        # 4. ~/.reason-ecosystem.cfg
        # 5. Local port file
        # 6. Pure local
        self.node_url: Optional[str] = node_url
        self.broker_url: Optional[str] = None
        self.xport_url: Optional[str] = None

        if not self.node_url:
            use_xchange = (
                os.environ.get("REASON_USE_XCHANGE")
                or os.environ.get("USE_WARF_XCHANGE")
                or os.environ.get("REASON_XCHANGE")
                or os.environ.get("XCHANGE")
            )
            if use_xchange and str(use_xchange).lower() not in ("0", "false", "no"):
                self.broker_url = XCHANGE_BROKER_URL
                self.xport_url = XPORT_URL
                self.node_url = self.broker_url  # for simple remember/recall paths

        if not self.node_url:
            for key in ENV_NODE_KEYS:
                val = os.environ.get(key)
                if val:
                    self.node_url = val.rstrip("/")
                    break

        if not self.node_url:
            self.node_url = self._load_node_url_from_config()

        if not self.node_url:
            self.node_url = self._discover_local_node_via_port()

        # If we have explicit broker/xport in config later, they can override. For now single node_url is the main path.

        self.available = False
        if self.node_url:
            self.available = self._check_health()

        # For GUI / advanced features
        self._last_heartbeat_cache: Dict[str, Any] = {}

    # ---------------- Discovery & Health ----------------

    def _discover_local_node_via_port(self) -> Optional[str]:
        try:
            if PORT_FILE.exists():
                port = int(PORT_FILE.read_text(encoding="utf-8").strip())
                if port:
                    return f"http://127.0.0.1:{port}"
        except Exception:
            pass
        return None

    def _load_node_url_from_config(self) -> Optional[str]:
        """Load preferred node_url from ~/.reason-ecosystem.cfg (written by installer)."""
        try:
            if CONFIG_FILE.exists():
                cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                url = cfg.get("node_url")
                if url:
                    return str(url).rstrip("/")
        except Exception:
            pass
        return None

    def _check_health(self) -> bool:
        if not self.node_url:
            return False
        try:
            if requests:
                r = requests.get(f"{self.node_url}/api/health", timeout=self.timeout)
                if r.ok:
                    data = r.json()
                    return data.get("status") == "ok"
            elif urllib_request:
                with urllib_request.urlopen(
                    f"{self.node_url}/api/health", timeout=self.timeout
                ) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    return data.get("status") == "ok"
        except Exception:
            pass
        return False

    def refresh_availability(self) -> bool:
        """Re-probe the node. Useful after starting a private node."""
        if self.node_url:
            self.available = self._check_health()
        else:
            # Try discovery again (node may have just started)
            self.node_url = self._discover_local_node_via_port()
            self.available = self._check_health() if self.node_url else False
        return self.available

    # ---------------- Local Schema (matches node/server.py exactly) ----------------

    def _ensure_local_schema(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS warf_artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    address TEXT NOT NULL UNIQUE,
                    domain TEXT NOT NULL,
                    category TEXT NOT NULL,
                    task TEXT NOT NULL,
                    deposited_at TEXT NOT NULL,
                    audit_hash TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_warf_domain_time ON warf_artifacts(domain, deposited_at DESC)"
            )
            conn.commit()
        finally:
            conn.close()

    def _get_conn(self):
        return sqlite3.connect(str(self.db_path))

    # ---------------- HTTP helpers ----------------

    def _http_get(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        if not self.node_url:
            return None
        try:
            headers = self._auth_headers()
            if requests:
                r = requests.get(url, params=params, headers=headers, timeout=self.timeout)
                r.raise_for_status()
                return r.json()
            elif urllib_request:
                if params:
                    q = "&".join(f"{k}={url_quote(str(v))}" for k, v in params.items())
                    url = f"{url}?{q}"
                req = urllib_request.Request(url)
                for k, v in (headers or {}).items():
                    req.add_header(k, v)
                with urllib_request.urlopen(req, timeout=self.timeout) as resp:
                    return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            self.logger.debug("HTTP GET failed: %s", exc)
            return None

    def _http_post(self, url: str, payload: Dict[str, Any]) -> Optional[Dict]:
        if not self.node_url:
            return None
        try:
            headers = self._auth_headers()
            if requests:
                r = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
                r.raise_for_status()
                return r.json()
            elif urllib_request:
                data = json.dumps(payload).encode("utf-8")
                req = urllib_request.Request(url, data=data, method="POST")
                req.add_header("Content-Type", "application/json")
                for k, v in (headers or {}).items():
                    req.add_header(k, v)
                with urllib_request.urlopen(req, timeout=self.timeout) as resp:
                    return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            self.logger.debug("HTTP POST failed: %s", exc)
            return None

    def _auth_headers(self) -> Dict[str, str]:
        token = (
            os.environ.get("REASON_RDN_TOKEN")
            or os.environ.get("RDN_AUTH_TOKEN")
            or os.environ.get("WARF_API_KEY")
            or os.environ.get("XPORT_API_KEY")
        )
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    # ------------------------------------------------------------------
    # Xchange / reason:// helpers (production bridge to warf.astrognosy.com)
    # ------------------------------------------------------------------

    def resolve_reason_uri(self, uri: str, bypass_cache: bool = False) -> Optional[Dict[str, Any]]:
        """
        Resolve a reason:// URI against an Xchange/Xport-compatible node (e.g. warf.astrognosy.com).

        This is the public-facing, IP-safe resolution path used by the broader WARF/reason ecosystem.
        Returns the artifact (with structural info, provenance, etc.) if the node supports the advanced
        reason:// registry protocol.

        Falls back gracefully if the node only speaks the simpler /api/resolve.
        """
        if not self.node_url:
            return None

        # Try the advanced Xport-style endpoint first (used by the real warf Xchange)
        try:
            from urllib.parse import quote as urlquote
            encoded = urlquote(uri, safe="")
            # The monowarfo/warf nodes support /resolve?address=reason://...
            url = f"{self.node_url}/resolve?address={encoded}"
            if bypass_cache:
                url += "&bypass_cache=true"
            data = self._http_get(url)
            if data:
                return data
        except Exception:
            pass

        # Fallback to our simpler API (local node or compatible Xchange)
        return self.resolve(uri)  # our resolve accepts address too

    def share_to_xchange(
        self,
        content: str,
        uri: Optional[str] = None,
        tags: Optional[List[str]] = None,
        project: str = "astrognosy",
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Deposit an artifact and mark it for the warf Xchange.

        When Xchange mode is active (or node_url points at the broker), this goes
        to the Railway reference broker. The broker will forward scoring to
        astragnostic-api (the domain-agnostic PCF engine on AWS ECS).

        The structural_hash (from our local protected PCF) is included for
        integrity. Full advanced scoring/arbitration happens server-side in the
        astragnostic engine.

        Returns the deposit result.
        """
        if meta is None:
            meta = {}
        if uri:
            meta["reason_uri"] = uri
        meta.setdefault("xchange_share", True)
        meta.setdefault("submitted_via", "reason-ecosystem")

        return self.remember(
            content=content,
            tags=tags or ["handoff", "xchange", "share"],
            project=project,
            meta=meta,
        )

    def xchange_arbitrate(
        self,
        query_text: str,
        packages: List[Dict[str, Any]],
        reason_address: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Submit packages for Xchange arbitration (full flow).

        This is the high-level way to trigger the broker -> astragnostic-api
        scoring pipeline from client code.

        The broker (warf.astrognosy.com on Railway) will:
        - Forward to astragnostic-api (AWS ECS) for real PCF scoring (the domain-agnostic engine)
        - Run Xtend quality gate
        - Potentially promote the winner to the reason:// Xport registry (reason.astrognosy.com)

        packages should be list of dicts with at least 'agent_id' and 'answer_text'.
        (Matches the advanced XchangePackage shape used by the reference broker.)

        Returns the arbitration result (winner, scores, audit_hash, possible promotion info).
        """
        # Use broker if we have it, else current node_url
        target = self.broker_url or self.node_url or XCHANGE_BROKER_URL
        if not target:
            raise RuntimeError("No Xchange broker configured for arbitration.")

        payload = {
            "query_text": query_text,
            "packages": packages,
        }
        if reason_address:
            payload["reason_address"] = reason_address

        # The public broker endpoint for full arbitration (from reference)
        url = f"{target.rstrip('/')}/v1/warf/xchange"
        result = self._http_post(url, payload)
        return result or {"status": "submitted", "target": target}

    def resolve_from_xport(self, uri: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Resolve a reason:// URI from the Xport side (after promotion from Xchange + Xtend).

        Uses the xport_url if configured (reason.astrognosy.com), otherwise falls back.
        This is the public registry path in the full architecture.
        """
        target = self.xport_url or self.node_url or XPORT_URL
        # Try advanced resolve first
        try:
            return self.resolve_reason_uri(uri, **kwargs)
        except Exception:
            # Fallback to simple resolve on the same target
            return self.resolve(uri) if hasattr(self, 'resolve') else None

    def list_prefix(self, prefix: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List artifacts whose address starts with the given prefix (e.g. 'reason://warf'
        or 'warf/build'). Works locally and against a node that supports /api/recall.
        Results are useful for browsing the reason:// namespace with partial URIs.
        """
        if not prefix:
            prefix = "reason://"
        if not prefix.startswith("reason://"):
            prefix = "reason://" + prefix.lstrip("/")

        limit = max(1, min(200, int(limit or 50)))

        # Try remote node first (broad recall + client-side filter)
        if self.node_url and self.available:
            try:
                results = self.recall(query="", limit=limit * 3)
                matches = [r for r in results if (r.get("address") or "").startswith(prefix)]
                return matches[:limit]
            except Exception:
                pass

        # Local fallback
        return self._list_prefix_local(prefix, limit)

    def _list_prefix_local(self, prefix: str, limit: int) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        conn = self._get_conn()
        try:
            conn.row_factory = sqlite3.Row
            sql = """
                SELECT address, domain, deposited_at, metadata_json 
                FROM warf_artifacts 
                WHERE address LIKE ? 
                ORDER BY deposited_at DESC 
                LIMIT ?
            """
            like = prefix + "%"
            rows = conn.execute(sql, (like, limit * 2)).fetchall()

            for row in rows:
                try:
                    meta = json.loads(row["metadata_json"])
                except Exception:
                    meta = {}
                results.append({
                    "address": row["address"],
                    "project": row["domain"],
                    "deposited_at": row["deposited_at"],
                    "content": meta.get("content", ""),
                    "tags": meta.get("tags", []),
                    "structural_hash": meta.get("structural_hash") or meta.get("audit_hash"),
                    "meta": meta,
                    "source": "local",
                })
        except Exception as e:
            logger.error("Local list_prefix failed: %s", e)
        finally:
            conn.close()
        return results[:limit]

    # ---------------- Core Operations ----------------

    def remember(
        self,
        content: str,
        tags: Optional[Iterable[str]] = None,
        project: str = "astrognosy",
        meta: Optional[Dict[str, Any]] = None,
        reason_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Deposit content. Uses HTTP node when available, otherwise local DB.
        Always returns a result with address + artifact_id.
        """
        tags = list(tags) if tags else []
        meta = dict(meta) if meta else {}
        content = (content or "").strip()
        if not content:
            return {"status": "error", "message": "Missing content"}

        project = (project or "unknown").strip()
        reason_address = reason_address or _project_address(project, content)

        # Build canonical metadata (content lives inside metadata_json)
        metadata: Dict[str, Any] = {
            "content": content,
            "tags": [str(t).strip() for t in tags if str(t).strip()],
            "project": project,
            "reason_address": reason_address,
            "stored_at": _now_iso(),
        }
        if meta:
            metadata.update(meta)

        audit_hash = _hash_payload(metadata)
        artifact_id = hashlib.sha1(
            f"{reason_address}:{audit_hash}".encode("utf-8")
        ).hexdigest()
        deposited_at = metadata["stored_at"]

        payload = {
            "content": content,
            "tags": metadata["tags"],
            "project": project,
            "reason_address": reason_address,
            "meta": meta,
        }

        # Prefer node
        if self.node_url and self.available:
            node_res = self._http_post(f"{self.node_url}/api/remember", payload)
            if node_res and node_res.get("status") == "remembered":
                if self.mirror_local:
                    self._remember_local_direct(
                        artifact_id, reason_address, project, deposited_at, audit_hash, metadata
                    )
                    node_res["local_mirrored"] = True
                node_res.setdefault("source", "node")
                return node_res

        # Fallback / mirror path
        return self._remember_local_direct(
            artifact_id, reason_address, project, deposited_at, audit_hash, metadata
        )

    def _remember_local_direct(
        self,
        artifact_id: str,
        address: str,
        domain: str,
        deposited_at: str,
        audit_hash: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        try:
            with self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO warf_artifacts
                    (artifact_id, address, domain, category, task, deposited_at, audit_hash, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        artifact_id,
                        address,
                        domain,
                        "handoff",
                        address.rsplit("/", 1)[-1],
                        deposited_at,
                        audit_hash,
                        json.dumps(metadata, ensure_ascii=True),
                    ),
                )
                conn.commit()
            return {
                "status": "remembered",
                "address": address,
                "artifact_id": artifact_id,
                "project": domain,
                "source": "local",
            }
        except Exception as e:
            logger.error("Local remember failed: %s", e)
            return {"status": "error", "message": str(e)}

    def recall(
        self,
        query: Optional[str] = None,
        tags: Optional[Iterable[str]] = None,
        project: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Search artifacts. When node is healthy, query the node (broad recall) then
        optionally post-filter by tags. Falls back to local DB with substring + tag filter.
        """
        tags = list(tags) if tags else None
        limit = max(1, min(100, int(limit or 20)))

        if self.node_url and self.available:
            params = {"query": query or "", "project": project or "", "limit": limit}
            node_res = self._http_get(f"{self.node_url}/api/recall", params=params)
            if node_res and node_res.get("status") == "ok":
                results = node_res.get("results", []) or []
                if tags:
                    results = [
                        r
                        for r in results
                        if any(t in (r.get("tags") or []) for t in tags)
                        or any(t in (r.get("address") or "") for t in tags)
                    ]
                return results[:limit]

        # Local fallback
        return self._recall_local(query=query, tags=tags, project=project, limit=limit)

    def _recall_local(
        self,
        query: Optional[str],
        tags: Optional[List[str]],
        project: Optional[str],
        limit: int,
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        needle = (query or "").lower().strip()

        conn = self._get_conn()
        try:
            conn.row_factory = sqlite3.Row
            sql = "SELECT address, domain, deposited_at, metadata_json FROM warf_artifacts WHERE 1=1"
            params: List[Any] = []

            if project:
                sql += " AND domain = ?"
                params.append(project)

            # We fetch a bit more then filter in Python for simplicity and correctness
            sql += " ORDER BY deposited_at DESC LIMIT ?"
            params.append(limit * 3)

            rows = conn.execute(sql, params).fetchall()

            for row in rows:
                try:
                    meta = json.loads(row["metadata_json"])
                except Exception:
                    continue

                haystack = " ".join(
                    [
                        row["address"] or "",
                        row["domain"] or "",
                        row["deposited_at"] or "",
                        json.dumps(meta, ensure_ascii=True),
                    ]
                ).lower()

                if needle and needle not in haystack:
                    continue

                if tags:
                    entry_tags = meta.get("tags", []) or []
                    if not any(t in entry_tags for t in tags) and not any(
                        t in (row["address"] or "") for t in tags
                    ):
                        continue

                results.append(
                    {
                        "address": row["address"],
                        "project": row["domain"],
                        "deposited_at": row["deposited_at"],
                        "content": meta.get("content", ""),
                        "tags": meta.get("tags", []),
                        "meta": meta,
                        "source": "local",
                    }
                )
                if len(results) >= limit:
                    break
        except Exception as e:
            logger.error("Local recall failed: %s", e)
        finally:
            conn.close()

        return results

    def resolve(self, address: str) -> Optional[Dict[str, Any]]:
        """Fetch a single artifact by its exact reason:// address."""
        if not address:
            return None

        if self.node_url and self.available:
            res = self._http_get(
                f"{self.node_url}/api/resolve", params={"address": address}
            )
            if res and res.get("status") == "ok":
                # Server now consistently returns "artifact"
                art = res.get("artifact") or res.get("result")
                if art:
                    art.setdefault("source", "node")
                    return art

        # Local
        conn = self._get_conn()
        try:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT address, domain, deposited_at, metadata_json FROM warf_artifacts WHERE address = ?",
                (address,),
            ).fetchone()
            if not row:
                return None
            meta = json.loads(row["metadata_json"])
            return {
                "address": row["address"],
                "project": row["domain"],
                "deposited_at": row["deposited_at"],
                "content": meta.get("content", ""),
                "tags": meta.get("tags", []),
                "meta": meta,
                "source": "local",
            }
        except Exception as e:
            logger.error("Local resolve failed: %s", e)
            return None
        finally:
            conn.close()

    # ---------------- GUI / Advanced helpers (heartbeat, recent projects) ----------------

    def get_heartbeat(self, project: Optional[str] = None) -> str:
        """ASCII sparkline of activity over the last 7 days (░ ▒ ▓ █)."""
        try:
            if self.node_url and self.available:
                # Ask for a broad recent set
                node_results = self._http_get(
                    f"{self.node_url}/api/recall",
                    params={"query": "handoff", "project": project or "", "limit": 300},
                )
                entries = (node_results or {}).get("results", []) if node_results else []
            else:
                entries = []

            if not entries:
                # local fallback
                conn = self._get_conn()
                try:
                    conn.row_factory = sqlite3.Row
                    sql = "SELECT deposited_at FROM warf_artifacts WHERE deposited_at > date('now', '-7 days')"
                    p = []
                    if project:
                        sql += " AND domain = ?"
                        p.append(project)
                    rows = conn.execute(sql, p).fetchall()
                    entries = [{"deposited_at": r["deposited_at"]} for r in rows]
                finally:
                    conn.close()

            counts: Dict[str, int] = {}
            for e in entries:
                ts = e.get("deposited_at", "")
                day = (ts or "")[:10]
                if day:
                    counts[day] = counts.get(day, 0) + 1

            spark = ""
            for i in range(6, -1, -1):
                day = (datetime.now(timezone.utc).date() - __import__("datetime").timedelta(days=i)).isoformat()
                c = counts.get(day, 0)
                if c == 0:
                    spark += "░"
                elif c < 3:
                    spark += "▒"
                elif c < 6:
                    spark += "▓"
                else:
                    spark += "█"
            return spark
        except Exception:
            return "░░░░░░░"

    def get_recent_projects(self, limit: int = 10) -> List[str]:
        """Most recently active projects (domains)."""
        try:
            if self.node_url and self.available:
                res = self._http_get(
                    f"{self.node_url}/api/recall",
                    params={"query": "", "project": "", "limit": 200},
                )
                entries = (res or {}).get("results", []) if res else []
                seen: set[str] = set()
                projects: List[str] = []
                for e in entries:
                    p = e.get("project") or e.get("domain")
                    if p and p not in seen:
                        seen.add(p)
                        projects.append(p)
                        if len(projects) >= limit:
                            break
                if projects:
                    return projects
            # local
            conn = self._get_conn()
            try:
                rows = conn.execute(
                    "SELECT DISTINCT domain FROM warf_artifacts ORDER BY deposited_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                return [r[0] for r in rows if r[0]]
            finally:
                conn.close()
        except Exception:
            return ["astrognosy"]

    # ---------------- Convenience ----------------

    def __repr__(self) -> str:
        return f"<RDNClient node={self.node_url or 'local'} available={self.available} db={self.db_path}>"
