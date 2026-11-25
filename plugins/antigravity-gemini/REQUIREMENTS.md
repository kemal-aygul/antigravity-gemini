# antigravity-gemini: requirements

Everything this plugin needs to work, in install order. `/antigravity-gemini:setup` reads this file, checks each item with `scripts/check-prereqs.sh`, and installs what is missing after the user confirms.

| # | Requirement | Why | Check (id in check-prereqs.sh) | Who sets it up |
|---|---|---|---|---|
| 1 | Claude Code with plugin support | Runs the plugin | — | User |
| 2 | Git | Claude Code adds the marketplace from GitHub with git. On Windows, Git for Windows also provides the bash that Claude Code and this plugin's hook use. | `git` | Setup command, after confirmation |
| 3 | uv | Starts the MCP server and installs its Python dependency (`mcp`). It also downloads Python 3.10+ if the machine has none. | `uv` | Setup command, after confirmation |
| 4 | Antigravity CLI (`agy`) | The bridge sends every task to it | `agy` | Setup command, after confirmation |
| 5 | Antigravity sign-in | `agy` needs an account to reach the models | `signin` | **User only** |
| 6 | Network access | First start downloads `mcp` from PyPI; every task calls Google's servers | — | — |
| 7 | Restart Claude Code | Picks up the new PATH and starts the MCP server | — | User |

Python does not need to be installed separately: uv handles it.

## Install commands (official sources only)

### Git
- Windows: `winget install --id Git.Git -e --source winget`, or the installer from https://git-scm.com/download/win
- macOS: `xcode-select --install` (or `brew install git`)
- Linux: the distribution's package manager, for example `sudo apt install git`

### uv (https://docs.astral.sh/uv/getting-started/installation/)
- Windows (PowerShell): `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
- macOS / Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Installs to `~/.local/bin` and adds it to PATH for new terminals.

### Antigravity CLI (https://antigravity.google/docs/getting-started?tab=cli)
- Windows (PowerShell): `irm https://antigravity.google/cli/install.ps1 | iex`
- Windows (CMD): `curl -fsSL https://antigravity.google/cli/install.cmd -o install.cmd && install.cmd && del install.cmd`
- macOS / Linux: `curl -fsSL https://antigravity.google/cli/install.sh | bash`
- Installs to `%LOCALAPPDATA%\agy\bin` on Windows and `~/.local/bin/agy` on macOS/Linux. Verify with `agy --version`; update later with `agy update`.
- If `agy` is somewhere else, set the `AGY_BIN` environment variable to its full path.

## Sign-in (the user does this, never the agent)

Run `agy` once in a terminal. It opens a browser to sign in (https://antigravity.google/docs/install?tab=cli):
- **Personal Google account** ("Google OAuth"): works with Free, Pro and Ultra plans. Google Workspace plans do not include Antigravity.
- **Google Cloud project**: for Gemini Enterprise or pay-as-you-go.
- **Over SSH**: `agy` prints a URL; open it on another machine and paste the code back.
- **Headless or CI**: set `modelProvider` to `"gemini"` in `~/.gemini/antigravity-cli/settings.json` and export `GEMINI_API_KEY`. The key belongs to the user; an agent must not type or store it.

Once signed in, `agy` keeps the token in the OS keyring (Windows Credential Manager, macOS Keychain, Linux Secret Service).

## Notes
- Which models you get depends on your account and plan. Claude checks with `list_antigravity_models`.
- The plugin itself stores no keys and sends nothing anywhere except through your own `agy`.
