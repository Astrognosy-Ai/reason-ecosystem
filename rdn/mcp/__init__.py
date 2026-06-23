"""MCP server exposing rdn memory tools for Claude, Grok, Codex, etc."""
from __future__ import annotations

__all__ = ["WARFMCPServer", "mcp_main"]


def __getattr__(name: str):
    if name == "WARFMCPServer":
        from .server import WARFMCPServer

        return WARFMCPServer
    if name == "mcp_main":
        from .server import main

        return main
    raise AttributeError(name)
