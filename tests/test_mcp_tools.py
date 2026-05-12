import pytest

from mcp_stdio_python_template.server import build_server


@pytest.mark.anyio
async def test_server_exposes_only_status_tool():
    server = build_server()

    tools = await server.list_tools()

    assert {tool.name for tool in tools} == {"status"}
    assert "version" not in {tool.name for tool in tools}


@pytest.mark.anyio
async def test_status_tool_takes_no_arguments_and_returns_ok():
    server = build_server()
    tools_by_name = {tool.name: tool for tool in await server.list_tools()}

    _, structured = await server.call_tool("status", {})

    assert tools_by_name["status"].inputSchema["properties"] == {}
    assert structured["result"] == "ok"
