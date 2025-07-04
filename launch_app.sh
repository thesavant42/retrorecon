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

shift $((OPTIND -1))

# Accept optional DB path after -l
if [ -z "$1" ]; then
  DB_PATH="$(pwd)/db/waybax.db"
else
  DB_PATH="$1"
fi

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
MCP_VENV="${MCP_VENV:-$MCP_DIR/.venv}"
if [ ! -d "$MCP_VENV" ]; then
  python3 -m venv "$MCP_VENV"
fi

"$MCP_VENV/bin/pip" install --upgrade pip
"$MCP_VENV/bin/pip" install -e "$MCP_DIR"

export RETRORECON_DB="$DB_PATH"
if [ ! -f "$DB_PATH" ]; then
  echo "Database not found at $DB_PATH"
fi

# On WSL, using win32 path may create issues; always use the venv python
"$python_cmd" app.py
