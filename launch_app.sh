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
# On WSL, using win32 path may create issues; always use the venv python
"$python_cmd" app.py
