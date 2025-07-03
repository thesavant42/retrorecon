#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

git pull

LISTEN_ADDR="127.0.0.1"
while getopts "l:" opt; do
  case $opt in
    l)
      LISTEN_ADDR="$OPTARG"
      ;;
  esac
done

if [ ! -d venv ]; then
  python3 -m venv venv
fi

venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt

export RETRORECON_LOG_LEVEL=DEBUG
export RETRORECON_LISTEN="$LISTEN_ADDR"

python_cmd="venv/bin/python"
# Setup vendored MCP SQLite server
MCP_DIR="external/mcp-sqlite"
if [ ! -d "$MCP_DIR/.venv" ]; then
  python3 -m venv "$MCP_DIR/.venv"
fi
"$MCP_DIR/.venv/bin/pip" install --upgrade pip
"$MCP_DIR/.venv/bin/pip" install -e "$MCP_DIR"

# Resolve database path for MCP server
DB_PATH="${RETRORECON_DB:-$(pwd)/db/waybax.db}"
if [ ! -f "$DB_PATH" ]; then
  echo "Database not found at $DB_PATH"
fi

# Start MCP server in background and ensure cleanup
"$MCP_DIR/.venv/bin/python" -m mcp_server_sqlite --db-path "$DB_PATH" &
MCP_PID=$!
trap 'kill $MCP_PID' EXIT

# On WSL, using win32 path may create issues; always use the venv python
"$python_cmd" app.py
