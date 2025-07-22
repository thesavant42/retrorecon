import os

CONFIG_VARS = {
    "RETRORECON_DB": {
        "desc": "The path to the SQLite database RetroRecon and the MCP server use.",
        "default": "db\waybax.db (relative to project root)",
        "example": r"db\waybax.db"
    },
    "RETRORECON_LISTEN": {
        "desc": "The IP address/interface for the Flask web server to bind to.",
        "default": "127.0.0.1 (localhost only)",
        "example": "0.0.0.0 (all interfaces), 192.168.1.10"
    },
    "MCP_VENV": {
        "desc": "Path to Python venv for the MCP server (advanced; usually auto-managed).",
        "default": r"external\mcp-sqlite\.venv (Windows default, relative to project root)",
        "example": r"C:\Users\youruser\GitHub\retrorecon\external\mcp-sqlite\.venv"
    }
}

def print_config_summary():
    print("RetroRecon/MCP Environment Configuration:\n")
    for var, info in CONFIG_VARS.items():
        val = os.environ.get(var)
        print(f"{var}:")
        print(f"  Current value: {val if val else '[not set]'}")
        print(f"  Description  : {info['desc']}")
        print(f"  Default      : {info['default']}")
        print(f"  Example      : {info['example']}")
        if not val:
            print("  [INFO] Using the default value above.\n")
        else:
            print("  [INFO] Using the value shown above.\n")

if __name__ == "__main__":
    print_config_summary()