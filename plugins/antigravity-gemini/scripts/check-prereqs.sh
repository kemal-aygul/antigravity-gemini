#!/usr/bin/env bash
# Checks what the antigravity-gemini plugin needs on this machine.
#
#   check-prereqs.sh          full check (also asks agy for its model list,
#                             which shows whether the user is signed in)
#   check-prereqs.sh --quick  fast presence check for the SessionStart hook;
#                             prints nothing when everything is installed
#
# Output lines: "<STATUS> <id> <detail>", STATUS is OK, MISSING or WARN.
# Exit code: full check 0 when nothing is MISSING, 1 otherwise; --quick always 0.

quick=0
[ "${1:-}" = "--quick" ] && quick=1

case "$(uname -s 2>/dev/null)" in
  MINGW*|MSYS*|CYGWIN*) os=windows ;;
  Darwin*) os=macos ;;
  *) os=linux ;;
esac

lines=()
missing=0
report() { lines+=("$1 $2 $3"); [ "$1" = "MISSING" ] && missing=1; return 0; }

first_existing() {
  for c in "$@"; do
    [ -n "$c" ] && [ -f "$c" ] && { printf '%s\n' "$c"; return 0; }
  done
  return 1
}

# Run a command with a time limit in seconds. Uses timeout or gtimeout when
# present (macOS ships neither by default), else a background watchdog.
run_with_limit() {
  limit="$1"; shift
  if command -v timeout >/dev/null 2>&1; then
    timeout "$limit" "$@"
  elif command -v gtimeout >/dev/null 2>&1; then
    gtimeout "$limit" "$@"
  else
    "$@" &
    cmd_pid=$!
    ( sleep "$limit"; kill "$cmd_pid" 2>/dev/null ) &
    watchdog_pid=$!
    wait "$cmd_pid"
    status=$?
    kill "$watchdog_pid" 2>/dev/null
    return "$status"
  fi
}

to_unix() { if command -v cygpath >/dev/null 2>&1; then cygpath -u "$1"; else printf '%s\n' "$1"; fi; }
local_app_data=""
[ -n "${LOCALAPPDATA:-}" ] && local_app_data="$(to_unix "$LOCALAPPDATA")"

# 1. git: Claude Code needs it to add the marketplace from GitHub.
if command -v git >/dev/null 2>&1; then
  report OK git "$(git --version 2>/dev/null)"
else
  report MISSING git "Git is not on PATH."
fi

# 2. uv: starts the MCP server and installs its Python dependency (and Python itself if needed).
uv_on_path="$(command -v uv 2>/dev/null)"
uv_elsewhere="$(first_existing "$HOME/.local/bin/uv" "$HOME/.local/bin/uv.exe" "$HOME/.cargo/bin/uv" "$HOME/.cargo/bin/uv.exe")"
if [ -n "$uv_on_path" ]; then
  report OK uv "$(uv --version 2>/dev/null) at $uv_on_path"
elif [ -n "$uv_elsewhere" ]; then
  report WARN uv "Installed at $uv_elsewhere but not on PATH. Restart Claude Code (or add its folder to PATH) so the MCP server can start."
else
  report MISSING uv "uv is not installed."
fi

# 3. agy: the Antigravity CLI the bridge calls.
agy_bin=""
agy_off_path=0
if [ -n "${AGY_BIN:-}" ] && [ -f "$(to_unix "$AGY_BIN")" ]; then
  agy_bin="$(to_unix "$AGY_BIN")"
elif command -v agy >/dev/null 2>&1; then
  agy_bin="$(command -v agy)"
else
  agy_lad=""
  [ -n "$local_app_data" ] && agy_lad="$local_app_data/agy/bin/agy.exe"
  agy_bin="$(first_existing "$agy_lad" "$HOME/AppData/Local/agy/bin/agy.exe" "$HOME/.local/bin/agy")"
  [ -n "$agy_bin" ] && agy_off_path=1
fi
if [ -n "$agy_bin" ] && [ "$agy_off_path" -eq 1 ]; then
  report WARN agy "Installed at $agy_bin but not on PATH. The MCP server still finds it; restart Claude Code (or add its folder to PATH) to use agy in a terminal."
elif [ -n "$agy_bin" ]; then
  report OK agy "$("$agy_bin" --version 2>/dev/null | head -n 1) at $agy_bin"
else
  report MISSING agy "Antigravity CLI (agy) is not installed, or AGY_BIN points to a missing file."
fi

# 4. Sign-in: only in the full check, because agy may open a browser when nobody is signed in.
if [ "$quick" -eq 0 ] && [ -n "$agy_bin" ]; then
  models_out="$(run_with_limit 45 "$agy_bin" models 2>/dev/null || true)"
  count="$(printf '%s\n' "$models_out" | grep -c "$(printf '\t')")"
  gemini4="$(printf '%s\n' "$models_out" | grep -c '^gemini-4-')"
  if [ "$count" -gt 0 ]; then
    report OK signin "agy returned $count models ($gemini4 Gemini 4 variants)."
  else
    report MISSING signin "agy returned no models: not signed in, no network, or no Antigravity plan on this account."
  fi
fi

if [ "$quick" -eq 1 ] && [ "$missing" -eq 0 ]; then
  has_warn=0
  for l in "${lines[@]}"; do case "$l" in WARN*) has_warn=1 ;; esac; done
  [ "$has_warn" -eq 0 ] && exit 0
fi

if [ "$quick" -eq 1 ]; then
  echo "antigravity-gemini plugin: some prerequisites are not ready, so the Gemini tools may not work."
fi
echo "os $os"
for l in "${lines[@]}"; do echo "$l"; done
if [ "$quick" -eq 1 ]; then
  echo "Tell the user, and offer to run /antigravity-gemini:setup, which installs what is missing after they confirm."
  # A SessionStart hook only passes its output to Claude on exit code 0.
  exit 0
fi
exit "$missing"
