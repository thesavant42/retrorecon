#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

# git pull - removed to prevent overwriting local changes

LISTEN_ADDR=""
DB_PATH=""

if [ -f launch_config.json ]; then
  LISTEN_ADDR=$(python3 - <<'EOF'
import json,sys
print(json.load(open('launch_config.json')).get('listen_addr',''))
EOF
  )
  DB_PATH=$(python3 - <<'EOF'
import json,sys
print(json.load(open('launch_config.json')).get('db_path',''))
EOF
  )
fi

[ -z "$LISTEN_ADDR" ] && LISTEN_ADDR="127.0.0.1"
[ -z "$DB_PATH" ] && DB_PATH="$(pwd)/db/waybax.db"

if [ ! -d venv ]; then
  python3 -m venv venv
fi

venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt

export RETRORECON_LOG_LEVEL=DEBUG
export RETRORECON_LISTEN="$LISTEN_ADDR"

python_cmd="venv/bin/python"
export RETRORECON_DB="$DB_PATH"
if [ ! -f "$DB_PATH" ]; then
  echo "Database not found at $DB_PATH"
fi

# On WSL, using win32 path may create issues; always use the venv python
"$python_cmd" app.py
