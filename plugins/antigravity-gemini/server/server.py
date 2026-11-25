# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=2.3,<3"]
# ///
"""MCP stdio bridge for invoking Google Antigravity CLI (agy) agents."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
from pathlib import Path
from typing import Any

from mcp.server import MCPServer

def _default_agy_paths() -> list[str]:
    """Default install locations of the Antigravity CLI, without user-specific paths."""
    paths: list[str] = []
    local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
    if local_app_data:
        paths.append(str(Path(local_app_data) / "agy" / "bin" / "agy.exe"))
    home = Path.home()
    paths.append(str(home / "AppData" / "Local" / "agy" / "bin" / "agy.exe"))
    paths.append(str(home / ".local" / "bin" / "agy"))
    return paths

VALID_EFFORTS = {"low", "medium", "high", "xhigh", "max"}
VALID_MODES = {"accept-edits", "auto", "plan"}
FRONTMATTER_KEYS = {"name", "description", "model", "mainAgent", "subagent"}
# Claude Code cuts every tool call at the "timeout" in .mcp.json (960 s); keep
# agy's own limit plus the 15 s grace period below it.
MAX_TIMEOUT_SECONDS = 940

mcp = MCPServer(
    name="antigravity-bridge",
    instructions=(
        "Bridge to invoke local Google Antigravity CLI (agy) agents, models, "
        "and custom subagents from Claude Code."
    ),
)


def resolve_agy_binary() -> str:
    """Resolve the path to agy.exe using env, PATH, or default install path."""
    candidates = [
        os.environ.get("AGY_BIN", "").strip(),
        shutil.which("agy") or "",
        *_default_agy_paths(),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(Path(candidate))
    raise FileNotFoundError(
        "Antigravity CLI (agy) not found. Install it, sign in once by running "
        "'agy' in a terminal, or set the AGY_BIN environment variable to its path."
    )


def parse_frontmatter(path: Path) -> dict[str, str]:
    """Extract lightweight YAML frontmatter metadata from a markdown agent file."""
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    meta: dict[str, str] = {}
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if ":" not in stripped or stripped.startswith("#"):
            continue
        key, _, value = stripped.partition(":")
        key = key.strip()
        if key in FRONTMATTER_KEYS:
            meta[key] = value.strip().strip("'\"")
    return meta


def _scan_agent_dirs(workspace_dir: str) -> list[dict[str, Any]]:
    """Discover markdown custom agent definitions globally and in workspace."""
    roots: list[tuple[str, Path]] = [
        ("global", Path.home() / ".gemini" / "config" / "agents"),
    ]
    if workspace_dir.strip():
        ws = Path(workspace_dir.strip())
        roots.append(("workspace", ws / ".agents" / "agents"))
        roots.append(("workspace", ws / ".agent" / "agents"))

    agents: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for scope, directory in roots:
        if not directory.is_dir():
            continue
        for md_file in sorted(directory.glob("*.md")):
            resolved = str(md_file.resolve())
            if resolved in seen_paths:
                continue
            seen_paths.add(resolved)
            meta = parse_frontmatter(md_file)
            agents.append(
                {
                    "name": meta.get("name") or md_file.stem,
                    "description": meta.get("description", ""),
                    "model": meta.get("model", "inherit"),
                    "mainAgent": meta.get("mainAgent", "true"),
                    "subagent": meta.get("subagent", "true"),
                    "scope": scope,
                    "path": resolved,
                }
            )
    return agents


async def _run_subprocess(
    args: list[str],
    cwd: str | None = None,
    timeout_seconds: int = 300,
) -> tuple[int, str, str]:
    """Run a subprocess safely without shell=True and enforce timeout."""
    cmd = list(args)
    if cmd[0].lower().endswith((".cmd", ".bat")):
        cmd = ["cmd.exe", "/c", *cmd]

    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd or None,
        env=env,
    )
    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout_seconds,
        )
    except TimeoutError:
        proc.terminate()
        try:
            await asyncio.wait_for(proc.wait(), timeout=5)
        except TimeoutError:
            proc.kill()
            await proc.wait()
        raise

    return (
        proc.returncode if proc.returncode is not None else -1,
        stdout_bytes.decode("utf-8", errors="replace"),
        stderr_bytes.decode("utf-8", errors="replace"),
    )


def _extract_json_payload(stdout: str) -> Any:
    """Parse JSON from stdout, skipping any leading non-JSON status lines."""
    text = stdout.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    for idx, ch in enumerate(text):
        if ch in "{[":
            try:
                obj, _ = decoder.raw_decode(text[idx:])
                return obj
            except json.JSONDecodeError:
                continue
    return None


@mcp.tool()
async def list_antigravity_agents(workspace_dir: str = "") -> str:
    """List available Antigravity CLI and custom markdown agents.

    Args:
        workspace_dir: Optional project directory to also scan .agents/agents/*.md.
    """
    try:
        agy_bin = resolve_agy_binary()
    except FileNotFoundError as exc:
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2)

    cli_agents_output = ""
    cli_stderr = ""
    cli_exit = 0
    try:
        cli_exit, cli_agents_output, cli_stderr = await _run_subprocess(
            [agy_bin, "agents"],
            cwd=workspace_dir.strip() or None,
            timeout_seconds=20,
        )
    except Exception as exc:
        cli_exit = -1
        cli_stderr = str(exc)

    custom_agents = _scan_agent_dirs(workspace_dir)
    payload: dict[str, Any] = {
        "ok": True,
        "agy_binary": agy_bin,
        "cli_exit_code": cli_exit,
        "cli_agents_output": cli_agents_output.strip(),
        "custom_agents": custom_agents,
        "note": (
            "Passing agent='' runs Antigravity's default primary agent, which "
            "can also spawn built-in 'research' and 'browser' subagents."
        ),
    }
    if cli_stderr.strip():
        payload["cli_stderr"] = cli_stderr.strip()
    return json.dumps(payload, ensure_ascii=False, indent=2)


@mcp.tool()
async def list_antigravity_models() -> str:
    """List available models from the installed Antigravity CLI."""
    try:
        agy_bin = resolve_agy_binary()
        exit_code, stdout, stderr = await _run_subprocess(
            [agy_bin, "models"],
            timeout_seconds=20,
        )
    except Exception as exc:
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2)

    models: list[dict[str, str]] = []
    for line in stdout.splitlines():
        if "\t" in line:
            model_id, _, label = line.partition("\t")
            if model_id.strip():
                models.append({"id": model_id.strip(), "label": label.strip()})

    payload: dict[str, Any] = {
        "ok": exit_code == 0,
        "exit_code": exit_code,
        "models": models,
    }
    if not models and stdout.strip():
        payload["raw_output"] = stdout.strip()
    if stderr.strip():
        payload["stderr"] = stderr.strip()
    return json.dumps(payload, ensure_ascii=False, indent=2)


def parse_usage_output(stdout: str) -> list[dict[str, Any]]:
    """Parse `agy -p /usage` lines: group<TAB>limit<TAB>percent%<TAB>reset time."""
    rows: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        parts = [part.strip() for part in line.split("\t")]
        if len(parts) != 4 or not parts[2].endswith("%"):
            continue
        try:
            remaining = float(parts[2].rstrip("%"))
        except ValueError:
            continue
        rows.append(
            {
                "group": parts[0],
                "limit": parts[1],
                "remaining_percent": int(remaining) if remaining.is_integer() else remaining,
                "resets_at": parts[3],
            }
        )
    return rows


@mcp.tool()
async def get_antigravity_usage() -> str:
    """Show the remaining Antigravity quota for this account (no model call, no quota used).

    Returns one row per model group and limit window (for example "Gemini Models",
    "Weekly Limit Remaining"), with the remaining percent and the UTC reset time.
    Accounts connected with a GEMINI_API_KEY have no account quota; check AI Studio instead.
    """
    try:
        agy_bin = resolve_agy_binary()
        exit_code, stdout, stderr = await _run_subprocess(
            [agy_bin, "-p", "/usage", "--print-timeout", "30s"],
            timeout_seconds=45,
        )
    except Exception as exc:
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2)

    rows = parse_usage_output(stdout)
    payload: dict[str, Any] = {
        "ok": exit_code == 0 and bool(rows),
        "exit_code": exit_code,
        "usage": rows,
    }
    if not rows:
        payload["raw_output"] = stdout.strip()[:2000]
        payload["hint"] = (
            "No quota rows found. Accounts using a GEMINI_API_KEY have no account quota "
            "(see AI Studio); otherwise run '/usage' inside an interactive 'agy' session."
        )
    if stderr.strip():
        payload["stderr"] = stderr.strip()[:2000]
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_run_command(
    agy_bin: str,
    prompt: str,
    *,
    agent: str = "",
    model: str = "",
    effort: str = "",
    mode: str = "",
    sandbox: bool = True,
    skip_permissions: bool = False,
    conversation_id: str = "",
    timeout_seconds: int = 300,
) -> list[str]:
    """Build the agy command for one headless task.

    Slash commands are disabled so a prompt that starts with "/" (for example
    "/swarm ...") is sent to the model as text instead of running a CLI command.
    """
    cmd = [agy_bin, "-p", prompt, "--output-format", "json", "--disable-slash-commands"]
    if agent.strip():
        cmd.extend(["--agent", agent.strip()])
    if model.strip():
        cmd.extend(["--model", model.strip()])
    if effort:
        cmd.extend(["--effort", effort])
    if mode:
        cmd.extend(["--mode", mode])
    if sandbox:
        cmd.append("--sandbox")
    if skip_permissions:
        cmd.append("--dangerously-skip-permissions")
    if conversation_id.strip():
        cmd.extend(["--conversation", conversation_id.strip()])
    cmd.extend(["--print-timeout", f"{int(timeout_seconds)}s"])
    return cmd


@mcp.tool()
async def run_antigravity_agent(
    prompt: str,
    agent: str = "",
    model: str = "",
    effort: str = "",
    mode: str = "",
    cwd: str = "",
    sandbox: bool = True,
    skip_permissions: bool = False,
    conversation_id: str = "",
    timeout_seconds: int = 300,
) -> str:
    """Run a task on an Antigravity agent in non-interactive headless mode.

    Args:
        prompt: Instruction or task prompt for the Antigravity agent.
        agent: Optional custom agent name (from list_antigravity_agents).
        model: Optional model ID (from list_antigravity_models).
        effort: Optional reasoning effort: low, medium, high, xhigh, max.
        mode: Optional execution mode: accept-edits, auto, plan.
        cwd: Optional working directory for the agent.
        sandbox: Run with Antigravity terminal sandbox enabled (default True).
        skip_permissions: Auto-approve tool permission requests (default False).
        conversation_id: Optional conversation ID to resume.
        timeout_seconds: Maximum execution time in seconds (default 300, at most 940).
    """
    if not prompt.strip():
        return json.dumps({"ok": False, "error": "prompt cannot be empty"}, indent=2)

    work_dir: str | None = None
    if cwd.strip():
        candidate = Path(cwd.strip())
        if not candidate.is_dir():
            return json.dumps(
                {"ok": False, "error": f"cwd does not exist or is not a directory: {cwd}"},
                ensure_ascii=False,
                indent=2,
            )
        work_dir = str(candidate)

    effort_clean = effort.strip().lower()
    if effort_clean and effort_clean not in VALID_EFFORTS:
        return json.dumps(
            {"ok": False, "error": f"Invalid effort '{effort}'. Must be one of: {sorted(VALID_EFFORTS)}"},
            indent=2,
        )

    mode_clean = mode.strip().lower()
    if mode_clean and mode_clean not in VALID_MODES:
        return json.dumps(
            {"ok": False, "error": f"Invalid mode '{mode}'. Must be one of: {sorted(VALID_MODES)}"},
            indent=2,
        )

    if timeout_seconds <= 0:
        return json.dumps({"ok": False, "error": "timeout_seconds must be > 0"}, indent=2)
    timeout_note = ""
    if timeout_seconds > MAX_TIMEOUT_SECONDS:
        timeout_note = (
            f"timeout_seconds {timeout_seconds} lowered to {MAX_TIMEOUT_SECONDS}, the most "
            "Claude Code's MCP tool timeout allows; split longer tasks."
        )
        timeout_seconds = MAX_TIMEOUT_SECONDS

    try:
        agy_bin = resolve_agy_binary()
    except FileNotFoundError as exc:
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2)

    cmd = build_run_command(
        agy_bin,
        prompt,
        agent=agent,
        model=model,
        effort=effort_clean,
        mode=mode_clean,
        sandbox=sandbox,
        skip_permissions=skip_permissions,
        conversation_id=conversation_id,
        timeout_seconds=timeout_seconds,
    )

    try:
        exit_code, stdout, stderr = await _run_subprocess(
            cmd,
            cwd=work_dir,
            timeout_seconds=int(timeout_seconds) + 15,
        )
    except TimeoutError:
        return json.dumps(
            {
                "ok": False,
                "error": f"Antigravity CLI timed out after {timeout_seconds}s.",
            },
            indent=2,
        )
    except Exception as exc:
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2)

    parsed = _extract_json_payload(stdout)
    ok = exit_code == 0
    payload: dict[str, Any] = {
        "ok": ok,
        "exit_code": exit_code,
        "result": parsed if parsed is not None else stdout.strip(),
    }
    if stderr.strip() or not ok:
        payload["stderr"] = stderr.strip()
    if timeout_note:
        payload["note"] = timeout_note

    combined_err = f"{stderr}\n{stdout}".lower()
    if not ok and any(tok in combined_err for tok in ("auth", "login", "sign in", "credential")):
        payload["hint"] = (
            "Authentication may be missing. Run 'agy' interactively once in PowerShell "
            "to sign in with your Google account."
        )

    return json.dumps(payload, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
