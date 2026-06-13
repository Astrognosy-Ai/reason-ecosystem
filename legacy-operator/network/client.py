"""
rdn/network/client.py -- Direct WARF Database Client for ReasonRDN
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

import requests


class RDNClient:
    """
    Client for interacting with a WARF node and/or local WARF memory.db.
    """
    def __init__(
        self,
        db_path: Optional[str] = None,
        node_url: Optional[str] = None,
        mirror_local: Optional[bool] = None,
        timeout: float = 10.0,
    ):
        # Default to standard user WARF path if not provided
        self.db_path = db_path or os.path.expanduser("~/.warf/memory.db")
        self.node_url = (node_url or os.environ.get("RDN_NODE_URL") or os.environ.get("WARF_NODE_URL"))
        if self.node_url:
            self.node_url = self.node_url.rstrip("/")
        self.mirror_local = True if mirror_local is None else mirror_local
        self.timeout = timeout
        self.logger = logging.getLogger("rdn.network")
        
        if not os.path.exists(self.db_path):
            self.logger.warning(f"WARF database not found at {self.db_path}")

    def _get_conn(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        return sqlite3.connect(self.db_path)

    def _node_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        if not self.node_url:
            return None
        try:
            resp = requests.request(
                method,
                f"{self.node_url}{path}",
                params=params,
                json=json_body,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            try:
                payload = resp.json()
            except ValueError:
                self.logger.warning("WARF node response was not valid JSON")
                return None
            if not isinstance(payload, dict):
                self.logger.warning("WARF node response JSON was not an object")
                return None
            return payload
        except requests.RequestException as exc:
            self.logger.warning(f"WARF node request failed: {exc}")
            return None

    def _remember_local(self, content: str, tags: List[str], project: str, meta: Optional[Dict] = None) -> Dict:
        artifact_id = uuid.uuid4().hex
        deposited_at = datetime.now(timezone.utc).isoformat()

        # ReasonRDN addresses follow the reason://<project>/handoff/<slug> pattern
        task_slug = hashlib.md5(content[:50].encode()).hexdigest()[:8]
        address = f"reason://{project}/handoff/{task_slug}"

        metadata = {
            "content": content,
            "tags": tags,
            "project": project
        }
        if meta:
            metadata.update(meta)

        metadata_json = json.dumps(metadata)
        audit_hash = hashlib.sha256(metadata_json.encode()).hexdigest()

        try:
            with self._get_conn() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO warf_artifacts 
                    (artifact_id, address, domain, category, task, deposited_at, audit_hash, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (artifact_id, address, project, "handoff", task_slug, deposited_at, audit_hash, metadata_json))
                conn.commit()
            return {"status": "remembered", "address": address, "artifact_id": artifact_id, "source": "local"}
        except Exception as e:
            self.logger.error(f"Direct DB deposit failed: {e}")
            return {"status": "error", "message": str(e)}

    def remember(self, content: str, tags: List[str], project: str, meta: Optional[Dict] = None) -> Dict:
        """
        Deposit reasoning into a WARF node or local WARF memory.db.
        """
        task_slug = hashlib.md5(content[:50].encode()).hexdigest()[:8]
        address = f"reason://{project}/handoff/{task_slug}"

        if self.node_url:
            payload = {
                "content": content,
                "tags": tags,
                "project": project,
                "reason_address": address,
            }
            node_result = self._node_request("POST", "/api/remember", json_body=payload)
            if node_result is not None and node_result.get("status") != "error":
                if self.mirror_local:
                    local_result = self._remember_local(content, tags, project, meta=meta)
                    node_result["local_status"] = local_result.get("status")
                node_result.setdefault("status", "remembered")
                node_result.setdefault("address", address)
                node_result["source"] = "node"
                return node_result

        return self._remember_local(content, tags, project, meta=meta)

    def _recall_local(self, tags: Optional[List[str]], project: Optional[str], limit: int) -> List[Dict]:
        results = []
        try:
            with self._get_conn() as conn:
                conn.row_factory = sqlite3.Row
                sql = "SELECT address, domain, deposited_at, metadata_json FROM warf_artifacts WHERE 1=1"
                params = []

                if project:
                    sql += " AND domain = ?"
                    params.append(project)

                # Broaden search to ensure we don't miss entries due to JSON formatting
                if tags:
                    for tag in tags:
                        sql += " AND (metadata_json LIKE ? OR address LIKE ?)"
                        params.append(f"%{tag}%")
                        params.append(f"%{tag}%")

                sql += " ORDER BY deposited_at DESC LIMIT ?"
                params.append(limit)

                rows = conn.execute(sql, params).fetchall()
                for row in rows:
                    try:
                        meta = json.loads(row["metadata_json"])
                        if tags:
                            entry_tags = meta.get("tags", [])
                            if not any(t in entry_tags for t in tags) and not any(t in row["address"] for t in tags):
                                continue

                        results.append({
                            "address": row["address"],
                            "project": row["domain"],
                            "deposited_at": row["deposited_at"],
                            "content": meta.get("content", meta.get("preview", "")),
                            "meta": meta,
                            "source": "local",
                        })
                    except Exception as json_err:
                        self.logger.warning(f"Failed to parse metadata for {row['address']}: {json_err}")

        except Exception as e:
            self.logger.error(f"Direct DB recall failed: {e}")

        return results

    def _recall_node(self, query: Optional[str], tags: Optional[List[str]], project: Optional[str], limit: int) -> Optional[List[Dict]]:
        query_text = query or "handoff"
        response = self._node_request("GET", "/api/recall", params={
            "query": query_text,
            "mode": "keyword",
            "project": project,
            "limit": limit,
        })
        if response is None:
            return None

        results = []
        entries = response.get("results", [])
        if not isinstance(entries, list):
            return []

        for entry in entries:
            if not isinstance(entry, dict):
                continue
            meta = {
                "tags": entry.get("tags", []),
                "project": entry.get("project", ""),
                "content": entry.get("content", ""),
            }
            if tags:
                entry_tags = meta.get("tags", [])
                if not any(t in entry_tags for t in tags):
                    continue
            results.append({
                "address": entry.get("address", ""),
                "project": entry.get("project", ""),
                "deposited_at": entry.get("deposited_at", ""),
                "content": entry.get("content", ""),
                "meta": meta,
                "source": "node",
            })

        return results

    def recall(self, query: Optional[str] = None, tags: Optional[List[str]] = None, project: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """
        Recall reasoning artifacts from a WARF node or local WARF memory.db.
        """
        if self.node_url:
            node_results = self._recall_node(query, tags, project, limit)
            if node_results is not None:
                return node_results

        return self._recall_local(tags, project, limit)

    def get_heartbeat(self, project: Optional[str] = None) -> str:
        """
        Cool Feature: Returns an ASCII sparkline of activity over the last 7 days.
        """
        try:
            if self.node_url:
                node_results = self._recall_node("handoff", ["handoff"], project, 200)
                if node_results is not None:
                    counts = {}
                    for entry in node_results:
                        ts = entry.get("deposited_at", "")
                        day = ts[:10]
                        if day:
                            counts[day] = counts.get(day, 0) + 1

                    import datetime
                    spark = ""
                    for i in range(6, -1, -1):
                        day = (datetime.date.today() - datetime.timedelta(days=i)).isoformat()
                        count = counts.get(day, 0)
                        if count == 0:
                            spark += "░"
                        elif count < 3:
                            spark += "▒"
                        elif count < 6:
                            spark += "▓"
                        else:
                            spark += "█"
                    return spark

            with self._get_conn() as conn:
                sql = "SELECT date(deposited_at) as day, count(*) as count FROM warf_artifacts WHERE deposited_at > date('now', '-7 days')"
                params = []
                if project:
                    sql += " AND domain = ?"
                    params.append(project)
                sql += " GROUP BY day ORDER BY day ASC"

                rows = conn.execute(sql, params).fetchall()
                counts = {r[0]: r[1] for r in rows}

                import datetime
                spark = ""
                for i in range(6, -1, -1):
                    day = (datetime.date.today() - datetime.timedelta(days=i)).isoformat()
                    count = counts.get(day, 0)
                    if count == 0:
                        spark += "░"
                    elif count < 3:
                        spark += "▒"
                    elif count < 6:
                        spark += "▓"
                    else:
                        spark += "█"
                return spark
        except Exception:
            return "░░░░░░░"

    def get_recent_projects(self) -> List[str]:
        """
        Get a list of projects recently worked on.
        """
        try:
            if self.node_url:
                node_results = self._recall_node("handoff", ["handoff"], None, 200)
                if node_results is not None:
                    projects = []
                    seen = set()
                    for entry in node_results:
                        project = entry.get("project", "")
                        if project and project not in seen:
                            projects.append(project)
                            seen.add(project)
                    if projects:
                        return projects

            with self._get_conn() as conn:
                rows = conn.execute("SELECT DISTINCT domain FROM warf_artifacts ORDER BY deposited_at DESC LIMIT 10").fetchall()
                return [r[0] for r in rows]
        except Exception:
            return ["astrognosy", "laminar", "warf-edge"]
