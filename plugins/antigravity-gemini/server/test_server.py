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
    "get_antigravity_usage",
    "run_antigravity_agent",
}


def test_parse_usage_output() -> None:
    import server

    sample = (
        "Gemini Models\tWeekly Limit Remaining\t93%\t2026-12-01T20:41:19Z\n"
        "Gemini Models\tFive Hour Limit Remaining\t97.5%\t2026-11-25T23:03:43Z\n"
        "some unrelated line\n"
    )
    rows = server.parse_usage_output(sample)
    assert rows == [
        {"group": "Gemini Models", "limit": "Weekly Limit Remaining",
         "remaining_percent": 93, "resets_at": "2026-12-01T20:41:19Z"},
        {"group": "Gemini Models", "limit": "Five Hour Limit Remaining",
         "remaining_percent": 97.5, "resets_at": "2026-11-25T23:03:43Z"},
    ], rows
    assert server.parse_usage_output("It looks like you tried to run /usage") == []


def test_build_run_command() -> None:
    import server

    cmd = server.build_run_command("agy", "/swarm do everything", model="m", effort="low")
    assert cmd[:3] == ["agy", "-p", "/swarm do everything"], cmd
    assert "--disable-slash-commands" in cmd, cmd
    assert "--sandbox" in cmd and "--dangerously-skip-permissions" not in cmd, cmd
    assert cmd[-2:] == ["--print-timeout", "300s"], cmd


def run_unit_tests() -> None:
    sys.path.insert(0, str(BRIDGE_DIR))
    test_parse_usage_output()
    test_build_run_command()
    print("Unit tests passed")


async def run_tests() -> None:
    sys.path.insert(0, str(BRIDGE_DIR))
    import server

    run_unit_tests()

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

            usage_res = await session.call_tool("get_antigravity_usage", {})
            usage_data = json.loads(usage_res.content[0].text)
            assert usage_data["ok"] is True, usage_data
            assert len(usage_data["usage"]) > 0, "Expected at least one quota row"
            print(f"[4c/5] get_antigravity_usage ok (rows={len(usage_data['usage'])})")

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
    # --unit runs only the tests that need no agy install or sign-in (used in CI).
    if "--unit" in sys.argv:
        run_unit_tests()
    else:
        asyncio.run(run_tests())
