---
description: Check and install everything the antigravity-gemini plugin needs (git, uv, Antigravity CLI), then guide sign-in
allowed-tools: Read, Bash
---

Set up this machine for the antigravity-gemini plugin.

1. Read `${CLAUDE_PLUGIN_ROOT}/REQUIREMENTS.md`. It lists every requirement and the only install commands you may use.
2. Run the full check: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/check-prereqs.sh"`. Each line is `<STATUS> <id> <detail>`; the `os` line says which install commands apply.
3. Show the user a short table: requirement, status, detail. If nothing is MISSING or WARN, skip to step 7.
4. For each MISSING item among `git`, `uv`, `agy`, in that order:
   - Show the exact command from REQUIREMENTS.md for this OS and where it comes from, and ask the user to confirm before you run it. One confirmation can cover all of them if the user says so.
   - Run only that official command. Do not substitute other sources, package mirrors or community packages.
   - On Windows, run PowerShell commands through `powershell -NoProfile -ExecutionPolicy Bypass -Command "..."`.
   - If a command fails, show the error and stop; do not try alternatives the user did not approve.
5. For `signin` MISSING: do not sign in for the user and never type, ask for or store passwords or API keys. Ask the user to open a terminal, run `agy`, finish the browser sign-in, and tell you when done. Mention the account notes from REQUIREMENTS.md (personal Google account on Free/Pro/Ultra, or a Google Cloud project; Workspace plans don't include Antigravity).
6. Run the full check again. A WARN for `uv` or `agy` "not on PATH" right after installing is expected: new installs land on PATH only for new processes.
   Then prepare the MCP server so its first start is fast: run `uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}/server/server.py" < /dev/null` once (use the full path to uv if it is not on PATH yet). It downloads Python and the `mcp` package into uv's cache and exits; without it the first start can take long enough to time out.
7. If anything was installed, or the plugin's MCP tools (`list_antigravity_models` and the rest) are not available in this session, tell the user to restart Claude Code and then run `/antigravity-gemini:agy-check`. Otherwise run the `/antigravity-gemini:agy-check` steps now.

End with a table of what was already there, what you installed, and what the user still has to do.
