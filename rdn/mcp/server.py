"""
rdn/mcp/server.py

MCP server exposing the unified ReasonRDN memory API as tools for Claude/Grok/Codex/etc.

Tools:
  - remember: Deposit content and local artifact metadata
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
    from mcp.server.stdio import stdio_server
    from mcp.types import CallToolResult, TextContent, Tool
    _mcp_available = True
except ImportError:
    Server = None
    stdio_server = None
    CallToolResult = TextContent = Tool = None

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

    def _text_result(self, payload, is_error: bool = False) -> CallToolResult:
        text = payload if isinstance(payload, str) else json.dumps(payload, indent=2)
        return CallToolResult(
            content=[TextContent(type="text", text=text)],
            isError=is_error,
        )

    def _tool_schemas(self) -> list[Tool]:
        return [
            Tool(
                name="remember",
                description="Deposit content to shared ReasonRDN memory. Tags help with discovery and filtering. Pass tokens_used for accurate harness metrics.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "The content / summary to remember"},
                        "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags for organization"},
                        "project": {"type": "string", "description": "Project / domain scope"},
                        "meta": {"type": "object", "description": "Optional metadata for the artifact."},
                        "tokens_used": {"type": "integer", "description": "Optional token count for harness metrics"},
                    },
                    "required": ["content"],
                },
            ),
            Tool(
                name="recall",
                description="Search shared memory by free-text query. Returns matching handoff artifacts ordered by recency.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "project": {"type": "string", "description": "Limit to a specific project/domain"},
                        "limit": {"type": "integer", "description": "Maximum results to return"},
                        "tokens_saved": {"type": "integer", "description": "Optional token-savings count for harness metrics"},
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="resolve",
                description="Fetch a single artifact by its exact reason:// address.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "address": {"type": "string", "description": "The reason:// address"},
                    },
                    "required": ["address"],
                },
            ),
            Tool(
                name="xchange_resolve",
                description="Resolve a full reason:// URI against the warf Xchange broker.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "uri": {"type": "string", "description": "reason://domain/category/task"},
                        "bypass_cache": {"type": "boolean"},
                    },
                    "required": ["uri"],
                },
            ),
            Tool(
                name="xchange_share",
                description="Share a high-signal artifact to the central warf Xchange.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "The insight, fix, or pattern"},
                        "uri": {"type": "string", "description": "Canonical reason:// URI"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "project": {"type": "string", "default": "astrognosy"},
                        "tokens_used": {"type": "integer", "description": "Optional token count for harness metrics"},
                    },
                    "required": ["content"],
                },
            ),
            Tool(
                name="harness_status",
                description="Get harness metrics and stack status.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
        ]

    def _register_tools(self):
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> CallToolResult:
            arguments = arguments or {}
            try:
                if name == "remember":
                    import rdn as reason
                    raw_tags = arguments.get("tags", [])
                    if isinstance(raw_tags, str):
                        tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
                    elif isinstance(raw_tags, (list, tuple)):
                        tags = [str(t).strip() for t in raw_tags if str(t).strip()]
                    else:
                        tags = []
                    tokens_used = arguments.get("tokens_used")
                    result = reason.remember(
                        content=arguments.get("content", ""),
                        tags=tags,
                        project=arguments.get("project", "astrognosy"),
                        meta=arguments.get("meta", {}) or {},
                        tokens_used=int(tokens_used) if tokens_used else None,
                    )
                    return self._text_result(result)

                if name == "recall":
                    query = arguments.get("query", "")
                    limit = int(arguments.get("limit", 10) or 10)
                    results = self.memory.recall(
                        query=query,
                        project=arguments.get("project", "astrognosy"),
                        limit=limit,
                    )
                    tokens_saved = arguments.get("tokens_saved")
                    try:
                        import rdn as reason
                        reason.record_recall(
                            query,
                            tokens_saved=int(tokens_saved) if tokens_saved else None,
                        )
                    except Exception:
                        pass
                    return self._text_result({"status": "ok", "results": results})

                if name == "resolve":
                    address = arguments.get("address", "")
                    artifact = self.memory.resolve(address)
                    if not artifact:
                        return self._text_result({"status": "not_found", "address": address})
                    return self._text_result({"status": "ok", "artifact": artifact})

                if name == "xchange_resolve":
                    uri = arguments.get("uri", "")
                    result = self.memory.resolve_reason_uri(
                        uri,
                        bypass_cache=bool(arguments.get("bypass_cache", False)),
                    )
                    return self._text_result(
                        {"status": "ok", "result": result or {"not_found": uri}}
                    )

                if name == "harness_status":
                    import rdn as reason
                    return self._text_result(
                        {
                            "status": "ok",
                            "harness": reason.harness_metrics(),
                            "stack": reason.status(),
                        }
                    )

                if name == "xchange_share":
                    import rdn as reason
                    raw_tags = arguments.get("tags", [])
                    if isinstance(raw_tags, str):
                        tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
                    else:
                        tags = raw_tags
                    tokens_used = arguments.get("tokens_used")
                    result = reason.remember(
                        content=arguments.get("content", ""),
                        uri=arguments.get("uri"),
                        tags=tags,
                        project=arguments.get("project", "astrognosy"),
                        tokens_used=int(tokens_used) if tokens_used else None,
                        xchange_share=True,
                    )
                    return self._text_result({"status": "shared", "result": result})

                return self._text_result(f"Unknown tool: {name}", is_error=True)
            except Exception as exc:
                return self._text_result(str(exc), is_error=True)

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return self._tool_schemas()

    async def _run_stdio(self):
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )

    def run(self):
        print("ReasonRDN MCP Server starting (unified client)...", file=sys.stderr)
        print(f"  Node available: {self.memory.available}", file=sys.stderr)
        print(f"  Node URL: {self.memory.node_url}", file=sys.stderr)
        print(f"  Local DB: {self.memory.db_path}", file=sys.stderr)
        if self.memory.node_url and "warf.astrognosy.com" in self.memory.node_url:
            print(
                "  *** Using warf Xchange - reasoning artifacts will be shared to the central exchange ***",
                file=sys.stderr,
            )

        asyncio.run(self._run_stdio())


def main():
    server = WARFMCPServer()
    server.run()


if __name__ == "__main__":
    main()
