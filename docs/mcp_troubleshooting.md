# RetroRecon MCP Server Troubleshooting and Implementation Guide

This document provides guidance on troubleshooting Model Context Protocol (MCP) server issues within the RetroRecon application. The default setup uses the `fetch-mcp` Node module as an SSE service for web content retrieval.

## 1. Understanding the RetroRecon MCP Integration

RetroRecon integrates an MCP server directly within its Flask application via the `RetroReconMCPServer` class in `retrorecon/mcp/server.py`. Earlier versions attempted to mount additional FastMCP servers, but this feature has been removed. The built-in server still handles SQL queries and a simple time function.

Key observations from the codebase:

*   **`RetroReconMCPServer`**: This class (in `retrorecon/mcp/server.py`) acts as RetroRecon's internal MCP server. It includes tools for `_query_sqlite`, `_get_current_datetime`, and `_fetch_url_content`.
*   **`MCPConfig`**: Defined in `retrorecon/mcp/config.py`, this dataclass holds configuration for the MCP server, including `api_base`, `model`, `temperature`, `row_limit`, `api_key`, `timeout`, and `alt_api_bases`.
*   **External Server Configuration**: Support for additional FastMCP servers has been removed, so the `mcp_servers` field is unused.


## 3. External Fetch Server

RetroRecon relies on the `fetch-mcp` package to retrieve web content. The service exposes an SSE endpoint (by default `http://localhost:3000/sse`). Add an entry like the following to `mcp_servers.json` and ensure the Node server is running:

```json
[
  {
    "name": "fetch",
    "transport": "sse",
    "url": "http://localhost:3000/sse"
  }
]
```

## 4. Recommendations for Programming Agent

To the programming agent, the following recommendations are provided to address the MCP server integration issues and facilitate the addition of new servers:

### 4.1. Enhance MCP Server Discovery and Status Reporting

**Problem**: The current implementation makes it difficult to ascertain why `memory` and `sequential-thinking` servers are not working, as there's limited visibility into their connection status or errors during tool invocation.

**Recommendation**: Implement robust MCP server discovery and status reporting mechanisms. This involves:

*   **Active Health Checks**: Periodically attempt to connect to the `api_base` of each configured MCP server and log its availability. This could be a simple HTTP GET request to the server's root or a dedicated health endpoint if the MCP server provides one. For STDIO servers, this would involve attempting to launch the process and verifying it runs without immediate errors.
*   **Detailed Error Logging**: When an MCP server connection fails or a tool invocation returns an error, log comprehensive details, including the server's `name`, `transport` type, `api_base` (if applicable) or `command` (if applicable), the specific error message, and any relevant stack traces. This will greatly aid in diagnosing issues like network accessibility, firewall blocks, incorrect server configurations, or issues with launching STDIO processes.
*   **User Interface for Server Status**: (Optional but highly recommended) Develop a simple UI within RetroRecon that displays the status of configured MCP servers (e.g., online/offline, last successful connection, last error). This would provide immediate feedback to the user about server availability.

### 4.2. Refactor MCP Server Configuration and Loading to Support Multiple Transports

**Problem**: The `mcp_servers` list is hardcoded in `retrorecon/mcp/config.py` and currently only supports `api_base`, making it unsuitable for STDIO modules.

**Recommendation**: Allow for more flexible MCP server configuration that explicitly defines the `transport` type and associated parameters (e.g., `api_base` for HTTP/SSE, `command` for STDIO). This involves:

*   **Update `MCPServersConfig`**: Modify the `MCPServersConfig` dataclass in `retrorecon/mcp/config.py` to include a `transport` field (e.g., `Literal["http", "stdio", "sse"]`, defaulting to `http`) and a `command` field (e.g., `Optional[List[str]] = None`) for STDIO servers. The `api_base` field would then become optional and only used for HTTP/SSE transports.
*   **External Configuration File**: Implement logic to load MCP server configurations from an external file (e.g., `mcp_servers.json` or `mcp_servers.yaml`). This file could be located in the user's data directory or a configurable path, allowing users to add or remove servers without modifying the core application code.
*   **Dynamic Server Registration**: Allow RetroRecon to dynamically register and unregister MCP servers based on the loaded configuration and their specified `transport` type.

### 4.3. Implement a Generic MCP Server Integration Mechanism

**Problem**: While `RetroReconMCPServer` is a good start, integrating new external MCP servers might require repetitive code if not generalized.

**Recommendation**: Develop a more generic mechanism for integrating external MCP servers, capable of handling different transport types. This could involve:

*   **MCP Client Abstraction**: Create a clear abstraction layer for interacting with MCP clients that can dynamically select the appropriate `FastMCP.Client` transport (e.g., `HttpClient`, `StdioClient`, `SSEClient`) based on the `transport` field in the configuration.
*   **Tool Discovery and Invocation**: Implement a robust system for discovering tools exposed by external MCP servers and invoking them. This would involve parsing the MCP server's capabilities (e.g., via its OpenAPI schema for HTTP/SSE, or through introspection for STDIO) and dynamically creating callable functions or methods within RetroRecon.

### 4.4. Testing and Validation

**Problem**: Without clear testing procedures, it's hard to confirm if MCP servers are correctly integrated and functioning.

**Recommendation**: Establish clear testing and validation procedures for MCP server integration:

*   **Unit Tests for MCP Integration**: Write unit tests that simulate connections to MCP servers (both HTTP/SSE and STDIO) and verify tool invocation. This will catch regressions and ensure that changes to the MCP integration logic do not break existing functionality.
*   **Integration Tests with Mock Servers**: Create integration tests that use mock MCP servers to simulate various scenarios (e.g., successful tool invocation, server errors, network timeouts, process exit for STDIO). This will help ensure the robustness of the MCP integration.
*   **User-Friendly Testing Tools**: Provide simple, user-friendly tools or commands within RetroRecon that allow users to test the connectivity and functionality of their configured MCP servers. For example, a CLI command like `retrorecon mcp test <server_name>` could attempt to connect to a specified server and list its available tools, providing specific feedback based on the transport type.

## 5. Conclusion

By addressing the fundamental difference in communication mechanisms for STDIO versus HTTP/SSE MCP servers, and by implementing a more flexible and robust framework for integrating new MCP servers, RetroRecon can significantly enhance its capabilities and provide a more seamless experience for users. These improvements allow the application to interact with a wider range of data sources and services.

## Appendix: Commands for User to Run

To help diagnose the `memory` and `sequential-thinking` server issues, please run the following commands in your Windows 11 Command Prompt or PowerShell and provide the output:

### Verify `basic-memory` Command:

```cmd
where basic-memory
```

### RetroRecon Debug Logging:

First, you will need to modify the RetroRecon logging configuration to `DEBUG` level. This typically involves finding the `logging.basicConfig` call in `retrorecon/__init__.py` or a similar central configuration file and changing `level=logging.INFO` to `level=logging.DEBUG`.

After modifying the logging level, run RetroRecon as usual and capture the console output:

```cmd
.\launch_app.bat > retrorecon_debug_log.txt 2>&1
```

Then, please provide the `retrorecon_debug_log.txt` file.

## References

*   [Model Context Protocol Official Documentation](https://modelcontextprotocol.io/)
*   [FastMCP GitHub Repository](https://github.com/jlowin/fastmcp)
*   [RetroRecon GitHub Repository](https://github.com/thesavant42/retrorecon)
