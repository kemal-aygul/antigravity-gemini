---
description: Check that the Antigravity CLI and the Gemini bridge work end to end
allowed-tools: mcp__plugin_antigravity-gemini_antigravity__list_antigravity_agents, mcp__plugin_antigravity-gemini_antigravity__list_antigravity_models, mcp__plugin_antigravity-gemini_antigravity__run_antigravity_agent
---

Check the antigravity-gemini setup on this machine, step by step, and stop at the first failure.

1. Call `list_antigravity_agents`. Report the `agy_binary` path it found. If it returns `ok: false`, say the Antigravity CLI was not found and explain the fix: install the Antigravity CLI, or set the `AGY_BIN` environment variable to the full path of `agy`.
2. Call `list_antigravity_models`. Report how many models were found and list the Gemini model IDs grouped by family. If none come back, say the user probably needs to sign in: run `agy` once in a terminal.
3. Pick the fastest available Gemini model (prefer `gemini-4-hydrogen-low`, else any `-low` Gemini model) and call `run_antigravity_agent` with the prompt: `Do not use any tools. Compute 17*23 and reply with exactly one line: "AGY_OK <result>".` and `timeout_seconds: 120`.
4. Pass only if the response contains `AGY_OK 391`.

If the MCP tools are missing entirely, the bridge did not start. On any failure, offer `/antigravity-gemini:setup`, which checks and installs the requirements.

Finish with a short table: step, result (pass/fail), and detail (path, model count, model used, duration).
