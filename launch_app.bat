@echo off
cd /d "%~dp0"

set LISTEN_ADDR=127.0.0.1
if "%1"=="-l" (
    set LISTEN_ADDR=%2
    shift
    shift
)

REM Accept optional DB path as first argument after -l
if "%1"=="" (
    set DB_PATH=%cd%\db\waybax.db
) else (
    set DB_PATH=%1
)

git pull

if not exist venv (
    python -m venv venv
)

venv\Scripts\python -m pip install --upgrade pip
venv\Scripts\pip install -r requirements.txt

set RETRORECON_LOG_LEVEL=DEBUG
set RETRORECON_LISTEN=%LISTEN_ADDR%

set RETRORECON_DB=%DB_PATH%

venv\Scripts\python app.py
