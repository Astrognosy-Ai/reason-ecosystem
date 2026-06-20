"""
rdn/mcp/server.py

MCP server exposing the unified ReasonRDN memory API as tools for Claude/Grok/Codex/etc.

Tools:
  - remember: Deposit content (auto structural fingerprint via protected PCF)
  - recall: Search by query string (+ project / limit)
  - resolve: Fetch exact artifact by reason:// address

Usage (after `pip install -e .`):
  python -m rdn.mcp.server
  rdn-mcp

Environment / config (for auto-deposit to warf Xchange or custom node):
  REASON_USE_XCHANGE=1          # or USE_WARF_XCHANGE=1 → https://warf.astrognosy.com
  REASON_NODE_URL=...
  RDN_NODE_URL=...
  The unified client loads from env + ~/.reason-ecosystem.cfg + local port file.

To share reasoning artifacts ecosystem-wide, install with --xchange or set the env var.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

# Lazy MCP import so the core rdn package works without the optional extra
_mcp_available = False
try:
    from mcp.server.lowlevel import Server
    from mcp.types import Tool, TextContent, ToolResponse, ToolErrorResponse
    _mcp_available = True
except ImportError:
    Server = None
    Tool = TextContent = ToolResponse = ToolErrorResponse = None

from rdn.client import RDNClient, XCHANGE_URL


class WARFMCPServer:
    """MCP server for ReasonRDN + warf Xchange.

    Provides local persistent memory + one-command federation to the central
    warf Xchange (https://warf.astrognosy.com) for ecosystem-wide verified artifacts.

    Agents are instructed to:
      - resolve before re-reasoning on known problems
      - remember decisions worth preserving
      - share high-value work to the Xchange (when configured)
    """

    def __init__(self):
        if not _mcp_available or Server is None:
            raise RuntimeError(
                "MCP support not installed. Install with: pip install 'reason-rdn[mcp]' or 'reason-rdn[full]'"
            )
        self.server = Server("ReasonRDN")
        self.memory = RDNClient()  # honors REASON_USE_XCHANGE, config, local port, etc.
        self._register_tools()

    def _register_tools(self):
        @self.server.call_tool()
        def remember(name: str, arguments: dict) -> ToolResponse:
            """Deposit content to shared ReasonRDN memory.
            Automatically emits to the agnostic harness metrics (token accounting, velocity, etc).
            If the client is in Xchange mode, this also feeds the warf flywheel.
            """
            try:
                content = arguments.get("content", "")
                raw_tags = arguments.get("tags", [])
                if isinstance(raw_tags, str):
                    tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
                elif isinstance(raw_tags, (list, tuple)):
                    tags = [str(t).strip() for t in raw_tags if str(t).strip()]
                else:
                    tags = []

                project = arguments.get("project", "astrognosy")
                meta = arguments.get("meta", {}) or {}
                tokens_used = arguments.get("tokens_used")  # agents can report real cost

                # Use high-level remember so tokens_used is recorded in HarnessMetrics
                # (and Xchange mode / broker routing is honored via the default client).
                import rdn as reason
                result = reason.remember(
                    content=content,
                    tags=tags,
                    project=project,
                    meta=meta,
                    tokens_used=int(tokens_used) if tokens_used else None,
                )

                # === MCP EMIT: Agents using tools automatically feed the harness ===
                # The high-level remember above already did the record_handoff with tokens.
                # If Xchange, it also recorded the share.
                try:
                    reason.harness_metrics()  # ensure summary is fresh
                except Exception:
                    pass

                return ToolResponse(
                    content=[TextContent(type="text", text=json.dumps(result, indent=2))],
                    is_error=False,
                )
            except Exception as e:
                return ToolErrorResponse(content=[TextContent(type="text", text=str(e))])

        @self.server.call_tool()
        def recall(name: str, arguments: dict) -> ToolResponse:
            """Search shared memory by free-text query.

            Automatically emits to the harness with real token savings when the calling
            agent passes `tokens_saved`. This is how agents get their personal + ecosystem
            metrics (velocity, ship rate, token savings) for free just by using the tools.
            """
            try:
                query = arguments.get("query", "")
                project = arguments.get("project", "astrognosy")
                limit = arguments.get("limit", 10)
                tokens_saved = arguments.get("tokens_saved")  # agents should pass this
                try:
                    limit = int(limit)
                except Exception:
                    limit = 10

                results = self.memory.recall(
                    query=query,
                    project=project,
                    limit=limit,
                )

                # MCP EMIT — record savings using the public helper (no double resolve needed)
                try:
                    import rdn as reason
                    saved = int(tokens_saved) if tokens_saved else None
                    reason.record_recall(query, tokens_saved=saved)
                except Exception:
                    pass

                return ToolResponse(
                    content=[TextContent(
                        type="text",
                        text=json.dumps({"status": "ok", "results": results}, indent=2),
                    )],
                    is_error=False,
                )
            except Exception as e:
                return ToolErrorResponse(content=[TextContent(type="text", text=str(e))])

        @self.server.call_tool()
        def resolve(name: str, arguments: dict) -> ToolResponse:
            """Fetch a single artifact by its reason:// address (local or Xchange)."""
            try:
                address = arguments.get("address", "")
                artifact = self.memory.resolve(address)

                if not artifact:
                    return ToolResponse(
                        content=[TextContent(
                            type="text",
                            text=json.dumps({"status": "not_found", "address": address}, indent=2),
                        )],
                        is_error=False,
                    )

                return ToolResponse(
                    content=[TextContent(
                        type="text",
                        text=json.dumps({"status": "ok", "artifact": artifact}, indent=2),
                    )],
                    is_error=False,
                )
            except Exception as e:
                return ToolErrorResponse(content=[TextContent(type="text", text=str(e))])

        @self.server.call_tool()
        def xchange_resolve(name: str, arguments: dict) -> ToolResponse:
            """Resolve a reason:// URI against the warf Xchange."""
            try:
                uri = arguments.get("uri", "")
                bypass = arguments.get("bypass_cache", False)
                result = self.memory.resolve_reason_uri(uri, bypass_cache=bypass)
                return ToolResponse(
                    content=[TextContent(
                        type="text",
                        text=json.dumps({"status": "ok", "result": result or {"not_found": uri}}, indent=2),
                    )],
                    is_error=False,
                )
            except Exception as e:
                return ToolErrorResponse(content=[TextContent(type="text", text=str(e))])

        @self.server.call_tool()
        def harness_status(name: str, arguments: dict) -> ToolResponse:
            """Get current harness metrics and stack status for self-assessment and suggestions."""
            try:
                import rdn as reason
                metrics = reason.harness_metrics()
                stack = reason.status()
                return ToolResponse(
                    content=[TextContent(
                        type="text",
                        text=json.dumps({"status": "ok", "harness": metrics, "stack": stack}, indent=2),
                    )],
                    is_error=False,
                )
            except Exception as e:
                return ToolErrorResponse(content=[TextContent(type="text", text=str(e))])

        @self.server.call_tool()
        def xchange_share(name: str, arguments: dict) -> ToolResponse:
            """Share high-value work to the warf Xchange (auto fingerprint included)."""
            try:
                content = arguments.get("content", "")
                uri = arguments.get("uri")
                tags = arguments.get("tags", [])
                project = arguments.get("project", "astrognosy")
                tokens_used = arguments.get("tokens_used")

                # Use high-level remember (with xchange_share) so it routes correctly
                # and tokens_used is recorded in HarnessMetrics without double-deposit.
                import rdn as reason
                result = reason.remember(
                    content=content,
                    uri=uri,
                    tags=tags,
                    project=project,
                    tokens_used=int(tokens_used) if tokens_used else None,
                    xchange_share=True,
                )

                return ToolResponse(
                    content=[TextContent(
                        type="text",
                        text=json.dumps({"status": "shared", "result": result}, indent=2),
                    )],
                    is_error=False,
                )
            except Exception as e:
                return ToolErrorResponse(content=[TextContent(type="text", text=str(e))])

        # Tool schemas (match the unified client capabilities)
        self.server.add_tool(
            Tool(
                name="remember",
                description="Deposit content to shared ReasonRDN memory. Tags help with discovery and filtering. Pass tokens_used for accurate harness metrics.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "The content / summary to remember"},
                        "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags for organization (e.g. ['ai', 'handoff', 'bugfix'])"},
                        "project": {"type": "string", "description": "Project / domain scope (default: 'astrognosy')"},
                        "meta": {"type": "object", "description": "Optional metadata. structural_hash (fingerprint) is added automatically by the handoff layer for relevance checking."},
                        "tokens_used": {"type": "integer", "description": "Optional: real tokens consumed to produce this artifact (for accurate harness metrics)"},
                    },
                    "required": ["content"],
                },
            )
        )

        self.server.add_tool(
            Tool(
                name="recall",
                description="Search shared memory by free-text query. Returns matching handoff artifacts ordered by recency.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query (substring match across content, tags, address, etc.)"},
                        "project": {"type": "string", "description": "Limit to a specific project/domain"},
                        "limit": {"type": "integer", "description": "Maximum results to return (default 10)"},
                        "tokens_saved": {"type": "integer", "description": "Optional: tokens this recall saved you (report for accurate harness token-savings metrics)"},
                    },
                    "required": ["query"],
                },
            )
        )

        self.server.add_tool(
            Tool(
                name="resolve",
                description="Fetch a single artifact by its exact reason:// address (from a previous remember or handoff). Works against local or Xchange.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "address": {"type": "string", "description": "The reason://project/handoff/xxxxxxxx address"},
                    },
                    "required": ["address"],
                },
            )
        )

        self.server.add_tool(
            Tool(
                name="xchange_resolve",
                description="Resolve a full reason:// URI against the warf Xchange (https://warf.astrognosy.com). Strongly recommended before re-reasoning a known problem.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "uri": {"type": "string", "description": "reason://domain/category/task"},
                        "bypass_cache": {"type": "boolean"},
                    },
                    "required": ["uri"],
                },
            )
        )

        self.server.add_tool(
            Tool(
                name="xchange_share",
                description="Share a high-signal artifact to the central warf Xchange. Includes protected structural fingerprint automatically. Use for reusable solutions, decisions, and patterns.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "The insight, fix, or pattern"},
                        "uri": {"type": "string", "description": "Canonical reason:// URI (optional but recommended)"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "project": {"type": "string", "default": "astrognosy"},
                        "tokens_used": {"type": "integer", "description": "Optional real token cost for accurate harness metrics"},
                    },
                    "required": ["content"],
                },
            )
        )

        self.server.add_tool(
            Tool(
                name="harness_status",
                description="Get the current harness metrics (token savings, velocity, ship rate, vibe stars, suggestions) and stack status. Agents can use this to self-assess impact and get workflow ideas.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            )
        )

    def run(self):
        print("ReasonRDN MCP Server starting (unified client)...")
        print(f"  Node available: {self.memory.available}")
        print(f"  Node URL: {self.memory.node_url}")
        print(f"  Local DB: {self.memory.db_path}")
        if self.memory.node_url and "warf.astrognosy.com" in self.memory.node_url:
            print("  *** Using warf Xchange - reasoning artifacts will be shared to the central exchange ***")

        asyncio.run(self.server.stdio())


def main():
    server = WARFMCPServer()
    server.run()


if __name__ == "__main__":
    main()
