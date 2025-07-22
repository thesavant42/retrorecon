# RetroRecon MCP Setup Guide

This guide will explain the 


## Understanding the 'program not found' Error

The error message `Failed to spawn: mcp-server-sqlite` followed by `Caused by: program not found` indicates that the `mcp-server-sqlite` executable could not be located by the system when the RetroRecon application attempted to launch it. This is a common issue when the program's path is not correctly set in the system's environment variables or when the executable itself is missing or not properly installed.

In the context of RetroRecon, the `launch_app.bat` script (for Windows) and `mcp_manager.py` are responsible for setting up and launching the `mcp-server-sqlite` subprocess. The `launch_app.bat` script attempts to create a virtual environment specifically for `mcp-server-sqlite` within the `external\mcp-sqlite` directory and then installs `mcp-server-sqlite` in editable mode using `pip install -e %MCP_DIR%`. The `mcp_manager.py` then tries to execute `mcp_server_sqlite` using `sys.executable -m mcp_server_sqlite`.

Our investigation revealed that while the `launch_app.bat` script attempts to set up a virtual environment and install `mcp-server-sqlite`, the `mcp-server-sqlite` executable itself is not directly placed in the `Scripts` directory of the virtual environment in a way that makes it globally accessible or directly executable without the `-m` flag. Instead, it's designed to be run as a Python module.

## Solution: Ensuring `mcp-server-sqlite` is Properly Installed and Executable

The core of the problem lies in how `mcp-server-sqlite` is expected to be launched. It's not a standalone executable in the traditional sense that you can just type `mcp-server-sqlite` and run. It's a Python module that needs to be executed via the Python interpreter.

Here's how to ensure it's set up correctly:

### Step 1: Verify Python and Virtual Environment Setup

First, ensure you have Python installed and that the virtual environment for `mcp-sqlite` is correctly created and activated. The `launch_app.bat` script handles this, but it's good to verify.

1.  **Navigate to the RetroRecon directory:**
    ```bash
    cd /path/to/your/retrorecon
    ```

2.  **Run the `launch_app.bat` script (or `launch_app.sh` for Linux/macOS):**
    This script will attempt to create and set up the virtual environments.
    ```bash
    .\launch_app.bat
    ```
    or
    ```bash
    ./launch_app.sh
    ```

### Step 2: Manually Install `mcp-server-sqlite` (if necessary)

If the `launch_app.bat` script didn't successfully install `mcp-server-sqlite` or if you're setting it up manually, you can do so within its dedicated virtual environment:

1.  **Create the virtual environment (if it doesn't exist):**
    ```bash
    python -m venv external/mcp-sqlite/.venv
    ```

2.  **Activate the virtual environment:**
    *   **Windows:**
        ```bash
        external\mcp-sqlite\.venv\Scripts\activate
        ```
    *   **Linux/macOS:**
        ```bash
        source external/mcp-sqlite/.venv/bin/activate
        ```

3.  **Install `mcp-server-sqlite` in editable mode:**
    This command tells pip to install the package located at `external/mcp-sqlite` in 


editable mode, which means that changes to the source code will be reflected immediately without needing to reinstall.
    ```bash
    pip install -e external/mcp-sqlite
    ```

### Step 3: Running the Application

With `mcp-server-sqlite` properly installed in its virtual environment, the `launch_app.bat` script should now be able to launch it correctly. The script uses `powershell` to start the `mcp-server-sqlite` process in the background and then launches the Flask application.

## Configuring Flask and LM Studio

You mentioned that your Flask app is on port 5000 and your LM Studio listens on 1234. Let's clarify how these components interact with `mcp-server-sqlite` in the RetroRecon architecture.

*   **Flask App (RetroRecon):** The Flask application, launched via `app.py`, is the main web interface for RetroRecon. It runs on port 5000 by default, as configured in `app.py` (`port = int(os.environ.get('RETRORECON_PORT', '5000'))`). The Flask app is responsible for launching and managing the `mcp-server-sqlite` subprocess. It does *not* directly communicate with LM Studio over a network port.

*   **`mcp-server-sqlite`:** This is a local server that provides a Model Context Protocol (MCP) interface to the SQLite database. As we've established, it's launched as a subprocess by the Flask app. It communicates with the Flask app via standard input/output, not over a network socket. The `MCP_PORT` variable in `mcp_manager.py` is a remnant and is not actually used for a TCP connection.

*   **LM Studio:** LM Studio is a separate application for running local language models. The error logs you provided show that LM Studio is trying to connect to an MCP bridge. This is where the confusion likely arises. The `mcp-server-sqlite` in RetroRecon is *not* intended to be a general-purpose MCP server for other applications like LM Studio to connect to. It's a dedicated, internal component of RetroRecon.

**Therefore, you do not need to configure LM Studio to connect to `mcp-server-sqlite`.** The connection error you see in the LM Studio logs is a symptom of LM Studio's own MCP bridge failing, likely because it's not configured to connect to a running MCP server, or the server it's trying to connect to is not available.

### Summary of the Correct Setup:

1.  **RetroRecon:**
    *   Run `launch_app.bat` (or `launch_app.sh`).
    *   This will start the Flask web server on `http://127.0.0.1:5000` (or the address you specify with the `-l` flag).
    *   The Flask app will automatically start and manage the `mcp-server-sqlite` subprocess.

2.  **LM Studio:**
    *   Run LM Studio as a separate application.
    *   If you are using LM Studio to serve a local LLM, you would typically configure your application (in this case, if you were to extend RetroRecon to use it) to make API calls to the endpoint provided by LM Studio (e.g., `http://localhost:1234/v1/chat/completions`).

There is no direct connection between the `mcp-server-sqlite` from RetroRecon and LM Studio. The `mcp-server-sqlite` is an internal implementation detail of RetroRecon.

I hope this guide clarifies the setup and helps you get RetroRecon running smoothly. If you have any further questions, feel free to ask!

