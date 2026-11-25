"""End-to-end tests for the Antigravity MCP Bridge."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

BRIDGE_DIR = Path(__file__).resolve().parent
SERVER_PATH = BRIDGE_DIR / "server.py"
EXPECTED_TOOLS = {
    "list_antigravity_agents",
    "list_antigravity_models",
    "run_antigravity_agent",
}


async def run_tests() -> None:
    sys.path.insert(0, str(BRIDGE_DIR))
    import server

    agy_bin = server.resolve_agy_binary()
    print(f"[1/5] Resolved agy binary: {agy_bin}")
    assert Path(agy_bin).is_file()

    params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_PATH)],
        env={"AGY_BIN": agy_bin},
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("[2/5] MCP stdio handshake succeeded")

            tools_resp = await session.list_tools()
            tool_names = {tool.name for tool in tools_resp.tools}
            print(f"[3/5] Listed MCP tools: {sorted(tool_names)}")
            assert EXPECTED_TOOLS.issubset(tool_names), f"Missing tools: {EXPECTED_TOOLS - tool_names}"

            agents_res = await session.call_tool("list_antigravity_agents", {})
            agents_data = json.loads(agents_res.content[0].text)
            assert agents_data["ok"] is True, agents_data
            print(f"[4/5] list_antigravity_agents ok (custom_agents={len(agents_data['custom_agents'])})")

            models_res = await session.call_tool("list_antigravity_models", {})
            models_data = json.loads(models_res.content[0].text)
            assert models_data["ok"] is True, models_data
            assert len(models_data["models"]) > 0, "Expected at least one model"
            print(f"[4b/5] list_antigravity_models ok (count={len(models_data['models'])})")

            run_res = await session.call_tool(
                "run_antigravity_agent",
                {
                    "prompt": "Reply with exactly: OK",
                    "sandbox": True,
                    "timeout_seconds": 90,
                },
            )
            run_data = json.loads(run_res.content[0].text)
            print(f"[5/5] run_antigravity_agent response: {json.dumps(run_data, ensure_ascii=False)}")
            assert run_data["ok"] is True, run_data
            assert "OK" in json.dumps(run_data["result"], ensure_ascii=False)

    print("ALL TESTS PASSED")


if __name__ == "__main__":
    asyncio.run(run_tests())
