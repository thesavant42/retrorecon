@echo off
cd /d "%~dp0"

git pull

if not exist venv (
    python -m venv venv
)

venv\Scripts\python -m pip install --upgrade pip
venv\Scripts\pip install -r requirements.txt

set RETRORECON_LOG_LEVEL=DEBUG

venv\Scripts\python app.py
