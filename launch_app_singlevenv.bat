@echo off
REM RetroRecon all-in-one Windows launch script using a single venv

REM Usage:
REM   launch_app_singlevenv.bat                          (uses db\waybax.db)
REM   launch_app_singlevenv.bat C:\path\to\your.db       (uses specified db file)

cd /d "%~dp0"

REM Create venv if it doesn't exist
if not exist venv (
    python -m venv venv
)

REM Upgrade pip and install main requirements
venv\Scripts\python -m pip install --upgrade pip
venv\Scripts\pip install -r requirements.txt

REM Install MCP server requirements into the same venv
if exist external\mcp-sqlite\setup.py (
    venv\Scripts\pip install -e external\mcp-sqlite
)

REM Determine DB path (argument takes precedence)
if "%~1"=="" (
    set DB_PATH=%cd%\db\waybax.db
) else (
    set DB_PATH=%~1
)

if not exist "%DB_PATH%" (
    echo Database not found at %DB_PATH%
    echo Creating empty SQLite file...
    venv\Scripts\python -c "import sqlite3; sqlite3.connect(r'%DB_PATH%').close()"
)

REM Set listen address to localhost by default
set LISTEN_ADDR=127.0.0.1

REM Start MCP server in background
start "MCP Server" venv\Scripts\python.exe -m mcp_server_sqlite --db-path "%DB_PATH%"

REM Wait a moment to let MCP server start up (optional)
timeout /t 2 >nul

REM Launch main app
venv\Scripts\python app.py

REM Optional: Stop MCP server after app exits (clean up)
REM If you want to ensure shutdown, you can add more logic here