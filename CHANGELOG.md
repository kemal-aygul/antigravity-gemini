# Changelog

All notable changes to the antigravity-gemini plugin. Versions follow `plugins/antigravity-gemini/.claude-plugin/plugin.json`.

## 0.5.1 — 2026-11-25

Fixes from a Gemini 4 Neon review of 0.5.0, each checked against the code.

### Fixed
- Windows: `.cmd` and `.bat` wrappers for `agy` are no longer run through `cmd.exe`, which could interpret `&`, `|` and `%VAR%` inside a prompt. The bridge skips them; the official CLI is `agy.exe`.
- On timeout or cancellation the bridge now kills `agy` together with every process it started, instead of only `agy` itself.
- When `agy` prints status lines that look like JSON, the bridge now takes the last JSON value (the result), not the first.
- `list_antigravity_agents` checks that `workspace_dir` exists and reports `ok: false` when `agy agents` fails.
- Custom Antigravity agents with multi-line descriptions (`description: >-`) are listed with their full description; indented lines no longer overwrite top-level fields.
- The sign-in hint says "in a terminal" on every OS and matches specific phrases instead of any word containing "auth".
- `check-prereqs.sh` limits the sign-in check to 45 s on macOS too (no `timeout` there), warns when `agy` is installed but not on PATH, and skips an empty `LOCALAPPDATA`.
- `/antigravity-gemini:setup` can run the final check: it is allowed the bridge's tools and points to the check steps.

### Changed
- The `antigravity` subagent treats file-edit permission and unsandboxed or auto-approved runs as separate authorizations.
- README: the update steps include `/plugin update` and a restart, and Google Workspace accounts are noted as not including Antigravity. INSTALL-PROMPT.md has an English introduction.
- Unit tests for JSON extraction, frontmatter parsing, batch-wrapper refusal and process-tree cleanup.

## 0.5.0 — 2026-11-25

### Fixed
- Long Gemini tasks were cut off after 2 minutes. Claude Code applies the MCP server's `timeout` in `.mcp.json` to every tool call, not only to start-up, so the subagents' 600–900 s limits never took effect. The timeout is now 960 s, and `run_antigravity_agent` lowers any `timeout_seconds` above 940 to 940 and says so in its result.
- A task prompt starting with `/` (for example `/swarm …`) ran as an Antigravity CLI command instead of reaching the model. `run_antigravity_agent` now passes `--disable-slash-commands`.

### Added
- The `antigravity` subagent and `/antigravity-gemini:agy-check` use `get_antigravity_usage`; the check now ends by showing the remaining quota.
- INSTALL-PROMPT.md mentions the Gemini family subagents and the quota question.
- GitHub Actions workflow that runs the unit tests (no `agy` needed) and validates the plugin's JSON and agent frontmatter.
- This changelog.

## 0.4.0 — 2026-11-25
### Added
- `get_antigravity_usage` MCP tool: remaining account quota per model group and window (weekly, five-hour), with reset times. It reads `agy -p /usage` and makes no model call.

## 0.3.1 — 2026-11-25
### Added
- A display color for each subagent (Neon purple, Carbon blue, Hydrogen green, Argon orange, `antigravity` cyan). The Claude desktop app may not show it.

## 0.3.0 — 2026-11-25
### Added
- One subagent per Gemini 4 family: `gemini-neon`, `gemini-carbon`, `gemini-hydrogen`, `gemini-argon`, with capability and cost figures in their descriptions.
- Benchmark and price table in the `gemini-delegate` skill; plan requirements and the Argon / Gemini 3.8 Flash removal (2026-11-30) in the README.

## 0.2.1 — 2026-11-25
### Fixed
- The first start of the MCP server could exceed Claude Code's 30 s connect timeout while uv downloaded Python and `mcp`; the timeout was raised to 120 s and `/antigravity-gemini:setup` warms uv's cache.
### Added
- INSTALL-PROMPT.md: a prompt that has Claude Code install and check the plugin.

## 0.2.0 — 2026-11-25
- First public version: MCP bridge (`list_antigravity_models`, `list_antigravity_agents`, `run_antigravity_agent`), `antigravity` subagent, `gemini-delegate` skill, `/antigravity-gemini:setup` and `/antigravity-gemini:agy-check` commands, and a start-up prerequisite check.
