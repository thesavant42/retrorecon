@echo off
cd /d "%~dp0"

set LISTEN_ADDR=
set DB_PATH=

REM Load options from launch_config.json if present
for /f "usebackq tokens=*" %%A in (`powershell -NoProfile -Command "(Get-Content -Raw launch_config.json | ConvertFrom-Json).listen_addr" 2^>nul`) do set LISTEN_ADDR=%%A
for /f "usebackq tokens=*" %%A in (`powershell -NoProfile -Command "(Get-Content -Raw launch_config.json | ConvertFrom-Json).db_path" 2^>nul`) do set DB_PATH=%%A

if "%LISTEN_ADDR%"=="" set LISTEN_ADDR=127.0.0.1
if "%DB_PATH%"=="" set DB_PATH=%cd%\db\waybax.db

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
