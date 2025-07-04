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

set MCP_DIR=external\mcp-sqlite
if "%MCP_VENV%"=="" (
    set MCP_VENV=%MCP_DIR%\.venv
)
if not exist %MCP_VENV% (
    python -m venv %MCP_VENV%
)

%MCP_VENV%\Scripts\python -m pip install --upgrade pip
%MCP_VENV%\Scripts\pip install -e %MCP_DIR%

set RETRORECON_DB=%DB_PATH%

for /f %%p in ('powershell -NoProfile -Command "($p=Start-Process -FilePath '%MCP_VENV%\Scripts\python.exe' -ArgumentList '-m mcp_server_sqlite --db-path \"%DB_PATH%\"' -PassThru); $p.Id"') do set MCP_PID=%%p

venv\Scripts\python app.py

powershell -NoProfile -Command "Stop-Process -Id %MCP_PID%"
