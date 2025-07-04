# RetroRecon MCP Setup Guide

This guide explains how to ensure the bundled `mcp-server-sqlite` starts correctly.
The server is launched automatically by the Flask application and communicates over
standard input/output—no TCP port is exposed.

## Steps

1. Run `launch_app.sh` (Linux/macOS) or `launch_app.bat` (Windows).
   These scripts create a virtual environment under `external/mcp-sqlite` and
   install the server in editable mode.
2. The Flask app will spawn `mcp-server-sqlite` whenever a database is created or
   loaded. If you see a "program not found" error, verify that the virtual
   environment exists and contains the package:
   ```bash
   ls external/mcp-sqlite/.venv
   ```
   Re-run the launch script if necessary.
3. There is no need to configure a port or connect LM Studio to this server. It
   is an internal helper used solely by RetroRecon.
