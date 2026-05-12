from pathlib import Path

import pytest
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"


@pytest.mark.anyio
async def test_stdio_server_exposes_status_tool_returning_ok():
    server_params = StdioServerParameters(
        command=str(PYTHON),
        args=["-m", "mcp_stdio_python_template"],
        cwd=ROOT,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            result = await session.call_tool("status", {})

    assert {tool.name for tool in tools.tools} == {"status"}
    assert result.structuredContent == {"result": "ok"}
