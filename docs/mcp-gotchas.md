# MCP Gotchas

This document summarizes issues discovered when working with the Model Context Protocol (MCP) integration.

## 1. Platform-specific paths

`mcp_servers.json` originally contained Windows style paths such as `".\\venv\\Scripts\\python.exe"`. On non-Windows platforms these commands do not exist which leads to `FileNotFoundError` or large stack traces when the MCP modules fail to start. The configuration now uses the portable `python` command instead.

## 2. Missing modules

If the configured STDIO command references a module that is not installed (for example `basic-memory`) the memory module fails to start. The startup code now checks for the module using `importlib.util.find_spec` and logs `"MCP module not installed"` instead of raising an exception.

***

During development each major test run is noted below.

- **Test run 1**: After installing dependencies and running the test suite, all `tests/test_mcp_*` tests passed.
- **Test run 2**: Verified that launching the MCP server logs a clear error when `basic-memory` is missing. No unhandled exceptions occurred.
- **Test run 3**: Updated shutdown logic to close the portal with `__exit__(None, None, None)`. Launching with a missing module no longer produces cancel scope errors.
