# RetroRecon MCP Server Troubleshooting and Implementation Guide

This document provides guidance on troubleshooting Model Context Protocol (MCP) server issues within the RetroRecon application and outlines the steps to integrate new MCP servers, using `mcp/fetch` as a practical example.

## 1. Understanding the RetroRecon MCP Integration

RetroRecon integrates an MCP server directly within its Flask application via the `RetroReconMCPServer` class in `retrorecon/mcp/server.py`. Earlier versions attempted to mount additional FastMCP servers, but this feature has been removed. The built-in server still handles SQL queries and a simple time function.

Key observations from the codebase:

*   **`RetroReconMCPServer`**: This class (in `retrorecon/mcp/server.py`) acts as RetroRecon's internal MCP server. It includes tools for `_query_sqlite`, `_get_current_datetime`, and `_fetch_url_content`. The `_fetch_url_content` tool is particularly relevant for the `mcp/fetch` use case.
*   **`MCPConfig`**: Defined in `retrorecon/mcp/config.py`, this dataclass holds configuration for the MCP server, including `api_base`, `model`, `temperature`, `row_limit`, `api_key`, `timeout`, and `alt_api_bases`.
*   **External Server Configuration**: Support for additional FastMCP servers has been removed, so the `mcp_servers` field is unused.


## 3. Adding a New MCP Server from Scratch: `mcp/fetch` Use Case

To add a new MCP server, you'll need to define its configuration in `retrorecon/mcp/config.py` and ensure that RetroRecon can properly interact with it. The `mcp/fetch` server, which provides web content fetching capabilities, is an excellent use case. Note that `mcp/fetch` can also be an STDIO module, or an HTTP server. For this example, we will assume it is an HTTP server for demonstration purposes, but the principles for STDIO apply as described above.

### 3.1. Understanding `mcp/fetch`

The `mcp/fetch` server typically exposes a tool (or tools) that can take a URL as input and return its content. The `RetroReconMCPServer` already has a `_fetch_url_content` tool, which demonstrates the functionality. For an external `mcp/fetch` server, you would be leveraging a separate service that provides this capability.

### 3.2. Steps to Add `mcp/fetch` Server (assuming HTTP transport):

1.  **Choose or Implement an `mcp/fetch` Server**: You can either use an existing `mcp/fetch` server implementation (e.g., from the `modelcontextprotocol` GitHub organization or PyPI) or create your own. For this guide, we'll assume you have a `mcp/fetch` server running and accessible at a specific `api_base` URL.

    *   **Example (Conceptual `mcp/fetch` server using FastMCP)**:
        ```python
        # fetch_server.py
        from fastmcp import FastMCP
        import httpx
        from mcp.types import TextContent

        mcp = FastMCP("fetch-server")

        @mcp.tool()
        async def fetch_url(url: str) -> TextContent:
            """Fetches the content of a given URL.

            Args:
                url: The URL to fetch.

            Returns:
                The content of the URL as a TextContent object.
            """
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    return TextContent(text=response.text)
            except httpx.RequestError as e:
                return TextContent(text=f"Error fetching URL {url}: {e}")
            except httpx.HTTPStatusError as e:
                return TextContent(text=f"HTTP error fetching URL {url}: {e}")

        if __name__ == "__main__":
            mcp.run()
        ```
        To run this conceptual server, you would typically execute `python fetch_server.py` in a terminal, and it would listen on a default port (e.g., 8000 or 8001, depending on FastMCP's default or if specified).

2.  **Configure `retrorecon/mcp/config.py`**: Open the `retrorecon/mcp/config.py` file and add a new entry to the `mcp_servers` list for your `mcp/fetch` server. Ensure the `api_base` points to where your `mcp/fetch` server is running.

    *   **Modified `config.py` (example, assuming `transport` field is added to `MCPServersConfig`)**:
        ```python
        # ... (existing imports and MCPConfig class)

        mcp_servers: MCPServersConfig = MCPServersConfig(
            servers=[
                {
                    "name": "memory",
                    "transport": "stdio", # New field
                    "command": ["npx", "@modelcontextprotocol/server-memory"], # New field
                    "model": "memory",
                    "description": "A memory server for storing and retrieving information.",
                },
                {
                    "name": "sequential-thinking",
                    "transport": "stdio", # New field
                    "command": ["npx", "@modelcontextprotocol/server-sequential-thinking"], # New field
                    "model": "sequential-thinking",
                    "description": "A server for sequential thinking and reasoning.",
                },
                {
                    "name": "fetch",
                    "transport": "http", # Explicitly set for HTTP server
                    "api_base": "http://localhost:8002/v1", # Assuming your fetch server runs on port 8002
                    "model": "fetch", # Or whatever model name your fetch server uses
                    "description": "A server for fetching web content.",
                },
            ]
        )
        ```
        **Important**: Adjust `http://localhost:8002/v1` to the actual address and port where your `mcp/fetch` server is running. For STDIO servers, replace `api_base` with `command` and set `transport` to `stdio`.

3.  **Restart RetroRecon**: After modifying `config.py`, you must restart the RetroRecon application for the changes to take effect.

4.  **Verify Integration**: Once RetroRecon is restarted, you should be able to interact with the `fetch` server through RetroRecon's MCP client. The exact method of interaction will depend on how RetroRecon exposes its MCP client to the user interface or internal logic. If RetroRecon has a mechanism to list available MCP tools, you should see the `fetch_url` tool (or whatever you named it in your `mcp/fetch` server implementation).

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

By addressing the fundamental difference in communication mechanisms for STDIO versus HTTP/SSE MCP servers, and by implementing a more flexible and robust framework for integrating new MCP servers, RetroRecon can significantly enhance its capabilities and provide a more seamless experience for users. The `mcp/fetch` use case serves as a prime example of how external MCP servers can extend RetroRecon's functionality, allowing it to interact with a wider range of data sources and services.

## Appendix: Commands for User to Run

To help diagnose the `memory` and `sequential-thinking` server issues, please run the following commands in your Windows 11 Command Prompt or PowerShell and provide the output:

### Verify `npx` Path:

```cmd
where npx
```

### RetroRecon Debug Logging:

First, you will need to modify the RetroRecon logging configuration to `DEBUG` level. This typically involves finding the `logging.basicConfig` call in `retrorecon/__init__.py` or a similar central configuration file and changing `level=logging.INFO` to `level=logging.DEBUG`.

After modifying the logging level, run RetroRecon as usual and capture the console output:

```cmd
.\launch_app.bat -l 0.0.0.0 > retrorecon_debug_log.txt 2>&1
```

Then, please provide the `retrorecon_debug_log.txt` file.

## References

*   [Model Context Protocol Official Documentation](https://modelcontextprotocol.io/)
*   [FastMCP GitHub Repository](https://github.com/jlowin/fastmcp)
*   [RetroRecon GitHub Repository](https://github.com/thesavant42/retrorecon)
