"""
warf_mcp_server.py

MCP server exposing ReasonRDN's memory API as Claude/Grok/Codex tools.

Installs as: 
  tools:
    - remember: Deposit content to shared memory
    - recall: Search shared memory
    - resolve: Fetch single artifact by address

Usage:
  python -m warf_mcp.server  # or reference in copilot/claude mcp.yml

Environment:
  REASON_NODE_URL     Custom node URL (optional)
  REASON_ECOSYSTEM_CONFIG   Path to .reason-ecosystem.cfg (optional)
"""

from __future__ import annotations
import json
import os
import sys
from pathlib import Path

try:
    from mcp.server.lowlevel import Server
    from mcp.types import (
        Tool, TextContent, ToolResponse, ToolErrorResponse
    )
except ImportError:
    print("Installing mcp...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "mcp", "-q"])
    from mcp.server.lowlevel import Server
    from mcp.types import Tool, TextContent, ToolResponse, ToolErrorResponse

from warf_ecosystem_client import EcosystemMemory


class WARFMCPServer:
    """MCP server for ReasonRDN memory API."""
    
    def __init__(self):
        self.server = Server("reason-ecosystem")
        self.memory = EcosystemMemory()
        self._register_tools()
    
    def _register_tools(self):
        """Register remember/recall/resolve tools."""
        
        @self.server.call_tool()
        def remember(name: str, arguments: dict) -> ToolResponse:
            """Deposit content to shared memory."""
            try:
                content = arguments.get("content", "")
                tags = arguments.get("tags", []).split(",") if isinstance(arguments.get("tags"), str) else arguments.get("tags", [])
                project = arguments.get("project", "astrognosy")
                meta = arguments.get("meta", {})
                
                result = self.memory.remember(
                    content=content,
                    tags=tags,
                    project=project,
                    meta=meta,
                )
                
                return ToolResponse(
                    content=[TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )],
                    is_error=False,
                )
            except Exception as e:
                return ToolErrorResponse(content=[TextContent(type="text", text=str(e))])
        
        @self.server.call_tool()
        def recall(name: str, arguments: dict) -> ToolResponse:
            """Search shared memory."""
            try:
                query = arguments.get("query", "")
                project = arguments.get("project", "astrognosy")
                limit = arguments.get("limit", 10)
                
                results = self.memory.recall(
                    query=query,
                    project=project,
                    limit=limit,
                )
                
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
            """Fetch single artifact by address."""
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
        
        # Register with server
        self.server.add_tool(
            Tool(
                name="remember",
                description="Deposit content to shared ReasonRDN memory. Tags help with discovery.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "The content to remember"},
                        "tags": {"type": "array", "description": "Tags for organization (e.g., ['ai', 'reasoning'])"},
                        "project": {"type": "string", "description": "Project scope (default: 'astrognosy')"},
                        "meta": {"type": "object", "description": "Optional metadata"},
                    },
                    "required": ["content"],
                },
            )
        )
        
        self.server.add_tool(
            Tool(
                name="recall",
                description="Search shared memory by query string. Returns matching artifacts.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "project": {"type": "string", "description": "Project scope (default: 'astrognosy')"},
                        "limit": {"type": "integer", "description": "Max results (default: 10)"},
                    },
                    "required": ["query"],
                },
            )
        )
        
        self.server.add_tool(
            Tool(
                name="resolve",
                description="Fetch a single artifact by its reason:// address.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "address": {"type": "string", "description": "reason:// address"},
                    },
                    "required": ["address"],
                },
            )
        )
    
    def run(self):
        """Run the MCP server."""
        print(f"WARF MCP Server starting...")
        print(f"Node available: {self.memory.available}")
        print(f"Node URL: {self.memory.node_url}")
        print(f"Local DB: {self.memory.local_db}")
        
        # For stdio transport
        import asyncio
        asyncio.run(self.server.stdio())


if __name__ == "__main__":
    server = WARFMCPServer()
    server.run()
