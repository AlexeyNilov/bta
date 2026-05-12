from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations


def build_server() -> FastMCP:
    server = FastMCP("mcp-stdio-python-template")

    @server.tool(
        name="status",
        description="Return the server health status.",
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    async def status() -> str:
        return "ok"

    return server
