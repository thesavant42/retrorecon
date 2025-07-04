# RetroRecon MCP Setup Guide

This guide explains how RetroRecon's embedded MCP server works.
The application now uses the `RetroReconMCPServer` class directly so no
separate `mcp-server-sqlite` process is launched.

## Steps

1. Run `launch_app.sh` (Linux/macOS) or `launch_app.bat` (Windows) to install
   the Python dependencies.
2. The Flask app automatically instantiates `RetroReconMCPServer` whenever a
   database is created or loaded. No separate background process is required.
3. There is no need to configure a port or connect LM Studio; the server runs
   entirely inside the application.
4. Set `RETRORECON_LOG_LEVEL=DEBUG` before launching to view MCP debug output in
   the console. Debug logs now include detailed information on which MCP servers
   are mounted, any health check failures, and when alternate API bases are used
   for fallback requests.

## Dynamic Tool Discovery

The embedded server now aggregates tools from all configured MCP services at
runtime. When a new service is mounted (locally or remotely), its tool list is
queried during startup. Healthy services are mounted under their configuration
name and their tools automatically become available to the LLM with the prefix
`<name>_`. No manual code changes are required for additional modules—simply add
an entry in the MCP configuration.
