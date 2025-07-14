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

## MCP Server Configuration Example

External servers are defined in a single JSON or YAML file such as
`mcp_servers.json`. Set the path with the `RETRORECON_MCP_SERVERS_FILE`
environment variable if needed. Each entry specifies how the server should be
launched or contacted:

```yaml
- name: memory
  transport: stdio
  command: ["basic-memory", "mcp", "--transport", "stdio"]
  model: memory
  description: A memory server for storing and retrieving information.
```

Place this file where your RetroRecon instance can load it (for example in the
project root) and ensure the application reads it on startup.

## Launching the Server

When using the `stdio` transport, RetroRecon starts the MCP server as a
subprocess. A simplified example looks like this:

```python
import subprocess

proc = subprocess.Popen(
    ["basic-memory", "mcp", "--transport", "stdio"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True,
)
```

RetroRecon keeps the process handle and communicates with the server through the
captured `stdin` and `stdout` streams.

## Listing Available Tools

To query a running server for its tool metadata, create a FastMCP client. The
client can introspect the server and return its registered tools:

```python
from fastmcp import StdioClient

client = StdioClient(proc.stdout, proc.stdin)
metadata = client.get_metadata()
print(metadata.tools)
```

The returned list contains tool names and schemas, which RetroRecon uses to
register each tool under the `<server>_` prefix for the LLM.
