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


def test_extract_json_payload() -> None:
    import server

    text = '[1] connecting...\n{"status": "starting"}\n{"status": "SUCCESS", "response": "ok"}\n'
    assert server._extract_json_payload(text) == {"status": "SUCCESS", "response": "ok"}
    assert server._extract_json_payload('{"a": 1}') == {"a": 1}
    assert server._extract_json_payload("no json here") is None


def test_parse_frontmatter() -> None:
    import tempfile

    import server

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "agent.md"
        path.write_text(
            "---\n"
            "name: my-agent\n"
            "description: >-\n"
            "  First line\n"
            "  second line.\n"
            "  model: not-a-key\n"
            "model: 'gemini-4-hydrogen-low'\n"
            "---\n"
            "body\n",
            encoding="utf-8",
        )
        meta = server.parse_frontmatter(path)
    assert meta == {
        "name": "my-agent",
        "description": "First line second line. model: not-a-key",
        "model": "gemini-4-hydrogen-low",
    }, meta


def test_batch_wrapper_refused() -> None:
    import os
    import tempfile

    import server

    with tempfile.TemporaryDirectory() as tmp:
        wrapper = Path(tmp) / "agy.cmd"
        wrapper.write_text("@echo off\n", encoding="utf-8")
        old = os.environ.get("AGY_BIN")
        os.environ["AGY_BIN"] = str(wrapper)
        try:
            try:
                found = server.resolve_agy_binary()
            except FileNotFoundError:
                found = ""
        finally:
            if old is None:
                os.environ.pop("AGY_BIN", None)
            else:
                os.environ["AGY_BIN"] = old
    assert not found.lower().endswith((".cmd", ".bat")), found


def test_timeout_kills_process_tree() -> None:
    import tempfile
    import time

    import server

    with tempfile.TemporaryDirectory() as tmp:
        marker = Path(tmp) / "child-survived.txt"
        child = f"import time, pathlib; time.sleep(3); pathlib.Path({str(marker)!r}).write_text('x')"
        parent = (
            "import subprocess, sys, time; "
            f"subprocess.Popen([sys.executable, '-c', {child!r}]); time.sleep(30)"
        )
        start = time.monotonic()
        try:
            asyncio.run(server._run_subprocess([sys.executable, "-c", parent], timeout_seconds=1))
            raise AssertionError("expected TimeoutError")
        except TimeoutError:
            pass
        assert time.monotonic() - start < 10, "timeout cleanup took too long"
        time.sleep(4)
        assert not marker.exists(), "child process outlived the timeout"


def run_unit_tests() -> None:
    sys.path.insert(0, str(BRIDGE_DIR))
    test_parse_usage_output()
    test_build_run_command()
    test_extract_json_payload()
    test_parse_frontmatter()
    test_batch_wrapper_refused()
    test_timeout_kills_process_tree()
    print("Unit tests passed")


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
        run_unit_tests()
        asyncio.run(run_tests())
